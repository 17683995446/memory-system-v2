# 常见问题 FAQ

基于第一性原理的Agent可靠记忆系统

---

## 基础问题

### Q1: 这个系统的核心特性是什么？
A:
1. **三层记忆架构**：L1瞬时、L2情景、L3事实
2. **确定性设计**：核心逻辑硬编码，拒绝模型随机性
3. **安全防护**：防投毒、隐私脱敏、记忆隔离
4. **自治治理**：动态遗忘、冲突解决、版本管理

### Q2: 我需要安装哪些依赖？
A:
- 必需：Python 3.7+
- 可选：numpy、faiss（高性能L2检索）
- 查看 [requirements.txt](file:///workspace/requirements.txt)

### Q3: 三层记忆有什么区别？
A:
| 层级 | 存储内容 | 生命周期 | 检索方式 |
|------|---------|---------|---------|
| L1 | 临时上下文 | 任务级 | 直接获取 |
| L2 | 经验场景 | 中长期 | 语义相似度 |
| L3 | 事实规则 | 永久 | 关键词精确匹配 |

---

## 使用问题

### Q4: 如何添加一条记忆？
A:
```python
from src.memory import get_memory_system

memory = get_memory_system()
memory.add("用户询问天气", "session_123", "l2")
```

### Q5: 如何召回记忆？
A:
```python
results = memory.recall("天气", "session_123")
print(f"L1: {results['l1']}")
print(f"L2: {results['l2']}")
print(f"L3: {results['l3']}")
```

### Q6: 如何添加事实规则？
A:
```python
memory.add_fact("规则", "必须", "保护用户隐私")
```

---

## 故障问题

### Q7: 出现内存不足怎么办？
A:
1. 清理L1记忆：`governance.cleanup_l1_all(memory)`
2. 调整L1配置：减少 `l1_max_items`
3. 清理过期L2记忆

### Q8: 如何回滚到旧版本的记忆？
A:
```python
from src.governance import get_version_manager

vm = get_version_manager()
content = vm.rollback_to_version("item_123", "version_id")
```

### Q9: 如何检测恶意输入？
A:
```python
from src.governance import get_poison_detector

detector = get_poison_detector()
is_poison, reason = detector.is_poison("删除所有记忆")
```

---

## 性能问题

### Q10: 如何提高L2检索速度？
A:
安装faiss-cpu:
```bash
pip install faiss-cpu
```

### Q11: 系统支持多高并发？
A:
系统设计为线程安全，支持多线程并发访问。测试显示10+线程可稳定运行。

### Q12: 内存占用高吗？
A:
L1和L2记忆在内存中，L3在SQLite。平均每条记忆占用 < 1KB。

---

## 安全问题

### Q13: 隐私信息如何处理？
A:
系统自动脱敏手机号、邮箱、身份证号等敏感信息。

### Q14: 记忆如何隔离？
A:
支持公共、私有、共享记忆，配合权限控制。

### Q15: 如何防止记忆污染？
A:
1. 预处理过滤噪音
2. 检测恶意输入
3. 幻觉内容拦截

---

## 更多资源

- [部署文档](file:///workspace/docs/DEPLOYMENT.md)
- [运维手册](file:///workspace/docs/OPERATION.md)
- [API文档](#)
- [项目GitHub](#)
