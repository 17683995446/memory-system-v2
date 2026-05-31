"""
记忆系统API测试客户端
测试API的各个功能
"""

import sys
import os
import json
import time
import threading
from http.server import HTTPServer
from io import BytesIO
from typing import Dict, List, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api_server import MemoryAPIHandler, APIResponse


class MockRequest:
    """模拟HTTP请求"""
    def __init__(self, method: str, path: str, body: bytes = None):
        self.method = method
        self.path = path
        self.body = body or b''
        self.rfile = BytesIO(body) if body else BytesIO()
        self.wfile = BytesIO()
        self.response_data = None
        self.response_status = None
        self.response_headers = {}

    def makefile(self, mode: str, *args, **kwargs):
        if mode == 'rb':
            return self.rfile
        elif mode == 'wb':
            return self.wfile
        raise NotImplementedError()

    def send_response(self, status_code: int):
        self.response_status = status_code

    def send_header(self, name: str, value: str):
        self.response_headers[name] = value

    def end_headers(self):
        pass


class APITestClient:
    """API测试客户端"""

    def __init__(self):
        # 创建一个简单的处理器实例来测试
        # 我们使用继承和模拟的方式
        class TestHandler(MemoryAPIHandler):
            def __init__(self, *args, **kwargs):
                # 不调用父类的__init__，因为它会尝试处理请求
                pass

        self.handler = TestHandler()
        # 手动初始化各个模块
        from src.memory import get_memory_system
        from src.qa import MemoryQASystem
        from src.export import MemoryExporter, MemorySharer
        from src.security import EncryptionManager, AccessControlManager

        self.handler.memory_system = get_memory_system()
        self.handler.qa_system = MemoryQASystem()
        self.handler.encryption_manager = EncryptionManager()
        self.handler.access_control = AccessControlManager()
        self.handler.conversation_map = {}
        self.handler.api_memories = []

    def request(self, method: str, path: str, body: Dict = None) -> Dict:
        """发送请求"""
        # 为每个请求创建新的处理实例
        class RequestHandler(MemoryAPIHandler):
            def __init__(self, client):
                # 复制必要的模块
                self.memory_system = client.handler.memory_system
                self.qa_system = client.handler.qa_system
                self.encryption_manager = client.handler.encryption_manager
                self.access_control = client.handler.access_control
                self.conversation_map = client.handler.conversation_map
                self.api_memories = client.handler.api_memories
                self.setup()

        req = RequestHandler(self)
        req.command = method
        req.path = path
        req.rfile = BytesIO()
        req.wfile = BytesIO()
        req.headers = {}

        if body:
            body_json = json.dumps(body).encode('utf-8')
            req.rfile = BytesIO(body_json)
            req.headers['Content-Length'] = str(len(body_json))

        # 模拟处理
        try:
            if method == 'GET':
                req.do_GET()
            elif method == 'POST':
                req.do_POST()
            elif method == 'DELETE':
                req.do_DELETE()
            elif method == 'OPTIONS':
                req.do_OPTIONS()
        except Exception as e:
            print(f"请求处理错误: {e}")

        # 获取响应
        response_data = req.wfile.getvalue()
        result = json.loads(response_data.decode('utf-8'))

        return result

    def get(self, path: str) -> Dict:
        return self.request('GET', path)

    def post(self, path: str, body: Dict) -> Dict:
        return self.request('POST', path, body)

    def delete(self, path: str) -> Dict:
        return self.request('DELETE', path)


