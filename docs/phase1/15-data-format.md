# 第15步：规划数据标准化格式

## L1 数据格式
**格式**：原始精简文本
**字段**
- text: 原始文本内容
- timestamp: 时间戳
- task_id: 任务ID

**不做**：不向量化

## L2 数据格式
**格式**：统一向量化文本
**字段**
- id: 唯一标识
- text: 原始文本
- embedding: 向量编码
- metadata: 元数据（标签、时间戳等）
- access_count: 访问次数
- last_access: 最后访问时间

**切片规则**：固定长度切片（如512字符）
Embedding：开源模型统一编码

## L3 数据格式
**格式**：「实体-属性-关系」标准三元组
**字段**
- 实体 (Entity)
- 属性 (Attribute)
- 关系 (Relation)
- 置信度 (Confidence)
- 来源 (Source)
- 时间戳 (Timestamp)
- 版本号 (Version)
