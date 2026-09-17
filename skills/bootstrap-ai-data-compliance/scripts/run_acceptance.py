#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from common import FACT_FIELDS, CLAIM_FIELDS, SKILL_VERSION, SOURCE_FIELDS, csv_bytes, read_csv, safe_write_bytes, safe_write_json, sha256

SCRIPT_DIR = Path(__file__).resolve().parent
FLOW = SCRIPT_DIR / "flow.py"
VALIDATOR = SCRIPT_DIR / "validator.py"


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
    return {"command": command, "returncode": result.returncode, "stdout_tail": result.stdout[-1200:], "stderr_tail": result.stderr[-1200:]}


def flow(*args: str) -> list[str]:
    return [sys.executable, str(FLOW), *args]


def validator(target: Path) -> list[str]:
    return [sys.executable, str(VALIDATOR), "--target", str(target), "--write-report"]


def complete_gate(target: Path) -> None:
    fact_path = target / "ai_compliance/02_evidence/fact_records.csv"
    rows = read_csv(fact_path)
    for index, row in enumerate(rows, 1):
        row.update({
            "evidence_id": f"EV-{index:03d}",
            "evidence_location": f"04_fact_verification/evidence/EV-{index:03d}.txt",
            "evidence_hash": "test-hash-" + str(index),
            "owner": "测试责任人",
            "fact_status": "客户已确认",
            "confirmation_method": "书面材料",
            "confirmed_by": "测试确认人",
            "confirmed_at": "2026-08-17",
            "conflict_status": "无冲突",
            "lawyer_review_status": "需律师确认",
            "recheck_status": "未复评",
            "boundary": "脱敏模拟事实，仅用于MVP验收",
        })
    safe_write_bytes(fact_path, csv_bytes(rows, FACT_FIELDS), allow_update=True)
    evidence_dir = target / "ai_compliance/04_fact_verification/evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1, len(rows) + 1):
        (evidence_dir / f"EV-{index:03d}.txt").write_text("脱敏模拟证据，仅用于Skill测试。\n", encoding="utf-8")
    gate_path = target / "ai_compliance/04_fact_verification/gate_evidence.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    for key in list(gate):
        if key not in {"schema_version", "notes"}:
            gate[key] = True
    gate["notes"] = "脱敏模拟场景已完成全部门禁，仅用于MVP验收。"
    safe_write_json(gate_path, gate, allow_update=True)


def create_generic_case(root: Path, profile: str, project_id: str, name: str, use_case: str) -> tuple[list[dict], Path]:
    target = root / project_id.lower()
    logs: list[dict] = []
    logs.append(run(flow("init", "--target", str(target), "--profile", profile, "--project-id", project_id, "--project-name", name, "--use-case", use_case)))
    inputs = target / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    (inputs / "项目资料.txt").write_text(f"{name}\n{use_case}\n脱敏模拟资料。\n", encoding="utf-8")
    logs.append(run(flow("advance", "--target", str(target), "--to", "startup_pack_ready")))
    logs.append(run(validator(target)))
    logs.append(run(flow("advance", "--target", str(target), "--to", "facts_verified")))
    complete_gate(target)
    logs.append(run(flow("advance", "--target", str(target), "--to", "candidate_ready")))
    logs.append(run(validator(target)))
    logs.append(run(flow("advance", "--target", str(target), "--to", "validated_archived")))
    logs.append(run(validator(target)))
    logs.append(run(flow("advance", "--target", str(target), "--to", "validated_archived")))
    return logs, target


