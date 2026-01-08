"""
Dashboard API - 个人仪表盘统计和数据接口
"""
from fastapi import APIRouter, Depends, HTTPException
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

from .middleware import get_current_user
from .auth import get_user_workspace_path

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _get_workspace_path(user_id: str) -> Path:
    """获取用户 workspace 根目录"""
    return get_user_workspace_path(user_id)


def _get_user_rags(user_id: str) -> List[Dict[str, Any]]:
    """获取用户所有 RAG 信息"""
    rags = []
    user_ws = _get_workspace_path(user_id)
    
    if not user_ws.exists():
        return rags
    
    for rag_dir in user_ws.iterdir():
        if rag_dir.is_dir() and rag_dir.name.startswith("rag_"):
            rag_info = {
                "rag_id": rag_dir.name,
                "path": str(rag_dir),
            }
            
            # 尝试读取知识图谱信息
            kg_file = rag_dir / "knowledge_graph" / "graph.json"
            if kg_file.exists():
                try:
                    with open(kg_file, 'r', encoding='utf-8') as f:
                        kg_data = json.load(f)
                        rag_info["graph_nodes"] = len(kg_data.get("entities", {}))
                        rag_info["graph_edges"] = len(kg_data.get("relationships", []))
                except:
                    rag_info["graph_nodes"] = 0
                    rag_info["graph_edges"] = 0
            else:
                rag_info["graph_nodes"] = 0
                rag_info["graph_edges"] = 0
            
            rags.append(rag_info)
    
    return rags


@dashboard_router.get("/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
):
    """
    获取个人仪表盘统计数据
    
    返回:
    - total_conversations: 总对话数
    - total_documents: 已上传文档数
    - total_memories: 记忆条目数
    - research_count: 深度研究次数
    - graph_nodes: 知识图谱节点总数
    - graph_edges: 知识图谱边总数
    """
    user_id = current_user["user_id"]
    
    # 获取 RAG 信息
    rags = _get_user_rags(user_id)
    
    # 统计图谱数据
    total_graph_nodes = sum(r.get("graph_nodes", 0) for r in rags)
    total_graph_edges = sum(r.get("graph_edges", 0) for r in rags)
    
    # 统计记忆数量
    total_memories = 0
    memory_db = Path(f"rag_storage/memory/user_{user_id}.db")
    if memory_db.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(memory_db))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memories")
            total_memories = cursor.fetchone()[0]
            conn.close()
        except:
            pass
    
    # 统计对话数 (从 metrics 日志)
    total_conversations = 0
    metrics_dir = Path("logs/metrics")
    if metrics_dir.exists():
        for log_file in metrics_dir.glob(f"rag_{user_id}*.jsonl"):
            try:
                with open(log_file, 'r') as f:
                    total_conversations += sum(1 for line in f if '"query_total"' in line)
            except:
                pass
    
    return {
        "total_conversations": total_conversations,
        "total_documents": len(rags),
        "total_memories": total_memories,
        "research_count": 0,  # TODO: 实现研究模式计数
        "graph_nodes": total_graph_nodes,
        "graph_edges": total_graph_edges,
    }


@dashboard_router.get("/persona")
async def get_user_persona(
    current_user: dict = Depends(get_current_user),
):
    """
    获取用户画像信息
    """
    user_id = current_user["user_id"]
    user_ws = _get_workspace_path(user_id)
    
    # 查找第一个 RAG 的用户画像
    persona = None
    
    if user_ws.exists():
        for rag_dir in user_ws.iterdir():
            if rag_dir.is_dir() and rag_dir.name.startswith("rag_"):
                persona_file = rag_dir / "config" / "user-persona.md"
                if persona_file.exists():
                    try:
                        content = persona_file.read_text(encoding='utf-8')
                        
                        # 解析 markdown 提取信息
                        persona = {
                            "name": current_user.get("username", "用户"),
                            "role": "知识探索者",
                            "tags": [],
                        }
                        
                        # 提取标签 (假设格式为 ## 兴趣领域 下的列表)
                        lines = content.split('\n')
                        in_interests = False
                        for line in lines:
                            if '兴趣' in line or '领域' in line or '专业' in line:
                                in_interests = True
                                continue
                            if in_interests and line.startswith('#'):
                                in_interests = False
                            if in_interests and line.strip().startswith('-'):
                                tag = line.strip().lstrip('-').strip()
                                if tag and len(tag) < 20:
                                    persona["tags"].append(tag)
                            if len(persona["tags"]) >= 5:
                                break
                        
                        break
                    except:
                        pass
    
    if not persona:
        # 返回默认画像
        persona = {
            "name": current_user.get("username", "用户"),
            "role": "新用户",
            "tags": [],
        }
    
    return persona


@dashboard_router.get("/usage")
async def get_usage_stats(
    current_user: dict = Depends(get_current_user),
):
    """
    获取使用统计数据
    """
    user_id = current_user["user_id"]
    
    # 从 metrics 日志统计
    chat_count = 0
    research_count = 0
    discussion_count = 0
    
    metrics_dir = Path("logs/metrics")
    if metrics_dir.exists():
        for log_file in metrics_dir.glob(f"*{user_id}*.jsonl"):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if '"query_total"' in line:
                            chat_count += 1
                        if '"research"' in line:
                            research_count += 1
            except:
                pass
    
    return {
        "chat": chat_count or 12,  # 演示数据
        "research": research_count or 3,
        "discussion": discussion_count or 5,
    }


@dashboard_router.get("/conversations")
async def get_recent_conversations(
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
):
    """
    获取最近对话列表
    """
    user_id = current_user["user_id"]
    
    conversations = []
    
    # 从 metrics 日志提取对话信息
    metrics_dir = Path("logs/metrics")
    if metrics_dir.exists():
        for log_file in metrics_dir.glob(f"*{user_id}*.jsonl"):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if data.get("event") == "query_total":
                                conversations.append({
                                    "id": data.get("rag_id", ""),
                                    "title": data.get("metadata", {}).get("file_name", "对话"),
                                    "preview": "...",
                                    "time": data.get("timestamp", ""),
                                })
                        except:
                            pass
            except:
                pass
    
    # 按时间倒序排列
    conversations.sort(key=lambda x: x.get("time", ""), reverse=True)
    
    return {
        "conversations": conversations[:limit]
    }


@dashboard_router.get("/activity")
async def get_activity_timeline(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
):
    """
    获取活动时间线
    """
    user_id = current_user["user_id"]
    
    # 生成过去 N 天的活动数据
    activity = []
    today = datetime.now()
    
    for i in range(days):
        date = today - timedelta(days=i)
        activity.append({
            "date": date.strftime("%Y-%m-%d"),
            "conversations": 0,
            "documents": 0,
        })
    
    # 从 metrics 日志统计每日活动
    metrics_dir = Path("logs/metrics")
    if metrics_dir.exists():
        for log_file in metrics_dir.glob(f"*{user_id}*.jsonl"):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            ts = data.get("timestamp", "")
                            if ts:
                                date_str = ts[:10]
                                for a in activity:
                                    if a["date"] == date_str:
                                        a["conversations"] += 1
                                        break
                        except:
                            pass
            except:
                pass
    
    return {
        "activity": activity
    }

