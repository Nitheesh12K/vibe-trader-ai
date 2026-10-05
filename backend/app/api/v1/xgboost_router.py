"""API Router for XGBoost Machine Learning Quantitative Research."""
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.xgboost import (
    XGBoostTrainRequest,
    XGBoostModelSummary,
    XGBoostModelDetail,
    XGBoostPredictRequest,
    XGBoostPredictionResponse,
    XGBoostJobResponse,
    XGBoostSynthesizeRequest,
    XGBoostSynthesizeResponse,
)
from app.services.xgboost_service import XGBoostService
from app.services.xgboost_advisory_explainer import XGBoostAdvisoryExplainer
from app.models.entities import XGBoostExperiment, XGBoostPredictionRecord

logger = logging.getLogger("vibe-trader-ai.xgboost_api")

router = APIRouter(prefix="/xgboost", tags=["Machine Learning - XGBoost Quantitative Research"])


@router.post("/train", response_model=XGBoostModelDetail, summary="Train XGBoost Model on Historical Data")
def train_xgboost_model(req: XGBoostTrainRequest, db: Session = Depends(get_db)):
    """Trains an XGBoost classifier to predict next-bar price direction using strictly causal features,
    chronological time-based splits, naive baseline benchmarking, and walk-forward validation.
    """
    try:
        experiment = XGBoostService.train_model(
            db=db,
            symbol=req.symbol.strip().upper(),
            timeframe=req.timeframe,
            market=req.market,
            train_ratio=req.train_ratio,
            val_ratio=req.val_ratio,
            num_folds=req.num_folds,
            max_depth=req.max_depth,
            learning_rate=req.learning_rate,
            n_estimators=req.n_estimators,
            subsample=req.subsample,
            colsample_bytree=req.colsample_bytree,
            random_seed=req.random_seed,
            experiment_name=req.experiment_name,
        )
        return _serialize_experiment_detail(experiment)
    except ValueError as ve:
        logger.warning(f"XGBoost training validation error: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"XGBoost training pipeline failure: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Training failure: {str(e)}")


@router.get("/models", response_model=List[XGBoostModelSummary], summary="List Trained XGBoost Model Experiments")
def list_models(
    symbol: Optional[str] = Query(None, description="Optional symbol filter"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieves all historical XGBoost experiments with out-of-sample metrics."""
    experiments = XGBoostService.list_experiments(db=db, symbol=symbol, limit=limit)
    summaries: List[XGBoostModelSummary] = []
    for exp in experiments:
        oos = json.loads(exp.out_of_sample_metrics or "{}")
        baselines = json.loads(exp.baseline_metrics or "{}")
        summaries.append(
            XGBoostModelSummary(
                model_id=exp.model_id,
                experiment_name=exp.experiment_name,
                model_version=exp.model_version,
                symbol=exp.symbol,
                market=exp.market,
                timeframe=exp.timeframe,
                status=exp.status,
                training_row_count=exp.training_row_count,
                test_row_count=exp.test_row_count,
                out_of_sample_accuracy=oos.get("accuracy"),
                out_of_sample_f1=oos.get("f1_score"),
                baseline_majority_accuracy=baselines.get("majority_class_baseline", {}).get("accuracy"),
                baseline_momentum_accuracy=baselines.get("momentum_direction_baseline", {}).get("accuracy"),
                created_at=exp.created_at.isoformat() if exp.created_at else "",
            )
        )
    return summaries


@router.get("/models/{model_id}", response_model=XGBoostModelDetail, summary="Get Full Experiment Metrics & Feature Importance")
def get_model_detail(model_id: str, db: Session = Depends(get_db)):
    """Retrieves full evaluation metrics, confusion matrix, baseline comparison, and feature importance."""
    exp = XGBoostService.get_experiment(db=db, model_id=model_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"XGBoost model '{model_id}' not found.")
    return _serialize_experiment_detail(exp)


@router.post("/predict", response_model=XGBoostPredictionResponse, summary="Generate Advisory Next-Bar Direction Inference")
def predict_advisory(req: XGBoostPredictRequest, db: Session = Depends(get_db)):
    """Generates an advisory price direction prediction for the latest candle.
    GUARANTEE: Does NOT trigger live or paper trade executions. Strictly advisory research.
    """
    try:
        record = XGBoostService.predict_advisory(
            db=db,
            symbol=req.symbol.strip().upper(),
            timeframe=req.timeframe,
            model_id=req.model_id,
        )
        return XGBoostPredictionResponse(
            prediction_id=record.prediction_id,
            experiment_id=record.experiment_id,
            model_version=record.model_version,
            symbol=record.symbol,
            market=record.market,
            timeframe=record.timeframe,
            feature_timestamp=record.feature_timestamp,
            prediction_timestamp=record.prediction_timestamp.isoformat(),
            predicted_class=record.predicted_class,
            predicted_direction="BULLISH_UP" if record.predicted_class == 1 else ("ABSTAIN" if record.predicted_class == -1 else "BEARISH_DOWN"),
            predicted_probability=record.predicted_probability,
            bullish_probability=record.bullish_probability,
            bearish_probability=record.bearish_probability,
            features_snapshot=json.loads(record.features_snapshot or "{}"),
            data_freshness_status=record.data_freshness_status,
            advisory_only=record.advisory_only,
            outcome_status=record.outcome_status,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(fe))
    except Exception as e:
        logger.error(f"XGBoost advisory prediction failure: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Prediction error: {str(e)}")


@router.get("/predictions", response_model=List[XGBoostPredictionResponse], summary="List Advisory Prediction History")
def list_predictions(
    symbol: Optional[str] = Query(None, description="Optional symbol filter"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists historical advisory predictions and outcome verification statuses."""
    records = XGBoostService.list_predictions(db=db, symbol=symbol, limit=limit)
    res: List[XGBoostPredictionResponse] = []
    for r in records:
        res.append(
            XGBoostPredictionResponse(
                prediction_id=r.prediction_id,
                experiment_id=r.experiment_id,
                model_version=r.model_version,
                symbol=r.symbol,
                market=r.market,
                timeframe=r.timeframe,
                feature_timestamp=r.feature_timestamp,
                prediction_timestamp=r.prediction_timestamp.isoformat() if r.prediction_timestamp else "",
                predicted_class=r.predicted_class,
                predicted_direction="BULLISH_UP" if r.predicted_class == 1 else ("ABSTAIN" if r.predicted_class == -1 else "BEARISH_DOWN"),
                predicted_probability=r.predicted_probability,
                bullish_probability=r.bullish_probability,
                bearish_probability=r.bearish_probability,
                features_snapshot=json.loads(r.features_snapshot or "{}"),
                data_freshness_status=r.data_freshness_status,
                advisory_only=r.advisory_only,
                outcome_status=r.outcome_status,
            )
        )
    return res


@router.get("/jobs/{job_id}", response_model=XGBoostJobResponse, summary="Query Training Job Status")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Queries asynchronous training job progress (synchronous wrapper maps completed models)."""
    exp = XGBoostService.get_experiment(db=db, model_id=job_id)
    if exp:
        return XGBoostJobResponse(
            job_id=job_id,
            status=exp.status,
            message="Model training completed successfully.",
            model_id=exp.model_id,
        )
    return XGBoostJobResponse(
        job_id=job_id,
        status="IDLE",
        message="No background job registered with this ID.",
    )


@router.post("/synthesize", response_model=XGBoostSynthesizeResponse, summary="Synthesize Strategy Signal with XGBoost & Qwen AI")
def synthesize_analysis(req: XGBoostSynthesizeRequest, db: Session = Depends(get_db)):
    """Synthesizes deterministic strategy signals, XGBoost direction probabilities,
    and Qwen/Local LLM explanations into an auditable research report with divergence detection.
    """
    try:
        # 1. Get or generate XGBoost prediction
        pred_dict = None
        try:
            pred_record = XGBoostService.predict_advisory(
                db=db,
                symbol=req.symbol.strip().upper(),
                timeframe=req.timeframe,
                model_id=req.model_id,
            )
            pred_dict = {
                "predicted_direction": "BULLISH_UP" if pred_record.predicted_class == 1 else "BEARISH_DOWN",
                "bullish_probability": pred_record.bullish_probability,
                "bearish_probability": pred_record.bearish_probability,
                "predicted_probability": pred_record.predicted_probability,
                "model_version": pred_record.model_version,
            }
        except Exception as e:
            logger.debug(f"XGBoost prediction not available for synthesis: {e}")
            pred_dict = {
                "predicted_direction": "UNKNOWN",
                "bullish_probability": 0.5,
                "bearish_probability": 0.5,
                "predicted_probability": 0.5,
                "model_version": "None",
            }

        # 2. Synthesize using XGBoostAdvisoryExplainer (with Qwen & deterministic fallback)
        res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
            db=db,
            symbol=req.symbol.strip().upper(),
            timeframe=req.timeframe,
            rule_signal=req.rule_signal,
            xgboost_prediction=pred_dict,
        )
        return XGBoostSynthesizeResponse(**res)
    except Exception as e:
        logger.error(f"Synthesis endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def _serialize_experiment_detail(exp: XGBoostExperiment) -> XGBoostModelDetail:
    """Helper to deserialize JSON strings into typed Pydantic structure."""
    return XGBoostModelDetail(
        model_id=exp.model_id,
        experiment_name=exp.experiment_name,
        model_version=exp.model_version,
        symbol=exp.symbol,
        market=exp.market,
        timeframe=exp.timeframe,
        target_definition=exp.target_definition,
        feature_version=exp.feature_version,
        training_start_timestamp=exp.training_start_timestamp,
        training_end_timestamp=exp.training_end_timestamp,
        validation_start_timestamp=exp.validation_start_timestamp,
        validation_end_timestamp=exp.validation_end_timestamp,
        test_start_timestamp=exp.test_start_timestamp,
        test_end_timestamp=exp.test_end_timestamp,
        training_row_count=exp.training_row_count,
        validation_row_count=exp.validation_row_count,
        test_row_count=exp.test_row_count,
        class_distribution=json.loads(exp.class_distribution or "{}"),
        hyperparameters=json.loads(exp.hyperparameters or "{}"),
        random_seed=exp.random_seed,
        baseline_metrics=json.loads(exp.baseline_metrics or "{}"),
        out_of_sample_metrics=json.loads(exp.out_of_sample_metrics or "{}"),
        walk_forward_metrics=json.loads(exp.walk_forward_metrics or "[]"),
        confusion_matrix=json.loads(exp.confusion_matrix or "{}"),
        feature_importance=json.loads(exp.feature_importance or "{}"),
        calibration_metrics=json.loads(exp.calibration_metrics or "{}"),
        artifact_path=exp.artifact_path,
        artifact_checksum=exp.artifact_checksum,
        status=exp.status,
        created_at=exp.created_at.isoformat() if exp.created_at else "",
        completed_at=exp.completed_at.isoformat() if exp.completed_at else None,
    )
