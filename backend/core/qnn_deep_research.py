"""
QNN 深度研究引擎 (Qualitative Neural Network Deep Research)

将 local-deepthink 的核心能力集成到 RAG 平台：
1. RAPTOR 层次化检索 - 多层摘要聚类检索
2. 多 Agent 协作网络 - QNN 架构
3. 反思传播机制 - Qualitative Backpropagation
4. 问题重构与迭代深化

核心优势：
- 用时间换质量：多轮迭代深化思考
- 多视角分析：不同人格 Agent 协作
- 自我改进：反思机制持续优化
- 层次化检索：RAPTOR 索引提升召回

Author: Integrated from local-deepthink
"""

import asyncio
import json
import os
import random
import re
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path

import httpx
from sklearn.cluster import KMeans
import numpy as np


# ============================================
# RAPTOR 层次化检索器
# ============================================

class RAPTORIndex:
    """
    RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval)
    层次化检索索引
    
    核心思想：
    1. 对文档分块
    2. 使用 KMeans 聚类相似块
    3. 为每个簇生成摘要
    4. 递归构建树状结构
    5. 检索时搜索所有层级
    """
    
    def __init__(
        self,
        llm_caller: Callable,
        embedding_caller: Callable,
        chunk_size: int = 800,
        chunk_overlap: int = 150
    ):
        self.llm_caller = llm_caller  # async def call(prompt) -> str
        self.embedding_caller = embedding_caller  # def embed(texts) -> List[List[float]]
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.tree: Dict[str, List[str]] = {}  # level -> [node_ids]
        self.all_nodes: Dict[str, Dict] = {}  # node_id -> {content, embedding, metadata}
        self.embeddings_matrix: Optional[np.ndarray] = None
        self.node_ids_list: List[str] = []
    
    def _split_text(self, text: str) -> List[str]:
        """分块文本"""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            # 尝试在句号或换行处断开
            if end < len(text):
                for sep in ['。', '\n\n', '\n', '。', '.', ' ']:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > self.chunk_size // 2:
                        end = start + last_sep + 1
                        break
            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap
        return [c for c in chunks if len(c) > 50]
    
    async def build_index(
        self,
        documents: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ):
        """
        构建 RAPTOR 索引
        
        Args:
            documents: [{"content": str, "metadata": dict}, ...]
            progress_callback: 进度回调函数
        """
        if progress_callback:
            await progress_callback("Step 1: 分块文档...")
        
        # Level 0: 原始分块
        level_0_ids = []
        for doc_idx, doc in enumerate(documents):
            chunks = self._split_text(doc.get("content", ""))
            for chunk_idx, chunk in enumerate(chunks):
                node_id = f"0_{doc_idx}_{chunk_idx}"
                self.all_nodes[node_id] = {
                    "content": chunk,
                    "metadata": {**doc.get("metadata", {}), "level": 0},
                    "embedding": None
                }
                level_0_ids.append(node_id)
        
        self.tree["0"] = level_0_ids
        
        if progress_callback:
            await progress_callback(f"Level 0: {len(level_0_ids)} 个原始块")
        
        # 为所有块计算嵌入
        all_contents = [self.all_nodes[nid]["content"] for nid in level_0_ids]
        if all_contents:
            embeddings = self.embedding_caller(all_contents)
            for idx, nid in enumerate(level_0_ids):
                self.all_nodes[nid]["embedding"] = embeddings[idx]
        
        # 递归构建上层
        current_level = 0
        while len(self.tree[str(current_level)]) > 3:
            next_level = current_level + 1
            current_ids = self.tree[str(current_level)]
            
            if progress_callback:
                await progress_callback(f"构建 Level {next_level}...")
            
            # 获取当前层的嵌入
            current_embeddings = np.array([
                self.all_nodes[nid]["embedding"] for nid in current_ids
            ])
            
            # 聚类
            n_clusters = max(2, len(current_ids) // 4)
            if n_clusters >= len(current_ids):
                n_clusters = max(1, len(current_ids) - 1)
            
            try:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
                labels = kmeans.fit_predict(current_embeddings)
            except Exception:
                # 聚类失败，结束构建
                break
            
            # 为每个簇生成摘要
            next_level_ids = []
            clusters = {}
            for idx, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(current_ids[idx])
            
            for cluster_id, node_ids in clusters.items():
                # 合并簇中的内容
                cluster_contents = [self.all_nodes[nid]["content"] for nid in node_ids]
                combined = "\n---\n".join(cluster_contents[:5])  # 限制长度
                
                # 生成摘要
                try:
                    summary = await self._summarize(combined)
                except Exception:
                    summary = combined[:500]
                
                new_node_id = f"{next_level}_{cluster_id}"
                
                # 计算摘要嵌入
                summary_embedding = self.embedding_caller([summary])[0]
                
                self.all_nodes[new_node_id] = {
                    "content": summary,
                    "metadata": {"level": next_level, "children": node_ids},
                    "embedding": summary_embedding
                }
                next_level_ids.append(new_node_id)
            
            self.tree[str(next_level)] = next_level_ids
            current_level = next_level
            
            if progress_callback:
                await progress_callback(f"Level {next_level}: {len(next_level_ids)} 个摘要节点")
        
        # 构建统一的嵌入矩阵用于检索
        self.node_ids_list = list(self.all_nodes.keys())
        self.embeddings_matrix = np.array([
            self.all_nodes[nid]["embedding"] for nid in self.node_ids_list
        ])
        
        if progress_callback:
            await progress_callback(f"RAPTOR 索引构建完成: 共 {len(self.all_nodes)} 个节点")
    
    async def _summarize(self, text: str) -> str:
        """使用 LLM 生成摘要"""
        prompt = f"""请对以下内容生成一个简洁的摘要，保留关键信息：

{text[:3000]}

摘要："""
        return await self.llm_caller(prompt)
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        检索相关文档
        
        使用余弦相似度搜索所有层级
        """
        if self.embeddings_matrix is None or len(self.node_ids_list) == 0:
            return []
        
        # 计算查询嵌入
        query_embedding = np.array(self.embedding_caller([query])[0])
        
        # 计算余弦相似度
        norms = np.linalg.norm(self.embeddings_matrix, axis=1)
        query_norm = np.linalg.norm(query_embedding)
        
        # 避免除零
        norms[norms == 0] = 1
        if query_norm == 0:
            query_norm = 1
        
        similarities = np.dot(self.embeddings_matrix, query_embedding) / (norms * query_norm)
        
        # 获取 top_k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            node_id = self.node_ids_list[idx]
            node = self.all_nodes[node_id]
            results.append({
                "content": node["content"],
                "metadata": node["metadata"],
                "score": float(similarities[idx]),
                "node_id": node_id
            })
        
        return results


# ============================================
# Agent 系统
# ============================================

# MBTI 人格类型及其特征
MBTI_PROFILES = {
    "INTJ": {"name": "策略家", "traits": "理性、独立、追求效率", "skills": ["系统分析", "长期规划", "批判性思维"]},
    "INTP": {"name": "逻辑学家", "traits": "好奇、创新、追求真理", "skills": ["抽象推理", "理论构建", "问题解构"]},
    "ENTJ": {"name": "指挥官", "traits": "果断、领导力强、目标导向", "skills": ["战略决策", "资源整合", "执行管理"]},
    "ENTP": {"name": "辩论家", "traits": "机智、挑战传统、善于辩论", "skills": ["创意思维", "多角度分析", "快速适应"]},
    "INFJ": {"name": "提倡者", "traits": "洞察力强、理想主义、关注意义", "skills": ["深度洞察", "价值判断", "综合理解"]},
    "INFP": {"name": "调解者", "traits": "理想主义、创造力、同理心", "skills": ["创意表达", "价值分析", "人文关怀"]},
    "ENFJ": {"name": "主角", "traits": "魅力、影响力、善于激励", "skills": ["团队协调", "沟通表达", "愿景描绘"]},
    "ENFP": {"name": "竞选者", "traits": "热情、创造力、善于连接", "skills": ["发散思维", "可能性探索", "灵感激发"]},
    "ISTJ": {"name": "物流师", "traits": "可靠、务实、注重细节", "skills": ["事实核查", "流程优化", "可靠执行"]},
    "ISFJ": {"name": "守护者", "traits": "细心、忠诚、注重和谐", "skills": ["细节关注", "历史参考", "稳定支持"]},
    "ESTJ": {"name": "执行者", "traits": "组织能力强、直接、传统", "skills": ["项目管理", "标准制定", "高效执行"]},
    "ESFJ": {"name": "领事", "traits": "合作、关怀、注重社交", "skills": ["团队建设", "需求识别", "共识达成"]},
}


@dataclass
class AgentPersona:
    """Agent 人格"""
    id: str
    name: str
    mbti: str
    career: str
    skills: List[str]
    system_prompt: str


@dataclass 
class AgentOutput:
    """Agent 输出"""
    agent_id: str
    problem: str
    solution: str
    reasoning: str
    skills_used: List[str]
    confidence: float = 0.8


class QNNAgent:
    """
    QNN Agent - 代表网络中的一个"神经元"
    
    每个 Agent 有自己的人格、技能和记忆
    """
    
    def __init__(
        self,
        agent_id: str,
        persona: AgentPersona,
        llm_caller: Callable,
    ):
        self.id = agent_id
        self.persona = persona
        self.llm_caller = llm_caller
        self.memory: List[Dict] = []
        self.epoch_history: List[AgentOutput] = []
    
    async def process(
        self,
        input_data: str,
        context: Optional[str] = None
    ) -> AgentOutput:
        """
        处理输入，生成输出
        """
        # 构建记忆字符串
        memory_str = ""
        if self.memory:
            recent_memories = self.memory[-5:]  # 最近5条记忆
            memory_str = "\n".join([f"- {json.dumps(m, ensure_ascii=False)}" for m in recent_memories])
        
        prompt = f"""# 你的身份
{self.persona.system_prompt}

# 你的记忆（过去的行动）
{memory_str if memory_str else "暂无历史记录"}

# 当前任务
{input_data}

{("# 参考上下文" + chr(10) + context) if context else ""}

# 输出要求
请以 JSON 格式输出，包含以下字段：
- "problem": 你理解的问题
- "solution": 你的解决方案
- "reasoning": 你的推理过程
- "skills_used": 你使用的技能列表
- "confidence": 你的置信度 (0-1)

JSON 输出："""

        try:
            response = await self.llm_caller(prompt)
            
            # 解析 JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {
                    "problem": input_data,
                    "solution": response,
                    "reasoning": "直接回复",
                    "skills_used": self.persona.skills[:2],
                    "confidence": 0.7
                }
            
            output = AgentOutput(
                agent_id=self.id,
                problem=data.get("problem", input_data),
                solution=data.get("solution", response),
                reasoning=data.get("reasoning", ""),
                skills_used=data.get("skills_used", []),
                confidence=data.get("confidence", 0.7)
            )
            
            # 更新记忆
            self.memory.append({
                "input": input_data[:200],
                "output_summary": output.solution[:200],
                "skills": output.skills_used
            })
            self.epoch_history.append(output)
            
            return output
            
        except Exception as e:
            return AgentOutput(
                agent_id=self.id,
                problem=input_data,
                solution=f"处理错误: {str(e)}",
                reasoning="",
                skills_used=[],
                confidence=0.1
            )
    
    def get_summary(self) -> str:
        """获取 Agent 的总结"""
        if not self.epoch_history:
            return "暂无历史"
        
        summaries = []
        for h in self.epoch_history[-3:]:
            summaries.append(f"- 问题: {h.problem[:100]}... → 方案: {h.solution[:100]}...")
        
        return "\n".join(summaries)


# ============================================
# QNN 网络
# ============================================

class QNNNetwork:
    """
    Qualitative Neural Network - 质化神经网络
    
    由多层 Agent 组成，模拟神经网络的前向传播和反向传播
    """
    
    def __init__(
        self,
        llm_caller: Callable,
        depth: int = 2,
        agents_per_layer: int = 3,
        selected_mbtis: Optional[List[str]] = None
    ):
        self.llm_caller = llm_caller
        self.depth = depth
        self.agents_per_layer = agents_per_layer
        self.selected_mbtis = selected_mbtis or list(MBTI_PROFILES.keys())[:agents_per_layer]
        
        self.layers: List[List[QNNAgent]] = []
        self.epoch = 0
        self.all_outputs: List[Dict] = []
    
    async def build_network(
        self,
        original_problem: str,
        progress_callback: Optional[Callable] = None
    ):
        """
        构建 Agent 网络
        """
        if progress_callback:
            await progress_callback("构建 QNN Agent 网络...")
        
        # 问题分解
        sub_problems = await self._decompose_problem(original_problem)
        
        for layer_idx in range(self.depth):
            layer = []
            
            for agent_idx in range(self.agents_per_layer):
                mbti = self.selected_mbtis[agent_idx % len(self.selected_mbtis)]
                profile = MBTI_PROFILES[mbti]
                
                # 分配子问题
                sub_problem_idx = (layer_idx * self.agents_per_layer + agent_idx) % len(sub_problems)
                assigned_problem = sub_problems[sub_problem_idx]
                
                # 创建人格
                persona = AgentPersona(
                    id=f"agent_{layer_idx}_{agent_idx}",
                    name=f"{profile['name']}_{agent_idx}",
                    mbti=mbti,
                    career=f"{profile['name']}研究员",
                    skills=profile['skills'],
                    system_prompt=self._build_agent_prompt(mbti, profile, assigned_problem, layer_idx)
                )
                
                agent = QNNAgent(
                    agent_id=persona.id,
                    persona=persona,
                    llm_caller=self.llm_caller
                )
                layer.append(agent)
            
            self.layers.append(layer)
            
            if progress_callback:
                await progress_callback(f"Layer {layer_idx}: 创建 {len(layer)} 个 Agent")
    
    def _build_agent_prompt(
        self,
        mbti: str,
        profile: Dict,
        assigned_problem: str,
        layer_idx: int
    ) -> str:
        """构建 Agent 系统提示词"""
        return f"""你是一个 **{profile['name']}** (MBTI: {mbti})，一个专门处理复杂问题的研究助手。

## 你的特质
{profile['traits']}

## 你的技能
- {chr(10).join(['- ' + s for s in profile['skills']])}

## 你的任务
你负责从 {profile['name']} 的视角分析问题：
{assigned_problem}

## 协作要求
- 第 {layer_idx} 层 Agent，需要{'综合前层观点' if layer_idx > 0 else '独立分析问题'}
- 发挥你的人格特质和专业技能
- 提供有洞察力的分析和建议
"""
    
    async def _decompose_problem(self, problem: str) -> List[str]:
        """分解问题为子问题"""
        total_agents = self.depth * self.agents_per_layer
        
        prompt = f"""你是一个问题分解专家。请将以下复杂问题分解为 {total_agents} 个互补的子问题。

原始问题：
{problem}

要求：
1. 每个子问题应该从不同角度切入
2. 子问题之间应该有一定的互补性
3. 覆盖问题的各个方面

请输出 JSON 格式：
{{"sub_problems": ["子问题1", "子问题2", ...]}}
"""
        
        try:
            response = await self.llm_caller(prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                sub_problems = data.get("sub_problems", [])
                if len(sub_problems) >= total_agents:
                    return sub_problems[:total_agents]
        except Exception:
            pass
        
        # 回退：使用原问题
        return [problem] * total_agents
    
    async def forward_pass(
        self,
        original_problem: str,
        context: str = "",
        progress_callback: Optional[Callable] = None
    ) -> List[AgentOutput]:
        """
        前向传播 - 所有 Agent 处理问题
        """
        if progress_callback:
            await progress_callback(f"Epoch {self.epoch}: 开始前向传播...")
        
        layer_outputs = []
        prev_layer_context = context
        
        for layer_idx, layer in enumerate(self.layers):
            if progress_callback:
                await progress_callback(f"处理 Layer {layer_idx} ({len(layer)} agents)...")
            
            # 构建输入
            if layer_idx == 0:
                input_data = original_problem
            else:
                # 使用前一层的输出作为输入
                prev_outputs = [o.solution for o in layer_outputs[-len(layer):]]
                input_data = f"基于前层分析：\n" + "\n---\n".join(prev_outputs)
            
            # 并行调用所有 Agent
            tasks = [
                agent.process(input_data, prev_layer_context)
                for agent in layer
            ]
            outputs = await asyncio.gather(*tasks)
            layer_outputs.extend(outputs)
            
            # 更新上下文
            prev_layer_context = "\n".join([o.solution for o in outputs])
        
        return layer_outputs
    
    async def synthesize(
        self,
        outputs: List[AgentOutput],
        original_problem: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        综合所有 Agent 的输出
        """
        if progress_callback:
            await progress_callback("综合所有 Agent 观点...")
        
        # 收集最后一层的输出
        last_layer_outputs = outputs[-self.agents_per_layer:]
        
        solutions_text = ""
        for out in last_layer_outputs:
            solutions_text += f"""
### Agent: {out.agent_id}
**问题理解**: {out.problem}
**解决方案**: {out.solution}
**推理过程**: {out.reasoning}
**使用技能**: {', '.join(out.skills_used)}
**置信度**: {out.confidence:.2f}
---
"""
        
        prompt = f"""你是一个综合分析师。请基于多个 AI Agent 的分析，生成一份全面的综合报告。

## 原始问题
{original_problem}

## 各 Agent 分析
{solutions_text}

## 综合报告要求
1. 整合各方观点，找出共识和分歧
2. 权衡不同角度，形成平衡的结论
3. 提供可行的建议和下一步方向
4. 如果有矛盾之处，尝试调和或指出

请生成综合报告："""

        return await self.llm_caller(prompt)
    
    async def reflection_pass(
        self,
        synthesized_result: str,
        original_problem: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        反思传播 - 分析结果，重构问题
        
        这是 QNN 的核心：基于结果反思，提出更深层的问题
        """
        if progress_callback:
            await progress_callback("执行反思传播...")
        
        prompt = f"""你是一个研究反思专家。请分析当前的研究结果，评估是否有显著进展。

## 原始问题
{original_problem}

## 当前综合结果
{synthesized_result}

## 分析要求
1. 评估当前结果的质量和深度
2. 识别尚未解决的方面
3. 如果有进展，提出一个更深层次的后续问题
4. 如果没有进展，建议调整研究方向

请以 JSON 格式输出：
{{
    "has_progress": true/false,
    "quality_score": 0-10,
    "key_insights": ["洞察1", "洞察2"],
    "remaining_gaps": ["缺口1", "缺口2"],
    "next_problem": "更深层次的问题（如果有进展）",
    "adjustment_suggestion": "调整建议（如果没进展）"
}}
"""
        
        try:
            response = await self.llm_caller(prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                if data.get("has_progress") and data.get("next_problem"):
                    return data["next_problem"]
        except Exception:
            pass
        
        return None
    
    async def run_epoch(
        self,
        problem: str,
        context: str = "",
        progress_callback: Optional[Callable] = None
    ) -> Tuple[str, List[AgentOutput]]:
        """
        运行一个完整的 epoch
        
        Returns:
            (synthesized_result, all_outputs)
        """
        self.epoch += 1
        
        # 前向传播
        outputs = await self.forward_pass(problem, context, progress_callback)
        
        # 综合
        result = await self.synthesize(outputs, problem, progress_callback)
        
        # 记录
        self.all_outputs.append({
            "epoch": self.epoch,
            "problem": problem,
            "outputs": [vars(o) for o in outputs],
            "synthesis": result
        })
        
        return result, outputs


# ============================================
# QNN 深度研究引擎
# ============================================

class QNNDeepResearchEngine:
    """
    QNN 深度研究引擎
    
    整合 RAPTOR 检索和 QNN 网络，实现深度研究
    """
    
    def __init__(
        self,
        llm_caller: Callable,
        embedding_caller: Callable,
        qnn_depth: int = 2,
        qnn_agents_per_layer: int = 3,
        max_epochs: int = 3,
        selected_mbtis: Optional[List[str]] = None
    ):
        self.llm_caller = llm_caller
        self.embedding_caller = embedding_caller
        self.qnn_depth = qnn_depth
        self.qnn_agents_per_layer = qnn_agents_per_layer
        self.max_epochs = max_epochs
        self.selected_mbtis = selected_mbtis or ["INTJ", "INTP", "ENTJ"]
        
        self.raptor_index: Optional[RAPTORIndex] = None
        self.qnn_network: Optional[QNNNetwork] = None
        self.research_log: List[Dict] = []
    
    async def initialize(
        self,
        documents: List[Dict[str, Any]],
        original_problem: str,
        progress_callback: Optional[Callable] = None
    ):
        """
        初始化研究引擎
        
        1. 构建 RAPTOR 索引
        2. 构建 QNN 网络
        """
        # 构建 RAPTOR 索引
        if progress_callback:
            await progress_callback("🔍 初始化 RAPTOR 层次化索引...")
        
        self.raptor_index = RAPTORIndex(
            llm_caller=self.llm_caller,
            embedding_caller=self.embedding_caller
        )
        
        if documents:
            await self.raptor_index.build_index(documents, progress_callback)
        
        # 构建 QNN 网络
        if progress_callback:
            await progress_callback("🧠 构建 QNN Agent 网络...")
        
        self.qnn_network = QNNNetwork(
            llm_caller=self.llm_caller,
            depth=self.qnn_depth,
            agents_per_layer=self.qnn_agents_per_layer,
            selected_mbtis=self.selected_mbtis
        )
        
        await self.qnn_network.build_network(original_problem, progress_callback)
    
    async def research(
        self,
        query: str,
        progress_callback: Optional[Callable] = None,
        step_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        执行深度研究
        
        Args:
            query: 研究问题
            progress_callback: 进度回调
            step_callback: 步骤完成回调
            
        Returns:
            研究结果
        """
        start_time = time.time()
        results = {
            "query": query,
            "epochs": [],
            "final_answer": "",
            "insights": [],
            "sources": [],
            "total_duration_ms": 0
        }
        
        current_problem = query
        all_context = ""
        
        for epoch in range(1, self.max_epochs + 1):
            epoch_start = time.time()
            
            if progress_callback:
                await progress_callback(f"🔄 Epoch {epoch}/{self.max_epochs}: 开始研究迭代...")
            
            # Step 1: RAPTOR 检索
            if self.raptor_index:
                if progress_callback:
                    await progress_callback(f"📚 检索相关文档...")
                
                retrieved = self.raptor_index.retrieve(current_problem, top_k=8)
                retrieval_context = "\n\n---\n\n".join([r["content"] for r in retrieved])
                results["sources"].extend([{
                    "content": r["content"][:500],
                    "score": r["score"],
                    "level": r["metadata"].get("level", 0)
                } for r in retrieved])
            else:
                retrieval_context = ""
            
            # Step 2: QNN 前向传播 + 综合
            full_context = f"{all_context}\n\n相关文档：\n{retrieval_context}" if retrieval_context else all_context
            
            synthesis, outputs = await self.qnn_network.run_epoch(
                current_problem,
                full_context,
                progress_callback
            )
            
            # Step 3: 反思传播
            next_problem = await self.qnn_network.reflection_pass(
                synthesis,
                query,
                progress_callback
            )
            
            epoch_result = {
                "epoch": epoch,
                "problem": current_problem,
                "synthesis": synthesis,
                "agent_contributions": len(outputs),
                "duration_ms": (time.time() - epoch_start) * 1000,
                "next_problem": next_problem
            }
            results["epochs"].append(epoch_result)
            
            if step_callback:
                await step_callback({
                    "type": "epoch_complete",
                    "epoch": epoch,
                    "synthesis_preview": synthesis[:500]
                })
            
            # 累积上下文
            all_context += f"\n\n--- Epoch {epoch} 结论 ---\n{synthesis}"
            
            # 如果有新问题，继续迭代
            if next_problem:
                current_problem = next_problem
                if progress_callback:
                    await progress_callback(f"💡 发现更深层问题: {next_problem[:100]}...")
            else:
                if progress_callback:
                    await progress_callback(f"✅ 研究达到收敛，停止迭代")
                break
        
        # 生成最终报告
        if progress_callback:
            await progress_callback("📝 生成最终研究报告...")
        
        final_report = await self._generate_final_report(
            query,
            results["epochs"],
            all_context
        )
        
        results["final_answer"] = final_report
        results["total_duration_ms"] = (time.time() - start_time) * 1000
        
        # 提取关键洞察
        results["insights"] = await self._extract_insights(final_report)
        
        return results
    
    async def _generate_final_report(
        self,
        original_query: str,
        epochs: List[Dict],
        accumulated_context: str
    ) -> str:
        """生成最终研究报告"""
        epoch_summaries = ""
        for ep in epochs:
            epoch_summaries += f"""
### 迭代 {ep['epoch']}
**研究问题**: {ep['problem']}
**主要发现**: {ep['synthesis'][:800]}...
---
"""
        
        prompt = f"""你是一个高级研究报告撰写者。请基于多轮深度研究的结果，生成一份完整的研究报告。

## 原始问题
{original_query}

## 研究过程
{epoch_summaries}

## 报告要求
1. 开篇总结：直接回答原始问题
2. 核心发现：列出最重要的 3-5 个发现
3. 详细分析：展开讨论每个关键点
4. 不同观点：如果有分歧，呈现不同视角
5. 局限性：承认研究的局限
6. 建议：提供可行的建议或下一步方向

请生成结构化的研究报告："""

        return await self.llm_caller(prompt)
    
    async def _extract_insights(self, report: str) -> List[str]:
        """从报告中提取关键洞察"""
        prompt = f"""从以下研究报告中提取 3-5 个最重要的洞察，每个用一句话概括。

报告：
{report[:2000]}

输出 JSON 格式：
{{"insights": ["洞察1", "洞察2", ...]}}
"""
        
        try:
            response = await self.llm_caller(prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("insights", [])
        except Exception:
            pass
        
        return []
    
    def get_network_summary(self) -> Dict:
        """获取网络状态摘要"""
        if not self.qnn_network:
            return {}
        
        summary = {
            "depth": self.qnn_depth,
            "agents_per_layer": self.qnn_agents_per_layer,
            "total_epochs": self.qnn_network.epoch,
            "agents": []
        }
        
        for layer_idx, layer in enumerate(self.qnn_network.layers):
            for agent in layer:
                summary["agents"].append({
                    "id": agent.id,
                    "name": agent.persona.name,
                    "mbti": agent.persona.mbti,
                    "outputs_count": len(agent.epoch_history)
                })
        
        return summary


# ============================================
# 便捷函数
# ============================================

async def run_qnn_deep_research(
    query: str,
    documents: List[Dict[str, Any]],
    llm_caller: Callable,
    embedding_caller: Callable,
    qnn_depth: int = 2,
    qnn_agents: int = 3,
    max_epochs: int = 2,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    执行 QNN 深度研究的便捷函数
    
    Args:
        query: 研究问题
        documents: 文档列表 [{"content": str, "metadata": dict}, ...]
        llm_caller: LLM 调用函数 async def call(prompt) -> str
        embedding_caller: 嵌入函数 def embed(texts) -> List[List[float]]
        qnn_depth: QNN 网络深度
        qnn_agents: 每层 Agent 数量
        max_epochs: 最大迭代次数
        progress_callback: 进度回调
        
    Returns:
        研究结果
    """
    engine = QNNDeepResearchEngine(
        llm_caller=llm_caller,
        embedding_caller=embedding_caller,
        qnn_depth=qnn_depth,
        qnn_agents_per_layer=qnn_agents,
        max_epochs=max_epochs
    )
    
    await engine.initialize(documents, query, progress_callback)
    return await engine.research(query, progress_callback)


# ============================================
# 导出
# ============================================

__all__ = [
    "RAPTORIndex",
    "QNNAgent",
    "QNNNetwork",
    "QNNDeepResearchEngine",
    "run_qnn_deep_research",
    "MBTI_PROFILES",
    "AgentPersona",
    "AgentOutput",
]

