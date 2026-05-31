# 第31阶段交付：CLI命令行工具

## 阶段概述

遵循"图难于其易，为大于其细"的原则，本阶段实现了完整的CLI命令行工具，让用户可以通过命令行高效地使用记忆系统的所有功能，提供了一种轻量级、灵活的交互方式。

## 核心功能

### 1. 命令行接口

- **简单易用**: 直观的命令行语法
- **模块化设计**: 每个命令独立实现
- **标准化参数**: 使用标准argparse库
- **丰富帮助**: 内置详细帮助信息

### 2. 记忆管理命令

- **添加记忆**: `add` - 添加新记忆到系统
- **列出记忆**: `list` - 列出所有记忆，支持层级筛选
- **获取记忆**: `get` - 获取单个记忆详情
- **删除记忆**: `delete` - 删除指定记忆
- **搜索记忆**: `search` - 关键词搜索

### 3. 问答系统命令

- **提问问题**: `ask` - 向记忆系统提问
- **多轮对话**: 支持对话上下文
- **来源显示**: 可选显示相关记忆来源

### 4. 数据导出命令

- **多格式导出**: JSON、Text、Markdown、CSV
- **文件输出**: 支持导出到文件
- **元数据控制**: 可选包含或排除元数据

### 5. 分享功能

- **创建分享**: `share` - 创建记忆分享
- **过期时间**: 支持设置过期时间
- **分享类型**: 支持不同分享类型

### 6. 配置管理

- **查看配置**: 显示当前配置
- **设置配置**: 修改配置项
- **持久化**: 配置保存到文件

### 7. 交互式模式

- **实时交互**: 进入交互式会话
- **快捷命令**: 支持缩写命令
- **命令历史**: 历史命令支持
- **会话管理**: 退出和清屏功能

## 实现文件

| 文件 | 说明 |
|------|------|
| [src/cli.py](../../src/cli.py) | CLI核心实现 |
| [test_phase31_cli.py](../../test_phase31_cli.py) | CLI功能测试 |
| [CLI_USAGE.md](../../CLI_USAGE.md) | CLI使用文档 |
| [docs/phase31/final_delivery.md](./final_delivery.md) | 本文档 |

## 使用示例

### 基础操作

```bash
# 添加记忆
python -m src.cli add "项目启动会议在2026年1月15日举行"

# 列出记忆
python -m src.cli list

# 搜索记忆
python -m src.cli search "项目"

# 提问问题
python -m src.cli ask "项目启动会议是什么时候？"
```

### 高级操作

```bash
# 导出记忆为JSON
python -m src.cli export --format json --output memories.json

# 导出为Markdown（适合阅读）
python -m src.cli export --format markdown --output memories.md

# 创建24小时有效的分享
python -m src.cli share --expires 24

# 设置默认层级
python -m src.cli config --set default_level=l3

# 查看统计信息
python -m src.cli stats
```

### 交互式模式

```bash
# 进入交互式模式
python -m src.cli interactive

# 在交互式模式下
memory> add 这是我的第一条记忆
memory> list
memory> search 项目
memory> ask 项目启动时间
memory> stats
memory> help
memory> exit
```

## 命令详解

### add - 添加记忆

```bash
# 基本用法
python -m src.cli add "记忆内容"

# 指定层级和来源
python -m src.cli add "张三负责前端开发" --level l2 --source "项目文档"

参数:
  content          记忆内容（必需）
  --level, -l      记忆层级 (l1/l2/l3)
  --source, -s     记忆来源
```

### list - 列出记忆

```bash
# 列出所有记忆
python -m src.cli list

# 按层级筛选
python -m src.cli list --level l2

# 限制返回数量
python -m src.cli list --limit 10

参数:
  --level, -l      按层级筛选
  --limit, -n      返回数量限制
```

### search - 搜索记忆

```bash
# 基本搜索
python -m src.cli search "项目"

参数:
  query            搜索关键词（必需）
```

### ask - 提问问题

```bash
# 基本提问
python -m src.cli ask "张三负责什么工作？"

# 显示相关记忆
python -m src.cli ask "项目启动时间" --show-sources

参数:
  question         问题内容（必需）
  --show-sources, -v  显示相关记忆来源
```

