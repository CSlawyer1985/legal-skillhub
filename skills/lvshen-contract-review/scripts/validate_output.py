#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
律审·合同审查1.0 · 交付物校验脚本（Deliverable Validator）
============================================================
用途：审查交付物（AI 将交付主体写入文件后）运行，客观校验格式、完整性与内容深度。
规则：输出 FAIL 或未运行 = 交付物不得视为完成，须修正后重跑直至 PASS。
判定逻辑与 step_gate 共用 scripts/_checks.py（P1-1 修复：单实现双入口，
杜绝「step_gate PASS 但 validate FAIL」的口径分叉）。
校验项（V1-V14）：
  V1-V6 格式校验：逐条表存在/自校验清单/风险编号连续/无禁用内部术语/修订方式标注/逐条表行数比对
  V7-V10 内容深度校验：要素提取表/5字段覆盖度/核对清单（含主体核验留痕）/自校验证据化（拦截交付物深度不足）
  V11 证据链留痕（交付物须含 step_gate PASS + validate PASS 运行标记）
  V12 四件套章节顺序（要素提取→逐条→修改建议→核对清单→自校验 标题位置递增）
  V13 脱敏闸门（检测手机号/身份证/银行卡等 PII，命中即 FAIL）
  V14 交叉引用校验（「问题N/🔴N/🟠N/附件X」引用须真实存在锚点，防编号重排后悬空引用/附件缺条）
用法：python3 validate_output.py <交付物文件路径> [-c 条款数] [--no-pii]
      --no-pii：跳过 V13 脱敏检测（内部审查场景显式豁免，须在自校验声明理由）
