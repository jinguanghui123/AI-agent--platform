from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    action_name: str  # 中文名称
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[Dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    id: int
    username: str  # 用户名
    action: str
    action_name: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[Dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogQuery(BaseModel):
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = 100