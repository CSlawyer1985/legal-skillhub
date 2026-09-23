#!/usr/bin/env python3
"""smoke_test.py — (快速版)案例检索报告Plus 冒烟测试。

Skill作者：浙江金道律师事务所 龚家勇律师（微信：13967182079）

校验两件事：
  1. score_fast.py：去重、5 要素加权、分级、案号完整性标记、入报门槛过滤；
  2. build_docx.py：DOCX 可生成、表格无空单元格、页脚含 PAGE/NUMPAGES 域、
     两处固定声明在位。

用例数据均为**虚构样例**，仅用于验证脚本行为，不代表任何真实裁判文书。

用法：
    python tests/smoke_test.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
OUT = HERE / "_out"

PY = sys.executable

# ---- 虚构样例数据（案号为示例格式，非真实文书） ----
CANDIDATES = [
    {"case_number": "（2023）浙01民终1001号", "court": "浙江省杭州市中级人民法院",
     "decision_date": "2023-05-18", "cause": "买卖合同纠纷",
     "title": "甲诉乙买卖合同纠纷案（样例）", "summary": "样例摘要一", "score": 0.91},
    {"case_number": "（2023）浙01民终1001号", "court": "浙江省杭州市中级人民法院",
     "decision_date": "2023-05-18", "cause": "买卖合同纠纷",
     "title": "重复项，应被去重", "summary": "样例摘要一（重复）", "score": 0.91},
    {"case_number": "（2022）浙02民终2002号", "court": "浙江省宁波市中级人民法院",
     "decision_date": "2022-11-02", "cause": "买卖合同纠纷",
     "title": "丙诉丁买卖合同纠纷案（样例）", "summary": "样例摘要二", "score": 0.86},
    {"case_number": "（2021）浙某某民初3003号", "court": "某基层人民法院",
     "decision_date": "2021-07-09", "cause": "买卖合同纠纷",
     "title": "脱敏案号样例（应标记不完整）", "summary": "样例摘要三", "score": 0.80},
    {"case_number": "（2024）沪01民终4004号", "court": "上海市第一中级人民法院",
     "decision_date": "2024-03-21", "cause": "买卖合同纠纷",
     "title": "戊诉己买卖合同纠纷案（样例）", "summary": "样例摘要四", "score": 0.77},
    {"case_number": "（2020）粤03民终5005号", "court": "广东省深圳市中级人民法院",
     "decision_date": "2020-09-30", "cause": "承揽合同纠纷",
     "title": "庚诉辛承揽合同纠纷案（样例，低分）", "summary": "样例摘要五", "score": 0.55},
    # 高分反向案例：事实高度相似但裁判驳回（S4＝0），若无方向闸门会以 8.0 分 A 级入报
    {"case_number": "（2024）京02民终6006号", "court": "北京市第二中级人民法院",
     "decision_date": 20260126, "cause": "9565",
     "title": "高分反向样例（应被方向闸门剔除）", "summary": "事实高度相似但裁判驳回", "score": 1.05},
    # 日期为中文格式；案由给文字
    {"case_number": "（2025）津01民终7007号", "court": "天津市第一中级人民法院",
     "decision_date": "2025年07月24日", "cause": "请求变更公司登记纠纷",
     "title": "正向样例（日期中文格式）", "summary": "样例摘要七", "score": 1.04},
    # 基层法院、得分率同为 100% 但裁判日期最新：用于校验「法院层级 ＞ 裁判日期」
    # （若排序退化为按日期降序，本例会挤掉中级人民法院案例而列首位）
    {"case_number": "（2026）浙0106民初9001号", "court": "杭州市西湖区人民法院",
     "court_level": "基层", "trial_procedure": "一审",
     "decision_date": "2026-03-01", "cause": "请求变更公司登记纠纷",
     "title": "基层高分类案（校验层级优先于日期）", "summary": "样例摘要八", "score": 1.06},
    # 重复入库：同一法院、同一裁判日期、同一标题，仅案号与脱敏称谓不同
    {"case_number": "（2025）浙0602民初522号", "court": "绍兴市越城区人民法院",
     "court_level": "基层", "trial_procedure": "一审",
     "decision_date": "2025-06-24", "cause": "请求变更公司登记纠纷",
     "title": "重复入库样例（同院同日同标题）", "summary": "样例摘要九", "score": 1.03},
    {"case_number": "（2025）浙0602民初540号", "court": "绍兴市越城区人民法院",
     "court_level": "基层", "trial_procedure": "一审",
     "decision_date": "2025-06-24", "cause": "请求变更公司登记纠纷",
     "title": "重复入库样例（同院同日同标题）", "summary": "样例摘要九（重复收录）", "score": 1.03},
]

# 判定表：r1 请求权基础 / r2 法律关系 / r3 案件事实（恒定三要素）
#          r4 结果相似度（仅在 --result-mode specified 时计入）
JUDGED = [
    {"case_number": "（2023）浙01民终1001号", "r1": 3, "r2": 3, "r3": 2, "r4": 2},
    {"case_number": "（2022）浙02民终2002号", "r1": 3, "r2": 2.5, "r3": 1.5, "r4": 2},
    {"case_number": "（2021）浙某某民初3003号", "r1": 2.5, "r2": 2, "r3": 1.5, "r4": 2},
    {"case_number": "（2024）沪01民终4004号", "r1": 1.5, "r2": 2, "r3": 1.5, "r4": 2},
    {"case_number": "（2020）粤03民终5005号", "r1": 0, "r2": 0.5, "r3": 1, "r4": 0.5},
    # 三要素高度相似、但裁判结果相反：未指定结果时应入报；指定结果时应剔除
    {"case_number": "（2024）京02民终6006号", "r1": 3, "r2": 3, "r3": 2, "r4": 0,
     "note": "请求权基础、法律关系、案件事实均高度相似，但裁判结果与检索方向相反"},
    {"case_number": "（2025）津01民终7007号", "r1": 2, "r2": 2.5, "r3": 1.5, "r4": 2},
    # 基层法院三要素满分、裁判日期最新：用于校验排序中「法院层级 ＞ 裁判日期」
    {"case_number": "（2026）浙0106民初9001号", "r1": 3, "r2": 3, "r3": 2, "r4": 2},
    # 重复入库组：两条均三要素满分，但仅有其中一条应占用入报名额
    {"case_number": "（2025）浙0602民初522号", "r1": 3, "r2": 3, "r3": 2, "r4": 2},
    {"case_number": "（2025）浙0602民初540号", "r1": 3, "r2": 3, "r3": 2, "r4": 2},
]

REPORT = {
    "title": "案件检索报告",
    "subtitle": "（样例数据·虚构，仅用于脚本冒烟测试）",
    "result_mode": "unspecified",
    "meta": {
        "检索主题": "买卖合同价款给付与违约责任认定（样例）",
        "检索地域范围": "浙江省（默认）",
        "检索时间范围": "2021-01-01 至 2026-09-22",
        "检索日期": "2026-09-22",
        "数据库": "华宇元典法律数据",
    },
    "overview": [
        "本例为脚本冒烟测试文本，全部内容均为虚构样例，不代表任何真实裁判文书。",
        "检索式与过滤条件如下：案件类别＝民事案件；案由＝买卖合同纠纷；文书类型＝判决书；时间范围＝近五年。",
    ],
    "overview_table": {
        "columns": ["项目", "内容"],
        "rows": [
            ["语义检索调用", "1 次（limit=30）"],
            ["精确检索调用", "0 次（候选充足，未触发兜底）"],
            ["详情调用", "4 次"],
            ["额度消耗", "约 50 点（样例）"],
        ],
    },
    "table": {
        "columns": ["序号", "案号", "审理法院", "裁判日期", "要素匹配度", "语义相关度", "级别", "核心裁判规则"],
        "rows": [
            ["1", "（2023）浙01民终1001号", "浙江省杭州市中级人民法院", "2023-05-18",
             "10.0", "0.91", "A", "样例规则一"],
            ["2", "（2022）浙02民终2002号", "浙江省宁波市中级人民法院", "2022-11-02",
             "9.0", "0.86", "A", "样例规则二"],
            ["3", "（2021）浙某某民初3003号", "某基层人民法院", "2021-07-09",
             "7.5", "0.80", "B", "样例规则三（案号脱敏）"],
            ["4", "（2024）沪01民终4004号", "上海市第一中级人民法院", "2024-03-21",
             "8.0", "0.77", "A", "样例规则四"],
        ],
    },
    "cases": [
        {
            "heading": "案例一　（2023）浙01民终1001号　浙江省杭州市中级人民法院",
            "flags": [],
            "sections": [
                {"label": "基本案情", "text": "样例案情文本（虚构）。"},
                {"label": "裁判要旨", "text": "样例裁判要旨（虚构）。"},
            ],
            "quotes": [{"title": "判词原文摘录（节录）", "text": "样例判词原文（虚构，节录）。"}],
            "analysis": "样例分析意见（虚构），此处应明确标注为分析意见而非裁判原文。",
        },
        {
            "heading": "案例二　（2021）浙某某民初3003号　某基层人民法院",
            "flags": ["案号部分脱敏，援引前须另行核实"],
            "sections": [{"label": "基本案情", "text": "样例案情文本（虚构，脱敏案号）。"}],
            "quotes": [{"title": "判词原文摘录（节录）", "text": "样例判词原文（虚构，节录）。"}],
            "analysis": "样例分析意见（虚构）。",
        },
    ],
    "conclusion": ["样例结论一（虚构）。", "样例结论二（虚构）。"],
    "risk": ["样例风险提示（虚构）。"],
}

FAILURES: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(("  [通过] " if cond else "  [失败] ") + msg)
    if not cond:
        FAILURES.append(msg)


def run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print("  " + proc.stdout.strip().replace("\n", "\n  "))
    if proc.returncode != 0:
        print(proc.stderr.strip())
    return proc.returncode


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cand_path = OUT / "_candidates.json"
    judged_path = OUT / "_judged.json"
    scored_path = OUT / "_scored.json"
    report_path = OUT / "report.json"
    docx_path = OUT / "案件检索报告_样例_20260922.docx"

    cand_path.write_text(json.dumps(CANDIDATES, ensure_ascii=False, indent=2), encoding="utf-8")
    judged_path.write_text(json.dumps({"cases": JUDGED}, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(REPORT, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------- 模式 A：未指定结果（默认）—— 结果相似度不计入 ----------
    print("== 1-A. 打分脚本（未指定结果模式：仅 r1+r2+r3 计入，满分 8） ==")
    rc = run([PY, str(SCRIPTS / "score_fast.py"), "--candidates", str(cand_path),
              "--judged", str(judged_path), "--out", str(scored_path), "--top-n", "8"])
    check(rc == 0, "score_fast.py 退出码为 0")
    if rc != 0:
        return 1

    scored = json.loads(scored_path.read_text(encoding="utf-8"))
    counts = scored["counts"]
    by_no = {r["case_number"]: r for r in scored["cases"]}
    check(scored["mode"] == "unspecified",
          "模式判定为 unspecified（未传 --result-mode 时的保守默认：结果相似度不计入）")
    check(scored["full_score"] == 8.0, "满分 8 分（结果相似度不计入）")
    check(counts["candidates"] == 11, "读入候选 11 条")
    check(counts["deduped"] == 10, "去重后 10 条（重复案号已合并）")
    check(counts["A"] == 6, "A 级 6 例（得分率 ≥80%）")
    check(counts["ah_incomplete"] == 1, "脱敏案号标记 1 例")
    check(counts["negative"] == 0, "未指定结果模式下不判负向（结果非匹配要素）")
    check(counts["duplicate_suspects"] == 1, "疑似重复入库标记 1 例（同院＋同日＋同标题）")

    # 核心：三要素高匹配但结果相反者，未指定结果时**应入报**
    rev = by_no["(2024)京02民终6006号"]
    check(rev["match_score"] == 8.0, "结果相反案例三要素满分 8.0")
    check(rev["match_rate"] == 100.0, "得分率 100%（结果相似度未拉低得分）")
    check(rev["level"] == "A", "未指定结果时该案例为 A 级")
    check(rev["report_eligible"] is True, "未指定结果时该案例入报（用户口径）")
    check(rev["result_note"] != "", "仍记录结果方向供报告标注")

    # 硬门槛：r1 过低者剔除
    low = by_no["(2020)粤03民终5005号"]
    check(low["report_eligible"] is False, "请求权基础 r1=0 者被硬门槛剔除")

    # 接口字段容错
    check(rev["decision_date"] == "2026-01-26", "整型日期 20260126 归一为 2026-01-26")
    check(by_no["(2025)津01民终7007号"]["decision_date"] == "2025-07-24",
          "中文日期「2025年07月24日」归一为 2025-07-24")
    check(rev["cause"] == "", "案由编码 9565 被跳过，不写入报告")
    check(by_no["(2025)津01民终7007号"]["cause"] == "请求变更公司登记纠纷", "案由文字正常取用")

    top = scored["cases"][0]
    check(top["match_rate"] == 100.0, "首位得分率 100%")
    check(top["ah_complete"] is True, "首位案号完整")
    masked = next(r for r in scored["cases"] if not r["ah_complete"])
    check("某某" in masked["case_number"], "脱敏案号被正确识别")
    check(counts["eligible"] == 9, "入报资格 9 例")

    # 排序优先级：得分率 ＞ 法院层级 ＞ 审判程序 ＞ 裁判日期
    order = [r["case_number"] for r in scored["cases"]]
    pos = {no: i for i, no in enumerate(order)}
    check(order[0] != "(2026)浙0106民初9001号",
          "基层法院案例未因裁判日期最新（2026-03-01）而列首位")
    check(pos["(2023)浙01民终1001号"] < pos["(2026)浙0106民初9001号"],
          "同级得分下中级人民法院案例排在基层法院之前（层级优先于日期）")
    check(pos["(2024)京02民终6006号"] < pos["(2026)浙0106民初9001号"],
          "同级得分下中级人民法院案例排在基层法院之前（第二组校验）")
    check(by_no["(2026)浙0106民初9001号"]["court_level"] == "基层",
          "court_level 字段正确落盘")

    # 重复入库：同院＋同日＋同标题，仅保留一条占用入报名额
    sus = [r for r in scored["cases"] if r["duplicate_suspect"]]
    check(len(sus) == 1, "疑似重复入库仅标记 1 例")
    victim = sus[0]
    check(victim["case_number"] in ("(2025)浙0602民初522号", "(2025)浙0602民初540号"),
          "被标记者来自同院同日同标题组")
    keep_no = victim["duplicate_of"]
    check(keep_no in ("(2025)浙0602民初522号", "(2025)浙0602民初540号")
          and keep_no != victim["case_number"], "重复项指向同组保留案号")
    check(by_no[keep_no]["duplicate_suspect"] is False, "保留项未被标记重复")
    check(victim["selected"] is False, "疑似重复项不占用入报名额")
    check(len(scored.get("duplicate_pairs", [])) == 1, "重复对已输出供报告披露")
    check(counts["selected"] == 8, "入报 8 例（重复项已排除，未占用名额）")

    # ---------- 模式 B：指定结果 —— 结果相似度计入 ----------
    print("== 1-B. 打分脚本（指定结果模式：r1+r2+r3+r4 计入，满分 10） ==")
    scored_b_path = OUT / "_scored_specified.json"
    rc = run([PY, str(SCRIPTS / "score_fast.py"), "--candidates", str(cand_path),
              "--judged", str(judged_path), "--out", str(scored_b_path),
              "--result-mode", "specified", "--result-target", "支持涤除登记诉请",
              "--top-n", "8"])
    check(rc == 0, "score_fast.py（specified）退出码为 0")
    if rc != 0:
        return 1

    sb = json.loads(scored_b_path.read_text(encoding="utf-8"))
    cb = sb["counts"]
    by_no_b = {r["case_number"]: r for r in sb["cases"]}
    check(sb["mode"] == "specified", "模式判定为 specified")
    check(sb["full_score"] == 10.0, "满分 10 分（结果相似度计入）")
    check(sb["result_target"] == "支持涤除登记诉请", "指定结果已记录")

    rev_b = by_no_b["(2024)京02民终6006号"]
    check(rev_b["match_score"] == 8.0, "结果相反案例原始总分 8.0（若无闸门即为 A 级）")
    check(rev_b["level"] == "负向", "结果闸门生效：级别判为「负向」")
    check(rev_b["report_eligible"] is False, "结果闸门生效：不得入报")
    check(sb.get("negative_list") == ["(2024)京02民终6006号"],
          "不符案例案号清单已输出，供报告披露")
    check(cb["negative"] == 1, "结果不符计数 1 例")
    check(cb["eligible"] == 8, "指定结果模式下入报资格 8 例")
    check(cb["selected"] == 7, "指定结果模式下入报 7 例（反向 1 例剔除 ＋ 重复 1 例排除）")
    check(by_no_b["(2023)浙01民终1001号"]["match_rate"] == 100.0, "完全匹配案例得分率 100%")

    # ---------- 模式 C：指定结果但漏填 r4 —— 应判「r4缺判」而非「负向」 ----------
    print("== 1-D. 指定结果模式下漏填 r4：应判 r4缺判，不得当作结果相反 ==")
    miss_cand_path = OUT / "_candidates_r4miss.json"
    miss_judged_path = OUT / "_judged_r4miss.json"
    miss_scored_path = OUT / "_scored_r4miss.json"
    miss_cand_path.write_text(json.dumps([
        {"case_number": "（2023）浙01民终1001号", "court": "浙江省杭州市中级人民法院",
         "decision_date": "2023-05-18", "cause": "请求变更公司登记纠纷",
         "title": "已判 r4 的正向样例", "summary": "s1", "score": 0.9},
        {"case_number": "（2023）浙01民终1002号", "court": "浙江省杭州市中级人民法院",
         "decision_date": "2023-06-18", "cause": "请求变更公司登记纠纷",
         "title": "漏填 r4 的样例", "summary": "s2", "score": 0.9},
    ], ensure_ascii=False), encoding="utf-8")
    miss_judged_path.write_text(json.dumps(
        {"result_mode": "specified",
         "cases": [{"case_number": "（2023）浙01民终1001号", "r1": 3, "r2": 3, "r3": 2, "r4": 2},
                   {"case_number": "（2023）浙01民终1002号", "r1": 3, "r2": 3, "r3": 2}]},
        ensure_ascii=False), encoding="utf-8")
    rc = run([PY, str(SCRIPTS / "score_fast.py"), "--candidates", str(miss_cand_path),
              "--judged", str(miss_judged_path), "--out", str(miss_scored_path), "--top-n", "8"])
    check(rc == 0, "score_fast.py（r4 缺判场景）退出码为 0")
    sm = json.loads(miss_scored_path.read_text(encoding="utf-8"))
    by_no_m = {r["case_number"]: r for r in sm["cases"]}
    miss_row = by_no_m["(2023)浙01民终1002号"]
    check(miss_row["level"] == "r4缺判", "漏填 r4 者判为「r4缺判」而非「负向」")
    check(miss_row["r4_missing"] is True, "r4_missing 标记为真")
    check(miss_row["report_eligible"] is False, "r4 缺判者暂不入报")
    check(sm["counts"]["r4_missing"] == 1, "r4 缺判计数 1 例")
    check(sm["counts"]["negative"] == 0, "r4 缺判不计入「结果不符」")
    check(sm.get("negative_list") is None, "r4 缺判者不进入不符清单（不得谎报为结果相反）")
    check(sm.get("r4_missing_list") == ["(2023)浙01民终1002号"], "r4 缺判清单单独输出，供补判")
    check(by_no_m["(2023)浙01民终1001号"]["report_eligible"] is True, "已填 r4 者正常入报")

    # ---------- 旧版字段检测 ----------
    print("== 1-C. 旧版字段（s1–s5）应报错而非静默换算 ==")
    legacy_path = OUT / "_judged_legacy.json"
    legacy_path.write_text(json.dumps(
        {"cases": [{"case_number": "（2023）浙01民终1001号", "s1": 2, "s2": 3, "s3": 2, "s4": 2, "s5": 1}]},
        ensure_ascii=False), encoding="utf-8")
    rc = run([PY, str(SCRIPTS / "score_fast.py"), "--candidates", str(cand_path),
              "--judged", str(legacy_path), "--out", str(OUT / "_scored_legacy.json")])
    check(rc == 3, "旧版 s1–s5 字段被拒绝（退出码 3），禁止静默换算")

    print("== 2. DOCX 生成 ==")
    rc = run([PY, str(SCRIPTS / "build_docx.py"), "--report", str(report_path),
              "--out", str(docx_path)])
    check(rc == 0, "build_docx.py 退出码为 0")
    if rc != 0:
        return 1
    check(docx_path.exists(), f"DOCX 已生成：{docx_path.name}")

    from docx import Document
    doc = Document(str(docx_path))
    check(len(doc.tables) == 3, "表格 3 张（头部五项 ＋ 检索概况 ＋ 一览表）")
    empty = [(ti, ri, ci) for ti, t in enumerate(doc.tables) for ri, row in enumerate(t.rows)
             for ci, cell in enumerate(row.cells) if not cell.text.strip()]
    check(not empty, "所有表格单元格非空")
    check(doc.tables[2].rows.__len__() == 5, "一览表 5 行（表头 ＋ 4 例）")

    footer_xml = doc.sections[0].footer.paragraphs[0]._p.xml
    check("PAGE" in footer_xml, "页脚含 PAGE 域")
    check("NUMPAGES" in footer_xml, "页脚含 NUMPAGES 域")

    full_text = "\n".join(p.text for p in doc.paragraphs)
    check("声明一-A（未指定结果模式）" in full_text, "固定声明一-A 在位（unspecified 模式）")
    check("声明一-B" not in full_text, "未指定结果模式下不出现声明一-B")
    check("声明二（案号与判词局限）" in full_text, "固定声明二在位")
    check("【分析意见】" in full_text, "分析意见标注在位")
    check("案号部分脱敏" in full_text, "脱敏警示标注在位")
    check("三要素" in full_text and "满分 8 分" in full_text,
          "一览表脚注按未指定结果模式写明「三要素／满分 8 分」")
    check("四要素" not in full_text and "满分 10 分" not in full_text,
          "未指定结果模式下不出现四要素／满分 10 分表述")

    # 声明一按匹配模式切换
    rep_b = dict(REPORT)
    rep_b["result_mode"] = "specified"
    rep_b_path = OUT / "report_specified.json"
    rep_b_path.write_text(json.dumps(rep_b, ensure_ascii=False, indent=2), encoding="utf-8")
    docx_b_path = OUT / "案件检索报告_样例_指定结果模式.docx"
    run([PY, str(SCRIPTS / "build_docx.py"), "--report", str(rep_b_path),
         "--out", str(docx_b_path)])
    txt_b = "\n".join(p.text for p in Document(str(docx_b_path)).paragraphs)
    check("声明一-B（指定结果模式）" in txt_b, "指定结果模式下声明一-B 在位")
    check("声明一-A" not in txt_b, "指定结果模式下不出现声明一-A")
    check("四要素" in txt_b and "满分 10 分" in txt_b,
          "一览表脚注按指定结果模式写明「四要素／满分 10 分」")

    print("\n== 结果 ==")
    if FAILURES:
        print(f"失败 {len(FAILURES)} 项：")
        for item in FAILURES:
            print("  - " + item)
        return 1
    print("全部通过。样例输出位于：" + str(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
