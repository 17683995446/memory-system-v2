# 记忆系统API - 快速开始

## 启动服务器

```bash
python -m src.api_server --port 8000
```

## 使用示例

### Python (使用 requests)
```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 添加记忆
response = requests.post(f"{BASE_URL}/api/memory", json={
    "content": "这是一条测试记忆",
    "source": "python_api",
    "level": "l2"
})
print("添加记忆:", response.json())

# 提问
response = requests.post(f"{BASE_URL}/api/qa/ask", json={
    "question": "这是关于什么的？"
})
print("问答结果:", response.json())

# 导出
response = requests.post(f"{BASE_URL}/api/export", json={
    "format": "json"
})
print("导出结果:", response.json())
```

### cURL
```bash
# 健康检查
curl http://localhost:8000/health

# 添加记忆
curl -X POST http://localhost:8000/api/memory \
  -H "Content-Type: application/json" \
  -d '{"content": "新的记忆", "source": "curl", "level": "l2"}'

# 列出所有记忆
curl http://localhost:8000/api/memories

# 提问
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "记忆内容是什么？"}'
```

## API端点总览
- GET /health - 健康检查
- POST /api/memory - 添加记忆
- GET /api/memory - 获取单个记忆
- GET /api/memories - 列出所有记忆
- DELETE /api/memory - 删除记忆
- POST /api/memory/search - 搜索记忆
- POST /api/qa/ask - 提问问题
- GET /api/qa/history - 获取对话历史
- POST /api/export - 导出记忆
- POST /api/share - 创建分享
- GET /api/stats - 获取系统统计