def test_api():
    """测试API功能"""
    print("\n" + "=" * 70)
    print("第30阶段测试: 记忆系统Web API")
    print("=" * 70)

    client = APITestClient()
    all_tests_passed = True

    # 测试1: 健康检查
    print("\n[测试1] 健康检查")
    try:
        result = client.get('/health')
        assert result['success']
        assert result['data']['status'] == 'healthy'
        print("✓ 健康检查通过")
    except Exception as e:
        print(f"✗ 健康检查失败: {e}")
        all_tests_passed = False

    # 测试2: 添加记忆
    print("\n[测试2] 添加记忆")
    try:
        result = client.post('/api/memory', {
            'content': '项目启动会议在2026年1月15日举行',
            'source': 'test',
            'level': 'l2'
        })
        assert result['success']
        mem_id = result['data']['id']
        print(f"✓ 记忆添加成功，ID: {mem_id}")

        # 添加更多记忆
        test_memories = [
            '张三负责前端开发，使用React框架',
            '李四负责后端开发，使用Python和FastAPI',
            '本周完成了用户界面设计评审'
        ]

        for content in test_memories:
            client.post('/api/memory', {
                'content': content,
                'source': 'test',
                'level': 'l2'
            })
        print("✓ 批量添加记忆成功")
    except Exception as e:
        print(f"✗ 添加记忆失败: {e}")
        all_tests_passed = False

    # 测试3: 列出记忆
    print("\n[测试3] 列出记忆")
    try:
        result = client.get('/api/memories')
        assert result['success']
        assert result['data']['count'] > 0
        print(f"✓ 列出记忆成功，共 {result['data']['count']} 条")
    except Exception as e:
        print(f"✗ 列出记忆失败: {e}")
        all_tests_passed = False

    # 测试4: 搜索记忆
    print("\n[测试4] 搜索记忆")
    try:
        result = client.post('/api/memory/search', {'query': '张三'})
        assert result['success']
        print(f"✓ 搜索成功，找到 {result['data']['count']} 条结果")
        for mem in result['data']['results']:
            print(f"  - {mem['text'][:40]}...")
    except Exception as e:
        print(f"✗ 搜索记忆失败: {e}")
        all_tests_passed = False

    # 测试5: 问答系统
    print("\n[测试5] 问答系统")
    try:
        # 先提问一个问题
        result = client.post('/api/qa/ask', {
            'question': '张三负责什么工作？'
        })
        assert result['success']
        conv_id = result['data']['conversation_id']
        print(f"✓ 提问成功，回答: {result['data']['answer']['answer'][:60]}...")
        print(f"  对话ID: {conv_id}")

        # 测试对话历史
        history_result = client.get(f'/api/qa/history?conversation_id={conv_id}')
        assert history_result['success']
        print("✓ 对话历史查询成功")
    except Exception as e:
        print(f"✗ 问答系统测试失败: {e}")
        all_tests_passed = False

    # 测试6: 导出记忆
    print("\n[测试6] 导出记忆")
    try:
        # 导出为JSON
        json_result = client.post('/api/export', {
            'format': 'json',
            'include_metadata': True
        })
        assert json_result['success']
        print(f"✓ JSON导出成功，共 {json_result['data']['memory_count']} 条记忆")

        # 导出为Markdown
        md_result = client.post('/api/export', {
            'format': 'markdown'
        })
        assert md_result['success']
        print("✓ Markdown导出成功")
    except Exception as e:
        print(f"✗ 导出记忆失败: {e}")
        all_tests_passed = False

    # 测试7: 系统统计
    print("\n[测试7] 系统统计")
    try:
        result = client.get('/api/stats')
        assert result['success']
        print(f"✓ 系统统计获取成功")
        print(f"  API记忆数: {result['data']['api_memory_count']}")
    except Exception as e:
        print(f"✗ 系统统计失败: {e}")
        all_tests_passed = False

    # 测试8: 创建分享
    print("\n[测试8] 创建分享")
    try:
        result = client.post('/api/share', {
            'type': 'read',
            'expires_hours': 24
        })
        assert result['success']
        print(f"✓ 创建分享成功")
        print(f"  分享ID: {result['data']['share_id']}")
        print(f"  分享记忆数: {result['data']['memory_count']}")
    except Exception as e:
        print(f"✗ 创建分享失败: {e}")
        all_tests_passed = False

    print("\n" + "=" * 70)
    if all_tests_passed:
        print("✓ 所有API测试通过!")
    else:
        print("✗ 部分测试失败")
    print("=" * 70)

    return all_tests_passed


