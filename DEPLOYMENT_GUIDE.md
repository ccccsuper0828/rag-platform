# RAG Platform 部署指南（基于 Claude Skills）

## 🏗️ 项目架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          前端 (Vue.js)                              │
│                     http://localhost:5173                           │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      后端 API (FastAPI)                             │
│                     http://localhost:8000                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ 认证 API   │  │ RAG 管理   │  │ 聊天 API   │  │ 深度研究   │    │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘    │
└────────┼───────────────┼───────────────┼───────────────┼────────────┘
         │               │               │               │
         │               ▼               ▼               │
         │    ┌─────────────────────────────────────┐    │
         │    │      AI Partner Runner              │    │
         │    │      http://localhost:9001          │    │
         │    │  ┌─────────────────────────────┐    │    │
         │    │  │     Claude Code CLI         │    │    │
         │    │  │  (调用 Claude Skills)       │◄───┼────┘
         │    │  └─────────────────────────────┘    │
         │    └─────────────────────────────────────┘
         │                     │
         │                     ▼
         │    ┌─────────────────────────────────────┐
         │    │   ai_partner_workspaces/            │
         │    │   └── user_{user_id}/               │
         │    │       └── rag_{rag_id}/             │
         │    │           ├── notes/   ← 用户文档   │
         │    │           ├── config/  ← 画像文件   │
         │    │           └── .claude/ ← Skills    │
         │    └─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       MySQL 数据库                                  │
│                   (用户认证、RAG 元数据)                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 部署前提条件

### 1. Claude Code CLI 安装与认证

这是项目的核心 - 必须正确安装和认证。

```bash
# 1. 安装 Claude Code CLI (全局)
npm install -g @anthropic-ai/claude-code

# 2. 验证安装
claude --version
# 应输出: claude X.Y.Z

# 3. 认证 Claude
# 方式 A: 使用 Anthropic 官方 API
export ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxx
claude auth

# 方式 B: 使用 Moonshot Kimi K2 (兼容 API)
# 在 ai_partner_runner/.env 中配置
```

### 2. 验证 Claude Code 可用

```bash
# 测试 Claude Code 是否正常工作
claude -p "你好，请简单介绍你自己"

# 如果成功，会输出 Claude 的回复
```

---

## 📁 目录结构

```
/Users/chaowang/rag platform/
├── rag-platform-mvp/
│   ├── frontend/                 # Vue.js 前端
│   ├── backend/                  # FastAPI 后端
│   ├── ai_partner_runner/        # Claude Skills 运行器
│   ├── ai_partner_workspaces/    # 用户工作区（自动创建）
│   │   └── user_{user_id}/
│   │       └── rag_{rag_id}/
│   │           ├── notes/        # 用户上传的文档（转为 .md）
│   │           ├── config/
│   │           │   ├── user-persona.md   # 用户画像
│   │           │   └── ai-persona.md     # AI 画像
│   │           └── .claude/
│   │               └── skills/
│   │                   └── ai-partner-chat/  # Claude Skill
│   └── contracts/                # NFT 智能合约
│
└── ai-partner-chat/              # Claude Skill 源码
    ├── SKILL.md                  # Skill 定义文件
    ├── scripts/                  # 向量化脚本
    └── assets/                   # 画像模板
```

---

## 🚀 部署步骤

### Step 1: 配置环境变量

#### AI Partner Runner (`ai_partner_runner/.env`)

```env
# ========== Claude Code 认证 ==========
# 方式 A: 直接使用 Anthropic API (推荐)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxx

# 方式 B: 使用 Moonshot Kimi K2 (兼容 API)
# ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic
# ANTHROPIC_AUTH_TOKEN=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# ========== Claude Code 配置 ==========
# Claude CLI 路径（通常自动检测）
CLAUDE_BIN=/Users/chaowang/.npm-global/bin/claude
# 或：/usr/local/bin/claude

# 重试配置
AI_PARTNER_CLAUDE_MAX_RETRIES=3
AI_PARTNER_CLAUDE_RETRY_BASE_SECONDS=1.0
AI_PARTNER_CLAUDE_RETRY_MAX_SECONDS=8.0

# ========== 工作区配置 ==========
# 工作区根目录
AI_PARTNER_WORKSPACES_DIR=/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces

# Skill 源码目录
AI_PARTNER_SKILL_SRC=/Users/chaowang/rag platform/ai-partner-chat
```

