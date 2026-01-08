"""
Memory 记忆系统
借鉴 Khoj 的实现，提供跨对话的长期记忆能力

核心特性：
1. 自动记忆提取：从对话中自动提取重要信息
2. 语义记忆检索：根据当前对话上下文检索相关记忆
3. 记忆衰减：旧记忆逐渐降低权重
4. 用户画像更新：根据记忆动态更新用户画像

存储说明：
- 使用统一数据库存储（支持 SQLite 开发 / PostgreSQL 生产）
- 每个用户的记忆完全隔离
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from functools import lru_cache

# 导入统一数据库
from core.database import MemoryDB, get_connection

# 配置
MAX_MEMORIES_PER_USER = int(os.getenv("MAX_MEMORIES_PER_USER", "1000"))
MEMORY_DECAY_DAYS = int(os.getenv("MEMORY_DECAY_DAYS", "30"))
AUTO_EXTRACT_MEMORIES = os.getenv("AUTO_EXTRACT_MEMORIES", "true").lower() == "true"


@dataclass
class Memory:
    """记忆对象"""
    id: str
    user_id: str
    text: str
    source: str  # "manual", "auto", "conversation"
    importance: float  # 0.0 - 1.0
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "source": self.source,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            text=data["text"],
            source=data["source"],
            importance=data["importance"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data.get("access_count", 0),
            metadata=data.get("metadata", {}),
        )


class MemoryStore:
    """
    记忆存储管理（使用统一数据库）
    
    支持：
    - CRUD 操作
    - 语义搜索（需要配合 LEANN）
    - 记忆衰减
    - 导入导出
    
    多租户隔离：每个用户只能访问自己的记忆
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def add(self, text: str, source: str = "manual", importance: float = 0.5, metadata: Optional[Dict] = None) -> Memory:
        """添加记忆（存储到统一数据库）"""
        # 使用统一数据库
        result = MemoryDB.add(
            user_id=self.user_id,
            text=text,
            source=source,
            importance=min(max(importance, 0.0), 1.0)
        )
        
        memory = Memory(
            id=result["id"],
            user_id=self.user_id,
            text=text,
            source=source,
            importance=importance,
            created_at=datetime.fromisoformat(result["created_at"]),
            last_accessed=datetime.fromisoformat(result["created_at"]),
            access_count=0,
            metadata=metadata or {},
        )
        
        # 检查是否超过限制
        self._enforce_limit()
        
        return memory
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """获取单条记忆"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM memories WHERE id = ? AND user_id = ?", 
                (memory_id, self.user_id)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_memory(dict(row))
        return None
    
    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        source: Optional[str] = None,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """列出记忆"""
        memories_data = MemoryDB.get_by_user(self.user_id, limit=limit)
        
        # 过滤
        result = []
        for data in memories_data:
            if data.get("importance", 0) >= min_importance:
                if source is None or data.get("source") == source:
                    result.append(self._row_to_memory(data))
        
        return result[:limit]
    
    def search(self, query: str, top_k: int = 10) -> List[Memory]:
        """搜索相关记忆"""
        results = MemoryDB.search(self.user_id, query, limit=top_k)
        memories = [self._row_to_memory(data) for data in results]
        
        # 更新访问时间
        for m in memories:
            self._update_access(m.id)
        
        return memories
    
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        return MemoryDB.delete(self.user_id, memory_id)
    
    def update_importance(self, memory_id: str, importance: float):
        """更新记忆重要性"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE memories SET importance = ? WHERE id = ? AND user_id = ?",
                (min(max(importance, 0.0), 1.0), memory_id, self.user_id)
            )
    
    def decay_old_memories(self):
        """衰减旧记忆的重要性"""
        cutoff_date = (datetime.now() - timedelta(days=MEMORY_DECAY_DAYS)).isoformat()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories 
                SET importance = importance * 0.9
                WHERE user_id = ? 
                  AND last_accessed < ?
                  AND importance > 0.1
            """, (self.user_id, cutoff_date))
            
            affected = cursor.rowcount
        
        if affected > 0:
            print(f"🧠 Decayed {affected} old memories for user {self.user_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(importance) as avg_importance,
                    SUM(access_count) as total_accesses
                FROM memories WHERE user_id = ?
            """, (self.user_id,))
            
            row = cursor.fetchone()
        
        return {
            "total_memories": row[0] or 0,
            "avg_importance": round(row[1] or 0, 2),
            "total_accesses": row[2] or 0,
        }
    
    def export_all(self) -> List[Dict[str, Any]]:
        """导出所有记忆"""
        memories = self.list(limit=MAX_MEMORIES_PER_USER)
        return [m.to_dict() for m in memories]
    
    def import_memories(self, memories_data: List[Dict[str, Any]]):
        """导入记忆"""
        for data in memories_data:
            self.add(
                text=data["text"],
                source=data.get("source", "import"),
                importance=data.get("importance", 0.5),
                metadata=data.get("metadata", {}),
            )
    
    def _row_to_memory(self, data: Dict) -> Memory:
        """将数据库行转换为 Memory 对象"""
        created_at = data.get("created_at", datetime.now().isoformat())
        last_accessed = data.get("last_accessed", created_at)
        
        # 处理日期格式
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(last_accessed, str):
            last_accessed = datetime.fromisoformat(last_accessed)
        
        return Memory(
            id=data.get("id", ""),
            user_id=data.get("user_id", self.user_id),
            text=data.get("text", ""),
            source=data.get("source", "manual"),
            importance=data.get("importance", 0.5),
            created_at=created_at,
            last_accessed=last_accessed,
            access_count=data.get("access_count", 0),
            metadata=json.loads(data.get("metadata", "{}")) if isinstance(data.get("metadata"), str) else data.get("metadata", {}),
        )
    
    def _update_access(self, memory_id: str):
        """更新记忆访问信息"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories 
                SET last_accessed = ?, access_count = access_count + 1
                WHERE id = ? AND user_id = ?
            """, (datetime.now().isoformat(), memory_id, self.user_id))
    
    def _enforce_limit(self):
        """强制执行记忆数量限制"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memories WHERE user_id = ?", (self.user_id,))
            count = cursor.fetchone()[0]
            
            if count > MAX_MEMORIES_PER_USER:
                # 删除最不重要的记忆
                cursor.execute("""
                    DELETE FROM memories 
                    WHERE id IN (
                        SELECT id FROM memories 
                        WHERE user_id = ?
                        ORDER BY importance ASC, last_accessed ASC
                        LIMIT ?
                    )
                """, (self.user_id, count - MAX_MEMORIES_PER_USER))
                
                deleted = cursor.rowcount
                print(f"🧹 Cleaned {deleted} old memories to enforce limit")


class MemoryExtractor:
    """
    自动记忆提取器
    
    从对话中自动提取值得记住的信息
    """
    
    # 触发记忆提取的关键词
    IMPORTANCE_KEYWORDS = [
        "记住", "重要", "关键", "注意", "不要忘记", "提醒我",
        "我喜欢", "我不喜欢", "我的", "我是", "我想要",
        "偏好", "习惯", "经常", "总是", "从不",
    ]
    
    @classmethod
    def should_extract(cls, text: str) -> bool:
        """判断是否应该提取记忆"""
        if not AUTO_EXTRACT_MEMORIES:
            return False
        
        text_lower = text.lower()
        return any(kw in text_lower for kw in cls.IMPORTANCE_KEYWORDS)
    
    @classmethod
    def extract_importance(cls, text: str) -> float:
        """根据内容判断记忆重要性"""
        text_lower = text.lower()
        importance = 0.3  # 基础重要性
        
        # 根据关键词调整重要性
        high_importance_words = ["重要", "关键", "不要忘记", "必须"]
        medium_importance_words = ["记住", "提醒我", "注意"]
        
        for word in high_importance_words:
            if word in text_lower:
                importance += 0.3
        
        for word in medium_importance_words:
            if word in text_lower:
                importance += 0.15
        
        # 根据长度调整（太短的可能不重要）
        if len(text) > 100:
            importance += 0.1
        
        return min(importance, 1.0)
    
    @classmethod
    def extract_from_conversation(
        cls,
        user_message: str,
        ai_response: str,
        memory_store: MemoryStore,
    ) -> Optional[Memory]:
        """从对话中提取记忆"""
        if not cls.should_extract(user_message):
            return None
        
        # 提取用户陈述中的关键信息
        importance = cls.extract_importance(user_message)
        
        # 创建记忆
        memory = memory_store.add(
            text=user_message[:500],  # 限制长度
            source="conversation",
            importance=importance,
            metadata={
                "ai_response_preview": ai_response[:200] if ai_response else "",
                "extracted_at": datetime.now().isoformat(),
            }
        )
        
        print(f"🧠 Auto-extracted memory (importance={importance:.2f}): {user_message[:50]}...")
        return memory


# 便捷函数
def get_memory_store(user_id: str) -> MemoryStore:
    """获取用户的记忆存储"""
    return MemoryStore(user_id)


def get_relevant_memories(user_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """获取与查询相关的记忆"""
    store = MemoryStore(user_id)
    memories = store.search(query, top_k=top_k)
    return [m.to_dict() for m in memories]


def add_memory(user_id: str, text: str, source: str = "manual", importance: float = 0.5) -> Dict[str, Any]:
    """添加记忆"""
    store = MemoryStore(user_id)
    memory = store.add(text, source, importance)
    return memory.to_dict()


def delete_memory(user_id: str, memory_id: str) -> bool:
    """删除记忆"""
    store = MemoryStore(user_id)
    return store.delete(memory_id)


# 导出
__all__ = [
    "Memory",
    "MemoryStore",
    "MemoryExtractor",
    "get_memory_store",
    "get_relevant_memories",
    "add_memory",
    "delete_memory",
]

