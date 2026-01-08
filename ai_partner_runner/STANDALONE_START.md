# AI Partner Runner 独立启动指南

## 📋 概述

AI Partner Runner 可以独立运行，不依赖 Docker 的 backend/frontend。适合：
- 本地开发和测试
- 直接使用 AI Partner 功能
- 调试和问题排查

## 🚀 快速启动

### 步骤 1：检查环境

```bash
# 检查 Python
python3 --version  # 需要 3.9+

# 检查 Claude Code
claude --version   # 需要已安装

# 检查 ripgrep（可选）
rg --version       # 或 ripgrepy 会自动处理
```

### 步骤 2：进入目录并设置虚拟环境

```bash
cd "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_runner"

# 创建虚拟环境（如果还没有）
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3：配置环境变量

```bash
# 复制示例配置文件
cp env.example .env

# 编辑 .env 文件，填入必要的配置
# 至少需要设置：
# - ANTHROPIC_AUTH_TOKEN: 你的 Moonshot API Key
```

**最小配置示例（.env）：**
```bash
# AI Partner Skill 路径
AI_PARTNER_SKILL_SRC="/Users/chaowang/rag platform/ai-partner-chat"

# Workspaces 目录
AI_PARTNER_WORKSPACES_DIR="/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces"

# Claude Code CLI 路径
CLAUDE_BIN="/Users/chaowang/.npm-global/bin/claude"

# Moonshot API 配置（必须）
ANTHROPIC_BASE_URL="https://api.moonshot.cn/anthropic"
ANTHROPIC_AUTH_TOKEN="你的 Moonshot API Key"
ANTHROPIC_MODEL="kimi-k2-thinking-turbo"
ANTHROPIC_SMALL_FAST_MODEL="kimi-k2-thinking-turbo"
```

### 步骤 4：启动服务

```bash
# 启动 Runner（开发模式，支持热重载）
uvicorn app:app --host 0.0.0.0 --port 9001 --reload

# 或生产模式（无热重载）
uvicorn app:app --host 0.0.0.0 --port 9001
```

## ✅ 验证服务

### 健康检查

```bash
curl http://localhost:9001/health
```

**预期响应：**
```json
{
  "ok": true,
  "claude": "/Users/chaowang/.npm-global/bin/claude",
  "skill_src": "/Users/chaowang/rag platform/ai-partner-chat",
  "workspaces_dir": "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces"
}
```

## 📝 直接使用 API

### 1. 构建 RAG（上传文档）

```bash
curl -X POST http://localhost:9001/v1/aipartner/build \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_rag_1",
    "file_name": "test.md",
    "extracted_text": "# 测试文档\n\n这是一份测试文档的内容。",
    "user_id": "test_user_1"
  }'
```

**响应：**
```json
{
  "rag_id": "test_rag_1",
  "ok": true,
  "workspace": "/path/to/workspace/test_rag_1",
  "warning": null
}
```

### 2. 开始对话

```bash
curl -X POST http://localhost:9001/v1/aipartner/chat \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_rag_1",
    "user_id": "test_user_1",
    "messages": [
      {"role": "user", "content": "这篇文档的主要内容是什么？"}
    ],
    "stream": false,
    "mode": "claude"
  }'
```

### 3. 获取知识图谱

```bash
curl -X POST http://localhost:9001/v1/aipartner/knowledge-graph \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_rag_1",
    "user_id": "test_user_1"
  }'
```

### 4. 重新生成画像

```bash
curl -X POST http://localhost:9001/v1/aipartner/personas/generate \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "test_rag_1",
    "user_id": "test_user_1",
    "force": true
  }'
```

## 🔧 常用操作

### 查看工作空间

```bash
# 查看所有工作空间
ls -la "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces/"

# 查看特定用户的工作空间
ls -la "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces/user_test_user_1/"

# 查看特定 RAG 的内容
ls -la "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces/user_test_user_1/test_rag_1/"
```

### 手动创建测试文档

```bash
# 创建测试 workspace
mkdir -p "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces/user_test_user_1/test_rag_1/notes"

