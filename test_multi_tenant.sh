#!/bin/bash

# 多租户系统测试脚本

BASE_URL="http://localhost:8000"

echo "🧪 多租户系统测试"
echo "=================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_register() {
    echo -e "${YELLOW}1. 测试用户注册${NC}"
    RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
            "username": "testuser_'$(date +%s)'",
            "email": "test_'$(date +%s)'@example.com",
            "password": "testpass123"
        }')
    
    if echo "$RESPONSE" | grep -q "access_token"; then
        echo -e "${GREEN}✅ 注册成功${NC}"
        TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        USER_ID=$(echo "$RESPONSE" | grep -o '"user_id":"[^"]*' | cut -d'"' -f4)
        echo "Token: ${TOKEN:0:50}..."
        echo "User ID: $USER_ID"
        echo "$TOKEN" > /tmp/test_token.txt
        echo "$USER_ID" > /tmp/test_user_id.txt
        return 0
    else
        echo -e "${RED}❌ 注册失败${NC}"
        echo "$RESPONSE"
        return 1
    fi
}

test_login() {
    echo ""
    echo -e "${YELLOW}2. 测试用户登录${NC}"
    RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "username": "testuser",
            "password": "testpass123"
        }')
    
    if echo "$RESPONSE" | grep -q "access_token"; then
        echo -e "${GREEN}✅ 登录成功${NC}"
        TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        echo "$TOKEN" > /tmp/test_token.txt
        return 0
    else
        echo -e "${RED}❌ 登录失败（可能需要先注册）${NC}"
        return 1
    fi
}

test_get_me() {
    echo ""
    echo -e "${YELLOW}3. 测试获取当前用户信息${NC}"
    if [ ! -f /tmp/test_token.txt ]; then
        echo -e "${RED}❌ 没有 token，请先注册或登录${NC}"
        return 1
    fi
    
    TOKEN=$(cat /tmp/test_token.txt)
    RESPONSE=$(curl -s -X GET "${BASE_URL}/v1/auth/me" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$RESPONSE" | grep -q "user_id"; then
        echo -e "${GREEN}✅ 获取用户信息成功${NC}"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
        return 0
    else
        echo -e "${RED}❌ 获取用户信息失败${NC}"
        echo "$RESPONSE"
        return 1
    fi
}

test_list_rags() {
    echo ""
    echo -e "${YELLOW}4. 测试获取 RAG 列表${NC}"
    if [ ! -f /tmp/test_token.txt ]; then
        echo -e "${RED}❌ 没有 token${NC}"
        return 1
    fi
    
    TOKEN=$(cat /tmp/test_token.txt)
    RESPONSE=$(curl -s -X GET "${BASE_URL}/v1/rag/list" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$RESPONSE" | grep -q "rags"; then
        echo -e "${GREEN}✅ 获取 RAG 列表成功${NC}"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
        return 0
    else
        echo -e "${YELLOW}⚠️  没有 RAG（这是正常的，如果还没有上传文件）${NC}"
        echo "$RESPONSE"
        return 0
    fi
}

# 运行测试
echo "检查服务是否运行..."
if ! curl -s "${BASE_URL}/" > /dev/null; then
    echo -e "${RED}❌ Backend 服务未运行，请先启动服务${NC}"
    echo "参考 START_GUIDE.md"
    exit 1
fi

echo -e "${GREEN}✅ Backend 服务运行中${NC}"
echo ""

# 执行测试
test_register || test_login
test_get_me
test_list_rags

echo ""
echo -e "${GREEN}测试完成！${NC}"
echo ""
echo "💡 提示："
echo "  - Token 保存在 /tmp/test_token.txt"
echo "  - User ID 保存在 /tmp/test_user_id.txt"
echo "  - 可以使用这些信息进行进一步的 API 测试"

