from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class QuoteItemInput(BaseModel):
    sku: str
    product_name: str
    specification: str = ""
    unit_price: float
    quantity: int = 1
    discount: float = 0.0


class QuoteCreate(BaseModel):
    customer_name: str
    customer_contact: Optional[str] = None
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    items: list[QuoteItemInput]
    valid_days: int = 30  # 报价有效期天数


class QuoteResponse(BaseModel):
    id: str
    quote_no: str
    customer_name: str
    items: list[dict]
    total_amount: float
    discount_total: float
    final_amount: float
    valid_until: date
    status: str
    pdf_url: Optional[str] = None
