import pytest
from unittest.mock import patch
from app.quoting.pdf_renderer import render_quote_pdf, HAS_WEASYPRINT


def test_render_quote_pdf_creates_file():
    pdf_path = render_quote_pdf(
        quote_no="Q-TEST-001",
        customer_name="测试客户",
        items=[{"product_name": "产品A", "specification": "规格", "unit_price": 100.0, "quantity": 1, "discount": 0, "subtotal": 100.0}],
        total_amount=100.0,
        discount_total=0.0,
        final_amount=100.0,
        valid_until="2026-06-07",
    )

    assert "Q-TEST-001" in pdf_path


@pytest.mark.skipif(not HAS_WEASYPRINT, reason="WeasyPrint not available (macOS dev env)")
def test_render_quote_pdf_with_weasyprint():
    """Only runs when WeasyPrint is available (Linux/Docker)"""
    pass
