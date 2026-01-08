# 系统启动指南

## 📋 前置条件

### 1. 安装 Claude Code CLI

```bash
# 创建 npm 全局目录（如果还没有）
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc

# 安装 Claude Code
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
which claude
```

### 2. 安装 ripgrep（可选，ripgrepy 会自动处理）

```bash
# macOS
brew install ripgrep

# 或使用 pip 安装 ripgrepy（会自动处理）
# 已在 requirements.txt 中包含
```

### 3. 准备 API Key

- **Moonshot API Key**：用于 Claude Code（Kimi 模型）
- 如果没有，可以注册：https://platform.moonshot.cn/

---

## 🚀 启动步骤

### 步骤 1：启动 AI Partner Runner（宿主机）

AI Partner Runner **必须在宿主机运行**，不能放在 Docker 容器中。

```bash
# 1. 进入目录
cd "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_runner"

# 2. 创建虚拟环境（如果还没有）
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp env.example .env
# 编辑 .env 文件，填入你的配置：
# - ANTHROPIC_AUTH_TOKEN: 你的 Moonshot API Key
# - AI_PARTNER_SKILL_SRC: ai-partner-chat 的路径（已默认配置）
# - AI_PARTNER_WORKSPACES_DIR: workspaces 目录（已默认配置）
# - CLAUDE_BIN: Claude Code 的路径（已默认配置）

# 5. 启动服务
uvicorn app:app --host 0.0.0.0 --port 9001 --reload
```

**验证 Runner 是否启动成功：**

```bash
# 健康检查
curl http://localhost:9001/health

# 应该返回：
# {
#   "ok": true,
#   "claude": "/Users/chaowang/.npm-global/bin/claude",
#   "skill_src": "/Users/chaowang/rag platform/ai-partner-chat",
#   "workspaces_dir": "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces"
# }
```

### 步骤 2：启动 Backend 和 Frontend（Docker）

在**新的终端窗口**中：

```bash
# 进入项目根目录
cd "/Users/chaowang/rag platform/rag-platform-mvp"

# 启动所有服务（backend + frontend）
docker-compose up --build

# 或者后台运行
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

**验证服务：**

```bash
# Backend 健康检查
curl http://localhost:8000/

# Frontend（浏览器访问）
open http://localhost:8080
```

---

## 🔧 环境配置说明

### AI Partner Runner 环境变量（`.env` 文件）

```bash
# ai-partner-chat skill 路径
AI_PARTNER_SKILL_SRC="/Users/chaowang/rag platform/ai-partner-chat"

# Workspaces 目录
AI_PARTNER_WORKSPACES_DIR="/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces"

# Claude Code CLI 路径
CLAUDE_BIN="/Users/chaowang/.npm-global/bin/claude"

# Moonshot API 配置
ANTHROPIC_BASE_URL="https://api.moonshot.cn/anthropic"
ANTHROPIC_AUTH_TOKEN="你的 Moonshot API Key"
ANTHROPIC_MODEL="kimi-k2-thinking-turbo"
ANTHROPIC_SMALL_FAST_MODEL="kimi-k2-thinking-turbo"

# 画像生成配置
AI_PARTNER_PERSONA_MAX_NOTES=20
AI_PARTNER_PERSONA_NOTE_MAX_CHARS=6000
AI_PARTNER_PERSONA_SIGNALS_MAX_CHARS=60000
```

### Docker 环境变量（`docker-compose.yml`）

```yaml
environment:
  - AI_PARTNER_RUNNER_URL=http://host.docker.internal:9001
```

---

## 📝 使用流程

### 1. 上传文件并构建 RAG

```bash
# 通过前端上传文件，或直接调用 API
curl -X POST http://localhost:8000/v1/rag/ \
  -F "file=@your_document.pdf"
```

### 2. 开始对话

```bash
# 通过前端界面提问，或调用 API
curl -X POST http://localhost:8000/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_1",
    "question": "这篇文档的主要内容是什么？"
  }'
```

### 3. 查看知识图谱

```bash
# 获取知识图谱数据
curl -X POST http://localhost:9001/v1/aipartner/knowledge-graph \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "rag_1"}'
```

---

## 🐛 常见问题排查

### 问题 1：Runner 启动失败

**错误：** `claude binary not found`

**解决：**
```bash
# 检查 Claude Code 是否安装
which claude
claude --version

# 如果找不到，检查 PATH
echo $PATH | grep npm-global

# 确保 .env 中的 CLAUDE_BIN 路径正确
```

### 问题 2：API Key 错误

**错误：** `Invalid API key · Please run /login`

**解决：**
```bash
# 检查 .env 文件中的 ANTHROPIC_AUTH_TOKEN
cat ai_partner_runner/.env | grep ANTHROPIC_AUTH_TOKEN

# 确保 API Key 正确，然后重启 Runner
```

### 问题 3：Backend 无法连接 Runner

**错误：** `Connection refused` 或 `host.docker.internal:9001`

**解决：**
```bash
# 1. 确保 Runner 在宿主机运行
curl http://localhost:9001/health

# 2. 检查 docker-compose.yml 中的配置
# 确保有 extra_hosts 和 AI_PARTNER_RUNNER_URL

# 3. 重启 Docker 容器
docker-compose restart backend
```

### 问题 4：Ripgrep 搜索失败

**错误：** `Ripgrep search failed`

**解决：**
```bash
# 安装 ripgrep（如果还没有）
brew install ripgrep  # macOS
# 或
pip install ripgrepy  # Python 包会自动处理
```

### 问题 5：知识图谱为空

**原因：** 实体提取可能没有找到匹配的模式

**解决：**
- 检查 `notes/` 目录中是否有文件
- 确保文件是 `.md` 或 `.txt` 格式
- 查看 Runner 日志中的错误信息

---

## 🔍 服务端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| AI Partner Runner | 9001 | 宿主机运行，处理 RAG 构建和对话 |
| Backend | 8000 | Docker 容器，API 网关 |
| Frontend | 8080 | Docker 容器，Web 界面 |

---

## 📊 监控和日志

### 查看 Runner 日志

Runner 运行在终端中，直接查看输出。

### 查看 Docker 日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 查看工作空间

```bash
# Workspaces 目录
ls -la "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces/"

# 查看特定 RAG 的工作空间
ls -la "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces/rag_1/"
```

---

## 🎯 快速启动脚本

创建 `start.sh` 文件：

```bash
#!/bin/bash

# 启动 AI Partner Runner
cd "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_runner"
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 9001 --reload &
RUNNER_PID=$!

echo "AI Partner Runner started (PID: $RUNNER_PID)"
echo "Waiting for Runner to be ready..."
sleep 3

# 启动 Docker 服务
cd "/Users/chaowang/rag platform/rag-platform-mvp"
docker-compose up --build

# 清理（Ctrl+C 时）
trap "kill $RUNNER_PID; docker-compose down" EXIT
```

使用：

```bash
chmod +x start.sh
./start.sh
```

---

## ✅ 验证清单

启动后，请验证以下内容：

- [ ] Claude Code 已安装：`claude --version`
- [ ] Runner 健康检查通过：`curl http://localhost:9001/health`
- [ ] Backend 健康检查通过：`curl http://localhost:8000/`
- [ ] Frontend 可以访问：`http://localhost:8080`
- [ ] 可以上传文件并构建 RAG
- [ ] 可以进行对话
- [ ] 可以获取知识图谱数据

---

## 🆘 需要帮助？

如果遇到问题：

1. 检查所有服务的日志
2. 验证环境变量配置
3. 确认端口没有被占用
4. 查看 `MIGRATION_SUMMARY.md` 了解架构变更

