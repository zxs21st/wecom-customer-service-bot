"""create bot_order and after_sales_ticket tables

Revision ID: 003
Revises: 002
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bot_order",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("order_no", sa.String(50), unique=True, nullable=False),
        sa.Column("quote_id", UUID(as_uuid=True), sa.ForeignKey("quote.id"), nullable=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("chat_id", sa.String(100), nullable=False),
        sa.Column("customer_name", sa.String(100), nullable=False),
        sa.Column("items", JSONB, nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'pending'"),
        sa.Column("tracking_info", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "after_sales_ticket",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("ticket_no", sa.String(50), unique=True, nullable=False),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("chat_id", sa.String(100), nullable=False),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("bot_order.id"), nullable=True),
        sa.Column("issue_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'open'"),
        sa.Column("assigned_to", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table("after_sales_ticket")
    op.drop_table("bot_order")
