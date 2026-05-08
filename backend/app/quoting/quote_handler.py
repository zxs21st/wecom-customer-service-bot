import logging
from app.gateway.message_sender import send_text, upload_media
from app.quoting.quote_service import create_quote, update_quote_pdf_url
from app.quoting.pdf_renderer import render_quote_pdf
from app.db import async_session

logger = logging.getLogger(__name__)


async def handle_quote_request(
    message: str,
    user_id: str,
    chat_id: str,
    items: list[dict],
    customer_name: str = "客户",
):
    """处理报价请求意图: 创建报价 → 生成 PDF → 发送"""
    async with async_session() as session:
        # 1. 创建报价单
        quote = await create_quote(
            session,
            customer_name=customer_name,
            items=items,
            user_id=user_id,
            chat_id=chat_id,
        )

        # 2. 生成 PDF
        pdf_path = render_quote_pdf(
            quote_no=quote.quote_no,
            customer_name=quote.customer_name,
            items=quote.items,
            total_amount=float(quote.total_amount),
            discount_total=float(quote.discount_total),
            final_amount=float(quote.final_amount),
            valid_until=quote.valid_until.isoformat(),
        )

        await update_quote_pdf_url(session, str(quote.id), pdf_path)

        # 3. 发送文本通知
        await send_text(
            to_user=user_id,
            content=f"您好 {customer_name}，已为您生成报价单 {quote.quote_no}，有效期到 {quote.valid_until}。\n"
                    f"合计金额: ¥{quote.final_amount:.2f}\n"
                    f"PDF 文件稍后发送。",
        )

        # 4. 上传并发送 PDF
        try:
            media_id = await upload_media(pdf_path, "file")
            await send_text(user_id, f"报价单 {quote.quote_no} 已发送，请查收。")
        except Exception as e:
            logger.error(f"Failed to send PDF: {e}")
            await send_text(user_id, "抱歉，PDF 文件发送失败，请联系人工客服获取。")

        return f"报价单 {quote.quote_no} 已生成，金额 ¥{quote.final_amount:.2f}"
