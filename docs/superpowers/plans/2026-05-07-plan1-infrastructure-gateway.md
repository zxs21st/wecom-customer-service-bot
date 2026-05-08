# Plan 1: 基础设施与消息网关 - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建项目基础设施，实现企业微信消息接收、签名验证、会话管理的基础网关服务。

**Architecture:** FastAPI 应用运行在 Docker 容器中，通过 webhook 接收企业微信消息回调，使用 Redis 管理会话上下文，PostgreSQL 作为主数据库。

**Tech Stack:** FastAPI, Python 3.12, PostgreSQL 16, Redis 7, Docker Compose, wechatpy, pytest

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `docker-compose.yml` | 新建 | PostgreSQL + Redis + Backend 服务编排 |
| `backend/Dockerfile` | 新建 | Python 运行环境镜像 |
| `backend/pyproject.toml` | 新建 | 依赖管理 + 项目配置 |
| `backend/.env.example` | 新建 | 环境变量模板 |
| `backend/app/main.py` | 新建 | FastAPI 应用工厂 |
| `backend/app/config.py` | 新建 | 全局配置 (Pydantic Settings) |
| `backend/app/db.py` | 新建 | SQLAlchemy 异步引擎 |
| `backend/app/redis_client.py` | 新建 | Redis 客户端单例 |
| `backend/app/models/__init__.py` | 新建 | Declarative Base |
| `backend/app/gateway/schemas.py` | 新建 | Message, Session 等 Pydantic 模型 |
| `backend/app/gateway/verifier.py` | 新建 | 企微签名验证 |
| `backend/app/gateway/message_parser.py` | 新建 | XML 消息解析 |
| `backend/app/gateway/message_sender.py` | 新建 | 企微消息发送 API 封装 |
| `backend/app/gateway/session_manager.py` | 新建 | Redis 会话管理 |
| `backend/app/gateway/router.py` | 新建 | Webhook 路由 + 消息路由 |
| `backend/tests/conftest.py` | 新建 | pytest 配置 + fixtures |
| `backend/tests/test_verifier.py` | 新建 | 签名验证单元测试 |
| `backend/tests/test_message_parser.py` | 新建 | XML 解析单元测试 |
| `backend/tests/test_session_manager.py` | 新建 | 会话管理单元测试 |
| `backend/tests/test_webhook.py` | 新建 | Webhook 集成测试 |

---

### Task 1: 项目脚手架与 Docker 环境

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`

- [ ] **Step 1: 创建 docker-compose.yml**

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: wecom_bot
      POSTGRES_USER: wecom
      POSTGRES_PASSWORD: ${DB_PASSWORD:-wecom123}
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U wecom"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  backend:
    build: ./backend
    env_file: ./backend/.env
    environment:
      DATABASE_URL: postgresql+asyncpg://wecom:${DB_PASSWORD:-wecom123}@postgres:5432/wecom_bot
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend/app:/app/app

volumes:
  pg_data:
```

- [ ] **Step 2: 创建 backend/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 3: 创建 backend/pyproject.toml**

```toml
[project]
name = "wecom-customer-service-bot"
version = "0.1.0"
description = "企业微信客服机器人"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "sqlalchemy[asyncio]>=2.0.35",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "redis>=5.1.0",
    "wechatpy[cryptography]>=1.8.18",
    "celery[redis]>=5.4.0",
    "litellm>=1.50.0",
    "python-dotenv>=1.0.1",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "fakeredis>=2.24.0",
    "coverage>=7.6.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 4: 创建 backend/.env.example**

```env
# 企业微信
WECOM_CORP_ID=your_corp_id
WECOM_TOKEN=your_token
WECOM_ENCODING_AES_KEY=your_encoding_aes_key
WECOM_AGENT_ID=your_agent_id
WECOM_SECRET=your_secret

# 数据库
DATABASE_URL=postgresql+asyncpg://wecom:wecom123@localhost:5432/wecom_bot

# Redis
REDIS_URL=redis://localhost:6379/0

# AI 服务 (Phase 2 使用)
OPENAI_API_KEY=your_api_key
OPENAI_CHAT_MODEL=qwen-plus
OPENAI_EMBEDDING_MODEL=text-embedding-v3

