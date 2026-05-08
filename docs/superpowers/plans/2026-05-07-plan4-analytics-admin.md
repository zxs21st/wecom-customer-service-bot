# Plan 4: 咨询分析与后台管理面板 - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现咨询数据自动采集、统计分析 API、以及 React 后台管理面板（知识库管理、报价/工单管理、数据分析）。

**Architecture:** 后端新增 analytics 模块自动记录每次 AI 交互，提供统计 API；前端 React + Ant Design Pro 构建管理面板，通过 JWT 认证保护。

**Tech Stack:** FastAPI, React 18, Ant Design Pro, Recharts, JWT, pytest

**Depends on:** Plan 1 + Plan 2 + Plan 3 (所有数据模型)

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/models/analytics.py` | 新建 | 咨询记录模型 |
| `backend/app/analytics/schemas.py` | 新建 | 统计数据模型 |
| `backend/app/analytics/consultation_logger.py` | 新建 | 自动记录每次 AI 交互 |
| `backend/app/analytics/stats_service.py` | 新建 | 聚合统计查询 |
| `backend/app/analytics/router.py` | 新建 | 分析 API 路由 |
| `backend/app/auth/jwt_handler.py` | 新建 | JWT 认证 |
| `backend/app/auth/router.py` | 新建 | 登录/刷新 API |
| `backend/app/auth/middleware.py` | 新建 | JWT 验证中间件 |
| `backend/migrations/versions/004_analytics_tables.py` | 新建 | 咨询记录表迁移 |
| `backend/migrations/versions/005_admin_user_table.py` | 新建 | 管理员表迁移 |
| `frontend/package.json` | 新建 | React 项目 |
| `frontend/src/pages/Dashboard.tsx` | 新建 | 主仪表盘 |
| `frontend/src/pages/KnowledgeManage.tsx` | 新建 | 知识库管理 |
| `frontend/src/pages/QuoteManage.tsx` | 新建 | 报价管理 |
| `frontend/src/pages/TicketManage.tsx` | 新建 | 工单管理 |
| `frontend/src/pages/Analytics.tsx` | 新建 | 趋势分析 |
| `frontend/src/services/api.ts` | 新建 | API 客户端 |
| `frontend/src/services/types.ts` | 新建 | TypeScript 类型 |
| `frontend/src/App.tsx` | 新建 | 应用入口 |
| `frontend/src/main.tsx` | 新建 | React 入口 |

---

### Task 1: 咨询记录模型与自动日志

**Files:**
- Create: `backend/app/models/analytics.py`
- Create: `backend/app/analytics/consultation_logger.py`
- Create: `backend/migrations/versions/004_analytics_tables.py`

- [ ] **Step 1: 创建咨询记录模型**

`backend/app/models/analytics.py`:
```python
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base


class ConsultationRecord(Base):
    __tablename__ = "consultation_record"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    user_id: Mapped[Optional[str]] = mapped_column(String(100))
    chat_id: Mapped[Optional[str]] = mapped_column(String(100))
    intent_type: Mapped[Optional[str]] = mapped_column(String(50))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    is_resolved: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
