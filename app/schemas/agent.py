from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AgentRoleResponse(BaseModel):
    id: str
    name: str
    description: str

    class Config:
        from_attributes = True


class WorkflowCreate(BaseModel):
    task: str
    roles: List[str]  # ["supervisor", "researcher", "writer"]
    title: Optional[str] = None


class WorkflowTaskResponse(BaseModel):
    id: int
    workflow_id: int
    agent_role: str
    task_description: str
    status: str
    result: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowResponse(BaseModel):
    id: int
    user_id: int
    title: str
    task_description: str
    status: str
    result: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    tasks: List[WorkflowTaskResponse] = []

    class Config:
        from_attributes = True
