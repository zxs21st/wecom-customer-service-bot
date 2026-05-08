from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class QuoteStatus:
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Quote(Base):
    __tablename__ = "quote"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    quote_no: Mapped[str] = mapped_column(String(50), unique=True)
    customer_name: Mapped[str] = mapped_column(String(100))
    customer_contact: Mapped[Optional[str]] = mapped_column(String(100))
    user_id: Mapped[Optional[str]] = mapped_column(String(100))
    chat_id: Mapped[Optional[str]] = mapped_column(String(100))
    items: Mapped[list[dict]] = mapped_column(JSONB)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), server_default="0")
    final_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    valid_until: Mapped[date]
    status: Mapped[str] = mapped_column(String(20), server_default="'draft'")
    prepared_by: Mapped[Optional[str]] = mapped_column(String(100))
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # relationship set via import ordering in __init__.py
