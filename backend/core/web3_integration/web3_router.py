"""
Web3 API 路由

独立的 API 端点，不影响现有 RAG API
所有端点都是可选的，Web3 功能禁用时返回友好错误
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from .config import is_web3_available, get_network_config, WEB3_ENABLED
from .nft_service import get_nft_service, NFTMintRequest, NFTMintResult
from .ipfs_service import get_ipfs_service
from .contract_service import get_contract_service

web3_router = APIRouter(prefix="/web3", tags=["Web3"])


# ==================== 请求/响应模型 ====================

class Web3StatusResponse(BaseModel):
    """Web3 状态响应"""
    enabled: bool
    web3_available: bool
    ipfs_available: bool
    contract_available: bool
    network: Optional[Dict[str, Any]] = None


class PrepareNFTRequest(BaseModel):
    """准备 NFT 铸造请求"""
    question: str
    answer: str
    sources: List[Dict[str, Any]] = []
    user_address: str
    metadata: Dict[str, Any] = {}


class UploadToIPFSRequest(BaseModel):
    """上传到 IPFS 请求"""
    content: Dict[str, Any]
    name: str = "rag_content"


class VerifyContentRequest(BaseModel):
    """验证内容请求"""
    token_id: int
    answer: str


# ==================== API 端点 ====================

@web3_router.get("/status", response_model=Web3StatusResponse)
async def get_web3_status():
    """
    获取 Web3 功能状态
    
    即使 Web3 禁用，此端点也会返回状态信息
    """
    ipfs = get_ipfs_service()
    contract = get_contract_service()
    
    return Web3StatusResponse(
        enabled=WEB3_ENABLED,
        web3_available=is_web3_available(),
        ipfs_available=ipfs.is_available(),
        contract_available=contract.is_available(),
        network=get_network_config() if WEB3_ENABLED else None
    )


@web3_router.get("/network")
async def get_network_info():
    """获取当前网络信息"""
    contract = get_contract_service()
    return contract.get_network_info()


@web3_router.post("/nft/prepare", response_model=NFTMintResult)
async def prepare_nft_mint(request: PrepareNFTRequest):
    """
    准备 NFT 铸造
    
    1. 上传内容到 IPFS
    2. 生成内容哈希
    3. 返回前端铸造所需参数
    
    实际铸造由前端完成（用户钱包签名）
    """
    nft_service = get_nft_service()
    
    if not nft_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="NFT service not available. Please configure IPFS settings."
        )
    
    mint_request = NFTMintRequest(
        question=request.question,
        answer=request.answer,
        sources=request.sources,
        user_address=request.user_address,
        metadata=request.metadata
    )
    
    result = await nft_service.prepare_nft_mint(mint_request)
    
    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.error or "NFT preparation failed"
        )
    
    return result


@web3_router.post("/ipfs/upload")
async def upload_to_ipfs(request: UploadToIPFSRequest):
    """直接上传内容到 IPFS"""
    ipfs = get_ipfs_service()
    
    if not ipfs.is_available():
        raise HTTPException(
            status_code=503,
            detail="IPFS service not available. Please configure Pinata API key."
        )
    
    cid = await ipfs.upload_json(request.content, request.name)
    
    if not cid:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload to IPFS"
        )
    
    return {
        "success": True,
        "cid": cid,
        "ipfs_url": f"ipfs://{cid}",
        "gateway_url": f"https://gateway.pinata.cloud/ipfs/{cid}"
    }


@web3_router.get("/ipfs/{cid}")
async def get_ipfs_content(cid: str):
    """从 IPFS 获取内容"""
    ipfs = get_ipfs_service()
    
    content = await ipfs.get_content(cid)
    
    if not content:
        raise HTTPException(
            status_code=404,
            detail="Content not found on IPFS"
        )
    
    import json
    try:
        return json.loads(content)
    except:
        return {"raw_content": content.decode('utf-8', errors='replace')}


@web3_router.post("/nft/verify")
async def verify_nft_content(request: VerifyContentRequest):
    """验证 NFT 内容是否匹配链上记录"""
    nft_service = get_nft_service()
    
    if not nft_service.contract.is_available():
        raise HTTPException(
            status_code=503,
            detail="Contract service not available"
        )
    
    result = await nft_service.verify_nft_content(
        token_id=request.token_id,
        answer=request.answer
    )
    
    return result


@web3_router.get("/nft/{token_id}")
async def get_nft_metadata(token_id: int):
    """获取 NFT 元数据"""
    contract = get_contract_service()
    
    if not contract.is_available():
        raise HTTPException(
            status_code=503,
            detail="Contract service not available"
        )
    
    metadata = await contract.get_token_metadata(token_id)
    
    if not metadata:
        raise HTTPException(
            status_code=404,
            detail="Token not found"
        )
    
    return metadata


@web3_router.post("/hash")
async def generate_content_hash(content: Dict[str, Any]):
    """生成内容哈希（用于前端验证）"""
    import hashlib
    import json
    
    normalized = json.dumps(content, sort_keys=True, separators=(',', ':'))
    hash_value = hashlib.sha256(normalized.encode()).hexdigest()
    
    return {
        "hash": f"0x{hash_value}",
        "algorithm": "sha256"
    }

