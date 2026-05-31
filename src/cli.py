"""
记忆系统CLI命令行工具
提供命令行接口访问记忆系统功能
"""

import sys
import os
import json
import time
import argparse
from typing import Dict, List, Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory import get_memory_system
from src.qa import MemoryQASystem
from src.export import MemoryExporter, MemorySharer


class MemoryCLI:
    """记忆系统CLI"""

    def __init__(self):
        self.memory_system = get_memory_system()
        self.qa_system = MemoryQASystem()
        self.exporter = MemoryExporter()
        self.sharer = MemorySharer()
        self.current_memories: List[Dict] = []
        self.conversation_id = None
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置"""
        config_path = os.path.expanduser("~/.memory_cli_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "default_level": "l2",
            "default_source": "cli",
            "output_format": "pretty",
            "max_results": 10,
        }

    def _save_config(self):
        """保存配置"""
        config_path = os.path.expanduser("~/.memory_cli_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    def _format_output(self, data: Any, format_type: Optional[str] = None) -> str:
        """格式化输出"""
        format_type = format_type or self.config.get("output_format", "pretty")

        if format_type == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == "compact":
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        else:  # pretty
            if isinstance(data, dict):
                lines = []
                for key, value in data.items():
                    if isinstance(value, list):
                        lines.append(f"{key}:")
                        for item in value:
                            lines.append(f"  - {item}")
                    else:
                        lines.append(f"{key}: {value}")
                return '\n'.join(lines)
            elif isinstance(data, list):
                lines = []
                for i, item in enumerate(data, 1):
                    if isinstance(item, dict):
                        lines.append(f"{i}. ")
                        for key, value in item.items():
                            lines.append(f"   {key}: {value}")
                    else:
                        lines.append(f"{i}. {item}")
                return '\n'.join(lines)
            else:
                return str(data)

    def cmd_add(self, args):
        """添加记忆"""
        content = args.content

        if not content:
            print("错误: 记忆内容不能为空")
            return 1

        level = args.level or self.config["default_level"]
        source = args.source or self.config["default_source"]

        # 添加到记忆系统
        mem_id = self.memory_system.add(content, source, level)

        # 保存到当前内存
        memory_item = {
            "id": mem_id,
            "text": content,
            "source": source,
            "level": level,
            "timestamp": time.time(),
        }
        self.current_memories.append(memory_item)

        print(f"✓ 记忆添加成功")
        print(f"  ID: {mem_id}")
        print(f"  层级: {level}")
        print(f"  来源: {source}")
        print(f"  内容: {content[:50]}{'...' if len(content) > 50 else ''}")

        return 0

    def cmd_list(self, args):
        """列出记忆"""
        level = args.level
        limit = args.limit or self.config["max_results"]

        # 获取记忆
        memories = self.current_memories

        if level:
            memories = [m for m in memories if m.get("level") == level]

        # 限制数量
        memories = memories[-limit:]

        if not memories:
            print("没有找到记忆")
            return 0

        print(f"共 {len(memories)} 条记忆:")
        print("=" * 70)

        for i, mem in enumerate(memories, 1):
            print(f"\n{i}. [{mem.get('level', 'unknown')}] {mem.get('id', 'N/A')}")
            print(f"   内容: {mem.get('text', '')[:60]}{'...' if len(mem.get('text', '')) > 60 else ''}")
            print(f"   来源: {mem.get('source', 'unknown')}")
            if 'timestamp' in mem:
                time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(mem['timestamp']))
                print(f"   时间: {time_str}")

        return 0

    def cmd_get(self, args):
        """获取单个记忆"""
        if not args.id:
            print("错误: 需要指定记忆ID")
            return 1

        memory = next((m for m in self.current_memories if m['id'] == args.id), None)

        if not memory:
            print(f"未找到记忆: {args.id}")
            return 1

        print("记忆详情:")
        print("=" * 70)
        print(self._format_output(memory))

        return 0

    def cmd_delete(self, args):
        """删除记忆"""
        if not args.id:
            print("错误: 需要指定记忆ID")
            return 1

        initial_count = len(self.current_memories)
        self.current_memories = [m for m in self.current_memories if m['id'] != args.id]

        if len(self.current_memories) < initial_count:
            print(f"✓ 记忆已删除: {args.id}")
            return 0
        else:
            print(f"未找到记忆: {args.id}")
            return 1

    def cmd_search(self, args):
        """搜索记忆"""
        if not args.query:
            print("错误: 需要指定搜索关键词")
            return 1

        query = args.query.lower()
        results = [m for m in self.current_memories if query in m.get('text', '').lower()]

        if not results:
            print(f"未找到包含 '{args.query}' 的记忆")
            return 0

        print(f"找到 {len(results)} 条相关记忆:")
        print("=" * 70)

        for i, mem in enumerate(results, 1):
            print(f"\n{i}. [{mem.get('level', 'unknown')}] {mem.get('id', 'N/A')}")
            print(f"   内容: {mem.get('text', '')[:80]}{'...' if len(mem.get('text', '')) > 80 else ''}")

        return 0

    def cmd_ask(self, args):
        """提问问题"""
        if not args.question:
            print("错误: 需要指定问题")
            return 1

        question = args.question

        # 调用QA系统
        result = self.qa_system.ask(
            question,
            self.current_memories,
            self.conversation_id
        )

        self.conversation_id = result['conversation_id']

        print(f"\n问题: {question}")
        print("=" * 70)
        print(f"回答: {result['answer']['answer']}")
        print("=" * 70)
        print(f"答案质量: {result['answer']['quality'].value}")
        print(f"置信度: {result['answer']['confidence']:.2f}")
        print(f"检索到: {len(result['retrieved_memories'])} 条相关记忆")
        print(f"对话ID: {self.conversation_id}")

        if args.show_sources and result['retrieved_memories']:
            print("\n相关记忆:")
            for i, item in enumerate(result['retrieved_memories'], 1):
                print(f"  {i}. {item['memory']['text'][:60]}...")

        return 0

    def cmd_export(self, args):
        """导出记忆"""
        format_type = args.format or "json"
        include_metadata = not args.no_metadata

        try:
            if format_type == "json":
                content = self.exporter.export_to_json(self.current_memories, include_metadata=include_metadata)
            elif format_type == "text":
                content = self.exporter.export_to_text(self.current_memories)
            elif format_type == "markdown":
                content = self.exporter.export_to_markdown(self.current_memories)
            elif format_type == "csv":
                content = self.exporter.export_to_csv(self.current_memories)
            else:
                print(f"不支持的格式: {format_type}")
                return 1

            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ 导出成功: {args.output}")
                print(f"  格式: {format_type}")
                print(f"  记忆数: {len(self.current_memories)}")
            else:
                print(content)

            return 0
        except Exception as e:
            print(f"导出失败: {e}")
            return 1

    def cmd_share(self, args):
        """创建分享"""
        memory_ids = args.memory_ids.split(',') if args.memory_ids else []
        share_type = args.type or "read"
        expires_hours = args.expires or 24

        memories_to_share = []
        if memory_ids:
            memories_to_share = [m for m in self.current_memories if m['id'] in memory_ids]
        else:
            memories_to_share = self.current_memories

        if not memories_to_share:
            print("错误: 没有可分享的记忆")
            return 1

        try:
            share_id = self.sharer.create_share(
                memory_ids=[m['id'] for m in memories_to_share],
                memories=memories_to_share,
                share_type=share_type,
                expires_at=time.time() + (expires_hours * 3600)
            )

            print("✓ 分享创建成功")
            print(f"  分享ID: {share_id}")
            print(f"  记忆数: {len(memories_to_share)}")
            print(f"  类型: {share_type}")
            print(f"  过期时间: {expires_hours}小时后")

            return 0
        except Exception as e:
            print(f"创建分享失败: {e}")
            return 1

    def cmd_stats(self, args):
        """显示统计信息"""
        stats = {
            "总记忆数": len(self.current_memories),
            "L1记忆数": len([m for m in self.current_memories if m.get('level') == 'l1']),
            "L2记忆数": len([m for m in self.current_memories if m.get('level') == 'l2']),
            "L3记忆数": len([m for m in self.current_memories if m.get('level') == 'l3']),
        }

        # 获取系统统计
        try:
            system_stats = self.memory_system.get_statistics()
            stats["系统记忆总数"] = system_stats.get("total_memories", 0)
        except Exception:
            pass

        print("统计信息:")
        print("=" * 70)
        print(self._format_output(stats))

        return 0

    def cmd_config(self, args):
        """配置管理"""
        if args.set:
            key, value = args.set.split('=', 1)

            # 类型转换
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)

            self.config[key] = value
            self._save_config()
            print(f"✓ 配置已更新: {key} = {value}")
            return 0

        elif args.get:
            key = args.get
            if key in self.config:
                print(f"{key} = {self.config[key]}")
            else:
                print(f"未找到配置项: {key}")
            return 0

        elif args.list_all:
            print("当前配置:")
            print("=" * 70)
            print(self._format_output(self.config))
            return 0

        else:
            print("配置项:")
            print("=" * 70)
            print(self._format_output(self.config))
            return 0

    def cmd_interactive(self, args):
        """交互式模式"""
        print("\n" + "=" * 70)
        print("记忆系统 CLI - 交互式模式")
        print("=" * 70)
        print("输入命令进行操作，输入 'help' 查看帮助，输入 'exit' 退出")
        print()

        while True:
            try:
                user_input = input("memory> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("再见!")
                    break

                if user_input.lower() in ['help', 'h', '?']:
                    self._show_help()
                    continue

                if user_input.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue

                # 解析命令
                parts = user_input.split()
                command = parts[0].lower()
                arg_str = ' '.join(parts[1:])

                # 简单的命令解析
                if command == 'add' or command == 'a':
                    content = arg_str
                    if not content:
                        print("请提供记忆内容")
                    else:
                        args = argparse.Namespace(content=content, level=None, source=None)
                        self.cmd_add(args)

                elif command == 'list' or command == 'ls':
                    args = argparse.Namespace(level=None, limit=None)
                    self.cmd_list(args)

                elif command == 'search' or command == 's':
                    args = argparse.Namespace(query=arg_str)
                    self.cmd_search(args)

                elif command == 'ask' or command == 'q':
                    args = argparse.Namespace(question=arg_str, show_sources=False)
                    self.cmd_ask(args)

                elif command == 'stats':
                    self.cmd_stats(argparse.Namespace())

                elif command == 'export':
                    args = argparse.Namespace(format='json', output=None, no_metadata=False)
                    self.cmd_export(args)

                else:
                    print(f"未知命令: {command}")
                    print("输入 'help' 查看帮助")

            except KeyboardInterrupt:
                print("\n再见!")
                break
            except Exception as e:
                print(f"错误: {e}")

        return 0

    def _show_help(self):
        """显示帮助信息"""
        help_text = """
