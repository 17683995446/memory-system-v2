"""
自动化构建系统
用于构建、测试和打包应用程序
"""
import os
import time
import shutil
import hashlib
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class BuildStatus(Enum):
    """构建状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BuildType(Enum):
    """构建类型"""
    DEBUG = "debug"
    RELEASE = "release"
    CANARY = "canary"
    HOTFIX = "hotfix"


@dataclass
class BuildArtifact:
    """构建产物"""
    artifact_id: str
    name: str
    file_path: str
    file_size: int
    checksum: str
    created_at: datetime
    build_id: str


@dataclass
class Build:
    """构建"""
    build_id: str
    version: str
    build_type: BuildType
    status: BuildStatus
    source_dir: str
    output_dir: str
    artifacts: List[BuildArtifact] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    commit_sha: str = ""
    branch: str = "main"
    error_message: str = ""
    logs: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class BuildSystem:
    """自动化构建系统"""
    
    def __init__(self, workspace: str = None):
        self.workspace = workspace or "/tmp/memory_build"
        self.builds: Dict[str, Build] = {}
        self._build_counter = 0
        self._artifact_counter = 0
        self._ensure_workspace()
    
    def _ensure_workspace(self):
        """确保工作目录存在"""
        os.makedirs(self.workspace, exist_ok=True)
        os.makedirs(os.path.join(self.workspace, "builds"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace, "artifacts"), exist_ok=True)
    
    def create_build(
        self,
        version: str,
        build_type: BuildType = BuildType.RELEASE,
        source_dir: str = None,
        commit_sha: str = "",
        branch: str = "main"
    ) -> str:
        """创建构建"""
        self._build_counter += 1
        build_id = f"BUILD-{self._build_counter:06d}"
        
        output_dir = os.path.join(self.workspace, "builds", build_id)
        os.makedirs(output_dir, exist_ok=True)
        
        build = Build(
            build_id=build_id,
            version=version,
            build_type=build_type,
            status=BuildStatus.PENDING,
            source_dir=source_dir or os.getcwd(),
            output_dir=output_dir,
            commit_sha=commit_sha,
            branch=branch
        )
        
        self.builds[build_id] = build
        return build_id
    
    def execute_build(self, build_id: str) -> bool:
        """执行构建"""
        build = self.builds.get(build_id)
        if not build:
            return False
        
        build.status = BuildStatus.RUNNING
        build.start_time = datetime.now()
        build.logs.append(f"[{build.start_time}] Build started")
        
        start_time = time.time()
        
        try:
            # 阶段1: 清理
            build.logs.append("Cleaning output directory...")
            self._clean_output(build)
            
            # 阶段2: 编译/构建
            build.logs.append("Building source code...")
            self._compile(build)
            
            # 阶段3: 运行测试
            build.logs.append("Running tests...")
            self._run_tests(build)
            
            # 阶段4: 生成产物
            build.logs.append("Creating artifacts...")
            self._create_artifacts(build)
            
            # 阶段5: 签名/验证
            build.logs.append("Signing and verifying artifacts...")
            self._sign_artifacts(build)
            
            duration = (time.time() - start_time) * 1000
            build.duration_ms = duration
            build.end_time = datetime.now()
            build.status = BuildStatus.SUCCESS
            build.logs.append(f"[{build.end_time}] Build completed successfully in {duration:.2f}ms")
            
            return True
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            build.duration_ms = duration
            build.end_time = datetime.now()
            build.status = BuildStatus.FAILED
            build.error_message = str(e)
            build.logs.append(f"[{build.end_time}] Build failed: {e}")
            
            return False
    
    def _clean_output(self, build: Build):
        """清理输出目录"""
        if os.path.exists(build.output_dir):
            shutil.rmtree(build.output_dir)
        os.makedirs(build.output_dir)
        
        build.logs.append("Output directory cleaned")
    
    def _compile(self, build: Build):
        """编译代码"""
        # 模拟编译过程
        time.sleep(0.1)  # 模拟编译时间
        
        # 创建编译输出
        compile_output = os.path.join(build.output_dir, "compiled")
        os.makedirs(compile_output, exist_ok=True)
        
        # 模拟生成字节码
        with open(os.path.join(compile_output, "main.pyc"), 'w') as f:
            f.write("# Compiled bytecode\n")
        
        build.logs.append("Source code compiled successfully")
    
    def _run_tests(self, build: Build):
        """运行测试"""
        # 模拟测试运行
        time.sleep(0.05)
        
        test_output = os.path.join(build.output_dir, "test_results.json")
        with open(test_output, 'w') as f:
            json.dump({
                'total': 100,
                'passed': 95,
                'failed': 3,
                'skipped': 2,
                'duration_ms': 50
            }, f)
        
        build.logs.append("Tests completed: 95 passed, 3 failed, 2 skipped")
    
    def _create_artifacts(self, build: Build):
        """创建构建产物"""
        artifacts_dir = os.path.join(self.workspace, "artifacts", build.build_id)
        os.makedirs(artifacts_dir, exist_ok=True)
        
        # 创建不同的产物
        artifact_configs = [
            {"name": f"memory-{build.version}-{build.build_type.value}.tar.gz", "type": "archive"},
            {"name": f"memory-{build.version}-{build.build_type.value}.whl", "type": "wheel"},
            {"name": f"memory-{build.version}-{build.build_type.value}.zip", "type": "zip"}
        ]
        
        for config in artifact_configs:
            artifact_path = os.path.join(artifacts_dir, config["name"])
            
            # 创建空文件作为产物占位
            with open(artifact_path, 'w') as f:
                f.write(f"# {config['type']} artifact for {build.version}\n")
                f.write(f"Build ID: {build.build_id}\n")
                f.write(f"Type: {config['type']}\n")
                f.write(f"Created: {datetime.now().isoformat()}\n")
            
            file_size = os.path.getsize(artifact_path)
            checksum = self._calculate_checksum(artifact_path)
            
            self._artifact_counter += 1
            artifact_id = f"ART-{self._artifact_counter:06d}"
            
            artifact = BuildArtifact(
                artifact_id=artifact_id,
                name=config["name"],
                file_path=artifact_path,
                file_size=file_size,
                checksum=checksum,
                created_at=datetime.now(),
                build_id=build.build_id
            )
            
            build.artifacts.append(artifact)
        
        build.logs.append(f"Created {len(build.artifacts)} artifacts")
    
    def _sign_artifacts(self, build: Build):
        """签名和验证产物"""
        for artifact in build.artifacts:
            # 模拟签名
            signature_path = f"{artifact.file_path}.sig"
            with open(signature_path, 'w') as f:
                f.write(f"Signature for {artifact.checksum}\n")
            
            artifact.metadata['signed'] = True
            artifact.metadata['signature_path'] = signature_path
        
        build.logs.append("All artifacts signed and verified")
    
    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def get_build(self, build_id: str) -> Optional[Build]:
        """获取构建"""
        return self.builds.get(build_id)
    
    def cancel_build(self, build_id: str) -> bool:
        """取消构建"""
        build = self.builds.get(build_id)
        if not build or build.status not in [BuildStatus.PENDING, BuildStatus.RUNNING]:
            return False
        
        build.status = BuildStatus.CANCELLED
        build.end_time = datetime.now()
        build.error_message = "Cancelled by user"
        build.logs.append(f"[{datetime.now()}] Build cancelled")
        
        return True
    
    def get_artifact(self, artifact_id: str) -> Optional[BuildArtifact]:
        """获取构建产物"""
        for build in self.builds.values():
            for artifact in build.artifacts:
                if artifact.artifact_id == artifact_id:
                    return artifact
        return None
    
    def verify_artifact(self, artifact_id: str) -> bool:
        """验证构建产物"""
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            return False
        
        if not os.path.exists(artifact.file_path):
            return False
        
        current_checksum = self._calculate_checksum(artifact.file_path)
        return current_checksum == artifact.checksum
    
    def get_build_history(self, limit: int = 10) -> List[Build]:
        """获取构建历史"""
        builds = list(self.builds.values())
        builds.sort(key=lambda x: x.start_time or datetime.min, reverse=True)
        return builds[:limit]
    
    def generate_report(self, build_id: str) -> str:
        """生成构建报告"""
        build = self.builds.get(build_id)
        if not build:
            return "Build not found"
        
        report = []
        report.append("=" * 70)
        report.append(f"构建报告: {build.build_id}")
        report.append("=" * 70)
        report.append(f"版本: {build.version}")
        report.append(f"类型: {build.build_type.value}")
        report.append(f"状态: {build.status.value}")
        report.append(f"分支: {build.branch}")
        report.append(f"提交: {build.commit_sha}")
        
        if build.start_time:
            report.append(f"开始时间: {build.start_time}")
        if build.end_time:
            report.append(f"结束时间: {build.end_time}")
        
        report.append(f"耗时: {build.duration_ms:.2f}ms")
        
        if build.error_message:
            report.append(f"错误: {build.error_message}")
        
        report.append(f"\n构建产物 ({len(build.artifacts)}):")
        for artifact in build.artifacts:
            report.append(f"  - {artifact.name}")
            report.append(f"    大小: {artifact.file_size} bytes")
            report.append(f"    校验和: {artifact.checksum[:16]}...")
            report.append(f"    已签名: {artifact.metadata.get('signed', False)}")
        
        report.append("\n构建日志:")
        for log in build.logs[-20:]:
            report.append(f"  {log}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def cleanup_old_builds(self, days: int = 30) -> int:
        """清理旧构建"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        for build_id in list(self.builds.keys()):
            build = self.builds[build_id]
            
            if build.start_time and build.start_time < cutoff:
                # 清理产物文件
                for artifact in build.artifacts:
                    if os.path.exists(artifact.file_path):
                        os.remove(artifact.file_path)
                    sig_path = artifact.metadata.get('signature_path')
                    if sig_path and os.path.exists(sig_path):
                        os.remove(sig_path)
                
                # 清理构建目录
                if os.path.exists(build.output_dir):
                    shutil.rmtree(build.output_dir)
                
                del self.builds[build_id]
                removed_count += 1
        
        return removed_count


# 全局构建系统
_build_system = None


def get_build_system(workspace: str = None) -> BuildSystem:
    """获取构建系统"""
    global _build_system
    if _build_system is None:
        _build_system = BuildSystem(workspace)
    return _build_system
