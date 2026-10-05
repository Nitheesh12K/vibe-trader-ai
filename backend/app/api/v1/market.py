"""Market data API endpoints."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.market_data_service import MarketDataService
from app.schemas.market import (
    DashboardSummaryResponse,
    InstrumentItem,
    OHLCResponse,
)

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/demo", response_model=DashboardSummaryResponse, summary="Demo Market Overview Data")
def get_demo_dashboard(db: Session = Depends(get_db)) -> DashboardSummaryResponse:
    """Fetch complete demo dashboard bundle including portfolio, instruments, status, and activity."""
    service = MarketDataService(db=db)
    return service.get_dashboard_summary()


@router.get("/instruments", response_model=List[InstrumentItem], summary="List Market Instruments")
def list_instruments(
    market: Optional[str] = Query(None, description="Filter by market: FOREX, NSE, or MCX"),
    db: Session = Depends(get_db),
) -> List[InstrumentItem]:
    """Retrieve watchlist instruments filtered optionally by market segment."""
    service = MarketDataService(db=db)
    return service.get_instruments(market=market)


@router.get("/ohlc/{symbol:path}", response_model=OHLCResponse, summary="Historical OHLC Candlestick Data")
def get_ohlc_data(
    symbol: str,
    timeframe: str = Query("1D", description="Candle timeframe: 1m, 5m, 15m, 1h, 1D"),
    db: Session = Depends(get_db),
) -> OHLCResponse:
    """Retrieve historical candlestick bar data for financial charting (supports Forex pairs like EUR/USD or EUR_USD)."""
    clean_sym = symbol.strip() if symbol else ""
    if not clean_sym:
        raise HTTPException(status_code=400, detail="Invalid symbol specified")
    service = MarketDataService(db=db)
    return service.get_ohlc(symbol=clean_sym, timeframe=timeframe)


@router.post("/csv/upload", summary="Validate & Import Historical CSV Dataset")
def upload_csv_dataset(payload: dict, db: Session = Depends(get_db)):
    """
    Validates an uploaded CSV dataset for OHLC consistency, chronological ordering,
    and missing values before persisting in SQLite for backtesting or chart analysis.
    """
    from app.services.csv_data_provider import CSVDataProvider

    csv_text = payload.get("csv_content", "")
    symbol = payload.get("symbol", "CUSTOM_CSV").strip().upper()
    market = payload.get("market", "CUSTOM")
    filename = payload.get("filename", f"{symbol.lower()}.csv")
    timeframe = payload.get("timeframe", "1D")
    overwrite = payload.get("overwrite", True)

    if not csv_text:
        raise HTTPException(status_code=400, detail="Field 'csv_content' is required.")

    result = CSVDataProvider.validate_and_parse_csv(csv_content=csv_text, symbol_override=symbol)
    res_dict = result.to_dict()

    if not result.is_valid:
        return res_dict

    # Persist in SQLite
    db_record = CSVDataProvider.save_dataset(
        db=db,
        validation_result=result,
        symbol=symbol,
        market=market,
        filename=filename,
        timeframe=timeframe,
        overwrite=overwrite,
    )
    res_dict["dataset_id"] = db_record.dataset_id
    res_dict["dataset"] = {
        "dataset_id": db_record.dataset_id,
        "symbol": db_record.symbol,
        "market": db_record.market,
        "original_filename": db_record.original_filename,
        "timeframe": db_record.timeframe,
        "row_count": db_record.row_count,
        "created_at": db_record.created_at.isoformat() if db_record.created_at else None,
    }
    return res_dict


@router.get("/csv/datasets", summary="List Loaded CSV Datasets")
def list_csv_datasets(db: Session = Depends(get_db)):
    """Returns all imported CSV datasets persisted in SQLite and active cache."""
    from app.services.csv_data_provider import CSVDataProvider
    datasets = CSVDataProvider.list_datasets(db=db)
    return {
        "datasets": datasets,
        "total_datasets": len(datasets),
    }


@router.get("/csv/datasets/{dataset_id:path}", summary="Get CSV Dataset Details")
def get_csv_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Retrieve details and sample candles for a specific CSV dataset."""
    from app.services.csv_data_provider import CSVDataProvider
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
            "preview_candles": [c.model_dump() for c in candles[:10]],
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
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "preview_candles": [c.model_dump() for c in candles[:10]] if candles else [],
    }


@router.delete("/csv/datasets/{dataset_id:path}", summary="Delete CSV Dataset")
def delete_csv_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Deletes a custom CSV dataset from SQLite and memory cache with audit logging."""
    from app.services.csv_data_provider import CSVDataProvider
    success = CSVDataProvider.delete_dataset(db=db, dataset_id_or_symbol=dataset_id)
    return {
        "success": success,
        "message": f"Dataset '{dataset_id}' deleted successfully.",
    }
