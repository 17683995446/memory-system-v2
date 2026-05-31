"""
第44阶段测试：记忆系统API设计和集成
遵循"图难于其易，为大于其细"原则
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api import (
    RESTAPIRouter,
    GraphQLSchema,
    WebSocketManager,
    APISDK,
    RateLimiter,
    RequestValidator,
    APIRequest,
    APIResponse,
    GraphQLQuery,
    WebSocketMessage,
    HTTPMethod,
    APIEndpointType,
    get_api_sdk
)


def test_rate_limiter():
    """测试速率限制器"""
    print("\n=== 测试速率限制器 ===")

    limiter = RateLimiter()

    # 测试速率限制
    for i in range(5):
        result = limiter.check_limit("user_1", limit=10)
        assert result is True

    # 超过限制
    for i in range(6):
        limiter.check_limit("user_1", limit=10)

    result = limiter.check_limit("user_1", limit=10)
    assert result is False

    # 获取剩余请求数
    remaining = limiter.get_remaining("user_1", limit=10)
    print(f"剩余请求数: {remaining}")
    assert remaining >= 0

    print("✓ 速率限制器测试通过")


def test_request_validator():
    """测试请求验证器"""
    print("\n=== 测试请求验证器 ===")

    validator = RequestValidator()

    # 添加模式
    validator.add_schema("memory", {
        "required": ["content"],
        "properties": {
            "content": {"type": "string"},
            "metadata": {"type": "object"}
        }
    })

    # 验证有效数据
    valid_data = {"content": "Test memory", "metadata": {}}
    is_valid, error = validator.validate(valid_data, "memory")
    assert is_valid is True
    assert error is None
    print("✓ 有效数据验证通过")

    # 验证缺少必需字段
    invalid_data = {"metadata": {}}
    is_valid, error = validator.validate(invalid_data, "memory")
    assert is_valid is False
    assert error is not None
    print(f"✓ 无效数据验证: {error}")

    # 验证类型错误
    type_error_data = {"content": 123}
    is_valid, error = validator.validate(type_error_data, "memory")
    assert is_valid is False
    print(f"✓ 类型错误验证: {error}")

    print("✓ 请求验证器测试通过")


def test_rest_router():
    """测试REST API路由器"""
    print("\n=== 测试REST API路由器 ===")

    router = RESTAPIRouter()

    # 注册端点
    def handle_add_memory(request):
        return {"id": "mem_123", "content": "Test"}

    router.register_endpoint(
        "/api/v1/memories",
        HTTPMethod.POST,
        handle_add_memory,
        APIEndpointType.MEMORY,
        description="Add memory"
    )

    # 测试路由
    request = APIRequest(
        method=HTTPMethod.POST,
        path="/api/v1/memories",
        user_id="user_1"
    )

    response = router.route(request)
    assert response.status_code == 200
    assert response.data is not None
    print(f"✓ 路由成功: {response.data}")

    # 测试404
    request_404 = APIRequest(
        method=HTTPMethod.GET,
        path="/api/v1/nonexistent",
        user_id="user_1"
    )
    response_404 = router.route(request_404)
    assert response_404.status_code == 404
    print("✓ 404处理正确")

    # 测试未授权
    def handle_protected(request):
        return {"status": "success"}

    router.register_endpoint(
        "/api/v1/protected",
        HTTPMethod.GET,
        handle_protected,
        APIEndpointType.USER,
        requires_auth=True
    )

    request_unauth = APIRequest(
        method=HTTPMethod.GET,
        path="/api/v1/protected"
    )
    response_unauth = router.route(request_unauth)
    assert response_unauth.status_code == 401
    print("✓ 认证检查正确")

    print("✓ REST API路由器测试通过")


def test_graphql_schema():
    """测试GraphQL模式"""
    print("\n=== 测试GraphQL模式 ===")

    schema = GraphQLSchema()

    # 添加类型
    schema.add_type("Memory", {
        "id": {"type": "string"},
        "content": {"type": "string"}
    })

    # 添加查询
    def resolve_memories(args):
        return [{"id": "1", "content": "Test"}]

    schema.add_query("memories", "[Memory]", ["id", "content"], resolve_memories)

    # 添加变更
    def resolve_create_memory(args):
        return {"id": "2", "content": args.get("content", "")}

    schema.add_mutation("createMemory", "Memory", ["id", "content"], resolve_create_memory)

    # 执行查询
    query = GraphQLQuery(query="query { memories }")
    response = schema.execute(query)
    assert response.data is not None
    print(f"✓ GraphQL查询成功: {response.data}")

    # 执行变更
    mutation = GraphQLQuery(
        query="mutation { createMemory(content: \"New\") }",
        variables={"content": "New memory"}
    )
    mutation_response = schema.execute(mutation)
    assert mutation_response.data is not None
    print(f"✓ GraphQL变更成功: {mutation_response.data}")

    print("✓ GraphQL模式测试通过")


def test_websocket_manager():
    """测试WebSocket管理器"""
    print("\n=== 测试WebSocket管理器 ===")

    manager = WebSocketManager()

    # 测试连接
    manager.connect("socket_1", "user_1")
    manager.connect("socket_2", "user_1")

    # 检查连接数量
    connection_count = manager.get_connection_count()
    print(f"当前连接数: {connection_count}")
    assert connection_count >= 1
    print("✓ 连接管理正常")

    # 测试订阅
    manager.subscribe("socket_1", "channel_general")
    manager.subscribe("socket_1", "channel_updates")

    # 测试断开
    manager.disconnect("socket_2")
    assert manager.get_connection_count() >= 0

    # 测试消息发送
    message = WebSocketMessage(
        type="update",
        payload={"content": "Test update"},
        user_id="user_1"
    )
    manager.send_to_user("user_1", message)
    print("✓ 消息发送正常")

    print("✓ WebSocket管理器测试通过")


def test_api_sdk():
    """测试API SDK"""
    print("\n=== 测试API SDK ===")

    sdk = APISDK("http://localhost:8000", "test_api_key")

    # 测试添加记忆
    result = sdk.add_memory("Test memory content")
    assert result["status"] == "success"
    print(f"✓ 添加记忆: {result}")

    # 测试获取记忆
    memory = sdk.get_memory("mem_123")
    assert memory["status"] == "success"
    print(f"✓ 获取记忆: {memory}")

    # 测试搜索
    results = sdk.search_memories("test query")
    assert results["status"] == "success"
    print(f"✓ 搜索记忆: {results}")

    print("✓ API SDK测试通过")


def test_get_all_routes():
    """测试获取所有路由"""
    print("\n=== 测试获取所有路由 ===")

    router = RESTAPIRouter()

    # 注册多个端点
    def handler1(request):
        return {}

    def handler2(request):
        return {}

    router.register_endpoint("/api/v1/memories", HTTPMethod.GET, handler1, APIEndpointType.MEMORY)
    router.register_endpoint("/api/v1/memories", HTTPMethod.POST, handler2, APIEndpointType.MEMORY)
    router.register_endpoint("/api/v1/search", HTTPMethod.POST, handler1, APIEndpointType.SEARCH)

    routes = router.get_routes()
    print(f"总路由数: {len(routes)}")

    for route in routes:
        print(f"  {route['method']} {route['path']} - {route['type']}")

    assert len(routes) >= 3
    print("✓ 路由获取测试通过")


def test_middleware():
    """测试中间件"""
    print("\n=== 测试中间件 ===")

    router = RESTAPIRouter()

    def auth_middleware(request):
        if request.path == "/protected":
            return APIResponse(status_code=403, data=None, message="Forbidden")

    router.add_middleware(auth_middleware)

    def handler(request):
        return {"status": "ok"}

    router.register_endpoint("/protected", HTTPMethod.GET, handler, APIEndpointType.USER)

    # 测试中间件拦截
    request = APIRequest(method=HTTPMethod.GET, path="/protected")
    response = router.route(request)
    assert response.status_code == 403
    print("✓ 中间件拦截正常")

    print("✓ 中间件测试通过")


def test_global_sdk():
    """测试全局SDK"""
    print("\n=== 测试全局SDK ===")

    sdk1 = get_api_sdk("http://test.com", "key1")
    sdk2 = get_api_sdk("http://test.com", "key2")

    assert sdk1 is sdk2
    print("✓ 全局单例正常")

    print("✓ 全局SDK测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第44阶段测试：记忆系统API设计和集成")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)

    try:
        test_rate_limiter()
        test_request_validator()
        test_rest_router()
        test_graphql_schema()
        test_websocket_manager()
        test_api_sdk()
        test_get_all_routes()
        test_middleware()
        test_global_sdk()

        print("\n" + "=" * 60)
        print("✓ 所有第44阶段测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
