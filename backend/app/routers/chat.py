from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse
from app.services import assistant_service

router = APIRouter(tags=["chat"])


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return assistant_service.answer_question(request.question)
