"""
NFT 数据模型

定义知识对话 NFT 的核心实体
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import hashlib


class NFTRarity(str, Enum):
    """NFT 稀有度等级"""
    COMMON = "common"       # 光源 50-69
    RARE = "rare"           # 光源 70-79 (NFT threshold)
    EPIC = "epic"           # 光源 80-89
    LEGENDARY = "legendary" # 光源 90-100


class NFTStatus(str, Enum):
    """NFT 状态"""
    PENDING = "pending"     # 待铸造
    MINTING = "minting"     # 铸造中
    MINTED = "minted"       # 已铸造
    LISTED = "listed"       # 已上架
    SOLD = "sold"           # 已售出
    BURNED = "burned"       # 已销毁


class NFTMetadata(BaseModel):
    """NFT 元数据（ERC-721 标准）"""
    name: str
    description: str
    image: str = ""                     # 生成的 NFT 图片 URL
    external_url: str = ""              # 外部链接
    
    # 标准属性
    attributes: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 自定义属性
    spark_value: float = 0              # 光源值
    question: str = ""                  # 问题
    answer_preview: str = ""            # 回答预览
    citations_count: int = 0            # 引用数量
    creator_id: str = ""                # 创建者 ID
    rag_id: str = ""                    # RAG ID
    conversation_id: str = ""           # 对话 ID
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为 ERC-721 标准格式"""
        return {
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "external_url": self.external_url,
            "attributes": self.attributes + [
                {"trait_type": "Spark Value", "value": self.spark_value},
                {"trait_type": "Citations", "value": self.citations_count},
                {"display_type": "date", "trait_type": "Created", "value": int(self.created_at.timestamp())}
            ]
        }


class NFTPricing(BaseModel):
    """NFT 定价模型"""
    base_price: float = 0               # 基础价格
    spark_multiplier: float = 1.0       # 光源值乘数
    rarity_multiplier: float = 1.0      # 稀有度乘数
    demand_multiplier: float = 1.0      # 需求乘数
    
    final_price: float = 0              # 最终价格
    currency: str = "SPARK"             # 货币单位（平台代币）
    
    @classmethod
    def calculate_price(cls, spark_value: float, like_count: int = 0, save_count: int = 0) -> "NFTPricing":
        """计算 NFT 价格"""
        pricing = cls()
        
        # 基础价格基于光源值
        if spark_value >= 90:
            pricing.base_price = 100
            pricing.rarity_multiplier = 3.0
        elif spark_value >= 80:
            pricing.base_price = 50
            pricing.rarity_multiplier = 2.0
        elif spark_value >= 70:
            pricing.base_price = 20
            pricing.rarity_multiplier = 1.5
        else:
            pricing.base_price = 10
            pricing.rarity_multiplier = 1.0
        
        # 光源值乘数
        pricing.spark_multiplier = spark_value / 70  # 以 70 为基准
        
        # 需求乘数（基于社交互动）
        demand_score = like_count + save_count * 2
        pricing.demand_multiplier = 1.0 + (demand_score * 0.05)  # 每个互动增加 5%
        
        # 计算最终价格
        pricing.final_price = round(
            pricing.base_price * 
            pricing.spark_multiplier * 
            pricing.rarity_multiplier * 
            pricing.demand_multiplier,
            2
        )
        
        return pricing


class KnowledgeNFT(BaseModel):
    """
    知识对话 NFT
    
    将高质量的 RAG 对话铸造为 NFT
    """
    # 基础标识
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token_id: str = ""                  # 链上 Token ID
    contract_address: str = ""          # 合约地址
    
    # 关联信息
    conversation_id: str                # 对话 ID
    user_id: str                        # 所有者 ID
    creator_id: str                     # 创建者 ID
    rag_id: str                         # RAG ID
    
    # NFT 属性
    rarity: NFTRarity = NFTRarity.RARE
    status: NFTStatus = NFTStatus.PENDING
    
    # 元数据
    metadata: NFTMetadata = Field(default_factory=NFTMetadata)
    metadata_uri: str = ""              # IPFS 元数据 URI
    
    # 定价
    pricing: NFTPricing = Field(default_factory=NFTPricing)
    listed_price: Optional[float] = None
    
    # 交易历史
    transaction_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    minted_at: Optional[datetime] = None
    
    @classmethod
    def from_conversation_spark(cls, spark_data: Dict[str, Any], user_id: str) -> "KnowledgeNFT":
        """从对话光源数据创建 NFT"""
        spark_value = spark_data.get("spark_value", 0)
        
        # 确定稀有度
        if spark_value >= 90:
            rarity = NFTRarity.LEGENDARY
        elif spark_value >= 80:
            rarity = NFTRarity.EPIC
        elif spark_value >= 70:
            rarity = NFTRarity.RARE
        else:
            rarity = NFTRarity.COMMON
        
        # 创建元数据
        question = spark_data.get("question", "")
        answer = spark_data.get("answer", "")
        
        metadata = NFTMetadata(
            name=f"Knowledge Spark #{spark_data.get('id', '')[:8]}",
            description=f"A high-quality knowledge conversation with {spark_value} spark value. Question: {question[:100]}...",
            spark_value=spark_value,
            question=question,
            answer_preview=answer[:200] if answer else "",
            citations_count=spark_data.get("citations_count", 0),
            creator_id=user_id,
            rag_id=spark_data.get("rag_id", ""),
            conversation_id=spark_data.get("conversation_id", ""),
            attributes=[
                {"trait_type": "Rarity", "value": rarity.value},
                {"trait_type": "Spark Value", "value": spark_value},
                {"trait_type": "Base Score", "value": spark_data.get("base_score", 0)},
                {"trait_type": "Citation Score", "value": spark_data.get("citation_score", 0)},
                {"trait_type": "Activation Score", "value": spark_data.get("activation_score", 0)},
                {"trait_type": "Behavior Score", "value": spark_data.get("behavior_score", 0)},
            ]
        )
        
        # 计算定价
        pricing = NFTPricing.calculate_price(
            spark_value,
            spark_data.get("like_count", 0),
            spark_data.get("save_count", 0)
        )
        
        return cls(
            conversation_id=spark_data.get("conversation_id", ""),
            user_id=user_id,
            creator_id=user_id,
            rag_id=spark_data.get("rag_id", ""),
            rarity=rarity,
            metadata=metadata,
            pricing=pricing
        )
    
    def generate_token_id(self) -> str:
        """生成唯一的 Token ID"""
        unique_string = f"{self.conversation_id}:{self.user_id}:{self.created_at.isoformat()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "token_id": self.token_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "creator_id": self.creator_id,
            "rag_id": self.rag_id,
            "rarity": self.rarity.value,
            "status": self.status.value,
            "metadata": self.metadata.to_dict(),
            "metadata_uri": self.metadata_uri,
            "pricing": {
                "base_price": self.pricing.base_price,
                "final_price": self.pricing.final_price,
                "currency": self.pricing.currency
            },
            "listed_price": self.listed_price,
            "created_at": self.created_at.isoformat(),
            "minted_at": self.minted_at.isoformat() if self.minted_at else None
        }


# API 请求模型
class MintNFTRequest(BaseModel):
    """铸造 NFT 请求"""
    conversation_id: str


class ListNFTRequest(BaseModel):
    """上架 NFT 请求"""
    nft_id: str
    price: float

