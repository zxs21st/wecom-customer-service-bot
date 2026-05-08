import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.knowledge.vector_search import search_similar


@pytest.mark.asyncio
async def test_search_returns_results():
    # Build mock row objects with attribute access
    def make_row(id, document_id, content, chunk_index, title, category, similarity):
        row = MagicMock()
        row.id = id
        row.document_id = document_id
        row.content = content
        row.chunk_index = chunk_index
        row.title = title
        row.category = category
        row.similarity = similarity
        return row

    mock_results = [
        make_row(1, "doc1", "content A", 0, "产品A", "product_knowledge", 0.92),
        make_row(2, "doc2", "content B", 1, "产品B", "product_knowledge", 0.85),
    ]

    mock_result_obj = MagicMock()
    mock_result_obj.fetchall.return_value = mock_results

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result_obj

    with patch("app.knowledge.vector_search.embed_text", return_value=[0.1] * 1536):
        results = await search_similar("产品规格", mock_session, top_k=2)
        assert len(results) == 2
        assert results[0]["title"] == "产品A"
        assert results[0]["similarity"] == 0.92
