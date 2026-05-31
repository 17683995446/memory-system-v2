"""
记忆系统API设计和集成模块
基于第一性原理：标准化、可扩展性、安全性
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class HTTPMethod(Enum):
    """HTTP方法"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class APIEndpointType(Enum):
    """API端点类型"""
    MEMORY = "memory"
    SEARCH = "search"
    USER = "user"
    SYSTEM = "system"
    STATISTICS = "statistics"


@dataclass
class APIEndpoint:
    """API端点定义"""
    path: str
    method: HTTPMethod
    endpoint_type: APIEndpointType
    handler: Callable
    description: str = ""
    requires_auth: bool = True
    rate_limit: int = 100
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIRequest:
    """API请求"""
    method: HTTPMethod
    path: str
    params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


@dataclass
class APIResponse:
    """API响应"""
    status_code: int
    data: Any
    message: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    rate_limit_remaining: int = 100
    timestamp: float = field(default_factory=time.time)


@dataclass
class GraphQLQuery:
    """GraphQL查询"""
    query: str
    variables: Dict[str, Any] = field(default_factory=dict)
    operation_name: Optional[str] = None


@dataclass
class GraphQLResponse:
    """GraphQL响应"""
    data: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WebSocketMessage:
    """WebSocket消息"""
    type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    user_id: Optional[str] = None


class RateLimiter:
    """速率限制器"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.limits: Dict[str, int] = defaultdict(lambda: 100)
    
    def check_limit(self, user_id: str, limit: int = 100) -> bool:
        """检查速率限制"""
        now = time.time()
        cutoff = now - 60  # 一分钟内
        
        # 清理旧请求
        self.requests[user_id] = [
            ts for ts in self.requests[user_id] if ts > cutoff
        ]
        
        if len(self.requests[user_id]) >= limit:
            return False
        
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: str, limit: int = 100) -> int:
        """获取剩余请求数"""
        now = time.time()
        cutoff = now - 60
        
        requests = [
            ts for ts in self.requests.get(user_id, [])
            if ts > cutoff
        ]
        
        return max(0, limit - len(requests))


class RequestValidator:
    """请求验证器"""
    
    def __init__(self):
        self.schemas: Dict[str, Dict[str, Any]] = {}
    
    def add_schema(self, name: str, schema: Dict[str, Any]):
        """添加验证模式"""
        self.schemas[name] = schema
    
    def validate(self, data: Dict[str, Any], schema_name: str) -> Tuple[bool, Optional[str]]:
        """验证数据"""
        if schema_name not in self.schemas:
            return True, None
        
        schema = self.schemas[schema_name]
        
        # 简单验证：检查必需字段
        required = schema.get("required", [])
        for field_name in required:
            if field_name not in data:
                return False, f"Missing required field: {field_name}"
        
        # 验证类型
        properties = schema.get("properties", {})
        for field_name, value in data.items():
            if field_name in properties:
                expected_type = properties[field_name].get("type")
                if expected_type and not self._check_type(value, expected_type):
                    return False, f"Invalid type for {field_name}"
        
        return True, None
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查类型"""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected = type_map.get(expected_type)
        if expected is None:
            return True
        
        return isinstance(value, expected)


class RESTAPIRouter:
    """REST API路由器"""
    
    def __init__(self):
        self.endpoints: Dict[str, Dict[HTTPMethod, APIEndpoint]] = defaultdict(dict)
        self.rate_limiter = RateLimiter()
        self.validator = RequestValidator()
        self.middleware: List[Callable] = []
    
    def register_endpoint(
        self,
        path: str,
        method: HTTPMethod,
        handler: Callable,
        endpoint_type: APIEndpointType,
        description: str = "",
        requires_auth: bool = True,
        rate_limit: int = 100
    ):
        """注册API端点"""
        endpoint = APIEndpoint(
            path=path,
            method=method,
            endpoint_type=endpoint_type,
            handler=handler,
            description=description,
            requires_auth=requires_auth,
            rate_limit=rate_limit
        )
        
        self.endpoints[path][method] = endpoint
    
    def add_middleware(self, middleware: Callable):
        """添加中间件"""
        self.middleware.append(middleware)
    
    def route(self, request: APIRequest) -> APIResponse:
        """路由请求"""
        # 执行中间件
        for mw in self.middleware:
            result = mw(request)
            if isinstance(result, APIResponse):
                return result
        
        # 查找端点
        path = request.path
        method = request.method
        
        if path not in self.endpoints or method not in self.endpoints[path]:
            return APIResponse(
                status_code=404,
                data=None,
                message="Endpoint not found"
            )
        
        endpoint = self.endpoints[path][method]
        
        # 速率限制检查
        if request.user_id:
            if not self.rate_limiter.check_limit(request.user_id, endpoint.rate_limit):
                return APIResponse(
                    status_code=429,
                    data=None,
                    message="Rate limit exceeded",
                    rate_limit_remaining=0
                )
        
        # 认证检查
        if endpoint.requires_auth and not request.user_id:
            return APIResponse(
                status_code=401,
                data=None,
                message="Authentication required"
            )
        
        # 执行处理器
        try:
            result = endpoint.handler(request)
            return APIResponse(
                status_code=200,
                data=result,
                rate_limit_remaining=self.rate_limiter.get_remaining(
                    request.user_id or "anonymous",
                    endpoint.rate_limit
                )
            )
        except Exception as e:
            return APIResponse(
                status_code=500,
                data=None,
                message=str(e)
            )
    
    def get_routes(self) -> List[Dict[str, Any]]:
        """获取所有路由"""
        routes = []
        for path, methods in self.endpoints.items():
            for method, endpoint in methods.items():
                routes.append({
                    "path": path,
                    "method": method.value,
                    "type": endpoint.endpoint_type.value,
                    "description": endpoint.description,
                    "requires_auth": endpoint.requires_auth,
                    "rate_limit": endpoint.rate_limit
                })
        return routes


