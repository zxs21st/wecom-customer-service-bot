import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.after_sales import AfterSalesTicket


def _generate_ticket_no() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = str(uuid.uuid4())[:4].upper()
    return f"AS-{today}-{suffix}"


async def create_ticket(
    session: AsyncSession,
    user_id: str,
    chat_id: str,
    issue_type: str,
    description: str,
    order_id: str | None = None,
) -> AfterSalesTicket:
    """创建售后工单"""
    ticket = AfterSalesTicket(
        id=uuid.uuid4(),
        ticket_no=_generate_ticket_no(),
        user_id=user_id,
        chat_id=chat_id,
        order_id=order_id,
        issue_type=issue_type,
        description=description,
        status="open",
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def update_ticket_status(
    session: AsyncSession,
    ticket_id: str,
    status: str,
    assigned_to: str | None = None,
) -> AfterSalesTicket:
    """更新工单状态"""
    ticket = await session.get(AfterSalesTicket, ticket_id)
    if not ticket:
        raise ValueError(f"Ticket {ticket_id} not found")
    ticket.status = status
    if assigned_to:
        ticket.assigned_to = assigned_to
    await session.commit()
    await session.refresh(ticket)
    return ticket
