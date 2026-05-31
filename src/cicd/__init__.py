"""
CI/CD模块
提供持续集成和持续部署功能
"""
from .pipeline_manager import (
    PipelineManager,
    Pipeline,
    PipelineRun,
    Stage,
    StageResult,
    PipelineStatus,
    StageStatus,
    get_pipeline_manager,
)

from .build_system import (
    BuildSystem,
    Build,
    BuildArtifact,
    BuildStatus,
    BuildType,
    get_build_system,
)

from .deployment import (
    DeploymentManager,
    Deployment,
    DeploymentTarget,
    DeploymentStatus,
    DeploymentStrategy,
    Environment,
    get_deployment_manager,
)

__all__ = [
    'PipelineManager',
    'Pipeline',
    'PipelineRun',
    'Stage',
    'StageResult',
    'PipelineStatus',
    'StageStatus',
    'get_pipeline_manager',
    'BuildSystem',
    'Build',
    'BuildArtifact',
    'BuildStatus',
    'BuildType',
    'get_build_system',
    'DeploymentManager',
    'Deployment',
    'DeploymentTarget',
    'DeploymentStatus',
    'DeploymentStrategy',
    'Environment',
    'get_deployment_manager',
]
