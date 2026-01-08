# RAG 架构迁移总结

## 概述

已将 `family-insurance-doc` 的 ripgrep 检索架构成功集成到 `ai-partner-runner`，替换了原有的 ChromaDB 向量数据库架构，并添加了知识图谱可视化功能。

## 主要变更

### 1. AI Partner Runner (`ai_partner_runner/`)

#### 检索架构替换
- ✅ **替换 `_retrieve_notes` 函数**：使用 `ripgrepy` 直接搜索文件，替代 ChromaDB 向量检索
- ✅ **移除向量数据库依赖**：不再需要创建和维护 `vector_db/` 目录
- ✅ **简化构建流程**：移除了向量索引构建步骤，文件直接通过 ripgrep 搜索

#### 新增功能
- ✅ **知识图谱可视化**：
  - 新增 `knowledge_graph.py` 模块
  - 自动提取实体（人物、组织、地点、技术、概念等）
  - 检测实体间关系（使用、实现、相关、依赖等）
  - 提供 `/v1/aipartner/knowledge-graph` API 端点
  - 图谱数据保存到 `workspace/knowledge_graph/graph.json`

#### 依赖更新
- ✅ 添加 `ripgrepy>=2.2.0` 到 `requirements.txt`

### 2. Backend (`backend/`)

#### 代码简化
- ✅ **简化 `rag_builder.py`**：仅保留文件解析功能，移除所有向量数据库和检索相关代码
- ✅ **删除 `advanced_retriever.py`**：不再需要混合检索器
- ✅ **大幅精简 `requirements.txt`**：
  - 移除：`llama-index-llms-ollama`, `llama-index-embeddings-huggingface`, `llama-index-vector-stores-chroma`, `chromadb`, `rank_bm25`, `jieba`, `nano-vectordb`, `rouge`, `mineru[core]` 等
  - 保留：仅文件解析所需的基础依赖

### 3. 删除的组件

- ✅ **删除 `e2graphrag_service/` 目录**
- ✅ **删除 `docker-compose.e2graphrag.yml`**
- ✅ **删除 `docker-compose.ragflow.yml`**

## 技术架构对比

### 之前（ChromaDB 向量检索）
```
文件上传 → PDF解析 → 文本分块 → 向量化 → ChromaDB存储 → 向量相似度检索
```

### 现在（Ripgrep 文件系统检索）
```
文件上传 → PDF解析 → 保存为文本 → Ripgrep直接搜索 → 返回匹配结果
```

## 优势

1. **更快的构建速度**：无需下载和初始化嵌入模型（~4.3GB），无需构建向量索引
2. **更简单的架构**：直接文件搜索，无需维护向量数据库
3. **更低的资源消耗**：不需要 ChromaDB 和嵌入模型的内存占用
4. **知识图谱可视化**：新增实体关系可视化功能，帮助理解文档结构

## API 变更

### 新增端点
- `POST /v1/aipartner/knowledge-graph`：获取知识图谱可视化数据

### 修改的端点
- `POST /v1/aipartner/index/rebuild`：现在返回提示信息，说明 ripgrep 不需要索引

## 使用说明

### 启动服务

1. **AI Partner Runner**（宿主机）：
```bash
cd ai_partner_runner
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 9001 --reload
```

2. **Backend**（Docker）：
```bash
docker-compose up backend
```

### 知识图谱可视化

构建完成后，知识图谱会自动生成。可以通过以下方式获取：

```bash
curl -X POST http://localhost:9001/v1/aipartner/knowledge-graph \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "rag_1"}'
```

返回格式：
```json
{
  "nodes": [
    {"id": "entity1", "label": "Entity 1", "type": "person", "size": 10, "files": ["note1.md"]}
  ],
  "links": [
    {"source": "entity1", "target": "entity2", "type": "related_to", "value": 1}
  ]
}
```

## 注意事项

1. **Ripgrep 依赖**：确保系统已安装 `ripgrep`（`rg` 命令），或 `ripgrepy` 会自动处理
2. **文件格式**：当前主要支持 `.md` 和 `.txt` 文件的搜索
3. **知识图谱**：实体提取使用简单的模式匹配，生产环境可考虑使用 NER 模型或 LLM

## 后续优化建议

1. 使用 LLM 进行更精确的实体提取和关系检测
2. 添加前端知识图谱可视化组件（D3.js/vis.js）
3. 支持更多文件格式的 ripgrep 搜索
4. 添加知识图谱的增量更新机制

