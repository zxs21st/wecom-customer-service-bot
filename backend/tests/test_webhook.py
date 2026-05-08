import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
@patch("app.gateway.router.verify_signature", return_value=False)
async def test_webhook_invalid_signature(mock_verify, client: AsyncClient):
    resp = await client.post(
        "/api/gateway/webhook",
        params={"msg_signature": "bad", "timestamp": "123", "nonce": "abc"},
        content="<xml><Encrypt>test</Encrypt></xml>",
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
@patch("app.gateway.router.verify_signature", return_value=True)
@patch("app.gateway.router.decrypt_message")
@patch("app.gateway.router.parse_xml")
@patch("app.gateway.router.add_message")
async def test_webhook_valid_message(mock_add, mock_parse, mock_decrypt, mock_verify, client: AsyncClient):
    from app.gateway.schemas import Message, MessageType

    mock_decrypt.return_value = "<xml>decrypted</xml>"
    mock_parse.return_value = Message(
        msg_id="1", from_user="user1", chat_id="chat1",
        msg_type=MessageType.TEXT, content="你好",
        timestamp=datetime.now(timezone.utc),
    )
    mock_add.return_value = AsyncMock()

    resp = await client.post(
        "/api/gateway/webhook",
        params={"msg_signature": "valid", "timestamp": "123", "nonce": "abc"},
        content="<xml>encrypted</xml>",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "reply" in data
