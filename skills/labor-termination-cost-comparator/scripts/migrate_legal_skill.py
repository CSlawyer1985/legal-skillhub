#!/usr/bin/env python3
"""将旧版 intake 迁移为 legal-skill-intake/v0.2；默认不原地修改。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def migrate_intake(document: object) -> dict:
    if not isinstance(document, dict):
        raise ValueError("intake 必须为 JSON 对象")
    migrated = dict(document)
    migrated["schema_version"] = "legal-skill-intake/v0.2"
    supplement = migrated.get("domain_supplement")
    if isinstance(supplement, list):
        normalized = []
        for index, item in enumerate(supplement, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"domain_supplement 第 {index} 项必须为对象")
            entry = dict(item)
            entry.setdefault("id", f"domain-supplement-{index:02d}")
            if "answer_summary" not in entry and "answer" in entry:
                entry["answer_summary"] = entry.pop("answer")
            if "internalized_rules" not in entry and entry.get("answer_summary"):
                entry["internalized_rules"] = [entry["answer_summary"]]
            entry.setdefault("sensitivity", "internalized-only")
            normalized.append(entry)
        migrated["domain_supplement"] = normalized
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(description="迁移法律 Skill intake schema")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        source = Path(args.input).resolve()
        output = Path(args.output).resolve()
        document = json.loads(source.read_text(encoding="utf-8"))
        migrated = migrate_intake(document)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(migrated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}")
        return 1
    print(f"已迁移 intake：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
