"""Dedicated Datasets API router for Data Manager."""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.csv_data_provider import CSVDataProvider

router = APIRouter(prefix="/datasets", tags=["Data Manager"])


@router.get("", summary="List All Imported Datasets")
def list_datasets(db: Session = Depends(get_db)):
    """Retrieve all persisted and demo datasets."""
    datasets = CSVDataProvider.list_datasets(db=db)
    return {
        "datasets": datasets,
        "total_datasets": len(datasets),
    }


@router.get("/{dataset_id:path}", summary="Get Dataset Details and Validation Report")
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata, validation status, and preview candles for a dataset."""
    record = CSVDataProvider.get_dataset_record(db=db, dataset_id_or_symbol=dataset_id)
    if not record:
        candles = CSVDataProvider.get_dataset(symbol_or_id=dataset_id, db=db)
        if not candles:
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
        return {
            "dataset_id": f"CACHE-{dataset_id}",
            "symbol": dataset_id.upper(),
            "market": "CUSTOM",
            "row_count": len(candles),
            "is_valid": True,
            "source": "DEMO / CACHED",
            "preview_candles": [c.model_dump() for c in candles[:15]],
        }

    candles = CSVDataProvider.get_dataset(symbol_or_id=record.symbol, db=db)
    return {
        "dataset_id": record.dataset_id,
        "symbol": record.symbol,
        "market": record.market,
        "original_filename": record.original_filename,
        "timeframe": record.timeframe,
        "row_count": record.row_count,
        "start_timestamp": record.start_timestamp,
        "end_timestamp": record.end_timestamp,
        "is_valid": record.is_valid,
        "source": "USER_IMPORTED" if record.dataset_id.startswith("DS-") else "DEMO",
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "preview_candles": [c.model_dump() for c in candles[:15]] if candles else [],
    }


@router.delete("/{dataset_id:path}", summary="Delete Dataset")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Delete a custom dataset from database and cache."""
    success = CSVDataProvider.delete_dataset(db=db, dataset_id_or_symbol=dataset_id)
    return {
        "success": success,
        "message": f"Dataset '{dataset_id}' deleted successfully.",
    }


@router.post("/upload", summary="Upload and Validate CSV Dataset")
async def upload_dataset(
    file: UploadFile = File(...),
    symbol: str = Form(None),
    market: str = Form("NSE"),
    timeframe: str = Form("1D"),
    db: Session = Depends(get_db),
):
    """Upload and validate a new historical CSV dataset."""
    content = await file.read()
    res = CSVDataProvider.ingest_csv_bytes(
        file_bytes=content,
        filename=file.filename or "uploaded.csv",
        db=db,
        symbol_override=symbol,
        market=market,
        timeframe=timeframe,
    )
    return res