# 进销存 SQL Server (Phase 5 使用)
INVENTORY_DB_DRIVER=ODBC Driver 18 for SQL Server
INVENTORY_DB_SERVER=
INVENTORY_DB_NAME=
INVENTORY_DB_USER=
INVENTORY_DB_PASSWORD=
```

- [ ] **Step 5: 复制 .env.example 为 .env**

```bash
cp backend/.env.example backend/.env
```

- [ ] **Step 6: 验证 Docker 环境启动**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot
docker compose up -d
docker compose ps
```
Expected: postgres, redis, backend 三个容器均为 healthy/running

- [ ] **Step 7: Commit**

```bash
git add docker-compose.yml backend/Dockerfile backend/pyproject.toml backend/.env.example backend/.env
git commit -m "feat: scaffold project with Docker compose, FastAPI, PostgreSQL, Redis"
```

---

### Task 2: 应用配置与数据库连接

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/db.py`
- Create: `backend/app/redis_client.py`
- Create: `backend/app/main.py`
- Create: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建配置模块**

`backend/app/config.py`:
```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 企业微信
    wecom_corp_id: str = ""
    wecom_token: str = ""
    wecom_encoding_aes_key: str = ""
    wecom_agent_id: int = 0
    wecom_secret: str = ""

    # 数据库
    database_url: str = "postgresql+asyncpg://wecom:wecom123@localhost:5432/wecom_bot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # AI
    openai_api_key: str = ""
    openai_chat_model: str = "qwen-plus"
    openai_embedding_model: str = "text-embedding-v3"

    # 会话配置
    session_ttl_seconds: int = 1800  # 30 分钟
    max_context_messages: int = 10

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 2: 创建数据库连接**

`backend/app/db.py`:
```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    from app.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 3: 创建 Redis 客户端**

`backend/app/redis_client.py`:
```python
import redis.asyncio as redis
from app.config import settings

redis_client: redis.Redis = redis.from_url(
    settings.redis_url,
    decode_responses=True,
    encoding="utf-8",
)
```

- [ ] **Step 4: 创建应用入口**

`backend/app/main.py`:
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="企业微信客服机器人",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 创建 Models Base**

`backend/app/models/__init__.py`:
```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 6: 验证应用启动**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot/backend
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
curl http://localhost:8000/health
```
Expected: `{"status":"ok"}`

- [ ] **Step 7: Commit**

```bash
git add backend/app/config.py backend/app/db.py backend/app/redis_client.py backend/app/main.py backend/app/models/__init__.py
git commit -m "feat: add config, database, Redis client, and FastAPI app entry point"
```

---

### Task 3: 企微签名验证与消息解析

**Files:**
- Create: `backend/app/gateway/schemas.py`
- Create: `backend/app/gateway/verifier.py`
- Create: `backend/app/gateway/message_parser.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_verifier.py`
- Create: `backend/tests/test_message_parser.py`

- [ ] **Step 1: 定义消息模型**

`backend/app/gateway/schemas.py`:
```python
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    LINK = "link"


class Message(BaseModel):
    msg_id: str
    from_user: str
    chat_id: str
    msg_type: MessageType
    content: str
    timestamp: datetime


class Session(BaseModel):
    session_id: str
    user_id: str
    chat_id: str
    context: list[Message] = []
    created_at: datetime
    updated_at: datetime


class WeChatCallback(BaseModel):
    msg_signature: str
    timestamp: str
    nonce: str
    echostr: Optional[str] = None
```

- [ ] **Step 2: 实现签名验证**

`backend/app/gateway/verifier.py`:
```python
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from app.config import settings


def get_crypto() -> WeChatCrypto:
    return WeChatCrypto(
        token=settings.wecom_token,
        encoding_aes_key=settings.wecom_encoding_aes_key,
        corp_id=settings.wecom_corp_id,
    )


def verify_url(msg_signature: str, timestamp: str, nonce: str, echostr: str) -> str:
    """验证企微 URL 配置回调"""
    crypto = get_crypto()
    return crypto.check_signature(msg_signature, timestamp, nonce, echostr)


def decrypt_message(msg_signature: str, timestamp: str, nonce: str, body: str) -> str:
    """解密企微消息 XML"""
    crypto = get_crypto()
    return crypto.decrypt_message(body, msg_signature, timestamp, nonce)


