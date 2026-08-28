import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("asistente_jnj")


class AppError(Exception):
    """Excepción base de la aplicación. status_code define la respuesta HTTP."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "internal_error"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ServiceUnavailableError(AppError):
    """Una integración externa (OpenAI, Pinecone, SQLiteCloud) no está configurada o falló."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "service_unavailable"


class BadFileError(AppError):
    """El archivo subido no es válido (tipo, tamaño, corrupto)."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "bad_file"


class SqlSafetyError(AppError):
    """La consulta generada no es una sentencia SELECT segura."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "sql_safety_error"


def register_exception_handlers(app) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning("AppError %s en %s: %s", exc.error_code, request.url.path, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "validation_error", "detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("Error no controlado en %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "detail": "Ocurrió un error inesperado. Intenta nuevamente en unos minutos.",
            },
        )
