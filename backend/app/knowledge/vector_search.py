import json
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.knowledge.embedding_service import embed_text

logger = logging.getLogger(__name__)

# pgvector 余弦相似度搜索查询
VECTOR_SEARCH_SQL = """
SELECT kv.id, kv.document_id, kv.content, kv.chunk_index, kd.title, kd.category,
       1 - (kv.embedding::vector <=> :query_vector::vector) AS similarity
FROM knowledge_vector kv
JOIN knowledge_document kd ON kv.document_id = kd.id
ORDER BY similarity DESC
LIMIT :top_k
"""


async def search_similar(query: str, session: AsyncSession, top_k: int = 5, category_filter: str | None = None) -> list[dict]:
    """搜索与查询文本相似的知识片段"""
    # 生成查询向量
    query_vector = await embed_text(query)
    query_vector_str = json.dumps(query_vector)

    # 构建 SQL
    sql = VECTOR_SEARCH_SQL
    if category_filter:
        sql = sql.replace("LIMIT :top_k", f"AND kd.category = :category\nLIMIT :top_k")

    result = await session.execute(
        text(sql),
        {
            "query_vector": query_vector_str,
            "top_k": top_k,
            "category": category_filter,
        } if category_filter else {
            "query_vector": query_vector_str,
            "top_k": top_k,
        }
    )

    rows = result.fetchall()
    return [
        {
            "id": str(row.id),
            "document_id": str(row.document_id),
            "content": row.content,
            "chunk_index": row.chunk_index,
            "title": row.title,
            "category": row.category,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]
