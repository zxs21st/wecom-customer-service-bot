from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.analytics import ConsultationRecord
from app.analytics.schemas import DashboardStats, DailyStat


async def get_dashboard_stats(session: AsyncSession) -> DashboardStats:
    """获取仪表盘统计数据"""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # 今日查询
    today_result = await session.execute(
        select(func.count(ConsultationRecord.id)).where(
            ConsultationRecord.created_at >= today_start
        )
    )
    today_queries = today_result.scalar() or 0

    # 今日已解决
    today_resolved_result = await session.execute(
        select(func.count(ConsultationRecord.id)).where(
            ConsultationRecord.created_at >= today_start,
            ConsultationRecord.is_resolved.is_(True),
        )
    )
    today_resolved = today_resolved_result.scalar() or 0

    # 总查询
    total_result = await session.execute(select(func.count(ConsultationRecord.id)))
    total_queries = total_result.scalar() or 0

    # 平均置信度
    conf_result = await session.execute(select(func.avg(ConsultationRecord.confidence)))
    avg_confidence = float((conf_result.scalar() or 0))

    # 未解决数
    unresolved_result = await session.execute(
        select(func.count(ConsultationRecord.id)).where(ConsultationRecord.is_resolved.is_(False))
    )
    unresolved_count = unresolved_result.scalar() or 0

    # 热门意图
    intent_result = await session.execute(
        select(ConsultationRecord.intent_type, func.count(ConsultationRecord.id))
        .group_by(ConsultationRecord.intent_type)
        .order_by(func.count(ConsultationRecord.id).desc())
        .limit(5)
    )
    top_intents = [{"intent": row[0] or "unknown", "count": row[1]} for row in intent_result.fetchall()]

    return DashboardStats(
        today_queries=today_queries,
        today_resolved=today_resolved,
        total_queries=total_queries,
        avg_confidence=round(avg_confidence, 2),
        top_intents=top_intents,
        unresolved_count=unresolved_count,
    )


async def get_daily_stats(session: AsyncSession, days: int = 30) -> list[DailyStat]:
    """获取每日统计趋势"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await session.execute(
        select(
            func.date(ConsultationRecord.created_at).label("date"),
            func.count(ConsultationRecord.id).label("total_queries"),
            func.count(ConsultationRecord.id).filter(ConsultationRecord.is_resolved.is_(True)).label("resolved"),
            func.avg(ConsultationRecord.confidence).label("avg_confidence"),
        )
        .where(ConsultationRecord.created_at >= cutoff)
        .group_by(func.date(ConsultationRecord.created_at))
        .order_by(func.date(ConsultationRecord.created_at))
    )
    return [
        DailyStat(
            date=row[0],
            total_queries=row[1],
            resolved_queries=row[2],
            avg_confidence=round(float(row[3] or 0), 2),
        )
        for row in result.fetchall()
    ]
