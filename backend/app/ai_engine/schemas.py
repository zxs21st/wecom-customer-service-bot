from enum import Enum
from typing import Optional
from pydantic import BaseModel


class IntentType(str, Enum):
    PRODUCT_KNOWLEDGE = "product_knowledge"
    CONFIG_QUERY = "config_query"
    INVENTORY_QUERY = "inventory_query"
    PRICE_INQUIRY = "price_inquiry"
    QUOTE_REQUEST = "quote_request"
    AFTER_SALES = "after_sales"
    ORDER_TRACKING = "order_tracking"
    GENERAL_CHAT = "general_chat"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class AIRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    chat_history: list[dict] = []  # 最近对话历史


class IntentResult(BaseModel):
    intent: IntentType
    confidence: float
    reply_text: Optional[str] = None


class AIResponse(BaseModel):
    intent: IntentType
    confidence: float
    reply_text: str
    sources: list[str] = []  # 引用的知识来源
