#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
律审·合同审查1.0 · 公共校验模块（_checks.py）
============================================================
用途：step_gate.py（顺序闸门）与 validate_output.py（终检）共享的**单一校验实现**。
      P1-1 修复：消除双实现——任何规则升级只改本文件一处，两闸门口径自动一致，
      不再出现「同一份交付物 step_gate PASS 但 validate FAIL」的分叉。

对外函数：
  section_between(content, start_kws, end_kws=None)  章节区间截取（多关键词/正则，P2-1/P2-3 模糊定位）
  count_table_rows(content)                         逐条表数据行数
  collect_risk_numbers(part)                        风险编号集合（表格首列 + 列表 ^N[.、] 合并，P2-2）
  count_risk_numbers(part)                          上述编号总数
  count_light_heads(part, light)                    「### 🔴/🟠」修改建议标题数
  risk_section_between(content)                     风险分级清单章节定位（多别名，P2-1 堵改名逃逸）
  gate_elements / gate_table / gate_suggestions / gate_checklist
                                                    四关判定（G1-G4 = V7/V6/V8/V9 共用，P1-1）
  pii_hits_of(text)                                 脱敏检测（V13/R5 共用，P2-4 收紧版）

被引用方：step_gate.py、validate_output.py、release_check.py（仅 import，不重复实现）。
本模块仅供同目录脚本内部 import，不作为独立入口，不参与 preflight P7 脚本清单。
"""

import re

# ── 常量（G1/G4 = V7/V9 共用） ─────────────────────────────────────────
ELEMENT_KEYWORDS = ["合同金额", "合同期限", "付款方式", "管辖", "交付物", "附件", "合同名称"]
CHECKLIST_MARKS_MIN = 25

# ── 章节定位（P2-1 多别名，堵「章节改名即豁免」逃逸） ────────────────────
RISK_SECTION_STARTS = [
    re.compile(r"风险[分级]{0,2}清单"),   # 风险清单 / 风险分级清单
    re.compile(r"风险.{0,4}清单"),        # 风险问题清单 / 风险点清单 …
    re.compile(r"风险分级"),             # 兜底
]
RISK_SECTION_ENDS = ["修改建议"]        # 风险区间截止于修改建议章节
SUGGEST_SECTION_ENDS = ["核对清单", "自校验", "复盘"]
# P2-3：自校验段截断关键词（标题行，兼容「## 七、复盘」式带章节号标题）
SELFCHECK_SECTION_ENDS = re.compile(r"^##[^\n]*(?:复盘|输出|交付|修订闭环)", re.M)


def section_between(content: str, start_kws, end_kws=None) -> str:
    """定位区间：start 取 start_kws 首个命中（支持 str 或 re.Pattern）；
    end 取 end_kws 中首个出现且位于 start 之后者；均未命中则返回 start 至文末。"""
    start = -1
    for kw in start_kws:
        if isinstance(kw, re.Pattern):
            m = kw.search(content)
            if m:
                start = m.start()
                break
        else:
            s = content.find(kw)
            if s >= 0:
                start = s
                break
    if start < 0:
        return ""
    if not end_kws:
        return content[start:]
    ends = [content.find(e, start + 1) for e in end_kws]
    ends = [e for e in ends if e >= 0]
    if not ends:
        return content[start:]
    return content[start:min(ends)]


def risk_section_between(content: str) -> str:
    """风险分级清单章节定位（P2-1：多别名模糊匹配，找不到返回空串由调用方判 FAIL）。"""
    return section_between(content, RISK_SECTION_STARTS, RISK_SECTION_ENDS)


def count_table_rows(content: str) -> int:
    """统计逐条表数据行数（表格行中以条款性内容开头的行）。"""
    rows = 0
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("|") and s.count("|") >= 3:
            # 排除表头分隔行和纯表头行
            if re.match(r"^\|[\s:|-]+\|$", s):
                continue
            if "条款号" in s or "条款" == s.strip("| ").strip():
                continue
            rows += 1
    return rows


_LIST_NUM_RE = re.compile(r"^\s*(\d{1,3})[.、]\s*(?!\d)", re.M)
_TABLE_NUM_RE = re.compile(r"^\|\s*(\d{1,3})\s*\|", re.M)


def collect_risk_numbers(part: str) -> list:
    """收集风险清单编号：表格首列数字 + 非表格列表编号（^N[.、]，排除 N.N 层级号）。
    P2-2：AI 改用列表格式列风险清单时编号检查不再整体绕过。"""
    nums = set()
    nums.update(int(m) for m in _TABLE_NUM_RE.findall(part))
    nums.update(int(m) for m in _LIST_NUM_RE.findall(part))
    return sorted(nums)


def count_risk_numbers(part: str) -> int:
    """风险编号总数（表格 + 列表合并，P2-2）。"""
    return len(collect_risk_numbers(part))


def count_light_heads(part: str, light: str) -> int:
    """统计段落中「### 🔴/🟠」修改建议标题数。"""
    return len(re.findall(rf"^###\s*{light}", part, re.M))


