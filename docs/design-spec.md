# 企业微信客服机器人 - 详细设计方案

> 版本: v1.0 | 日期: 2026-05-07

## 1. 系统概述

### 1.1 产品定位
面向企业的智能客服机器人，部署于企业微信群中，为客户提供产品知识、配置、供货情况及价格的实时咨询服务。

### 1.2 核心能力
- **智能问答**: 基于 RAG 的产品知识问答
- **实时库存**: 对接进销存系统获取实时库存
- **销售推荐**: 结合近期销售指导清单做智能推荐
- **报价生成**: 自动生成专业 PDF 报价单并发送
- **数据分析**: 咨询数据实时同步至后台管理面板

### 1.3 用户角色
| 角色 | 说明 |
|------|------|
| 终端客户 | 在企业微信群中咨询的终端用户 |
| 客服人员 | 后台管理面板使用者，管理知识库、查看咨询分析 |
| 系统管理员 | 系统配置、进销存对接配置、用户权限管理 |

## 2. 技术栈

| 层级 | 选型 | 说明 |
|------|------|------|
| 后端框架 | FastAPI (Python 3.12+) | 异步、轻量、自动 OpenAPI 文档 |
| AI 编排 | LiteLLM + LangChain | RAG pipeline、多模型切换 |
| 向量存储 | PostgreSQL + pgvector | 同时承载业务数据和向量检索 |
| 消息队列 | Redis + Celery | 异步任务、定时同步、削峰 |
| 后台前端 | React + Ant Design Pro | 企业级管理面板 |
| 报价生成 | WeasyPrint | HTML/CSS → 专业 PDF |
| 企微 SDK | wechatpy + 官方 API | 消息回调、群管理、文件发送 |

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        企业微信客户端                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  客户群聊     │  │  客服群聊     │  │  管理后台     │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
└─────────┼──────────────────┼──────────────────┼──────────────────────┘
          │ 企微回调         │ 企微回调         │ HTTP/WebSocket
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI 网关服务                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 消息接收模块  │  │ 身份验证模块  │  │ 会话管理模块  │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
└─────────┼──────────────────┼──────────────────┼──────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AI 客服引擎                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 意图识别      │  │ 知识检索      │  │ 回答生成      │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
└─────────┼──────────────────┼──────────────────┼──────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  进销存对接层    │  │  知识库 (RAG)    │  │  销售指导引擎    │         │
│  - 库存查询      │  │  - 产品资料      │  │  - 主推清单      │         │
│  - 价格查询      │  │  - 配置指南      │  │  - 促销规则      │         │
│  - 供货周期      │  │  - FAQ          │  │  - 折扣策略      │         │
└─────────────────┘  └─────────────────┘  └─────────────────┘         │
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      后台管理面板 (React)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 咨询分析      │  │ 知识库管理    │  │ 销售指导配置  │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

## 4. 详细模块设计

### 4.1 消息网关模块 (gateway/)

**职责**: 接收企业微信消息回调，解析消息内容，路由到对应处理器

**核心功能**:
1. **消息接收**: 接收企微服务器 POST 请求，支持文本、图片、文件、语音消息类型
2. **签名验证**: 验证企微消息签名 (token + encodingAESKey)
3. **消息解析**: 提取发送者 ID、群 ID、消息类型、消息内容
4. **会话路由**: 根据用户 ID 和群 ID 路由到对应会话上下文
5. **消息发送**: 封装企微 API，支持发送文本、图片、文件、链接、小程序卡片

**接口定义**:
```python
# POST /api/gateway/webhook - 企微消息回调
# POST /api/gateway/send - 主动发送消息到群
# GET  /api/gateway/verify - 企微 URL 验证

class Message:
    msg_id: str              # 消息唯一 ID
    from_user: str           # 发送者企微 ID
    chat_id: str             # 群聊 ID
    msg_type: MessageType    # text/image/file/voice
    content: str             # 消息内容
    timestamp: datetime      # 消息时间

class Session:
    session_id: str          # 会话唯一标识
    user_id: str             # 用户 ID
    chat_id: str             # 群 ID
    context: List[Message]   # 最近 N 条消息上下文
    created_at: datetime
    updated_at: datetime
```

