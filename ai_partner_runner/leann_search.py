"""
LEANN Hybrid Search for AI Partner Runner
==========================================
Provides semantic + keyword hybrid search for note retrieval.

This module replaces pure ripgrep search with LEANN-powered hybrid search:
- LEANN: semantic understanding ("机器学习" matches "ML", "deep learning")
- ripgrep: exact keyword matching (fallback, always available)
- Hybrid: combines both for best results

Usage:
    from leann_search import hybrid_search
    
    results = hybrid_search(
        workspace_path="/path/to/workspace",
        query="How does authentication work?",
        top_k=5
    )
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# Configuration
ENABLE_LEANN = os.getenv("ENABLE_LEANN", "true").lower() in ("true", "1", "yes")
LEANN_SEMANTIC_WEIGHT = float(os.getenv("LEANN_SEMANTIC_WEIGHT", "0.7"))
LEANN_KEYWORD_WEIGHT = float(os.getenv("LEANN_KEYWORD_WEIGHT", "0.3"))


@dataclass
class SearchResult:
    """Unified search result."""
    content: str
    filepath: str
    filename: str
    score: float = 0.0
    line_number: int = 0
    chunk_id: int = 0
    chunk_type: str = "hybrid"
    source: str = "hybrid"  # "leann", "ripgrep", or "hybrid"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _get_leann_searcher(workspace_path: Path):
    """Get LEANN HybridSearcher if available."""
    if not ENABLE_LEANN:
        return None
    
    try:
        # Add backend/core to path for leann_rag import
        backend_core = Path(__file__).parent.parent / "backend" / "core"
        if backend_core.exists() and str(backend_core) not in sys.path:
            sys.path.insert(0, str(backend_core))
        
        from leann_rag import HybridSearcher
        return HybridSearcher(workspace_path)
    except ImportError as e:
        logger.debug(f"LEANN not available: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to initialize LEANN searcher: {e}")
        return None


def _ripgrep_search(notes_dir: Path, query: str, top_k: int = 5) -> List[SearchResult]:
    """
    Fallback ripgrep keyword search.
    Compatible with original ai_partner_runner behavior.
    """
    if not notes_dir.exists():
        return []
    
    try:
        import ripgrepy
    except ImportError:
        logger.debug("ripgrepy not available")
        return []
    
    results = []
    try:
        rg = ripgrepy.Ripgrepy(query, str(notes_dir))
        rg = rg.glob("*.md").glob("*.txt").E("utf-8").C(5)
        
        try:
            rg_output = rg.json().run()
            if hasattr(rg_output, 'as_dict'):
                matches = rg_output.as_dict if isinstance(rg_output.as_dict, list) else [rg_output.as_dict]
            else:
                matches = []
        except Exception:
            matches = []
        
        seen_files = set()
        for match in matches[:top_k * 2]:
            if isinstance(match, dict):
                data = match.get('data', {})
                path_data = data.get('path', {})
                lines_data = data.get('lines', {})
                
                filepath = path_data.get('text', '') if isinstance(path_data, dict) else str(path_data)
                content = lines_data.get('text', '') if isinstance(lines_data, dict) else str(lines_data)
                line_num = data.get('line_number', 0)
                
                if filepath and content and filepath not in seen_files:
                    seen_files.add(filepath)
                    
                    # Score based on match count
                    score = content.lower().count(query.lower())
                    
                    results.append(SearchResult(
                        content=content.strip(),
                        filepath=str(Path(filepath).resolve()),
                        filename=Path(filepath).name,
                        score=float(score),
                        line_number=line_num,
                        source="ripgrep",
                        chunk_type="grep_match",
                    ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        
    except Exception as e:
        logger.debug(f"Ripgrep search failed: {e}")
    
    return results[:top_k]


def _reciprocal_rank_fusion(
    semantic_results: List[SearchResult],
    keyword_results: List[SearchResult],
    semantic_weight: float = LEANN_SEMANTIC_WEIGHT,
    keyword_weight: float = LEANN_KEYWORD_WEIGHT,
    k: int = 60,
) -> List[SearchResult]:
    """
    Merge results using Reciprocal Rank Fusion.
    
    RRF provides a robust way to combine rankings from different sources.
    """
    result_map: Dict[str, SearchResult] = {}
    scores: Dict[str, float] = {}
    
    # Process semantic results
    for rank, result in enumerate(semantic_results):
        key = f"{result.filepath}:{hash(result.content[:100])}"
        rrf_score = semantic_weight * (1.0 / (k + rank + 1))
        
        if key in scores:
            scores[key] += rrf_score
        else:
            scores[key] = rrf_score
            result_map[key] = result
    
    # Process keyword results
    for rank, result in enumerate(keyword_results):
        key = f"{result.filepath}:{hash(result.content[:100])}"
        rrf_score = keyword_weight * (1.0 / (k + rank + 1))
        
        if key in scores:
            scores[key] += rrf_score
        else:
            scores[key] = rrf_score
            result_map[key] = result
    
    # Sort by combined score
    sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
    
    merged = []
    for key in sorted_keys:
        result = result_map[key]
        result.score = scores[key]
        result.source = "hybrid"
        merged.append(result)
    
    return merged


def hybrid_search(
    workspace_path: Path,
    query: str,
    top_k: int = 5,
    use_leann: bool = True,
    semantic_weight: float = LEANN_SEMANTIC_WEIGHT,
    keyword_weight: float = LEANN_KEYWORD_WEIGHT,
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining LEANN semantic and ripgrep keyword search.
    
    Args:
        workspace_path: Path to user workspace
        query: Search query
        top_k: Number of results to return
        use_leann: Whether to use LEANN semantic search
        semantic_weight: Weight for semantic results (0-1)
        keyword_weight: Weight for keyword results (0-1)
        
    Returns:
        List of search result dicts with 'content', 'filepath', 'filename', etc.
    """
    workspace = Path(workspace_path)
    notes_dir = workspace / "notes"
    
    # Try LEANN semantic search
    semantic_results = []
    if use_leann and ENABLE_LEANN:
        try:
            searcher = _get_leann_searcher(workspace)
            if searcher is not None:
                leann_results = searcher.search(query, top_k=top_k * 2)
                semantic_results = [
                    SearchResult(
                        content=r.content if hasattr(r, 'content') else r.get('content', ''),
                        filepath=r.filepath if hasattr(r, 'filepath') else r.get('filepath', ''),
                        filename=r.filename if hasattr(r, 'filename') else r.get('filename', ''),
                        score=r.score if hasattr(r, 'score') else r.get('score', 0.0),
                        source="leann",
                    )
                    for r in leann_results
                ]
                logger.info(f"LEANN returned {len(semantic_results)} semantic results")
                searcher.cleanup()
        except Exception as e:
            logger.warning(f"LEANN search failed, falling back to ripgrep: {e}")
    
    # Always get ripgrep results (as fallback or for hybrid)
    keyword_results = _ripgrep_search(notes_dir, query, top_k=top_k * 2)
    
    # Decide on result merging strategy
    if not semantic_results and not keyword_results:
        logger.info("No search results found")
        return []
    
    if not semantic_results:
        # LEANN not available or failed, use ripgrep only
        logger.info("Using ripgrep-only results")
        return [r.to_dict() for r in keyword_results[:top_k]]
    
    if not keyword_results:
        # No ripgrep results, use LEANN only
        logger.info("Using LEANN-only results")
        return [r.to_dict() for r in semantic_results[:top_k]]
    
    # Merge using RRF
    logger.info(f"Merging {len(semantic_results)} semantic + {len(keyword_results)} keyword results")
    merged = _reciprocal_rank_fusion(
        semantic_results,
        keyword_results,
        semantic_weight,
        keyword_weight,
    )
    
    return [r.to_dict() for r in merged[:top_k]]


