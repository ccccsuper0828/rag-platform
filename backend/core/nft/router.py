"""
NFT API 路由

提供 NFT 铸造、管理和交易接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import Optional

from ..middleware import get_current_user
from ..spark.storage import spark_storage
from .models import (
    KnowledgeNFT, 
    NFTStatus, 
    MintNFTRequest, 
    ListNFTRequest,
    NFTPricing
)
from .storage import nft_storage

nft_router = APIRouter(prefix="/nft", tags=["NFT"])


@nft_router.post("/mint")
async def mint_nft(
    request: MintNFTRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    铸造 NFT
    
    将高光源对话铸造为 NFT
    """
    user_id = current_user["user_id"]
    
    # 获取对话光源数据
    spark = spark_storage.get_conversation_spark(user_id, request.conversation_id)
    if not spark:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 检查是否有资格铸造
    if not spark.nft_eligible:
        raise HTTPException(
            status_code=400, 
            detail=f"对话光源值 ({spark.spark_value}) 未达到 NFT 铸造标准 (≥70)"
        )
    
    # 检查是否已铸造
    existing_nft = nft_storage.get_nft_by_conversation(request.conversation_id)
    if existing_nft:
        raise HTTPException(status_code=400, detail="此对话已铸造为 NFT")
    
    # 创建 NFT
    spark_data = spark.to_dict()
    nft = KnowledgeNFT.from_conversation_spark(spark_data, user_id)
    
    # 生成 Token ID
    nft.token_id = nft.generate_token_id()
    nft.status = NFTStatus.MINTED
    nft.minted_at = datetime.now()
    
    # 保存 NFT
    nft_id = nft_storage.save_nft(nft)
    
    # 更新对话光源记录
    spark_storage.update_conversation_spark(
        user_id, 
        request.conversation_id,
        {
            "nft_minted": True,
            "nft_token_id": nft.token_id
        }
    )
    
    return {
        "success": True,
        "message": "NFT 铸造成功！",
        "data": nft.to_dict()
    }


@nft_router.get("/my")
async def get_my_nfts(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的 NFT 列表
    """
    user_id = current_user["user_id"]
    
    nfts = nft_storage.get_user_nfts(user_id)
    
    # 筛选状态
    if status:
        nfts = [n for n in nfts if n.status.value == status]
    
    return {
        "success": True,
        "count": len(nfts),
        "data": [n.to_dict() for n in nfts]
    }


@nft_router.get("/marketplace")
async def get_marketplace(
    limit: int = Query(default=20, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    获取 NFT 市场（已上架的 NFT）
    """
    listed_nfts = nft_storage.get_all_listed_nfts(limit)
    
    return {
        "success": True,
        "count": len(listed_nfts),
        "data": [n.to_dict() for n in listed_nfts]
    }


@nft_router.get("/stats")
async def get_nft_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    获取 NFT 统计信息
    """
    stats = nft_storage.get_nft_stats()
    
    return {
        "success": True,
        "data": stats
    }


@nft_router.get("/{nft_id}")
async def get_nft_detail(
    nft_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取 NFT 详情
    """
    user_id = current_user["user_id"]
    
    nft = nft_storage.get_nft(user_id, nft_id)
    if not nft:
        raise HTTPException(status_code=404, detail="NFT 不存在")
    
    return {
        "success": True,
        "data": nft.to_dict()
    }


@nft_router.post("/{nft_id}/list")
async def list_nft(
    nft_id: str,
    request: ListNFTRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    上架 NFT
    """
    user_id = current_user["user_id"]
    
    nft = nft_storage.get_nft(user_id, nft_id)
    if not nft:
        raise HTTPException(status_code=404, detail="NFT 不存在")
    
    if nft.status != NFTStatus.MINTED:
        raise HTTPException(status_code=400, detail=f"NFT 状态不允许上架: {nft.status.value}")
    
    # 更新状态
    nft.status = NFTStatus.LISTED
    nft.listed_price = request.price
    nft_storage.save_nft(nft)
    
    return {
        "success": True,
        "message": "NFT 上架成功！",
        "data": nft.to_dict()
    }


@nft_router.post("/{nft_id}/unlist")
async def unlist_nft(
    nft_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    下架 NFT
    """
    user_id = current_user["user_id"]
    
    nft = nft_storage.get_nft(user_id, nft_id)
    if not nft:
        raise HTTPException(status_code=404, detail="NFT 不存在")
    
    if nft.status != NFTStatus.LISTED:
        raise HTTPException(status_code=400, detail="NFT 未上架")
    
    nft.status = NFTStatus.MINTED
    nft.listed_price = None
    nft_storage.save_nft(nft)
    
    return {
        "success": True,
        "message": "NFT 已下架"
    }


@nft_router.get("/price/estimate")
async def estimate_price(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    估算 NFT 价格
    """
    user_id = current_user["user_id"]
    
    spark = spark_storage.get_conversation_spark(user_id, conversation_id)
    if not spark:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    pricing = NFTPricing.calculate_price(
        spark.spark_value,
        spark.like_count,
        spark.save_count
    )
    
    return {
        "success": True,
        "data": {
            "conversation_id": conversation_id,
            "spark_value": spark.spark_value,
            "nft_eligible": spark.nft_eligible,
            "pricing": {
                "base_price": pricing.base_price,
                "spark_multiplier": pricing.spark_multiplier,
                "rarity_multiplier": pricing.rarity_multiplier,
                "demand_multiplier": pricing.demand_multiplier,
                "estimated_price": pricing.final_price,
                "currency": pricing.currency
            }
        }
    }

