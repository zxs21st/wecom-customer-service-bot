import logging
from fastapi import APIRouter
from app.knowledge.schemas import SearchRequest, SearchResult
from app.knowledge.vector_search import search_similar

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/search", response_model=list[SearchResult])
async def search(data: SearchRequest):
    """搜索知识 (通过 WeKnora API)"""
    results = await search_similar(data.query, top_k=data.top_k)
    return [
        SearchResult(
            id=r["id"],
            title=r["title"],
            content=r["content"][:300],
            similarity=r["similarity"],
            category=r.get("category", ""),
        )
        for r in results
    ]
