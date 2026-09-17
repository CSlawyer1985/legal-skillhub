#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""status.py — 完卷：幂等重跑归档 + （确认后可选）合并

案子材料补齐后说「完卷」，本质是对同一案卷重新跑 archive_case（已处理的不动，
只补新槽位、更新 manifest）。合并仍须明确传入 --merge yes；偏好不会绕过确认。

用法:
  python status.py <案卷文件夹或输出文件夹> [--firm X] [--merge yes|no] [--values f.json]
"""
import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import archive_case


def main():
    if len(sys.argv) < 2:
        print("Usage: status.py <案卷文件夹或输出文件夹> [--firm X] [--merge yes|no] [--values f.json]")
        sys.exit(1)
    print("=" * 60)
    print("[完卷] 重新扫描案卷材料，补齐缺口并更新 manifest …")
    print("=" * 60)
    # archive_case.main() 已具备幂等重跑与合并逻辑
    archive_case.main()


if __name__ == '__main__':
    main()
