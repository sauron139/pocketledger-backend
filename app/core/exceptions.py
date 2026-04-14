from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(404, message)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(401, message)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(403, message)


class ConflictError(AppException):
    def __init__(self, message: str = "Conflict"):
        super().__init__(409, message)


class BadRequestError(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(400, message)


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "An unexpected error occurred"},
    )
