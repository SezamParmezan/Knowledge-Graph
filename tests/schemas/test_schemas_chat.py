import pytest

from app.schemas.chat import ChatRequest, ChatResponse
from pydantic import ValidationError


def test_chat_request_validates_minimum_length():
    request = ChatRequest(session_id="session-1", question="What is AI?")

    assert request.session_id == "session-1"
    assert request.node_id is None
    assert request.question == "What is AI?"


def test_chat_request_rejects_short_question():
    with pytest.raises(ValidationError):
        ChatRequest(session_id="session-1", question="Hi")


def test_chat_response_defaults_empty_lists():
    response = ChatResponse(answer="42")

    assert response.answer == "42"
    assert response.sources == []
    assert response.suggested_nodes == []
