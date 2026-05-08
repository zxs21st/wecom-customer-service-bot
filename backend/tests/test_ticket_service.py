import pytest
from unittest.mock import AsyncMock, MagicMock
from app.after_sales.ticket_service import create_ticket, update_ticket_status


@pytest.mark.asyncio
async def test_create_ticket():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    ticket = await create_ticket(
        mock_session,
        user_id="user1",
        chat_id="chat1",
        issue_type="return",
        description="产品质量问题",
    )

    assert ticket.user_id == "user1"
    assert ticket.status == "open"
    assert ticket.ticket_no.startswith("AS-")


@pytest.mark.asyncio
async def test_update_ticket_status():
    mock_ticket = MagicMock()
    mock_ticket.status = "open"

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_ticket)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    ticket = await update_ticket_status(mock_session, "ticket-1", "in_progress", "agent_1")
    assert ticket.status == "in_progress"
    assert ticket.assigned_to == "agent_1"
