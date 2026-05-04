import asyncio
import json

from fastapi import Request
from app.core.exceptions import (
    AiAPIError,
    InputValidationError,
    KGException,
    NodeNotFoundError,
    ScrapingError,
    SessionNotFoundError,
    kg_exception_handler,
    unhandled_exception_handler,
)


def test_exception_subclasses_define_status_codes_and_messages():
    input_error = InputValidationError()
    assert isinstance(input_error, KGException)
    assert input_error.status_code == 422
    assert input_error.message == "Invalid input"

    scraping_error = ScrapingError(url="https://example.com", reason="timeout")
    assert scraping_error.status_code == 422
    assert "Failed to scrape https://example.com" in scraping_error.message

    api_error = AiAPIError("service unavailable")
    assert api_error.status_code == 503
    assert "AI API:" in api_error.message

    node_error = NodeNotFoundError("n1")
    assert node_error.status_code == 404
    assert "Node 'n1' not found" in node_error.message

    session_error = SessionNotFoundError("s1")
    assert session_error.status_code == 404
    assert "Session 's1' not found" in session_error.message


def make_request():
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "scheme": "http",
            "server": ("testserver", 80),
        }
    )


def test_kg_exception_handler_returns_json_response():
    request = make_request()
    response = asyncio.run(kg_exception_handler(request, InputValidationError()))

    assert response.status_code == 422
    assert json.loads(response.body) == {"error": "Invalid input", "type": "InputValidationError"}


def test_unhandled_exception_handler_returns_500():
    request = make_request()
    response = asyncio.run(unhandled_exception_handler(request, Exception("boom")))

    assert response.status_code == 500
    assert json.loads(response.body) == {"error": "An unexpected error occurred", "type": "Exception"}