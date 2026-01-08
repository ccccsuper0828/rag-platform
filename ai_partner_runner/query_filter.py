"""
Query filter extraction module.
Extracts metadata filters from natural language queries to enable smart filtering.
"""
import re
from typing import Dict, Optional, List


class QueryFilterExtractor:
    """
    Extract metadata filters from natural language queries.
    Inspired by LangExtract-RAG's extract_smart_filters.
    """
    
    def __init__(self):
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize extraction patterns"""
        # Version patterns
        self.version_patterns = [
            r'v(?:ersion)?\s*([\d.]+)',           # version 2.0, v2.0
            r'([\d.]+)\s*(?:版本|version)',        # 2.0版本
            r'V([\d.]+)',                          # V2.0
        ]
        
        # Service/API patterns
        self.service_keywords = {
            'authentication': ['authentication', 'auth', 'oauth', 'login', '认证', '授权', '登录'],
            'storage': ['storage', 'store', 'bucket', 'object', '存储', '存储服务'],
            'api': ['api', 'endpoint', '接口', '端点'],
            'database': ['database', 'db', 'sql', '数据库'],
            'cache': ['cache', 'redis', 'memcached', '缓存'],
        }
        
        # Document type patterns
        self.doc_type_keywords = {
            'troubleshooting': ['troubleshoot', 'troubleshooting', 'error', 'fix', 'problem', 'issue', 
                               'bug', '故障', '错误', '问题', '修复', '排查', '调试'],
            'guide': ['guide', 'tutorial', 'how to', 'how-to', 'walkthrough', 'step',
                     '指南', '教程', '如何', '步骤', '操作'],
            'reference': ['reference', 'api', 'specification', 'spec', 'documentation',
                         '参考', '规范', '说明', '文档', '接口文档'],
            'note': ['note', 'notes', 'memo', 'journal', 'log', '记录',
                    '笔记', '记录', '日志', '备忘录'],
        }
    
    def extract_filters(self, query: str) -> Dict[str, any]:
        """
        Extract metadata filters from query.
        
        Args:
            query: Natural language query
        
        Returns:
            Dictionary with filter criteria
        """
        filters = {}
        query_lower = query.lower()
        
        # Extract version
        version = self._extract_version(query)
        if version:
            filters['version'] = version
        
        # Extract service
        service = self._extract_service(query_lower)
        if service:
            filters['service'] = service
        
        # Extract document type
        doc_type = self._extract_doc_type(query_lower)
        if doc_type:
            filters['doc_type'] = doc_type
        
        # Extract tags (from query keywords)
        tags = self._extract_tags(query_lower)
        if tags:
            filters['tags'] = tags
        
        # Check for deprecated filter
        if any(keyword in query_lower for keyword in ['deprecated', 'legacy', 'old', '已弃用', '旧版']):
            filters['deprecated'] = False  # Usually want non-deprecated
        
        return filters
    
    def _extract_version(self, query: str) -> Optional[str]:
        """Extract version number from query"""
        for pattern in self.version_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_service(self, query_lower: str) -> Optional[str]:
        """Extract service name from query"""
        # Check for specific service keywords
        for service_name, keywords in self.service_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                # Map to canonical service name
                if service_name == 'authentication':
                    return 'Authentication API'
                elif service_name == 'storage':
                    return 'Storage Service'
                elif service_name == 'api':
                    # Try to extract more specific API name
                    api_match = re.search(r'([\w\s]+)\s*(?:api|接口)', query_lower)
                    if api_match:
                        return api_match.group(1).strip().title() + ' API'
                    return 'API'
                else:
                    return service_name.title() + ' Service'
        
        return None
    
    def _extract_doc_type(self, query_lower: str) -> Optional[str]:
        """Extract document type from query"""
        for doc_type, keywords in self.doc_type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return doc_type
        return None
    
    def _extract_tags(self, query_lower: str) -> List[str]:
        """Extract relevant tags from query"""
        tags = []
        
        # Common technical keywords
        tech_keywords = [
            'oauth', 'rest', 'graphql', 'rate limit', 'authentication',
            'storage', 'database', 'cache', 'queue',
            '认证', '存储', '数据库', '缓存'
        ]
        
        for keyword in tech_keywords:
            if keyword in query_lower:
                tags.append(keyword)
        
        return tags
    
    def explain_filters(self, filters: Dict) -> str:
        """Generate human-readable explanation of filters"""
        if not filters:
            return "无过滤条件"
        
        parts = []
        if 'version' in filters:
            parts.append(f"版本: {filters['version']}")
        if 'service' in filters:
            parts.append(f"服务: {filters['service']}")
        if 'doc_type' in filters:
            parts.append(f"文档类型: {filters['doc_type']}")
        if 'tags' in filters:
            parts.append(f"标签: {', '.join(filters['tags'])}")
        if 'deprecated' in filters:
            parts.append(f"已弃用: {'否' if not filters['deprecated'] else '是'}")
        
        return " | ".join(parts) if parts else "无过滤条件"

