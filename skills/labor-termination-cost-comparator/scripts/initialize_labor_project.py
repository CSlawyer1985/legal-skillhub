#!/usr/bin/env python3
"""规划或初始化劳动解除成本项目的三目录结构。

默认只输出计划；只有提供 --initialize 才写入用户选择的根目录。已有文件不覆盖。
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


FOLDERS = [
    "01_输入材料/01_文字与问卷",
    "01_输入材料/02_劳动合同与制度",
    "01_输入材料/03_工资考勤与福利",
    "01_输入材料/04_解除通知与程序材料",
    "01_输入材料/05_其他附件",
    "02_处理过程/01_材料清单与哈希",
    "02_处理过程/02_PDF转换包",
    "02_处理过程/03_事实与证据",
    "02_处理过程/04_法律核验",
    "02_处理过程/05_计算与方案",
    "02_处理过程/06_Word生成与检查",
    "02_处理过程/07_人工复核",
    "03_输出交付/01_客户版",
    "03_输出交付/02_内部底稿",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="规划或初始化劳动解除成本项目")
    parser.add_argument("--root", required=True, help="用户已选择的项目父目录")
    parser.add_argument("--keyword", required=True, help="项目关键词，不含敏感个人信息")
    parser.add_argument("--date", default=date.today().strftime("%Y%m%d"), help="项目日期 YYYYMMDD")
    parser.add_argument("--initialize", action="store_true", help="确认写入并创建目录")
    args = parser.parse_args()

    project = Path(args.root).expanduser().resolve() / f"{args.date}_{args.keyword}"
    paths = [project / folder for folder in FOLDERS]
    print(f"项目目录：{project}")
    print("将创建：")
    for path in paths:
        print(f"- {path}")
    if not args.initialize:
        print("仅规划，未写入；确认后再次提供 --initialize 才创建目录。")
        return 0
    project.mkdir(parents=True, exist_ok=False)
    for path in paths:
        path.mkdir(parents=True, exist_ok=False)
    (project / "文件夹使用说明.md").write_text(
        "# 文件夹使用说明\n\n本项目按 01_输入材料、02_处理过程、03_输出交付三目录运行。请先阅读 Skill 包内的项目文件契约。\n",
        encoding="utf-8",
    )
    print(f"已初始化：{project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
