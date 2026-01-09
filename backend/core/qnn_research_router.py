"""
QNN 深度研究 API 路由

提供深度研究功能的 API 端点
"""

import asyncio
import json
import os
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pathlib import Path

from core.middleware import get_current_user, get_user_workspace
from core.qnn_deep_research import (
    QNNDeepResearchEngine,
    run_qnn_deep_research,
    MBTI_PROFILES
)

import httpx

qnn_research_router = APIRouter(prefix="/research", tags=["QNN Deep Research"])


# ============================================
# 请求/响应模型
# ============================================

class QNNResearchRequest(BaseModel):
    """深度研究请求"""
    query: str
    qnn_depth: int = 2  # 网络深度 (1-4)
    qnn_agents_per_layer: int = 3  # 每层 Agent 数量 (2-6)
    max_epochs: int = 2  # 最大迭代次数 (1-5)
    selected_mbtis: Optional[List[str]] = None  # 选择的 MBTI 类型
    use_web_search: bool = False  # 是否使用网络搜索


class QNNResearchResponse(BaseModel):
    """深度研究响应"""
    query: str
    final_answer: str
    insights: List[str]
    epochs_completed: int
    total_duration_ms: float
    network_summary: Dict[str, Any]


# ============================================
# 辅助函数
# ============================================

async def create_llm_caller(model_name: str = "qwen3:8b"):
    """创建 LLM 调用函数 - 优先使用 Claude/Kimi K2，回退到 Ollama"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_base_url = os.getenv("ANTHROPIC_BASE_URL", "")
    anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    runner_url = os.getenv("AI_PARTNER_RUNNER_URL", "http://localhost:9001")
    
    async def call_llm(prompt: str) -> str:
        # 优先尝试 Anthropic Claude API (或 Kimi K2)
        if anthropic_key:
            try:
                import anthropic
                # 支持自定义 base_url (如 Kimi K2)
                client_kwargs = {"api_key": anthropic_key}
                if anthropic_base_url:
                    client_kwargs["base_url"] = anthropic_base_url
                client = anthropic.Anthropic(**client_kwargs)
                response = client.messages.create(
                    model=anthropic_model,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
                if result:
                    print(f"[create_llm_caller] Claude/Kimi API success, len={len(result)}")
                    return result
            except Exception as e:
                print(f"[create_llm_caller] Claude/Kimi API error: {e}")
        
        # 尝试 AI Partner Runner
        if runner_url:
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{runner_url}/v1/aipartner/chat",
                        json={
                            "messages": [{"role": "user", "content": prompt}],
                            "mode": "claude",
                            "stream": False
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        result = data.get("answer", data.get("content", ""))
                        if result and len(result) > 10:
                            print(f"[create_llm_caller] Runner success, len={len(result)}")
                            return result
            except Exception as e:
                print(f"[create_llm_caller] Runner error: {e}")
        
        # 回退到 Ollama 本地模型
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7, "num_predict": 2000}
                    }
                )
                if response.status_code == 200:
                    result = response.json().get("response", "")
                    print(f"[create_llm_caller] Ollama success, len={len(result)}")
                    return result
            except Exception as e:
                print(f"[create_llm_caller] Ollama error: {e}")
        return ""
    
    return call_llm


def create_embedding_caller(model_name: str = "nomic-embed-text"):
    """创建嵌入函数"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    def embed_texts(texts: List[str]) -> List[List[float]]:
        import requests
        
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{ollama_url}/api/embeddings",
                    json={"model": model_name, "prompt": text},
                    timeout=30
                )
                if response.status_code == 200:
                    embeddings.append(response.json().get("embedding", []))
                else:
                    embeddings.append([0.0] * 768)  # 默认维度
            except Exception:
                embeddings.append([0.0] * 768)
        
        return embeddings
    
    return embed_texts


