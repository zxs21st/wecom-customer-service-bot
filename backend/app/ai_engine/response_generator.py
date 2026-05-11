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
        model="anthropic/qwen3.6-plus",
        messages=messages,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
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
