# LEANN 集成指南

## 🚀 概述

本项目已集成 **LEANN** (Low-storage Embedding for Approximate Nearest Neighbor search)，实现：

| 特性 | 效果 |
|------|------|
| **存储节省** | 97% 存储空间节省 vs 传统向量数据库 |
| **语义搜索** | "机器学习" 匹配 "ML", "deep learning" |
| **混合检索** | 语义 + 关键词，双重保障 |
| **无精度损失** | 与 FAISS 相同的搜索质量 |
| **本地运行** | 数据不离开你的机器 |

## 📦 安装

### 方式 1：从 PyPI 安装（推荐）

```bash
# 安装 LEANN 核心包
pip install leann-core leann-backend-hnsw

# 或者一次性安装所有依赖
pip install -r backend/requirements.txt
pip install -r ai_partner_runner/requirements.txt
```

### 方式 2：从本地 LEANN 仓库安装

如果你有 LEANN 源码（位于 `../LEANN`），可以：

```bash
# 进入 LEANN 目录
cd ../LEANN

# 安装依赖
uv sync

# 或者用 pip 安装为可编辑包
pip install -e packages/leann-core -e packages/leann-backend-hnsw
```

## ⚙️ 配置

### 环境变量

在 `.env` 或环境中设置：

```bash
# 启用/禁用 LEANN（默认启用）
ENABLE_LEANN=true

# 嵌入模型配置
LEANN_EMBEDDING_MODEL=facebook/contriever      # 默认模型，768维
# LEANN_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5  # 中文优化
# LEANN_EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5  # 更高精度

# 嵌入模式
LEANN_EMBEDDING_MODE=sentence-transformers  # 本地模型（默认）
# LEANN_EMBEDDING_MODE=ollama              # 使用 Ollama
# LEANN_EMBEDDING_MODE=openai              # 使用 OpenAI API

# 混合搜索权重
LEANN_SEMANTIC_WEIGHT=0.7    # 语义搜索权重（0-1）
LEANN_KEYWORD_WEIGHT=0.3     # 关键词搜索权重（0-1）

# 分块参数
LEANN_CHUNK_SIZE=512         # 每个文本块的最大字符数
LEANN_CHUNK_OVERLAP=64       # 块之间的重叠字符数

# 后端选择
LEANN_BACKEND=hnsw           # hnsw（默认）或 diskann
```

### 推荐的模型配置

| 场景 | 模型 | 说明 |
|------|------|------|
| **通用（英文）** | `facebook/contriever` | 默认，平衡速度和质量 |
| **中文优化** | `BAAI/bge-small-zh-v1.5` | 中文语义理解更好 |
| **高精度** | `sentence-transformers/all-mpnet-base-v2` | 更高质量，稍慢 |
| **轻量级** | `sentence-transformers/all-MiniLM-L6-v2` | 更快，适合低配机器 |
| **本地 Ollama** | `nomic-embed-text` | 通过 Ollama 运行 |

## 🏗️ 架构

```
用户问题
    │
    ▼
┌─────────────────────────────────────────────┐
│           混合检索 (HybridSearcher)          │
│  ┌─────────────────┐  ┌─────────────────────┐│
│  │  LEANN 语义搜索  │  │   ripgrep 关键词    ││
│  │  (70% 权重)     │  │   (30% 权重)        ││
│  └────────┬────────┘  └──────────┬──────────┘│
│           │                      │           │
│           └──────────┬───────────┘           │
│                      │                       │
│           ┌──────────▼──────────┐            │
│           │  RRF 融合排序       │            │
│           │  (Reciprocal Rank   │            │
│           │   Fusion)           │            │
│           └──────────┬──────────┘            │
└──────────────────────┼───────────────────────┘
                       │
                       ▼
              Top-K 检索结果
                       │
                       ▼
              Claude Code 生成回答
```

## 📊 存储对比

