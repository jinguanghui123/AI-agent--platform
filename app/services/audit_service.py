from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog, AUDIT_ACTIONS
from app.models.user import User


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        user_id: int,
        action: str,
        resource_type: str = None,
        resource_id: int = None,
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """记录审计日志"""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)
        self.db.commit()

    def get_user_logs(
        self,
        user_id: int,
        action: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """获取用户的审计日志"""
        query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)

        if action:
            query = query.filter(AuditLog.action == action)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    def get_all_logs(
        self,
        action: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """获取所有审计日志（管理员用）"""
        query = self.db.query(AuditLog)

        if action:
            query = query.filter(AuditLog.action == action)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    def get_logs_by_resource(self, resource_type: str, resource_id: int) -> List[AuditLog]:
        """获取特定资源的审计日志"""
        return self.db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(AuditLog.created_at.desc()).all()

    def get_action_name(self, action: str) -> str:
        """获取操作的中文名称"""
        return AUDIT_ACTIONS.get(action, action)


# 审计日志装饰器
def audit_action(action: str, resource_type: str = None):
    """审计日志装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从 kwargs 或 args 获取 user_id 和其他信息
            result = await func(*args, **kwargs)
            # 这里可以通过切面方式记录日志
            # 实际使用需要在具体接口中调用 audit_service.log()
            return result
        return wrapper
    return decorator