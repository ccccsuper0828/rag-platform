"""
图谱适配器模块 - 基于 Yuxi-Know 的架构设计
提供统一的图谱查询接口，支持多种图谱后端
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import json
import re
from collections import defaultdict


# =============================================================================
# 停用词和过滤规则 - 参考 Yuxi-Know 的知识图谱质量控制
# =============================================================================

# 中文停用词列表 - 会被过滤的词汇
CHINESE_STOPWORDS: Set[str] = {
    # 常见虚词
    "通过", "之后", "之前", "以及", "或者", "因此", "所以", "但是", "然而",
    "虽然", "尽管", "如果", "那么", "这样", "那样", "什么", "怎么", "为什么",
    "哪些", "哪个", "这个", "那个", "一些", "一个", "每个", "所有", "任何",
    "其他", "另外", "此外", "并且", "而且", "不仅", "不但", "只是", "只有",
    "可以", "可能", "应该", "需要", "必须", "能够", "不能", "不会", "不是",
    "已经", "正在", "将要", "曾经", "一直", "总是", "经常", "有时", "偶尔",
    "非常", "特别", "十分", "相当", "比较", "更加", "最为", "极为", "极其",
    "主要", "重要", "关键", "核心", "基本", "基础", "初步", "进一步", "最终",
    "首先", "其次", "然后", "最后", "同时", "当时", "目前", "现在", "以后",
    "包括", "例如", "比如", "即", "就是", "也就是", "也就", "即是", "则是",
    "这些", "那些", "他们", "我们", "你们", "它们", "自己", "本身", "对方",
    "上述", "下述", "上面", "下面", "前面", "后面", "里面", "外面", "中间",
    "方面", "情况", "问题", "时候", "地方", "过程", "结果", "原因", "目的",
    "作用", "影响", "效果", "意义", "价值", "特点", "特征", "性质", "属性",
    "方式", "方法", "手段", "途径", "渠道", "角度", "层面", "程度", "范围",
    "条件", "环境", "背景", "前提", "基于", "根据", "按照", "依据", "针对",
    "关于", "对于", "由于", "在于", "属于", "用于", "便于", "有利于", "不利于",
    "进行", "实现", "完成", "达到", "获得", "取得", "产生", "形成", "构成",
    "提供", "支持", "帮助", "促进", "推动", "加强", "改善", "提高", "增加",
    "减少", "降低", "避免", "防止", "解决", "处理", "应对", "满足", "符合",
    "具有", "拥有", "存在", "发生", "出现", "变化", "发展", "增长", "下降",
    "表示", "说明", "显示", "证明", "反映", "体现", "表明", "意味着", "代表",
    "认为", "觉得", "感觉", "发现", "了解", "知道", "明白", "理解", "确定",
    "一种", "两种", "多种", "各种", "某种", "这种", "那种", "同种", "异种",
    "第一", "第二", "第三", "第四", "第五", "更多", "更少", "更高", "更低",
    "大量", "少量", "部分", "全部", "整体", "局部", "多数", "少数", "个别",
    "一般", "普通", "特殊", "正常", "异常", "常见", "罕见", "典型", "非典型",
    "简单", "复杂", "容易", "困难", "直接", "间接", "明显", "不明显", "清楚",
    "确实", "的确", "实际", "事实", "真正", "真实", "具体", "详细", "简要",
    "相关", "相似", "相同", "不同", "类似", "一致", "差异", "区别", "联系",
    "以下", "以上", "之间", "之内", "之外", "以内", "以外", "左右", "上下",
}

# 无效中文实体开头字符 - 这些字符不应该出现在实体开头
INVALID_CHINESE_PREFIXES: Set[str] = {
    "的", "了", "在", "是", "有", "和", "与", "或", "及", "等",
    "对", "为", "从", "向", "被", "把", "将", "给", "让", "使",
    "户", "员", "者", "家", "人", "们",  # 通常是人称后缀
}

# 英文停用词列表
ENGLISH_STOPWORDS: Set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "can", "shall", "of", "to", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "under",
    "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "just", "but", "and", "or", "if", "because", "until",
    "while", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further",
    "this", "that", "these", "those", "am", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because",
    "as", "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after",
    "above", "below", "to", "from", "up", "down", "in", "out", "on", "off",
    "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "which", "who", "whom", "this", "that",
    "these", "those", "what", "which", "who", "whom", "whose", "where",
    "when", "why", "how", "i", "me", "my", "myself", "we", "our", "ours",
    "ourselves", "you", "your", "yours", "yourself", "yourselves", "he",
    "him", "his", "himself", "she", "her", "hers", "herself", "it", "its",
    "itself", "they", "them", "their", "theirs", "themselves", "also",
    "use", "used", "using", "uses", "based", "way", "ways", "make",
    "makes", "made", "get", "gets", "got", "see", "saw", "seen", "like",
    "likes", "need", "needs", "needed", "want", "wants", "wanted",
    "example", "examples", "etc", "ie", "eg", "via", "per", "thus",
}

# 不应该被识别为实体的低质量模式
INVALID_ENTITY_PATTERNS: List[str] = [
    r'^[\d\.\,\-\+\*\/\=\%\$\#\@\!\&\(\)\[\]\{\}]+$',  # 纯符号/数字
    r'^\d+$',  # 纯数字
    r'^[a-z]$',  # 单个小写字母
    r'^[\u4e00-\u9fa5]$',  # 单个汉字
    r'^http[s]?://',  # URL
    r'^\S+@\S+\.\S+$',  # 邮箱
    r'^[\u4e00-\u9fa5]{1}[\u7684\u5730\u5f97\u4e86\u8fc7\u7740\u5417\u5462\u5427\u554a]$',  # 常见语气词组合
]

# 实体质量评分规则
MIN_ENTITY_LENGTH = 2  # 最小实体长度
MAX_ENTITY_LENGTH = 50  # 最大实体长度
MIN_ENTITY_FREQUENCY = 1  # 最小出现频率（可调整）
MEANINGFUL_ENTITY_PATTERN = re.compile(
    r'^[\u4e00-\u9fa5a-zA-Z][\u4e00-\u9fa5a-zA-Z0-9\-\_\.\s]*[\u4e00-\u9fa5a-zA-Z0-9]$|^[\u4e00-\u9fa5a-zA-Z]{2}$'
)


def is_valid_entity(text: str, entity_type: str = None) -> bool:
    """
    检查实体是否有效
    
    Args:
        text: 实体文本
        entity_type: 实体类型
    
    Returns:
        bool: 是否为有效实体
    """
    if not text or not isinstance(text, str):
        return False
    
    text = text.strip()
    
    # 长度检查
    if len(text) < MIN_ENTITY_LENGTH or len(text) > MAX_ENTITY_LENGTH:
        return False
    
    # 停用词检查
    text_lower = text.lower()
    if text_lower in ENGLISH_STOPWORDS or text in CHINESE_STOPWORDS:
        return False
    
    # 检查中文实体的无效开头
    if text and '\u4e00' <= text[0] <= '\u9fa5':
        if text[0] in INVALID_CHINESE_PREFIXES:
            return False
        # 检查是否包含"的"在中间（可能是句子片段）
        if "的" in text[1:-1] and len(text) > 8:
            # 如果包含"的"且长度较长，可能是句子片段而非实体
            de_count = text.count("的")
            if de_count >= 2:  # 包含多个"的"，很可能不是实体
                return False
    
    # 无效模式检查
    for pattern in INVALID_ENTITY_PATTERNS:
        if re.match(pattern, text):
            return False
    
    # 有意义模式检查
    if not MEANINGFUL_ENTITY_PATTERN.match(text):
        return False
    
    # 纯空格/标点检查
    if not any(c.isalnum() or '\u4e00' <= c <= '\u9fa5' for c in text):
        return False
    
    return True


def calculate_entity_score(
    entity_text: str,
    entity_type: str,
    frequency: int = 1,
    context_quality: float = 1.0
) -> float:
    """
    计算实体质量分数
    
    Args:
        entity_text: 实体文本
        entity_type: 实体类型
        frequency: 出现频率
        context_quality: 上下文质量 (0-1)
    
    Returns:
        float: 质量分数 (0-1)
    """
    if not is_valid_entity(entity_text, entity_type):
        return 0.0
    
    score = 0.5  # 基础分
    
    # 长度加分 - 适中长度的实体更可能是高质量的
    length = len(entity_text)
    if 3 <= length <= 20:
        score += 0.2
    elif 2 <= length <= 30:
        score += 0.1
    
    # 类型加分 - 某些类型更可信
    high_quality_types = {'technology', 'organization', 'person', 'product'}
    if entity_type and entity_type.lower() in high_quality_types:
        score += 0.15
    
    # 频率加分
    if frequency >= 3:
        score += 0.15
    elif frequency >= 2:
        score += 0.1
    
    # 上下文质量
    score *= context_quality
    
    return min(1.0, score)


@dataclass
class GraphQueryConfig:
    """图谱查询配置"""
    keyword: str = ""
    max_nodes: int = 100
    max_depth: int = 2
    filters: Dict = field(default_factory=dict)


@dataclass
class GraphMetadata:
    """图谱元数据"""
    graph_type: str
    id_field: str = "id"
    name_field: str = "name"
    supports_search: bool = True


class GraphAdapter(ABC):
    """图谱适配器基类 - 定义统一的图谱操作接口"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.metadata = self._get_metadata()
    
    @abstractmethod
    def _get_metadata(self) -> GraphMetadata:
        """获取图谱元数据"""
        pass
    
    @abstractmethod
    async def query_nodes(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """
        查询节点
        
        Args:
            keyword: 搜索关键词，"*" 表示返回所有节点
            **kwargs: 其他查询参数 (max_nodes, max_depth 等)
        
        Returns:
            {"nodes": [...], "edges": [...]}
        """
        pass
    
    @abstractmethod
    async def get_stats(self, **kwargs) -> Dict[str, Any]:
        """获取图谱统计信息"""
        pass
    
    @abstractmethod
    async def get_labels(self) -> List[str]:
        """获取所有实体类型/标签"""
        pass
    
    def _create_standard_node(
        self,
        node_id: str,
        name: str,
        entity_type: str,
        properties: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """创建标准化节点格式"""
        return {
            "id": node_id,
            "name": name,
            "type": entity_type,
            "properties": properties or {},
            "data": {
                "label": name,
                "original": {
                    "id": node_id,
                    "name": name,
                    "type": entity_type,
                    "properties": properties or {},
                    "labels": [entity_type],
                }
            }
        }
    
    def _create_standard_edge(
        self,
        edge_id: str,
        source_id: str,
        target_id: str,
        edge_type: str,
        properties: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """创建标准化边格式"""
        return {
            "id": edge_id,
            "source_id": source_id,
            "target_id": target_id,
            "type": edge_type,
            "properties": properties or {},
            "data": {
                "label": edge_type,
                "original": {
                    "type": edge_type,
                    "properties": properties or {},
                }
            }
        }


class LocalKnowledgeGraphAdapter(GraphAdapter):
    """
    本地知识图谱适配器
    从 workspace 的 notes 目录提取实体和关系构建图谱
    """
    
    def __init__(self, workspace_path: Path, config: Dict[str, Any] = None):
        self.workspace = Path(workspace_path)
        self.kg_dir = self.workspace / "knowledge_graph"
        self.kg_dir.mkdir(parents=True, exist_ok=True)
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, Any]] = []
        self._graph_built = False
        super().__init__(config)
    
    def _get_metadata(self) -> GraphMetadata:
        return GraphMetadata(
            graph_type="local",
            id_field="id",
            name_field="name",
            supports_search=True,
        )
    
    def _extract_entities(self, text: str, filename: str) -> List[Dict[str, str]]:
        """
        从文本中提取实体
        
        使用改进的实体提取逻辑:
        1. 更精确的正则表达式模式
        2. 停用词过滤
        3. 实体质量评分
        4. 优先匹配特定类型（技术、组织等）再匹配通用类型（人名）
        """
        entities = []
        
        # 技术相关术语的关键词（用于辅助分类）
        TECH_KEYWORDS = {
            'store', 'database', 'cache', 'vector', 'embedding', 'retrieval',
            'query', 'search', 'index', 'api', 'sdk', 'framework', 'library',
            'engine', 'server', 'client', 'service', 'tool', 'plugin', 'extension',
            'generation', 'augmented', 'learning', 'machine', 'deep', 'neural',
            'model', 'algorithm', 'processing', 'analysis', 'pipeline', 'workflow',
            'window', 'sliding', 'chunk', 'split', 'parse', 'extract', 'transform',
            'load', 'deploy', 'build', 'test', 'debug', 'monitor', 'log', 'trace',
            'hybrid', 'multi', 'cross', 'semantic', 'lexical', 'sparse', 'dense',
            'rag', 'llm', 'nlp', 'ai', 'ml', 'dl', 'cv', 'gpt', 'bert', 'transformer',
            'compose', 'container', 'kubernetes', 'docker', 'cloud', 'aws', 'azure',
        }
        
        # 改进的实体提取模式 - 按优先级排序
        # 先匹配具有明确特征的实体类型，避免被 person 模式错误捕获
        patterns = [
            # 1. 技术 - 最高优先级
            ('technology', [
                # 知名技术栈和工具 - 精确匹配
                r'\b(Python|JavaScript|TypeScript|React|Vue\.?js|Angular|FastAPI|Django|Flask|Express|Node\.js|Deno|Rust|Go|Java|C\+\+|Swift|Kotlin)\b',
                r'\b(Docker|Kubernetes|K8s|AWS|Azure|GCP|Terraform|Ansible|Jenkins|GitLab|GitHub|Nginx|Apache)\b',
                r'\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|Kafka|RabbitMQ|Celery|Milvus|Weaviate|Pinecone)\b',
                r'\b(RAG|LLM|GPT|ChatGPT|Claude|BERT|Transformer|NLP|CNN|RNN|LSTM|Attention|OpenAI|Anthropic)\b',
                r'\b(TensorFlow|PyTorch|Keras|Scikit-learn|Pandas|NumPy|Hugging\s*Face|LangChain|LlamaIndex)\b',
                r'\b(REST|RESTful|GraphQL|gRPC|WebSocket|HTTP|HTTPS|TCP|UDP|OAuth|JWT|API|SDK)\b',
                r'\b(Element\s*Plus|Ant\s*Design|Material\s*UI|Tailwind|Bootstrap|Chakra)\b',
                # 技术概念（两个或多个单词的技术术语）
                r'\b(Vector\s+Store|Vector\s+Database|Embedding\s+Model|Language\s+Model)\b',
                r'\b(Query\s+Expansion|Hybrid\s+Retrieval|Semantic\s+Search|Lexical\s+Search)\b',
                r'\b(Sliding\s+Window|Chunking\s+Strategy|Document\s+Parsing|Text\s+Extraction)\b',
                r'\b(Augmented\s+Generation|Retrieval\s+Augmented|Knowledge\s+Graph)\b',
                r'\b(Docker\s+Compose|Docker\s+Swarm|Container\s+Orchestration)\b',
                # 中文技术术语 - 更严格，必须以技术关键词开头
                r'(?<![的在从向到把将被对])((?:向量|知识|索引|检索|语义|文档|数据|分布式|微服务|消息|内存|文件|对象)[a-zA-Z\u4e00-\u9fa5]{0,4}(?:库|引擎|模型|算法|协议|接口|缓存|存储|系统|服务))',
            ]),
            # 2. 产品
            ('product', [
                r'\b(iPhone|iPad|MacBook|Windows|Linux|Ubuntu|Android|iOS|macOS)\b',
                r'\b(Chrome|Firefox|Safari|Edge|Opera)\b',
                r'\b(Office|Word|Excel|PowerPoint|Outlook|Teams|Slack|Notion|Figma|Sketch)\b',
                r'\b(VS\s*Code|Visual\s*Studio|IntelliJ|PyCharm|Eclipse|Xcode|Sublime\s*Text|Cursor)\b',
            ]),
            # 3. 组织
            ('organization', [
                r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:Inc|Corp|Ltd|Company|Co|LLC|Foundation|Institute|University|College)\.?)\b',
                r'\b(Google|Microsoft|Amazon|Meta|Apple|OpenAI|Anthropic|Hugging\s*Face|NVIDIA)\b',
                r'([\u4e00-\u9fa5]{2,}(?:公司|企业|集团|银行|医院|学校|大学|学院|研究院|研究所|实验室|中心|协会|基金会))',
            ]),
            # 4. 概念 - 只匹配纯名词短语，避免动词开头
            ('concept', [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:System|Method|Algorithm|Architecture|Pattern|Model|Theory|Principle|Protocol|Standard))\b',
                # 中文概念：必须以名词性词语开头，避免动词和句子片段
                r'(?<![把将被对从向在是有和与或及等到])((?:数据|知识|信息|系统|网络|云|智能|深度|机器|自然语言|图像|语音|文本|用户|客户|产品|服务|业务|市场|金融|投资|风险|安全|性能|质量|效率|成本)[a-zA-Z\u4e00-\u9fa5]{1,8}(?:技术|方案|架构|模式|方法|策略|理论|原理|规范|体系|系统|平台|引擎|工具))',
            ]),
            # 5. 地点 - 更严格的匹配，避免句子片段
            ('location', [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:City|State|County|Province|Region|Country|Island|Mountain|River|Lake|Ocean|Sea|Bay|Valley))\b',
                # 中文地名：必须以地名专有名词开头
                r'(?<![的在从向到])((?:北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|重庆|天津|苏州|东莞|青岛|长沙|郑州|宁波|佛山|无锡|合肥|沈阳|济南|厦门|福州|昆明|哈尔滨|长春|大连|南宁|贵阳|太原|石家庄|南昌|海口|兰州|银川|西宁|拉萨|呼和浩特|乌鲁木齐)(?:市)?)',
            ]),
            # 6. 文档 - 不匹配对话中的文档引用
            ('document', [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Paper|Article|Book|Report|Guide|Manual|Documentation|Specification))\b',
                # 中文文档：只匹配具体的文档名称，不匹配对话语句
                r'《([\u4e00-\u9fa5a-zA-Z0-9]{2,20})》',  # 书名号包裹的文档名
            ]),
            # 7. 人名 - 最后匹配，避免捕获技术术语
            ('person', [
                # 中文姓名：2-4个字，必须带职称后缀
                r'(?<![a-zA-Z])([\u4e00-\u9fa5]{2,4})(?:先生|女士|老师|教授|博士|院士|工程师|主任|经理|总裁|董事)(?![a-zA-Z\u4e00-\u9fa5])',
            ]),
        ]
        
        seen_entities = set()  # 去重
        matched_spans = []  # 已匹配的文本范围，避免重复匹配
        
        for entity_type, type_patterns in patterns:
            for pattern in type_patterns:
                try:
                    # 技术类型使用不区分大小写匹配
                    flags = re.IGNORECASE if entity_type in ('technology', 'product') else 0
                    matches = re.finditer(pattern, text, flags)
                    
                    for match in matches:
                        # 检查是否与已匹配的范围重叠
                        start, end = match.start(), match.end()
                        is_overlapping = any(
                            (s <= start < e) or (s < end <= e) or (start <= s and end >= e)
                            for s, e in matched_spans
                        )
                        if is_overlapping:
                            continue
                        
                        # 获取匹配的组，处理多组情况
                        entity_text = None
                        for group in match.groups():
                            if group:
                                entity_text = group.strip()
                                break
                        
                        if not entity_text:
                            continue
                        
                        # 使用新的验证函数
                        if not is_valid_entity(entity_text, entity_type):
                            continue
                        
                        # 对于通用匹配，检查是否应该重新分类为技术类型
                        actual_type = entity_type
                        if entity_type == 'person':
                            # 检查是否包含技术关键词
                            words_lower = entity_text.lower().split()
                            if any(word in TECH_KEYWORDS for word in words_lower):
                                actual_type = 'technology'
                        
                        # 计算质量分数
                        score = calculate_entity_score(entity_text, actual_type)
                        if score < 0.3:  # 低于阈值的实体不采用
                            continue
                        
                        # 去重检查 (大小写不敏感)
                        entity_key = entity_text.lower()
                        if entity_key in seen_entities:
                            continue
                        seen_entities.add(entity_key)
                        
                        # 记录匹配范围
                        matched_spans.append((start, end))
                        
                        entities.append({
                            'text': entity_text,
                            'type': actual_type,
                            'start': start,
                            'end': end,
                            'source_file': filename,
                            'quality_score': score,
                        })
                except re.error as e:
                    print(f"Regex error for pattern {pattern}: {e}")
                    continue
        
        return entities
    
    def _detect_relationships(self, entities: List[Dict], text: str) -> List[Dict[str, Any]]:
        """检测实体之间的关系"""
        relationships = []
        
        relation_keywords = {
            'uses': ['使用', 'uses', 'utilizes', 'employs', '采用', '应用'],
            'implements': ['实现', 'implements', 'builds', 'creates', '开发', '构建'],
            'related_to': ['相关', 'related', 'associated', 'connected', '关联', '涉及'],
            'part_of': ['属于', 'part of', 'member of', '包含', '组成'],
            'depends_on': ['依赖', 'depends on', 'requires', 'needs', '需要', '基于'],
            'extends': ['扩展', 'extends', 'inherits', '继承', '派生'],
            'integrates': ['集成', 'integrates', 'combines', '整合', '融合'],
        }
        
        for i, e1 in enumerate(entities):
            for j, e2 in enumerate(entities[i+1:], start=i+1):
                distance = abs(e1['start'] - e2['start'])
                if distance < 150:  # 实体距离阈值
                    start = min(e1['start'], e2['start'])
                    end = max(e1['end'], e2['end'])
                    context = text[max(0, start-30):min(len(text), end+30)]
                    
                    relation_type = None
                    for rel_type, keywords in relation_keywords.items():
                        if any(kw in context.lower() for kw in keywords):
                            relation_type = rel_type
                            break
                    
                    if not relation_type:
                        relation_type = 'related_to'
                    
                    relationships.append({
                        'source': e1['text'],
                        'target': e2['text'],
                        'type': relation_type,
                        'source_type': e1['type'],
                        'target_type': e2['type'],
                    })
        
        return relationships
    
    async def build_graph(self) -> Dict[str, Any]:
        """
        从 notes 目录构建知识图谱
        
        使用改进的实体提取和过滤逻辑:
        1. 质量评分过滤
        2. 频率过滤
        3. 上下文相关性过滤
        """
        notes_dir = self.workspace / "notes"
        if not notes_dir.exists():
            return {'entities': {}, 'relationships': []}
        
        all_entities = []
        all_relationships = []
        entity_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        entity_scores: Dict[str, float] = {}  # 实体质量分数
        
        for note_file in notes_dir.glob("**/*"):
            if note_file.is_file() and note_file.suffix in ['.md', '.txt', '.pdf']:
                try:
                    if note_file.suffix == '.pdf':
                        # PDF 需要特殊处理，这里跳过
                        continue
                    
                    text = note_file.read_text(encoding="utf-8", errors="ignore")
                    filename = note_file.name
                    
                    entities = self._extract_entities(text, filename)
                    all_entities.extend(entities)
                    
                    relationships = self._detect_relationships(entities, text)
                    all_relationships.extend(relationships)
                    
                    for entity in entities:
                        entity_text = entity['text']
                        entity_counts[entity_text][entity['type']] += 1
                        # 记录最高质量分数
                        current_score = entity.get('quality_score', 0.5)
                        if entity_text not in entity_scores or current_score > entity_scores[entity_text]:
                            entity_scores[entity_text] = current_score
                            
                except Exception as e:
                    print(f"Error processing {note_file}: {e}")
                    continue
        
        # 合并和过滤实体 - 使用大小写不敏感的键进行去重
        consolidated_entities = {}
        entity_key_map = {}  # 小写键 -> 原始文本的映射
        
        for entity in all_entities:
            text = entity['text']
            text_key = text.lower().strip()  # 用于去重的键
            
            # 跳过已处理的实体（大小写不敏感）
            if text_key in entity_key_map:
                original_text = entity_key_map[text_key]
                consolidated_entities[original_text]['count'] += 1
                consolidated_entities[original_text]['files'].add(entity['source_file'])
                continue
            
            # 计算综合频率
            total_freq = sum(entity_counts[text].values())
            
            # 最终质量评估
            base_score = entity_scores.get(text, 0.5)
            # 频率加成
            if total_freq >= 3:
                base_score = min(1.0, base_score + 0.2)
            elif total_freq >= 2:
                base_score = min(1.0, base_score + 0.1)
            
            # 过滤低质量实体
            # 只保留质量分数 >= 0.4 或频率 >= 2 的实体
            if base_score < 0.4 and total_freq < 2:
                continue
            
            entity_key_map[text_key] = text
            consolidated_entities[text] = {
                'id': text,
                'label': text,
                'type': entity['type'],
                'count': total_freq,
                'files': set([entity['source_file']]),
                'quality_score': base_score,
            }
        
        # 转换 files 集合为列表
        for entity in consolidated_entities.values():
            entity['files'] = list(entity['files'])
        
        # 去重关系并只保留有效实体间的关系
        seen_rels = set()
        unique_relationships = []
        valid_entity_names = set(consolidated_entities.keys())
        
        for rel in all_relationships:
            # 只保留两端都是有效实体的关系
            if rel['source'] not in valid_entity_names or rel['target'] not in valid_entity_names:
                continue
            
            key = (rel['source'], rel['target'], rel['type'])
            reverse_key = (rel['target'], rel['source'], rel['type'])
            
            # 避免重复关系（包括反向）
            if key not in seen_rels and reverse_key not in seen_rels:
                seen_rels.add(key)
                unique_relationships.append(rel)
        
        self.entities = consolidated_entities
        self.relationships = unique_relationships
        self._graph_built = True
        
        # 保存图谱
        self._save_graph()
        
        print(f"[KnowledgeGraph] Built graph with {len(consolidated_entities)} entities and {len(unique_relationships)} relationships")
        
        return {
            'entities': consolidated_entities,
            'relationships': unique_relationships,
        }
    
    def _save_graph(self):
        """保存图谱到文件"""
        kg_data = {
            'entities': self.entities,
            'relationships': self.relationships,
        }
        kg_file = self.kg_dir / "graph.json"
        with open(kg_file, 'w', encoding='utf-8') as f:
            json.dump(kg_data, f, ensure_ascii=False, indent=2)
    
    def _load_graph(self) -> bool:
        """从文件加载图谱"""
        kg_file = self.kg_dir / "graph.json"
        if kg_file.exists():
            try:
                with open(kg_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entities = data.get('entities', {})
                    self.relationships = data.get('relationships', [])
                    self._graph_built = True
                    return True
            except Exception as e:
                print(f"Error loading graph: {e}")
        return False
    
    async def _ensure_graph(self):
        """确保图谱已构建"""
        if not self._graph_built:
            if not self._load_graph():
                await self.build_graph()
    
    async def query_nodes(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """查询节点"""
        await self._ensure_graph()
        
        max_nodes = kwargs.get('max_nodes', 100)
        
        nodes = []
        edges = []
        node_ids = set()
        seen_names = set()  # 用于去重节点名称
        
        # 筛选节点
        for entity_id, entity_data in self.entities.items():
            if keyword == "*" or keyword.lower() in entity_id.lower():
                if len(nodes) < max_nodes:
                    # 额外的去重检查 - 使用小写名称
                    name = entity_data['label']
                    name_key = name.lower().strip()
                    if name_key in seen_names:
                        continue
                    seen_names.add(name_key)
                    
                    node = self._create_standard_node(
                        node_id=entity_id,
                        name=name,
                        entity_type=entity_data['type'],
                        properties={
                            'count': entity_data.get('count', 1),
                            'files': entity_data.get('files', []),
                        }
                    )
                    nodes.append(node)
                    node_ids.add(entity_id)
        
        # 筛选边 (只保留两端节点都存在的边)
        edge_idx = 0
        for rel in self.relationships:
            if rel['source'] in node_ids and rel['target'] in node_ids:
                edge = self._create_standard_edge(
                    edge_id=f"edge_{edge_idx}",
                    source_id=rel['source'],
                    target_id=rel['target'],
                    edge_type=rel['type'],
                )
                edges.append(edge)
                edge_idx += 1
        
        return {'nodes': nodes, 'edges': edges}
    
    async def get_stats(self, **kwargs) -> Dict[str, Any]:
        """获取图谱统计信息"""
        await self._ensure_graph()
        
        type_counts = defaultdict(int)
        for entity in self.entities.values():
            type_counts[entity['type']] += 1
        
        entity_types = [
            {'type': t, 'count': c}
            for t, c in sorted(type_counts.items(), key=lambda x: -x[1])
        ]
        
        return {
            'total_nodes': len(self.entities),
            'total_edges': len(self.relationships),
            'entity_types': entity_types,
        }
    
    async def get_labels(self) -> List[str]:
        """获取所有实体类型"""
        await self._ensure_graph()
        
        labels = set()
        for entity in self.entities.values():
            labels.add(entity['type'])
        
        return sorted(list(labels))


class GraphAdapterFactory:
    """图谱适配器工厂"""
    
    _adapters: Dict[str, type] = {
        'local': LocalKnowledgeGraphAdapter,
    }
    
    @classmethod
    def register(cls, graph_type: str, adapter_class: type):
        """注册新的适配器类型"""
        cls._adapters[graph_type] = adapter_class
    
    @classmethod
    def create(cls, graph_type: str, workspace_path: Path, **kwargs) -> GraphAdapter:
        """创建适配器实例"""
        if graph_type not in cls._adapters:
            raise ValueError(f"Unknown graph type: {graph_type}. Available: {list(cls._adapters.keys())}")
        
        adapter_class = cls._adapters[graph_type]
        return adapter_class(workspace_path, kwargs)
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """获取所有可用的图谱类型"""
        return list(cls._adapters.keys())


# 延迟注册 Neo4j 和 LightRAG 适配器（避免循环导入）
def register_all_adapters():
    """注册所有可用的图谱适配器"""
    try:
        from .neo4j_adapter import Neo4jGraphAdapter
        GraphAdapterFactory.register("neo4j", Neo4jGraphAdapter)
    except ImportError:
        pass  # neo4j 包未安装
    
    try:
        from .lightrag_integration import LightRAGGraphAdapter
        GraphAdapterFactory.register("lightrag", LightRAGGraphAdapter)
    except ImportError:
        pass  # lightrag 依赖未安装

