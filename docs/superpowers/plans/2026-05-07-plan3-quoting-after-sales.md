# Plan 3: 报价生成、售后与订单管理 - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 PDF 报价单生成、售后工单管理、机器人自主订单记录。

**Architecture:** 报价数据存储在 PostgreSQL，使用 WeasyPrint 将 HTML 模板渲染为 PDF，售后工单和订单作为独立模块管理，与 AI 引擎通过意图路由连接。

**Tech Stack:** WeasyPrint, FastAPI, PostgreSQL, Jinja2, pytest

**Depends on:** Plan 1 (消息发送、会话管理) + Plan 2 (意图分类、AIResponse)

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/models/quoting.py` | 新建 | Quote + QuoteItem SQLAlchemy 模型 |
| `backend/app/models/after_sales.py` | 新建 | BotOrder + AfterSalesTicket 模型 |
| `backend/app/quoting/schemas.py` | 新建 | 报价请求/响应模型 |
| `backend/app/quoting/quote_service.py` | 新建 | 报价 CRUD、价格计算 |
| `backend/app/quoting/pdf_renderer.py` | 新建 | WeasyPrint HTML → PDF |
| `backend/app/quoting/quote_handler.py` | 新建 | 报价意图处理器 |
| `backend/app/quoting/router.py` | 新建 | 报价 API 路由 |
| `backend/app/quoting/templates/quote_standard.html` | 新建 | 标准报价 PDF 模板 |
| `backend/app/after_sales/schemas.py` | 新建 | 售后请求/响应模型 |
| `backend/app/after_sales/ticket_service.py` | 新建 | 工单 CRUD、状态流转 |
| `backend/app/after_sales/order_service.py` | 新建 | 订单 CRUD、报价转订单 |
| `backend/app/after_sales/after_sales_handler.py` | 新建 | 售后意图处理器 |
| `backend/app/after_sales/router.py` | 新建 | 售后 API 路由 |
| `backend/migrations/versions/002_quoting_tables.py` | 新建 | 报价表迁移 |
| `backend/migrations/versions/003_after_sales_tables.py` | 新建 | 售后/订单表迁移 |
| `backend/tests/test_quote_service.py` | 新建 | 报价服务测试 |
| `backend/tests/test_pdf_renderer.py` | 新建 | PDF 生成测试 |
| `backend/tests/test_ticket_service.py` | 新建 | 工单生命周期测试 |
| `backend/tests/test_order_service.py` | 新建 | 订单服务测试 |

---

### Task 1: 报价数据模型与迁移

**Files:**
- Create: `backend/app/models/quoting.py`
- Create: `backend/migrations/versions/002_quoting_tables.py`

- [ ] **Step 1: 创建报价模型**

`backend/app/models/quoting.py`:
```python
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base


class QuoteStatus:
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Quote(Base):
    __tablename__ = "quote"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    quote_no: Mapped[str] = mapped_column(String(50), unique=True)
    customer_name: Mapped[str] = mapped_column(String(100))
    customer_contact: Mapped[Optional[str]] = mapped_column(String(100))
    user_id: Mapped[Optional[str]] = mapped_column(String(100))  # 企微用户 ID
    chat_id: Mapped[Optional[str]] = mapped_column(String(100))  # 群聊 ID
    items: Mapped[list[dict]] = mapped_column(JSONB)  # 报价明细
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    final_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    valid_until: Mapped[date]
    status: Mapped[str] = mapped_column(String(20), default=QuoteStatus.DRAFT)
    prepared_by: Mapped[Optional[str]] = mapped_column(String(100))
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    order: Mapped[Optional["BotOrder"]] = relationship(back_populates="quote")


class QuoteItem:
    """Pydantic-like dict structure stored in JSONB"""
    # {
    #     "sku": str,
    #     "product_name": str,
    #     "specification": str,
    #     "unit_price": float,
    #     "quantity": int,
    #     "discount": float,
    #     "subtotal": float,
    # }
