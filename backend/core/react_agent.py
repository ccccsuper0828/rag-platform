"""
ReAct Agent 实现
基于 "Reasoning and Acting" 范式的智能代理

核心循环：
Thought → Action → Observation → Thought → ...

特性：
1. 动态推理：根据观察结果调整下一步行动
2. 多工具调用：支持搜索、计算、代码执行等
3. 反思机制：每步都有自我评估
4. 最大迭代限制：防止无限循环
"""

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx


class ActionType(str, Enum):
    """可用的 Action 类型"""
    SEARCH = "search"           # 搜索文档
    WEB_SEARCH = "web_search"   # 网络搜索
    CALCULATE = "calculate"     # 数学计算
    LOOKUP = "lookup"           # 查找特定信息
    SUMMARIZE = "summarize"     # 总结内容
    COMPARE = "compare"         # 对比分析
    FINISH = "finish"           # 完成任务


@dataclass
class ThoughtActionObservation:
    """单个 ReAct 循环步骤"""
    step: int
    thought: str                      # 推理过程
    action: ActionType                # 选择的动作
    action_input: str                 # 动作输入
    observation: str = ""             # 动作结果
    is_final: bool = False            # 是否是最终答案
    confidence: float = 0.0           # 置信度 0-1
    duration_ms: float = 0.0


@dataclass
class ReActTrace:
    """完整的 ReAct 执行轨迹"""
    query: str
    steps: List[ThoughtActionObservation] = field(default_factory=list)
    final_answer: str = ""
    total_duration_ms: float = 0.0
    success: bool = False
    error: Optional[str] = None


