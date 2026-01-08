from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from dotenv import dotenv_values, load_dotenv
from knowledge_graph import KnowledgeGraphBuilder
from metadata_extractor import MetadataExtractor, MetadataStore
from query_filter import QueryFilterExtractor

# LEANN hybrid search integration
try:
    from leann_search import hybrid_search, build_leann_index, ENABLE_LEANN
    LEANN_AVAILABLE = True
except ImportError:
    LEANN_AVAILABLE = False
    ENABLE_LEANN = False
    def hybrid_search(*args, **kwargs):
        return []
    def build_leann_index(*args, **kwargs):
        return False


# Load env from the runner directory (not the current working dir).
_HERE = Path(__file__).resolve().parent
load_dotenv(dotenv_path=_HERE / ".env", override=False)
load_dotenv(dotenv_path=_HERE / "env", override=False)
load_dotenv(override=False)


def _dotenv_overrides() -> Dict[str, str]:
    """
    Hot-load env values from runner-local .env files so users can update credentials
    without restarting the runner process.
    """
    merged: Dict[str, str] = {}
    for p in (_HERE / ".env", _HERE / "env"):
        try:
            if p.exists():
                vals = dotenv_values(p)  # type: ignore[arg-type]
                for k, v in (vals or {}).items():
                    if isinstance(k, str) and isinstance(v, str) and v != "":
                        merged[k] = v
        except Exception:
            continue
    return merged

_RETRY_AFTER_RE = re.compile(r"try\\s+again\\s+after\\s+(\\d+)\\s*seconds?", re.IGNORECASE)
_MASK_AK_RE = re.compile(r"<ak-[^>]+>")


def _parse_retry_after_seconds(msg: str) -> Optional[float]:
    m = _RETRY_AFTER_RE.search(msg or "")
    if not m:
        return None
    try:
        return float(int(m.group(1)))
    except Exception:
        return None


def _is_retriable_claude_error(msg: str) -> bool:
    s = (msg or "").lower()
    # Moonshot/Anthropic style
    if "rate_limit" in s or "429" in s or "try again after" in s:
        return True
    # common transient failures
    if (
        "timed out" in s
        or "timeout" in s
        or "connection error" in s
        or "econnreset" in s
        or "temporarily" in s
        or "503" in s
        or "502" in s
        or "504" in s
    ):
        return True
    return False


def _is_session_conflict_error(msg: str) -> bool:
    """Check if error is 'session already in use' conflict."""
    s = (msg or "").lower()
    return "session" in s and "already in use" in s


def _is_auth_error(msg: str) -> bool:
    s = (msg or "").lower()
    return "invalid api key" in s or "please run /login" in s or "authentication_failed" in s


def _is_quota_error(msg: str) -> bool:
    s = (msg or "").lower()
    return "exceeded_current_quota" in s or "insufficient balance" in s or "recharge" in s or "billing" in s


def _retry_params() -> Tuple[int, float, float]:
    # max_retries counts *extra* attempts after the first failure
    max_retries = int(os.getenv("AI_PARTNER_CLAUDE_MAX_RETRIES", "3"))
    base = float(os.getenv("AI_PARTNER_CLAUDE_RETRY_BASE_SECONDS", "1.0"))
    cap = float(os.getenv("AI_PARTNER_CLAUDE_RETRY_MAX_SECONDS", "8.0"))
    return max(0, max_retries), max(0.0, base), max(0.0, cap)


def _sleep_backoff(attempt: int, err_msg: str) -> float:
    # If provider told us exactly how long to wait, respect it.
    ra = _parse_retry_after_seconds(err_msg)
    if ra is not None:
        wait = ra
    else:
        _, base, cap = _retry_params()
        wait = min(cap, base * (2**max(0, attempt)))
    # add small jitter
    wait = wait + random.random() * 0.25
    time.sleep(wait)
    return wait


def _retry_prompt(prompt: str) -> str:
    # When a request fails mid-way, instruct Claude to continue rather than restart.
    return (
        prompt
        + "\n\n（系统提示：刚才请求可能因限流/网络中断未完成。"
        + "如果你已经开始回答，请从中断处继续，不要重复已输出内容；否则正常回答。）\n继续"
    )


def _sanitize_error_text(msg: str) -> str:
    s = (msg or "").strip()
    if not s:
        return s
    # Mask Moonshot-style key fragments that sometimes appear in error messages.
    s = _MASK_AK_RE.sub("<ak-***MASKED***>", s)
    # Mask any literal auth token if it appears.
    tok = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
    if tok and tok in s:
        s = s.replace(tok, "***MASKED***")
    return s


def _dedupe_delta(already: str, new: str) -> str:
    """
    Claude Code stream-json may emit both incremental deltas and a later full message.
    This function returns only the non-duplicated suffix to emit.
    """
    if not new:
        return ""
    if not already:
        return new
    # If we've already seen this content, drop it.
    if new in already:
        return ""
    if already.endswith(new):
        return ""
    # If the new chunk contains everything we've already emitted, emit only the tail.
    if new.startswith(already):
        return new[len(already) :]
    # Otherwise, compute maximal overlap where already's suffix == new's prefix.
    max_k = min(len(already), len(new))
    for k in range(max_k, 0, -1):
        if already.endswith(new[:k]):
            return new[k:]
    return new


def _claude_bin() -> str:
    # Prefer explicit path; fallback to PATH.
    return os.getenv("CLAUDE_BIN", str(Path.home() / ".npm-global" / "bin" / "claude"))


def _skill_src() -> Path:
    p = os.getenv("AI_PARTNER_SKILL_SRC", "").strip()
    if not p:
        raise RuntimeError("AI_PARTNER_SKILL_SRC is required")
    return Path(p).expanduser()


def _workspaces_dir() -> Path:
    p = os.getenv("AI_PARTNER_WORKSPACES_DIR", "").strip()
    if not p:
        raise RuntimeError("AI_PARTNER_WORKSPACES_DIR is required")
    return Path(p).expanduser()


def _workspace(rag_id: str, user_id: Optional[str] = None) -> Path:
    """
    获取 workspace 路径，支持多租户隔离
    如果提供了 user_id，使用用户专属的 workspace
    """
    if user_id:
        # 多租户模式：每个用户有独立的目录
        return _workspaces_dir() / f"user_{user_id}" / rag_id
    else:
        # 兼容旧模式：直接使用 rag_id
        return _workspaces_dir() / rag_id


