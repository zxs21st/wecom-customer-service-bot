# Plan 5: 进销存对接与销售指导引擎 (DEFERRED) - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对接开龙进销存 SQL Server 数据库，实现实时库存/价格查询，结合销售指导清单做智能推荐。

**Architecture:** 通过 pyodbc 直连 SQL Server (只读)，Redis 缓存高频查询，定义 `InventoryProvider` 接口，先用 Mock 实现开发，获取实际表结构后替换。

**Tech Stack:** pyodbc, Microsoft ODBC Driver 18, Redis, FastAPI, pytest

**Depends on:** Plan 1 (基础架构) + Plan 2 (AI 引擎) + Plan 3 (报价服务)

**Blocked on:** 开龙进销存实际表结构

---

## 前置准备

在开始此 Plan 之前，需要完成：
1. 获取开龙进销存的表结构文档 (联系厂商或使用 SSMS 查看)
2. 确认网络连通性 (应用服务器 → SQL Server 1433 端口)
3. 创建只读账号 `wecom_reader`

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/inventory/provider.py` | 新建 | InventoryProvider 接口定义 + Mock 实现 |
| `backend/app/inventory/sql_server.py` | 新建 | SQL Server 连接池 + pyodbc 查询封装 |
| `backend/app/inventory/inventory_service.py` | 新建 | 库存查询业务逻辑 |
| `backend/app/inventory/cache_layer.py` | 新建 | Redis 缓存层 |
| `backend/app/inventory/inventory_handler.py` | 新建 | 库存查询意图处理器 |
| `backend/app/inventory/router.py` | 新建 | 库存查询 API 路由 |
| `backend/app/inventory/schemas.py` | 新建 | 库存/价格数据模型 |
| `backend/app/sales/guidance_service.py` | 新建 | 销售指导 CRUD |
| `backend/app/sales/recommendation_engine.py` | 新建 | 推荐算法 |
| `backend/app/sales/sales_handler.py` | 新建 | 销售推荐意图处理器 |
| `backend/app/sales/router.py` | 新建 | 销售指导 API 路由 |
| `backend/app/sales/schemas.py` | 新建 | 销售指导数据模型 |
| `backend/app/models/sales.py` | 新建 | 销售指导 SQLAlchemy 模型 |
| `backend/migrations/versions/006_sales_guidance_tables.py` | 新建 | 销售指导表迁移 |
| `backend/tests/test_inventory_service.py` | 新建 | 库存服务测试 |
| `backend/tests/test_cache_layer.py` | 新建 | 缓存层测试 |
| `backend/tests/test_recommendation_engine.py` | 新建 | 推荐引擎测试 |

---

### Task 1: InventoryProvider 接口与 Mock 实现

**Files:**
- Create: `backend/app/inventory/schemas.py`
- Create: `backend/app/inventory/provider.py`

- [ ] **Step 1: 定义数据模型**

`backend/app/inventory/schemas.py`:
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class StockInfo(BaseModel):
    sku: str
    product_name: str
    available_qty: float
    warehouse_location: str = ""
    last_updated: Optional[datetime] = None


class PriceInfo(BaseModel):
    sku: str
    standard_price: float
    tier_prices: list[tuple[int, float]] = []  # (min_qty, price)
    promo_price: Optional[float] = None
    currency: str = "CNY"


class LeadTimeInfo(BaseModel):
    sku: str
    lead_time_days: int
    available: bool = True
    next_arrival_date: Optional[str] = None


class ProductInfo(BaseModel):
    sku: str
    name: str
    category: str = ""
    specifications: dict = {}
    image_url: Optional[str] = None
```

- [ ] **Step 2: 定义 Provider 接口**