**技术要点**:
- 使用 wechatpy 解析企微消息 XML
- 会话上下文存储在 Redis (TTL 30 分钟)
- 消息队列异步处理耗时操作 (文件下载、AI 响应)

### 4.2 AI 客服引擎 (ai_engine/)

**职责**: 意图识别、知识检索、回答生成

**核心功能**:
1. **意图分类**: 识别用户咨询意图 (产品知识/配置查询/库存查询/价格咨询/报价请求)
2. **上下文管理**: 维护多轮对话上下文，支持追问和指代消解
3. **知识检索**: 基于向量相似度检索相关知识片段
4. **回答生成**: 结合检索结果和上下文生成自然语言回复
5. **人工转接**: 当置信度低于阈值时，提示转人工客服

**意图分类模型**:
```python
class IntentType(Enum):
    PRODUCT_KNOWLEDGE = "product_knowledge"    # 产品知识
    CONFIG_QUERY = "config_query"              # 配置查询
    INVENTORY_QUERY = "inventory_query"        # 库存查询
    PRICE_INQUIRY = "price_inquiry"            # 价格咨询
    QUOTE_REQUEST = "quote_request"            # 报价请求
    AFTER_SALES = "after_sales"                # 售后问题
    ORDER_TRACKING = "order_tracking"          # 订单/工单查询
    GENERAL_CHAT = "general_chat"              # 一般闲聊
    ESCALATE_TO_HUMAN = "escalate_to_human"    # 转人工

class AIResponse:
    intent: IntentType
    confidence: float              # 置信度 0-1
    reply_text: str                # 回复文本
    quote_data: Optional[QuoteData] # 报价数据 (仅报价请求时)
    sources: List[str]             # 引用知识来源
```

**Prompt 设计**:
```
你是一个专业的客服助手，负责回答客户关于产品的咨询。

## 可用信息:
{retrieved_knowledge}
{inventory_data}
{sales_guidance}

## 回答要求:
1. 基于提供的信息回答，不编造信息
2. 如果信息不足，诚实地告知客户
3. 回答简洁专业，突出关键信息
4. 如有促销活动或推荐产品，适度提及
```

### 4.3 进销存对接层 (inventory/)

**职责**: 与现有进销存系统对接，获取实时库存、价格、供货周期

**对接方式**: 直接连接 SQL Server 数据库 (只读)

**技术选型**:
- **pyodbc** + Microsoft ODBC Driver 18 for SQL Server — 微软官方驱动，性能最好，推荐
- 备选 **pymssql** — 纯 Python 实现，无系统依赖，但性能稍弱

**Docker 镜像配置**:
```dockerfile
FROM python:3.12-slim
# 安装微软 ODBC 驱动
RUN apt-get update && apt-get install -y curl gnupg2 && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    pip install pyodbc
```

**安全策略**:
- 专用只读账号 `wecom_reader`，仅授予 SELECT 权限
- 连接字符串加密存储在环境变量中
- 数据库防火墙仅允许应用服务器 IP 访问

**核心功能**:
1. **库存查询**: 根据产品 SKU 查询实时库存数量
2. **价格查询**: 获取产品标准价格、阶梯价格、促销价格
3. **供货周期**: 查询产品预计供货时间
4. **产品目录**: 获取完整产品目录及分类信息
5. **数据缓存**: 高频查询数据缓存 (Redis, TTL 10 分钟，直连场景适当延长)
6. **慢查询保护**: 查询超时限制 (5s)，防止阻塞主流程

**表结构映射示例** (需根据实际进销存表结构调整):
```python
# 典型进销存表结构 (需适配实际 schema)
# SELECT sku, product_name, available_qty, warehouse 
# FROM inventory_stock WITH (NOLOCK) WHERE sku = ?

# SELECT sku, standard_price, tier_price_json, promo_price 
# FROM product_price WITH (NOLOCK) WHERE sku = ?
```

**NOLOCK 提示**: SQL Server 查询建议使用 `WITH (NOLOCK)` 避免读锁影响业务系统，但需注意脏读风险。库存数据短暂不一致可接受。

