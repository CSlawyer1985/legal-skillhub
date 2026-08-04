"""
Markdown report renderer for contract comparison results.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime


def render_diff_report(
    diff_items: List[Dict[str, Any]],
    file_a_name: str = "合同A",
    file_b_name: str = "合同B",
    tier: str = "FREE",
    include_same: bool = False,
) -> str:
    """Render a Markdown diff report.

    Args:
        diff_items: List of diff items from compare_clauses
        file_a_name: Name of the first contract
        file_b_name: Name of the second contract
        tier: Subscription tier
        include_same: Whether to include unchanged clauses

    Returns:
        Markdown report string
    """
    lines = []
    lines.append(f"# 合同差异比对报告")
    lines.append(f"")
    lines.append(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**比对合同：** {file_a_name} vs {file_b_name}")
    lines.append(f"**套餐等级：** {tier}")
    lines.append("")

    # Summary
    summary = _build_summary(diff_items)
    lines.append("## 📊 差异摘要")
    lines.append("")
    lines.append(f"| 类型 | 数量 |")
    lines.append(f"|------|------|")
    lines.append(f"| 🔴 删除条款 | {summary['deleted_count']} |")
    lines.append(f"| 🟡 修改条款 | {summary['modified_count']} |")
    lines.append(f"| 🟢 新增条款 | {summary['new_count']} |")
    if include_same:
        lines.append(f"| ⚪ 相同条款 | {summary['same_count']} |")
    lines.append(f"| **合计差异** | **{summary['total_changes']}** |")
    lines.append("")

    # Filter items
    filtered = diff_items if include_same else [d for d in diff_items if d["type"] != "same"]

    # Deleted clauses
    deleted = [d for d in filtered if d["type"] == "deleted"]
    if deleted:
        lines.append("## 🗑️ 删除条款")
        lines.append("")
        for item in deleted:
            clause = item.get("clause_a") or {}
            lines.append(f"### {clause.get('number', 'N/A')} - {clause.get('title', '无标题')}")
            lines.append("")
            lines.append("```")
            lines.append(clause.get("content", "")[:1000])
            lines.append("```")
            lines.append("")

    # Modified clauses
    modified = [d for d in filtered if d["type"] == "modified"]
    if modified:
        lines.append("## ✏️ 修改条款")
        lines.append("")
        for item in modified:
            clause_a = item.get("clause_a") or {}
            clause_b = item.get("clause_b") or {}
            lines.append(f"### {clause_b.get('number', clause_a.get('number', 'N/A'))} - {clause_b.get('title', clause_a.get('title', '无标题'))}")
            lines.append("")
            if item.get("diff_content"):
                lines.append(item["diff_content"])
            else:
                lines.append("**原内容：**")
                lines.append("```")
                lines.append(clause_a.get("content", "")[:800])
                lines.append("```")
                lines.append("")
                lines.append("**新内容：**")
                lines.append("```")
                lines.append(clause_b.get("content", "")[:800])
                lines.append("```")
            lines.append("")

    # New clauses
    new_items = [d for d in filtered if d["type"] == "new"]
    if new_items:
        lines.append("## ➕ 新增条款")
        lines.append("")
        for item in new_items:
            clause = item.get("clause_b") or {}
            lines.append(f"### {clause.get('number', 'N/A')} - {clause.get('title', '无标题')}")
            lines.append("")
            lines.append("```")
            lines.append(clause.get("content", "")[:1000])
            lines.append("```")
            lines.append("")

    # Same clauses (if requested)
    if include_same:
        same = [d for d in filtered if d["type"] == "same"]
        if same:
            lines.append("## ⚪ 相同条款（未变动）")
            lines.append("")
            for item in same:
                clause = item.get("clause_a") or {}
                lines.append(f"- **{clause.get('number', 'N/A')}** {clause.get('title', '')}")
            lines.append("")

    lines.append("---")
    lines.append("*报告由合同智能比对工具自动生成*")

    return "\n".join(lines)


def render_multi_version_report(
    all_clauses: List[Dict[str, List[Dict]]],
    file_info: List[Dict[str, str]],
    diff_results: List[Dict[str, Any]],
    key_summaries: Dict[str, List[Dict[str, str]]] = None,
    risk_items: List[Dict[str, Any]] = None,
) -> str:
    """Render a multi-version comparison report (PRO tier).

    Args:
        all_clauses: List of clause lists (one per file)
        file_info: List of dicts with filename, version_label, date
        diff_results: List of diff results between consecutive versions
        key_summaries: Dict mapping filename to key clause summaries
        risk_items: List of risk assessments

    Returns:
        Markdown report string
    """
    lines = []
    lines.append(f"# 合同多版本比对报告")
    lines.append("")
    lines.append(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**版本数量：** {len(file_info)}")
    lines.append("")

    # Version timeline
    lines.append("## 📅 版本时间轴")
    lines.append("")
    lines.append("| # | 文件名 | 版本标签 | 日期 |")
    lines.append("|---|--------|---------|------|")
    for i, f in enumerate(file_info, 1):
        lines.append(f"| {i} | {f.get('filename', 'N/A')} | {f.get('version_label', f'版本{i}')} | {f.get('date', 'N/A')} |")
    lines.append("")

    # Summary across all comparisons
    total_new = sum(len([d for d in dr if d["type"] == "new"]) for dr in diff_results)
    total_deleted = sum(len([d for d in dr if d["type"] == "deleted"]) for dr in diff_results)
    total_modified = sum(len([d for d in dr if d["type"] == "modified"]) for dr in diff_results)

    lines.append("## 📊 总体差异统计")
    lines.append("")
    lines.append(f"| 指标 | 数量 |")
    lines.append(f"|------|------|")
    lines.append(f"| 新增条款总数 | {total_new} |")
    lines.append(f"| 删除条款总数 | {total_deleted} |")
    lines.append(f"| 修改条款总数 | {total_modified} |")
    lines.append("")

    # Per-version diffs
    for i, (diff_items, info) in enumerate(zip(diff_results, file_info[:-1])):
        next_info = file_info[i + 1]
        filtered = [d for d in diff_items if d["type"] != "same"]

        if not filtered:
            continue

        lines.append(f"## 版本{i+1} → 版本{i+2} 差异 ({info.get('version_label', f'版本{i+1}')} → {next_info.get('version_label', f'版本{i+2}')})")
        lines.append("")

        for item in filtered:
            diff_type = item.get("type", "")
            clause_a = item.get("clause_a") or {}
            clause_b = item.get("clause_b") or {}

            if diff_type == "new":
                lines.append(f"### 🟢 新增：{clause_b.get('number', 'N/A')} {clause_b.get('title', '')}")
                lines.append("```")
                lines.append(clause_b.get("content", "")[:500])
                lines.append("```")
            elif diff_type == "deleted":
                lines.append(f"### 🔴 删除：{clause_a.get('number', 'N/A')} {clause_a.get('title', '')}")
            elif diff_type == "modified":
                lines.append(f"### 🟡 修改：{clause_b.get('number', clause_a.get('number', 'N/A'))} {clause_b.get('title', clause_a.get('title', ''))}")
                if item.get("diff_content"):
                    lines.append(item["diff_content"])
            lines.append("")

    # Key clause summaries
    if key_summaries:
        lines.append("## 📌 关键条款摘要")
        lines.append("")
        for info in file_info:
            fname = info.get("filename", "")
            summary = (key_summaries or {}).get(fname, [])
            if summary:
                lines.append(f"### {info.get('version_label', fname)} 关键条款")
                lines.append("")
                for s in summary:
                    lines.append(f"- **{s.get('number', '')} {s.get('title', '')}**：{s.get('summary', '')}")
                lines.append("")

    # Risk assessment
    if risk_items:
        lines.append("## ⚠️ 风险评估")
        lines.append("")
        risk_colors = {"high": "🔴 高风险", "medium": "🟠 中风险", "low": "🟢 低风险"}

        high_risk = [r for r in risk_items if r.get("risk_level") == "high"]
        medium_risk = [r for r in risk_items if r.get("risk_level") == "medium"]
        low_risk = [r for r in risk_items if r.get("risk_level") == "low"]

        if high_risk:
            lines.append("### 🔴 高风险条款")
            lines.append("")
            for r in high_risk:
                clause = r.get("clause", {}) or {}
                lines.append(f"- **{clause.get('number', '')} {clause.get('title', '')}**：{r.get('risk_reason', '')}")
            lines.append("")

        if medium_risk:
            lines.append("### 🟠 中风险条款")
            lines.append("")
            for r in medium_risk:
                clause = r.get("clause", {}) or {}
                lines.append(f"- **{clause.get('number', '')} {clause.get('title', '')}**：{r.get('risk_reason', '')}")
            lines.append("")

        if low_risk:
            lines.append("### 🟢 低风险条款")
            lines.append("")
            for r in low_risk:
                clause = r.get("clause", {}) or {}
                lines.append(f"- **{clause.get('number', '')} {clause.get('title', '')}**：{r.get('risk_reason', '')}")
            lines.append("")

    lines.append("---")
    lines.append("*多版本比对报告由合同智能比对工具自动生成*")

    return "\n".join(lines)


def _build_summary(diff_items: List[Dict[str, Any]]) -> Dict[str, int]:
    """Build summary statistics."""
    summary = {
        "total_changes": 0,
        "new_count": 0,
        "deleted_count": 0,
        "modified_count": 0,
        "same_count": 0,
    }
    for item in diff_items:
        t = item.get("type", "same")
        summary["total_changes"] += 1
        if t == "new":
            summary["new_count"] += 1
        elif t == "deleted":
            summary["deleted_count"] += 1
        elif t == "modified":
            summary["modified_count"] += 1
        else:
            summary["same_count"] += 1
    return summary
