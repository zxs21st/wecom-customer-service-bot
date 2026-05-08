import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.analytics.schemas import DashboardStats, DailyStat, ConsultationRecordResponse
from app.analytics.stats_service import get_dashboard_stats, get_daily_stats
from app.analytics.consultation_logger import log_consultation
from app.models.analytics import ConsultationRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(db: AsyncSession = Depends(get_db)):
    """获取仪表盘统计"""
    return await get_dashboard_stats(db)


@router.get("/daily", response_model=list[DailyStat])
async def daily_stats(days: int = 30, db: AsyncSession = Depends(get_db)):
    """获取每日统计趋势"""
    return await get_daily_stats(db, days=days)


@router.get("/records", response_model=list[ConsultationRecordResponse])
async def list_records(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """查询咨询记录列表"""
    result = await db.execute(
        select(ConsultationRecord)
        .order_by(ConsultationRecord.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()
    return [
        ConsultationRecordResponse(
            id=str(r.id),
            session_id=r.session_id,
            user_id=r.user_id,
            intent_type=r.intent_type,
            question=r.question,
            answer=r.answer,
            confidence=r.confidence,
            is_resolved=r.is_resolved,
            created_at=r.created_at.isoformat(),
        )
        for r in records
    ]