```

更新 `backend/app/models/__init__.py` 添加:
```python
from app.models import quoting  # noqa: F401
```

- [ ] **Step 2: 创建报价表迁移**

`backend/migrations/versions/002_quoting_tables.py`:
```python
"""create quote table

Revision ID: 002
Revises: 001
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "quote",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("quote_no", sa.String(50), unique=True, nullable=False),
        sa.Column("customer_name", sa.String(100), nullable=False),
        sa.Column("customer_contact", sa.String(100), nullable=True),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("chat_id", sa.String(100), nullable=True),
        sa.Column("items", JSONB, nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_total", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("final_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("valid_until", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'draft'"),
        sa.Column("prepared_by", sa.String(100), nullable=True),
        sa.Column("pdf_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table("quote")
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/quoting.py backend/app/models/__init__.py backend/migrations/versions/002_quoting_tables.py
git commit -m "feat: add Quote model and Alembic migration"
```

---

### Task 2: 报价服务与 PDF 生成

**Files:**
- Create: `backend/app/quoting/schemas.py`
- Create: `backend/app/quoting/quote_service.py`
- Create: `backend/app/quoting/pdf_renderer.py`
- Create: `backend/app/quoting/templates/quote_standard.html`

- [ ] **Step 1: 定义报价 Schema**

`backend/app/quoting/schemas.py`:
```python
from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, UUID4


class QuoteItemInput(BaseModel):
    sku: str
    product_name: str
    specification: str = ""
    unit_price: float
    quantity: int = 1
    discount: float = 0.0


class QuoteCreate(BaseModel):
    customer_name: str
    customer_contact: Optional[str] = None
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    items: list[QuoteItemInput]
    valid_days: int = 30  # 报价有效期天数


class QuoteResponse(BaseModel):
    id: UUID4
    quote_no: str
    customer_name: str
    items: list[dict]
    total_amount: float
    discount_total: float
    final_amount: float
    valid_until: date
    status: str
    pdf_url: Optional[str] = None
```

- [ ] **Step 2: 实现报价服务**

`backend/app/quoting/quote_service.py`:
```python
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.quoting import Quote, QuoteStatus


def _generate_quote_no() -> str:
    """生成报价单号: Q-YYYYMMDD-XXXX"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = str(uuid.uuid4())[:4].upper()
    return f"Q-{today}-{suffix}"