class ReActAgent:
    """
    ReAct 智能代理
    
    实现 Thought → Action → Observation 循环推理
    """
    
    # ReAct 提示模板
    SYSTEM_PROMPT = """你是一个遵循 ReAct 范式的智能助手。对于每个问题，你需要：

1. **Thought**: 分析当前情况，思考下一步该做什么
2. **Action**: 选择一个动作执行
3. **Observation**: 观察动作的结果

可用的动作:
- search[query]: 在用户文档中搜索相关信息
- web_search[query]: 在互联网上搜索信息
- calculate[expression]: 执行数学计算
- lookup[term]: 查找特定术语或概念
- summarize[text]: 总结一段文本
- compare[item1 vs item2]: 对比两个事物
- finish[answer]: 给出最终答案

规则:
1. 每次只能执行一个动作
2. 根据观察结果决定下一步
3. 如果已有足够信息，使用 finish[答案] 结束
4. 最多执行 {max_steps} 步

输出格式:
Thought: [你的思考过程]
Action: [动作名称][参数]
"""

    STEP_PROMPT = """
当前问题: {query}

已执行的步骤:
{history}

上一步的观察结果:
{last_observation}

请继续推理，给出下一步的 Thought 和 Action。
如果已有足够信息回答问题，使用 Action: finish[你的答案]

Thought:"""

    def __init__(
        self,
        max_steps: int = 8,
        search_fn: Optional[Callable] = None,
        web_search_fn: Optional[Callable] = None,
        llm_fn: Optional[Callable] = None,
    ):
        self.max_steps = max_steps
        self.search_fn = search_fn or self._default_search
        self.web_search_fn = web_search_fn or self._default_web_search
        self.llm_fn = llm_fn or self._default_llm
        
        self._action_handlers = {
            ActionType.SEARCH: self._handle_search,
            ActionType.WEB_SEARCH: self._handle_web_search,
            ActionType.CALCULATE: self._handle_calculate,
            ActionType.LOOKUP: self._handle_lookup,
            ActionType.SUMMARIZE: self._handle_summarize,
            ActionType.COMPARE: self._handle_compare,
            ActionType.FINISH: self._handle_finish,
        }
    
    async def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> ReActTrace:
        """
        执行 ReAct 推理循环
        
        Args:
            query: 用户问题
            context: 额外上下文（如用户记忆、文档等）
            
        Returns:
            ReActTrace: 完整的执行轨迹
        """
        trace = ReActTrace(query=query)
        start_time = time.time()
        
        history = []
        last_observation = "（开始）"
        
        try:
            for step_num in range(1, self.max_steps + 1):
                step_start = time.time()
                
                # 1. 生成 Thought 和 Action
                thought, action, action_input = await self._generate_thought_action(
                    query, history, last_observation
                )
                
                # 2. 执行 Action 获取 Observation
                observation, is_final, confidence = await self._execute_action(
                    action, action_input, context
                )
                
                step_duration = (time.time() - step_start) * 1000
                
                # 3. 记录步骤
                step = ThoughtActionObservation(
                    step=step_num,
                    thought=thought,
                    action=action,
                    action_input=action_input,
                    observation=observation,
                    is_final=is_final,
                    confidence=confidence,
                    duration_ms=step_duration,
                )
                trace.steps.append(step)
                
                # 更新历史
                history.append(f"Step {step_num}:\nThought: {thought}\nAction: {action.value}[{action_input}]\nObservation: {observation}")
                last_observation = observation
                
                # 4. 检查是否完成
                if is_final:
                    trace.final_answer = observation
                    trace.success = True
                    break
            
            # 如果达到最大步数仍未完成，尝试总结
            if not trace.success:
                trace.final_answer = await self._force_finish(query, history)
                trace.success = True
                
        except Exception as e:
            trace.error = str(e)
            trace.success = False
        
        trace.total_duration_ms = (time.time() - start_time) * 1000
        return trace
    
    async def _generate_thought_action(
        self, 
        query: str, 
        history: List[str], 
        last_observation: str
    ) -> Tuple[str, ActionType, str]:
        """生成下一步的 Thought 和 Action"""
        
        prompt = self.STEP_PROMPT.format(
            query=query,
            history="\n\n".join(history) if history else "（尚无）",
            last_observation=last_observation,
        )
        
        # 调用 LLM 生成
        response = await self.llm_fn(prompt)
        
        # 解析 Thought 和 Action
        thought, action, action_input = self._parse_response(response)
        
        return thought, action, action_input
    
    def _parse_response(self, response: str) -> Tuple[str, ActionType, str]:
        """解析 LLM 响应，提取 Thought 和 Action"""
        
        # 提取 Thought
        thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|$)", response, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else response.split("Action:")[0].strip()
        
        # 提取 Action
        action_match = re.search(r"Action:\s*(\w+)\[([^\]]*)\]", response)
        if action_match:
            action_name = action_match.group(1).lower()
            action_input = action_match.group(2).strip()
        else:
            # 默认使用 finish
            action_name = "finish"
            action_input = thought
        
        # 映射 action 名称
        action_map = {
            "search": ActionType.SEARCH,
            "web_search": ActionType.WEB_SEARCH,
            "websearch": ActionType.WEB_SEARCH,
            "calculate": ActionType.CALCULATE,
            "calc": ActionType.CALCULATE,
            "lookup": ActionType.LOOKUP,
            "summarize": ActionType.SUMMARIZE,
            "summary": ActionType.SUMMARIZE,
            "compare": ActionType.COMPARE,
            "finish": ActionType.FINISH,
            "answer": ActionType.FINISH,
        }
        
        action = action_map.get(action_name, ActionType.FINISH)
        
        return thought, action, action_input
    
    async def _execute_action(
        self, 
        action: ActionType, 
        action_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, bool, float]:
        """
        执行动作并返回观察结果
        
        Returns:
            (observation, is_final, confidence)
        """
        handler = self._action_handlers.get(action, self._handle_finish)
        return await handler(action_input, context)
    
    async def _handle_search(self, query: str, context: Optional[Dict] = None) -> Tuple[str, bool, float]:
        """搜索文档"""
        try:
            results = await self.search_fn(query)
            if results:
                observation = f"找到 {len(results)} 条相关结果:\n"
                for i, r in enumerate(results[:3], 1):
                    content = r.get("content", "")[:300]
                    observation += f"{i}. {content}...\n"
                return observation, False, 0.7
            else:
                return "未找到相关文档。", False, 0.3
        except Exception as e:
            return f"搜索失败: {e}", False, 0.1
    
    async def _handle_web_search(self, query: str, context: Optional[Dict] = None) -> Tuple[str, bool, float]:
        """网络搜索"""
        try:
            results = await self.web_search_fn(query)
            if results:
                observation = f"网络搜索结果:\n"
                for i, r in enumerate(results[:3], 1):
                    title = r.get("title", "")
                    snippet = r.get("snippet", "")[:200]
                    observation += f"{i}. {title}: {snippet}...\n"
                return observation, False, 0.6
            else:
                return "网络搜索未返回结果。", False, 0.2
        except Exception as e:
            return f"网络搜索失败: {e}", False, 0.1
    
    async def _handle_calculate(self, expression: str, context: Optional[Dict] = None) -> Tuple[str, bool, float]:
        """数学计算"""
        import math
        
        try:
            safe_dict = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, "sqrt": math.sqrt,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "log": math.log, "log10": math.log10, "exp": math.exp,
                "pi": math.pi, "e": math.e,
            }
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return f"计算结果: {expression} = {result}", False, 0.95
        except Exception as e:
            return f"计算错误: {e}", False, 0.1
    
    async def _handle_lookup(self, term: str, context: Optional[Dict] = None) -> Tuple[str, bool, float]:
        """查找术语"""
        # 先尝试文档搜索
        return await self._handle_search(f"什么是 {term}", context)
    
    async def _handle_summarize(self, text: str, context: Optional[Dict] = None) -> Tuple[str, bool, float]:
        """总结文本"""
        prompt = f"请用 2-3 句话总结以下内容:\n{text[:2000]}"
        try:
            summary = await self.llm_fn(prompt)
            return f"总结: {summary}", False, 0.8
        except Exception as e:
            return f"总结失败: {e}", False, 0.2
    
    async def _handle_compare(self, items: str, context: Optional[Dict] = None) -> Tuple[str, bool, float]:
        """对比分析"""
        prompt = f"请对比分析: {items}"
        try:
            comparison = await self.llm_fn(prompt)
            return f"对比结果: {comparison}", False, 0.7
        except Exception as e:
            return f"对比失败: {e}", False, 0.2
    
    async def _handle_finish(self, answer: str, context: Optional[Dict] = None) -> Tuple[str, bool, float]:
        """完成任务"""
        return answer, True, 0.9
    
    async def _force_finish(self, query: str, history: List[str]) -> str:
        """强制生成最终答案"""
        prompt = f"""基于以下推理过程，请给出最终答案:

问题: {query}

推理过程:
{chr(10).join(history[-5:])}

请直接给出简洁的答案:"""
        
        try:
            return await self.llm_fn(prompt)
        except:
            return "无法生成最终答案，请查看推理过程。"
    
    # 默认实现
    async def _default_search(self, query: str) -> List[Dict]:
        """默认搜索实现"""
        return []
    
    async def _default_web_search(self, query: str) -> List[Dict]:
        """默认网络搜索实现"""
        return []
    
    async def _default_llm(self, prompt: str) -> str:
        """默认 LLM 实现（需要替换）"""
        # 简单的规则匹配作为 fallback
        if "finish" in prompt.lower():
            return "Action: finish[基于现有信息无法给出完整答案]"
        return f"Thought: 分析问题中...\nAction: search[{prompt[:50]}]"


