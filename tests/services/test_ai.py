import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ai import AIService


@pytest.fixture
def ai_service():
    with patch('app.services.ai.AsyncGroq'):
        service = AIService()
        service.client = MagicMock()
        return service


def test_parse_json_simple():
    service = AIService.__new__(AIService)
    raw = '{"key": "value"}'
    result = service._parse_json(raw)
    assert result == {"key": "value"}


def test_parse_json_with_markdown():
    service = AIService.__new__(AIService)
    raw = '```json\n{"key": "value"}\n```'
    result = service._parse_json(raw)
    assert result == {"key": "value"}


def test_parse_json_with_whitespace():
    service = AIService.__new__(AIService)
    raw = '  \n{"key": "value"}\n  '
    result = service._parse_json(raw)
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_build_graph_url_source(ai_service):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "topic": "Test",
        "nodes": [{"id": "1", "label": "Node1"}],
        "edges": []
    })
    ai_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    result = await ai_service.build_graph("Test text", "en", 2, "url")
    assert "topic" in result
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_build_graph_term_source(ai_service):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "topic": "Science",
        "nodes": [],
        "edges": []
    })
    ai_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    result = await ai_service.build_graph("Science", "en", 1, "term", 0.5)
    assert isinstance(result, dict)