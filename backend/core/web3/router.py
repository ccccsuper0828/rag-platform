"""
Web3 NFT API 路由

提供 NFT 铸造签名和链上数据查询接口
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..middleware import get_current_user
from ..spark.storage import spark_storage
from .signer import nft_signer, nft_contract

web3_router = APIRouter(prefix="/web3", tags=["Web3 NFT"])


class MintSignatureRequest(BaseModel):
    """铸造签名请求"""
    conversation_id: str
    wallet_address: str
    ipfs_cid: Optional[str] = ""
    price: int = 0  # 访问价格（以 UTIL 代币的最小单位计）


class MintSignatureResponse(BaseModel):
    """铸造签名响应"""
    success: bool
    signature: Optional[str] = None
    message_hash: Optional[str] = None
    signer: Optional[str] = None
    error: Optional[str] = None
    mint_data: Optional[dict] = None


@web3_router.get("/config")
async def get_web3_config(current_user: dict = Depends(get_current_user)):
    """
    获取 Web3 配置信息
    """
    return {
        "success": True,
        "data": {
            "signer_configured": nft_signer.is_configured(),
            "signer_address": nft_signer.get_signer_address(),
            "contract_configured": nft_contract.is_configured(),
            "contract_address": nft_contract.contract_address,
            "network": "sepolia"
        }
    }


@web3_router.post("/mint-signature", response_model=MintSignatureResponse)
async def get_mint_signature(
    request: MintSignatureRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    获取 NFT 铸造签名
    
    流程：
    1. 验证用户是否拥有该对话
    2. 验证对话光源值是否达到铸造门槛 (≥70)
    3. 生成签名供用户在链上铸造
    """
    user_id = current_user["user_id"]
    
    # 检查签名服务是否配置
    if not nft_signer.is_configured():
        return MintSignatureResponse(
            success=False,
            error="NFT 签名服务未配置，请联系管理员设置 NFT_SIGNER_PRIVATE_KEY"
        )
    
    # 获取对话光源记录
    spark = spark_storage.get_conversation_spark(user_id, request.conversation_id)
    if not spark:
        return MintSignatureResponse(
            success=False,
            error="对话不存在或不属于当前用户"
        )
    
    # 验证光源值
    if spark.spark_value < 70:
        return MintSignatureResponse(
            success=False,
            error=f"光源值 {spark.spark_value:.1f} 未达到铸造门槛 70"
        )
    
    # 检查是否已铸造
    if spark.nft_minted:
        return MintSignatureResponse(
            success=False,
            error="该对话已铸造过 NFT"
        )
    
    # 检查链上是否已铸造
    if nft_contract.is_configured():
        if nft_contract.is_conversation_minted(request.conversation_id):
            return MintSignatureResponse(
                success=False,
                error="该对话已在链上铸造"
            )
    
    # 生成签名
    result = nft_signer.sign_mint_request(
        user_address=request.wallet_address,
        conversation_id=request.conversation_id,
        rag_id=spark.rag_id,
        spark_value=int(spark.spark_value),
        base_score=int(spark.base_score),
        citation_score=int(spark.citation_score),
        activation_score=int(spark.activation_score),
        behavior_score=int(spark.behavior_score)
    )
    
    if not result:
        return MintSignatureResponse(
            success=False,
            error="签名生成失败"
        )
    
    if "error" in result:
        return MintSignatureResponse(
            success=False,
            error=result["error"]
        )
    
    # 返回签名和铸造数据
    return MintSignatureResponse(
        success=True,
        signature=result["signature"],
        message_hash=result["message_hash"],
        signer=result["signer"],
        mint_data={
            "conversationId": request.conversation_id,
            "ragId": spark.rag_id,
            "ipfsCID": request.ipfs_cid or f"spark-{request.conversation_id}",
            "sparkValue": int(spark.spark_value),
            "baseScore": int(spark.base_score),
            "citationScore": int(spark.citation_score),
            "activationScore": int(spark.activation_score),
            "behaviorScore": int(spark.behavior_score),
            "price": request.price,
            "rarity": _get_rarity(spark.spark_value)
        }
    )


def _get_rarity(spark_value: float) -> str:
    """获取稀有度名称"""
    if spark_value >= 85:
        return "Legendary"
    elif spark_value >= 70:
        return "Epic"
    elif spark_value >= 50:
        return "Rare"
    return "Common"


@web3_router.post("/confirm-mint/{conversation_id}")
async def confirm_mint(
    conversation_id: str,
    token_id: int,
    tx_hash: str,
    current_user: dict = Depends(get_current_user)
):
    """
    确认 NFT 铸造完成
    
    用户在链上铸造成功后调用此接口更新后端状态
    """
    user_id = current_user["user_id"]
    
    # 获取对话光源记录
    spark = spark_storage.get_conversation_spark(user_id, conversation_id)
    if not spark:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 更新铸造状态
    from datetime import datetime
    spark.nft_minted = True
    spark.nft_token_id = str(token_id)
    spark.nft_minted_at = datetime.now()
    
    spark_storage.save_conversation_spark(spark)
    
    # 更新用户档案
    spark_storage.update_user_profile(user_id)
    
    return {
        "success": True,
        "message": "NFT 铸造状态已更新",
        "data": {
            "conversation_id": conversation_id,
            "token_id": token_id,
            "tx_hash": tx_hash
        }
    }


@web3_router.get("/nft/{token_id}")
async def get_nft_info(
    token_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取 NFT 链上信息
    """
    if not nft_contract.is_configured():
        raise HTTPException(status_code=503, detail="合约未配置")
    
    info = nft_contract.get_nft_info(token_id)
    if not info:
        raise HTTPException(status_code=404, detail="NFT 不存在")
    
    return {
        "success": True,
        "data": info
    }


@web3_router.get("/nft/by-conversation/{conversation_id}")
async def get_nft_by_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    通过对话 ID 获取 NFT 信息
    """
    if not nft_contract.is_configured():
        raise HTTPException(status_code=503, detail="合约未配置")
    
    token_id = nft_contract.get_token_by_conversation(conversation_id)
    if token_id is None:
        raise HTTPException(status_code=404, detail="该对话未铸造 NFT")
    
    info = nft_contract.get_nft_info(token_id)
    
    return {
        "success": True,
        "data": {
            "token_id": token_id,
            **info
        }
    }


@web3_router.get("/access-check/{token_id}")
async def check_access(
    token_id: int,
    wallet_address: str,
    current_user: dict = Depends(get_current_user)
):
    """
    检查用户是否有 NFT 访问权限
    """
    if not nft_contract.is_configured():
        raise HTTPException(status_code=503, detail="合约未配置")
    
    has_access = nft_contract.has_access(wallet_address, token_id)
    
    return {
        "success": True,
        "data": {
            "token_id": token_id,
            "wallet_address": wallet_address,
            "has_access": has_access
        }
    }

