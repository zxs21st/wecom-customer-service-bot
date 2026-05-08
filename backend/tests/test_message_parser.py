from app.gateway.message_parser import parse_xml
from app.gateway.schemas import MessageType


TEXT_XML = """<xml>
<ToUserName><![CDATA[corp123]]></ToUserName>
<FromUserName><![CDATA[user456]]></FromUserName>
<CreateTime>1700000000</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[这个产品多少钱？]]></Content>
<MsgId>12345</MsgId>
<AgentID>1000002</AgentID>
</xml>"""

IMAGE_XML = """<xml>
<ToUserName><![CDATA[corp123]]></ToUserName>
<FromUserName><![CDATA[user456]]></FromUserName>
<CreateTime>1700000000</CreateTime>
<MsgType><![CDATA[image]]></MsgType>
<MediaId><![CDATA[media_abc123]]></MediaId>
<MsgId>12346</MsgId>
<AgentID>1000002</AgentID>
</xml>"""


def test_parse_text_message():
    msg = parse_xml(TEXT_XML)
    assert msg.msg_id == "12345"
    assert msg.from_user == "user456"
    assert msg.chat_id == "1000002"
    assert msg.msg_type == MessageType.TEXT
    assert msg.content == "这个产品多少钱？"


def test_parse_image_message():
    msg = parse_xml(IMAGE_XML)
    assert msg.msg_type == MessageType.IMAGE
    assert msg.content == "media_abc123"


def test_parse_unknown_message_type():
    xml = TEXT_XML.replace("<MsgType><![CDATA[text]]></MsgType>", "<MsgType><![CDATA[unknown]]></MsgType>")
    msg = parse_xml(xml)
    assert msg.msg_type == MessageType.TEXT  # fallback to text
