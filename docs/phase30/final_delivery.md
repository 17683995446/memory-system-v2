# 第30阶段交付: 记忆系统Web API

## 阶段概述

遵循"图难于其易，为大于其细"的原则，本阶段实现了完整的记忆系统Web API，提供了RESTful风格的HTTP接口，让用户可以轻松地通过API使用记忆系统的所有功能。

## 核心功能

### 1. API服务架构
- **HTTP服务器**: 基于Python标准库 `http.server` 实现
- **RESTful设计**: 符合REST架构风格的API设计
- **JSON格式**: 所有请求和响应使用JSON格式
- **CORS支持**: 跨域资源共享支持，方便前端调用

### 2. 记忆管理API
- **添加记忆**: `POST /api/memory` - 添加新的记忆
- **获取记忆**: `GET /api/memory?id=<ID>` - 获取单个记忆
- **列出记忆**: `GET /api/memories?limit=<N>&level=<L>` - 列出所有记忆
- **删除记忆**: `DELETE /api/memory?id=<ID>` - 删除指定记忆
- **搜索记忆**: `POST /api/memory/search` - 搜索相关记忆

### 3. 问答系统API
- **提问问题**: `POST /api/qa/ask` - 向记忆系统提问
- **对话历史**: `GET /api/qa/history?conversation_id=<ID>` - 获取对话历史
- **清除对话**: `DELETE /api/conversation?conversation_id=<ID>` - 清除对话

### 4. 导出和分享API
- **导出记忆**: `POST /api/export` - 导出为JSON/Text/Markdown/CSV格式
- **创建分享**: `POST /api/share` - 创建记忆分享链接

### 5. 系统管理API
- **健康检查**: `GET /health` - 检查服务状态
- **系统统计**: `GET /api/stats` - 获取系统统计信息

## 实现文件

| 文件 | 说明 |
|------|------|
| [src/api_server.py](../../src/api_server.py) | API服务器核心实现 |
| [test_phase30_api_simple.py](../../test_phase30_api_simple.py) | API功能测试 |
| [API_QUICKSTART.md](../../API_QUICKSTART.md) | API快速开始指南 |
| [docs/phase30/final_delivery.md](./final_delivery.md) | 本文档 |

## 使用示例

### 启动API服务器

```bash
# 默认端口 8000
python -m src.api_server

# 指定端口
python -m src.api_server --port 9000

# 指定监听地址
python -m src.api_server --host 0.0.0.0 --port 8000
```

### Python使用示例

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. 健康检查
response = requests.get(f"{BASE_URL}/health")
print("健康检查:", response.json())

# 2. 添加记忆
response = requests.post(f"{BASE_URL}/api/memory", json={
    "content": "项目启动会议在2026年1月15日举行",
    "source": "api_test",
    "level": "l2"
})
print("添加记忆:", response.json())

# 3. 列出所有记忆
response = requests.get(f"{BASE_URL}/api/memories")
print("记忆列表:", response.json())

# 4. 搜索记忆
response = requests.post(f"{BASE_URL}/api/memory/search", json={
    "query": "项目"
})
print("搜索结果:", response.json())

# 5. 提问问题
response = requests.post(f"{BASE_URL}/api/qa/ask", json={
    "question": "项目启动会议是什么时候？"
})
result = response.json()
print("问答结果:", result)
print("回答:", result['data']['answer']['answer'])

# 6. 导出记忆
response = requests.post(f"{BASE_URL}/api/export", json={
    "format": "json",
    "include_metadata": True
})
print("导出结果:", response.json())

# 7. 创建分享
response = requests.post(f"{BASE_URL}/api/share", json={
    "type": "read",
    "expires_hours": 24
})
print("分享结果:", response.json())

# 8. 获取系统统计
response = requests.get(f"{BASE_URL}/api/stats")
print("系统统计:", response.json())
```

### cURL使用示例

```bash
# 健康检查
curl http://localhost:8000/health

# 添加记忆
curl -X POST http://localhost:8000/api/memory \
  -H "Content-Type: application/json" \
  -d '{"content": "新的记忆内容", "source": "curl", "level": "l2"}'

