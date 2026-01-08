# RAG Platform MVP

## 📚 文档索引

### 🎯 核心文档

1. **[完整架构文档](./COMPLETE_ARCHITECTURE.md)** - 完整的系统架构、技术栈、API 文档
2. **[技术概览](./TECHNICAL_OVERVIEW.md)** - 快速技术概览和关键信息

### 🔧 功能文档

3. **[多租户系统指南](./MULTI_TENANT_GUIDE.md)** - 多租户系统使用指南
4. **[LangExtract 集成](./LANGEXTRACT_INTEGRATION.md)** - 元数据提取和智能过滤
5. **[本地沙盒方案](./LOCAL_SANDBOX_SOLUTION.md)** - 本地沙盒技术方案
6. **[沙盒实施指南](./SANDBOX_IMPLEMENTATION_GUIDE.md)** - 沙盒实施步骤

### 📋 其他文档

7. **[迁移总结](./MIGRATION_SUMMARY.md)** - 从 ChromaDB 迁移到 Ripgrep
8. **[实施总结](./IMPLEMENTATION_SUMMARY.md)** - 多租户系统实施总结
9. **[启动指南](./START_GUIDE.md)** - 系统启动指南

---

## 🚀 快速开始

### 1. 启动 AI Partner Runner

```bash
cd ai_partner_runner
./start_standalone.sh
```

### 2. 启动 Backend 和 Frontend

```bash
docker-compose up
```

### 3. 访问系统

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- Runner API: http://localhost:9001

---

## 🏗️ 系统架构

```
Frontend (Vue.js) :8080
    ↓
Backend Gateway (FastAPI) :8000
    ↓
AI Partner Runner (FastAPI) :9001
    ↓
本地沙盒存储 (~/.rag-platform-sandboxes/)
```

---

## ✨ 核心特性

- ✅ **Ripgrep 高性能检索**：基于文件系统的直接搜索
- ✅ **元数据智能过滤**：LangExtract 技术融合
- ✅ **知识图谱可视化**：实体和关系提取
- ✅ **Claude Code 集成**：个性化 AI 对话
- ✅ **多租户隔离**：完全独立的数据空间
- ✅ **本地沙盒**：用户数据本地化存储和自动恢复

---

## 📖 文档说明

### 完整架构文档
包含系统概述、整体架构、核心组件、RAG 架构、多租户系统、本地沙盒方案、数据流、技术栈、部署架构、API 文档等完整信息。

### 技术概览
快速查阅版本，包含核心技术和关键信息。

### 功能文档
各功能模块的详细使用指南和技术说明。

---

## 🔧 技术栈

- **后端**：FastAPI, Python 3.9+
- **前端**：Vue.js 3, Vite
- **检索**：Ripgrep
- **AI**：Claude Code CLI
- **存储**：文件系统 + JSON
- **部署**：Docker, Docker Compose

---

## 📝 更新日志

- **2025-01-20**：创建完整架构文档和技术概览
- **2025-01-20**：集成 LangExtract 技术
- **2025-01-20**：实现多租户系统
- **2025-01-20**：设计本地沙盒方案

---

## 📞 支持

如有问题，请查看相关文档或提交 Issue。

