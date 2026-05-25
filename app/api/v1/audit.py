from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.audit_service import AuditService, AUDIT_ACTIONS
from app.schemas.audit_log import AuditLogListResponse

router = APIRouter()


@router.get("/logs", response_model=List[AuditLogListResponse])
def get_logs(
    action: Optional[str] = Query(None, description="操作类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取审计日志列表"""
    service = AuditService(db)

    # 解析日期
    from datetime import datetime
    start = None
    end = None
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")

    # 获取日志
    logs = service.get_user_logs(
        user_id=current_user.id,
        action=action,
        start_date=start,
        end_date=end,
        limit=limit
    )

    return [
        {
            "id": log.id,
            "username": current_user.username,
            "action": log.action,
            "action_name": service.get_action_name(log.action),
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at
        }
        for log in logs
    ]


@router.get("/actions")
def get_actions():
    """获取所有可记录的操作类型"""
    return [
        {"id": action, "name": name}
        for action, name in AUDIT_ACTIONS.items()
    ]