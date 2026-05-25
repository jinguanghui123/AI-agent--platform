from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime
from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)  # 主管/调研/写手
    role = Column(String(20), nullable=False)  # supervisor/researcher/writer
    system_prompt = Column(Text, nullable=False)
    model_id = Column(String(50), default="minimax")
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowSession(Base):
    __tablename__ = "workflow_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200))
    task_description = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    result = Column(Text, nullable=True)  # 最终汇总结果
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflow_sessions.id"), nullable=False)
    agent_role = Column(String(20), nullable=False)  # supervisor/researcher/writer
    task_description = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    result = Column(Text, nullable=True)  # Agent 输出结果
    created_at = Column(DateTime, default=datetime.utcnow)