#### 后端 (`backend/.env`)

```env
# ========== 数据库 ==========
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=rag_platform

# ========== AI Partner Runner ==========
AI_PARTNER_RUNNER_URL=http://localhost:9001

# ========== 认证 ==========
JWT_SECRET=your-very-secure-jwt-secret-key

# ========== 可选：备用 LLM ==========
# 当 Claude Skills 不可用时的备选
ANTHROPIC_API_KEY=sk-ant-api03-xxx  # 备选 Claude API
OLLAMA_URL=http://localhost:11434   # 本地 Ollama
```

### Step 2: 安装依赖

```bash
# 1. 后端依赖
cd "/Users/chaowang/rag platform/rag-platform-mvp/backend"
pip install -r requirements.txt

# 2. AI Partner Runner 依赖
cd "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_runner"
pip install -r requirements.txt

# 3. 前端依赖
cd "/Users/chaowang/rag platform/rag-platform-mvp/frontend"
npm install
```

### Step 3: 启动服务

**终端 1: 启动 MySQL（如果使用 Docker）**
```bash
docker run -d --name rag-mysql \
  -e MYSQL_ROOT_PASSWORD=yourpassword \
  -e MYSQL_DATABASE=rag_platform \
  -p 3306:3306 \
  mysql:8.0
```

**终端 2: 启动 AI Partner Runner**
```bash
cd "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_runner"
python -m uvicorn app:app --host 0.0.0.0 --port 9001 --reload
```

**终端 3: 启动后端**
```bash
cd "/Users/chaowang/rag platform/rag-platform-mvp/backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**终端 4: 启动前端**
```bash
cd "/Users/chaowang/rag platform/rag-platform-mvp/frontend"
npm run dev
```

### Step 4: 验证部署

```bash
# 1. 检查 AI Partner Runner
curl http://localhost:9001/health
# 应返回: {"ok":true,"claude":"/path/to/claude",...}

# 2. 检查后端
curl http://localhost:8000/health

# 3. 访问前端
open http://localhost:5173
```

---

## 📋 工作流程

### 用户上传文件时发生了什么？

```
1. 用户上传 PDF/DOCX/TXT
       │
       ▼
2. 后端 /v1/rag/upload
   - 提取文本
   - 生成 rag_id
       │
       ▼
3. 调用 AI Partner Runner /v1/aipartner/build
   - 创建 workspace: ai_partner_workspaces/user_xxx/rag_xxx/
   - 将文档转为 .md 存入 notes/
   - 安装 Claude Skill
   - 生成用户画像 (user-persona.md)
   - 生成 AI 画像 (ai-persona.md)
   - 构建知识图谱
       │
       ▼
4. 返回成功，用户可以开始聊天
```

### 用户聊天时发生了什么？

```
1. 用户发送问题
       │
       ▼
2. 后端 /v1/chat/stream
   - 获取用户记忆
   - 代理到 AI Partner Runner
       │
       ▼
3. AI Partner Runner /v1/aipartner/chat
   - 定位 workspace
   - 构建 prompt (包含用户画像)
       │
       ▼
4. 调用 Claude Code CLI
   claude -p "..." --output-format stream-json
       │
       ▼
5. Claude Code 执行 Skill
   - 读取 notes/ 中的文档
   - 读取 config/user-persona.md
   - 基于上下文生成回答
       │
       ▼
6. 流式返回给前端
```

---

## 🔐 安全配置

### API Key 保护

```bash
# 确保 .env 文件不被提交到 Git
echo "*.env" >> .gitignore
echo ".env" >> .gitignore

# 生产环境使用环境变量
export ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

### Claude Code 信任设置

