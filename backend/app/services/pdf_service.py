import io
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config import get_settings
from app.core.exceptions import BadFileError

logger = logging.getLogger("asistente_jnj.pdf")


def extract_text(filename: str, content: bytes) -> str:
    if not filename.lower().endswith(".pdf"):
        raise BadFileError(f"'{filename}' no es un PDF (solo se aceptan archivos .pdf).")

    settings = get_settings()
    max_bytes = settings.PDF_MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise BadFileError(
            f"'{filename}' supera el tamaño máximo permitido de {settings.PDF_MAX_FILE_SIZE_MB} MB."
        )

    try:
        reader = PdfReader(io.BytesIO(content))
        pages_text = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as exc:
        raise BadFileError(f"No se pudo leer '{filename}': el PDF parece estar corrupto.") from exc
    except Exception as exc:  # defensivo: pypdf puede lanzar varios tipos según el PDF
        raise BadFileError(f"No se pudo procesar '{filename}': {exc}") from exc

    text = "\n\n".join(p for p in pages_text if p.strip())
    if not text.strip():
        raise BadFileError(
            f"'{filename}' no contiene texto extraíble (¿es un PDF escaneado sin OCR?)."
        )
    return text


def chunk_text(text: str) -> list[str]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.PDF_CHUNK_SIZE,
        chunk_overlap=settings.PDF_CHUNK_OVERLAP,
    )
    return splitter.split_text(text)
