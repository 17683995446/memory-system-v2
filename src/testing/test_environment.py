"""
测试环境管理器
用于管理和隔离测试环境
"""
import os
import shutil
import tempfile
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class EnvironmentType(Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ResourceType(Enum):
    """资源类型"""
    DATABASE = "database"
    CACHE = "cache"
    FILE = "file"
    CONFIG = "config"
    NETWORK = "network"


@dataclass
class EnvironmentConfig:
    """环境配置"""
    env_type: EnvironmentType
    name: str
    base_path: str
    resources: Dict[ResourceType, Dict] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


@dataclass
class TestResource:
    """测试资源"""
    resource_id: str
    resource_type: ResourceType
    name: str
    config: Dict
    created_at: float
    is_active: bool = True
    cleanup_func: Optional[Callable] = None


class TestEnvironmentManager:
    """测试环境管理器"""
    
    def __init__(self):
        self.environments: Dict[str, EnvironmentConfig] = {}
        self.resources: Dict[str, TestResource] = {}
        self._resource_counter = 0
        self._env_counter = 0
        
        # 创建默认测试环境
        self._create_default_environments()
    
    def _create_default_environments(self):
        """创建默认环境"""
        # 测试环境
        test_path = os.path.join(tempfile.gettempdir(), "memory_test_env")
        os.makedirs(test_path, exist_ok=True)
        
        self.create_environment(
            name="default_test",
            env_type=EnvironmentType.TESTING,
            base_path=test_path
        )
    
    def create_environment(
        self,
        name: str,
        env_type: EnvironmentType,
        base_path: Optional[str] = None,
        variables: Dict[str, str] = None
    ) -> str:
        """创建测试环境"""
        self._env_counter += 1
        env_id = f"ENV-{self._env_counter:04d}"
        
        if base_path is None:
            base_path = os.path.join(tempfile.gettempdir(), f"memory_env_{env_id}")
        
        os.makedirs(base_path, exist_ok=True)
        
        config = EnvironmentConfig(
            env_type=env_type,
            name=name,
            base_path=base_path,
            variables=variables or {}
        )
        
        self.environments[env_id] = config
        return env_id
    
    def get_environment(self, env_id: str) -> Optional[EnvironmentConfig]:
        """获取环境配置"""
        return self.environments.get(env_id)
    
    def setup_resource(
        self,
        env_id: str,
        resource_type: ResourceType,
        name: str,
        config: Dict = None
    ) -> Optional[str]:
        """设置测试资源"""
        env = self.environments.get(env_id)
        if not env:
            return None
        
        self._resource_counter += 1
        resource_id = f"RES-{self._resource_counter:04d}"
        
        resource_config = config or {}
        
        # 根据资源类型创建资源
        if resource_type == ResourceType.FILE:
            resource_path = os.path.join(env.base_path, name)
            os.makedirs(os.path.dirname(resource_path), exist_ok=True)
            with open(resource_path, 'w') as f:
                f.write(resource_config.get('content', ''))
            resource_config['path'] = resource_path
        
        elif resource_type == ResourceType.CACHE:
            # 创建内存缓存模拟
            cache_data = {}
            resource_config['data'] = cache_data
        
        resource = TestResource(
            resource_id=resource_id,
            resource_type=resource_type,
            name=name,
            config=resource_config,
            created_at=time.time()
        )
        
        self.resources[resource_id] = resource
        return resource_id
    
    def get_resource(self, resource_id: str) -> Optional[TestResource]:
        """获取测试资源"""
        return self.resources.get(resource_id)
    
    def cleanup_resource(self, resource_id: str) -> bool:
        """清理测试资源"""
        resource = self.resources.get(resource_id)
        if not resource:
            return False
        
        try:
            # 调用自定义清理函数
            if resource.cleanup_func:
                resource.cleanup_func()
            
            # 根据资源类型清理
            if resource.resource_type == ResourceType.FILE:
                path = resource.config.get('path')
                if path and os.path.exists(path):
                    os.remove(path)
            
            elif resource.resource_type == ResourceType.DATABASE:
                # 数据库清理逻辑
                pass
            
            resource.is_active = False
            return True
            
        except Exception:
            return False
    
    def cleanup_environment(self, env_id: str) -> bool:
        """清理整个测试环境"""
        env = self.environments.get(env_id)
        if not env:
            return False
        
        # 清理所有相关资源
        env_resources = [
            rid for rid, r in self.resources.items()
            if r.config.get('env_id') == env_id
        ]
        
        for rid in env_resources:
            self.cleanup_resource(rid)
        
        # 删除环境目录
        try:
            if os.path.exists(env.base_path):
                shutil.rmtree(env.base_path)
            del self.environments[env_id]
            return True
        except Exception:
            return False
    
    def snapshot_environment(self, env_id: str) -> Optional[Dict]:
        """创建环境快照"""
        env = self.environments.get(env_id)
        if not env:
            return None
        
        snapshot = {
            'env_id': env_id,
            'name': env.name,
            'type': env.env_type.value,
            'timestamp': time.time(),
            'resources': [],
            'files': {}
        }
        
        # 快照资源
        for rid, resource in self.resources.items():
            if resource.is_active:
                snapshot['resources'].append({
                    'resource_id': rid,
                    'type': resource.resource_type.value,
                    'name': resource.name
                })
        
        # 快照文件
        if os.path.exists(env.base_path):
            for root, dirs, files in os.walk(env.base_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, env.base_path)
                    try:
                        with open(file_path, 'r') as f:
                            snapshot['files'][rel_path] = f.read()
                    except Exception:
                        pass
        
        return snapshot
    
    def restore_environment(self, snapshot: Dict) -> Optional[str]:
        """恢复环境快照"""
        env_id = self.create_environment(
            name=f"{snapshot['name']}_restored",
            env_type=EnvironmentType[snapshot['type'].upper()],
            base_path=os.path.join(tempfile.gettempdir(), f"restored_{snapshot['env_id']}")
        )
        
        env = self.environments[env_id]
        
        # 恢复文件
        for rel_path, content in snapshot.get('files', {}).items():
            file_path = os.path.join(env.base_path, rel_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
        
        return env_id
    
    def set_environment_variable(self, env_id: str, key: str, value: str) -> bool:
        """设置环境变量"""
        env = self.environments.get(env_id)
        if not env:
            return False
        
        env.variables[key] = value
        return True
    
    def get_environment_variable(self, env_id: str, key: str) -> Optional[str]:
        """获取环境变量"""
        env = self.environments.get(env_id)
        if not env:
            return None
        
        return env.variables.get(key)
    
    def apply_environment(self, env_id: str) -> bool:
        """应用环境配置到当前进程"""
        env = self.environments.get(env_id)
        if not env:
            return False
        
        # 设置环境变量
        for key, value in env.variables.items():
            os.environ[key] = value
        
        return True
    
    def generate_report(self) -> str:
        """生成环境报告"""
        report = []
        report.append("=" * 70)
        report.append("测试环境报告")
        report.append("=" * 70)
        
        report.append(f"\n环境总数: {len(self.environments)}")
        
        for env_id, env in self.environments.items():
            report.append(f"\n环境: {env.name} ({env_id})")
            report.append(f"  类型: {env.env_type.value}")
            report.append(f"  路径: {env.base_path}")
            report.append(f"  变量数: {len(env.variables)}")
        
        report.append(f"\n资源总数: {len(self.resources)}")
        
        by_type = {}
        for rid, resource in self.resources.items():
            rtype = resource.resource_type.value
            if rtype not in by_type:
                by_type[rtype] = []
            by_type[rtype].append(resource)
        
        for rtype, resources in by_type.items():
            report.append(f"\n{rtype}: {len(resources)}")
            for resource in resources:
                status = "活跃" if resource.is_active else "已清理"
                report.append(f"  - {resource.name} ({status})")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def export_config(self, env_id: str, filepath: str) -> bool:
        """导出环境配置"""
        env = self.environments.get(env_id)
        if not env:
            return False
        
        config = {
            'env_id': env_id,
            'name': env.name,
            'type': env.env_type.value,
            'base_path': env.base_path,
            'variables': env.variables,
            'metadata': env.metadata
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return True
    
    def import_config(self, filepath: str) -> Optional[str]:
        """导入环境配置"""
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        env_id = self.create_environment(
            name=config['name'],
            env_type=EnvironmentType[config['type'].upper()],
            base_path=config['base_path'],
            variables=config.get('variables', {})
        )
        
        return env_id


# 全局测试环境管理器
_env_manager = None


def get_env_manager() -> TestEnvironmentManager:
    """获取测试环境管理器"""
    global _env_manager
    if _env_manager is None:
        _env_manager = TestEnvironmentManager()
    return _env_manager
