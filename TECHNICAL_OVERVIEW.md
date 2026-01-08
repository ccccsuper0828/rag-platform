# RAG 平台技术概览

## 🎯 快速概览

这是一个**多租户 RAG 平台**，使用 **ripgrep** 进行高性能检索，集成 **LangExtract** 智能过滤，支持 **知识图谱可视化** 和 **本地沙盒存储**。

---

## 🏗️ 架构简图

```
Frontend (Vue.js) :8080
    ↓
Backend Gateway (FastAPI) :8000
    ├─ 认证/授权 (JWT)
    ├─ 文件上传/解析
    └─ 多租户路由
    ↓
AI Partner Runner (FastAPI) :9001
    ├─ RAG 引擎 (Ripgrep)
    ├─ 元数据提取/过滤
    ├─ 知识图谱构建
    └─ Claude Code 集成
    ↓
本地沙盒存储 (~/.rag-platform-sandboxes/)
    ├─ 用户数据
    ├─ RAG 数据
    └─ 会话历史
```

---

## 🔧 核心技术

### 1. RAG 检索

**技术**：Ripgrep + 元数据过滤

**流程**：
```
查询 → 提取过滤器 → 元数据过滤 → ripgrep 搜索 → 返回结果
```

**优势**：
- ⚡ 高性能（< 100ms）
- 🎯 精确过滤（版本/服务感知）
- 📊 元数据增强

### 2. 元数据提取

**技术**：正则表达式 + 模式匹配

**提取字段**：
- 版本（version）
- 服务（service）
- 文档类型（doc_type）
- 标签（tags）
- 速率限制（rate_limits）

**存储**：`metadata.json`

### 3. 知识图谱

**技术**：实体提取 + 关系映射

**实体类型**：
- Person（人物）
- Organization（组织）
- Technology（技术）
- Concept（概念）

**存储**：`knowledge_graph/graph.json`

### 4. 多租户隔离

**技术**：JWT + 目录隔离

**隔离策略**：
```
workspace/user_{user_id}/rag_{rag_id}/
```

**安全**：
- ✅ 密码加密（bcrypt）
- ✅ JWT Token
- ✅ 权限检查

### 5. 本地沙盒

**技术**：目录沙盒 + 自动恢复

**结构**：
```
~/.rag-platform-sandboxes/user_{user_id}/
├── data/          # 用户数据
├── config/        # 配置
└── workspace/     # Claude Code workspace
```

**功能**：
- ✅ 数据本地化
- ✅ 自动恢复
- ✅ 备份/迁移

---

## 📊 数据流

### 文件上传

```
用户上传 → Backend → 文本提取 → Runner → 元数据提取 → 保存到沙盒
```

### 查询流程

```
用户查询 → Backend → Runner → 提取过滤器 → 元数据过滤 → ripgrep 搜索 → Claude Code → 返回
```

### 会话恢复

```
启动 → 扫描沙盒 → 恢复会话 → 加载 RAG → 就绪
```

---

## 🚀 快速开始

### 1. 启动 Runner

```bash
cd ai_partner_runner
./start_standalone.sh
```

### 2. 启动 Backend

```bash
cd backend
docker-compose up backend
```

### 3. 启动 Frontend

```bash
cd frontend
docker-compose up frontend
```

### 4. 访问

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- Runner API: http://localhost:9001

---

## 📁 关键文件

### Backend
- `backend/main.py` - FastAPI 应用
- `backend/core/auth.py` - 认证模块
- `backend/core/architectures.py` - 架构路由

### Runner
- `ai_partner_runner/app.py` - Runner 主应用
- `ai_partner_runner/metadata_extractor.py` - 元数据提取
- `ai_partner_runner/query_filter.py` - 查询过滤
- `ai_partner_runner/knowledge_graph.py` - 知识图谱

### 配置
- `docker-compose.yml` - Docker 编排
- `.env` - 环境变量

---

## 🔑 环境变量

### Backend
```bash
JWT_SECRET_KEY=your-secret-key
AI_PARTNER_RUNNER_URL=http://host.docker.internal:9001
```

### Runner
```bash
CLAUDE_BIN=/path/to/claude
ANTHROPIC_AUTH_TOKEN=your-token
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

---

## 📈 性能指标

| 操作 | 性能 |
|------|------|
| Ripgrep 搜索 | < 100ms (1000 文件) |
| 元数据过滤 | < 10ms |
| 文件上传 | < 5s (10MB PDF) |
| RAG 构建 | < 30s (100 页) |
| 查询响应 | < 3s (含 LLM) |

---

## 🔒 安全特性

- ✅ JWT Token 认证
- ✅ 密码加密（bcrypt）
- ✅ 数据完全隔离
- ✅ 权限检查
- ✅ 访问日志

---

## 📚 相关文档

- [完整架构文档](./COMPLETE_ARCHITECTURE.md)
- [多租户指南](./MULTI_TENANT_GUIDE.md)
- [LangExtract 集成](./LANGEXTRACT_INTEGRATION.md)
- [本地沙盒方案](./LOCAL_SANDBOX_SOLUTION.md)

---

## 🎯 技术栈

- **后端**：FastAPI, Python 3.9+
- **前端**：Vue.js 3, Vite
- **检索**：Ripgrep
- **AI**：Claude Code CLI
- **存储**：文件系统 + JSON
- **部署**：Docker, Docker Compose

---

## ✅ 核心功能

- [x] Ripgrep 高性能检索
- [x] 元数据智能过滤
- [x] 知识图谱可视化
- [x] Claude Code 集成
- [x] 多租户隔离
- [x] 本地沙盒存储
- [ ] 沙盒管理器（待实现）
- [ ] 数据加密（待实现）

---

**最后更新**：2025-01-20