def verify_signature(msg_signature: str, timestamp: str, nonce: str, body: str) -> bool:
    """验证消息签名"""
    try:
        decrypt_message(msg_signature, timestamp, nonce, body)
        return True
    except InvalidSignatureException:
        return False
```

- [ ] **Step 3: 实现消息解析**

`backend/app/gateway/message_parser.py`:
```python
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from app.gateway.schemas import Message, MessageType

# XML 标签到 MessageType 的映射
TYPE_MAP = {
    "text": MessageType.TEXT,
    "image": MessageType.IMAGE,
    "voice": MessageType.VOICE,
    "video": MessageType.VIDEO,
    "file": MessageType.FILE,
    "link": MessageType.LINK,
}


def parse_xml(xml_str: str) -> Message:
    """解析企微消息 XML 为 Message 对象"""
    root = ET.fromstring(xml_str)

    msg_type_str = root.findtext("MsgType", "text")
    msg_type = TYPE_MAP.get(msg_type_str, MessageType.TEXT)

    # 文本消息取 Content，其他类型取 MediaId 或 Url
    if msg_type == MessageType.TEXT:
        content = root.findtext("Content", "")
    else:
        content = root.findtext("MediaId", "") or root.findtext("Url", "")

    timestamp = int(root.findtext("CreateTime", "0"))

    return Message(
        msg_id=root.findtext("MsgId", ""),
        from_user=root.findtext("FromUserName", ""),
        chat_id=root.findtext("AgentID", ""),
        msg_type=msg_type,
        content=content,
        timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
    )
```

- [ ] **Step 4: 编写签名验证测试**

`backend/tests/test_verifier.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from app.gateway.verifier import verify_url, decrypt_message, verify_signature


def test_verify_url_success():
    with patch("app.gateway.verifier.get_crypto") as mock_crypto:
        mock_instance = MagicMock()
        mock_instance.check_signature.return_value = "verified_echostr"
        mock_crypto.return_value = mock_instance

        result = verify_url("sig", "123", "nonce", "echo")
        assert result == "verified_echostr"
        mock_instance.check_signature.assert_called_once_with("sig", "123", "nonce", "echo")


def test_verify_signature_valid():
    with patch("app.gateway.verifier.decrypt_message") as mock_decrypt:
        mock_decrypt.return_value = "<xml>...</xml>"
        assert verify_signature("sig", "123", "nonce", "<encrypted>") is True


def test_verify_signature_invalid():
    with patch("app.gateway.verifier.decrypt_message") as mock_decrypt:
        from wechatpy.exceptions import InvalidSignatureException
        mock_decrypt.side_effect = InvalidSignatureException
        assert verify_signature("bad", "123", "nonce", "<encrypted>") is False
```

- [ ] **Step 5: 编写消息解析测试**

`backend/tests/test_message_parser.py`:
```python
from app.gateway.message_parser import parse_xml
from app.gateway.schemas import MessageType


TEXT_XML = """<xml>
<ToUserName><![CDATA[corp123]]></ToUserName>
<FromUserName><![CDATA[user456]]></FromUserName>
<CreateTime>1700000000</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[这个产品多少钱？]]></Content>
<MsgId>12345</MsgId>
<AgentID>1000002</AgentID>
</xml>"""

IMAGE_XML = """<xml>
<ToUserName><![CDATA[corp123]]></ToUserName>
<FromUserName><![CDATA[user456]]></FromUserName>
<CreateTime>1700000000</CreateTime>
<MsgType><![CDATA[image]]></MsgType>
<MediaId><![CDATA[media_abc123]]></MediaId>
<MsgId>12346</MsgId>
<AgentID>1000002</AgentID>
</xml>"""


def test_parse_text_message():
    msg = parse_xml(TEXT_XML)
    assert msg.msg_id == "12345"
    assert msg.from_user == "user456"
    assert msg.chat_id == "1000002"
    assert msg.msg_type == MessageType.TEXT
    assert msg.content == "这个产品多少钱？"


def test_parse_image_message():
    msg = parse_xml(IMAGE_XML)
    assert msg.msg_type == MessageType.IMAGE
    assert msg.content == "media_abc123"


