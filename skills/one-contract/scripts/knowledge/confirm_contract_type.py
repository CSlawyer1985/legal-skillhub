#!/usr/bin/env python3
"""交叉检验 AI 的合同归类，并产出可留痕的溯源记录。

设计前提（产品负责人 2026-09-17 定）：
- **路由器只做初判与交叉校验，不作为唯一入口**；
- 路由器能直接命中最好；不能命中时，由 AI 对整份合同作语义归类；
- AI 的归类必须落在**目录中真实存在**的类型上——本工具负责这一道校验，
  并记录 AI 归类与路由器初判之间的分歧。

本工具**不改变分类结论**，只做三件事：校验、比对、留痕。

分类的三条合法出路：
1. `routable_types` 中的具体类型（且已 active）—— 最优；
2. `domain_fallbacks` 中的「待细分」类型 —— 诚实承认尚无成熟专项类型；
3. **都不在** —— 拒绝。AI 不得凭空造类型或指向未启用资产。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = SKILL_ROOT / "assets" / "knowledge_v2"
ROUTER = SKILL_ROOT / "scripts" / "knowledge" / "route_enterprise_contract.py"


def _load(name: str) -> dict[str, Any]:
    return json.loads((ASSET_ROOT / name).read_text(encoding="utf-8"))


def _router_first_pass(title: str, our_role: str) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(ROUTER), "--title", title, "--our-role", our_role or "unknown"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()[:400]}
    return json.loads(proc.stdout)


def confirm(*, title: str, proposed: str, basis: str, our_role: str,
            router_initial: dict[str, Any] | None = None,
            human_confirmed: bool = False) -> dict[str, Any]:
    taxonomy = _load("taxonomy_v2.json")
    manifest = _load("asset_manifest.json")

    routable = {x["type_id"]: x for x in taxonomy.get("routable_types", [])}
    fallbacks = {x["type_id"]: x for x in taxonomy.get("domain_fallbacks", [])}
    catalog = {x["type_id"]: x for x in taxonomy.get("catalog_types", [])}
    active_types = set(manifest.get("active_type_ids", []))
    active_modules = set(manifest.get("active_module_ids", []))

    initial = router_initial if router_initial is not None else _router_first_pass(title, our_role)
    notes: list[str] = []

    if proposed in routable:
        entry = routable[proposed]
        missing = sorted(set(entry.get("required_modules") or []) - active_modules)
        verdict = "accepted" if not missing else "rejected"
        check = {
            "kind": "routable_specific_type",
            "in_routable_types": True,
            "is_domain_fallback": False,
            "catalog_status": catalog.get(proposed, {}).get("approval_status"),
            "is_active": proposed in active_types,
            "required_modules_resolvable": not missing,
            "missing_modules": missing,
            "domain_code": entry.get("domain_code"),
            "name": entry.get("name"),
        }
        if missing:
            notes.append(f"该类型声明的模块中有 {len(missing)} 个未启用：{missing}")
        if proposed not in active_types:
            verdict = "rejected"
            notes.append("该类型未启用（不在 manifest.active_type_ids）")
    elif proposed in fallbacks:
        check = {
            "kind": "domain_fallback",
            "in_routable_types": False,
            "is_domain_fallback": True,
            "catalog_status": None,
            "is_active": None,
            "required_modules_resolvable": None,
            "missing_modules": [],
            "domain_code": fallbacks[proposed].get("domain_code"),
            "name": fallbacks[proposed].get("name"),
        }
        verdict = "accepted_with_fallback"
        notes.append(
            "目录中尚无覆盖该交易实质的成熟专项类型；本结论为诚实承认"
            "「待细分」，不是归类失败。若反复出现，应作为新增类型的候选依据。"
        )
    else:
        check = {"kind": "unknown", "in_routable_types": False, "is_domain_fallback": False}
        verdict = "rejected"
        notes.append(
            "该 type_id 既不在 routable_types 也不在 domain_fallbacks —— "
            "AI 不得凭空构造类型或指向未启用资产。请改为目录中真实存在的类型，"
            "或退到本域的「待细分」类型。"
        )

    router_type = initial.get("primary_type_id")
    router_status = initial.get("classification_status")
    check["router_initial_type_id"] = router_type
    check["router_initial_status"] = router_status
    check["router_agrees"] = router_type == proposed
    check["human_confirmed"] = bool(human_confirmed)
    if check["router_agrees"]:
        check["divergence"] = None
    elif router_status == "low":
        check["divergence"] = (
            "路由器未命中标题（low，落域兜底）；AI 依交易实质归类。"
            "这正是「初判 + 交叉校验」分工的正常场景。"
        )
    else:
        check["divergence"] = (
            f"路由器命中为 {router_type}（{router_status}），AI 归类为 {proposed}。"
            "**分歧需人工复核**：多数情况是路由配置缺该类型的关键词，"
            "也可能是 AI 判断有误。应记录并在后续复盘。"
        )

    # 路由器已形成 medium/high 的具体判断时，AI 改判不得仅靠“目标类型存在”
    # 就自动放行。否则调用方只看 exit code / verdict，会在无人确认的情况下
    # 加载另一套专项规则。人工确认后可显式放行，并把确认事实写入溯源记录。
    material_divergence = (
        verdict != "rejected"
        and not check["router_agrees"]
        and router_status in ("high", "medium")
    )
    if material_divergence and not human_confirmed:
        verdict = "needs_human_review"
        notes.append("路由器已有中高置信结论且与 AI 归类不一致；人工确认前不得加载专项规则。")
    elif material_divergence and human_confirmed:
        notes.append("分歧已由人工显式确认；保留路由器原判断与确认记录供后续复盘。")
    check["requires_human_review"] = verdict == "needs_human_review"

    return {
        "schema_version": "1.0",
        "title": title,
        "our_role": our_role,
        "proposed_by": "ai_semantic_classification",
        "human_confirmation": {
            "confirmed": bool(human_confirmed),
            "required_by_divergence": material_divergence,
        },
        "proposed_type_id": proposed,
        "basis": basis,
        "router_initial": {
            "primary_type_id": router_type,
            "primary_domain_code": initial.get("primary_domain_code"),
            "classification_status": router_status,
            "evidence": initial.get("evidence"),
        },
        "cross_check": check,
        "verdict": verdict,
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="交叉检验 AI 的合同归类并产出溯源记录（不改变结论，只校验、比对、留痕）"
    )
    parser.add_argument("--title", required=True, help="合同标题")
    parser.add_argument("--proposed", required=True, help="AI 归类到的 type_id")
    parser.add_argument("--basis", required=True, help="AI 归类的依据（读到了哪些交易事实）")
    parser.add_argument("--our-role", default="unknown")
    parser.add_argument(
        "--human-confirmed",
        action="store_true",
        help="人工已复核并确认 AI 归类；仅用于处理中高置信路由分歧",
    )
    parser.add_argument("--router-json", default="",
                        help="路由器初判的 JSON 文件；不传则本工具自行调用路由器")
    parser.add_argument("--out", default="", help="把溯源记录写入指定文件")
    args = parser.parse_args()

    initial = None
    if args.router_json:
        initial = json.loads(Path(args.router_json).read_text(encoding="utf-8"))

    record = confirm(
        title=args.title, proposed=args.proposed, basis=args.basis,
        our_role=args.our_role, router_initial=initial,
        human_confirmed=args.human_confirmed,
    )
    text = json.dumps(record, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    if record["verdict"] == "rejected":
        return 1
    if record["verdict"] == "needs_human_review":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
