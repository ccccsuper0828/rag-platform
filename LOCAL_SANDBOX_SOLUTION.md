# 本地沙盒/虚拟机技术解决方案

## 🎯 目标

实现类似 Manus 的功能，将用户上传的文件、RAG 数据和 Claude Code 会话保存在用户本地的沙盒/虚拟机中，启动应用时自动读取资料和历史。

## 🏗️ 架构设计

### 核心概念

**用户沙盒（User Sandbox）**：
- 每个用户拥有独立的、完全隔离的本地环境
- 包含所有用户数据、配置、会话历史
- 可以打包、备份、迁移
- 启动时自动挂载和恢复

### 架构层次

```
┌─────────────────────────────────────────────────┐
│           Application Layer (Backend/Runner)      │
├─────────────────────────────────────────────────┤
│         Sandbox Manager (Orchestration)         │
├─────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌────────┐│
│  │ User Sandbox │  │ User Sandbox │  │  ...   ││
│  │   (User 1)   │  │   (User 2)  │  │        ││
│  └──────────────┘  └──────────────┘  └────────┘│
├─────────────────────────────────────────────────┤
│         Storage Layer (Local Filesystem)         │
└─────────────────────────────────────────────────┘
```

---

## 📦 方案 1：基于目录的沙盒（推荐，轻量级）

### 设计思路

使用**目录隔离 + 符号链接 + 配置文件**实现沙盒效果，无需真正的虚拟机。

### 沙盒结构

```
~/.rag-platform-sandboxes/
├── user_{user_id}/
│   ├── .sandbox-config.json          # 沙盒配置和元数据
│   ├── .sandbox-state.json           # 沙盒状态（运行中/已停止）
│   ├── data/                          # 用户数据目录
│   │   ├── uploads/                  # 用户上传的文件
│   │   │   ├── file1.pdf
│   │   │   └── file2.md
│   │   ├── notes/                     # 处理后的笔记
│   │   │   └── *.md
│   │   ├── rag/                       # RAG 数据
│   │   │   ├── metadata.json         # 元数据索引
│   │   │   ├── knowledge_graph/      # 知识图谱
│   │   │   └── search_index/          # 搜索索引（ripgrep 数据）
│   │   └── sessions/                  # Claude Code 会话
│   │       ├── session_001.json       # 会话历史
│   │       ├── session_002.json
│   │       └── current_session.json
│   ├── config/                        # 配置文件
│   │   ├── user-persona.md
│   │   ├── ai-persona.md
│   │   ├── claude-session-id.txt
│   │   └── app-config.json
│   ├── workspace/                      # Claude Code workspace
│   │   ├── .claude/
│   │   │   └── skills/
│   │   └── scripts/
│   ├── venv/                           # Python 虚拟环境（可选）
│   └── logs/                          # 日志文件
│       ├── app.log
│       └── claude-code.log
```

### 沙盒配置文件

**`.sandbox-config.json`**：
```json
{
  "sandbox_id": "user_abc123",
  "user_id": "abc123",
  "created_at": "2025-01-20T10:00:00Z",
  "last_accessed": "2025-01-20T15:30:00Z",
  "status": "active",
  "version": "1.0",
  "data_paths": {
    "uploads": "data/uploads",
    "notes": "data/notes",
    "rag": "data/rag",
    "sessions": "data/sessions",
    "config": "config",
    "workspace": "workspace"
  },
  "claude_code": {
    "session_id": "session_xyz789",
    "session_history_path": "data/sessions/current_session.json",
    "workspace_path": "workspace"
  },
  "rag": {
    "metadata_file": "data/rag/metadata.json",
    "knowledge_graph_file": "data/rag/knowledge_graph/graph.json",
    "search_index_enabled": true
  },
  "auto_restore": {
    "enabled": true,
    "restore_sessions": true,
    "restore_rag": true,
    "restore_config": true
  }
}
```

**`.sandbox-state.json`**：
```json
{
  "status": "running",
  "started_at": "2025-01-20T15:30:00Z",
  "process_id": 12345,
  "ports": {
    "runner": 9001,
    "backend": 8000
  },
  "last_backup": "2025-01-20T14:00:00Z"
}
```

### 实现要点