# 创建测试文档
cat > "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_workspaces/user_test_user_1/test_rag_1/notes/test.md" << 'EOF'
# 测试文档

这是一个测试文档。

## 主要内容

1. 第一点
2. 第二点
3. 第三点

## 总结

这是文档的总结部分。
EOF
```

### 查看日志

Runner 运行在终端中，直接查看输出即可。如果需要保存日志：

```bash
# 启动并保存日志
uvicorn app:app --host 0.0.0.0 --port 9001 --reload 2>&1 | tee runner.log
```

## 🐛 故障排查

### 问题 1：端口被占用

```bash
# 检查端口占用
lsof -i :9001

# 或使用其他端口
uvicorn app:app --host 0.0.0.0 --port 9002 --reload
```

### 问题 2：Claude Code 找不到

```bash
# 检查 Claude Code
which claude
claude --version

# 如果找不到，检查 .env 中的 CLAUDE_BIN 路径
cat .env | grep CLAUDE_BIN
```

### 问题 3：API Key 错误

```bash
# 检查 .env 配置
cat .env | grep ANTHROPIC_AUTH_TOKEN

# 确保 API Key 正确，然后重启服务
```

### 问题 4：Skill 路径错误

```bash
# 检查 skill 目录是否存在
ls -la "/Users/chaowang/rag platform/ai-partner-chat"

# 检查 .env 中的路径
cat .env | grep AI_PARTNER_SKILL_SRC
```

## 📊 性能监控

### 查看服务状态

```bash
# 健康检查
curl http://localhost:9001/health

# 查看进程
ps aux | grep uvicorn
```

### 测试响应时间

```bash
# 测试构建时间
time curl -X POST http://localhost:9001/v1/aipartner/build \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "perf_test", "file_name": "test.md", "extracted_text": "test"}'

# 测试对话时间
time curl -X POST http://localhost:9001/v1/aipartner/chat \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "perf_test", "messages": [{"role": "user", "content": "test"}]}'
```

## 🎯 使用场景

### 场景 1：本地开发测试

```bash
# 启动 Runner
uvicorn app:app --host 0.0.0.0 --port 9001 --reload

# 在另一个终端测试
curl http://localhost:9001/health
```

### 场景 2：直接集成到其他应用

```python
import httpx

# 构建 RAG
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:9001/v1/aipartner/build",
        json={
            "rag_id": "my_rag",
            "file_name": "doc.md",
            "extracted_text": "文档内容...",
            "user_id": "user_123"
        }
    )
    print(response.json())
```

### 场景 3：命令行工具

```bash
# 创建简单的 CLI 脚本
cat > rag_cli.sh << 'EOF'
#!/bin/bash
RAG_ID=$1
QUESTION=$2
TOKEN=$3

curl -X POST http://localhost:9001/v1/aipartner/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"rag_id\": \"$RAG_ID\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$QUESTION\"}]
  }"
EOF

chmod +x rag_cli.sh
./rag_cli.sh "my_rag" "文档内容是什么？"
```

## 🔄 与 Docker Backend 集成

如果后续需要与 Docker Backend 集成：

1. **保持 Runner 在宿主机运行**（端口 9001）
2. **启动 Docker Backend**（端口 8000）
3. **Backend 通过 `host.docker.internal:9001` 访问 Runner**

```bash
# Backend 环境变量
AI_PARTNER_RUNNER_URL=http://host.docker.internal:9001
```

## 📚 相关文档

- `README.md` - 完整使用说明
- `MULTI_TENANT_GUIDE.md` - 多租户系统指南
- `START_GUIDE.md` - 完整系统启动指南

## 💡 提示

1. **开发模式**：使用 `--reload` 参数，代码修改后自动重启
2. **生产模式**：去掉 `--reload`，使用进程管理器（如 systemd, supervisor）
3. **多实例**：可以启动多个 Runner 实例，使用不同端口
4. **反向代理**：可以使用 Nginx 做负载均衡和 SSL 终止

