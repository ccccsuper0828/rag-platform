#!/bin/bash

# AI Partner Runner 独立启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 AI Partner Runner 独立启动${NC}"
echo "=================="
echo ""

# 检查当前目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python: $(python3 --version)${NC}"

# 检查 Claude Code
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}⚠️  Claude Code 未找到，请检查 PATH 或 .env 中的 CLAUDE_BIN${NC}"
else
    echo -e "${GREEN}✅ Claude Code: $(claude --version)${NC}"
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 创建虚拟环境...${NC}"
    python3 -m venv .venv
fi

# 激活虚拟环境
echo -e "${YELLOW}🔧 激活虚拟环境...${NC}"
source .venv/bin/activate

# 安装/更新依赖
echo -e "${YELLOW}📥 检查依赖...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 创建 .env 文件...${NC}"
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${YELLOW}⚠️  请编辑 .env 文件，至少设置 ANTHROPIC_AUTH_TOKEN${NC}"
    else
        echo -e "${RED}❌ env.example 不存在${NC}"
        exit 1
    fi
fi

# 检查必要的环境变量
if ! grep -q "ANTHROPIC_AUTH_TOKEN" .env || grep -q "替换为你的" .env; then
    echo -e "${YELLOW}⚠️  请确保 .env 中设置了有效的 ANTHROPIC_AUTH_TOKEN${NC}"
fi

# 获取端口（从环境变量或默认）
PORT=${PORT:-9001}
HOST=${HOST:-0.0.0.0}

echo ""
echo -e "${GREEN}✅ 环境检查完成${NC}"
echo ""
echo -e "${YELLOW}启动服务...${NC}"
echo -e "  - 地址: http://${HOST}:${PORT}"
echo -e "  - 健康检查: http://localhost:${PORT}/health"
echo -e "  - 按 Ctrl+C 停止"
echo ""

# 启动服务
uvicorn app:app --host "$HOST" --port "$PORT" --reload