**接口定义**:
```python
class InventoryService:
    async def get_stock(self, sku: str) -> StockInfo
    async def get_price(self, sku: str, quantity: int) -> PriceInfo
    async def get_lead_time(self, sku: str) -> LeadTimeInfo
    async def search_products(self, keyword: str) -> List[ProductInfo]

class StockInfo:
    sku: str
    product_name: str
    available_qty: float
    warehouse_location: str
    last_updated: datetime

class PriceInfo:
    sku: str
    standard_price: float
    tier_prices: List[Tuple[int, float]]  # (min_qty, price)
    promo_price: Optional[float]
    currency: str = "CNY"

class ProductInfo:
    sku: str
    name: str
    category: str
    specifications: dict
    image_url: Optional[str]
```

**对接方式**:
- 优先使用现有进销存系统的 REST API
- 如无 API，考虑数据库直连 (只读权限)
- 数据同步频率: 实时查询 + 定时缓存更新

### 4.4 知识库管理 (knowledge/)

**职责**: 产品知识向量化存储与 RAG 检索

**核心功能**:
1. **知识录入**: 支持上传文档 (PDF/Word/Excel) 或直接录入文本
2. **文档解析**: 使用 Tika/LLM 解析文档结构，提取产品规格、配置信息
3. **向量化**: 将知识文本切片并通过 embedding 模型转换为向量
4. **检索**: 基于语义相似度检索相关知识片段
5. **知识更新**: 支持知识的增删改查，自动重新向量化

**知识库结构**:
```sql
-- 知识文档表
CREATE TABLE knowledge_document (
    id UUID PRIMARY KEY,
    title VARCHAR(255),
    category VARCHAR(100),  -- 产品知识/配置指南/FAQ
    content TEXT,
    metadata JSONB,         -- 产品SKU、版本号等
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 向量存储 (pgvector)
CREATE TABLE knowledge_vector (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES knowledge_document(id),
    chunk_index INT,
    content TEXT,
    embedding vector(1536),  -- OpenAI embedding 维度
    created_at TIMESTAMP
);
```

**RAG 检索流程**:
1. 用户问题 → embedding 模型 → 向量
2. 向量相似度搜索 (top_k=5)
3. 重排序 (可选: 使用 cross-encoder)
4. 返回相关片段给 AI 引擎

### 4.5 销售指导引擎 (sales/)

**职责**: 管理近期产品销售指导清单，提供推荐策略

**核心功能**:
1. **主推清单**: 维护近期主推产品列表
2. **促销规则**: 管理促销活动、折扣策略
3. **推荐算法**: 结合库存、利润、促销生成推荐
4. **话术模板**: 管理推荐话术，确保客服回复一致性

**数据结构**:
```python
class SalesGuidance:
    id: UUID
    product_sku: str
    priority: int                  # 推荐优先级 1-10
    promo_type: PromoType          # 折扣/满减/赠品
    discount_rate: float           # 折扣率
    start_date: date
    end_date: date
    talk_template: str             # 推荐话术模板
    is_active: bool

class Recommendation:
    product: ProductInfo
    reason: str                    # 推荐理由 (热销/促销/库存充足)
    discount_info: Optional[str]   # 折扣信息
    suggested_reply: str           # 建议回复
```

### 4.6 报价生成器 (quoting/)

**职责**: 根据咨询内容生成专业 PDF 报价单

**核心功能**:
1. **报价模板**: 支持多种报价模板 (标准/促销/定制)
2. **价格计算**: 根据数量、折扣、促销计算最终价格
3. **PDF 生成**: 使用 WeasyPrint 将 HTML 模板渲染为 PDF
4. **文件发送**: 通过企微 API 发送 PDF 到客户群
5. **报价记录**: 保存报价历史，支持追踪和统计
6. **报价转订单**: 客户确认后自动生成订单记录

**报价数据结构**:
```python
class QuoteItem:
    sku: str
    product_name: str
    specification: str
    unit_price: float
    quantity: int
    discount: float
    subtotal: float

class Quote:
    id: UUID
    quote_no: str                  # 报价单号 (自动生成)
    customer_name: str
    customer_contact: str
    items: List[QuoteItem]
    total_amount: float
    discount_total: float
    final_amount: float
    valid_until: date              # 报价有效期
    prepared_by: str               # 生成人
    created_at: datetime
    status: QuoteStatus            # draft/sent/accepted/rejected
    pdf_url: Optional[str]         # PDF 文件 URL
```