def create_api_documentation():
    """创建API文档"""
    doc_content = """# 记忆系统API文档

## 基础信息
- 基础URL: `http://localhost:8000`
- 数据格式: JSON
- 编码: UTF-8

## 通用响应格式
```json
{
  "success": true/false,
  "data": {...},
  "error": "错误信息",
  "timestamp": 1234567890.123
}
```

## API端点

### 1. 健康检查
- **URL**: `GET /health`
- **说明**: 检查服务是否正常运行
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "service": "Memory System API",
    "version": "1.0.0"
  }
}
```

### 2. 添加记忆
- **URL**: `POST /api/memory`
- **请求体**:
```json
{
  "content": "记忆内容",
  "source": "来源",
  "level": "l2",
  "encrypt": false
}
```
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "mem_xxx",
    "content": "记忆内容",
    "source": "来源",
    "level": "l2"
  }
}
```

### 3. 获取单个记忆
- **URL**: `GET /api/memory?id=<记忆ID>`

### 4. 列出记忆
- **URL**: `GET /api/memories?limit=<数量>&level=<层级>`

### 5. 删除记忆
- **URL**: `DELETE /api/memory?id=<记忆ID>`

### 6. 搜索记忆
- **URL**: `POST /api/memory/search`
- **请求体**:
```json
{
  "query": "搜索关键词"
}
```

### 7. 提问问题
- **URL**: `POST /api/qa/ask`
- **请求体**:
```json
{
  "question": "问题内容",
  "conversation_id": "对话ID（可选）"
}
```

### 8. 获取对话历史
- **URL**: `GET /api/qa/history?conversation_id=<对话ID>`

### 9. 清除对话
- **URL**: `DELETE /api/conversation?conversation_id=<对话ID>`

### 10. 导出记忆
- **URL**: `POST /api/export`
- **请求体**:
```json
{
  "format": "json|text|markdown|csv",
  "include_metadata": true
}
```

### 11. 创建分享
- **URL**: `POST /api/share`
- **请求体**:
```json
{
  "memory_ids": ["id1", "id2"],
  "type": "read",
  "expires_hours": 24
}
```

### 12. 获取系统统计
- **URL**: `GET /api/stats`

## 使用示例 (Python)

```python
import requests
import json

# 基础URL
BASE_URL = "http://localhost:8000"

# 添加记忆
response = requests.post(f"{BASE_URL}/api/memory", json={
    "content": "这是一条新的记忆",
    "source": "api_test",
    "level": "l2"
})
print(response.json())

# 提问问题
response = requests.post(f"{BASE_URL}/api/qa/ask", json={
    "question": "这是关于什么的？"
})
print(response.json())

# 导出记忆
response = requests.post(f"{BASE_URL}/api/export", json={
    "format": "json",
    "include_metadata": true
})
print(response.json())
```

## 使用示例 (curl)

```bash
# 添加记忆
curl -X POST http://localhost:8000/api/memory \\
  -H "Content-Type: application/json" \\
  -d '{"content": "新的记忆内容", "source": "curl", "level": "l2"}'

# 提问
curl -X POST http://localhost:8000/api/qa/ask \\
  -H "Content-Type: application/json" \\
  -d '{"question": "项目启动会议时间?"}'

# 导出
curl -X POST http://localhost:8000/api/export \\
  -H "Content-Type: application/json" \\
  -d '{"format": "json"}'
```
"""
    return doc_content


if __name__ == "__main__":
    # 运行API测试
    success = test_api()

    # 生成API文档
    doc = create_api_documentation()
    with open('API_DOCUMENTATION.md', 'w', encoding='utf-8') as f:
        f.write(doc)
    print("\n✓ API文档已生成: API_DOCUMENTATION.md")

    sys.exit(0 if success else 1)
