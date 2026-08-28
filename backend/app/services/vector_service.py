import logging
import uuid
from functools import lru_cache

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import ServiceUnavailableError

logger = logging.getLogger("asistente_jnj.vector")


@lru_cache
def _get_pinecone_client() -> Pinecone:
    settings = get_settings()
    if not settings.has_pinecone:
        raise ServiceUnavailableError(
            "Pinecone no está configurado (faltan PINECONE_API_KEY / PINECONE_INDEX_NAME)."
        )
    return Pinecone(api_key=settings.PINECONE_API_KEY)


def _ensure_index_exists(pc: Pinecone) -> None:
    settings = get_settings()
    existing = {idx["name"] for idx in pc.list_indexes()}
    if settings.PINECONE_INDEX_NAME in existing:
        return
    logger.info("Creando índice de Pinecone '%s'...", settings.PINECONE_INDEX_NAME)
    pc.create_index(
        name=settings.PINECONE_INDEX_NAME,
        dimension=settings.OPENAI_EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION),
    )


def _get_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()
    if not settings.has_openai:
        raise ServiceUnavailableError("OpenAI no está configurado (falta OPENIA_API_KEY).")
    return OpenAIEmbeddings(
        api_key=settings.OPENIA_API_KEY,
        model=settings.OPENAI_EMBEDDING_MODEL,
        dimensions=settings.OPENAI_EMBEDDING_DIMENSION,
    )


@lru_cache
def _get_vector_store() -> PineconeVectorStore:
    settings = get_settings()
    pc = _get_pinecone_client()
    _ensure_index_exists(pc)
    index = pc.Index(settings.PINECONE_INDEX_NAME)
    return PineconeVectorStore(index=index, embedding=_get_embeddings())


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_not_exception_type(ServiceUnavailableError),
    reraise=True,
)
def index_chunks(filename: str, chunks: list[str]) -> int:
    """Genera embeddings y sube los chunks a Pinecone. Devuelve cuántos se indexaron."""
    if not chunks:
        return 0
    store = _get_vector_store()
    docs = [
        Document(page_content=chunk, metadata={"source": filename, "chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]
    ids = [str(uuid.uuid4()) for _ in docs]
    try:
        store.add_documents(docs, ids=ids)
    except Exception as exc:
        logger.error("Fallo al indexar '%s' en Pinecone: %s", filename, exc)
        raise ServiceUnavailableError(f"No se pudo indexar '{filename}' en Pinecone.") from exc
    return len(docs)


def similarity_search(question: str) -> list[tuple[str, float, str]]:
    """Devuelve [(texto, score, fuente)] relevantes para la pregunta, o [] si no hay/hay error."""
    settings = get_settings()
    if not (settings.has_pinecone and settings.has_openai):
        logger.info("Búsqueda vectorial omitida: Pinecone u OpenAI no configurados.")
        return []
    try:
        store = _get_vector_store()
        results = store.similarity_search_with_score(question, k=settings.PINECONE_TOP_K)
    except Exception as exc:
        logger.warning("Búsqueda vectorial falló, se continúa sin este contexto: %s", exc)
        return []

    relevant = []
    for doc, score in results:
        if score >= settings.PINECONE_SCORE_THRESHOLD:
            source = doc.metadata.get("source", "documento")
            relevant.append((doc.page_content, score, source))
    return relevant
