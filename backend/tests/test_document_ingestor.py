import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.knowledge.document_ingestor import ingest_document


@pytest.mark.asyncio
async def test_ingest_document_splits_and_embeds():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    with patch("app.knowledge.document_ingestor.chunk_text") as mock_chunk:
        mock_chunk.return_value = ["chunk1", "chunk2"]
        with patch("app.knowledge.document_ingestor.embed_texts") as mock_embed:
            mock_embed.return_value = [[0.1] * 1536, [0.2] * 1536]

            doc = await ingest_document(
                mock_session,
                title="测试产品",
                category="product_knowledge",
                content="这是一个测试产品。",
            )

            # 验证调用了分块和向量化
            mock_chunk.assert_called_once()
            mock_embed.assert_called_once_with(["chunk1", "chunk2"])
            mock_session.add.assert_called()
