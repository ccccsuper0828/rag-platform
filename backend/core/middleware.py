"""
认证中间件和依赖注入
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from core.auth import verify_token, user_manager, get_user_workspace_path
from pathlib import Path

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    从 JWT token 中获取当前用户
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token中缺少用户信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = user_manager.get_user_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
    }


def get_user_workspace(user: dict = Depends(get_current_user)) -> Path:
    """
    获取当前用户的 workspace 路径
    确保不同用户的数据完全隔离
    """
    workspace = get_user_workspace_path(user["user_id"])
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    可选的认证（用于某些公开接口）
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        return None
    
    user_id: str = payload.get("sub")
    if user_id is None:
        return None
    
    user = user_manager.get_user_by_id(user_id)
    if user is None or not user.is_active:
        return None
    
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
    }

