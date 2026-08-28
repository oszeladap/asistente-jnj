import logging

from fastapi import APIRouter, File, UploadFile

from app.core.exceptions import AppError, BadFileError
from app.schemas import UploadResponse, UploadedFileSummary
from app.services import pdf_service, vector_service

logger = logging.getLogger("asistente_jnj.upload")

router = APIRouter(tags=["upload"])


@router.post("/api/upload", response_model=UploadResponse)
async def upload_pdfs(files: list[UploadFile] = File(...)):
    summaries: list[UploadedFileSummary] = []
    total = 0

    for upload in files:
        try:
            content = await upload.read()
            text = pdf_service.extract_text(upload.filename or "documento.pdf", content)
            chunks = pdf_service.chunk_text(text)
            indexed = vector_service.index_chunks(upload.filename or "documento.pdf", chunks)
            summaries.append(
                UploadedFileSummary(
                    filename=upload.filename or "documento.pdf",
                    chunks_indexed=indexed,
                    status="ok",
                )
            )
            total += indexed
        except BadFileError as exc:
            summaries.append(
                UploadedFileSummary(
                    filename=upload.filename or "documento.pdf",
                    chunks_indexed=0,
                    status="error",
                    error=exc.detail,
                )
            )
        except AppError as exc:
            summaries.append(
                UploadedFileSummary(
                    filename=upload.filename or "documento.pdf",
                    chunks_indexed=0,
                    status="error",
                    error=exc.detail,
                )
            )
        except Exception as exc:
            logger.exception("Error inesperado procesando '%s'", upload.filename)
            summaries.append(
                UploadedFileSummary(
                    filename=upload.filename or "documento.pdf",
                    chunks_indexed=0,
                    status="error",
                    error=f"Error inesperado: {exc}",
                )
            )

    return UploadResponse(files=summaries, total_chunks_indexed=total)
