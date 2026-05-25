from pydantic import BaseModel
from typing import List

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    status: str = "active"

class ModelListResponse(BaseModel):
    models: List[ModelInfo]