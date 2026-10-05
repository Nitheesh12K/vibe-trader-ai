"""News evidence travels separately from model-generated interpretation."""
from datetime import datetime
from typing import Literal
import re
import unicodedata
from pydantic import AwareDatetime, BaseModel, Field, ConfigDict, field_validator


class NewsArticle(BaseModel):
    title: str = Field(min_length=1, max_length=220)
    publisher: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=2048)
    published_at: AwareDatetime
    retrieved_at: AwareDatetime
    snippet: str = Field(default="", max_length=500)
    provider: str
    evidence_type: Literal["SEARCH_EXCERPT"] = "SEARCH_EXCERPT"


class NewsResult(BaseModel):
    status: Literal["OK", "NO_RECENT_NEWS", "PROVIDER_ERROR", "CLARIFICATION"]
    provider: str
    error_code: Literal["RATE_LIMITED", "AUTH_REQUIRED", "TIMEOUT", "CONFIGURATION_ERROR", "BAD_RESPONSE", "UNAVAILABLE"] | None = None
    query: str = ""
    articles: list[NewsArticle] = Field(default_factory=list)
    checked_at: AwareDatetime
    cache_hit: bool = False
    context_reused: bool = False
    retrieval_ms: float = 0
    max_age_hours: int = 72
    rejected_results: int = 0
    notice: str = ""
    summary: str = ""
    possible_market_implications: str = ""
    model_metrics: dict[str, float] = Field(default_factory=dict)


class NewsAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Summary is an exact retrieved headline (runtime enum); interpretation
    # remains qualitative. This avoids changing facts through paraphrasing.
    summary: str = Field(min_length=1, max_length=220)
    possible_market_implications: str = Field(max_length=800, pattern=r"^[A-Za-z \t\n,.;:!?()'\"/&-]*$")
    source_ids: list[int] = Field(min_length=1, max_length=5)

    @field_validator("possible_market_implications", mode="before")
    @classmethod
    def qualitative_prose(cls, value):
        if isinstance(value, str):
            value = unicodedata.normalize("NFKC", value)
            if re.search(r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|hundred|thousand|million|billion)\b", value, re.I):
                raise ValueError("Quantitative news claims belong in retrieved evidence")
        return value