1. **沙盒管理器（SandboxManager）**
   - 创建、启动、停止、删除沙盒
   - 自动恢复沙盒状态
   - 管理沙盒生命周期

2. **数据隔离**
   - 每个用户独立的目录
   - 严格的权限控制
   - 符号链接隔离（可选）

3. **自动恢复**
   - 启动时读取 `.sandbox-state.json`
   - 恢复 Claude Code 会话
   - 加载 RAG 数据和元数据
   - 恢复配置文件

---

## 📦 方案 2：基于 Docker 容器的沙盒（隔离性更强）

### 设计思路

为每个用户创建独立的 Docker 容器，实现更强的隔离。

### 容器结构

```yaml
# docker-compose.sandbox.yml (per user)
version: '3.8'

services:
  user_sandbox_abc123:
    image: rag-platform-sandbox:latest
    container_name: sandbox_user_abc123
    volumes:
      - ./sandboxes/user_abc123/data:/app/data:rw
      - ./sandboxes/user_abc123/config:/app/config:ro
      - ./sandboxes/user_abc123/workspace:/app/workspace:rw
    environment:
      - USER_ID=abc123
      - SANDBOX_ID=user_abc123
      - AUTO_RESTORE=true
    ports:
      - "9001:9001"  # Runner port (per user)
    restart: unless-stopped
    networks:
      - sandbox_network
```

### 数据卷映射

```
Host: ~/.rag-platform-sandboxes/user_abc123/
  ├── data/          → Container: /app/data
  ├── config/        → Container: /app/config
  └── workspace/     → Container: /app/workspace
```

### 优势

- ✅ 完全隔离（进程、网络、文件系统）
- ✅ 易于备份（整个容器或数据卷）
- ✅ 可移植（容器镜像 + 数据卷）
- ✅ 资源限制（CPU、内存）

### 劣势

- ❌ 需要 Docker 环境
- ❌ 资源消耗较大
- ❌ 启动时间稍长

---

## 📦 方案 3：基于系统级沙盒（macOS/Windows）

### macOS：使用 App Sandbox

利用 macOS 的 App Sandbox 机制：

```xml
<!-- Entitlements.plist -->
<key>com.apple.security.app-sandbox</key>
<true/>
<key>com.apple.security.files.user-selected.read-write</key>
<true/>
<key>com.apple.security.files.downloads.read-write</key>
<true/>
```

### Windows：使用 AppContainer

利用 Windows 的 AppContainer 隔离机制。

---

## 🚀 推荐方案：混合方案（目录沙盒 + 可选容器）

### 架构设计

```
┌─────────────────────────────────────────────┐
│         Sandbox Manager Service              │
│  - 管理所有用户沙盒                           │
│  - 启动/停止/恢复沙盒                         │
│  - 监控沙盒状态                               │
└─────────────────────────────────────────────┘
           │
           ├─── 模式 A：目录沙盒（默认，轻量）
           │    ~/.rag-platform-sandboxes/user_xxx/
           │
           └─── 模式 B：Docker 容器（可选，强隔离）
                docker run sandbox_user_xxx
```

### 沙盒管理器设计

**SandboxManager 类**：

```python
class SandboxManager:
    """
    管理用户沙盒的创建、启动、恢复、停止
    """
    
    def __init__(self, base_path: Path, mode: str = "directory"):
        """
        Args:
            base_path: 沙盒基础目录
            mode: "directory" 或 "docker"
        """
        self.base_path = base_path
        self.mode = mode
        self.sandboxes: Dict[str, UserSandbox] = {}
    
    def create_sandbox(self, user_id: str) -> UserSandbox:
        """创建新沙盒"""
        pass
    
    def start_sandbox(self, user_id: str) -> bool:
        """启动沙盒并自动恢复"""
        pass
    
    def stop_sandbox(self, user_id: str) -> bool:
        """停止沙盒并保存状态"""
        pass
    
    def restore_sandbox(self, user_id: str) -> bool:
        """恢复沙盒状态"""
        pass
    
    def backup_sandbox(self, user_id: str, backup_path: Path) -> bool:
        """备份沙盒"""
        pass
    
    def list_sandboxes(self) -> List[str]:
        """列出所有沙盒"""
        pass
```

**UserSandbox 类**：

