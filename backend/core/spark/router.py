"""
光源算法 API 路由

提供光源系统的 REST API 接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime

from ..middleware import get_current_user
from .models import (
    ConversationSpark,
    SparkCalculateRequest,
    SparkActionRequest,
    SparkConfig
)
from .calculator import spark_calculator
from .storage import spark_storage

spark_router = APIRouter(prefix="/spark", tags=["Spark Algorithm"])


# ==================== 光源计算 ====================

@spark_router.post("/calculate")
async def calculate_spark(
    request: SparkCalculateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    计算对话的光源值
    
    在每次 RAG 对话完成后调用此接口
    """
    user_id = current_user["user_id"]
    
    # 计算光源值
    result = spark_calculator.calculate_spark(
        question=request.question,
        answer=request.answer,
        citations=request.citations
    )
    
    # 创建并保存对话光源记录
    spark = spark_calculator.create_conversation_spark(
        rag_id=request.rag_id,
        user_id=user_id,
        question=request.question,
        answer=request.answer,
        citations=request.citations
    )
    
    conversation_id = spark_storage.save_conversation_spark(spark)
    
    # 更新知识节点的引用统计
    for citation in request.citations:
        spark_storage.update_knowledge_node_citation(
            rag_id=request.rag_id,
            node_id=citation.get("node_id", ""),
            spark_value=result["spark_value"],
            content_preview=citation.get("content", "")[:100],
            source_file=citation.get("source_file", "")
        )
    
    # 更新用户档案
    spark_storage.update_user_profile(user_id)
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "spark_value": result["spark_value"],
        "nft_eligible": result["nft_eligible"],
        "scores": result["scores"],
        "details": result["details"]
    }


