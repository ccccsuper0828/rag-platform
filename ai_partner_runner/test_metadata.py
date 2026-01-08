#!/usr/bin/env python3
"""
测试元数据提取和智能过滤功能
"""
from pathlib import Path
from metadata_extractor import MetadataExtractor, DocumentMetadata
from query_filter import QueryFilterExtractor

# 测试数据
test_documents = [
    {
        "title": "Authentication API Reference v2.0",
        "content": """# Authentication API v2.0

The Authentication API provides secure access control.

## OAuth 2.0 Implementation
To authenticate using OAuth 2.0, send a POST request to /auth/oauth2/token.

### Rate Limits
- Standard tier: 100 requests per minute
- Premium tier: 1000 requests per minute

Note: API key authentication is deprecated as of v2.0.
Last updated: 2024-03-15"""
    },
    {
        "title": "Authentication API Reference v1.0 (Legacy)",
        "content": """# Authentication API v1.0 (Legacy)

## API Key Authentication
Generate an API key from the dashboard.

### Rate Limits
- All tiers: 60 requests per minute

Note: This version is deprecated. Please upgrade to v2.0.
Last updated: 2023-01-10"""
    },
    {
        "title": "Troubleshooting Guide: Authentication Errors",
        "content": """# Troubleshooting Guide: Authentication Errors

## Problem: 401 Unauthorized Error
**Cause**: Invalid or expired credentials
**Solution**: Verify that your OAuth token hasn't expired.

Last updated: 2024-03-20"""
    }
]

def test_metadata_extraction():
    """测试元数据提取"""
    print("=" * 70)
    print("测试 1: 元数据提取")
    print("=" * 70)
    
    extractor = MetadataExtractor()
    
    for i, doc in enumerate(test_documents, 1):
        print(f"\n文档 {i}: {doc['title']}")
        metadata = extractor.extract_metadata(
            doc['content'],
            filename=f"doc_{i}.md",
            title=doc['title']
        )
        
        print(f"  服务: {metadata.service}")
        print(f"  版本: {metadata.version}")
        print(f"  类型: {metadata.doc_type}")
        print(f"  已弃用: {metadata.deprecated}")
        print(f"  速率限制: {metadata.rate_limits}")
        print(f"  标签: {metadata.tags}")
        print(f"  日期: {metadata.date}")

def test_query_filter_extraction():
    """测试查询过滤器提取"""
    print("\n" + "=" * 70)
    print("测试 2: 查询过滤器提取")
    print("=" * 70)
    
    extractor = QueryFilterExtractor()
    
    test_queries = [
        "How do I authenticate with OAuth in version 2.0?",
        "What are the rate limits for authentication?",
        "How do I troubleshoot 401 errors?",
        "Tell me about storage pricing",
        "Show me the API reference for v1.0",
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        filters = extractor.extract_filters(query)
        if filters:
            explanation = extractor.explain_filters(filters)
            print(f"  过滤器: {explanation}")
            print(f"  详情: {filters}")
        else:
            print("  无过滤器")

def test_metadata_filtering():
    """测试元数据过滤"""
    print("\n" + "=" * 70)
    print("测试 3: 元数据过滤模拟")
    print("=" * 70)
    
    extractor = MetadataExtractor()
    filter_extractor = QueryFilterExtractor()
    
    # 提取所有文档的元数据
    documents_with_metadata = []
    for doc in test_documents:
        metadata = extractor.extract_metadata(
            doc['content'],
            filename=doc['title'],
            title=doc['title']
        )
        documents_with_metadata.append({
            'title': doc['title'],
            'content': doc['content'],
            'metadata': metadata
        })
    
    # 测试查询
    query = "How do I authenticate with OAuth in version 2.0?"
    print(f"\n查询: {query}")
    
    # 提取过滤器
    filters = filter_extractor.extract_filters(query)
    print(f"提取的过滤器: {filter_extractor.explain_filters(filters)}")
    
    # 模拟过滤
    print("\n过滤结果:")
    matching_docs = []
    for doc in documents_with_metadata:
        match = True
        metadata = doc['metadata']
        
        # 版本过滤
        if 'version' in filters:
            if metadata.version != filters['version']:
                match = False
        
        # 服务过滤
        if 'service' in filters and match:
            query_service = filters['service'].lower()
            doc_service = metadata.service.lower()
            if query_service not in doc_service and doc_service not in query_service:
                match = False
        
        if match:
            matching_docs.append(doc)
            print(f"  ✅ {doc['title']}")
            print(f"     服务: {metadata.service}, 版本: {metadata.version}, 类型: {metadata.doc_type}")
        else:
            print(f"  ❌ {doc['title']} (不匹配)")
    
    print(f"\n匹配文档数: {len(matching_docs)}/{len(documents_with_metadata)}")

if __name__ == "__main__":
    test_metadata_extraction()
    test_query_filter_extraction()
    test_metadata_filtering()
    
    print("\n" + "=" * 70)
    print("✅ 所有测试完成")
    print("=" * 70)

