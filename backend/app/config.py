"""Configuración de la aplicación a partir de variables de entorno.

No lanza excepciones si faltan claves: cada servicio decide en tiempo de uso
si puede operar o debe devolver un error controlado (ver core/exceptions.py).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI (el nombre de variable pedido por el negocio, aunque tenga un typo)
    OPENIA_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSION: int = 1536

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = ""
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    PINECONE_TOP_K: int = 4
    # Con embeddings truncados (p.ej. 1024 dims vía Matryoshka) la similitud coseno de
    # coincidencias reales suele rondar 0.6-0.8, no cerca de 1.0. 0.75 descartaba
    # coincidencias válidas en pruebas reales; 0.5 es un umbral más realista.
    PINECONE_SCORE_THRESHOLD: float = 0.5

    # SQLiteCloud
    CADENA_SQLITECLOUD: str = ""
    SQL_QUERY_TIMEOUT_SECONDS: int = 15
    SQL_MAX_ROWS: int = 25

    # Servidor
    PORT: int = 3000
    CORS_ORIGINS: str = "*"

    # Chunking de PDFs
    PDF_CHUNK_SIZE: int = 1000
    PDF_CHUNK_OVERLAP: int = 150
    PDF_MAX_FILE_SIZE_MB: int = 20

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def has_openai(self) -> bool:
        return bool(self.OPENIA_API_KEY)

    @property
    def has_pinecone(self) -> bool:
        return bool(self.PINECONE_API_KEY and self.PINECONE_INDEX_NAME)

    @property
    def has_sqlitecloud(self) -> bool:
        return bool(self.CADENA_SQLITECLOUD)


@lru_cache
def get_settings() -> Settings:
    return Settings()