`backend/app/inventory/provider.py`:
```python
from abc import ABC, abstractmethod
from app.inventory.schemas import StockInfo, PriceInfo, LeadTimeInfo, ProductInfo


class InventoryProvider(ABC):
    """进销存数据提供者接口"""

    @abstractmethod
    async def get_stock(self, sku: str) -> StockInfo | None:
        pass

    @abstractmethod
    async def get_price(self, sku: str, quantity: int = 1) -> PriceInfo | None:
        pass

    @abstractmethod
    async def get_lead_time(self, sku: str) -> LeadTimeInfo | None:
        pass

    @abstractmethod
    async def search_products(self, keyword: str, limit: int = 10) -> list[ProductInfo]:
        pass


class MockInventoryProvider(InventoryProvider):
    """Mock 实现，用于开发和测试"""

    _MOCK_DATA = {
        "SKU001": {
            "name": "产品 A",
            "category": "电子产品",
            "stock": 100,
            "price": 299.0,
            "lead_time": 3,
        },
        "SKU002": {
            "name": "产品 B",
            "category": "电子产品",
            "stock": 0,
            "price": 599.0,
            "lead_time": 15,
        },
        "SKU003": {
            "name": "配件 C",
            "category": "配件",
            "stock": 500,
            "price": 29.9,
            "lead_time": 1,
        },
    }

    async def get_stock(self, sku: str) -> StockInfo | None:
        data = self._MOCK_DATA.get(sku)
        if not data:
            return None
        return StockInfo(
            sku=sku,
            product_name=data["name"],
            available_qty=data["stock"],
        )

    async def get_price(self, sku: str, quantity: int = 1) -> PriceInfo | None:
        data = self._MOCK_DATA.get(sku)
        if not data:
            return None
        return PriceInfo(
            sku=sku,
            standard_price=data["price"],
        )

    async def get_lead_time(self, sku: str) -> LeadTimeInfo | None:
        data = self._MOCK_DATA.get(sku)
        if not data:
            return None
        return LeadTimeInfo(
            sku=sku,
            lead_time_days=data["lead_time"],
            available=data["stock"] > 0,
        )

    async def search_products(self, keyword: str, limit: int = 10) -> list[ProductInfo]:
        results = []
        for sku, data in self._MOCK_DATA.items():
            if keyword.lower() in sku.lower() or keyword.lower() in data["name"].lower():
                results.append(ProductInfo(
                    sku=sku,
                    name=data["name"],
                    category=data["category"],
                ))
        return results[:limit]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/inventory/schemas.py backend/app/inventory/provider.py
git commit -m "feat: define InventoryProvider interface with Mock implementation"
```

---

### Task 2: SQL Server 连接层

**Files:**
- Create: `backend/app/inventory/sql_server.py`
- Create: `backend/Dockerfile` (更新，添加 ODBC 驱动)

- [ ] **Step 1: 实现 SQL Server 连接**

`backend/app/inventory/sql_server.py`:
```python
import logging
import pyodbc
from contextlib import contextmanager
from app.config import settings

logger = logging.getLogger(__name__)


def _build_connection_string() -> str:
    """构建 SQL Server 连接字符串"""
    return (
        f"DRIVER={{{settings.inventory_db_driver}}};"
        f"SERVER={settings.inventory_db_server};"
        f"DATABASE={settings.inventory_db_name};"
        f"UID={settings.inventory_db_user};"
        f"PWD={settings.inventory_db_password};"
        f"Encrypt={settings.inventory_db_encrypt};"
        f"TrustServerCertificate={settings.inventory_db_trust_cert};"
    )


@contextmanager
def get_connection():
    """获取 SQL Server 连接 (上下文管理器)"""
    conn = None
    try:
        conn = pyodbc.connect(_build_connection_string(), timeout=5)
        yield conn
    except pyodbc.Error as e:
        logger.error(f"SQL Server connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def execute_query(query: str, params: tuple = ()) -> list[dict]:
    """执行查询，返回字典列表"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
```

- [ ] **Step 2: 更新 Dockerfile 添加 ODBC 驱动**