# ── 四关判定（G1-G4 = V7/V6/V8/V9 共用，P1-1 单实现） ───────────────────
def gate_elements(content: str):
    has = "要素提取" in content
    hits = sum(1 for k in ELEMENT_KEYWORDS if k in content)
    return has and hits >= 5, f"要素提取章节={'有' if has else '无'}，要素词命中 {hits}/{len(ELEMENT_KEYWORDS)}"


def gate_table(content: str, clause_count):
    rows = count_table_rows(content)
    return rows >= clause_count, f"逐条表 {rows} 行 vs 提取条款 {clause_count} 条"


def gate_suggestions(content: str):
    risk_section = risk_section_between(content)
    if not risk_section:
        # P2-1：找不到风险清单章节 = FAIL（堵「改名即跳过」逃逸），不再静默放行
        return False, "未定位到风险分级清单章节（输出须含「风险分级清单/风险分级/风险…清单」标题）"
    has_group_headers = ("### 🔴" in risk_section) and ("### 🟠" in risk_section)
    total_n = count_risk_numbers(risk_section)
    red_part = section_between(risk_section, ["### 🔴"], ["### 🟠"])
    orange_part = section_between(risk_section, ["### 🟠"], ["### 🟢"])
    red_n = count_risk_numbers(red_part)
    orange_n = count_risk_numbers(orange_part)
    suggest_section = section_between(content, ["修改建议"], SUGGEST_SECTION_ENDS)
    red_heads = count_light_heads(suggest_section, "🔴")
    orange_heads = count_light_heads(suggest_section, "🟠")
    if total_n == 0:
        return True, "未检测到风险清单编号（跳过）"
    if not has_group_headers:
        return False, "风险清单未按 ### 🔴/🟠/🟢 三级分组（违反输出规范，无法核验覆盖度）"
    return (red_heads >= red_n and orange_heads >= orange_n), \
        f"风险清单 🔴{red_n}/🟠{orange_n} vs 修改建议 🔴{red_heads}/🟠{orange_heads}"


def gate_checklist(content: str):
    has = "核对清单" in content
    marks = len(re.findall(r"\|\s*(✅|⚠️)\s*\|", content))
    return has and marks >= CHECKLIST_MARKS_MIN, \
        f"核对清单章节={'有' if has else '无'}，结果标记 {marks} 处（需≥{CHECKLIST_MARKS_MIN}）"


# ── 脱敏检测（V13/R5 共用，P2-4 收紧版） ───────────────────────────────
_ID_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
_ID_CHECK_CHARS = "10X98765432"


def _id_checksum_ok(id17: str, check: str) -> bool:
    """GB 11643 身份证校验位合法性 + 出生日期段合理性（P2-4：拦截日期戳/单号误报）。"""
    if len(id17) != 17 or not id17.isdigit():
        return False
    year, month, day = int(id17[6:10]), int(id17[10:12]), int(id17[12:14])
    if not (1900 <= year <= 2026 and 1 <= month <= 12 and 1 <= day <= 31):
        return False
    s = sum(int(d) * w for d, w in zip(id17, _ID_WEIGHTS)) % 11
    return _ID_CHECK_CHARS[s] == check.upper()


def pii_hits_of(text: str) -> dict:
    """剔除 URL 后检测 PII，返回 {类型: [样例…]}。
    P2-4 收紧：手机号前后非数字且前缀非字母（SN138… 序列号不误报）、精确 11 位；
    银行卡限 16/19 位两档（排除 17/18 位身份证字段）；
    身份证须校验位合法 + 出生日期段合理（大幅降低 18 位日期戳/单号误报）。"""
    no_urls = re.sub(r"https?://\S+", " [URL] ", text)
    hits = {}
    phones = re.findall(r"(?<![\dA-Za-z])1[3-9]\d{9}(?!\d)", no_urls)
    if phones:
        hits["手机号"] = phones[:3]
    id_hits = []
    for m in re.finditer(r"(?<!\d)(\d{17})([\dXx])(?!\d)", no_urls):
        if _id_checksum_ok(m.group(1), m.group(2)):
            id_hits.append(m.group(0))
    if id_hits:
        hits["身份证"] = id_hits[:3]
    banks = re.findall(r"(?<!\d)(?:\d{16}|\d{19})(?!\d)", no_urls)
    if banks:
        hits["银行卡"] = banks[:3]
    return hits
