#!/usr/bin/env python3
"""复算 LaborPilot 公开知识载荷与构建统计清单。

默认只检查公开包中的编译载荷和哈希清单，不输出知识卡正文。开发者可额外
提供私有法规拆分目录，复算 149 份来源文件的编号、范围与 SHA-256。
"""

from __future__ import annotations

import argparse
import ast
import base64
import binascii
import hashlib
import json
import marshal
from pathlib import Path
import re
from typing import Any
import zlib


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROUTER = ROOT / "scripts" / "issue_router.py"
DEFAULT_MANIFEST = ROOT / "data" / "knowledge-build-stats.json"
PACKAGE_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
SOURCE_FILE_PATTERN = re.compile(r"^(\d{3})-(.+)\.md$")


def canonical_digest(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compiled_knowledge_literal(router_path: Path) -> str:
    tree = ast.parse(router_path.read_text(encoding="utf-8"), filename=str(router_path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_COMPILED_KNOWLEDGE"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, str) and value:
                return value
    raise ValueError("公开争点路由脚本缺少 _COMPILED_KNOWLEDGE。")


def operational_fallback_route_count(cards: list[dict[str, Any]]) -> int:
    """从编译载荷识别劳动合同纠纷兜底运行路由。"""
    return sum(
        not str(card.get("g", "")).strip()
        and str(card.get("id", "")).strip() == "GATE-205"
        and "劳动合同纠纷" in f"{card.get('t', '')}\n{card.get('bd', '')}"
        and "兜底" in f"{card.get('t', '')}\n{card.get('bd', '')}"
        for card in cards
    )


def payload_stats(router_path: Path) -> dict[str, Any]:
    encoded = compiled_knowledge_literal(router_path)
    compressed = base64.b64decode(encoded, validate=True)
    marshalled = zlib.decompress(compressed)
    cards = marshal.loads(marshalled)
    if not isinstance(cards, list) or not all(isinstance(card, dict) for card in cards):
        raise ValueError("编译知识载荷不是知识卡 object 数组。")
    card_ids = [str(card.get("id", "")).strip() for card in cards]
    if not all(card_ids) or len(card_ids) != len(set(card_ids)):
        raise ValueError("编译知识载荷存在空卡号或重复卡号。")
    issue_cards = [card for card in cards if str(card.get("g", "")).strip()]
    gate_cards = [card for card in cards if not str(card.get("g", "")).strip()]
    issue_gate_labels = sorted({str(card["g"]).strip() for card in issue_cards})
    fallback_route_count = operational_fallback_route_count(cards)
    return {
        "total_cards": len(cards),
        "issue_card_count": len(issue_cards),
        "gate_card_count": len(gate_cards),
        "zhejiang_guidance_card_count": sum(bool(str(card.get("zj", "")).strip()) for card in cards),
        "statutory_leaf_route_count": len(issue_gate_labels),
        "operational_fallback_route_count": fallback_route_count,
        "total_route_category_count": len(issue_gate_labels) + fallback_route_count,
        "compiled_blob_sha256": sha256_bytes(compressed),
        "marshalled_payload_sha256": sha256_bytes(marshalled),
        "canonical_cards_sha256": canonical_digest(cards),
        "card_id_set_sha256": sha256_bytes("\n".join(sorted(card_ids)).encode("utf-8")),
        "issue_gate_label_set_sha256": sha256_bytes("\n".join(issue_gate_labels).encode("utf-8")),
    }


def source_entries_from_directory(source_dir: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob("[0-9][0-9][0-9]-*.md")):
        match = SOURCE_FILE_PATTERN.fullmatch(path.name)
        if not match or match.group(1) == "000":
            continue
        sequence = int(match.group(1))
        title = match.group(2)
        entries.append({
            "source_id": f"SRC-{sequence:03d}",
            "scope": "zhejiang" if "浙江" in title else "national_or_other",
            "size_bytes": path.stat().st_size,
            "title_sha256": sha256_bytes(title.encode("utf-8")),
            "content_sha256": sha256_bytes(path.read_bytes()),
        })
    return entries


def compare(expected: Any, actual: Any, field: str, findings: list[str]) -> None:
    if expected != actual:
        findings.append(f"{field} 不一致：清单={expected!r}，当前={actual!r}。")


def validate_manifest(
    manifest: dict[str, Any],
    current_payload: dict[str, Any],
    source_dir: Path | None,
) -> list[str]:
    findings: list[str] = []
    compare("1.0.0", manifest.get("manifest_version"), "manifest_version", findings)
    compare(PACKAGE_VERSION, manifest.get("package_version"), "package_version", findings)

    expected_payload = manifest.get("knowledge_payload")
    if not isinstance(expected_payload, dict):
        findings.append("knowledge_payload 必须是 object。")
    else:
        for field, actual in current_payload.items():
            compare(expected_payload.get(field), actual, f"knowledge_payload.{field}", findings)

    inventory = manifest.get("source_inventory")
    if not isinstance(inventory, dict):
        findings.append("source_inventory 必须是 object。")
        return findings
    entries = inventory.get("entries")
    if not isinstance(entries, list) or not all(isinstance(item, dict) for item in entries):
        findings.append("source_inventory.entries 必须是 object 数组。")
        return findings
    source_ids = [item.get("source_id") for item in entries]
    expected_ids = [f"SRC-{index:03d}" for index in range(1, 150)]
    compare(inventory.get("document_count"), len(entries), "source_inventory.document_count", findings)
    compare(expected_ids, source_ids, "source_inventory.source_id 序列", findings)
    compare(inventory.get("entries_sha256"), canonical_digest(entries), "source_inventory.entries_sha256", findings)
    scope_counts = {
        "zhejiang": sum(item.get("scope") == "zhejiang" for item in entries),
        "national_or_other": sum(item.get("scope") == "national_or_other" for item in entries),
    }
    compare(inventory.get("scope_counts"), scope_counts, "source_inventory.scope_counts", findings)
    for index, item in enumerate(entries):
        if set(item) != {"source_id", "scope", "size_bytes", "title_sha256", "content_sha256"}:
            findings.append(f"source_inventory.entries[{index}] 字段集合不符合公开最小清单。")
        for field in ("title_sha256", "content_sha256"):
            if not isinstance(item.get(field), str) or not re.fullmatch(r"[a-f0-9]{64}", item[field]):
                findings.append(f"source_inventory.entries[{index}].{field} 不是合法 SHA-256。")

    if source_dir is not None:
        actual_entries = source_entries_from_directory(source_dir)
        compare(entries, actual_entries, "私有来源目录复算结果", findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="复算 LaborPilot 知识构建统计，不输出完整知识卡")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--router", default=str(DEFAULT_ROUTER))
    parser.add_argument("--source-dir", help="可选：私有法规拆分目录，用于复算 149 份来源哈希")
    args = parser.parse_args()

    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        current_payload = payload_stats(Path(args.router))
        source_dir = Path(args.source_dir).expanduser().resolve() if args.source_dir else None
        findings = validate_manifest(manifest, current_payload, source_dir)
    except (OSError, ValueError, SyntaxError, json.JSONDecodeError, binascii.Error, zlib.error) as exc:
        findings = [str(exc)]
        current_payload = {}

    result = {
        "status": "pass" if not findings else "blocked",
        "package_version": PACKAGE_VERSION,
        "statistics": {
            key: current_payload.get(key)
            for key in (
                "total_cards", "issue_card_count", "gate_card_count",
                "zhejiang_guidance_card_count", "statutory_leaf_route_count",
                "operational_fallback_route_count", "total_route_category_count",
            )
        },
        "findings": findings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