async def load_documents_for_rag(rag_id: str, user_workspace: Path) -> List[Dict[str, Any]]:
    """加载 RAG 的文档"""
    documents = []
    
    # 获取 backend 目录的绝对路径
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parent.parent  # core -> backend
    project_dir = backend_dir.parent  # backend -> rag-platform-mvp
    
    print(f"[load_documents_for_rag] rag_id={rag_id}, user_workspace={user_workspace}")
    print(f"[load_documents_for_rag] backend_dir={backend_dir}, project_dir={project_dir}")
    
    # 从 rag_id 中提取 user_id（格式: rag_{user_id}_{hash}）
    parts = rag_id.split('_')
    if len(parts) >= 2:
        user_id = parts[1]
    else:
        user_id = "unknown"
    
    print(f"[load_documents_for_rag] extracted user_id={user_id}")
    
    # 尝试多个可能的路径
    possible_rag_dirs = [
        project_dir / "ai_partner_workspaces" / f"user_{user_id}" / rag_id,
        user_workspace / rag_id,
        user_workspace,
        Path("/app/ai_partner_workspaces") / f"user_{user_id}" / rag_id,  # Docker 路径
    ]
    
    print(f"[load_documents_for_rag] Checking paths:")
    for d in possible_rag_dirs:
        exists = d.exists()
        has_notes = (d / "notes").exists() if exists else False
        print(f"  - {d}: exists={exists}, has_notes={has_notes}")
    
    rag_dir = None
    for d in possible_rag_dirs:
        if d.exists() and (d / "notes").exists():
            rag_dir = d
            break
    
    if not rag_dir:
        print(f"[load_documents_for_rag] No valid RAG directory found for {rag_id}")
        return documents
    
    print(f"[load_documents_for_rag] Using RAG directory: {rag_dir}")
    
    # 尝试加载 notes 目录的文档
    notes_dir = rag_dir / "notes"
    if notes_dir.exists():
        for file_path in notes_dir.glob("*"):
            if file_path.suffix in [".md", ".txt", ".json"]:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    documents.append({
                        "content": content,
                        "metadata": {
                            "source": file_path.name,
                            "path": str(file_path)
                        }
                    })
                    print(f"[load_documents_for_rag] Loaded: {file_path.name}")
                except Exception as e:
                    print(f"[load_documents_for_rag] Error loading {file_path}: {e}")
    
    # 尝试加载 uploads 目录的文档
    uploads_dir = rag_dir / "uploads"
    if uploads_dir.exists():
        for file_path in uploads_dir.glob("*.txt"):
            try:
                content = file_path.read_text(encoding="utf-8")
                documents.append({
                    "content": content,
                    "metadata": {
                        "source": file_path.name,
                        "path": str(file_path)
                    }
                })
            except Exception:
                pass
    
    print(f"[load_documents_for_rag] Total documents loaded: {len(documents)}")
    return documents


# ============================================
# API 端点
# ============================================

@qnn_research_router.get("/mbti-options")
async def get_mbti_options():
    """获取可用的 MBTI 人格类型"""
    return {
        "mbtis": [
            {
                "type": mbti,
                "name": profile["name"],
                "traits": profile["traits"],
                "skills": profile["skills"]
            }
            for mbti, profile in MBTI_PROFILES.items()
        ]
    }