```python
class UserSandbox:
    """
    单个用户沙盒实例
    """
    
    def __init__(self, sandbox_path: Path):
        self.path = sandbox_path
        self.config = self._load_config()
        self.state = self._load_state()
    
    def restore(self):
        """恢复沙盒状态"""
        # 1. 恢复 Claude Code 会话
        # 2. 加载 RAG 数据
        # 3. 恢复配置文件
        # 4. 启动相关服务
        pass
    
    def save_state(self):
        """保存当前状态"""
        pass
    
    def get_data_path(self, data_type: str) -> Path:
        """获取数据路径"""
        pass
```

---

## 📋 数据持久化方案

### 1. 用户上传文件

**存储位置**：
```
~/.rag-platform-sandboxes/user_{user_id}/data/uploads/
```

**元数据索引**：
```json
{
  "files": [
    {
      "id": "file_001",
      "original_name": "document.pdf",
      "stored_path": "data/uploads/file_001.pdf",
      "uploaded_at": "2025-01-20T10:00:00Z",
      "size": 1024000,
      "mime_type": "application/pdf",
      "extracted_text_path": "data/notes/file_001.md",
      "metadata": {
        "service": "Authentication API",
        "version": "2.0",
        "doc_type": "reference"
      }
    }
  ]
}
```

### 2. RAG 数据

**存储位置**：
```
~/.rag-platform-sandboxes/user_{user_id}/data/rag/
├── metadata.json              # 文档元数据索引
├── knowledge_graph/
│   └── graph.json            # 知识图谱数据
└── search_index/             # 搜索索引（ripgrep 数据）
    └── index.json
```

### 3. Claude Code 会话

**存储位置**：
```
~/.rag-platform-sandboxes/user_{user_id}/data/sessions/
├── current_session.json       # 当前会话
├── session_history.jsonl      # 会话历史（JSONL 格式）
└── session_metadata.json      # 会话元数据
```

**会话格式**：
```json
{
  "session_id": "session_xyz789",
  "created_at": "2025-01-20T10:00:00Z",
  "last_updated": "2025-01-20T15:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "How do I authenticate?",
      "timestamp": "2025-01-20T10:05:00Z"
    },
    {
      "role": "assistant",
      "content": "To authenticate...",
      "timestamp": "2025-01-20T10:05:05Z"
    }
  ],
  "context": {
    "rag_id": "rag_001",
    "relevant_notes": ["note1.md", "note2.md"]
  }
}
```

### 4. 配置文件

**存储位置**：
```
~/.rag-platform-sandboxes/user_{user_id}/config/
├── user-persona.md
├── ai-persona.md
├── claude-session-id.txt
└── app-config.json
```

---

## 🔄 自动恢复机制

### 启动流程

```
应用启动
  ↓
SandboxManager 初始化
  ↓
扫描所有沙盒目录
  ↓
对每个活跃用户：
  ├─ 读取 .sandbox-config.json
  ├─ 读取 .sandbox-state.json
  ├─ 恢复 Claude Code 会话
  │   └─ 从 data/sessions/ 加载会话历史
  ├─ 恢复 RAG 数据
  │   ├─ 加载 metadata.json
  │   ├─ 加载 knowledge_graph/graph.json
  │   └─ 重建搜索索引（如需要）
  ├─ 恢复配置文件
  │   ├─ 加载 user-persona.md
  │   └─ 加载 ai-persona.md
  └─ 启动 Runner 服务（绑定到沙盒）
  ↓
沙盒就绪，可以处理请求
```

### 恢复检查清单

**Claude Code 会话恢复**：
- [ ] 检查 `data/sessions/current_session.json` 是否存在
- [ ] 验证会话 ID 是否有效
- [ ] 恢复会话历史到 Claude Code
- [ ] 验证会话状态

**RAG 数据恢复**：
- [ ] 检查 `data/rag/metadata.json` 是否存在
- [ ] 验证元数据索引完整性
- [ ] 检查知识图谱数据
- [ ] 验证搜索索引（如使用）

**配置文件恢复**：
- [ ] 检查配置文件是否存在
- [ ] 验证配置文件格式
- [ ] 加载到内存

**文件数据恢复**：
- [ ] 检查 `data/uploads/` 目录
- [ ] 验证文件完整性
- [ ] 重建文件索引

