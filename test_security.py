"""
安全功能测试
验证认证、速率限制、审计日志等安全功能
"""

import sys
import os
from typing import Dict, Any
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.security import (
    get_security_config,
    get_jwt_auth,
    get_rate_limiter,
    get_audit_log,
    SecurityHeaders
)


def test_jwt_authentication():
    """测试JWT认证"""
    print("\n" + "=" * 60)
    print("测试 JWT 认证")
    print("=" * 60)
    
    jwt_auth = get_jwt_auth()
    
    # 测试Token生成
    token, api_token = jwt_auth.generate_token("test_user_1", ["read", "write"])
    print(f"✓ Token 生成: {token[:20]}...")
    
    # 测试Token验证
    verified = jwt_auth.verify_token(token)
    assert verified is not None, "Token验证失败"
    assert verified.user_id == "test_user_1", "用户ID不匹配"
    assert verified.has_scope("read"), "Scope检查失败"
    print(f"✓ Token 验证: 通过")
    
    # 测试过期
    old_token, _ = jwt_auth.generate_token("test_user_2", expire_hours=-1)
    expired = jwt_auth.verify_token(old_token)
    assert expired is None, "过期Token不应被验证"
    print(f"✓ 过期Token: 正确拒绝")
    
    # 测试撤销
    success = jwt_auth.revoke_token(api_token.token_id)
    assert success, "Token撤销失败"
    revoked = jwt_auth.verify_token(token)
    assert revoked is None, "已撤销Token不应被验证"
    print(f"✓ Token 撤销: 通过")
    
    return True


def test_rate_limiting():
    """测试速率限制"""
    print("\n" + "=" * 60)
    print("测试速率限制")
    print("=" * 60)
    
    limiter = get_rate_limiter()
    client_id = "test_client_1"
    
    # 测试正常请求
    for i in range(50):
        allowed, remaining, reset = limiter.check_rate_limit(client_id)
        assert allowed, "正常请求不应被限制"
    
    print(f"✓ 正常请求: 通过")
    
    # 测试限制
    config = get_security_config()
    limit = config.rate_limit_requests
    
    hit_limit = False
    for i in range(limit + 10):
        allowed, remaining, reset = limiter.check_rate_limit(f"{client_id}_2")
        if not allowed:
            hit_limit = True
            print(f"✓ 速率限制触发: 在{i}次请求后")
            break
    
    assert hit_limit, "速率限制应被触发"
    print(f"✓ 速率限制: 通过")
    
    # 测试登录尝试
    user_id = "test_user_3"
    for i in range(3):
        allowed, _, _ = limiter.check_login_attempt(user_id)
        assert allowed, f"第{i+1}次登录尝试应允许"
        limiter.record_login_attempt(user_id, False)
    
    print(f"✓ 登录尝试限制: 通过")
    
    return True


def test_security_headers():
    """测试安全头"""
    print("\n" + "=" * 60)
    print("测试安全头")
    print("=" * 60)
    
    headers = SecurityHeaders.get_headers(True)
    
    assert "X-Content-Type-Options" in headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    
    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] == "DENY"
    
    assert "X-XSS-Protection" in headers
    print(f"✓ 安全头检查: 通过")
    print(f"  安全头数量: {len(headers)}")
    
    return True


def test_audit_log():
    """测试审计日志"""
    print("\n" + "=" * 60)
    print("测试审计日志")
    print("=" * 60)
    
    audit_log = get_audit_log()
    
    # 记录登录
    audit_log.log_login_attempt("test_user_a", True, "192.168.1.1")
    audit_log.log_login_attempt("test_user_b", False, "10.0.0.1")
    
    # 记录Token事件
    audit_log.log_token_creation("test_user_a", "192.168.1.1")
    audit_log.log_token_revocation("test_user_a", "token-123", "192.168.1.1")
    
    # 记录可疑活动
    audit_log.log_suspicious_activity(
        "test_user_c",
        "BRUTE_FORCE_ATTEMPT",
        {"attempts": 100},
        "8.8.8.8"
    )
    
    # 检查日志
    recent = audit_log.get_recent_logs(10)
    assert len(recent) >= 5, "日志记录失败"
    
    warnings = audit_log.get_recent_logs(10, level="WARNING")
    assert len(warnings) >= 1, "警告日志缺失"
    
    print(f"✓ 审计日志: 通过")
    print(f"  总日志数: {len(recent)}")
    
    return True


def test_integration():
    """集成测试"""
    print("\n" + "=" * 60)
    print("安全集成测试")
    print("=" * 60)
    
    # 完整流程
    audit_log = get_audit_log()
    jwt_auth = get_jwt_auth()
    limiter = get_rate_limiter()
    
    # 登录
    user_id = "integration_test_user"
    audit_log.log_login_attempt(user_id, True, "127.0.0.1")
    token, api_token = jwt_auth.generate_token(user_id)
    
    # 使用API
    for i in range(10):
        allowed, _, _ = limiter.check_rate_limit(user_id)
        assert allowed, "正常请求应通过"
    
    # 撤销Token
    jwt_auth.revoke_token(api_token.token_id)
    audit_log.log_token_revocation(user_id, api_token.token_id, "127.0.0.1")
    
    print(f"✓ 完整流程: 通过")
    return True


def main():
    """运行所有测试"""
    tests = [
        ("JWT认证", test_jwt_authentication),
        ("速率限制", test_rate_limiting),
        ("安全头", test_security_headers),
        ("审计日志", test_audit_log),
        ("集成测试", test_integration)
    ]
    
    results = []
    for name, test in tests:
        try:
            passed = test()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    for name, passed, error in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"\n{status}: {name}")
        if error:
            print(f"  错误: {error}")
    
    passed_count = sum(1 for _, p, _ in results if p)
    print(f"\n总计: {passed_count}/{len(tests)} 测试通过")
    
    return passed_count == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
