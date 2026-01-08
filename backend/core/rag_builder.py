"""
RAG Builder with LEANN Semantic Search Integration
===================================================
Handles file parsing/extraction AND builds LEANN semantic indexes.

Key improvements over ripgrep-only approach:
- Semantic search: finds related content even without exact keyword matches
- 97% storage savings: LEANN's graph-based approach vs traditional vector DBs
- Hybrid search: combines semantic + keyword for best results
- PDF转换: 保留表格和图片格式的增强文本提取
"""
import os
import logging
from llama_index.core import SimpleDirectoryReader, Document
import fitz  # PyMuPDF
from core.video_processor import VideoProcessor
from core.metrics import JsonlMetricsLogger
from core.pdf_converter import PDFConverter, convert_pdf_after_upload
from typing import Tuple, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# LEANN integration flag - can be disabled via environment
ENABLE_LEANN = os.getenv("ENABLE_LEANN", "true").lower() in ("true", "1", "yes")


class RagBuilder:
    """
    RAG Builder with optional LEANN semantic indexing.
    
    Features:
    - File parsing (PDF, video, text, etc.)
    - LEANN semantic index building (optional, enabled by default)
    - Chunk-based text splitting for better retrieval
    """
    
    def __init__(self, init_models: bool = False):
        """
        Initialize RAG Builder.
        
        Args:
            init_models: If True and LEANN is enabled, pre-load embedding model
        """
        self._video_processor: VideoProcessor | None = None
        self._leann_manager = None
        
        if init_models and ENABLE_LEANN:
            self._init_leann()

    def _get_video_processor(self) -> VideoProcessor:
        """按需创建 VideoProcessor（Whisper 将延迟加载）。"""
        if self._video_processor is None:
            self._video_processor = VideoProcessor(model_size=os.getenv("WHISPER_MODEL_SIZE", "base"))
        return self._video_processor
    
    def _init_leann(self):
        """Initialize LEANN manager (lazy import to avoid startup overhead)."""
        if self._leann_manager is not None:
            return
        
        try:
            from core.leann_rag import LeannIndexManager
            logger.info("LEANN integration enabled")
        except ImportError as e:
            logger.warning(f"LEANN not available: {e}")
            logger.info("Install with: pip install leann-core leann-backend-hnsw")
    
    def build_leann_index(
        self,
        workspace_path: Path,
        documents: List[Document],
        force_rebuild: bool = False,
        metrics: Optional[JsonlMetricsLogger] = None,
    ) -> bool:
        """
        Build LEANN semantic index from documents.
        
        Args:
            workspace_path: Path to user's workspace
            documents: List of LlamaIndex Documents
            force_rebuild: Force rebuild even if index exists
            metrics: Optional metrics logger
            
        Returns:
            True if successful, False otherwise
        """
        if not ENABLE_LEANN:
            logger.debug("LEANN disabled via ENABLE_LEANN=false")
            return False
        
        try:
            from core.leann_rag import LeannIndexManager, chunk_text
        except ImportError as e:
            logger.warning(f"LEANN not available: {e}")
            return False
        
        if not documents:
            logger.warning("No documents to index with LEANN")
            return False
        
        if metrics:
            metrics.write("leann_build_start", {"num_documents": len(documents)})
        
        try:
            # Convert LlamaIndex Documents to chunks
            all_chunks = []
            for doc in documents:
                text = doc.text if hasattr(doc, 'text') else str(doc)
                if not text.strip():
                    continue
                
                # Extract metadata
                meta = {}
                if hasattr(doc, 'metadata'):
                    meta = dict(doc.metadata)
                
                # Chunk the document
                chunks = chunk_text(
                    text,
                    metadata={
                        "filename": meta.get("file_name", "unknown"),
                        "filepath": meta.get("source", ""),
                        "page_number": meta.get("page_number", 0),
                        **meta,
                    }
                )
                all_chunks.extend(chunks)
            
            if not all_chunks:
                logger.warning("No chunks generated from documents")
                return False
            
            logger.info(f"Building LEANN index with {len(all_chunks)} chunks from {len(documents)} documents")
            
            # Build LEANN index
            manager = LeannIndexManager(workspace_path)
            
            if metrics:
                with metrics.time_block("leann_index_build"):
                    success = manager.build_index(all_chunks, force_rebuild=force_rebuild)
            else:
                success = manager.build_index(all_chunks, force_rebuild=force_rebuild)
            
            if success and metrics:
                metrics.write("leann_build_complete", {
                    "num_chunks": len(all_chunks),
                    "success": True,
                })
            
            return success
            
        except Exception as e:
            logger.error(f"LEANN index build failed: {e}")
            import traceback
            traceback.print_exc()
            
            if metrics:
                metrics.write("leann_build_error", {"error": str(e)})
            
            return False

    def _load_pdf_by_page(self, file_path: str, preserve_format: bool = True) -> List[Document]:
        """
        将 PDF 按页拆分为 Document，并写入页码元数据，便于问答时回链定位。
        
        Args:
            file_path: PDF 文件路径
            preserve_format: 是否保留表格和图片格式（默认 True）
            
        Returns:
            List[Document]: 文档列表
        """
        docs: List[Document] = []
        base_name = os.path.basename(file_path)
        file_path_obj = Path(file_path)
        
        # 如果启用格式保留，先转换 PDF 到增强文本
        if preserve_format:
            try:
                converter = PDFConverter(preserve_tables=True, preserve_images=True)
                
                # 生成转换后的 txt 文件路径
                txt_path = file_path_obj.with_suffix('.converted.txt')
                
                # 转换 PDF
                txt_path_str, full_text = converter.convert(file_path, str(txt_path))
                logger.info(f"PDF 已转换为增强文本: {txt_path_str}")
                
                # 按页分割提取的文本
                pages = self._split_converted_text_by_page(full_text)
                
                for i, page_text in enumerate(pages):
                    if page_text.strip():
                        docs.append(
                            Document(
                                text=page_text,
                                metadata={
                                    "file_name": base_name,
                                    "file_type": "pdf",
                                    "page_label": str(i + 1),
                                    "page_number": i + 1,
                                    "source": file_path,
                                    "converted_txt": str(txt_path),
                                    "format_preserved": True,
                                },
                            )
                        )
                
                # 如果成功提取了内容，返回
                if docs:
                    return docs
                    
                logger.warning("增强转换未提取到内容，回退到基础提取")
                
            except Exception as e:
                logger.warning(f"增强 PDF 转换失败: {e}，回退到基础提取")
        
        # 回退到基础 PyMuPDF 提取
        pdf = fitz.open(file_path)
        for i in range(pdf.page_count):
            page = pdf.load_page(i)
            text = page.get_text("text") or ""
            docs.append(
                Document(
                    text=text,
                    metadata={
                        "file_name": base_name,
                        "file_type": "pdf",
                        "page_label": str(i + 1),
                        "page_number": i + 1,
                        "source": file_path,
                        "format_preserved": False,
                    },
                )
            )
        pdf.close()
        return docs
    
    def _split_converted_text_by_page(self, full_text: str) -> List[str]:
        """
        将转换后的完整文本按页分割。
        
        转换后的文本使用 "## 【第 X 页】" 格式标记页面边界。
        """
        import re
        
        # 匹配页面标记
        page_pattern = r'## 【第 (\d+) 页】'
        
        # 分割文本
        parts = re.split(page_pattern, full_text)
        
        pages = []
        
        # parts 格式: [header, page_num1, content1, page_num2, content2, ...]
        if len(parts) >= 3:
            # 跳过文件头部
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    page_num = parts[i]
                    page_content = parts[i + 1]
                    
                    # 清理分隔线
                    page_content = re.sub(r'-{40,}', '', page_content)
                    page_content = page_content.strip()
                    
                    pages.append(page_content)
        else:
            # 如果没有页面标记，作为单页处理
            pages.append(full_text)
        
        return pages

    def extract_documents(
        self, file_path: str, metrics: Optional[JsonlMetricsLogger] = None
    ) -> Tuple[List[Document], str]:
        """解析/转录文件为 Documents，并返回 extracted_text（用于预览/调试）。"""
        file_ext = os.path.splitext(file_path)[1].lower()
        documents: List[Document] = []
        extracted_text = ""

        if metrics:
            metrics.write("extract_start", {"file_path": file_path, "file_ext": file_ext})

        if file_ext in [".mp4", ".avi", ".mov", ".mkv"]:
            print(f"Detected video file: {file_path}")
            if metrics:
                with metrics.time_block("parse_video"):
                    documents, extracted_text = self._get_video_processor().process(file_path)
            else:
                documents, extracted_text = self._get_video_processor().process(file_path)
        elif file_ext == ".pdf":
            if metrics:
                with metrics.time_block("parse_pdf_by_page"):
                    documents = self._load_pdf_by_page(file_path)
            else:
                documents = self._load_pdf_by_page(file_path)
            extracted_text = "\n".join([doc.text for doc in documents if doc.text])
        else:
            if metrics:
                with metrics.time_block("parse_generic"):
                    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
            else:
                documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
            extracted_text = "\n".join([doc.text for doc in documents])

        if metrics:
            metrics.write("extract_done", {"documents": len(documents), "extracted_text_len": len(extracted_text)})

        return documents, extracted_text
