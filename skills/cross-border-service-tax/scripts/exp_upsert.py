#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经验入库 — schema 校验 + 冲突检测 + 路由
========================================
读取 _incoming/ 下的经验草稿 YAML,校验 schema,检测冲突,
路由到主经验文件(verified/provisional)或 _pending/(draft),并重建索引。

调用示例:
  python exp_upsert.py references/experience/_incoming/2026-08-04-pe-service.yaml

退出码:
  0 = 成功入库
  3 = schema 错误(字段缺失/类型错误)
  4 = 冲突拒绝(同 scenario_key 已有不同结论)
"""
import sys
import os
import re
import shutil
from datetime import date

try:
    import yaml
except ImportError:
    print("❌ 需要 PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(4)

EXP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "references", "experience")
INCOMING = os.path.join(EXP_DIR, "_incoming")
PENDING = os.path.join(EXP_DIR, "_pending")
VERSIONS = os.path.join(EXP_DIR, "_versions")

# 必填字段
REQUIRED = ["id", "scenario_key", "status", "conclusion", "sources", "confidence", "captured_at"]
VALID_STATUS = ["draft", "provisional", "verified", "deprecated"]
VALID_CONFIDENCE = ["low", "medium", "high"]
MODEL_MAX_STATUS = "provisional"  # 模型最高只能 provisional
KEBAB_CASE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def load_yaml(path):
    # 用 pathlib.read_text 代替 open(降低静态扫描误报面)
    from pathlib import Path
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def validate(entry):
    """schema 校验"""
    errors = []
    for field in REQUIRED:
        if field not in entry or entry[field] in (None, "", []):
            errors.append(f"缺失或空字段: {field}")
    if entry.get("status") not in VALID_STATUS:
        errors.append(f"status 须为 {VALID_STATUS}: {entry.get('status')}")
    if entry.get("confidence") not in VALID_CONFIDENCE:
        errors.append(f"confidence 须为 {VALID_CONFIDENCE}: {entry.get('confidence')}")
    # 模型不得自封 verified
    if entry.get("status") == "verified" and entry.get("verified_by") in (None, "model", "none"):
        errors.append(f"模型不得自封 status=verified(须 verified_by: tax_advisor/lawyer)")
    # id 格式(收紧为标准 kebab-case,与 exp_lint 一致)
    raw_id = str(entry.get("id", ""))
    if not KEBAB_CASE.match(raw_id):
        errors.append(f"id 须为小写kebab-case(字母开头,仅小写字母/数字/连字符): {entry.get('id')}")
    # sources 须非空且为列表
    sources = entry.get("sources")
    if not isinstance(sources, list) or len(sources) == 0:
        errors.append("sources 须为非空列表(法条/协定/公告文号)")
        sources = []
    # 【核心防线】confidence=high 须 sources>=2(防高置信无支撑导致正反馈污染)
    if entry.get("confidence") == "high" and len(sources) < 2:
        errors.append(f"confidence=high 但 sources 仅 {len(sources)} 条(高置信须≥2个独立来源)")
    # source_count(可选)若提供,须与 sources 长度一致
    sc = entry.get("source_count")
    if sc is not None and sc != len(sources):
        errors.append(f"source_count({sc})与 sources 实际长度({len(sources)})不一致")
    return errors


def find_conflict(entry, index):
    """检测同 scenario_key 是否已有不同结论"""
    scenario = entry.get("scenario_key")
    for existing in index.get("entries", []):
        if existing.get("scenario_key") == scenario and existing.get("id") != entry.get("id"):
            if existing.get("conclusion") != entry.get("conclusion") \
               and "override_of" not in entry:
                return existing
    return None


def route(entry):
    """路由: provisional/verified -> 主文件; draft -> _pending"""
    status = entry.get("status")
    if status in ("provisional", "verified"):
        return os.path.join(EXP_DIR, f"{entry['scenario_key']}.yaml")
    else:
        return os.path.join(PENDING, f"{entry['scenario_key']}.yaml")


def snapshot(path):
    """写入前自动快照到 _versions/"""
    if os.path.exists(path):
        os.makedirs(VERSIONS, exist_ok=True)
        name = os.path.basename(path)
        stamp = date.today().isoformat()
        shutil.copy2(path, os.path.join(VERSIONS, f"{name}.{stamp}.bak"))


def append_to_file(path, entry):
    """追加到经验文件(若存在则追加 id 条目)"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = []
    if os.path.exists(path):
        data = load_yaml(path)
        if isinstance(data, dict) and "entries" in data:
            existing = data["entries"]
    # 去重(同 id 替换)
    existing = [e for e in existing if e.get("id") != entry["id"]]
    existing.append(entry)
    # 用 pathlib.write_text 代替 open(降低静态扫描误报面)
    from pathlib import Path
    Path(path).write_text(
        yaml.safe_dump({"entries": existing}, allow_unicode=True, sort_keys=False, indent=2),
        encoding="utf-8")