退出码：0=PASS；1=FAIL；2=用法错误。
"""

import os
import re
import sys

# 单实现双入口（P1-1）：判定逻辑唯一源为 _checks.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _checks import (  # noqa: E402
    SELFCHECK_SECTION_ENDS,
    collect_risk_numbers,
    gate_checklist,
    gate_elements,
    gate_suggestions,
    gate_table,
    pii_hits_of,
    risk_section_between,
)

FORBIDDEN = ["TC/CM", "R-01", "O-01", "回链"]
REVISION = ["可直接修订", "须商业协商"]
FAST_MODE_MARK = "快审"
VAGUE_SELFCHECK = ["全过", "均给出", "全部完成"]
PII_EXEMPT_NOTE = "已用 --no-pii 显式豁免（自校验须声明理由）"


def main():
    args = [a for a in sys.argv[1:]]
    clause_count = None
    no_pii = "--no-pii" in args
    if no_pii:
        args = [a for a in args if a != "--no-pii"]
    if "-c" in args:
        idx = args.index("-c")
        try:
            clause_count = int(args[idx + 1])
            args = args[:idx] + args[idx + 2:]
        except (ValueError, IndexError):
            print("用法: python3 validate_output.py <交付物文件路径> [-c 条款数]")
            sys.exit(2)
    if len(args) < 1:
        print("用法: python3 validate_output.py <交付物文件路径> [-c 条款数]")
        sys.exit(2)
    path = args[0]
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:  # noqa: BLE001
        print(f"无法读取文件: {e}")
        sys.exit(2)

    is_fast = FAST_MODE_MARK in content
    checks = []  # (name, ok, detail)

    # V1 逐条表存在
    has_table = ("逐条" in content) or ("条款号" in content and "结论" in content)
    checks.append(("V1 逐条表存在（覆盖首部至签署页）", has_table,
                   "检测到逐条表标记" if has_table else "未检测到逐条表（最小交付物缺失）"))

    # V2 自校验清单存在且含产出物指向
    has_selfcheck = "自校验" in content and ("✅" in content or "已" in content)
    checks.append(("V2 自校验清单存在且含产出物指向", has_selfcheck,
                   "检测到自校验标记" if has_selfcheck else "未检测到自校验清单"))

    # V3 风险编号连续（无跳号）——风险清单章节内 表格+列表 编号合并（P2-2）
    risk_section = risk_section_between(content)
    nums = collect_risk_numbers(risk_section)
    if len(nums) >= 2:
        expected = list(range(1, max(nums) + 1))
        missing_nums = [n for n in expected if n not in nums]
        checks.append(("V3 风险编号连续（无跳号）", not missing_nums,
                       f"检测到编号 1-{max(nums)}" if not missing_nums else f"跳号/缺失: {missing_nums}"))
    else:
        checks.append(("V3 风险编号连续（无跳号）", True, "未检测到风险清单编号（跳过）"))

    # V4 禁用内部术语
    found_forbidden = [t for t in FORBIDDEN if t in content]
    checks.append(("V4 无禁用内部术语/字母编码", not found_forbidden,
                   "通过" if not found_forbidden else f"命中禁用术语: {found_forbidden}"))

    # V5 修订方式标注（快审档位跳过）
    if is_fast:
        checks.append(("V5 修订方式标注（可直接修订/须商业协商）", True, "快审档位，跳过"))
    else:
        missing_rev = [r for r in REVISION if r not in content]
        checks.append(("V5 修订方式标注（可直接修订/须商业协商）", not missing_rev,
                       "双轨标注全命中" if not missing_rev else f"缺失: {missing_rev}"))

    # V6 逐条表行数 vs extract_clauses 条款数比对（= G2 共用）
    if clause_count is not None:
        v6_ok, v6_detail = gate_table(content, clause_count)
        checks.append((f"V6 逐条表行数≥提取条款数（{v6_detail}）", v6_ok,
                       "全覆盖" if v6_ok else "逐条表行数不足，疑似漏条款"))
    else:
        checks.append(("V6 逐条表行数≥提取条款数", True, "未提供 -c 条款数（跳过比对）"))

    # ---- 内容深度闸门 ----

    # V7 要素提取表存在（= G1 共用）
    v7_ok, v7_detail = gate_elements(content)
    checks.append(("V7 要素提取表存在（含关键要素词）", v7_ok, v7_detail))

    # V8 5字段覆盖度：修改建议「### 🔴/🟠」标题数 ≥ 风险分级清单中🔴🟠编号数（= G3 共用，P2-1/P2-2）
    v8_ok, v8_detail = gate_suggestions(content)
    checks.append(("V8 5字段覆盖度（🔴🟠逐条有建议）", v8_ok, v8_detail))

    # V9 核对清单存在（= G4 共用）+ 主体核验留痕（P2-5）
    v9_ok, v9_detail = gate_checklist(content)
    if "主体核验" in content:
        # P2-5：含主体核验字样时，须有留痕之一：
        # ①「✅已通过[工具]核验」②「主体核验降级记录」③核对清单行「| N | 主体核验 | ✅ |」，
        # 防「MCP 缺失 → 口头转人工」的无痕降级（交付物须留痕供委托人/后续复核）。
        has_proof = bool(re.search(
            r"✅已通过.{0,20}核验|主体核验降级记录|^\|\s*\d{1,3}\s*\|\s*主体核验\s*\|\s*✅",
            content, re.M))
        if not has_proof:
            v9_ok = False
            v9_detail += "；主体核验无留痕（须含「✅已通过[工具]核验」或「主体核验降级记录」或核对清单行「主体核验|✅」）"
    checks.append(("V9 核对清单存在（逐项结果）", v9_ok, v9_detail))

    # V10 自校验证据化：自校验段含具体条款引用 ≥ 3 处，且无「全过」空泛词
    # P2-3：截断改用「二级标题关键词」（复盘/输出/交付/修订闭环）首个匹配，防正文误截
    selfcheck_heads = list(re.finditer(r"^##.*自校验", content, re.M))
    start = selfcheck_heads[-1].start() if selfcheck_heads else content.rfind("自校验")
    section = content[start:] if start >= 0 else ""
    sc_end = SELFCHECK_SECTION_ENDS.search(section)
    if sc_end:
        section = section[:sc_end.start()]
    specific_refs = len(re.findall(r"(?:🔴|🟠|🟢)\s*\d+|第\s*\d+\s*条|[一二三四五六七八九十]+\.\d+", section))
    vague_hits = [w for w in VAGUE_SELFCHECK if w in section]
    checks.append(("V10 自校验证据化（具体指向+无空泛词）",
                   ("自校验" in content) and specific_refs >= 3 and not vague_hits,
                   f"自校验段具体引用 {specific_refs} 处（需≥3）" + (f"，空泛词命中: {vague_hits}" if vague_hits else "")))

    # ---- 证据链 / 顺序 / 脱敏闸门 ----

    # V11 证据链留痕：交付物须含脚本运行证据标记（step_gate PASS + validate PASS）
    has_sg_evidence = ("step_gate" in content) and ("PASS" in content)
    has_v_evidence = ("validate" in content) and ("PASS" in content)
    checks.append(("V11 证据链留痕（step_gate/validate 运行标记）",
                   has_sg_evidence and has_v_evidence,
                   "双脚本运行标记齐备" if (has_sg_evidence and has_v_evidence)
                   else f"缺失: {'step_gate' if not has_sg_evidence else ''}{'、' if (not has_sg_evidence and not has_v_evidence) else ''}{'validate' if not has_v_evidence else ''}运行标记"))

    # V12 四件套章节顺序（标题位置递增：要素提取→逐条→修改建议→核对清单→自校验）
    def title_pos(kw):
        m = re.search(r"^##.*" + re.escape(kw), content, re.M)
        return m.start() if m else -1

    sc_matches = list(re.finditer(r"^##.*自校验", content, re.M))
    sc_pos = sc_matches[-1].start() if sc_matches else -1
    positions = [title_pos("要素提取"), title_pos("逐条"), title_pos("修改建议"),
                 title_pos("核对清单"), sc_pos]
    ordered = all(p >= 0 for p in positions) and all(positions[i] < positions[i + 1] for i in range(4))
    pos_detail = " → ".join([str(p) if p >= 0 else "缺" for p in positions])
    checks.append(("V12 四件套章节顺序（要素→逐条→建议→核对→自校验）",
                   ordered,
                   f"标题位置: {pos_detail}" if not ordered else f"顺序正确（{pos_detail}）"))

    # V13 脱敏闸门：检测常见 PII 模式（手机号/身份证/银行卡）；--no-pii 显式豁免
    # P2-4：收紧正则（手机号前后非数字、银行卡 16/19 两档、身份证校验位+出生日期段校验）
    if no_pii:
        checks.append((("V13 脱敏闸门（PII 检测）"), True, PII_EXEMPT_NOTE))
    else:
        pii_hits = pii_hits_of(content)
        checks.append(("V13 脱敏闸门（PII 检测）", not pii_hits,
                       "未检测到 PII" if not pii_hits else f"命中: {pii_hits}（须替换为【已脱敏】）"))

    # V14 交叉引用校验：扫描「问题 N」「🔴NN/🟠NN」「附件X」引用，验证被引用对象真实存在（防编号重排后引用断裂/附件缺条）
    ref_pattern = re.compile(r"(?:问题|🔴|🟠|🟢)\s*(\d{1,2})")
    refs = sorted(set(int(m) for m in ref_pattern.findall(content)))
    # 收集文中真实存在的目标锚点：①「### 🔴/🟠/🟢 NN.」标题 ②「**问题 N（」标题 ③「| N |」表格行 ④「NN. 条款定位」式列表
    anchors = set()
    anchors.update(int(m) for m in re.findall(r"^###\s*(?:🔴|🟠|🟢)\s*(\d{1,2})[\.、]", content, re.M))
    anchors.update(int(m) for m in re.findall(r"^\*\*问题\s*(\d{1,2})[（(]", content, re.M))
    anchors.update(int(m) for m in re.findall(r"^\|\s*(\d{1,2})\s*\|", content, re.M))
    anchors.update(int(m) for m in re.findall(r"^\s*(\d{1,2})[\.、]\s*(?:条款|问题|①|【)", content, re.M))
    # 附件章节引用校验：文中引用「附件一/附件2」，须存在对应「## 附件X」章节标题
    # 排除文号误报：紧邻「号」后的「附件N」（如财税〔2016〕36号附件1）系文号组成部分，不算附件章节引用
    attach_refs = set(re.findall(r"(?<!号)附件([一二三四五六七八九十\d])", content))
    attach_anchors = set(re.findall(r"^#+\s*附件([一二三四五六七八九十\d])", content, re.M))
    missing_attach = sorted(a for a in attach_refs if a not in attach_anchors)
    # 数字引用缺失判定：「问题N/🔴N」被引用但全文无该编号锚点
    missing_refs = sorted(r for r in refs if r not in anchors)
    if missing_refs:
        v14_ok, v14_detail = False, f"悬空引用（文中无对应锚点）: {missing_refs}"
    elif missing_attach:
        v14_ok, v14_detail = False, f"附件引用断裂（引用附件{missing_attach}但无对应章节）"
    else:
        v14_ok, v14_detail = True, f"引用 {len(refs)} 处、附件 {len(attach_refs)} 处，锚点齐备"
    checks.append(("V14 交叉引用校验（引用编号/附件真实存在）", v14_ok, v14_detail))

    # 汇总
    fails = [c for c in checks if not c[1]]
    print("=" * 58)
    print("律审·合同审查1.0 交付物校验（Deliverable Validator）")
    print("=" * 58)
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        if detail:
            print(f"      └─ {detail}")
    print("-" * 58)
    if fails:
        print(f"总体状态: FAIL（{len(fails)} 项未过）→ 须修正后重跑，交付物不得视为完成")
        sys.exit(1)
    print("总体状态: PASS → 交付物格式与内容深度校验通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
