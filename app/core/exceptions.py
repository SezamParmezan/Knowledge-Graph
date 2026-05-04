from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger


class KGException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
        '''Standard exception for the application'''


class InputValidationError(KGException):
    def __init__(self, message: str = "Invalid input", status_code: int = 422):
        super().__init__(message, status_code)
        '''Exception for input validation errors'''


class ScrapingError(KGException):
    def __init__(self, url: str, reason: str = ""):
        msg = f"Failed to scrape {url}. Reason: {reason}"
        super().__init__(msg, status_code=422)
        '''Exception for errors during web scraping'''


class AiAPIError(KGException):
    def __init__(self, message: str):
        super().__init__(f"AI API: {message}", status_code=503)


class NodeNotFoundError(KGException):
    def __init__(self, node_id: str):
        super().__init__(f"Node '{node_id}' not found", status_code=404)


class SessionNotFoundError(KGException):
    def __init__(self, session_id: str):
        super().__init__(f"Session '{session_id}' not found", status_code=404)


'''FastAPI handler for KGException'''
async def kg_exception_handler(request: Request, exc: KGException) -> JSONResponse:
    logger.warning(f"{exc.status_code} | {exc.message} | path={request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "type": type(exc).__name__},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc} | path={request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred", "type": type(exc).__name__},
    )