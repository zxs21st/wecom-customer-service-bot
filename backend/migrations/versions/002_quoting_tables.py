"""create quote table

Revision ID: 002
Revises: 001
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "quote",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("quote_no", sa.String(50), unique=True, nullable=False),
        sa.Column("customer_name", sa.String(100), nullable=False),
        sa.Column("customer_contact", sa.String(100), nullable=True),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("chat_id", sa.String(100), nullable=True),
        sa.Column("items", JSONB, nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_total", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("final_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("valid_until", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'draft'"),
        sa.Column("prepared_by", sa.String(100), nullable=True),
        sa.Column("pdf_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table("quote")
