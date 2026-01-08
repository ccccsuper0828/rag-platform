"""
Metadata extraction module inspired by LangExtract-RAG.
Extracts structured metadata from documents to enable smart filtering.
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field


@dataclass
class DocumentMetadata:
    """Structured metadata for documents"""
    service: str = "unknown"           # Service/API name
    version: str = "unknown"            # Version number
    doc_type: str = "reference"        # reference/guide/troubleshooting/note
    category: str = "general"           # Document category
    tags: List[str] = field(default_factory=list)  # Tags/keywords
    rate_limits: List[str] = field(default_factory=list)  # Rate limit information
    deprecated: bool = False            # Is deprecated
    date: Optional[str] = None          # Document date
    author: Optional[str] = None       # Author information
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DocumentMetadata':
        """Create from dictionary"""
        return cls(**data)


class MetadataExtractor:
    """
    Extract structured metadata from documents.
    Uses enhanced regex patterns (inspired by LangExtract-RAG) with optional LLM enhancement.
    """
    
    def __init__(self, use_llm: bool = False):
        """
        Initialize metadata extractor.
        
        Args:
            use_llm: Whether to use LLM for enhanced extraction (requires API)
        """
        self.use_llm = use_llm
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for metadata extraction"""
        # Version patterns
        self.version_patterns = [
            r'v(?:ersion)?\s*([\d.]+)',           # v2.0, version 2.0
            r'([\d.]+)\s*(?:版本|version)',        # 2.0版本, 2.0 version
            r'V([\d.]+)',                          # V2.0
        ]
        
        # Service/API patterns
        self.service_patterns = [
            r'([\w\s]+(?:API|Service|服务|接口))',  # Authentication API, Storage Service
            r'#\s*([\w\s]+(?:API|Service))',       # # Authentication API
            r'##\s*([\w\s]+(?:API|Service))',      # ## Authentication API
        ]
        
        # Document type patterns
        self.doc_type_keywords = {
            'troubleshooting': ['troubleshoot', 'troubleshooting', 'error', 'fix', 'problem', 'issue', 
                               '故障', '错误', '问题', '修复', '排查'],
            'guide': ['guide', 'tutorial', 'how to', 'how-to', 'walkthrough',
                     '指南', '教程', '如何', '步骤'],
            'reference': ['reference', 'api', 'specification', 'spec',
                         '参考', '规范', '说明', '文档'],
            'note': ['note', 'notes', 'memo', 'journal', 'log',
                    '笔记', '记录', '日志', '备忘录'],
        }
        
        # Rate limit patterns
        self.rate_limit_patterns = [
            r'(\d+)\s*(?:requests?|req)[/\s]*(?:per\s*)?(?:min|minute|分钟)',
            r'(\d+)\s*次[/\s]*(?:每|per)\s*(?:分钟|min|minute)',
            r'rate\s*limit[:\s]+(\d+)',
            r'速率限制[:\s]+(\d+)',
        ]
        
        # Date patterns
        self.date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',                # 2024-03-15
            r'(\d{4}/\d{2}/\d{2})',                # 2024/03/15
            r'(\d{4}\.\d{2}\.\d{2})',              # 2024.03.15
            r'(?:last\s*updated|更新于)[:\s]+(\d{4}[-/]\d{2}[-/]\d{2})',
        ]
    
    def extract_metadata(self, content: str, filename: str = "", title: str = "") -> DocumentMetadata:
        """
        Extract metadata from document content.
        
        Args:
            content: Document content
            filename: Filename (for context)
            title: Document title (for context)
        
        Returns:
            DocumentMetadata object
        """
        metadata = DocumentMetadata()
        
        # Combine title and content for extraction
        full_text = f"{title}\n{content}" if title else content
        full_text_lower = full_text.lower()
        
        # Extract version
        metadata.version = self._extract_version(full_text, title)
        
        # Extract service/API name
        metadata.service = self._extract_service(full_text, title, filename)
        
        # Determine document type
        metadata.doc_type = self._extract_doc_type(full_text_lower, title.lower(), filename.lower())
        
        # Extract rate limits
        metadata.rate_limits = self._extract_rate_limits(full_text)
        
        # Check for deprecation
        metadata.deprecated = self._check_deprecated(full_text_lower)
        
        # Extract date
        metadata.date = self._extract_date(full_text)
        
        # Extract tags (simple keyword extraction)
        metadata.tags = self._extract_tags(full_text, metadata)
        
        return metadata
    
    def _extract_version(self, text: str, title: str = "") -> str:
        """Extract version number"""
        # Try title first (more likely to have version)
        for pattern in self.version_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Try in content
        for pattern in self.version_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def _extract_service(self, text: str, title: str = "", filename: str = "") -> str:
        """Extract service/API name"""
        # Try title first
        for pattern in self.service_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                service = match.group(1).strip()
                # Clean up common prefixes
                service = re.sub(r'^(#+\s*)', '', service)
                return service
        
        # Try filename
        if filename:
            # Remove extension and common suffixes
            base_name = Path(filename).stem
            # Check if it looks like a service name
            if any(keyword in base_name.lower() for keyword in ['api', 'service', '接口', '服务']):
                return base_name
        
        # Try in content (first heading)
        heading_match = re.search(r'^#+\s*([\w\s]+(?:API|Service|服务|接口))', text, re.MULTILINE | re.IGNORECASE)
        if heading_match:
            return heading_match.group(1).strip()
        
        return "unknown"
    
    def _extract_doc_type(self, text_lower: str, title_lower: str = "", filename_lower: str = "") -> str:
        """Determine document type"""
        # Check title first
        for doc_type, keywords in self.doc_type_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return doc_type
        
        # Check filename
        for doc_type, keywords in self.doc_type_keywords.items():
            if any(keyword in filename_lower for keyword in keywords):
                return doc_type
        
        # Check content
        for doc_type, keywords in self.doc_type_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return doc_type
        
        # Default to reference for technical docs, note for others
        if any(keyword in text_lower for keyword in ['api', 'endpoint', 'request', 'response', '接口', '端点']):
            return "reference"
        
        return "note"
    
    def _extract_rate_limits(self, text: str) -> List[str]:
        """Extract rate limit information"""
        rate_limits = []
        
        for pattern in self.rate_limit_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                rate_limits.append(match.group(0))
        
        return list(set(rate_limits))  # Remove duplicates
    
    def _check_deprecated(self, text_lower: str) -> bool:
        """Check if document is deprecated"""
        deprecated_keywords = [
            'deprecated', 'legacy', 'obsolete', 'outdated',
            '已弃用', '已废弃', '旧版', '过时'
        ]
        return any(keyword in text_lower for keyword in deprecated_keywords)
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract document date"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_tags(self, text: str, metadata: DocumentMetadata) -> List[str]:
        """Extract tags/keywords from document"""
        tags = []
        
        # Add service name as tag
        if metadata.service != "unknown":
            tags.append(metadata.service.lower())
        
        # Add version as tag
        if metadata.version != "unknown":
            tags.append(f"v{metadata.version}")
        
        # Extract common technical keywords
        tech_keywords = [
            'authentication', 'auth', 'oauth', 'api', 'rest', 'graphql',
            'storage', 'database', 'cache', 'queue', 'message',
            '认证', '授权', '存储', '数据库', '缓存'
        ]
        
        text_lower = text.lower()
        for keyword in tech_keywords:
            if keyword in text_lower:
                tags.append(keyword)
        
        return list(set(tags))  # Remove duplicates
    
    def extract_from_file(self, file_path: Path) -> DocumentMetadata:
        """Extract metadata from a file"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            filename = file_path.name
            # Try to extract title from first line or filename
            title = ""
            lines = content.split('\n')
            if lines:
                first_line = lines[0].strip()
                if first_line.startswith('#'):
                    title = first_line.lstrip('#').strip()
            
            return self.extract_metadata(content, filename, title)
        except Exception as e:
            print(f"Error extracting metadata from {file_path}: {e}")
            return DocumentMetadata()


class MetadataStore:
    """Store and manage document metadata"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.metadata_file = workspace / "metadata.json"
        self.metadata: Dict[str, DocumentMetadata] = {}
        self._load()
    
    def _load(self):
        """Load metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metadata = {
                        k: DocumentMetadata.from_dict(v) 
                        for k, v in data.items()
                    }
            except Exception as e:
                print(f"Error loading metadata: {e}")
                self.metadata = {}
    
    def save(self):
        """Save metadata to file"""
        try:
            data = {
                k: v.to_dict() 
                for k, v in self.metadata.items()
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving metadata: {e}")
    
    def get_metadata(self, filepath: str) -> Optional[DocumentMetadata]:
        """Get metadata for a file"""
        return self.metadata.get(filepath)
    
    def set_metadata(self, filepath: str, metadata: DocumentMetadata):
        """Set metadata for a file"""
        self.metadata[filepath] = metadata
    
    def filter_files(self, filters: Dict[str, Any]) -> List[str]:
        """
        Filter files based on metadata criteria.
        
        Args:
            filters: Dictionary with filter criteria
                - service: Service name (fuzzy match)
                - version: Version number (exact match)
                - doc_type: Document type (exact match)
                - tags: List of tags (any match)
                - deprecated: Boolean
        
        Returns:
            List of filepaths matching the filters
        """
        matching_files = []
        
        for filepath, metadata in self.metadata.items():
            match = True
            
            # Service filter (fuzzy match)
            if 'service' in filters:
                query_service = filters['service'].lower()
                doc_service = metadata.service.lower()
                if query_service not in doc_service and doc_service not in query_service:
                    # Try keyword matching
                    query_keywords = set(query_service.replace('api', '').replace('service', '').split())
                    doc_keywords = set(doc_service.replace('api', '').replace('service', '').split())
                    if not query_keywords.intersection(doc_keywords):
                        match = False
            
            # Version filter (exact match)
            if 'version' in filters and match:
                if metadata.version != filters['version']:
                    match = False
            
            # Document type filter (exact match)
            if 'doc_type' in filters and match:
                if metadata.doc_type != filters['doc_type']:
                    match = False
            
            # Tags filter (any match)
            if 'tags' in filters and match:
                filter_tags = set(t.lower() for t in filters['tags'])
                doc_tags = set(t.lower() for t in metadata.tags)
                if not filter_tags.intersection(doc_tags):
                    match = False
            
            # Deprecated filter
            if 'deprecated' in filters and match:
                if metadata.deprecated != filters['deprecated']:
                    match = False
            
            if match:
                matching_files.append(filepath)
        
        return matching_files

