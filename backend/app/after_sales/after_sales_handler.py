import logging
from app.gateway.message_sender import send_text
from app.ai_engine.schemas import IntentType
from app.ai_engine.response_generator import generate_response
from app.knowledge.vector_search import search_similar
from app.db import async_session

logger = logging.getLogger(__name__)


async def handle_after_sales(
    message: str,
    user_id: str,
    chat_id: str,
    chat_history: list[dict] | None = None,
):
    """处理售后意图: RAG 知识问答 + 必要时创建工单"""
    async with async_session() as session:
        # 1. 检索售后政策知识
        results = await search_similar(message, session, top_k=5, category_filter="after_sales")

        # 2. 生成回答
        if results:
            response = await generate_response(IntentType.AFTER_SALES, message, results, chat_history)
            await send_text(to_user=user_id, content=response.reply_text)
            return response.reply_text
        else:
            # 3. 无相关知识 → 创建工单
            from app.after_sales.ticket_service import create_ticket
            ticket = await create_ticket(
                session,
                user_id=user_id,
                chat_id=chat_id,
                issue_type="complaint",
                description=message,
            )
            reply = f"抱歉，这个问题我需要记录并转交人工处理。\n"
            reply += f"工单号: {ticket.ticket_no}\n"
            reply += f"我们将在 24 小时内联系您。"
            await send_text(to_user=user_id, content=reply)
            return reply