# 列出记忆
curl http://localhost:8000/api/memories

# 搜索记忆
curl -X POST http://localhost:8000/api/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "记忆"}'

# 提问
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "这是关于什么的？"}'

# 导出
curl -X POST http://localhost:8000/api/export \
  -H "Content-Type: application/json" \
  -d '{"format": "json"}'
```

### JavaScript使用示例

```javascript
const BASE_URL = "http://localhost:8000";

// 添加记忆
fetch(`${BASE_URL}/api/memory`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        content: "来自JavaScript的记忆",
        source: "javascript",
        level: "l2"
    })
})
.then(response => response.json())
.then(data => console.log('添加记忆:', data));

// 提问
fetch(`${BASE_URL}/api/qa/ask`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        question: "这条记忆是什么内容？"
    })
})
.then(response => response.json())
.then(data => console.log('回答:', data.data.answer.answer));
```

## API端点详细说明

### 通用响应格式

所有API响应遵循统一格式：

```json
{
    "success": true/false,
    "data": {...},
    "error": "错误信息（如果失败）",
    "timestamp": 1234567890.123
}
```

### 1. 健康检查

- **URL**: `GET /health`
- **说明**: 检查API服务是否正常运行
- **响应示例**:
```json
{
    "success": true,
    "data": {
        "status": "healthy",
        "service": "Memory System API",
        "version": "1.0.0"
    },
    "timestamp": 1779811648.458
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
        "id": "l2_1234567890",
        "content": "记忆内容",
        "source": "来源",
        "level": "l2"
    }
}
```

### 3. 列出记忆

- **URL**: `GET /api/memories?limit=<N>&level=<层级>`
- **参数**:
  - `limit`: 返回的最大数量（默认50）
  - `level`: 按层级筛选（可选）
- **响应示例**:
```json
{
    "success": true,
    "data": {
        "count": 4,
        "memories": [...]
    }
}
```

### 4. 提问问题

- **URL**: `POST /api/qa/ask`
- **请求体**:
```json
{
    "question": "问题内容",
    "conversation_id": "对话ID（可选，用于多轮对话）"
}
```
- **响应示例**:
```json
{
    "success": true,
    "data": {
        "question": "问题内容",
        "answer": {
            "answer": "回答内容",
            "quality": "good",
            "confidence": 0.85,
            "sources": [...]
        },
        "analysis": {
            "question_type": "factual",
            "keywords": [...]
        },
        "conversation_id": "abc123",
        "retrieved_count": 3
    }
}
```

## 设计原则

本阶段严格遵循基于第一性原理的设计准则：

1. **简洁性**: 提供简单明了的API接口
2. **统一性**: 所有API使用统一的响应格式
3. **实用性**: 覆盖实际使用场景的常用功能
4. **可扩展性**: 易于添加新的API端点
5. **兼容性**: 使用标准HTTP协议，支持多种客户端

## 测试覆盖

运行API功能测试：

```bash
python test_phase30_api_simple.py
```

测试结果：
- ✓ 模块初始化
- ✓ 记忆管理（添加、搜索）
- ✓ 问答系统
- ✓ 导出和分享功能
- ✓ 统计信息

## 验收标准

| 标准 | 状态 |
|------|------|
| API服务架构完整 | ✓ 完成 |
| 记忆管理API功能正常 | ✓ 完成 |
| 问答系统API功能正常 | ✓ 完成 |
| 导出分享API功能正常 | ✓ 完成 |
| 所有功能测试通过 | ✓ 完成 |
| API文档完善 | ✓ 完成 |

## 总结

第30阶段圆满完成！我们实现了：

1. **完整的Web API服务**: 基于Python标准库的HTTP服务器
2. **全面的API端点**: 12个API接口，覆盖所有核心功能
3. **多语言支持**: 提供Python、cURL、JavaScript使用示例
4. **完善的文档**: API文档和快速开始指南
5. **功能测试**: 所有核心功能测试通过

Web API让记忆系统可以轻松集成到各种应用中，提供了标准化的访问方式！
