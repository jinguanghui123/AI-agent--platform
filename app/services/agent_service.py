from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.agent import WorkflowSession, WorkflowTask
from app.services.model_gateway import model_gateway


# 预定义 Agent 角色配置
AGENT_ROLES = {
    "supervisor": {
        "name": "主管 Agent",
        "system_prompt": """你是一个专业的项目主管，负责分解复杂任务并协调其他 Agent 工作。

你的职责：
1. 分析用户输入的复杂任务
2. 将任务分解为可执行的子任务
3. 为每个子任务分配合适的执行 Agent
4. 协调各 Agent 的工作
5. 汇总最终结果

输出格式：
请按以下格式分解任务：
【任务分解】
1. [子任务1描述] - 执行 Agent: [agent_name]
2. [子任务2描述] - 执行 Agent: [agent_name]
...

【执行指令】
为每个 Agent 生成具体的执行指令。""",
        "model": "minimax"
    },
    "researcher": {
        "name": "调研 Agent",
        "system_prompt": """你是一个专业的市场调研员，擅长收集、整理和分析信息。

你的职责：
1. 搜索和收集相关信息
2. 整理数据和分析要点
3. 生成结构化的调研报告
4. 提供数据支撑的观点

请基于给定的任务描述，执行调研并输出报告。报告要求：
- 结构清晰，层次分明
- 数据准确，来源可靠
- 观点客观，有理有据""",
        "model": "minimax"
    },
    "writer": {
        "name": "写手 Agent",
        "system_prompt": """你是一个专业的文案写手，擅长各类文案的创作。

你的职责：
1. 根据任务要求创作文案
2. 标题吸引人，内容有价值
3. 格式规范，表达流畅
4. 符合目标受众的阅读习惯

支持的文案类型：
- 小红书文案
- 产品介绍
- 推广文案
- 邮件草稿
- 社交媒体帖子

请基于给定的任务描述和素材，创作高质量文案。""",
        "model": "minimax"
    }
}


class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def get_available_roles(self) -> List[Dict]:
        """获取可用的 Agent 角色列表"""
        return [
            {
                "id": role_id,
                "name": config["name"],
                "description": config["system_prompt"][:100] + "..."
            }
            for role_id, config in AGENT_ROLES.items()
        ]

    async def execute_agent_task(self, agent_role: str, task_description: str, context: str = "") -> str:
        """执行单个 Agent 任务"""
        if agent_role not in AGENT_ROLES:
            raise ValueError(f"未知的 Agent 角色: {agent_role}")

        config = AGENT_ROLES[agent_role]

        # 构建消息
        messages = [
            {"role": "system", "content": config["system_prompt"]}
        ]

        if context:
            messages.append({"role": "user", "content": f"上下文信息：\n{context}\n\n任务：\n{task_description}"})
        else:
            messages.append({"role": "user", "content": task_description})

        # 调用模型
        result = await model_gateway.chat(config["model"], messages)
        return result

    async def create_and_execute_workflow(
        self,
        user_id: int,
        task_description: str,
        selected_roles: List[str],
        title: str = None
    ) -> WorkflowSession:
        """创建并执行工作流"""
        # 过滤有效的角色
        valid_roles = [r for r in selected_roles if r in AGENT_ROLES]
        if not valid_roles:
            valid_roles = ["researcher", "writer"]  # 默认角色

        # 创建工作流会话
        workflow = WorkflowSession(
            user_id=user_id,
            title=title or task_description[:50],
            task_description=task_description,
            status="running"
        )
        self.db.add(workflow)
        self.db.flush()

        try:
            # 步骤1：使用主管 Agent 分解任务
            supervisor_config = AGENT_ROLES["supervisor"]
            roles_list = ", ".join([AGENT_ROLES[r]["name"] for r in valid_roles])

            supervisor_task = f"""请分析以下任务，并分解为具体的执行步骤。

任务：{task_description}

可用的 Agent 角色：
{roles_list}

请给出任务分解计划和具体的执行指令。"""

            supervisor_result = await self.execute_agent_task("supervisor", supervisor_task)

            # 创建主管任务记录
            supervisor_task_record = WorkflowTask(
                workflow_id=workflow.id,
                agent_role="supervisor",
                task_description=supervisor_task,
                status="completed",
                result=supervisor_result
            )
            self.db.add(supervisor_task_record)

            # 步骤2：并行执行各子任务 Agent
            agent_results = {}
            for role in valid_roles:
                agent_task_desc = f"""基于以下任务分解结果，执行具体的调研工作。

主管 Agent 的分解：
{supervisor_result}

你的具体任务：{task_description}

请执行并输出结果。"""

                agent_result = await self.execute_agent_task(role, agent_task_desc, supervisor_result)
                agent_results[role] = agent_result

                # 创建任务记录
                task_record = WorkflowTask(
                    workflow_id=workflow.id,
                    agent_role=role,
                    task_description=agent_task_desc,
                    status="completed",
                    result=agent_result
                )
                self.db.add(task_record)

            # 步骤3：主管 Agent 汇总
            summary_task = f"""请汇总以下各 Agent 的工作结果，生成最终报告。

任务：{task_description}

各 Agent 的结果：
{chr(10).join([f'{AGENT_ROLES[r]["name"]}：\n{agent_results[r]}' for r in valid_roles])}

请生成结构化的最终报告。"""

            summary_result = await self.execute_agent_task("supervisor", summary_task)

            # 创建汇总任务记录
            summary_task_record = WorkflowTask(
                workflow_id=workflow.id,
                agent_role="supervisor",
                task_description="汇总各 Agent 结果",
                status="completed",
                result=summary_result
            )
            self.db.add(summary_task_record)

            # 更新工作流状态
            workflow.result = summary_result
            workflow.status = "completed"

            self.db.commit()
            self.db.refresh(workflow)

            return workflow

        except Exception as e:
            workflow.status = "failed"
            self.db.commit()
            raise e

    def get_workflow(self, workflow_id: int, user_id: int) -> Optional[WorkflowSession]:
        """获取工作流详情"""
        return self.db.query(WorkflowSession).filter(
            WorkflowSession.id == workflow_id,
            WorkflowSession.user_id == user_id
        ).first()

    def get_workflow_tasks(self, workflow_id: int) -> List[WorkflowTask]:
        """获取工作流的的所有任务"""
        return self.db.query(WorkflowTask).filter(
            WorkflowTask.workflow_id == workflow_id
        ).order_by(WorkflowTask.created_at.asc()).all()

    def list_workflows(self, user_id: int) -> List[WorkflowSession]:
        """列出用户的所有工作流"""
        return self.db.query(WorkflowSession).filter(
            WorkflowSession.user_id == user_id
        ).order_by(WorkflowSession.created_at.desc()).all()
