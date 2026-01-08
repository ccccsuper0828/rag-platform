"""
LightRAG 集成模块 - 使用 LightRAG 作为图谱构建引擎
LightRAG 是一个轻量级的知识图谱 + RAG 系统

特性:
- 自动实体和关系提取
- 图谱增强的检索
- 支持多种 LLM 后端
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LightRAGConfig:
    """LightRAG 配置"""
    working_dir: Path
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1200
    chunk_overlap: int = 100
    max_tokens: int = 4096
    use_local_llm: bool = False
    local_llm_url: str = "http://localhost:9001"


class LightRAGEngine:
    """
    LightRAG 图谱构建引擎
    
    提供:
    1. 文档处理和分块
    2. 自动实体/关系提取
    3. 图谱构建和存储
    4. 图谱增强检索
    """
    
    def __init__(self, config: LightRAGConfig):
        self.config = config
        self.working_dir = Path(config.working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.graph_file = self.working_dir / "graph.json"
        self.index_file = self.working_dir / "index.json"
        
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, Any]] = []
        self._load_graph()
    
    def _load_graph(self):
        """加载已有的图谱"""
        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entities = data.get("entities", {})
                    self.relationships = data.get("relationships", [])
                logger.info(f"Loaded graph: {len(self.entities)} entities, {len(self.relationships)} relationships")
            except Exception as e:
                logger.error(f"Failed to load graph: {e}")
    
    def _save_graph(self):
        """保存图谱"""
        try:
            with open(self.graph_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "entities": self.entities,
                    "relationships": self.relationships,
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved graph: {len(self.entities)} entities, {len(self.relationships)} relationships")
        except Exception as e:
            logger.error(f"Failed to save graph: {e}")
    
    async def insert_document(
        self, 
        text: str, 
        metadata: Dict[str, Any] = None,
        extract_entities: bool = True
    ) -> Dict[str, Any]:
        """
        插入文档并构建图谱
        
        Args:
            text: 文档文本
            metadata: 文档元数据
            extract_entities: 是否提取实体
        
        Returns:
            处理结果
        """
        from .llm_entity_extractor import LLMEntityExtractor
        
        chunks = self._chunk_text(text)
        all_entities = []
        all_relationships = []
        
        if extract_entities:
            extractor = LLMEntityExtractor(
                backend="local" if self.config.use_local_llm else "openai",
                runner_url=self.config.local_llm_url,
            )
            
            for i, chunk in enumerate(chunks):
                try:
                    result = await extractor.extract(chunk)
                    
                    # 添加实体
                    for entity in result.get("entities", []):
                        entity_id = f"{entity['name']}_{entity['type']}"
                        if entity_id not in self.entities:
                            self.entities[entity_id] = {
                                "id": entity_id,
                                "name": entity["name"],
                                "type": entity["type"],
                                "description": entity.get("description", ""),
                                "source_chunks": [i],
                                "count": 1,
                            }
                        else:
                            self.entities[entity_id]["count"] += 1
                            if i not in self.entities[entity_id]["source_chunks"]:
                                self.entities[entity_id]["source_chunks"].append(i)
                        all_entities.append(entity)
                    
                    # 添加关系
                    for rel in result.get("relationships", []):
                        self.relationships.append({
                            "source": rel["source"],
                            "target": rel["target"],
                            "type": rel["type"],
                            "description": rel.get("description", ""),
                            "source_chunk": i,
                        })
                        all_relationships.append(rel)
                
                except Exception as e:
                    logger.error(f"Failed to extract from chunk {i}: {e}")
        
        self._save_graph()
        
        return {
            "chunks_processed": len(chunks),
            "entities_extracted": len(all_entities),
            "relationships_extracted": len(all_relationships),
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
        }
    
    def _chunk_text(self, text: str) -> List[str]:
        """将文本分块"""
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        # 按段落分割
        paragraphs = text.split('\n\n')
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
        
        return chunks
    
    async def query(
        self, 
        query: str, 
        mode: str = "hybrid",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        图谱增强查询
        
        Args:
            query: 查询文本
            mode: 查询模式 ("local", "global", "hybrid")
            top_k: 返回结果数
        
        Returns:
            查询结果
        """
        # 在图谱中搜索相关实体
        relevant_entities = []
        query_lower = query.lower()
        
        for entity_id, entity in self.entities.items():
            name_lower = entity["name"].lower()
            if query_lower in name_lower or name_lower in query_lower:
                relevant_entities.append(entity)
        
        # 获取相关关系
        relevant_rels = []
        entity_names = {e["name"] for e in relevant_entities}
        
        for rel in self.relationships:
            if rel["source"] in entity_names or rel["target"] in entity_names:
                relevant_rels.append(rel)
        
        # 构建上下文
        context_parts = []
        
        if relevant_entities:
            context_parts.append("相关实体:")
            for e in relevant_entities[:top_k]:
                context_parts.append(f"- {e['name']} ({e['type']}): {e.get('description', '')}")
        
        if relevant_rels:
            context_parts.append("\n相关关系:")
            for r in relevant_rels[:top_k]:
                context_parts.append(f"- {r['source']} --[{r['type']}]--> {r['target']}")
        
        return {
            "context": "\n".join(context_parts),
            "entities": relevant_entities[:top_k],
            "relationships": relevant_rels[:top_k],
            "mode": mode,
        }
    
    def get_graph_data(self) -> Dict[str, Any]:
        """获取完整图谱数据用于可视化"""
        nodes = [
            {
                "id": entity_id,
                "name": entity["name"],
                "type": entity["type"],
                "data": entity,
            }
            for entity_id, entity in self.entities.items()
        ]
        
        edges = [
            {
                "id": f"{rel['source']}_{rel['type']}_{rel['target']}",
                "source": f"{rel['source']}_{self._get_entity_type(rel['source'])}",
                "target": f"{rel['target']}_{self._get_entity_type(rel['target'])}",
                "type": rel["type"],
                "data": rel,
            }
            for rel in self.relationships
            if self._entity_exists(rel['source']) and self._entity_exists(rel['target'])
        ]
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
            }
        }
    
    def _get_entity_type(self, name: str) -> str:
        """获取实体类型"""
        for entity_id, entity in self.entities.items():
            if entity["name"] == name:
                return entity["type"]
        return "Unknown"
    
    def _entity_exists(self, name: str) -> bool:
        """检查实体是否存在"""
        for entity in self.entities.values():
            if entity["name"] == name:
                return True
        return False
    
    async def clear(self):
        """清空图谱"""
        self.entities = {}
        self.relationships = []
        self._save_graph()


