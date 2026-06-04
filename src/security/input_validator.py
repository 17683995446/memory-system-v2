"""
输入验证与安全防护模块
基于第一性原理：不信任任何输入，所有外部输入必须验证和净化
"""

import re
import html
import unicodedata
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from urllib.parse import urlparse


class ValidationError(Exception):
    """验证错误"""
    def __init__(self, field: str, reason: str, value: Any = None):
        self.field = field
        self.reason = reason
        self.value = value
        super().__init__(f"[{field}] {reason}")


class InputType(Enum):
    """输入类型"""
    TEXT = "text"
    HTML = "html"
    URL = "url"
    EMAIL = "email"
    IDENTIFIER = "identifier"
    COMMAND = "command"
    PATH = "path"
    JSON = "json"
    SQL = "sql"


class InputValidator:
    """输入验证器 - 所有外部输入的入口关卡"""

    # SQL注入危险关键词
    SQL_DANGEROUS_KEYWORDS: Set[str] = {
        'drop', 'delete', 'truncate', 'insert', 'update', 'alter',
        'exec', 'execute', 'union', 'select', 'from', 'where',
        'or', 'and', 'not', 'null', 'cast', 'convert',
        'xp_', 'sp_', 'sysobjects', 'syscolumns'
    }

    # SQL注入危险模式
    SQL_DANGEROUS_PATTERNS = [
        r"(\b(union|select|insert|update|delete|drop|alter)\b.*\b(from|into|table|database)\b)",
        r"(\b(or|and)\b\s+\d+\s*=\s*\d+)",
        r"(--|#|/\*|\*/)",
        r"(\bxp_|\bsp_)[a-z]+",
        r"(exec\s*\(|execute\s*\()",
        r"(cast\s*\(|convert\s*\()",
    ]

    # XSS危险模式
    XSS_PATTERNS = [
        r"<script[^>]*>[\s\S]*?</script>",
        r"javascript:",
        r"on\w+\s*=\s*['\"]",
        r"on\w+\s*=\s*[^\s>]*",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<form[^>]*>",
        r"<input[^>]*type\s*=\s*['\"]?hidden",
        r"<img[^>]*on\w+",
        r"<body[^>]*on\w+",
        r"<[^>]+\son\w+",
        r"expression\s*\(",
        r"url\s*\(",
        r"eval\s*\(",
    ]

    # 路径遍历危险模式
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.",
        r"^/",
        r"[a-zA-Z]:\\\\",
        r"%2e%2e",
        r"\x00",
    ]

    # 命令注入危险字符
    COMMAND_INJECTION_CHARS = {';', '&', '|', '`', '$', '(', ')', '<', '>', '\\', '{', '}'}

    # 最大长度限制
    MAX_TEXT_LENGTH = 10 * 1024 * 1024  # 10MB
    MAX_IDENTIFIER_LENGTH = 256
    MAX_URL_LENGTH = 2048
    MAX_EMAIL_LENGTH = 254

    @classmethod
    def validate_text(
        cls,
        value: Any,
        field_name: str = "text",
        max_length: Optional[int] = None,
        min_length: int = 1,
        allow_empty: bool = False,
        strip: bool = True
    ) -> str:
        """验证文本输入"""
        if value is None:
            if allow_empty:
                return ""
            raise ValidationError(field_name, "不能为空", value)

        if not isinstance(value, str):
            value = str(value)

        if strip:
            value = value.strip()

        if not value and not allow_empty:
            raise ValidationError(field_name, "不能为空字符串", value)

        max_len = max_length or cls.MAX_TEXT_LENGTH
        if len(value) > max_len:
            raise ValidationError(field_name, f"超过最大长度{max_len}", value[:100])

        if len(value) < min_length:
            raise ValidationError(field_name, f"小于最小长度{min_length}", value)

        # 检查控制字符（除了常见的换行制表）
        for i, char in enumerate(value):
            if unicodedata.category(char) == 'Cc' and char not in '\t\n\r':
                raise ValidationError(field_name, f"包含非法控制字符(位置{i})", value[:100])

        return value

    @classmethod
    def validate_identifier(
        cls,
        value: Any,
        field_name: str = "identifier",
        pattern: Optional[str] = None
    ) -> str:
        """验证标识符（只允许字母数字下划线连字符）"""
        value = cls.validate_text(value, field_name, max_length=cls.MAX_IDENTIFIER_LENGTH)

        if pattern:
            if not re.match(pattern, value):
                raise ValidationError(field_name, "格式不符合要求", value)
        else:
            # 默认只允许安全字符
            if not re.match(r'^[a-zA-Z0-9_\-]+$', value):
                raise ValidationError(field_name, "只能包含字母、数字、下划线和连字符", value)

        return value

    @classmethod
    def validate_email(cls, value: Any, field_name: str = "email") -> str:
        """验证邮箱"""
        value = cls.validate_text(value, field_name, max_length=cls.MAX_EMAIL_LENGTH)

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            raise ValidationError(field_name, "邮箱格式不正确", value)

        return value.lower()

    @classmethod
    def validate_url(cls, value: Any, field_name: str = "url", allowed_schemes: Optional[Set[str]] = None) -> str:
        """验证URL"""
        value = cls.validate_text(value, field_name, max_length=cls.MAX_URL_LENGTH)

        try:
            parsed = urlparse(value)
        except Exception:
            raise ValidationError(field_name, "URL格式不正确", value)

        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(field_name, "URL必须包含协议和主机", value)

        schemes = allowed_schemes or {'http', 'https'}
        if parsed.scheme.lower() not in schemes:
            raise ValidationError(field_name, f"只允许协议: {schemes}", value)

        # 检查URL中的XSS
        if cls.contains_xss(value):
            raise ValidationError(field_name, "URL包含危险内容", value)

        return value

    @classmethod
    def validate_path(cls, value: Any, field_name: str = "path", base_dir: Optional[str] = None) -> str:
        """验证文件路径，防止路径遍历"""
        value = cls.validate_text(value, field_name, max_length=4096)

        # 检查路径遍历
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value):
                raise ValidationError(field_name, "路径包含非法字符", value)

        # 如果指定了基础目录，确保路径在基础目录内
        if base_dir:
            import os
            full_path = os.path.abspath(os.path.join(base_dir, value))
            base_abs = os.path.abspath(base_dir)
            if not full_path.startswith(base_abs):
                raise ValidationError(field_name, "路径超出允许范围", value)

        return value

    @classmethod
    def contains_sql_injection(cls, value: str) -> Tuple[bool, Optional[str]]:
        """检查是否包含SQL注入"""
        value_lower = value.lower()

        for pattern in cls.SQL_DANGEROUS_PATTERNS:
            match = re.search(pattern, value_lower, re.IGNORECASE)
            if match:
                return True, f"检测到SQL注入模式: {match.group()[:50]}"

        return False, None

    @classmethod
    def contains_xss(cls, value: str) -> Tuple[bool, Optional[str]]:
        """检查是否包含XSS攻击"""
        for pattern in cls.XSS_PATTERNS:
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                return True, f"检测到XSS模式: {match.group()[:50]}"

        return False, None

    @classmethod
    def contains_command_injection(cls, value: str) -> Tuple[bool, Optional[str]]:
        """检查是否包含命令注入"""
        dangerous_count = sum(1 for c in value if c in cls.COMMAND_INJECTION_CHARS)
        if dangerous_count > len(value) * 0.1:  # 超过10%的危险字符
            return True, "检测到命令注入特征"

        # 检查常见的命令注入模式
        cmd_patterns = [
            r"\b(sh|bash|cmd|powershell|python|ruby|perl)\s+-[a-z]+",
            r"\b(curl|wget|nc|netcat)\s+",
            r"\b(rm|del|rmdir|mkfs)\s+-[rf]+",
        ]
        for pattern in cmd_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True, "检测到命令执行特征"

        return False, None

    @classmethod
    def sanitize_html(cls, value: str, allowed_tags: Optional[Set[str]] = None) -> str:
        """净化HTML内容"""
        if not value:
            return value

        # 先转义所有HTML
        escaped = html.escape(value)

        # 如果允许特定标签，再选择性恢复
        if allowed_tags:
            for tag in allowed_tags:
                # 恢复允许的标签（简化实现）
                escaped = escaped.replace(f"&lt;{tag}&gt;", f"<{tag}>")
                escaped = escaped.replace(f"&lt;/{tag}&gt;", f"</{tag}>")

        return escaped

    @classmethod
    def sanitize_sql_like(cls, value: str) -> str:
        """净化SQL LIKE参数"""
        # 转义SQL LIKE特殊字符
        value = value.replace('\\', '\\\\')
        value = value.replace('%', '\\%')
        value = value.replace('_', '\\_')
        return value

    @classmethod
    def validate_memory_content(cls, content: Any) -> str:
        """验证记忆内容 - 综合安全检查"""
        # 基础文本验证
        text = cls.validate_text(content, "content", max_length=cls.MAX_TEXT_LENGTH)

        # SQL注入检查
        has_sql, reason = cls.contains_sql_injection(text)
        if has_sql:
            raise ValidationError("content", f"包含SQL注入风险: {reason}", text[:100])

        # XSS检查
        has_xss, reason = cls.contains_xss(text)
        if has_xss:
            raise ValidationError("content", f"包含XSS攻击风险: {reason}", text[:100])

        # 命令注入检查
        has_cmd, reason = cls.contains_command_injection(text)
        if has_cmd:
            raise ValidationError("content", f"包含命令注入风险: {reason}", text[:100])

        return text

    @classmethod
    def validate_api_request(cls, body: Dict[str, Any]) -> Dict[str, Any]:
        """验证API请求体"""
        validated = {}

        # 验证content
        if 'content' in body:
            validated['content'] = cls.validate_memory_content(body['content'])

        # 验证task_id
        if 'task_id' in body:
            validated['task_id'] = cls.validate_identifier(body['task_id'], "task_id")

        # 验证level
        if 'level' in body:
            level = str(body['level']).lower()
            if level not in {'l1', 'l2', 'l3'}:
                raise ValidationError("level", "必须是 l1/l2/l3 之一", level)
            validated['level'] = level

        # 验证source
        if 'source' in body:
            validated['source'] = cls.validate_text(body['source'], "source", max_length=256)

        # 验证query
        if 'query' in body:
            validated['query'] = cls.validate_text(body['query'], "query", max_length=1000)

        # 验证question
        if 'question' in body:
            validated['question'] = cls.validate_text(body['question'], "question", max_length=2000)

        # 验证id
        if 'id' in body:
            validated['id'] = cls.validate_identifier(body['id'], "id")

        # 验证format
        if 'format' in body:
            fmt = str(body['format']).lower()
            if fmt not in {'json', 'text', 'markdown', 'csv'}:
                raise ValidationError("format", "必须是 json/text/markdown/csv 之一", fmt)
            validated['format'] = fmt

        return validated


class SecurityHeaders:
    """安全响应头"""

    DEFAULT_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; object-src 'none'",
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }

    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """获取默认安全头"""
        return cls.DEFAULT_HEADERS.copy()
