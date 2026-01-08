"""
Citation-aware Chat Router for RAG.
Provides streaming chat responses with inline citations.
Supports both document RAG retrieval and web search.
"""

import asyncio
import json
import os
import re
from typing import Optional, AsyncGenerator, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pathlib import Path
import httpx
import hashlib

from core.middleware import get_current_user, get_user_workspace
from core.citation_handler import CitationHandler, ResponseMode, Citation
from core.spark.calculator import spark_calculator
from core.spark.storage import spark_storage

citation_chat_router = APIRouter(prefix="/rag", tags=["Citation Chat"])

# 会话历史缓存：{user_id: {rag_id: [messages]}}
conversation_history: dict = {}


def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract text content from a PDF file using pdfplumber.
    """
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"Error extracting PDF text with pdfplumber: {e}")
        # Fallback to PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(pdf_path))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except Exception as e2:
            print(f"Error extracting PDF text with PyPDF2: {e2}")
            return ""


# 网络搜索配置
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")


def find_rag_workspace(workspace_path: Path, rag_id: str) -> Optional[Path]:
    """
    Find the RAG workspace directory by rag_id.
    """
    if not workspace_path.exists():
        return None
    
    for subdir in workspace_path.iterdir():
        if subdir.is_dir():
            if subdir.name == rag_id:
                return subdir
            if subdir.name == f"rag_{rag_id}":
                return subdir
            if rag_id in subdir.name and subdir.name.startswith("rag_"):
                return subdir
    
    return None


class CitationChatRequest(BaseModel):
    question: str
    response_mode: str = "normal"
    include_citations: bool = True
    conversation_id: Optional[str] = None
    enable_web_search: bool = False


class CitationChatResponse(BaseModel):
    content: str
    citations: list
    mode: str


def get_rag_document_content(workspace_path: Path, rag_id: str) -> tuple[str, Optional[dict]]:
    """
    Get the document content and page offset map for a RAG.
    Now supports PDF files using pdfplumber, and falls back to text files.
    """
    document_text = ""
    page_offset_map = {}
    
    # 首先尝试从数据库获取 RAG 的文件路径
    try:
        from core.database import RagDB
        rag_info = RagDB.get_rag_by_id(rag_id)
        if rag_info and rag_info.get("file_path"):
            file_path = Path(rag_info["file_path"])
            # 如果是相对路径，相对于 backend 目录解析
            if not file_path.is_absolute():
                backend_dir = Path(__file__).parent.parent
                file_path = backend_dir / file_path
            
            if file_path.exists() and file_path.suffix.lower() == '.pdf':
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        for i, page in enumerate(pdf.pages):
                            page_text = page.extract_text()
                            if page_text:
                                page_offset_map[i + 1] = len(document_text)
                                document_text += f"\n--- 第 {i+1} 页 ---\n{page_text}\n"
                    print(f"✅ 从 PDF 提取文本成功: {file_path}, 共 {len(pdf.pages)} 页")
                    return document_text, page_offset_map
                except Exception as e:
                    print(f"❌ PDF 提取失败: {e}")
    except Exception as e:
        print(f"❌ 从数据库获取 RAG 信息失败: {e}")
    
    # 回退: 从 uploads 目录查找 PDF 文件
    uploads_dir = workspace_path / "uploads"
    if uploads_dir.exists():
        for file_path in uploads_dir.glob("*.pdf"):
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            page_offset_map[i + 1] = len(document_text)
                            document_text += f"\n--- 第 {i+1} 页 ---\n{page_text}\n"
                print(f"✅ 从 uploads 目录提取 PDF: {file_path}")
                if document_text:
                    return document_text, page_offset_map
            except Exception as e:
                print(f"❌ 从 uploads 目录提取 PDF 失败: {e}")
    
    # 回退: 从 notes 目录读取文本文件
    notes_dir = workspace_path / "notes"
    if notes_dir.exists():
        for file_path in notes_dir.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.md']:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        document_text += f"\n\n--- {file_path.name} ---\n\n"
                        document_text += f.read()
                except Exception:
                    pass
    
    return document_text, page_offset_map


async def perform_web_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Perform web search using Tavily or Serper API.
    Returns a list of search results with title, url, and snippet.
    """
    results = []
    
    # Try Tavily first
    if TAVILY_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": TAVILY_API_KEY,
                        "query": query,
                        "search_depth": "basic",
                        "include_answer": True,
                        "max_results": num_results
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    for r in data.get("results", [])[:num_results]:
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "snippet": r.get("content", ""),
                            "source": "tavily"
                        })
                    # Add Tavily's answer if available
                    if data.get("answer"):
                        results.insert(0, {
                            "title": "AI 摘要",
                            "url": "",
                            "snippet": data["answer"],
                            "source": "tavily_answer"
                        })
                    return results
        except Exception as e:
            print(f"Tavily search error: {e}")
    
    # Try Serper as fallback
    if SERPER_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": SERPER_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "num": num_results
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    for r in data.get("organic", [])[:num_results]:
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("link", ""),
                            "snippet": r.get("snippet", ""),
                            "source": "serper"
                        })
                    return results
        except Exception as e:
            print(f"Serper search error: {e}")
    
    # Fallback: Use DuckDuckGo HTML scraping (no API key needed)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (compatible; RAGPlatform/1.0)"}
            )
            if response.status_code == 200:
                # Simple parsing of DuckDuckGo HTML results
                text = response.text
                # Extract result snippets using regex (simplified)
                result_blocks = re.findall(r'<a class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>.*?<a class="result__snippet"[^>]*>([^<]*)</a>', text, re.DOTALL)
                for url, title, snippet in result_blocks[:num_results]:
                    results.append({
                        "title": title.strip(),
                        "url": url,
                        "snippet": snippet.strip(),
                        "source": "duckduckgo"
                    })
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
    
    return results


