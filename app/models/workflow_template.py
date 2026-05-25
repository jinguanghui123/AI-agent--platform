from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from datetime import datetime
from app.core.database import Base


class WorkflowTemplate(Base):
    """预制工作流模板"""
    __tablename__ = "workflow_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 模板名称
    description = Column(Text)  # 模板描述
    category = Column(String(50))  # 模板分类: research/prd/campaign
    steps = Column(JSON, nullable=False)  # 工作流步骤配置
    # steps 格式: [{"order": 1, "agent_role": "researcher", "task_template": "..."}, ...]
    icon = Column(String(50), default="document")  # 图标
    is_active = Column(Integer, default=1)  # 是否启用
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 预置模板数据
DEFAULT_TEMPLATES = [
    {
        "name": "市场调研",
        "description": "完成市场调研并生成报告，适合产品上市前调研",
        "category": "research",
        "icon": "search",
        "steps": [
            {"order": 1, "agent_role": "supervisor", "task_template": "分析任务：{task}，分解为调研步骤"},
            {"order": 2, "agent_role": "researcher", "task_template": "执行市场调研：{task}，输出调研报告"},
            {"order": 3, "agent_role": "writer", "task_template": "基于调研报告撰写：市场分析报告"},
            {"order": 4, "agent_role": "supervisor", "task_template": "汇总所有结果，生成最终报告"}
        ]
    },
    {
        "name": "PRD 生成",
        "description": "从调研到 PRD 文档，适合产品经理",
        "category": "prd",
        "icon": "document",
        "steps": [
            {"order": 1, "agent_role": "supervisor", "task_template": "分析需求：{task}，分解为 PRD 制作步骤"},
            {"order": 2, "agent_role": "researcher", "task_template": "调研市场和竞品：{task}"},
            {"order": 3, "agent_role": "writer", "task_template": "基于调研结果，撰写 PRD 文档"},
            {"order": 4, "agent_role": "supervisor", "task_template": "汇总并生成最终 PRD"}
        ]
    },
    {
        "name": "活动策划",
        "description": "完成活动策划并生成推广文案",
        "category": "campaign",
        "icon": "promotion",
        "steps": [
            {"order": 1, "agent_role": "supervisor", "task_template": "分析活动需求：{task}，制定策划步骤"},
            {"order": 2, "agent_role": "researcher", "task_template": "调研目标市场和受众：{task}"},
            {"order": 3, "agent_role": "writer", "task_template": "基于调研，撰写活动策划方案"},
            {"order": 4, "agent_role": "writer", "task_template": "撰写推广文案和社交媒体帖子"},
            {"order": 5, "agent_role": "supervisor", "task_template": "汇总生成完整活动策划"}
        ]
    },
    {
        "name": "小红书文案",
        "description": "快速生成小红书种草文案",
        "category": "content",
        "icon": "edit",
        "steps": [
            {"order": 1, "agent_role": "supervisor", "task_template": "分析产品：{task}，制定文案方向"},
            {"order": 2, "agent_role": "writer", "task_template": "撰写小红书种草文案，包含标题和正文"},
            {"order": 3, "agent_role": "supervisor", "task_template": "优化并生成最终文案"}
        ]
    }
]