修改 `backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖 (包括微软 ODBC 驱动)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl gnupg2 \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/inventory/sql_server.py backend/Dockerfile
git commit -m "feat: add SQL Server connection layer with pyodbc and ODBC Driver 18"
```

---

### Task 3: 库存服务与缓存层

**Files:**
- Create: `backend/app/inventory/cache_layer.py`
- Create: `backend/app/inventory/inventory_service.py`

- [ ] **Step 1: 实现缓存层**

`backend/app/inventory/cache_layer.py`:
```python
import json
import logging
from typing import Optional
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

CACHE_TTL = 600  # 10 分钟


def _cache_key(prefix: str, key: str) -> str:
    return f"inventory:{prefix}:{key}"


async def get_cached(prefix: str, key: str) -> Optional[dict]:
    """从缓存获取"""
    data = await redis_client.get(_cache_key(prefix, key))
    if data:
        logger.debug(f"Cache hit: {prefix}:{key}")
        return json.loads(data)
    return None


async def set_cached(prefix: str, key: str, value: dict) -> None:
    """写入缓存"""
    await redis_client.setex(
        _cache_key(prefix, key),
        CACHE_TTL,
        json.dumps(value, ensure_ascii=False, default=str),
    )


async def invalidate(prefix: str, key: str) -> None:
    """使缓存失效"""
    await redis_client.delete(_cache_key(prefix, key))
```

- [ ] **Step 2: 实现库存服务 (SQL Server 实现)**

`backend/app/inventory/inventory_service.py`:
```python
import logging
from app.inventory.schemas import StockInfo, PriceInfo, LeadTimeInfo, ProductInfo
from app.inventory.provider import InventoryProvider
from app.inventory.cache_layer import get_cached, set_cached

logger = logging.getLogger(__name__)


class SQLServerInventoryProvider(InventoryProvider):
    """SQL Server 进销存数据提供者"""

    # 需要根据实际开龙进销存表结构调整
    # 以下为典型进销存表的示例查询

    STOCK_QUERY = """
        SELECT sku, product_name, available_qty, warehouse
        FROM inventory_stock WITH (NOLOCK)
        WHERE sku = ?
    """

    PRICE_QUERY = """
        SELECT sku, standard_price, tier_price_json, promo_price
        FROM product_price WITH (NOLOCK)
        WHERE sku = ?
    """

    LEAD_TIME_QUERY = """
        SELECT sku, lead_time_days, next_arrival_date
        FROM product_supply WITH (NOLOCK)
        WHERE sku = ?
    """

    SEARCH_QUERY = """
        SELECT TOP (?) sku, product_name, category, specifications
        FROM product_catalog WITH (NOLOCK)
        WHERE product_name LIKE ? OR sku LIKE ?
    """

    async def get_stock(self, sku: str) -> StockInfo | None:
        cached = await get_cached("stock", sku)
        if cached:
            return StockInfo(**cached)

        from app.inventory.sql_server import execute_query
        results = execute_query(self.STOCK_QUERY, (sku,))
        if not results:
            return None

        info = StockInfo(
            sku=results[0]["sku"],
            product_name=results[0]["product_name"],
            available_qty=float(results[0]["available_qty"]),
            warehouse_location=results[0].get("warehouse", ""),
        )
        await set_cached("stock", sku, info.model_dump())
        return info

    async def get_price(self, sku: str, quantity: int = 1) -> PriceInfo | None:
        cached = await get_cached("price", f"{sku}:{quantity}")
        if cached:
            return PriceInfo(**cached)

        from app.inventory.sql_server import execute_query
        results = execute_query(self.PRICE_QUERY, (sku,))
        if not results:
            return None

        info = PriceInfo(
            sku=results[0]["sku"],
            standard_price=float(results[0]["standard_price"]),
            tier_prices=[],  # 需要根据实际表结构调整
            promo_price=float(results[0]["promo_price"]) if results[0].get("promo_price") else None,
        )
        await set_cached("price", f"{sku}:{quantity}", info.model_dump())
        return info

    async def get_lead_time(self, sku: str) -> LeadTimeInfo | None:
        from app.inventory.sql_server import execute_query
        results = execute_query(self.LEAD_TIME_QUERY, (sku,))
        if not results:
            return None
        return LeadTimeInfo(
            sku=sku,
            lead_time_days=results[0].get("lead_time_days", 7),
            next_arrival_date=results[0].get("next_arrival_date"),
        )

    async def search_products(self, keyword: str, limit: int = 10) -> list[ProductInfo]:
        from app.inventory.sql_server import execute_query
        pattern = f"%{keyword}%"
        results = execute_query(self.SEARCH_QUERY, (limit, pattern, pattern))
        return [
            ProductInfo(
                sku=r["sku"],
                name=r["product_name"],
                category=r.get("category", ""),
                specifications=r.get("specifications", {}),
            )
            for r in results
        ]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/inventory/cache_layer.py backend/app/inventory/inventory_service.py
git commit -m "feat: implement inventory service with Redis caching and SQL Server provider"
```

