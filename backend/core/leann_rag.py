"""
LEANN RAG Integration Module
============================
Provides semantic search capabilities with 97% storage savings.

Key features:
- Graph-based selective recomputation (no embedding storage)
- On-demand embedding computation for high accuracy
- Hybrid search: combines LEANN semantic + ripgrep keyword search
- Multi-tenant isolation support
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# LEANN configuration
LEANN_EMBEDDING_MODEL = os.getenv("LEANN_EMBEDDING_MODEL", "facebook/contriever")
LEANN_EMBEDDING_MODE = os.getenv("LEANN_EMBEDDING_MODE", "sentence-transformers")
LEANN_BACKEND = os.getenv("LEANN_BACKEND", "hnsw")
LEANN_CHUNK_SIZE = int(os.getenv("LEANN_CHUNK_SIZE", "512"))
LEANN_CHUNK_OVERLAP = int(os.getenv("LEANN_CHUNK_OVERLAP", "64"))


@dataclass
class SearchResult:
    """Unified search result from LEANN or ripgrep."""
    content: str
    filepath: str
    filename: str
    score: float = 0.0
    chunk_id: int = 0
    source: str = "leann"  # "leann" or "ripgrep"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LeannIndexManager:
    """
    Manages LEANN semantic indexes for multi-tenant RAG.
    
    Storage structure:
    workspace/
    ├── leann_index/
    │   ├── documents.leann
    │   ├── documents.leann.meta.json
    │   ├── documents.leann.passages.jsonl
    │   └── documents.leann.passages.idx
    └── notes/
        └── *.md
    """
    
    def __init__(self, workspace_path: Path):
        self.workspace = Path(workspace_path)
        self.index_dir = self.workspace / "leann_index"
        self.index_path = self.index_dir / "documents.leann"
        self._searcher = None
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Create necessary directories."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_leann_imports(self):
        """Lazy import LEANN to avoid startup overhead."""
        try:
            from leann import LeannBuilder, LeannSearcher
            return LeannBuilder, LeannSearcher
        except ImportError as e:
            logger.error(f"LEANN not installed: {e}")
            logger.info("Install with: pip install leann-core leann-backend-hnsw")
            raise ImportError(
                "LEANN is required for semantic search. "
                "Install with: pip install leann-core leann-backend-hnsw"
            ) from e
    
    def build_index(
        self,
        documents: List[Dict[str, Any]],
        force_rebuild: bool = False
    ) -> bool:
        """
        Build LEANN index from documents.
        
        Args:
            documents: List of dicts with 'text', 'metadata' keys
            force_rebuild: If True, rebuild even if index exists
            
        Returns:
            True if build successful
        """
        LeannBuilder, _ = self._get_leann_imports()
        
        # Check if index exists and skip if not forcing rebuild
        meta_path = Path(f"{self.index_path}.meta.json")
        if meta_path.exists() and not force_rebuild:
            logger.info(f"Index already exists at {self.index_path}, skipping rebuild")
            return True
        
        if not documents:
            logger.warning("No documents to index")
            return False
        
        logger.info(f"Building LEANN index with {len(documents)} documents...")
        logger.info(f"  Model: {LEANN_EMBEDDING_MODEL}")
        logger.info(f"  Backend: {LEANN_BACKEND}")
        logger.info(f"  Chunk size: {LEANN_CHUNK_SIZE}")
        
        try:
            # Create builder with configuration
            builder = LeannBuilder(
                backend_name=LEANN_BACKEND,
                embedding_model=LEANN_EMBEDDING_MODEL,
                embedding_mode=LEANN_EMBEDDING_MODE,
                is_recompute=True,  # Key: enables 97% storage savings
                is_compact=True,    # Key: uses CSR format for minimal storage
            )
            
            # Add documents with metadata
            for i, doc in enumerate(documents):
                text = doc.get("text", "")
                if not text.strip():
                    continue
                    
                metadata = doc.get("metadata", {})
                metadata["id"] = str(i)
                metadata["chunk_index"] = i
                
                builder.add_text(text, metadata=metadata)
            
            # Build the index (graph-only, no embedding storage!)
            builder.build_index(str(self.index_path))
            
            logger.info(f"✅ LEANN index built successfully at {self.index_path}")
            
            # Log storage savings
            self._log_storage_stats()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to build LEANN index: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _log_storage_stats(self):
        """Log storage statistics to demonstrate savings."""
        try:
            total_size = 0
            for f in self.index_dir.glob("*"):
                if f.is_file():
                    total_size += f.stat().st_size
            
            # Estimate what FAISS would use (768-dim embeddings * 4 bytes * num_docs)
            meta_path = Path(f"{self.index_path}.meta.json")
            if meta_path.exists():
                with open(meta_path) as f:
                    meta = json.load(f)
                    dim = meta.get("dimensions", 768)
                    # Count passages
                    passages_path = self.index_dir / "documents.leann.passages.jsonl"
                    if passages_path.exists():
                        with open(passages_path) as pf:
                            num_docs = sum(1 for _ in pf)
                        
                        # FAISS would use: num_docs * dim * 4 bytes (float32)
                        faiss_size = num_docs * dim * 4
                        savings = (1 - total_size / max(faiss_size, 1)) * 100
                        
                        logger.info(f"📊 Storage Stats:")
                        logger.info(f"   LEANN: {total_size / 1024:.1f} KB")
                        logger.info(f"   FAISS (est): {faiss_size / 1024:.1f} KB")
                        logger.info(f"   Savings: {savings:.1f}%")
        except Exception as e:
            logger.debug(f"Could not compute storage stats: {e}")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        complexity: int = 64
    ) -> List[SearchResult]:
        """
        Semantic search using LEANN.
        
        Args:
            query: Search query
            top_k: Number of results to return
            complexity: Search complexity (higher = more accurate but slower)
            
        Returns:
            List of SearchResult objects
        """
        _, LeannSearcher = self._get_leann_imports()
        
        meta_path = Path(f"{self.index_path}.meta.json")
        if not meta_path.exists():
            logger.warning("LEANN index not found, cannot perform semantic search")
            return []
        
        try:
            # Initialize searcher (cached)
            if self._searcher is None:
                self._searcher = LeannSearcher(str(self.index_path))
            
            # Perform semantic search
            results = self._searcher.search(
                query,
                top_k=top_k,
                complexity=complexity,
                recompute_embeddings=True,  # On-demand embedding computation
            )
            
            # Convert to SearchResult objects
            search_results = []
            for r in results:
                search_results.append(SearchResult(
                    content=r.text,
                    filepath=r.metadata.get("filepath", ""),
                    filename=r.metadata.get("filename", ""),
                    score=float(r.score),
                    chunk_id=r.metadata.get("chunk_index", 0),
                    source="leann",
                    metadata=r.metadata,
                ))
            
            logger.info(f"LEANN search returned {len(search_results)} results for: {query[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"LEANN search failed: {e}")
            return []
    
    def cleanup(self):
        """Cleanup resources."""
        if self._searcher is not None:
            try:
                self._searcher.cleanup()
            except Exception:
                pass
            self._searcher = None


class HybridSearcher:
    """
    Combines LEANN semantic search with ripgrep keyword search.
    
    Strategy:
    1. Run both LEANN (semantic) and ripgrep (keyword) in parallel
    2. Merge results using Reciprocal Rank Fusion (RRF)
    3. Return top-k unified results
    """
    
    def __init__(self, workspace_path: Path):
        self.workspace = Path(workspace_path)
        self.leann_manager = LeannIndexManager(workspace_path)
        self.notes_dir = self.workspace / "notes"
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            semantic_weight: Weight for LEANN semantic results (0-1)
            keyword_weight: Weight for ripgrep keyword results (0-1)
            
        Returns:
            List of SearchResult objects, sorted by combined score
        """
        # Get semantic results from LEANN
        semantic_results = self.leann_manager.search(query, top_k=top_k * 2)
        
        # Get keyword results from ripgrep
        keyword_results = self._ripgrep_search(query, top_k=top_k * 2)
        
        # If only one source has results, return those
        if not semantic_results and not keyword_results:
            return []
        if not semantic_results:
            return keyword_results[:top_k]
        if not keyword_results:
            return semantic_results[:top_k]
        
        # Merge using Reciprocal Rank Fusion
        merged = self._reciprocal_rank_fusion(
            semantic_results,
            keyword_results,
            semantic_weight,
            keyword_weight,
        )
        
        return merged[:top_k]
    
    def _ripgrep_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Perform ripgrep keyword search."""
        if not self.notes_dir.exists():
            return []
        
        try:
            import ripgrepy
            
            rg = ripgrepy.Ripgrepy(query, str(self.notes_dir))
            rg = rg.glob("*.md").glob("*.txt").E("utf-8").C(3)
            
            try:
                rg_output = rg.json().run()
                if hasattr(rg_output, 'as_dict'):
                    matches = rg_output.as_dict if isinstance(rg_output.as_dict, list) else [rg_output.as_dict]
                else:
                    matches = []
            except Exception:
                matches = []
            
            results = []
            seen_files = set()
            
            for match in matches[:top_k * 2]:
                if isinstance(match, dict):
                    data = match.get('data', {})
                    path_data = data.get('path', {})
                    lines_data = data.get('lines', {})
                    
                    filepath = path_data.get('text', '') if isinstance(path_data, dict) else str(path_data)
                    content = lines_data.get('text', '') if isinstance(lines_data, dict) else str(lines_data)
                    
                    if filepath and content and filepath not in seen_files:
                        seen_files.add(filepath)
                        
                        # Score based on match count
                        score = content.lower().count(query.lower())
                        
                        results.append(SearchResult(
                            content=content.strip(),
                            filepath=filepath,
                            filename=Path(filepath).name,
                            score=float(score),
                            source="ripgrep",
                        ))
            
            # Sort by score descending
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except ImportError:
            logger.debug("ripgrepy not available, skipping keyword search")
            return []
        except Exception as e:
            logger.debug(f"Ripgrep search failed: {e}")
            return []
    
    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        semantic_weight: float,
        keyword_weight: float,
        k: int = 60,  # RRF constant
    ) -> List[SearchResult]:
        """
        Merge results using Reciprocal Rank Fusion.
        
        RRF score = sum(1 / (k + rank)) for each ranking list
        """
        # Build content-to-result map (use content hash as key)
        result_map: Dict[str, SearchResult] = {}
        scores: Dict[str, float] = {}
        
        # Process semantic results
        for rank, result in enumerate(semantic_results):
            key = f"{result.filepath}:{result.content[:100]}"
            rrf_score = semantic_weight * (1.0 / (k + rank + 1))
            
            if key in scores:
                scores[key] += rrf_score
            else:
                scores[key] = rrf_score
                result_map[key] = result
        
        # Process keyword results
        for rank, result in enumerate(keyword_results):
            key = f"{result.filepath}:{result.content[:100]}"
            rrf_score = keyword_weight * (1.0 / (k + rank + 1))
            
            if key in scores:
                scores[key] += rrf_score
            else:
                scores[key] = rrf_score
                result_map[key] = result
        
        # Sort by combined score
        sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
        
        # Build final results with combined scores
        merged_results = []
        for key in sorted_keys:
            result = result_map[key]
            result.score = scores[key]
            result.source = "hybrid"
            merged_results.append(result)
        
        return merged_results
    
    def build_index(self, documents: List[Dict[str, Any]], force_rebuild: bool = False) -> bool:
        """Build LEANN index from documents."""
        return self.leann_manager.build_index(documents, force_rebuild)
    
    def cleanup(self):
        """Cleanup resources."""
        self.leann_manager.cleanup()


def chunk_text(
    text: str,
    chunk_size: int = LEANN_CHUNK_SIZE,
    chunk_overlap: int = LEANN_CHUNK_OVERLAP,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks for indexing.
    
    Args:
        text: Input text
        chunk_size: Maximum characters per chunk
        chunk_overlap: Overlap between chunks
        metadata: Metadata to attach to each chunk
        
    Returns:
        List of dicts with 'text' and 'metadata' keys
    """
    if not text.strip():
        return []
    
    metadata = metadata or {}
    chunks = []
    
    # Split by paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    current_chunk = ""
    chunk_index = 0
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{para}".strip() if current_chunk else para
        else:
            if current_chunk:
                chunks.append({
                    "text": current_chunk,
                    "metadata": {
                        **metadata,
                        "chunk_index": chunk_index,
                    }
                })
                chunk_index += 1
                
                # Keep overlap
                if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                    current_chunk = current_chunk[-chunk_overlap:] + "\n\n" + para
                else:
                    current_chunk = para
            else:
                # Paragraph is too long, split by sentences
                sentences = para.replace(". ", ".\n").split("\n")
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= chunk_size:
                        current_chunk = f"{current_chunk} {sent}".strip() if current_chunk else sent
                    else:
                        if current_chunk:
                            chunks.append({
                                "text": current_chunk,
                                "metadata": {
                                    **metadata,
                                    "chunk_index": chunk_index,
                                }
                            })
                            chunk_index += 1
                        current_chunk = sent
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk,
            "metadata": {
                **metadata,
                "chunk_index": chunk_index,
            }
        })
    
    return chunks


# Convenience functions for integration
def create_leann_index(
    workspace_path: Path,
    documents: List[Dict[str, Any]],
    force_rebuild: bool = False
) -> bool:
    """
    Create LEANN index for a workspace.
    
    Args:
        workspace_path: Path to workspace directory
        documents: List of dicts with 'text', 'metadata' keys
        force_rebuild: Force rebuild even if index exists
        
    Returns:
        True if successful
    """
    manager = LeannIndexManager(workspace_path)
    return manager.build_index(documents, force_rebuild)


def search_with_leann(
    workspace_path: Path,
    query: str,
    top_k: int = 5,
    use_hybrid: bool = True,
) -> List[Dict[str, Any]]:
    """
    Search using LEANN (optionally with hybrid search).
    
    Args:
        workspace_path: Path to workspace directory
        query: Search query
        top_k: Number of results
        use_hybrid: Whether to combine with ripgrep
        
    Returns:
        List of result dicts
    """
    if use_hybrid:
        searcher = HybridSearcher(workspace_path)
    else:
        searcher = LeannIndexManager(workspace_path)
    
    try:
        results = searcher.search(query, top_k=top_k)
        return [r.to_dict() for r in results]
    finally:
        searcher.cleanup()

