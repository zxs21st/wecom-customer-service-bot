import pytest
from unittest.mock import AsyncMock, MagicMock
from app.after_sales.order_service import create_order_from_quote


@pytest.mark.asyncio
async def test_create_order_from_quote():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    order = await create_order_from_quote(
        mock_session,
        quote_id="test-quote-id",
        user_id="user1",
        chat_id="chat1",
        customer_name="测试客户",
        items=[{"sku": "A1", "name": "产品A"}],
        total_amount=1000.0,
    )

    assert order.customer_name == "测试客户"
    assert order.status == "pending"
    assert order.order_no.startswith("BOT-")
