"""
激励分配引擎

计算和分配用户奖励
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from .models import (
    RewardRecord,
    RewardPool,
    RewardType,
    RewardStatus,
    UserRewardSummary
)


class RewardEngine:
    """
    激励分配引擎
    
    核心功能：
    1. 计算用户应得的奖励
    2. 分配和记录奖励
    3. 管理奖励池
    """
    
    # 奖励配置
    REWARD_RATES = {
        RewardType.HIGH_SPARK_CONVERSATION: {
            "base": 5.0,                    # 基础奖励
            "spark_multiplier": 0.1,        # 每点光源额外奖励
            "threshold": 70                 # 光源阈值
        },
        RewardType.NFT_MINT: {
            "base": 10.0,                   # 铸造 NFT 奖励
            "rarity_bonus": {
                "rare": 5.0,
                "epic": 15.0,
                "legendary": 30.0
            }
        },
        RewardType.CITATION_CONTRIBUTION: {
            "per_citation": 0.5,            # 每次被引用奖励
            "high_spark_bonus": 1.0         # 被高光对话引用额外奖励
        },
        RewardType.DAILY_CHECK_IN: {
            "base": 1.0,
            "streak_bonus": 0.5,            # 连续签到加成
            "max_streak_bonus": 5.0         # 最大连续签到加成
        },
        RewardType.LEADERBOARD: {
            "daily_top_10": [50, 30, 20, 10, 8, 6, 5, 4, 3, 2],
            "weekly_top_10": [200, 150, 100, 80, 60, 50, 40, 30, 20, 10]
        },
        RewardType.ACHIEVEMENT: {
            "first_conversation": 5.0,
            "first_nft": 20.0,
            "spark_100": 10.0,
            "spark_500": 30.0,
            "spark_1000": 50.0
        }
    }
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.rewards_file = self.data_dir / "rewards.json"
        self.pools_file = self.data_dir / "reward_pools.json"
        
        self._init_files()
    
    def _init_files(self):
        """初始化数据文件"""
        for file_path in [self.rewards_file, self.pools_file]:
            if not file_path.exists():
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f)
    
    def _load_json(self, file_path: Path) -> Dict:
        """加载 JSON 文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_json(self, file_path: Path, data: Dict):
        """保存 JSON 文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    # ==================== 奖励计算 ====================
    
    def calculate_conversation_reward(
        self, 
        spark_value: float,
        citations_count: int = 0
    ) -> float:
        """计算对话奖励"""
        config = self.REWARD_RATES[RewardType.HIGH_SPARK_CONVERSATION]
        
        if spark_value < config["threshold"]:
            return 0
        
        base = config["base"]
        spark_bonus = (spark_value - config["threshold"]) * config["spark_multiplier"]
        
        return round(base + spark_bonus, 2)
    
    def calculate_nft_reward(self, rarity: str) -> float:
        """计算 NFT 铸造奖励"""
        config = self.REWARD_RATES[RewardType.NFT_MINT]
        
        base = config["base"]
        rarity_bonus = config["rarity_bonus"].get(rarity, 0)
        
        return round(base + rarity_bonus, 2)
    
    def calculate_citation_reward(
        self, 
        citation_count: int,
        high_spark_count: int = 0
    ) -> float:
        """计算引用贡献奖励"""
        config = self.REWARD_RATES[RewardType.CITATION_CONTRIBUTION]
        
        base = citation_count * config["per_citation"]
        high_spark_bonus = high_spark_count * config["high_spark_bonus"]
        
        return round(base + high_spark_bonus, 2)
    
    # ==================== 奖励发放 ====================
    
    def create_reward(
        self,
        user_id: str,
        reward_type: RewardType,
        amount: float,
        reference_id: str = "",
        description: str = "",
        expires_days: Optional[int] = None
    ) -> RewardRecord:
        """创建奖励记录"""
        reward = RewardRecord(
            user_id=user_id,
            reward_type=reward_type,
            amount=amount,
            reference_id=reference_id,
            description=description,
            expires_at=datetime.now() + timedelta(days=expires_days) if expires_days else None
        )
        
        self._save_reward(reward)
        return reward
    
    def claim_reward(self, user_id: str, reward_id: str) -> bool:
        """领取奖励"""
        data = self._load_json(self.rewards_file)
        
        if user_id not in data or reward_id not in data[user_id]:
            return False
        
        reward_data = data[user_id][reward_id]
        
        # 检查状态
        if reward_data["status"] != RewardStatus.PENDING.value:
            return False
        
        # 检查是否过期
        if reward_data.get("expires_at"):
            expires_at = datetime.fromisoformat(reward_data["expires_at"])
            if datetime.now() > expires_at:
                data[user_id][reward_id]["status"] = RewardStatus.EXPIRED.value
                self._save_json(self.rewards_file, data)
                return False
        
        # 更新状态
        data[user_id][reward_id]["status"] = RewardStatus.CLAIMED.value
        data[user_id][reward_id]["claimed_at"] = datetime.now().isoformat()
        
        self._save_json(self.rewards_file, data)
        return True
    
    def claim_all_rewards(self, user_id: str) -> Dict[str, Any]:
        """领取所有待领取的奖励"""
        data = self._load_json(self.rewards_file)
        
        if user_id not in data:
            return {"claimed": 0, "amount": 0}
        
        claimed_count = 0
        total_amount = 0
        
        for reward_id, reward_data in data[user_id].items():
            if reward_data["status"] == RewardStatus.PENDING.value:
                # 检查是否过期
                if reward_data.get("expires_at"):
                    expires_at = datetime.fromisoformat(reward_data["expires_at"])
                    if datetime.now() > expires_at:
                        data[user_id][reward_id]["status"] = RewardStatus.EXPIRED.value
                        continue
                
                data[user_id][reward_id]["status"] = RewardStatus.CLAIMED.value
                data[user_id][reward_id]["claimed_at"] = datetime.now().isoformat()
                claimed_count += 1
                total_amount += reward_data["amount"]
        
        self._save_json(self.rewards_file, data)
        
        return {
            "claimed": claimed_count,
            "amount": round(total_amount, 2)
        }
    
    def _save_reward(self, reward: RewardRecord):
        """保存奖励记录"""
        data = self._load_json(self.rewards_file)
        
        if reward.user_id not in data:
            data[reward.user_id] = {}
        
        data[reward.user_id][reward.id] = reward.to_dict()
        self._save_json(self.rewards_file, data)
    
    # ==================== 奖励查询 ====================
    
    def get_user_rewards(
        self, 
        user_id: str,
        status: Optional[RewardStatus] = None
    ) -> List[RewardRecord]:
        """获取用户奖励列表"""
        data = self._load_json(self.rewards_file)
        
        if user_id not in data:
            return []
        
        rewards = []
        for reward_data in data[user_id].values():
            if status and reward_data["status"] != status.value:
                continue
            rewards.append(self._deserialize_reward(reward_data))
        
        # 按时间排序
        rewards.sort(key=lambda x: x.created_at, reverse=True)
        return rewards
    
    def get_user_summary(self, user_id: str) -> UserRewardSummary:
        """获取用户奖励汇总"""
        rewards = self.get_user_rewards(user_id)
        
        summary = UserRewardSummary(user_id=user_id)
        
        for reward in rewards:
            summary.total_earned += reward.amount
            
            if reward.status == RewardStatus.PENDING:
                summary.total_pending += reward.amount
            elif reward.status == RewardStatus.CLAIMED:
                summary.total_claimed += reward.amount
            
            # 按类型统计
            type_key = reward.reward_type.value
            if type_key not in summary.by_type:
                summary.by_type[type_key] = 0
            summary.by_type[type_key] += reward.amount
        
        summary.recent_rewards = rewards[:10]
        
        return summary
    
    def get_pending_amount(self, user_id: str) -> float:
        """获取待领取金额"""
        rewards = self.get_user_rewards(user_id, RewardStatus.PENDING)
        return sum(r.amount for r in rewards)
    
    def _deserialize_reward(self, data: Dict) -> RewardRecord:
        """反序列化奖励记录"""
        return RewardRecord(
            id=data.get("id", ""),
            user_id=data.get("user_id", ""),
            reward_type=RewardType(data.get("reward_type", "spark_bonus")),
            amount=data.get("amount", 0),
            currency=data.get("currency", "SPARK"),
            status=RewardStatus(data.get("status", "pending")),
            reference_id=data.get("reference_id", ""),
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            claimed_at=datetime.fromisoformat(data["claimed_at"]) if data.get("claimed_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )
    
    # ==================== 自动奖励 ====================
    
    def award_high_spark_conversation(
        self, 
        user_id: str,
        conversation_id: str,
        spark_value: float
    ) -> Optional[RewardRecord]:
        """为高光对话发放奖励"""
        amount = self.calculate_conversation_reward(spark_value)
        
        if amount <= 0:
            return None
        
        return self.create_reward(
            user_id=user_id,
            reward_type=RewardType.HIGH_SPARK_CONVERSATION,
            amount=amount,
            reference_id=conversation_id,
            description=f"高光对话奖励 (光源值: {spark_value})"
        )
    
    def award_nft_mint(
        self,
        user_id: str,
        nft_id: str,
        rarity: str
    ) -> RewardRecord:
        """为 NFT 铸造发放奖励"""
        amount = self.calculate_nft_reward(rarity)
        
        return self.create_reward(
            user_id=user_id,
            reward_type=RewardType.NFT_MINT,
            amount=amount,
            reference_id=nft_id,
            description=f"NFT 铸造奖励 ({rarity} 稀有度)"
        )


# 全局引擎实例
reward_engine = RewardEngine()

