from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


class SourceInfo(BaseModel):
    type: Literal["vector", "sql"]
    detail: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceInfo] = Field(default_factory=list)


class UploadedFileSummary(BaseModel):
    filename: str
    chunks_indexed: int
    status: Literal["ok", "error"]
    error: str | None = None


class UploadResponse(BaseModel):
    files: list[UploadedFileSummary]
    total_chunks_indexed: int


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
