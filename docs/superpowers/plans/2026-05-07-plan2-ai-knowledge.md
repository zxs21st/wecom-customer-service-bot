# Plan 2: AI 引擎与知识库 - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现基于 RAG 的智能问答引擎，支持意图识别、知识检索、回答生成。

**Architecture:** LiteLLM 驱动意图分类和回答生成，PostgreSQL pgvector 存储知识向量，实现完整的 RAG 检索增强生成流程。

**Tech Stack:** LiteLLM, LangChain, pgvector, SQLAlchemy, FastAPI, pytest

**Depends on:** Plan 1 (基础设施、消息模型、会话管理、消息发送)

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/models/knowledge.py` | 新建 | 知识文档 + 向量 SQLAlchemy 模型 |
| `backend/app/ai_engine/schemas.py` | 新建 | AI 请求/响应 Pydantic 模型 |
| `backend/app/ai_engine/intent_classifier.py` | 新建 | 意图分类 (LLM-based) |
| `backend/app/ai_engine/response_generator.py` | 新建 | 回答生成 (Prompt + 知识注入) |
| `backend/app/ai_engine/prompt_templates.py` | 新建 | 各意图类型的系统 Prompt |
| `backend/app/ai_engine/router.py` | 新建 | AI 对话 API 路由 |
| `backend/app/knowledge/document_ingestor.py` | 新建 | 文档上传 → 解析 → 分块 → 向量化 |
| `backend/app/knowledge/chunker.py` | 新建 | 文本分块策略 |
| `backend/app/knowledge/embedding_service.py` | 新建 | Embedding API 封装 |
| `backend/app/knowledge/vector_search.py` | 新建 | pgvector 相似度搜索 |
| `backend/app/knowledge/router.py` | 新建 | 知识库 CRUD + 搜索 API |
| `backend/app/knowledge/schemas.py` | 新建 | 知识库请求/响应模型 |
| `backend/migrations/versions/001_knowledge_tables.py` | 新建 | Alembic 迁移 |
| `backend/tests/test_intent_classifier.py` | 新建 | 意图分类测试 |
| `backend/tests/test_rag_pipeline.py` | 新建 | RAG 端到端测试 |
| `backend/tests/test_document_ingestor.py` | 新建 | 文档入库测试 |
| `backend/tests/test_vector_search.py` | 新建 | 向量搜索测试 |

---

### Task 1: 知识数据模型与迁移

**Files:**
- Create: `backend/app/models/knowledge.py`
- Create: `backend/migrations/versions/001_knowledge_tables.py`
- Modify: `backend/app/models/__init__.py` (导出 knowledge models)

- [ ] **Step 1: 创建知识模型**

`backend/app/models/knowledge.py`:
```python
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100))  # product_knowledge, config_guide, faq, after_sales
    content: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSONB, name="metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    vectors: Mapped[list["KnowledgeVector"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class KnowledgeVector(Base):
    __tablename__ = "knowledge_vector"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_document.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[str] = mapped_column(
        "embedding",
        String,  # pgvector column manageded by extension, mapped as string for now
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="vectors")
```

> 注意：pgvector 的 `vector(1536)` 类型需要通过 `pgvector.sqlalchemy.Vector` 映射。需要安装 `pgvector` Python 包。

更新 `backend/app/models/__init__.py`:
```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so they're registered with Base.metadata
# isort: skip_file
from app.models import knowledge  # noqa: F401
```

- [ ] **Step 2: 创建 Alembic 迁移**

`backend/migrations/versions/001_knowledge_tables.py`:
```python
"""create knowledge_document and knowledge_vector tables

Revision ID: 001
Revises:
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 启用 pgvector 扩展
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_document",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "knowledge_vector",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("knowledge_document.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", sa.Text, nullable=True),  # pgvector column, manageded by extension
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_index("idx_vector_document", "knowledge_vector", ["document_id"])


def downgrade():
    op.drop_index("idx_vector_document", "knowledge_vector")
    op.drop_table("knowledge_vector")
    op.drop_table("knowledge_document")
    op.execute("DROP EXTENSION IF EXISTS vector")
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/knowledge.py backend/app/models/__init__.py backend/migrations/
git commit -m "feat: add knowledge document and vector models with Alembic migration"
```

---

### Task 2: Embedding 服务与向量搜索

**Files:**
- Create: `backend/app/knowledge/embedding_service.py`
- Create: `backend/app/knowledge/vector_search.py`
- Create: `backend/app/knowledge/schemas.py`

- [ ] **Step 1: 实现 Embedding 服务**

`backend/app/knowledge/embedding_service.py`:
```python
import litellm
from app.config import settings


async def embed_text(text: str) -> list[float]:
    """将文本转换为向量 (1536 维)"""
    response = await litellm.aembedding(
        model=settings.openai_embedding_model,
        input=text,
        api_key=settings.openai_api_key,
    )
    return response.data[0]["embedding"]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量将文本转换为向量"""
    response = await litellm.aembedding(
        model=settings.openai_embedding_model,
        input=texts,
        api_key=settings.openai_api_key,
    )
    return [d["embedding"] for d in response.data]
