#!/usr/bin/env python3
"""
日志规范化脚本
自动将所有print替换为logger调用
"""

import os
import re
from pathlib import Path


def normalize_file(filepath):
    """规范化单个文件的日志"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 检查是否已经导入了logger
    has_logger_import = 'from ..utils.logger import get_logger' in content or \
                       'from src.utils.logger import get_logger' in content or \
                       'get_logger()' in content
    
    # 替换简单的print语句
    # print("...") -> logger.info("...")
    content = re.sub(
        r'^([ \t]*)print\((["\'])(.+?)\2\)',
        r'\1logger.info(\2\3\2)',
        content,
        flags=re.MULTILINE
    )
    
    # print(f"...") -> logger.info(f"...")
    content = re.sub(
        r'^([ \t]*)print\((f["\'])(.+?)\2\)',
        r'\1logger.info(\2\3\2)',
        content,
        flags=re.MULTILINE
    )
    
    # print(variable) -> logger.info(str(variable))
    content = re.sub(
        r'^([ \t]*)print\(([^"\']+?)\)',
        r'\1logger.info(str(\2))',
        content,
        flags=re.MULTILINE
    )
    
    if content != original and not has_logger_import:
        # 需要添加logger导入
        # 找到最后一个import语句，在其后添加
        lines = content.split('\n')
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_idx = i + 1
        
        # 确定相对导入路径
        rel_path = os.path.relpath(filepath, '/workspace/src')
        depth = len(rel_path.split(os.sep)) - 1
        if depth > 0:
            prefix = '.' * depth
            logger_import = f"from {prefix}utils.logger import get_logger"
        else:
            logger_import = "from .utils.logger import get_logger"
        
        lines.insert(import_idx, logger_import)
        lines.insert(import_idx + 1, "")
        
        # 在类初始化或函数开头添加logger初始化
        for i, line in enumerate(lines):
            if 'def __init__(self' in line or 'def main(' in line:
                # 在下一行添加logger初始化
                indent = len(line) - len(line.lstrip()) + 4
                lines.insert(i + 1, ' ' * indent + 'self._logger = get_logger()')
                break
        
        content = '\n'.join(lines)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """主函数"""
    src_dir = Path('/workspace/src')
    modified_files = []
    
    for py_file in src_dir.rglob('*.py'):
        # 跳过__pycache__和已规范化的文件
        if '__pycache__' in str(py_file):
            continue
        
        if normalize_file(str(py_file)):
            modified_files.append(str(py_file))
    
    print(f"已规范化 {len(modified_files)} 个文件:")
    for f in modified_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
