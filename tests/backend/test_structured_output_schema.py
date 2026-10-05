"""Task 1.5: Structured-Output Schema & Parser Validation Test Suite.
Verifies:
1. Valid structured Qwen advisory response adheres strictly to schema.
2. Optional fields handled and defaulted properly.
3. Invalid JSON cleanly caught with typed failure.
4. Truncated JSON safely handled without crash.
5. Markdown code-fence stripped and successfully deserialized.
6. Missing required fields caught and typed.
7. Wrong field types caught and rejected.
8. Invalid direction rejected.
9. Probability bounds enforcement (reject < 0.0 or > 1.0).
10. NaN and Infinity explicitly rejected.
11. Stale or future timestamps rejected.
12. Unknown schema version rejected.
13. Unexpected fields rejected (extra="forbid").
14. Oversized response bounded.
15. Malicious instruction injection text rejected.
16. Deterministic fallback activated safely upon validation failure.
"""
import sys
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, init_db
from app.schemas.qwen_advisory import QwenAdvisoryContract, AdvisoryValidationFailure
from app.services.qwen_advisory_parser import QwenResponseParser, QwenAdvisoryAdapter
from app.services.xgboost_advisory_explainer import XGBoostAdvisoryExplainer


@pytest.fixture
def db_session():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_sample_valid_dict():
    return {
        "schema_version": "1.0.0",
        "summary": "Confluent bullish continuation signaled by EMA crossover and XGBoost 68% probability.",
        "deterministic_signal": "BUY",
        "xgboost_direction": "BULLISH_UP",
        "xgboost_probability": 0.68,
        "probability_calibrated": True,
        "divergence_detected": False,
        "divergence_reason": None,
        "synthesis_verdict": "CONFLUENT_BULLISH",
        "explanation": "The 9-EMA remains above the 21-EMA while the next-bar probability indicates upward continuation.",
        "risk_context": "Invalidation stop-loss below nearest swing low at 2,450 INR.",
        "warnings": [],
        "input_timestamp": int(time.time()),
        "model_name": "qwen3-local:latest",
        "model_version": "1.0.0",
        "advisory_caveat": "XGBoost outputs and AI explanations are strictly advisory research. Zero real-money trades are executed.",
    }


def test_valid_structured_response():
    """Verify that a compliant JSON payload parses into a valid QwenAdvisoryContract."""
    data = get_sample_valid_dict()
    contract = QwenAdvisoryContract(**data)
    assert contract.schema_version == "1.0.0"
    assert contract.deterministic_signal == "BUY"
    assert contract.xgboost_probability == 0.68
    assert contract.divergence_detected is False


def test_valid_response_with_optional_fields_omitted():
    """Verify that omitting optional fields (e.g. divergence_reason, warnings) succeeds."""
    data = get_sample_valid_dict()
    data.pop("divergence_reason")
    data.pop("warnings")
    contract = QwenAdvisoryContract(**data)
    assert contract.warnings == []
    assert contract.divergence_reason is None


def test_invalid_json_handling():
    """Verify malformed JSON returns a typed validation failure."""
    raw = "{ 'summary': 'bad json with single quotes and no closing brace' "
    contract, failure = QwenResponseParser.parse_and_validate(
        raw_text=raw,
        expected_signal="BUY",
        input_timestamp=int(time.time()),
    )
    assert contract is None
    assert failure is not None
    assert failure.error_type == "JSON_DECODE_ERROR"
    assert "Malformed JSON" in failure.error_detail


def test_truncated_json_handling():
    """Verify truncated JSON returns failure without unhandled exception."""
    raw = '{"schema_version": "1.0.0", "summary": "Truncated mid-sentence and not closed'
    contract, failure = QwenResponseParser.parse_and_validate(
        raw_text=raw,
        expected_signal="BUY",
        input_timestamp=int(time.time()),
    )
    assert contract is None
    assert failure is not None
    assert failure.error_type == "JSON_DECODE_ERROR"