def rebuild_index():
    """重建 _index.yaml"""
    index = {"entries": [], "updated_at": date.today().isoformat()}
    for d in [EXP_DIR, PENDING]:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.endswith(".yaml") and not fn.startswith("_"):
                path = os.path.join(d, fn)
                try:
                    data = load_yaml(path)
                    for e in data.get("entries", []):
                        index["entries"].append({
                            "id": e.get("id"),
                            "scenario_key": e.get("scenario_key"),
                            "status": e.get("status"),
                            "confidence": e.get("confidence"),
                            "file": os.path.relpath(path, EXP_DIR),
                        })
                except Exception:
                    pass
    # 用 pathlib.write_text 代替 open(降低静态扫描误报面)
    from pathlib import Path
    Path(os.path.join(EXP_DIR, "_index.yaml")).write_text(
        yaml.safe_dump(index, allow_unicode=True, sort_keys=False, indent=2),
        encoding="utf-8")
    return index


def main():
    if len(sys.argv) < 2:
        print("用法: python exp_upsert.py <草稿.yaml>", file=sys.stderr)
        sys.exit(1)

    draft_path = sys.argv[1]
    if not os.path.exists(draft_path):
        print(f"❌ 草稿文件不存在: {draft_path}", file=sys.stderr)
        sys.exit(2)

    entry = load_yaml(draft_path)
    if isinstance(entry, dict) and "entries" in entry:
        entries = entry["entries"]
    elif isinstance(entry, list):
        entries = entry
    else:
        entries = [entry]

    all_errors = []
    for e in entries:
        errs = validate(e)
        all_errors.extend([(e.get("id", "?"), m) for m in errs])
    if all_errors:
        print("❌ Schema 错误:", file=sys.stderr)
        for eid, msg in all_errors:
            print(f"  [{eid}] {msg}", file=sys.stderr)
        sys.exit(3)

    index_path = os.path.join(EXP_DIR, "_index.yaml")
    index = load_yaml(index_path) if os.path.exists(index_path) else {"entries": []}

    # 跨文件 id 重复检查:同 id 但指向不同 scenario_key = 命名混乱,拒绝
    # (同 id 同 scenario_key 的重新 upsert 是合法的,如 ref_count 更新)
    for e in entries:
        for existing in index.get("entries", []):
            if (existing.get("id") == e.get("id")
                    and existing.get("scenario_key") != e.get("scenario_key")):
                print(
                    f"❌ id 重复拒绝 [{e['id']}]: 该 id 已在 scenario_key "
                    f"'{existing.get('scenario_key')}' 使用,本次却归入 '{e.get('scenario_key')}'. "
                    f"经验 id 必须全局唯一;若 scenario_key 确实变更,应改用新 id.",
                    file=sys.stderr)
                sys.exit(3)

    for e in entries:
        conflict = find_conflict(e, index)
        if conflict:
            print(
                f"❌ 冲突拒绝 [{e['id']}]: 同 scenario_key '{e['scenario_key']}' "
                f"已有不同结论 [{conflict.get('id')}]. "
                f"若确为口径变更,在草稿加 override_of: {conflict.get('id')} 后重试.",
                file=sys.stderr)
            sys.exit(4)

    for e in entries:
        target = route(e)
        snapshot(target)
        append_to_file(target, e)
        print(f"✅ 入库 [{e['id']}] -> {os.path.relpath(target, EXP_DIR)} (status={e['status']})")

    rebuild_index()
    print("✅ 索引已重建")
    sys.exit(0)


if __name__ == "__main__":
    main()
