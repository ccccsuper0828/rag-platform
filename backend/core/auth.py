"""
用户认证和授权模块
支持 JWT token 认证和多租户隔离
"""
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# 导入数据库操作类
from core.database import UserDB

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天


class UserCreate(BaseModel):
    """用户注册请求"""
    username: str
    email: str  # 简化验证，接受任意格式
    password: str


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class User(BaseModel):
    """用户模型"""
    id: str
    username: str
    email: str
    password_hash: str
    created_at: str
    is_active: bool = True


class Token(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class UserManager:
    """用户管理类 - 使用 MySQL 数据库"""
    
    def __init__(self):
        pass  # 数据库在 database.py 中初始化
    
    def _hash_password(self, password: str) -> str:
        """加密密码"""
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def _generate_user_id(self) -> str:
        """生成用户ID"""
        return hashlib.sha256(f"{secrets.token_urlsafe(16)}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    
    def create_user(self, user_data: UserCreate) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        existing = UserDB.get_by_username(user_data.username)
        if existing:
            raise ValueError("用户名已存在")
        
        # 创建新用户
        user_id = self._generate_user_id()
        password_hash = self._hash_password(user_data.password)
        
        success = UserDB.create(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash
        )
        
        if not success:
            raise ValueError("用户创建失败")
        
        return User(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            created_at=datetime.now().isoformat(),
            is_active=True,
        )
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户身份"""
        user_data = UserDB.get_by_username(username)
        
        if user_data:
            if self._verify_password(password, user_data.get("password_hash", "")):
                return User(
                    id=user_data["id"],
                    username=user_data["username"],
                    email=user_data.get("email", ""),
                    password_hash=user_data["password_hash"],
                    created_at=str(user_data.get("created_at", "")),
                    is_active=bool(user_data.get("is_active", True))
                )
        
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        user_data = UserDB.get_by_id(user_id)
        if user_data:
            return User(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data.get("email", ""),
                password_hash=user_data["password_hash"],
                created_at=str(user_data.get("created_at", "")),
                is_active=bool(user_data.get("is_active", True))
            )
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        user_data = UserDB.get_by_username(username)
        if user_data:
            return User(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data.get("email", ""),
                password_hash=user_data["password_hash"],
                created_at=str(user_data.get("created_at", "")),
                is_active=bool(user_data.get("is_active", True))
            )
        return None


# 全局用户管理器实例
user_manager = UserManager()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证 JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# 统一的用户数据目录
USER_DATA_DIR = Path(os.getenv("USER_DATA_DIR", "user_data"))


def get_user_data_path(user_id: str) -> Path:
    """获取用户的根数据目录"""
    return USER_DATA_DIR / user_id


def get_user_workspace_path(user_id: str) -> Path:
    """获取用户的 workspace 路径（用于 RAG 工作空间）"""
    return get_user_data_path(user_id) / "workspaces"


def get_user_uploads_path(user_id: str) -> Path:
    """获取用户的上传文件路径"""
    return get_user_data_path(user_id) / "uploads"

