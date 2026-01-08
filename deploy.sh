#!/bin/bash
# ============================================
# RAG Platform 生产部署脚本
# ============================================

set -e

echo "🚀 RAG Platform 生产部署"
echo "========================="
echo ""

# 检查 .env.production 文件
if [ ! -f ".env.production" ]; then
    echo "❌ 错误: .env.production 文件不存在"
    echo "   请复制 .env.example 为 .env.production 并配置"
    echo ""
    echo "   cp .env.example .env.production"
    echo "   nano .env.production"
    exit 1
fi

# 加载环境变量
set -a
source .env.production
set +a

# 检查必要的环境变量
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ 错误: ANTHROPIC_API_KEY 未设置"
    exit 1
fi

if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "your-very-long-random-string-for-jwt-signing" ]; then
    echo "❌ 错误: JWT_SECRET 未设置或使用默认值"
    echo "   请运行: openssl rand -hex 32"
    exit 1
fi

echo "✅ 环境变量检查通过"
echo ""

# 停止旧容器
echo "📋 停止旧容器..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
echo ""

# 构建镜像
echo "📋 构建 Docker 镜像..."
docker compose -f docker-compose.prod.yml build --no-cache
echo ""

# 启动服务
echo "📋 启动服务..."
docker compose -f docker-compose.prod.yml up -d
echo ""

# 等待服务就绪
echo "📋 等待服务启动..."
sleep 10

# 检查服务状态
echo "📋 检查服务状态..."
echo ""

# 检查各个服务
services=("mysql" "runner" "backend" "frontend")
all_healthy=true

for service in "${services[@]}"; do
    status=$(docker compose -f docker-compose.prod.yml ps --format json | grep "$service" | head -1 || echo "")
    if echo "$status" | grep -q "running"; then
        echo "   ✅ $service: 运行中"
    else
        echo "   ❌ $service: 异常"
        all_healthy=false
    fi
done

echo ""

if [ "$all_healthy" = true ]; then
    echo "========================="
    echo "✅ 部署成功！"
    echo "========================="
    echo ""
    echo "📍 访问地址:"
    echo "   http://localhost (或你的域名)"
    echo ""
    echo "📋 查看日志:"
    echo "   docker compose -f docker-compose.prod.yml logs -f"
    echo ""
    echo "🛑 停止服务:"
    echo "   docker compose -f docker-compose.prod.yml down"
else
    echo "========================="
    echo "⚠️  部分服务异常"
    echo "========================="
    echo ""
    echo "查看日志排查问题:"
    echo "   docker compose -f docker-compose.prod.yml logs"
fi

