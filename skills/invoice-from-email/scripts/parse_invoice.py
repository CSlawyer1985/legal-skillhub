# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票文本结构化解析脚本 v2

从 ocr_extract.py 输出的 Markdown 文本中提取结构化字段，输出 JSON。
支持三类文档：电子发票、行程单、火车票。

v2 改进：
  - 跨行标签值匹配（处理 PDF 文字层标签与值分离的问题）
  - 类型检测修复（T2 航站楼不再误判为火车票）
  - 新增 warnings 字段标注数据质量问题

用法：
  python parse_invoice.py <input.md> [-o output.json]
"""

import sys
import os
import re
import json


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def clean_amount(s: str) -> float:
    s = s.replace("¥", "").replace("￥", "").replace(",", "").replace("，", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def clean_date(s: str) -> str:
    s = s.strip()
    m = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', s)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    m = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', s)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    return s


def flatten_text(text: str) -> str:
    """
    将多行文本压平：去掉行内多余空格，合并空行，保留换行。
    同时生成一个"合并版"——相邻行用空格拼接，解决标签和值分两行的问题。
    返回 (original, merged) 两个版本。
    """
    lines = [l.strip() for l in text.split("\n")]
    # 过滤掉纯分隔符行
    lines = [l for l in lines if l and not re.match(r'^[-=_]{3,}$', l)]

    original = "\n".join(lines)

    # merged: 相邻行合并（中间加空格），使跨行标签-值回到同一行
    merged_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # 如果当前行看起来像标签（以中文/英文词结尾，无数字/¥），且下一行是值
        if i + 1 < len(lines) and _is_label(line) and _is_value_line(lines[i + 1]):
            merged_lines.append(line + " " + lines[i + 1])
            i += 2
        else:
            merged_lines.append(line)
            i += 1
    merged = "\n".join(merged_lines)

    return original, merged


def _is_label(line: str) -> bool:
    """判断一行是否为标签（不含金额、不含纯数字、不以日期开头）"""
    if re.search(r'[¥￥]\s*\d', line):
        return False
    if re.match(r'^[\d\s,.]+$', line):
        return False
    if re.match(r'^\d{4}[-/年]', line):
        return False
    # 标签通常较短，以中文或特定英文词结尾
    return len(line) < 50 and bool(re.search(r'[：:。、】)]$', line) or re.search(r'[号码日期名称额率方]$', line))


def _is_value_line(line: str) -> bool:
    """判断一行是否为值（含数字、含¥、或为长串数字）"""
    if re.search(r'[¥￥]\s*\d', line):
        return True
    if re.match(r'^\d{8,}$', line):  # 发票号码
        return True
    if re.match(r'^\d{4}\s*年', line):  # 日期
        return True
    if re.search(r'\d{18}', line):  # 统一社会信用代码
        return True
    return False


def find_amounts_with_labels(text: str) -> dict:
    """
    从文本中提取所有 ¥ 金额及其前面最近的标签行。
    返回 {label: amount, ...}
    """
    lines = text.split("\n")
    pairs = {}
    prev_label = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        amount_m = re.search(r'[¥￥]\s*([\d,.]+)', stripped)
        if amount_m:
            if prev_label:
                key = prev_label.strip().rstrip("：:").strip()
                pairs[key] = clean_amount(amount_m.group(1))
                prev_label = ""
            else:
                pairs[f"_amount_{len(pairs)}"] = clean_amount(amount_m.group(1))
            continue

        # 不是金额行，记录为下一个金额的标签
        if not re.match(r'^\d{4}[-/年]', stripped) and not re.match(r'^[\d\s,.]+$', stripped):
            prev_label = stripped

    return pairs


def search_multiline(text: str, label: str, value_pattern: str, max_lines: int = 3) -> str:
    """
    跨行搜索标签对应的值。
    先在 original 文本中搜索同行的，然后在 merged 文本中搜索。
    如果都失败，在原始文本中找标签行，扫描后续 N 行。
    """
    # 先试直接匹配（同在一行）
    pat = re.compile(f'{label}[：:]*\\s*({value_pattern})')
    m = pat.search(text)
    if m:
        return m.group(1).strip()

    # 在原始文本中找标签位置，向下扫描
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if label in line:
            for j in range(i + 1, min(i + max_lines + 1, len(lines))):
                m = re.search(value_pattern, lines[j])
                if m:
                    return m.group(1).strip()
            break

    return ""


# ── 电子发票解析 ─────────────────────────────────────────────────────────────

def parse_invoice(text: str, filename: str, merged: str) -> dict:
    warnings = []
    result = {
        "type": "invoice",
        "file": filename,
        "invoice_number": "",
        "invoice_date": "",
        "seller_name": "",
        "amount_excluding_tax": 0.0,
        "tax_amount": 0.0,
        "total_amount": 0.0,
    }

    # 发票号码（长数字串，>= 16 位，排除银行账号等短号）
    # 策略：扫描全文找最长的纯数字串（>= 16 位）
    all_nums = re.findall(r'\b(\d{12,})\b', merged)
    candidate = ""
    for n in all_nums:
        if len(n) >= 16 and len(n) > len(candidate):
            candidate = n
    if candidate:
        result["invoice_number"] = candidate
    else:
        # 回退到跨行搜索
        inv_no = search_multiline(text, "发票号码", r'(\d{10,})', max_lines=60)
        if inv_no and len(inv_no) >= 10:
            result["invoice_number"] = inv_no
    if not result["invoice_number"]:
        inv_no = search_multiline(text, "发票号码", r'(\d{10,})', max_lines=60)
        if inv_no:
            result["invoice_number"] = inv_no

    # 开票日期：先跨行搜，再全文扫日期模式
    date_str = search_multiline(text, "开票日期", r'(.+?)(?:\n|$)', max_lines=60)
    if date_str:
        result["invoice_date"] = clean_date(date_str)
    if not result["invoice_date"]:
        for line in merged.split("\n"):
            m = re.search(r'(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)', line)
            if m:
                result["invoice_date"] = clean_date(m.group(1))
                break

    # 销售方名称（含"公司"的完整名称）
    seller = search_multiline(text, "销售方名称", r'(.+?公司)')
    if not seller:
        for pat in [r'名称[：:]\s*(.+?公司)', r'销售方[：:]\s*(.+?公司)']:
            m = re.search(pat, merged)
            if m:
                seller = m.group(1).strip()
                break
    if seller:
        result["seller_name"] = seller

    # 金额：用标签-金额配对 + 直接扫描所有 ¥ 金额
    amounts = find_amounts_with_labels(merged)
    for key, val in amounts.items():
        kl = key.lower().replace(" ", "")
        if "价税合计" in kl or "合计" in kl or key == "价税合计（小写）":
            if val > result["total_amount"]:
                result["total_amount"] = val
        if ("金额" in kl and "不含" in kl) or "不含税" in kl:
            result["amount_excluding_tax"] = val
        if "税额" in kl:
            result["tax_amount"] = val

    if result["total_amount"] == 0.0 and amounts:
        result["total_amount"] = max(amounts.values())

    # 如果标签匹配不到不含税/税额，用所有金额推算
    # 电子发票格式：金额（不含税）、税额、价税合计 三个值依次出现
    if result["amount_excluding_tax"] == 0.0 or result["tax_amount"] == 0.0:
        all_amounts = sorted([v for v in amounts.values() if v > 0], reverse=True)
        if len(all_amounts) >= 3:
            # 最大的是价税合计，其次两个是不含税和税额
            if result["total_amount"] == 0.0:
                result["total_amount"] = all_amounts[0]
            remaining = [a for a in all_amounts if a != result["total_amount"]]
            if remaining and result["amount_excluding_tax"] == 0.0:
                result["amount_excluding_tax"] = max(remaining)
                remaining = [a for a in remaining if a != result["amount_excluding_tax"]]
            if remaining and result["tax_amount"] == 0.0:
                result["tax_amount"] = max(remaining)

    # 质量检查
    if not result["invoice_number"]:
        warnings.append("未提取到发票号码")
    if not result["invoice_date"]:
        warnings.append("未提取到开票日期")
    if not result["seller_name"]:
        warnings.append("未提取到销售方名称")
    if result["amount_excluding_tax"] == 0.0 and result["tax_amount"] == 0.0:
        warnings.append("未提取到不含税金额和税额")

    if warnings:
        result["warnings"] = warnings

    return result


# ── 行程单解析 ───────────────────────────────────────────────────────────────

def parse_itinerary(text: str, filename: str, merged: str) -> dict:
    warnings = []
    result = {
        "type": "itinerary",
        "file": filename,
        "date": "",
        "time": "",
        "departure": "",
        "destination": "",
        "vehicle": "",
        "amount": 0.0,
    }

    # 日期时间：从行程时间行提取
    m = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', text)
    if m:
        result["date"] = m.group(1)
        result["time"] = m.group(2)
    else:
        m = re.search(r'申请时间[：:]\s*(\d{4}-\d{2}-\d{2})', text)
        if m:
            result["date"] = m.group(1)

    # 从表格数据中提取行程详情：服务商、车型、上车时间、起点、终点、金额
    # 高德行程单格式：序号 / 服务商 / 车型 / 上车时间 / 城市 / 起点 / 终点 / 金额
    # 数据在表格行中，用数字序号开头
    trip_m = re.search(
        r'(\d+)\s*\n\s*(\S+)\s*\n\s*(\S+)\s*\n\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*\n\s*(\S+市)\s*\n\s*(.+?)\s*\n\s*(.+?)\s*\n\s*(\d+\.?\d*)元',
        text
    )
    if trip_m:
        result["vehicle"] = trip_m.group(3)  # 车型
        if not result["time"]:
            result["time"] = trip_m.group(4).split()[-1] if " " in trip_m.group(4) else ""
        result["departure"] = trip_m.group(6).strip()
        result["destination"] = trip_m.group(7).strip()
        result["amount"] = float(trip_m.group(8))

    # 如果表格匹配失败，用简单字段匹配
    if not result["departure"]:
        for line in text.split("\n"):
            stripped = line.strip()
            if not result["vehicle"]:
                m = re.search(r'(经济型|特惠快车|快车|专车|优享|拼车|顺风车|出租车)', stripped)
                if m:
                    result["vehicle"] = m.group(1)

    # 金额（如果表格未提取到）
    if result["amount"] == 0.0:
        amounts = find_amounts_with_labels(text)
        for key, val in amounts.items():
            kl = key.lower().replace(" ", "")
            if any(kw in kl for kw in ["合计", "实付", "金额", "总价", "应付"]):
                result["amount"] = val
                break
        if result["amount"] == 0.0 and amounts:
            result["amount"] = max(amounts.values())

    # 质量检查
    if not result["departure"] and not result["destination"]:
        warnings.append("未提取到行程起终点")
    if not result["time"]:
        warnings.append("未提取到行程时间")

    if warnings:
        result["warnings"] = warnings

    return result


# ── 火车票解析 ───────────────────────────────────────────────────────────────

def parse_train_ticket(text: str, filename: str, merged: str) -> dict:
    warnings = []
    result = {
        "type": "train",
        "file": filename,
        "train_number": "",
        "departure_date": "",
        "departure_time": "",
        "departure_station": "",
        "arrival_station": "",
        "seat_type": "",
        "amount": 0.0,
    }

    # 车次
    m = re.search(r'([GDCKZ]\d{1,5})', text)
    if m:
        # 排除 "T2" 航站楼：T2 后面跟的不是数字而是航站楼相关文字
        candidate = m.group(1)
        ctx_start = max(0, m.start() - 5)
        ctx_end = min(len(text), m.end() + 10)
        ctx = text[ctx_start:ctx_end]
        if not re.search(r'航站楼|航站|Terminal|T\d\s*航', ctx):
            result["train_number"] = candidate

    # 出发日期/时间
    for pat in [
        r'(\d{4})年(\d{2})月(\d{2})日\s*(\d{2}:\d{2})',
        r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})',
    ]:
        m = re.search(pat, text)
        if m:
            if len(m.groups()) == 4:
                result["departure_date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                result["departure_time"] = m.group(4)
            else:
                result["departure_date"] = m.group(1)
                result["departure_time"] = m.group(2)
            break

    # 出发站/到达站（各种格式）
    for pat in [
        r'(\S+站)\s*[→\-—]\s*(\S+站)',
        r'(\S+)\s*[→\-—]\s*(\S+站)',
        r'(\S+站)\s*[→\-—]\s*(\S+)',
    ]:
        m = re.search(pat, text)
        if m:
            result["departure_station"] = m.group(1).strip()
            result["arrival_station"] = m.group(2).strip()
            break

    # 如果没有站到站格式，找"站"字符附近的模式
    if not result["departure_station"]:
        stations = re.findall(r'(\S+站)', text)
        if len(stations) >= 2:
            result["departure_station"] = stations[0]
            result["arrival_station"] = stations[1]

    # 座位
    for pat in [r'([一二三]等座)', r'(硬[座卧]|软[座卧]|无座)', r'(商务座|特等座)']:
        m = re.search(pat, text)
        if m:
            result["seat_type"] = m.group(1)
            break

    # 金额
    m = re.search(r'票价[：:]*\s*[¥￥]\s*([\d,.]+)', text)
    if m:
        result["amount"] = clean_amount(m.group(1))
    else:
        m = re.search(r'[¥￥]\s*([\d,.]+)', text)
        if m:
            result["amount"] = clean_amount(m.group(1))

    # 质量检查
    if not result["train_number"]:
        warnings.append("未提取到车次号")
    if not result["departure_station"]:
        warnings.append("未提取到出发/到达站")

    if warnings:
        result["warnings"] = warnings

    return result


# ── 文档类型检测（v2 修复 T2 航站楼误判）────────────────────────────────────

def detect_type(text: str) -> str:
    """
    检测文档类型。v2 改进：火车票需同时满足车次号上下文中不含"航站楼"。
    """
    # 火车票检测：要有车次 + 铁路相关上下文
    has_train_number = bool(re.search(r'[GDCKZ]\d{1,5}', text))
    has_rail_context = any(k in text for k in ["车票", "铁路", "客票", "票价", "车次"])
    has_rail_station = len(re.findall(r'\S+站', text)) >= 2

    if has_train_number and (has_rail_context or has_rail_station):
        # 额外检查：排除 T2 航站楼
        t2_ctx = re.search(r'(T\d)\s*(航站楼|航站|Terminal|号门|门外|侧)', text)
        if not t2_ctx or has_rail_context:
            return "train"

    # 行程单检测
    if any(k in text for k in ["行程单", "行程报销单", "AMAP ITINERARY", "高德地图—打车"]):
        return "itinerary"

    # 发票检测
    if any(k in text for k in ["发票", "价税合计", "发票号码"]):
        return "invoice"

    return "invoice"


# ── 主逻辑 ───────────────────────────────────────────────────────────────────

def parse_file(md_path: str) -> dict:
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    filename = ""
    m = re.match(r'^# (.+)$', text, re.MULTILINE)
    if m:
        filename = m.group(1).strip()

    original, merged = flatten_text(text)
    doc_type = detect_type(text)

    if doc_type == "invoice":
        result = parse_invoice(text, filename, merged)
    elif doc_type == "itinerary":
        result = parse_itinerary(text, filename, merged)
    elif doc_type == "train":
        result = parse_train_ticket(text, filename, merged)
    else:
        result = {"type": "unknown", "file": filename}

    result["source_file"] = os.path.basename(md_path)
    return result


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    md_path = sys.argv[1]
    output_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "-o" and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
            break

    if not os.path.exists(md_path):
        print(f"❌ 文件不存在: {md_path}")
        sys.exit(1)

    result = parse_file(md_path)
    json_str = json.dumps(result, ensure_ascii=False, indent=2)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        w = result.get("warnings", [])
        warn_str = f" (⚠️ {len(w)} warnings)" if w else ""
        print(f"✅ {result['type']}: {result.get('file', '?')} → {output_path}{warn_str}")
    else:
        print(json_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
