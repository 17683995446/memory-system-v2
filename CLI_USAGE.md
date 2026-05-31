# 记忆系统CLI命令行工具

## 快速开始

### 安装

CLI工具无需额外安装，直接运行即可：

```bash
# 方式1: 直接运行
python -m src.cli

# 方式2: 添加可执行权限后运行
chmod +x src/cli.py
./src/cli.py

# 方式3: 使用 memory 命令 (需要配置PATH)
python -m src.cli <命令>
```

### 基本使用

```bash
# 添加记忆
python -m src.cli add "项目启动会议在2026年1月15日举行"

# 列出所有记忆
python -m src.cli list

# 搜索记忆
python -m src.cli search "项目"

# 提问问题
python -m src.cli ask "项目启动会议是什么时候？"

# 导出记忆
python -m src.cli export --format json --output memories.json

# 显示帮助
python -m src.cli --help
```

## 命令详解

### 1. 添加记忆 `add`

```bash
# 基本用法
python -m src.cli add "记忆内容"

# 指定层级和来源
python -m src.cli add "张三负责前端开发" --level l2 --source "项目文档"

# 快捷方式
python -m src.cli add "李四负责后端开发"
```

### 2. 列出记忆 `list`

```bash
# 列出所有记忆
python -m src.cli list

# 按层级筛选
python -m src.cli list --level l2

# 限制返回数量
python -m src.cli list --limit 10
```

### 3. 搜索记忆 `search`

```bash
# 基本搜索
python -m src.cli search "项目"

# 搜索多个关键词
python -m src.cli search "张三"
python -m src.cli search "前端"
```

### 4. 提问问题 `ask`

```bash
# 基本提问
python -m src.cli ask "张三负责什么工作？"

# 显示相关记忆来源
python -m src.cli ask "项目启动时间" --show-sources

# 快捷方式
python -m src.cli ask "谁负责前端开发？"
```

### 5. 导出记忆 `export`

```bash
# 导出为JSON格式
python -m src.cli export --format json

# 导出到文件
python -m src.cli export --format json --output memories.json

# 导出为Markdown
python -m src.cli export --format markdown --output memories.md

# 导出为CSV
python -m src.cli export --format csv --output memories.csv

# 导出为纯文本
python -m src.cli export --format text --output memories.txt

# 不包含元数据
python -m src.cli export --format json --no-metadata
```

### 6. 创建分享 `share`

```bash
# 创建分享（分享所有记忆）
python -m src.cli share

# 指定过期时间
python -m src.cli share --expires 48

# 指定分享类型
python -m src.cli share --type read

# 分享指定记忆
python -m src.cli share --memory-ids mem_001,mem_002
```

### 7. 统计信息 `stats`

```bash
# 显示统计信息
python -m src.cli stats
```

### 8. 配置管理 `config`

```bash
# 显示当前配置
python -m src.cli config

# 设置配置项
python -m src.cli config --set default_level=l3

# 获取单个配置项
python -m src.cli config --get default_level

# 列出所有配置
python -m src.cli config --list-all
```

### 9. 交互式模式 `interactive`

```bash
# 进入交互式模式
python -m src.cli interactive
```

在交互式模式下：

```bash
memory> add 这是我的第一条记忆
memory> list
memory> search 项目
memory> ask 项目启动时间
memory> stats
memory> help
memory> exit
```

## 配置项

CLI支持以下配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| default_level | 默认记忆层级 | l2 |
| default_source | 默认来源 | cli |
| output_format | 输出格式 (pretty/json/compact) | pretty |
| max_results | 最大返回数量 | 10 |

配置存储在 `~/.memory_cli_config.json`

## 快捷命令

在交互式模式下，可以使用以下快捷命令：

| 快捷键 | 对应命令 | 说明 |
|--------|----------|------|
| a | add | 添加记忆 |
| ls | list | 列出记忆 |
| s | search | 搜索记忆 |
| q | ask | 提问 |
| stats | stats | 统计信息 |
| export | export | 导出 |
| clear | - | 清屏 |
| help | - | 显示帮助 |
| exit | - | 退出 |

## 高级用法

### 批量添加记忆

```bash
# 从文件批量添加
echo "第一条记忆" | python -m src.cli add "$(cat)"
python -m src.cli add "第二条记忆"
python -m src.cli add "第三条记忆"
```

### 组合使用

```bash
# 添加后立即列出
python -m src.cli add "新记忆" && python -m src.cli list

# 添加后立即导出
python -m src.cli add "重要记忆" && python -m src.cli export --format json --output new_memories.json
```

### 使用管道

```bash
# 结合其他命令使用
python -m src.cli list | grep "项目"
```

## 常见问题

### Q: 如何查看帮助？
```bash
python -m src.cli --help
```

### Q: 如何设置默认层级？
```bash
python -m src.cli config --set default_level=l3
```

### Q: 如何导出特定格式？
```bash
# JSON
python -m src.cli export --format json

# Markdown (适合阅读)
python -m src.cli export --format markdown

# CSV (适合数据分析)
python -m src.cli export --format csv
```

### Q: 如何创建带过期的分享？
```bash
python -m src.cli share --expires 168  # 7天后过期
```

### Q: 交互式模式有哪些快捷键？
- `Ctrl+C`: 退出当前操作
- `Ctrl+D`: 退出交互式模式
- `↑/↓`: 命令历史（如果支持）

## 错误处理

CLI会返回以下退出码：

- `0`: 成功
- `1`: 失败（错误）

```bash
# 检查命令是否成功
python -m src.cli add "记忆" && echo "添加成功"
```
