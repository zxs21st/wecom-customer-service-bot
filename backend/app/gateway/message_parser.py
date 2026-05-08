import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from app.gateway.schemas import Message, MessageType

# XML 标签到 MessageType 的映射
TYPE_MAP = {
    "text": MessageType.TEXT,
    "image": MessageType.IMAGE,
    "voice": MessageType.VOICE,
    "video": MessageType.VIDEO,
    "file": MessageType.FILE,
    "link": MessageType.LINK,
}


def parse_xml(xml_str: str) -> Message:
    """解析企微消息 XML 为 Message 对象"""
    root = ET.fromstring(xml_str)

    msg_type_str = root.findtext("MsgType", "text")
    msg_type = TYPE_MAP.get(msg_type_str, MessageType.TEXT)

    # 文本消息取 Content，其他类型取 MediaId 或 Url
    if msg_type == MessageType.TEXT:
        content = root.findtext("Content", "")
    else:
        content = root.findtext("MediaId", "") or root.findtext("Url", "")

    timestamp = int(root.findtext("CreateTime", "0"))

    return Message(
        msg_id=root.findtext("MsgId", ""),
        from_user=root.findtext("FromUserName", ""),
        chat_id=root.findtext("AgentID", ""),
        msg_type=msg_type,
        content=content,
        timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
    )
