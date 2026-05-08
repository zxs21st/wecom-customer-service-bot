from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    LINK = "link"


class Message(BaseModel):
    msg_id: str
    from_user: str
    chat_id: str
    msg_type: MessageType
    content: str
    timestamp: datetime


class Session(BaseModel):
    session_id: str
    user_id: str
    chat_id: str
    context: list[Message] = []
    created_at: datetime
    updated_at: datetime


class WeChatCallback(BaseModel):
    msg_signature: str
    timestamp: str
    nonce: str
    echostr: Optional[str] = None
