"""Advisory Explanation Synthesis Engine integrating Rule-Based Signals,
XGBoost Machine Learning Probabilities, and Qwen / Local LLM Reasoning.
Strictly advisory: Does not trigger order execution or override Risk Guardian.
"""
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.services.ai_provider import OllamaProvider
from app.services.audit_service import AuditService
from app.schemas.qwen_advisory import QwenAdvisoryContract
from app.services.qwen_advisory_parser import QwenResponseParser, QwenAdvisoryAdapter
from app.models.entities import utcnow

logger = logging.getLogger("vibe-trader-ai.xgboost_explainer")


class XGBoostAdvisoryExplainer:
    """Synthesizes deterministic strategy signals, XGBoost direction probabilities,
    and Qwen/Local LLM explanations into a strictly typed, auditable research report.
    """

    DEFAULT_TIMEOUT_SECONDS = 4.0

    @classmethod
    def resolve_best_qwen_model(cls, available_models: List[str], requested: Optional[str] = None) -> str:
        """Dynamically identifies the best local Qwen model from Ollama."""
        if requested and requested in available_models:
            return requested
        for m in available_models:
            if "qwen" in m.lower():
                return m
        return requested or "qwen3-local:latest"

    @classmethod
    def synthesize_advisory_analysis(
        cls,
        db: Session,
        symbol: str,
        timeframe: str,
        rule_signal: str,
        xgboost_prediction: Optional[Dict[str, Any]] = None,
        technical_context: Optional[Dict[str, Any]] = None,
        ollama_host: str = "http://127.0.0.1:11434",
        model_name: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        input_timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Synthesizes rule-based signals and XGBoost predictions using Qwen with strict schema validation
        and reliable deterministic fallback.
        """
        now_ts = input_timestamp or int(datetime.now(timezone.utc).timestamp())
        tech_ctx = technical_context or {}
        xgb_ctx = dict(xgboost_prediction) if xgboost_prediction else {
            "predicted_direction": "UNKNOWN",
            "predicted_probability": 0.5,
            "bullish_probability": 0.5,
            "bearish_probability": 0.5,
            "advisory_only": True,
        }
        pred_prob = float(xgb_ctx.get("predicted_probability", 0.5))
        pred_dir = str(xgb_ctx.get("predicted_direction", "UNKNOWN")).upper()
        if "bullish_probability" not in xgb_ctx:
            xgb_ctx["bullish_probability"] = pred_prob if pred_dir in ["UP", "BULLISH_UP"] else (1.0 - pred_prob)
        if "bearish_probability" not in xgb_ctx:
            xgb_ctx["bearish_probability"] = pred_prob if pred_dir in ["DOWN", "BEARISH_DOWN"] else (1.0 - pred_prob)

        # Format normalized signal
        norm_signal = rule_signal.strip().upper()
        if norm_signal.startswith("STRATEGY_"):
            norm_signal = norm_signal.replace("STRATEGY_", "")

        # Check alignment / divergence between rule-based signal and XGBoost
        rule_is_bullish = norm_signal in ["BUY", "BUY_CANDIDATE"]
        rule_is_bearish = norm_signal in ["SELL", "SELL_CANDIDATE"]
        bullish_prob = float(xgb_ctx.get("bullish_probability", 0.5))
        bearish_prob = float(xgb_ctx.get("bearish_probability", 0.5))

        xgb_is_bullish = bullish_prob > 0.52
        xgb_is_bearish = bearish_prob > 0.52

        divergence_detected = False
        divergence_summary = "Rule-based signal and XGBoost direction are consistent."

        if rule_is_bullish and xgb_is_bearish:
            divergence_detected = True
            divergence_summary = (
                f"DIVERGENCE DETECTED: Deterministic rule proposes BUY, but XGBoost model forecasts "
                f"{bearish_prob*100:.1f}% downside probability."
            )
        elif rule_is_bearish and xgb_is_bullish:
            divergence_detected = True
            divergence_summary = (
                f"DIVERGENCE DETECTED: Deterministic rule proposes SELL, but XGBoost model forecasts "
                f"{bullish_prob*100:.1f}% upside probability."
            )
        elif not rule_is_bullish and xgb_is_bullish and "HOLD" in norm_signal:
            divergence_summary = (
                f"CAUTION: XGBoost forecasts {bullish_prob*100:.1f}% upward momentum, "
                "but rule-based strategy remains in HOLD state awaiting strict indicator confirmation."
            )

        verdict = (
            "DIVERGENT"
            if divergence_detected
            else (
                "CONFLUENT_BULLISH"
                if rule_is_bullish and xgb_is_bullish
                else ("CONFLUENT_BEARISH" if rule_is_bearish and xgb_is_bearish else "NEUTRAL_UNCERTAIN")
            )
        )

        # Build context for LLM
        synthesis_context = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": now_ts,
            "rule_based_signal": norm_signal,
            "xgboost_prediction": {
                "predicted_direction": xgb_ctx.get("predicted_direction", "UNKNOWN"),
                "predicted_probability": round(float(xgb_ctx.get("predicted_probability", 0.5)), 4),
                "bullish_probability": round(bullish_prob, 4),
                "bearish_probability": round(bearish_prob, 4),
                "model_version": xgb_ctx.get("model_version", "1.0.0"),
                "advisory_only": True,
            },
            "technical_indicators": {
                "rsi_14": tech_ctx.get("rsi_14"),
                "macd_hist_norm": tech_ctx.get("macd_hist_norm"),
                "ema_trend_50": tech_ctx.get("ema_trend_50"),
                "atr_norm_14": tech_ctx.get("atr_norm_14"),
            },
        }

        # Attempt Qwen / Ollama inference
        ollama_provider = OllamaProvider(host=ollama_host, default_model=model_name or "qwen3-local:latest")
        health = ollama_provider.check_health()

        contract: Optional[QwenAdvisoryContract] = None
        provider_used = "DETERMINISTIC_FALLBACK"
        chosen_model = model_name

        if health.get("status") == "ONLINE":
            avail = health.get("available_models", [])
            chosen_model = cls.resolve_best_qwen_model(avail, requested=model_name)

            prompt = (
                "You are Vibe Trading AI's Senior Quantitative Research Analyst (Qwen). "
                "Analyze the synthesized quantitative context below and return ONLY valid JSON matching this schema:\n"
                "{\n"
                '  "schema_version": "1.0.0",\n'
                '  "summary": "1-2 concise sentences summarizing the directional interaction.",\n'
                '  "deterministic_signal": "BUY" | "SELL" | "HOLD" | "BUY_CANDIDATE" | "NO_TRADE",\n'
                '  "xgboost_direction": "BULLISH_UP" | "BEARISH_DOWN" | "UP" | "DOWN" | "UNKNOWN" | "ABSTAIN",\n'
                '  "xgboost_probability": 0.0 to 1.0,\n'
                '  "divergence_detected": true | false,\n'
                '  "divergence_reason": "Description of any disagreement or null if aligned",\n'
                '  "synthesis_verdict": "CONFLUENT_BULLISH" | "CONFLUENT_BEARISH" | "DIVERGENT" | "NEUTRAL_UNCERTAIN",\n'
                '  "explanation": "2-3 concise factual sentences citing provided indicators.",\n'
                '  "risk_context": "Risk limits and invalidation boundaries.",\n'
                '  "warnings": ["warning 1"],\n'
                '  "input_timestamp": 1234567890,\n'
                f'  "model_name": "{chosen_model}",\n'
                '  "model_version": "1.0.0",\n'
                '  "advisory_caveat": "XGBoost outputs and AI explanations are strictly advisory research. Zero real-money trades are executed."\n'
                "}\n\n"
                "RULES:\n"
                "1. NEVER invent prices, volumes, or indicators. Only reference provided context values.\n"
                "2. If rule signal and XGBoost disagree, set divergence_detected to true.\n"
                "3. Never output executable code or trading instructions.\n"
                "4. Adhere strictly to JSON output.\n\n"
                f"SYNTHESIS CONTEXT:\n{json.dumps(synthesis_context, indent=2)}"
            )

            try:
                import httpx
                start_req = time.perf_counter()
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(
                        f"{ollama_provider.host}/api/generate",
                        json={
                            "model": chosen_model,
                            "prompt": prompt,
                            "stream": False,
                            "format": "json",
                            "options": {"temperature": 0.1, "num_predict": 384},
                        },
                    )
                    latency_ms = (time.perf_counter() - start_req) * 1000

                    if resp.status_code == 200:
                        raw = resp.json().get("response", "{}")
                        contract, failure = QwenResponseParser.parse_and_validate(
                            raw_text=raw,
                            expected_signal=norm_signal,
                            input_timestamp=now_ts,
                            model_name=chosen_model,
                            model_version="1.0.0",
                            xgboost_context=xgb_ctx,
                        )
                        if contract:
                            provider_used = f"OLLAMA_{chosen_model.upper()}"
                            logger.info(f"Qwen advisory contract validated ({provider_used}, {latency_ms:.1f}ms)")
                        else:
                            logger.warning(
                                f"Qwen advisory validation failed ({failure.error_type}: {failure.error_detail}); "
                                "falling back to deterministic synthesis."
                            )
            except Exception as e:
                logger.debug(f"Ollama Qwen synthesis unavailable, offline, or timed out: {e}")
                contract = None

        # Fallback to deterministic synthesis if Ollama is offline or failed validation
        if not contract:
            provider_used = "DETERMINISTIC_FALLBACK"
            contract = QwenAdvisoryContract(
                schema_version="1.0.0",
                summary=f"Deterministic synthesis for {symbol} ({norm_signal}). {divergence_summary}"[:500],
                deterministic_signal=norm_signal if norm_signal in ["BUY", "SELL", "HOLD", "BUY_CANDIDATE", "NO_TRADE"] else "HOLD",
                xgboost_direction=xgb_ctx.get("predicted_direction", "UP" if float(xgb_ctx.get("bullish_probability", 0.5)) >= 0.5 else "DOWN"),
                xgboost_probability=round(float(xgb_ctx.get("predicted_probability", xgb_ctx.get("bullish_probability", 0.5))), 4),
                probability_calibrated=False,
                divergence_detected=divergence_detected,
                divergence_reason=divergence_summary if divergence_detected else None,
                synthesis_verdict=verdict,
                explanation=(
                    f"Rule signal '{norm_signal}' evaluated against XGBoost next-bar direction "
                    f"({xgb_ctx.get('predicted_direction')} with {xgb_ctx.get('predicted_probability', xgb_ctx.get('bullish_probability', 0.5))*100:.1f}% probability). "
                    f"{divergence_summary}"
                )[:2000],
                risk_context="Deterministic Risk Guardian enforces strict stop-loss, position limits, and daily loss caps.",
                warnings=[divergence_summary] if divergence_detected else [],
                input_timestamp=now_ts,
                model_name="deterministic-fallback-analyzer",
                model_version="1.0.0",
                advisory_caveat="XGBoost outputs and AI explanations are strictly advisory research. Zero real-money trades are executed.",
            )

        # Transform to unified payload supporting both strict contract and legacy viewers
        result = QwenAdvisoryAdapter.to_synthesize_response_dict(
            contract=contract,
            symbol=symbol,
            timeframe=timeframe,
            provider_used=provider_used,
            xgboost_prediction_dict=xgb_ctx,
            technical_context=technical_context,
            raw_rule_signal=rule_signal,
        )

        # Log to tamper-evident audit trail
        try:
            AuditService.log_event(
                db=db,
                event_type="XGBOOST_ADVISORY_SYNTHESIS",
                action="SYNTHESIS_EVALUATED",
                actor=provider_used,
                symbol=symbol,
                details={
                    "rule_signal": norm_signal,
                    "xgb_direction": contract.xgboost_direction,
                    "divergence": contract.divergence_detected,
                    "verdict": contract.synthesis_verdict,
                    "schema_version": contract.schema_version,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to log advisory synthesis audit event: {e}")

        return result
