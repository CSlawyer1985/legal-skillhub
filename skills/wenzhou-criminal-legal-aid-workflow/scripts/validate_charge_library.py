#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="校验常见罪名基础说明库的结构和必要字段。")
    parser.add_argument(
        "library",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "references" / "charge-law-library.json",
    )
    args = parser.parse_args()
    path = args.library.resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"罪名库校验失败：无法读取 {path}：{exc}")
    errors: list[str] = []
    try:
        date.fromisoformat(str(payload.get("reviewed_on", "")))
    except ValueError:
        errors.append("reviewed_on 必须是 YYYY-MM-DD")
    sources = payload.get("official_sources")
    if not isinstance(sources, list) or not sources:
        errors.append("official_sources 不能为空")
    charges = payload.get("charges")
    if not isinstance(charges, dict) or not charges:
        errors.append("charges 不能为空")
        charges = {}
    for name, entry in charges.items():
        if not isinstance(entry, dict):
            errors.append(f"{name}: 条目必须是对象")
            continue
        for field in ("category", "articles", "meeting_summary", "review_notes"):
            if not entry.get(field):
                errors.append(f"{name}: 缺少 {field}")
        if not str(name).endswith("罪"):
            errors.append(f"{name}: 应使用正式罪名并以‘罪’结尾")
        if len(str(entry.get("meeting_summary", ""))) < 45:
            errors.append(f"{name}: meeting_summary 过短")
    if errors:
        raise SystemExit("罪名库校验失败：\n- " + "\n- ".join(errors))
    warnings: list[str] = []
    try:
        reviewed = date.fromisoformat(str(payload["reviewed_on"]))
        stale_days = (date.today() - reviewed).days
        if stale_days > 90:
            warnings.append(
                f"罪名库核验日期为 {payload['reviewed_on']}（距今{stale_days}天，已超过90天）；"
                "按 charge-library-guide.md 用现行官方法源复核全部条目并更新 reviewed_on 后，再继续用于正式生成"
            )
    except (KeyError, ValueError):
        pass
    print(f"PASS: {path}（{len(charges)}个罪名，核验日期 {payload['reviewed_on']}）")
    for warning in warnings:
        print(f"注意：{warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

