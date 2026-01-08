"""
IPFS 存储服务

支持：
- Pinata (推荐)
- 本地 IPFS 节点
- Infura IPFS

完全独立，不影响 RAG 功能
"""

import os
import json
import hashlib
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from .config import (
    IPFS_ENABLED,
    IPFS_API_URL,
    IPFS_API_KEY,
    IPFS_API_SECRET,
    PINATA_JWT
)

logger = logging.getLogger(__name__)


class IPFSService:
    """IPFS 存储服务"""
    
    def __init__(self):
        self.enabled = IPFS_ENABLED
        self.pinata_jwt = PINATA_JWT
        self.api_key = IPFS_API_KEY
        self.api_secret = IPFS_API_SECRET
    
    def is_available(self) -> bool:
        """检查 IPFS 服务是否可用"""
        return self.enabled and (self.pinata_jwt or (self.api_key and self.api_secret))
    
    async def upload_json(self, data: Dict[str, Any], name: str = "rag_content") -> Optional[str]:
        """
        上传 JSON 数据到 IPFS
        
        Args:
            data: 要上传的数据
            name: 文件名
            
        Returns:
            IPFS CID 或 None
        """
        if not self.is_available():
            logger.warning("IPFS service not available")
            return None
        
        try:
            # 添加元数据
            content = {
                **data,
                "_metadata": {
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "platform": "rag-platform",
                    "version": "1.0"
                }
            }
            
            json_str = json.dumps(content, ensure_ascii=False, indent=2)
            
            return await self._upload_to_pinata(json_str.encode('utf-8'), f"{name}.json")
            
        except Exception as e:
            logger.error(f"IPFS upload error: {e}")
            return None
    
    async def upload_text(self, text: str, name: str = "content") -> Optional[str]:
        """上传文本到 IPFS"""
        if not self.is_available():
            return None
        
        try:
            return await self._upload_to_pinata(text.encode('utf-8'), f"{name}.txt")
        except Exception as e:
            logger.error(f"IPFS text upload error: {e}")
            return None
    
    async def _upload_to_pinata(self, content: bytes, filename: str) -> Optional[str]:
        """使用 Pinata API 上传"""
        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        
        headers = {}
        if self.pinata_jwt:
            headers["Authorization"] = f"Bearer {self.pinata_jwt}"
        else:
            headers["pinata_api_key"] = self.api_key
            headers["pinata_secret_api_key"] = self.api_secret
        
        # 创建 multipart 请求
        files = {
            "file": (filename, content)
        }
        
        # 可选：添加 Pinata 元数据
        pinata_metadata = json.dumps({
            "name": filename,
            "keyvalues": {
                "platform": "rag-platform",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        data = {
            "pinataMetadata": pinata_metadata
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                cid = result.get("IpfsHash")
                logger.info(f"Uploaded to IPFS: {cid}")
                return cid
            else:
                logger.error(f"Pinata upload failed: {response.text}")
                return None
    
    async def get_content(self, cid: str) -> Optional[bytes]:
        """从 IPFS 获取内容"""
        gateways = [
            f"https://gateway.pinata.cloud/ipfs/{cid}",
            f"https://ipfs.io/ipfs/{cid}",
            f"https://cloudflare-ipfs.com/ipfs/{cid}",
            f"https://dweb.link/ipfs/{cid}"
        ]
        
        async with httpx.AsyncClient(timeout=30) as client:
            for gateway in gateways:
                try:
                    response = await client.get(gateway)
                    if response.status_code == 200:
                        return response.content
                except Exception as e:
                    logger.debug(f"Gateway {gateway} failed: {e}")
                    continue
        
        logger.error(f"Failed to fetch IPFS content: {cid}")
        return None
    
    def generate_content_hash(self, content: str) -> str:
        """生成内容哈希（用于链上验证）"""
        normalized = json.dumps(content, sort_keys=True, separators=(',', ':'))
        content_hash = hashlib.sha256(normalized.encode()).hexdigest()
        return f"0x{content_hash}"


# 单例
_ipfs_service: Optional[IPFSService] = None


def get_ipfs_service() -> IPFSService:
    """获取 IPFS 服务实例"""
    global _ipfs_service
    if _ipfs_service is None:
        _ipfs_service = IPFSService()
    return _ipfs_service

