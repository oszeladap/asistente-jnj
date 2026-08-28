# Asistente JNJ

Asistente de chat inteligente que responde preguntas combinando:

1. **Documentos PDF** vectorizados en **Pinecone** (búsqueda semántica / RAG).
2. Una base de datos **SQLiteCloud**, consultada en lenguaje natural vía **LangChain**.
3. **OpenAI** como motor de generación de respuestas.

El flujo de una pregunta siempre consulta primero la base vectorial y después la base SQL,
combinando ambos contextos para generar la respuesta final.

## Estructura del proyecto

```
backend/    API en Python (FastAPI) — PDFs, Pinecone, SQLiteCloud, OpenAI
frontend/   SPA en Angular + PrimeNG — chat con historial y subida de PDFs
```

## Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate      # Windows
pip install -r requirements.txt
cp .env.example .env        # completa tus API keys reales
uvicorn app.main:app --reload --port 8000
```

Endpoints:

- `GET  /api/health` — estado del servicio y qué integraciones están configuradas.
- `POST /api/upload` — sube uno o varios PDFs (`multipart/form-data`, campo `files`), los trocea,
  genera embeddings y los indexa en Pinecone.
- `POST /api/chat` — `{ "question": "..." }`. Busca primero en Pinecone, luego en SQLiteCloud
  (vía LangChain), y sintetiza la respuesta con OpenAI.

El backend **arranca aunque falten API keys**: cada endpoint devuelve un `503` con un mensaje
claro si la integración necesaria no está configurada, en vez de fallar de forma abrupta.

### Variables de entorno (`backend/.env`)

| Variable | Descripción |
|---|---|
| `OPENIA_API_KEY` | API key de OpenAI |
| `PINECONE_API_KEY` | API key de Pinecone |
| `PINECONE_INDEX_NAME` | Nombre del índice (se crea automáticamente si no existe) |
| `CADENA_SQLITECLOUD` | Cadena de conexión, formato `sqlitecloud://host:puerto/db?apikey=...` |
| `PORT` | Puerto del servidor (Railway lo inyecta automáticamente) |
| `CORS_ORIGINS` | Orígenes permitidos para el frontend, separados por comas |

## Frontend

```bash
cd frontend
npm install
npm start            # http://localhost:4200, apunta a http://localhost:8000
```

Layout de dos secciones: historial de conversación arriba (con scroll y estado "pensando…"),
y la barra de entrada de preguntas + subida de PDFs abajo. El botón "Enviar" se deshabilita
mientras se espera la respuesta del backend.

Antes de desplegar a producción, actualiza `frontend/src/environments/environment.prod.ts`
con la URL pública real del backend en Railway.

## Despliegue en Railway

Este repo incluye `railway.json` en `backend/` y `frontend/`. En Railway, crea **dos servicios**
dentro del mismo proyecto, cada uno apuntando a su subcarpeta como *Root Directory*.

Luego, carga las variables de entorno reales (no están en el repo por seguridad):

```bash
railway variables set OPENIA_API_KEY=... --service backend
railway variables set PINECONE_API_KEY=... --service backend
railway variables set PINECONE_INDEX_NAME=... --service backend
railway variables set CADENA_SQLITECLOUD=... --service backend
railway variables set CORS_ORIGINS=https://<url-del-frontend>.up.railway.app --service backend
```

Sin esas variables, ambos servicios arrancan y responden (`/api/health`, la SPA), pero el chat
y la subida de PDFs devuelven un error controlado hasta que se configuren las keys reales.