```

- [ ] **Step 2: 实现向量搜索**

`backend/app/knowledge/vector_search.py`:
```python
import json
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.knowledge.embedding_service import embed_text

logger = logging.getLogger(__name__)

# pgvector 余弦相似度搜索查询
VECTOR_SEARCH_SQL = """
SELECT kv.id, kv.document_id, kv.content, kv.chunk_index, kd.title, kd.category,
       1 - (kv.embedding::vector <=> :query_vector::vector) AS similarity
FROM knowledge_vector kv
JOIN knowledge_document kd ON kv.document_id = kd.id
ORDER BY similarity DESC
LIMIT :top_k
"""


async def search_similar(query: str, session: AsyncSession, top_k: int = 5, category_filter: str | None = None) -> list[dict]:
    """搜索与查询文本相似的知识片段"""
    # 生成查询向量
    query_vector = await embed_text(query)
    query_vector_str = json.dumps(query_vector)

    # 构建 SQL
    sql = VECTOR_SEARCH_SQL
    if category_filter:
        sql = sql.replace("LIMIT :top_k", f"AND kd.category = :category\nLIMIT :top_k")

    result = await session.execute(
        text(sql),
        {
            "query_vector": query_vector_str,
            "top_k": top_k,
            "category": category_filter,
        } if category_filter else {
            "query_vector": query_vector_str,
            "top_k": top_k,
        }
    )

    rows = result.fetchall()
    return [
        {
            "id": str(row.id),
            "document_id": str(row.document_id),
            "content": row.content,
            "chunk_index": row.chunk_index,
            "title": row.title,
            "category": row.category,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]
```

- [ ] **Step 3: 定义知识库 Schema**

`backend/app/knowledge/schemas.py`:
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, UUID4


class DocumentCreate(BaseModel):
    title: str
    category: str
    content: str
    metadata: Optional[dict] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[dict] = None


class DocumentResponse(BaseModel):
    id: UUID4
    title: str
    category: str
    content: str
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None


class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    similarity: float
    category: str
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/knowledge/embedding_service.py backend/app/knowledge/vector_search.py backend/app/knowledge/schemas.py
git commit -m "feat: implement embedding service and pgvector similarity search"
```

---

### Task 3: 文档入库与分块

**Files:**
- Create: `backend/app/knowledge/chunker.py`
- Create: `backend/app/knowledge/document_ingestor.py`

- [ ] **Step 1: 实现文本分块**

`backend/app/knowledge/chunker.py`:
```python
import re

# 默认分块配置
CHUNK_SIZE = 500      # 每块最大字符数
CHUNK_OVERLAP = 50    # 块之间重叠字符数


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """将文本按语义边界分块"""
    # 先按段落分割
    paragraphs = re.split(r"\n\s*\n", text)

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # 如果当前块 + 新段落不超过限制，追加
        if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
            current_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
        else:
            # 保存当前块
            if current_chunk:
                chunks.append(current_chunk)
            # 如果单个段落超过限制，按句子分割
            if len(paragraph) > chunk_size:
                sentences = re.split(r"(?<=[。！？.!?])", paragraph)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(sentence) > chunk_size:
                        # 强制截断
                        for i in range(0, len(sentence), chunk_size):
                            chunks.append(sentence[i:i + chunk_size])
                    elif len(current_chunk) + len(sentence) + 1 <= chunk_size:
                        current_chunk = current_chunk + " " + sentence if current_chunk else sentence
                    else:
                        chunks.append(current_chunk)
                        current_chunk = sentence
            else:
                current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
```

- [ ] **Step 2: 实现文档入库**

`backend/app/knowledge/document_ingestor.py`:
```python
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeDocument, KnowledgeVector
from app.knowledge.chunker import chunk_text
from app.knowledge.embedding_service import embed_texts

logger = logging.getLogger(__name__)


async def ingest_document(
    session: AsyncSession,
    title: str,
    category: str,
    content: str,
    metadata: dict | None = None,
) -> KnowledgeDocument:
    """将文档入库：解析 → 分块 → 向量化 → 存储"""
    # 1. 创建文档记录
    doc_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    document = KnowledgeDocument(
        id=doc_id,
        title=title,
        category=category,
        content=content,
        metadata=metadata,
        created_at=now,
        updated_at=now,
    )
    session.add(document)

    # 2. 分块
    chunks = chunk_text(content)
    logger.info(f"Document '{title}' split into {len(chunks)} chunks")

    # 3. 批量生成向量
    embeddings = await embed_texts(chunks)

    # 4. 创建向量记录
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vector = KnowledgeVector(
            id=uuid.uuid4(),
            document_id=doc_id,
            chunk_index=i,
            content=chunk,
            embedding=str(embedding),  # pgvector column, stored as string for now
        )
        session.add(vector)

    await session.commit()
    await session.refresh(document)
    return document
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/knowledge/chunker.py backend/app/knowledge/document_ingestor.py
git commit -m "feat: implement document ingestion with text chunking and batch embedding"
```

---

### Task 4: 意图分类与回答生成

**Files:**
- Create: `backend/app/ai_engine/schemas.py`
- Create: `backend/app/ai_engine/intent_classifier.py`
- Create: `backend/app/ai_engine/prompt_templates.py`
- Create: `backend/app/ai_engine/response_generator.py`

- [ ] **Step 1: 定义 AI 引擎 Schema**

`backend/app/ai_engine/schemas.py`:
```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class IntentType(str, Enum):
    PRODUCT_KNOWLEDGE = "product_knowledge"
    CONFIG_QUERY = "config_query"
    INVENTORY_QUERY = "inventory_query"
    PRICE_INQUIRY = "price_inquiry"
    QUOTE_REQUEST = "quote_request"
    AFTER_SALES = "after_sales"
    ORDER_TRACKING = "order_tracking"
    GENERAL_CHAT = "general_chat"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class AIRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    chat_history: list[str] = []  # 最近对话历史


class IntentResult(BaseModel):
    intent: IntentType
    confidence: float
    reply_text: Optional[str] = None


class AIResponse(BaseModel):
    intent: IntentType
    confidence: float
    reply_text: str
    sources: list[str] = []  # 引用的知识来源
```

- [ ] **Step 2: 实现意图分类**

`backend/app/ai_engine/intent_classifier.py`:
```python
import litellm
import json
import logging
from app.config import settings
from app.ai_engine.schemas import IntentType

logger = logging.getLogger(__name__)

INTENT_CLASSIFICATION_PROMPT = """你是一个意图分类器。将用户的咨询消息分类为以下意图之一：

- product_knowledge: 询问产品功能、特性、规格
- config_query: 询问产品配置、兼容性、技术参数
- inventory_query: 询问库存、供货周期、是否有货
- price_inquiry: 询问价格、折扣、优惠
- quote_request: 要求生成报价单
- after_sales: 退换货、保修、维修、投诉
- order_tracking: 查询订单状态、物流
- general_chat: 一般性对话、问候
- escalation_to_human: 明确要求转人工

请只返回 JSON 格式，不要返回其他内容：
{"intent": "意图名称", "confidence": 0.0-1.0}

用户消息: {message}
"""


async def classify_intent(message: str) -> tuple[IntentType, float]:
    """使用 LLM 对用户消息进行意图分类"""
    prompt = INTENT_CLASSIFICATION_PROMPT.format(message=message)

    response = await litellm.acompletion(
        model=settings.openai_chat_model,
        messages=[{"role": "user", "content": prompt}],
        api_key=settings.openai_api_key,
        temperature=0.1,
        max_tokens=50,
    )

    result_text = response.choices[0].message.content.strip()
    try:
        result = json.loads(result_text)
        intent = IntentType(result["intent"])
        confidence = float(result.get("confidence", 0.7))
        return intent, confidence
    except (json.JSONDecodeError, KeyError, ValueError):
        logger.warning(f"Failed to parse intent: {result_text}, defaulting to general_chat")
        return IntentType.GENERAL_CHAT, 0.5
```

- [ ] **Step 3: 实现 Prompt 模板**

`backend/app/ai_engine/prompt_templates.py`:
```python
SYSTEM_PROMPTS = {
    "product_knowledge": """你是一个专业的客服助手。基于以下知识片段回答客户关于产品的问题。

## 相关知识:
{knowledge}

## 回答要求:
1. 仅基于提供的知识回答
2. 如果知识中没有相关信息，诚实告知
3. 回答简洁专业
4. 引用知识来源时标注标题""",

    "config_query": """你是一个技术支持专家。基于以下配置指南回答客户问题。

## 相关配置信息:
{knowledge}

## 回答要求:
1. 基于提供的信息回答
2. 技术参数要准确
3. 如果信息不足，建议客户联系技术支持""",

    "after_sales": """你是一个售后客服。基于以下政策回答客户的售后问题。

## 相关售后政策:
{knowledge}

## 回答要求:
1. 清晰说明退换货/保修条件
2. 提供具体的操作流程
3. 如需人工介入，告知客户转接流程""",

    "general_chat": """你是一个友好的客服助手。请礼貌地回应客户。

如果客户询问产品相关问题，引导他们提供更多信息以便帮助。
保持友好、专业的态度。""",
}


def get_system_prompt(intent_type: str, knowledge_text: str) -> str:
    """获取对应意图的系统 Prompt"""
    template = SYSTEM_PROMPTS.get(intent_type, SYSTEM_PROMPTS["general_chat"])
    return template.format(knowledge=knowledge_text)
```

- [ ] **Step 4: 实现回答生成**

`backend/app/ai_engine/response_generator.py`:
```python
import litellm
import logging
from app.config import settings
from app.ai_engine.schemas import IntentType, AIResponse
from app.ai_engine.prompt_templates import get_system_prompt

logger = logging.getLogger(__name__)


async def generate_response(
    intent: IntentType,
    message: str,
    knowledge_results: list[dict],
    chat_history: list[dict] | None = None,
) -> AIResponse:
    """基于意图和知识检索结果生成回答"""
    # 构建知识文本
    knowledge_text = ""
    sources = []
    for i, result in enumerate(knowledge_results, 1):
        knowledge_text += f"[{i}] {result.get('title', '未知')}: {result['content']}\n\n"
        sources.append(result.get("title", "未知来源"))

    # 获取系统 Prompt
    system_prompt = get_system_prompt(intent.value, knowledge_text)

    # 构建消息历史
    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": message})

    # 调用 LLM
    response = await litellm.acompletion(
        model=settings.openai_chat_model,
        messages=messages,
        api_key=settings.openai_api_key,
        temperature=0.3,
        max_tokens=1000,
    )

    reply = response.choices[0].message.content.strip()

    return AIResponse(
        intent=intent,
        confidence=0.8,  # 生成成功时默认置信度
        reply_text=reply,
        sources=sources,
    )
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/ai_engine/schemas.py backend/app/ai_engine/intent_classifier.py backend/app/ai_engine/prompt_templates.py backend/app/ai_engine/response_generator.py
git commit -m "feat: implement intent classification and AI response generation with prompt templates"
```

---

### Task 5: AI 对话路由与知识库 API

**Files:**
- Create: `backend/app/ai_engine/router.py`
- Create: `backend/app/knowledge/router.py`

- [ ] **Step 1: 创建 AI 对话路由**

`backend/app/ai_engine/router.py`:
```python
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.ai_engine.schemas import AIRequest, AIResponse, IntentType
from app.ai_engine.intent_classifier import classify_intent
from app.ai_engine.response_generator import generate_response
from app.knowledge.vector_search import search_similar

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
        return AIResponse(
            intent=intent,
            confidence=confidence,
            reply_text="抱歉，这个问题我暂时无法准确回答。正在为您转接人工客服，请稍等。",
            sources=[],
        )

    # 3. 一般闲聊 → 直接回复
    if intent == IntentType.GENERAL_CHAT:
        response = await generate_response(intent, request.message, [])
        return response

    # 4. 知识检索 → RAG 回答
    # 根据意图确定搜索类别
    category_map = {
        IntentType.PRODUCT_KNOWLEDGE: "product_knowledge",
        IntentType.CONFIG_QUERY: "config_guide",
        IntentType.AFTER_SALES: "after_sales",
    }
    category = category_map.get(intent)

    # 搜索相关知识
    results = await search_similar(request.message, db, top_k=5, category_filter=category)
    logger.info(f"Found {len(results)} relevant knowledge pieces")

    # 生成回答
    response = await generate_response(intent, request.message, results, request.chat_history)
    response.confidence = confidence
    return response


@router.post("/intent")
async def classify(request: AIRequest):
    """仅返回意图分类结果 (调试用)"""
    intent, confidence = await classify_intent(request.message)
    return {"intent": intent.value, "confidence": confidence}
```

- [ ] **Step 2: 创建知识库路由**

`backend/app/knowledge/router.py`:
```python
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models.knowledge import KnowledgeDocument
from app.knowledge.schemas import DocumentCreate, DocumentUpdate, DocumentResponse, SearchRequest, SearchResult
from app.knowledge.document_ingestor import ingest_document
from app.knowledge.vector_search import search_similar

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/documents", response_model=DocumentResponse)
async def create_document(data: DocumentCreate, db: AsyncSession = Depends(get_db)):
    """录入知识文档"""
    doc = await ingest_document(
        db,
        title=data.title,
        category=data.category,
        content=data.content,
        metadata=data.metadata,
    )
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        content=doc.content,
        metadata=doc.metadata,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """获取知识文档详情"""
    result = await db.get(KnowledgeDocument, doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=result.id,
        title=result.title,
        category=result.category,
        content=result.content,
        metadata=result.metadata,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(category: str | None = None, db: AsyncSession = Depends(get_db)):
    """列出知识文档"""
    from sqlalchemy import select
    query = select(KnowledgeDocument)
    if category:
        query = query.where(KnowledgeDocument.category == category)
    query = query.order_by(KnowledgeDocument.created_at.desc())
    result = await db.execute(query)
    docs = result.scalars().all()
    return [
        DocumentResponse(
            id=d.id, title=d.title, category=d.category, content=d.content,
            metadata=d.metadata, created_at=d.created_at, updated_at=d.updated_at,
        )
        for d in docs
    ]


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """删除知识文档"""
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
    return {"status": "ok"}


@router.post("/search", response_model=list[SearchResult])
async def search(data: SearchRequest, db: AsyncSession = Depends(get_db)):
    """搜索知识"""
    results = await search_similar(data.query, db, top_k=data.top_k, category_filter=data.category)
    return [
        SearchResult(
            id=r["id"],
            title=r["title"],
            content=r["content"][:300],  # 截断预览
            similarity=r["similarity"],
            category=r["category"],
        )
        for r in results
    ]
```

- [ ] **Step 3: 注册路由到 main.py**

修改 `backend/app/main.py`，添加 imports 和 router 注册：
```python
from app.ai_engine.router import router as ai_router
from app.knowledge.router import router as knowledge_router

# 在 app.include_router(gateway_router) 之后添加:
app.include_router(ai_router)
app.include_router(knowledge_router)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/ai_engine/router.py backend/app/knowledge/router.py backend/app/main.py
git commit -m "feat: add AI chat and knowledge base CRUD API endpoints"
```

---

### Task 6: 测试

**Files:**
- Create: `backend/tests/test_intent_classifier.py`
- Create: `backend/tests/test_rag_pipeline.py`
- Create: `backend/tests/test_document_ingestor.py`
- Create: `backend/tests/test_vector_search.py`

- [ ] **Step 1: 意图分类测试**

`backend/tests/test_intent_classifier.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock
from app.ai_engine.intent_classifier import classify_intent
from app.ai_engine.schemas import IntentType


@pytest.mark.asyncio
async def test_classify_price_inquiry():
    with patch("app.ai_engine.intent_classifier.litellm.acompletion") as mock:
        mock.return_value = AsyncMock()
        mock.return_value.choices = [
            AsyncMock(message=AsyncMock(content='{"intent": "price_inquiry", "confidence": 0.9}'))
        ]

        intent, confidence = await classify_intent("这个产品多少钱？")
        assert intent == IntentType.PRICE_INQUIRY
        assert confidence == 0.9


@pytest.mark.asyncio
async def test_classify_after_sales():
    with patch("app.ai_engine.intent_classifier.litellm.acompletion") as mock:
        mock.return_value = AsyncMock()
        mock.return_value.choices = [
            AsyncMock(message=AsyncMock(content='{"intent": "after_sales", "confidence": 0.85}'))
        ]

        intent, confidence = await classify_intent("我想退货，怎么操作？")
        assert intent == IntentType.AFTER_SALES


@pytest.mark.asyncio
async def test_classify_fallback():
    with patch("app.ai_engine.intent_classifier.litellm.acompletion") as mock:
        mock.return_value = AsyncMock()
        mock.return_value.choices = [
            AsyncMock(message=AsyncMock(content="invalid json"))
        ]

        intent, confidence = await classify_intent("随便聊聊")
        assert intent == IntentType.GENERAL_CHAT
        assert confidence == 0.5
```

- [ ] **Step 2: 向量搜索测试**

`backend/tests/test_vector_search.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock
from app.knowledge.vector_search import search_similar


@pytest.mark.asyncio
async def test_search_returns_results():
    mock_results = [
        (1, "doc1", "content A", 0, "产品A", "product_knowledge", 0.92),
        (2, "doc2", "content B", 1, "产品B", "product_knowledge", 0.85),
    ]

    with patch("app.knowledge.vector_search.embed_text", return_value=[0.1] * 1536):
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.fetchall.return_value = mock_results

        results = await search_similar("产品规格", mock_session, top_k=2)
        assert len(results) == 2
        assert results[0]["title"] == "产品A"
        assert results[0]["similarity"] == 0.92
```

- [ ] **Step 3: 文档入库测试**

`backend/tests/test_document_ingestor.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.knowledge.document_ingestor import ingest_document


@pytest.mark.asyncio
async def test_ingest_document_splits_and_embeds():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    with patch("app.knowledge.document_ingestor.chunk_text") as mock_chunk:
        mock_chunk.return_value = ["chunk1", "chunk2"]
        with patch("app.knowledge.document_ingestor.embed_texts") as mock_embed:
            mock_embed.return_value = [[0.1] * 1536, [0.2] * 1536]

            doc = await ingest_document(
                mock_session,
                title="测试产品",
                category="product_knowledge",
                content="这是一个测试产品。",
            )

            # 验证调用了分块和向量化
            mock_chunk.assert_called_once()
            mock_embed.assert_called_once_with(["chunk1", "chunk2"])
            mock_session.add.assert_called()
```

- [ ] **Step 4: RAG 管道测试**

`backend/tests/test_rag_pipeline.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock
from app.ai_engine.response_generator import generate_response
from app.ai_engine.schemas import IntentType


@pytest.mark.asyncio
async def test_generate_response_with_knowledge():
    knowledge_results = [
        {"title": "产品A规格", "content": "产品A尺寸为10x20x30cm，重量500g"},
    ]

    with patch("app.ai_engine.response_generator.litellm.acompletion") as mock:
        mock.return_value = AsyncMock()
        mock.return_value.choices = [
            AsyncMock(message=AsyncMock(content="产品A的尺寸为10x20x30cm，重量为500g。"))
        ]

        response = await generate_response(
            IntentType.PRODUCT_KNOWLEDGE,
            "产品A的尺寸是多少？",
            knowledge_results,
        )

        assert response.intent == IntentType.PRODUCT_KNOWLEDGE
        assert "10x20x30cm" in response.reply_text
        assert len(response.sources) == 1
        assert response.sources[0] == "产品A规格"
```

- [ ] **Step 5: 运行全部测试**

```bash
cd /Users/zhangxuesong/projects/wecom-customer-service-bot/backend
python -m pytest tests/ -v
```
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add backend/tests/test_intent_classifier.py backend/tests/test_rag_pipeline.py backend/tests/test_document_ingestor.py backend/tests/test_vector_search.py
git commit -m "test: add unit tests for intent classifier, vector search, ingestion, and RAG pipeline"
```

---

## Plan 2 完成标准

- [x] 知识文档 CRUD API 可用 (`/api/knowledge/documents`)
- [x] 知识搜索 API 可用 (`/api/knowledge/search`)
- [x] AI 对话 API 可用 (`/api/ai/chat`) — 接收消息 → 意图分类 → RAG → 回答
- [x] 文档入库 → 自动分块 → 向量化 → 可搜索
- [x] 低置信度意图自动转人工回复
- [x] 所有单元测试通过

## Plan 3 前置接口

Plan 2 为 Plan 3 提供以下接口/能力：
- `IntentType` 枚举 — 用于路由到不同处理器
- `AIResponse` 模型 — 包含回答文本和知识来源
- `classify_intent()` — 报价/售后意图分类
- `generate_response()` — 基于知识的回答生成