**PDF 模板设计**:
- 公司 logo + 联系方式
- 报价单号 + 日期
- 客户信息
- 产品明细表格
- 价格汇总
- 条款说明 (有效期、付款方式、交货期)

### 4.7 售后与订单管理 (after_sales/)

**职责**: 处理售后咨询，管理机器人自主产生的订单/报价记录

**设计思路**: 售后问题分两层处理：

**第一层：纯知识问答（RAG）** — 不需要对接外部系统，只要知识库有内容即可回答。

| 场景 | 示例 | 数据来源 |
|------|------|----------|
| 退换货政策 | "怎么退货？" | 知识库 RAG |
| 保修政策 | "保修期多久？" | 知识库 RAG |
| 使用说明 | "这个怎么用？" | 知识库 RAG |
| 故障排查 | "出现XX错误怎么办" | 知识库 RAG |
| 投诉流程 | "我要投诉" | 知识库 RAG |

**第二层：个人订单/工单查询** — 需要查询具体业务数据。

| 场景 | 数据来源策略 |
|------|-------------|
| 查询报价单状态 | 机器人本地 PostgreSQL（自己维护的报价/订单记录） |
| 查询进销存订单 | 对接 SQL Server 订单表（如果进销存有） |
| 查询售后工单 | 对接工单系统或本地维护 |

**机器人自主订单/报价记录表**:
```sql
-- 订单记录表 (机器人自己维护)
CREATE TABLE bot_order (
    id UUID PRIMARY KEY,
    order_no VARCHAR(50) UNIQUE,     -- 订单号 (BOT-YYYYMMDD-XXXX)
    quote_id UUID REFERENCES quote(id), -- 关联的报价单
    user_id VARCHAR(100),            -- 企微用户 ID
    chat_id VARCHAR(100),            -- 群聊 ID
    customer_name VARCHAR(100),
    items JSONB,                     -- 产品明细
    total_amount DECIMAL(10,2),
    status VARCHAR(20),              -- pending/confirmed/shipped/completed
    tracking_info TEXT,              -- 物流信息
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 售后工单表
CREATE TABLE after_sales_ticket (
    id UUID PRIMARY KEY,
    ticket_no VARCHAR(50) UNIQUE,    -- 工单号 (AS-YYYYMMDD-XXXX)
    user_id VARCHAR(100),
    chat_id VARCHAR(100),
    order_id UUID REFERENCES bot_order(id), -- 关联订单 (可选)
    issue_type VARCHAR(50),          -- return/exchange/repair/complaint
    description TEXT,
    status VARCHAR(20),              -- open/in_progress/resolved/closed
    assigned_to VARCHAR(100),        -- 分配给的处理人
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**核心功能**:
1. **售后意图识别**: 识别客户售后问题类型
2. **知识检索**: RAG 检索售后政策、操作指南
3. **工单创建**: 需要人工介入时自动创建工单
4. **订单查询**: 查询机器人自主维护的订单记录
5. **状态通知**: 订单发货/工单处理进度主动推送客户

### 4.8 咨询分析模块 (analytics/)

**职责**: 实时同步咨询数据，提供后台分析面板

**核心功能**:
1. **咨询记录**: 记录每条咨询的意图、回答、满意度
2. **实时面板**: 展示今日咨询量、热点问题、未解决问题
3. **趋势分析**: 咨询量趋势、热点问题变化
4. **客服效能**: 响应时间、解决率、客户满意度
5. **导出报表**: 支持 Excel/PDF 格式报表导出

**数据结构**:
```sql
-- 咨询记录表
CREATE TABLE consultation_record (
    id UUID PRIMARY KEY,
    session_id VARCHAR(100),
    user_id VARCHAR(100),
    chat_id VARCHAR(100),
    intent_type VARCHAR(50),
    question TEXT,
    answer TEXT,
    confidence FLOAT,
    is_resolved BOOLEAN,
    created_at TIMESTAMP
);

-- 咨询统计视图
CREATE VIEW daily_consultation_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_queries,
    COUNT(CASE WHEN is_resolved THEN 1 END) as resolved_queries,
    AVG(confidence) as avg_confidence
