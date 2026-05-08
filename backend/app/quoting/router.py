import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.quoting.schemas import QuoteCreate, QuoteResponse
from app.quoting.quote_service import create_quote, get_quote, accept_quote, update_quote_pdf_url
from app.quoting.pdf_renderer import render_quote_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quotes", tags=["quotes"])


@router.post("/", response_model=QuoteResponse)
async def create(data: QuoteCreate, db: AsyncSession = Depends(get_db)):
    """创建报价单"""
    items = [item.model_dump() for item in data.items]
    quote = await create_quote(
        db,
        customer_name=data.customer_name,
        items=items,
        user_id=data.user_id,
        chat_id=data.chat_id,
        customer_contact=data.customer_contact,
        valid_days=data.valid_days,
    )
    return _to_response(quote)


@router.post("/{quote_id}/generate-pdf")
async def generate_pdf(quote_id: str, db: AsyncSession = Depends(get_db)):
    """生成报价 PDF"""
    quote = await get_quote(db, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    pdf_path = render_quote_pdf(
        quote_no=quote.quote_no,
        customer_name=quote.customer_name,
        items=quote.items,
        total_amount=float(quote.total_amount),
        discount_total=float(quote.discount_total),
        final_amount=float(quote.final_amount),
        valid_until=quote.valid_until.isoformat(),
    )

    await update_quote_pdf_url(db, quote_id, pdf_path)
    return {"pdf_url": pdf_path}


@router.post("/{quote_id}/accept")
async def accept(quote_id: str, db: AsyncSession = Depends(get_db)):
    """接受报价单"""
    quote = await accept_quote(db, quote_id)
    return {"status": "ok", "quote_no": quote.quote_no}


def _to_response(quote) -> QuoteResponse:
    return QuoteResponse(
        id=str(quote.id),
        quote_no=quote.quote_no,
        customer_name=quote.customer_name,
        items=quote.items,
        total_amount=float(quote.total_amount),
        discount_total=float(quote.discount_total),
        final_amount=float(quote.final_amount),
        valid_until=quote.valid_until,
        status=quote.status,
        pdf_url=quote.pdf_url,
    )
