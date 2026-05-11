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
    openai_base_url: str = ""
    openai_embedding_model: str = "text-embedding-v3"

    # WeKnora 知识库
    weknora_base_url: str = ""
    weknora_api_key: str = ""
    weknora_kb_id: str = ""

    # 会话配置
    session_ttl_seconds: int = 1800  # 30 分钟
    max_context_messages: int = 10

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
