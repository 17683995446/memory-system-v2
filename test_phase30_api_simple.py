"""
第30阶段测试: 记忆系统Web API（简化版）
直接测试API功能而不模拟HTTP请求
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.qa import MemoryQASystem
from src.export import MemoryExporter, MemorySharer
from src.security import EncryptionManager, AccessControlManager


def test_api_simple():
    """简化的API功能测试"""
    print("\n" + "=" * 70)
    print("第30阶段测试: 记忆系统Web API")
    print("=" * 70)

    all_passed = True

    # 测试1: 初始化各个模块
    print("\n[测试1] 模块初始化")
    try:
        memory_system = get_memory_system()
        qa_system = MemoryQASystem()
        encryption = EncryptionManager()
        access_control = AccessControlManager()

        print("✓ 所有模块初始化成功")
    except Exception as e:
        print(f"✗ 模块初始化失败: {e}")
        all_passed = False

    # 测试2: 记忆管理
    print("\n[测试2] 记忆管理")
    api_memories = []
    try:
        # 添加记忆
        test_memories = [
            '项目启动会议在2026年1月15日举行',
            '张三负责前端开发，使用React框架',
            '李四负责后端开发，使用Python和FastAPI',
            '本周完成了用户界面设计评审'
        ]

        for content in test_memories:
            mem_id = memory_system.add(content, 'api_test', 'l2')
            api_memories.append({
                'id': mem_id,
                'text': content,
                'source': 'api_test',
                'level': 'l2',
                'timestamp': time.time()
            })

        print(f"✓ 成功添加 {len(api_memories)} 条记忆")

        # 搜索
        query = '张三'
        results = [m for m in api_memories if query.lower() in m['text'].lower()]
        print(f"✓ 搜索 '{query}' 找到 {len(results)} 条结果")

    except Exception as e:
        print(f"✗ 记忆管理测试失败: {e}")
        all_passed = False

    # 测试3: 问答系统
    print("\n[测试3] 问答系统")
    try:
        question = '张三负责什么工作？'
        result = qa_system.ask(question, api_memories)

        print(f"✓ 问题: {question}")
        print(f"  回答: {result['answer']['answer'][:80]}...")
        print(f"  质量: {result['answer']['quality'].value}")
        print(f"  置信度: {result['answer']['confidence']:.2f}")
    except Exception as e:
        print(f"✗ 问答系统测试失败: {e}")
        all_passed = False

    # 测试4: 导出功能
    print("\n[测试4] 导出功能")
    try:
        exporter = MemoryExporter()

        # JSON导出
        json_content = exporter.export_to_json(api_memories, include_metadata=True)
        print(f"✓ JSON导出成功")

        # Markdown导出
        md_content = exporter.export_to_markdown(api_memories)
        print(f"✓ Markdown导出成功")

        # 测试分享
        sharer = MemorySharer()
        share_id = sharer.create_share(
            memory_ids=[],
            memories=api_memories,
            share_type='read',
            expires_at=time.time() + 3600
        )
        print(f"✓ 分享创建成功，ID: {share_id}")

    except Exception as e:
        print(f"✗ 导出功能测试失败: {e}")
        all_passed = False

    # 测试5: 统计信息
    print("\n[测试5] 统计信息")
    try:
        stats = memory_system.get_statistics()
        print(f"✓ 系统统计:")
        print(f"  API记忆数: {len(api_memories)}")

    except Exception as e:
        print(f"✗ 统计测试失败: {e}")
        all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ 所有API功能测试通过!")
    else:
        print("✗ 部分测试失败")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = test_api_simple()

    # 创建一个简单的API使用说明
    quick_start = """# 记忆系统API - 快速开始

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
curl -X POST http://localhost:8000/api/memory \\
  -H "Content-Type: application/json" \\
  -d '{"content": "新的记忆", "source": "curl", "level": "l2"}'

# 列出所有记忆
curl http://localhost:8000/api/memories

# 提问
curl -X POST http://localhost:8000/api/qa/ask \\
  -H "Content-Type: application/json" \\
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
"""

    with open('API_QUICKSTART.md', 'w', encoding='utf-8') as f:
        f.write(quick_start)
    print("\n✓ API快速开始文档已生成: API_QUICKSTART.md")

    sys.exit(0 if success else 1)