def copy_bci_fixture(source_root: Path, target: Path) -> str:
    paths = [
        "ai/work/knowledge_hub/01_indexes/source_records.csv",
        "ai/work/knowledge_hub/01_indexes/claim_records.csv",
        "ai/work/knowledge_hub/01_indexes/assessment_records.csv",
        "ai/outputs/脑机接口医疗AI法律合规全景图（交互版）.html",
    ]
    for relative in paths:
        source = source_root / relative
        if not source.exists():
            raise FileNotFoundError(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return sha256(target / paths[-1])


def create_bci_case(root: Path, source_root: Path) -> tuple[list[dict], Path, bool]:
    target = root / "bci-adopt"
    before = copy_bci_fixture(source_root, target)
    logs = [run(flow("adopt", "--target", str(target), "--profile", "bci-medical-ai", "--project-id", "BCI-MVP", "--project-name", "脑机接口医疗AI合规适配测试", "--use-case", "既有项目只读接入"))]
    logs.append(run(flow("advance", "--target", str(target), "--to", "startup_pack_ready")))
    logs.append(run(validator(target)))
    logs.append(run(flow("advance", "--target", str(target), "--to", "facts_verified")))
    after = sha256(target / "ai/outputs/脑机接口医疗AI法律合规全景图（交互版）.html")
    return logs, target, before == after


def clone_case(source: Path, destination: Path) -> Path:
    shutil.copytree(source, destination)
    return destination


def mutate_docx(path: Path, marker: str) -> None:
    with zipfile.ZipFile(path, "r") as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    xml_name = "word/document.xml"
    xml = entries[xml_name].decode("utf-8")
    xml = xml.replace("</w:body>", f"<w:p><w:r><w:t>{marker}</w:t></w:r></w:p></w:body>")
    entries[xml_name] = xml.encode("utf-8")
    temporary = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    temporary.replace(path)


def negative_tests(root: Path, clean_case: Path) -> list[dict]:
    results = []
    duplicate = clone_case(clean_case, root / "negative-duplicate")
    source_path = duplicate / "ai_compliance/02_evidence/source_records.csv"
    rows = read_csv(source_path)
    rows.append(dict(rows[0]))
    safe_write_bytes(source_path, csv_bytes(rows, SOURCE_FIELDS), allow_update=True)
    results.append({"name": "duplicate_id", "run": run(validator(duplicate)), "expected": 5})

    label_case = clone_case(clean_case, root / "negative-label")
    claim_path = label_case / "ai_compliance/02_evidence/claim_records.csv"
    claims = read_csv(claim_path)
    claims[0]["evidence_label"] = "自动确认"
    safe_write_bytes(claim_path, csv_bytes(claims, CLAIM_FIELDS), allow_update=True)
    results.append({"name": "illegal_label", "run": run(validator(label_case)), "expected": 5})

    absolute = clone_case(clean_case, root / "negative-absolute")
    project_path = absolute / "ai_compliance/00_project/project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["legacy_path"] = "/Users/example/old-computer/private-project"
    safe_write_json(project_path, project, allow_update=True)
    results.append({"name": "absolute_path", "run": run(validator(absolute)), "expected": 5})

    formal = clone_case(clean_case, root / "negative-formal")
    candidate = sorted((formal / "ai_compliance/05_candidate_delivery/Word候选包").glob("*.docx"))[0]
    mutate_docx(candidate, "本文件为正式法律意见")
    results.append({"name": "formal_opinion_wording", "run": run(validator(formal)), "expected": 5})

    elevated = clone_case(clean_case, root / "negative-research-elevation")
    source_path = elevated / "ai_compliance/02_evidence/source_records.csv"
    sources = read_csv(source_path)
    sources[0]["source_type"] = "论文"
    safe_write_bytes(source_path, csv_bytes(sources, SOURCE_FIELDS), allow_update=True)
    claim_path = elevated / "ai_compliance/02_evidence/claim_records.csv"
    claims = read_csv(claim_path)
    claims[0]["legal_effect"] = "直接证明法律义务"
    claims[0]["claim_boundary"] = ""
    safe_write_bytes(claim_path, csv_bytes(claims, CLAIM_FIELDS), allow_update=True)
    results.append({"name": "research_elevated_to_law", "run": run(validator(elevated)), "expected": 5})

    overwrite = run(flow("init", "--target", str(clean_case), "--profile", "internal-knowledge-assistant", "--project-id", "CHANGED", "--project-name", "不同名称", "--use-case", "冲突测试"))
    results.append({"name": "overwrite_protection", "run": overwrite, "expected": 4})

    formal_stage = run(flow("advance", "--target", str(clean_case), "--to", "formal_opinion"))
    results.append({"name": "unsupported_formal_stage", "run": formal_stage, "expected": 2})
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bci-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(tempfile.mkdtemp(prefix="bootstrap-ai-data-compliance-acceptance-", dir="/private/tmp"))
    dry_target = root / "dry-run-target"
    dry = run(flow("init", "--target", str(dry_target), "--profile", "internal-knowledge-assistant", "--project-id", "DRY", "--project-name", "预演", "--use-case", "不写入测试", "--dry-run"))
    internal_logs, internal = create_generic_case(root, "internal-knowledge-assistant", "IKA-MVP", "内部知识助手合规测试", "企业内部文档检索与问答")
    customer_logs, customer = create_generic_case(root, "customer-service-agent", "CSA-MVP", "客服Agent合规测试", "面向消费者的智能客服与人工转接")
    bci_logs, bci, bci_hash_unchanged = create_bci_case(root, args.bci_source_root.resolve())
    negatives = negative_tests(root, internal)
    positive_runs = [dry, *internal_logs, *customer_logs, *bci_logs]
    gate_blocks = [item for item in positive_runs if item["returncode"] == 3]
    unexpected = [item for item in positive_runs if item["returncode"] not in {0, 3}]
    negative_passed = all(item["run"]["returncode"] == item["expected"] for item in negatives)
    checks = {
        "dry_run_no_write": dry["returncode"] == 0 and not dry_target.exists(),
        "internal_full_flow": json.loads((internal / "ai_compliance/06_validation/domain_validation.json").read_text(encoding="utf-8"))["passed"],
        "customer_agent_full_flow": json.loads((customer / "ai_compliance/06_validation/domain_validation.json").read_text(encoding="utf-8"))["passed"],
        "bci_adopt_startup_flow": json.loads((bci / "ai_compliance/06_validation/domain_validation.json").read_text(encoding="utf-8"))["passed"],
        "bci_formal_hash_unchanged": bci_hash_unchanged,
        "fact_gate_blocks_before_confirmation": len(gate_blocks) >= 3,
        "positive_runs_expected": not unexpected,
        "negative_cases_blocked": negative_passed,
        "archive_created": (internal / f"ai_compliance/07_archive/{SKILL_VERSION}/AI数据合规候选交付包-{SKILL_VERSION}.zip").exists() and (customer / f"ai_compliance/07_archive/{SKILL_VERSION}/AI数据合规候选交付包-{SKILL_VERSION}.zip").exists(),
    }
    report = {
        "schema_version": "1.0",
        "passed": all(checks.values()),
        "completion_marker": "DOMAIN_VERIFIED" if all(checks.values()) else "NOT_VERIFIED",
        "instruction_stability": "NOT_VERIFIED",
        "checks": checks,
        "workspace": str(root),
        "scenario_paths": {"internal": str(internal), "customer_agent": str(customer), "bci": str(bci)},
        "negative_cases": [{"name": item["name"], "expected": item["expected"], "actual": item["run"]["returncode"]} for item in negatives],
        "unexpected_runs": unexpected,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        safe_write_json(args.output, report, allow_update=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 5)


if __name__ == "__main__":
    main()
