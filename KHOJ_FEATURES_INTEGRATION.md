# RAG Studio 2.0 - Khoj 风格升级

本次升级借鉴了 Khoj 项目的优秀设计，为 MVP 带来了四大核心功能和全新的时尚界面。

## 🎨 全新时尚界面

借鉴 Khoj 的设计语言，我们重新设计了整个前端界面：

### 设计特点
- **橙色主题**：采用温暖的橙色作为主色调，搭配渐变效果
- **深色模式**：一键切换深色/浅色主题
- **侧边栏导航**：可折叠的侧边栏，包含 Home、Chat、Research、Memory 四个主要视图
- **卡片式布局**：功能卡片采用悬浮效果和渐变背景
- **流畅动画**：fadeInUp、typing indicator 等微交互动画
- **响应式设计**：完美适配桌面和移动端

### 界面预览
```
┌──────────────────────────────────────────────────────┐
│ 🧠 RAG Studio                      [Dark Mode Toggle]│
├──────────┬───────────────────────────────────────────┤
│ 🏠 Home  │                                           │
│ 💬 Chat  │   Transform Your Documents               │
│ 🔬 Research│   Into Intelligent Knowledge            │
│ 🧠 Memory │                                           │
│          │   ┌─────────────────────────────────┐     │
│          │   │  📄 Drop your file here         │     │
│          │   │     or browse                   │     │
│          │   └─────────────────────────────────┘     │
│          │                                           │
│          │   ┌────┐ ┌────┐ ┌────┐ ┌────┐            │
│          │   │🔍  │ │🔬  │ │🧠  │ │⚡  │            │
│          │   │Sem │ │Res │ │Mem │ │CE  │            │
│          │   └────┘ └────┘ └────┘ └────┘            │
│──────────┴───────────────────────────────────────────│
│ 👤 User                                              │
└──────────────────────────────────────────────────────┘
```

## 🔬 Research 深度研究模式

借鉴 Khoj 的 Research 模式，提供多步骤、多工具并行调用的深度研究能力。

### 核心特性
1. **查询分解**：将复杂问题拆分为子问题
2. **并行搜索**：同时搜索多个数据源（文档、网络）
3. **结果综合**：智能合并多个来源的信息
4. **迭代深化**：根据中间结果调整搜索策略

### API 使用
```http
POST /v1/research/
Content-Type: application/json
Authorization: Bearer <token>

{
  "rag_id": "rag_xxx",
  "query": "分析当前RAG技术的发展趋势和挑战",
  "options": {
    "searchDocs": true,
    "searchWeb": true,
    "runCode": false
  }
}
```

### 响应示例
```json
{
  "query": "分析当前RAG技术的发展趋势和挑战",
  "answer": "📚 **文档信息：**\n1. RAG技术正在向多模态方向发展...\n\n🌐 **网络信息：**\n1. 最新研究显示...",
  "steps": [
    {"id": "step_1", "title": "分析查询", "status": "completed", "result": "识别出 3 个子问题"},
    {"id": "step_2", "title": "搜索文档", "status": "completed", "result": "找到 5 条相关文档"},
    {"id": "step_3", "title": "网络搜索", "status": "completed", "result": "获取 3 条网络结果"},
    {"id": "step_4", "title": "综合分析", "status": "completed", "result": "研究报告生成完成"}
  ],
  "sources_count": 8,
  "total_duration_ms": 3245.67
}
```

## ⚡ Cross-Encoder 重排序

借鉴 Khoj 的 Cross-Encoder 实现，提供两阶段检索以显著提升搜索精度。

### 工作原理
```
查询 → [Bi-Encoder快速召回] → 候选集 → [Cross-Encoder精排] → 最终结果
         (LEANN: ~100个)              (Top-k: 5-10个)
```

### 精度提升
- 通常提升 5-15% 的搜索精度
- 更好地理解 query-document 语义关系
- 适合需要高精度的场景

### 配置
```bash
# 环境变量
ENABLE_CROSS_ENCODER=true
CROSS_ENCODER_MODEL=BAAI/bge-reranker-base
RERANK_TOP_K=5
```

### 代码示例
```python
from core.cross_encoder import rerank_with_cross_encoder

# 假设 documents 是 LEANN 返回的候选集
reranked = rerank_with_cross_encoder(
    query="如何优化RAG系统的性能？",
    documents=documents,
    top_k=5,
    score_threshold=0.3
)

# reranked 现在包含 cross_encoder_score 字段
for doc in reranked:
    print(f"Score: {doc['cross_encoder_score']:.3f} - {doc['content'][:50]}")
```

## 🧠 Memory 记忆系统

借鉴 Khoj 的记忆系统，提供跨对话的长期记忆能力。

