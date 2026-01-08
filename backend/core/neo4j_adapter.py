"""
Neo4j 图谱适配器 - 连接 Neo4j 图数据库
支持高性能图查询和知识图谱存储
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import os
import logging

from .graph_adapters import GraphAdapter, GraphMetadata

logger = logging.getLogger(__name__)


@dataclass
class Neo4jConfig:
    """Neo4j 连接配置"""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"


class Neo4jGraphAdapter(GraphAdapter):
    """
    Neo4j 图谱适配器
    
    提供对 Neo4j 图数据库的统一访问接口
    支持知识图谱的存储、查询和可视化
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.neo4j_config = Neo4jConfig(
            uri=config.get("uri", os.getenv("NEO4J_URI", "bolt://localhost:7687")),
            username=config.get("username", os.getenv("NEO4J_USER", "neo4j")),
            password=config.get("password", os.getenv("NEO4J_PASSWORD", "password")),
            database=config.get("database", os.getenv("NEO4J_DATABASE", "neo4j")),
        )
        self._driver = None
        self._connected = False
    
    def _get_metadata(self) -> GraphMetadata:
        return GraphMetadata(
            graph_type="neo4j",
            id_field="elementId",
            name_field="name",
            supports_search=True,
        )
    
    async def connect(self):
        """建立与 Neo4j 的连接"""
        try:
            from neo4j import AsyncGraphDatabase
            self._driver = AsyncGraphDatabase.driver(
                self.neo4j_config.uri,
                auth=(self.neo4j_config.username, self.neo4j_config.password)
            )
            # 验证连接
            async with self._driver.session(database=self.neo4j_config.database) as session:
                await session.run("RETURN 1")
            self._connected = True
            logger.info(f"Connected to Neo4j at {self.neo4j_config.uri}")
        except ImportError:
            logger.warning("neo4j package not installed. Run: pip install neo4j")
            self._connected = False
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._connected = False
    
    async def disconnect(self):
        """断开连接"""
        if self._driver:
            await self._driver.close()
            self._connected = False
    
    async def query_nodes(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """
        查询节点和边
        
        Args:
            keyword: 搜索关键词，"*" 返回所有节点
            max_nodes: 最大返回节点数 (默认 100)
            max_depth: 关系深度 (默认 2)
            labels: 过滤的节点标签列表
        
        Returns:
            {"nodes": [...], "edges": [...]}
        """
        if not self._connected:
            await self.connect()
            if not self._connected:
                return {"nodes": [], "edges": []}
        
        max_nodes = kwargs.get("max_nodes", 100)
        max_depth = kwargs.get("max_depth", 2)
        labels = kwargs.get("labels", [])
        
        try:
            async with self._driver.session(database=self.neo4j_config.database) as session:
                # 构建查询
                if keyword == "*" or not keyword:
                    # 返回所有节点及其关系
                    cypher = """
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]->(m)
                    RETURN n, r, m
                    LIMIT $limit
                    """
                    params = {"limit": max_nodes}
                else:
                    # 按关键词搜索
                    cypher = """
                    MATCH (n)
                    WHERE n.name =~ $pattern OR n.label =~ $pattern OR any(prop in keys(n) WHERE n[prop] =~ $pattern)
                    OPTIONAL MATCH (n)-[r*1..{depth}]-(m)
                    RETURN n, r, m
                    LIMIT $limit
                    """.replace("{depth}", str(max_depth))
                    params = {
                        "pattern": f"(?i).*{keyword}.*",
                        "limit": max_nodes
                    }
                
                result = await session.run(cypher, params)
                records = await result.data()
                
                nodes = {}
                edges = []
                
                for record in records:
                    # 处理节点
                    if record.get("n"):
                        node = record["n"]
                        node_id = str(node.element_id) if hasattr(node, 'element_id') else str(id(node))
                        if node_id not in nodes:
                            nodes[node_id] = self._create_standard_node(
                                node_id=node_id,
                                name=node.get("name", node.get("label", node_id)),
                                entity_type=list(node.labels)[0] if node.labels else "Entity",
                                properties=dict(node),
                            )
                    
                    if record.get("m"):
                        node = record["m"]
                        node_id = str(node.element_id) if hasattr(node, 'element_id') else str(id(node))
                        if node_id not in nodes:
                            nodes[node_id] = self._create_standard_node(
                                node_id=node_id,
                                name=node.get("name", node.get("label", node_id)),
                                entity_type=list(node.labels)[0] if node.labels else "Entity",
                                properties=dict(node),
                            )
                    
                    # 处理关系
                    if record.get("r"):
                        rels = record["r"]
                        if not isinstance(rels, list):
                            rels = [rels]
                        for rel in rels:
                            if rel:
                                edge_id = str(rel.element_id) if hasattr(rel, 'element_id') else str(id(rel))
                                edges.append(self._create_standard_edge(
                                    edge_id=edge_id,
                                    source_id=str(rel.start_node.element_id),
                                    target_id=str(rel.end_node.element_id),
                                    edge_type=rel.type,
                                    properties=dict(rel),
                                ))
                
                return {
                    "nodes": list(nodes.values()),
                    "edges": edges,
                }
        
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            return {"nodes": [], "edges": []}
    
    async def add_entity(self, entity: Dict[str, Any]) -> str:
        """添加实体节点"""
        if not self._connected:
            await self.connect()
        
        try:
            async with self._driver.session(database=self.neo4j_config.database) as session:
                label = entity.get("type", "Entity")
                props = {k: v for k, v in entity.items() if k != "type"}
                
                cypher = f"""
                CREATE (n:{label} $props)
                RETURN elementId(n) as id
                """
                result = await session.run(cypher, {"props": props})
                record = await result.single()
                return record["id"] if record else None
        except Exception as e:
            logger.error(f"Failed to add entity: {e}")
            return None
    
    async def add_relationship(
        self, 
        source_id: str, 
        target_id: str, 
        rel_type: str, 
        properties: Dict[str, Any] = None
    ) -> str:
        """添加关系"""
        if not self._connected:
            await self.connect()
        
        try:
            async with self._driver.session(database=self.neo4j_config.database) as session:
                cypher = f"""
                MATCH (a), (b)
                WHERE elementId(a) = $source_id AND elementId(b) = $target_id
                CREATE (a)-[r:{rel_type} $props]->(b)
                RETURN elementId(r) as id
                """
                result = await session.run(cypher, {
                    "source_id": source_id,
                    "target_id": target_id,
                    "props": properties or {}
                })
                record = await result.single()
                return record["id"] if record else None
        except Exception as e:
            logger.error(f"Failed to add relationship: {e}")
            return None
    
    async def import_graph(self, entities: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
        """批量导入图谱数据"""
        if not self._connected:
            await self.connect()
        
        entity_id_map = {}
        imported_entities = 0
        imported_rels = 0
        
        try:
            async with self._driver.session(database=self.neo4j_config.database) as session:
                # 批量创建节点
                for entity in entities:
                    label = entity.get("type", "Entity")
                    name = entity.get("name", entity.get("text", ""))
                    props = {
                        "name": name,
                        **{k: v for k, v in entity.items() if k not in ["type", "text", "name"]}
                    }
                    
                    cypher = f"""
                    MERGE (n:{label} {{name: $name}})
                    SET n += $props
                    RETURN elementId(n) as id
                    """
                    result = await session.run(cypher, {"name": name, "props": props})
                    record = await result.single()
                    if record:
                        entity_id_map[name] = record["id"]
                        imported_entities += 1
                
                # 批量创建关系
                for rel in relationships:
                    source = rel.get("source")
                    target = rel.get("target")
                    rel_type = rel.get("type", "RELATED_TO").upper().replace(" ", "_")
                    
                    if source in entity_id_map and target in entity_id_map:
                        cypher = f"""
                        MATCH (a), (b)
                        WHERE elementId(a) = $source_id AND elementId(b) = $target_id
                        MERGE (a)-[r:{rel_type}]->(b)
                        RETURN elementId(r) as id
                        """
                        result = await session.run(cypher, {
                            "source_id": entity_id_map[source],
                            "target_id": entity_id_map[target],
                        })
                        if await result.single():
                            imported_rels += 1
            
            return {
                "success": True,
                "entities_imported": imported_entities,
                "relationships_imported": imported_rels,
            }
        
        except Exception as e:
            logger.error(f"Failed to import graph: {e}")
            return {
                "success": False,
                "error": str(e),
                "entities_imported": imported_entities,
                "relationships_imported": imported_rels,
            }
    
    async def get_stats(self, **kwargs) -> Dict[str, Any]:
        """获取图谱统计信息"""
        if not self._connected:
            await self.connect()
            if not self._connected:
                return {"total_nodes": 0, "total_edges": 0, "labels": []}
        
        try:
            async with self._driver.session(database=self.neo4j_config.database) as session:
                # 节点数量
                result = await session.run("MATCH (n) RETURN count(n) as count")
                record = await result.single()
                node_count = record["count"] if record else 0
                
                # 关系数量
                result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
                record = await result.single()
                edge_count = record["count"] if record else 0
                
                # 标签统计
                result = await session.run("""
                    CALL db.labels() YIELD label
                    RETURN label
                """)
                records = await result.data()
                labels = [r["label"] for r in records]
                
                return {
                    "total_nodes": node_count,
                    "total_edges": edge_count,
                    "labels": labels,
                    "connected": True,
                }
        
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total_nodes": 0, "total_edges": 0, "labels": [], "error": str(e)}
    
    async def get_labels(self) -> List[str]:
        """获取所有节点标签"""
        stats = await self.get_stats()
        return stats.get("labels", [])
    
    async def clear_graph(self) -> bool:
        """清空图谱 (谨慎使用)"""
        if not self._connected:
            await self.connect()
        
        try:
            async with self._driver.session(database=self.neo4j_config.database) as session:
                await session.run("MATCH (n) DETACH DELETE n")
            logger.warning("Neo4j graph cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear graph: {e}")
            return False


# 注册适配器到工厂
def register_neo4j_adapter():
    """注册 Neo4j 适配器到适配器工厂"""
    from .graph_adapters import GraphAdapterFactory
    GraphAdapterFactory.register_adapter("neo4j", Neo4jGraphAdapter)

