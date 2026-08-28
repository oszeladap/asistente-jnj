import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.core.exceptions import ServiceUnavailableError, SqlSafetyError
from app.schemas import ChatResponse, SourceInfo
from app.services import sql_service, vector_service

logger = logging.getLogger("asistente_jnj.assistant")

_SYSTEM_PROMPT = (
    "Eres un asistente que responde preguntas usando ÚNICAMENTE el contexto que se te entrega. "
    "El contexto puede venir de documentos (base vectorial) y/o de una base de datos SQL. "
    "Si el contexto no contiene la respuesta, dilo honestamente en vez de inventar. "
    "Responde en español, de forma clara y concisa."
)


def _build_llm() -> ChatOpenAI:
    settings = get_settings()
    if not settings.has_openai:
        raise ServiceUnavailableError("OpenAI no está configurado (falta OPENIA_API_KEY).")
    return ChatOpenAI(api_key=settings.OPENIA_API_KEY, model=settings.OPENAI_CHAT_MODEL, temperature=0.2)


def answer_question(question: str) -> ChatResponse:
    settings = get_settings()
    sources: list[SourceInfo] = []
    context_parts: list[str] = []

    # 1) Primero: base de datos vectorial (Pinecone)
    try:
        vector_hits = vector_service.similarity_search(question)
    except ServiceUnavailableError:
        vector_hits = []
    if vector_hits:
        context_parts.append(
            "Contexto de documentos (Pinecone):\n"
            + "\n---\n".join(text for text, _score, _src in vector_hits)
        )
        for _text, score, src in vector_hits:
            sources.append(SourceInfo(type="vector", detail=f"{src} (score={score:.2f})"))

    # 2) Después: base de datos SQLiteCloud (vía LangChain)
    try:
        sql_result = sql_service.query_database(question)
    except SqlSafetyError as exc:
        sql_result = None
        logger.warning("Consulta SQL rechazada por seguridad: %s", exc.detail)
    except ServiceUnavailableError:
        sql_result = None

    if sql_result:
        context_parts.append(f"Resultado de la base de datos SQL:\n{sql_result}")
        sources.append(SourceInfo(type="sql", detail="SQLiteCloud"))

    if not context_parts:
        if not settings.has_openai:
            raise ServiceUnavailableError(
                "El asistente no está configurado todavía: falta OPENIA_API_KEY. "
                "Configura las variables de entorno para habilitar el chat."
            )
        return ChatResponse(
            answer=(
                "No encontré información relevante en los documentos ni en la base de datos "
                "para responder tu pregunta. Prueba reformularla o sube documentos relacionados."
            ),
            sources=[],
        )

    llm = _build_llm()
    context_text = "\n\n".join(context_parts)
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(
            content=f"Contexto disponible:\n\n{context_text}\n\nPregunta del usuario: {question}"
        ),
    ]
    try:
        result = llm.invoke(messages)
    except Exception as exc:
        logger.error("Fallo al generar respuesta con OpenAI: %s", exc)
        raise ServiceUnavailableError("El motor de IA no respondió correctamente. Intenta de nuevo.") from exc

    return ChatResponse(answer=result.content, sources=sources)
