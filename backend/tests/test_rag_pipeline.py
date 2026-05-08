import pytest
from unittest.mock import patch, AsyncMock
from app.ai_engine.response_generator import generate_response
from app.ai_engine.schemas import IntentType


@pytest.mark.asyncio
async def test_generate_response_with_knowledge():
    knowledge_results = [
        {"title": "产品A规格", "content": "产品A尺寸为10x20x30cm，重量500g"},
    ]

    with patch("app.ai_engine.response_generator.litellm.acompletion") as mock:
        mock.return_value = AsyncMock()
        mock.return_value.choices = [
            AsyncMock(message=AsyncMock(content="产品A的尺寸为10x20x30cm，重量为500g。"))
        ]

        response = await generate_response(
            IntentType.PRODUCT_KNOWLEDGE,
            "产品A的尺寸是多少？",
            knowledge_results,
        )

        assert response.intent == IntentType.PRODUCT_KNOWLEDGE
        assert "10x20x30cm" in response.reply_text
        assert len(response.sources) == 1
        assert response.sources[0] == "产品A规格"
