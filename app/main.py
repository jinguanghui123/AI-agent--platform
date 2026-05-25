from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.v1 import auth, chat, model, knowledge, agent, workflow_template, team, audit, sso, feishu
from app.core.config import settings
from app.core.database import engine, Base

app = FastAPI(title="AI Agent Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["对话"])
app.include_router(model.router, prefix="/api/v1/models", tags=["模型"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["知识库"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["Agent"])
app.include_router(workflow_template.router, prefix="/api/v1/workflow", tags=["工作流"])
app.include_router(team.router, prefix="/api/v1/team", tags=["团队"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["审计"])
app.include_router(sso.router, prefix="/api/v1/sso", tags=["SSO"])
app.include_router(feishu.router, prefix="/api/v1/feishu", tags=["飞书插件"])

# 静态文件服务 - 上传的图片
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "AI Agent Platform API"}

@app.get("/health")
async def health():
    return {"status": "ok"}