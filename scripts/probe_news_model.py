"""Opt-in public-news-only real Qwen diagnostic, isolated from user portfolios."""
import json
import sys
from pathlib import Path
from unittest.mock import patch
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.database.base import Base
from app.services.market_assistant_service import MarketAssistantService as Chat


def main():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with httpx.Client(trust_env=False) as client, Session(engine) as db:
        Chat._ollama_client = client
        original = client.post
        def record(*args, **kwargs):
            response = original(*args, **kwargs)
            (ROOT / "docs/news_public_model_probe.json").write_text(json.dumps({"prompt": kwargs["json"]["prompt"], "payload": response.json()}, indent=2, ensure_ascii=False), encoding="utf-8")
            return response
        with patch.object(client, "post", side_effect=record):
            result = Chat.process_chat_message(db, "public-news-probe", "Latest NIFTY news")
        print(result.content)
        print("fallback:", result.is_fallback)
    engine.dispose()


if __name__ == "__main__":
    main()
