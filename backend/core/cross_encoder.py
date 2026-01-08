"""
Cross-Encoder 重排序模块
借鉴 Khoj 的实现，提供两阶段检索：
1. 第一阶段：使用 Bi-Encoder (LEANN) 快速召回候选
2. 第二阶段：使用 Cross-Encoder 精确重排序

优势：
- 显著提升搜索精度 (通常提升 5-15%)
- 更好地理解 query-document 语义关系
- 适合需要高精度的场景
"""

import os
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache
import numpy as np

# Cross-Encoder 配置
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "BAAI/bge-reranker-base")
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "5"))
ENABLE_RERANK = os.getenv("ENABLE_CROSS_ENCODER", "true").lower() == "true"


@lru_cache(maxsize=1)
def load_cross_encoder():
    """
    懒加载 Cross-Encoder 模型
    使用 LRU 缓存确保只加载一次
    """
    try:
        from sentence_transformers import CrossEncoder
        
        print(f"📊 Loading Cross-Encoder model: {CROSS_ENCODER_MODEL}")
        model = CrossEncoder(CROSS_ENCODER_MODEL, max_length=512)
        print("✅ Cross-Encoder loaded successfully")
        return model
    except ImportError:
        print("⚠️ sentence-transformers not installed, Cross-Encoder disabled")
        return None
    except Exception as e:
        print(f"⚠️ Failed to load Cross-Encoder: {e}")
        return None


def rerank_with_cross_encoder(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = RERANK_TOP_K,
    score_threshold: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    使用 Cross-Encoder 重排序文档
    
    Args:
        query: 用户查询
        documents: 待重排序的文档列表，每个文档需包含 'content' 字段
        top_k: 返回的 top-k 结果数
        score_threshold: 最低分数阈值，低于此分数的文档将被过滤
        
    Returns:
        重排序后的文档列表，包含 cross_encoder_score 字段
    """
    if not ENABLE_RERANK:
        print("ℹ️ Cross-Encoder reranking disabled")
        return documents[:top_k]
    
    if not documents:
        return []
    
    cross_encoder = load_cross_encoder()
    if cross_encoder is None:
        print("⚠️ Cross-Encoder not available, returning original order")
        return documents[:top_k]
    
    # 准备 query-document pairs
    pairs = [(query, doc.get("content", "")) for doc in documents]
    
    # 批量计算 Cross-Encoder 分数
    try:
        scores = cross_encoder.predict(pairs, show_progress_bar=False)
    except Exception as e:
        print(f"⚠️ Cross-Encoder prediction failed: {e}")
        return documents[:top_k]
    
    # 将分数添加到文档
    for doc, score in zip(documents, scores):
        doc["cross_encoder_score"] = float(score)
    
    # 过滤低于阈值的文档
    filtered_docs = [
        doc for doc in documents 
        if doc.get("cross_encoder_score", 0) >= score_threshold
    ]
    
    # 按 Cross-Encoder 分数降序排序
    reranked_docs = sorted(
        filtered_docs,
        key=lambda x: x.get("cross_encoder_score", 0),
        reverse=True
    )
    
    print(f"🎯 Cross-Encoder reranking: {len(documents)} -> {len(reranked_docs[:top_k])} documents")
    
    return reranked_docs[:top_k]


def hybrid_search_with_rerank(
    query: str,
    semantic_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]],
    semantic_weight: float = 0.6,
    keyword_weight: float = 0.4,
    top_k: int = 10,
    use_cross_encoder: bool = True,
) -> List[Dict[str, Any]]:
    """
    混合搜索 + Cross-Encoder 重排序
    
    结合语义搜索和关键词搜索结果，然后使用 Cross-Encoder 精排
    
    Args:
        query: 用户查询
        semantic_results: 语义搜索结果
        keyword_results: 关键词搜索结果
        semantic_weight: 语义搜索权重
        keyword_weight: 关键词搜索权重
        top_k: 返回的 top-k 结果数
        use_cross_encoder: 是否使用 Cross-Encoder
        
    Returns:
        融合并重排序后的结果
    """
    # 使用 Reciprocal Rank Fusion (RRF) 融合结果
    k = 60  # RRF 常数
    fused_scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}
    
    # 处理语义搜索结果
    for rank, doc in enumerate(semantic_results):
        doc_id = doc.get("content", str(rank))[:100]  # 使用内容前100字符作为ID
        score = semantic_weight / (k + rank + 1)
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + score
        doc_map[doc_id] = doc
    
    # 处理关键词搜索结果
    for rank, doc in enumerate(keyword_results):
        doc_id = doc.get("content", str(rank))[:100]
        score = keyword_weight / (k + rank + 1)
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + score
        if doc_id not in doc_map:
            doc_map[doc_id] = doc
    
    # 按融合分数排序
    sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
    fused_docs = [doc_map[doc_id] for doc_id in sorted_ids[:top_k * 2]]  # 取更多候选用于重排序
    
    # 添加融合分数
    for doc, doc_id in zip(fused_docs, sorted_ids[:len(fused_docs)]):
        doc["fused_score"] = fused_scores[doc_id]
    
    # 使用 Cross-Encoder 重排序
    if use_cross_encoder and ENABLE_RERANK:
        return rerank_with_cross_encoder(query, fused_docs, top_k=top_k)
    
    return fused_docs[:top_k]


def batch_rerank(
    query: str,
    document_batches: List[List[Dict[str, Any]]],
    top_k_per_batch: int = 3,
) -> List[Dict[str, Any]]:
    """
    批量重排序多个文档批次
    
    适用于从多个来源获取文档的场景
    
    Args:
        query: 用户查询
        document_batches: 多个文档批次
        top_k_per_batch: 每批次返回的 top-k
        
    Returns:
        合并并重排序后的结果
    """
    all_docs = []
    
    for batch in document_batches:
        reranked = rerank_with_cross_encoder(query, batch, top_k=top_k_per_batch)
        all_docs.extend(reranked)
    
    # 最终全局重排序
    if all_docs:
        return rerank_with_cross_encoder(query, all_docs, top_k=top_k_per_batch * len(document_batches))
    
    return []


# 导出
__all__ = [
    "rerank_with_cross_encoder",
    "hybrid_search_with_rerank",
    "batch_rerank",
    "load_cross_encoder",
    "ENABLE_RERANK",
]