# ============ Planning Agent ============

@dataclass
class PlanStep:
    """计划步骤"""
    id: int
    description: str
    depends_on: List[int] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None


@dataclass
class Plan:
    """执行计划"""
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    current_step: int = 0
    completed: bool = False


class PlanningAgent:
    """
    Planning Agent 实现
    
    两阶段执行:
    1. Plan: 分析问题，制定执行计划
    2. Execute: 按计划逐步执行，动态调整
    
    特性:
    - 任务分解
    - 依赖管理
    - 反思调整
    - 并行执行（当步骤无依赖时）
    """
    
    PLANNING_PROMPT = """你是一个任务规划专家。请为以下目标制定执行计划。

目标: {goal}

要求:
1. 将目标分解为 3-7 个具体步骤
2. 每个步骤应该是可执行的具体任务
3. 标注步骤之间的依赖关系
4. 考虑并行执行的可能性

输出格式（JSON）:
{{
  "steps": [
    {{"id": 1, "description": "步骤描述", "depends_on": []}},
    {{"id": 2, "description": "步骤描述", "depends_on": [1]}},
    ...
  ]
}}

请生成计划:"""

    REFLECTION_PROMPT = """评估当前执行状态，决定是否需要调整计划。

原始目标: {goal}
当前计划: {plan}
已完成步骤: {completed}
当前结果: {current_result}

问题:
1. 当前进展是否符合预期？
2. 是否需要调整后续步骤？
3. 是否可以提前结束？

请给出简短评估和建议:"""

    def __init__(
        self,
        llm_fn: Optional[Callable] = None,
        react_agent: Optional[ReActAgent] = None,
        max_replans: int = 2,
    ):
        self.llm_fn = llm_fn
        self.react_agent = react_agent or ReActAgent()
        self.max_replans = max_replans
    
    async def run(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行 Plan-and-Execute 流程
        
        Args:
            goal: 用户目标
            context: 额外上下文
            
        Returns:
            执行结果
        """
        start_time = time.time()
        results = {
            "goal": goal,
            "plans": [],
            "steps_executed": [],
            "final_result": "",
            "success": False,
            "total_duration_ms": 0,
        }
        
        try:
            # Phase 1: 制定计划
            plan = await self._create_plan(goal)
            results["plans"].append(self._plan_to_dict(plan))
            
            replan_count = 0
            
            # Phase 2: 执行计划
            while not plan.completed and plan.current_step < len(plan.steps):
                step = plan.steps[plan.current_step]
                
                # 检查依赖
                if not self._dependencies_met(step, plan):
                    plan.current_step += 1
                    continue
                
                # 执行步骤（使用 ReAct Agent）
                step.status = "running"
                trace = await self.react_agent.run(step.description, context)
                
                step.result = trace.final_answer
                step.status = "completed" if trace.success else "failed"
                
                results["steps_executed"].append({
                    "step_id": step.id,
                    "description": step.description,
                    "result": step.result,
                    "react_steps": len(trace.steps),
                })
                
                # 反思与调整
                should_replan = await self._should_replan(plan, step)
                if should_replan and replan_count < self.max_replans:
                    plan = await self._replan(plan, step)
                    results["plans"].append(self._plan_to_dict(plan))
                    replan_count += 1
                else:
                    plan.current_step += 1
                
                # 检查是否可以提前完成
                if await self._can_finish_early(plan, goal):
                    plan.completed = True
            
            # 汇总结果
            results["final_result"] = await self._synthesize_results(goal, plan)
            results["success"] = True
            
        except Exception as e:
            results["error"] = str(e)
        
        results["total_duration_ms"] = (time.time() - start_time) * 1000
        return results
    
    async def _create_plan(self, goal: str) -> Plan:
        """创建执行计划"""
        prompt = self.PLANNING_PROMPT.format(goal=goal)
        
        if self.llm_fn:
            response = await self.llm_fn(prompt)
        else:
            # 默认简单计划
            response = json.dumps({
                "steps": [
                    {"id": 1, "description": f"搜索关于 '{goal}' 的信息", "depends_on": []},
                    {"id": 2, "description": "分析搜索结果", "depends_on": [1]},
                    {"id": 3, "description": "总结并给出答案", "depends_on": [2]},
                ]
            })
        
        # 解析计划
        try:
            # 尝试提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                plan_data = {"steps": []}
        except:
            plan_data = {"steps": []}
        
        plan = Plan(goal=goal)
        for step_data in plan_data.get("steps", []):
            plan.steps.append(PlanStep(
                id=step_data.get("id", len(plan.steps) + 1),
                description=step_data.get("description", "执行任务"),
                depends_on=step_data.get("depends_on", []),
            ))
        
        # 确保至少有一个步骤
        if not plan.steps:
            plan.steps.append(PlanStep(id=1, description=f"分析并回答: {goal}"))
        
        return plan
    
    def _dependencies_met(self, step: PlanStep, plan: Plan) -> bool:
        """检查步骤依赖是否满足"""
        for dep_id in step.depends_on:
            dep_step = next((s for s in plan.steps if s.id == dep_id), None)
            if dep_step and dep_step.status != "completed":
                return False
        return True
    
    async def _should_replan(self, plan: Plan, current_step: PlanStep) -> bool:
        """判断是否需要重新规划"""
        if current_step.status == "failed":
            return True
        
        # 简单启发式：如果结果为空或太短，可能需要调整
        if current_step.result and len(current_step.result) < 20:
            return True
        
        return False
    
    async def _replan(self, plan: Plan, failed_step: PlanStep) -> Plan:
        """重新规划"""
        # 简化实现：标记失败步骤，添加备选步骤
        new_step = PlanStep(
            id=len(plan.steps) + 1,
            description=f"使用替代方法: {failed_step.description}",
            depends_on=[s.id for s in plan.steps if s.status == "completed"],
        )
        plan.steps.append(new_step)
        plan.current_step = len(plan.steps) - 1
        return plan
    
    async def _can_finish_early(self, plan: Plan, goal: str) -> bool:
        """判断是否可以提前完成"""
        completed = [s for s in plan.steps if s.status == "completed"]
        if len(completed) >= 2:
            # 检查是否已有足够信息
            combined = " ".join([s.result or "" for s in completed])
            if len(combined) > 200:
                return True
        return False
    
    async def _synthesize_results(self, goal: str, plan: Plan) -> str:
        """综合所有步骤结果"""
        completed_results = [
            f"- {s.description}: {s.result}"
            for s in plan.steps
            if s.status == "completed" and s.result
        ]
        
        if not completed_results:
            return "未能收集到足够信息来回答问题。"
        
        summary = f"针对目标「{goal}」的分析结果:\n\n"
        summary += "\n".join(completed_results)
        
        return summary
    
    def _plan_to_dict(self, plan: Plan) -> Dict[str, Any]:
        """将计划转换为字典"""
        return {
            "goal": plan.goal,
            "steps": [
                {
                    "id": s.id,
                    "description": s.description,
                    "depends_on": s.depends_on,
                    "status": s.status,
                    "result": s.result,
                }
                for s in plan.steps
            ],
            "current_step": plan.current_step,
            "completed": plan.completed,
        }


# ============ 便捷函数 ============

async def run_react(
    query: str,
    search_fn: Optional[Callable] = None,
    llm_fn: Optional[Callable] = None,
    max_steps: int = 6,
) -> ReActTrace:
    """
    运行 ReAct Agent
    """
    agent = ReActAgent(
        max_steps=max_steps,
        search_fn=search_fn,
        llm_fn=llm_fn,
    )
    return await agent.run(query)


async def run_planning(
    goal: str,
    llm_fn: Optional[Callable] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    运行 Planning Agent
    """
    agent = PlanningAgent(llm_fn=llm_fn)
    return await agent.run(goal, context)


# 导出
__all__ = [
    "ActionType",
    "ThoughtActionObservation",
    "ReActTrace",
    "ReActAgent",
    "PlanStep",
    "Plan",
    "PlanningAgent",
    "run_react",
    "run_planning",
]

