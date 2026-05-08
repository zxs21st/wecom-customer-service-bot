from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TicketCreate(BaseModel):
    user_id: str
    chat_id: str
    order_id: Optional[str] = None
    issue_type: str  # return/exchange/repair/complaint
    description: str


class TicketResponse(BaseModel):
    id: str
    ticket_no: str
    issue_type: str
    description: str
    status: str
    assigned_to: Optional[str] = None
    created_at: datetime


class OrderResponse(BaseModel):
    id: str
    order_no: str
    customer_name: str
    items: list[dict]
    total_amount: float
    status: str
    tracking_info: Optional[str] = None
    created_at: datetime
