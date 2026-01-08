"""
NFT 铸造服务

将 RAG 答案铸造为 NFT 的完整流程
独立于 RAG 核心功能
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from .ipfs_service import get_ipfs_service
from .contract_service import get_contract_service
from .config import is_web3_available, get_network_config

logger = logging.getLogger(__name__)


class NFTMintRequest(BaseModel):
    """NFT 铸造请求"""
    question: str
    answer: str
    sources: list = []
    user_address: str
    metadata: Dict[str, Any] = {}


class NFTMintResult(BaseModel):
    """NFT 铸造结果"""
    success: bool
    ipfs_cid: Optional[str] = None
    content_hash: Optional[str] = None
    transaction_params: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class NFTService:
    """NFT 铸造服务"""
    
    def __init__(self):
        self.ipfs = get_ipfs_service()
        self.contract = get_contract_service()
    
    def is_available(self) -> bool:
        """检查 NFT 服务是否可用"""
        # 至少需要 IPFS 可用
        return self.ipfs.is_available()
    
    async def prepare_nft_mint(self, request: NFTMintRequest) -> NFTMintResult:
        """
        准备 NFT 铸造（上传到 IPFS + 生成交易参数）
        
        实际铸造由前端完成（用户钱包签名）
        """
        if not self.is_available():
            return NFTMintResult(
                success=False,
                error="NFT service not available (IPFS not configured)"
            )
        
        try:
            # 1. 生成内容哈希
            content_hash = self._generate_content_hash(request.answer)
            
            # 2. 构建 NFT 元数据
            metadata = self._build_metadata(request, content_hash)
            
            # 3. 上传到 IPFS
            ipfs_cid = await self.ipfs.upload_json(
                metadata,
                name=f"rag_nft_{content_hash[:16]}"
            )
            
            if not ipfs_cid:
                return NFTMintResult(
                    success=False,
                    content_hash=content_hash,
                    error="Failed to upload to IPFS"
                )
            
            # 4. 生成前端铸造参数
            tx_params = None
            if self.contract.is_available():
                tx_params = self.contract.generate_mint_params_for_frontend(
                    question=request.question,
                    answer=request.answer,
                    ipfs_cid=ipfs_cid
                )
            
            return NFTMintResult(
                success=True,
                ipfs_cid=ipfs_cid,
                content_hash=content_hash,
                transaction_params=tx_params
            )
            
        except Exception as e:
            logger.error(f"NFT mint preparation error: {e}")
            return NFTMintResult(
                success=False,
                error=str(e)
            )
    
    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希"""
        normalized = json.dumps(content, sort_keys=True, separators=(',', ':'))
        hash_value = hashlib.sha256(normalized.encode()).hexdigest()
        return f"0x{hash_value}"
    
    def _build_metadata(self, request: NFTMintRequest, content_hash: str) -> Dict[str, Any]:
        """构建 NFT 元数据（遵循 OpenSea 标准）"""
        return {
            # OpenSea 标准字段
            "name": f"RAG Answer: {request.question[:50]}...",
            "description": f"AI-generated answer verified on blockchain.\n\nQuestion: {request.question}",
            "image": "ipfs://QmDefault...",  # 可替换为动态生成的图片
            "external_url": "https://your-platform.com",
            
            # 自定义属性
            "attributes": [
                {
                    "trait_type": "Content Hash",
                    "value": content_hash[:16] + "..."
                },
                {
                    "trait_type": "Source Count",
                    "value": len(request.sources)
                },
                {
                    "trait_type": "Created",
                    "value": datetime.utcnow().strftime("%Y-%m-%d")
                },
                {
                    "trait_type": "Platform",
                    "value": "RAG Platform"
                }
            ],
            
            # 完整内容
            "content": {
                "question": request.question,
                "answer": request.answer,
                "sources": request.sources,
                "content_hash": content_hash,
                "timestamp": datetime.utcnow().isoformat(),
                "verified": True
            },
            
            # 用户自定义元数据
            "custom_metadata": request.metadata
        }
    
    async def verify_nft_content(self, token_id: int, answer: str) -> Dict[str, Any]:
        """验证 NFT 内容是否匹配链上记录"""
        if not self.contract.is_available():
            return {
                "verified": False,
                "error": "Contract service not available"
            }
        
        try:
            # 获取链上元数据
            token_meta = await self.contract.get_token_metadata(token_id)
            if not token_meta:
                return {
                    "verified": False,
                    "error": "Token not found"
                }
            
            # 从 IPFS 获取内容
            ipfs_content = await self.ipfs.get_content(token_meta["answer_cid"])
            if not ipfs_content:
                return {
                    "verified": False,
                    "error": "IPFS content not found"
                }
            
            # 比较哈希
            stored_data = json.loads(ipfs_content)
            stored_hash = stored_data.get("content", {}).get("content_hash", "")
            current_hash = self._generate_content_hash(answer)
            
            return {
                "verified": stored_hash == current_hash,
                "token_id": token_id,
                "stored_hash": stored_hash,
                "computed_hash": current_hash,
                "ipfs_cid": token_meta["answer_cid"]
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e)
            }


# 单例
_nft_service: Optional[NFTService] = None


def get_nft_service() -> NFTService:
    """获取 NFT 服务实例"""
    global _nft_service
    if _nft_service is None:
        _nft_service = NFTService()
    return _nft_service

