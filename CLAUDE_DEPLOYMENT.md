# RAG Platform - Claude 集成部署指南

## 🏗️ 架构概览

本项目使用 **三层 LLM 架构**，确保 Claude 能力完整封装：

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue.js)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      后端 API (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ 聊天 API    │  │ 深度研究    │  │ 知识图谱    │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LLM 层 (优先级)                             │
│  1️⃣ AI Partner Runner (Claude Code CLI)  ← 主力                 │
│  2️⃣ Anthropic API (Claude Sonnet)        ← 备选                 │
│  3️⃣ Ollama (本地模型)                    ← 离线备份              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 部署方式选择

### 方式一：Claude Code CLI（推荐 - 最强能力）

这是项目默认使用的方式，通过 Claude Code CLI 获得完整的 Agent 能力（工具调用、文件操作等）。

#### 步骤 1: 安装 Claude Code CLI

```bash
# 全局安装 Claude Code
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
```

#### 步骤 2: 配置 API 认证

编辑 `ai_partner_runner/.env`:

```env
# === Claude Code 认证 ===
# 方式 A: 直接使用 Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx

# 方式 B: 使用兼容 API（如 Moonshot Kimi K2）
ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic
ANTHROPIC_AUTH_TOKEN=sk-xxxxxxxxxx

# Claude Code 配置
CLAUDE_BIN=/usr/local/bin/claude  # 或 ~/.npm-global/bin/claude
AI_PARTNER_CLAUDE_MAX_RETRIES=3
AI_PARTNER_CLAUDE_RETRY_BASE_SECONDS=1.0
```

#### 步骤 3: 登录 Claude

```bash
# 首次使用需要登录
claude login

# 或使用 API Key 登录
export ANTHROPIC_API_KEY=sk-ant-api03-xxxx
claude auth
```

---

### 方式二：Anthropic API（简单直接）

如果不需要 Agent 能力，可以直接使用 Anthropic API。

#### 配置后端

编辑 `backend/.env`:

```env
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx

# 模型选择
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

#### 后端会自动优先使用 Claude

代码逻辑（`citation_chat_router.py`）：

```python
async def generate_llm_response(...):
    # 优先级 1: Anthropic Claude
    if anthropic_key:
        client = anthropic.Anthropic(api_key=anthropic_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            ...
        )
        return response.content[0].text
    
    # 优先级 2: OpenAI
    # 优先级 3: Ollama 本地
```

---

### 方式三：AWS Bedrock Claude（企业级）

适合生产环境的企业级部署。

#### 配置

编辑 `backend/.env`:

```env
# AWS Bedrock 配置
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

#### 需要修改后端代码支持 Bedrock

```python
import boto3
from botocore.config import Config

def get_bedrock_client():
    return boto3.client(
        'bedrock-runtime',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        config=Config(read_timeout=120)
    )

async def generate_claude_response_bedrock(prompt: str) -> str:
    client = get_bedrock_client()
    response = client.invoke_model(
        modelId=os.getenv('BEDROCK_MODEL_ID'),
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        })
    )
    return json.loads(response['body'].read())['content'][0]['text']
```

---

## 🚀 完整部署步骤

### 1. 环境准备

```bash
cd "/Users/chaowang/rag platform/rag-platform-mvp"

# 安装后端依赖
cd backend
pip install anthropic httpx python-dotenv

# 安装 AI Partner Runner 依赖
cd ../ai_partner_runner
pip install -r requirements.txt

# 安装前端依赖
cd ../frontend
npm install
```

### 2. 配置文件设置

**`backend/.env`:**

```env
# === 数据库 ===
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DB=rag_platform

# === Claude API (后端备选) ===
ANTHROPIC_API_KEY=sk-ant-api03-xxxx

# === AI Partner Runner ===
AI_PARTNER_RUNNER_URL=http://localhost:9001

# === 其他 ===
JWT_SECRET=your-secret-key
OLLAMA_URL=http://localhost:11434
```

**`ai_partner_runner/.env`:**

```env
# === Claude Code 认证（主力 LLM）===
# 选项 A: 直接 Anthropic
ANTHROPIC_API_KEY=sk-ant-api03-xxxx

# 选项 B: Moonshot Kimi K2 (兼容 API)
# ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic
# ANTHROPIC_AUTH_TOKEN=sk-xxx

# === Claude 配置 ===
CLAUDE_BIN=/usr/local/bin/claude
AI_PARTNER_CLAUDE_MAX_RETRIES=3
```

### 3. 启动服务

```bash
# 终端 1: 启动后端
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2: 启动 AI Partner Runner
cd ai_partner_runner
python -m uvicorn app:app --host 0.0.0.0 --port 9001 --reload

# 终端 3: 启动前端
cd frontend
npm run dev

# 终端 4: (可选) 启动 Ollama 作为备份
ollama serve
```

### 4. 验证 Claude 集成

```bash
# 测试 AI Partner Runner
curl -X POST http://localhost:9001/v1/aipartner/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"你好，你是谁？"}],"mode":"claude"}'

# 测试后端聊天
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test123456"}' | jq -r '.access_token')

curl -X POST http://localhost:8000/v1/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rag_id":"your_rag_id","question":"测试问题"}'
```

---

## 🐳 Docker 部署（生产环境）

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AI_PARTNER_RUNNER_URL=http://runner:9001
      - MYSQL_HOST=mysql
    depends_on:
      - mysql
      - runner
    volumes:
      - ./ai_partner_workspaces:/app/ai_partner_workspaces

  runner:
    build: ./ai_partner_runner
    ports:
      - "9001:9001"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./ai_partner_workspaces:/app/ai_partner_workspaces
      - ~/.claude:/root/.claude  # Claude Code 配置

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_DATABASE: rag_platform
    volumes:
      - mysql_data:/var/lib/mysql

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  mysql_data:
  ollama_data:
```

### 启动生产环境

```bash
# 创建 .env 文件
echo "ANTHROPIC_API_KEY=sk-ant-api03-xxxx" > .env
echo "MYSQL_PASSWORD=your-secure-password" >> .env

# 启动所有服务
docker-compose up -d
```

---

## 📊 LLM 调用链路

```
用户提问
    │
    ▼
┌─────────────────────────────────────┐
│  后端 /v1/chat/stream               │
│  ↓                                  │
│  1. AI Partner Runner (Claude Code) │ ← 主力：完整 Agent 能力
│     - 文件读写                       │
│     - 工具调用                       │
│     - 多轮对话记忆                   │
│  ↓ (失败时)                         │
│  2. Anthropic API (Claude Sonnet)   │ ← 备选：纯文本生成
│  ↓ (失败时)                         │
│  3. Ollama (本地 qwen2.5:7b)        │ ← 离线兜底
└─────────────────────────────────────┘
    │
    ▼
流式返回给前端
```

---

## ⚠️ 常见问题

### Q: Claude Code CLI 报错 "API key not valid"

```bash
# 重新认证
claude logout
claude login

# 或设置环境变量
export ANTHROPIC_API_KEY=sk-ant-api03-xxxx
```

### Q: AI Partner Runner 无响应

```bash
# 检查服务状态
curl http://localhost:9001/health

# 查看日志
tail -f /tmp/runner.log

# 重启服务
pkill -f "uvicorn app:app"
cd ai_partner_runner
python -m uvicorn app:app --port 9001 --reload
```

### Q: 如何切换到纯 Anthropic API 模式

在 `backend/.env` 中设置:

```env
# 禁用 AI Partner Runner
AI_PARTNER_RUNNER_URL=

# 启用 Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-xxxx
```

---

## 🔐 安全建议

1. **API Key 保护**: 永远不要将 API Key 提交到 Git
2. **环境隔离**: 使用 `.env` 文件，并加入 `.gitignore`
3. **速率限制**: 在后端添加请求限制防止 API 滥用
4. **日志脱敏**: 确保日志中不包含敏感信息

---

## 📝 总结

| 方式 | 能力等级 | 适用场景 | 配置复杂度 |
|------|---------|---------|-----------|
| Claude Code CLI | ⭐⭐⭐⭐⭐ | 开发/测试 | 中等 |
| Anthropic API | ⭐⭐⭐⭐ | 生产环境 | 简单 |
| AWS Bedrock | ⭐⭐⭐⭐ | 企业生产 | 复杂 |
| Ollama 备份 | ⭐⭐⭐ | 离线/降级 | 简单 |

**推荐配置**: Claude Code CLI (主力) + Anthropic API (备选) + Ollama (离线)

