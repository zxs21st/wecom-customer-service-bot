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