def build_leann_index(
    workspace_path: Path,
    force_rebuild: bool = False,
) -> bool:
    """
    Build LEANN index for a workspace.
    Called during /v1/aipartner/build.
    
    Args:
        workspace_path: Path to workspace
        force_rebuild: Force rebuild even if index exists
        
    Returns:
        True if successful
    """
    if not ENABLE_LEANN:
        logger.info("LEANN disabled, skipping index build")
        return False
    
    workspace = Path(workspace_path)
    notes_dir = workspace / "notes"
    
    if not notes_dir.exists():
        logger.warning(f"Notes directory not found: {notes_dir}")
        return False
    
    try:
        # Add backend/core to path
        backend_core = Path(__file__).parent.parent / "backend" / "core"
        if backend_core.exists() and str(backend_core) not in sys.path:
            sys.path.insert(0, str(backend_core))
        
        from leann_rag import LeannIndexManager, chunk_text
        
        # Collect all note files
        all_chunks = []
        for note_file in notes_dir.glob("**/*"):
            if not note_file.is_file():
                continue
            if note_file.suffix not in [".md", ".txt"]:
                continue
            
            try:
                content = note_file.read_text(encoding="utf-8", errors="ignore")
                if not content.strip():
                    continue
                
                chunks = chunk_text(
                    content,
                    metadata={
                        "filename": note_file.name,
                        "filepath": str(note_file.resolve()),
                    }
                )
                all_chunks.extend(chunks)
                
            except Exception as e:
                logger.warning(f"Failed to process {note_file}: {e}")
                continue
        
        if not all_chunks:
            logger.warning("No chunks to index")
            return False
        
        logger.info(f"Building LEANN index with {len(all_chunks)} chunks")
        
        manager = LeannIndexManager(workspace)
        return manager.build_index(all_chunks, force_rebuild=force_rebuild)
        
    except ImportError as e:
        logger.warning(f"LEANN not available: {e}")
        return False
    except Exception as e:
        logger.error(f"LEANN index build failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# For testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LEANN hybrid search")
    parser.add_argument("workspace", help="Path to workspace")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--build", action="store_true", help="Build index first")
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace)
    
    if args.build:
        print("Building LEANN index...")
        success = build_leann_index(workspace, force_rebuild=True)
        print(f"Build {'successful' if success else 'failed'}")
    
    print(f"\nSearching for: {args.query}")
    results = hybrid_search(workspace, args.query, top_k=args.top_k)
    
    print(f"\n{len(results)} results:")
    for i, r in enumerate(results):
        print(f"\n[{i+1}] {r['filename']} (score: {r['score']:.4f}, source: {r['source']})")
        print(f"    {r['content'][:200]}...")

