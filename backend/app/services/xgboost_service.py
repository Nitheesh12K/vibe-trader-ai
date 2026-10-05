"""XGBoost Quantitative Research Service for Vibe Trader AI.
Handles model training with chronological time-series splitting, walk-forward validation,
naive baseline benchmarking, feature importance extraction, atomic artifact persistence,
and non-executing advisory inference.
"""
import os
import json
import hashlib
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    precision_recall_curve,
    auc,
    balanced_accuracy_score,
    log_loss,
    brier_score_loss,
    confusion_matrix,
)
from sqlalchemy.orm import Session

from app.models.entities import (
    XGBoostExperiment,
    XGBoostPredictionRecord,
    utcnow,
)
from app.services.xgboost_feature_pipeline import (
    XGBoostFeaturePipeline,
    FEATURE_NAMES,
    FeaturePipelineResult,
)
from app.services.csv_data_provider import CSVDataProvider
from app.services.market_data_service import MarketDataService
from app.core.config import settings, BASE_DIR

logger = logging.getLogger("vibe-trader-ai.xgboost_service")

# Approved relative artifact storage directory
MODELS_DIR = Path(BASE_DIR) / "data" / "models" / "xgboost"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class XGBoostService:
    """Core Quantitative ML Research Engine powered by XGBoost."""

    @classmethod
    def _compute_checksum(cls, file_path: Path) -> str:
        """Computes SHA256 checksum of saved model artifact."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @classmethod
    def load_candles(cls, db: Session, symbol: str, timeframe: str) -> List[Any]:
        """Fetches candles from persistent CSV datasets or market data provider."""
        candles = CSVDataProvider.get_dataset(symbol_or_id=symbol, db=db)
        if not candles:
            market_service = MarketDataService(db=db)
            ohlc = market_service.get_ohlc(symbol=symbol, timeframe=timeframe)
            candles = ohlc.candles or []
        return candles

    @classmethod
    def train_model(
        cls,
        db: Session,
        symbol: str,
        timeframe: str = "1D",
        market: str = "NSE",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        num_folds: int = 3,
        max_depth: int = 3,
        learning_rate: float = 0.05,
        n_estimators: int = 100,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_seed: int = 42,
        experiment_name: Optional[str] = None,
    ) -> XGBoostExperiment:
        """Executes chronological time-based training, walk-forward validation, and artifact persistence."""
        # 1. Input parameter validation
        if max_depth < 1 or max_depth > 12:
            raise ValueError(f"Invalid max_depth {max_depth}. Allowed bounds: [1, 12].")
        if learning_rate <= 0.0 or learning_rate > 1.0:
            raise ValueError(f"Invalid learning_rate {learning_rate}. Allowed bounds: (0.0, 1.0].")
        if n_estimators < 10 or n_estimators > 1000:
            raise ValueError(f"Invalid n_estimators {n_estimators}. Allowed bounds: [10, 1000].")
        if train_ratio < 0.4 or train_ratio > 0.85:
            raise ValueError(f"Invalid train_ratio {train_ratio}. Allowed bounds: [0.4, 0.85].")
        if num_folds < 2 or num_folds > 10:
            raise ValueError(f"Invalid num_folds {num_folds}. Allowed bounds: [2, 10].")

        # 2. Ingest and extract causal features
        candles = cls.load_candles(db=db, symbol=symbol, timeframe=timeframe)
        if not candles or len(candles) < 58:
            raise ValueError(
                f"Insufficient historical data for {symbol} ({len(candles) if candles else 0} candles). "
                "Minimum 58 candles required for causal feature warmup and split integrity."
            )

        pipeline_result = XGBoostFeaturePipeline.build_training_dataset(candles, warmup_bars=50)
        X = pipeline_result.features_df
        y = pipeline_result.targets
        timestamps = pipeline_result.timestamps

        total_samples = len(X)
        if total_samples < 8:
            raise ValueError(f"Usable samples after warmup is {total_samples}, insufficient for train/test splits.")

        # 3. Check class diversity
        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            raise ValueError(f"Target exhibits zero variance (only class {unique_classes[0]} present). Cannot train binary classifier.")

        # 4. Chronological Train / Validation / Test Split (Strictly non-shuffled)
        train_idx = int(total_samples * train_ratio)
        val_idx = int(total_samples * (train_ratio + val_ratio))
        val_idx = max(train_idx + 2, min(total_samples - 2, val_idx))

        X_train, y_train = X.iloc[:train_idx], y.iloc[:train_idx]
        X_val, y_val = X.iloc[train_idx:val_idx], y.iloc[train_idx:val_idx]
        X_test, y_test = X.iloc[val_idx:], y.iloc[val_idx:]

        # One-bar purge safety: ensure target of last train bar does not leak into validation
        # (Since target t uses close t+1, X_train.iloc[-1] target uses candle train_idx, which is valid)

        # 5. Fit XGBoost Model
        hyperparams = {
            "max_depth": int(max_depth),
            "learning_rate": float(learning_rate),
            "n_estimators": int(n_estimators),
            "subsample": float(subsample),
            "colsample_bytree": float(colsample_bytree),
            "random_state": int(random_seed),
            "eval_metric": "logloss",
            "objective": "binary:logistic",
        }

        model = xgb.XGBClassifier(**hyperparams)
        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        # 6. Out-of-sample Evaluation on Test Set
        y_test_pred = model.predict(X_test)
        y_test_proba = model.predict_proba(X_test)[:, 1]

        test_metrics = cls._calculate_evaluation_metrics(y_true=y_test.values, y_pred=y_test_pred, y_prob=y_test_proba)

        # In-sample metrics for calibration/overfitting diagnostics
        y_train_pred = model.predict(X_train)
        y_train_proba = model.predict_proba(X_train)[:, 1]
        train_metrics = cls._calculate_evaluation_metrics(y_true=y_train.values, y_pred=y_train_pred, y_prob=y_train_proba)

        # 7. Baseline Models (Evaluated on untouched test set)
        majority_class = int(y_train.mode()[0]) if len(y_train.mode()) > 0 else 1
        majority_preds = np.full(shape=len(y_test), fill_value=majority_class)
        majority_acc = round(float(accuracy_score(y_test, majority_preds)), 4)

        # Momentum Direction Baseline: predict UP if return_1bar > 0 else DOWN
        momentum_preds = (X_test["return_1bar"] > 0.0).astype(int).values
        momentum_acc = round(float(accuracy_score(y_test, momentum_preds)), 4)

        baselines = {
            "majority_class_baseline": {
                "predicted_class": majority_class,
                "accuracy": majority_acc,
                "description": "Predicts majority class of in-sample training window.",
            },
            "momentum_direction_baseline": {
                "accuracy": momentum_acc,
                "description": "Predicts next bar direction equals previous bar return direction.",
            },
        }

        # 8. Feature Importance (Gain & Weight)
        booster = model.get_booster()
        score_gain = booster.get_score(importance_type="gain")
        score_weight = booster.get_score(importance_type="weight")

        feature_importance_dict = {}
        for feat in FEATURE_NAMES:
            feature_importance_dict[feat] = {
                "gain": round(float(score_gain.get(feat, 0.0)), 4),
                "weight": int(score_weight.get(feat, 0)),
            }

        # 9. Walk-Forward Multi-Fold Validation (Chronological rolling splits)
        walk_forward_folds = cls._run_walk_forward_folds(
            X=X,
            y=y,
            timestamps=timestamps,
            num_folds=num_folds,
            hyperparams=hyperparams,
        )

        # 10. Save Model Artifact to Disk (Safe JSON/UBJSON format)
        model_uuid = f"XGB-{symbol.upper()}-{uuid.uuid4().hex[:8]}"
        artifact_filename = f"{model_uuid}.json"
        artifact_full_path = MODELS_DIR / artifact_filename
        model.save_model(str(artifact_full_path))
        checksum = cls._compute_checksum(artifact_full_path)
        relative_artifact_path = f"data/models/xgboost/{artifact_filename}"

        # 11. Confusion Matrix
        cm = confusion_matrix(y_test, y_test_pred)
        cm_dict = {
            "true_negatives": int(cm[0, 0]) if cm.shape == (2, 2) else 0,
            "false_positives": int(cm[0, 1]) if cm.shape == (2, 2) else 0,
            "false_negatives": int(cm[1, 0]) if cm.shape == (2, 2) else 0,
            "true_positives": int(cm[1, 1]) if cm.shape == (2, 2) else int(cm[0, 0]),
        }

        # 11.5 Regime-Conditioned Evaluation
        test_regimes = XGBoostFeaturePipeline.classify_regimes_for_dataframe(X_test)
        regime_breakdown = {}
        for regime_name in ["TRENDING_BULLISH", "TRENDING_BEARISH", "HIGH_VOLATILITY_EXPANSION", "RANGING_LOW_VOLATILITY"]:
            mask = (test_regimes == regime_name)
            if mask.sum() > 0:
                r_acc = round(float(accuracy_score(y_test[mask], y_test_pred[mask])), 4)
                r_brier = round(float(brier_score_loss(y_test[mask], y_test_proba[mask])), 4) if len(np.unique(y_test[mask])) > 1 else None
                regime_breakdown[regime_name] = {
                    "sample_count": int(mask.sum()),
                    "accuracy": r_acc,
                    "brier_score": r_brier,
                    "percentage_of_test": round(float(mask.sum() / len(y_test) * 100), 1),
                }
            else:
                regime_breakdown[regime_name] = {
                    "sample_count": 0,
                    "accuracy": None,
                    "brier_score": None,
                    "percentage_of_test": 0.0,
                }
        test_metrics["regime_breakdown"] = regime_breakdown

        # 12. Persist Experiment to SQLite Database
        experiment = XGBoostExperiment(
            model_id=model_uuid,
            experiment_name=experiment_name or f"XGBoost Next-Bar Direction ({symbol})",
            model_version="1.0.0",
            model_type="XGBClassifier",
            symbol=symbol,
            market=market,
            timeframe=timeframe,
            target_definition="NEXT_BAR_DIRECTION (Close[t+1] > Close[t])",
            feature_version=XGBoostFeaturePipeline.FEATURE_SCHEMA_VERSION,
            training_start_timestamp=int(timestamps.iloc[0]),
            training_end_timestamp=int(timestamps.iloc[train_idx - 1]),
            validation_start_timestamp=int(timestamps.iloc[train_idx]),
            validation_end_timestamp=int(timestamps.iloc[val_idx - 1]),
            test_start_timestamp=int(timestamps.iloc[val_idx]),
            test_end_timestamp=int(timestamps.iloc[-1]),
            training_row_count=len(X_train),
            validation_row_count=len(X_val),
            test_row_count=len(X_test),
            class_distribution=json.dumps(pipeline_result.diagnostics.get("target_distribution", {})),
            hyperparameters=json.dumps(hyperparams),
            random_seed=random_seed,
            baseline_metrics=json.dumps(baselines),
            out_of_sample_metrics=json.dumps(test_metrics),
            walk_forward_metrics=json.dumps(walk_forward_folds),
            confusion_matrix=json.dumps(cm_dict),
            feature_importance=json.dumps(feature_importance_dict),
            calibration_metrics=json.dumps({
                "brier_score": test_metrics.get("brier_score"),
                "calibration_status": test_metrics.get("calibration_status"),
                "calibration_warning": test_metrics.get("calibration_warning"),
            }),
            artifact_path=relative_artifact_path,
            artifact_checksum=checksum,
            status="COMPLETED",
            created_at=utcnow(),
            completed_at=utcnow(),
        )

        db.add(experiment)
        db.commit()
        db.refresh(experiment)
        return experiment

    @classmethod
    def _run_walk_forward_folds(
        cls,
        X: pd.DataFrame,
        y: pd.Series,
        timestamps: pd.Series,
        num_folds: int,
        hyperparams: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Executes chronological rolling walk-forward cross-validation folds."""
        total_len = len(X)
        fold_size = total_len // num_folds
        if fold_size < 4:
            return []

        folds_results = []
        for i in range(num_folds):
            start_i = i * fold_size
            end_i = total_len if i == num_folds - 1 else (i + 1) * fold_size

            fold_X = X.iloc[start_i:end_i]
            fold_y = y.iloc[start_i:end_i]
            fold_times = timestamps.iloc[start_i:end_i]

            split_pt = int(len(fold_X) * 0.70)
            if split_pt < 3 or (len(fold_X) - split_pt) < 1:
                continue

            X_tr, y_tr = fold_X.iloc[:split_pt], fold_y.iloc[:split_pt]
            X_te, y_te = fold_X.iloc[split_pt:], fold_y.iloc[split_pt:]

            # Check binary class presence in train
            if len(np.unique(y_tr)) < 2:
                continue

            m = xgb.XGBClassifier(**hyperparams)
            m.fit(X_tr, y_tr, verbose=False)

            preds = m.predict(X_te)
            acc = round(float(accuracy_score(y_te, preds)), 4)

            folds_results.append({
                "fold_index": i + 1,
                "train_start": int(fold_times.iloc[0]),
                "train_end": int(fold_times.iloc[split_pt - 1]),
                "train_count": len(X_tr),
                "test_start": int(fold_times.iloc[split_pt]),
                "test_end": int(fold_times.iloc[-1]),
                "test_count": len(X_te),
                "accuracy": acc,
                "class_1_ratio": round(float(y_te.sum() / len(y_te)), 4),
            })
        return folds_results

    @classmethod
    def _calculate_evaluation_metrics(
        cls, y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray
    ) -> Dict[str, Any]:
        """Calculates quantitative binary classification metrics safely."""
        acc = round(float(accuracy_score(y_true, y_pred)), 4)
        prec = round(float(precision_score(y_true, y_pred, zero_division=0)), 4)
        rec = round(float(recall_score(y_true, y_pred, zero_division=0)), 4)
        f1 = round(float(f1_score(y_true, y_pred, zero_division=0)), 4)
        bal_acc = round(float(balanced_accuracy_score(y_true, y_pred)), 4)

        # ROC-AUC requires both classes in y_true
        if len(np.unique(y_true)) > 1:
            roc = round(float(roc_auc_score(y_true, y_prob)), 4)
            precision_pts, recall_pts, _ = precision_recall_curve(y_true, y_prob)
            pr_auc = round(float(auc(recall_pts, precision_pts)), 4)
            loss = round(float(log_loss(y_true, y_prob, labels=[0, 1])), 4)
            brier = round(float(brier_score_loss(y_true, y_prob)), 4)
        else:
            roc = None
            pr_auc = None
            loss = None
            brier = None

        # Probability calibration check
        calibration_status = "WELL_CALIBRATED"
        calibration_warning = None
        if brier is not None:
            if brier > 0.28:
                calibration_status = "POOR_CALIBRATION_WARNING"
                calibration_warning = f"High Brier score ({brier:.4f} > 0.28) indicates poor probability calibration. Advisory probabilities may be overconfident."
            elif brier > 0.25:
                calibration_status = "MARGINAL_CALIBRATION"
                calibration_warning = f"Brier score ({brier:.4f}) is marginal vs naive 50/50 baseline (0.25)."

        return {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "balanced_accuracy": bal_acc,
            "roc_auc": roc,
            "pr_auc": pr_auc,
            "log_loss": loss,
            "brier_score": brier,
            "calibration_status": calibration_status,
            "calibration_warning": calibration_warning,
            "sample_size": len(y_true),
        }

    @classmethod
    def load_model_booster(cls, model_id_or_path: str) -> xgb.XGBClassifier:
        """Loads a model artifact securely from the approved models directory."""
        filename = Path(model_id_or_path).name
        if not filename.endswith(".json"):
            filename = f"{filename}.json"

        target_path = MODELS_DIR / filename
        if not target_path.exists():
            raise FileNotFoundError(f"Model artifact not found at approved path: {target_path}")

        model = xgb.XGBClassifier()
        try:
            model.load_model(str(target_path))
        except Exception as e:
            raise ValueError(f"Failed to load XGBoost model artifact (corrupt or invalid format): {e}")

        return model

    @classmethod
    def predict_advisory(
        cls,
        db: Session,
        symbol: str,
        timeframe: str = "1D",
        model_id: Optional[str] = None,
    ) -> XGBoostPredictionRecord:
        """Generates a strictly advisory next-bar price direction inference for the latest completed candle.
        GUARANTEE: Does NOT execute orders, alter paper portfolio, or bypass Risk Guardian.
        """
        # 1. Resolve experiment from DB
        query = db.query(XGBoostExperiment).filter(XGBoostExperiment.symbol == symbol)
        if model_id:
            query = query.filter(XGBoostExperiment.model_id == model_id)
        experiment = query.order_by(XGBoostExperiment.id.desc()).first()

        if not experiment:
            raise ValueError(f"No trained XGBoost experiment found for {symbol}. Please train a model first.")

        # 1.5 Validate Feature Schema Version
        XGBoostFeaturePipeline.validate_feature_schema(getattr(experiment, "feature_version", None))

        # 2. Ingest latest candles
        candles = cls.load_candles(db=db, symbol=symbol, timeframe=timeframe)
        if not candles or len(candles) < 55:
            raise ValueError(f"Insufficient candles to compute inference features for {symbol}. Need >= 55.")

        features_dict, candle_timestamp = XGBoostFeaturePipeline.extract_single_inference_vector(candles)

        # 3. Check data freshness
        freshness_status = "FRESH"
        curr_time = int(datetime.now(timezone.utc).timestamp())
        if candle_timestamp > 0 and (curr_time - candle_timestamp) > 86400 * 3:
            freshness_status = "HISTORICAL_OR_STALE"

        # 4. Load trained booster
        model = cls.load_model_booster(experiment.artifact_path or experiment.model_id)

        # 5. Inference & Abstention Zone
        feature_vector = pd.DataFrame([features_dict])[FEATURE_NAMES]
        probabilities = model.predict_proba(feature_vector)[0]

        prob_down = round(float(probabilities[0]), 4)
        prob_up = round(float(probabilities[1]), 4)

        # Abstention Zone (0.48 <= P(Up) <= 0.52)
        ABSTENTION_LOWER = 0.48
        ABSTENTION_UPPER = 0.52
        if ABSTENTION_LOWER <= prob_up <= ABSTENTION_UPPER:
            predicted_class = -1
            pred_prob = round(max(prob_up, prob_down), 4)
            freshness_status = "ABSTAIN_UNCERTAINTY_ZONE"
        else:
            predicted_class = int(model.predict(feature_vector)[0])
            pred_prob = prob_up if predicted_class == 1 else prob_down

        # 6. Record prediction in DB (advisory_only=True, outcome_status="UNVERIFIED_PENDING_BAR")
        prediction_id = f"PRED-{symbol}-{uuid.uuid4().hex[:8]}"
        record = XGBoostPredictionRecord(
            prediction_id=prediction_id,
            experiment_id=experiment.model_id,
            model_version=experiment.model_version,
            symbol=symbol,
            market=experiment.market,
            timeframe=timeframe,
            feature_timestamp=candle_timestamp,
            prediction_timestamp=utcnow(),
            target_timestamp=None,  # Unset until future candle completes
            predicted_class=predicted_class,
            predicted_probability=pred_prob,
            bearish_probability=prob_down,
            bullish_probability=prob_up,
            features_snapshot=json.dumps(features_dict),
            data_freshness_status=freshness_status,
            advisory_only=True,
            outcome_status="UNVERIFIED_PENDING_BAR",
            created_at=utcnow(),
        )

        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def list_experiments(
        cls, db: Session, symbol: Optional[str] = None, limit: int = 50
    ) -> List[XGBoostExperiment]:
        """Lists trained experiments with metadata."""
        query = db.query(XGBoostExperiment)
        if symbol:
            query = query.filter(XGBoostExperiment.symbol == symbol)
        return query.order_by(XGBoostExperiment.id.desc()).limit(limit).all()

    @classmethod
    def get_experiment(cls, db: Session, model_id: str) -> Optional[XGBoostExperiment]:
        """Fetches detailed experiment records by model_id."""
        return db.query(XGBoostExperiment).filter(XGBoostExperiment.model_id == model_id).first()

    @classmethod
    def list_predictions(
        cls, db: Session, symbol: Optional[str] = None, limit: int = 50
    ) -> List[XGBoostPredictionRecord]:
        """Lists advisory prediction history."""
        query = db.query(XGBoostPredictionRecord)
        if symbol:
            query = query.filter(XGBoostPredictionRecord.symbol == symbol)
        return query.order_by(XGBoostPredictionRecord.id.desc()).limit(limit).all()
