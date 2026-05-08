import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models.knowledge import KnowledgeDocument
from app.knowledge.schemas import DocumentCreate, DocumentUpdate, DocumentResponse, SearchRequest, SearchResult
from app.knowledge.document_ingestor import ingest_document
from app.knowledge.vector_search import search_similar

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/documents", response_model=DocumentResponse)
async def create_document(data: DocumentCreate, db: AsyncSession = Depends(get_db)):
    """录入知识文档"""
    doc = await ingest_document(
        db,
        title=data.title,
        category=data.category,
        content=data.content,
        metadata=data.metadata,
    )
    return DocumentResponse(
        id=str(doc.id),
        title=doc.title,
        category=doc.category,
        content=doc.content,
        metadata=doc.metadata,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """获取知识文档详情"""
    result = await db.get(KnowledgeDocument, doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=str(result.id),
        title=result.title,
        category=result.category,
        content=result.content,
        metadata=result.metadata,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(category: str | None = None, db: AsyncSession = Depends(get_db)):
    """列出知识文档"""
    query = select(KnowledgeDocument)
    if category:
        query = query.where(KnowledgeDocument.category == category)
    query = query.order_by(KnowledgeDocument.created_at.desc())
    result = await db.execute(query)
    docs = result.scalars().all()
    return [
        DocumentResponse(
            id=str(d.id), title=d.title, category=d.category, content=d.content,
            metadata=d.metadata, created_at=d.created_at, updated_at=d.updated_at,
        )
        for d in docs
    ]


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """删除知识文档"""
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
    return {"status": "ok"}


@router.post("/search", response_model=list[SearchResult])
async def search(data: SearchRequest, db: AsyncSession = Depends(get_db)):
    """搜索知识"""
    results = await search_similar(data.query, db, top_k=data.top_k, category_filter=data.category)
    return [
        SearchResult(
            id=r["id"],
            title=r["title"],
            content=r["content"][:300],  # 截断预览
            similarity=r["similarity"],
            category=r["category"],
        )
        for r in results
    ]
