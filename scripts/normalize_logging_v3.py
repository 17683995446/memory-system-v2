#!/usr/bin/env python3
"""
日志规范化脚本 V3
逐行精确替换print为logger
"""

import os
import re
from pathlib import Path


def get_import_line(filepath):
    """根据文件路径确定logger导入语句"""
    rel_path = os.path.relpath(filepath, '/workspace')
    if rel_path.startswith('tests/'):
        return "from src.utils.logger import get_logger"
    elif rel_path.startswith('src/'):
        parts = rel_path.split('/')
        depth = len(parts) - 2  # 减去 'src' 和文件名
        if depth > 0:
            prefix = '.' * depth
            return f"from {prefix}utils.logger import get_logger"
        else:
            return "from .utils.logger import get_logger"
    else:
        return "from src.utils.logger import get_logger"


def normalize_file(filepath):
    """规范化单个文件的日志"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    original_lines = lines[:]
    modified = False
    has_logger_import = False
    has_get_logger_call = False
    
    # 先检查是否已有logger导入
    for line in lines:
        if 'get_logger' in line and ('import' in line or 'from' in line):
            has_logger_import = True
        if 'get_logger()' in line:
            has_get_logger_call = True
    
    # 逐行处理
    new_lines = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('print('):
            indent = line[:len(line) - len(line.lstrip())]
            # 提取print内容
            match = re.match(r'print\((.*)\)', stripped)
            if match:
                content = match.group(1)
                # 如果是字符串字面量或f-string，直接替换
                if (content.startswith('"') and content.endswith('"')) or \
                   (content.startswith("'") and content.endswith("'")) or \
                   (content.startswith('f"') and content.endswith('"')) or \
                   (content.startswith("f'") and content.endswith("'")):
                    new_line = f"{indent}logger.info({content})\n"
                else:
                    # 变量或表达式
                    new_line = f"{indent}logger.info(str({content}))\n"
                new_lines.append(new_line)
                modified = True
                continue
        new_lines.append(line)
    
    lines = new_lines
    
    # 如果需要添加导入
    if modified and not has_logger_import:
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_idx = i + 1
        
        logger_import = get_import_line(filepath)
        lines.insert(import_idx, logger_import + '\n')
        lines.insert(import_idx + 1, '\n')
    
    # 如果需要添加logger初始化（且没有已存在的）
    if modified and not has_get_logger_call:
        for i, line in enumerate(lines):
            if 'def __init__(self' in line:
                indent = len(line) - len(line.lstrip()) + 4
                lines.insert(i + 1, ' ' * indent + 'self._logger = get_logger()\n')
                break
            elif 'def main(' in line:
                indent = len(line) - len(line.lstrip()) + 4
                lines.insert(i + 1, ' ' * indent + 'logger = get_logger()\n')
                break
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    return False


def main():
    """主函数"""
    src_dir = Path('/workspace/src')
    tests_dir = Path('/workspace/tests')
    modified_files = []
    
    for py_file in list(src_dir.rglob('*.py')) + list(tests_dir.rglob('*.py')):
        if '__pycache__' in str(py_file):
            continue
        
        if normalize_file(str(py_file)):
            modified_files.append(str(py_file))
    
    print(f"已规范化 {len(modified_files)} 个文件:")
    for f in modified_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
