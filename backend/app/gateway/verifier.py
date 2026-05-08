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
