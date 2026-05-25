from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.workflow_template import WorkflowTemplate, DEFAULT_TEMPLATES
from app.models.agent import WorkflowSession, WorkflowTask
from app.services.agent_service import AGENT_ROLES
from app.services.model_gateway import model_gateway


class WorkflowTemplateService:
    def __init__(self, db: Session):
        self.db = db

    def init_default_templates(self):
        """初始化默认模板"""
        existing = self.db.query(WorkflowTemplate).count()
        if existing > 0:
            return

        for template_data in DEFAULT_TEMPLATES:
            template = WorkflowTemplate(
                name=template_data["name"],
                description=template_data["description"],
                category=template_data["category"],
                icon=template_data["icon"],
                steps=template_data["steps"]
            )
            self.db.add(template)

        self.db.commit()

    def list_templates(self, category: str = None) -> List[WorkflowTemplate]:
        """列出所有模板"""
        query = self.db.query(WorkflowTemplate).filter(WorkflowTemplate.is_active == 1)
        if category:
            query = query.filter(WorkflowTemplate.category == category)
        return query.order_by(WorkflowTemplate.id.asc()).all()

    def get_template(self, template_id: int) -> Optional[WorkflowTemplate]:
        """获取模板详情"""
        return self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.id == template_id,
            WorkflowTemplate.is_active == 1
        ).first()

    async def execute_template(
        self,
        template_id: int,
        user_id: int,
        task: str
    ) -> WorkflowSession:
        """执行模板工作流"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError("模板不存在")

        # 创建工作流会话
        workflow = WorkflowSession(
            user_id=user_id,
            title=template.name,
            task_description=task,
            status="running"
        )
        self.db.add(workflow)
        self.db.flush()

        try:
            results = {}

            # 按顺序执行每个步骤
            for step in sorted(template.steps, key=lambda x: x["order"]):
                agent_role = step["agent_role"]
                task_template = step["task_template"].replace("{task}", task)

                # 构建上下文
                context = ""
                if results:
                    context = "前序步骤结果：\n" + "\n".join([
                        f"{AGENT_ROLES.get(k, {}).get('name', k)}: {v}"
                        for k, v in results.items()
                    ]) + "\n\n"

                # 执行 Agent 任务
                agent_config = AGENT_ROLES.get(agent_role)
                if not agent_config:
                    continue

                messages = [
                    {"role": "system", "content": agent_config["system_prompt"]},
                    {"role": "user", "content": context + task_template}
                ]

                result = await model_gateway.chat(agent_config["model"], messages)

                # 保存任务结果
                task_record = WorkflowTask(
                    workflow_id=workflow.id,
                    agent_role=agent_role,
                    task_description=task_template,
                    status="completed",
                    result=result
                )
                self.db.add(task_record)

                results[agent_role] = result

            # 汇总结果
            workflow.result = results.get("supervisor", list(results.values())[-1] if results else "")
            workflow.status = "completed"
            self.db.commit()
            self.db.refresh(workflow)

            return workflow

        except Exception as e:
            workflow.status = "failed"
            self.db.commit()
            raise e

    def get_categories(self) -> List[Dict]:
        """获取所有分类"""
        templates = self.db.query(WorkflowTemplate.category).distinct().all()
        categories = []
        for t in templates:
            if t.category:
                category_names = {
                    "research": "市场调研",
                    "prd": "PRD 生成",
                    "campaign": "活动策划",
                    "content": "内容创作"
                }
                categories.append({
                    "id": t.category,
                    "name": category_names.get(t.category, t.category)
                })
        return categories