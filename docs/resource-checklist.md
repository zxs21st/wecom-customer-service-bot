# 企业微信客服机器人 - 资源准备清单

> 创建日期: 2026-05-07 | 项目: wecom-customer-service-bot

---

## P0 — 必须有 (开发前必须到位)

### 1. 企业微信管理员权限

| 项目 | 获取方式 | 说明 |
|------|---------|------|
| 企业微信管理员账号 | 联系企业 IT 管理员 | 需要登录企业微信管理后台 qy.weixin.qq.com |
| Corp ID (企业ID) | 管理后台 → 我的企业 → 企业信息 | 企业唯一标识，格式如 `ww1234567890abcdef` |
| 创建自建应用 | 管理后台 → 应用管理 → 自建 → 创建应用 | 应用名称如 "智能客服助手" |
| Agent ID | 创建应用后在应用详情页可见 | 应用的 AgentId，数字格式 |
| Secret | 应用详情页 → Secret → 点击"查看/重置" | 应用的 Secret，仅创建时可见一次 |
| Token + EncodingAESKey | 应用详情页 → 设置API接收消息 → 随机生成 | 消息回调加密验证用 |

**配置步骤：**
1. 登录 [企业微信管理后台](https://qy.weixin.qq.com)
2. 进入「应用管理」→「自建」→「创建应用」
3. 填写应用名称（如"智能客服助手"）、上传 logo、设置可见范围
4. 创建完成后，在应用详情页记录 **Corp ID**、**Agent ID**、**Secret**
5. 点击「设置API接收消息」→ 点击「随机获取」生成 **Token** 和 **EncodingAESKey**
6. 设置回调 URL（需要公网可达，见下方"服务器"部分）

### 2. AI API Key

| 项目 | 推荐值 | 获取方式 |
|------|--------|---------|
| API Key | 通义千问 DashScope | [控制台](https://dashscope.console.aliyun.com) → API-KEY |
| Embedding 模型 | `text-embedding-v3` | 通义千问 Embedding 系列，中文效果好 |
| Chat 模型 | `qwen-plus` 或 `qwen-max` | qwen-plus 性价比高，max 效果最好 |

**备选方案：** 如果使用 OpenAI 兼容 API：
- `OPENAI_API_KEY`: 你的 API Key
- `OPENAI_CHAT_MODEL`: 如 `gpt-4o`、`gpt-4o-mini`
- `OPENAI_EMBEDDING_MODEL`: `text-embedding-3-small`

### 3. 公网可达的地址

| 方案 | 适用场景 | 说明 |
|------|---------|------|
| **云服务器** (推荐) | 生产环境 | 阿里云/腾讯云轻量服务器 (2核4G起步) |
| **内网穿透** | 开发测试 | ngrok / Cloudflare Tunnel / frp |
| **本地 + 端口转发** | 开发测试 | 路由器映射公网 IP:8000 → 内网:8000 |

**云服务器推荐配置：**
- 2 核 CPU / 4 GB 内存 / 50 GB SSD
- 操作系统: Ubuntu 22.04 / Debian 12
- 公网 IP + 安全组放行 8000 端口

**内网穿透 (开发阶段)：**
```bash
# ngrok 示例
ngrok http 8000
# 会生成一个临时公网 URL，如 https://xxx.ngrok-free.app
```

---

## P1 — 开发阶段需要

### 4. 开发环境

| 项目 | 要求 |
|------|------|
| Docker Desktop | 已安装 (用于本地 Docker Compose) |
| Python | 3.12+ (本地开发) |
| Node.js | 18+ (前端开发) |
| Git | 版本控制 |

### 5. 企业微信测试群

| 步骤 | 操作 |
|------|------|
| 1 | 在企业微信中创建一个测试群 |
| 2 | 将"智能客服助手"应用添加到群聊 |
| 3 | 在群里发消息测试机器人回调 |

### 6. 域名 + HTTPS (可选)

| 说明 | 备注 |
|------|------|
| 企微支持 HTTP 回调 | 开发阶段不需要 HTTPS |
| 生产环境推荐 HTTPS | 可使用 Let's Encrypt 免费证书 |
| 域名备案 | 国内服务器需要 ICP 备案 |

---

## P2 — Plan 5 阶段需要 (不急于开发)

### 7. 开龙进销存数据库访问

| 项目 | 说明 |
|------|------|
| SQL Server 版本 | 确认版本 (2008/2012/2016/2019/2022) |
| 数据库名称 | 开龙进销存使用的数据库名 |
| 服务器地址 | SQL Server IP 地址和端口 (默认 1433) |
| 只读账号 | 创建专用账号 `wecom_reader`，仅授予 SELECT 权限 |
| 网络连通 | 应用服务器需能访问 SQL Server 1433 端口 |
| 表结构信息 | 用 SSMS 查看或联系开龙技术支持获取数据字典 |

**表结构查看方法：**
```sql
-- 查看所有表
SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';

-- 查看表字段
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '目标表名';
```

**需要关注的核心表类型：**
| 业务域 | 需要确认的表 | 关键字段 |
|--------|-------------|----------|
| 产品目录 | 商品表/物料表 | SKU、名称、规格、分类、单位 |
| 库存 | 库存表 | SKU、仓库、可用数量 |
| 价格 | 价格表 | SKU、标准价、会员价、促销价 |
| 客户 | 客户表 | 客户编号、名称、联系方式 |

---

## 环境变量汇总

项目启动时需要配置的环境变量（详见 `backend/.env.example`）：

### 必须配置

| 变量名 | 示例值 | 来源 |
|--------|--------|------|
| `WECOM_CORP_ID` | `ww1234567890abcdef` | 企业微信管理后台 |
| `WECOM_TOKEN` | `随机字符串` | 应用回调配置 |
| `WECOM_ENCODING_AES_KEY` | `43 位随机字符串` | 应用回调配置 |
| `WECOM_AGENT_ID` | `1000002` | 应用详情页 |
| `WECOM_SECRET` | `Secret 值` | 应用详情页 |
| `OPENAI_API_KEY` | `sk-xxx` | DashScope / OpenAI 控制台 |
| `OPENAI_CHAT_MODEL` | `qwen-plus` | 选择的聊天模型 |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-v3` | 选择的 Embedding 模型 |

### 默认值可用

| 变量名 | 默认值 |
|--------|--------|
| `DATABASE_URL` | `postgresql+asyncpg://wecom:wecom123@localhost:5432/wecom_bot` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `DB_PASSWORD` | `wecom123` |

### Plan 5 需要

| 变量名 | 说明 |
|--------|------|
| `INVENTORY_DB_DRIVER` | 如 `ODBC Driver 18 for SQL Server` |
| `INVENTORY_DB_SERVER` | SQL Server 地址:端口 |
| `INVENTORY_DB_NAME` | 数据库名 |
| `INVENTORY_DB_USER` | 只读用户名 |
| `INVENTORY_DB_PASSWORD` | 只读密码 |
| `INVENTORY_DB_ENCRYPT` | `yes` 或 `no` |
| `INVENTORY_DB_TRUST_CERT` | `yes` 或 `no` |

---

## 检查清单

- [ ] 企业微信管理员账号可用
- [ ] Corp ID 已记录
- [ ] 自建应用已创建
- [ ] Agent ID 已记录
- [ ] Secret 已记录
- [ ] Token + EncodingAESKey 已记录
- [ ] AI API Key 已获取
- [ ] 云服务器或内网穿透已准备
- [ ] Docker Desktop 已安装
- [ ] Python 3.12+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] 企业微信测试群已创建
- [ ] (Plan 5) 开龙进销存 SQL Server 可访问
- [ ] (Plan 5) 表结构信息已获取
