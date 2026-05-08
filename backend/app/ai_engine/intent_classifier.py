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
{{"intent": "意图名称", "confidence": 0.0-1.0}}

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