FROM consultation_record
GROUP BY DATE(created_at);
```

## 5. 部署架构

### 5.1 Docker Compose 配置
```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: wecom_bot
      POSTGRES_USER: wecom
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    environment:
      # 自身业务数据库 (PostgreSQL)
      DATABASE_URL: postgresql://wecom:${DB_PASSWORD}@postgres:5432/wecom_bot
      REDIS_URL: redis://redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      WECOM_CORP_ID: ${WECOM_CORP_ID}
      WECOM_AGENT_ID: ${WECOM_AGENT_ID}
      WECOM_SECRET: ${WECOM_SECRET}
      # 进销存 SQL Server 连接
      INVENTORY_DB_DRIVER: "ODBC Driver 18 for SQL Server"
      INVENTORY_DB_SERVER: ${INVENTORY_DB_HOST}
      INVENTORY_DB_NAME: ${INVENTORY_DB_NAME}
      INVENTORY_DB_USER: ${INVENTORY_DB_USER}
      INVENTORY_DB_PASSWORD: ${INVENTORY_DB_PASSWORD}
      INVENTORY_DB_ENCRYPT: "yes"
      INVENTORY_DB_TRUST_CERT: "yes"
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pg_data:
```

### 5.2 环境变量
```env
# 数据库
DB_PASSWORD=your_db_password

# AI 服务
OPENAI_API_KEY=your_openai_key
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_CHAT_MODEL=gpt-4

# 企业微信
WECOM_CORP_ID=your_corp_id
WECOM_AGENT_ID=your_agent_id
WECOM_SECRET=your_secret
WECOM_TOKEN=your_token
WECOM_ENCODING_AES_KEY=your_encoding_key

# 进销存 SQL Server 直连
INVENTORY_DB_HOST=sqlserver.yourcompany.com,1433
INVENTORY_DB_NAME=ERP_DB
INVENTORY_DB_USER=wecom_reader
INVENTORY_DB_PASSWORD=your_sql_password
```

## 6. 安全设计

### 6.1 消息安全
- 企微消息签名验证 (token + encodingAESKey)
- 敏感信息过滤 (手机号、身份证号等)
- 消息内容长度限制 (防止注入攻击)

### 6.2 数据安全
- 数据库连接使用 SSL
- 敏感数据加密存储 (客户信息、API 密钥)
- 报价文件访问权限控制

### 6.3 API 安全
- 后台管理面板 JWT 认证
- 接口限流 (Redis + sliding window)
- 进销存 API 调用频率控制

## 7. 开发计划

| 阶段 | 时间 | 内容 |
|------|------|------|
| **Phase 1** | 第 1-2 周 | 消息网关 + 基础会话管理 + 企微对接 |
| **Phase 2** | 第 3-4 周 | AI 引擎 + 意图识别 + 知识检索 (含售后知识) |
| **Phase 3** | 第 5-6 周 | 进销存对接 + 销售指导引擎 |
| **Phase 4** | 第 7-8 周 | 报价生成 + 售后工单管理 |
| **Phase 5** | 第 9-10 周 | 后台管理面板 + 咨询分析 |
| **Phase 6** | 第 11-12 周 | 测试优化 + 部署上线 |

## 8. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| SQL Server 网络隔离 | 高 | 确认防火墙规则，必要时通过跳板机/专线 |
| 进销存查询性能影响 | 中 | 使用 WITH (NOLOCK)、合理索引、Redis 缓存 |
| 表结构变更 | 中 | 建立进销存表结构变更通知机制 |
| AI 回答准确率不足 | 中 | 增加人工审核环节，持续优化知识库 |
| 企微接口频率限制 | 中 | 消息队列削峰，合理控制发送频率 |
| 向量检索性能瓶颈 | 低 | pgvector 索引优化，定期清理过期数据 |
| 售后工单缺乏处理流程 | 中 | 工单自动路由 + 超时升级机制 |

## 9. 后续扩展

- **多语言支持**: 支持中英文双语客服
- **语音识别**: 支持语音消息转文本处理
- **客户画像**: 基于咨询历史构建客户画像
- **智能外呼**: 结合企微电话能力主动回访
- **多渠道接入**: 扩展至钉钉、飞书等平台
