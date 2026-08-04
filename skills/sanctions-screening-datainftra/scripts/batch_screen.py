#!/usr/bin/env python3
"""
批量筛查模块
支持从 CSV/文本文件批量导入实体名单，逐条执行筛查
"""

import csv
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from screen_entity import screen_entity, format_screening_report


def batch_screen_from_list(
    entities: list,
    entity_type: str = "LegalEntity",
    verify_official: bool = True,
    search_intel: bool = True,
    score_threshold: float = 0.4,
) -> list:
    """
    批量筛查实体列表

    参数:
        entities: 实体信息列表 [{"name": str, "type": str, ...}, ...]
        entity_type: 默认实体类型
        verify_official: 是否官方校验
        search_intel: 是否情报搜索
        score_threshold: 最低匹配分
    返回:
        筛查结果列表
    """
    results = []
    total = len(entities)

    for i, entity in enumerate(entities, 1):
        name = entity if isinstance(entity, str) else entity.get("name", "")
        e_type = entity.get("type", entity_type) if isinstance(entity, dict) else entity_type

        if not name.strip():
            continue

        print(f"\n{'='*50}", file=sys.stderr)
        print(f"[{i}/{total}] 筛查: {name}", file=sys.stderr)
        print(f"{'='*50}", file=sys.stderr)

        try:
            report = screen_entity(
                entity_name=name.strip(),
                entity_type=e_type,
                verify_official=verify_official,
                search_intel=search_intel,
                score_threshold=score_threshold,
            )
            results.append(report)
        except Exception as e:
            print(f"  错误: {e}", file=sys.stderr)
            results.append({
                "entity": name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })

    return results


def batch_screen_from_csv(
    csv_path: str,
    name_column: str = "name",
    type_column: str = "type",
    **kwargs,
) -> list:
    """
    从 CSV 文件批量筛查

    CSV 格式要求：至少有一列包含实体名称
    列名可配置（默认 name_column="name"）
    """
    entities = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get(name_column, "").strip()
            if name:
                entities.append({
                    "name": name,
                    "type": row.get(type_column, "LegalEntity"),
                })
    return batch_screen_from_list(entities, **kwargs)


def format_batch_summary(results: list) -> str:
    """生成批量筛查汇总报告"""
    lines = []
    lines.append("# 📋 批量制裁筛查汇总报告")
    lines.append(f"\n**筛查时间：** {datetime.now().isoformat()}")
    lines.append(f"**实体总数：** {len(results)}")

    # 统计
    hits = [r for r in results if r.get("opensanctions_screening", {}).get("status") == "hit"]
    clears = [r for r in results if r.get("opensanctions_screening", {}).get("status") == "clear"]
    errors = [r for r in results if r.get("error")]

    lines.append(f"\n## 📊 汇总")
    lines.append(f"| 状态 | 数量 |")
    lines.append(f"|------|------|")
    lines.append(f"| ⚠️ 命中 | {len(hits)} |")
    lines.append(f"| ✅ 清除 | {len(clears)} |")
    lines.append(f"| ❌ 错误 | {len(errors)} |")

    # 风险排行
    if hits:
        lines.append(f"\n## 🔴 命中实体详情（按风险评分排序）")
        hits.sort(
            key=lambda x: x.get("risk_assessment", {}).get("total_score", 0),
            reverse=True,
        )
        lines.append(f"\n| # | 实体 | 风险等级 | 评分 | 行动建议 |")
        lines.append(f"|---|------|---------|------|---------|")
        for i, r in enumerate(hits, 1):
            name = r.get("entity", "N/A")
            risk = r.get("risk_assessment", {})
            level = risk.get("risk_level", "N/A")
            score = risk.get("total_score", 0)
            action = r.get("recommendation", {}).get("action", "N/A")
            lines.append(f"| {i} | {name} | {level} | {score}/80 | {action} |")

    if clears:
        lines.append(f"\n## ✅ 清除实体")
        for r in clears:
            lines.append(f"- {r.get('entity', 'N/A')}")

    return "\n".join(lines)


def main():
    """CLI 入口"""
    import argparse
    parser = argparse.ArgumentParser(description="批量制裁筛查")

    parser.add_argument("input", help="输入文件路径 (CSV) 或逗号分隔的实体名称列表")
    parser.add_argument("--name-column", default="name", help="CSV 中实体名列名")
    parser.add_argument("--type", default="LegalEntity", help="默认实体类型")
    parser.add_argument("--no-verify", action="store_true", help="跳过官方校验")
    parser.add_argument("--no-intel", action="store_true", help="跳过情报搜索")
    parser.add_argument("--threshold", type=float, default=0.4)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", "-o", default=None, help="输出文件")

    args = parser.parse_args()

    # 判断输入类型
    if os.path.isfile(args.input) and args.input.endswith(".csv"):
        results = batch_screen_from_csv(
            args.input,
            name_column=args.name_column,
            entity_type=args.type,
            verify_official=not args.no_verify,
            search_intel=not args.no_intel,
            score_threshold=args.threshold,
        )
    else:
        # 按逗号分隔的实体名列表
        entities = [e.strip() for e in args.input.split(",") if e.strip()]
        results = batch_screen_from_list(
            entities,
            entity_type=args.type,
            verify_official=not args.no_verify,
            search_intel=not args.no_intel,
            score_threshold=args.threshold,
        )

    if args.json:
        output = json.dumps(results, ensure_ascii=False, indent=2)
    else:
        output = format_batch_summary(results)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n报告已保存至: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
