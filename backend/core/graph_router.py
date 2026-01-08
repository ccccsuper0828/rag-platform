"""
图谱 API 路由 - 提供知识图谱的查询和可视化接口
基于 Yuxi-Know 的 graph_router 设计
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pathlib import Path
from typing import Optional
import traceback

from .middleware import get_current_user
from .graph_adapters import GraphAdapterFactory, LocalKnowledgeGraphAdapter
from .auth import get_user_workspace_path

graph_router = APIRouter(prefix="/graph", tags=["graph"])


def _get_workspace_path(user_id: str, rag_id: str) -> Path:
    """获取用户的 workspace 路径"""
    # 使用统一的用户数据目录
    user_workspace = get_user_workspace_path(user_id)
    
    if user_workspace.exists():
        # 查找匹配 rag_id 的目录
        for subdir in user_workspace.iterdir():
            if subdir.is_dir():
                # 完全匹配 - rag_id 就是目录名
                if subdir.name == rag_id:
                    return subdir
                # 检查 rag_{rag_id} 模式
                if subdir.name == f"rag_{rag_id}":
                    return subdir
                # 检查 rag_id 是否在目录名中
                if rag_id in subdir.name and subdir.name.startswith("rag_"):
                    return subdir
    
    raise ValueError(f"Workspace not found for user {user_id}, rag {rag_id}")


async def _get_graph_adapter(user_id: str, rag_id: str) -> LocalKnowledgeGraphAdapter:
    """获取图谱适配器实例"""
    try:
        workspace_path = _get_workspace_path(user_id, rag_id)
        adapter = GraphAdapterFactory.create('local', workspace_path)
        return adapter
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@graph_router.get("/subgraph")
async def get_subgraph(
    rag_id: str = Query(..., description="RAG 知识库 ID"),
    keyword: str = Query("*", description="搜索关键词，* 表示全部"),
    max_nodes: int = Query(100, description="最大节点数", ge=1, le=500),
    max_depth: int = Query(2, description="最大深度", ge=1, le=5),
    current_user: dict = Depends(get_current_user),
):
    """
    获取知识图谱子图数据
    
    返回格式与 @antv/g6 兼容:
    {
        "nodes": [{"id": "...", "name": "...", "type": "...", ...}],
        "edges": [{"id": "...", "source_id": "...", "target_id": "...", "type": "..."}]
    }
    """
    try:
        user_id = current_user["user_id"]
        adapter = await _get_graph_adapter(user_id, rag_id)
        
        result = await adapter.query_nodes(
            keyword=keyword,
            max_nodes=max_nodes,
            max_depth=max_depth,
        )
        
        return {
            "success": True,
            "data": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting subgraph: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get subgraph: {str(e)}")


@graph_router.get("/stats")
async def get_graph_stats(
    rag_id: str = Query(..., description="RAG 知识库 ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    获取图谱统计信息
    
    返回:
    {
        "total_nodes": 数量,
        "total_edges": 数量,
        "entity_types": [{"type": "...", "count": 数量}, ...]
    }
    """
    try:
        user_id = current_user["user_id"]
        adapter = await _get_graph_adapter(user_id, rag_id)
        
        stats = await adapter.get_stats()
        
        return {
            "success": True,
            "data": stats,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@graph_router.get("/labels")
async def get_graph_labels(
    rag_id: str = Query(..., description="RAG 知识库 ID"),
    current_user: dict = Depends(get_current_user),
):
    """获取图谱的所有实体类型/标签"""
    try:
        user_id = current_user["user_id"]
        adapter = await _get_graph_adapter(user_id, rag_id)
        
        labels = await adapter.get_labels()
        
        return {
            "success": True,
            "data": {"labels": labels},
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting labels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get labels: {str(e)}")


@graph_router.post("/rebuild")
async def rebuild_graph(
    rag_id: str = Query(..., description="RAG 知识库 ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    重新构建知识图谱
    
    从 notes 目录重新提取实体和关系
    """
    try:
        user_id = current_user["user_id"]
        adapter = await _get_graph_adapter(user_id, rag_id)
        
        # 强制重新构建
        result = await adapter.build_graph()
        
        return {
            "success": True,
            "message": "图谱重建成功",
            "data": {
                "node_count": len(result.get('entities', {})),
                "edge_count": len(result.get('relationships', [])),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error rebuilding graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rebuild graph: {str(e)}")


@graph_router.get("/list")
async def list_available_graphs(
    current_user: dict = Depends(get_current_user),
):
    """
    获取当前用户所有可用的知识图谱列表
    """
    try:
        user_id = current_user["user_id"]
        
        graphs = []
        
        # 搜索用户的 workspaces 目录
        user_ws_dir = get_user_workspace_path(user_id)
        if user_ws_dir.exists():
            for rag_dir in user_ws_dir.iterdir():
                if rag_dir.is_dir() and rag_dir.name.startswith("rag_"):
                    kg_file = rag_dir / "knowledge_graph" / "graph.json"
                    has_graph = kg_file.exists()
                    
                    graphs.append({
                        "id": rag_dir.name,
                        "name": rag_dir.name,
                        "type": "local",
                        "has_graph": has_graph,
                        "status": "active" if has_graph else "pending",
                    })
        
        return {
            "success": True,
            "data": graphs,
        }
    except Exception as e:
        print(f"Error listing graphs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list graphs: {str(e)}")

