#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经验库质量门 — 过期/低质/一致性校验
==================================
检查经验库,防止低质经验进入主推理(正反馈污染防护):
  - sources 为空 -> error
  - status/confidence 非法 -> error
  - id 重复(跨文件) -> error
  - confidence=high 但 sources<2 -> error(高置信须≥2个独立来源,核心防线)
  - source_count(若提供)与 sources 长度不一致 -> error
  - status=verified 但 verified_by=none -> warning
  - provisional 经验被引用≥provisional_review_threshold 且未复核 -> warning
  - verified 经验 last_verified 超 stale_warning_months -> warning(法条/口径会变)
  - _pending/ 文件超 pending_retention_days 未复核 -> warning

调用示例:
  python exp_lint.py                      # 全库扫描
  python exp_lint.py --file xxx.yaml      # 单文件检查
  python exp_lint.py --strict             # 严格模式(warning也算失败,用于CI门禁)
  python exp_lint.py --json               # JSON输出(机器可读,便于集成)

退出码: 0=通过(可能有warning) 1=有error 2=文件不存在
"""
import sys
import os
import re
import json
import argparse
from datetime import date, datetime

try:
    import yaml
except ImportError:
    print("❌ 需要 PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

EXP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "references", "experience")
PENDING = os.path.join(EXP_DIR, "_pending")

VALID_STATUS = ("draft", "provisional", "verified", "deprecated")
VALID_CONFIDENCE = ("low", "medium", "high")
KEBAB_CASE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def load_config():
    """从 _config.yaml 加载配置,失败用默认值。配置驱动而非硬编码。"""
    cfg_path = os.path.join(EXP_DIR, "_config.yaml")
    defaults = {
        "stale_warning_months": 12,
        "pending_retention_days": 90,
        "provisional_review_threshold": 3,
    }
    if not os.path.exists(cfg_path):
        return defaults
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return {k: data.get(k, v) for k, v in defaults.items()}
    except Exception:
        return defaults


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def months_since(d_str):
    try:
        d = datetime.strptime(str(d_str)[:10], "%Y-%m-%d").date()
        return (date.today() - d).days / 30.0
    except Exception:
        return None


def check_entry(e, cfg, all_ids):
    """检查单条经验,返回 (errors, warns, infos)"""
    errors, warns, infos = [], [], []
    eid = e.get("id", "<无id>")

    # 1. sources 校验(必填非空列表)
    sources = e.get("sources")
    if not isinstance(sources, list) or len(sources) == 0:
        errors.append(f"[{eid}] sources 须为非空列表(法条/协定/公告文号)")
        sources = []  # 后续检查避免再次报错

    # 2. 枚举字段校验
    if e.get("status") not in VALID_STATUS:
        errors.append(f"[{eid}] status 非法: {e.get('status')}(应为 {VALID_STATUS})")
    if e.get("confidence") not in VALID_CONFIDENCE:
        errors.append(f"[{eid}] confidence 非法: {e.get('confidence')}(应为 {VALID_CONFIDENCE})")

    # 3. id 格式 + 跨文件唯一性
    raw_id = e.get("id")
    if not isinstance(raw_id, str) or not KEBAB_CASE.match(str(raw_id)):
        errors.append(f"[{eid}] id 须为小写kebab-case: {raw_id}")
    elif raw_id in all_ids:
        errors.append(f"[{raw_id}] id 重复(跨文件已出现,经验id必须全局唯一)")
    else:
        all_ids.add(raw_id)

    # 4. 【核心防线】confidence=high 但 sources<2 -> error(防高置信无支撑)
    #    这是防正反馈污染的关键:模型自封 high confidence 却只有1个来源,容易错误归纳
    conf = e.get("confidence")
    if conf == "high" and len(sources) < 2:
        errors.append(f"[{eid}] confidence=high 但 sources 仅 {len(sources)} 条(高置信须≥2个独立来源)")

    # 5. source_count(可选字段)若提供,须与 len(sources) 一致
    sc = e.get("source_count")
    if sc is not None and sc != len(sources):
        errors.append(f"[{eid}] source_count({sc})与 sources 实际长度({len(sources)})不一致")

    # 6. status=verified 但 verified_by 为空/none/model -> warning
    status = e.get("status")
    verified_by = e.get("verified_by")
    if status == "verified" and (not verified_by or verified_by in ("none", "model")):
        warns.append(f"[{eid}] status=verified 但 verified_by={verified_by}(须 tax_advisor/lawyer 确认)")

    # 7. provisional 引用计数达门槛且未复核 -> warning(升级门触发)
    refs = e.get("ref_count", 0)
    if status == "provisional" and refs >= cfg["provisional_review_threshold"] and not e.get("last_verified"):
        warns.append(f"[{eid}] provisional 经验被引用 {refs} 次(≥{cfg['provisional_review_threshold']}),未复核——建议强制复核后再升级;可用 assets/经典案例库/ 覆盖相同 scenario_key 的案例交叉验证")

    # 8. verified 经验过期 -> warning(法条/口径会变)
    last_verified = e.get("last_verified") or e.get("captured_at")
    if status == "verified" and last_verified:
        m = months_since(last_verified)
        if m and m > cfg["stale_warning_months"]:
            warns.append(f"[{eid}] verified 经验 {m:.0f} 个月未复核(>{cfg['stale_warning_months']}),法条/口径可能过期")

    return errors, warns, infos


def main():
    parser = argparse.ArgumentParser(description="经验库质量门")
    parser.add_argument("--file", default=None, help="只检查单个 YAML 文件")
    parser.add_argument("--strict", action="store_true", help="严格模式(warning也算失败,用于CI门禁)")
    parser.add_argument("--json", action="store_true", help="JSON 输出(机器可读)")
    args = parser.parse_args()

    cfg = load_config()
    all_errors, all_warns, all_infos = [], [], []
    checked = 0
    all_ids = set()

    # 收集要检查的文件
    if args.file:
        if not os.path.exists(args.file):
            msg = f"文件不存在: {args.file}"
            if args.json:
                print(json.dumps({"status": "error", "error": msg}, ensure_ascii=False), file=sys.stderr)
            else:
                print(f"❌ {msg}", file=sys.stderr)
            sys.exit(2)
        files = [args.file]
        dirs = []
    else:
        files = []
        dirs = [EXP_DIR, PENDING]

    for d in dirs:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".yaml") and not fn.startswith("_"):
                files.append(os.path.join(d, fn))

    for path in files:
        rel = os.path.relpath(path, EXP_DIR) if EXP_DIR in path else path
        try:
            data = load_yaml(path)
        except yaml.YAMLError as ex:
            all_errors.append(f"{rel}: YAML 解析失败 - {ex}")
            continue
        except Exception as ex:
            all_errors.append(f"{rel}: 读取失败 - {ex}")
            continue

        entries = data.get("entries", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for e in entries:
            if not isinstance(e, dict):
                all_errors.append(f"{rel}: 经验条目应为字典")
                continue
            checked += 1
            errs, warns, infos = check_entry(e, cfg, all_ids)
            all_errors.extend(errs)
            all_warns.extend(warns)
            all_infos.extend(infos)

        # _pending 文件过期(仅全库模式)
        if not args.file and PENDING in path:
            mtime = date.fromtimestamp(os.path.getmtime(path))
            age = (date.today() - mtime).days
            if age > cfg["pending_retention_days"]:
                all_warns.append(f"{rel} 在 _pending 超 {cfg['pending_retention_days']} 天未复核")

    # 结果判定
    has_error = len(all_errors) > 0
    strict_fail = args.strict and len(all_warns) > 0
    passed = not has_error and not strict_fail

    # 输出
    if args.json:
        result = {
            "status": "success" if passed else "error",
            "checked": checked,
            "errors": all_errors,
            "warnings": all_warns,
            "infos": all_infos,
            "summary": {
                "errors": len(all_errors),
                "warnings": len(all_warns),
                "strict_mode": args.strict,
                "passed": passed,
            },
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if passed else 1)

    # 人类可读输出
    print(f"检查 {checked} 条经验")
    for i in all_infos:
        print(f"ℹ️  {i}")
    for w in all_warns:
        print(f"⚠️  {w}")
    for e in all_errors:
        print(f"❌ {e}")
    print("-" * 40)

    if has_error:
        print(f"结果: ❌ {len(all_errors)} 个 error")
    elif strict_fail:
        print(f"结果: ❌ {len(all_warns)} 个 warning(--strict 模式视为失败)")
    elif all_warns:
        print(f"结果: ⚠️ {len(all_warns)} 个 warning(非阻断)")
    else:
        print("结果: ✅ 经验库健康")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
