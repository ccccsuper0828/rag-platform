#!/bin/bash
# ============================================================
# RAG Platform 部署脚本
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}       RAG Platform 生产环境部署脚本${NC}"
echo -e "${BLUE}============================================================${NC}"

# 检查 Docker
check_docker() {
    echo -e "${YELLOW}检查 Docker...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker 未安装${NC}"
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误: Docker Compose 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker 已安装${NC}"
}

# 检查配置文件
check_config() {
    echo -e "${YELLOW}检查配置文件...${NC}"
    if [ ! -f "$PROJECT_DIR/.env.prod" ]; then
        echo -e "${YELLOW}未找到 .env.prod，从模板创建...${NC}"
        cp "$PROJECT_DIR/deploy/env.prod.template" "$PROJECT_DIR/.env.prod"
        echo -e "${RED}请编辑 .env.prod 填写生产配置后重新运行此脚本${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ 配置文件存在${NC}"
}

# 构建镜像
build_images() {
    echo -e "${YELLOW}构建 Docker 镜像...${NC}"
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml build
    echo -e "${GREEN}✓ 镜像构建完成${NC}"
}

# 启动服务
start_services() {
    echo -e "${YELLOW}启动服务...${NC}"
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
    echo -e "${GREEN}✓ 服务已启动${NC}"
}

# 等待服务就绪
wait_for_services() {
    echo -e "${YELLOW}等待服务就绪...${NC}"
    
    # 等待 MySQL
    echo -n "等待 MySQL..."
    for i in {1..30}; do
        if docker exec rag_mysql mysqladmin ping -h localhost --silent 2>/dev/null; then
            echo -e " ${GREEN}OK${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # 等待 Backend
    echo -n "等待 Backend..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e " ${GREEN}OK${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    echo -e "${GREEN}✓ 所有服务已就绪${NC}"
}

# 显示状态
show_status() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${GREEN}部署完成！${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
    echo -e "服务状态:"
    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" ps
    echo ""
    echo -e "访问地址:"
    echo -e "  - 前端: ${GREEN}http://localhost${NC}"
    echo -e "  - API:  ${GREEN}http://localhost/api${NC}"
    echo -e "  - MinIO: ${GREEN}http://localhost:9001${NC}"
    echo ""
    echo -e "查看日志: ${YELLOW}docker-compose -f docker-compose.prod.yml logs -f${NC}"
}

# 主流程
main() {
    check_docker
    check_config
    build_images
    start_services
    wait_for_services
    show_status
}

# 解析参数
case "${1:-}" in
    build)
        check_docker
        build_images
        ;;
    start)
        check_docker
        check_config
        start_services
        wait_for_services
        show_status
        ;;
    stop)
        cd "$PROJECT_DIR"
        docker-compose -f docker-compose.prod.yml down
        echo -e "${GREEN}服务已停止${NC}"
        ;;
    restart)
        cd "$PROJECT_DIR"
        docker-compose -f docker-compose.prod.yml restart
        echo -e "${GREEN}服务已重启${NC}"
        ;;
    logs)
        cd "$PROJECT_DIR"
        docker-compose -f docker-compose.prod.yml logs -f ${2:-}
        ;;
    status)
        cd "$PROJECT_DIR"
        docker-compose -f docker-compose.prod.yml ps
        ;;
    *)
        main
        ;;
esac

