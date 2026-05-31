# 第17步：敲定召回权重排序固定算法

## 权重排序算法（固定规则，无概率随机）

### 排序优先级（从高到低）
1. **任务匹配度（最高）**
   - 与当前任务关键词匹配程度
   - 匹配规则：精确匹配 > 部分匹配 > 无匹配

2. **信息时效性**
   - 时间越新权重越高
   - 按时间戳倒序排列

3. **使用频次**
   - 访问次数越高权重越高
   - 按访问次数倒序排列

### 排序算法伪代码
```python
def sort_memories(memories, current_task):
    # 第一层排序：任务匹配度
    memories.sort(key=lambda x: calculate_match_score(x, current_task), reverse=True)
    # 第二层排序：时效性
    memories.sort(key=lambda x: x.timestamp, reverse=True)
    # 第三层排序：使用频次
    memories.sort(key=lambda x: x.access_count, reverse=True)
    return memories
```

### 限流熔断规则
- 单次召回总量不超过N条（如10条）
- L1最多M条（如3条）
- L2最多K条（如5条）
- L3最多P条（如2条）

### 冲突去重规则
- 内容相似度超过阈值则去重
- 保留最新版本
- 保留高优先级层级内容