---

## 🔒 安全隔离方案

### 1. 文件系统隔离

**目录权限**：
```bash
# 每个用户沙盒目录
chmod 700 ~/.rag-platform-sandboxes/user_{user_id}/
chmod 600 ~/.rag-platform-sandboxes/user_{user_id}/.sandbox-config.json
chmod 600 ~/.rag-platform-sandboxes/user_{user_id}/.sandbox-state.json
```

**访问控制**：
- 只有沙盒管理器可以访问
- 用户只能通过 API 访问自己的沙盒
- 系统级隔离（不同用户无法访问其他用户的沙盒）

### 2. 进程隔离

**目录沙盒模式**：
- 每个用户独立的 Runner 进程
- 使用不同的工作目录
- 环境变量隔离

**Docker 模式**：
- 每个用户独立的容器
- 完全进程隔离
- 网络隔离

### 3. 数据加密（可选）

**敏感数据加密**：
- 配置文件加密存储
- 会话历史加密（可选）
- 使用用户特定的加密密钥

---

## 📦 沙盒打包和迁移

### 打包格式

```bash
# 打包沙盒
tar -czf sandbox_user_abc123.tar.gz \
  ~/.rag-platform-sandboxes/user_abc123/

# 包含内容：
# - 所有数据文件
# - 配置文件
# - 会话历史
# - 元数据索引
```

### 迁移流程

```
源机器：
  1. 停止沙盒
  2. 打包沙盒目录
  3. 导出沙盒配置

目标机器：
  1. 解压沙盒目录
  2. 导入沙盒配置
  3. 验证数据完整性
  4. 启动沙盒
```

---

## 🚀 启动时自动恢复实现

### 恢复服务（SandboxRestoreService）

```python
class SandboxRestoreService:
    """
    负责在应用启动时自动恢复所有用户沙盒
    """
    
    def restore_all_sandboxes(self):
        """恢复所有活跃用户的沙盒"""
        sandboxes = self.scan_sandboxes()
        
        for sandbox_id in sandboxes:
            try:
                sandbox = UserSandbox.load(sandbox_id)
                if sandbox.config['auto_restore']['enabled']:
                    sandbox.restore()
                    print(f"✅ Restored sandbox: {sandbox_id}")
            except Exception as e:
                print(f"❌ Failed to restore {sandbox_id}: {e}")
    
    def scan_sandboxes(self) -> List[str]:
        """扫描所有沙盒目录"""
        base_path = Path.home() / ".rag-platform-sandboxes"
        return [
            d.name for d in base_path.iterdir()
            if d.is_dir() and d.name.startswith("user_")
        ]
```

### 启动脚本集成

```python
# app.py 启动时
def startup():
    """应用启动时执行"""
    # 1. 初始化 SandboxManager
    sandbox_manager = SandboxManager(
        base_path=Path.home() / ".rag-platform-sandboxes"
    )
    
    # 2. 恢复所有沙盒
    restore_service = SandboxRestoreService(sandbox_manager)
    restore_service.restore_all_sandboxes()
    
    # 3. 启动 API 服务
    # ...
```

---

## 📊 数据存储结构（完整版）

```
~/.rag-platform-sandboxes/
├── .global-config.json              # 全局配置
├── user_abc123/
│   ├── .sandbox-config.json         # 沙盒配置
│   ├── .sandbox-state.json          # 沙盒状态
│   ├── .sandbox-lock                # 沙盒锁文件（防止并发）
│   │
│   ├── data/
│   │   ├── uploads/                 # 原始上传文件
│   │   │   ├── file_001.pdf
│   │   │   └── file_002.md
│   │   │   └── .uploads-index.json  # 文件索引
│   │   │
│   │   ├── notes/                    # 处理后的笔记
│   │   │   ├── file_001.md
│   │   │   └── file_002.md
│   │   │
│   │   ├── rag/                      # RAG 数据
│   │   │   ├── metadata.json         # 元数据索引
│   │   │   ├── knowledge_graph/
│   │   │   │   └── graph.json
│   │   │   └── search_index/
│   │   │       └── index.json
│   │   │
│   │   └── sessions/                 # Claude Code 会话
│   │       ├── current_session.json
│   │       ├── session_history.jsonl
│   │       └── session_metadata.json
│   │
│   ├── config/                       # 配置文件
│   │   ├── user-persona.md
│   │   ├── ai-persona.md
│   │   ├── claude-session-id.txt
│   │   └── app-config.json
│   │
│   ├── workspace/                    # Claude Code workspace
│   │   ├── .claude/
│   │   │   └── skills/
│   │   └── scripts/
│   │
│   ├── venv/                         # Python 环境（可选）
│   │
│   └── logs/                         # 日志
│       ├── app.log
│       └── claude-code.log
│
└── user_def456/
    └── ... (same structure)
```