@qnn_research_router.post("/{rag_id}/qnn-research")
async def run_qnn_research(
    rag_id: str,
    request: QNNResearchRequest,
    user=Depends(get_current_user)
):
    """
    执行 QNN 深度研究
    
    流式返回研究进度和结果
    """
    user_workspace = get_user_workspace(user)
    print(f"[qnn-research] START rag_id={rag_id}, user_id={user.get('user_id')}, query={request.query[:50]}...")
    
    # 验证参数
    if request.qnn_depth < 1 or request.qnn_depth > 4:
        raise HTTPException(400, "qnn_depth 必须在 1-4 之间")
    if request.qnn_agents_per_layer < 2 or request.qnn_agents_per_layer > 6:
        raise HTTPException(400, "qnn_agents_per_layer 必须在 2-6 之间")
    if request.max_epochs < 1 or request.max_epochs > 5:
        raise HTTPException(400, "max_epochs 必须在 1-5 之间")
    
    async def research_stream():
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'status', 'message': '🚀 启动 QNN 深度研究引擎...'})}\n\n"
            
            # 创建 LLM 和嵌入调用器
            llm_caller = await create_llm_caller()
            embedding_caller = create_embedding_caller()
            
            # 加载文档
            yield f"data: {json.dumps({'type': 'status', 'message': '📂 加载知识库文档...'})}\n\n"
            documents = await load_documents_for_rag(rag_id, user_workspace)
            
            if not documents:
                yield f"data: {json.dumps({'type': 'warning', 'message': '⚠️ 未找到文档，将仅使用 QNN 网络进行分析'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'status', 'message': f'📚 已加载 {len(documents)} 个文档'})}\n\n"
            
            # 进度回调
            async def progress_callback(message: str):
                yield f"data: {json.dumps({'type': 'progress', 'message': message})}\n\n"
            
            # 创建研究引擎
            engine = QNNDeepResearchEngine(
                llm_caller=llm_caller,
                embedding_caller=embedding_caller,
                qnn_depth=request.qnn_depth,
                qnn_agents_per_layer=request.qnn_agents_per_layer,
                max_epochs=request.max_epochs,
                selected_mbtis=request.selected_mbtis
            )
            
            # 初始化
            yield f"data: {json.dumps({'type': 'status', 'message': '🔧 初始化研究引擎...'})}\n\n"
            
            # 由于 progress_callback 是生成器函数，我们需要收集进度消息
            progress_messages = []
            
            async def collect_progress(msg: str):
                progress_messages.append(msg)
            
            await engine.initialize(documents, request.query, collect_progress)
            
            for msg in progress_messages:
                yield f"data: {json.dumps({'type': 'progress', 'message': msg})}\n\n"
            
            # 执行研究
            yield f"data: {json.dumps({'type': 'status', 'message': '🧠 开始深度研究...'})}\n\n"
            
            progress_messages = []
            
            async def step_callback(step_info: Dict):
                if step_info.get("type") == "epoch_complete":
                    epoch = step_info.get("epoch", 0)
                    preview = step_info.get("synthesis_preview", "")[:300]
                    yield f"data: {json.dumps({'type': 'epoch', 'epoch': epoch, 'preview': preview})}\n\n"
            
            result = await engine.research(request.query, collect_progress)
            
            for msg in progress_messages:
                yield f"data: {json.dumps({'type': 'progress', 'message': msg})}\n\n"
            
            # 发送结果
            yield f"data: {json.dumps({'type': 'status', 'message': '✅ 研究完成！'})}\n\n"
            
            # 发送最终结果
            final_result = {
                "type": "result",
                "query": result["query"],
                "final_answer": result["final_answer"],
                "insights": result["insights"],
                "epochs_completed": len(result["epochs"]),
                "total_duration_ms": result["total_duration_ms"],
                "network_summary": engine.get_network_summary(),
                "sources_count": len(result["sources"]),
                "epochs_detail": [
                    {
                        "epoch": ep["epoch"],
                        "problem": ep["problem"],
                        "synthesis_preview": ep["synthesis"][:500],
                        "duration_ms": ep["duration_ms"]
                    }
                    for ep in result["epochs"]
                ]
            }
            
            yield f"data: {json.dumps(final_result)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            import traceback
            yield f"data: {json.dumps({'type': 'error', 'message': f'研究失败: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type': 'traceback', 'detail': traceback.format_exc()})}\n\n"
    
    return StreamingResponse(
        research_stream(),
        media_type="text/event-stream"
    )


