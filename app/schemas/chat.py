from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageCreate(BaseModel):
    content: str
    session_id: Optional[int] = None
    model_id: str = "minimax"

class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    content_type: str = "text"
    image_url: Optional[str] = None
    model_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    title: Optional[str] = "新对话"
    model_id: str = "minimax"

class SessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    model_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    model_id: str = "minimax"
    images: Optional[List[str]] = None  # 图片URL列表

class ChatResponse(BaseModel):
    session_id: int
    message: MessageResponse