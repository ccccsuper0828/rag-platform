#!/bin/bash
# RAG Platform 一键启动脚本
# 基于 Claude Skills 架构

set -e

PROJECT_DIR="/Users/chaowang/rag platform/rag-platform-mvp"
LOG_DIR="/tmp"

echo "🚀 RAG Platform 启动脚本"
echo "========================="
echo ""

# 1. 检查 Claude Code CLI
echo "📋 检查 Claude Code CLI..."
CLAUDE_BIN="${CLAUDE_BIN:-$(which claude 2>/dev/null || echo "$HOME/.npm-global/bin/claude")}"

if [ ! -f "$CLAUDE_BIN" ]; then
    echo "❌ Claude Code CLI 未找到！"
    echo "   请运行: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

echo "   ✅ Claude CLI: $CLAUDE_BIN"

# 检查 Claude 认证
if [ -z "$ANTHROPIC_API_KEY" ]; then
    if [ -f "$PROJECT_DIR/ai_partner_runner/.env" ]; then
        source "$PROJECT_DIR/ai_partner_runner/.env" 2>/dev/null || true
    fi
fi

if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$ANTHROPIC_AUTH_TOKEN" ]; then
    echo "⚠️  警告: ANTHROPIC_API_KEY 未设置"
    echo "   Claude Code 可能无法正常工作"
    echo "   请在 ai_partner_runner/.env 中配置"
fi

echo ""

# 2. 停止已有进程
echo "📋 停止已有进程..."
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "uvicorn app:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 2
echo "   ✅ 已清理"
echo ""

# 3. 启动 AI Partner Runner
echo "📋 启动 AI Partner Runner (port 9001)..."
cd "$PROJECT_DIR/ai_partner_runner"
nohup python -m uvicorn app:app --host 0.0.0.0 --port 9001 --reload > "$LOG_DIR/runner.log" 2>&1 &
RUNNER_PID=$!
sleep 3

# 验证 Runner
if curl -s http://localhost:9001/health | grep -q '"ok":true'; then
    echo "   ✅ Runner 启动成功 (PID: $RUNNER_PID)"
else
    echo "   ❌ Runner 启动失败，查看日志: $LOG_DIR/runner.log"
    tail -20 "$LOG_DIR/runner.log"
    exit 1
fi
echo ""

# 4. 启动后端
echo "📋 启动后端 API (port 8000)..."
cd "$PROJECT_DIR/backend"
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
sleep 3

# 验证后端
if curl -s http://localhost:8000/health 2>/dev/null | grep -q "ok\|healthy"; then
    echo "   ✅ 后端启动成功 (PID: $BACKEND_PID)"
elif curl -s http://localhost:8000/v1/auth/login -X OPTIONS 2>/dev/null | head -1 | grep -q ""; then
    echo "   ✅ 后端启动成功 (PID: $BACKEND_PID)"
else
    echo "   ⚠️  后端可能仍在启动中..."
    echo "   查看日志: $LOG_DIR/backend.log"
fi
echo ""

# 5. 启动前端
echo "📋 启动前端 (port 5173)..."
cd "$PROJECT_DIR/frontend"
nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
sleep 3
echo "   ✅ 前端启动成功 (PID: $FRONTEND_PID)"
echo ""

# 6. 显示状态
echo "========================="
echo "✅ RAG Platform 启动完成!"
echo "========================="
echo ""
echo "📍 服务地址:"
echo "   前端:     http://localhost:5173"
echo "   后端 API: http://localhost:8000"
echo "   Runner:   http://localhost:9001"
echo ""
echo "📋 日志文件:"
echo "   Runner:   $LOG_DIR/runner.log"
echo "   Backend:  $LOG_DIR/backend.log"
echo "   Frontend: $LOG_DIR/frontend.log"
echo ""
echo "🔧 Claude Skills 配置:"
echo "   Claude CLI:  $CLAUDE_BIN"
echo "   Workspaces:  $PROJECT_DIR/ai_partner_workspaces/"
echo "   Skill 源码:  /Users/chaowang/rag platform/ai-partner-chat/"
echo ""
echo "📖 详细部署文档: $PROJECT_DIR/DEPLOYMENT_GUIDE.md"
echo ""
