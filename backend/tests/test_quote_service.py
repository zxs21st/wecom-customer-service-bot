import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from app.quoting.quote_service import create_quote, _calculate_items


def test_calculate_items_with_discount():
    items = [
        {"sku": "A1", "product_name": "产品A", "unit_price": 100.0, "quantity": 2, "discount": 0.1},
    ]
    total, discount_total, final = _calculate_items(items)
    assert total == Decimal("200.0")
    assert discount_total == Decimal("20.0")
    assert final == Decimal("180.0")


def test_calculate_items_no_discount():
    items = [
        {"sku": "A1", "product_name": "产品A", "unit_price": 50.0, "quantity": 3, "discount": 0},
    ]
    total, discount_total, final = _calculate_items(items)
    assert total == Decimal("150.0")
    assert discount_total == Decimal("0")
    assert final == Decimal("150.0")


def test_calculate_items_multiple():
    items = [
        {"sku": "A1", "product_name": "产品A", "unit_price": 100.0, "quantity": 1, "discount": 0},
        {"sku": "B1", "product_name": "产品B", "unit_price": 200.0, "quantity": 2, "discount": 0.2},
    ]
    total, discount_total, final = _calculate_items(items)
    assert total == Decimal("500.0")
    assert discount_total == Decimal("80.0")
    assert final == Decimal("420.0")


@pytest.mark.asyncio
async def test_create_quote():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    items = [{"sku": "A1", "product_name": "产品A", "unit_price": 100.0, "quantity": 1, "discount": 0, "subtotal": 100.0}]

    quote = await create_quote(
        mock_session,
        customer_name="测试客户",
        items=items,
    )

    assert quote.customer_name == "测试客户"
    assert quote.status == "draft"
    mock_session.add.assert_called_once()
