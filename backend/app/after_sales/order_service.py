import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.after_sales import BotOrder


def _generate_order_no() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = str(uuid.uuid4())[:4].upper()
    return f"BOT-{today}-{suffix}"


async def create_order_from_quote(
    session: AsyncSession,
    quote_id: str,
    user_id: str,
    chat_id: str,
    customer_name: str,
    items: list[dict],
    total_amount: float,
) -> BotOrder:
    """将报价转为订单"""
    order = BotOrder(
        id=uuid.uuid4(),
        order_no=_generate_order_no(),
        quote_id=quote_id,
        user_id=user_id,
        chat_id=chat_id,
        customer_name=customer_name,
        items=items,
        total_amount=Decimal(str(total_amount)),
        status="pending",
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_order(session: AsyncSession, order_id: str) -> BotOrder | None:
    """获取订单"""
    return await session.get(BotOrder, order_id)


async def update_order_status(
    session: AsyncSession,
    order_id: str,
    status: str,
    tracking_info: str | None = None,
) -> BotOrder:
    """更新订单状态"""
    order = await session.get(BotOrder, order_id)
    if not order:
        raise ValueError(f"Order {order_id} not found")
    order.status = status
    if tracking_info:
        order.tracking_info = tracking_info
    await session.commit()
    await session.refresh(order)
    return order
