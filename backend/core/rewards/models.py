"""
激励系统数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class RewardType(str, Enum):
    """奖励类型"""
    SPARK_BONUS = "spark_bonus"         # 光源值奖励
    DAILY_CHECK_IN = "daily_check_in"   # 每日签到
    HIGH_SPARK_CONVERSATION = "high_spark_conversation"  # 高光对话
    NFT_MINT = "nft_mint"               # NFT 铸造奖励
    CITATION_CONTRIBUTION = "citation_contribution"  # 引用贡献
    REFERRAL = "referral"               # 推荐奖励
    ACHIEVEMENT = "achievement"         # 成就奖励
    LEADERBOARD = "leaderboard"         # 排行榜奖励


class RewardStatus(str, Enum):
    """奖励状态"""
    PENDING = "pending"     # 待发放
    CLAIMED = "claimed"     # 已领取
    EXPIRED = "expired"     # 已过期


class RewardRecord(BaseModel):
    """
    奖励记录
    
    记录每一次奖励的详细信息
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # 奖励信息
    reward_type: RewardType
    amount: float
    currency: str = "SPARK"
    
    # 状态
    status: RewardStatus = RewardStatus.PENDING
    
    # 关联信息
    reference_id: str = ""      # 关联的对话/NFT/etc ID
    description: str = ""       # 奖励描述
    
    # 时间
    created_at: datetime = Field(default_factory=datetime.now)
    claimed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "reward_type": self.reward_type.value,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "reference_id": self.reference_id,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class RewardPool(BaseModel):
    """
    奖励池
    
    管理奖励资金池的分配
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    
    # 资金
    total_amount: float = 0
    distributed_amount: float = 0
    remaining_amount: float = 0
    
    # 分配规则
    distribution_rules: Dict[str, Any] = Field(default_factory=dict)
    
    # 时间
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    
    # 状态
    is_active: bool = True
    
    def calculate_remaining(self) -> float:
        """计算剩余金额"""
        self.remaining_amount = self.total_amount - self.distributed_amount
        return self.remaining_amount
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "total_amount": self.total_amount,
            "distributed_amount": self.distributed_amount,
            "remaining_amount": self.remaining_amount,
            "is_active": self.is_active,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None
        }


class UserRewardSummary(BaseModel):
    """用户奖励汇总"""
    user_id: str
    total_earned: float = 0
    total_pending: float = 0
    total_claimed: float = 0
    
    # 各类型奖励统计
    by_type: Dict[str, float] = Field(default_factory=dict)
    
    # 最近奖励
    recent_rewards: List[RewardRecord] = Field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "total_earned": self.total_earned,
            "total_pending": self.total_pending,
            "total_claimed": self.total_claimed,
            "by_type": self.by_type,
            "recent_rewards": [r.to_dict() for r in self.recent_rewards[-10:]]
        }

