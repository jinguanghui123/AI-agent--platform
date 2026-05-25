from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.agent_service import AgentService
from app.schemas.agent import (
    AgentRoleResponse,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowTaskResponse
)

router = APIRouter()


@router.get("/roles", response_model=List[AgentRoleResponse])
def get_agent_roles():
    """获取可用的 Agent 角色列表"""
    return [
        {"id": "supervisor", "name": "主管 Agent", "description": "负责分解任务、协调工作、汇总结果"},
        {"id": "researcher", "name": "调研 Agent", "description": "负责搜索信息、生成调研报告"},
        {"id": "writer", "name": "写手 Agent", "description": "负责创作各类文案内容"}
    ]


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建并执行多 Agent 工作流"""
    service = AgentService(db)
    try:
        workflow = await service.create_and_execute_workflow(
            user_id=current_user.id,
            task_description=request.task,
            selected_roles=request.roles,
            title=request.title
        )
        # 获取关联的任务
        tasks = service.get_workflow_tasks(workflow.id)
        return {
            "id": workflow.id,
            "user_id": workflow.user_id,
            "title": workflow.title,
            "task_description": workflow.task_description,
            "status": workflow.status,
            "result": workflow.result,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
            "tasks": tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")


@router.get("/workflows", response_model=List[WorkflowResponse])
def list_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出用户的所有工作流"""
    service = AgentService(db)
    workflows = service.list_workflows(current_user.id)
    result = []
    for w in workflows:
        tasks = service.get_workflow_tasks(w.id)
        result.append({
            "id": w.id,
            "user_id": w.user_id,
            "title": w.title,
            "task_description": w.task_description,
            "status": w.status,
            "result": w.result,
            "created_at": w.created_at,
            "updated_at": w.updated_at,
            "tasks": tasks
        })
    return result


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流详情"""
    service = AgentService(db)
    workflow = service.get_workflow(workflow_id, current_user.id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    tasks = service.get_workflow_tasks(workflow.id)
    return {
        "id": workflow.id,
        "user_id": workflow.user_id,
        "title": workflow.title,
        "task_description": workflow.task_description,
        "status": workflow.status,
        "result": workflow.result,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
        "tasks": tasks
    }
