from datetime import datetime, timezone
from typing import Optional

from decimal import Decimal

from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class BotOrder(Base):
    __tablename__ = "bot_order"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    order_no: Mapped[str] = mapped_column(String(50), unique=True)
    quote_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("quote.id"), nullable=True)
    user_id: Mapped[str] = mapped_column(String(100))
    chat_id: Mapped[str] = mapped_column(String(100))
    customer_name: Mapped[str] = mapped_column(String(100))
    items: Mapped[dict] = mapped_column(JSONB)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), server_default="'pending'")
    tracking_info: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # relationships set via import ordering in __init__.py


class AfterSalesTicket(Base):
    __tablename__ = "after_sales_ticket"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    ticket_no: Mapped[str] = mapped_column(String(50), unique=True)
    user_id: Mapped[str] = mapped_column(String(100))
    chat_id: Mapped[str] = mapped_column(String(100))
    order_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("bot_order.id"), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="'open'")
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # relationships set via import ordering in __init__.py
