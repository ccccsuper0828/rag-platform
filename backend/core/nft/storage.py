"""
NFT 存储管理

使用统一数据库存储
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from .models import KnowledgeNFT, NFTStatus, NFTRarity, NFTMetadata, NFTPricing

# 导入统一数据库
from core.database import NftDB, get_connection


class NFTStorage:
    """NFT 数据存储管理器（使用统一数据库）"""
    
    def __init__(self, data_dir: str = "data"):
        # 保留参数兼容性
        pass
    
    def save_nft(self, nft: KnowledgeNFT) -> str:
        """保存 NFT 到数据库"""
        NftDB.create({
            "id": nft.id,
            "token_id": nft.token_id,
            "conversation_id": nft.conversation_id,
            "user_id": nft.user_id,
            "creator_id": nft.creator_id,
            "rag_id": nft.rag_id,
            "rarity": nft.rarity.value,
            "status": nft.status.value,
            "metadata": {
                "name": nft.metadata.name,
                "description": nft.metadata.description,
                "image": nft.metadata.image,
                "spark_value": nft.metadata.spark_value,
                "question": nft.metadata.question,
                "answer_preview": nft.metadata.answer_preview,
                "citations_count": nft.metadata.citations_count,
                "creator_id": nft.metadata.creator_id,
                "rag_id": nft.metadata.rag_id,
                "conversation_id": nft.metadata.conversation_id,
                "attributes": nft.metadata.attributes,
                "created_at": nft.metadata.created_at.isoformat()
            },
            "pricing": {
                "base_price": nft.pricing.base_price,
                "spark_multiplier": nft.pricing.spark_multiplier,
                "rarity_multiplier": nft.pricing.rarity_multiplier,
                "demand_multiplier": nft.pricing.demand_multiplier,
                "final_price": nft.pricing.final_price,
                "currency": nft.pricing.currency
            },
            "created_at": nft.created_at.isoformat(),
            "minted_at": nft.minted_at.isoformat() if nft.minted_at else None
        })
        return nft.id
    
    def get_nft(self, user_id: str, nft_id: str) -> Optional[KnowledgeNFT]:
        """获取 NFT"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM nfts WHERE id = ? AND user_id = ?
            """, (nft_id, user_id))
            row = cursor.fetchone()
            if row:
                return self._deserialize_nft(dict(row))
        return None
    
    def get_nft_by_conversation(self, conversation_id: str) -> Optional[KnowledgeNFT]:
        """通过对话 ID 获取 NFT"""
        data = NftDB.get_by_conversation(conversation_id)
        if data:
            return self._deserialize_nft(data)
        return None
    
    def get_user_nfts(self, user_id: str) -> List[KnowledgeNFT]:
        """获取用户所有 NFT"""
        nfts = NftDB.get_by_user(user_id)
        return [self._deserialize_nft(n) for n in nfts]
    
    def get_all_listed_nfts(self, limit: int = 50) -> List[KnowledgeNFT]:
        """获取所有已上架的 NFT"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM nfts WHERE status = 'listed'
                ORDER BY listed_price DESC
                LIMIT ?
            """, (limit,))
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data["metadata"] = json.loads(data.get("metadata") or "{}")
                data["pricing"] = json.loads(data.get("pricing") or "{}")
                results.append(self._deserialize_nft(data))
            return results
    
    def get_nft_stats(self) -> Dict[str, Any]:
        """获取 NFT 统计"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # 统计总数
            cursor.execute("SELECT COUNT(*) FROM nfts WHERE status IN ('minted', 'listed', 'sold')")
            total_minted = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM nfts WHERE status = 'listed'")
            total_listed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM nfts WHERE status = 'sold'")
            total_sold = cursor.fetchone()[0]
            
            # 按稀有度统计
            cursor.execute("SELECT rarity, COUNT(*) FROM nfts GROUP BY rarity")
            by_rarity = {"common": 0, "rare": 0, "epic": 0, "legendary": 0}
            for row in cursor.fetchall():
                if row[0] in by_rarity:
                    by_rarity[row[0]] = row[1]
            
            # 总价值
            cursor.execute("SELECT SUM(listed_price) FROM nfts WHERE status = 'listed'")
            total_value = cursor.fetchone()[0] or 0
            
            return {
                "total_minted": total_minted,
                "total_listed": total_listed,
                "total_sold": total_sold,
                "by_rarity": by_rarity,
                "total_value": total_value
            }
    
    def update_nft_status(self, user_id: str, nft_id: str, status: NFTStatus) -> bool:
        """更新 NFT 状态"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            minted_at = None
            if status == NFTStatus.MINTED:
                minted_at = datetime.now().isoformat()
            
            if minted_at:
                cursor.execute("""
                    UPDATE nfts SET status = ?, minted_at = ?
                    WHERE id = ? AND user_id = ?
                """, (status.value, minted_at, nft_id, user_id))
            else:
                cursor.execute("""
                    UPDATE nfts SET status = ?
                    WHERE id = ? AND user_id = ?
                """, (status.value, nft_id, user_id))
            
            return cursor.rowcount > 0
    
    def _deserialize_nft(self, data: Dict) -> KnowledgeNFT:
        """反序列化 NFT"""
        metadata_data = data.get("metadata", {})
        if isinstance(metadata_data, str):
            metadata_data = json.loads(metadata_data)
        
        pricing_data = data.get("pricing", {})
        if isinstance(pricing_data, str):
            pricing_data = json.loads(pricing_data)
        
        return KnowledgeNFT(
            id=data.get("id", ""),
            token_id=data.get("token_id", ""),
            contract_address=data.get("contract_address", ""),
            conversation_id=data.get("conversation_id", ""),
            user_id=data.get("user_id", ""),
            creator_id=data.get("creator_id", ""),
            rag_id=data.get("rag_id", ""),
            rarity=NFTRarity(data.get("rarity", "rare")),
            status=NFTStatus(data.get("status", "pending")),
            metadata=NFTMetadata(
                name=metadata_data.get("name", ""),
                description=metadata_data.get("description", ""),
                image=metadata_data.get("image", ""),
                spark_value=metadata_data.get("spark_value", 0),
                question=metadata_data.get("question", ""),
                answer_preview=metadata_data.get("answer_preview", ""),
                citations_count=metadata_data.get("citations_count", 0),
                creator_id=metadata_data.get("creator_id", ""),
                rag_id=metadata_data.get("rag_id", ""),
                conversation_id=metadata_data.get("conversation_id", ""),
                attributes=metadata_data.get("attributes", []),
                created_at=datetime.fromisoformat(metadata_data["created_at"]) if metadata_data.get("created_at") else datetime.now()
            ),
            metadata_uri=data.get("metadata_uri", ""),
            pricing=NFTPricing(
                base_price=pricing_data.get("base_price", 0),
                spark_multiplier=pricing_data.get("spark_multiplier", 1.0),
                rarity_multiplier=pricing_data.get("rarity_multiplier", 1.0),
                demand_multiplier=pricing_data.get("demand_multiplier", 1.0),
                final_price=pricing_data.get("final_price", 0),
                currency=pricing_data.get("currency", "SPARK")
            ),
            listed_price=data.get("listed_price"),
            transaction_history=data.get("transaction_history", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            minted_at=datetime.fromisoformat(data["minted_at"]) if data.get("minted_at") else None
        )


# 全局存储实例
nft_storage = NFTStorage()