@qnn_research_router.post("/{rag_id}/quick-research")
async def run_quick_research(
    rag_id: str,
    request: QNNResearchRequest,
    user=Depends(get_current_user)
):
    """
    执行快速研究（非流式，适合小规模问题）
    """
    user_workspace = get_user_workspace(user)
    
    # 使用较小的参数
    depth = min(request.qnn_depth, 2)
    agents = min(request.qnn_agents_per_layer, 3)
    epochs = min(request.max_epochs, 2)
    
    try:
        llm_caller = await create_llm_caller()
        embedding_caller = create_embedding_caller()
        
        documents = await load_documents_for_rag(rag_id, user_workspace)
        
        result = await run_qnn_deep_research(
            query=request.query,
            documents=documents,
            llm_caller=llm_caller,
            embedding_caller=embedding_caller,
            qnn_depth=depth,
            qnn_agents=agents,
            max_epochs=epochs
        )
        
        return QNNResearchResponse(
            query=result["query"],
            final_answer=result["final_answer"],
            insights=result["insights"],
            epochs_completed=len(result["epochs"]),
            total_duration_ms=result["total_duration_ms"],
            network_summary={}
        )
        
    except Exception as e:
        raise HTTPException(500, f"研究失败: {str(e)}")


@qnn_research_router.get("/{rag_id}/estimate")
async def estimate_research_time(
    rag_id: str,
    qnn_depth: int = 2,
    qnn_agents: int = 3,
    max_epochs: int = 2,
    user=Depends(get_current_user)
):
    """
    估算研究时间
    """
    # 基础时间估算（秒）
    base_time_per_agent = 15  # 每个 Agent 约 15 秒
    base_time_per_epoch = 10  # 每个 Epoch 额外 10 秒（综合+反思）
    
    total_agents = qnn_depth * qnn_agents
    estimated_seconds = (
        total_agents * base_time_per_agent * max_epochs +
        max_epochs * base_time_per_epoch
    )
    
    return {
        "total_agents": total_agents,
        "layers": qnn_depth,
        "agents_per_layer": qnn_agents,
        "max_epochs": max_epochs,
        "estimated_seconds": estimated_seconds,
        "estimated_minutes": round(estimated_seconds / 60, 1),
        "quality_estimate": {
            "depth_score": min(qnn_depth / 3, 1.0),
            "diversity_score": min(qnn_agents / 4, 1.0),
            "iteration_score": min(max_epochs / 3, 1.0),
            "overall": min((qnn_depth + qnn_agents + max_epochs) / 9, 1.0)
        }
    }


