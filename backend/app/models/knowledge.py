from datetime import datetime, timezone
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

EMBEDDING_DIM = 1536


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100))  # product_knowledge, config_guide, faq, after_sales
    content: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSONB, name="metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    vectors: Mapped[list["KnowledgeVector"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class KnowledgeVector(Base):
    __tablename__ = "knowledge_vector"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_document.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="vectors")
