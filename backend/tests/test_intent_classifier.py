import pytest
from unittest.mock import patch, AsyncMock
from app.ai_engine.intent_classifier import classify_intent
from app.ai_engine.schemas import IntentType


@pytest.mark.asyncio
async def test_classify_price_inquiry():
    with patch("app.ai_engine.intent_classifier.litellm.acompletion") as mock:
        mock.return_value = AsyncMock()
        mock.return_value.choices = [
            AsyncMock(message=AsyncMock(content='{"intent": "price_inquiry", "confidence": 0.9}'))
        ]

        intent, confidence = await classify_intent("这个产品多少钱？")
        assert intent == IntentType.PRICE_INQUIRY
        assert confidence == 0.9


@pytest.mark.asyncio
async def test_classify_after_sales():
    with patch("app.ai_engine.intent_classifier.litellm.acompletion") as mock:
        mock.return_value = AsyncMock()
        mock.return_value.choices = [
            AsyncMock(message=AsyncMock(content='{"intent": "after_sales", "confidence": 0.85}'))
        ]

        intent, confidence = await classify_intent("我想退货，怎么操作？")
        assert intent == IntentType.AFTER_SALES


@pytest.mark.asyncio
async def test_classify_fallback():
    with patch("app.ai_engine.intent_classifier.litellm.acompletion") as mock:
        mock.return_value = AsyncMock()
        mock.return_value.choices = [
            AsyncMock(message=AsyncMock(content="invalid json"))
        ]

        intent, confidence = await classify_intent("随便聊聊")
        assert intent == IntentType.GENERAL_CHAT
        assert confidence == 0.5
