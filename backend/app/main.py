import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import configure_logging
from app.routers import chat, health, upload

configure_logging()
logger = logging.getLogger("asistente_jnj")

settings = get_settings()

app = FastAPI(
    title="Asistente JNJ API",
    description="Asistente de chat con RAG (Pinecone) y consultas SQL (SQLiteCloud) sobre OpenAI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(chat.router)


@app.on_event("startup")
async def on_startup():
    logger.info(
        "Asistente JNJ iniciado | OpenAI=%s Pinecone=%s SQLiteCloud=%s",
        settings.has_openai,
        settings.has_pinecone,
        settings.has_sqlitecloud,
    )
