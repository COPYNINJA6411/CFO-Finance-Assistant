"""Validated boundaries for user questions and assistant responses."""
from pydantic import BaseModel, Field

class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)

class AssistantResponse(BaseModel):
    answer: str
    sql: str | None = None
    rows: list[dict] = Field(default_factory=list)
    reconciled: bool = False
    latency_ms: int = Field(ge=0)
