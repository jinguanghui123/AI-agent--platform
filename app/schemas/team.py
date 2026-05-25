from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class TeamDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberResponse] = []

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    user_id: int
    role: str = "member"