def _ensure_dirs(ws: Path) -> None:
    ws.mkdir(parents=True, exist_ok=True)
    (ws / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
    (ws / "config").mkdir(exist_ok=True)
    (ws / "notes").mkdir(exist_ok=True)
    (ws / "scripts").mkdir(exist_ok=True)
    (ws / "knowledge_graph").mkdir(exist_ok=True)  # For knowledge graph storage


def _claude_session_id_path(ws: Path) -> Path:
    return ws / "config" / "claude_session_id.txt"


def _get_or_create_claude_session_id(ws: Path, force_new: bool = False) -> str:
    p = _claude_session_id_path(ws)
    if not force_new:
        try:
            if p.exists():
                sid = p.read_text(encoding="utf-8", errors="ignore").strip()
                if sid:
                    return sid
        except Exception:
            pass
    sid = str(uuid.uuid4())
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(sid, encoding="utf-8")
    return sid


def _reset_claude_session_id(ws: Path) -> str:
    """Force create a new session ID (used when session conflict occurs)."""
    return _get_or_create_claude_session_id(ws, force_new=True)

def _uploads_manifest(ws: Path) -> Path:
    return ws / "config" / "uploads.jsonl"

def _append_upload_record(ws: Path, file_name: str) -> None:
    rec = {"file_name": file_name, "ts": int(__import__("time").time())}
    _uploads_manifest(ws).parent.mkdir(parents=True, exist_ok=True)
    with open(_uploads_manifest(ws), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def _latest_uploaded_filename(ws: Path) -> Optional[str]:
    path = _uploads_manifest(ws)
    if not path.exists():
        return None
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, dict) and isinstance(obj.get("file_name"), str):
                return obj["file_name"]
    except Exception:
        return None
    return None

def _resolve_target_note(ws: Path) -> Optional[str]:
    """
    Heuristic: pick the note corresponding to the latest uploaded file name.
    If not found, and there's exactly one note, return it.
    """
    notes = _list_notes(ws)
    if not notes:
        return None
    latest = _latest_uploaded_filename(ws)
    if latest:
        stem = Path(latest).stem
        candidate = stem + ".md"
        if candidate in notes:
            return candidate
    if len(notes) == 1:
        return notes[0]
    return None

def _looks_like_doc_summary_question(q: str) -> bool:
    s = (q or "").strip()
    needles = ["这篇文档", "这个文档", "这份文档", "这篇文章", "这份文件", "讲了什么", "主要说了什么", "总结", "概述"]
    return any(n in s for n in needles)

def _list_notes(ws: Path) -> List[str]:
    notes_dir = ws / "notes"
    if not notes_dir.exists():
        return []
    files = [p.name for p in notes_dir.glob("**/*") if p.is_file()]
    files.sort()
    return files

def _looks_like_uploads_question(q: str) -> bool:
    s = (q or "").strip()
    needles = ["我上传了什么", "我上传了哪些", "我上传的是什么", "上传了什么", "上传了哪些", "我传了什么"]
    return any(n in s for n in needles)


def _install_skill(ws: Path) -> Path:
    src = _skill_src()
    if not src.exists():
        raise RuntimeError(f"Skill source not found: {src}")
    dst = ws / ".claude" / "skills" / "ai-partner-chat"
    # sync copy (overwrite)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def _ensure_personas(skill_dir: Path, ws: Path) -> None:
    assets = skill_dir / "assets"
    user_tpl = assets / "user-persona-template.md"
    ai_tpl = assets / "ai-persona-template.md"
    user_dst = ws / "config" / "user-persona.md"
    ai_dst = ws / "config" / "ai-persona.md"
    if not user_dst.exists() and user_tpl.exists():
        shutil.copyfile(user_tpl, user_dst)
    if not ai_dst.exists() and ai_tpl.exists():
        shutil.copyfile(ai_tpl, ai_dst)


def _write_default_chunk_and_index(ws: Path) -> Path:
    """
    Create scripts/chunk_and_index.py in workspace.
    This is a simple, deterministic chunker (paragraph-based) that conforms to ai-partner-chat schema,
    without asking Claude to generate per-file chunking code.
    """
    target = ws / "scripts" / "chunk_and_index.py"
    if target.exists():
        return target

    code = f"""\
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent / ".claude/skills/ai-partner-chat/scripts"))

from chunk_schema import Chunk, validate_chunk
from vector_indexer import VectorIndexer

MAX_CHARS = 1200

def chunk_note_file(filepath: str) -> List[Chunk]:
    p = Path(filepath)
    text = p.read_text(encoding="utf-8", errors="ignore")
    # naive split by blank lines, then pack to MAX_CHARS
    parts = [s.strip() for s in text.split("\\n\\n") if s.strip()]
    chunks: List[Chunk] = []
    buf = ""
    idx = 0
    def flush(b: str):
        nonlocal idx
        if not b.strip():
            return
        c: Chunk = {{
            "content": b.strip(),
            "metadata": {{
                "filename": p.name,
                "filepath": str(p.resolve()),
                "chunk_id": idx,
                "chunk_type": "paragraph",
            }},
        }}
        validate_chunk(c)
        chunks.append(c)
        idx += 1

    for part in parts:
        if len(buf) + len(part) + 2 <= MAX_CHARS:
            buf = (buf + "\\n\\n" + part).strip() if buf else part
        else:
            flush(buf)
            buf = part
    flush(buf)
    return chunks

def main():
    indexer = VectorIndexer(db_path="./vector_db")
    indexer.initialize_db()
    all_chunks: List[Chunk] = []
    for note_file in Path("./notes").glob("**/*"):
        if note_file.is_file():
            all_chunks.extend(chunk_note_file(str(note_file)))
    indexer.index_chunks(all_chunks)

if __name__ == "__main__":
    main()
"""
    target.write_text(code, encoding="utf-8")
    return target


def _venv_python(ws: Path) -> Path:
    return ws / "venv" / "bin" / "python"

def _index_enabled() -> bool:
    # Ripgrep search doesn't need indexing, always return False
    return False


def _ensure_venv(ws: Path, skill_dir: Path) -> None:
    if not _index_enabled():
        return
    py = _venv_python(ws)
    if not py.exists():
        subprocess.run(["python3", "-m", "venv", str(ws / "venv")], cwd=ws, check=True)
    req = skill_dir / "scripts" / "requirements.txt"
    if not req.exists():
        raise RuntimeError(f"Missing requirements: {req}")
    subprocess.run([str(py), "-m", "pip", "install", "-r", str(req)], cwd=ws, check=True)


def _run_chunk_index(ws: Path) -> None:
    if not _index_enabled():
        return
    py = _venv_python(ws)
    if not py.exists():
        raise RuntimeError("venv python missing; did venv creation fail?")
    script = ws / "scripts" / "chunk_and_index.py"
    if not script.exists():
        raise RuntimeError("chunk_and_index.py missing")
    subprocess.run([str(py), str(script)], cwd=ws, check=True)


def _read_file(path: Path, max_chars: int = 20000) -> str:
    if not path.exists():
        return ""
    s = path.read_text(encoding="utf-8", errors="ignore")
    return s[:max_chars]

def _is_template_persona(text: str) -> bool:
    s = (text or "").strip()
    if not s:
        return True
    # Heuristic: templates contain bracket placeholders
    return "[" in s and "]" in s and "Persona" in s

def _notes_corpus(ws: Path, max_chars: int = 24000) -> str:
    """
    Read notes/* and return a truncated corpus for persona generation.
    """
    parts: List[str] = []
    for p in sorted((ws / "notes").glob("**/*")):
        if not p.is_file():
            continue
        txt = _read_file(p, max_chars=8000)
        if not txt.strip():
            continue
        parts.append(f"\n\n=== {p.name} ===\n{txt}")
        if sum(len(x) for x in parts) >= max_chars:
            break
    corpus = "".join(parts)
    return corpus[:max_chars]

def _notes_max_mtime(ws: Path) -> float:
    max_m = 0.0
    for p in (ws / "notes").glob("**/*"):
        if p.is_file():
            try:
                max_m = max(max_m, p.stat().st_mtime)
            except Exception:
                pass
    return max_m

def _persona_signals_path(ws: Path) -> Path:
    return ws / "config" / "persona-signals.md"

def _persona_config_int(name: str, default: int) -> int:
    try:
        v = int(os.getenv(name, str(default)).strip())
        return max(1, v)
    except Exception:
        return default

def _build_persona_signals(ws: Path, force: bool) -> str:
    """
    Stage-1: summarize each note into "persona signals" (structured bullets).
    Saves to config/persona-signals.md and returns the content.
    """
    signals_path = _persona_signals_path(ws)
    if not force and signals_path.exists():
        try:
            if signals_path.stat().st_mtime >= _notes_max_mtime(ws):
                return _read_file(signals_path, max_chars=80000)
        except Exception:
            pass

    max_notes = _persona_config_int("AI_PARTNER_PERSONA_MAX_NOTES", 20)
    note_max_chars = _persona_config_int("AI_PARTNER_PERSONA_NOTE_MAX_CHARS", 6000)
    total_max_chars = _persona_config_int("AI_PARTNER_PERSONA_SIGNALS_MAX_CHARS", 60000)

    # pick most recently modified notes first
    note_files = [p for p in (ws / "notes").glob("**/*") if p.is_file()]
    note_files.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    note_files = note_files[:max_notes]

    system_prompt = (
        "你是 Persona 信号提取器。你将阅读用户的单篇笔记文本，"
        "提炼出对用户画像有用的“信号”。不要编造事实；不确定就标注为“可能/推测”。"
        "输出必须是 Markdown，且尽量短。"
    )

    def summarize_one(filename: str, text: str) -> str:
        prompt = f"""\
请从下面这篇笔记中提取“用户画像信号”，输出为 Markdown，严格按以下结构：

- 事实/背景（只写笔记明确提到的）
- 偏好/厌恶（语言风格、沟通方式、做事方式、工具偏好）
- 当前项目/目标（明确提到的）
- 反复出现的主题/关注点（可推断，但要写“可能/倾向”）
- 可用于 AI 伴侣的回应偏好（例如：更喜欢步骤/更喜欢简洁/更喜欢反问）

注意：
- 不要输出“根据你提供的…”这类前言
- 不要输出任何 JSON
- 尽量控制在 12 条要点以内

【文件名】{filename}
【笔记正文】
{text}

只输出 Markdown 要点。
"""
        out = subprocess.run(
            [_claude_bin(), "-p", "--output-format", "text", "--system-prompt", system_prompt, prompt],
            cwd=ws,
            env=_claude_env(),
            capture_output=True,
            text=True,
        )
        if out.returncode != 0:
            raise RuntimeError(out.stderr.strip() or out.stdout.strip() or "persona signals extraction failed")
        return out.stdout.strip()

    blocks: List[str] = []
    total = 0
    for p in note_files:
        txt = _read_file(p, max_chars=note_max_chars)
        if not txt.strip():
            continue
        block = summarize_one(p.name, txt)
        if not block.strip():
            continue
        header = f"\n\n## {p.name}\n"
        chunk = header + block + "\n"
        blocks.append(chunk)
        total += len(chunk)
        if total >= total_max_chars:
            break

    content = "# Persona Signals (auto-generated)\n" + "".join(blocks)
    signals_path.write_text(content, encoding="utf-8")
    return content

def _generate_personas(ws: Path, force: bool = False) -> None:
    """
    Use Claude Code to generate user-persona.md and ai-persona.md from notes.
    Requires runner env (ANTHROPIC_* vars) to be set (Kimi/Claude).
    """
    if os.getenv("AI_PARTNER_GENERATE_PERSONAS", "1").strip().lower() not in ("1", "true", "yes", "on"):
        return

    user_path = ws / "config" / "user-persona.md"
    ai_path = ws / "config" / "ai-persona.md"

    user_existing = _read_file(user_path, max_chars=20000)
    ai_existing = _read_file(ai_path, max_chars=20000)

    if not force:
        # If user already edited personas (no placeholder-like template), keep them.
        if user_existing.strip() and not _is_template_persona(user_existing):
            user_ok = True
        else:
            user_ok = False
        if ai_existing.strip() and not _is_template_persona(ai_existing):
            ai_ok = True
        else:
            ai_ok = False
        if user_ok and ai_ok:
            return

    # === Two-stage persona generation ===
    # Stage-1: per-note persona signals (structured summaries)
    signals = _build_persona_signals(ws, force=force)
    if not signals.strip():
        return

    # Backup if overwriting
    def backup(p: Path):
        if p.exists():
            bak = p.with_suffix(p.suffix + ".bak")
            try:
                shutil.copyfile(p, bak)
            except Exception:
                pass

    system_prompt = (
        "你是一个 AI 伴侣产品的 Persona 生成器。"
        "你的任务是根据用户的笔记/文本，推断并输出清晰、具体、可执行的 persona。"
        "不要编造具体事实；不确定就用“可能/倾向/偏好”表达。输出必须是 Markdown。"
    )

    def sanitize_markdown_start(text: str, heading: str) -> str:
        s = (text or "").lstrip()
        if s.startswith(heading):
            return s
        idx = s.find(heading)
        if idx != -1:
            return s[idx:]
        return s

    user_prompt = f"""\
你将基于“Persona Signals”（多篇笔记的结构化摘要）生成最终的 `user-persona.md`（Markdown）。
要求：
- 尽可能具体（职业/关注主题/沟通偏好/工作风格/学习目标/当前项目/常用工具等）
- 必须替换掉模板里的占位符（不要出现 [xxx] 这种）
- 如果信息不足，保留结构但写“未知/未提及”，并给出你推断的“可能偏好”（用“可能/倾向”措辞）
- 严禁输出任何前言/解释；输出必须从 `# User Persona` 开始

【Persona Signals】
{signals}

请直接输出最终的 `user-persona.md` 全文（不要加额外解释）。
"""

    ai_prompt = f"""\
你将基于“Persona Signals”（多篇笔记的结构化摘要）生成最终的 `ai-persona.md`（Markdown），作为“AI 伴侣”的人设与回应策略。
要求：
- 贴合用户偏好：语气、结构、鼓励/追问方式
- 给出明确的“回应策略模板”（例如：先共情一句→再给 3 条行动建议→再问 1 个澄清问题）
- 说明如何自然引用用户笔记（避免生硬引用）
- 必须替换掉模板里的占位符（不要出现 [xxx] 这种）
- 严禁输出任何前言/解释；输出必须从 `# AI Persona` 开始

【Persona Signals】
{signals}

请直接输出最终的 `ai-persona.md` 全文（不要加额外解释）。
"""

    # Generate user persona
    if force or _is_template_persona(user_existing):
        backup(user_path)
        user_out = subprocess.run(
            [_claude_bin(), "-p", "--output-format", "text", "--system-prompt", system_prompt, user_prompt],
            cwd=ws,
            env=_claude_env(),
            capture_output=True,
            text=True,
        )
        if user_out.returncode != 0:
            raise RuntimeError(user_out.stderr.strip() or user_out.stdout.strip() or "persona generation failed")
        user_md = sanitize_markdown_start(user_out.stdout, "# User Persona")
        user_path.write_text(user_md.strip() + "\n", encoding="utf-8")

    # Generate ai persona
    if force or _is_template_persona(ai_existing):
        backup(ai_path)
        ai_out = subprocess.run(
            [_claude_bin(), "-p", "--output-format", "text", "--system-prompt", system_prompt, ai_prompt],
            cwd=ws,
            env=_claude_env(),
            capture_output=True,
            text=True,
        )
        if ai_out.returncode != 0:
            raise RuntimeError(ai_out.stderr.strip() or ai_out.stdout.strip() or "persona generation failed")
        ai_md = sanitize_markdown_start(ai_out.stdout, "# AI Persona")
        ai_path.write_text(ai_md.strip() + "\n", encoding="utf-8")


def _retrieve_notes(ws: Path, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Hybrid search: combines LEANN semantic search with ripgrep keyword search.
    
    LEANN provides:
    - Semantic understanding (finds "ML" when searching "machine learning")
    - 97% storage savings vs traditional vector DBs
    - High precision retrieval
    
    Falls back to ripgrep-only if LEANN is not available.
    
    Returns list of dicts with 'content', 'filepath', 'filename', 'line_number', 'metadata' keys.
    """
    notes_dir = ws / "notes"
    if not notes_dir.exists():
        return []
    
    # ============ LEANN Hybrid Search (Primary) ============
    if LEANN_AVAILABLE and ENABLE_LEANN:
        try:
            print(f"🔍 Using LEANN hybrid search for: {query[:50]}...")
            results = hybrid_search(
                workspace_path=ws,
                query=query,
                top_k=top_k,
                use_leann=True,
            )
            if results:
                print(f"✅ LEANN returned {len(results)} results")
                # Load metadata for each result
                metadata_store = MetadataStore(ws)
                for r in results:
                    filepath = r.get('filepath', '')
                    if filepath:
                        metadata = metadata_store.get_metadata(filepath)
                        r['metadata'] = metadata.to_dict() if metadata else {}
                return results
            else:
                print("⚠️ LEANN returned no results, falling back to ripgrep")
        except Exception as e:
            print(f"⚠️ LEANN search failed: {e}, falling back to ripgrep")
    
    # ============ Ripgrep Fallback (with metadata filtering) ============
    try:
        import ripgrepy
    except ImportError:
        # Final fallback: simple file content search
        return _simple_file_search(ws, query, top_k)
    
    # Step 1: Extract filters from query (LangExtract-RAG inspired)
    filter_extractor = QueryFilterExtractor()
    filters = filter_extractor.extract_filters(query)
    
    if filters:
        print(f"🎯 Smart filters extracted: {filter_extractor.explain_filters(filters)}")
    
    # Step 2: Load metadata store
    metadata_store = MetadataStore(ws)
    
    # Step 3: Filter files by metadata if filters exist
    candidate_files = None
    if filters:
        matching_files = metadata_store.filter_files(filters)
        if matching_files:
            candidate_files = [Path(f) for f in matching_files if Path(f).exists()]
            print(f"📋 Filtered to {len(candidate_files)} files matching metadata criteria")
    
    # Step 4: Search with ripgrep
    results = []
    try:
        if candidate_files:
            all_matches = []
            for file_path in candidate_files[:10]:
                try:
                    rg = ripgrepy.Ripgrepy(query, str(file_path))
                    rg = rg.E("utf-8").C(5)
                    matches = rg.json().run()
                    if hasattr(matches, 'as_dict'):
                        if isinstance(matches.as_dict, list):
                            all_matches.extend(matches.as_dict)
                        else:
                            all_matches.append(matches.as_dict)
                except:
                    continue
            matches = all_matches
        else:
            rg = ripgrepy.Ripgrepy(query, str(notes_dir))
            rg = rg.glob("*.md").glob("*.txt").E("utf-8").C(5)
            rg_output = rg.json().run()
            if hasattr(rg_output, 'as_dict'):
                matches = rg_output.as_dict if isinstance(rg_output.as_dict, list) else [rg_output.as_dict]
            else:
                matches = []
                output_str = rg.run().as_string
                for line in output_str.split('\n'):
                    if line.strip():
                        try:
                            match = json.loads(line)
                            matches.append(match)
                        except:
                            continue
        
        # Step 5: Process matches and add metadata
        seen_files = set()
        for match in matches[:top_k * 3]:
            if isinstance(match, dict):
                data = match.get('data', {})
                path_data = data.get('path', {})
                lines_data = data.get('lines', {})
                
                filepath = path_data.get('text', '') if isinstance(path_data, dict) else str(path_data)
                content = lines_data.get('text', '') if isinstance(lines_data, dict) else str(lines_data)
                line_num = data.get('line_number', 0)
                
                if filepath and content:
                    filepath = str(Path(filepath).resolve())
                    filename = Path(filepath).name
                    
                    if filepath not in seen_files:
                        seen_files.add(filepath)
                        
                        metadata = metadata_store.get_metadata(filepath)
                        metadata_dict = metadata.to_dict() if metadata else {}
                        
                        results.append({
                            'content': content.strip(),
                            'filepath': filepath,
                            'filename': filename,
                            'line_number': line_num,
                            'chunk_id': 0,
                            'chunk_type': 'grep_match',
                            'metadata': metadata_dict,
                        })
                        if len(results) >= top_k:
                            break
    except Exception as e:
        print(f"Ripgrep search failed: {e}, falling back to file content search")
        return _simple_file_search(ws, query, top_k, candidate_files)
    
    return results[:top_k]


def _simple_file_search(ws: Path, query: str, top_k: int, candidate_files: Optional[List[Path]] = None) -> List[Dict[str, Any]]:
    """Simple file content search fallback."""
    notes_dir = ws / "notes"
    metadata_store = MetadataStore(ws)
    results = []
    
    search_files = candidate_files if candidate_files else list(notes_dir.glob("**/*.md"))[:top_k * 2]
    for note_file in search_files:
        if note_file.is_file():
            try:
                content = note_file.read_text(encoding="utf-8", errors="ignore")
                if query.lower() in content.lower():
                    metadata = metadata_store.get_metadata(str(note_file.resolve()))
                    metadata_dict = metadata.to_dict() if metadata else {}
                    
                    results.append({
                        'content': content[:1000],
                        'filepath': str(note_file.resolve()),
                        'filename': note_file.name,
                        'line_number': 0,
                        'chunk_id': 0,
                        'chunk_type': 'file_match',
                        'metadata': metadata_dict,
                    })
                    if len(results) >= top_k:
                        break
            except:
                continue
    
    return results


def _is_identity_question(text: str) -> bool:
    """Detect if user is asking about their identity or persona."""
    identity_patterns = [
        "我是谁", "你知道我是谁", "认识我吗", "了解我吗",
        "你对我了解", "我的身份", "我的背景", "关于我",
        "who am i", "do you know me", "about me"
    ]
    text_lower = text.lower()
    return any(p in text_lower for p in identity_patterns)


def _is_document_question(text: str) -> bool:
    """Detect if user is asking about document content."""
    doc_patterns = [
        "这篇", "这个文档", "文档内容", "总结", "摘要",
        "讲了什么", "说了什么", "主要内容", "文件说",
        "this document", "summarize", "what does it say"
    ]
    text_lower = text.lower()
    return any(p in text_lower for p in doc_patterns)


def _build_partner_prompt(ws: Path, messages: List[Dict[str, str]]) -> str:
    user_persona = _read_file(ws / "config" / "user-persona.md")
    ai_persona = _read_file(ws / "config" / "ai-persona.md")
    
    # current user message is last user role
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = m.get("content", "")
            break
    
    note_files = [p for p in (ws / "notes").glob("**/*") if p.is_file()]
    note_names = ", ".join([p.name for p in note_files[:20]])
    history_text = "\n".join([f'{m.get("role","")}: {m.get("content","")}' for m in messages[-6:]])
    
    # ============ Smart Question Routing ============
    # 1. Identity questions → Use User Persona directly
    if _is_identity_question(last_user):
        prompt = f"""\
用户问的是关于"他/她是谁"的问题。请根据 User Persona 中的信息，用亲切自然的方式回答。

【User Persona（从笔记分析得出）】
{user_persona if user_persona.strip() else "(还没有用户画像，请让用户多上传一些笔记)"}

【对话历史】
{history_text}

回答要求：
- 直接回答，像老朋友一样
- 从画像中提炼关键特征（职业、风格、偏好）
- 如果画像不足，坦诚说"我对你的了解还不多，多聊聊吧"
- 不要列举画像的原文，要用自己的话说

请回答：
"""
        return prompt
    
    # 2. Document questions → Use note content directly
    if _is_document_question(last_user):
        excerpts = []
        for note_file in note_files[:3]:  # Latest 3 notes
            excerpts.append(f"**{note_file.name}**:\n{_read_file(note_file, max_chars=6000)}")
        notes_content = "\n\n---\n\n".join(excerpts) if excerpts else "(没有笔记文件)"
        
        prompt = f"""\
用户问的是关于文档内容的问题。请直接阅读笔记内容并回答。

【笔记内容】
{notes_content}

【对话历史】
{history_text}

回答要求：
- 直接基于笔记内容回答
- 可以总结、分析、提炼要点
- 使用自然语言，不要机械引用

请回答：
"""
        return prompt
    
    # 3. General questions → Lightweight RAG
    relevant = _retrieve_notes(ws, last_user, top_k=3)
    
    notes_text = ""
    if relevant:
        for i, n in enumerate(relevant[:3]):
            content = n.get("content") or ""
            filename = n.get("filename", "")
            notes_text += f"\n[{filename}]\n{content[:800]}\n"
    else:
        # Fallback: include first note excerpt
        if note_files:
            notes_text = _read_file(note_files[0], max_chars=2000)
    
    notes_available = bool(notes_text.strip())
    
    # Simplified AI persona (extract key traits only)
    ai_style = ""
    if ai_persona.strip():
        # Extract just the core style, not all the rules
        ai_style = "回复风格：简洁直接，先给结论再解释，必要时用代码块。"
    
    prompt = f"""\
你是用户的 AI 伴侣，了解用户的背景和偏好。请自然地对话。

【用户特征】
{user_persona[:1500] if user_persona else "(暂无画像)"}

【相关笔记】
{notes_text if notes_available else "(没有找到相关笔记)"}

【对话历史】
{history_text}

{ai_style}

请直接回答用户的问题，不要过度格式化。
"""
    return prompt


def _build_skill_prompt(ws: Path, messages: List[Dict[str, str]]) -> str:
    """
    Build a prompt that explicitly invokes the ai-partner-chat skill (slash command)
    and forces Claude Code to read the target note when the user asks "this document".
    """
    history = "\n".join([f'{m.get("role","")}: {m.get("content","")}' for m in messages[-12:]])
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = m.get("content", "")
            break

    notes = _list_notes(ws)
    target = _resolve_target_note(ws)

    guidance = ""
    if _looks_like_doc_summary_question(last_user):
        if target:
            guidance = (
                f"你需要总结的“这篇文档”默认指向当前会话最新上传的笔记文件：`notes/{target}`。\n"
                "在回答前请先使用 Read 工具读取该文件（不要凭空猜测）。\n"
            )
        elif notes:
            guidance = (
                "用户说“这篇文档”但当前会话下有多份 notes 文件，请先列出文件名并追问用户要总结哪一份。\n"
            )

    formatting = (
        "【输出格式要求】\n"
        "- 必须分段输出，段落之间空一行\n"
        "- 每个段落用这些小图标符号之一开头：◆、▶、✓、→（不要用 emoji）\n"
        "- 建议段落结构（按需取用）：\n"
        "  ◆ 结论（1-2句）\n"
        "  ▶ 要点（3-6条，短句）\n"
        "  ✓ 引用到的笔记内容（如有，列出关键信息）\n"
        "  → 下一步建议（2-4条，可执行）\n"
        "  → 需要我确认的问题（最多1个）\n"
    )

    # 直接读取并包含用户画像，避免 Claude Code 访问权限问题
    user_persona = _read_file(ws / "config" / "user-persona.md", max_chars=3000)
    ai_persona = _read_file(ws / "config" / "ai-persona.md", max_chars=2000)
    
    persona_section = ""
    if user_persona.strip():
        persona_section = f"【用户画像（已加载）】\n{user_persona[:2000]}\n\n"
    if ai_persona.strip():
        persona_section += f"【AI 回复策略（已加载）】\n{ai_persona[:1500]}\n\n"

    return (
        "/ai-partner-chat\n"
        "你在一个本地 workspace 中运行。用户画像和笔记内容已直接提供给你，无需再次读取文件。\n\n"
        + persona_section
        + f"【Notes Inventory】{', '.join(notes) if notes else '(none)'}\n"
        + (f"【Target Note】notes/{target}\n" if target else "")
        + ("\n" + guidance if guidance else "\n")
        + "\n"
        + formatting
        + "【Conversation History】\n"
        + history
        + "\n\n请直接给出 assistant 回复，不要说需要读取文件或没有访问权限。\n"
    )


def _claude_env() -> Dict[str, str]:
    env = dict(os.environ)
    # Hot-load runner-local .env overrides on every invocation (no runner restart needed).
    env.update(_dotenv_overrides())
    # Ensure claude sees project as trusted (we control workspace dir)
    env.setdefault("CLAUDE_DISABLE_TELEMETRY", "1")
    return env


def _run_claude_print(ws: Path, prompt: str, use_session: bool = False) -> str:
    claude = _claude_bin()
    if not Path(claude).exists():
        raise RuntimeError(f"claude binary not found at {claude}. Set CLAUDE_BIN or install claude.")
    
    # Build args - skip session-id for simpler single-turn mode
    args = [claude, "-p", "--output-format", "text"]
    if use_session:
        sid = _get_or_create_claude_session_id(ws)
        args.extend(["--session-id", sid])
    args.append(prompt)
    
    proc = subprocess.run(
        args,
        cwd=ws,
        env=_claude_env(),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"claude exit {proc.returncode}")
    return proc.stdout


def _stream_claude_text(ws: Path, prompt: str, use_session: bool = False) -> Iterable[bytes]:
    """
    Use `--output-format stream-json` then extract delta text best-effort.
    """
    claude = _claude_bin()
    if not Path(claude).exists():
        raise RuntimeError(f"claude binary not found at {claude}. Set CLAUDE_BIN or install claude.")
    
    args = [claude, "-p", "--verbose", "--output-format", "stream-json"]
    if use_session:
        sid = _get_or_create_claude_session_id(ws)
        args.extend(["--session-id", sid])
    args.append(prompt)
    
    p = subprocess.Popen(
        args,
        cwd=ws,
        env=_claude_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def emit(s: str) -> bytes:
        return s.encode("utf-8", errors="ignore")

    # stream-json is line-delimited JSON
    assert p.stdout is not None
    last_text: str = ""
    emitted: str = ""
    last_error_text: str = ""
    for line in p.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        # best-effort extraction (Claude Code stream-json)
        delta = _extract_text_from_event(obj)
        if delta:
            last_text = delta
            to_emit = _dedupe_delta(emitted, delta)
            if to_emit:
                emitted += to_emit
                yield emit(to_emit)
        # capture explicit error/result payloads even if we later fail with non-zero rc
        if isinstance(obj, dict):
            if isinstance(obj.get("error"), str) and obj.get("error"):
                # e.g. {"error":"authentication_failed"}
                if isinstance(obj.get("result"), str) and obj.get("result"):
                    last_error_text = obj["result"]
            if obj.get("type") == "result" and obj.get("is_error") is True and isinstance(obj.get("result"), str):
                last_error_text = obj["result"]

    rc = p.wait()
    if rc != 0:
        err = (p.stderr.read() if p.stderr else "") if p.stderr else ""
        msg = err.strip() or (last_error_text.strip() if last_error_text else "") or (last_text.strip() if last_text else "")
        raise RuntimeError(msg or f"claude exit {rc}")

def _run_claude_with_tool_trace_print(ws: Path, prompt: str) -> str:
    """
    Non-stream: run claude in stream-json mode, then convert events to a single text transcript.
    This approximates the local Claude Code experience with tool call trace.
    """
    out_parts: List[str] = []
    for b in _stream_claude_with_tool_trace(ws, prompt):
        out_parts.append(b.decode("utf-8", errors="ignore"))
        if sum(len(x) for x in out_parts) > 200000:
            break
    return "".join(out_parts)

def _stream_claude_with_tool_trace(ws: Path, prompt: str, use_session: bool = False) -> Iterable[bytes]:
    """
    Run Claude Code in print+stream-json mode with tools enabled and emit a human-readable trace:
    - Assistant text deltas
    - Tool invocations (best-effort)
    """
    claude = _claude_bin()
    if not Path(claude).exists():
        raise RuntimeError(f"claude binary not found at {claude}. Set CLAUDE_BIN or install claude.")

    # NOTE: `--add-dir` takes a variadic list of directories; without a `--` separator,
    # the positional `prompt` may be mistakenly consumed as a directory, causing:
    # "Input must be provided either through stdin or as a prompt argument when using --print"
    args = [
        claude,
        "-p",
        "--verbose",
        "--output-format",
        "stream-json",
        "--include-partial-messages",
        "--permission-mode",
        "dontAsk",
        "--tools",
        "default",
        "--add-dir",
        str(ws),
        "--",
        prompt,
    ]
    p = subprocess.Popen(
        args,
        cwd=ws,
        env=_claude_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def emit(s: str) -> bytes:
        return s.encode("utf-8", errors="ignore")

    def _extract_tool(obj: Dict[str, Any]) -> Optional[Tuple[str, Any]]:
        # Try common shapes
        name = obj.get("tool") or obj.get("tool_name") or obj.get("name")
        inp = obj.get("input") or obj.get("tool_input") or obj.get("arguments")
        if isinstance(name, str) and (name.lower() in ("bash", "read", "edit") or "tool" in obj.get("type", "").lower()):
            return name, inp
        # Some events nest tool info
        if isinstance(obj.get("tool_use"), dict):
            tu = obj["tool_use"]
            name = tu.get("name")
            inp = tu.get("input")
            if isinstance(name, str):
                return name, inp
        return None

    assert p.stdout is not None
    last_text: str = ""
    emitted: str = ""
    last_error_text: str = ""
    for line in p.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue

        # Assistant text delta
        delta = _extract_text_from_event(obj)
        if delta:
            last_text = delta
            to_emit = _dedupe_delta(emitted, delta)
            if to_emit:
                emitted += to_emit
                yield emit(to_emit)
            continue

        # Capture explicit error events so rc!=0 can surface a useful message
        if isinstance(obj, dict):
            if isinstance(obj.get("error"), str) and obj.get("error"):
                if isinstance(obj.get("result"), str) and obj.get("result"):
                    last_error_text = obj["result"]
            if obj.get("type") == "result" and obj.get("is_error") is True and isinstance(obj.get("result"), str):
                last_error_text = obj["result"]

        # Tool trace (best-effort)
        if isinstance(obj, dict):
            tool = _extract_tool(obj)
            if tool:
                name, inp = tool
                if isinstance(inp, str):
                    shown = inp.strip()
                else:
                    try:
                        shown = json.dumps(inp, ensure_ascii=False)
                    except Exception:
                        shown = str(inp)
                yield emit(f"\n\n⏺ {name}({shown})\n")

    rc = p.wait()
    if rc != 0:
        err = (p.stderr.read() if p.stderr else "") if p.stderr else ""
        msg = err.strip() or (last_error_text.strip() if last_error_text else "") or (last_text.strip() if last_text else "")
        raise RuntimeError(msg or f"claude exit {rc}")


def _run_claude_resume_print(ws: Path, resume_session_id: str, prompt: str) -> str:
    claude = _claude_bin()
    if not Path(claude).exists():
        raise RuntimeError(f"claude binary not found at {claude}. Set CLAUDE_BIN or install claude.")
    proc = subprocess.run(
        [claude, "-p", "--resume", resume_session_id, "--output-format", "text", prompt],
        cwd=ws,
        env=_claude_env(),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"claude exit {proc.returncode}")
    return proc.stdout


def _stream_claude_resume_with_tool_trace(ws: Path, resume_session_id: str, prompt: str) -> Iterable[bytes]:
    """
    Resume an existing Claude Code session and continue with tools enabled.
    """
    claude = _claude_bin()
    if not Path(claude).exists():
        raise RuntimeError(f"claude binary not found at {claude}. Set CLAUDE_BIN or install claude.")
    args = [
        claude,
        "-p",
        "--resume",
        resume_session_id,
        "--verbose",
        "--output-format",
        "stream-json",
        "--include-partial-messages",
        "--permission-mode",
        "dontAsk",
        "--tools",
        "default",
        "--add-dir",
        str(ws),
        "--",
        prompt,
    ]
    p = subprocess.Popen(
        args,
        cwd=ws,
        env=_claude_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def emit(s: str) -> bytes:
        return s.encode("utf-8", errors="ignore")

    last_text: str = ""
    emitted: str = ""
    last_error_text: str = ""
    assert p.stdout is not None
    for line in p.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue

        delta = _extract_text_from_event(obj)
        if delta:
            last_text = delta
            to_emit = _dedupe_delta(emitted, delta)
            if to_emit:
                emitted += to_emit
                yield emit(to_emit)
            continue

        if isinstance(obj, dict):
            if isinstance(obj.get("error"), str) and obj.get("error"):
                if isinstance(obj.get("result"), str) and obj.get("result"):
                    last_error_text = obj["result"]
            if obj.get("type") == "result" and obj.get("is_error") is True and isinstance(obj.get("result"), str):
                last_error_text = obj["result"]

    rc = p.wait()
    if rc != 0:
        err = (p.stderr.read() if p.stderr else "") if p.stderr else ""
        msg = err.strip() or (last_error_text.strip() if last_error_text else "") or (last_text.strip() if last_text else "")
        raise RuntimeError(msg or f"claude exit {rc}")


def _extract_text_from_event(obj: Any) -> str:
    """
    Claude Code `--output-format stream-json` events can be:
    - {"delta": "..."}  (streaming text)
    - {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}
    - {"type":"result","result":"..."}
    """
    if not isinstance(obj, dict):
        return ""
    # direct strings
    for k in ("delta", "content", "text"):
        v = obj.get(k)
        if isinstance(v, str) and v:
            return v
    # assistant message content list
    msg = obj.get("message")
    if isinstance(msg, dict):
        c = msg.get("content")
        if isinstance(c, str) and c:
            return c
        if isinstance(c, list):
            parts: List[str] = []
            for item in c:
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            if parts:
                return "".join(parts)
    # result summary
    if isinstance(obj.get("result"), str) and obj.get("result"):
        return obj["result"]
    return ""

class BuildRequest(BaseModel):
    rag_id: str
    file_name: str = "uploaded.txt"
    extracted_text: str
    user_id: Optional[str] = None  # 多租户支持


class BuildResponse(BaseModel):
    rag_id: str
    ok: bool
    workspace: str
    warning: Optional[str] = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    rag_id: str
    messages: List[ChatMessage] = Field(..., min_length=1, max_length=20)
    stream: bool = False
    force_regenerate_personas: bool = False
    # Default to "claude" so responses come directly from Claude Code (agent style).
    mode: Literal["partner", "claude"] = "claude"
    show_tool_trace: bool = True
    user_id: Optional[str] = None  # 多租户支持


app = FastAPI(title="AI Partner Runner", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/health")
def health():
    return {
        "ok": True,
        "claude": str(_claude_bin()),
        "skill_src": str(_skill_src()),
        "workspaces_dir": str(_workspaces_dir()),
    }


@app.post("/v1/aipartner/build", response_model=BuildResponse)
def build(req: BuildRequest):
    try:
        # 使用 user_id 创建隔离的 workspace
        ws = _workspace(req.rag_id, req.user_id)
        _ensure_dirs(ws)
        skill_dir = _install_skill(ws)
        _ensure_personas(skill_dir, ws)

        # Save extracted text into notes
        note_path = ws / "notes" / (Path(req.file_name).stem + ".md")
        note_path.write_text(req.extracted_text, encoding="utf-8")
        _append_upload_record(ws, req.file_name)

        # Skip vector indexing - we use ripgrep for search instead
        # _write_default_chunk_and_index(ws)
        # _ensure_venv(ws, skill_dir)
        # _run_chunk_index(ws)

        # Generate personas from notes (fills templates)
        warning = None
        try:
            _generate_personas(ws, force=False)
        except Exception as e:
            msg = str(e)
            # If Claude is unavailable (auth/quota/transient), don't fail the build.
            # Users can regenerate personas later when API is available.
            if _is_auth_error(msg):
                warning = "personas_skipped_auth_error"
            elif _is_quota_error(msg):
                warning = "personas_skipped_quota_error"
            elif _is_retriable_claude_error(msg):
                warning = "personas_skipped_transient_error"
            else:
                raise

        # Build knowledge graph from notes
        try:
            kg_builder = KnowledgeGraphBuilder(ws)
            kg_builder.build_from_notes()
            kg_builder.save_graph()
        except Exception as e:
            print(f"Knowledge graph build failed (non-fatal): {e}")
        
        # ============ Build LEANN semantic index ============
        # This enables semantic search with 97% storage savings
        if LEANN_AVAILABLE and ENABLE_LEANN:
            try:
                print("🧠 Building LEANN semantic index...")
                leann_success = build_leann_index(ws, force_rebuild=False)
                if leann_success:
                    print("✅ LEANN semantic index built successfully")
                else:
                    print("⚠️ LEANN index build failed (non-fatal, ripgrep will be used)")
            except Exception as e:
                print(f"LEANN index build failed (non-fatal): {e}")
        else:
            print("ℹ️ LEANN disabled or not available, using ripgrep-only search")
        
        # Extract and store metadata for all notes (LangExtract-RAG inspired)
        try:
            print("📊 Extracting document metadata...")
            extractor = MetadataExtractor()
            metadata_store = MetadataStore(ws)
            
            notes_dir = ws / "notes"
            if notes_dir.exists():
                for note_file in notes_dir.glob("**/*"):
                    if note_file.is_file() and note_file.suffix in ['.md', '.txt']:
                        try:
                            metadata = extractor.extract_from_file(note_file)
                            metadata_store.set_metadata(str(note_file.resolve()), metadata)
                            print(f"  ✓ {note_file.name}: {metadata.service} v{metadata.version} ({metadata.doc_type})")
                        except Exception as e:
                            print(f"  ⚠️  Failed to extract metadata from {note_file.name}: {e}")
                
                metadata_store.save()
                print(f"✅ Metadata extracted and saved for {len(metadata_store.metadata)} files")
        except Exception as e:
            print(f"Metadata extraction failed (non-fatal): {e}")

        # Vector DB is replaced by ripgrep search, no warning needed
        return BuildResponse(rag_id=req.rag_id, ok=True, workspace=str(ws), warning=warning)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"build failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/aipartner/chat")
def chat(req: ChatRequest):
    # 使用 user_id 获取正确的 workspace
    ws = _workspace(req.rag_id, req.user_id)
    if not ws.exists():
        raise HTTPException(status_code=404, detail="workspace not found; build first")

    # Optional: force regenerate personas before answering (when user updated notes/persona workflow)
    if req.force_regenerate_personas:
        try:
            _generate_personas(ws, force=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"persona regenerate failed: {e}")

    msgs = [m.model_dump() for m in req.messages]

    # Deterministic answer for "what did I upload" to avoid hallucinations.
    last_user = ""
    for m in reversed(msgs):
        if m.get("role") == "user":
            last_user = m.get("content", "")
            break
    if _looks_like_uploads_question(last_user):
        files = _list_notes(ws)
        if not files:
            return PlainTextResponse("我还没在这个会话下看到任何 notes 文件。请先上传/构建。", media_type="text/plain")
        return PlainTextResponse(
            "你当前会话下的 notes 文件：\n- " + "\n- ".join(files),
            media_type="text/plain",
        )

    if req.mode == "claude":
        # Use ai-partner-chat skill (slash command) so Claude behaves like local Claude Code workflow.
        prompt = _build_skill_prompt(ws, msgs)
    else:
        prompt = _build_partner_prompt(ws, msgs)
    sid = _get_or_create_claude_session_id(ws)
    if not req.stream:
        max_retries, _, _ = _retry_params()
        last_err: Optional[str] = None
        for attempt in range(max_retries + 1):
            try:
                # For Claude-mode retries, prefer resuming the same Claude Code session and sending "继续".
                if attempt == 0:
                    p = prompt
                else:
                    p = "继续"
                if req.mode == "claude" and req.show_tool_trace:
                    if attempt == 0:
                        out = _run_claude_with_tool_trace_print(ws, p)
                    else:
                        out = _run_claude_resume_print(ws, sid, p)
                else:
                    out = _run_claude_print(ws, p)
                return PlainTextResponse(out, media_type="text/plain")
            except Exception as e:
                last_err = str(e)
                # Handle session conflict by resetting session ID and retrying
                if _is_session_conflict_error(last_err):
                    sid = _reset_claude_session_id(ws)
                    # Retry with new session
                    continue
                # Do not 500 for common config/billing issues; return a readable message.
                if last_err and _is_auth_error(last_err):
                    safe = _sanitize_error_text(last_err)
                    return PlainTextResponse(
                        "→ 系统：Claude 鉴权失败（API key 未生效）。\n"
                        "请检查 Runner 的 `.env` 是否设置了 `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN`，保存后直接再发一次同样的问题即可（无需重启 Runner）。\n\n"
                        f"（错误信息：{safe}）",
                        media_type="text/plain",
                    )
                if last_err and _is_quota_error(last_err):
                    safe = _sanitize_error_text(last_err)
                    return PlainTextResponse(
                        "→ 系统：账户余额/配额不足，无法继续请求模型。\n"
                        "请先充值/调整套餐后再重试。\n\n"
                        f"（错误信息：{safe}）",
                        media_type="text/plain",
                    )
                if not _is_retriable_claude_error(last_err) or attempt >= max_retries:
                    break
                _sleep_backoff(attempt, last_err)

        # For retriable failures (e.g., 429), do not return 500; surface a friendly message.
        if last_err and _is_retriable_claude_error(last_err):
            safe_err = _sanitize_error_text(last_err)
            return PlainTextResponse(
                "→ 系统：触发限流/临时故障，已自动重试仍失败。\n"
                "请稍等 2-5 秒后再发送同一个问题。\n\n"
                f"（错误信息：{safe_err}）",
                media_type="text/plain",
            )
        raise HTTPException(status_code=500, detail=str(last_err or "unknown error"))

    def gen():
        nonlocal prompt  # Fix: declare prompt as nonlocal since it's reassigned later
        max_retries, _, _ = _retry_params()
        attempt = 0
        yielded_any = False
        tail_buf: List[str] = []

        def _record_tail(chunk: bytes) -> None:
            try:
                s = chunk.decode("utf-8", errors="ignore")
            except Exception:
                return
            if not s:
                return
            tail_buf.append(s)
            # keep last ~2k chars
            joined = "".join(tail_buf)
            if len(joined) > 2400:
                tail_buf.clear()
                tail_buf.append(joined[-2000:])

        while True:
            try:
                # Attempt 0: normal prompt
                # Retry: resume same session and say "继续" (Claude Code built-in behavior).
                if attempt == 0:
                    p = prompt
                    stream_iter = (
                        _stream_claude_with_tool_trace(ws, p)
                        if (req.mode == "claude" and req.show_tool_trace)
                        else _stream_claude_text(ws, p)
                    )
                else:
                    p = "继续"
                    stream_iter = (
                        _stream_claude_resume_with_tool_trace(ws, sid, p)
                        if (req.mode == "claude" and req.show_tool_trace)
                        else _stream_claude_text(ws, p)
                    )
                for b in stream_iter:
                    yielded_any = True
                    _record_tail(b)
                    yield b
                return
            except Exception as e:
                msg = str(e)
                safe_msg = _sanitize_error_text(msg)
                if not _is_retriable_claude_error(msg) or attempt >= max_retries:
                    yield f"\n\n→ 系统：发生错误：{safe_msg}".encode("utf-8")
                    return

                # If we already streamed something, try a "continue" run with a small tail context.
                if yielded_any:
                    tail = "".join(tail_buf).strip()
                    yield "\n\n→ 系统：遇到限流/临时故障，正在自动继续…\n\n".encode("utf-8")
                    extra = ""
                    if tail:
                        extra = (
                            "\n\n【上次输出末尾片段】\n"
                            + tail[-800:]
                            + "\n\n请从上述片段之后继续，不要重复已输出内容。\n继续"
                        )
                    prompt2 = prompt + extra
                    attempt += 1
                    prompt = prompt2  # type: ignore[assignment]
                    yielded_any = False
                    tail_buf.clear()
                    continue

                _sleep_backoff(attempt, msg)
                attempt += 1

    return StreamingResponse(gen(), media_type="text/plain")


class RegenerateRequest(BaseModel):
    rag_id: str
    force: bool = True
    user_id: Optional[str] = None  # 多租户支持


@app.post("/v1/aipartner/personas/generate")
def regenerate_personas(req: RegenerateRequest):
    ws = _workspace(req.rag_id, req.user_id)
    if not ws.exists():
        raise HTTPException(status_code=404, detail="workspace not found; build first")
    try:
        _generate_personas(ws, force=bool(req.force))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ReindexRequest(BaseModel):
    rag_id: str
    user_id: Optional[str] = None  # 多租户支持


@app.post("/v1/aipartner/index/rebuild")
def rebuild_index(req: ReindexRequest):
    """Rebuild is not needed with ripgrep - files are searched directly."""
    ws = _workspace(req.rag_id, req.user_id)
    if not ws.exists():
        raise HTTPException(status_code=404, detail="workspace not found; build first")
    return {"ok": True, "message": "Ripgrep search doesn't require indexing - files are searched directly"}


class KnowledgeGraphRequest(BaseModel):
    rag_id: str


class KnowledgeGraphRequest(BaseModel):
    rag_id: str
    user_id: Optional[str] = None  # 多租户支持


@app.post("/v1/aipartner/knowledge-graph")
def post_knowledge_graph(req: KnowledgeGraphRequest):
    """Get knowledge graph visualization data (POST)."""
    ws = _workspace(req.rag_id, req.user_id)
    if not ws.exists():
        raise HTTPException(status_code=404, detail="workspace not found; build first")
    
    try:
        kg_builder = KnowledgeGraphBuilder(ws)
        kg_builder.build_from_notes()
        graph_data = kg_builder.get_graph_for_visualization()
        return JSONResponse(content=graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build knowledge graph: {str(e)}")


@app.get("/v1/aipartner/knowledge-graph/{rag_id}")
def get_knowledge_graph(rag_id: str, user_id: Optional[str] = None):
    """Get knowledge graph visualization data (GET)."""
    ws = _workspace(rag_id, user_id)
    if not ws.exists():
        return JSONResponse(content={"nodes": [], "links": [], "message": "workspace not found"})
    
    try:
        kg_builder = KnowledgeGraphBuilder(ws)
        kg_builder.build_from_notes()
        graph_data = kg_builder.get_graph_for_visualization()
        return JSONResponse(content=graph_data)
    except Exception as e:
        print(f"Knowledge graph error: {e}")
        return JSONResponse(content={"nodes": [], "links": [], "message": str(e)})


# ──────────────────────────────────────────────────────────────────────────────
# 意图识别 API - 使用 Claude 进行精确的查询意图识别
# ──────────────────────────────────────────────────────────────────────────────

class IntentRequest(BaseModel):
    query: str
    context: Optional[str] = ""
    rag_id: Optional[str] = None
    user_id: Optional[str] = None


INTENT_PROMPT = """分析以下用户查询，识别其真实意图。

## 意图类型
- QUESTION: 提问，需要基于知识库回答
- SUMMARIZE: 总结请求
- SEARCH: 搜索请求
- ANALYZE: 分析请求
- COMPARE: 对比请求
- EXPLAIN: 解释请求
- CODE: 代码相关请求
- RESEARCH: 深度研究请求
- CHAT: 闲聊
- COMMAND: 系统命令
- IDENTITY: 身份询问（"你是谁"/"我是谁"等）

## 用户查询
{query}

## 上下文
{context}

以 JSON 格式返回：
```json
{{
  "primary_intent": "主要意图",
  "secondary_intents": [],
  "entities": ["关键实体"],
  "requires_knowledge_base": true/false,
  "requires_web_search": true/false,
  "confidence": 0.9,
  "suggested_action": "建议处理方式"
}}
```
"""


@app.post("/v1/aipartner/intent")
def recognize_intent(req: IntentRequest):
    """
    使用 Claude 进行精确的意图识别
    替代硬编码的关键词匹配
    """
    query = req.query.strip()
    context = req.context or ""
    
    # 快速规则检测常见意图
    query_lower = query.lower()
    
    # 身份询问
    if any(p in query_lower for p in ["你是谁", "我是谁", "who are you", "who am i", "介绍自己"]):
        return JSONResponse(content={
            "primary_intent": "IDENTITY",
            "secondary_intents": [],
            "entities": [],
            "requires_knowledge_base": True,
            "requires_web_search": False,
            "confidence": 0.98,
            "suggested_action": "读取用户/AI画像回答身份问题"
        })
    
    # 总结请求
    if any(p in query_lower for p in ["总结", "摘要", "概括", "summarize", "summary"]):
        return JSONResponse(content={
            "primary_intent": "SUMMARIZE",
            "secondary_intents": [],
            "entities": [],
            "requires_knowledge_base": True,
            "requires_web_search": False,
            "confidence": 0.92,
            "suggested_action": "对文档进行摘要"
        })
    
    # 深度研究
    if any(p in query_lower for p in ["深入研究", "详细分析", "全面了解", "research", "deep dive"]):
        return JSONResponse(content={
            "primary_intent": "RESEARCH",
            "secondary_intents": ["ANALYZE"],
            "entities": [],
            "requires_knowledge_base": True,
            "requires_web_search": True,
            "confidence": 0.88,
            "suggested_action": "启动深度研究模式"
        })
    
    # 代码相关
    if any(p in query_lower for p in ["代码", "函数", "实现", "code", "function", "debug", "bug"]):
        return JSONResponse(content={
            "primary_intent": "CODE",
            "secondary_intents": [],
            "entities": [],
            "requires_knowledge_base": True,
            "requires_web_search": False,
            "confidence": 0.85,
            "suggested_action": "处理代码相关请求"
        })
    
    # 对于复杂查询，使用 Claude 进行意图识别
    if req.rag_id and req.user_id:
        try:
            ws = _workspace(req.rag_id, req.user_id)
            if ws.exists():
                prompt = INTENT_PROMPT.format(query=query, context=context)
                sid = _get_or_create_claude_session_id(ws)
                
                # 使用 Claude 进行意图识别
                answer, _ = _call_claude_raw(ws, prompt, session_id=sid)
                
                # 尝试解析 JSON
                try:
                    json_start = answer.find("{")
                    json_end = answer.rfind("}") + 1
                    if json_start != -1 and json_end > json_start:
                        intent_data = json.loads(answer[json_start:json_end])
                        return JSONResponse(content=intent_data)
                except:
                    pass
        except Exception as e:
            print(f"Intent recognition with Claude failed: {e}")
    
    # 默认：普通问题
    return JSONResponse(content={
        "primary_intent": "QUESTION",
        "secondary_intents": [],
        "entities": query.split()[:5],
        "requires_knowledge_base": True,
        "requires_web_search": False,
        "confidence": 0.7,
        "suggested_action": "基于知识库回答问题"
    })


# ──────────────────────────────────────────────────────────────────────────────
# 实体提取 API - 使用 LLM 进行智能实体和关系提取
# ──────────────────────────────────────────────────────────────────────────────

class EntityExtractRequest(BaseModel):
    text: str
    max_length: int = 4000
    rag_id: Optional[str] = None
    user_id: Optional[str] = None


ENTITY_EXTRACT_PROMPT = """从以下文本中提取实体和关系。

## 实体类型
- Person: 人物
- Organization: 组织机构
- Technology: 技术相关
- Concept: 抽象概念
- Location: 地点
- Product: 产品或项目

## 关系类型
- USES: 使用
- IMPLEMENTS: 实现
- CREATED_BY: 创建
- PART_OF: 属于
- DEPENDS_ON: 依赖
- RELATED_TO: 相关

## 输入文本
{text}

以 JSON 格式返回：
```json
{{
  "entities": [
    {{"name": "名称", "type": "类型", "description": "描述"}}
  ],
  "relationships": [
    {{"source": "源实体", "target": "目标实体", "type": "关系类型"}}
  ]
}}
```
"""


@app.post("/v1/aipartner/entity-extract")
def extract_entities(req: EntityExtractRequest):
    """
    使用 LLM 进行智能实体和关系提取
    替代正则表达式硬编码方法
    """
    text = req.text[:req.max_length]
    
    if req.rag_id and req.user_id:
        try:
            ws = _workspace(req.rag_id, req.user_id)
            if ws.exists():
                prompt = ENTITY_EXTRACT_PROMPT.format(text=text)
                sid = _get_or_create_claude_session_id(ws)
                
                answer, _ = _call_claude_raw(ws, prompt, session_id=sid)
                
                try:
                    json_start = answer.find("{")
                    json_end = answer.rfind("}") + 1
                    if json_start != -1 and json_end > json_start:
                        result = json.loads(answer[json_start:json_end])
                        return JSONResponse(content=result)
                except:
                    pass
        except Exception as e:
            print(f"Entity extraction with Claude failed: {e}")
    
    # 回退到简单的正则提取
    entities = []
    relationships = []
    
    # 简单模式匹配
    tech_patterns = [
        r'\b(Python|JavaScript|TypeScript|React|Vue|FastAPI|Django|Docker|Kubernetes)\b',
        r'\b(RAG|LLM|GPT|Claude|BERT|NLP|ML|AI|API)\b',
    ]
    
    import re
    for pattern in tech_patterns:
        for match in re.finditer(pattern, text):
            entity_name = match.group(1)
            if not any(e["name"] == entity_name for e in entities):
                entities.append({
                    "name": entity_name,
                    "type": "Technology",
                    "description": f"从文本中提取的技术实体"
                })
    
    return JSONResponse(content={
        "entities": entities,
        "relationships": relationships,
        "source": "regex_fallback"
    })


# ========== 启动入口 ==========
if __name__ == "__main__":
    import uvicorn
    print("🚀 启动 AI Partner Runner...")
    uvicorn.run(app, host="0.0.0.0", port=9001)

