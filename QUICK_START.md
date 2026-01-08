# 快速启动指南

## 🚀 一键启动（推荐）

最简单的方式，一键启动所有服务：

```bash
# 进入项目根目录
cd "/Users/chaowang/rag platform/rag-platform-mvp"

# 一键启动所有服务
./start_all.sh
```

这个脚本会：
1. ✅ 自动启动 AI Partner Runner（后台）
2. ✅ 自动启动 Backend 和 Frontend（Docker）
3. ✅ 检查服务健康状态

**停止所有服务：**
```bash
./stop_all.sh
```

---

## 🚀 手动启动（分步）

### 步骤 1：启动 AI Partner Runner（宿主机）

AI Partner Runner **必须在宿主机运行**，不能放在 Docker 容器中。

```bash
# 进入 Runner 目录
cd "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_runner"

# 方式 1：使用启动脚本（推荐）
./start_standalone.sh

# 方式 2：手动启动
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# 编辑 .env，填入 ANTHROPIC_AUTH_TOKEN
uvicorn app:app --host 0.0.0.0 --port 9001 --reload
```

**验证 Runner 启动成功：**
```bash
curl http://localhost:9001/health
# 应该返回 {"ok": true, ...}
```

---

### 步骤 2：启动 Backend 和 Frontend（Docker）

在**新的终端窗口**中：

```bash
# 进入项目根目录
cd "/Users/chaowang/rag platform/rag-platform-mvp"

# 启动所有服务
docker-compose up --build

# 或后台运行
docker-compose up -d --build
```

**验证服务：**
```bash
# Backend
curl http://localhost:8000/

# Frontend（浏览器）
open http://localhost:8080
```

---

### 步骤 3：访问系统

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Runner API**: http://localhost:9001

---

## ⚙️ 环境配置

### AI Partner Runner 配置（`.env` 文件）

位置：`ai_partner_runner/.env`

**必须配置：**
```bash
ANTHROPIC_AUTH_TOKEN="你的 Moonshot API Key"
```

**可选配置（已有默认值）：**
```bash
AI_PARTNER_SKILL_SRC="/Users/chaowang/rag platform/ai-partner-chat"
AI_PARTNER_WORKSPACES_DIR="/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces"
CLAUDE_BIN="/Users/chaowang/.npm-global/bin/claude"
ANTHROPIC_BASE_URL="https://api.moonshot.cn/anthropic"
ANTHROPIC_MODEL="kimi-k2-thinking-turbo"
```

---

## 🔍 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| AI Partner Runner | 9001 | 宿主机运行，处理 RAG 和对话 |
| Backend | 8000 | Docker 容器，API 网关 |
| Frontend | 8080 | Docker 容器，Web 界面 |

---

## ✅ 启动检查清单

启动后，请验证：

- [ ] Runner 健康检查：`curl http://localhost:9001/health`
- [ ] Backend 健康检查：`curl http://localhost:8000/`
- [ ] Frontend 可访问：http://localhost:8080
- [ ] 可以上传文件
- [ ] 可以进行对话

---

## 🐛 常见问题

### 问题 1：Runner 启动失败

**错误：** `claude binary not found`

**解决：**
```bash
# 检查 Claude Code
which claude
claude --version

# 如果找不到，检查 .env 中的 CLAUDE_BIN
cat ai_partner_runner/.env | grep CLAUDE_BIN
```

### 问题 2：API Key 错误

**错误：** `Invalid API key · Please run /login`

**解决：**
```bash
# 检查 .env 文件
cat ai_partner_runner/.env | grep ANTHROPIC_AUTH_TOKEN

# 确保 API Key 正确，然后重启 Runner
```

### 问题 3：Backend 无法连接 Runner

**错误：** `Connection refused` 或 `host.docker.internal:9001`

**解决：**
```bash
# 1. 确保 Runner 在宿主机运行
curl http://localhost:9001/health

# 2. 重启 Docker 容器
docker-compose restart backend
```

---

## 📝 使用流程

### 1. 上传文件并构建 RAG

通过前端界面上传文件，或调用 API：
```bash
curl -X POST http://localhost:8000/v1/rag/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@your_document.pdf"
```

### 2. 开始对话

通过前端界面提问，或调用 API：
```bash
curl -X POST http://localhost:8000/v1/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_xxx",
    "question": "这篇文档的主要内容是什么？"
  }'
```

### 3. 查看知识图谱

通过前端界面查看，或调用 API：
```bash
curl -X GET "http://localhost:9001/v1/aipartner/knowledge-graph?rag_id=rag_xxx&user_id=user_xxx"
```

---

## 🔄 停止服务

### 方式 1：使用停止脚本（推荐）

```bash
cd "/Users/chaowang/rag platform/rag-platform-mvp"
./stop_all.sh
```

### 方式 2：手动停止

**停止 Runner：**
- 如果在终端前台运行，按 `Ctrl+C`
- 如果后台运行，使用：`kill $(cat .runner.pid)` 或 `pkill -f "uvicorn app:app"`

**停止 Docker 服务：**
```bash
docker-compose down
```

---

## 📚 更多文档

- [完整启动指南](./START_GUIDE.md) - 详细的启动说明
- [AI Partner Runner 独立启动](./ai_partner_runner/STANDALONE_START.md) - Runner 详细文档
- [多租户系统指南](./MULTI_TENANT_GUIDE.md) - 用户认证和使用
- [完整架构文档](./COMPLETE_ARCHITECTURE.md) - 系统架构详解

---

## 💡 提示

1. **开发模式**：Runner 使用 `--reload` 参数，代码修改后自动重启
2. **生产模式**：去掉 `--reload`，使用进程管理器
3. **多终端**：Runner 和 Docker 需要在不同的终端窗口运行
4. **端口占用**：如果端口被占用，可以修改端口或停止占用进程

---

**最后更新**：2025-01-20

