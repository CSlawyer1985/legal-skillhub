#!/usr/bin/env python3
"""背调报告质控校验器（确定性检查，对标工程化标杆）。
用法: python3 scripts/check_report.py <报告底稿.md> <附件底稿.md>
检查：必备章节齐全；正文引用的来源编号（A/B 系列）在附件中全部有定义；
附件中定义的来源均被正文引用；无内部字样；执行摘要与准入结论存在。
全部通过退出码 0，否则 1。
"""
import os
import glob
import re
import sys

REQUIRED_SECTIONS = ["执行摘要", "报告说明", "工商基本信息", "股权结构", "董监高",
                     "主营业务", "诉讼与被执行", "行政处罚", "知识产权", "舆情",
                     "客户准入合规审查", "利益冲突检索", "反洗钱义务触发判断",
                     "受益所有人", "名单筛查", "付费能力", "准入结论",
                     "律师视角分析", "替代方案", "首次洽谈问题清单",
                     "数据口径冲突表", "时间轴与行动窗口", "收费方案与退出机制",
                     "人工核验清单", "未能核实事项", "结论"]
BANNED = ["待确认", "工作底稿", "内部参考", "审批签字", "风险评级："]


def main(report_path, annex_path):
    report = open(report_path, encoding="utf-8").read()
    annex = open(annex_path, encoding="utf-8").read()
    fails = []

    for s in REQUIRED_SECTIONS:
        if s not in report:
            fails.append(f"缺章节: {s}")
    for w in BANNED:
        if w in report:
            fails.append(f"出现内部字样: {w}")

    cited = set(re.findall(r"\b([AB]\d{1,2})\b", report))
    defined = set(re.findall(r"^## ([AB]\d{1,2})\.", annex, re.M))
    for ref in sorted(cited - defined):
        fails.append(f"正文引用但附件未定义: {ref}")
    for ref in sorted(defined - cited):
        fails.append(f"附件定义但正文未引用: {ref}")

    if "红" not in report or "绿" not in report:
        fails.append("执行摘要红黄绿风险信号清单缺失")

    # 配套文件检查（警告级）
    outdir = os.path.dirname(report_path)
    for comp in ["证据账本.md"]:
        if not os.path.exists(os.path.join(outdir, comp)):
            fails.append(f"缺配套文件: {comp}")
    if not glob.glob(os.path.join(outdir, "采集原始数据", "*.json")):
        print("WARN 未发现 MCP 采集原始数据（纯公开检索模式，证据账本来源类型应如实标注）")

    if fails:
        print("FAIL")
        for f in fails:
            print(" -", f)
        sys.exit(1)
    print(f"PASS 章节{len(REQUIRED_SECTIONS)}项 来源引用{len(cited)}条双向一致 无内部字样")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
