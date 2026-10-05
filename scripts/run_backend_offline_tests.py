"""Run the full existing backend suite without competing for local inference.

Tests that explicitly mock model responses override this patch. Conditional real
model tests skip. Real inference is verified separately through the website.
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import pytest
with patch("app.services.ai_provider.OllamaProvider.check_health", return_value={"status": "OFFLINE", "available_models": []}):
    raise SystemExit(pytest.main(sys.argv[1:] or ["tests/backend", "-q", "--disable-warnings"]))