### export - 导出记忆

```bash
# JSON格式
python -m src.cli export --format json

# 导出到文件
python -m src.cli export --format json --output memories.json

# Markdown格式
python -m src.cli export --format markdown --output memories.md

# CSV格式
python -m src.cli export --format csv --output memories.csv

参数:
  --format, -f     导出格式 (json/text/markdown/csv)
  --output, -o     输出文件路径
  --no-metadata    不包含元数据
```

### share - 创建分享

```bash
# 创建分享
python -m src.cli share

# 指定过期时间和类型
python -m src.cli share --expires 48 --type read

参数:
  --memory-ids     记忆ID列表（逗号分隔）
  --type, -t        分享类型 (read)
  --expires, -e    过期时间（小时）
```

### stats - 统计信息

```bash
# 显示统计
python -m src.cli stats
```

### config - 配置管理

```bash
# 查看配置
python -m src.cli config

# 设置配置
python -m src.cli config --set default_level=l3

# 获取单项配置
python -m src.cli config --get default_level

参数:
  --set            设置配置项 (key=value)
  --get            获取配置项
  --list-all       列出所有配置
```

### interactive - 交互式模式

```bash
# 进入交互式模式
python -m src.cli interactive

快捷命令:
  a <内容>         = add <内容>
  ls               = list
  s <关键词>        = search <关键词>
  q <问题>         = ask <问题>
  clear            = 清屏
  help             = 显示帮助
  exit             = 退出
```

## 配置项

CLI支持以下配置项，存储在 `~/.memory_cli_config.json`:

| 配置项 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| default_level | 默认记忆层级 | l2 | l1/l2/l3 |
| default_source | 默认来源 | cli | web/api |
| output_format | 输出格式 | pretty | pretty/json/compact |
| max_results | 最大返回数量 | 10 | 1-100 |

## 设计原则

本阶段严格遵循基于第一性原理的设计准则：

1. **简洁性**: 命令简单直观，易于记忆
2. **一致性**: 所有命令使用统一的参数风格
3. **实用性**: 提供最常用的功能
4. **可扩展性**: 易于添加新命令
5. **用户友好**: 详细的帮助信息和错误提示

## 测试覆盖

运行CLI功能测试：

```bash
python test_phase31_cli.py
```

测试结果：
- ✓ CLI初始化和配置管理
- ✓ 添加记忆功能
- ✓ 列出记忆功能
- ✓ 搜索记忆功能
- ✓ 提问问题功能
- ✓ 统计信息显示
- ✓ 多格式导出功能（JSON、Markdown）
- ✓ 创建分享功能
- ✓ 删除记忆功能

## 验收标准

| 标准 | 状态 |
|------|------|
| CLI架构设计合理 | ✓ 完成 |
| 记忆管理命令完整 | ✓ 完成 |
| 问答系统命令正常 | ✓ 完成 |
| 导出分享命令正常 | ✓ 完成 |
| 交互式模式功能完整 | ✓ 完成 |
| 配置管理功能正常 | ✓ 完成 |
| 所有测试通过 | ✓ 完成 |
| CLI文档完善 | ✓ 完成 |

## 与API的关系

CLI和Web API互补使用：

| 特性 | CLI | Web API |
|------|-----|---------|
| 交互方式 | 命令行 | HTTP请求 |
| 适用场景 | 快速操作、脚本集成 | 远程访问、程序集成 |
| 性能 | 即时响应 | 需要网络 |
| 功能 | 基本操作 | 完整功能 |

## 总结

第31阶段圆满完成！我们实现了：

1. **完整的CLI工具**: 9个核心命令，覆盖所有基本功能
2. **交互式模式**: 实时会话，支持快捷命令
3. **配置管理**: 灵活的个性化配置
4. **多格式导出**: JSON、Text、Markdown、CSV
5. **完善的文档**: 详细的使用指南和示例
6. **全面的测试**: 所有功能测试通过

CLI命令行工具提供了一种轻量级、高效的方式来使用记忆系统，特别适合快速操作和脚本自动化场景！

---

**遵循原则**: 图难于其易，为大于其细。天下难事，必作于易；天下大事，必作于细。
