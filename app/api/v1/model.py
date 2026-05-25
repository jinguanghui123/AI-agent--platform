from fastapi import APIRouter
from app.schemas.model import ModelListResponse, ModelInfo
from app.services.model_gateway import model_gateway

router = APIRouter()

@router.get("", response_model=ModelListResponse)
def list_models():
    models = model_gateway.list_models()
    return {"models": models}