from pydantic import BaseModel
from typing import List, Optional, Dict


class WorkflowTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    icon: str
    steps: List[Dict]

    class Config:
        from_attributes = True


class WorkflowTemplateListResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    icon: str

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    id: str
    name: str


class WorkflowExecuteRequest(BaseModel):
    template_id: int
    task: str


class WorkflowExecuteResponse(BaseModel):
    id: int
    title: str
    status: str
    result: Optional[str] = None

    class Config:
        from_attributes = True