@spark_router.get("/conversation/{conversation_id}")
async def get_conversation_spark(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取对话的光源详情
    """
    user_id = current_user["user_id"]
    
    spark = spark_storage.get_conversation_spark(user_id, conversation_id)
    if not spark:
        raise HTTPException(status_code=404, detail="对话光源记录不存在")
    
    return {
        "success": True,
        "data": spark.to_dict()
    }


@spark_router.get("/conversations")
async def list_conversations(
    rag_id: Optional[str] = None,
    min_spark: float = 0,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户的对话光源列表
    """
    user_id = current_user["user_id"]
    
    if rag_id:
        # 获取特定 RAG 下的对话
        conversations = spark_storage.get_rag_conversations(rag_id)
        # 过滤当前用户的对话
        conversations = [c for c in conversations if c.user_id == user_id]
    else:
        # 获取用户所有对话
        conversations = spark_storage.get_user_conversations(user_id)
    
    # 过滤最低光源值
    conversations = [c for c in conversations if c.spark_value >= min_spark]
    
    # 排序
    conversations.sort(key=lambda x: x.spark_value, reverse=True)
    
    # 分页
    total = len(conversations)
    conversations = conversations[offset:offset + limit]
    
    return {
        "success": True,
        "total": total,
        "data": [c.to_dict() for c in conversations]
    }


# ==================== 用户行为 ====================

@spark_router.post("/conversation/{conversation_id}/like")
async def like_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    点赞对话
    """
    user_id = current_user["user_id"]
    
    spark = spark_storage.get_conversation_spark(user_id, conversation_id)
    if not spark:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 更新点赞数
    new_like_count = spark.like_count + 1
    new_behavior_score = min(
        new_like_count * SparkConfig.LIKE_SCORE +
        spark.save_count * SparkConfig.SAVE_SCORE +
        spark.share_count * SparkConfig.SHARE_SCORE +
        spark.reuse_count * SparkConfig.REUSE_SCORE,
        SparkConfig.MAX_BEHAVIOR_SCORE
    )
    
    # 重新计算光源值
    spark.like_count = new_like_count
    spark.behavior_score = new_behavior_score
    spark.spark_value = spark.calculate_spark_value()
    spark.nft_eligible = spark.check_nft_eligibility()
    spark.updated_at = datetime.now()
    
    spark_storage.save_conversation_spark(spark)
    
    return {
        "success": True,
        "like_count": new_like_count,
        "new_spark_value": spark.spark_value,
        "nft_eligible": spark.nft_eligible
    }


@spark_router.post("/conversation/{conversation_id}/save")
async def save_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    收藏对话
    """
    user_id = current_user["user_id"]
    
    spark = spark_storage.get_conversation_spark(user_id, conversation_id)
    if not spark:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 更新收藏数
    new_save_count = spark.save_count + 1
    new_behavior_score = min(
        spark.like_count * SparkConfig.LIKE_SCORE +
        new_save_count * SparkConfig.SAVE_SCORE +
        spark.share_count * SparkConfig.SHARE_SCORE +
        spark.reuse_count * SparkConfig.REUSE_SCORE,
        SparkConfig.MAX_BEHAVIOR_SCORE
    )
    
    spark.save_count = new_save_count
    spark.behavior_score = new_behavior_score
    spark.spark_value = spark.calculate_spark_value()
    spark.nft_eligible = spark.check_nft_eligibility()
    spark.updated_at = datetime.now()
    
    spark_storage.save_conversation_spark(spark)
    
    return {
        "success": True,
        "save_count": new_save_count,
        "new_spark_value": spark.spark_value,
        "nft_eligible": spark.nft_eligible
    }


@spark_router.post("/conversation/{conversation_id}/share")
async def share_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    分享对话
    """
    user_id = current_user["user_id"]
    
    spark = spark_storage.get_conversation_spark(user_id, conversation_id)
    if not spark:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 更新分享数
    new_share_count = spark.share_count + 1
    new_behavior_score = min(
        spark.like_count * SparkConfig.LIKE_SCORE +
        spark.save_count * SparkConfig.SAVE_SCORE +
        new_share_count * SparkConfig.SHARE_SCORE +
        spark.reuse_count * SparkConfig.REUSE_SCORE,
        SparkConfig.MAX_BEHAVIOR_SCORE
    )
    
    spark.share_count = new_share_count
    spark.behavior_score = new_behavior_score
    spark.spark_value = spark.calculate_spark_value()
    spark.nft_eligible = spark.check_nft_eligibility()
    spark.updated_at = datetime.now()
    
    spark_storage.save_conversation_spark(spark)
    
    return {
        "success": True,
        "share_count": new_share_count,
        "new_spark_value": spark.spark_value,
        "nft_eligible": spark.nft_eligible
    }


# ==================== 用户档案 ====================

@spark_router.get("/profile")
async def get_my_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的光源档案
    """
    user_id = current_user["user_id"]
    
    profile = spark_storage.update_user_profile(user_id)
    
    return {
        "success": True,
        "data": profile.to_dict()
    }


@spark_router.get("/profile/{user_id}")
async def get_user_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定用户的光源档案（公开信息）
    """
    profile = spark_storage.get_user_profile(user_id)
    
    # 只返回公开信息
    return {
        "success": True,
        "data": {
            "user_id": profile.user_id,
            "total_spark": profile.total_spark,
            "average_spark": profile.average_spark,
            "total_conversations": profile.total_conversations,
            "high_spark_conversations": profile.high_spark_conversations,
            "reputation_level": profile.reputation_level,
            "nft_count": profile.nft_count
        }
    }


# ==================== 排行榜 ====================

@spark_router.get("/leaderboard/users")
async def get_user_leaderboard(
    limit: int = Query(default=20, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户光源排行榜
    """
    leaderboard = spark_storage.get_leaderboard(limit)
    
    return {
        "success": True,
        "data": leaderboard
    }


@spark_router.get("/leaderboard/conversations")
async def get_conversation_leaderboard(
    limit: int = Query(default=20, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    获取高光源对话排行榜
    """
    conversations = spark_storage.get_all_conversations(
        limit=limit,
        min_spark=50,  # 只显示光源≥50的对话
        sort_by="spark_value"
    )
    
    return {
        "success": True,
        "data": [
            {
                "rank": i + 1,
                "conversation_id": c.conversation_id,
                "user_id": c.user_id,
                "question": c.question[:50] + "..." if len(c.question) > 50 else c.question,
                "spark_value": c.spark_value,
                "nft_eligible": c.nft_eligible,
                "nft_minted": c.nft_minted,
                "created_at": c.created_at.isoformat()
            }
            for i, c in enumerate(conversations)
        ]
    }


# ==================== 知识节点 ====================

@spark_router.get("/knowledge/{rag_id}/nodes")
async def get_knowledge_nodes(
    rag_id: str,
    limit: int = Query(default=20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    获取 RAG 知识节点的光源贡献排行
    """
    nodes = spark_storage.get_rag_knowledge_nodes(rag_id)
    
    # 按节点价值排序
    nodes.sort(key=lambda x: x.node_value, reverse=True)
    nodes = nodes[:limit]
    
    return {
        "success": True,
        "data": [n.to_dict() for n in nodes]
    }


# ==================== NFT 相关 ====================

@spark_router.get("/nft/eligible")
async def get_nft_eligible_conversations(
    current_user: dict = Depends(get_current_user)
):
    """
    获取有资格铸造 NFT 的对话列表
    """
    user_id = current_user["user_id"]
    
    conversations = spark_storage.get_user_conversations(user_id)
    eligible = [
        c.to_dict() for c in conversations 
        if c.nft_eligible and not c.nft_minted
    ]
    
    return {
        "success": True,
        "count": len(eligible),
        "data": eligible
    }


@spark_router.get("/stats")
async def get_spark_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    获取光源系统统计信息
    """
    user_id = current_user["user_id"]
    
    # 获取用户数据
    conversations = spark_storage.get_user_conversations(user_id)
    profile = spark_storage.get_user_profile(user_id)
    
    # 计算统计
    spark_values = [c.spark_value for c in conversations]
    
    return {
        "success": True,
        "data": {
            "total_conversations": len(conversations),
            "total_spark": sum(spark_values),
            "average_spark": sum(spark_values) / len(spark_values) if spark_values else 0,
            "max_spark": max(spark_values) if spark_values else 0,
            "min_spark": min(spark_values) if spark_values else 0,
            "nft_eligible_count": sum(1 for c in conversations if c.nft_eligible),
            "nft_minted_count": sum(1 for c in conversations if c.nft_minted),
            "reputation_level": profile.reputation_level,
            "next_level_threshold": SparkConfig.REPUTATION_LEVELS.get(
                profile.reputation_level + 1, 
                float('inf')
            )
        }
    }

