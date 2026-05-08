import json
from datetime import datetime, timezone
from typing import Optional
from app.config import settings
from app.gateway.schemas import Message, Session
from app.redis_client import redis_client


def _session_key(session_id: str) -> str:
    return f"session:{session_id}"


async def get_session(session_id: str) -> Optional[Session]:
    """获取会话上下文"""
    data = await redis_client.get(_session_key(session_id))
    if not data:
        return None
    session_dict = json.loads(data)
    session_dict["context"] = [Message(**m) for m in session_dict.get("context", [])]
    return Session(**session_dict)


async def create_session(user_id: str, chat_id: str) -> Session:
    """创建新会话"""
    session_id = f"{user_id}:{chat_id}"
    now = datetime.now(timezone.utc)
    session = Session(
        session_id=session_id,
        user_id=user_id,
        chat_id=chat_id,
        context=[],
        created_at=now,
        updated_at=now,
    )
    await _save_session(session)
    return session


async def add_message(user_id: str, chat_id: str) -> Session:
    """添加消息到会话上下文"""
    session_id = f"{user_id}:{chat_id}"
    session = await get_session(session_id)
    if not session:
        session = await create_session(user_id, chat_id)
    session.updated_at = datetime.now(timezone.utc)
    await _save_session(session)
    return session


async def _save_session(session: Session) -> None:
    """保存会话到 Redis"""
    data = session.model_dump(mode="json")
    await redis_client.setex(
        _session_key(session.session_id),
        settings.session_ttl_seconds,
        json.dumps(data, ensure_ascii=False),
    )
