from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
from core.metrics import JsonlMetricsLogger
import time
import httpx
from core.architectures import build_session, query_session
from core.auth import (
    UserCreate, UserLogin, Token, user_manager,
    create_access_token, get_user_workspace_path, get_user_uploads_path
)
from core.middleware import get_current_user, get_user_workspace
from datetime import timedelta
from typing import Any, Dict, List, Optional

# 导入新的高级功能模块
from core.research_mode import run_research, ResearchMode
from core.memory_system import (
    get_memory_store, get_relevant_memories, 
    add_memory, delete_memory, MemoryExtractor
)
from core.mcp_protocol import get_mcp_tools, call_mcp_tool, mcp_registry
from core.cross_encoder import rerank_with_cross_encoder, ENABLE_RERANK
from core.react_agent import ReActAgent, PlanningAgent, run_react, run_planning
from core.discussion import discussion_manager, DiscussionMessage
from core.graph_router import graph_router
from core.dashboard import dashboard_router
from core.citation_chat_router import citation_chat_router
from core.qnn_research_router import qnn_research_router
from core.spark.router import spark_router
from core.nft.router import nft_router
from core.rewards.router import rewards_router
from core.web3.router import web3_router
from core.knowledge_graph import kg_router

app = FastAPI(
    title="RAG Studio Platform", 
    version="2.0.0",
    description="Multi-Tenant RAG Platform with Research Mode, Memory System, Cross-Encoder and MCP Support"
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# 注册图谱路由
app.include_router(graph_router, prefix="/v1")

# 注册仪表盘路由
app.include_router(dashboard_router, prefix="/v1")

# 注册引用聊天路由
app.include_router(citation_chat_router, prefix="/v1")

# 注册 QNN 深度研究路由
app.include_router(qnn_research_router, prefix="/v1")

# 注册光源算法路由
app.include_router(spark_router, prefix="/v1")

# 注册 NFT 路由
app.include_router(nft_router, prefix="/v1")

# 注册激励路由
app.include_router(rewards_router, prefix="/v1")

# 注册 Web3 NFT 路由 (原有光源 NFT)
app.include_router(web3_router, prefix="/v1")

# 注册 Web3 集成路由 (新增 RAG 答案 NFT)
# 独立模块，可选启用，不影响 RAG 核心功能
try:
    from core.web3_integration import web3_router as web3_integration_router
    app.include_router(web3_integration_router, prefix="/v1")
    print("✅ Web3 Integration module loaded")
except ImportError as e:
    print(f"ℹ️ Web3 Integration module not loaded: {e}")

# 注册知识图谱路由
app.include_router(kg_router, prefix="/v1")
print("✅ Knowledge Graph module loaded")

# 多租户 RAG 缓存：{user_id: {rag_id: session_data}}
rag_engine_cache: dict = {} 

# 导入统一数据库
from core.database import init_database, RagDB, UserDB
import json
import hashlib

# 确保数据目录存在
os.makedirs("data", exist_ok=True)

# 初始化数据库（创建表结构）
init_database()


def add_rag_metadata(user_id: str, rag_id: str, file_path: str, arch: str, content_hash: str = ""):
    """添加新的 RAG 元数据到数据库"""
    file_type = Path(file_path).suffix.lower() if file_path else None
    file_size = Path(file_path).stat().st_size if file_path and Path(file_path).exists() else 0
    workspace_path = str(get_user_workspace_path(user_id) / rag_id)
    
    RagDB.create(
        rag_id=rag_id,
        user_id=user_id,
        name=Path(file_path).name if file_path else rag_id,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        workspace_path=workspace_path
    )


def check_duplicate_content(user_id: str, content_hash: str) -> Optional[dict]:
    """检查用户是否已上传过相同内容的文件"""
    # 从数据库检查
    user_rags = RagDB.get_by_user(user_id)
    for rag in user_rags:
        # 根据 rag_id 中的哈希前缀判断
        if rag.get("id", "").endswith(content_hash[:12]):
            return {
                "rag_id": rag.get("id"),
                "file_path": rag.get("file_path"),
                "created_at": rag.get("created_at"),
            }
    return None


def compute_file_content_hash(file_content: bytes) -> str:
    """计算文件内容的 SHA-256 哈希值"""
    return hashlib.sha256(file_content).hexdigest()


def get_user_rag_metadata(user_id: str) -> list:
    """获取用户的所有 RAG 元数据"""
    rags = RagDB.get_by_user(user_id)
    return [{
        "rag_id": r.get("id"),
        "file_path": r.get("file_path"),
        "arch": "aipartner",  # 默认架构
        "created_at": r.get("created_at"),
    } for r in rags]


def load_rag_metadata() -> dict:
    """兼容旧代码：从数据库加载所有 RAG 元数据"""
    # 这个函数保留用于兼容，但实际从数据库读取
    from core.database import get_connection, _row_to_dict
    result = {}
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, name, file_path, created_at FROM rags WHERE status = 'active'")
        for row in cursor.fetchall():
            # MySQL 返回字典，SQLite 返回 Row 对象
            row_dict = _row_to_dict(row) if not isinstance(row, dict) else row
            user_id = row_dict["user_id"]
            rag_id = row_dict["id"]
            if user_id not in result:
                result[user_id] = {}
            result[user_id][rag_id] = {
                "rag_id": rag_id,
                "file_path": row_dict["file_path"],
                "arch": "aipartner",
                "created_at": str(row_dict["created_at"]),
            }
    return result

# 初始化 MCP 工具
mcp_registry.initialize_default_tools()

@app.get("/")
def read_root():
    return {
        "message": "RAG Studio Platform is running",
        "version": "2.0.0",
        "features": [
            "Semantic Search (LEANN)",
            "Cross-Encoder Reranking",
            "Research Mode",
            "Memory System",
            "MCP Protocol"
        ]
    }


# ========== 用户认证相关 API ==========

@app.post("/v1/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """用户注册"""
    try:
        user = user_manager.create_user(user_data)
        
        # 创建用户专属的 workspace 目录
        workspace = get_user_workspace_path(user.id)
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "notes").mkdir(exist_ok=True)
        (workspace / "config").mkdir(exist_ok=True)
        (workspace / "knowledge_graph").mkdir(exist_ok=True)
        
        # 生成 token
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username},
            expires_delta=timedelta(minutes=60 * 24 * 7)  # 7天
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            username=user.username
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@app.post("/v1/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    """用户登录"""
    user = user_manager.authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=timedelta(minutes=60 * 24 * 7)  # 7天
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username
    )


@app.get("/v1/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


# ========== RAG 相关 API（需要认证）==========

@app.post("/v1/rag/")
async def create_rag(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    文件上传并创建 RAG（多租户隔离）
    每个用户有独立的 RAG 实例
    基于内容哈希进行去重，防止重复上传相同内容
    """
    try:
        user_id = current_user["user_id"]
        
        # 先读取文件内容计算哈希
        file_content = await file.read()
        content_hash = compute_file_content_hash(file_content)
        
        # 检查是否已存在相同内容的文件
        existing_rag = check_duplicate_content(user_id, content_hash)
        if existing_rag:
            raise HTTPException(
                status_code=409,  # Conflict
                detail={
                    "error": "duplicate_content",
                    "message": f"该文件内容已上传过，请勿重复上传",
                    "existing_file": Path(existing_rag["file_path"]).name,
                    "existing_rag_id": existing_rag["rag_id"],
                    "uploaded_at": existing_rag.get("created_at", "未知时间")
                }
            )
        
        # 用户专属的上传目录（统一目录结构）
        user_uploads_dir = get_user_uploads_path(user_id)
        user_uploads_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = user_uploads_dir / file.filename
        # 将已读取的内容写入文件
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # 使用内容哈希生成唯一的 rag_id（确保相同内容始终得到相同 ID）
        import hashlib
        rag_id = f"rag_{user_id}_{content_hash[:12]}"
        arch = "aipartner"
        metrics = JsonlMetricsLogger(rag_id=rag_id, arch=arch)
        
        print(f"[User {user_id}] Building RAG for {file.filename}...")
        with metrics.time_block("rag_build_total", {"file_name": file.filename, "user_id": user_id}):
            # 传递用户ID和workspace路径给build_session
            session, extracted_text = await build_session(
                arch=arch, 
                rag_id=rag_id, 
                file_path=str(file_path), 
                metrics=metrics,
                user_id=user_id  # 传递用户ID用于workspace隔离
            )
        
        # 按用户隔离的缓存
        if user_id not in rag_engine_cache:
            rag_engine_cache[user_id] = {}
        
        rag_engine_cache[user_id][rag_id] = {
            "session": session,
            "arch": arch,
            "metrics_path": metrics.path,
            "file_path": str(file_path),
            "extracted_text": extracted_text,
        }
        
        # 持久化 RAG 元数据（包含内容哈希用于去重）
        add_rag_metadata(user_id, rag_id, str(file_path), arch, content_hash)
        
        print(f"[User {user_id}] RAG built successfully with ID: {rag_id}")
        
        text_preview = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
        
        return {
            "rag_id": rag_id, 
            "arch": arch,
            "message": "AI Partner 构建成功",
            "extracted_text_preview": text_preview,
            "metrics_file": metrics.path,
            "features": {
                "cross_encoder": ENABLE_RERANK,
                "memory_system": True,
                "research_mode": True,
                "mcp_tools": len(get_mcp_tools()),
            }
        }
    except MemoryError:
        raise HTTPException(
            status_code=500,
            detail="Out of memory while building RAG. Try increasing Docker memory, disabling heavy models, or using baseline arch.",
        )
    except Exception as e:
        print(f"Error creating RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.options("/v1/rag/")
async def create_rag_options(request: Request):
    return {"ok": True}


# 问答请求模型
class QueryRequest(BaseModel):
    rag_id: str
    question: str


@app.post("/v1/chat/")
async def chat(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    问答接口（多租户隔离）
    只能访问当前用户的 RAG
    """
    user_id = current_user["user_id"]
    
    # 检查用户是否有该 RAG
    if user_id not in rag_engine_cache:
        raise HTTPException(
            status_code=404,
            detail="用户没有可用的 RAG。请先上传文件创建 RAG。",
        )
    
    if request.rag_id not in rag_engine_cache[user_id]:
        raise HTTPException(
            status_code=404,
            detail="RAG 不存在或不属于当前用户。请检查 rag_id 是否正确。",
        )
    
    try:
        session = rag_engine_cache[user_id][request.rag_id]
        arch = session.get("arch", "aipartner")
        metrics = JsonlMetricsLogger(rag_id=request.rag_id, arch=arch)

        # 获取相关记忆
        relevant_memories = get_relevant_memories(user_id, request.question, top_k=3)
        memory_context = ""
        if relevant_memories:
            memory_texts = [m["text"] for m in relevant_memories]
            memory_context = "\n".join([f"- {t}" for t in memory_texts])

        t0 = time.perf_counter()
        response, reference_list = await query_session(
            session["session"], 
            request.question, 
            metrics=metrics,
            memory_context=memory_context  # 传递记忆上下文
        )
        total_ms = (time.perf_counter() - t0) * 1000.0
        metrics.write("chat_total", {"question": request.question, "duration_ms": round(total_ms, 3), "user_id": user_id})
        
        answer_text = str(response)
        
        # 自动提取记忆
        memory_store = get_memory_store(user_id)
        extracted_memory = MemoryExtractor.extract_from_conversation(
            request.question, answer_text, memory_store
        )
        
        return {
            "answer": answer_text, 
            "sources": [], 
            "metrics_file": metrics.path,
            "memory_extracted": extracted_memory is not None,
        }
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/stream")
async def chat_stream(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    流式问答接口（多租户隔离）
    返回 text/plain 流式响应，前端可实时显示
    """
    user_id = current_user["user_id"]
    
    # 检查用户是否有该 RAG
    if user_id not in rag_engine_cache:
        raise HTTPException(
            status_code=404,
            detail="用户没有可用的 RAG。请先上传文件创建 RAG。",
        )
    
    if request.rag_id not in rag_engine_cache[user_id]:
        raise HTTPException(
            status_code=404,
            detail="RAG 不存在或不属于当前用户。请检查 rag_id 是否正确。",
        )
    
    session = rag_engine_cache[user_id][request.rag_id]
    runner_url = session["session"].get("runner_url", "").rstrip("/")
    rag_id = session["session"].get("rag_id", request.rag_id)
    
    # 获取相关记忆
    relevant_memories = get_relevant_memories(user_id, request.question, top_k=3)
    memory_context = ""
    if relevant_memories:
        memory_texts = [m["text"] for m in relevant_memories]
        memory_context = "【用户记忆】\n" + "\n".join([f"- {t}" for t in memory_texts]) + "\n\n"
    
    async def generate():
        """流式生成器：代理 AI Partner Runner 的流式响应，失败时回退到 Ollama"""
        enhanced_question = memory_context + request.question if memory_context else request.question
        use_ollama_fallback = False
        error_msg = ""
        
        # 首先尝试 AI Partner Runner
        if runner_url:
            try:
                payload = {
                    "rag_id": rag_id,
                    "messages": [{"role": "user", "content": enhanced_question}],
                    "stream": True,
                    "mode": "claude",
                    "show_tool_trace": True,
                    "user_id": user_id,
                }
                
                async with httpx.AsyncClient(timeout=600.0) as client:
                    async with client.stream(
                        "POST",
                        f"{runner_url}/v1/aipartner/chat",
                        json=payload,
                    ) as response:
                        if response.status_code >= 400:
                            error_text = await response.aread()
                            error_str = error_text.decode()
                            # 检查是否是配额/限流错误，需要回退到 Ollama
                            if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                                use_ollama_fallback = True
                                error_msg = error_str
                            else:
                                yield f"错误: {error_str}"
                                return
                        else:
                            # 检查流式响应中是否有错误
                            full_response = ""
                            async for chunk in response.aiter_bytes():
                                if chunk:
                                    chunk_str = chunk.decode("utf-8", errors="ignore")
                                    full_response += chunk_str
                                    # 检查是否是 API 限流错误
                                    if "429" in chunk_str or "exceeded_current_quota" in chunk_str:
                                        use_ollama_fallback = True
                                        error_msg = chunk_str
                                        break
                                    yield chunk
                            if not use_ollama_fallback:
                                return  # 成功完成
                            
            except Exception as e:
                use_ollama_fallback = True
                error_msg = str(e)
        else:
            use_ollama_fallback = True
            error_msg = "AI Partner Runner URL 未配置"
        
        # 回退到 Ollama
        if use_ollama_fallback:
            yield f"\n\n💡 正在切换到本地 Ollama 模型...\n\n".encode("utf-8") if isinstance(error_msg, str) else b"\n\n"
            
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
            
            # 获取文档内容作为上下文
            extracted_text = session.get("extracted_text", "")[:8000] if session else ""
            
            system_prompt = f"""你是一个智能文档助手。根据以下文档内容回答用户的问题。

【文档内容】
{extracted_text}

请直接、准确地回答问题。如果文档中没有相关信息，请诚实地说明。"""

            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(
                        f"{ollama_url}/api/generate",
                        json={
                            "model": ollama_model,
                            "prompt": f"{system_prompt}\n\n用户问题: {enhanced_question}",
                            "stream": True,
                        },
                    )
                    
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        yield data["response"].encode("utf-8")
                                except:
                                    pass
                    else:
                        yield f"Ollama 错误: {response.status_code}".encode("utf-8")
                        
            except Exception as e:
                yield f"\n\n[Ollama 错误: {str(e)}]".encode("utf-8")
    
    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/v1/rag/list")
async def list_rags(current_user: dict = Depends(get_current_user)):
    """获取当前用户的所有 RAG 列表（从持久化存储和内存缓存合并）"""
    user_id = current_user["user_id"]
    
    # 从持久化存储获取元数据
    persisted_rags = get_user_rag_metadata(user_id)
    
    # 从内存缓存获取（用于检查哪些 RAG 已激活）
    active_rags = set()
    if user_id in rag_engine_cache:
        active_rags = set(rag_engine_cache[user_id].keys())
    
    # 合并并标记状态
    rags = []
    seen_rag_ids = set()
    
    # 先添加持久化的 RAG（包含历史记录）
    for rag_data in persisted_rags:
        rag_id = rag_data.get("rag_id")
        if rag_id and rag_id not in seen_rag_ids:
            rags.append({
                "rag_id": rag_id,
                "arch": rag_data.get("arch", "aipartner"),
                "file_path": rag_data.get("file_path", ""),
                "created_at": rag_data.get("created_at", ""),
                "active": rag_id in active_rags,  # 是否在内存中激活
            })
            seen_rag_ids.add(rag_id)
    
    # 再添加只在内存中的 RAG（新创建但未持久化的）
    if user_id in rag_engine_cache:
        for rag_id, session_data in rag_engine_cache[user_id].items():
            if rag_id not in seen_rag_ids:
                rags.append({
                    "rag_id": rag_id,
                    "arch": session_data.get("arch", "aipartner"),
                    "file_path": session_data.get("file_path", ""),
                    "created_at": "",
                    "active": True,
                })
    
    return {"rags": rags}


@app.get("/v1/rag/{rag_id}/knowledge-graph")
async def get_knowledge_graph(
    rag_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    获取指定 RAG 的知识图谱数据，用于前端可视化
    """
    user_id = current_user["user_id"]
    runner_url = os.getenv("AI_PARTNER_RUNNER_URL", "http://localhost:9001").rstrip("/")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{runner_url}/v1/aipartner/knowledge-graph/{rag_id}",
                params={"user_id": user_id}
            )
            if response.status_code == 200:
                return response.json()
            else:
                # 返回空图谱
                return {
                    "nodes": [],
                    "links": [],
                    "message": "知识图谱尚未生成"
                }
    except Exception as e:
        print(f"Error fetching knowledge graph: {e}")
        return {
            "nodes": [],
            "links": [],
            "message": f"获取知识图谱失败: {str(e)}"
        }


@app.get("/v1/rag/{rag_id}/files")
async def get_rag_files(
    rag_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    获取指定 RAG 的所有文件列表（包含文件内容预览）
    """
    user_id = current_user["user_id"]
    
    # 从元数据获取 RAG 信息
    metadata = load_rag_metadata()
    if user_id not in metadata or rag_id not in metadata[user_id]:
        raise HTTPException(status_code=404, detail="RAG 不存在")
    
    rag_info = metadata[user_id][rag_id]
    file_path = rag_info.get("file_path", "")
    
    if not file_path or not Path(file_path).exists():
        return {"files": []}
    
    # 获取文件信息
    file_stat = Path(file_path).stat()
    files = [{
        "name": Path(file_path).name,
        "path": file_path,
        "size": file_stat.st_size,
        "size_human": f"{file_stat.st_size / 1024:.1f} KB" if file_stat.st_size > 1024 else f"{file_stat.st_size} B",
        "uploaded_at": rag_info.get("created_at", ""),
        "content_hash": rag_info.get("content_hash", "")[:16] + "..." if rag_info.get("content_hash") else "",
    }]
    
    return {"files": files}


class ActivateRagRequest(BaseModel):
    rag_id: str


@app.post("/v1/rag/activate")
async def activate_rag(
    request: ActivateRagRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    激活一个已存在的 RAG（重新加载到内存）
    用于服务重启后恢复之前的 RAG
    """
    user_id = current_user["user_id"]
    rag_id = request.rag_id
    
    # 检查是否已在内存中
    if user_id in rag_engine_cache and rag_id in rag_engine_cache[user_id]:
        return {
            "status": "already_active",
            "rag_id": rag_id,
            "message": "RAG 已经激活",
        }
    
    # 从持久化存储获取元数据
    user_rags = get_user_rag_metadata(user_id)
    rag_metadata = None
    for rag in user_rags:
        if rag.get("rag_id") == rag_id:
            rag_metadata = rag
            break
    
    if not rag_metadata:
        raise HTTPException(
            status_code=404,
            detail="RAG 不存在或不属于当前用户。",
        )
    
    file_path = rag_metadata.get("file_path", "")
    arch = rag_metadata.get("arch", "aipartner")
    
    # 检查文件是否仍然存在
    if not Path(file_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"原始文件已被删除: {file_path}",
        )
    
    try:
        # 重新构建 session
        metrics = JsonlMetricsLogger(rag_id=rag_id, arch=arch)
        
        print(f"[User {user_id}] Re-activating RAG: {rag_id}")
        with metrics.time_block("rag_reactivate", {"rag_id": rag_id, "user_id": user_id}):
            session, extracted_text = await build_session(
                arch=arch,
                rag_id=rag_id,
                file_path=file_path,
                metrics=metrics,
                user_id=user_id,
            )
        
        # 保存到缓存
        if user_id not in rag_engine_cache:
            rag_engine_cache[user_id] = {}
        
        rag_engine_cache[user_id][rag_id] = {
            "session": session,
            "arch": arch,
            "metrics_path": metrics.path,
            "file_path": file_path,
            "extracted_text": extracted_text,
        }
        
        print(f"[User {user_id}] RAG re-activated successfully: {rag_id}")
        
        return {
            "status": "activated",
            "rag_id": rag_id,
            "message": "RAG 激活成功",
        }
    
    except Exception as e:
        print(f"Error activating RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Research Mode API ==========

class ResearchRequest(BaseModel):
    rag_id: str
    query: str
    options: Optional[Dict[str, bool]] = None


@app.post("/v1/research/")
async def research(
    request: ResearchRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    深度研究模式
    多步骤、多工具并行调用
    """
    user_id = current_user["user_id"]
    
    # 验证 RAG 存在
    if user_id not in rag_engine_cache or request.rag_id not in rag_engine_cache.get(user_id, {}):
        raise HTTPException(
            status_code=404,
            detail="RAG 不存在或不属于当前用户。",
        )
    
    try:
        # 获取 LEANN searcher（如果可用）
        leann_searcher = None  # 实际可从 session 中获取
        
        result = await run_research(
            query=request.query,
            rag_id=request.rag_id,
            user_id=user_id,
            leann_searcher=leann_searcher,
            options=request.options,
        )
        
        return result
    except Exception as e:
        print(f"Research error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Memory System API ==========

class MemoryCreate(BaseModel):
    text: str
    source: str = "manual"
    importance: float = 0.5


class MemorySearch(BaseModel):
    query: str
    top_k: int = 10


@app.get("/v1/memory/")
async def list_memories(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """获取用户的记忆列表"""
    user_id = current_user["user_id"]
    store = get_memory_store(user_id)
    
    memories = store.list(limit=limit, offset=offset)
    stats = store.get_stats()
    
    return {
        "memories": [m.to_dict() for m in memories],
        "stats": stats,
    }


@app.post("/v1/memory/")
async def create_memory(
    memory_data: MemoryCreate,
    current_user: dict = Depends(get_current_user),
):
    """添加新记忆"""
    user_id = current_user["user_id"]
    
    memory = add_memory(
        user_id=user_id,
        text=memory_data.text,
        source=memory_data.source,
        importance=memory_data.importance,
    )
    
    return {"memory": memory, "message": "记忆已保存"}


@app.post("/v1/memory/search")
async def search_memories(
    search_data: MemorySearch,
    current_user: dict = Depends(get_current_user),
):
    """搜索相关记忆"""
    user_id = current_user["user_id"]
    
    memories = get_relevant_memories(
        user_id=user_id,
        query=search_data.query,
        top_k=search_data.top_k,
    )
    
    return {"memories": memories}


@app.delete("/v1/memory/{memory_id}")
async def remove_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user),
):
    """删除记忆"""
    user_id = current_user["user_id"]
    
    success = delete_memory(user_id, memory_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    return {"message": "记忆已删除"}


@app.get("/v1/memory/export")
async def export_memories(current_user: dict = Depends(get_current_user)):
    """导出所有记忆"""
    user_id = current_user["user_id"]
    store = get_memory_store(user_id)
    
    memories = store.export_all()
    
    return {"memories": memories, "count": len(memories)}


# ========== MCP Protocol API ==========

@app.get("/v1/mcp/tools")
async def list_mcp_tools(current_user: dict = Depends(get_current_user)):
    """获取可用的 MCP 工具列表"""
    tools = get_mcp_tools()
    return {"tools": tools}


class MCPToolCall(BaseModel):
    tool_name: str
    params: Dict[str, Any]


@app.post("/v1/mcp/call")
async def execute_mcp_tool(
    tool_call: MCPToolCall,
    current_user: dict = Depends(get_current_user),
):
    """调用 MCP 工具"""
    try:
        result = await call_mcp_tool(tool_call.tool_name, tool_call.params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== System API ==========

@app.get("/v1/system/features")
async def get_features():
    """获取系统功能状态"""
    return {
        "features": {
            "cross_encoder": {
                "enabled": ENABLE_RERANK,
                "model": os.getenv("CROSS_ENCODER_MODEL", "BAAI/bge-reranker-base"),
            },
            "research_mode": {
                "enabled": True,
                "max_iterations": 5,
            },
            "memory_system": {
                "enabled": True,
                "max_memories_per_user": int(os.getenv("MAX_MEMORIES_PER_USER", "1000")),
            },
            "mcp_protocol": {
                "enabled": True,
                "tools_count": len(get_mcp_tools()),
            },
            "leann": {
                "enabled": os.getenv("ENABLE_LEANN", "true").lower() == "true",
                "embedding_model": os.getenv("LEANN_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"),
            },
            "react_agent": {
                "enabled": True,
                "description": "ReAct 推理 (Thought → Action → Observation)",
                "max_steps": 8,
            },
            "planning_agent": {
                "enabled": True,
                "description": "Planning 推理 (Plan → Execute → Reflect)",
                "max_replans": 2,
            },
        }
    }


# 获取定价预览（模拟）
@app.get("/v1/pricing_preview/")
async def get_pricing_preview(rag_id: str):
    return {"price_options": [
        {"type": "按次付费", "price": "0.1 元/次"},
        {"type": "包周套餐", "price": "10 元/周"},
        {"type": "企业买断", "price": "999 元/永久"},
    ]}


# ========== ReAct Agent API ==========

class ReActRequest(BaseModel):
    rag_id: str
    query: str
    max_steps: int = 6


@app.post("/v1/react/")
async def react_reasoning(
    request: ReActRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    ReAct 推理模式
    
    实现 Thought → Action → Observation 循环
    支持多步推理和动态工具调用
    """
    user_id = current_user["user_id"]
    
    # 验证 RAG 存在
    if user_id not in rag_engine_cache or request.rag_id not in rag_engine_cache.get(user_id, {}):
        raise HTTPException(
            status_code=404,
            detail="RAG 不存在或不属于当前用户。",
        )
    
    try:
        # 获取相关记忆作为上下文
        memories = get_relevant_memories(user_id, request.query, top_k=3)
        context = {
            "user_id": user_id,
            "rag_id": request.rag_id,
            "memories": memories,
        }
        
        # 运行 ReAct Agent
        trace = await run_react(
            query=request.query,
            max_steps=request.max_steps,
        )
        
        return {
            "query": trace.query,
            "success": trace.success,
            "final_answer": trace.final_answer,
            "steps": [
                {
                    "step": s.step,
                    "thought": s.thought,
                    "action": s.action.value,
                    "action_input": s.action_input,
                    "observation": s.observation,
                    "confidence": s.confidence,
                    "duration_ms": s.duration_ms,
                }
                for s in trace.steps
            ],
            "total_duration_ms": trace.total_duration_ms,
            "error": trace.error,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Planning Agent API ==========

class PlanningRequest(BaseModel):
    rag_id: str
    goal: str
    max_replans: int = 2


@app.post("/v1/planning/")
async def planning_reasoning(
    request: PlanningRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Planning 推理模式
    
    两阶段执行:
    1. Plan: 分析问题，制定执行计划
    2. Execute: 按计划逐步执行，动态调整
    
    支持任务分解、依赖管理和反思调整
    """
    user_id = current_user["user_id"]
    
    # 验证 RAG 存在
    if user_id not in rag_engine_cache or request.rag_id not in rag_engine_cache.get(user_id, {}):
        raise HTTPException(
            status_code=404,
            detail="RAG 不存在或不属于当前用户。",
        )
    
    try:
        # 获取上下文
        memories = get_relevant_memories(user_id, request.goal, top_k=3)
        context = {
            "user_id": user_id,
            "rag_id": request.rag_id,
            "memories": memories,
        }
        
        # 运行 Planning Agent
        result = await run_planning(
            goal=request.goal,
            context=context,
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== RAG 大厅 & 讨论大厅 API ==========

@app.get("/v1/rag/hall")
async def get_rag_hall():
    """
    获取 RAG 大厅 - 所有公开的 RAG 知识库
    类似 Khoj 的 Agents 页面
    """
    # 从所有用户的 RAG 元数据中获取公开的 RAG
    all_metadata = load_rag_metadata()
    
    public_rags = []
    for user_id, user_rags in all_metadata.items():
        for rag_id, rag_info in user_rags.items():
            # 获取文件名作为标题
            file_path = rag_info.get("file_path", "")
            file_name = file_path.split("/")[-1] if file_path else "未命名"
            
            # 获取最近访问该 RAG 的用户数
            recent_users = discussion_manager.get_recent_users(rag_id)
            
            public_rags.append({
                "rag_id": rag_id,
                "title": file_name,
                "owner_id": user_id,
                "arch": rag_info.get("arch", "aipartner"),
                "created_at": rag_info.get("created_at", ""),
                "recent_user_count": len(recent_users),
                "has_active_discussion": rag_id in discussion_manager.rag_rooms,
            })
    
    return {"rags": public_rags}


@app.get("/v1/discussion/rooms")
async def get_discussion_rooms(current_user: dict = Depends(get_current_user)):
    """获取所有活跃的讨论室"""
    rooms = discussion_manager.get_all_public_rooms()
    return {"rooms": rooms}


class JoinDiscussionRequest(BaseModel):
    rag_id: str


@app.post("/v1/discussion/join")
async def join_discussion(
    request: JoinDiscussionRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    加入或创建 RAG 讨论室
    返回房间信息和 WebSocket 连接地址
    """
    user_id = current_user["user_id"]
    username = current_user.get("username", f"用户_{user_id[:6]}")
    
    # 记录用户访问 RAG
    discussion_manager.record_rag_access(request.rag_id, user_id)
    
    # 获取或创建讨论室
    room = discussion_manager.get_or_create_room(request.rag_id)
    
    # 获取最近访问该 RAG 的其他用户
    recent_users = discussion_manager.get_recent_users(request.rag_id)
    
    return {
        "room_id": room.room_id,
        "rag_id": request.rag_id,
        "websocket_url": f"/ws/discussion/{room.room_id}",
        "room_info": room.to_dict(),
        "recent_users": recent_users,
    }


@app.websocket("/ws/discussion/{room_id}")
async def discussion_websocket(
    websocket: WebSocket,
    room_id: str,
):
    """
    讨论室 WebSocket 连接
    支持实时聊天
    """
    await websocket.accept()
    
    # 从 query params 获取认证信息
    # 实际应用中应该使用更安全的认证方式
    try:
        # 等待客户端发送认证消息
        auth_data = await websocket.receive_json()
        if auth_data.get("type") != "auth":
            await websocket.close(code=4001, reason="认证失败")
            return
        
        user_id = auth_data.get("user_id")
        username = auth_data.get("username", f"用户_{user_id[:6] if user_id else 'unknown'}")
        
        if not user_id:
            await websocket.close(code=4001, reason="缺少用户ID")
            return
    except Exception as e:
        await websocket.close(code=4001, reason=str(e))
        return
    
    # 获取讨论室
    room = discussion_manager.get_room_by_id(room_id)
    if not room:
        await websocket.close(code=4004, reason="讨论室不存在")
        return
    
    # 加入房间
    joined = await discussion_manager.join_room(room, user_id, username, websocket)
    if not joined:
        await websocket.close(code=4005, reason="加入失败")
        return
    
    # 启动清理任务
    discussion_manager.start_cleanup_task()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            msg_type = data.get("type")
            
            if msg_type == "message":
                content = data.get("content", "").strip()
                if content:
                    await discussion_manager.send_message(
                        room_id, user_id, username, content
                    )
            
            elif msg_type == "ping":
                # 心跳检测
                await websocket.send_json({"type": "pong"})
                # 更新用户活跃时间
                if user_id in room.active_users:
                    room.active_users[user_id]["last_active"] = time.time()
            
            elif msg_type == "leave":
                break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await discussion_manager.leave_room(room_id, user_id)


# 在 chat 端点中记录用户访问 RAG
@app.post("/v1/rag/access")
async def record_rag_access(
    request: JoinDiscussionRequest,
    current_user: dict = Depends(get_current_user),
):
    """记录用户访问 RAG（用于讨论室匹配）"""
    user_id = current_user["user_id"]
    discussion_manager.record_rag_access(request.rag_id, user_id)
    
    recent_users = discussion_manager.get_recent_users(request.rag_id)
    
    return {
        "rag_id": request.rag_id,
        "recorded": True,
        "recent_user_count": len(recent_users),
    }
