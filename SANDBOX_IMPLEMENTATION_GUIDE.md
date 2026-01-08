# 本地沙盒实施指南

## 🎯 实施目标

将用户数据封装在本地沙盒中，实现：
- ✅ 完全隔离的用户环境
- ✅ 自动恢复数据和会话
- ✅ 易于备份和迁移
- ✅ 启动时自动加载

## 📋 实施步骤

### 步骤 1：设计沙盒目录结构

**基础路径**：
```
~/.rag-platform-sandboxes/user_{user_id}/
```

**目录结构**：
```
user_{user_id}/
├── .sandbox-config.json      # 沙盒配置
├── .sandbox-state.json       # 运行状态
├── data/                     # 用户数据
│   ├── uploads/              # 上传文件
│   ├── notes/                # 笔记
│   ├── rag/                  # RAG 数据
│   └── sessions/             # 会话历史
├── config/                   # 配置
└── workspace/                # Claude Code workspace
```

### 步骤 2：实现沙盒管理器

**核心类**：
- `SandboxManager`：管理所有沙盒
- `UserSandbox`：单个用户沙盒
- `SandboxRestoreService`：恢复服务

### 步骤 3：修改现有代码

**Runner (`app.py`)**：
- 启动时检查/创建沙盒
- 从沙盒读取配置和数据
- 保存状态到沙盒

**Backend (`main.py`)**：
- 文件上传保存到沙盒
- 查询时从沙盒读取数据

### 步骤 4：实现自动恢复

**恢复流程**：
1. 扫描所有沙盒
2. 读取配置和状态
3. 恢复会话历史
4. 加载 RAG 数据
5. 启动服务

## 🔧 技术细节

### 沙盒配置格式

```json
{
  "sandbox_id": "user_abc123",
  "user_id": "abc123",
  "created_at": "2025-01-20T10:00:00Z",
  "data_paths": {
    "uploads": "data/uploads",
    "notes": "data/notes",
    "rag": "data/rag",
    "sessions": "data/sessions"
  },
  "auto_restore": {
    "enabled": true,
    "restore_sessions": true,
    "restore_rag": true
  }
}
```

### 状态保存格式

```json
{
  "status": "running",
  "started_at": "2025-01-20T15:30:00Z",
  "last_backup": "2025-01-20T14:00:00Z"
}
```

## 📝 实施检查清单

- [ ] 设计沙盒目录结构
- [ ] 实现 SandboxManager
- [ ] 实现 UserSandbox
- [ ] 实现自动恢复逻辑
- [ ] 修改 Runner 集成沙盒
- [ ] 修改 Backend 集成沙盒
- [ ] 测试创建/删除沙盒
- [ ] 测试数据持久化
- [ ] 测试自动恢复
- [ ] 测试备份/迁移

## 🚀 快速开始

1. **创建沙盒目录结构**
2. **实现基础 SandboxManager**
3. **集成到 Runner 启动流程**
4. **测试验证**

详细实施步骤请参考 `LOCAL_SANDBOX_SOLUTION.md`。

