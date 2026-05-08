from datetime import date
from pydantic import BaseModel


class DashboardStats(BaseModel):
    today_queries: int
    today_resolved: int
    total_queries: int
    avg_confidence: float
    top_intents: list[dict]  # [{"intent": str, "count": int}]
    unresolved_count: int


class DailyStat(BaseModel):
    date: date
    total_queries: int
    resolved_queries: int
    avg_confidence: float


class ConsultationRecordResponse(BaseModel):
    id: str
    session_id: str | None
    user_id: str | None
    intent_type: str | None
    question: str
    answer: str | None
    confidence: float | None
    is_resolved: bool | None
    created_at: str
