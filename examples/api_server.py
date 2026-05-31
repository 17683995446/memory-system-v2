"""
API服务运行示例
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory import get_memory_system
from src.preprocessing import get_preprocessor
from src.api import create_api_service


def main():
    """启动API服务"""
    print("=" * 70)
    print("启动基于第一性原理的Agent可靠记忆系统 - API服务")
    print("=" * 70)
    
    # 初始化系统
    memory_system = get_memory_system()
    preprocessor = get_preprocessor()
    
    # 创建API服务
    api = create_api_service(memory_system, preprocessor)
    
    print("\n可用端点:")
    print("  GET  /health                    - 健康检查")
    print("  POST /api/v1/memory             - 添加记忆")
    print("  POST /api/v1/recall             - 召回记忆")
    print("  POST /api/v1/fact               - 添加事实")
    print("  GET  /api/v1/facts              - 查询事实")
    print("  GET  /api/v1/stats              - 获取统计")
    print("  POST /api/v1/preprocess         - 预处理文本")
    print("\nAPI文档: http://localhost:5000/apidocs/")
    
    print("\n启动服务...")
    api.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == "__main__":
    main()