def _calculate_items(items: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
    """计算总价、折扣、最终金额"""
    total = Decimal("0")
    discount_total = Decimal("0")
    for item in items:
        unit_price = Decimal(str(item["unit_price"]))
        quantity = item["quantity"]
        discount = Decimal(str(item.get("discount", 0)))
        subtotal = unit_price * quantity * (1 - discount)
        item["subtotal"] = float(subtotal)
        total += unit_price * quantity
        discount_total += unit_price * quantity * discount
    final_amount = total - discount_total
    return total, discount_total, final_amount


async def create_quote(
    session: AsyncSession,
    customer_name: str,
    items: list[dict],
    user_id: str | None = None,
    chat_id: str | None = None,
    customer_contact: str | None = None,
    valid_days: int = 30,
) -> Quote:
    """创建报价单"""
    total, discount_total, final_amount = _calculate_items(items)
    valid_until = datetime.now(timezone.utc) + timedelta(days=valid_days)

    quote = Quote(
        id=uuid.uuid4(),
        quote_no=_generate_quote_no(),
        customer_name=customer_name,
        customer_contact=customer_contact,
        user_id=user_id,
        chat_id=chat_id,
        items=items,
        total_amount=total,
        discount_total=discount_total,
        final_amount=final_amount,
        valid_until=valid_until.date(),
        status=QuoteStatus.DRAFT,
        prepared_by="bot",
    )
    session.add(quote)
    await session.commit()
    await session.refresh(quote)
    return quote


async def get_quote(session: AsyncSession, quote_id: str) -> Quote | None:
    """获取报价单"""
    return await session.get(Quote, quote_id)


async def accept_quote(session: AsyncSession, quote_id: str) -> Quote:
    """接受报价单"""
    quote = await session.get(Quote, quote_id)
    if not quote:
        raise ValueError(f"Quote {quote_id} not found")
    quote.status = QuoteStatus.ACCEPTED
    await session.commit()
    await session.refresh(quote)
    return quote


async def update_quote_pdf_url(session: AsyncSession, quote_id: str, pdf_url: str) -> Quote:
    """更新报价 PDF URL"""
    quote = await session.get(Quote, quote_id)
    if quote:
        quote.pdf_url = pdf_url
        await session.commit()
        await session.refresh(quote)
    return quote
```

- [ ] **Step 3: 实现 PDF 渲染**

`backend/app/quoting/pdf_renderer.py`:
```python
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

logger = logging.getLogger(__name__)

# PDF 输出目录
PDF_DIR = Path(__file__).parent / "output"
PDF_DIR.mkdir(exist_ok=True)

# 模板目录
TEMPLATE_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def render_quote_pdf(
    quote_no: str,
    customer_name: str,
    items: list[dict],
    total_amount: float,
    discount_total: float,
    final_amount: float,
    valid_until: str,
    template_name: str = "quote_standard.html",
) -> str:
    """将报价数据渲染为 PDF 文件，返回文件路径"""
    template = jinja_env.get_template(template_name)

    html_content = template.render(
        quote_no=quote_no,
        customer_name=customer_name,
        items=items,
        total_amount=total_amount,
        discount_total=discount_total,
        final_amount=final_amount,
        valid_until=valid_until,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
    )

    # 生成 PDF 文件
    pdf_filename = f"{quote_no}.pdf"
    pdf_path = PDF_DIR / pdf_filename
    HTML(string=html_content).write_pdf(str(pdf_path))

    logger.info(f"PDF quote generated: {pdf_path}")
    return str(pdf_path)
```

- [ ] **Step 4: 创建报价 HTML 模板**

`backend/app/quoting/templates/quote_standard.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: "Microsoft YaHei", sans-serif; padding: 40px; color: #333; }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #1890ff; padding-bottom: 20px; }
        .header h1 { color: #1890ff; margin: 0; }
        .info { margin-bottom: 20px; }
        .info p { margin: 5px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th { background: #1890ff; color: white; padding: 10px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #eee; }
        .total { text-align: right; font-size: 18px; margin-top: 20px; }
        .total strong { color: #1890ff; }
        .terms { margin-top: 40px; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>报价单</h1>
        <p>单号: {{ quote_no }} | 生成时间: {{ generated_at }}</p>
    </div>

    <div class="info">
        <p><strong>客户:</strong> {{ customer_name }}</p>
        <p><strong>报价有效期:</strong> {{ valid_until }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>产品名称</th>
                <th>规格</th>
                <th>单价</th>
                <th>数量</th>
                <th>折扣</th>
                <th>小计</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.product_name }}</td>
                <td>{{ item.specification }}</td>
                <td>¥{{ "%.2f"|format(item.unit_price) }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ "%.0f"|format(item.discount * 100) }}%</td>
                <td>¥{{ "%.2f"|format(item.subtotal) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="total">
        <p>原价: ¥{{ "%.2f"|format(total_amount) }}</p>
        {% if discount_total > 0 %}
        <p>优惠: -¥{{ "%.2f"|format(discount_total) }}</p>
        {% endif %}
        <p><strong>合计: ¥{{ "%.2f"|format(final_amount) }}</strong></p>
    </div>

    <div class="terms">
        <p>条款说明:</p>
        <p>1. 本报价有效期至 {{ valid_until }}</p>
        <p>2. 付款方式: 合同签订后 30 日内</p>
        <p>3. 交货期: 收到订单后 7-15 个工作日</p>
    </div>
</body>
</html>
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/quoting/
git commit -m "feat: implement quote service and WeasyPrint PDF generation with template"
```

---

### Task 3: 报价路由与意图处理器

**Files:**
- Create: `backend/app/quoting/router.py`
- Create: `backend/app/quoting/quote_handler.py`

- [ ] **Step 1: 创建报价路由**

`backend/app/quoting/router.py`:
```python
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
        id=quote.id,
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
```

- [ ] **Step 2: 创建报价意图处理器**

`backend/app/quoting/quote_handler.py`:
```python
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
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/quoting/router.py backend/app/quoting/quote_handler.py
git commit -m "feat: add quote API endpoints and intent handler for quote generation workflow"
```

---

### Task 4: 售后工单与订单模型

**Files:**
- Create: `backend/app/models/after_sales.py`
- Create: `backend/migrations/versions/003_after_sales_tables.py`

- [ ] **Step 1: 创建售后/订单模型**

`backend/app/models/after_sales.py`:
```python
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base


class BotOrder(Base):
    __tablename__ = "bot_order"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    order_no: Mapped[str] = mapped_column(String(50), unique=True)
    quote_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("quote.id"), nullable=True)
    user_id: Mapped[str] = mapped_column(String(100))
    chat_id: Mapped[str] = mapped_column(String(100))
    customer_name: Mapped[str] = mapped_column(String(100))
    items: Mapped[dict] = mapped_column(JSONB)
    total_amount: Mapped[float] = mapped_column(prec=10, scale=2)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/confirmed/shipped/completed
    tracking_info: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    quote: Mapped[Optional["Quote"]] = relationship(back_populates="order")
    tickets: Mapped[list["AfterSalesTicket"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class AfterSalesTicket(Base):
    __tablename__ = "after_sales_ticket"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    ticket_no: Mapped[str] = mapped_column(String(50), unique=True)
    user_id: Mapped[str] = mapped_column(String(100))
    chat_id: Mapped[str] = mapped_column(String(100))
    order_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("bot_order.id"), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(50))  # return/exchange/repair/complaint
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open/in_progress/resolved/closed
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    order: Mapped[Optional["BotOrder"]] = relationship(back_populates="tickets")
```

更新 `backend/app/models/__init__.py` 添加:
```python
from app.models import after_sales  # noqa: F401
```

- [ ] **Step 2: 创建售后/订单表迁移**

`backend/migrations/versions/003_after_sales_tables.py`:
```python
"""create bot_order and after_sales_ticket tables

Revision ID: 003
Revises: 002
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bot_order",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("order_no", sa.String(50), unique=True, nullable=False),
        sa.Column("quote_id", UUID(as_uuid=True), sa.ForeignKey("quote.id"), nullable=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("chat_id", sa.String(100), nullable=False),
        sa.Column("customer_name", sa.String(100), nullable=False),
        sa.Column("items", JSONB, nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'pending'"),
        sa.Column("tracking_info", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "after_sales_ticket",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("ticket_no", sa.String(50), unique=True, nullable=False),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("chat_id", sa.String(100), nullable=False),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("bot_order.id"), nullable=True),
        sa.Column("issue_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'open'"),
        sa.Column("assigned_to", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table("after_sales_ticket")
    op.drop_table("bot_order")
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/after_sales.py backend/app/models/__init__.py backend/migrations/versions/003_after_sales_tables.py
git commit -m "feat: add BotOrder and AfterSalesTicket models with migration"
```

---

### Task 5: 工单服务与订单服务

**Files:**
- Create: `backend/app/after_sales/schemas.py`
- Create: `backend/app/after_sales/ticket_service.py`
- Create: `backend/app/after_sales/order_service.py`

- [ ] **Step 1: 定义售后 Schema**

`backend/app/after_sales/schemas.py`:
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, UUID4


class TicketCreate(BaseModel):
    user_id: str
    chat_id: str
    order_id: Optional[UUID4] = None
    issue_type: str  # return/exchange/repair/complaint
    description: str


class TicketResponse(BaseModel):
    id: UUID4
    ticket_no: str
    issue_type: str
    description: str
    status: str
    assigned_to: Optional[str] = None
    created_at: datetime


class OrderResponse(BaseModel):
    id: UUID4
    order_no: str
    customer_name: str
    items: list[dict]
    total_amount: float
    status: str
    tracking_info: Optional[str] = None
    created_at: datetime
```

- [ ] **Step 2: 工单服务**

`backend/app/after_sales/ticket_service.py`:
```python
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.after_sales import AfterSalesTicket


def _generate_ticket_no() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = str(uuid.uuid4())[:4].upper()
    return f"AS-{today}-{suffix}"


async def create_ticket(
    session: AsyncSession,
    user_id: str,
    chat_id: str,
    issue_type: str,
    description: str,
    order_id: str | None = None,
) -> AfterSalesTicket:
    """创建售后工单"""
    ticket = AfterSalesTicket(
        id=uuid.uuid4(),
        ticket_no=_generate_ticket_no(),
        user_id=user_id,
        chat_id=chat_id,
        order_id=order_id,
        issue_type=issue_type,
        description=description,
        status="open",
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def update_ticket_status(
    session: AsyncSession,
    ticket_id: str,
    status: str,
    assigned_to: str | None = None,
) -> AfterSalesTicket:
    """更新工单状态"""
    ticket = await session.get(AfterSalesTicket, ticket_id)
    if not ticket:
        raise ValueError(f"Ticket {ticket_id} not found")
    ticket.status = status
    if assigned_to:
        ticket.assigned_to = assigned_to
    await session.commit()
    await session.refresh(ticket)
    return ticket
```

- [ ] **Step 3: 订单服务**

`backend/app/after_sales/order_service.py`:
```python
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.after_sales import BotOrder


def _generate_order_no() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = str(uuid.uuid4())[:4].upper()
    return f"BOT-{today}-{suffix}"


async def create_order_from_quote(
    session: AsyncSession,
    quote_id: str,
    user_id: str,
    chat_id: str,
    customer_name: str,
    items: list[dict],
    total_amount: float,
) -> BotOrder:
    """将报价转为订单"""
    order = BotOrder(
        id=uuid.uuid4(),
        order_no=_generate_order_no(),
        quote_id=quote_id,
        user_id=user_id,
        chat_id=chat_id,
        customer_name=customer_name,
        items=items,
        total_amount=total_amount,
        status="pending",
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_order(session: AsyncSession, order_id: str) -> BotOrder | None:
    """获取订单"""
    return await session.get(BotOrder, order_id)


async def update_order_status(
    session: AsyncSession,
    order_id: str,
    status: str,
    tracking_info: str | None = None,
) -> BotOrder:
    """更新订单状态"""
    order = await session.get(BotOrder, order_id)
    if not order:
        raise ValueError(f"Order {order_id} not found")
    order.status = status
    if tracking_info:
        order.tracking_info = tracking_info
    await session.commit()
    await session.refresh(order)
    return order
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/after_sales/schemas.py backend/app/after_sales/ticket_service.py backend/app/after_sales/order_service.py
git commit -m "feat: implement ticket service and order service with quote-to-order conversion"
```

---

### Task 6: 售后路由与意图处理器

**Files:**
- Create: `backend/app/after_sales/router.py`
- Create: `backend/app/after_sales/after_sales_handler.py`

- [ ] **Step 1: 创建售后路由**

`backend/app/after_sales/router.py`:
```python
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.after_sales.schemas import TicketCreate, TicketResponse, OrderResponse
from app.after_sales.ticket_service import create_ticket, update_ticket_status
from app.after_sales.order_service import get_order

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/after-sales", tags=["after-sales"])


@router.post("/tickets", response_model=TicketResponse)
async def create_ticket_endpoint(data: TicketCreate, db: AsyncSession = Depends(get_db)):
    """创建售后工单"""
    ticket = await create_ticket(
        db,
        user_id=data.user_id,
        chat_id=data.chat_id,
        issue_type=data.issue_type,
        description=data.description,
        order_id=str(data.order_id) if data.order_id else None,
    )
    return TicketResponse(
        id=ticket.id,
        ticket_no=ticket.ticket_no,
        issue_type=ticket.issue_type,
        description=ticket.description,
        status=ticket.status,
        assigned_to=ticket.assigned_to,
        created_at=ticket.created_at,
    )


@router.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, status: str, assigned_to: str | None = None, db: AsyncSession = Depends(get_db)):
    """更新工单状态"""
    ticket = await update_ticket_status(db, ticket_id, status, assigned_to)
    return {"status": "ok", "ticket_no": ticket.ticket_no}


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_endpoint(order_id: str, db: AsyncSession = Depends(get_db)):
    """获取订单详情"""
    order = await get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(
        id=order.id,
        order_no=order.order_no,
        customer_name=order.customer_name,
        items=order.items,
        total_amount=float(order.total_amount),
        status=order.status,
        tracking_info=order.tracking_info,
        created_at=order.created_at,
    )
```

- [ ] **Step 2: 创建售后意图处理器**

`backend/app/after_sales/after_sales_handler.py`:
```python
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
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/after_sales/router.py backend/app/after_sales/after_sales_handler.py
git commit -m "feat: add after-sales API and intent handler with RAG QA + ticket fallback"
```

---

### Task 7: 测试

**Files:**
- Create: `backend/tests/test_quote_service.py`
- Create: `backend/tests/test_pdf_renderer.py`
- Create: `backend/tests/test_ticket_service.py`
- Create: `backend/tests/test_order_service.py`

- [ ] **Step 1: 报价服务测试**

`backend/tests/test_quote_service.py`:
```python
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from app.quoting.quote_service import create_quote, _calculate_items


def test_calculate_items_with_discount():
    items = [
        {"sku": "A1", "product_name": "产品A", "unit_price": 100.0, "quantity": 2, "discount": 0.1},
    ]
    total, discount_total, final = _calculate_items(items)
    assert total == Decimal("200.0")
    assert discount_total == Decimal("20.0")
    assert final == Decimal("180.0")


@pytest.mark.asyncio
async def test_create_quote():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    items = [{"sku": "A1", "product_name": "产品A", "unit_price": 100.0, "quantity": 1, "discount": 0, "subtotal": 100.0}]

    quote = await create_quote(
        mock_session,
        customer_name="测试客户",
        items=items,
    )

    assert quote.customer_name == "测试客户"
    assert quote.status == "draft"
    mock_session.add.assert_called_once()
```

- [ ] **Step 2: PDF 渲染测试**

`backend/tests/test_pdf_renderer.py`:
```python
import pytest
from unittest.mock import patch
from app.quoting.pdf_renderer import render_quote_pdf


def test_render_quote_pdf_creates_file():
    with patch("app.quoting.pdf_renderer.HTML") as mock_html:
        mock_instance = type("MockHTML", (), {"write_pdf": lambda self, path: None})()
        mock_html.return_value = mock_instance

        pdf_path = render_quote_pdf(
            quote_no="Q-TEST-001",
            customer_name="测试客户",
            items=[{"product_name": "产品A", "specification": "规格", "unit_price": 100.0, "quantity": 1, "discount": 0, "subtotal": 100.0}],
            total_amount=100.0,
            discount_total=0.0,
            final_amount=100.0,
            valid_until="2026-06-07",
        )

        mock_html.assert_called_once()
        assert "Q-TEST-001" in pdf_path
```

- [ ] **Step 3: 工单服务测试**

`backend/tests/test_ticket_service.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.after_sales.ticket_service import create_ticket, update_ticket_status


@pytest.mark.asyncio
async def test_create_ticket():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    ticket = await create_ticket(
        mock_session,
        user_id="user1",
        chat_id="chat1",
        issue_type="return",
        description="产品质量问题",
    )

    assert ticket.user_id == "user1"
    assert ticket.status == "open"
    assert ticket.ticket_no.startswith("AS-")
```

- [ ] **Step 4: 订单服务测试**

`backend/tests/test_order_service.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.after_sales.order_service import create_order_from_quote


@pytest.mark.asyncio
async def test_create_order_from_quote():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    order = await create_order_from_quote(
        mock_session,
        quote_id="test-quote-id",
        user_id="user1",
        chat_id="chat1",
        customer_name="测试客户",
        items=[{"sku": "A1", "name": "产品A"}],
        total_amount=1000.0,
    )

    assert order.customer_name == "测试客户"
    assert order.status == "pending"
    assert order.order_no.startswith("BOT-")
```

- [ ] **Step 5: 运行全部测试**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot/backend
python -m pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/tests/test_quote_service.py backend/tests/test_pdf_renderer.py backend/tests/test_ticket_service.py backend/tests/test_order_service.py
git commit -m "test: add tests for quote service, PDF renderer, ticket service, order service"
```

---

## Plan 3 完成标准

- [x] 创建报价单 → 自动计算价格
- [x] 生成 PDF 报价单 → 可下载
- [x] 售后工单创建 → 状态可追踪
- [x] 报价转订单 → 订单状态管理
- [x] 所有单元测试通过

## Plan 4 前置接口

Plan 3 为 Plan 4 提供以下数据模型：
- `Quote` 模型 — 报价统计、转化率分析
- `BotOrder` 模型 — 订单量统计
- `AfterSalesTicket` 模型 — 工单解决率统计