### 核心特性
1. **自动记忆提取**：从对话中自动提取重要信息
2. **语义记忆检索**：根据当前对话上下文检索相关记忆
3. **记忆衰减**：旧记忆逐渐降低权重
4. **用户画像更新**：根据记忆动态更新用户画像

### API 使用

#### 列出记忆
```http
GET /v1/memory/?limit=50&offset=0
Authorization: Bearer <token>
```

#### 添加记忆
```http
POST /v1/memory/
Content-Type: application/json
Authorization: Bearer <token>

{
  "text": "用户偏好使用 Python 进行开发",
  "source": "manual",
  "importance": 0.8
}
```

#### 搜索记忆
```http
POST /v1/memory/search
Content-Type: application/json
Authorization: Bearer <token>

{
  "query": "编程偏好",
  "top_k": 5
}
```

#### 删除记忆
```http
DELETE /v1/memory/{memory_id}
Authorization: Bearer <token>
```

### 自动记忆提取
对话中包含以下关键词时，系统会自动提取记忆：
- "记住"、"重要"、"关键"、"注意"
- "我喜欢"、"我不喜欢"、"我的"、"我是"
- "偏好"、"习惯"、"经常"、"总是"

## 🔧 MCP 协议支持

借鉴 Khoj 的 MCP 实现，提供标准化的外部工具调用能力。

### 什么是 MCP？
Model Context Protocol (MCP) 是一个标准化的协议，用于让 AI 模型与外部工具进行交互。

### 内置工具
| 工具名称 | 类型 | 描述 |
|---------|------|------|
| `read_file` | filesystem | 读取文件内容 |
| `web_search` | browser | 网络搜索 |
| `calculator` | custom | 数学计算 |
| `datetime` | custom | 日期时间操作 |

### API 使用

#### 列出可用工具
```http
GET /v1/mcp/tools
Authorization: Bearer <token>
```

#### 调用工具
```http
POST /v1/mcp/call
Content-Type: application/json
Authorization: Bearer <token>

{
  "tool_name": "calculator",
  "params": {
    "expression": "sqrt(16) + pow(2, 3)"
  }
}
```

### 自定义工具
```python
from core.mcp_protocol import MCPTool, MCPToolDefinition, MCPToolParameter, register_custom_tool

class MyCustomTool(MCPTool):
    @property
    def definition(self) -> MCPToolDefinition:
        return MCPToolDefinition(
            name="my_tool",
            description="我的自定义工具",
            tool_type=MCPToolType.CUSTOM,
            parameters=[
                MCPToolParameter(
                    name="input",
                    type="string",
                    description="输入参数",
                ),
            ],
        )
    
    async def execute(self, input: str, **kwargs) -> MCPToolResult:
        # 工具逻辑
        return MCPToolResult(success=True, output=f"处理结果: {input}")

# 注册工具
register_custom_tool(MyCustomTool())
```

## 📦 新增文件结构

```
backend/core/
├── cross_encoder.py      # Cross-Encoder 重排序模块
├── research_mode.py      # Research 深度研究模式
├── memory_system.py      # Memory 记忆系统
└── mcp_protocol.py       # MCP 协议支持

frontend/src/
└── App.vue               # 全新时尚界面

rag_storage/
└── memory/               # 记忆数据库存储目录
    └── user_{id}.db      # 每个用户的记忆 SQLite 数据库
```

## 🚀 快速开始

### 1. 更新依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）
```bash
# Cross-Encoder
export ENABLE_CROSS_ENCODER=true
export CROSS_ENCODER_MODEL=BAAI/bge-reranker-base

# Memory
export MAX_MEMORIES_PER_USER=1000
export MEMORY_DECAY_DAYS=30
export AUTO_EXTRACT_MEMORIES=true

# LEANN
export ENABLE_LEANN=true
export LEANN_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

### 3. 启动服务
```bash
# 后端
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 前端
cd frontend && npm run dev

# AI Partner Runner
cd ai_partner_runner && python app.py
```

## 🎯 功能对比

| 功能 | MVP 1.0 | MVP 2.0 (Khoj 风格) |
|------|---------|---------------------|
| 搜索 | 关键词 | 语义 + Cross-Encoder |
| 界面 | 基础 | 时尚 Khoj 风格 |
| 研究 | ❌ | ✅ Research 模式 |
| 记忆 | ❌ | ✅ 长期记忆系统 |
| 工具 | ❌ | ✅ MCP 协议 |
| 主题 | 浅色 | 浅色 + 深色 |

## 📚 参考资料

- [Khoj Project](https://github.com/khoj-ai/khoj)
- [LEANN - Low-Storage Vector Database](../LEANN/README.md)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Cross-Encoder for Reranking](https://www.sbert.net/examples/applications/cross-encoder/README.html)