---

## 🔧 技术实现要点

### 1. 沙盒管理器

**核心功能**：
- 创建/删除沙盒
- 启动/停止沙盒
- 恢复沙盒状态
- 备份/恢复沙盒
- 监控沙盒健康

### 2. 状态持久化

**保存时机**：
- 每次操作后保存状态
- 定期自动保存
- 优雅关闭时保存

**保存内容**：
- 沙盒配置
- 运行状态
- 会话信息
- 最后访问时间

### 3. 自动恢复逻辑

**恢复顺序**：
1. 加载沙盒配置
2. 验证数据完整性
3. 恢复配置文件
4. 恢复 RAG 数据
5. 恢复 Claude Code 会话
6. 启动相关服务

### 4. 并发控制

**锁机制**：
- 使用文件锁防止并发访问
- `.sandbox-lock` 文件
- 超时自动释放

---

## 🎯 实施建议

### 阶段 1：基础沙盒（推荐先实施）

1. **实现目录沙盒**
   - 创建沙盒目录结构
   - 实现 SandboxManager
   - 实现基本的数据存储

2. **实现自动恢复**
   - 启动时扫描沙盒
   - 恢复配置和数据
   - 启动 Runner

3. **测试验证**
   - 创建/删除沙盒
   - 数据持久化
   - 自动恢复

### 阶段 2：增强功能（后续）

1. **Docker 容器支持**（可选）
2. **数据加密**（可选）
3. **沙盒备份/迁移工具**
4. **监控和日志**

---

## 📝 配置文件示例

### 全局配置

**`~/.rag-platform-sandboxes/.global-config.json`**：
```json
{
  "version": "1.0",
  "sandbox_mode": "directory",
  "base_path": "~/.rag-platform-sandboxes",
  "default_auto_restore": true,
  "backup_enabled": true,
  "backup_schedule": "daily",
  "max_sandboxes": 100,
  "default_quota": {
    "storage_gb": 10,
    "files": 1000
  }
}
```

### 用户沙盒配置

**`.sandbox-config.json`**（已在上面展示）

---

## 🔍 与现有系统集成

### 修改点

1. **Runner 启动时**
   - 检查用户沙盒是否存在
   - 如果不存在，创建新沙盒
   - 如果存在，恢复沙盒状态

2. **文件上传时**
   - 保存到用户沙盒的 `data/uploads/`
   - 更新文件索引
   - 提取元数据

3. **RAG 构建时**
   - 数据保存到用户沙盒的 `data/rag/`
   - 元数据保存到 `metadata.json`
   - 知识图谱保存到 `knowledge_graph/`

4. **会话保存时**
   - 保存到用户沙盒的 `data/sessions/`
   - 更新会话元数据

---

## ✅ 优势总结

### 目录沙盒方案
- ✅ 轻量级，无需额外依赖
- ✅ 快速启动
- ✅ 易于备份和迁移
- ✅ 资源消耗低

### Docker 容器方案
- ✅ 完全隔离
- ✅ 可移植性强
- ✅ 资源限制
- ✅ 适合生产环境

---

## 🚀 快速实施路径

### 最小可行方案（MVP）

1. **创建沙盒目录结构**
2. **实现 SandboxManager 基础功能**
3. **实现自动恢复逻辑**
4. **集成到现有 Runner**

### 完整方案

按照阶段 1 → 2 逐步实施。

---

## 📚 参考

- Claude Code Sandboxing: https://docs.claude.com/zh-CN/docs/claude-code/sandboxing
- Docker 容器隔离
- macOS App Sandbox
- 多租户数据隔离最佳实践