class GraphQLSchema:
    """GraphQL模式定义"""
    
    def __init__(self):
        self.types: Dict[str, Dict[str, Any]] = {}
        self.queries: Dict[str, Dict[str, Any]] = {}
        self.mutations: Dict[str, Dict[str, Any]] = {}
        self.resolvers: Dict[str, Callable] = {}
    
    def add_type(self, name: str, fields: Dict[str, Any]):
        """添加类型定义"""
        self.types[name] = fields
    
    def add_query(self, name: str, query_type: str, fields: List[str], resolver: Callable):
        """添加查询"""
        self.queries[name] = {
            "type": query_type,
            "fields": fields,
            "resolver": resolver
        }
        self.resolvers[f"query.{name}"] = resolver
    
    def add_mutation(self, name: str, mutation_type: str, fields: List[str], resolver: Callable):
        """添加变更"""
        self.mutations[name] = {
            "type": mutation_type,
            "fields": fields,
            "resolver": resolver
        }
        self.resolvers[f"mutation.{name}"] = resolver
    
    def execute(self, query: GraphQLQuery) -> GraphQLResponse:
        """执行查询"""
        try:
            # 解析查询
            operation = self._parse_query(query.query)
            
            if not operation:
                return GraphQLResponse(
                    errors=[{"message": "Invalid query"}]
                )
            
            # 执行操作
            op_type = operation.get("type")  # query or mutation
            op_name = operation.get("name")
            selections = operation.get("selections", [])
            
            results = {}
            for selection in selections:
                field_name = selection.get("field")
                resolver_key = f"{op_type}.{field_name}"
                
                if resolver_key in self.resolvers:
                    resolver = self.resolvers[resolver_key]
                    args = selection.get("arguments", {})
                    
                    # 合并查询变量
                    for arg_name, arg_value in args.items():
                        if isinstance(arg_value, dict) and "variable" in arg_value:
                            var_name = arg_value["variable"]
                            args[arg_name] = query.variables.get(var_name)
                    
                    result = resolver(args)
                    results[field_name] = result
            
            return GraphQLResponse(data=results)
            
        except Exception as e:
            return GraphQLResponse(
                errors=[{"message": str(e)}]
            )
    
    def _parse_query(self, query_str: str) -> Optional[Dict[str, Any]]:
        """简单查询解析"""
        # 这是一个简化实现，实际应该使用graphql-core等库
        if query_str.strip().startswith("query"):
            return {"type": "query", "selections": []}
        elif query_str.strip().startswith("mutation"):
            return {"type": "mutation", "selections": []}
        return None


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.connections: Dict[str, Set[str]] = defaultdict(set)
        self.user_sockets: Dict[str, str] = {}
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.message_handlers: Dict[str, Callable] = {}
    
    def connect(self, socket_id: str, user_id: str):
        """建立连接"""
        self.connections[user_id].add(socket_id)
        self.user_sockets[socket_id] = user_id
    
    def disconnect(self, socket_id: str):
        """断开连接"""
        if socket_id in self.user_sockets:
            user_id = self.user_sockets.pop(socket_id)
            if user_id in self.connections and socket_id in self.connections[user_id]:
                self.connections[user_id].discard(socket_id)
    
    def subscribe(self, socket_id: str, channel: str):
        """订阅频道"""
        self.subscriptions[channel].add(socket_id)
    
    def unsubscribe(self, socket_id: str, channel: str):
        """取消订阅"""
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(socket_id)
    
    def send_to_user(self, user_id: str, message: WebSocketMessage):
        """发送给用户"""
        if user_id in self.connections:
            for socket_id in self.connections[user_id]:
                self._send_message(socket_id, message)
    
    def broadcast_to_channel(self, channel: str, message: WebSocketMessage):
        """广播到频道"""
        if channel in self.subscriptions:
            for socket_id in self.subscriptions[channel]:
                self._send_message(socket_id, message)
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """添加消息处理器"""
        self.message_handlers[message_type] = handler
    
    def handle_message(self, socket_id: str, message: WebSocketMessage):
        """处理消息"""
        if message.type in self.message_handlers:
            handler = self.message_handlers[message.type]
            handler(socket_id, message)
    
    def _send_message(self, socket_id: str, message: WebSocketMessage):
        """发送消息（需要与实际的WebSocket实现集成）"""
        # 这里应该是实际的发送逻辑
        pass
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self.user_sockets)


