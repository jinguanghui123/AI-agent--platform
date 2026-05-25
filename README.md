# AI Agent 平台

一个统一的 AI Agent 平台，让用户在一个平台里搞定所有 AI 任务。

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写你的 API Keys
```

### 2. 启动服务

```bash
# 开发模式
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

cd web
npm install
npm run dev
```

### 3. Docker 部署

```bash
docker-compose up -d
```

访问 http://localhost 即可使用。

## 功能

- [x] 用户注册/登录
- [x] 对话界面（支持多模型切换）
- [x] 对话历史管理
- [x] 模型网关（支持 MiniMax/DeepSeek/GPT-4）
- [ ] 多 Agent 协作
- [ ] 知识库
- [ ] 企业模式

## 技术栈

- 前端: Vue3 + Vite + Element Plus
- 后端: FastAPI + SQLAlchemy
- 数据库: SQLite (MVP) / 可迁移到 PostgreSQL
- 部署: Docker