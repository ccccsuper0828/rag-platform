"""
LLM 实体提取器 - 使用 Claude/LLM 进行智能实体和关系提取
替代基于正则表达式的硬编码方法
"""
import json
import os
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """提取的实体"""
    name: str
    type: str
    description: str = ""
    aliases: List[str] = None
    confidence: float = 1.0


@dataclass
class ExtractedRelationship:
    """提取的关系"""
    source: str
    target: str
    relation_type: str
    description: str = ""
    confidence: float = 1.0


class LLMEntityExtractor:
    """
    使用 LLM 进行智能实体和关系提取
    
    支持的 LLM 后端:
    - claude: Anthropic Claude API
    - openai: OpenAI API
    - local: 本地 AI Partner Runner
    """
    
    EXTRACTION_PROMPT = """你是一个专业的知识图谱构建助手。请从以下文本中提取实体和关系。

## 实体类型
- Person: 人物（包括历史人物、作者、专家等）
- Organization: 组织机构（公司、团队、部门等）
- Technology: 技术相关（编程语言、框架、工具、协议等）
- Concept: 抽象概念（方法论、理论、模式等）
- Location: 地点
- Event: 事件
- Product: 产品或项目
- Document: 文档、论文、书籍等

## 关系类型
- USES: A 使用 B
- IMPLEMENTS: A 实现 B
- CREATED_BY: A 由 B 创建
- PART_OF: A 是 B 的一部分
- DEPENDS_ON: A 依赖 B
- EXTENDS: A 扩展 B
- RELATED_TO: A 与 B 相关
- INTEGRATES: A 集成 B
- MANAGES: A 管理 B
- BELONGS_TO: A 属于 B

## 输入文本
{text}

## 输出格式
请以 JSON 格式返回，结构如下：
```json
{{
  "entities": [
    {{"name": "实体名称", "type": "实体类型", "description": "简短描述", "confidence": 0.95}}
  ],
  "relationships": [
    {{"source": "源实体名称", "target": "目标实体名称", "relation_type": "关系类型", "description": "关系描述", "confidence": 0.9}}
  ]
}}
```

注意：
1. 只提取明确出现在文本中的实体，不要推测
2. 关系的 source 和 target 必须是提取的实体名称
3. confidence 表示提取的确信度 (0-1)
4. 实体名称保持原文形式，不要翻译
5. 每个实体只提取一次，去重处理
"""

    def __init__(
        self,
        backend: str = "local",
        api_key: Optional[str] = None,
        runner_url: str = "http://localhost:9001",
    ):
        self.backend = backend
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.runner_url = runner_url
    
    async def extract(self, text: str, max_length: int = 4000) -> Dict[str, Any]:
        """
        从文本中提取实体和关系
        
        Args:
            text: 输入文本
            max_length: 最大文本长度（避免超过 token 限制）
        
        Returns:
            {"entities": [...], "relationships": [...]}
        """
        # 截断过长文本
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        prompt = self.EXTRACTION_PROMPT.format(text=text)
        
        try:
            if self.backend == "claude":
                response = await self._call_claude(prompt)
            elif self.backend == "openai":
                response = await self._call_openai(prompt)
            else:
                response = await self._call_local_runner(prompt)
            
            return self._parse_response(response)
        
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {"entities": [], "relationships": [], "error": str(e)}
    
    async def _call_claude(self, prompt: str) -> str:
        """调用 Claude API"""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-haiku-20240307",  # 使用较快的模型
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    
    async def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI API"""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_local_runner(self, prompt: str) -> str:
        """调用本地 AI Partner Runner"""
        async with httpx.AsyncClient(timeout=120) as client:
            # 使用一个临时的 workspace 进行实体提取
            response = await client.post(
                f"{self.runner_url}/v1/aipartner/entity-extract",
                json={"text": prompt},
            )
            
            # 如果专门的端点不存在，回退到通用聊天接口
            if response.status_code == 404:
                response = await client.post(
                    f"{self.runner_url}/v1/aipartner/chat",
                    json={
                        "question": prompt,
                        "workspace_name": "entity_extraction",
                        "system_prompt": "You are a knowledge graph extraction assistant. Always respond in valid JSON.",
                    },
                )
            
            response.raise_for_status()
            data = response.json()
            return data.get("answer", data.get("content", ""))
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        try:
            # 尝试提取 JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                # 验证并规范化数据
                entities = []
                for e in data.get("entities", []):
                    if isinstance(e, dict) and "name" in e and "type" in e:
                        entities.append(ExtractedEntity(
                            name=e["name"],
                            type=e["type"],
                            description=e.get("description", ""),
                            aliases=e.get("aliases"),
                            confidence=e.get("confidence", 1.0),
                        ))
                
                relationships = []
                for r in data.get("relationships", []):
                    if isinstance(r, dict) and "source" in r and "target" in r:
                        relationships.append(ExtractedRelationship(
                            source=r["source"],
                            target=r["target"],
                            relation_type=r.get("relation_type", "RELATED_TO"),
                            description=r.get("description", ""),
                            confidence=r.get("confidence", 1.0),
                        ))
                
                return {
                    "entities": [
                        {"name": e.name, "type": e.type, "description": e.description, "confidence": e.confidence}
                        for e in entities
                    ],
                    "relationships": [
                        {"source": r.source, "target": r.target, "type": r.relation_type, "description": r.description, "confidence": r.confidence}
                        for r in relationships
                    ],
                }
            
            return {"entities": [], "relationships": [], "error": "No JSON found in response"}
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"entities": [], "relationships": [], "error": f"JSON parse error: {e}"}


class IntentRecognizer:
    """
    意图识别器 - 使用 LLM 精确识别用户查询意图
    替代硬编码的关键词匹配
    """
    
    INTENT_PROMPT = """你是一个智能意图识别助手。请分析用户的查询，识别其真实意图。

## 可识别的意图类型
- QUESTION: 提问，需要基于知识库回答的问题
- SUMMARIZE: 总结请求，需要对文档或内容进行摘要
- SEARCH: 搜索请求，需要在知识库中查找信息
- ANALYZE: 分析请求，需要对数据或内容进行分析
- COMPARE: 对比请求，需要比较多个概念或实体
- EXPLAIN: 解释请求，需要详细解释某个概念
- CODE: 代码相关请求，需要生成、解释或修改代码
- RESEARCH: 深度研究请求，需要多步骤深入探索
- CHAT: 闲聊，不需要知识库支持的对话
- COMMAND: 系统命令，如"帮我创建..."、"设置..."等
- IDENTITY: 身份询问，如"你是谁"、"我是谁"等

## 用户查询
{query}

## 上下文信息（如果有）
{context}

## 输出格式
请以 JSON 格式返回：
```json
{{
  "primary_intent": "主要意图类型",
  "secondary_intents": ["次要意图列表"],
  "entities": ["查询中涉及的关键实体"],
  "keywords": ["关键词列表"],
  "requires_knowledge_base": true/false,
  "requires_web_search": true/false,
  "confidence": 0.95,
  "suggested_action": "建议的处理方式描述"
}}
```
"""

    def __init__(
        self,
        backend: str = "local",
        api_key: Optional[str] = None,
        runner_url: str = "http://localhost:9001",
    ):
        self.backend = backend
        self.api_key = api_key
        self.runner_url = runner_url
    
    async def recognize(
        self, 
        query: str, 
        context: str = "",
        fast_mode: bool = True
    ) -> Dict[str, Any]:
        """
        识别用户查询的意图
        
        Args:
            query: 用户查询
            context: 可选的上下文信息
            fast_mode: 快速模式，使用简化的规则 + LLM 验证
        
        Returns:
            意图识别结果
        """
        # 快速模式：先用简单规则预判断，再用 LLM 验证
        if fast_mode:
            quick_intent = self._quick_intent_check(query)
            if quick_intent["confidence"] > 0.9:
                return quick_intent
        
        # 完整 LLM 意图识别
        prompt = self.INTENT_PROMPT.format(query=query, context=context or "无")
        
        try:
            if self.backend == "claude" and self.api_key:
                response = await self._call_claude(prompt)
            elif self.backend == "openai" and self.api_key:
                response = await self._call_openai(prompt)
            else:
                response = await self._call_local_runner(prompt)
            
            return self._parse_intent_response(response)
        
        except Exception as e:
            logger.error(f"Intent recognition failed: {e}")
            # 回退到快速模式
            return self._quick_intent_check(query)
    
    def _quick_intent_check(self, query: str) -> Dict[str, Any]:
        """快速意图检测（规则预判断）"""
        query_lower = query.lower().strip()
        
        # 身份询问模式
        identity_patterns = [
            "你是谁", "我是谁", "who are you", "who am i",
            "介绍一下你", "tell me about yourself",
        ]
        if any(p in query_lower for p in identity_patterns):
            return {
                "primary_intent": "IDENTITY",
                "secondary_intents": [],
                "entities": [],
                "keywords": [],
                "requires_knowledge_base": True,  # 需要读取用户画像
                "requires_web_search": False,
                "confidence": 0.95,
                "suggested_action": "读取用户画像和 AI 画像进行回答",
            }
        
        # 总结模式
        summarize_patterns = ["总结", "摘要", "概括", "summarize", "summary", "overview"]
        if any(p in query_lower for p in summarize_patterns):
            return {
                "primary_intent": "SUMMARIZE",
                "secondary_intents": [],
                "entities": [],
                "keywords": [],
                "requires_knowledge_base": True,
                "requires_web_search": False,
                "confidence": 0.85,
                "suggested_action": "对文档进行摘要总结",
            }
        
        # 深度研究模式
        research_patterns = [
            "深入研究", "详细分析", "全面了解", "深度探索",
            "research", "deep dive", "comprehensive", "in-depth",
        ]
        if any(p in query_lower for p in research_patterns):
            return {
                "primary_intent": "RESEARCH",
                "secondary_intents": ["ANALYZE"],
                "entities": [],
                "keywords": [],
                "requires_knowledge_base": True,
                "requires_web_search": True,
                "confidence": 0.85,
                "suggested_action": "启动深度研究模式",
            }
        
        # 代码相关
        code_patterns = [
            "代码", "函数", "实现", "code", "function", "implement",
            "debug", "fix", "bug", "error", "语法",
        ]
        if any(p in query_lower for p in code_patterns):
            return {
                "primary_intent": "CODE",
                "secondary_intents": [],
                "entities": [],
                "keywords": [],
                "requires_knowledge_base": True,
                "requires_web_search": False,
                "confidence": 0.8,
                "suggested_action": "处理代码相关请求",
            }
        
        # 默认：普通问题
        return {
            "primary_intent": "QUESTION",
            "secondary_intents": [],
            "entities": [],
            "keywords": query.split()[:5],
            "requires_knowledge_base": True,
            "requires_web_search": False,
            "confidence": 0.6,
            "suggested_action": "基于知识库回答问题",
        }
    
    async def _call_claude(self, prompt: str) -> str:
        """调用 Claude API"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    
    async def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI API"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_local_runner(self, prompt: str) -> str:
        """调用本地 Runner 进行意图识别"""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.runner_url}/v1/aipartner/intent",
                    json={"query": prompt},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("result", "")
            except:
                pass
        
        # 回退到简单规则
        return json.dumps(self._quick_intent_check(prompt.split("## 用户查询")[-1].split("## 上下文")[0].strip()))
    
    def _parse_intent_response(self, response: str) -> Dict[str, Any]:
        """解析意图识别响应"""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return {
                    "primary_intent": data.get("primary_intent", "QUESTION"),
                    "secondary_intents": data.get("secondary_intents", []),
                    "entities": data.get("entities", []),
                    "keywords": data.get("keywords", []),
                    "requires_knowledge_base": data.get("requires_knowledge_base", True),
                    "requires_web_search": data.get("requires_web_search", False),
                    "confidence": data.get("confidence", 0.5),
                    "suggested_action": data.get("suggested_action", ""),
                }
        except json.JSONDecodeError:
            pass
        
        return self._quick_intent_check(response)