async def get_rag_session(user_id: str, rag_id: str) -> Optional[Dict[str, Any]]:
    """
    Get RAG session from the engine cache.
    """
    # Import here to avoid circular imports
    try:
        from main import rag_engine_cache
        if user_id in rag_engine_cache and rag_id in rag_engine_cache[user_id]:
            return rag_engine_cache[user_id][rag_id]
    except ImportError:
        pass
    return None


async def query_rag_with_retrieval(
    session: Dict[str, Any],
    question: str,
    user_id: str,
) -> tuple[str, List[Dict[str, Any]]]:
    """
    Query the RAG using AI Partner Runner with proper retrieval.
    Returns (answer, sources).
    """
    session_data = session.get("session", {})
    runner_url = session_data.get("runner_url", os.getenv("AI_PARTNER_RUNNER_URL", "http://localhost:9001")).rstrip("/")
    rag_id = session_data.get("rag_id", "")
    
    payload = {
        "rag_id": rag_id,
        "messages": [{"role": "user", "content": question}],
        "stream": False,
        "mode": "claude",
        "show_tool_trace": True,
        "user_id": user_id,
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{runner_url}/v1/aipartner/chat",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", data.get("content", ""))
                sources = data.get("sources", [])
                return answer, sources
            else:
                print(f"RAG query failed: {response.status_code}")
                return "", []
    except Exception as e:
        print(f"RAG query error: {e}")
        return "", []


