from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    id: int
    document_id: int
    content: str
    chunk_index: int
    token_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class SearchResult(BaseModel):
    id: int
    content: str
    similarity: float
    document_id: int
    chunk_index: int


class RAGChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    model_id: str = "minimax"
    top_k: Optional[int] = 5


class RAGChatResponse(BaseModel):
    answer: str
    chunks: List[SearchResult]
    session_id: Optional[int] = None
