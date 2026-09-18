#!/usr/bin/env python3
"""为下游法律 Skill 规划或显式初始化中文法律工作区；默认只规划不写入。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROFILES = {
    "case_analysis_v2": ["案件控制台", "原始材料", "AI可读材料", "案件认知/过程研究", "案件认知/阶段定稿", "阶段工作成果", "外部提交包", "结案归档", "审计日志", "项目脚本"],
    "due_diligence": ["项目管理", "原始底稿", "AI可读材料", "事实与证据", "风险条线", "法律研究", "报告组装", "律师复核", "正式交付", "归档", "审计日志"],
    "contract_review": ["项目管理", "原始合同与附件", "版本与修订记录", "当事人与交易背景", "条款审查", "法律研究与依据", "风险清单与谈判建议", "律师复核", "定稿与交付", "审计日志"],
    "legal_research": ["研究任务与范围", "问题树与检索计划", "事实与假设", "权威法源", "裁判与行政口径", "学理与辅助资料", "来源核验记录", "分析草稿", "人工复核", "研究备忘录", "审计日志"],
}


def plan(profile: str, root: Path, initialize: bool = False) -> dict:
    if profile not in PROFILES:
        raise ValueError(f"不支持的工作流：{profile}")
    existing = sorted(p.name for p in root.iterdir()) if root.is_dir() else []
    legacy = sorted(name for name in ("input", "scratch", "output", "review") if (root / name).exists())
    directories = [root / item for item in PROFILES[profile]]
    created: list[str] = []
    if initialize:
        root.mkdir(parents=True, exist_ok=True)
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(root)))
        guide = root / "文件夹使用说明.md"
        if not guide.exists():
            guide.write_text("# 文件夹使用说明\n\n请阅读生成 Skill 提供的工作流配置，并按法律工作阶段归档文件。\n", encoding="utf-8")
            created.append(guide.name)
    return {"workflow_family": profile, "root": str(root), "plan_only": not initialize, "directories": [str(p.relative_to(root)) for p in directories], "existing_entries": existing, "legacy_directories": legacy, "created": created}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, choices=sorted(PROFILES))
    parser.add_argument("--root", required=True)
    parser.add_argument("--initialize", action="store_true")
    args = parser.parse_args()
    print(json.dumps(plan(args.profile, Path(args.root), args.initialize), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