async def stream_citation_response(
    question: str,
    document_content: str,
    mode: ResponseMode,
    workspace_path: Path,
    user_id: str,
    rag_id: str,
    enable_web_search: bool = False,
    conversation_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Stream a response with citations using RAG retrieval.
    
    Key improvements:
    1. Uses RAG engine for proper semantic retrieval
    2. Supports web search integration
    3. Maintains conversation history
    4. Generates accurate citations based on retrieved chunks
    """
    import httpx
    
    try:
        # Step 1: Get RAG session
        print(f"🚀 [STREAM START] Starting stream_citation_response")
        print(f"🚀 [STREAM START] document_content length: {len(document_content) if document_content else 0}")
        session = await get_rag_session(user_id, rag_id)
        print(f"🚀 [STREAM START] session: {session is not None}")
        
        retrieved_context = ""
        web_search_results = []
        sources = []
        
        # Step 2: Web search (if enabled)
        if enable_web_search:
            yield f"data: {json.dumps({'type': 'status', 'message': '🌐 正在搜索网络...'}, ensure_ascii=False)}\n\n"
            web_search_results = await perform_web_search(question, num_results=5)
            
            if web_search_results:
                yield f"data: {json.dumps({'type': 'status', 'message': f'🔍 找到 {len(web_search_results)} 条网络结果'}, ensure_ascii=False)}\n\n"
                web_context = "\n\n【网络搜索结果】\n"
                for i, result in enumerate(web_search_results, 1):
                    web_context += f"\n[网络来源{i}] {result['title']}\n{result['snippet']}\n"
                    if result['url']:
                        web_context += f"来源: {result['url']}\n"
                retrieved_context += web_context
        
        # Step 3: RAG retrieval
        yield f"data: {json.dumps({'type': 'status', 'message': '📚 正在检索文档...'}, ensure_ascii=False)}\n\n"
        
        print(f"📋 [STREAM DEBUG] document_content length in stream: {len(document_content) if document_content else 0}")
        print(f"📋 [STREAM DEBUG] session exists: {session is not None}")
        
        # 优先使用从 PDF 提取的文档内容进行检索
        use_pdf_content = True
        
        if session and not document_content:
            # 只有当没有 PDF 内容时才使用 AI Partner Runner
            rag_answer, rag_sources = await query_rag_with_retrieval(session, question, user_id)
            
            # 检查 rag_answer 是否像有效内容（不是 JSON 日志）
            is_valid_answer = rag_answer and not rag_answer.strip().startswith('{') and '"event"' not in rag_answer
            
            if is_valid_answer:
                retrieved_context += f"\n\n【文档检索结果】\n{rag_answer}"
                sources = rag_sources
                use_pdf_content = False
        
        if use_pdf_content and document_content:
            # 使用 PDF 内容进行关键词检索
            print(f"📋 [DEBUG] 使用 PDF 内容进行检索，内容长度: {len(document_content)}")
            chunks = split_into_chunks(document_content, chunk_size=500)
            relevant_chunks = find_relevant_chunks(question, chunks, top_k=5)
            
            if relevant_chunks:
                retrieved_context += "\n\n【文档相关内容】\n"
                for i, (chunk, score) in enumerate(relevant_chunks, 1):
                    retrieved_context += f"\n[文档片段{i}] (相关度: {score:.2f})\n{chunk}\n"
            else:
                # 没有找到相关片段，使用文档前面部分
                print(f"📋 [DEBUG] 未找到相关片段，使用文档前 4000 字符")
                retrieved_context = f"【文档内容】\n{document_content[:4000]}"
        
        if not retrieved_context.strip():
            yield f"data: {json.dumps({'type': 'error', 'message': '没有找到相关内容'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            return
        
        # Step 4: Get conversation history
        conv_key = f"{user_id}:{rag_id}:{conversation_id or 'default'}"
        history = conversation_history.get(conv_key, [])
        
        # Step 5: Build prompt
        system_prompt = build_citation_system_prompt(mode, enable_web_search)
        
        history_text = ""
        if history:
            history_text = "\n【对话历史】\n"
            for msg in history[-6:]:  # Last 3 exchanges
                role = "用户" if msg["role"] == "user" else "助手"
                history_text += f"{role}: {msg['content'][:200]}...\n" if len(msg['content']) > 200 else f"{role}: {msg['content']}\n"
        
        user_message = f"""基于以下检索到的内容回答问题。请使用中文回答，并在回答中添加引用标注。

{retrieved_context}
{history_text}
问题: {question}

请按以下格式回答：
1. 直接回答问题，在引用处使用 [^1], [^2] 等标注
2. 在回答末尾列出所有引用来源

回答:"""

        yield f"data: {json.dumps({'type': 'status', 'message': '🤔 正在生成回答...'}, ensure_ascii=False)}\n\n"
        
        # Step 6: Generate response using LLM
        full_response = await generate_llm_response(system_prompt, user_message, workspace_path)
        
        if full_response:
            yield f"data: {json.dumps({'type': 'content', 'text': full_response}, ensure_ascii=False)}\n\n"
            
            # Update conversation history
            if conv_key not in conversation_history:
                conversation_history[conv_key] = []
            conversation_history[conv_key].append({"role": "user", "content": question})
            conversation_history[conv_key].append({"role": "assistant", "content": full_response})
            
            # Keep only last 10 exchanges
            if len(conversation_history[conv_key]) > 20:
                conversation_history[conv_key] = conversation_history[conv_key][-20:]
        else:
            # Fallback response
            full_response = generate_fallback_response(question, retrieved_context, mode, web_search_results)
            yield f"data: {json.dumps({'type': 'content', 'text': full_response}, ensure_ascii=False)}\n\n"
        
        # Step 7: Parse and send citations
        content, citations = CitationHandler.parse_response(full_response)
        
        # Add web search sources as citations
        for i, result in enumerate(web_search_results):
            if result.get('url'):
                yield f"data: {json.dumps({'type': 'web_source', 'source': result}, ensure_ascii=False)}\n\n"
        
        # Send document citations
        enriched_citations = CitationHandler.enrich_citations_with_positions(
            citations, document_content, None
        )
        
        for citation in enriched_citations:
            yield f"data: {json.dumps({'type': 'citation', 'citation': CitationHandler.to_dict(citation)}, ensure_ascii=False)}\n\n"
        
        # Step 8: 计算并保存光源值
        try:
            # 准备引用数据用于光源计算
            spark_citations = [
                {
                    "node_id": hashlib.md5(c.text[:50].encode()).hexdigest() if c.text else "",
                    "content": c.text or "",
                    "relevance_score": 0.7,  # 默认相关性
                    "source_file": ""
                }
                for c in enriched_citations
            ]
            
            # 添加网络搜索结果作为引用
            for result in web_search_results:
                spark_citations.append({
                    "node_id": hashlib.md5(result.get('url', '')[:50].encode()).hexdigest(),
                    "content": result.get('snippet', ''),
                    "relevance_score": 0.6,
                    "source_file": result.get('url', '')
                })
            
            # 创建对话光源记录
            spark = spark_calculator.create_conversation_spark(
                rag_id=rag_id,
                user_id=user_id,
                question=question,
                answer=full_response,
                citations=spark_citations
            )
            
            # 保存光源记录
            conversation_spark_id = spark_storage.save_conversation_spark(spark)
            
            # 更新知识节点引用统计
            for sc in spark_citations:
                if sc.get("node_id"):
                    spark_storage.update_knowledge_node_citation(
                        rag_id=rag_id,
                        node_id=sc["node_id"],
                        spark_value=spark.spark_value,
                        content_preview=sc.get("content", "")[:100],
                        source_file=sc.get("source_file", "")
                    )
            
            # 更新用户档案
            spark_storage.update_user_profile(user_id)
            
            # 发送光源值事件
            yield f"data: {json.dumps({'type': 'spark', 'data': {'conversation_id': conversation_spark_id, 'spark_value': spark.spark_value, 'nft_eligible': spark.nft_eligible, 'scores': {'base': spark.base_score, 'citation': spark.citation_score, 'activation': spark.activation_score, 'behavior': spark.behavior_score}}}, ensure_ascii=False)}\n\n"
        
        except Exception as spark_error:
            print(f"Spark calculation error: {spark_error}")
            # 光源计算失败不影响主流程
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        print(f"Stream error: {e}")
        import traceback
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"


def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    text = text.strip()
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence ending
            for sep in ['。', '！', '？', '.', '!', '?', '\n\n', '\n']:
                idx = text.rfind(sep, start + chunk_size // 2, end)
                if idx > start:
                    end = idx + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


def find_relevant_chunks(query: str, chunks: List[str], top_k: int = 5) -> List[tuple]:
    """
    Find most relevant chunks using improved keyword matching.
    Returns list of (chunk, score) tuples.
    """
    # Clean query
    query_clean = query.lower().replace('?', '').replace('？', '').replace('是什么', '').replace('有哪些', '')
    
    # Extract keywords with better Chinese handling
    query_words = set()
    
    # Split by spaces and common delimiters
    for word in re.split(r'[\s,，、。！？!?]+', query_clean):
        if len(word) >= 2:
            query_words.add(word)
        # Extract 2-character combinations from Chinese text
        if len(word) >= 2:
            for i in range(len(word) - 1):
                query_words.add(word[i:i+2])
    
    # Add domain-specific keywords based on question type
    question_patterns = {
        '技术': ['技术', '框架', '架构', '工具', '语言', '库', 'api', 'sdk'],
        '核心': ['核心', '主要', '关键', '重要', '基础'],
        '功能': ['功能', '特性', '能力', '支持'],
        '使用': ['使用', '用于', '采用', '实现'],
    }
    
    for keyword, related in question_patterns.items():
        if keyword in query_clean:
            query_words.update(related)
    
    scored_chunks = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = 0
        matched_terms = []
        
        for word in query_words:
            if len(word) >= 2:
                count = chunk_lower.count(word)
                if count > 0:
                    weight = len(word) * (1 + count * 0.5)  # More occurrences = higher score
                    score += weight
                    matched_terms.append(word)
        
        # Bonus for chunks containing multiple different query terms
        unique_matches = len(set(matched_terms))
        if unique_matches >= 2:
            score *= (1 + unique_matches * 0.2)
        
        # Bonus for structural markers (headers, lists)
        if any(marker in chunk for marker in ['###', '##', '#', '•', '1)', '2)', 'A.', 'B.', '步骤', 'Step']):
            score *= 1.2
        
        if score > 0:
            scored_chunks.append((chunk, score))
    
    # Sort by score and return top_k
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    
    # If no matches, return first few chunks as context
    if not scored_chunks and chunks:
        return [(chunk, 0.1) for chunk in chunks[:top_k]]
    
    return scored_chunks[:top_k]


def build_citation_system_prompt(mode: ResponseMode, enable_web_search: bool) -> str:
    """Build system prompt based on response mode."""
    base_prompt = """你是一个专业的文档研究助手。你的任务是基于检索到的文档内容和可能的网络搜索结果来回答用户问题。

回答要求：
1. 准确性：只基于提供的内容回答，不要编造信息
2. 引用：在回答中使用 [^1], [^2] 等标注引用来源
3. 结构：回答要清晰、有条理"""

    if mode == ResponseMode.CONCISE:
        base_prompt += "\n4. 简洁：回答要简短精炼，直击要点"
    elif mode == ResponseMode.DETAILED:
        base_prompt += "\n4. 详细：提供全面深入的分析，包含更多细节"
    else:  # NORMAL
        base_prompt += "\n4. 平衡：提供适中长度的完整回答"
    
    if enable_web_search:
        base_prompt += "\n5. 网络信息：如果使用了网络搜索结果，请标明来源并注明是网络信息"
    
    return base_prompt


async def generate_llm_response(system_prompt: str, user_message: str, workspace_path: Path) -> str:
    """
    Generate LLM response using available backends.
    Priority: Anthropic > OpenAI > Local Runner
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Try Anthropic
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Anthropic error: {e}")
    
    # Try OpenAI
    if openai_key:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "max_tokens": 4096
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI error: {e}")
    
    # Try Ollama (local LLM) - preferred for document QA
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Build a combined prompt for Ollama
            combined_prompt = f"{system_prompt}\n\n{user_message}"
            
            response = await client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": "qwen2.5:7b",  # or your preferred local model
                    "prompt": combined_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2048
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("response", "")
                if answer and len(answer) > 10:
                    print(f"📋 [LLM] Ollama response success, length: {len(answer)}")
                    return answer
    except Exception as e:
        print(f"Ollama error: {e}")
    
    # Try local AI Partner Runner as final fallback
    runner_url = os.getenv("AI_PARTNER_RUNNER_URL", "http://localhost:9001")
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{runner_url}/v1/aipartner/chat",
                json={
                    "question": user_message,
                    "workspace_name": workspace_path.name if workspace_path else "default",
                    "system_prompt": system_prompt
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", data.get("content", ""))
                # Validate the answer - reject if it looks like logs
                if answer and not answer.strip().startswith('{') and '"event"' not in answer:
                    return answer
    except Exception as e:
        print(f"Runner error: {e}")
    
    return ""


def generate_fallback_response(
    question: str, 
    context: str, 
    mode: ResponseMode,
    web_results: List[Dict[str, Any]]
) -> str:
    """
    Generate a fallback response when LLM is not available.
    Uses the retrieved context directly with improved extraction.
    """
    response = "根据检索到的内容：\n\n"
    
    # Extract text fragments from context (removing metadata markers)
    clean_context = context
    for marker in ['【文档相关内容】', '【文档检索结果】', '【网络搜索结果】', '[文档片段', '(相关度:']:
        clean_context = clean_context.replace(marker, '')
    
    # Split into meaningful segments
    segments = re.split(r'[\n。！？!?]', clean_context)
    
    # Build query keywords
    query_clean = question.lower().replace('?', '').replace('？', '').replace('是什么', '').replace('有哪些', '')
    query_words = set()
    for word in re.split(r'[\s,，、]+', query_clean):
        if len(word) >= 2:
            query_words.add(word)
            # Extract 2-char combinations
            for i in range(len(word) - 1):
                query_words.add(word[i:i+2])
    
    # Add domain keywords
    for keyword in ['技术', '核心', '框架', '架构', '功能', '特性']:
        if keyword in question:
            query_words.add(keyword)
    
    relevant = []
    for seg in segments:
        seg = seg.strip()
        if not seg or len(seg) < 15:
            continue
        
        seg_lower = seg.lower()
        # Score this segment
        score = sum(1 for word in query_words if word in seg_lower and len(word) >= 2)
        
        if score > 0:
            relevant.append((seg, score))
    
    # Sort by score
    relevant.sort(key=lambda x: x[1], reverse=True)
    
    if relevant:
        top_segments = relevant[:5]
        for i, (sent, _) in enumerate(top_segments, 1):
            response += f"{sent}。[^{i}]\n\n"
        
        response += "\n---\n**引用来源:**\n"
        for i, (sent, _) in enumerate(top_segments, 1):
            preview = sent[:100] + "..." if len(sent) > 100 else sent
            response += f"[^{i}]: {preview}\n"
    elif context.strip():
        # If no keyword matches, return first part of context
        first_chunk = context[:1500]
        response += first_chunk + "\n\n[^1]\n"
        response += "\n---\n**引用来源:**\n"
        response += f"[^1]: {first_chunk[:100]}...\n"
    else:
        response = "抱歉，无法从文档中找到与您问题直接相关的内容。请尝试用不同的方式提问。"
    
    # Add web search results if available
    if web_results:
        response += "\n\n**网络搜索结果:**\n"
        for i, result in enumerate(web_results, 1):
            response += f"\n{i}. **{result['title']}**\n{result['snippet']}\n"
            if result.get('url'):
                response += f"   来源: {result['url']}\n"
    
    return response


@citation_chat_router.post("/{rag_id}/chat-with-citations")
async def chat_with_citations(
    rag_id: str,
    request: CitationChatRequest,
    current_user: dict = Depends(get_current_user),
    workspace_path: Path = Depends(get_user_workspace)
):
    """
    Chat with a RAG and get responses with inline citations.
    Supports web search integration.
    """
    user_id = current_user["user_id"]
    document_content = ""
    page_offset_map = {}
    rag_workspace = None
    
    # 首先尝试从元数据获取文件内容
    metadata = load_rag_metadata_from_file()
    print(f"📋 [DEBUG] user_id: {user_id}, rag_id: {rag_id}")
    print(f"📋 [DEBUG] metadata keys: {list(metadata.keys())}")
    
    if user_id in metadata and rag_id in metadata[user_id]:
        rag_info = metadata[user_id][rag_id]
        file_path = rag_info.get("file_path", "")
        print(f"📋 [DEBUG] rag_info: {rag_info}")
        print(f"📋 [DEBUG] file_path from metadata: {file_path}")
        
        if file_path:
            full_path = Path(file_path)
            if not full_path.is_absolute():
                full_path = Path(__file__).parent.parent / file_path
            
            print(f"📋 [DEBUG] full_path: {full_path}")
            print(f"📋 [DEBUG] full_path exists: {full_path.exists()}")
            
            if full_path.exists():
                try:
                    if str(full_path).lower().endswith('.pdf'):
                        # Extract text from PDF
                        print(f"📋 [DEBUG] Extracting PDF text from: {full_path}")
                        document_content = extract_pdf_text(full_path)
                        print(f"📋 [DEBUG] PDF extracted, content length: {len(document_content)} chars")
                    else:
                        # Read text file directly
                        with open(full_path, "r", encoding="utf-8") as f:
                            document_content = f.read()
                except Exception as e:
                    print(f"❌ Error reading document: {e}")
    
    # 如果没有从元数据找到，尝试从 workspace 获取
    if not document_content:
        rag_workspace = find_rag_workspace(workspace_path, rag_id)
        if rag_workspace is not None:
            document_content, page_offset_map = get_rag_document_content(rag_workspace, rag_id)
    
    print(f"📋 [DEBUG] Final document_content length: {len(document_content)}")
    print(f"📋 [DEBUG] document_content preview: {document_content[:200]}...")
    
    if not document_content.strip():
        raise HTTPException(
            status_code=404,
            detail="No document content found for this RAG"
        )
    
    # Parse response mode
    try:
        mode = ResponseMode(request.response_mode)
    except ValueError:
        mode = ResponseMode.NORMAL
    
    return StreamingResponse(
        stream_citation_response(
            request.question,
            document_content,
            mode,
            rag_workspace,
            user_id,
            rag_id,
            enable_web_search=request.enable_web_search,
            conversation_id=request.conversation_id
        ),
        media_type="text/event-stream"
    )


def load_rag_metadata_from_file() -> dict:
    """从数据库加载 RAG 元数据"""
    from core.database import get_connection, _row_to_dict
    result = {}
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, name, file_path, created_at FROM rags WHERE status = 'active'")
            for row in cursor.fetchall():
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
    except Exception as e:
        print(f"Error loading RAG metadata from database: {e}")
    return result


@citation_chat_router.get("/{rag_id}/document-info")
async def get_document_info(
    rag_id: str,
    current_user: dict = Depends(get_current_user),
    workspace_path: Path = Depends(get_user_workspace)
):
    """
    Get information about the documents in a RAG.
    First tries to get info from metadata, then falls back to workspace.
    """
    user_id = current_user["user_id"]
    documents = []
    
    # 首先从元数据获取文件信息
    metadata = load_rag_metadata_from_file()
    if user_id in metadata and rag_id in metadata[user_id]:
        rag_info = metadata[user_id][rag_id]
        file_path = rag_info.get("file_path", "")
        
        if file_path and Path(file_path).exists():
            file_stat = Path(file_path).stat()
            documents.append({
                "name": Path(file_path).name,
                "path": file_path,
                "size": file_stat.st_size,
                "type": "upload",
                "created_at": rag_info.get("created_at", "")
            })
    
    # 如果没有从元数据找到，尝试从 workspace 目录获取
    if not documents:
        rag_workspace = find_rag_workspace(workspace_path, rag_id)
        
        if rag_workspace is not None:
            notes_dir = rag_workspace / "notes"
            uploads_dir = rag_workspace / "uploads"
            
            if notes_dir.exists():
                for fp in notes_dir.glob("*"):
                    if fp.is_file():
                        documents.append({
                            "name": fp.name,
                            "path": str(fp.relative_to(rag_workspace)),
                            "size": fp.stat().st_size,
                            "type": "note"
                        })
            
            if uploads_dir.exists():
                for fp in uploads_dir.glob("*"):
                    if fp.is_file():
                        documents.append({
                            "name": fp.name,
                            "path": str(fp.relative_to(rag_workspace)),
                            "size": fp.stat().st_size,
                            "type": "upload"
                        })
    
    return {
        "rag_id": rag_id,
        "documents": documents,
        "total_count": len(documents)
    }


@citation_chat_router.get("/{rag_id}/pdf-url")
async def get_pdf_url(
    rag_id: str,
    current_user: dict = Depends(get_current_user),
    workspace_path: Path = Depends(get_user_workspace)
):
    """
    Get the URL for a PDF file in the RAG (if available).
    First tries to get from database metadata, then falls back to workspace.
    """
    user_id = current_user["user_id"]
    
    # 首先从数据库获取文件路径
    metadata = load_rag_metadata_from_file()
    if user_id in metadata and rag_id in metadata[user_id]:
        rag_info = metadata[user_id][rag_id]
        file_path = rag_info.get("file_path", "")
        
        if file_path:
            full_path = Path(file_path)
            if full_path.exists() and full_path.suffix.lower() == ".pdf":
                return {
                    "pdf_url": f"/v1/rag/{rag_id}/file/{full_path.name}",
                    "pdf_name": full_path.name,
                    "file_path": str(full_path)
                }
    
    # 备选：在 workspace 目录查找
    rag_workspace = find_rag_workspace(workspace_path, rag_id)
    if rag_workspace is not None:
        uploads_dir = rag_workspace / "uploads"
        notes_dir = rag_workspace / "notes"
        
        pdf_files = []
        for search_dir in [uploads_dir, notes_dir]:
            if search_dir.exists():
                pdf_files.extend(search_dir.glob("*.pdf"))
        
        if pdf_files:
            pdf_path = pdf_files[0]
            return {
                "pdf_url": f"/v1/rag/{rag_id}/file/{pdf_path.name}",
                "pdf_name": pdf_path.name,
                "file_path": str(pdf_path)
            }
    
    return {"pdf_url": None, "message": "No PDF files found"}


@citation_chat_router.get("/{rag_id}/document-content")
async def get_document_content(
    rag_id: str,
    current_user: dict = Depends(get_current_user),
    workspace_path: Path = Depends(get_user_workspace)
):
    """
    Get the text content of documents in the RAG.
    First tries to get content from metadata file path, then falls back to workspace.
    """
    user_id = current_user["user_id"]
    document_content = ""
    
    # 首先从元数据获取文件路径并读取内容
    metadata = load_rag_metadata_from_file()
    if user_id in metadata and rag_id in metadata[user_id]:
        rag_info = metadata[user_id][rag_id]
        file_path = rag_info.get("file_path", "")
        
        if file_path and Path(file_path).exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    document_content = f.read()
            except Exception:
                # 如果是 PDF，可能需要特殊处理
                pass
    
    # 如果没有从元数据找到内容，尝试从 workspace 获取
    if not document_content:
        rag_workspace = find_rag_workspace(workspace_path, rag_id)
        if rag_workspace is not None:
            document_content, _ = get_rag_document_content(rag_workspace, rag_id)
    
    if not document_content:
        raise HTTPException(status_code=404, detail="Document content not found")
    
    return {
        "content": document_content,
        "rag_id": rag_id
    }


@citation_chat_router.get("/{rag_id}/file/{filename}")
async def serve_file(
    rag_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user),
    workspace_path: Path = Depends(get_user_workspace)
):
    """
    Serve a file from the RAG.
    First tries to get from database metadata, then falls back to workspace.
    """
    from fastapi.responses import FileResponse
    import urllib.parse
    
    user_id = current_user["user_id"]
    decoded_filename = urllib.parse.unquote(filename)
    
    def get_content_type(fname):
        if fname.lower().endswith('.pdf'):
            return "application/pdf"
        elif fname.lower().endswith('.txt'):
            return "text/plain"
        elif fname.lower().endswith('.md'):
            return "text/markdown"
        return "application/octet-stream"
    
    # 首先从数据库获取文件路径
    metadata = load_rag_metadata_from_file()
    if user_id in metadata and rag_id in metadata[user_id]:
        rag_info = metadata[user_id][rag_id]
        file_path_str = rag_info.get("file_path", "")
        
        if file_path_str:
            file_path = Path(file_path_str)
            if file_path.exists() and file_path.is_file():
                if file_path.name == decoded_filename or decoded_filename in str(file_path):
                    return FileResponse(
                        path=file_path,
                        media_type=get_content_type(file_path.name),
                        filename=file_path.name
                    )
    
    # 备选：在 workspace 目录查找
    rag_workspace = find_rag_workspace(workspace_path, rag_id)
    if rag_workspace is not None:
        for search_dir in [rag_workspace / "notes", rag_workspace / "uploads"]:
            file_path = search_dir / decoded_filename
            if file_path.exists() and file_path.is_file():
                return FileResponse(
                    path=file_path,
                    media_type=get_content_type(decoded_filename),
                    filename=decoded_filename
                )
    
    raise HTTPException(status_code=404, detail="File not found")


@citation_chat_router.delete("/{rag_id}/conversation")
async def clear_conversation(
    rag_id: str,
    conversation_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Clear conversation history for a RAG.
    """
    user_id = current_user["user_id"]
    conv_key = f"{user_id}:{rag_id}:{conversation_id or 'default'}"
    
    if conv_key in conversation_history:
        del conversation_history[conv_key]
    
    return {"message": "Conversation history cleared", "rag_id": rag_id}


@citation_chat_router.post("/{rag_id}/web-search")
async def web_search(
    rag_id: str,
    query: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Perform a web search (standalone endpoint).
    """
    results = await perform_web_search(query, num_results=10)
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }
