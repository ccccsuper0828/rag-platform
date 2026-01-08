"""
Research 深度研究模式
借鉴 Khoj 的实现，提供多步骤、多工具并行调用的深度研究能力

核心特性：
1. 查询分解：将复杂问题拆分为子问题
2. 并行搜索：同时搜索多个数据源
3. 结果综合：智能合并多个来源的信息
4. 迭代深化：根据中间结果调整搜索策略
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import httpx


class ResearchStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ResearchStep:
    """研究步骤"""
    id: str
    title: str
    description: str
    status: ResearchStepStatus = ResearchStepStatus.PENDING
    result: Optional[str] = None
    duration_ms: float = 0
    tool_used: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchContext:
    """研究上下文，在步骤间传递"""
    original_query: str
    sub_queries: List[str] = field(default_factory=list)
    gathered_info: List[Dict[str, Any]] = field(default_factory=list)
    intermediate_answers: List[str] = field(default_factory=list)
    current_focus: Optional[str] = None


class ResearchMode:
    """
    深度研究模式
    
    支持的工具：
    - document_search: 搜索本地文档
    - web_search: 网络搜索
    - code_execution: 代码执行
    - summarize: 内容摘要
    """
    
    def __init__(
        self,
        rag_id: str,
        user_id: str,
        leann_searcher: Optional[Any] = None,
        web_search_enabled: bool = True,
        code_execution_enabled: bool = False,
        max_iterations: int = 5,
    ):
        self.rag_id = rag_id
        self.user_id = user_id
        self.leann_searcher = leann_searcher
        self.web_search_enabled = web_search_enabled
        self.code_execution_enabled = code_execution_enabled
        self.max_iterations = max_iterations
        
        self.steps: List[ResearchStep] = []
        self.context = None
        self._step_callbacks: List[Callable] = []
    
    def on_step_update(self, callback: Callable[[ResearchStep], None]):
        """注册步骤更新回调"""
        self._step_callbacks.append(callback)
    
    def _notify_step_update(self, step: ResearchStep):
        """通知步骤更新"""
        for callback in self._step_callbacks:
            try:
                callback(step)
            except Exception as e:
                print(f"Step callback error: {e}")
    
    def _add_step(self, title: str, description: str, tool: Optional[str] = None) -> ResearchStep:
        """添加研究步骤"""
        step = ResearchStep(
            id=f"step_{len(self.steps) + 1}",
            title=title,
            description=description,
            tool_used=tool,
        )
        self.steps.append(step)
        return step
    
    def _update_step(
        self,
        step: ResearchStep,
        status: ResearchStepStatus,
        result: Optional[str] = None,
        duration_ms: float = 0,
    ):
        """更新步骤状态"""
        step.status = status
        if result:
            step.result = result
        step.duration_ms = duration_ms
        self._notify_step_update(step)
    
    async def decompose_query(self, query: str) -> List[str]:
        """
        将复杂查询分解为子查询
        
        使用简单的启发式规则或 LLM 来分解
        """
        # 简单的规则分解
        sub_queries = []
        
        # 检测 "和" "以及" 等连接词
        if "和" in query or "以及" in query:
            parts = query.replace("以及", "和").split("和")
            sub_queries.extend([p.strip() for p in parts if p.strip()])
        
        # 检测问号分隔的多个问题
        if "？" in query:
            parts = query.split("？")
            sub_queries.extend([p.strip() + "？" for p in parts if p.strip()])
        
        # 如果没有分解，使用原始查询
        if not sub_queries:
            sub_queries = [query]
        
        return sub_queries[:5]  # 最多5个子查询
    
    async def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索本地文档"""
        if self.leann_searcher:
            try:
                results = self.leann_searcher.search(query, top_k=top_k)
                return [
                    {
                        "source": "document",
                        "content": r.text if hasattr(r, 'text') else str(r),
                        "score": r.score if hasattr(r, 'score') else 0,
                        "metadata": r.metadata if hasattr(r, 'metadata') else {},
                    }
                    for r in results
                ]
            except Exception as e:
                print(f"Document search error: {e}")
        return []
    
    async def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        网络搜索
        
        使用 DuckDuckGo 或其他搜索引擎
        """
        if not self.web_search_enabled:
            return []
        
        try:
            # 使用 DuckDuckGo HTML 搜索
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query, "kl": "cn-zh"},
                    headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}
                )
                
                if response.status_code == 200:
                    # 简单解析结果（实际应使用 BeautifulSoup）
                    return [
                        {
                            "source": "web",
                            "content": f"Web search result for: {query}",
                            "url": "https://duckduckgo.com",
                            "score": 0.8,
                        }
                    ]
        except Exception as e:
            print(f"Web search error: {e}")
        
        return []
    
    async def execute_code(self, code: str) -> Dict[str, Any]:
        """
        执行代码（沙箱环境）
        
        注意：生产环境需要安全沙箱
        """
        if not self.code_execution_enabled:
            return {"error": "Code execution disabled"}
        
        # 简化实现，实际需要安全沙箱
        try:
            # 仅允许安全的数学和数据操作
            safe_globals = {"__builtins__": {}}
            safe_locals = {}
            
            # 不执行实际代码，返回模拟结果
            return {
                "output": "Code execution simulated",
                "success": True,
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def synthesize_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
    ) -> str:
        """
        综合多个来源的结果
        
        生成最终答案
        """
        if not results:
            return "未找到相关信息。"
        
        # 按来源分组
        doc_results = [r for r in results if r.get("source") == "document"]
        web_results = [r for r in results if r.get("source") == "web"]
        
        # 构建综合答案
        answer_parts = []
        
        if doc_results:
            answer_parts.append("📚 **文档信息：**")
            for i, r in enumerate(doc_results[:3], 1):
                content = r.get("content", "")[:500]
                answer_parts.append(f"{i}. {content}")
        
        if web_results:
            answer_parts.append("\n🌐 **网络信息：**")
            for i, r in enumerate(web_results[:3], 1):
                content = r.get("content", "")[:500]
                answer_parts.append(f"{i}. {content}")
        
        return "\n".join(answer_parts)
    
    async def research(
        self,
        query: str,
        options: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """
        执行深度研究
        
        Args:
            query: 研究问题
            options: 研究选项 (searchWeb, runCode, searchDocs)
            
        Returns:
            研究结果
        """
        options = options or {"searchDocs": True, "searchWeb": True, "runCode": False}
        
        self.context = ResearchContext(original_query=query)
        self.steps = []
        all_results = []
        
        start_time = time.time()
        
        # Step 1: 分析查询
        step1 = self._add_step("分析查询", "理解研究问题并规划搜索策略", "query_analysis")
        self._update_step(step1, ResearchStepStatus.RUNNING)
        
        try:
            sub_queries = await self.decompose_query(query)
            self.context.sub_queries = sub_queries
            
            self._update_step(
                step1,
                ResearchStepStatus.COMPLETED,
                f"识别出 {len(sub_queries)} 个子问题",
                (time.time() - start_time) * 1000
            )
        except Exception as e:
            self._update_step(step1, ResearchStepStatus.FAILED, str(e))
            sub_queries = [query]
        
        # Step 2: 搜索文档
        if options.get("searchDocs", True):
            step2 = self._add_step("搜索文档", "在本地知识库中查找相关信息", "document_search")
            self._update_step(step2, ResearchStepStatus.RUNNING)
            
            step2_start = time.time()
            try:
                # 并行搜索所有子查询
                doc_tasks = [self.search_documents(q) for q in sub_queries]
                doc_results_nested = await asyncio.gather(*doc_tasks, return_exceptions=True)
                
                doc_results = []
                for results in doc_results_nested:
                    if isinstance(results, list):
                        doc_results.extend(results)
                
                all_results.extend(doc_results)
                
                self._update_step(
                    step2,
                    ResearchStepStatus.COMPLETED,
                    f"找到 {len(doc_results)} 条相关文档",
                    (time.time() - step2_start) * 1000
                )
            except Exception as e:
                self._update_step(step2, ResearchStepStatus.FAILED, str(e))
        
        # Step 3: 网络搜索
        if options.get("searchWeb", True) and self.web_search_enabled:
            step3 = self._add_step("网络搜索", "在互联网上搜索最新信息", "web_search")
            self._update_step(step3, ResearchStepStatus.RUNNING)
            
            step3_start = time.time()
            try:
                # 并行网络搜索
                web_tasks = [self.search_web(q) for q in sub_queries[:2]]  # 限制网络搜索数量
                web_results_nested = await asyncio.gather(*web_tasks, return_exceptions=True)
                
                web_results = []
                for results in web_results_nested:
                    if isinstance(results, list):
                        web_results.extend(results)
                
                all_results.extend(web_results)
                
                self._update_step(
                    step3,
                    ResearchStepStatus.COMPLETED,
                    f"获取 {len(web_results)} 条网络结果",
                    (time.time() - step3_start) * 1000
                )
            except Exception as e:
                self._update_step(step3, ResearchStepStatus.FAILED, str(e))
        
        # Step 4: 综合结果
        step4 = self._add_step("综合分析", "整合所有信息生成研究报告", "synthesis")
        self._update_step(step4, ResearchStepStatus.RUNNING)
        
        step4_start = time.time()
        try:
            final_answer = await self.synthesize_results(query, all_results)
            
            self._update_step(
                step4,
                ResearchStepStatus.COMPLETED,
                "研究报告生成完成",
                (time.time() - step4_start) * 1000
            )
        except Exception as e:
            self._update_step(step4, ResearchStepStatus.FAILED, str(e))
            final_answer = "研究过程中出现错误，请稍后重试。"
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "query": query,
            "answer": final_answer,
            "steps": [
                {
                    "id": s.id,
                    "title": s.title,
                    "description": s.description,
                    "status": s.status.value,
                    "result": s.result,
                    "duration_ms": s.duration_ms,
                    "tool": s.tool_used,
                }
                for s in self.steps
            ],
            "sources_count": len(all_results),
            "total_duration_ms": total_time,
            "sub_queries": self.context.sub_queries,
        }


# 便捷函数
async def run_research(
    query: str,
    rag_id: str,
    user_id: str,
    leann_searcher: Optional[Any] = None,
    options: Optional[Dict[str, bool]] = None,
) -> Dict[str, Any]:
    """
    执行深度研究的便捷函数
    """
    research = ResearchMode(
        rag_id=rag_id,
        user_id=user_id,
        leann_searcher=leann_searcher,
        web_search_enabled=options.get("searchWeb", True) if options else True,
        code_execution_enabled=options.get("runCode", False) if options else False,
    )
    
    return await research.research(query, options)


# 导出
__all__ = [
    "ResearchMode",
    "ResearchStep",
    "ResearchStepStatus",
    "ResearchContext",
    "run_research",
]

