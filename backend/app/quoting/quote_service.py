import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.quoting import Quote, QuoteStatus


def _generate_quote_no() -> str:
    """生成报价单号: Q-YYYYMMDD-XXXX"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = str(uuid.uuid4())[:4].upper()
    return f"Q-{today}-{suffix}"


def _calculate_items(items: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
    """计算总价、折扣、最终金额"""
    total = Decimal("0")
    discount_total = Decimal("0")
    for item in items:
        unit_price = Decimal(str(item["unit_price"]))
        quantity = item["quantity"]
        discount = Decimal(str(item.get("discount", 0)))
        subtotal = unit_price * quantity * (1 - discount)
        item["subtotal"] = float(subtotal)
        total += unit_price * quantity
        discount_total += unit_price * quantity * discount
    final_amount = total - discount_total
    return total, discount_total, final_amount


async def create_quote(
    session: AsyncSession,
    customer_name: str,
    items: list[dict],
    user_id: str | None = None,
    chat_id: str | None = None,
    customer_contact: str | None = None,
    valid_days: int = 30,
) -> Quote:
    """创建报价单"""
    total, discount_total, final_amount = _calculate_items(items)
    valid_until = datetime.now(timezone.utc) + timedelta(days=valid_days)

    quote = Quote(
        id=uuid.uuid4(),
        quote_no=_generate_quote_no(),
        customer_name=customer_name,
        customer_contact=customer_contact,
        user_id=user_id,
        chat_id=chat_id,
        items=items,
        total_amount=total,
        discount_total=discount_total,
        final_amount=final_amount,
        valid_until=valid_until.date(),
        status=QuoteStatus.DRAFT,
        prepared_by="bot",
    )
    session.add(quote)
    await session.commit()
    await session.refresh(quote)
    return quote


async def get_quote(session: AsyncSession, quote_id: str) -> Quote | None:
    """获取报价单"""
    return await session.get(Quote, quote_id)


async def accept_quote(session: AsyncSession, quote_id: str) -> Quote:
    """接受报价单"""
    quote = await session.get(Quote, quote_id)
    if not quote:
        raise ValueError(f"Quote {quote_id} not found")
    quote.status = QuoteStatus.ACCEPTED
    await session.commit()
    await session.refresh(quote)
    return quote


async def update_quote_pdf_url(session: AsyncSession, quote_id: str, pdf_url: str) -> Quote:
    """更新报价 PDF URL"""
    quote = await session.get(Quote, quote_id)
    if quote:
        quote.pdf_url = pdf_url
        await session.commit()
        await session.refresh(quote)
    return quote
