#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""案号格式校验脚本（case_number_validator.py）。

功能：校验案号格式。数据源：assets/data/case_number_format.json。

调用方式：
  python scripts/case_number_validator.py --number "（2026）浙0203刑初123号"

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}，data含格式校验结果、
    符合的格式类型；
  - 退出码：0成功 / 1参数错误 / 2数据文件缺失或损坏 / 3计算或校验失败。
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

SCRIPT_NAME = "case_number_validator"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "data")


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def load_formats():
    path = os.path.join(DATA_DIR, "case_number_format.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="案号格式校验：按文书类型正则表达式库校验案号格式。")
    parser.add_argument("--number", required=True, help="待校验案号（如“（2026）浙0203刑初123号”）")
    args = parser.parse_args()
    trace_id = make_trace_id()

    formats = load_formats()
    if formats is None:
        print(json.dumps(envelope("error", "ERR_IO",
                                  "case_number_format.json缺失或损坏", None),
                         ensure_ascii=False, indent=2))
        sys.exit(2)

    number = args.number.strip()
    matched = []
    for ftype, spec in (formats.get("formats") or {}).items():
        pattern = spec.get("pattern", "") if isinstance(spec, dict) else spec
        try:
            import re
            if re.fullmatch(pattern, number) or re.match(pattern + "$", number):
                matched.append({"type": ftype,
                                "pattern": pattern,
                                "example": spec.get("sanitized_example", "") if isinstance(spec, dict) else ""})
        except re.error:
            continue

    # 年代判断：旧式"字第"格式按年份判真伪（2016年1月1日起取消该格式）
    import re
    era_note = None
    old_style = re.match(r"^[（(]((?:19|20)\d{2})[）)].{0,8}刑[初终再]字第\d+号$", number)
    if old_style:
        year = int(old_style.group(1))
        if year <= 2015:
            era_note = "旧式案号格式（%d年，2016年1月1日《人民法院案件编号规则》施行前），年代与格式相符，属历史案号；引用前仍须检索核实案号真实性" % year
        else:
            era_note = "虚构案号特征：%d年及以后的案号已取消\"字第\"格式（2016年1月1日起施行新编号规则），该案号格式与年代矛盾" % year
            matched = []

    data = {"trace_id": trace_id, "number": number,
            "valid": bool(matched),
            "matched_types": matched,
            "era_note": era_note,
            "verdict": ("格式合法：符合%s" % "、".join(m["type"] for m in matched)) if matched
            else ("格式不合法：%s（虚构检查断言触发）" % era_note if era_note
                  else "格式不合法：不符合任何已知案号格式（可能为虚构案号——虚构检查断言触发）")}
    print(json.dumps(envelope("ok" if matched else "error",
                              None if matched else "ERR_TYPE_INVALID",
                              "校验完成", data), ensure_ascii=False, indent=2))
    sys.exit(0 if matched else 3)


if __name__ == "__main__":
    main()
