"""
安全API服务运行示例
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory import get_memory_system
from src.preprocessing import get_preprocessor
from src.api.secure_api import create_secure_api_service


def main():
    """启动安全API服务"""
    print("=" * 70)
    print("启动 安全增强版 Agent记忆系统 API服务")
    print("=" * 70)
    print("\n安全功能:")
    print("  - JWT Token 认证")
    print("  - API 速率限制")
    print("  - 安全头防护")
    print("  - 安全审计日志")
    print("\n端点:")
    print("  POST /api/v1/auth/login          - 登录获取Token")
    print("  POST /api/v1/auth/token          - 创建Token")
    print("  DELETE /api/v1/auth/token        - 撤销Token")
    print("  GET /health                      - 健康检查")
    print("  POST /api/v1/memory              - 添加记忆")
    print("  POST /api/v1/recall              - 召回记忆")
    print("  POST /api/v1/fact                - 添加事实")
    print("  GET /api/v1/stats                - 统计信息")
    print("  GET /api/v1/security/audit       - 审计日志")
    
    print("\n快速测试:")
    print("  # 1. 登录获取Token")
    print("  curl -X POST http://localhost:5000/api/v1/auth/login \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"user_id\":\"test_user\",\"password\":\"1234\"}'")
    print("\n  # 2. 使用Token访问受保护端点")
    print("  curl -X POST http://localhost:5000/api/v1/memory \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print("    -d '{\"text\":\"测试记忆\",\"session_id\":\"test\"}'")
    
    memory_system = get_memory_system()
    preprocessor = get_preprocessor()
    api = create_secure_api_service(memory_system, preprocessor)
    
    print("\n启动服务...")
    api.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == "__main__":
    main()