```bash
# 允许 Claude Code 在工作区执行
export CLAUDE_DISABLE_TELEMETRY=1

# 或在 ~/.claude/settings.json 中配置
```

---

## 🐳 Docker 部署（生产环境）

### docker-compose.yml

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_DATABASE: rag_platform
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  runner:
    build: ./ai_partner_runner
    ports:
      - "9001:9001"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CLAUDE_BIN=/usr/local/bin/claude
    volumes:
      - ./ai_partner_workspaces:/app/ai_partner_workspaces
      - ../ai-partner-chat:/app/skill_src
      # 挂载 Claude 配置（认证信息）
      - ~/.claude:/root/.claude:ro

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - AI_PARTNER_RUNNER_URL=http://runner:9001
      - MYSQL_HOST=mysql
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - mysql
      - runner
    volumes:
      - ./ai_partner_workspaces:/app/ai_partner_workspaces

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  mysql_data:
```

### Runner Dockerfile

```dockerfile
FROM python:3.11-slim

# 安装 Node.js (for Claude CLI)
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs

# 安装 Claude CLI
RUN npm install -g @anthropic-ai/claude-code

# 安装 Python 依赖
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9001"]
```

---

## ⚠️ 常见问题

### Q: Claude Code CLI 报错 "API key not valid"

```bash
# 1. 检查环境变量
echo $ANTHROPIC_API_KEY

# 2. 重新登录
claude logout
claude login

# 3. 或直接设置
export ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

### Q: AI Partner Runner 无法找到 claude 二进制

```bash
# 1. 找到 claude 安装位置
which claude
# 或
npm list -g | grep claude

# 2. 在 .env 中设置正确路径
CLAUDE_BIN=/Users/your_user/.npm-global/bin/claude
```

### Q: 聊天无响应

```bash
# 1. 检查 Runner 日志
tail -f /tmp/runner.log

# 2. 确认 workspace 存在
ls -la ai_partner_workspaces/user_xxx/rag_xxx/notes/

# 3. 手动测试 Claude
cd ai_partner_workspaces/user_xxx/rag_xxx/
claude -p "请阅读 notes/ 目录中的文档，然后回答问题：这个文档是关于什么的？"
```

### Q: 深度研究功能不工作

深度研究需要 LLM 支持。确保以下之一可用：
1. `ANTHROPIC_API_KEY` 已设置（后端备用 Claude API）
2. Ollama 正在运行（`ollama serve`）

---

## 📊 监控与日志

### 查看各服务日志

```bash
# Runner 日志
tail -f /tmp/runner.log

# 后端日志
tail -f /tmp/backend.log

# Claude Code 调用追踪
# 在 Runner 请求中设置 show_tool_trace: true
```

### 健康检查

```bash
# 一键检查所有服务
echo "=== AI Partner Runner ===" && curl -s http://localhost:9001/health | jq
echo "=== Backend ===" && curl -s http://localhost:8000/health | jq
echo "=== Frontend ===" && curl -s http://localhost:5173 | head -5
```

---

## ✅ 部署检查清单

- [ ] Claude Code CLI 已安装 (`claude --version`)
- [ ] Claude 已认证 (`claude auth` 或设置 `ANTHROPIC_API_KEY`)
- [ ] AI Partner Runner `.env` 已配置
- [ ] Backend `.env` 已配置
- [ ] MySQL 数据库已启动
- [ ] AI Partner Runner 运行在 9001 端口
- [ ] Backend 运行在 8000 端口
- [ ] Frontend 运行在 5173 端口
- [ ] `/health` 端点返回正常

---

## 🎯 关键点总结

1. **核心依赖**: Claude Code CLI - 必须正确安装和认证
2. **数据流**: 用户文件 → .md 存入 notes/ → Claude Code 读取并回答
3. **认证链**: Anthropic API Key → Claude Code CLI → AI Partner Runner → Backend → Frontend
4. **工作区隔离**: 每个用户的每个 RAG 都有独立的工作区
5. **Skill 机制**: `ai-partner-chat` Skill 定义了 Claude 如何读取笔记和生成回答

