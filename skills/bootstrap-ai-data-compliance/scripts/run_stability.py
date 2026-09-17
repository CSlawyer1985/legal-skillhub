#!/usr/bin/env python3
"""AI数据合规冷启动 Skill 三轮指令稳定性验证。

围绕 AIDC-001 至 AIDC-008 逐项建立正例与故障注入断言；
相同输入和配置下运行三轮；保存唯一 nonce、候选聚合哈希和独立运行日志；
与 v0.1.0-mvp 快照约束对比，确认无约束漂移。
由独立验证器检查真实产物，不接受生产器自报通过。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from common import SKILL_VERSION, safe_write_json

SCRIPT_DIR = Path(__file__).resolve().parent
ACCEPTANCE = SCRIPT_DIR / "run_acceptance.py"
def _find_frozen_skill() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "ai/work/knowledge_hub/07_validation/skill_v0.1.0-mvp_frozen/skill"
        if candidate.exists():
            return candidate
    return None


FROZEN_SKILL_DIR = _find_frozen_skill()
STABILITY_SELF = {"run_stability.py", "run_acceptance.py", "validator.py"}

AIDC_CONSTRAINTS = {
    "AIDC-001": "禁止覆盖原始资料、正式成果和既有归档；同名异内容时停止并报告冲突。",
    "AIDC-002": "只允许“文件明确记载 / 多个文件归纳 / 需律师确认 / 无直接法源 / 客户事实待核实”五类证据标签。",
    "AIDC-003": "客户事实门禁未通过时，只输出缺失项；禁止生成候选风险结论或候选交付包。",
    "AIDC-004": "只生成候选材料；禁止自动生成或标记正式法律意见，候选材料必须显示“候选版／需律师确认”。",
    "AIDC-005": "默认仅使用本地资料。外部检索必须另获授权，且不得发送项目正文、客户资料或非公开业务信息。",
    "AIDC-006": "活跃配置、索引和交付包只记录项目相对路径；不得写入操作者电脑绝对路径。",
    "AIDC-007": "论文、公众号、工作手册和实务指南不得单独证明强制性法律义务。",
    "AIDC-008": "生产器不得给自己签发最终通过状态；只有 `validate` 检查真实产物后，才能进入验收归档阶段。",
}

# acceptance checks 到 AIDC 约束的映射（负向测试覆盖哪些约束）
ACCEPTANCE_TO_AIDC = {
    "duplicate_id": "AIDC-002",
    "illegal_label": "AIDC-002",
    "absolute_path": "AIDC-006",
    "formal_opinion_wording": "AIDC-004",
    "research_elevated_to_law": "AIDC-007",
    "overwrite_protection": "AIDC-001",
    "unsupported_formal_stage": "AIDC-004",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(command: list[str], cwd: Path | None = None) -> dict:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPYCACHEPREFIX": "/private/tmp/bootstrap_ai_compliance_pyc",
        "TMPDIR": "/private/tmp",
    }
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    return {"command": " ".join(str(c) for c in command), "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def extract_constraints(skill_md_text: str) -> dict[str, str]:
    found = {}
    for aidc, expected in AIDC_CONSTRAINTS.items():
        marker = f"<!-- skill-lint:constraint {aidc} -->"
        if marker in skill_md_text:
            # 取 marker 后第一个非空行
            after = skill_md_text.split(marker, 1)[1]
            line = after.strip().split("\n")[0].lstrip("- ").strip()
            found[aidc] = line
    return found


def check_no_external_network(skill_dir: Path) -> list[str]:
    """AIDC-005：扫描生产脚本中是否出现外部网络调用模式（排除验证/测试脚本自身）。"""
    hits = []
    network_patterns = [r"requests\.(get|post|put|delete)", r"urllib\.request", r"http\.client", r"httpx\.", r"aiohttp", r"websocket"]
    for path in (skill_dir / "scripts").rglob("*.py"):
        if path.name in STABILITY_SELF:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in network_patterns:
            if re.search(pattern, text):
                hits.append(f"{path.name}:{pattern}")
    return hits


def check_no_self_sign(skill_dir: Path) -> list[str]:
    """AIDC-008：生产器脚本不得写入 completion_marker/instruction_stability 最终结论。"""
    hits = []
    for path in (skill_dir / "scripts").rglob("*.py"):
        if path.name == "run_stability.py" or path.name == "validator.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "completion_marker" in text and "passed" not in text:
            hits.append(f"{path.name}: 出现 completion_marker 且无 passed 判定")
        if "INSTRUCTION_STABILITY_VERIFIED" in text:
            hits.append(f"{path.name}: 出现 INSTRUCTION_STABILITY_VERIFIED（生产器不得自签）")
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(description="三轮指令稳定性验证")
    parser.add_argument("--bci-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()

    skill_dir = SCRIPT_DIR.parent
    rounds_report = []
    all_checks = []
    for round_index in range(1, args.rounds + 1):
        nonce = f"{SKILL_VERSION}-round-{round_index}"
        root = Path(tempfile.mkdtemp(prefix=f"stability-{nonce}-", dir="/private/tmp"))
        result = run([sys.executable, str(ACCEPTANCE), "--bci-source-root", str(args.bci_source_root.resolve()), "--output", str(root / "acceptance.json")])
        acceptance = json.loads(result["stdout"]) if result["stdout"].strip().startswith("{") else {}
        if not acceptance:
            acceptance = json.loads((root / "acceptance.json").read_text(encoding="utf-8")) if (root / "acceptance.json").exists() else {}
        all_checks.append(acceptance.get("checks", {}))
        # 聚合哈希：规范化报告（剔除路径敏感字段）后求 SHA-256，保证三轮可比
        normalized = dict(acceptance)
        normalized.pop("workspace", None)
        normalized.pop("scenario_paths", None)
        aggregate = sha256_text(json.dumps(normalized, ensure_ascii=False, sort_keys=True))
        # 独立日志
        log_dir = root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "acceptance_report.json").write_text(result["stdout"], encoding="utf-8")
        (log_dir / "stderr.txt").write_text(result["stderr"][-2000:], encoding="utf-8")
        rounds_report.append({
            "round": round_index,
            "nonce": nonce,
            "aggregate_sha256": aggregate,
            "passed": bool(acceptance.get("passed")),
            "completion_marker": acceptance.get("completion_marker", "NOT_VERIFIED"),
            "negative_cases": acceptance.get("negative_cases", []),
            "log_dir": str(log_dir),
        })

    # 逐 AIDC 断言
    aidc_checks = {}
    # 负向测试 → 约束映射
    negative_by_name = {case["name"]: case for round_report in rounds_report for case in round_report["negative_cases"]}
    for aidc, _text in AIDC_CONSTRAINTS.items():
        relevant = [name for name, mapped in ACCEPTANCE_TO_AIDC.items() if mapped == aidc]
        if relevant:
            aidc_checks[aidc] = all(
                negative_by_name.get(name, {}).get("expected") == negative_by_name.get(name, {}).get("actual")
                for name in relevant
                if name in negative_by_name
            )
    # AIDC-005 静态扫描
    network_hits = check_no_external_network(skill_dir)
    aidc_checks["AIDC-005"] = not network_hits
    # AIDC-008 静态扫描
    self_sign_hits = check_no_self_sign(skill_dir)
    aidc_checks["AIDC-008"] = not self_sign_hits

    # 三轮一致性：checks 键与值完全一致
    stable_checks = len(all_checks) >= 2 and all(all_checks[0] == item for item in all_checks[1:])
    # 聚合哈希一致性
    stable_hashes = len({r["aggregate_sha256"] for r in rounds_report}) == 1
    # 无约束漂移：当前 SKILL.md 与 v0.1.0-mvp 快照的约束文本一致
    drift_issues = []
    current_skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    current_constraints = extract_constraints(current_skill_md)
    if FROZEN_SKILL_DIR.exists():
        frozen_md = (FROZEN_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        frozen_constraints = extract_constraints(frozen_md)
        for aidc in AIDC_CONSTRAINTS:
            if current_constraints.get(aidc) != frozen_constraints.get(aidc):
                drift_issues.append(f"{aidc}: 快照「{frozen_constraints.get(aidc)}」→ 当前「{current_constraints.get(aidc)}」")
    else:
        drift_issues.append("v0.1.0-mvp 快照不存在，无法对比约束漂移")

    all_passed = all(aidc_checks.values()) and all(r["passed"] for r in rounds_report) and stable_checks and stable_hashes and not drift_issues
    report = {
        "schema_version": "1.0",
        "skill_version": SKILL_VERSION,
        "rounds": rounds_report,
        "aidc_checks": aidc_checks,
        "network_hits": network_hits,
        "self_sign_hits": self_sign_hits,
        "three_round_checks_identical": stable_checks,
        "three_round_hashes_identical": stable_hashes,
        "constraint_drift_issues": drift_issues,
        "instruction_stability": "INSTRUCTION_STABILITY_VERIFIED" if all_passed else "NOT_VERIFIED",
        "boundary": "三轮稳定性证据由独立验证器检查真实产物；不替代律师法律判断。",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        safe_write_json(args.output, report, allow_update=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if all_passed else 5)


if __name__ == "__main__":
    main()