可用命令:
  add <内容>           - 添加新记忆
  list                 - 列出所有记忆
  search <关键词>      - 搜索记忆
  ask <问题>           - 向记忆系统提问
  stats                - 显示统计信息
  export [格式]        - 导出记忆 (json/text/markdown/csv)
  share                - 创建分享
  config               - 显示配置
  clear                - 清屏
  help                 - 显示帮助
  exit                 - 退出

快捷键:
  a <内容>            = add <内容>
  ls                  = list
  s <关键词>          = search <关键词>
  q <问题>            = ask <问题>
        """
        print(help_text)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="记忆系统 CLI - 命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  添加记忆:     memory add "这是一条新的记忆"
  列出记忆:     memory list --level l2
  搜索记忆:     memory search "项目"
  提问:        memory ask "这是什么内容？"
  导出:        memory export --format json --output memories.json
  交互模式:    memory interactive
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 添加记忆
    add_parser = subparsers.add_parser('add', help='添加新记忆')
    add_parser.add_argument('content', help='记忆内容')
    add_parser.add_argument('--level', '-l', help='记忆层级 (l1/l2/l3)')
    add_parser.add_argument('--source', '-s', help='记忆来源')

    # 列出记忆
    list_parser = subparsers.add_parser('list', help='列出记忆')
    list_parser.add_argument('--level', '-l', help='按层级筛选')
    list_parser.add_argument('--limit', '-n', type=int, help='返回数量限制')

    # 获取记忆
    get_parser = subparsers.add_parser('get', help='获取单个记忆')
    get_parser.add_argument('--id', '-i', required=True, help='记忆ID')

    # 删除记忆
    delete_parser = subparsers.add_parser('delete', help='删除记忆')
    delete_parser.add_argument('--id', '-i', required=True, help='记忆ID')

    # 搜索记忆
    search_parser = subparsers.add_parser('search', help='搜索记忆')
    search_parser.add_argument('query', help='搜索关键词')

    # 提问
    ask_parser = subparsers.add_parser('ask', help='向记忆系统提问')
    ask_parser.add_argument('question', help='问题内容')
    ask_parser.add_argument('--show-sources', '-v', action='store_true', help='显示相关记忆')

    # 导出
    export_parser = subparsers.add_parser('export', help='导出记忆')
    export_parser.add_argument('--format', '-f', choices=['json', 'text', 'markdown', 'csv'], default='json', help='导出格式')
    export_parser.add_argument('--output', '-o', help='输出文件路径')
    export_parser.add_argument('--no-metadata', action='store_true', help='不包含元数据')

    # 分享
    share_parser = subparsers.add_parser('share', help='创建分享')
    share_parser.add_argument('--memory-ids', help='记忆ID列表 (逗号分隔)')
    share_parser.add_argument('--type', '-t', default='read', help='分享类型')
    share_parser.add_argument('--expires', '-e', type=int, default=24, help='过期时间(小时)')

    # 统计
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')

    # 配置
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('--set', help='设置配置项 (key=value)')
    config_parser.add_argument('--get', help='获取配置项')
    config_parser.add_argument('--list-all', action='store_true', help='列出所有配置')

    # 交互式模式
    interactive_parser = subparsers.add_parser('interactive', help='交互式模式')

    # 解析参数
    args = parser.parse_args()

    # 如果没有命令，显示帮助
    if not args.command:
        parser.print_help()
        return 0

    # 创建CLI实例
    cli = MemoryCLI()

    # 根据命令执行相应操作
    if args.command == 'add':
        return cli.cmd_add(args)
    elif args.command == 'list':
        return cli.cmd_list(args)
    elif args.command == 'get':
        return cli.cmd_get(args)
    elif args.command == 'delete':
        return cli.cmd_delete(args)
    elif args.command == 'search':
        return cli.cmd_search(args)
    elif args.command == 'ask':
        return cli.cmd_ask(args)
    elif args.command == 'export':
        return cli.cmd_export(args)
    elif args.command == 'share':
        return cli.cmd_share(args)
    elif args.command == 'stats':
        return cli.cmd_stats(args)
    elif args.command == 'config':
        return cli.cmd_config(args)
    elif args.command == 'interactive':
        return cli.cmd_interactive(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
