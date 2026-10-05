"""Pydantic schemas for XGBoost Machine Learning Research and Advisory Inference."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class XGBoostTrainRequest(BaseModel):
    symbol: str = Field("RELIANCE", description="Symbol to train on (e.g., RELIANCE, TATASTEEL, NIFTY 50)")
    market: str = Field("NSE", description="Market identifier")
    timeframe: str = Field("1D", description="Timeframe")
    train_ratio: float = Field(0.70, ge=0.4, le=0.85, description="Proportion of data for training")
    val_ratio: float = Field(0.15, ge=0.05, le=0.3, description="Proportion of data for validation")
    num_folds: int = Field(3, ge=2, le=10, description="Chronological walk-forward folds count")
    max_depth: int = Field(3, ge=1, le=12, description="Maximum tree depth for XGBoost")
    learning_rate: float = Field(0.05, gt=0.0, le=1.0, description="Boosting learning rate / eta")
    n_estimators: int = Field(100, ge=10, le=1000, description="Number of boosting rounds")
    subsample: float = Field(0.8, gt=0.0, le=1.0, description="Subsample ratio of training instances")
    colsample_bytree: float = Field(0.8, gt=0.0, le=1.0, description="Subsample ratio of columns per tree")
    random_seed: int = Field(42, description="Random seed for reproducibility")
    experiment_name: Optional[str] = Field(None, max_length=100, description="Custom label for experiment")


class BaselineComparison(BaseModel):
    majority_class_accuracy: float
    momentum_direction_accuracy: float
    xgboost_out_of_sample_accuracy: float
    accuracy_delta_vs_majority: float
    accuracy_delta_vs_momentum: float


class XGBoostModelSummary(BaseModel):
    model_id: str
    experiment_name: str
    model_version: str
    symbol: str
    market: str
    timeframe: str
    status: str
    training_row_count: int
    test_row_count: int
    out_of_sample_accuracy: Optional[float] = None
    out_of_sample_f1: Optional[float] = None
    baseline_majority_accuracy: Optional[float] = None
    baseline_momentum_accuracy: Optional[float] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class XGBoostModelDetail(BaseModel):
    model_id: str
    experiment_name: str
    model_version: str
    symbol: str
    market: str
    timeframe: str
    target_definition: str
    feature_version: str
    training_start_timestamp: Optional[int] = None
    training_end_timestamp: Optional[int] = None
    validation_start_timestamp: Optional[int] = None
    validation_end_timestamp: Optional[int] = None
    test_start_timestamp: Optional[int] = None
    test_end_timestamp: Optional[int] = None
    training_row_count: int
    validation_row_count: int
    test_row_count: int
    class_distribution: Dict[str, Any] = {}
    hyperparameters: Dict[str, Any] = {}
    random_seed: int
    baseline_metrics: Dict[str, Any] = {}
    out_of_sample_metrics: Dict[str, Any] = {}
    walk_forward_metrics: List[Dict[str, Any]] = []
    confusion_matrix: Dict[str, Any] = {}
    feature_importance: Dict[str, Any] = {}
    calibration_metrics: Dict[str, Any] = {}
    artifact_path: Optional[str] = None
    artifact_checksum: Optional[str] = None
    status: str
    created_at: str
    completed_at: Optional[str] = None


class XGBoostPredictRequest(BaseModel):
    symbol: str = Field("RELIANCE", description="Symbol to predict")
    timeframe: str = Field("1D", description="Timeframe")
    model_id: Optional[str] = Field(None, description="Optional specific model ID (defaults to latest)")


class XGBoostPredictionResponse(BaseModel):
    prediction_id: str
    experiment_id: str
    model_version: str
    symbol: str
    market: str
    timeframe: str
    feature_timestamp: int
    prediction_timestamp: str
    predicted_class: int  # 1 = Bullish/Up, 0 = Bearish/Down
    predicted_direction: str  # "BULLISH_UP" or "BEARISH_DOWN"
    predicted_probability: float
    bullish_probability: float
    bearish_probability: float
    features_snapshot: Dict[str, float] = {}
    data_freshness_status: str
    advisory_only: bool = True
    outcome_status: str
    disclaimer: str = (
        "RESEARCH ADVISORY ONLY — NOT A TRADE INSTRUCTION. "
        "Next-bar probability does not guarantee live execution success or future profitability."
    )


class XGBoostJobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    model_id: Optional[str] = None


class XGBoostSynthesizeRequest(BaseModel):
    symbol: str = Field("RELIANCE", description="Symbol to synthesize")
    timeframe: str = Field("1D", description="Timeframe")
    rule_signal: str = Field("HOLD", description="Optional rule-based signal (e.g. BUY_CANDIDATE, HOLD)")
    model_id: Optional[str] = Field(None, description="Optional specific model ID")


class XGBoostSynthesizeResponse(BaseModel):
    symbol: str
    timeframe: str
    provider_used: str
    rule_signal: str
    xgboost_prediction: Dict[str, Any]
    synthesis: Dict[str, Any]
    divergence_detected: bool
    timestamp: str

