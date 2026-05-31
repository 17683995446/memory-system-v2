"""
增强版安全API服务
包含认证、速率限制、安全头、审计日志
"""

from flask import Flask, request, jsonify
from typing import Dict, Any, Optional
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from src.security import get_jwt_auth, get_audit_log
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            get_audit_log().log(
                "WARNING", 
                "AUTH_MISSING", 
                client_ip=request.remote_addr,
                details={"endpoint": request.path}
            )
            return jsonify({'error': 'Authorization required'}), 401
        
        token = auth_header.split(' ', 1)[1]
        jwt_auth = get_jwt_auth()
        api_token = jwt_auth.verify_token(token)
        
        if not api_token:
            get_audit_log().log(
                "WARNING", 
                "AUTH_INVALID", 
                client_ip=request.remote_addr,
                details={"endpoint": request.path}
            )
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.api_token = api_token
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limited(client_id: Optional[str] = None):
    """速率限制装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from src.security import get_rate_limiter, get_audit_log
            
            cid = client_id or request.remote_addr or "unknown"
            limiter = get_rate_limiter()
            allowed, remaining, reset_sec = limiter.check_rate_limit(cid)
            
            response = None
            if not allowed:
                get_audit_log().log_rate_limit_hit(cid, request.remote_addr or "unknown")
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': reset_sec
                }), 429
            
            @wraps(f)
            def after_request(response_obj):
                response_obj.headers['X-RateLimit-Limit'] = str(limiter.config.rate_limit_requests)
                response_obj.headers['X-RateLimit-Remaining'] = str(remaining)
                response_obj.headers['X-RateLimit-Reset'] = str(reset_sec)
                return response_obj
            
            if response:
                return after_request(response[0]), response[1]
            
            result = f(*args, **kwargs)
            if isinstance(result, tuple):
                return after_request(result[0]), result[1]
            return after_request(result)
        
        return decorated_function
    return decorator


def add_security_headers(f):
    """安全头装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from src.security import SecurityHeaders, get_security_config
        
        result = f(*args, **kwargs)
        if isinstance(result, tuple):
            response = result[0]
            status = result[1]
        else:
            response = result
            status = 200
        
        headers = SecurityHeaders.get_headers(get_security_config().enable_security_headers)
        for key, value in headers.items():
            response.headers[key] = value
        
        if isinstance(result, tuple):
            return response, status
        return response
    
    return decorated_function