class APISDK:
    """记忆系统SDK"""
    
    def __init__(self, base_url: str, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.rest_router = RESTAPIRouter()
        self.graphql = GraphQLSchema()
        self.ws_manager = WebSocketManager()
    
    # Memory Operations
    def add_memory(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """添加记忆"""
        return self._make_request(
            HTTPMethod.POST,
            "/api/v1/memories",
            body={"content": content, "metadata": metadata or {}}
        )
    
    def get_memory(self, memory_id: str) -> Dict[str, Any]:
        """获取记忆"""
        return self._make_request(
            HTTPMethod.GET,
            f"/api/v1/memories/{memory_id}"
        )
    
    def update_memory(self, memory_id: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """更新记忆"""
        return self._make_request(
            HTTPMethod.PUT,
            f"/api/v1/memories/{memory_id}",
            body={"content": content, "metadata": metadata or {}}
        )
    
    def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """删除记忆"""
        return self._make_request(
            HTTPMethod.DELETE,
            f"/api/v1/memories/{memory_id}"
        )
    
    def search_memories(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索记忆"""
        return self._make_request(
            HTTPMethod.POST,
            "/api/v1/search",
            body={"query": query, "filters": filters or {}}
        )
    
    # GraphQL Operations
    def execute_graphql(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行GraphQL查询"""
        graphql_query = GraphQLQuery(
            query=query,
            variables=variables or {}
        )
        return self.graphql.execute(graphql_query)
    
    # WebSocket Operations
    def connect_websocket(self, user_id: str) -> str:
        """建立WebSocket连接"""
        socket_id = hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()
        self.ws_manager.connect(socket_id, user_id)
        return socket_id
    
    def subscribe_to_updates(self, socket_id: str, channel: str):
        """订阅更新"""
        self.ws_manager.subscribe(socket_id, channel)
    
    def _make_request(
        self,
        method: HTTPMethod,
        path: str,
        params: Dict[str, Any] = None,
        body: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """发起HTTP请求"""
        # 这里应该是实际的HTTP请求逻辑
        # 简化实现，返回模拟数据
        return {
            "status": "success",
            "method": method.value,
            "path": path,
            "timestamp": time.time()
        }


# 全局SDK实例
_global_sdk: Optional[APISDK] = None


def get_api_sdk(base_url: str = "http://localhost:8000", api_key: str = "") -> APISDK:
    """获取API SDK单例"""
    global _global_sdk
    if _global_sdk is None:
        _global_sdk = APISDK(base_url, api_key)
    return _global_sdk


class APIIntegration:
    """API集成管理器"""
    
    def __init__(self):
        self.rest_router = RESTAPIRouter()
        self.graphql_schema = GraphQLSchema()
        self.ws_manager = WebSocketManager()
        self.sdk = APISDK("http://localhost:8000")
    
    def setup_routes(self):
        """设置路由"""
        # Memory endpoints
        self.rest_router.register_endpoint(
            "/api/v1/memories",
            HTTPMethod.POST,
            self._handle_add_memory,
            APIEndpointType.MEMORY,
            description="Add a new memory"
        )
        
        self.rest_router.register_endpoint(
            "/api/v1/memories/{id}",
            HTTPMethod.GET,
            self._handle_get_memory,
            APIEndpointType.MEMORY,
            description="Get a memory by ID"
        )
        
        # Search endpoints
        self.rest_router.register_endpoint(
            "/api/v1/search",
            HTTPMethod.POST,
            self._handle_search,
            APIEndpointType.SEARCH,
            description="Search memories"
        )
        
        # System endpoints
        self.rest_router.register_endpoint(
            "/api/v1/health",
            HTTPMethod.GET,
            self._handle_health,
            APIEndpointType.SYSTEM,
            description="Health check",
            requires_auth=False
        )
        
        # Setup GraphQL
        self.graphql_schema.add_type("Memory", {
            "id": {"type": "string"},
            "content": {"type": "string"},
            "created_at": {"type": "float"}
        })
        
        self.graphql_schema.add_query(
            "memories",
            "[Memory]",
            ["id", "content", "created_at"],
            lambda args: []
        )
        
        self.graphql_schema.add_mutation(
            "createMemory",
            "Memory",
            ["id", "content"],
            lambda args: {}
        )
    
    def _handle_add_memory(self, request: APIRequest) -> Dict[str, Any]:
        """处理添加记忆"""
        return {"status": "success", "id": "mem_123"}
    
    def _handle_get_memory(self, request: APIRequest) -> Dict[str, Any]:
        """处理获取记忆"""
        return {"id": "mem_123", "content": "Test memory"}
    
    def _handle_search(self, request: APIRequest) -> Dict[str, Any]:
        """处理搜索"""
        return {"results": [], "count": 0}
    
    def _handle_health(self, request: APIRequest) -> Dict[str, Any]:
        """处理健康检查"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "connections": self.ws_manager.get_connection_count()
        }
    
    def get_all_routes(self) -> List[Dict[str, Any]]:
        """获取所有路由"""
        return self.rest_router.get_routes()
