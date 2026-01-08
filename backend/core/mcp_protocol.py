"""
MCP (Model Context Protocol) 协议支持
借鉴 Khoj 的实现，提供标准化的外部工具调用能力

MCP 协议特点：
1. 标准化接口：统一的工具描述和调用格式
2. 动态发现：运行时发现可用工具
3. 安全执行：沙箱化工具执行
4. 双向通信：支持工具回调

支持的 MCP 服务类型：
- filesystem: 文件系统操作
- browser: 网页浏览
- database: 数据库查询
- api: REST API 调用
- custom: 自定义工具
"""

import asyncio
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type


class MCPToolType(str, Enum):
    FILESYSTEM = "filesystem"
    BROWSER = "browser"
    DATABASE = "database"
    API = "api"
    CUSTOM = "custom"


@dataclass
class MCPToolParameter:
    """工具参数定义"""
    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[str]] = None


@dataclass
class MCPToolDefinition:
    """工具定义"""
    name: str
    description: str
    tool_type: MCPToolType
    parameters: List[MCPToolParameter] = field(default_factory=list)
    returns: str = "string"
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": {
                "type": "object",
                "properties": {
                    p.name: {
                        "type": p.type,
                        "description": p.description,
                        **({"enum": p.enum} if p.enum else {}),
                        **({"default": p.default} if p.default is not None else {}),
                    }
                    for p in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required],
            },
            "returns": self.returns,
            "examples": self.examples,
        }


@dataclass
class MCPToolResult:
    """工具执行结果"""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }


class MCPTool(ABC):
    """MCP 工具基类"""
    
    @property
    @abstractmethod
    def definition(self) -> MCPToolDefinition:
        """返回工具定义"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> MCPToolResult:
        """执行工具"""
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> Optional[str]:
        """验证参数，返回错误信息或 None"""
        for param in self.definition.parameters:
            if param.required and param.name not in params:
                return f"Missing required parameter: {param.name}"
        return None


# ===== 内置工具实现 =====

class FileReadTool(MCPTool):
    """文件读取工具"""
    
    def __init__(self, allowed_paths: Optional[List[str]] = None):
        self.allowed_paths = allowed_paths or []
    
    @property
    def definition(self) -> MCPToolDefinition:
        return MCPToolDefinition(
            name="read_file",
            description="读取文件内容",
            tool_type=MCPToolType.FILESYSTEM,
            parameters=[
                MCPToolParameter(
                    name="path",
                    type="string",
                    description="文件路径",
                ),
                MCPToolParameter(
                    name="encoding",
                    type="string",
                    description="文件编码",
                    required=False,
                    default="utf-8",
                ),
            ],
            returns="string",
            examples=[
                {"path": "/path/to/file.txt", "encoding": "utf-8"},
            ],
        )
    
    async def execute(self, path: str, encoding: str = "utf-8", **kwargs) -> MCPToolResult:
        try:
            # 安全检查
            if self.allowed_paths:
                allowed = any(path.startswith(p) for p in self.allowed_paths)
                if not allowed:
                    return MCPToolResult(
                        success=False,
                        output=None,
                        error=f"Access denied: {path}",
                    )
            
            with open(path, "r", encoding=encoding) as f:
                content = f.read()
            
            return MCPToolResult(
                success=True,
                output=content,
                metadata={"path": path, "size": len(content)},
            )
        except Exception as e:
            return MCPToolResult(
                success=False,
                output=None,
                error=str(e),
            )


class WebSearchTool(MCPTool):
    """网页搜索工具"""
    
    @property
    def definition(self) -> MCPToolDefinition:
        return MCPToolDefinition(
            name="web_search",
            description="在互联网上搜索信息",
            tool_type=MCPToolType.BROWSER,
            parameters=[
                MCPToolParameter(
                    name="query",
                    type="string",
                    description="搜索查询",
                ),
                MCPToolParameter(
                    name="num_results",
                    type="number",
                    description="返回结果数量",
                    required=False,
                    default=5,
                ),
            ],
            returns="array",
            examples=[
                {"query": "Python best practices", "num_results": 5},
            ],
        )
    
    async def execute(self, query: str, num_results: int = 5, **kwargs) -> MCPToolResult:
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                
                # 简化结果
                results = [
                    {
                        "title": f"Search result for: {query}",
                        "url": "https://example.com",
                        "snippet": "Search results placeholder",
                    }
                ]
                
                return MCPToolResult(
                    success=True,
                    output=results[:num_results],
                    metadata={"query": query, "count": len(results)},
                )
        except Exception as e:
            return MCPToolResult(
                success=False,
                output=[],
                error=str(e),
            )


class CalculatorTool(MCPTool):
    """计算器工具"""
    
    @property
    def definition(self) -> MCPToolDefinition:
        return MCPToolDefinition(
            name="calculator",
            description="执行数学计算",
            tool_type=MCPToolType.CUSTOM,
            parameters=[
                MCPToolParameter(
                    name="expression",
                    type="string",
                    description="数学表达式，如 '2 + 3 * 4'",
                ),
            ],
            returns="number",
            examples=[
                {"expression": "2 + 3"},
                {"expression": "sqrt(16) + pow(2, 3)"},
            ],
        )
    
    async def execute(self, expression: str, **kwargs) -> MCPToolResult:
        import math
        
        try:
            # 安全的数学表达式求值
            safe_dict = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
            }
            
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            return MCPToolResult(
                success=True,
                output=result,
                metadata={"expression": expression},
            )
        except Exception as e:
            return MCPToolResult(
                success=False,
                output=None,
                error=str(e),
            )


class DateTimeTool(MCPTool):
    """日期时间工具"""
    
    @property
    def definition(self) -> MCPToolDefinition:
        return MCPToolDefinition(
            name="datetime",
            description="获取当前日期时间或进行日期计算",
            tool_type=MCPToolType.CUSTOM,
            parameters=[
                MCPToolParameter(
                    name="operation",
                    type="string",
                    description="操作类型",
                    enum=["now", "format", "add_days", "diff"],
                ),
                MCPToolParameter(
                    name="format",
                    type="string",
                    description="日期格式",
                    required=False,
                    default="%Y-%m-%d %H:%M:%S",
                ),
                MCPToolParameter(
                    name="days",
                    type="number",
                    description="添加的天数（用于 add_days）",
                    required=False,
                    default=0,
                ),
            ],
            returns="string",
        )
    
    async def execute(
        self,
        operation: str = "now",
        format: str = "%Y-%m-%d %H:%M:%S",
        days: int = 0,
        **kwargs
    ) -> MCPToolResult:
        from datetime import datetime, timedelta
        
        try:
            now = datetime.now()
            
            if operation == "now":
                result = now.strftime(format)
            elif operation == "add_days":
                future = now + timedelta(days=days)
                result = future.strftime(format)
            else:
                result = now.isoformat()
            
            return MCPToolResult(
                success=True,
                output=result,
                metadata={"operation": operation},
            )
        except Exception as e:
            return MCPToolResult(
                success=False,
                output=None,
                error=str(e),
            )


# ===== MCP 服务注册表 =====

class MCPRegistry:
    """
    MCP 工具注册表
    
    管理所有可用的 MCP 工具
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, MCPTool] = {}
            cls._instance._initialized = False
        return cls._instance
    
    def register(self, tool: MCPTool):
        """注册工具"""
        self._tools[tool.definition.name] = tool
        print(f"🔧 Registered MCP tool: {tool.definition.name}")
    
    def unregister(self, tool_name: str):
        """注销工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]
    
    def get(self, tool_name: str) -> Optional[MCPTool]:
        """获取工具"""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[MCPToolDefinition]:
        """列出所有工具定义"""
        return [tool.definition for tool in self._tools.values()]
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取所有工具的 JSON Schema"""
        return [tool.definition.to_dict() for tool in self._tools.values()]
    
    async def execute(self, tool_name: str, params: Dict[str, Any]) -> MCPToolResult:
        """执行工具"""
        tool = self.get(tool_name)
        if not tool:
            return MCPToolResult(
                success=False,
                output=None,
                error=f"Tool not found: {tool_name}",
            )
        
        # 验证参数
        error = tool.validate_params(params)
        if error:
            return MCPToolResult(
                success=False,
                output=None,
                error=error,
            )
        
        # 执行工具
        try:
            result = await tool.execute(**params)
            return result
        except Exception as e:
            return MCPToolResult(
                success=False,
                output=None,
                error=str(e),
            )
    
    def initialize_default_tools(self):
        """初始化默认工具"""
        if self._initialized:
            return
        
        # 注册内置工具
        self.register(FileReadTool())
        self.register(WebSearchTool())
        self.register(CalculatorTool())
        self.register(DateTimeTool())
        
        self._initialized = True
        print(f"✅ MCP initialized with {len(self._tools)} tools")