---

### Task 4: 库存查询 API 与意图处理器

**Files:**
- Create: `backend/app/inventory/router.py`
- Create: `backend/app/inventory/inventory_handler.py`

- [ ] **Step 1: 创建库存查询路由**

`backend/app/inventory/router.py`:
```python
import logging
from fastapi import APIRouter
from app.inventory.provider import InventoryProvider
from app.inventory.schemas import StockInfo, PriceInfo, ProductInfo

logger = logging.getLogger(__name__)

# 全局 provider 实例 (启动时注入)
provider: InventoryProvider | None = None

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/stock/{sku}")
async def get_stock(sku: str):
    """查询库存"""
    if not provider:
        return {"error": "Inventory provider not configured"}
    stock = await provider.get_stock(sku)
    return stock or {"sku": sku, "error": "Product not found"}


@router.get("/price/{sku}")
async def get_price(sku: str, quantity: int = 1):
    """查询价格"""
    if not provider:
        return {"error": "Inventory provider not configured"}
    price = await provider.get_price(sku, quantity)
    return price or {"sku": sku, "error": "Product not found"}


@router.get("/search")
async def search_products(keyword: str, limit: int = 10):
    """搜索产品"""
    if not provider:
        return {"error": "Inventory provider not configured"}
    products = await provider.search_products(keyword, limit)
    return products
```

- [ ] **Step 2: 创建库存意图处理器**

`backend/app/inventory/inventory_handler.py`:
```python
import logging
from app.gateway.message_sender import send_text
from app.inventory.provider import InventoryProvider

logger = logging.getLogger(__name__)


async def handle_inventory_query(
    message: str,
    user_id: str,
    provider: InventoryProvider,
):
    """处理库存/价格查询意图"""
    # 从消息中提取 SKU 或产品名称 (简单关键词匹配)
    # 实际应用中可以使用 LLM 提取
    products = await provider.search_products(message, limit=1)

    if not products:
        await send_text(
            to_user=user_id,
            content="抱歉，未找到相关产品。请提供产品名称或编号。",
        )
        return "未找到产品"

    product = products[0]
    stock = await provider.get_stock(product.sku)
    price = await provider.get_price(product.sku)

    reply = f"**{product.name}**\n"
    if stock:
        stock_status = f"库存 {stock.available_qty} 件" if stock.available_qty > 0 else "暂时缺货"
        reply += f"库存: {stock_status}\n"
    if price:
        reply += f"价格: ¥{price.standard_price:.2f}\n"
    reply += f"编号: {product.sku}"

    await send_text(to_user=user_id, content=reply)
    return reply
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/inventory/router.py backend/app/inventory/inventory_handler.py
git commit -m "feat: add inventory query API and intent handler"
```

---

### Task 5: 销售指导引擎

