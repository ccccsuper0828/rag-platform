import os
from typing import Any, Dict, Tuple

import httpx

from core.metrics import JsonlMetricsLogger
from core.rag_builder import RagBuilder


async def build_session(
    arch: str, rag_id: str, file_path: str, metrics: JsonlMetricsLogger, user_id: str = None
) -> Tuple[Dict[str, Any], str]:
    """
    AI Partner only:
    - Parse file into extracted_text (baseline parser for file support)
    - Send extracted_text to host-side AI Partner Runner (Claude Code)
    - Support multi-tenant isolation via user_id
    """
    arch = (arch or "aipartner").lower()
    if arch not in ("aipartner", "ai-partner", "ai_partner"):
        raise ValueError("Only arch=aipartner is supported.")

    runner_url = os.getenv("AI_PARTNER_RUNNER_URL", "http://localhost:9001").rstrip("/")

    with metrics.time_block("aipartner_parse"):
        parser = RagBuilder(init_models=False)
        _, extracted_text = parser.extract_documents(file_path, metrics=None)

    # 传递 user_id 给 runner 以实现租户隔离
    payload = {
        "rag_id": rag_id, 
        "file_name": os.path.basename(file_path), 
        "extracted_text": extracted_text,
        "user_id": user_id  # 添加用户ID用于workspace隔离
    }
    with metrics.time_block("aipartner_runner_build"):
        async with httpx.AsyncClient(timeout=1800.0) as client:
            resp = await client.post(f"{runner_url}/v1/aipartner/build", json=payload)
            if resp.status_code >= 400:
                raise ValueError(f"AI Partner runner build failed: {resp.status_code} {resp.text}")

    session = {
        "arch": "aipartner", 
        "type": "aipartner_remote", 
        "runner_url": runner_url, 
        "rag_id": rag_id,
        "user_id": user_id  # 保存用户ID到session
    }
    return session, extracted_text


async def query_session(
    session: Dict[str, Any], 
    question: str, 
    metrics: JsonlMetricsLogger,
    memory_context: str = ""
):
    """
    Return Claude Code output directly (no post-processing/proxy reformatting).
    Supports multi-tenant isolation and memory context.
    """
    if session.get("type") != "aipartner_remote":
        raise ValueError("Only aipartner_remote session type is supported.")

    runner_url = session["runner_url"].rstrip("/")
    rag_id = session.get("rag_id") or metrics.rag_id
    user_id = session.get("user_id")  # 获取用户ID
    
    # 如果有记忆上下文，将其添加到问题前面
    enhanced_question = question
    if memory_context:
        enhanced_question = f"【用户记忆】\n{memory_context}\n\n【问题】\n{question}"
    
    payload = {
        "rag_id": rag_id,
        "messages": [{"role": "user", "content": enhanced_question}],
        "stream": False,
        "mode": "claude",
        "show_tool_trace": True,
        "user_id": user_id,  # 传递用户ID给runner
    }
    with metrics.time_block("aipartner_remote_chat", {"question": question}):
        async with httpx.AsyncClient(timeout=600.0) as client:
            resp = await client.post(f"{runner_url}/v1/aipartner/chat", json=payload)
            if resp.status_code >= 400:
                raise ValueError(f"AI Partner runner chat failed: {resp.status_code} {resp.text}")
            return resp.text, None


