import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.ai_engine.schemas import AIRequest, AIResponse, IntentType
from app.ai_engine.intent_classifier import classify_intent
from app.ai_engine.response_generator import generate_response
from app.knowledge.vector_search import search_similar
from app.analytics.consultation_logger import log_consultation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/chat", response_model=AIResponse)
async def chat(request: AIRequest, db: AsyncSession = Depends(get_db)):
    """处理 AI 对话请求"""
    # 1. 意图分类
    intent, confidence = await classify_intent(request.message)
    logger.info(f"Intent: {intent} (confidence: {confidence})")

    # 2. 低置信度 → 转人工
    if confidence < 0.5 or intent == IntentType.ESCALATE_TO_HUMAN:
        response = AIResponse(
            intent=intent,
            confidence=confidence,
            reply_text="抱歉，这个问题我暂时无法准确回答。正在为您转接人工客服，请稍等。",
            sources=[],
        )
        await log_consultation(
            db,
            question=request.message,
            answer=response.reply_text,
            intent_type=intent.value,
            confidence=confidence,
            session_id=request.session_id,
            is_resolved=False,
        )
        return response

    # 3. 一般闲聊 → 直接回复
    if intent == IntentType.GENERAL_CHAT:
        response = await generate_response(intent, request.message, [])
        await log_consultation(
            db,
            question=request.message,
            answer=response.reply_text,
            intent_type=intent.value,
            confidence=confidence,
            session_id=request.session_id,
        )
        return response

    # 4. 知识检索 → RAG 回答
    # 搜索相关知识
    results = await search_similar(request.message, top_k=5)
    logger.info(f"Found {len(results)} relevant knowledge pieces from WeKnora")

    # 生成回答
    response = await generate_response(intent, request.message, results, request.chat_history)
    response.confidence = confidence

    # 记录咨询
    await log_consultation(
        db,
        question=request.message,
        answer=response.reply_text,
        intent_type=intent.value,
        confidence=confidence,
        session_id=request.session_id,
        is_resolved=confidence >= 0.5,
    )
    return response


@router.post("/intent")
async def classify(request: AIRequest):
    """仅返回意图分类结果 (调试用)"""
    intent, confidence = await classify_intent(request.message)
    return {"intent": intent.value, "confidence": confidence}
