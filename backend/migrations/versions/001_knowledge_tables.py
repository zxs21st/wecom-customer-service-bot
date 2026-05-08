"""create knowledge_document and knowledge_vector tables

Revision ID: 001
Revises:
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 启用 pgvector 扩展
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_document",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "knowledge_vector",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("knowledge_document.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", sa.Text, nullable=True),  # pgvector column, manageded by extension
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_index("idx_vector_document", "knowledge_vector", ["document_id"])


def downgrade():
    op.drop_index("idx_vector_document", "knowledge_vector")
    op.drop_table("knowledge_vector")
    op.drop_table("knowledge_document")
    op.execute("DROP EXTENSION IF EXISTS vector")
