"""
激励系统 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from ..middleware import get_current_user
from .models import RewardStatus, RewardType
from .engine import reward_engine

rewards_router = APIRouter(prefix="/rewards", tags=["Rewards"])


@rewards_router.get("/summary")
async def get_rewards_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    获取奖励汇总
    """
    user_id = current_user["user_id"]
    
    summary = reward_engine.get_user_summary(user_id)
    
    return {
        "success": True,
        "data": summary.to_dict()
    }


@rewards_router.get("/pending")
async def get_pending_rewards(
    current_user: dict = Depends(get_current_user)
):
    """
    获取待领取的奖励
    """
    user_id = current_user["user_id"]
    
    rewards = reward_engine.get_user_rewards(user_id, RewardStatus.PENDING)
    total = sum(r.amount for r in rewards)
    
    return {
        "success": True,
        "count": len(rewards),
        "total_pending": round(total, 2),
        "data": [r.to_dict() for r in rewards]
    }


@rewards_router.get("/history")
async def get_reward_history(
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    获取奖励历史
    """
    user_id = current_user["user_id"]
    
    status_filter = RewardStatus(status) if status else None
    rewards = reward_engine.get_user_rewards(user_id, status_filter)
    
    return {
        "success": True,
        "count": len(rewards),
        "data": [r.to_dict() for r in rewards[:limit]]
    }


@rewards_router.post("/claim/{reward_id}")
async def claim_reward(
    reward_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    领取单个奖励
    """
    user_id = current_user["user_id"]
    
    success = reward_engine.claim_reward(user_id, reward_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="无法领取此奖励")
    
    return {
        "success": True,
        "message": "奖励领取成功！"
    }


@rewards_router.post("/claim-all")
async def claim_all_rewards(
    current_user: dict = Depends(get_current_user)
):
    """
    一键领取所有待领取的奖励
    """
    user_id = current_user["user_id"]
    
    result = reward_engine.claim_all_rewards(user_id)
    
    return {
        "success": True,
        "message": f"成功领取 {result['claimed']} 个奖励",
        "data": result
    }


@rewards_router.get("/stats")
async def get_reward_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    获取奖励统计
    """
    user_id = current_user["user_id"]
    
    summary = reward_engine.get_user_summary(user_id)
    
    return {
        "success": True,
        "data": {
            "total_earned": summary.total_earned,
            "total_pending": summary.total_pending,
            "total_claimed": summary.total_claimed,
            "by_type": summary.by_type
        }
    }