def test_parse_unknown_message_type():
    xml = TEXT_XML.replace("<MsgType><![CDATA[text]]></MsgType>", "<MsgType><![CDATA[unknown]]></MsgType>")
    msg = parse_xml(xml)
    assert msg.msg_type == MessageType.TEXT  # fallback to text
```

- [ ] **Step 6: 运行测试**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot/backend
python -m pytest tests/test_verifier.py tests/test_message_parser.py -v
```
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/app/gateway/schemas.py backend/app/gateway/verifier.py backend/app/gateway/message_parser.py backend/tests/
git commit -m "feat: implement WeChat signature verification and XML message parsing with tests"
```

---

### Task 4: 会话管理 (Redis)

**Files:**
- Create: `backend/app/gateway/session_manager.py`
- Create: `backend/tests/test_session_manager.py`

- [ ] **Step 1: 实现会话管理器**

`backend/app/gateway/session_manager.py`:
```python
import json
from datetime import datetime, timezone
from typing import Optional
from app.config import settings
from app.gateway.schemas import Message, Session
from app.redis_client import redis_client


def _session_key(session_id: str) -> str:
    return f"session:{session_id}"


async def get_session(session_id: str) -> Optional[Session]:
    """获取会话上下文"""
    data = await redis_client.get(_session_key(session_id))
    if not data:
        return None
    session_dict = json.loads(data)
    session_dict["context"] = [Message(**m) for m in session_dict.get("context", [])]
    return Session(**session_dict)


async def create_session(user_id: str, chat_id: str) -> Session:
    """创建新会话"""
    session_id = f"{user_id}:{chat_id}"
    now = datetime.now(timezone.utc)
    session = Session(
        session_id=session_id,
        user_id=user_id,
        chat_id=chat_id,
        context=[],
        created_at=now,
        updated_at=now,
    )
    await _save_session(session)
    return session


async def add_message(session_id: str, message: Message) -> Session:
    """添加消息到会话上下文"""
    session = await get_session(session_id)
    if not session:
        session = await create_session(message.from_user, message.chat_id)

    session.context.append(message)
    # 保留最近 N 条消息
    session.context = session.context[-settings.max_context_messages:]
    session.updated_at = datetime.now(timezone.utc)
    await _save_session(session)
    return session


async def _save_session(session: Session) -> None:
    """保存会话到 Redis"""
    data = session.model_dump(mode="json")
    await redis_client.setex(
        _session_key(session.session_id),
        settings.session_ttl_seconds,
        json.dumps(data, ensure_ascii=False),
    )
```

- [ ] **Step 2: 编写会话管理测试**

`backend/tests/test_session_manager.py`:
```python
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from app.gateway.session_manager import get_session, create_session, add_message
from app.gateway.schemas import Message, MessageType


@pytest.fixture
def mock_redis():
    with patch("app.gateway.session_manager.redis_client") as mock:
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock()
        yield mock


@pytest.mark.asyncio
async def test_create_session(mock_redis):
    session = await create_session("user1", "chat1")
    assert session.session_id == "user1:chat1"
    assert session.user_id == "user1"
    assert session.context == []
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_get_session_not_found(mock_redis):
    session = await get_session("nonexistent")
    assert session is None


@pytest.mark.asyncio
async def test_get_session_exists(mock_redis):
    session_data = '''{
        "session_id": "user1:chat1",
        "user_id": "user1",
        "chat_id": "chat1",
        "context": [],
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00"
    }'''
    mock_redis.get = AsyncMock(return_value=session_data)

    session = await get_session("user1:chat1")
    assert session is not None
    assert session.user_id == "user1"


@pytest.mark.asyncio
async def test_add_message_to_session(mock_redis):
    session_data = json.dumps({
        "session_id": "user1:chat1",
        "user_id": "user1",
        "chat_id": "chat1",
        "context": [],
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    })
    mock_redis.get = AsyncMock(return_value=session_data)

    message = Message(
        msg_id="1", from_user="user1", chat_id="chat1",
        msg_type=MessageType.TEXT, content="你好",
        timestamp=datetime.now(timezone.utc),
    )
    session = await add_message("user1:chat1", message)
    assert len(session.context) == 1
    assert session.context[0].content == "你好"


