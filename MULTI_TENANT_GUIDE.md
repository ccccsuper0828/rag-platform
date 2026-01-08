# 多租户系统使用指南

## 📋 概述

系统已升级为**多租户架构**，每个用户拥有：
- ✅ 独立的用户账户（注册/登录）
- ✅ 独立的 RAG 工作空间
- ✅ 独立的 Claude Skills 配置
- ✅ 完全隔离的知识文档（不会交叉）

## 🏗️ 架构设计

### 数据隔离策略

```
ai_partner_workspaces/
├── user_{user_id_1}/          # 用户1的独立空间
│   ├── rag_xxx/
│   │   ├── notes/              # 用户1的文档
│   │   ├── config/             # 用户1的画像配置
│   │   └── knowledge_graph/    # 用户1的知识图谱
│   └── rag_yyy/
├── user_{user_id_2}/          # 用户2的独立空间
│   └── rag_zzz/
└── ...
```

### 认证流程

1. **用户注册** → 生成 JWT Token
2. **用户登录** → 获取 JWT Token
3. **API 调用** → 携带 Token 在 Header 中
4. **后端验证** → 提取 user_id，路由到对应的 workspace

## 🚀 API 使用示例

### 1. 用户注册

```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "secure_password_123"
  }'
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "a1b2c3d4e5f6g7h8",
  "username": "alice"
}
```

### 2. 用户登录

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "secure_password_123"
  }'
```

### 3. 获取当前用户信息

```bash
curl -X GET http://localhost:8000/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. 上传文件并创建 RAG（需要认证）

```bash
curl -X POST http://localhost:8000/v1/rag/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@document.pdf"
```

**响应：**
```json
{
  "rag_id": "rag_a1b2c3d4e5f6g7h8_abc12345",
  "arch": "aipartner",
  "message": "AI Partner 构建成功",
  "extracted_text_preview": "...",
  "metrics_file": "..."
}
```

### 5. 对话（需要认证）

```bash
curl -X POST http://localhost:8000/v1/chat/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_id": "rag_a1b2c3d4e5f6g7h8_abc12345",
    "question": "这篇文档的主要内容是什么？"
  }'
```

### 6. 获取用户的 RAG 列表

```bash
curl -X GET http://localhost:8000/v1/rag/list \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**响应：**
```json
{
  "rags": [
    {
      "rag_id": "rag_a1b2c3d4e5f6g7h8_abc12345",
      "arch": "aipartner",
      "file_path": "uploads/user_a1b2c3d4e5f6g7h8/document.pdf"
    }
  ]
}
```

## 🔒 安全特性

### 1. 密码加密
- 使用 `bcrypt` 加密存储密码
- 密码永远不会以明文形式存储或传输

### 2. JWT Token
- Token 有效期：7天
- 使用 HS256 算法签名
- 包含用户ID和用户名

### 3. 数据隔离
- 每个用户的 workspace 完全独立
- 用户无法访问其他用户的数据
- 所有 API 调用都会验证用户身份

### 4. 权限检查
- 所有 RAG 相关操作都需要认证
- 系统自动验证用户是否有权限访问指定的 RAG

## 📁 文件存储结构

### 用户上传文件
```
uploads/
├── user_{user_id_1}/
│   ├── document1.pdf
│   └── document2.txt
├── user_{user_id_2}/
│   └── document3.pdf
└── ...
```

### 用户工作空间
```
ai_partner_workspaces/
├── user_{user_id_1}/
│   ├── rag_xxx/
│   │   ├── notes/
│   │   │   └── document1.md
│   │   ├── config/
│   │   │   ├── user-persona.md
│   │   │   └── ai-persona.md
│   │   └── knowledge_graph/
│   │       └── graph.json
│   └── rag_yyy/
└── user_{user_id_2}/
    └── rag_zzz/
```

## 🔧 配置说明

### Backend 环境变量

```bash
# JWT 密钥（生产环境请使用强随机密钥）
JWT_SECRET_KEY=your-secret-key-here

# Workspace 基础目录
AI_PARTNER_WORKSPACES_DIR=/path/to/ai_partner_workspaces
```

### Runner 环境变量

无需额外配置，Runner 会自动根据 `user_id` 创建隔离的 workspace。

## 🧪 测试多租户隔离

### 测试步骤

1. **创建两个用户**
```bash
# 用户1
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "email": "user1@test.com", "password": "pass1"}'

# 用户2
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user2", "email": "user2@test.com", "password": "pass2"}'
```

2. **用户1上传文档**
```bash
curl -X POST http://localhost:8000/v1/rag/ \
  -H "Authorization: Bearer USER1_TOKEN" \
  -F "file=@user1_doc.pdf"
```

3. **用户2上传文档**
```bash
curl -X POST http://localhost:8000/v1/rag/ \
  -H "Authorization: Bearer USER2_TOKEN" \
  -F "file=@user2_doc.pdf"
```

4. **验证隔离**
```bash
# 用户1只能看到自己的RAG
curl -X GET http://localhost:8000/v1/rag/list \
  -H "Authorization: Bearer USER1_TOKEN"

# 用户2尝试访问用户1的RAG（应该失败）
curl -X POST http://localhost:8000/v1/chat/ \
  -H "Authorization: Bearer USER2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "USER1_RAG_ID", "question": "test"}'
# 应该返回 404 错误
```

## 🐛 常见问题

### Q1: 如何重置用户密码？

目前需要手动修改 `data/users.json` 文件，或通过管理员接口（待实现）。

### Q2: Token 过期怎么办？

重新调用 `/v1/auth/login` 获取新的 Token。

### Q3: 如何删除用户数据？

删除对应的 workspace 目录：
```bash
rm -rf ai_partner_workspaces/user_{user_id}/
rm -rf uploads/user_{user_id}/
```

### Q4: 用户数据备份？

备份整个 `ai_partner_workspaces/` 和 `uploads/` 目录即可。

## 📊 数据库结构

### 用户数据（JSON 文件）

位置：`backend/data/users.json`

格式：
```json
{
  "user_id_1": {
    "id": "user_id_1",
    "username": "alice",
    "email": "alice@example.com",
    "password_hash": "$2b$12$...",
    "created_at": "2025-01-20T10:00:00",
    "is_active": true
  },
  "user_id_2": {
    ...
  }
}
```

**注意：** 生产环境建议使用 PostgreSQL 或 MySQL 替代 JSON 文件。

## 🚀 生产环境建议

1. **使用真实数据库**
   - 替换 JSON 文件存储为 PostgreSQL/MySQL
   - 添加数据库连接池

2. **增强安全性**
   - 使用更强的 JWT Secret Key
   - 添加 Token 刷新机制
   - 实现密码重置功能
   - 添加登录失败次数限制

3. **性能优化**
   - 使用 Redis 缓存用户信息
   - 实现 Token 黑名单机制
   - 添加 API 限流

4. **监控和日志**
   - 记录所有用户操作
   - 监控异常访问尝试
   - 添加审计日志

## ✅ 功能清单

- [x] 用户注册
- [x] 用户登录
- [x] JWT Token 认证
- [x] 多租户 workspace 隔离
- [x] RAG 数据隔离
- [x] 文件上传隔离
- [x] 知识图谱隔离
- [ ] 密码重置（待实现）
- [ ] 用户管理界面（待实现）
- [ ] 数据库迁移（待实现）

