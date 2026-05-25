from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.workflow_template_service import WorkflowTemplateService
from app.schemas.workflow_template import (
    WorkflowTemplateResponse,
    WorkflowTemplateListResponse,
    CategoryResponse,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse
)

router = APIRouter()


@router.get("/templates", response_model=List[WorkflowTemplateListResponse])
def list_templates(
    category: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出所有工作流模板"""
    service = WorkflowTemplateService(db)
    service.init_default_templates()  # 初始化默认模板
    return service.list_templates(category)


@router.get("/templates/{template_id}", response_model=WorkflowTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板详情"""
    service = WorkflowTemplateService(db)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有模板分类"""
    service = WorkflowTemplateService(db)
    return service.get_categories()


@router.post("/execute", response_model=WorkflowExecuteResponse)
async def execute_template(
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行工作流模板"""
    service = WorkflowTemplateService(db)
    try:
        workflow = await service.execute_template(
            template_id=request.template_id,
            user_id=current_user.id,
            task=request.task
        )
        return {
            "id": workflow.id,
            "title": workflow.title,
            "status": workflow.status,
            "result": workflow.result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")