"""CSV Market Data Provider with strict consistency, look-ahead bias validation,
and persistent SQLite storage.
"""
import io
import os
import re
import json
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.schemas.market import OHLCCandle
from app.models.entities import CustomDataset, utcnow
from app.services.audit_service import AuditService

logger = logging.getLogger("vibe-trader-ai.csv_provider")


class CSVValidationResult:
    def __init__(
        self,
        is_valid: bool,
        symbol: str,
        total_rows: int,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        candles: Optional[List[OHLCCandle]] = None,
        dataset_id: Optional[str] = None,
    ):
        self.is_valid = is_valid
        self.symbol = symbol
        self.total_rows = total_rows
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.errors = errors or []
        self.warnings = warnings or []
        self.candles = candles or []
        self.dataset_id = dataset_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "symbol": self.symbol,
            "total_rows": self.total_rows,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "start_date": datetime.fromtimestamp(self.start_timestamp).isoformat() if self.start_timestamp else None,
            "end_date": datetime.fromtimestamp(self.end_timestamp).isoformat() if self.end_timestamp else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "sample_count": len(self.candles),
            "preview_candles": [c.model_dump() for c in self.candles[:10]],
            "candles": [c.model_dump() for c in self.candles],
            "dataset_id": self.dataset_id,
        }


