"""create consultation_record table

Revision ID: 004
Revises: 003
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "consultation_record",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("chat_id", sa.String(100), nullable=True),
        sa.Column("intent_type", sa.String(50), nullable=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("is_resolved", sa.Boolean, nullable=True, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # 创建按日统计视图
    op.execute("""
        CREATE VIEW daily_consultation_stats AS
        SELECT
            DATE(created_at) as date,
            COUNT(*) as total_queries,
            COUNT(CASE WHEN is_resolved THEN 1 END) as resolved_queries,
            AVG(confidence) as avg_confidence
        FROM consultation_record
        GROUP BY DATE(created_at)
    """)


def downgrade():
    op.execute("DROP VIEW IF EXISTS daily_consultation_stats")
    op.drop_table("consultation_record")
