#!/usr/bin/env python3
"""
修复模块级别缺少logger初始化的问题
"""

import os
from pathlib import Path


def fix_file(filepath):
    """修复单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    lines = content.split('\n')
    
    # 检查是否有模块级别的logger使用（不在类/函数内）
    has_module_level_logger_use = False
    in_function = False
    indent_level = 0
    
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('def ') or stripped.startswith('class '):
            in_function = True
        if in_function:
            continue
        if stripped.startswith('logger.'):
            has_module_level_logger_use = True
            break
    
    if not has_module_level_logger_use:
        return False
    
    # 检查是否已有模块级别的logger初始化
    has_module_logger_init = False
    for line in lines:
        if line.strip() == 'logger = get_logger()':
            has_module_logger_init = True
            break
    
    if has_module_logger_init:
        return False
    
    # 找到get_logger导入的位置，在其后添加logger初始化
    import_idx = -1
    for i, line in enumerate(lines):
        if 'get_logger' in line and ('import' in line or 'from' in line):
            import_idx = i + 1
    
    if import_idx > 0:
        lines.insert(import_idx, 'logger = get_logger()')
        content = '\n'.join(lines)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    src_dir = Path('/workspace/src')
    modified_files = []
    
    for py_file in src_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        if fix_file(str(py_file)):
            modified_files.append(str(py_file))
    
    print(f"已修复 {len(modified_files)} 个文件:")
    for f in modified_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
