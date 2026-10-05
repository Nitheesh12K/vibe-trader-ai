"""Strict, Versioned Pydantic Schema Contract for Qwen / Local LLM Advisory Reports.
Enforces non-executable text, finite probabilities, enum consistency, and extra-field rejection.
"""
import math
import re
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# Disallowed code / prompt injection patterns
DANGEROUS_PATTERNS = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"\beval\s*\(", re.IGNORECASE),
    re.compile(r"\bexec\s*\(", re.IGNORECASE),
    re.compile(r"\bos\.system\s*\(", re.IGNORECASE),
    re.compile(r"\bsubprocess\.", re.IGNORECASE),
    re.compile(r"\b__import__\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE),
]

ALLOWED_SIGNALS = {
    "BUY",
    "SELL",
    "HOLD",
    "BUY_CANDIDATE",
    "SELL_CANDIDATE",
    "NO_TRADE",
    "INVALID_DATA",
    "STRATEGY_BUY",
    "STRATEGY_SELL",
    "STRATEGY_HOLD",
}

ALLOWED_XGB_DIRECTIONS = {
    "BULLISH_UP",
    "BEARISH_DOWN",
    "UP",
    "DOWN",
    "UNKNOWN",
    "ABSTAIN",
}

ALLOWED_VERDICTS = {
    "CONFLUENT_BULLISH",
    "CONFLUENT_BEARISH",
    "DIVERGENT",
    "NEUTRAL_UNCERTAIN",
}


def sanitize_and_check_text(value: str, field_name: str) -> str:
    """Ensures text does not contain executable code or instruction injection attempts."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(value):
            raise ValueError(f"Dangerous code or injection pattern detected in {field_name}")
    return value.strip()


class QwenAdvisoryContract(BaseModel):
    """Version 1.0.0 strict contract for Qwen / Local LLM Advisory Explanation Output.
    Strictly advisory: does NOT authorize live or paper trading orders.
    """
    schema_version: Literal["1.0.0"] = Field(
        "1.0.0",
        description="Semantic version of the advisory contract.",
    )
    summary: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Concise high-level synthesis of signals.",
    )
    deterministic_signal: str = Field(
        ...,
        description="Underlying deterministic strategy proposal.",
    )
    xgboost_direction: Optional[str] = Field(
        None,
        description="Machine learning forecast direction.",
    )
    xgboost_probability: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Calibrated or raw probability estimate in [0.0, 1.0]. None if unavailable.",
    )
    probability_calibrated: bool = Field(
        False,
        description="Whether probability score has been empirically calibrated on holdout sets.",
    )
    divergence_detected: bool = Field(
        False,
        description="True if deterministic signal and XGBoost forecast contradict.",
    )
    divergence_reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Explanation of statistical or directional divergence.",
    )
    synthesis_verdict: str = Field(
        ...,
        description="Synthesized classification verdict.",
    )
    explanation: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Factual, grounded rationale referencing only verified indicators.",
    )
    risk_context: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Risk boundaries and stop-loss / invalidation context.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Active market anomaly, stale data, or execution warnings.",
    )
    input_timestamp: int = Field(
        ...,
        description="Unix timestamp (seconds) of the market candle or inference context evaluated.",
    )
    model_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Name of the model generating the explanation (e.g. qwen3-local, deterministic-fallback).",
    )
    model_version: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Version string of the model or fallback engine.",
    )
    advisory_caveat: str = Field(
        "XGBoost forecasts and AI explanations are strictly advisory research. Zero real-money trades are executed.",
        max_length=500,
        description="Mandatory legal and safety disclaimer.",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    @field_validator("summary", "explanation", "risk_context", "advisory_caveat")
    @classmethod
    def validate_text_safety(cls, v: str, info) -> str:
        return sanitize_and_check_text(v, info.field_name)

    @field_validator("deterministic_signal")
    @classmethod
    def validate_deterministic_signal(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if v_clean not in ALLOWED_SIGNALS:
            raise ValueError(f"Invalid deterministic signal '{v}'. Must be one of {sorted(ALLOWED_SIGNALS)}")
        return v_clean

    @field_validator("xgboost_direction")
    @classmethod
    def validate_xgboost_direction(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_clean = v.strip().upper()
        if v_clean not in ALLOWED_XGB_DIRECTIONS:
            raise ValueError(f"Invalid XGBoost direction '{v}'. Must be one of {sorted(ALLOWED_XGB_DIRECTIONS)}")
        return v_clean

    @field_validator("synthesis_verdict")
    @classmethod
    def validate_synthesis_verdict(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if v_clean not in ALLOWED_VERDICTS:
            raise ValueError(f"Invalid synthesis verdict '{v}'. Must be one of {sorted(ALLOWED_VERDICTS)}")
        return v_clean

    @field_validator("xgboost_probability")
    @classmethod
    def validate_finite_probability(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if math.isnan(v) or math.isinf(v):
            raise ValueError("xgboost_probability cannot be NaN or Infinite")
        if v < 0.0 or v > 1.0:
            raise ValueError("xgboost_probability must be bounded between 0.0 and 1.0")
        return round(float(v), 4)

    @field_validator("input_timestamp")
    @classmethod
    def validate_timestamp_range(cls, v: int) -> int:
        if v < 946684800:  # Jan 1, 2000
            raise ValueError("input_timestamp is unreasonably old or invalid")
        # Allow up to 1 day into future for timezone skew, but reject distant future
        import time
        now_ts = int(time.time())
        if v > now_ts + 86400 * 2:
            raise ValueError("input_timestamp cannot be in the distant future")
        return v

    @field_validator("warnings")
    @classmethod
    def validate_warnings_elements(cls, v: List[str]) -> List[str]:
        return [sanitize_and_check_text(item, "warnings") for item in v if item]

    @model_validator(mode="after")
    def validate_semantic_coherence(self):
        """Cross-field consistency check."""
        if self.divergence_detected and not self.divergence_reason:
            self.divergence_reason = "Divergence detected between strategy rule and machine learning forecast."
        return self


class AdvisoryValidationFailure(BaseModel):
    """Typed record of a schema validation or parsing failure."""
    is_valid: bool = False
    error_type: str
    error_detail: str
    raw_response_snippet: Optional[str] = None
    fallback_activated: bool = True
    timestamp: str
