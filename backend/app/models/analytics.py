from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, DateTime, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ConsultationRecord(Base):
    __tablename__ = "consultation_record"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    user_id: Mapped[Optional[str]] = mapped_column(String(100))
    chat_id: Mapped[Optional[str]] = mapped_column(String(100))
    intent_type: Mapped[Optional[str]] = mapped_column(String(50))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    is_resolved: Mapped[Optional[bool]] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
