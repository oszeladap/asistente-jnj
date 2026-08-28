import logging
import re
from functools import lru_cache

import sqlitecloud
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine

from app.config import get_settings
from app.core.exceptions import ServiceUnavailableError, SqlSafetyError

logger = logging.getLogger("asistente_jnj.sql")

# SQLAlchemy's sqlite dialect always tries to register REGEXP/FLOOR helper functions
# via dbapi_connection.create_function(...) on connect. SQLiteCloud's DB-API connection
# doesn't support registering custom functions (they'd need to run on the remote
# server), so it raises instead of silently ignoring the call. We don't rely on those
# helper functions in generated SQL, so make create_function a no-op for our engine.
sqlitecloud.dbapi2.Connection.create_function = lambda self, *args, **kwargs: None

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|ATTACH|PRAGMA|GRANT)\b",
    re.IGNORECASE,
)


@lru_cache
def _get_database() -> SQLDatabase:
    """El paquete `sqlitecloud` no registra un dialecto de SQLAlchemy propio, pero su
    módulo `dbapi2` es una implementación DB-API 2.0 compatible con `sqlite3`. Se usa
    el dialecto `sqlite` estándar de SQLAlchemy con un `creator` que abre la conexión
    real contra SQLiteCloud."""
    settings = get_settings()
    if not settings.has_sqlitecloud:
        raise ServiceUnavailableError("SQLiteCloud no está configurado (falta CADENA_SQLITECLOUD).")
    try:
        connection_string = settings.CADENA_SQLITECLOUD
        engine = create_engine(
            "sqlite://",
            creator=lambda: sqlitecloud.dbapi2.connect(connection_string),
            module=sqlitecloud.dbapi2,
        )
        return SQLDatabase(engine, sample_rows_in_table_info=2)
    except Exception as exc:
        logger.error("No se pudo conectar a SQLiteCloud: %s", exc)
        raise ServiceUnavailableError("No se pudo conectar a la base de datos SQLiteCloud.") from exc


def _get_llm() -> ChatOpenAI:
    settings = get_settings()
    if not settings.has_openai:
        raise ServiceUnavailableError("OpenAI no está configurado (falta OPENIA_API_KEY).")
    return ChatOpenAI(api_key=settings.OPENIA_API_KEY, model=settings.OPENAI_CHAT_MODEL, temperature=0)


def _is_safe_select(sql: str) -> bool:
    cleaned = sql.strip().strip(";").strip()
    if not cleaned:
        return False
    if not cleaned.upper().lstrip("(").startswith("SELECT"):
        return False
    if _FORBIDDEN_KEYWORDS.search(cleaned):
        return False
    return True


def query_database(question: str) -> str | None:
    """Convierte la pregunta a SQL (SELECT-only), la ejecuta y devuelve el resultado en texto.

    Devuelve None si SQLiteCloud/OpenAI no están configurados o si algo falla,
    para que el flujo de chat pueda continuar sin este contexto.
    """
    settings = get_settings()
    if not (settings.has_sqlitecloud and settings.has_openai):
        logger.info("Consulta SQL omitida: SQLiteCloud u OpenAI no configurados.")
        return None

    try:
        db = _get_database()
        chain = create_sql_query_chain(_get_llm(), db, k=settings.SQL_MAX_ROWS)
        raw_sql = chain.invoke({"question": question})
    except Exception as exc:
        logger.warning("No se pudo generar la consulta SQL, se continúa sin este contexto: %s", exc)
        return None

    # create_sql_query_chain a veces antepone una etiqueta tipo "SQLQuery:" al SQL real.
    generated_sql = re.sub(r"^\s*SQLQuery\s*:\s*", "", raw_sql, flags=re.IGNORECASE)

    if not _is_safe_select(generated_sql):
        logger.warning("Consulta SQL generada rechazada por seguridad: %s", generated_sql)
        raise SqlSafetyError("La consulta generada no es una lectura (SELECT) segura.")

    safe_sql = generated_sql.strip().rstrip(";")
    if "LIMIT" not in safe_sql.upper():
        safe_sql = f"{safe_sql} LIMIT {settings.SQL_MAX_ROWS}"

    try:
        result = db.run(safe_sql)
    except Exception as exc:
        logger.warning("La ejecución de la consulta SQL falló, se continúa sin este contexto: %s", exc)
        return None

    if not result or not str(result).strip():
        return None

    # Se incluye la consulta ejecutada junto al resultado: sin ella, el LLM de síntesis
    # solo ve tuplas sueltas sin saber qué columnas/filtros representan, y termina
    # respondiendo "no tengo información" aunque el resultado sí sea relevante.
    return f"Consulta SQL ejecutada: {safe_sql}\nResultado: {result}"
