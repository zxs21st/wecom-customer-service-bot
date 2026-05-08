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