@qnn_research_router.post("/{rag_id}/kg-research")
async def run_kg_enhanced_research(
    rag_id: str,
    request: QNNResearchRequest,
    user=Depends(get_current_user)
):
    """
    知识图谱增强的深度研究
    
    结合知识图谱进行更精准的研究
    """
    user_id = user["user_id"]
    user_workspace = get_user_workspace(user)
    
    async def research_stream():
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': '🚀 启动知识图谱增强研究...'})}\n\n"
            
            # 1. 从知识图谱获取相关上下文
            yield f"data: {json.dumps({'type': 'status', 'message': '🧠 查询知识图谱...'})}\n\n"
            
            kg_context = ""
            try:
                from core.knowledge_graph import get_knowledge_graph_service
                kg_service = get_knowledge_graph_service(user_id, rag_id)
                
                if hasattr(kg_service, 'search'):
                    # 搜索相关实体和关系
                    search_results = await kg_service.search(request.query, limit=10)
                    if search_results:
                        kg_context = "相关知识图谱事实:\n"
                        for result in search_results:
                            if isinstance(result, dict) and result.get("fact"):
                                kg_context += f"- {result['fact']}\n"
                        yield f"data: {json.dumps({'type': 'status', 'message': f'📊 找到 {len(search_results)} 条相关知识'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'status', 'message': '📊 知识图谱暂无相关数据'})}\n\n"
            except Exception as kg_e:
                yield f"data: {json.dumps({'type': 'warning', 'message': f'知识图谱查询跳过: {str(kg_e)}'})}\n\n"
            
            # 2. 创建 LLM 和嵌入调用器
            llm_caller = await create_llm_caller()
            embedding_caller = create_embedding_caller()
            
            # 3. 加载文档
            yield f"data: {json.dumps({'type': 'status', 'message': '📂 加载知识库文档...'})}\n\n"
            documents = await load_documents_for_rag(rag_id, user_workspace)
            
            # 如果有知识图谱上下文，添加为额外文档
            if kg_context:
                documents.insert(0, {
                    "content": kg_context,
                    "metadata": {
                        "source": "knowledge_graph",
                        "path": "kg://entities"
                    }
                })
            
            if not documents:
                yield f"data: {json.dumps({'type': 'warning', 'message': '⚠️ 未找到文档'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'status', 'message': f'📚 已加载 {len(documents)} 个文档'})}\n\n"
            
            # 4. 创建研究引擎
            engine = QNNDeepResearchEngine(
                llm_caller=llm_caller,
                embedding_caller=embedding_caller,
                qnn_depth=request.qnn_depth,
                qnn_agents_per_layer=request.qnn_agents_per_layer,
                max_epochs=request.max_epochs,
                selected_mbtis=request.selected_mbtis
            )
            
            # 5. 初始化和执行研究
            yield f"data: {json.dumps({'type': 'status', 'message': '🔧 初始化研究引擎...'})}\n\n"
            
            progress_messages = []
            
            async def collect_progress(msg: str):
                progress_messages.append(msg)
            
            await engine.initialize(documents, request.query, collect_progress)
            
            for msg in progress_messages:
                yield f"data: {json.dumps({'type': 'progress', 'message': msg})}\n\n"
            
            yield f"data: {json.dumps({'type': 'status', 'message': '🧠 开始知识图谱增强研究...'})}\n\n"
            
            progress_messages = []
            result = await engine.research(request.query, collect_progress)
            
            for msg in progress_messages:
                yield f"data: {json.dumps({'type': 'progress', 'message': msg})}\n\n"
            
            # 6. 尝试将研究结果添加到知识图谱
            try:
                from core.knowledge_graph import get_knowledge_graph_service
                kg_service = get_knowledge_graph_service(user_id, rag_id)
                
                if hasattr(kg_service, 'add_document_to_graph'):
                    # 将研究结果添加到知识图谱
                    await kg_service.add_document_to_graph(
                        content=f"问题: {request.query}\n\n答案: {result['final_answer']}",
                        source_name="research_result",
                        source_description="QNN深度研究结果"
                    )
                    yield f"data: {json.dumps({'type': 'status', 'message': '📈 研究结果已添加到知识图谱'})}\n\n"
                elif hasattr(kg_service, 'add_document'):
                    await kg_service.add_document(
                        content=f"问题: {request.query}\n\n答案: {result['final_answer']}",
                        source="research_result"
                    )
                    yield f"data: {json.dumps({'type': 'status', 'message': '📈 研究结果已添加到知识图谱'})}\n\n"
            except Exception as add_e:
                yield f"data: {json.dumps({'type': 'info', 'message': f'知识图谱更新跳过: {str(add_e)}'})}\n\n"
            
            # 7. 发送结果
            yield f"data: {json.dumps({'type': 'status', 'message': '✅ 知识图谱增强研究完成！'})}\n\n"
            
            final_result = {
                "type": "result",
                "query": result["query"],
                "final_answer": result["final_answer"],
                "insights": result["insights"],
                "epochs_completed": len(result["epochs"]),
                "total_duration_ms": result["total_duration_ms"],
                "network_summary": engine.get_network_summary(),
                "sources_count": len(result["sources"]),
                "kg_enhanced": bool(kg_context),
                "epochs_detail": [
                    {
                        "epoch": ep["epoch"],
                        "problem": ep["problem"],
                        "synthesis_preview": ep["synthesis"][:500],
                        "duration_ms": ep["duration_ms"]
                    }
                    for ep in result["epochs"]
                ]
            }
            
            yield f"data: {json.dumps(final_result)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            import traceback
            yield f"data: {json.dumps({'type': 'error', 'message': f'研究失败: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type': 'traceback', 'detail': traceback.format_exc()})}\n\n"
    
    return StreamingResponse(
        research_stream(),
        media_type="text/event-stream"
    )


# 导出路由
__all__ = ["qnn_research_router"]

