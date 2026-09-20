#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_report.py — legal-research-report 产出报告的机械校验脚本（第一层测试）

用法：
    python3 check_report.py <报告文件>     # 支持 .md / .txt / .html / .docx

检查内容：
    1. 结构完整性：七部分栏目是否齐备
    2. 必备表格：检索过程记录表 / 条文核验表 / 类案一览表 / 分歧对照表的关键列
    3. 红线扫描：绝对化承诺、把个案当通则的高危表述
    4. 案号与链接：案号正则统计、http(s) 链接统计
    5. 计数一致性：检索结果声明数与表格实际行数比对（WARN 级）

输出 PASS / FAIL / WARN 清单；任一 FAIL 退出码为 1，否则为 0。
机械校验只能发现"形"的问题，"实"的问题须配合 tests/ 第二、三层测试。
"""
import re
import sys
import zipfile


def load_text(path: str) -> str:
    if path.endswith(".docx"):
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
            text = re.sub(r"<[^>]+>", "", xml)
            # docx 超链接存储在关系文件中，正文中取不到 URL，需补读 .rels
            try:
                rels = z.read("word/_rels/document.xml.rels").decode("utf-8", errors="ignore")
                urls = re.findall(r'Target="(https?://[^"]+)"', rels)
                text += "\n" + "\n".join(urls)
            except KeyError:
                pass
        return text
    if path.endswith(".html") or path.endswith(".htm"):
        raw = open(path, encoding="utf-8", errors="ignore").read()
        urls = re.findall(r'href="(https?://[^"]+)"', raw)
        text = re.sub(r"<[^>]+>", "", raw)
        return text + "\n" + "\n".join(urls)
    return open(path, encoding="utf-8", errors="ignore").read()


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    text = load_text(path)
    results = []  # (level, item, detail)

    def ok(item, detail=""):
        results.append(("PASS", item, detail))

    def fail(item, detail=""):
        results.append(("FAIL", item, detail))

    def warn(item, detail=""):
        results.append(("WARN", item, detail))

    # ---------- 1. 结构完整性 ----------
    sections = [
        ("一、问题的界定与检索路径", "问题的界定|问题界定"),
        ("二、法律依据", "法律依据|规范体系"),
        ("三、类案检索与裁判规则", "类案检索"),
        ("四、实务分歧观点及主流倾向", "实务分歧"),
        ("五、研究结论与风险提示", "研究结论"),
        ("六、未采信事项说明", "未采信事项"),
        ("附：数据库定位信息", "数据库定位信息"),
    ]
    for name, kw in sections:
        if any(a in text for a in kw.split("|")):
            ok(f"栏目：{name}")
        else:
            fail(f"栏目缺失：{name}")

    # 摘要"先看结论"（v1.2.1 起为固定栏目；WARN 级，便于旧报告过渡）
    if "先看结论" in text or "摘要" in text[:800]:
        ok("栏目：摘要（先看结论）")
    else:
        warn("栏目建议：缺摘要", "v1.2.1 起摘要为固定栏目（核心判断+变量框架+编号结论），建议补充")

    # ---------- 2. 必备表格关键要素 ----------
    # 每项为关键词组；组内以 | 分隔的视为"任一命中即可"（允许按命题语境改写列名）
    table_checks = [
        ("检索过程记录表", ["检索人", "检索日期", "检索平台", "检索关键词"]),
        ("条文核验表（效力状态列）", ["效力状态|效力/使用说明|效力说明"]),
        ("类案一览表（含效力层级/受新规或批复影响列）", ["效力层级", "受新规影响|受批复影响|受新法影响"]),
        ("分歧对照表（含主流倾向列）", ["主流倾向"]),
    ]
    for name, kws in table_checks:
        missing = []
        for k in kws:
            alternatives = k.split("|")
            if not any(a in text for a in alternatives):
                missing.append(alternatives[0])
        if not missing:
            ok(f"表格：{name}")
        else:
            fail(f"表格要素缺失：{name}（缺：{'、'.join(missing)}）")

    # ---------- 3. 红线扫描 ----------
    red_patterns = [
        (r"保证胜诉|稳赢|百分之百胜诉|必胜", "绝对化承诺（胜诉）"),
        (r"保证无责|绝对不承担责任|必然免责", "绝对化承诺（责任）"),
        (r"规避监管|隐匿财产|转移资产逃避", "违法操作方案"),
    ]
    for pat, label in red_patterns:
        hits = re.findall(pat, text)
        if hits:
            fail(f"红线：{label}", f"出现 {len(hits)} 处：{hits[:3]}")
        else:
            ok(f"红线扫描：{label}")

    # 个案当通则的高危表述（WARN 级，需人工判断语境）
    for pat, label in [
        (r"各级法院均|法院普遍|已形成(统一|稳定)裁判规则", "把样本包装成趋势"),
    ]:
        hits = re.findall(pat, text)
        if hits:
            warn(f"疑似{label}", f"出现 {len(hits)} 处，请人工确认语境：{hits[:3]}")
        else:
            ok(f"趋势表述扫描：{label}")

    # 样本不足声明（加分项，有则提示 PASS）
    if "样本" in text and ("有限" in text or "不足" in text):
        ok("样本量克制表述：存在")

    # ---------- 4. 案号与链接 ----------
    case_nos = re.findall(r"[（(]\d{4}[）)][^\s，。、；）)]{1,25}?号", text)
    uniq = sorted(set(case_nos))
    if len(uniq) >= 4:
        ok("案号统计", f"识别到 {len(uniq)} 个不同案号")
    elif uniq:
        warn("案号统计", f"仅识别到 {len(uniq)} 个案号，案例覆盖度请人工确认")
    else:
        fail("案号统计", "未识别到任何案号")

    links = re.findall(r"https?://[^\s）)\]>\"']+", text)
    if links:
        ok("链接统计", f"识别到 {len(links)} 个 http(s) 链接")
    else:
        fail("链接统计", "未识别到任何数据库定位链接")

    # ---------- 5. 计数一致性（WARN 级） ----------
    m = re.search(r"法条\s*(\d+)\s*项", text)
    if m:
        declared = int(m.group(1))
        warn("计数核对", f"声明法条 {declared} 项——请与条文核验表实际行数人工比对（机械计数不可靠，列为 WARN）")
    m2 = re.search(r"案例\s*(\d+)\s*个", text)
    if m2:
        declared = int(m2.group(1))
        if abs(declared - len(uniq)) <= 3:
            ok("案例计数核对", f"声明 {declared} 个，识别 {len(uniq)} 个，基本一致")
        else:
            warn("案例计数核对", f"声明 {declared} 个，识别 {len(uniq)} 个，差异较大，请人工核对")

    # ---------- 输出 ----------
    print(f"\n===== check_report 校验结果：{path} =====\n")
    n_fail = 0
    for level, item, detail in results:
        if level == "FAIL":
            n_fail += 1
        line = f"[{level}] {item}"
        if detail:
            line += f" —— {detail}"
        print(line)
    n_pass = sum(1 for r in results if r[0] == "PASS")
    n_warn = sum(1 for r in results if r[0] == "WARN")
    print(f"\n合计：PASS {n_pass} / WARN {n_warn} / FAIL {n_fail}")
    print("提示：FAIL 必须修复；WARN 需人工确认；机械校验通过 ≠ 内容正确，请配合 tests/ 第二、三层测试。")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
