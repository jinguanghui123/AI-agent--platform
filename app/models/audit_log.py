from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from datetime import datetime
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # login/logout/chat/create_team/etc
    resource_type = Column(String(50))  # session/team/document/workflow
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON)  # 额外详情
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


# 操作类型定义
AUDIT_ACTIONS = {
    # 认证
    "login": "登录",
    "logout": "登出",
    "register": "注册",

    # 对话
    "create_session": "创建会话",
    "delete_session": "删除会话",
    "send_message": "发送消息",

    # 知识库
    "upload_document": "上传文档",
    "delete_document": "删除文档",
    "search_knowledge": "搜索知识库",

    # Agent
    "create_workflow": "创建工作流",
    "execute_workflow": "执行工作流",

    # 团队
    "create_team": "创建团队",
    "delete_team": "删除团队",
    "add_team_member": "添加团队成员",
    "remove_team_member": "移除团队成员",
}