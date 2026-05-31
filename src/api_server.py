"""
记忆系统Web API服务
提供HTTP接口访问所有记忆系统功能
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory import get_memory_system
from src.qa import MemoryQASystem
from src.export import MemoryExporter, MemorySharer, EnhancedMemoryWithExport
from src.security import EncryptionManager, AccessControlManager, EnhancedMemoryWithSecurity


@dataclass
class APIResponse:
    """API响应结构"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: float = 0.0

    def __post_init__(self):
        self.timestamp = time.time()

    def to_dict(self) -> Dict:
        return asdict(self)


class MemoryAPIHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""

    def __init__(self, *args, **kwargs):
        # 初始化各个模块
        self.memory_system = get_memory_system()
        self.qa_system = MemoryQASystem()
        self.encryption_manager = EncryptionManager()
        self.access_control = AccessControlManager()
        self.conversation_map: Dict[str, List[Dict]] = {}

        # 初始化内存中的记忆存储（用于API）
        self.api_memories: List[Dict] = []

        super().__init__(*args, **kwargs)

    def _send_response(self, response: APIResponse, status_code: int = 200):
        """发送API响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

        response_str = json.dumps(response.to_dict(), ensure_ascii=False, indent=2)
        self.wfile.write(response_str.encode('utf-8'))

    def do_OPTIONS(self):
        """处理OPTIONS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def _read_json_body(self) -> Optional[Dict]:
        """读取JSON请求体"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                return json.loads(body.decode('utf-8'))
            return {}
        except Exception as e:
            return None

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        params = parse_qs(parsed_path.query)

        if path == '/api/memory':
            self._handle_get_memory(params)
        elif path == '/api/memories':
            self._handle_list_memories(params)
        elif path == '/api/qa/history':
            self._handle_get_conversation_history(params)
        elif path == '/api/stats':
            self._handle_get_stats()
        elif path == '/health':
            self._handle_health_check()
        else:
            self._send_response(
                APIResponse(success=False, error=f"未知路径: {path}"),
                status_code=404
            )

    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        body = self._read_json_body()

        if body is None:
            self._send_response(
                APIResponse(success=False, error="无效的请求体"),
                status_code=400
            )
            return

        if path == '/api/memory':
            self._handle_add_memory(body)
        elif path == '/api/qa/ask':
            self._handle_ask_question(body)
        elif path == '/api/memory/search':
            self._handle_search_memories(body)
        elif path == '/api/export':
            self._handle_export_memories(body)
        elif path == '/api/share':
            self._handle_create_share(body)
        else:
            self._send_response(
                APIResponse(success=False, error=f"未知路径: {path}"),
                status_code=404
            )

    def do_DELETE(self):
        """处理DELETE请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        params = parse_qs(parsed_path.query)

        if path == '/api/memory':
            self._handle_delete_memory(params)
        elif path == '/api/conversation':
            self._handle_clear_conversation(params)
        else:
            self._send_response(
                APIResponse(success=False, error=f"未知路径: {path}"),
                status_code=404
            )

    def _handle_health_check(self):
        """健康检查"""
        self._send_response(APIResponse(
            success=True,
            data={
                "status": "healthy",
                "service": "Memory System API",
                "version": "1.0.0"
            }
        ))

    def _handle_get_stats(self):
        """获取系统统计信息"""
        try:
            stats = self.memory_system.get_statistics()
            stats['api_memory_count'] = len(self.api_memories)
            self._send_response(APIResponse(success=True, data=stats))
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )

    def _handle_add_memory(self, body: Dict):
        """添加记忆"""
        try:
            content = body.get('content')
            if not content:
                self._send_response(
                    APIResponse(success=False, error="缺少必要参数: content"),
                    status_code=400
                )
                return

            source = body.get('source', 'api')
            level = body.get('level', 'l2')
            encrypt = body.get('encrypt', False)

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

            self._send_response(APIResponse(
                success=True,
                data={
                    'id': mem_id,
                    'content': content,
                    'source': source,
                    'level': level
                }
            ))
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )

    def _handle_get_memory(self, params: Dict):
        """获取单个记忆"""
        try:
            memory_ids = params.get('id', [])
            if not memory_ids:
                self._send_response(
                    APIResponse(success=False, error="缺少必要参数: id"),
                    status_code=400
                )
                return

            mem_id = memory_ids[0]

            # 从API内存存储中查找
            memory = next((m for m in self.api_memories if m['id'] == mem_id), None)

            if memory:
                self._send_response(APIResponse(success=True, data=memory))
            else:
                self._send_response(
                    APIResponse(success=False, error=f"未找到记忆: {mem_id}"),
                    status_code=404
                )
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )

    def _handle_list_memories(self, params: Dict):
        """列出所有记忆"""
        try:
            limit = int(params.get('limit', [50])[0])
            level = params.get('level', [None])[0]

            memories = self.api_memories

            # 按层级过滤
            if level:
                memories = [m for m in memories if m['level'] == level]

            # 限制数量
            memories = memories[-limit:] if len(memories) > limit else memories

            self._send_response(APIResponse(
                success=True,
                data={
                    'count': len(memories),
                    'memories': memories
                }
            ))
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )

    def _handle_delete_memory(self, params: Dict):
        """删除记忆"""
        try:
            memory_ids = params.get('id', [])
            if not memory_ids:
                self._send_response(
                    APIResponse(success=False, error="缺少必要参数: id"),
                    status_code=400
                )
                return

            mem_id = memory_ids[0]

            # 从API内存存储中删除
            initial_count = len(self.api_memories)
            self.api_memories = [m for m in self.api_memories if m['id'] != mem_id]

            if len(self.api_memories) < initial_count:
                self._send_response(APIResponse(
                    success=True,
                    data={'id': mem_id, 'deleted': True}
                ))
            else:
                self._send_response(
                    APIResponse(success=False, error=f"未找到记忆: {mem_id}"),
                    status_code=404
                )
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )

    def _handle_search_memories(self, body: Dict):
        """搜索记忆"""
        try:
            query = body.get('query')
            if not query:
                self._send_response(
                    APIResponse(success=False, error="缺少必要参数: query"),
                    status_code=400
                )
                return

            # 简单关键词搜索
            results = []
            query_lower = query.lower()

            for memory in self.api_memories:
                if query_lower in memory['text'].lower():
                    results.append(memory)

            self._send_response(APIResponse(
                success=True,
                data={
                    'query': query,
                    'count': len(results),
                    'results': results
                }
            ))
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )

    def _handle_ask_question(self, body: Dict):
        """提问问题"""
        try:
            question = body.get('question')
            if not question:
                self._send_response(
                    APIResponse(success=False, error="缺少必要参数: question"),
                    status_code=400
                )
                return

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

            self._send_response(APIResponse(
                success=True,
                data={
                    'question': question,
                    'answer': result['answer'],
                    'analysis': {
                        'question_type': result['analysis']['question_type'].value,
                        'keywords': result['analysis']['keywords']
                    },
                    'conversation_id': new_conv_id,
                    'retrieved_count': len(result['retrieved_memories'])
                }
            ))
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )

    def _handle_get_conversation_history(self, params: Dict):
        """获取对话历史"""
        try:
            conversation_ids = params.get('conversation_id', [])
            if not conversation_ids:
                # 返回所有对话
                self._send_response(APIResponse(
                    success=True,
                    data={
                        'conversations': list(self.conversation_map.keys())
                    }
                ))
                return

            conv_id = conversation_ids[0]
            history = self.conversation_map.get(conv_id, [])

            self._send_response(APIResponse(
                success=True,
                data={
                    'conversation_id': conv_id,
                    'history': history
                }
            ))
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )

    def _handle_clear_conversation(self, params: Dict):
        """清除对话"""
        try:
            conversation_ids = params.get('conversation_id', [])
            if not conversation_ids:
                # 清除所有对话
                self.conversation_map.clear()
                self._send_response(APIResponse(
                    success=True,
                    data={'cleared_all': True}
                ))
                return

            conv_id = conversation_ids[0]
            if conv_id in self.conversation_map:
                del self.conversation_map[conv_id]
                self._send_response(APIResponse(
                    success=True,
                    data={'conversation_id': conv_id, 'cleared': True}
                ))
            else:
                self._send_response(
                    APIResponse(success=False, error=f"未找到对话: {conv_id}"),
                    status_code=404
                )
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )

    def _handle_export_memories(self, body: Dict):
        """导出记忆"""
        try:
            format_type = body.get('format', 'json')
            include_metadata = body.get('include_metadata', True)

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

            self._send_response(APIResponse(
                success=True,
                data={
                    'format': format_type,
                    'content': content,
                    'memory_count': len(self.api_memories)
                }
            ))
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )

    def _handle_create_share(self, body: Dict):
        """创建分享"""
        try:
            memory_ids = body.get('memory_ids', [])
            share_type = body.get('type', 'read')
            expires_hours = body.get('expires_hours', 24)

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

            self._send_response(APIResponse(
                success=True,
                data={
                    'share_id': share_id,
                    'memory_count': len(memories_to_share),
                    'type': share_type,
                    'expires_in': f"{expires_hours}小时"
                }
            ))
        except Exception as e:
            self._send_response(
                APIResponse(success=False, error=str(e)),
                status_code=500
            )


def run_server(host: str = '0.0.0.0', port: int = 8000):
    """运行API服务器"""
    print(f"启动记忆系统API服务器...")
    print(f"监听地址: http://{host}:{port}")

    try:
        server = HTTPServer((host, port), MemoryAPIHandler)
        print(f"服务器已启动，按 Ctrl+C 停止")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        server.server_close()
        print("服务器已停止")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='记忆系统API服务器')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=8000, help='监听端口')

    args = parser.parse_args()
    run_server(args.host, args.port)
