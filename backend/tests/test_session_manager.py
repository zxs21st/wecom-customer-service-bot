import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from app.gateway.session_manager import get_session, create_session, add_message
from app.gateway.schemas import Message, MessageType


@pytest.fixture
def mock_redis():
    with patch("app.gateway.session_manager.redis_client") as mock:
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock()
        yield mock


@pytest.mark.asyncio
async def test_create_session(mock_redis):
    session = await create_session("user1", "chat1")
    assert session.session_id == "user1:chat1"
    assert session.user_id == "user1"
    assert session.context == []
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_get_session_not_found(mock_redis):
    session = await get_session("nonexistent")
    assert session is None


@pytest.mark.asyncio
async def test_get_session_exists(mock_redis):
    session_data = '''{
        "session_id": "user1:chat1",
        "user_id": "user1",
        "chat_id": "chat1",
        "context": [],
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00"
    }'''
    mock_redis.get = AsyncMock(return_value=session_data)

    session = await get_session("user1:chat1")
    assert session is not None
    assert session.user_id == "user1"


@pytest.mark.asyncio
async def test_add_message_to_session(mock_redis):
    session_data = json.dumps({
        "session_id": "user1:chat1",
        "user_id": "user1",
        "chat_id": "chat1",
        "context": [],
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    })
    mock_redis.get = AsyncMock(return_value=session_data)

    session = await add_message("user1", "chat1")
    assert session.session_id == "user1:chat1"
