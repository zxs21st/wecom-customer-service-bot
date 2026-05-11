import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


async def search_similar(query: str, db=None, top_k: int = 5, category_filter: str | None = None) -> list[dict]:
    """通过 WeKnora API 搜索相关知识"""
    if not settings.weknora_base_url or not settings.weknora_api_key:
        logger.warning("WeKnora 未配置，返回空结果")
        return []

    params = {"query": query, "top_k": top_k}
    if settings.weknora_kb_id:
        params["kb_id"] = settings.weknora_kb_id
    if category_filter:
        params["category"] = category_filter

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{settings.weknora_base_url}/api/v1/knowledge/search",
                params=params,
                headers={"x-api-key": settings.weknora_api_key},
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("data", []):
            results.append({
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "content": item.get("description", ""),
                "category": "",
                "similarity": 1.0,
                "source": item.get("file_name", ""),
            })

        logger.info(f"WeKnora search returned {len(results)} results for: {query[:30]}")
        return results

    except Exception as e:
        logger.error(f"WeKnora search error: {e}")
        return []
