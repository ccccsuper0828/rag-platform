"""
Knowledge Graph Service - 基于 Graphiti 的知识图谱服务
支持 FalkorDB 作为图数据库后端，Ollama 作为本地 LLM
"""

import os
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# 检查是否启用知识图谱
KG_ENABLED = os.getenv("KG_ENABLED", "false").lower() == "true"
FALKORDB_HOST = os.getenv("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", "6379"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# 全局 Graphiti 实例
_graphiti_instance: Optional[Any] = None


class GraphitiService:
    """Graphiti 知识图谱服务封装"""
    
    def __init__(self, user_id: str, rag_id: str):
        self.user_id = user_id
        self.rag_id = rag_id
        # 使用连字符代替下划线，避免 RediSearch 分词问题
        # RediSearch 会把下划线当作分词符号，导致查询语法错误
        safe_user_id = user_id.replace("_", "-")
        safe_rag_id = rag_id.replace("_", "-")
        self.group_id = f"{safe_user_id}-{safe_rag_id}"
        self._graphiti = None
    
    async def _get_graphiti(self):
        """获取或创建 Graphiti 实例"""
        global _graphiti_instance
        
        if _graphiti_instance is not None:
            return _graphiti_instance
        
        if not KG_ENABLED:
            logger.warning("Knowledge Graph is disabled. Set KG_ENABLED=true to enable.")
            return None
        
        try:
            from graphiti_core import Graphiti
            from graphiti_core.driver.falkordb_driver import FalkorDriver
            from graphiti_core.llm_client.config import LLMConfig
            from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
            from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
            from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
            
            # 创建 FalkorDB 驱动
            driver = FalkorDriver(
                host=FALKORDB_HOST,
                port=FALKORDB_PORT,
                database=f"rag_{self.user_id[:8]}"  # 每个用户一个数据库
            )
            
            # 配置 Ollama LLM 客户端
            llm_config = LLMConfig(
                api_key="ollama",  # Ollama 不需要真正的 API key
                model=OLLAMA_MODEL,
                small_model=OLLAMA_MODEL,
                base_url=f"{OLLAMA_URL}/v1",
            )
            
            llm_client = OpenAIGenericClient(config=llm_config)
            
            # 配置 Embedding（使用 Ollama）
            embedder = OpenAIEmbedder(
                config=OpenAIEmbedderConfig(
                    api_key="ollama",
                    embedding_model="nomic-embed-text",
                    embedding_dim=768,
                    base_url=f"{OLLAMA_URL}/v1",
                )
            )
            
            # 配置 Cross Encoder
            cross_encoder = OpenAIRerankerClient(client=llm_client, config=llm_config)
            
            # 创建 Graphiti 实例
            graphiti = Graphiti(
                graph_driver=driver,
                llm_client=llm_client,
                embedder=embedder,
                cross_encoder=cross_encoder,
            )
            
            _graphiti_instance = graphiti
            logger.info(f"Graphiti initialized with FalkorDB at {FALKORDB_HOST}:{FALKORDB_PORT}")
            return graphiti
            
        except ImportError as e:
            logger.error(f"Failed to import Graphiti: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            return None
    
    async def add_document_to_graph(
        self, 
        content: str, 
        source_name: str,
        source_description: str = "RAG document"
    ) -> Dict[str, Any]:
        """将文档内容添加到知识图谱"""
        graphiti = await self._get_graphiti()
        if not graphiti:
            return {"success": False, "error": "Graphiti not available"}
        
        try:
            from graphiti_core.nodes import EpisodeType
            
            # 将文档分块添加为 episodes
            chunks = self._split_content(content)
            
            for i, chunk in enumerate(chunks):
                await graphiti.add_episode(
                    name=f"{source_name}_chunk_{i}",
                    episode_body=chunk,
                    source=EpisodeType.text,
                    source_description=source_description,
                    reference_time=datetime.now(timezone.utc),
                    group_id=self.group_id,
                )
            
            logger.info(f"Added {len(chunks)} chunks to knowledge graph for {source_name}")
            return {
                "success": True,
                "chunks_added": len(chunks),
                "group_id": self.group_id
            }
            
        except Exception as e:
            logger.error(f"Failed to add document to graph: {e}")
            return {"success": False, "error": str(e)}
    
    async def search(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索知识图谱"""
        graphiti = await self._get_graphiti()
        if not graphiti:
            return []
        
        try:
            results = await graphiti.search(
                query=query,
                group_ids=[self.group_id],
                num_results=limit
            )
            
            return [
                {
                    "uuid": str(r.uuid),
                    "fact": r.fact,
                    "source_node": r.source_node_uuid,
                    "target_node": r.target_node_uuid,
                    "valid_at": str(r.valid_at) if hasattr(r, 'valid_at') and r.valid_at else None,
                    "invalid_at": str(r.invalid_at) if hasattr(r, 'invalid_at') and r.invalid_at else None,
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Knowledge graph search failed: {e}")
            return []
    
    async def get_entities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取知识图谱中的实体节点"""
        graphiti = await self._get_graphiti()
        if not graphiti:
            return []
        
        try:
            from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
            
            # 使用节点搜索获取实体
            search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
            search_config.limit = limit
            
            results = await graphiti._search(
                query="*",  # 获取所有实体
                config=search_config,
                group_ids=[self.group_id],
            )
            
            return [
                {
                    "uuid": str(node.uuid),
                    "name": node.name,
                    "summary": node.summary[:200] if node.summary else "",
                    "labels": list(node.labels) if hasattr(node, 'labels') else [],
                    "created_at": str(node.created_at) if hasattr(node, 'created_at') else None,
                }
                for node in results.nodes
            ]
            
        except Exception as e:
            logger.error(f"Failed to get entities: {e}")
            return []
    
    async def get_relationships(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取知识图谱中的关系边"""
        graphiti = await self._get_graphiti()
        if not graphiti:
            return []
        
        try:
            # 搜索获取边
            results = await graphiti.search(
                query="*",
                group_ids=[self.group_id],
                num_results=limit
            )
            
            return [
                {
                    "uuid": str(r.uuid),
                    "fact": r.fact,
                    "source": r.source_node_uuid,
                    "target": r.target_node_uuid,
                    "type": r.name if hasattr(r, 'name') else "RELATED_TO",
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get relationships: {e}")
            return []
    
    async def get_graph_data(self) -> Dict[str, Any]:
        """获取完整的图数据（用于可视化）"""
        entities = await self.get_entities()
        relationships = await self.get_relationships()
        
        # 转换为 D3.js 兼容格式
        nodes = [
            {
                "id": e["uuid"],
                "name": e["name"],
                "group": e["labels"][0] if e["labels"] else "Entity",
                "summary": e["summary"],
            }
            for e in entities
        ]
        
        links = [
            {
                "source": r["source"],
                "target": r["target"],
                "type": r["type"],
                "fact": r["fact"],
            }
            for r in relationships
        ]
        
        return {
            "nodes": nodes,
            "links": links,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(links),
            }
        }
    
    def _split_content(self, content: str, chunk_size: int = 1000) -> List[str]:
        """将内容分块"""
        # 按段落分割
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [content]
    
    async def close(self):
        """关闭连接"""
        global _graphiti_instance
        if _graphiti_instance:
            await _graphiti_instance.close()
            _graphiti_instance = None


# 本地知识图谱缓存（在内存中持久化）
_local_kg_cache: Dict[str, 'LocalKnowledgeGraph'] = {}


# 简化的本地知识图谱（不依赖 FalkorDB）
class LocalKnowledgeGraph:
    """本地知识图谱实现（用于没有 FalkorDB 的环境）"""
    
    def __init__(self, user_id: str, rag_id: str):
        self.user_id = user_id
        self.rag_id = rag_id
        # 使用连字符代替下划线，保持与 GraphitiService 一致
        safe_user_id = user_id.replace("_", "-")
        safe_rag_id = rag_id.replace("_", "-")
        self.cache_key = f"{safe_user_id}-{safe_rag_id}"
        
        # 如果缓存中已有数据，恢复
        if self.cache_key in _local_kg_cache:
            cached = _local_kg_cache[self.cache_key]
            self.nodes = cached.nodes
            self.edges = cached.edges
        else:
            self.nodes: Dict[str, Dict] = {}
            self.edges: List[Dict] = []
            _local_kg_cache[self.cache_key] = self
    
    async def extract_entities_from_text(self, text: str, llm_client=None) -> List[Dict]:
        """使用 spaCy 和正则表达式从文本中提取实体"""
        import re
        
        entities = []
        
        # 尝试使用 spaCy 进行实体提取
        try:
            import spacy
            try:
                nlp = spacy.load("en_core_web_sm")
            except OSError:
                # 如果模型未下载，使用 blank 模型
                nlp = spacy.blank("en")
            
            doc = nlp(text[:50000])  # 限制长度
            for ent in doc.ents:
                if ent.text not in [e["name"] for e in entities]:
                    entities.append({
                        "name": ent.text,
                        "type": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                    })
        except Exception as e:
            logger.warning(f"spaCy extraction failed: {e}, using regex fallback")
        
        # 正则表达式补充提取（特别是保险相关术语）
        patterns = {
            "Person": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            "Organization": r'\b(?:AIA|友邦|平安|中国人寿|太平洋|新华|泰康|人保|安联|保诚|[A-Z]{2,})\b',
            "Insurance": r'\b(?:人寿保险|重疾险|医疗险|意外险|寿险|年金险|投连险|万能险|终身寿险|定期寿险|分红险)\b',
            "Coverage": r'\b(?:保额|保费|保障期限|缴费期|等待期|免责条款|理赔|现金价值|保单贷款)\b',
            "Technology": r'\b(?:Python|JavaScript|TypeScript|React|Vue|FastAPI|Django|Docker|Kubernetes|RAG|LLM|GPT|Claude|API)\b',
            "Amount": r'\b(?:\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:元|万|亿|USD|HKD|RMB)\b',
        }
        
        for entity_type, pattern in patterns.items():
            for match in re.finditer(pattern, text):
                name = match.group()
                if name not in [e["name"] for e in entities] and len(name) > 1:
                    entities.append({
                        "name": name,
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                    })
        
        return entities
    
    async def add_document(self, content: str, source: str) -> Dict:
        """添加文档到本地图"""
        entities = await self.extract_entities_from_text(content)
        
        # 添加节点
        for entity in entities:
            node_id = f"{entity['type']}_{entity['name']}"
            if node_id not in self.nodes:
                self.nodes[node_id] = {
                    "id": node_id,
                    "name": entity["name"],
                    "type": entity["type"],
                    "group": entity["type"],
                    "source": source,
                }
        
        # 创建简单的共现关系（限制数量避免过多）
        new_edges = 0
        for i, e1 in enumerate(entities[:50]):  # 限制前50个实体
            for e2 in entities[i+1:i+10]:  # 每个实体最多连接10个
                edge = {
                    "source": f"{e1['type']}_{e1['name']}",
                    "target": f"{e2['type']}_{e2['name']}",
                    "type": "CO_OCCURS",
                }
                if edge not in self.edges:
                    self.edges.append(edge)
                    new_edges += 1
        
        # 保存到缓存
        _local_kg_cache[self.cache_key] = self
        
        return {
            "success": True,
            "entities_found": len(entities),
            "edges_created": new_edges
        }
    
    def get_graph_data(self) -> Dict:
        """获取图数据"""
        return {
            "nodes": list(self.nodes.values()),
            "links": self.edges,
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
            }
        }


def get_knowledge_graph_service(user_id: str, rag_id: str):
    """获取知识图谱服务实例"""
    if KG_ENABLED:
        return GraphitiService(user_id, rag_id)
    else:
        return LocalKnowledgeGraph(user_id, rag_id)