class LightRAGGraphAdapter:
    """
    LightRAG 图谱适配器
    将 LightRAG 接入统一的图谱适配器接口
    """
    
    def __init__(self, workspace_path: Path, config: Dict[str, Any] = None):
        self.workspace = Path(workspace_path)
        lightrag_config = LightRAGConfig(
            working_dir=self.workspace / "lightrag",
            use_local_llm=config.get("use_local_llm", True) if config else True,
            local_llm_url=config.get("local_llm_url", "http://localhost:9001") if config else "http://localhost:9001",
        )
        self.engine = LightRAGEngine(lightrag_config)
    
    async def build_from_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从文档列表构建图谱"""
        total_result = {
            "documents_processed": 0,
            "total_entities": 0,
            "total_relationships": 0,
        }
        
        for doc in documents:
            text = doc.get("content", doc.get("text", ""))
            if text:
                result = await self.engine.insert_document(text, metadata=doc.get("metadata"))
                total_result["documents_processed"] += 1
                total_result["total_entities"] = result["total_entities"]
                total_result["total_relationships"] = result["total_relationships"]
        
        return total_result
    
    async def query_nodes(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """查询节点"""
        graph_data = self.engine.get_graph_data()
        
        if keyword and keyword != "*":
            # 过滤节点
            keyword_lower = keyword.lower()
            filtered_nodes = [
                n for n in graph_data["nodes"]
                if keyword_lower in n["name"].lower()
            ]
            
            # 获取相关边
            node_ids = {n["id"] for n in filtered_nodes}
            filtered_edges = [
                e for e in graph_data["edges"]
                if e["source"] in node_ids or e["target"] in node_ids
            ]
            
            return {
                "nodes": filtered_nodes,
                "edges": filtered_edges,
            }
        
        return graph_data
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        graph_data = self.engine.get_graph_data()
        return graph_data["stats"]
    
    async def query_with_context(self, query: str) -> Dict[str, Any]:
        """带上下文的查询"""
        return await self.engine.query(query)

