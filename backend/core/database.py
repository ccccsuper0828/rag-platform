"""
统一数据库管理模块

多租户平台的核心数据存储层：
- 用户数据
- RAG 元数据（原文件在本地沙盒）
- 光源记录
- NFT 记录
- 激励记录
- 记忆库

支持 SQLite（开发）和 MySQL（生产）
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import threading

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

# 数据库配置
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")  # mysql 或 sqlite
IS_MYSQL = DATABASE_TYPE.lower() == "mysql"

# MySQL 配置
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "rag_platform")

# 数据目录（SQLite 备用）
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 连接池
_local = threading.local()


def get_db_path() -> str:
    """获取 SQLite 数据库路径"""
    return str(DATA_DIR / "platform.db")


@contextmanager
def get_connection():
    """获取数据库连接（上下文管理器）"""
    if IS_MYSQL:
        import pymysql
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(get_db_path(), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_database():
    """初始化数据库表结构"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if IS_MYSQL:
            # ==================== MySQL 表结构 ====================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(64) PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active TINYINT DEFAULT 1,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            # ==================== SQLite 表结构 ====================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)
        
        # ==================== RAG 元数据表 ====================
        if IS_MYSQL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rags (
                    id VARCHAR(64) PRIMARY KEY,
                    user_id VARCHAR(64) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    file_path TEXT,
                    file_type VARCHAR(50),
                    file_size BIGINT,
                    status VARCHAR(20) DEFAULT 'active',
                    workspace_path TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME,
                    INDEX idx_rags_user (user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rags (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    file_path TEXT,
                    file_type TEXT,
                    file_size INTEGER,
                    status TEXT DEFAULT 'active',
                    workspace_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rags_user ON rags(user_id)")
        
        # ==================== 光源记录表 ====================
        if IS_MYSQL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spark_conversations (
                    id VARCHAR(64) PRIMARY KEY,
                    conversation_id VARCHAR(64) UNIQUE NOT NULL,
                    rag_id VARCHAR(64) NOT NULL,
                    user_id VARCHAR(64) NOT NULL,
                    question TEXT NOT NULL,
                    answer LONGTEXT,
                    citations JSON,
                    base_score DECIMAL(10,4) DEFAULT 0,
                    citation_score DECIMAL(10,4) DEFAULT 0,
                    activation_score DECIMAL(10,4) DEFAULT 0,
                    behavior_score DECIMAL(10,4) DEFAULT 0,
                    spark_value DECIMAL(10,4) DEFAULT 0,
                    like_count INT DEFAULT 0,
                    save_count INT DEFAULT 0,
                    share_count INT DEFAULT 0,
                    reuse_count INT DEFAULT 0,
                    nft_eligible TINYINT DEFAULT 0,
                    nft_minted TINYINT DEFAULT 0,
                    nft_token_id VARCHAR(100),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME,
                    INDEX idx_spark_user (user_id),
                    INDEX idx_spark_rag (rag_id),
                    INDEX idx_spark_value (spark_value DESC),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (rag_id) REFERENCES rags(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spark_conversations (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT UNIQUE NOT NULL,
                    rag_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT,
                    citations TEXT,
                    base_score REAL DEFAULT 0,
                    citation_score REAL DEFAULT 0,
                    activation_score REAL DEFAULT 0,
                    behavior_score REAL DEFAULT 0,
                    spark_value REAL DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    save_count INTEGER DEFAULT 0,
                    share_count INTEGER DEFAULT 0,
                    reuse_count INTEGER DEFAULT 0,
                    nft_eligible INTEGER DEFAULT 0,
                    nft_minted INTEGER DEFAULT 0,
                    nft_token_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (rag_id) REFERENCES rags(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_spark_user ON spark_conversations(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_spark_rag ON spark_conversations(rag_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_spark_value ON spark_conversations(spark_value DESC)")
        
        # ==================== 知识节点光源表 ====================
        if IS_MYSQL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spark_knowledge_nodes (
                    id VARCHAR(64) PRIMARY KEY,
                    node_id VARCHAR(64) NOT NULL,
                    rag_id VARCHAR(64) NOT NULL,
                    content_preview TEXT,
                    source_file VARCHAR(500),
                    total_citations INT DEFAULT 0,
                    high_spark_citations INT DEFAULT 0,
                    contributed_spark DECIMAL(10,4) DEFAULT 0,
                    node_value DECIMAL(10,4) DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME,
                    UNIQUE KEY unique_node_rag (node_id, rag_id),
                    INDEX idx_rag (rag_id),
                    FOREIGN KEY (rag_id) REFERENCES rags(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spark_knowledge_nodes (
                    id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    rag_id TEXT NOT NULL,
                    content_preview TEXT,
                    source_file TEXT,
                    total_citations INTEGER DEFAULT 0,
                    high_spark_citations INTEGER DEFAULT 0,
                    contributed_spark REAL DEFAULT 0,
                    node_value REAL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    UNIQUE(node_id, rag_id),
                    FOREIGN KEY (rag_id) REFERENCES rags(id)
                )
            """)
        
        # ==================== 用户光源档案表 ====================
        if IS_MYSQL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spark_profiles (
                    user_id VARCHAR(64) PRIMARY KEY,
                    total_spark DECIMAL(12,4) DEFAULT 0,
                    average_spark DECIMAL(10,4) DEFAULT 0,
                    total_conversations INT DEFAULT 0,
                    high_spark_conversations INT DEFAULT 0,
                    reputation_level INT DEFAULT 1,
                    reputation_score DECIMAL(10,4) DEFAULT 0,
                    nft_count INT DEFAULT 0,
                    nft_total_value DECIMAL(12,4) DEFAULT 0,
                    rewards_earned DECIMAL(12,4) DEFAULT 0,
                    rewards_pending DECIMAL(12,4) DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spark_profiles (
                    user_id TEXT PRIMARY KEY,
                    total_spark REAL DEFAULT 0,
                    average_spark REAL DEFAULT 0,
                    total_conversations INTEGER DEFAULT 0,
                    high_spark_conversations INTEGER DEFAULT 0,
                    reputation_level INTEGER DEFAULT 1,
                    reputation_score REAL DEFAULT 0,
                    nft_count INTEGER DEFAULT 0,
                    nft_total_value REAL DEFAULT 0,
                    rewards_earned REAL DEFAULT 0,
                    rewards_pending REAL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
        
        # ==================== NFT 表 ====================
        if IS_MYSQL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nfts (
                    id VARCHAR(64) PRIMARY KEY,
                    token_id VARCHAR(100) UNIQUE,
                    conversation_id VARCHAR(64) NOT NULL,
                    user_id VARCHAR(64) NOT NULL,
                    creator_id VARCHAR(64) NOT NULL,
                    rag_id VARCHAR(64) NOT NULL,
                    rarity VARCHAR(20) DEFAULT 'rare',
                    status VARCHAR(20) DEFAULT 'pending',
                    metadata JSON,
                    metadata_uri TEXT,
                    pricing JSON,
                    listed_price DECIMAL(12,4),
                    created_at DATETIME NOT NULL,
                    minted_at DATETIME,
                    INDEX idx_nft_user (user_id),
                    INDEX idx_nft_status (status),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nfts (
                    id TEXT PRIMARY KEY,
                    token_id TEXT UNIQUE,
                    conversation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    creator_id TEXT NOT NULL,
                    rag_id TEXT NOT NULL,
                    rarity TEXT DEFAULT 'rare',
                    status TEXT DEFAULT 'pending',
                    metadata TEXT,
                    metadata_uri TEXT,
                    pricing TEXT,
                    listed_price REAL,
                    created_at TEXT NOT NULL,
                    minted_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (conversation_id) REFERENCES spark_conversations(conversation_id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nft_user ON nfts(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nft_status ON nfts(status)")
        
        # ==================== 奖励记录表 ====================
        if IS_MYSQL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rewards (
                    id VARCHAR(64) PRIMARY KEY,
                    user_id VARCHAR(64) NOT NULL,
                    reward_type VARCHAR(50) NOT NULL,
                    amount DECIMAL(12,4) NOT NULL,
                    currency VARCHAR(20) DEFAULT 'SPARK',
                    status VARCHAR(20) DEFAULT 'pending',
                    reference_id VARCHAR(64),
                    description TEXT,
                    created_at DATETIME NOT NULL,
                    claimed_at DATETIME,
                    expires_at DATETIME,
                    INDEX idx_rewards_user (user_id),
                    INDEX idx_rewards_status (status),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rewards (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    reward_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'SPARK',
                    status TEXT DEFAULT 'pending',
                    reference_id TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    claimed_at TEXT,
                    expires_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rewards_user ON rewards(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rewards_status ON rewards(status)")
        
        # ==================== 记忆表 ====================
        if IS_MYSQL:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id VARCHAR(64) PRIMARY KEY,
                    user_id VARCHAR(64) NOT NULL,
                    text TEXT NOT NULL,
                    source VARCHAR(50) DEFAULT 'manual',
                    importance DECIMAL(5,4) DEFAULT 0.5,
                    access_count INT DEFAULT 0,
                    metadata JSON,
                    created_at DATETIME NOT NULL,
                    last_accessed DATETIME,
                    INDEX idx_memories_user (user_id),
                    INDEX idx_memories_importance (importance DESC),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    source TEXT DEFAULT 'manual',
                    importance REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC)")
        
        conn.commit()
        print("✅ 数据库初始化完成")


# SQL 参数占位符
def _ph():
    """获取 SQL 参数占位符"""
    return "%s" if IS_MYSQL else "?"


def _row_to_dict(row) -> Optional[Dict]:
    """将数据库行转换为字典"""
    if row is None:
        return None
    if IS_MYSQL:
        return dict(row) if row else None
    else:
        return dict(row) if row else None


# ==================== 用户操作 ====================

class UserDB:
    """用户数据库操作"""
    
    @staticmethod
    def create(user_id: str, username: str, email: str, password_hash: str) -> bool:
        """创建用户"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                ph = _ph()
                cursor.execute(f"""
                    INSERT INTO users (id, username, email, password_hash, created_at)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph})
                """, (user_id, username, email, password_hash, datetime.now().isoformat()))
                return True
        except Exception as e:
            if "Duplicate" in str(e) or "UNIQUE" in str(e):
                return False
            raise
    
    @staticmethod
    def get_by_username(username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"SELECT * FROM users WHERE username = {ph}", (username,))
            row = cursor.fetchone()
            return _row_to_dict(row)
    
    @staticmethod
    def get_by_id(user_id: str) -> Optional[Dict]:
        """根据 ID 获取用户"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"SELECT * FROM users WHERE id = {ph}", (user_id,))
            row = cursor.fetchone()
            return _row_to_dict(row)


# ==================== RAG 操作 ====================

class RagDB:
    """RAG 元数据数据库操作"""
    
    @staticmethod
    def create(rag_id: str, user_id: str, name: str, file_path: str, 
               file_type: str = None, file_size: int = 0, workspace_path: str = None) -> bool:
        """创建 RAG 记录"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                ph = _ph()
                cursor.execute(f"""
                    INSERT INTO rags (id, user_id, name, file_path, file_type, file_size, workspace_path, created_at)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                """, (rag_id, user_id, name, file_path, file_type, file_size, workspace_path, datetime.now().isoformat()))
                return True
        except Exception as e:
            if "Duplicate" in str(e) or "UNIQUE" in str(e):
                return False
            raise
    
    @staticmethod
    def get_by_user(user_id: str) -> List[Dict]:
        """获取用户的所有 RAG"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                SELECT * FROM rags WHERE user_id = {ph} AND status = 'active' 
                ORDER BY created_at DESC
            """, (user_id,))
            return [_row_to_dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_by_id(rag_id: str) -> Optional[Dict]:
        """根据 ID 获取 RAG"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"SELECT * FROM rags WHERE id = {ph}", (rag_id,))
            row = cursor.fetchone()
            return _row_to_dict(row)
    
    @staticmethod
    def update_status(rag_id: str, status: str) -> bool:
        """更新 RAG 状态"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                UPDATE rags SET status = {ph}, updated_at = {ph} WHERE id = {ph}
            """, (status, datetime.now().isoformat(), rag_id))
            return cursor.rowcount > 0


# ==================== 光源操作 ====================

class SparkDB:
    """光源数据库操作"""
    
    @staticmethod
    def save_conversation(data: Dict) -> bool:
        """保存对话光源记录"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            if IS_MYSQL:
                cursor.execute(f"""
                    INSERT INTO spark_conversations 
                    (id, conversation_id, rag_id, user_id, question, answer, citations,
                     base_score, citation_score, activation_score, behavior_score, spark_value,
                     like_count, save_count, share_count, reuse_count,
                     nft_eligible, nft_minted, nft_token_id, created_at, updated_at)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    ON DUPLICATE KEY UPDATE
                    answer = VALUES(answer), citations = VALUES(citations),
                    base_score = VALUES(base_score), citation_score = VALUES(citation_score),
                    activation_score = VALUES(activation_score), behavior_score = VALUES(behavior_score),
                    spark_value = VALUES(spark_value), updated_at = VALUES(updated_at)
                """, (
                    data.get("id"),
                    data.get("conversation_id"),
                    data.get("rag_id"),
                    data.get("user_id"),
                    data.get("question"),
                    data.get("answer"),
                    json.dumps(data.get("citations", [])),
                    data.get("base_score", 0),
                    data.get("citation_score", 0),
                    data.get("activation_score", 0),
                    data.get("behavior_score", 0),
                    data.get("spark_value", 0),
                    data.get("like_count", 0),
                    data.get("save_count", 0),
                    data.get("share_count", 0),
                    data.get("reuse_count", 0),
                    1 if data.get("nft_eligible") else 0,
                    1 if data.get("nft_minted") else 0,
                    data.get("nft_token_id"),
                    data.get("created_at", datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))
            else:
                cursor.execute(f"""
                    INSERT OR REPLACE INTO spark_conversations 
                    (id, conversation_id, rag_id, user_id, question, answer, citations,
                     base_score, citation_score, activation_score, behavior_score, spark_value,
                     like_count, save_count, share_count, reuse_count,
                     nft_eligible, nft_minted, nft_token_id, created_at, updated_at)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                """, (
                    data.get("id"),
                    data.get("conversation_id"),
                    data.get("rag_id"),
                    data.get("user_id"),
                    data.get("question"),
                    data.get("answer"),
                    json.dumps(data.get("citations", [])),
                    data.get("base_score", 0),
                    data.get("citation_score", 0),
                    data.get("activation_score", 0),
                    data.get("behavior_score", 0),
                    data.get("spark_value", 0),
                    data.get("like_count", 0),
                    data.get("save_count", 0),
                    data.get("share_count", 0),
                    data.get("reuse_count", 0),
                    1 if data.get("nft_eligible") else 0,
                    1 if data.get("nft_minted") else 0,
                    data.get("nft_token_id"),
                    data.get("created_at", datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))
            return True
    
    @staticmethod
    def get_conversation(user_id: str, conversation_id: str) -> Optional[Dict]:
        """获取对话光源记录"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                SELECT * FROM spark_conversations 
                WHERE user_id = {ph} AND conversation_id = {ph}
            """, (user_id, conversation_id))
            row = cursor.fetchone()
            if row:
                data = _row_to_dict(row)
                citations = data.get("citations") or "[]"
                data["citations"] = json.loads(citations) if isinstance(citations, str) else citations
                data["nft_eligible"] = bool(data.get("nft_eligible"))
                data["nft_minted"] = bool(data.get("nft_minted"))
                return data
            return None
    
    @staticmethod
    def get_user_conversations(user_id: str, limit: int = 50) -> List[Dict]:
        """获取用户所有对话"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                SELECT * FROM spark_conversations 
                WHERE user_id = {ph} 
                ORDER BY spark_value DESC
                LIMIT {ph}
            """, (user_id, limit))
            results = []
            for row in cursor.fetchall():
                data = _row_to_dict(row)
                citations = data.get("citations") or "[]"
                data["citations"] = json.loads(citations) if isinstance(citations, str) else citations
                data["nft_eligible"] = bool(data.get("nft_eligible"))
                data["nft_minted"] = bool(data.get("nft_minted"))
                results.append(data)
            return results
    
    @staticmethod
    def update_behavior(user_id: str, conversation_id: str, field: str, increment: int = 1) -> Optional[Dict]:
        """更新行为计数"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            # 更新计数
            cursor.execute(f"""
                UPDATE spark_conversations 
                SET {field} = {field} + {ph}, updated_at = {ph}
                WHERE user_id = {ph} AND conversation_id = {ph}
            """, (increment, datetime.now().isoformat(), user_id, conversation_id))
            
            # 返回更新后的记录
            cursor.execute(f"""
                SELECT * FROM spark_conversations 
                WHERE user_id = {ph} AND conversation_id = {ph}
            """, (user_id, conversation_id))
            row = cursor.fetchone()
            return _row_to_dict(row)
    
    @staticmethod
    def get_leaderboard(limit: int = 20) -> List[Dict]:
        """获取光源排行榜"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                SELECT user_id, 
                       SUM(spark_value) as total_spark,
                       COUNT(*) as total_conversations,
                       SUM(CASE WHEN spark_value >= 70 THEN 1 ELSE 0 END) as high_spark_count
                FROM spark_conversations
                GROUP BY user_id
                ORDER BY total_spark DESC
                LIMIT {ph}
            """, (limit,))
            return [_row_to_dict(row) for row in cursor.fetchall()]


# ==================== 记忆操作 ====================

class MemoryDB:
    """记忆数据库操作"""
    
    @staticmethod
    def add(user_id: str, text: str, source: str = "manual", importance: float = 0.5) -> Dict:
        """添加记忆"""
        import uuid
        memory_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                INSERT INTO memories (id, user_id, text, source, importance, created_at, last_accessed)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """, (memory_id, user_id, text, source, importance, now, now))
        
        return {
            "id": memory_id,
            "user_id": user_id,
            "text": text,
            "source": source,
            "importance": importance,
            "created_at": now
        }
    
    @staticmethod
    def get_by_user(user_id: str, limit: int = 50) -> List[Dict]:
        """获取用户的记忆"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                SELECT * FROM memories 
                WHERE user_id = {ph} 
                ORDER BY importance DESC, created_at DESC
                LIMIT {ph}
            """, (user_id, limit))
            return [_row_to_dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def delete(user_id: str, memory_id: str) -> bool:
        """删除记忆"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                DELETE FROM memories WHERE id = {ph} AND user_id = {ph}
            """, (memory_id, user_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def search(user_id: str, query: str, limit: int = 10) -> List[Dict]:
        """搜索记忆（简单关键词匹配）"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                SELECT * FROM memories 
                WHERE user_id = {ph} AND text LIKE {ph}
                ORDER BY importance DESC
                LIMIT {ph}
            """, (user_id, f"%{query}%", limit))
            return [_row_to_dict(row) for row in cursor.fetchall()]


# ==================== NFT 操作 ====================

class NftDB:
    """NFT 数据库操作"""
    
    @staticmethod
    def create(data: Dict) -> bool:
        """创建 NFT 记录"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                INSERT INTO nfts 
                (id, token_id, conversation_id, user_id, creator_id, rag_id,
                 rarity, status, metadata, pricing, created_at, minted_at)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """, (
                data.get("id"),
                data.get("token_id"),
                data.get("conversation_id"),
                data.get("user_id"),
                data.get("creator_id"),
                data.get("rag_id"),
                data.get("rarity", "rare"),
                data.get("status", "minted"),
                json.dumps(data.get("metadata", {})),
                json.dumps(data.get("pricing", {})),
                data.get("created_at", datetime.now().isoformat()),
                data.get("minted_at")
            ))
            return True
    
    @staticmethod
    def get_by_user(user_id: str) -> List[Dict]:
        """获取用户的 NFT"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                SELECT * FROM nfts WHERE user_id = {ph} ORDER BY created_at DESC
            """, (user_id,))
            results = []
            for row in cursor.fetchall():
                data = _row_to_dict(row)
                metadata = data.get("metadata") or "{}"
                pricing = data.get("pricing") or "{}"
                data["metadata"] = json.loads(metadata) if isinstance(metadata, str) else metadata
                data["pricing"] = json.loads(pricing) if isinstance(pricing, str) else pricing
                results.append(data)
            return results
    
    @staticmethod
    def get_by_conversation(conversation_id: str) -> Optional[Dict]:
        """根据对话 ID 获取 NFT"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"SELECT * FROM nfts WHERE conversation_id = {ph}", (conversation_id,))
            row = cursor.fetchone()
            if row:
                data = _row_to_dict(row)
                metadata = data.get("metadata") or "{}"
                pricing = data.get("pricing") or "{}"
                data["metadata"] = json.loads(metadata) if isinstance(metadata, str) else metadata
                data["pricing"] = json.loads(pricing) if isinstance(pricing, str) else pricing
                return data
            return None


# ==================== 奖励操作 ====================

class RewardDB:
    """奖励数据库操作"""
    
    @staticmethod
    def create(user_id: str, reward_type: str, amount: float, 
               reference_id: str = "", description: str = "") -> Dict:
        """创建奖励记录"""
        import uuid
        reward_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                INSERT INTO rewards (id, user_id, reward_type, amount, reference_id, description, created_at)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """, (reward_id, user_id, reward_type, amount, reference_id, description, now))
        
        return {
            "id": reward_id,
            "user_id": user_id,
            "reward_type": reward_type,
            "amount": amount,
            "status": "pending",
            "created_at": now
        }
    
    @staticmethod
    def get_by_user(user_id: str, status: str = None) -> List[Dict]:
        """获取用户的奖励"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            if status:
                cursor.execute(f"""
                    SELECT * FROM rewards WHERE user_id = {ph} AND status = {ph}
                    ORDER BY created_at DESC
                """, (user_id, status))
            else:
                cursor.execute(f"""
                    SELECT * FROM rewards WHERE user_id = {ph} ORDER BY created_at DESC
                """, (user_id,))
            return [_row_to_dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def claim(user_id: str, reward_id: str) -> bool:
        """领取奖励"""
        with get_connection() as conn:
            cursor = conn.cursor()
            ph = _ph()
            cursor.execute(f"""
                UPDATE rewards SET status = 'claimed', claimed_at = {ph}
                WHERE id = {ph} AND user_id = {ph} AND status = 'pending'
            """, (datetime.now().isoformat(), reward_id, user_id))
            return cursor.rowcount > 0


# 初始化数据库
init_database()

