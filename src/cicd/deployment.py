"""
自动化部署系统
用于管理和执行应用程序部署
"""
import time
import json
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class DeploymentStatus(Enum):
    """部署状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class DeploymentStrategy(Enum):
    """部署策略"""
    IMMEDIATE = "immediate"      # 立即部署
    CANARY = "canary"           # 灰度部署
    BLUE_GREEN = "blue_green"   # 蓝绿部署
    ROLLING = "rolling"         # 滚动部署


class Environment(Enum):
    """部署环境"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DeploymentTarget:
    """部署目标"""
    target_id: str
    name: str
    host: str
    port: int
    path: str
    weight: int = 100  # 用于灰度部署
    health_check_url: str = ""
    is_active: bool = True
    metadata: Dict = field(default_factory=dict)


@dataclass
class Deployment:
    """部署"""
    deployment_id: str
    version: str
    environment: Environment
    strategy: DeploymentStrategy
    status: DeploymentStatus
    targets: List[DeploymentTarget]
    build_id: str = ""
    rollback_from: str = ""  # 回滚来源
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    health_check_passes: int = 0
    health_check_fails: int = 0
    error_message: str = ""
    logs: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class DeploymentManager:
    """自动化部署管理器"""
    
    def __init__(self):
        self.deployments: Dict[str, Deployment] = {}
        self.environments: Dict[str, Dict[str, Any]] = {
            "development": {
                "name": "Development",
                "servers": ["dev-server-1", "dev-server-2"],
                "config": {}
            },
            "testing": {
                "name": "Testing",
                "servers": ["test-server-1", "test-server-2"],
                "config": {}
            },
            "staging": {
                "name": "Staging",
                "servers": ["staging-server-1", "staging-server-2", "staging-server-3"],
                "config": {}
            },
            "production": {
                "name": "Production",
                "servers": ["prod-server-1", "prod-server-2", "prod-server-3", "prod-server-4"],
                "config": {}
            }
        }
        self._deployment_counter = 0
        self._lock = threading.Lock()
    
    def create_deployment(
        self,
        version: str,
        environment: Environment,
        strategy: DeploymentStrategy = DeploymentStrategy.IMMEDIATE,
        targets: List[DeploymentTarget] = None,
        build_id: str = ""
    ) -> str:
        """创建部署"""
        with self._lock:
            self._deployment_counter += 1
            deployment_id = f"DEPLOY-{self._deployment_counter:06d}"
            
            # 默认目标
            if not targets:
                targets = self._create_default_targets(environment)
            
            deployment = Deployment(
                deployment_id=deployment_id,
                version=version,
                environment=environment,
                strategy=strategy,
                status=DeploymentStatus.PENDING,
                targets=targets,
                build_id=build_id
            )
            
            self.deployments[deployment_id] = deployment
            return deployment_id
    
    def _create_default_targets(self, environment: Environment) -> List[DeploymentTarget]:
        """创建默认部署目标"""
        targets = []
        env_name = environment.value
        
        for i in range(1, 3):
            target_id = f"TARGET-{env_name}-{i:02d}"
            target = DeploymentTarget(
                target_id=target_id,
                name=f"{env_name}-node-{i}",
                host=f"{env_name}-server-{i}.local",
                port=8080,
                path=f"/app/{env_name}",
                weight=50,
                health_check_url=f"http://{env_name}-server-{i}.local:8080/health"
            )
            targets.append(target)
        
        return targets
    
    def execute_deployment(self, deployment_id: str) -> bool:
        """执行部署"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False
        
        deployment.status = DeploymentStatus.RUNNING
        deployment.start_time = datetime.now()
        deployment.logs.append(f"[{deployment.start_time}] Deployment started")
        
        start_time = time.time()
        
        try:
            if deployment.strategy == DeploymentStrategy.IMMEDIATE:
                success = self._deploy_immediate(deployment)
            elif deployment.strategy == DeploymentStrategy.CANARY:
                success = self._deploy_canary(deployment)
            elif deployment.strategy == DeploymentStrategy.BLUE_GREEN:
                success = self._deploy_blue_green(deployment)
            elif deployment.strategy == DeploymentStrategy.ROLLING:
                success = self._deploy_rolling(deployment)
            else:
                success = self._deploy_immediate(deployment)
            
            duration = (time.time() - start_time) * 1000
            deployment.duration_ms = duration
            deployment.end_time = datetime.now()
            
            if success:
                deployment.status = DeploymentStatus.SUCCESS
                deployment.logs.append(f"[{deployment.end_time}] Deployment completed successfully")
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.logs.append(f"[{deployment.end_time}] Deployment failed")
            
            return success
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            deployment.duration_ms = duration
            deployment.end_time = datetime.now()
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            deployment.logs.append(f"[{deployment.end_time}] Deployment failed: {e}")
            
            return False
    
    def _deploy_immediate(self, deployment: Deployment) -> bool:
        """立即部署到所有目标"""
        deployment.logs.append("Using immediate deployment strategy")
        
        for target in deployment.targets:
            deployment.logs.append(f"Deploying to {target.name} ({target.host})...")
            
            # 模拟部署过程
            time.sleep(0.1)
            
            # 模拟健康检查
            if self._health_check(target):
                deployment.health_check_passes += 1
                deployment.logs.append(f"  ✓ {target.name} is healthy")
            else:
                deployment.health_check_fails += 1
                deployment.logs.append(f"  ✗ {target.name} health check failed")
        
        return deployment.health_check_fails == 0
    
    def _deploy_canary(self, deployment: Deployment) -> bool:
        """灰度部署"""
        deployment.logs.append("Using canary deployment strategy")
        
        # 1. 先部署到小部分（灰度）
        canary_targets = [t for t in deployment.targets if t.weight < 50]
        if not canary_targets:
            canary_targets = [deployment.targets[0]] if deployment.targets else []
        
        deployment.logs.append(f"Deploying to {len(canary_targets)} canary target(s)...")
        
        for target in canary_targets:
            deployment.logs.append(f"Deploying to canary: {target.name}...")
            time.sleep(0.1)
            
            if self._health_check(target):
                deployment.health_check_passes += 1
                deployment.logs.append(f"  ✓ Canary {target.name} is healthy")
            else:
                deployment.health_check_fails += 1
                deployment.logs.append(f"  ✗ Canary {target.name} health check failed")
        
        # 2. 等待稳定期
        deployment.logs.append("Waiting for canary stabilization...")
        time.sleep(0.1)
        
        # 3. 全量部署
        deployment.logs.append("Rolling out to all targets...")
        remaining_targets = [t for t in deployment.targets if t not in canary_targets]
        
        for target in remaining_targets:
            deployment.logs.append(f"Deploying to {target.name}...")
            time.sleep(0.1)
            
            if self._health_check(target):
                deployment.health_check_passes += 1
            else:
                deployment.health_check_fails += 1
        
        return deployment.health_check_fails == 0
    
    def _deploy_blue_green(self, deployment: Deployment) -> bool:
        """蓝绿部署"""
        deployment.logs.append("Using blue-green deployment strategy")
        
        # 1. 部署到绿色环境
        deployment.logs.append("Deploying to green environment...")
        green_targets = deployment.targets[:len(deployment.targets)//2] if len(deployment.targets) > 1 else deployment.targets
        
        for target in green_targets:
            deployment.logs.append(f"Deploying to green: {target.name}...")
            time.sleep(0.1)
            
            if self._health_check(target):
                deployment.health_check_passes += 1
        
        # 2. 验证绿色环境
        deployment.logs.append("Validating green environment...")
        time.sleep(0.1)
        
        # 3. 切换流量
        deployment.logs.append("Switching traffic to green...")
        
        # 4. 部署到蓝色环境
        deployment.logs.append("Deploying to blue environment...")
        blue_targets = deployment.targets[len(deployment.targets)//2:]
        
        for target in blue_targets:
            deployment.logs.append(f"Deploying to blue: {target.name}...")
            time.sleep(0.1)
            
            if self._health_check(target):
                deployment.health_check_passes += 1
            else:
                deployment.health_check_fails += 1
        
        return deployment.health_check_fails == 0
    
    def _deploy_rolling(self, deployment: Deployment) -> bool:
        """滚动部署"""
        deployment.logs.append("Using rolling deployment strategy")
        
        # 逐个部署
        for i, target in enumerate(deployment.targets, 1):
            deployment.logs.append(f"Deploying to {target.name} ({i}/{len(deployment.targets)})...")
            
            # 模拟部署
            time.sleep(0.1)
            
            # 健康检查
            if self._health_check(target):
                deployment.health_check_passes += 1
                deployment.logs.append(f"  ✓ {target.name} is healthy")
                
                # 确保旧实例仍在运行
                if i > 1:
                    deployment.logs.append(f"  ✓ Previous instances still running")
            else:
                deployment.health_check_fails += 1
                deployment.logs.append(f"  ✗ {target.name} health check failed")
                
                # 遇到失败可以考虑回滚
                if deployment.metadata.get('rollback_on_failure', False):
                    deployment.logs.append("Rolling back due to failure...")
                    return False
        
        return deployment.health_check_fails == 0
    
    def _health_check(self, target: DeploymentTarget) -> bool:
        """健康检查"""
        # 模拟健康检查
        time.sleep(0.01)
        # 90%成功率模拟
        return hash(target.target_id) % 10 != 0
    
    def rollback_deployment(self, deployment_id: str, from_version: str = "") -> bool:
        """回滚部署"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False
        
        deployment.logs.append(f"[{datetime.now()}] Starting rollback...")
        
        # 创建回滚部署记录
        rollback_deployment_id = self.create_deployment(
            version=from_version or deployment.metadata.get('previous_version', 'unknown'),
            environment=deployment.environment,
            strategy=DeploymentStrategy.IMMEDIATE,
            targets=deployment.targets.copy(),
            build_id=""
        )
        
        rollback_deployment = self.deployments[rollback_deployment_id]
        rollback_deployment.rollback_from = deployment_id
        rollback_deployment.metadata['is_rollback'] = True
        
        # 执行回滚
        success = self.execute_deployment(rollback_deployment_id)
        
        if success:
            deployment.status = DeploymentStatus.ROLLED_BACK
            deployment.logs.append(f"[{datetime.now()}] Rollback completed")
        else:
            deployment.logs.append(f"[{datetime.now()}] Rollback failed")
        
        return success
    
    def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """获取部署"""
        return self.deployments.get(deployment_id)
    
    def cancel_deployment(self, deployment_id: str) -> bool:
        """取消部署"""
        deployment = self.deployments.get(deployment_id)
        if not deployment or deployment.status not in [DeploymentStatus.PENDING, DeploymentStatus.RUNNING]:
            return False
        
        deployment.status = DeploymentStatus.CANCELLED
        deployment.end_time = datetime.now()
        deployment.error_message = "Cancelled by user"
        deployment.logs.append(f"[{datetime.now()}] Deployment cancelled")
        
        return True
    
    def get_deployment_history(self, environment: Environment = None, limit: int = 10) -> List[Deployment]:
        """获取部署历史"""
        deployments = list(self.deployments.values())
        
        if environment:
            deployments = [d for d in deployments if d.environment == environment]
        
        deployments.sort(key=lambda x: x.start_time or datetime.min, reverse=True)
        return deployments[:limit]
    
    def get_active_deployments(self, environment: Environment = None) -> List[Deployment]:
        """获取活跃部署"""
        deployments = [
            d for d in self.deployments.values()
            if d.status in [DeploymentStatus.RUNNING, DeploymentStatus.PENDING]
        ]
        
        if environment:
            deployments = [d for d in deployments if d.environment == environment]
        
        return deployments
    
    def generate_report(self, deployment_id: str) -> str:
        """生成部署报告"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return "Deployment not found"
        
        report = []
        report.append("=" * 70)
        report.append(f"部署报告: {deployment.deployment_id}")
        report.append("=" * 70)
        report.append(f"版本: {deployment.version}")
        report.append(f"环境: {deployment.environment.value}")
        report.append(f"策略: {deployment.strategy.value}")
        report.append(f"状态: {deployment.status.value}")
        
        if deployment.start_time:
            report.append(f"开始时间: {deployment.start_time}")
        if deployment.end_time:
            report.append(f"结束时间: {deployment.end_time}")
        
        report.append(f"耗时: {deployment.duration_ms:.2f}ms")
        report.append(f"健康检查: {deployment.health_check_passes} 通过, {deployment.health_check_fails} 失败")
        
        if deployment.error_message:
            report.append(f"错误: {deployment.error_message}")
        
        report.append(f"\n部署目标 ({len(deployment.targets)}):")
        for target in deployment.targets:
            status = "活跃" if target.is_active else "非活跃"
            report.append(f"  - {target.name} ({target.host}:{target.port}) [{status}]")
        
        report.append("\n部署日志:")
        for log in deployment.logs[-20:]:
            report.append(f"  {log}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)


# 全局部署管理器
_deployment_manager = None


def get_deployment_manager() -> DeploymentManager:
    """获取部署管理器"""
    global _deployment_manager
    if _deployment_manager is None:
        _deployment_manager = DeploymentManager()
    return _deployment_manager
