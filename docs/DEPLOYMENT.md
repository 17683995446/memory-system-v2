# 部署文档

基于第一性原理的Agent可靠记忆系统部署指南

## 目录

1. [环境要求](#环境要求)
2. [快速开始](#快速开始)
3. [详细部署步骤](#详细部署步骤)
4. [配置说明](#配置说明)
5. [故障排查](#故障排查)

---

## 环境要求

### 软件依赖
- Python 3.7+
- 可选依赖：
  - numpy (向量运算，L2记忆)
  - faiss (向量索引，高性能L2检索)

### 硬件要求
- 内存：最少 512MB，推荐 2GB+
- 存储：最少 100MB 可用空间
- CPU：单核即可，推荐 2核+

---

## 快速开始

### 1. 克隆或下载项目
```bash
cd /path/to/project
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 创建必要的目录
```bash
mkdir -p data logs
```

### 4. 运行测试
```bash
# 运行所有阶段测试
python test_memory.py
python test_phase3.py
python test_phase4.py
python test_phase5_unit_tests.py
python test_phase5_integration.py
python test_phase5_performance.py
```

### 5. 在代码中使用
```python
from src.memory import get_memory_system
from src.preprocessing import get_preprocessor

# 初始化
memory = get_memory_system()
preprocessor = get_preprocessor()

# 添加记忆
result = preprocessor.process("用户询问今天天气")
if result['passed']:
    memory.add(result['processed_text'], "session_123")

# 召回记忆
results = memory.recall("天气", "session_123")
print(f"L1: {results['l1']}")
print(f"L2: {results['l2']}")
print(f"L3: {results['l3']}")
```

---

## 详细部署步骤

### 步骤1：准备项目目录

```bash
# 创建项目目录
mkdir -p /opt/memory_system
cd /opt/memory_system

# 复制项目文件
# ...

# 创建数据和日志目录
mkdir -p data logs data/versions
```

### 步骤2：设置Python环境

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 步骤3：配置系统

编辑配置文件（可选），使用默认配置即可直接运行：
```python
from src.config import get_settings

settings = get_settings()
# 可修改配置后保存
```

### 步骤4：启动服务（可选）

系统设计为库形式使用，可集成到您的应用中，或创建简单的服务：

```python
# app.py - 简单的服务示例
from src.memory import get_memory_system

memory = get_memory_system()

# 在您的应用中集成...
```

---

## 配置说明

### 核心配置项

所有配置均位于 `src/config/settings.py`

| 配置项 | 默认值 | 说明 |
|-------|-------|------|
| `data_dir` | "./data" | 数据存储目录 |
| `log_dir` | "./logs" | 日志目录 |
| `l1_max_items` | 100 | L1记忆最大条目数 |
| `l1_ttl_seconds` | 3600 | L1记忆生存时间（秒） |
| `l2_cleanup_days` | 30 | L2清理周期（天） |
| `l2_min_access_count` | 3 | L2最低访问次数 |

### 遗忘阈值配置

在 `advanced_governance.py` 中配置：

```python
thresholds = get_forget_thresholds()
thresholds.l1_ttl_seconds = 7200  # 2小时
thresholds.l2_max_days = 60  # 60天
thresholds.l2_min_access_count = 5  # 5次
```

### 日志配置

系统使用Python标准日志模块，可通过环境变量配置：

```bash
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

---

## 故障排查

### 常见问题

#### 问题1：导入错误
```
ModuleNotFoundError: No module named 'src'
```
**解决**: 确保项目根目录在PYTHONPATH中
```bash
export PYTHONPATH=/path/to/project:$PYTHONPATH
```

#### 问题2：FAISS导入失败
系统会自动降级使用简单的List存储，无需特殊处理。如果需要高性能，安装faiss：
```bash
pip install faiss-cpu
```

#### 问题3：权限错误
确保数据和日志目录可写
```bash
chmod 755 data logs
```

### 查看日志
```bash
tail -f logs/*.log
```

### 获取支持
如遇问题，请检查：
1. Python版本 >= 3.7
2. 所有依赖已安装
3. 目录权限正确
4. 查看日志文件了解详情

---

## 附录

### 目录结构
```
memory_system/
├── src/                    # 源代码
│   ├── memory/            # 记忆模块
│   ├── preprocessing/     # 预处理模块
│   ├── governance/        # 治理模块
│   ├── iteration/         # 复盘模块
│   ├── config/            # 配置
│   ├── utils/             # 工具
│   └── testing/           # 测试框架
├── data/                  # 数据存储
├── logs/                  # 日志文件
├── docs/                  # 文档
├── requirements.txt       # 依赖
└── test_*.py             # 测试脚本
```