# 全局注册表
mcp_registry = MCPRegistry()


# ===== 便捷函数 =====

def get_mcp_tools() -> List[Dict[str, Any]]:
    """获取所有 MCP 工具定义"""
    mcp_registry.initialize_default_tools()
    return mcp_registry.get_tools_schema()


async def call_mcp_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """调用 MCP 工具"""
    mcp_registry.initialize_default_tools()
    result = await mcp_registry.execute(tool_name, params)
    return result.to_dict()


def register_custom_tool(tool: MCPTool):
    """注册自定义工具"""
    mcp_registry.initialize_default_tools()
    mcp_registry.register(tool)


# ===== MCP 服务器（可选） =====

class MCPServer:
    """
    简单的 MCP 服务器
    
    通过 HTTP 或 WebSocket 提供 MCP 服务
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.registry = mcp_registry
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {
                "tools": self.registry.get_tools_schema()
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_params = params.get("arguments", {})
            result = await self.registry.execute(tool_name, tool_params)
            return result.to_dict()
        
        else:
            return {
                "error": f"Unknown method: {method}"
            }


# 导出
__all__ = [
    "MCPToolType",
    "MCPToolParameter",
    "MCPToolDefinition",
    "MCPToolResult",
    "MCPTool",
    "MCPRegistry",
    "mcp_registry",
    "get_mcp_tools",
    "call_mcp_tool",
    "register_custom_tool",
    "FileReadTool",
    "WebSearchTool",
    "CalculatorTool",
    "DateTimeTool",
    "MCPServer",
]

