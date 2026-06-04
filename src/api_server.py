"""
记忆系统Web API服务
提供HTTP接口访问所有记忆系统功能
基于第一性原理：确定性、健壮性、安全性
"""

import os
import sys
import json
import time
import uuid
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from enum import Enum

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory import get_memory_system
from src.qa import MemoryQASystem
from src.export import MemoryExporter, MemorySharer, EnhancedMemoryWithExport
from src.security import EncryptionManager, AccessControlManager, EnhancedMemoryWithSecurity
from src.utils.logger import get_logger

logger = get_logger()


class ErrorCode(Enum):
    """标准化错误码"""
    SUCCESS = 0
    INVALID_REQUEST = 1001
    MISSING_PARAMETER = 1002
    INVALID_PARAMETER = 1003
    RESOURCE_NOT_FOUND = 2001
    RESOURCE_ALREADY_EXISTS = 2002
    INTERNAL_ERROR = 5001
    RATE_LIMIT_EXCEEDED = 5002
    SERVICE_UNAVAILABLE = 5003


@dataclass
class APIResponse:
    """API响应结构"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_code: int = 0
    request_id: str = ""
    timestamp: float = 0.0

    def __post_init__(self):
        self.timestamp = time.time()

    def to_dict(self) -> Dict:
        return asdict(self)


class RequestValidator:
    """请求参数校验器"""

    # 合法的层级值
    VALID_LEVELS = {'l1', 'l2', 'l3'}
    # 最大内容长度 10MB
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    # 最大查询长度
    MAX_QUERY_LENGTH = 1000
    # 默认分页限制
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 1000

    @classmethod
    def validate_content(cls, content: Any) -> tuple[bool, Optional[str]]:
        """校验内容参数"""
        if content is None:
            return False, "内容不能为空"
        if not isinstance(content, str):
            return False, "内容必须是字符串"
        if len(content) == 0:
            return False, "内容不能为空字符串"
        if len(content.encode('utf-8')) > cls.MAX_CONTENT_LENGTH:
            return False, f"内容超过最大长度限制 {cls.MAX_CONTENT_LENGTH} 字节"
        return True, None

    @classmethod
    def validate_level(cls, level: Any) -> tuple[bool, Optional[str]]:
        """校验层级参数"""
        if level is None:
            return True, None  # 使用默认值
        if not isinstance(level, str):
            return False, "层级必须是字符串"
        if level.lower() not in cls.VALID_LEVELS:
            return False, f"层级必须是以下之一: {cls.VALID_LEVELS}"
        return True, None

    @classmethod
    def validate_query(cls, query: Any) -> tuple[bool, Optional[str]]:
        """校验查询参数"""
        if query is None:
            return False, "查询不能为空"
        if not isinstance(query, str):
            return False, "查询必须是字符串"
        if len(query) == 0:
            return False, "查询不能为空字符串"
        if len(query) > cls.MAX_QUERY_LENGTH:
            return False, f"查询超过最大长度 {cls.MAX_QUERY_LENGTH}"
        return True, None

    @classmethod
    def validate_limit(cls, limit: Any) -> tuple[int, Optional[str]]:
        """校验限制参数，返回(有效值, 错误信息)"""
        if limit is None:
            return cls.DEFAULT_LIMIT, None
        try:
            val = int(limit)
            if val < 1:
                return cls.DEFAULT_LIMIT, "限制必须大于0"
            if val > cls.MAX_LIMIT:
                return cls.MAX_LIMIT, f"限制超过最大值，已调整为 {cls.MAX_LIMIT}"
            return val, None
        except (ValueError, TypeError):
            return cls.DEFAULT_LIMIT, "限制必须是整数"

    @classmethod
    def validate_memory_id(cls, mem_id: Any) -> tuple[bool, Optional[str]]:
        """校验记忆ID"""
        if mem_id is None:
            return False, "ID不能为空"
        if not isinstance(mem_id, str):
            return False, "ID必须是字符串"
        if len(mem_id) == 0:
            return False, "ID不能为空字符串"
        if len(mem_id) > 256:
            return False, "ID长度不能超过256"
        return True, None


class RateLimiter:
    """API速率限制器"""

    def __init__(self, default_limit: int = 100, window_seconds: int = 60):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def check_limit(self, client_id: str, limit: Optional[int] = None) -> bool:
        """检查是否超过速率限制"""
        now = time.time()
        cutoff = now - self.window_seconds
        limit = limit or self.default_limit

        with self._lock:
            if client_id not in self._requests:
                self._requests[client_id] = []

            # 清理过期请求
            self._requests[client_id] = [
                ts for ts in self._requests[client_id] if ts > cutoff
            ]

            if len(self._requests[client_id]) >= limit:
                logger.warning(f"[RateLimit] Client {client_id} exceeded limit {limit}")
                return False

            self._requests[client_id].append(now)
            return True

    def get_remaining(self, client_id: str, limit: Optional[int] = None) -> int:
        """获取剩余请求数"""
        now = time.time()
        cutoff = now - self.window_seconds
        limit = limit or self.default_limit

        with self._lock:
            requests = self._requests.get(client_id, [])
            valid_requests = [ts for ts in requests if ts > cutoff]
            return max(0, limit - len(valid_requests))


class MemoryAPIHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""

    # 类级别的速率限制器
    rate_limiter = RateLimiter(default_limit=100, window_seconds=60)

    def __init__(self, *args, **kwargs):
        self._logger = get_logger()
        # 初始化各个模块
        self.memory_system = get_memory_system()
        self.qa_system = MemoryQASystem()
        self.encryption_manager = EncryptionManager()
        self.access_control = AccessControlManager()
        self.conversation_map: Dict[str, List[Dict]] = {}

        # 初始化内存中的记忆存储（用于API）
        self.api_memories: List[Dict] = []

        super().__init__(*args, **kwargs)

    def _generate_request_id(self) -> str:
        """生成请求ID"""
        return f"req_{uuid.uuid4().hex[:16]}_{int(time.time() * 1000)}"

    def _get_client_id(self) -> str:
        """获取客户端标识"""
        # 优先使用X-Forwarded-For，然后是Remote-Addr
        forwarded = self.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return self.client_address[0] if self.client_address else 'unknown'

    def _send_response(self, response: APIResponse, status_code: int = 200):
        """发送API响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Request-ID')
        self.send_header('X-Request-ID', response.request_id)
        self.end_headers()

        response_str = json.dumps(response.to_dict(), ensure_ascii=False, indent=2)
        self.wfile.write(response_str.encode('utf-8'))

    def _create_success_response(self, data: Any, request_id: str) -> APIResponse:
        """创建成功响应"""
        return APIResponse(success=True, data=data, request_id=request_id)

    def _create_error_response(self, error: str, error_code: ErrorCode, request_id: str) -> APIResponse:
        """创建错误响应（不暴露内部细节）"""
        # 内部错误不返回详细异常信息
        if error_code == ErrorCode.INTERNAL_ERROR:
            safe_error = "内部服务错误，请稍后重试"
            self._logger.error(f"[InternalError] request_id={request_id}, detail={error}")
        else:
            safe_error = error
        return APIResponse(
            success=False,
            error=safe_error,
            error_code=error_code.value,
            request_id=request_id
        )

    def do_OPTIONS(self):
        """处理OPTIONS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Request-ID')
        self.end_headers()

    def _read_json_body(self) -> Optional[Dict]:
        """读取JSON请求体"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                if content_length > RequestValidator.MAX_CONTENT_LENGTH:
                    return {'__error': f'请求体超过最大限制 {RequestValidator.MAX_CONTENT_LENGTH} 字节'}
                body = self.rfile.read(content_length)
                return json.loads(body.decode('utf-8'))
            return {}
        except json.JSONDecodeError as e:
            return {'__error': f'JSON解析错误: {str(e)}'}
        except Exception as e:
            return {'__error': f'读取请求体错误: {str(e)}'}

    def do_GET(self):
        """处理GET请求"""
        request_id = self._generate_request_id()
        client_id = self._get_client_id()

        # 速率限制检查
        if not self.rate_limiter.check_limit(client_id):
            self._send_response(
                self._create_error_response(
                    "请求过于频繁，请稍后再试",
                    ErrorCode.RATE_LIMIT_EXCEEDED,
                    request_id
                ),
                status_code=429
            )
            return

        parsed_path = urlparse(self.path)
        path = parsed_path.path
        params = parse_qs(parsed_path.query)

        self._logger.info(f"[API] {request_id} GET {path} client={client_id}")

        try:
            if path == '/api/memory':
                self._handle_get_memory(params, request_id)
            elif path == '/api/memories':
                self._handle_list_memories(params, request_id)
            elif path == '/api/qa/history':
                self._handle_get_conversation_history(params, request_id)
            elif path == '/api/stats':
                self._handle_get_stats(request_id)
            elif path == '/health':
                self._handle_health_check(request_id)
            else:
                self._send_response(
                    self._create_error_response(
                        f"未知路径: {path}",
                        ErrorCode.RESOURCE_NOT_FOUND,
                        request_id
                    ),
                    status_code=404
                )
        except Exception as e:
            self._logger.error(f"[API Error] {request_id} GET {path}: {str(e)}")
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def do_POST(self):
        """处理POST请求"""
        request_id = self._generate_request_id()
        client_id = self._get_client_id()

        # 速率限制检查
        if not self.rate_limiter.check_limit(client_id):
            self._send_response(
                self._create_error_response(
                    "请求过于频繁，请稍后再试",
                    ErrorCode.RATE_LIMIT_EXCEEDED,
                    request_id
                ),
                status_code=429
            )
            return

        parsed_path = urlparse(self.path)
        path = parsed_path.path
        body = self._read_json_body()

        # 检查请求体读取错误
        if body and '__error' in body:
            self._send_response(
                self._create_error_response(
                    body['__error'],
                    ErrorCode.INVALID_REQUEST,
                    request_id
                ),
                status_code=400
            )
            return

        self._logger.info(f"[API] {request_id} POST {path} client={client_id}")

        try:
            if path == '/api/memory':
                self._handle_add_memory(body or {}, request_id)
            elif path == '/api/qa/ask':
                self._handle_ask_question(body or {}, request_id)
            elif path == '/api/memory/search':
                self._handle_search_memories(body or {}, request_id)
            elif path == '/api/export':
                self._handle_export_memories(body or {}, request_id)
            elif path == '/api/share':
                self._handle_create_share(body or {}, request_id)
            else:
                self._send_response(
                    self._create_error_response(
                        f"未知路径: {path}",
                        ErrorCode.RESOURCE_NOT_FOUND,
                        request_id
                    ),
                    status_code=404
                )
        except Exception as e:
            self._logger.error(f"[API Error] {request_id} POST {path}: {str(e)}")
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def do_DELETE(self):
        """处理DELETE请求"""
        request_id = self._generate_request_id()
        client_id = self._get_client_id()

        # 速率限制检查
        if not self.rate_limiter.check_limit(client_id):
            self._send_response(
                self._create_error_response(
                    "请求过于频繁，请稍后再试",
                    ErrorCode.RATE_LIMIT_EXCEEDED,
                    request_id
                ),
                status_code=429
            )
            return

        parsed_path = urlparse(self.path)
        path = parsed_path.path
        params = parse_qs(parsed_path.query)

        self._logger.info(f"[API] {request_id} DELETE {path} client={client_id}")

        try:
            if path == '/api/memory':
                self._handle_delete_memory(params, request_id)
            elif path == '/api/conversation':
                self._handle_clear_conversation(params, request_id)
            else:
                self._send_response(
                    self._create_error_response(
                        f"未知路径: {path}",
                        ErrorCode.RESOURCE_NOT_FOUND,
                        request_id
                    ),
                    status_code=404
                )
        except Exception as e:
            self._logger.error(f"[API Error] {request_id} DELETE {path}: {str(e)}")
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def _handle_health_check(self, request_id: str):
        """健康检查"""
        self._send_response(self._create_success_response(
            {
                "status": "healthy",
                "service": "Memory System API",
                "version": "1.1.0",
                "features": ["rate_limiting", "request_validation", "structured_errors"]
            },
            request_id
        ))

    def _handle_get_stats(self, request_id: str):
        """获取系统统计信息"""
        try:
            stats = self.memory_system.get_statistics()
            stats['api_memory_count'] = len(self.api_memories)
            stats['rate_limit_remaining'] = self.rate_limiter.get_remaining(self._get_client_id())
            self._send_response(self._create_success_response(stats, request_id))
        except Exception as e:
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def _handle_add_memory(self, body: Dict, request_id: str):
        """添加记忆"""
        content = body.get('content')

        # 校验内容
        valid, error = RequestValidator.validate_content(content)
        if not valid:
            self._send_response(
                self._create_error_response(error, ErrorCode.INVALID_PARAMETER, request_id),
                status_code=400
            )
            return

        source = body.get('source', 'api')
        level = body.get('level', 'l2')
        encrypt = body.get('encrypt', False)

        # 校验层级
        valid, error = RequestValidator.validate_level(level)
        if not valid:
            self._send_response(
                self._create_error_response(error, ErrorCode.INVALID_PARAMETER, request_id),
                status_code=400
            )
            return

        try:
            # 添加到记忆系统
            mem_id = self.memory_system.add(content, source, level)

            # 保存到API内存存储（用于后续查询）
            memory_item = {
                'id': mem_id,
                'text': content,
                'source': source,
                'level': level,
                'encrypted': encrypt,
                'timestamp': time.time()
            }
            self.api_memories.append(memory_item)

            self._logger.info(f"[API] {request_id} Added memory {mem_id}")

            self._send_response(self._create_success_response(
                {
                    'id': mem_id,
                    'content': content,
                    'source': source,
                    'level': level
                },
                request_id
            ))
        except Exception as e:
            self._logger.error(f"[API] {request_id} Failed to add memory: {e}")
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def _handle_get_memory(self, params: Dict, request_id: str):
        """获取单个记忆"""
        memory_ids = params.get('id', [])
        if not memory_ids:
            self._send_response(
                self._create_error_response(
                    "缺少必要参数: id",
                    ErrorCode.MISSING_PARAMETER,
                    request_id
                ),
                status_code=400
            )
            return

        mem_id = memory_ids[0]

        # 校验ID
        valid, error = RequestValidator.validate_memory_id(mem_id)
        if not valid:
            self._send_response(
                self._create_error_response(error, ErrorCode.INVALID_PARAMETER, request_id),
                status_code=400
            )
            return

        # 从API内存存储中查找
        memory = next((m for m in self.api_memories if m['id'] == mem_id), None)

        if memory:
            self._send_response(self._create_success_response(memory, request_id))
        else:
            self._send_response(
                self._create_error_response(
                    f"未找到记忆: {mem_id}",
                    ErrorCode.RESOURCE_NOT_FOUND,
                    request_id
                ),
                status_code=404
            )

    def _handle_list_memories(self, params: Dict, request_id: str):
        """列出所有记忆"""
        try:
            limit_str = params.get('limit', [str(RequestValidator.DEFAULT_LIMIT)])[0]
            limit, error = RequestValidator.validate_limit(limit_str)
            if error and limit == RequestValidator.DEFAULT_LIMIT:
                # 只是警告，使用默认值
                pass

            level = params.get('level', [None])[0]
            if level:
                valid, error = RequestValidator.validate_level(level)
                if not valid:
                    self._send_response(
                        self._create_error_response(error, ErrorCode.INVALID_PARAMETER, request_id),
                        status_code=400
                    )
                    return

            memories = self.api_memories

            # 按层级过滤
            if level:
                memories = [m for m in memories if m['level'] == level]

            # 限制数量
            memories = memories[-limit:] if len(memories) > limit else memories

            self._send_response(self._create_success_response(
                {
                    'count': len(memories),
                    'limit': limit,
                    'memories': memories
                },
                request_id
            ))
        except Exception as e:
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def _handle_delete_memory(self, params: Dict, request_id: str):
        """删除记忆"""
        memory_ids = params.get('id', [])
        if not memory_ids:
            self._send_response(
                self._create_error_response(
                    "缺少必要参数: id",
                    ErrorCode.MISSING_PARAMETER,
                    request_id
                ),
                status_code=400
            )
            return

        mem_id = memory_ids[0]

        # 校验ID
        valid, error = RequestValidator.validate_memory_id(mem_id)
        if not valid:
            self._send_response(
                self._create_error_response(error, ErrorCode.INVALID_PARAMETER, request_id),
                status_code=400
            )
            return

        # 从API内存存储中删除
        initial_count = len(self.api_memories)
        self.api_memories = [m for m in self.api_memories if m['id'] != mem_id]

        if len(self.api_memories) < initial_count:
            self._logger.info(f"[API] {request_id} Deleted memory {mem_id}")
            self._send_response(self._create_success_response(
                {'id': mem_id, 'deleted': True},
                request_id
            ))
        else:
            self._send_response(
                self._create_error_response(
                    f"未找到记忆: {mem_id}",
                    ErrorCode.RESOURCE_NOT_FOUND,
                    request_id
                ),
                status_code=404
            )

    def _handle_search_memories(self, body: Dict, request_id: str):
        """搜索记忆"""
        query = body.get('query')

        # 校验查询
        valid, error = RequestValidator.validate_query(query)
        if not valid:
            self._send_response(
                self._create_error_response(error, ErrorCode.INVALID_PARAMETER, request_id),
                status_code=400
            )
            return

        try:
            # 简单关键词搜索
            results = []
            query_lower = query.lower()

            for memory in self.api_memories:
                if query_lower in memory['text'].lower():
                    results.append(memory)

            self._send_response(self._create_success_response(
                {
                    'query': query,
                    'count': len(results),
                    'results': results
                },
                request_id
            ))
        except Exception as e:
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def _handle_ask_question(self, body: Dict, request_id: str):
        """提问问题"""
        question = body.get('question')

        # 校验问题
        valid, error = RequestValidator.validate_query(question)
        if not valid:
            self._send_response(
                self._create_error_response(error, ErrorCode.INVALID_PARAMETER, request_id),
                status_code=400
            )
            return

        try:
            conversation_id = body.get('conversation_id')

            # 调用QA系统
            result = self.qa_system.ask(question, self.api_memories, conversation_id)

            # 保存对话历史
            new_conv_id = result['conversation_id']
            if new_conv_id not in self.conversation_map:
                self.conversation_map[new_conv_id] = []
            self.conversation_map[new_conv_id].append({
                'question': question,
                'answer': result['answer'],
                'timestamp': time.time()
            })

            self._send_response(self._create_success_response(
                {
                    'question': question,
                    'answer': result['answer'],
                    'analysis': {
                        'question_type': result['analysis']['question_type'].value,
                        'keywords': result['analysis']['keywords']
                    },
                    'conversation_id': new_conv_id,
                    'retrieved_count': len(result['retrieved_memories'])
                },
                request_id
            ))
        except Exception as e:
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def _handle_get_conversation_history(self, params: Dict, request_id: str):
        """获取对话历史"""
        try:
            conversation_ids = params.get('conversation_id', [])
            if not conversation_ids:
                # 返回所有对话
                self._send_response(self._create_success_response(
                    {
                        'conversations': list(self.conversation_map.keys())
                    },
                    request_id
                ))
                return

            conv_id = conversation_ids[0]
            history = self.conversation_map.get(conv_id, [])

            self._send_response(self._create_success_response(
                {
                    'conversation_id': conv_id,
                    'history': history
                },
                request_id
            ))
        except Exception as e:
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def _handle_clear_conversation(self, params: Dict, request_id: str):
        """清除对话"""
        try:
            conversation_ids = params.get('conversation_id', [])
            if not conversation_ids:
                # 清除所有对话
                self.conversation_map.clear()
                self._send_response(self._create_success_response(
                    {'cleared_all': True},
                    request_id
                ))
                return

            conv_id = conversation_ids[0]
            if conv_id in self.conversation_map:
                del self.conversation_map[conv_id]
                self._send_response(self._create_success_response(
                    {'conversation_id': conv_id, 'cleared': True},
                    request_id
                ))
            else:
                self._send_response(
                    self._create_error_response(
                        f"未找到对话: {conv_id}",
                        ErrorCode.RESOURCE_NOT_FOUND,
                        request_id
                    ),
                    status_code=404
                )
        except Exception as e:
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def _handle_export_memories(self, body: Dict, request_id: str):
        """导出记忆"""
        try:
            format_type = body.get('format', 'json')
            include_metadata = body.get('include_metadata', True)

            # 校验格式
            valid_formats = {'json', 'text', 'markdown', 'csv'}
            if format_type not in valid_formats:
                self._send_response(
                    self._create_error_response(
                        f"格式必须是以下之一: {valid_formats}",
                        ErrorCode.INVALID_PARAMETER,
                        request_id
                    ),
                    status_code=400
                )
                return

            exporter = MemoryExporter()

            if format_type == 'json':
                content = exporter.export_to_json(self.api_memories, include_metadata=include_metadata)
            elif format_type == 'text':
                content = exporter.export_to_text(self.api_memories)
            elif format_type == 'markdown':
                content = exporter.export_to_markdown(self.api_memories)
            elif format_type == 'csv':
                content = exporter.export_to_csv(self.api_memories)
            else:
                content = exporter.export_to_json(self.api_memories, include_metadata=include_metadata)

            self._send_response(self._create_success_response(
                {
                    'format': format_type,
                    'content': content,
                    'memory_count': len(self.api_memories)
                },
                request_id
            ))
        except Exception as e:
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )

    def _handle_create_share(self, body: Dict, request_id: str):
        """创建分享"""
        try:
            memory_ids = body.get('memory_ids', [])
            share_type = body.get('type', 'read')
            expires_hours = body.get('expires_hours', 24)

            # 校验分享类型
            valid_types = {'read', 'write'}
            if share_type not in valid_types:
                self._send_response(
                    self._create_error_response(
                        f"分享类型必须是以下之一: {valid_types}",
                        ErrorCode.INVALID_PARAMETER,
                        request_id
                    ),
                    status_code=400
                )
                return

            # 校验过期时间
            try:
                expires_hours = int(expires_hours)
                if expires_hours < 1 or expires_hours > 720:
                    raise ValueError("过期时间必须在1-720小时之间")
            except (ValueError, TypeError):
                self._send_response(
                    self._create_error_response(
                        "过期时间必须是1-720之间的整数",
                        ErrorCode.INVALID_PARAMETER,
                        request_id
                    ),
                    status_code=400
                )
                return

            sharer = MemorySharer()

            # 获取要分享的记忆
            memories_to_share = []
            if memory_ids:
                memories_to_share = [m for m in self.api_memories if m['id'] in memory_ids]
            else:
                memories_to_share = self.api_memories

            share_id = sharer.create_share(
                memory_ids=memory_ids,
                memories=memories_to_share,
                share_type=share_type,
                expires_at=time.time() + (expires_hours * 3600)
            )

            self._send_response(self._create_success_response(
                {
                    'share_id': share_id,
                    'memory_count': len(memories_to_share),
                    'type': share_type,
                    'expires_in': f"{expires_hours}小时"
                },
                request_id
            ))
        except Exception as e:
            self._send_response(
                self._create_error_response(str(e), ErrorCode.INTERNAL_ERROR, request_id),
                status_code=500
            )


def run_server(host: str = '0.0.0.0', port: int = 8000):
    """运行API服务器"""
    logger.info(f"启动记忆系统API服务器...")
    logger.info(f"监听地址: http://{host}:{port}")

    try:
        server = HTTPServer((host, port), MemoryAPIHandler)
        logger.info(f"服务器已启动，按 Ctrl+C 停止")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("正在停止服务器...")
        server.server_close()
        logger.info("服务器已停止")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='记忆系统API服务器')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=8000, help='监听端口')

    args = parser.parse_args()
    run_server(args.host, args.port)
