#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
律师案件归档助手 - 备份脚本
将技能文件备份到指定目录
"""

import os
import shutil
import datetime

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
# 备份目录（修改为您需要的备份路径）
BACKUP_DIR = r'D:\backup-fanglawerguidangzhushou'

def main():
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    backup_path = os.path.join(BACKUP_DIR, date_str)
    os.makedirs(backup_path, exist_ok=True)
    
    # 技能文件
    files = [
        'SKILL.md',
        'archive_case.py', 
        'config.py',
        'ocr_tool.py',
    ]
    
    for f in files:
        src = os.path.join(SKILL_DIR, f)
        dst = os.path.join(backup_path, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f'已备份: {f}')
    
    print(f'\n备份完成！共 {len(files)} 个文件')
    print(f'备份位置: {backup_path}')

if __name__ == '__main__':
    main()