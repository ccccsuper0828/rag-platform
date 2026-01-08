"""
Knowledge Graph API Router
知识图谱 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from core.middleware import get_current_user
from .graphiti_service import get_knowledge_graph_service, KG_ENABLED

kg_router = APIRouter(prefix="/knowledge-graph", tags=["Knowledge Graph"])


class AddDocumentRequest(BaseModel):
    content: str
    source_name: str
    source_description: Optional[str] = "RAG document"


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10


@kg_router.get("/status")
async def get_kg_status():
    """获取知识图谱服务状态"""
    return {
        "enabled": KG_ENABLED,
        "backend": "graphiti+falkordb" if KG_ENABLED else "local",
        "message": "Knowledge Graph service is active" if KG_ENABLED else "Using local fallback"
    }


@kg_router.get("/{rag_id}/graph")
async def get_graph_data(
    rag_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取知识图谱数据（用于可视化）"""
    user_id = current_user["user_id"]
    kg_service = get_knowledge_graph_service(user_id, rag_id)
    
    try:
        if hasattr(kg_service, 'get_graph_data'):
            if hasattr(kg_service.get_graph_data, '__call__'):
                # 检查是否是协程
                result = kg_service.get_graph_data()
                if hasattr(result, '__await__'):
                    data = await result
                else:
                    data = result
            else:
                data = kg_service.get_graph_data()
        else:
            data = {"nodes": [], "links": [], "stats": {"node_count": 0, "edge_count": 0}}
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {"nodes": [], "links": [], "stats": {"node_count": 0, "edge_count": 0}}
        }


@kg_router.post("/{rag_id}/add")
async def add_to_graph(
    rag_id: str,
    request: AddDocumentRequest,
    current_user: dict = Depends(get_current_user)
):
    """添加内容到知识图谱"""
    user_id = current_user["user_id"]
    kg_service = get_knowledge_graph_service(user_id, rag_id)
    
    try:
        if hasattr(kg_service, 'add_document_to_graph'):
            result = await kg_service.add_document_to_graph(
                content=request.content,
                source_name=request.source_name,
                source_description=request.source_description
            )
        elif hasattr(kg_service, 'add_document'):
            result = await kg_service.add_document(
                content=request.content,
                source=request.source_name
            )
        else:
            result = {"success": False, "error": "Method not available"}
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@kg_router.post("/{rag_id}/search")
async def search_graph(
    rag_id: str,
    request: SearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """搜索知识图谱"""
    user_id = current_user["user_id"]
    kg_service = get_knowledge_graph_service(user_id, rag_id)
    
    try:
        if hasattr(kg_service, 'search'):
            results = await kg_service.search(
                query=request.query,
                limit=request.limit
            )
        else:
            results = []
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@kg_router.get("/{rag_id}/entities")
async def get_entities(
    rag_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """获取实体列表"""
    user_id = current_user["user_id"]
    kg_service = get_knowledge_graph_service(user_id, rag_id)
    
    try:
        if hasattr(kg_service, 'get_entities'):
            entities = await kg_service.get_entities(limit=limit)
        elif hasattr(kg_service, 'nodes'):
            entities = list(kg_service.nodes.values())[:limit]
        else:
            entities = []
        
        return {
            "success": True,
            "entities": entities,
            "count": len(entities)
        }
    except Exception as e:
        return {
            "success": False,
            "entities": [],
            "error": str(e)
        }


@kg_router.get("/{rag_id}/relationships")
async def get_relationships(
    rag_id: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """获取关系列表"""
    user_id = current_user["user_id"]
    kg_service = get_knowledge_graph_service(user_id, rag_id)
    
    try:
        if hasattr(kg_service, 'get_relationships'):
            relationships = await kg_service.get_relationships(limit=limit)
        elif hasattr(kg_service, 'edges'):
            relationships = kg_service.edges[:limit]
        else:
            relationships = []
        
        return {
            "success": True,
            "relationships": relationships,
            "count": len(relationships)
        }
    except Exception as e:
        return {
            "success": False,
            "relationships": [],
            "error": str(e)
        }


@kg_router.post("/{rag_id}/build")
async def build_knowledge_graph(
    rag_id: str,
    current_user: dict = Depends(get_current_user)
):
    """从 RAG 文档构建知识图谱"""
    user_id = current_user["user_id"]
    
    # 获取 RAG 的文档内容
    try:
        from pathlib import Path
        import os
        
        # 获取 backend 目录的绝对路径
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent.parent  # core/knowledge_graph -> core -> backend
        project_dir = backend_dir.parent  # backend -> rag-platform-mvp
        
        # 尝试多个可能的路径
        possible_paths = [
            project_dir / "ai_partner_workspaces" / f"user_{user_id}" / rag_id,
            backend_dir / "user_data" / user_id / "workspaces" / rag_id,
        ]
        
        rag_dir = None
        for p in possible_paths:
            if p.exists():
                rag_dir = p
                break
        
        if not rag_dir:
            raise HTTPException(status_code=404, detail=f"RAG directory not found")
        
        # 读取文档内容
        content = ""
        file_name = "document"
        
        # 尝试读取 uploads 目录中的 txt 文件
        uploads_dir = rag_dir / "uploads"
        if uploads_dir.exists():
            for txt_file in uploads_dir.glob("*.txt"):
                try:
                    content += txt_file.read_text(encoding="utf-8") + "\n\n"
                    file_name = txt_file.stem
                except Exception:
                    pass
        
        # 尝试读取 notes 目录
        notes_dir = rag_dir / "notes"
        if notes_dir.exists():
            for note_file in notes_dir.glob("*"):
                if note_file.suffix in [".md", ".txt"]:
                    try:
                        content += note_file.read_text(encoding="utf-8") + "\n\n"
                    except Exception:
                        pass
        
        # 尝试读取 leann_index 目录（可能有提取的文本）
        leann_dir = rag_dir / "leann_index"
        if leann_dir.exists() and not content:
            for txt_file in leann_dir.glob("*.txt"):
                try:
                    content += txt_file.read_text(encoding="utf-8") + "\n\n"
                except Exception:
                    pass
        
        # 尝试读取 metadata.json 获取原始文件信息
        metadata_file = rag_dir / "metadata.json"
        if metadata_file.exists():
            import json
            try:
                meta = json.loads(metadata_file.read_text())
                file_name = meta.get("file_name", file_name)
            except Exception:
                pass
        
        # 模拟 session 结构
        session = {
            "extracted_text": content,
            "file_name": file_name
        } if content else None
        if not session:
            raise HTTPException(status_code=404, detail="RAG not found")
        
        content = session.get("extracted_text", "")
        if not content:
            raise HTTPException(status_code=400, detail="No content in RAG")
        
        # 构建知识图谱
        kg_service = get_knowledge_graph_service(user_id, rag_id)
        
        if hasattr(kg_service, 'add_document_to_graph'):
            result = await kg_service.add_document_to_graph(
                content=content,
                source_name=session.get("file_name", "document"),
                source_description="RAG document content"
            )
        elif hasattr(kg_service, 'add_document'):
            result = await kg_service.add_document(
                content=content,
                source=session.get("file_name", "document")
            )
        else:
            result = {"success": False, "error": "Build method not available"}
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

