import logging
from fastapi import APIRouter, Request, HTTPException
from app.gateway.verifier import verify_url, decrypt_message, verify_signature
from app.gateway.message_parser import parse_xml
from app.gateway.session_manager import add_message
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
