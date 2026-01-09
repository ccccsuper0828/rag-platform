"""
光源数据存储管理

使用统一数据库存储（支持 SQLite 开发 / PostgreSQL 生产）
"""

import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from .models import (
    ConversationSpark,
    KnowledgeNodeSpark,
    UserSparkProfile,
    SparkSnapshot,
    Citation
)

# 导入统一数据库
from core.database import SparkDB, get_connection


class SparkStorage:
    """
    光源数据存储管理器（使用统一数据库）
    """
    
    def __init__(self, data_dir: str = "data"):
        # 保留参数兼容性，但不再使用文件存储
        pass
    
    # ==================== 对话光源记录 ====================
    
    def save_conversation_spark(self, spark: ConversationSpark) -> str:
        """保存对话光源记录到数据库"""
        data = {
            "id": spark.id,
            "conversation_id": spark.conversation_id,
            "rag_id": spark.rag_id,
            "user_id": spark.user_id,
            "question": spark.question,
            "answer": spark.answer,
            "citations": [
                {
                    "node_id": c.node_id,
                    "content_preview": c.content_preview,
                    "relevance_score": c.relevance_score,
                    "source_file": c.source_file
                }
                for c in spark.citations
            ],
            "base_score": spark.base_score,
            "citation_score": spark.citation_score,
            "activation_score": spark.activation_score,
            "behavior_score": spark.behavior_score,
            "spark_value": spark.spark_value,
            "like_count": spark.like_count,
            "save_count": spark.save_count,
            "share_count": spark.share_count,
            "reuse_count": spark.reuse_count,
            "nft_eligible": spark.nft_eligible,
            "nft_minted": spark.nft_minted,
            "nft_token_id": spark.nft_token_id,
            "created_at": spark.created_at.isoformat(),
        }
        
        SparkDB.save_conversation(data)
        return spark.conversation_id
    
    def get_conversation_spark(
        self, 
        user_id: str, 
        conversation_id: str
    ) -> Optional[ConversationSpark]:
        """获取对话光源记录"""
        data = SparkDB.get_conversation(user_id, conversation_id)
        if not data:
            return None
        return self._deserialize_conversation_spark(data)
    
    def get_user_conversations(self, user_id: str) -> List[ConversationSpark]:
        """获取用户所有对话光源记录"""
        conversations = SparkDB.get_user_conversations(user_id)
        return [self._deserialize_conversation_spark(c) for c in conversations]
    
    def get_rag_conversations(self, rag_id: str) -> List[ConversationSpark]:
        """获取 RAG 下所有对话光源记录"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM spark_conversations WHERE rag_id = %s
                ORDER BY spark_value DESC
            """, (rag_id,))
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data["citations"] = json.loads(data.get("citations") or "[]")
                data["nft_eligible"] = bool(data.get("nft_eligible"))
                data["nft_minted"] = bool(data.get("nft_minted"))
                results.append(self._deserialize_conversation_spark(data))
            return results
    
    def get_all_conversations(
        self, 
        limit: int = 100,
        offset: int = 0,
        min_spark: float = 0,
        sort_by: str = "spark_value"
    ) -> List[ConversationSpark]:
        """获取所有对话光源记录"""
        order_by = "spark_value DESC" if sort_by == "spark_value" else "created_at DESC"
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM spark_conversations 
                WHERE spark_value >= %s
                ORDER BY {order_by}
                LIMIT %s OFFSET %s
            """, (min_spark, limit, offset))
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data["citations"] = json.loads(data.get("citations") or "[]")
                data["nft_eligible"] = bool(data.get("nft_eligible"))
                data["nft_minted"] = bool(data.get("nft_minted"))
                results.append(self._deserialize_conversation_spark(data))
            return results
    
    def update_conversation_spark(
        self, 
        user_id: str, 
        conversation_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """更新对话光源记录"""
        with get_connection() as conn:
            cursor = conn.cursor()
            set_clauses = ", ".join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [datetime.now().isoformat(), user_id, conversation_id]
            cursor.execute(f"""
                UPDATE spark_conversations 
                SET {set_clauses}, updated_at = %s
                WHERE user_id = %s AND conversation_id = %s
            """, values)
            return cursor.rowcount > 0
    
    def _deserialize_conversation_spark(self, data: Dict) -> ConversationSpark:
        """反序列化对话光源记录"""
        citations = data.get("citations", [])
        if isinstance(citations, str):
            citations = json.loads(citations)
        
        return ConversationSpark(
            id=data.get("id", ""),
            rag_id=data.get("rag_id", ""),
            conversation_id=data.get("conversation_id", ""),
            user_id=data.get("user_id", ""),
            question=data.get("question", ""),
            answer=data.get("answer", ""),
            citations=[
                Citation(**c) if isinstance(c, dict) else c for c in citations
            ],
            base_score=data.get("base_score", 0),
            citation_score=data.get("citation_score", 0),
            activation_score=data.get("activation_score", 0),
            behavior_score=data.get("behavior_score", 0),
            spark_value=data.get("spark_value", 0),
            spark_history=[],  # 数据库版本简化了历史记录
            like_count=data.get("like_count", 0),
            save_count=data.get("save_count", 0),
            share_count=data.get("share_count", 0),
            reuse_count=data.get("reuse_count", 0),
            nft_eligible=data.get("nft_eligible", False),
            nft_minted=data.get("nft_minted", False),
            nft_token_id=data.get("nft_token_id"),
            nft_minted_at=datetime.fromisoformat(data["nft_minted_at"]) if data.get("nft_minted_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now()),
            updated_at=datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) else data.get("updated_at", datetime.now())
        )
    
    # ==================== 知识节点光源 ====================
    
    def save_knowledge_node_spark(self, node: KnowledgeNodeSpark) -> str:
        """保存知识节点光源"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO spark_knowledge_nodes 
                (id, node_id, rag_id, content_preview, source_file, 
                 total_citations, high_spark_citations, contributed_spark, node_value,
                 created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    content_preview = VALUES(content_preview),
                    total_citations = VALUES(total_citations),
                    high_spark_citations = VALUES(high_spark_citations),
                    contributed_spark = VALUES(contributed_spark),
                    node_value = VALUES(node_value),
                    updated_at = VALUES(updated_at)
            """, (
                node.id, node.node_id, node.rag_id, node.content_preview, node.source_file,
                node.total_citations, node.high_spark_citations, node.contributed_spark, node.node_value,
                node.created_at.isoformat(), datetime.now().isoformat()
            ))
        return node.node_id
    
    def get_knowledge_node_spark(
        self, 
        rag_id: str, 
        node_id: str
    ) -> Optional[KnowledgeNodeSpark]:
        """获取知识节点光源"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM spark_knowledge_nodes 
                WHERE rag_id = %s AND node_id = %s
            """, (rag_id, node_id))
            row = cursor.fetchone()
            if row:
                return KnowledgeNodeSpark(**dict(row))
        return None
    
    def get_rag_knowledge_nodes(self, rag_id: str) -> List[KnowledgeNodeSpark]:
        """获取 RAG 下所有知识节点光源"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM spark_knowledge_nodes 
                WHERE rag_id = %s
                ORDER BY node_value DESC
            """, (rag_id,))
            return [KnowledgeNodeSpark(**dict(row)) for row in cursor.fetchall()]
    
    def update_knowledge_node_citation(
        self,
        rag_id: str,
        node_id: str,
        spark_value: float,
        content_preview: str = "",
        source_file: str = ""
    ):
        """更新知识节点的引用统计"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查节点是否存在
            cursor.execute("""
                SELECT * FROM spark_knowledge_nodes 
                WHERE rag_id = %s AND node_id = %s
            """, (rag_id, node_id))
            row = cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            if not row:
                # 创建新节点
                cursor.execute("""
                    INSERT INTO spark_knowledge_nodes 
                    (id, node_id, rag_id, content_preview, source_file,
                     total_citations, high_spark_citations, contributed_spark, node_value,
                     created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    node_id, node_id, rag_id, content_preview, source_file,
                    1, 1 if spark_value >= 70 else 0, spark_value, 0,
                    now, now
                ))
            else:
                node_data = dict(row)
                total = node_data.get("total_citations", 0) + 1
                high_spark = node_data.get("high_spark_citations", 0) + (1 if spark_value >= 70 else 0)
                contributed = node_data.get("contributed_spark", 0) + spark_value
                
                # 计算节点价值
                citation_value = math.log(total + 1) * 10
                high_spark_value = high_spark * 5
                contribution_value = math.log(contributed + 1) * 5
                node_value = min(round(citation_value + high_spark_value + contribution_value, 2), 100)
                
                cursor.execute("""
                    UPDATE spark_knowledge_nodes 
                    SET total_citations = %s, high_spark_citations = %s, 
                        contributed_spark = %s, node_value = %s, updated_at = %s
                    WHERE rag_id = %s AND node_id = %s
                """, (total, high_spark, contributed, node_value, now, rag_id, node_id))
    
    # ==================== 用户光源档案 ====================
    
    def get_user_profile(self, user_id: str) -> UserSparkProfile:
        """获取用户光源档案"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM spark_profiles WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            
            if row:
                data = dict(row)
                return UserSparkProfile(
                    user_id=user_id,
                    total_spark=data.get("total_spark", 0),
                    average_spark=data.get("average_spark", 0),
                    total_conversations=data.get("total_conversations", 0),
                    high_spark_conversations=data.get("high_spark_conversations", 0),
                    reputation_level=data.get("reputation_level", 1),
                    reputation_score=data.get("reputation_score", 0),
                    nft_count=data.get("nft_count", 0),
                    nft_total_value=data.get("nft_total_value", 0),
                    rewards_earned=data.get("rewards_earned", 0),
                    rewards_pending=data.get("rewards_pending", 0),
                    created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()
                )
        
        # 创建新档案
        return UserSparkProfile(user_id=user_id)
    
    def update_user_profile(self, user_id: str) -> UserSparkProfile:
        """更新用户光源档案"""
        # 获取用户所有对话
        conversations = self.get_user_conversations(user_id)
        
        # 计算统计
        profile = self.get_user_profile(user_id)
        profile.update_stats(conversations)
        
        # 保存到数据库
        now = datetime.now().isoformat()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO spark_profiles 
                (user_id, total_spark, average_spark, total_conversations, high_spark_conversations,
                 reputation_level, reputation_score, nft_count, nft_total_value, 
                 rewards_earned, rewards_pending, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    total_spark = VALUES(total_spark),
                    average_spark = VALUES(average_spark),
                    total_conversations = VALUES(total_conversations),
                    high_spark_conversations = VALUES(high_spark_conversations),
                    reputation_level = VALUES(reputation_level),
                    reputation_score = VALUES(reputation_score),
                    nft_count = VALUES(nft_count),
                    nft_total_value = VALUES(nft_total_value),
                    rewards_earned = VALUES(rewards_earned),
                    rewards_pending = VALUES(rewards_pending),
                    updated_at = VALUES(updated_at)
            """, (
                user_id, profile.total_spark, profile.average_spark,
                profile.total_conversations, profile.high_spark_conversations,
                profile.reputation_level, profile.reputation_score,
                profile.nft_count, profile.nft_total_value,
                profile.rewards_earned, profile.rewards_pending,
                profile.created_at.isoformat(), now
            ))
        
        return profile
    
    def get_leaderboard(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取光源排行榜"""
        leaderboard = SparkDB.get_leaderboard(limit)
        
        # 添加排名
        for i, profile in enumerate(leaderboard, 1):
            profile["rank"] = i
        
        return leaderboard


# 全局存储实例
spark_storage = SparkStorage()

