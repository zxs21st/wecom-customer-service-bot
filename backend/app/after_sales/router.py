import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.after_sales.schemas import TicketCreate, TicketResponse, OrderResponse
from app.after_sales.ticket_service import create_ticket, update_ticket_status
from app.after_sales.order_service import get_order

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/after-sales", tags=["after-sales"])


@router.post("/tickets", response_model=TicketResponse)
async def create_ticket_endpoint(data: TicketCreate, db: AsyncSession = Depends(get_db)):
    """创建售后工单"""
    ticket = await create_ticket(
        db,
        user_id=data.user_id,
        chat_id=data.chat_id,
        issue_type=data.issue_type,
        description=data.description,
        order_id=data.order_id,
    )
    return TicketResponse(
        id=str(ticket.id),
        ticket_no=ticket.ticket_no,
        issue_type=ticket.issue_type,
        description=ticket.description,
        status=ticket.status,
        assigned_to=ticket.assigned_to,
        created_at=ticket.created_at,
    )


@router.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, status: str, assigned_to: str | None = None, db: AsyncSession = Depends(get_db)):
    """更新工单状态"""
    ticket = await update_ticket_status(db, ticket_id, status, assigned_to)
    return {"status": "ok", "ticket_no": ticket.ticket_no}


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_endpoint(order_id: str, db: AsyncSession = Depends(get_db)):
    """获取订单详情"""
    order = await get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(
        id=str(order.id),
        order_no=order.order_no,
        customer_name=order.customer_name,
        items=order.items,
        total_amount=float(order.total_amount),
        status=order.status,
        tracking_info=order.tracking_info,
        created_at=order.created_at,
    )
