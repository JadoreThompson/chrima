import logging
from typing import Callable

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from chrima.workspace.exception import WorkspaceNotFoundException
from chrima.workspace.wallet.exception import (
    WalletNotFoundException,
    WalletInUseException,
)
from chrima.price.exception import PriceNotFoundException
from chrima.product.exception import ProductNotFoundException
from chrima.tokens.exception import TokenNotFoundException
from chrima.transaction.exception import TransactionNotFoundException
from chrima.user.exception import UserNotFoundException


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._handlers: dict[type[Exception], Callable] = {
            HTTPException: self._handle_http_exception,
            RequestValidationError: self._handle_request_validation_error,
            # 404
            UserNotFoundException: lambda req, exc: self._create_error_response(
                404, str(exc)
            ),
            WorkspaceNotFoundException: lambda req, exc: self._create_error_response(
                404, str(exc)
            ),
            PriceNotFoundException: lambda req, exc: self._create_error_response(
                404, str(exc)
            ),
            ProductNotFoundException: lambda req, exc: self._create_error_response(
                404, str(exc)
            ),
            TokenNotFoundException: lambda req, exc: self._create_error_response(
                404, str(exc)
            ),
            WalletNotFoundException: lambda req, exc: self._create_error_response(
                404, str(exc)
            ),
            WalletInUseException: lambda req, exc: self._create_error_response(
                409, str(exc)
            ),
            TransactionNotFoundException: lambda req, exc: self._create_error_response(
                404, str(exc)
            ),
        }

        self._logger = logging.getLogger(self.__class__.__name__)

    def register_handler(self, exc_type: type[Exception], handler: Callable) -> None:
        self._handlers[exc_type] = handler

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            handler = self._handlers.get(type(exc))

            if handler is not None:
                return handler(request, exc)

            self._logger.error("An unhandled exception occurred", exc_info=exc)

            return self._create_error_response(
                status_code=500,
                message="An unexpected error occurred. Please try again later.",
            )

    def _create_error_response(self, status_code: int, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"error": message},
        )

    def _handle_http_exception(
        self,
        req: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        return self._create_error_response(exc.status_code, exc.detail)

    def _handle_request_validation_error(
        self,
        req: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        error = exc.errors()[0]

        msg = error["msg"]
        error_type = error["type"].replace("_", " ")

        clean_msg = msg.lower().replace(f"{error_type},", "").strip()

        if clean_msg:
            clean_msg = clean_msg[0].upper() + clean_msg[1:]

        return self._create_error_response(422, clean_msg or "Invalid request body")
