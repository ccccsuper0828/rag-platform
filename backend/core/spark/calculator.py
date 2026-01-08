"""
光源值计算器

实现光源算法的核心计算逻辑：
- 基础质量分计算
- 引用关系分计算
- 知识激活度计算
- 用户行为分计算
"""

import re
import math
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .models import (
    ConversationSpark, 
    KnowledgeNodeSpark, 
    UserSparkProfile,
    SparkSnapshot,
    SparkConfig,
    Citation
)


class SparkCalculator:
    """
    光源值计算器
    
    核心职责：
    1. 计算单次对话的光源值
    2. 更新知识节点的光源贡献
    3. 更新用户的光源档案
    """
    
    def __init__(self):
        self.config = SparkConfig
    
    # ==================== 基础质量分计算 ====================
    
    def calculate_base_score(
        self,
        question: str,
        answer: str,
        citations: List[Citation]
    ) -> Tuple[float, Dict[str, float]]:
        """
        计算基础质量分 (0-30分)
        
        评估维度:
        - 问题质量 (0-10)
        - 回答完整性 (0-10)
        - 引用匹配度 (0-10)
        """
        details = {}
        
        # 1. 问题质量 (0-10分)
        question_score = self._evaluate_question_quality(question)
        details["question_quality"] = question_score
        
        # 2. 回答完整性 (0-10分)
        answer_score = self._evaluate_answer_completeness(answer)
        details["answer_completeness"] = answer_score
        
        # 3. 引用匹配度 (0-10分)
        citation_match_score = self._evaluate_citation_match(answer, citations)
        details["citation_match"] = citation_match_score
        
        total = question_score + answer_score + citation_match_score
        return min(total, self.config.MAX_BASE_SCORE), details
    
    def _evaluate_question_quality(self, question: str) -> float:
        """评估问题质量"""
        score = 0
        
        # 长度评估 (0-3分)
        q_len = len(question)
        if 10 <= q_len <= 50:
            score += 2
        elif 50 < q_len <= 200:
            score += 3  # 适中长度最佳
        elif q_len > 200:
            score += 2
        elif q_len >= 5:
            score += 1
        
        # 是否包含具体术语/关键词 (0-3分)
        # 检查是否有具体的名词、动词等
        specific_patterns = [
            r'什么是|怎么|如何|为什么|哪些|多少',  # 疑问词
            r'\d+',  # 包含数字
            r'[A-Za-z]{3,}',  # 包含英文术语
        ]
        for pattern in specific_patterns:
            if re.search(pattern, question):
                score += 1
        score = min(score, 6)  # 上限6分
        
        # 问题格式良好 (0-4分)
        if question.endswith('?') or question.endswith('？'):
            score += 1
        if not any(c in question for c in ['!', '！', '...']):
            score += 1  # 没有过度感叹
        if len(question.split()) >= 3 or len(question) >= 10:
            score += 2  # 足够详细
        
        return min(score, 10)
    
    def _evaluate_answer_completeness(self, answer: str) -> float:
        """评估回答完整性"""
        score = 0
        
        # 长度评估 (0-4分)
        a_len = len(answer)
        if a_len >= 500:
            score += 4
        elif a_len >= 200:
            score += 3
        elif a_len >= 100:
            score += 2
        elif a_len >= 50:
            score += 1
        
        # 结构化内容 (0-3分)
        # 检查是否有列表、分段等
        if re.search(r'[\n].*[\n]', answer):
            score += 1  # 有分段
        if re.search(r'[1-9][.、]|[-*•]', answer):
            score += 1  # 有列表
        if re.search(r'：|:|首先|其次|最后|总之', answer):
            score += 1  # 有逻辑连接词
        
        # 包含示例或证据 (0-3分)
        if re.search(r'例如|比如|举例|示例', answer):
            score += 1
        if re.search(r'根据|依据|参考|引用', answer):
            score += 1
        if re.search(r'数据|统计|研究|报告', answer):
            score += 1
        
        return min(score, 10)
    
    def _evaluate_citation_match(
        self, 
        answer: str, 
        citations: List[Citation]
    ) -> float:
        """评估引用匹配度"""
        if not citations:
            return 0
        
        score = 0
        
        # 有引用就给基础分 (0-4分)
        citation_count = len(citations)
        score += min(citation_count * 2, 4)
        
        # 引用内容与回答的相关性 (0-6分)
        total_relevance = sum(c.relevance_score for c in citations)
        avg_relevance = total_relevance / len(citations) if citations else 0
        score += avg_relevance * 6  # relevance_score 假设是 0-1
        
        return min(score, 10)
    
    # ==================== 引用关系分计算 ====================
    
    def calculate_citation_score(
        self, 
        citations: List[Citation],
        knowledge_nodes: Dict[str, KnowledgeNodeSpark]
    ) -> Tuple[float, Dict[str, float]]:
        """
        计算引用关系分 (0-25分)
        
        评估维度:
        - 引用数量 (0-10)
        - 引用节点价值 (0-10)
        - 引用多样性 (0-5)
        """
        details = {}
        
        if not citations:
            return 0, {"citation_count": 0, "node_value": 0, "diversity": 0}
        
        # 1. 引用数量 (0-10分)
        citation_count = len(citations)
        count_score = min(citation_count * 2, 10)
        details["citation_count"] = count_score
        
        # 2. 引用节点的价值 (0-10分)
        node_value_score = 0
        for citation in citations:
            node = knowledge_nodes.get(citation.node_id)
            if node:
                # 被多次引用的节点价值更高
                value_contribution = math.log(node.total_citations + 1) * 0.5
                node_value_score += min(value_contribution, 2)
        node_value_score = min(node_value_score, 10)
        details["node_value"] = node_value_score
        
        # 3. 引用多样性 (0-5分)
        unique_sources = set(c.source_file for c in citations if c.source_file)
        diversity_score = min(len(unique_sources), 5)
        details["diversity"] = diversity_score
        
        total = count_score + node_value_score + diversity_score
        return min(total, self.config.MAX_CITATION_SCORE), details
    
    # ==================== 知识激活度计算 ====================
    
    def calculate_activation_score(
        self, 
        question: str,
        answer: str,
        citations: List[Citation], 
        total_knowledge_nodes: int = 100
    ) -> Tuple[float, Dict[str, float]]:
        """
        计算知识激活度 (0-20分)
        
        评估维度:
        - 激活节点数 (0-8)
        - 知识深度 (0-6)
        - 知识覆盖度 (0-6)
        """
        details = {}
        
        # 1. 激活节点数 (0-8分)
        activated_nodes = len(citations)
        activation_score = min(activated_nodes * 2, 8)
        details["activated_nodes"] = activation_score
        
        # 2. 知识深度 - 推理复杂度 (0-6分)
        depth_score = self._evaluate_reasoning_depth(question, answer)
        details["reasoning_depth"] = depth_score
        
        # 3. 知识覆盖度 (0-6分)
        coverage = activated_nodes / max(total_knowledge_nodes, 1)
        coverage_score = min(coverage * 60, 6)  # 覆盖10%得满分
        details["coverage"] = coverage_score
        
        total = activation_score + depth_score + coverage_score
        return min(total, self.config.MAX_ACTIVATION_SCORE), details
    
    def _evaluate_reasoning_depth(self, question: str, answer: str) -> float:
        """评估推理深度"""
        score = 0
        
        # 检查是否涉及因果推理
        causal_patterns = [
            r'因为|所以|导致|造成|原因|结果',
            r'如果|那么|假设|条件',
            r'首先.*然后|第一.*第二',
        ]
        for pattern in causal_patterns:
            if re.search(pattern, answer):
                score += 1
        
        # 检查是否有多角度分析
        perspective_patterns = [
            r'一方面.*另一方面',
            r'优点.*缺点|利.*弊',
            r'从.*角度|从.*来看',
        ]
        for pattern in perspective_patterns:
            if re.search(pattern, answer):
                score += 1
        
        # 检查是否有综合结论
        if re.search(r'综上|总之|总结|因此|所以', answer):
            score += 1
        
        return min(score, 6)
    
    # ==================== 用户行为分计算 ====================
    
    def calculate_behavior_score(
        self,
        like_count: int,
        save_count: int,
        share_count: int,
        reuse_count: int
    ) -> Tuple[float, Dict[str, float]]:
        """
        计算用户行为分 (0-25分)
        
        基于用户互动行为的动态评分
        """
        details = {}
        
        # 1. 点赞分 (0-8分)
        like_score = min(like_count * self.config.LIKE_SCORE, 8)
        details["likes"] = like_score
        
        # 2. 收藏分 (0-7分)
        save_score = min(save_count * self.config.SAVE_SCORE, 7)
        details["saves"] = save_score
        
        # 3. 分享分 (0-5分)
        share_score = min(share_count * self.config.SHARE_SCORE, 5)
        details["shares"] = share_score
        
        # 4. 被复用分 (0-5分) - 最有价值的行为
        reuse_score = min(reuse_count * self.config.REUSE_SCORE, 5)
        details["reuses"] = reuse_score
        
        total = like_score + save_score + share_score + reuse_score
        return min(total, self.config.MAX_BEHAVIOR_SCORE), details
    
    # ==================== 综合计算 ====================
    
    def calculate_spark(
        self, 
        question: str,
        answer: str,
        citations: List[Dict[str, Any]],
        knowledge_nodes: Dict[str, KnowledgeNodeSpark] = None,
        like_count: int = 0,
        save_count: int = 0,
        share_count: int = 0,
        reuse_count: int = 0,
        total_knowledge_nodes: int = 100
    ) -> Dict[str, Any]:
        """
        计算完整的光源值
        
        返回:
        - spark_value: 综合光源值 (0-100)
        - 各维度分数
        - 计算详情
        """
        knowledge_nodes = knowledge_nodes or {}
        
        # 转换 citations
        citation_objs = [
            Citation(
                node_id=c.get("node_id", hashlib.md5(c.get("content", "")[:50].encode()).hexdigest()),
                content_preview=c.get("content", "")[:100],
                relevance_score=c.get("relevance_score", 0.5),
                source_file=c.get("source_file", "")
            )
            for c in citations
        ]
        
        # 计算各维度分数
        base_score, base_details = self.calculate_base_score(
            question, answer, citation_objs
        )
        
        citation_score, citation_details = self.calculate_citation_score(
            citation_objs, knowledge_nodes
        )
        
        activation_score, activation_details = self.calculate_activation_score(
            question, answer, citation_objs, total_knowledge_nodes
        )
        
        behavior_score, behavior_details = self.calculate_behavior_score(
            like_count, save_count, share_count, reuse_count
        )
        
        # 计算综合光源值
        weighted_sum = (
            base_score * self.config.WEIGHT_BASE_QUALITY +
            citation_score * self.config.WEIGHT_CITATION +
            activation_score * self.config.WEIGHT_ACTIVATION +
            behavior_score * self.config.WEIGHT_BEHAVIOR
        )
        
        max_possible = (
            self.config.MAX_BASE_SCORE * self.config.WEIGHT_BASE_QUALITY +
            self.config.MAX_CITATION_SCORE * self.config.WEIGHT_CITATION +
            self.config.MAX_ACTIVATION_SCORE * self.config.WEIGHT_ACTIVATION +
            self.config.MAX_BEHAVIOR_SCORE * self.config.WEIGHT_BEHAVIOR
        )
        
        spark_value = (weighted_sum / max_possible) * 100 if max_possible > 0 else 0
        spark_value = min(round(spark_value, 2), 100)
        
        # 判断 NFT 资格
        nft_eligible = spark_value >= self.config.NFT_ELIGIBILITY_THRESHOLD
        
        return {
            "spark_value": spark_value,
            "nft_eligible": nft_eligible,
            "scores": {
                "base_score": round(base_score, 2),
                "citation_score": round(citation_score, 2),
                "activation_score": round(activation_score, 2),
                "behavior_score": round(behavior_score, 2)
            },
            "details": {
                "base": base_details,
                "citation": citation_details,
                "activation": activation_details,
                "behavior": behavior_details
            },
            "weights": {
                "base": self.config.WEIGHT_BASE_QUALITY,
                "citation": self.config.WEIGHT_CITATION,
                "activation": self.config.WEIGHT_ACTIVATION,
                "behavior": self.config.WEIGHT_BEHAVIOR
            }
        }
    
    def create_conversation_spark(
        self,
        rag_id: str,
        user_id: str,
        question: str,
        answer: str,
        citations: List[Dict[str, Any]],
        **kwargs
    ) -> ConversationSpark:
        """
        创建对话光源记录
        """
        # 计算光源值
        result = self.calculate_spark(
            question=question,
            answer=answer,
            citations=citations,
            **kwargs
        )
        
        # 创建记录
        spark = ConversationSpark(
            rag_id=rag_id,
            user_id=user_id,
            question=question,
            answer=answer,
            citations=[
                Citation(
                    node_id=c.get("node_id", ""),
                    content_preview=c.get("content", "")[:100],
                    relevance_score=c.get("relevance_score", 0.5),
                    source_file=c.get("source_file", "")
                )
                for c in citations
            ],
            base_score=result["scores"]["base_score"],
            citation_score=result["scores"]["citation_score"],
            activation_score=result["scores"]["activation_score"],
            behavior_score=result["scores"]["behavior_score"],
            spark_value=result["spark_value"],
            nft_eligible=result["nft_eligible"]
        )
        
        # 添加初始快照
        spark.spark_history.append(SparkSnapshot(
            spark_value=result["spark_value"],
            base_score=result["scores"]["base_score"],
            citation_score=result["scores"]["citation_score"],
            activation_score=result["scores"]["activation_score"],
            behavior_score=result["scores"]["behavior_score"],
            trigger="create"
        ))
        
        return spark


# 全局计算器实例
spark_calculator = SparkCalculator()