def test_markdown_wrapped_json():
    """Verify that markdown fences around JSON are stripped and parsed cleanly."""
    data = get_sample_valid_dict()
    raw = f"```json\n{json.dumps(data, indent=2)}\n```"
    contract, failure = QwenResponseParser.parse_and_validate(
        raw_text=raw,
        expected_signal="BUY",
        input_timestamp=data["input_timestamp"],
    )
    assert failure is None
    assert contract is not None
    assert contract.synthesis_verdict == "CONFLUENT_BULLISH"


def test_missing_required_fields():
    """Verify missing required fields (e.g. risk_context) fails validation."""
    data = get_sample_valid_dict()
    data.pop("risk_context")
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)


def test_wrong_field_types():
    """Verify passing an integer where string is required fails validation."""
    data = get_sample_valid_dict()
    data["summary"] = 12345  # should be string
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)


def test_invalid_direction():
    """Verify invalid direction label is rejected."""
    data = get_sample_valid_dict()
    data["xgboost_direction"] = "MOON_MISSION"
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)


def test_probability_out_of_bounds():
    """Verify probability < 0.0 or > 1.0 is rejected."""
    data = get_sample_valid_dict()
    data["xgboost_probability"] = 1.25
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)

    data["xgboost_probability"] = -0.10
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)


def test_nan_and_infinity_rejection():
    """Verify NaN and Inf are rejected."""
    data = get_sample_valid_dict()
    data["xgboost_probability"] = float("nan")
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)

    data["xgboost_probability"] = float("inf")
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)


def test_invalid_or_stale_timestamp():
    """Verify timestamps prior to 2000 or in the distant future are rejected."""
    data = get_sample_valid_dict()
    data["input_timestamp"] = 100  # epoch 1970
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)

    data["input_timestamp"] = 3000000000  # far future
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)


def test_unknown_schema_version():
    """Verify non-supported schema version string is rejected."""
    data = get_sample_valid_dict()
    data["schema_version"] = "99.0.0"
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)


def test_unexpected_fields_rejected():
    """Verify extra fields are strictly forbidden by schema configuration."""
    data = get_sample_valid_dict()
    data["secret_backdoor_field"] = "malicious_payload"
    with pytest.raises(Exception):
        QwenAdvisoryContract(**data)


def test_oversized_response_bounded():
    """Verify extremely large text inputs are safely truncated to protect memory."""
    giant_text = "A" * 20000
    cleaned = QwenResponseParser.clean_raw_text(giant_text)
    assert len(cleaned) <= QwenResponseParser.MAX_RAW_LENGTH


def test_malicious_instruction_like_text_in_explanation():
    """Verify prompt injection and code execution patterns in text fields are rejected."""
    data = get_sample_valid_dict()
    data["explanation"] = "Wait for pullback. <script>alert('pwned')</script>"
    with pytest.raises(Exception) as exc_info:
        QwenAdvisoryContract(**data)
    assert "injection pattern detected" in str(exc_info.value).lower()

    data["explanation"] = "Evaluate setup. os.system('rm -rf /')"
    with pytest.raises(Exception) as exc_info:
        QwenAdvisoryContract(**data)
    assert "injection pattern detected" in str(exc_info.value).lower()


def test_deterministic_fallback_after_schema_validation_failure(db_session):
    """Verify that when Qwen returns an invalid schema, the explainer invokes the deterministic fallback."""
    with patch("httpx.Client.post") as mock_post, patch("app.services.ai_provider.OllamaProvider.check_health") as mock_health:
        mock_health.return_value = {"status": "ONLINE", "available_models": ["qwen3-local:latest"]}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Return invalid payload (missing mandatory keys)
        mock_resp.json.return_value = {"response": '{"broken": "output"}'}
        mock_post.return_value = mock_resp

        res = XGBoostAdvisoryExplainer.synthesize_advisory_analysis(
            db=db_session,
            symbol="TCS",
            timeframe="1D",
            rule_signal="BUY",
            xgboost_prediction={"predicted_direction": "UP", "predicted_probability": 0.60},
        )
        assert res["provider_used"] == "DETERMINISTIC_FALLBACK"
        assert res["contract"]["model_name"] == "deterministic-fallback-analyzer"
        assert res["schema_version"] == "1.0.0"
        assert res["synthesis"]["synthesis_verdict"] == "CONFLUENT_BULLISH"
