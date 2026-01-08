"""
光源算法数据模型

定义光源系统中的核心实体：
- ConversationSpark: 对话光源记录
- KnowledgeNodeSpark: 知识节点光源贡献
- UserSparkProfile: 用户光源档案
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class SparkConfig:
    """光源算法配置"""
    
    # 各维度权重
    WEIGHT_BASE_QUALITY = 0.30      # 基础质量分权重
    WEIGHT_CITATION = 0.25          # 引用关系分权重
    WEIGHT_ACTIVATION = 0.20        # 知识激活度权重
    WEIGHT_BEHAVIOR = 0.25          # 用户行为分权重
    
    # 各维度最高分
    MAX_BASE_SCORE = 30             # 基础质量分上限
    MAX_CITATION_SCORE = 25         # 引用关系分上限
    MAX_ACTIVATION_SCORE = 20       # 知识激活度上限
    MAX_BEHAVIOR_SCORE = 25         # 用户行为分上限
    
    # NFT 相关配置
    NFT_ELIGIBILITY_THRESHOLD = 70  # NFT 铸造资格阈值
    NFT_MIN_STABLE_PERIODS = 3      # 最少稳定周期数
    NFT_STABILITY_RATIO = 0.8       # 稳定性阈值比例
    
    # 行为分数配置
    LIKE_SCORE = 1.0                # 每个点赞的分数
    SAVE_SCORE = 2.0                # 每个收藏的分数
    SHARE_SCORE = 2.5               # 每次分享的分数
    REUSE_SCORE = 2.5               # 每次被复用的分数
    
    # 声誉等级阈值
    REPUTATION_LEVELS = {
        1: 0,
        2: 100,
        3: 300,
        4: 600,
        5: 1000,
        6: 2000,
        7: 4000,
        8: 8000,
        9: 15000,
        10: 30000
    }


class SparkSnapshot(BaseModel):
    """光源值快照 - 记录某个时刻的光源值及其组成"""
    timestamp: datetime = Field(default_factory=datetime.now)
    spark_value: float = 0
    base_score: float = 0
    citation_score: float = 0
    activation_score: float = 0
    behavior_score: float = 0
    trigger: str = "system"  # 触发更新的原因: system, like, save, share, reuse


class Citation(BaseModel):
    """引用记录"""
    node_id: str                    # 知识节点 ID
    content_preview: str = ""       # 内容预览
    relevance_score: float = 0      # 相关性得分
    source_file: str = ""           # 来源文件


class ConversationSpark(BaseModel):
    """
    对话光源记录
    
    核心实体，记录每次 RAG 对话的光源值及相关信息
    """
    # 基础标识
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rag_id: str
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # 对话内容
    question: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    
    # 分项分数 (0-各自上限)
    base_score: float = 0           # 基础质量分 (0-30)
    citation_score: float = 0       # 引用关系分 (0-25)
    activation_score: float = 0     # 知识激活度 (0-20)
    behavior_score: float = 0       # 用户行为分 (0-25)
    
    # 综合光源值 (0-100)
    spark_value: float = 0
    
    # 光源值历史 (用于判断稳定性)
    spark_history: List[SparkSnapshot] = Field(default_factory=list)
    
    # 用户行为统计
    like_count: int = 0
    save_count: int = 0
    share_count: int = 0
    reuse_count: int = 0
    
    # NFT 状态
    nft_eligible: bool = False
    nft_minted: bool = False
    nft_token_id: Optional[str] = None
    nft_minted_at: Optional[datetime] = None
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def calculate_spark_value(self) -> float:
        """计算综合光源值"""
        config = SparkConfig
        
        value = (
            self.base_score * config.WEIGHT_BASE_QUALITY +
            self.citation_score * config.WEIGHT_CITATION +
            self.activation_score * config.WEIGHT_ACTIVATION +
            self.behavior_score * config.WEIGHT_BEHAVIOR
        )
        
        # 归一化到 0-100
        max_possible = (
            config.MAX_BASE_SCORE * config.WEIGHT_BASE_QUALITY +
            config.MAX_CITATION_SCORE * config.WEIGHT_CITATION +
            config.MAX_ACTIVATION_SCORE * config.WEIGHT_ACTIVATION +
            config.MAX_BEHAVIOR_SCORE * config.WEIGHT_BEHAVIOR
        )
        
        normalized = (value / max_possible) * 100 if max_possible > 0 else 0
        return min(round(normalized, 2), 100)
    
    def check_nft_eligibility(self) -> bool:
        """检查是否有资格铸造 NFT"""
        config = SparkConfig
        
        # 条件1: 当前光源值达到阈值
        if self.spark_value < config.NFT_ELIGIBILITY_THRESHOLD:
            return False
        
        # 条件2: 光源值稳定（不是暂时飙升）
        if len(self.spark_history) >= config.NFT_MIN_STABLE_PERIODS:
            recent = self.spark_history[-config.NFT_MIN_STABLE_PERIODS:]
            avg = sum(s.spark_value for s in recent) / len(recent)
            threshold = config.NFT_ELIGIBILITY_THRESHOLD * config.NFT_STABILITY_RATIO
            if avg < threshold:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "rag_id": self.rag_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "question": self.question,
            "answer": self.answer[:200] + "..." if len(self.answer) > 200 else self.answer,
            "citations_count": len(self.citations),
            "base_score": self.base_score,
            "citation_score": self.citation_score,
            "activation_score": self.activation_score,
            "behavior_score": self.behavior_score,
            "spark_value": self.spark_value,
            "like_count": self.like_count,
            "save_count": self.save_count,
            "share_count": self.share_count,
            "reuse_count": self.reuse_count,
            "nft_eligible": self.nft_eligible,
            "nft_minted": self.nft_minted,
            "nft_token_id": self.nft_token_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class KnowledgeNodeSpark(BaseModel):
    """
    知识节点光源贡献
    
    记录每个知识片段（chunk）对光源系统的贡献
    """
    # 基础标识
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str                    # 知识节点 ID（通常是 content hash）
    rag_id: str
    
    # 内容信息
    content_preview: str = ""       # 内容预览（前100字符）
    source_file: str = ""           # 来源文件
    
    # 被引用统计
    total_citations: int = 0        # 被引用总次数
    high_spark_citations: int = 0   # 被高光源对话引用次数（光源≥70）
    
    # 贡献的光源
    contributed_spark: float = 0    # 贡献的光源总量
    
    # 节点价值
    node_value: float = 0           # 节点价值评分 (0-100)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def calculate_node_value(self) -> float:
        """计算节点价值"""
        import math
        
        # 基于被引用次数和高光源引用次数计算
        citation_value = math.log(self.total_citations + 1) * 10
        high_spark_value = self.high_spark_citations * 5
        contribution_value = math.log(self.contributed_spark + 1) * 5
        
        value = citation_value + high_spark_value + contribution_value
        return min(round(value, 2), 100)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "node_id": self.node_id,
            "rag_id": self.rag_id,
            "content_preview": self.content_preview,
            "source_file": self.source_file,
            "total_citations": self.total_citations,
            "high_spark_citations": self.high_spark_citations,
            "contributed_spark": self.contributed_spark,
            "node_value": self.node_value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class UserSparkProfile(BaseModel):
    """
    用户光源档案
    
    记录用户的累计光源值、声誉等级等信息
    """
    # 基础标识
    user_id: str
    
    # 累计光源
    total_spark: float = 0          # 累计光源值
    average_spark: float = 0        # 平均光源值
    
    # 对话统计
    total_conversations: int = 0
    high_spark_conversations: int = 0  # 高光源对话数（≥70）
    
    # 知识贡献
    knowledge_nodes_created: int = 0    # 创建的知识节点数
    knowledge_citations_received: int = 0  # 知识被引用次数
    
    # 声誉系统
    reputation_level: int = 1       # 声誉等级 (1-10)
    reputation_score: float = 0     # 声誉积分
    
    # NFT 统计
    nft_count: int = 0              # 拥有的 NFT 数量
    nft_total_value: float = 0      # NFT 总价值
    
    # 激励统计
    rewards_earned: float = 0       # 累计获得的奖励
    rewards_pending: float = 0      # 待领取的奖励
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def calculate_reputation_level(self) -> int:
        """计算声誉等级"""
        levels = SparkConfig.REPUTATION_LEVELS
        current_level = 1
        
        for level, threshold in sorted(levels.items()):
            if self.total_spark >= threshold:
                current_level = level
            else:
                break
        
        return current_level
    
    def update_stats(self, conversations: List[ConversationSpark]):
        """更新统计信息"""
        self.total_conversations = len(conversations)
        self.total_spark = sum(c.spark_value for c in conversations)
        self.average_spark = self.total_spark / len(conversations) if conversations else 0
        self.high_spark_conversations = sum(
            1 for c in conversations 
            if c.spark_value >= SparkConfig.NFT_ELIGIBILITY_THRESHOLD
        )
        self.nft_count = sum(1 for c in conversations if c.nft_minted)
        self.reputation_level = self.calculate_reputation_level()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "total_spark": round(self.total_spark, 2),
            "average_spark": round(self.average_spark, 2),
            "total_conversations": self.total_conversations,
            "high_spark_conversations": self.high_spark_conversations,
            "knowledge_nodes_created": self.knowledge_nodes_created,
            "knowledge_citations_received": self.knowledge_citations_received,
            "reputation_level": self.reputation_level,
            "reputation_score": round(self.reputation_score, 2),
            "nft_count": self.nft_count,
            "nft_total_value": round(self.nft_total_value, 2),
            "rewards_earned": round(self.rewards_earned, 2),
            "rewards_pending": round(self.rewards_pending, 2),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# API 请求/响应模型
class SparkCalculateRequest(BaseModel):
    """计算光源值请求"""
    rag_id: str
    question: str
    answer: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)


class SparkActionRequest(BaseModel):
    """光源行为请求（点赞/收藏/分享）"""
    conversation_id: str


class SparkLeaderboardResponse(BaseModel):
    """排行榜响应"""
    rank: int
    user_id: str
    username: str
    total_spark: float
    high_spark_conversations: int
    reputation_level: int