class SecureMemoryAPI:
    """安全增强版记忆系统API"""
    
    def __init__(self, memory_system, preprocessor=None):
        self.app = Flask(__name__)
        self.memory_system = memory_system
        self.preprocessor = preprocessor
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """设置中间件"""
        @self.app.before_request
        def before_request():
            request.start_time = time.time()
        
        @self.app.after_request
        def after_request(response):
            if hasattr(request, 'start_time'):
                duration = (time.time() - request.start_time) * 1000
                response.headers['X-Response-Time'] = f'{duration:.2f}ms'
            return response
    
    def _setup_routes(self):
        """设置路由"""
        # 公开端点（健康检查）
        self.app.add_url_rule('/health', 'health', self.health_check, methods=['GET'])
        
        # 认证端点
        self.app.add_url_rule('/api/v1/auth/login', 'login', self.login, methods=['POST'])
        self.app.add_url_rule('/api/v1/auth/token', 'create_token', self.create_token, methods=['POST'])
        self.app.add_url_rule('/api/v1/auth/token', 'revoke_token', self.revoke_token, methods=['DELETE'])
        
        # 记忆操作（需要认证）
        self.app.add_url_rule(
            '/api/v1/memory', 
            'add_memory', 
            self._wrap_secure(self.add_memory), 
            methods=['POST']
        )
        self.app.add_url_rule(
            '/api/v1/memory/<memory_id>', 
            'get_memory', 
            self._wrap_secure(self.get_memory), 
            methods=['GET']
        )
        self.app.add_url_rule(
            '/api/v1/memory/<memory_id>', 
            'delete_memory', 
            self._wrap_secure(self.delete_memory), 
            methods=['DELETE']
        )
        
        # 召回
        self.app.add_url_rule(
            '/api/v1/recall', 
            'recall_memory', 
            self._wrap_secure(self.recall_memory), 
            methods=['POST']
        )
        
        # 事实操作
        self.app.add_url_rule(
            '/api/v1/fact', 
            'add_fact', 
            self._wrap_secure(self.add_fact), 
            methods=['POST']
        )
        self.app.add_url_rule(
            '/api/v1/facts', 
            'query_facts', 
            self._wrap_secure(self.query_facts), 
            methods=['GET']
        )
        
        # 统计
        self.app.add_url_rule(
            '/api/v1/stats', 
            'get_stats', 
            self._wrap_secure(self.get_stats), 
            methods=['GET']
        )
        
        # 治理
        self.app.add_url_rule(
            '/api/v1/governance/cleanup', 
            'cleanup', 
            self._wrap_secure(self.cleanup), 
            methods=['POST']
        )
        
        # 预处理
        self.app.add_url_rule(
            '/api/v1/preprocess', 
            'preprocess', 
            self._wrap_secure(self.preprocess), 
            methods=['POST']
        )
        
        # 安全管理
        self.app.add_url_rule(
            '/api/v1/security/audit', 
            'get_audit_logs', 
            self._wrap_secure(self.get_audit_logs), 
            methods=['GET']
        )
    
    def _wrap_secure(self, f):
        """包装安全中间件"""
        return add_security_headers(rate_limited()(require_auth(f)))
    
    def health_check(self):
        """健康检查"""
        from src.security import SecurityHeaders, get_security_config
        
        response = jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'version': '1.1.0',
            'security_enabled': True
        })
        
        headers = SecurityHeaders.get_headers(get_security_config().enable_security_headers)
        for key, value in headers.items():
            response.headers[key] = value
        
        return response
    
    def login(self):
        """简单登录（生产环境应使用真实认证）"""
        from src.security import get_jwt_auth, get_audit_log, get_rate_limiter
        
        try:
            data = request.get_json() or {}
            user_id = data.get('user_id', 'anonymous')
            password = data.get('password', '')
            
            # 检查登录尝试
            allowed, remaining, reset_sec = get_rate_limiter().check_login_attempt(user_id)
            if not allowed:
                get_audit_log().log_suspicious_activity(
                    user_id,
                    "TOO_MANY_LOGIN_ATTEMPTS",
                    {},
                    request.remote_addr or "unknown"
                )
                return jsonify({
                    'error': 'Too many login attempts',
                    'retry_after': reset_sec
                }), 429
            
            # 简化的密码检查（生产环境应使用加密存储和验证）
            if password and len(password) >= 4:
                # 生成token
                token, api_token = get_jwt_auth().generate_token(user_id)
                
                get_rate_limiter().record_login_attempt(user_id, True)
                get_audit_log().log_login_attempt(user_id, True, request.remote_addr or "unknown")
                get_audit_log().log_token_creation(user_id, request.remote_addr or "unknown")
                
                return jsonify({
                    'success': True,
                    'token': token,
                    'user_id': user_id,
                    'expires_at': api_token.expires_at
                }), 200
            else:
                get_rate_limiter().record_login_attempt(user_id, False)
                get_audit_log().log_login_attempt(user_id, False, request.remote_addr or "unknown")
                return jsonify({'error': 'Invalid credentials'}), 401
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({'error': 'Login failed'}), 500
    
    def create_token(self):
        """创建Token（管理员功能）"""
        from src.security import get_jwt_auth, get_audit_log
        
        try:
            data = request.get_json() or {}
            user_id = data.get('user_id', 'anonymous')
            scopes = data.get('scopes', ['*'])
            expire_hours = data.get('expire_hours', 24)
            
            token, api_token = get_jwt_auth().generate_token(user_id, scopes, expire_hours)
            get_audit_log().log_token_creation(user_id, request.remote_addr or "unknown")
            
            return jsonify({
                'success': True,
                'token': token,
                'user_id': user_id,
                'expires_at': api_token.expires_at
            }), 201
                
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            return jsonify({'error': 'Token creation failed'}), 500
    
    def revoke_token(self):
        """撤销Token"""
        from src.security import get_jwt_auth, get_audit_log
        
        try:
            data = request.get_json() or {}
            token_id = data.get('token_id')
            
            if not token_id:
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ', 1)[1]
                    token_id = token.split('.', 1)[0]
            
            if token_id:
                user_id = request.api_token.user_id if hasattr(request, 'api_token') else 'unknown'
                success = get_jwt_auth().revoke_token(token_id)
                get_audit_log().log_token_revocation(user_id, token_id, request.remote_addr or "unknown")
                return jsonify({'success': success}), 200
            
            return jsonify({'error': 'Token ID required'}), 400
                
        except Exception as e:
            logger.error(f"Token revocation error: {e}")
            return jsonify({'error': 'Token revocation failed'}), 500
    
    def add_memory(self):
        """添加记忆"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            text = data.get('text')
            session_id = data.get('session_id', 'default')
            level = data.get('level', 'l2')
            
            if not text:
                return jsonify({'error': 'Text is required'}), 400
            
            if self.preprocessor:
                result = self.preprocessor.process(text)
                if not result['passed']:
                    return jsonify({
                        'error': 'Validation failed',
                        'reasons': result['reasons']
                    }), 400
                text = result['processed_text']
            
            memory_id = self.memory_system.add(text, session_id, level)
            
            return jsonify({
                'success': True,
                'memory_id': memory_id,
                'session_id': session_id,
                'level': level
            }), 201
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_memory(self, memory_id: str):
        """获取记忆"""
        try:
            return jsonify({
                'memory_id': memory_id,
                'message': 'Memory retrieval endpoint'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def delete_memory(self, memory_id: str):
        """删除记忆"""
        try:
            return jsonify({
                'success': True,
                'memory_id': memory_id
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def recall_memory(self):
        """召回记忆"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            query = data.get('query')
            session_id = data.get('session_id', 'default')
            
            if not query:
                return jsonify({'error': 'Query is required'}), 400
            
            results = self.memory_system.recall(query, session_id)
            
            return jsonify({
                'success': True,
                'query': query,
                'session_id': session_id,
                'results': results,
                'counts': {
                    'l1': len(results.get('l1', [])),
                    'l2': len(results.get('l2', [])),
                    'l3': len(results.get('l3', []))
                }
            })
            
        except Exception as e:
            logger.error(f"Error recalling memory: {e}")
            return jsonify({'error': str(e)}), 500
    
    def add_fact(self):
        """添加事实"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            entity = data.get('entity')
            attribute = data.get('attribute')
            value = data.get('value')
            
            if not all([entity, attribute, value]):
                return jsonify({'error': 'entity, attribute, value are required'}), 400
            
            fact_id = self.memory_system.add_fact(entity, attribute, value)
            
            return jsonify({
                'success': True,
                'fact_id': fact_id
            }), 201
            
        except Exception as e:
            logger.error(f"Error adding fact: {e}")
            return jsonify({'error': str(e)}), 500
    
    def query_facts(self):
        """查询事实"""
        try:
            entity = request.args.get('entity')
            attribute = request.args.get('attribute')
            
            return jsonify({
                'facts': [],
                'entity': entity,
                'attribute': attribute
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_stats(self):
        """获取统计信息"""
        try:
            from src.governance import get_statistics_collector
            
            stats = get_statistics_collector()
            summary = stats.get_summary()
            
            return jsonify({
                'success': True,
                'statistics': summary
            })
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    def cleanup(self):
        """清理操作"""
        try:
            data = request.get_json() or {}
            level = data.get('level', 'l2')
            
            from src.governance import get_governance
            
            governance = get_governance()
            
            if level == 'l1':
                governance.cleanup_l1_all(self.memory_system)
            elif level == 'l2':
                days = data.get('days', 30)
                governance.cleanup_l2_old(self.memory_system, days)
            
            return jsonify({
                'success': True,
                'level': level
            })
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return jsonify({'error': str(e)}), 500
    
    def preprocess(self):
        """预处理文本"""
        try:
            if not self.preprocessor:
                return jsonify({'error': 'Preprocessor not enabled'}), 400
            
            data = request.get_json()
            if not data or 'text' not in data:
                return jsonify({'error': 'Text is required'}), 400
            
            result = self.preprocessor.process(
                data['text'],
                check_hallucination=data.get('check_hallucination', False)
            )
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        except Exception as e:
            logger.error(f"Error during preprocess: {e}")
            return jsonify({'error': str(e)}), 500
    
    def get_audit_logs(self):
        """获取审计日志"""
        try:
            from src.security import get_audit_log
            
            limit = request.args.get('limit', 100, type=int)
            level = request.args.get('level')
            
            logs = get_audit_log().get_recent_logs(limit, level)
            
            return jsonify({
                'success': True,
                'logs': logs,
                'total': len(logs)
            })
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return jsonify({'error': str(e)}), 500
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """运行API服务"""
        self.app.run(host=host, port=port, debug=debug)


def create_secure_api_service(memory_system, preprocessor=None) -> SecureMemoryAPI:
    """创建安全API服务实例"""
    return SecureMemoryAPI(memory_system, preprocessor)