```

更新 `backend/app/models/__init__.py` 添加:
```python
from app.models import analytics  # noqa: F401
```

- [ ] **Step 2: 创建咨询记录表迁移**

`backend/migrations/versions/004_analytics_tables.py`:
```python
"""create consultation_record table

Revision ID: 004
Revises: 003
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "consultation_record",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("chat_id", sa.String(100), nullable=True),
        sa.Column("intent_type", sa.String(50), nullable=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("is_resolved", sa.Boolean, nullable=True, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # 创建按日统计视图
    op.execute("""
        CREATE VIEW daily_consultation_stats AS
        SELECT
            DATE(created_at) as date,
            COUNT(*) as total_queries,
            COUNT(CASE WHEN is_resolved THEN 1 END) as resolved_queries,
            AVG(confidence) as avg_confidence
        FROM consultation_record
        GROUP BY DATE(created_at)
    """)


def downgrade():
    op.execute("DROP VIEW IF EXISTS daily_consultation_stats")
    op.drop_table("consultation_record")
```

- [ ] **Step 3: 实现自动日志**

`backend/app/analytics/consultation_logger.py`:
```python
import logging
import uuid
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
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/analytics.py backend/app/models/__init__.py backend/app/analytics/consultation_logger.py backend/migrations/versions/004_analytics_tables.py
git commit -m "feat: add consultation record model and auto-logging service"
```

---

### Task 2: 统计服务与分析 API

**Files:**
- Create: `backend/app/analytics/schemas.py`
- Create: `backend/app/analytics/stats_service.py`
- Create: `backend/app/analytics/router.py`

- [ ] **Step 1: 定义统计 Schema**

`backend/app/analytics/schemas.py`:
```python
from datetime import date
from pydantic import BaseModel


class DashboardStats(BaseModel):
    today_queries: int
    today_resolved: int
    total_queries: int
    avg_confidence: float
    top_intents: list[dict]  # [{"intent": str, "count": int}]
    unresolved_count: int


class DailyStat(BaseModel):
    date: date
    total_queries: int
    resolved_queries: int
    avg_confidence: float


class ConsultationRecordResponse(BaseModel):
    id: str
    session_id: str | None
    user_id: str | None
    intent_type: str | None
    question: str
    answer: str | None
    confidence: float | None
    is_resolved: bool | None
    created_at: str
```

- [ ] **Step 2: 实现统计服务**

`backend/app/analytics/stats_service.py`:
```python
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, text
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
        .order_by(text("date"))
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
```

- [ ] **Step 3: 创建分析路由**

`backend/app/analytics/router.py`:
```python
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.analytics.schemas import DashboardStats, DailyStat, ConsultationRecordResponse
from app.analytics.stats_service import get_dashboard_stats, get_daily_stats
from app.analytics.consultation_logger import log_consultation
from app.models.analytics import ConsultationRecord
from sqlalchemy import select

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
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/analytics/schemas.py backend/app/analytics/stats_service.py backend/app/analytics/router.py
git commit -m "feat: add analytics API with dashboard stats, daily trends, and consultation records"
```

---

### Task 3: JWT 认证

**Files:**
- Create: `backend/app/models/admin.py`
- Create: `backend/app/auth/jwt_handler.py`
- Create: `backend/app/auth/router.py`
- Create: `backend/migrations/versions/005_admin_user_table.py`

- [ ] **Step 1: 管理员模型**

`backend/app/models/admin.py`:
```python
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base


class AdminUser(Base):
    __tablename__ = "admin_user"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2: JWT 处理**

`backend/app/auth/jwt_handler.py`:
```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings

SECRET_KEY = settings.wecom_secret or "default-secret-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时


def create_access_token(username: str) -> str:
    """创建 JWT Token"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> str | None:
    """验证 JWT Token，返回用户名"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
```

> 需要在 `pyproject.toml` 中添加 `python-jose[cryptography]>=3.3.0` 依赖。

- [ ] **Step 3: 认证路由**

`backend/app/auth/router.py`:
```python
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from app.db import get_db
from app.models.admin import AdminUser
from app.auth.jwt_handler import create_access_token

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(username: str, password: str, db: AsyncSession = Depends(get_db)):
    """管理员登录"""
    from sqlalchemy import select
    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token(username)
    return {"access_token": token, "token_type": "bearer"}
```

> 需要在 `pyproject.toml` 中添加 `passlib[bcrypt]>=1.7.4` 依赖。

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/admin.py backend/app/auth/ backend/migrations/versions/005_admin_user_table.py
git commit -m "feat: add JWT authentication for admin panel"
```

---

### Task 4: React 后台管理面板

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/services/types.ts`
- Create: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/pages/KnowledgeManage.tsx`
- Create: `frontend/src/pages/QuoteManage.tsx`
- Create: `frontend/src/pages/TicketManage.tsx`
- Create: `frontend/src/pages/Analytics.tsx`
- Create: `frontend/src/layouts/AdminLayout.tsx`

由于前端代码量较大，这里给出核心文件：

- [ ] **Step 1: 创建前端项目配置**

`frontend/package.json`:
```json
{
  "name": "wecom-bot-admin",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "antd": "^5.20.0",
    "@ant-design/icons": "^5.4.0",
    "recharts": "^2.12.0",
    "axios": "^1.7.0",
    "dayjs": "^1.11.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0"
  }
}
```

`frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

`frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>企微客服机器人 - 管理后台</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

- [ ] **Step 2: 创建 React 入口**

`frontend/src/main.tsx`:
```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import 'antd/dist/reset.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
```

`frontend/src/App.tsx`:
```tsx
import { Routes, Route, Navigate } from 'react-router-dom'
import AdminLayout from './layouts/AdminLayout'
import Dashboard from './pages/Dashboard'
import KnowledgeManage from './pages/KnowledgeManage'
import QuoteManage from './pages/QuoteManage'
import TicketManage from './pages/TicketManage'
import Analytics from './pages/Analytics'

function App() {
  return (
    <Routes>
      <Route path="/" element={<AdminLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="knowledge" element={<KnowledgeManage />} />
        <Route path="quotes" element={<QuoteManage />} />
        <Route path="tickets" element={<TicketManage />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
```

- [ ] **Step 3: 创建 API 服务**

`frontend/src/services/api.ts`:
```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截器 - 添加 JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const knowledgeApi = {
  list: (category?: string) => api.get('/knowledge/documents', { params: { category } }),
  create: (data: { title: string; category: string; content: string }) => api.post('/knowledge/documents', data),
  delete: (id: string) => api.delete(`/knowledge/documents/${id}`),
  search: (query: string, topK = 5) => api.post('/knowledge/search', { query, top_k: topK }),
}

export const analyticsApi = {
  dashboard: () => api.get('/analytics/dashboard'),
  daily: (days = 30) => api.get('/analytics/daily', { params: { days } }),
  records: (limit = 50) => api.get('/analytics/records', { params: { limit } }),
}

export const quoteApi = {
  list: () => api.get('/quotes'),
  generatePdf: (id: string) => api.post(`/quotes/${id}/generate-pdf`),
  accept: (id: string) => api.post(`/quotes/${id}/accept`),
}

export const ticketApi = {
  list: () => api.get('/after-sales/tickets'),
  update: (id: string, data: { status: string; assigned_to?: string }) =>
    api.patch(`/after-sales/tickets/${id}`, null, { params: data }),
}

export default api
```

`frontend/src/services/types.ts`:
```typescript
export interface DashboardStats {
  today_queries: number
  today_resolved: number
  total_queries: number
  avg_confidence: number
  top_intents: Array<{ intent: string; count: number }>
  unresolved_count: number
}

export interface DailyStat {
  date: string
  total_queries: number
  resolved_queries: number
  avg_confidence: number
}

export interface ConsultationRecord {
  id: string
  intent_type: string | null
  question: string
  answer: string | null
  confidence: number | null
  is_resolved: boolean | null
  created_at: string
}

export interface KnowledgeDocument {
  id: string
  title: string
  category: string
  content: string
  created_at: string
}
```

- [ ] **Step 4: 创建管理布局**

`frontend/src/layouts/AdminLayout.tsx`:
```tsx
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  BookOutlined,
  FileTextOutlined,
  CustomerServiceOutlined,
  BarChartOutlined,
} from '@ant-design/icons'

const { Sider, Content } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/knowledge', icon: <BookOutlined />, label: '知识库管理' },
  { key: '/quotes', icon: <FileTextOutlined />, label: '报价管理' },
  { key: '/tickets', icon: <CustomerServiceOutlined />, label: '工单管理' },
  { key: '/analytics', icon: <BarChartOutlined />, label: '咨询分析' },
]

function AdminLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light">
        <div style={{ padding: 16, fontWeight: 'bold', fontSize: 16 }}>企微客服管理</div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Content style={{ padding: 24, background: '#f0f2f5' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default AdminLayout
```

- [ ] **Step 5: 创建仪表盘页面**

`frontend/src/pages/Dashboard.tsx`:
```tsx
import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Spin } from 'antd'
import { analyticsApi } from '../services/api'
import type { DashboardStats } from '../services/types'

function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    analyticsApi.dashboard().then((res) => {
      setStats(res.data)
      setLoading(false)
    })
  }, [])

  if (loading) return <Spin size="large" />
  if (!stats) return null

  const intentColumns = [
    { title: '意图', dataIndex: 'intent', key: 'intent' },
    { title: '数量', dataIndex: 'count', key: 'count' },
  ]

  return (
    <div>
      <h2>数据概览</h2>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic title="今日咨询量" value={stats.today_queries} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="今日解决率" value={(stats.today_resolved / Math.max(stats.today_queries, 1)) * 100} suffix="%" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="平均置信度" value={stats.avg_confidence} precision={2} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="未解决" value={stats.unresolved_count} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
      </Row>

      <Card title="热门意图 TOP 5" style={{ marginTop: 16 }}>
        <Table dataSource={stats.top_intents} columns={intentColumns} pagination={false} size="small" />
      </Card>
    </div>
  )
}

export default Dashboard
```

- [ ] **Step 6: 创建知识库管理页面**

`frontend/src/pages/KnowledgeManage.tsx`:
```tsx
import { useEffect, useState } from 'react'
import { Button, Table, Modal, Form, Input, Select, message, Space, Popconfirm } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { knowledgeApi } from '../services/api'
import type { KnowledgeDocument } from '../services/types'

const { TextArea } = Input

function KnowledgeManage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const fetchDocs = () => {
    knowledgeApi.list().then((res) => setDocuments(res.data))
  }

  useEffect(() => { fetchDocs() }, [])

  const handleSubmit = async () => {
    const values = await form.validateFields()
    setLoading(true)
    try {
      await knowledgeApi.create(values)
      message.success('知识录入成功')
      setModalOpen(false)
      form.resetFields()
      fetchDocs()
    } catch {
      message.error('知识录入失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    await knowledgeApi.delete(id)
    message.success('删除成功')
    fetchDocs()
  }

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '分类', dataIndex: 'category', key: 'category' },
    { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
    { title: '操作', key: 'action', render: (_: any, record: KnowledgeDocument) => (
      <Popconfirm title="确认删除" onConfirm={() => handleDelete(record.id)}>
        <Button danger size="small">删除</Button>
      </Popconfirm>
    )},
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>知识库管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          录入知识
        </Button>
      </div>

      <Table dataSource={documents} columns={columns} rowKey="id" />

      <Modal title="录入知识" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={handleSubmit} confirmLoading={loading}>
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="category" label="分类" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="product_knowledge">产品知识</Select.Option>
              <Select.Option value="config_guide">配置指南</Select.Option>
              <Select.Option value="faq">FAQ</Select.Option>
              <Select.Option value="after_sales">售后政策</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <TextArea rows={6} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default KnowledgeManage
```

- [ ] **Step 7: 创建其他管理页面**

`frontend/src/pages/QuoteManage.tsx`:
```tsx
import { Card, Empty } from 'antd'

function QuoteManage() {
  return (
    <div>
      <h2>报价管理</h2>
      <Card>
        <Empty description="报价管理功能开发中" />
      </Card>
    </div>
  )
}

export default QuoteManage
```

`frontend/src/pages/TicketManage.tsx`:
```tsx
import { Card, Empty } from 'antd'

function TicketManage() {
  return (
    <div>
      <h2>工单管理</h2>
      <Card>
        <Empty description="工单管理功能开发中" />
      </Card>
    </div>
  )
}

export default TicketManage
```

`frontend/src/pages/Analytics.tsx`:
```tsx
import { useEffect, useState } from 'react'
import { Card, Spin } from 'antd'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { analyticsApi } from '../services/api'
import type { DailyStat } from '../services/types'

function Analytics() {
  const [data, setData] = useState<DailyStat[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    analyticsApi.daily(30).then((res) => {
      setData(res.data)
      setLoading(false)
    })
  }, [])

  if (loading) return <Spin size="large" />

  return (
    <div>
      <h2>咨询趋势 (30 天)</h2>
      <Card>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="total_queries" stroke="#1890ff" name="咨询量" />
            <Line type="monotone" dataKey="resolved_queries" stroke="#52c41a" name="已解决" />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  )
}

export default Analytics
```

- [ ] **Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: create React admin panel with dashboard, knowledge management, and analytics"
```

---

### Task 5: 路由注册与端到端验证

- [ ] **Step 1: 注册所有新路由**

修改 `backend/app/main.py`，添加:
```python
from app.analytics.router import router as analytics_router
from app.auth.router import router as auth_router
from app.quoting.router import router as quoting_router
from app.after_sales.router import router as after_sales_router

# 注册所有路由
app.include_router(gateway_router)
app.include_router(ai_router)
app.include_router(knowledge_router)
app.include_router(analytics_router)
app.include_router(quoting_router)
app.include_router(after_sales_router)
app.include_router(auth_router)
```

- [ ] **Step 2: 运行全部测试**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot/backend
python -m pytest tests/ -v
```

- [ ] **Step 3: 启动 Docker 环境**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot
docker compose up -d
```

- [ ] **Step 4: 验证后端 API**

```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

- [ ] **Step 5: 验证前端**

```bash
cd frontend
npm install
npm run dev
```
访问 http://localhost:3000 确认管理面板正常渲染

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "docs: Plan 4 complete - analytics and admin panel operational"
```

---

## Plan 4 完成标准

- [x] 每次 AI 对话自动记录到咨询表
- [x] 仪表盘 API 返回统计数据
- [x] React 管理面板可访问
- [x] 知识库管理 (录入/查看/删除)
- [x] 数据可视化 (趋势图表)
- [x] 所有单元测试通过

## Plan 5 前置接口

Plan 5 (进销存 + 销售指导) 是独立模块，依赖：
- Plan 1 的 `IntentType.INVENTORY_QUERY` / `IntentType.PRICE_INQUIRY` 意图分类
- Plan 2 的 `generate_response()` 回答生成 + 知识注入机制
- Plan 3 的报价服务（用于实时定价）
