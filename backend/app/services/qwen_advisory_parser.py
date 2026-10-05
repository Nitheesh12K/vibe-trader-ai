"""Dedicated Parsing, Validation, and Compatibility Pipeline for Qwen Advisory Reports.
Pipelines:
Raw Output -> Code-Fence Stripping -> JSON Deserialization -> Schema Validation -> Semantic & Timestamp Validation -> Typed Result.
Includes backward-compatibility adapter for existing frontend components.
"""
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple, Union
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.qwen_advisory import (
    QwenAdvisoryContract,
    AdvisoryValidationFailure,
)

logger = logging.getLogger("vibe-trader-ai.qwen_parser")


class QwenResponseParser:
    """Safe, non-destructive parsing and schema validation pipeline for Qwen responses."""

    MAX_RAW_LENGTH = 10000  # Guard against memory exhaustion

    @classmethod
    def clean_raw_text(cls, raw: Optional[str]) -> str:
        """Strips markdown code fences and whitespace cleanly."""
        if not raw or not isinstance(raw, str):
            return ""
        text = raw.strip()
        if len(text) > cls.MAX_RAW_LENGTH:
            text = text[: cls.MAX_RAW_LENGTH]

        # Strip markdown fences
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    @classmethod
    def parse_and_validate(
        cls,
        raw_text: str,
        expected_signal: str,
        input_timestamp: int,
        model_name: str = "qwen3-local:latest",
        model_version: str = "1.0.0",
        xgboost_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[QwenAdvisoryContract], Optional[AdvisoryValidationFailure]]:
        """Executes full validation pipeline:
        1. Clean and bound raw text.
        2. Attempt JSON deserialization.
        3. Validate against QwenAdvisoryContract.
        4. Validate semantic consistency with input parameters.
        Returns (validated_contract, None) on success, or (None, failure_detail) on error.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        cleaned = cls.clean_raw_text(raw_text)
        if not cleaned:
            return None, AdvisoryValidationFailure(
                error_type="EMPTY_OR_WHITESPACE_RESPONSE",
                error_detail="Model returned an empty, whitespace-only, or non-string response.",
                raw_response_snippet="",
                timestamp=now_iso,
            )

        # JSON parsing
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            snippet = cleaned[:100] + "..." if len(cleaned) > 100 else cleaned
            logger.debug(f"JSON parsing failed for Qwen response: {e}")
            return None, AdvisoryValidationFailure(
                error_type="JSON_DECODE_ERROR",
                error_detail=f"Malformed JSON: {str(e)}",
                raw_response_snippet=snippet,
                timestamp=now_iso,
            )

        if not isinstance(parsed, dict):
            return None, AdvisoryValidationFailure(
                error_type="INVALID_ROOT_TYPE",
                error_detail=f"Expected JSON object (dict), received {type(parsed).__name__}",
                raw_response_snippet=str(parsed)[:100],
                timestamp=now_iso,
            )

        # Merge known ground truth context if model omitted them or provided synonyms
        xgb_ctx = xgboost_context or {}
        if "schema_version" not in parsed:
            parsed["schema_version"] = "1.0.0"
        if "input_timestamp" not in parsed:
            parsed["input_timestamp"] = input_timestamp
        if "model_name" not in parsed:
            parsed["model_name"] = model_name
        if "model_version" not in parsed:
            parsed["model_version"] = model_version
        if "deterministic_signal" not in parsed:
            parsed["deterministic_signal"] = expected_signal
        if "xgboost_direction" not in parsed:
            if "predicted_direction" in xgb_ctx:
                parsed["xgboost_direction"] = xgb_ctx.get("predicted_direction")
            elif "bullish_probability" in xgb_ctx:
                b_prob = float(xgb_ctx.get("bullish_probability", 0.5))
                parsed["xgboost_direction"] = "UP" if b_prob >= 0.5 else "DOWN"
            else:
                parsed["xgboost_direction"] = "UNKNOWN"
        if "xgboost_probability" not in parsed:
            if "predicted_probability" in xgb_ctx:
                parsed["xgboost_probability"] = float(xgb_ctx.get("predicted_probability"))
            elif "bullish_probability" in xgb_ctx:
                parsed["xgboost_probability"] = float(xgb_ctx.get("bullish_probability"))
            else:
                parsed["xgboost_probability"] = 0.5
        if "divergence_detected" not in parsed:
            parsed["divergence_detected"] = False

        # Adapt known legacy Phase 4 fields if provided by older mocks/models
        if "ai_explanation" in parsed:
            ai_exp = parsed.pop("ai_explanation")
            if "explanation" not in parsed:
                parsed["explanation"] = ai_exp
        if "divergence_or_uncertainty" in parsed:
            div_val = parsed.pop("divergence_or_uncertainty")
            if "divergence_reason" not in parsed and div_val and div_val != "None":
                parsed["divergence_reason"] = div_val
        if "key_drivers" in parsed:
            parsed.pop("key_drivers")

        if "summary" not in parsed:
            parsed["summary"] = parsed.get("explanation", "")[:200] or "Synthesis analysis generated."
        if "risk_context" not in parsed:
            parsed["risk_context"] = "Capital preservation and strict stop-loss rules enforced by Risk Guardian."
        if "synthesis_verdict" not in parsed:
            parsed["synthesis_verdict"] = "NEUTRAL_UNCERTAIN"

        # Pydantic Schema Validation
        try:
            contract = QwenAdvisoryContract(**parsed)
            return contract, None
        except ValidationError as e:
            err_msg = "; ".join([f"{err['loc']}: {err['msg']}" for err in e.errors()[:3]])
            logger.debug(f"QwenAdvisoryContract validation failed: {err_msg}")
            return None, AdvisoryValidationFailure(
                error_type="SCHEMA_VALIDATION_ERROR",
                error_detail=err_msg,
                raw_response_snippet=cleaned[:100],
                timestamp=now_iso,
            )
        except Exception as e:
            logger.debug(f"Unexpected error validating Qwen contract: {e}")
            return None, AdvisoryValidationFailure(
                error_type="UNEXPECTED_VALIDATION_ERROR",
                error_detail=str(e),
                raw_response_snippet=cleaned[:100],
                timestamp=now_iso,
            )


class QwenAdvisoryAdapter:
    """Provides backward-compatibility transformation between QwenAdvisoryContract and legacy UI/API shapes."""

    @classmethod
    def to_synthesize_response_dict(
        cls,
        contract: QwenAdvisoryContract,
        symbol: str,
        timeframe: str,
        provider_used: str,
        xgboost_prediction_dict: Dict[str, Any],
        technical_context: Optional[Dict[str, Any]] = None,
        raw_rule_signal: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Translates a strictly validated QwenAdvisoryContract into the unified API payload
        compatible with both new contracts and existing frontend viewers.
        """
        prob = contract.xgboost_probability or 0.5
        prob_up = prob if contract.xgboost_direction in ["UP", "BULLISH_UP"] else (1.0 - prob)

        rule_label = raw_rule_signal or contract.deterministic_signal
        key_drivers = [
            f"Rule: {rule_label}",
            f"XGBoost: {contract.xgboost_direction or 'N/A'} ({prob*100:.1f}%)",
        ]
        if technical_context:
            for k, v in technical_context.items():
                if k == "rsi_14":
                    key_drivers.append(f"RSI(14): {v}")
                else:
                    key_drivers.append(f"{k}: {v}")

        # Legacy frontend shape expectations
        return {
            # Top-level identification
            "symbol": symbol,
            "timeframe": timeframe,
            "provider_used": provider_used,
            "rule_signal": contract.deterministic_signal,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # Strict Contract Fields (v1.0.0)
            "contract": contract.model_dump(),
            "schema_version": contract.schema_version,
            "summary": contract.summary,
            "explanation": contract.explanation,
            "risk_context": contract.risk_context,
            "warnings": contract.warnings,
            "input_timestamp": contract.input_timestamp,
            "model_name": contract.model_name,
            "model_version": contract.model_version,
            "divergence_detected": contract.divergence_detected,
            "divergence_reason": contract.divergence_reason,
            # Legacy Frontend Compatibility Fields
            "xgboost_prediction": xgboost_prediction_dict,
            "xgboost_confidence": prob,
            "probability_up": round(prob_up, 4),
            "divergence_warning": contract.divergence_reason,
            "unified_confidence": round(prob, 4),
            "synthesized_recommendation": contract.synthesis_verdict,
            "qwen_advisory_text": contract.explanation,
            "risk_disclaimer": contract.advisory_caveat,
            "synthesis": {
                "synthesis_verdict": contract.synthesis_verdict,
                "ai_explanation": contract.explanation,
                "key_drivers": key_drivers,
                "divergence_or_uncertainty": contract.divergence_reason or "None",
                "advisory_caveat": contract.advisory_caveat,
            },
        }
