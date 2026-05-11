import pytest
from unittest.mock import patch, AsyncMock
from app.knowledge.vector_search import search_similar


@pytest.mark.asyncio
async def test_search_returns_results():
    mock_response_data = {
        "data": [
            {
                "id": "kb1",
                "title": "产品A规格说明",
                "description": "产品A的详细规格参数",
                "file_name": "product_a.pdf",
            },
            {
                "id": "kb2",
                "title": "产品B规格说明",
                "description": "产品B的详细规格参数",
                "file_name": "product_b.pdf",
            },
        ],
        "success": True,
    }

    async def fake_get(*args, **kwargs):
        class FakeResp:
            def raise_for_status(self):
                pass
            def json(self):
                return mock_response_data
        return FakeResp()

    with patch("app.knowledge.vector_search.settings") as mock_settings:
        mock_settings.weknora_base_url = "http://test-server"
        mock_settings.weknora_api_key = "test-key"
        mock_settings.weknora_kb_id = "test-kb"

        with patch("app.knowledge.vector_search.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=AsyncMock(get=fake_get))
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            results = await search_similar("产品规格", top_k=2)
            assert len(results) == 2
            assert results[0]["title"] == "产品A规格说明"
            assert results[0]["similarity"] == 1.0