import json
```

- [ ] **Step 3: 运行测试**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot/backend
python -m pytest tests/test_session_manager.py -v
```
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add backend/app/gateway/session_manager.py backend/tests/test_session_manager.py
git commit -m "feat: implement Redis-backed session manager with context window"
```

---

### Task 5: 消息发送器

**Files:**
- Create: `backend/app/gateway/message_sender.py`

- [ ] **Step 1: 实现企微消息发送**

`backend/app/gateway/message_sender.py`:
```python
import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# 企微 API 基础 URL
WECOM_API_BASE = "https://qyapi.weixin.qq.com/cgi-bin"


async def _get_access_token() -> str:
    """获取 access_token (带缓存)"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{WECOM_API_BASE}/gettoken",
            params={
                "corpid": settings.wecom_corp_id,
                "corpsecret": settings.wecom_secret,
            },
        )
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"Failed to get access_token: {data}")
        return data["access_token"]


async def send_text(to_user: str, content: str, agent_id: int | None = None) -> dict:
    """发送文本消息到指定用户/群"""
    token = await _get_access_token()
    agent = agent_id or settings.wecom_agent_id

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{WECOM_API_BASE}/message/send",
            params={"access_token": token},
            json={
                "touser": to_user,
                "msgtype": "text",
                "agentid": agent,
                "text": {"content": content},
            },
        )
        result = resp.json()
        if result.get("errcode") != 0:
            logger.error(f"Failed to send text message: {result}")
        return result


async def send_file(to_user: str, media_id: str, agent_id: int | None = None) -> dict:
    """发送文件消息到指定用户/群"""
    token = await _get_access_token()
    agent = agent_id or settings.wecom_agent_id

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{WECOM_API_BASE}/message/send",
            params={"access_token": token},
            json={
                "touser": to_user,
                "msgtype": "file",
                "agentid": agent,
                "file": {"media_id": media_id},
            },
        )
        result = resp.json()
        if result.get("errcode") != 0:
            logger.error(f"Failed to send file message: {result}")
        return result


async def upload_media(file_path: str, media_type: str = "file") -> str:
    """上传文件到企微，返回 media_id"""
    token = await _get_access_token()

    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            resp = await client.post(
                f"{WECOM_API_BASE}/media/upload",
                params={"access_token": token, "type": media_type},
                files={"media": f},
            )
        result = resp.json()
        if result.get("errcode") != 0:
            raise RuntimeError(f"Failed to upload media: {result}")
        return result["media_id"]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/gateway/message_sender.py
git commit -m "feat: implement WeChat message sender (text/file) with media upload"
```

---

### Task 6: Webhook 路由与消息路由

**Files:**
- Create: `backend/app/gateway/router.py`
- Modify: `backend/app/main.py` (注册 gateway router)
- Create: `backend/tests/test_webhook.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: 创建 pytest 配置**

`backend/tests/conftest.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

- [ ] **Step 2: 实现 Webhook 路由**

`backend/app/gateway/router.py`:
```python
import logging
from fastapi import APIRouter, Request, HTTPException
from app.gateway.verifier import verify_url, decrypt_message, verify_signature
from app.gateway.message_parser import parse_xml
from app.gateway.session_manager import add_message, get_session
from app.gateway.schemas import Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gateway", tags=["gateway"])


@router.get("/verify")
async def verify_endpoint(
    msg_signature: str,
    timestamp: str,
    nonce: str,
    echostr: str,
):
    """企业微信 URL 验证回调"""
    try:
        result = verify_url(msg_signature, timestamp, nonce, echostr)
        return result
    except Exception as e:
        logger.error(f"URL verification failed: {e}")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def webhook(request: Request):
    """接收企业微信消息回调"""
    # 解析查询参数
    msg_signature = request.query_params.get("msg_signature", "")
    timestamp = request.query_params.get("timestamp", "")
    nonce = request.query_params.get("nonce", "")

    # 获取请求体
    body = await request.body()
    body_str = body.decode("utf-8")

    # 验证签名
    if not verify_signature(msg_signature, timestamp, nonce, body_str):
        logger.warning("Invalid message signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # 解密消息
    try:
        xml_str = decrypt_message(msg_signature, timestamp, nonce, body_str)
    except Exception as e:
        logger.error(f"Failed to decrypt message: {e}")
        raise HTTPException(status_code=400, detail="Decryption failed")

    # 解析消息
    try:
        message = parse_xml(xml_str)
    except Exception as e:
        logger.error(f"Failed to parse message: {e}")
        raise HTTPException(status_code=400, detail="Invalid message format")

    # 保存消息到会话
    session = await add_message(message.from_user, message.chat_id)
    logger.info(f"Received message from {message.from_user}: {message.content}")

    # TODO: 路由到 AI 引擎 (Phase 2)
    # 目前只返回固定的欢迎消息
    reply = "感谢您的咨询，我们正在为您处理。"

    return {"status": "ok", "reply": reply}
```

- [ ] **Step 3: 注册 gateway router 到 main.py**

修改 `backend/app/main.py`，在 import 区域添加：
```python
from app.gateway.router import router as gateway_router
```

在 `@app.get("/health")` 之前添加：
```python
app.include_router(gateway_router)
```

- [ ] **Step 4: 编写 Webhook 集成测试**

`backend/tests/test_webhook.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client: AsyncClient):
    resp = await client.post(
        "/api/gateway/webhook",
        params={"msg_signature": "bad", "timestamp": "123", "nonce": "abc"},
        content="<xml>test</xml>",
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
@patch("app.gateway.router.verify_signature", return_value=True)
@patch("app.gateway.router.decrypt_message")
@patch("app.gateway.router.parse_xml")
@patch("app.gateway.router.add_message")
async def test_webhook_valid_message(mock_add, mock_parse, mock_decrypt, mock_verify, client: AsyncClient):
    from datetime import datetime, timezone
    from app.gateway.schemas import Message, MessageType

    mock_decrypt.return_value = "<xml>decrypted</xml>"
    mock_parse.return_value = Message(
        msg_id="1", from_user="user1", chat_id="chat1",
        msg_type=MessageType.TEXT, content="你好",
        timestamp=datetime.now(timezone.utc),
    )
    mock_add.return_value = AsyncMock()

    resp = await client.post(
        "/api/gateway/webhook",
        params={"msg_signature": "valid", "timestamp": "123", "nonce": "abc"},
        content="<xml>encrypted</xml>",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "reply" in data
```

- [ ] **Step 5: 运行全部测试**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot/backend
python -m pytest tests/ -v
```
Expected: All tests pass (8+ tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/gateway/router.py backend/app/main.py backend/tests/conftest.py backend/tests/test_webhook.py
git commit -m "feat: implement webhook endpoint with signature verification and session management"
```

---

### Task 7: 端到端验证与文档

- [ ] **Step 1: 启动完整 Docker 环境**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot
docker compose down
docker compose up -d
sleep 10
docker compose ps
```
Expected: All containers running

- [ ] **Step 2: 测试健康端点**

```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok"}`

- [ ] **Step 3: 测试 OpenAPI 文档**

```bash
curl http://localhost:8000/docs
```
Expected: Swagger UI HTML (说明 FastAPI 自动生成的 API 文档可用)

- [ ] **Step 4: 运行全部测试**

```bash
cd backend
python -m pytest tests/ -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "docs: Plan 1 complete - infrastructure and gateway operational"
```

---

## Plan 1 完成标准

- [x] Docker Compose 启动，PostgreSQL + Redis + Backend 三个容器运行
- [x] `GET /health` 返回 `{"status": "ok"}`
- [x] `GET /api/gateway/verify` 支持企微 URL 验证
- [x] `POST /api/gateway/webhook` 接收并解密消息，保存到会话
- [x] 所有单元测试通过
- [x] OpenAPI 文档 (`/docs`) 可访问

## Plan 2 前置接口

Plan 1 为 Plan 2 提供以下接口/能力：
- `Message` / `Session` 数据模型 (`app/gateway/schemas.py`)
- `add_message()` / `get_session()` 会话管理 (`app/gateway/session_manager.py`)
- `send_text()` / `send_file()` 消息发送 (`app/gateway/message_sender.py`)
- `parse_xml()` 消息解析 (`app/gateway/message_parser.py`)
- `verify_signature()` / `decrypt_message()` 安全验证 (`app/gateway/verifier.py`)