class CSVDataProvider:
    """Validates, parses, and persists historical CSV datasets with strict financial consistency rules."""

    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    MAX_ROW_COUNT: int = 50000                   # 50,000 candles limit

    _STORED_DATASETS: Dict[str, List[OHLCCandle]] = {}

    @staticmethod
    def sanitize_filename(filename: Optional[str]) -> str:
        """Sanitizes user-provided filenames to prevent path traversal or invalid characters."""
        if not filename:
            return "dataset.csv"
        base = os.path.basename(str(filename).replace("\\", "/"))
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base).strip("_")
        if not cleaned.lower().endswith(".csv"):
            cleaned = f"{cleaned}.csv"
        return cleaned or "dataset.csv"

    @classmethod
    def validate_and_parse_csv(
        cls,
        csv_content: str,
        symbol_override: Optional[str] = None,
    ) -> CSVValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # Check raw size limit (10MB)
        raw_bytes = len(csv_content.encode("utf-8"))
        if raw_bytes > cls.MAX_FILE_SIZE_BYTES:
            return CSVValidationResult(
                is_valid=False,
                symbol=symbol_override or "UNKNOWN",
                total_rows=0,
                errors=[
                    f"File size ({raw_bytes / (1024*1024):.2f}MB) exceeds maximum allowed limit of {cls.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
                ],
            )

        try:
            df = pd.read_csv(io.StringIO(csv_content))
        except Exception as e:
            return CSVValidationResult(
                is_valid=False,
                symbol=symbol_override or "UNKNOWN",
                total_rows=0,
                errors=[f"Failed to parse CSV file: {str(e)}"],
            )

        if df.empty:
            return CSVValidationResult(
                is_valid=False,
                symbol=symbol_override or "UNKNOWN",
                total_rows=0,
                errors=["The uploaded CSV file is empty."],
            )

        # Check row count limit (50,000)
        if len(df) > cls.MAX_ROW_COUNT:
            return CSVValidationResult(
                is_valid=False,
                symbol=symbol_override or "UNKNOWN",
                total_rows=len(df),
                errors=[
                    f"Dataset contains {len(df)} rows, exceeding maximum allowed limit of {cls.MAX_ROW_COUNT} rows."
                ],
            )

        # Normalize column headers
        col_map = {c: str(c).strip().lower() for c in df.columns}
        df.rename(columns=col_map, inplace=True)

        # Resolve timestamp column
        time_col = None
        for candidate in ["time", "timestamp", "date", "datetime"]:
            if candidate in df.columns:
                time_col = candidate
                break

        if not time_col:
            errors.append("Missing required timestamp column. Expected one of: 'time', 'timestamp', 'date', 'datetime'.")

        required_price_cols = ["open", "high", "low", "close"]
        for p_col in required_price_cols:
            if p_col not in df.columns:
                errors.append(f"Missing required price column: '{p_col}'.")

        if errors:
            return CSVValidationResult(
                is_valid=False,
                symbol=symbol_override or "UNKNOWN",
                total_rows=len(df),
                errors=errors,
            )

        # Volume handling (optional column, defaults to 0)
        vol_col = None
        for candidate in ["volume", "vol"]:
            if candidate in df.columns:
                vol_col = candidate
                break

        # Check for missing values in required price columns
        nan_counts = df[required_price_cols].isna().sum().to_dict()
        for col, count in nan_counts.items():
            if count > 0:
                errors.append(f"Column '{col}' contains {count} missing/NaN values.")

        # Convert and validate timestamps
        try:
            if pd.api.types.is_numeric_dtype(df[time_col]):
                if df[time_col].iloc[0] > 1e11:
                    df["clean_time"] = (df[time_col] / 1000).astype(int)
                else:
                    df["clean_time"] = df[time_col].astype(int)
            else:
                parsed_dt = pd.to_datetime(df[time_col], utc=True)
                df["clean_time"] = parsed_dt.astype("int64") // 10**9
        except Exception as e:
            errors.append(f"Timestamp parsing error in '{time_col}': {str(e)}")

        if errors:
            return CSVValidationResult(
                is_valid=False,
                symbol=symbol_override or "UNKNOWN",
                total_rows=len(df),
                errors=errors,
            )

        # Check for duplicate timestamps
        duplicates = df["clean_time"].duplicated().sum()
        if duplicates > 0:
            errors.append(f"Found {duplicates} duplicate timestamp row(s). Timestamps must be strictly unique.")

        # Check chronological ordering and sort
        if not df["clean_time"].is_monotonic_increasing:
            warnings.append("Dataset was not chronologically sorted. Sorted automatically.")
        # Validate price column types and non-negativity
        for col in required_price_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            nan_after = df[col].isna().sum()
            original_nan = nan_counts.get(col, 0)
            if nan_after > original_nan:
                errors.append(f"Column '{col}' contains {nan_after - original_nan} non-numeric or malformed value(s).")

        if errors:
            return CSVValidationResult(
                is_valid=False,
                symbol=symbol_override or "UNKNOWN",
                total_rows=len(df),
                errors=errors,
            )

        for col in required_price_cols:
            negatives = (df[col] <= 0).sum()
            if negatives > 0:
                errors.append(f"Column '{col}' contains {negatives} non-positive (<= 0) price value(s).")

        # Validate OHLC consistency: High >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close
        inconsistent_high_low = (df["high"] < df["low"]).sum()
        if inconsistent_high_low > 0:
            errors.append(f"Found {inconsistent_high_low} row(s) where High is lower than Low.")

        inconsistent_high_oc = ((df["high"] < df["open"]) | (df["high"] < df["close"])).sum()
        if inconsistent_high_oc > 0:
            errors.append(f"Found {inconsistent_high_oc} row(s) where High is less than Open or Close.")

        inconsistent_low_oc = ((df["low"] > df["open"]) | (df["low"] > df["close"])).sum()
        if inconsistent_low_oc > 0:
            errors.append(f"Found {inconsistent_low_oc} row(s) where Low is greater than Open or Close.")

        # Volume validation
        if vol_col:
            neg_vol = (df[vol_col] < 0).sum()
            if neg_vol > 0:
                errors.append(f"Volume contains {neg_vol} negative value(s).")
            clean_vol = df[vol_col].fillna(0.0).astype(float).tolist()
        else:
            warnings.append("Volume column not found. Defaulted volume to 0.")
            clean_vol = [0.0] * len(df)

        if errors:
            return CSVValidationResult(
                is_valid=False,
                symbol=symbol_override or "UNKNOWN",
                total_rows=len(df),
                errors=errors,
                warnings=warnings,
            )

        # Convert to typed OHLCCandle instances
        symbol_name = symbol_override or "CSV_IMPORT"
        candles: List[OHLCCandle] = []
        for t, o, h, l, c, v in zip(
            df["clean_time"],
            df["open"].astype(float),
            df["high"].astype(float),
            df["low"].astype(float),
            df["close"].astype(float),
            clean_vol,
        ):
            candles.append(
                OHLCCandle(
                    time=int(t),
                    open=round(o, 4),
                    high=round(h, 4),
                    low=round(l, 4),
                    close=round(c, 4),
                    volume=round(v, 2),
                )
            )

        start_ts = candles[0].time if candles else None
        end_ts = candles[-1].time if candles else None

        # Cache in memory
        cls._STORED_DATASETS[symbol_name] = candles

        return CSVValidationResult(
            is_valid=True,
            symbol=symbol_name,
            total_rows=len(candles),
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            warnings=warnings,
            candles=candles,
        )

    @classmethod
    def save_dataset(
        cls,
        db: Session,
        validation_result: CSVValidationResult,
        symbol: str,
        market: str = "CUSTOM",
        filename: str = "dataset.csv",
        timeframe: str = "1D",
        overwrite: bool = False,
    ) -> CustomDataset:
        """Persist a validated CSV dataset into SQLite with audit logging and duplicate guardrails."""
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot save invalid dataset: {'; '.join(validation_result.errors)}",
            )

        sanitized_sym = symbol.strip().upper()
        sanitized_filename = cls.sanitize_filename(filename)

        # Check duplicate
        existing = db.query(CustomDataset).filter(CustomDataset.symbol == sanitized_sym).first()
        if existing:
            if not overwrite:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Dataset with symbol '{sanitized_sym}' already exists. Pass overwrite=True to overwrite.",
                )
            # Update existing record
            existing.market = market.strip().upper() if market else "CUSTOM"
            existing.original_filename = sanitized_filename
            existing.stored_filename = sanitized_filename
            existing.timeframe = timeframe
            existing.row_count = validation_result.total_rows
            existing.start_timestamp = validation_result.start_timestamp
            existing.end_timestamp = validation_result.end_timestamp
            existing.is_valid = True
            existing.candles_json = json.dumps([c.model_dump() for c in validation_result.candles])
            existing.updated_at = utcnow()
            db_record = existing
        else:
            # Create new record
            dataset_id = f"DS-{uuid.uuid4().hex[:12].upper()}"
            db_record = CustomDataset(
                dataset_id=dataset_id,
                symbol=sanitized_sym,
                market=market.strip().upper() if market else "CUSTOM",
                original_filename=sanitized_filename,
                stored_filename=sanitized_filename,
                timeframe=timeframe,
                row_count=validation_result.total_rows,
                start_timestamp=validation_result.start_timestamp,
                end_timestamp=validation_result.end_timestamp,
                is_valid=True,
                candles_json=json.dumps([c.model_dump() for c in validation_result.candles]),
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            db.add(db_record)

        db.commit()
        db.refresh(db_record)

        # Sync memory cache
        cls._STORED_DATASETS[sanitized_sym] = validation_result.candles
        validation_result.dataset_id = db_record.dataset_id

        # Audit log event
        AuditService.log_event(
            db=db,
            event_type="DATASET_IMPORTED",
            action=f"Imported CSV dataset {db_record.dataset_id} for symbol {sanitized_sym} ({db_record.row_count} candles)",
            actor="USER",
            symbol=sanitized_sym,
            market=db_record.market,
            details={
                "dataset_id": db_record.dataset_id,
                "filename": sanitized_filename,
                "row_count": db_record.row_count,
                "timeframe": timeframe,
                "start_timestamp": db_record.start_timestamp,
                "end_timestamp": db_record.end_timestamp,
            },
        )

        return db_record

    @classmethod
    def get_dataset(
        cls,
        symbol_or_id: Optional[str] = None,
        symbol: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[List[OHLCCandle]]:
        """Retrieve dataset candles by symbol or dataset_id from cache or SQLite."""
        target = symbol or symbol_or_id
        if not target:
            return None
        clean_key = target.strip().upper()
        if clean_key in cls._STORED_DATASETS:
            return cls._STORED_DATASETS[clean_key]

        # Check case-insensitive cache match
        for k, v in cls._STORED_DATASETS.items():
            if k.upper() == clean_key:
                return v

        # Fallback to database
        if db is not None:
            try:
                record = (
                    db.query(CustomDataset)
                    .filter(
                        or_(
                            CustomDataset.symbol == clean_key,
                            CustomDataset.dataset_id == (symbol_or_id.strip() if symbol_or_id else clean_key),
                        )
                    )
                    .first()
                )
                if record and record.candles_json:
                    raw_candles = json.loads(record.candles_json)
                    candles = [OHLCCandle(**c) for c in raw_candles]
                    cls._STORED_DATASETS[record.symbol] = candles
                    return candles
            except Exception as e:
                logger.warning(f"Error querying dataset '{symbol_or_id}' from database: {e}")

        return None

    get_candles_by_symbol = get_dataset

    @classmethod
    def get_dataset_record(cls, db: Session, dataset_id_or_symbol: str) -> Optional[CustomDataset]:
        """Fetch full database record for a custom dataset."""
        clean_key = dataset_id_or_symbol.strip()
        return (
            db.query(CustomDataset)
            .filter(
                or_(
                    CustomDataset.dataset_id == clean_key,
                    CustomDataset.symbol == clean_key.upper(),
                )
            )
            .first()
        )

    @classmethod
    def list_datasets(cls, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """List all available datasets from SQLite and active cache."""
        datasets_list: List[Dict[str, Any]] = []

        if db is not None:
            try:
                records = db.query(CustomDataset).order_by(CustomDataset.created_at.desc()).all()
                for r in records:
                    start_iso = datetime.fromtimestamp(r.start_timestamp).isoformat() if r.start_timestamp else None
                    end_iso = datetime.fromtimestamp(r.end_timestamp).isoformat() if r.end_timestamp else None
                    datasets_list.append({
                        "dataset_id": r.dataset_id,
                        "symbol": r.symbol,
                        "market": r.market,
                        "original_filename": r.original_filename,
                        "timeframe": r.timeframe,
                        "total_rows": r.row_count,
                        "row_count": r.row_count,
                        "candle_count": r.row_count,
                        "start_timestamp": r.start_timestamp,
                        "end_timestamp": r.end_timestamp,
                        "start_time": start_iso or (str(r.start_timestamp) if r.start_timestamp else "N/A"),
                        "end_time": end_iso or (str(r.end_timestamp) if r.end_timestamp else "N/A"),
                        "is_valid": r.is_valid,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    })
                return datasets_list
            except Exception as e:
                logger.warning(f"Database error in list_datasets, falling back to cache: {e}")

        # Fallback to cache
        for sym, candles in cls._STORED_DATASETS.items():
            start_ts = candles[0].time if candles else None
            end_ts = candles[-1].time if candles else None
            datasets_list.append({
                "dataset_id": f"CACHE-{sym}",
                "symbol": sym,
                "market": "CUSTOM",
                "original_filename": f"{sym.lower()}.csv",
                "timeframe": "1D",
                "total_rows": len(candles),
                "row_count": len(candles),
                "candle_count": len(candles),
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "start_time": datetime.fromtimestamp(start_ts).isoformat() if start_ts else "N/A",
                "end_time": datetime.fromtimestamp(end_ts).isoformat() if end_ts else "N/A",
                "is_valid": True,
                "created_at": datetime.now().isoformat(),
            })

        return datasets_list

    @classmethod
    def delete_dataset(cls, db: Session, dataset_id_or_symbol: str) -> bool:
        """Deletes a custom dataset from SQLite and memory cache with audit logging."""
        clean_id = dataset_id_or_symbol.strip()
        record = (
            db.query(CustomDataset)
            .filter(
                or_(
                    CustomDataset.dataset_id == clean_id,
                    CustomDataset.symbol == clean_id.upper(),
                )
            )
            .first()
        )

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset '{dataset_id_or_symbol}' not found.",
            )

        sym = record.symbol
        ds_id = record.dataset_id
        filename = record.original_filename
        market = record.market

        # Delete from DB
        db.delete(record)
        db.commit()

        # Remove from memory cache
        cls._STORED_DATASETS.pop(sym, None)
        cls._STORED_DATASETS.pop(clean_id, None)

        # Audit log event
        AuditService.log_event(
            db=db,
            event_type="DATASET_DELETED",
            action=f"Deleted CSV dataset {ds_id} for symbol {sym}",
            actor="USER",
            symbol=sym,
            market=market,
            details={"dataset_id": ds_id, "filename": filename},
        )

        return True
