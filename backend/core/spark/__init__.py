"""
光源算法模块 (Spark Algorithm)

将每一次 RAG 问答转化为可计量、可交易、可激励的"知识行为资产"。

核心组件:
- models: 数据模型定义
- calculator: 光源值计算器
- router: API 路由
"""

from .models import (
    ConversationSpark,
    KnowledgeNodeSpark,
    UserSparkProfile,
    SparkSnapshot,
    SparkConfig
)
from .calculator import SparkCalculator
from .router import spark_router

__all__ = [
    "ConversationSpark",
    "KnowledgeNodeSpark",
    "UserSparkProfile",
    "SparkSnapshot",
    "SparkConfig",
    "SparkCalculator",
    "spark_router"
]
