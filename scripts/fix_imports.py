#!/usr/bin/env python3
"""
修复错误的logger导入路径
"""

import os
from pathlib import Path


def fix_imports_in_file(filepath):
    """修复单个文件中的错误导入"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    rel_path = os.path.relpath(filepath, '/workspace')
    
    if not rel_path.startswith('src/'):
        return False
    
    parts = rel_path.split('/')
    # 从文件所在目录到 src/ 目录的深度
    # 例如 src/memory/l2_memory.py -> 在 src/memory/ 目录下，到 src/ 需要 ../
    depth = len(parts) - 1  # 减去文件名
    
    if depth > 1:
        prefix = '.' * depth
        correct_import = f"from {prefix}utils.logger import get_logger"
        wrong_import = "from .utils.logger import get_logger"
        
        if wrong_import in content:
            content = content.replace(wrong_import, correct_import)
    
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
        
        if fix_imports_in_file(str(py_file)):
            modified_files.append(str(py_file))
    
    print(f"已修复 {len(modified_files)} 个文件:")
    for f in modified_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
