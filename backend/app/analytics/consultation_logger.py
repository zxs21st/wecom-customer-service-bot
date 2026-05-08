import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.analytics import ConsultationRecord

logger = logging.getLogger(__name__)


async def log_consultation(
    session: AsyncSession,
    question: str,
    answer: str | None = None,
    intent_type: str | None = None,
    confidence: float | None = None,
    user_id: str | None = None,
    chat_id: str | None = None,
    session_id: str | None = None,
    is_resolved: bool = True,
):
    """记录一次咨询"""
    record = ConsultationRecord(
        id=str(uuid.uuid4()),
        session_id=session_id,
        user_id=user_id,
        chat_id=chat_id,
        intent_type=intent_type,
        question=question,
        answer=answer,
        confidence=confidence,
        is_resolved=is_resolved,
    )
    session.add(record)
    await session.commit()
    logger.info(f"Logged consultation: intent={intent_type}, user={user_id}")