| 数据量 | 传统 FAISS | LEANN | 节省 |
|--------|-----------|-------|------|
| 1K 文档 | 3 MB | 100 KB | 97% |
| 10K 文档 | 30 MB | 1 MB | 97% |
| 100K 文档 | 300 MB | 10 MB | 97% |
| 1M 文档 | 3 GB | 100 MB | 97% |

**为什么 LEANN 这么小？**
- 不存储嵌入向量
- 只存储图结构（CSR 格式）
- 搜索时按需计算嵌入

## 🔧 使用方式

### 自动集成（已配置）

上传文件时会自动：
1. 解析文件内容
2. 分块处理
3. 构建 LEANN 语义索引
4. 后续查询使用混合搜索

### 手动使用 API

```python
from pathlib import Path
from core.leann_rag import LeannIndexManager, HybridSearcher, chunk_text

# 构建索引
workspace = Path("/path/to/workspace")
manager = LeannIndexManager(workspace)

# 准备文档
documents = [
    {"text": "LEANN 是一个低存储的向量索引库...", "metadata": {"filename": "intro.md"}},
    {"text": "语义搜索可以理解用户意图...", "metadata": {"filename": "semantic.md"}},
]

# 构建索引
manager.build_index(documents, force_rebuild=True)

# 搜索
results = manager.search("向量数据库存储优化", top_k=5)
for r in results:
    print(f"{r.filename}: {r.score:.4f}")
    print(f"  {r.content[:100]}...")
```

### 混合搜索

```python
from core.leann_rag import HybridSearcher

searcher = HybridSearcher(workspace)

# 混合搜索（语义 + 关键词）
results = searcher.search(
    query="如何减少存储空间",
    top_k=5,
    semantic_weight=0.7,  # LEANN 语义搜索权重
    keyword_weight=0.3,   # ripgrep 关键词权重
)
```

## 🐛 故障排除

### LEANN 未生效

检查日志：
```
⚠️ LEANN not available, using ripgrep-only search
```

解决方案：
```bash
# 检查是否安装
pip list | grep leann

# 重新安装
pip install leann-core leann-backend-hnsw --force-reinstall
```

### 索引构建失败

检查日志：
```
LEANN index build failed: ...
```

常见原因：
1. **内存不足**：减小 `LEANN_CHUNK_SIZE`
2. **模型下载失败**：检查网络，或使用本地模型
3. **权限问题**：检查 workspace 目录权限

### 搜索质量差

调整参数：
```bash
# 增加语义权重（更依赖语义理解）
LEANN_SEMANTIC_WEIGHT=0.8
LEANN_KEYWORD_WEIGHT=0.2

# 或增加关键词权重（更依赖精确匹配）
LEANN_SEMANTIC_WEIGHT=0.5
LEANN_KEYWORD_WEIGHT=0.5
```

## 📈 性能优化

### 首次加载慢

首次使用时需要下载模型（~400MB），后续会缓存。

加速方案：
```bash
# 预先下载模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('facebook/contriever')"
```

### GPU 加速

```bash
# 使用 GPU
export LEANN_EMBEDDING_DEVICE=cuda

# 或 Apple Silicon
export LEANN_EMBEDDING_DEVICE=mps
```

### 批量索引优化

对于大量文档，增加批处理大小：
```python
# 在 embedding_options 中设置
builder = LeannBuilder(
    backend_name="hnsw",
    embedding_options={"batch_size": 64}
)
```

## 🔒 隐私说明

- **本地运行**：所有嵌入计算在本地完成
- **无数据上传**：使用 `sentence-transformers` 模式时无网络请求
- **多租户隔离**：每个用户有独立的索引目录

## 📚 更多资源

- [LEANN 官方文档](https://github.com/yichuan-w/LEANN)
- [LEANN 论文](https://arxiv.org/abs/2506.08276)
- [Sentence Transformers](https://www.sbert.net/)

## 🤝 贡献

如有问题或建议，欢迎提 Issue 或 PR！

