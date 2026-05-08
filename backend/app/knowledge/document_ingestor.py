import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeDocument, KnowledgeVector
from app.knowledge.chunker import chunk_text
from app.knowledge.embedding_service import embed_texts

logger = logging.getLogger(__name__)


async def ingest_document(
    session: AsyncSession,
    title: str,
    category: str,
    content: str,
    metadata: dict | None = None,
) -> KnowledgeDocument:
    """将文档入库：解析 → 分块 → 向量化 → 存储"""
    # 1. 创建文档记录
    doc_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    document = KnowledgeDocument(
        id=doc_id,
        title=title,
        category=category,
        content=content,
        metadata=metadata,
        created_at=now,
        updated_at=now,
    )
    session.add(document)

    # 2. 分块
    chunks = chunk_text(content)
    logger.info(f"Document '{title}' split into {len(chunks)} chunks")

    # 3. 批量生成向量
    embeddings = await embed_texts(chunks)

    # 4. 创建向量记录
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vector = KnowledgeVector(
            id=uuid.uuid4(),
            document_id=doc_id,
            chunk_index=i,
            content=chunk,
            embedding=embedding,
        )
        session.add(vector)

    await session.commit()
    await session.refresh(document)
    return document
