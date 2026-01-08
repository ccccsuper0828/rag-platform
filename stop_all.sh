#!/bin/bash

# RAG Platform 停止脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 停止 RAG Platform 服务${NC}"
echo "=================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 停止 Runner
if [ -f ".runner.pid" ]; then
    RUNNER_PID=$(cat .runner.pid)
    if ps -p $RUNNER_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}停止 Runner (PID: $RUNNER_PID)...${NC}"
        kill $RUNNER_PID
        echo -e "${GREEN}✅ Runner 已停止${NC}"
    else
        echo -e "${YELLOW}Runner 进程不存在${NC}"
    fi
    rm -f .runner.pid
else
    echo -e "${YELLOW}未找到 Runner PID 文件${NC}"
    # 尝试查找并停止
    if pgrep -f "uvicorn app:app" > /dev/null; then
        echo -e "${YELLOW}发现 Runner 进程，正在停止...${NC}"
        pkill -f "uvicorn app:app"
        echo -e "${GREEN}✅ Runner 已停止${NC}"
    fi
fi

# 停止 Docker 服务
echo -e "${YELLOW}停止 Docker 服务...${NC}"
docker-compose down

echo ""
echo -e "${GREEN}✅ 所有服务已停止${NC}"

