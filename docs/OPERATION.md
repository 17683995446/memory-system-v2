# 运维手册

基于第一性原理的Agent可靠记忆系统运维指南

## 目录

1. [日常运维](#日常运维)
2. [监控与告警](#监控与告警)
3. [备份与恢复](#备份与恢复)
4. [性能优化](#性能优化)
5. [常见运维任务](#常见运维任务)

---

## 日常运维

### 检查系统状态

```python
# 检查统计信息
from src.governance import get_statistics_collector

stats = get_statistics_collector()
summary = stats.get_summary()
print(f"总操作: {summary['total_operations']}")
print(f"成功率: {summary['success_rate']:.2%}")
```

### 查看异常
```python
from src.governance import get_anomaly_marker

anomalies = get_anomaly_marker()
unresolved = anomalies.get_unresolved_anomalies()
for a in unresolved:
    print(f"{a['id']} - {a['description']}")
```

### 清理过期记忆
```python
from src.governance import get_governance
from src.memory import get_memory_system

memory = get_memory_system()
governance = get_governance()

# 清理L1
governance.cleanup_l1_all(memory)

# 清理L2过期
governance.cleanup_l2_old(memory)
```

---

## 监控与告警

### 关键指标监控

| 指标 | 推荐阈值 | 说明 |
|-----|---------|------|
| 错误率 | < 1% | 高于此值应告警 |
| 平均延迟 | < 100ms | 响应延迟 |
| L1条目数 | < 配置最大值 | L1内存使用 |
| L2条目数 | 定期查看 | L2增长趋势 |

### 日志监控

```bash
# 实时查看日志
tail -f logs/memory_system_*.log

# 搜索错误
grep "ERROR" logs/memory_system_*.log
```

### 告警条件

建议配置以下告警：
1. 错误率 > 5%
2. L2条目快速增长（> 1000/小时）
3. 系统无操作 > 1小时

---

## 备份与恢复

### 数据备份

```bash
# 备份L3事实数据
cp -r data/ backup/$(date +%Y%m%d)/

# 备份版本历史
cp -r data/versions/ backup/$(date +%Y%m%d)/
```

### 数据恢复

```bash
# 从备份恢复
cp -r backup/YYYYMMDD/* data/
```

### 建议备份策略

| 类型 | 频率 | 保留期限 |
|-----|------|---------|
| L3事实 | 每日 | 30天 |
| 版本历史 | 每周 | 90天 |
| 完整备份 | 每月 | 180天 |

---

## 性能优化

### 优化L2检索速度

如启用faiss：
```bash
pip install faiss-cpu
```

### 内存优化

调整配置：
```python
from src.config import get_settings

settings = get_settings()
# 减少L1最大条目
settings.l1_max_items = 50
```

### 清理冗余

```python
from src.governance import get_governance
from src.memory import get_memory_system

governance = get_governance()
memory = get_memory_system()

# 清理低频L2
governance.cleanup_l2_low_freq(memory, min_access=5)
```

---

## 常见运维任务

### 任务1：添加事实规则
```python
from src.memory import get_memory_system

memory = get_memory_system()
memory.add_fact("规则", "必须", "保护用户隐私")
```

### 任务2：修正错误记忆
```python
from src.governance import get_memory_correction

correction = get_memory_correction()
version_id = correction.submit_correction(
    "item_123",
    {"value": "correct_value"},
    "纠正错误数据",
    "admin"
)
```

### 任务3：调整遗忘策略
```python
from src.governance import get_forget_thresholds

thresholds = get_forget_thresholds()
thresholds.l2_max_days = 60  # 延长到60天
```

### 任务4：导出统计数据
```python
from src.governance import get_statistics_collector

stats = get_statistics_collector()
summary = stats.get_summary()
import json
print(json.dumps(summary, indent=2))
```

---

## 附录：紧急处理

### 系统异常
1. 检查日志 `logs/`
2. 查看统计信息
3. 检查未解决异常
4. 必要时重启应用

### 数据损坏
1. 停止应用
2. 从备份恢复
3. 检查版本历史
4. 重新启动

### 性能严重下降
1. 检查L1条目数
2. 清理过期L2
3. 检查是否有频繁的大召回
4. 考虑优化配置