**Files:**
- Create: `backend/app/models/sales.py`
- Create: `backend/app/sales/schemas.py`
- Create: `backend/app/sales/guidance_service.py`
- Create: `backend/app/sales/recommendation_engine.py`
- Create: `backend/app/sales/sales_handler.py`
- Create: `backend/app/sales/router.py`
- Create: `backend/migrations/versions/006_sales_guidance_tables.py`

- [ ] **Step 1: 创建销售指导模型**

`backend/app/models/sales.py`:
```python
from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import String, Text, DateTime, Date, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base


class SalesGuidance(Base):
    __tablename__ = "sales_guidance"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    product_sku: Mapped[str] = mapped_column(String(50))
    product_name: Mapped[str] = mapped_column(String(200))
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1-10
    promo_type: Mapped[str] = mapped_column(String(50), default="none")  # discount/full_reduce/gift
    discount_rate: Mapped[float] = mapped_column(Float, default=0)
    start_date: Mapped[date]
    end_date: Mapped[date]
    talk_template: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2: 创建迁移**

`backend/migrations/versions/006_sales_guidance_tables.py`:
```python
"""create sales_guidance table

Revision ID: 006
Revises: 005
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sales_guidance",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("product_sku", sa.String(50), nullable=False),
        sa.Column("product_name", sa.String(200), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="5"),
        sa.Column("promo_type", sa.String(50), nullable=False, server_default="'none'"),
        sa.Column("discount_rate", sa.Float, nullable=False, server_default="0"),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("talk_template", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table("sales_guidance")
```

- [ ] **Step 3: 推荐引擎**

`backend/app/sales/recommendation_engine.py`:
```python
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sales import SalesGuidance
from app.inventory.provider import InventoryProvider
from app.inventory.schemas import ProductInfo

logger = logging.getLogger(__name__)


async def get_recommendations(
    session: AsyncSession,
    provider: InventoryProvider,
    keyword: str | None = None,
    limit: int = 3,
) -> list[dict]:
    """获取推荐产品 (结合库存 + 销售指导)"""
    # 1. 获取活跃的销售指导
    now = datetime.now(timezone.utc).date()
    result = await session.execute(
        select(SalesGuidance)
        .where(
            SalesGuidance.is_active.is_(True),
            SalesGuidance.start_date <= now,
            SalesGuidance.end_date >= now,
        )
        .order_by(SalesGuidance.priority.desc())
        .limit(limit)
    )
    guidances = result.scalars().all()

    recommendations = []
    for g in guidances:
        # 检查库存
        stock = await provider.get_stock(g.product_sku)
        available = stock.available_qty > 0 if stock else False

        recommendations.append({
            "sku": g.product_sku,
            "name": g.product_name,
            "priority": g.priority,
            "promo_type": g.promo_type,
            "discount_rate": g.discount_rate,
            "in_stock": available,
            "stock_qty": stock.available_qty if stock else 0,
            "talk_template": g.talk_template,
        })

    return recommendations
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/sales.py backend/app/models/__init__.py backend/app/sales/ backend/migrations/versions/006_sales_guidance_tables.py
git commit -m "feat: implement sales guidance engine with recommendation logic"
```

---

### Task 6: 测试

**Files:**
- Create: `backend/tests/test_inventory_service.py`
- Create: `backend/tests/test_cache_layer.py`
- Create: `backend/tests/test_recommendation_engine.py`

- [ ] **Step 1: Mock 库存服务测试**

`backend/tests/test_inventory_service.py`:
```python
import pytest
from app.inventory.provider import MockInventoryProvider


@pytest.mark.asyncio
async def test_mock_get_stock():
    provider = MockInventoryProvider()
    stock = await provider.get_stock("SKU001")
    assert stock is not None
    assert stock.sku == "SKU001"
    assert stock.available_qty == 100


@pytest.mark.asyncio
async def test_mock_get_stock_not_found():
    provider = MockInventoryProvider()
    stock = await provider.get_stock("UNKNOWN")
    assert stock is None


@pytest.mark.asyncio
async def test_mock_get_price():
    provider = MockInventoryProvider()
    price = await provider.get_price("SKU001")
    assert price is not None
    assert price.standard_price == 299.0


@pytest.mark.asyncio
async def test_mock_search_products():
    provider = MockInventoryProvider()
    products = await provider.search_products("产品")
    assert len(products) >= 2
```

- [ ] **Step 2: 缓存层测试**

`backend/tests/test_cache_layer.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch
from app.inventory.cache_layer import get_cached, set_cached, invalidate


@pytest.mark.asyncio
async def test_cache_miss():
    with patch("app.inventory.cache_layer.redis_client") as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        result = await get_cached("stock", "SKU001")
        assert result is None


@pytest.mark.asyncio
async def test_cache_hit():
    with patch("app.inventory.cache_layer.redis_client") as mock_redis:
        import json
        mock_redis.get = AsyncMock(return_value=json.dumps({"sku": "SKU001", "available_qty": 100}))
        result = await get_cached("stock", "SKU001")
        assert result["sku"] == "SKU001"


@pytest.mark.asyncio
async def test_set_cache():
    with patch("app.inventory.cache_layer.redis_client") as mock_redis:
        mock_redis.setex = AsyncMock()
        await set_cached("stock", "SKU001", {"sku": "SKU001"})
        mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_invalidate_cache():
    with patch("app.inventory.cache_layer.redis_client") as mock_redis:
        mock_redis.delete = AsyncMock()
        await invalidate("stock", "SKU001")
        mock_redis.delete.assert_called_once()
```

- [ ] **Step 3: 推荐引擎测试**

`backend/tests/test_recommendation_engine.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.sales.recommendation_engine import get_recommendations


@pytest.mark.asyncio
async def test_recommendations_with_mock_provider():
    mock_session = AsyncMock()
    mock_provider = MagicMock()
    mock_provider.get_stock = AsyncMock()
    mock_provider.get_stock.return_value = MagicMock(available_qty=100)

    # Mock SQL result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    recs = await get_recommendations(mock_session, mock_provider)
    assert isinstance(recs, list)
```

- [ ] **Step 4: 运行全部测试**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot/backend
python -m pytest tests/ -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_inventory_service.py backend/tests/test_cache_layer.py backend/tests/test_recommendation_engine.py
git commit -m "test: add tests for inventory service, cache layer, and recommendation engine"
```

---

## Plan 5 完成标准

- [x] Mock 库存服务可用 (开发阶段)
- [x] SQL Server 连接层就绪 (等待表结构)
- [x] 库存查询 API 可用
- [x] Redis 缓存生效
- [x] 销售推荐引擎工作
- [x] 所有单元测试通过

## 表结构对接清单

获取开龙进销存表结构后，需要修改以下 SQL 查询:

| 查询用途 | 需修改的 SQL | 需要确认的表名/字段 |
|----------|-------------|-------------------|
| 库存查询 | `STOCK_QUERY` | 库存表名、SKU字段名、数量字段名 |
| 价格查询 | `PRICE_QUERY` | 价格表名、标准价字段、促销价字段 |
| 供货周期 | `LEAD_TIME_QUERY` | 供货表名、供货周期字段 |
| 产品搜索 | `SEARCH_QUERY` | 产品目录表名、名称字段、分类字段 |

---

## 与 AI 引擎集成

Plan 5 完成后，需要在 `backend/app/main.py` 的启动逻辑中注入 provider:

```python
from app.inventory.provider import SQLServerInventoryProvider
from app.inventory.router import provider as inventory_provider
from app.inventory.router import router as inventory_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # 注入库存服务 provider
    from app.inventory.router import provider as inv_provider
    # 根据环境变量选择 Mock 或 SQL Server 实现
    inv_provider = SQLServerInventoryProvider()  # 或 MockInventoryProvider()
    yield
```
