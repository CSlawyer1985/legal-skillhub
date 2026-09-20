#!/usr/bin/env python3
"""legal-meta-skill 的稳定命令入口。"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

try:
    from scripts.create_legal_skill import create_skill
    from scripts.export_legal_skill_ir import build_ir
    from scripts.legal_meta_security import sha256_file
    from scripts.validate_legal_skill import check
except ModuleNotFoundError:
    from create_legal_skill import create_skill
    from export_legal_skill_ir import build_ir
    from legal_meta_security import sha256_file
    from validate_legal_skill import check


ROOT = Path(__file__).resolve().parents[1]


def _write_or_print(payload: object, output: str) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output == "-":
        print(text, end="")
        return
    path = Path(output).absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _validate(skill_dir: Path) -> int:
    errors, warnings = check(skill_dir)
    for warning in warnings:
        print(f"警告：{warning}")
    for error in errors:
        print(f"错误：{error}")
    if errors:
        print(f"验证失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"验证通过：{skill_dir.name}（{len(warnings)} 个警告）")
    return 0


def _audit(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    errors, warnings = check(skill_dir)
    payload: dict[str, object] = {
        "schema_version": "legal-skill-audit-report/v1",
        "skill": skill_dir.name,
        "read_only": True,
        "errors": errors,
        "warnings": warnings,
        "evidence_boundary": {
            "static_package_checks": "passed" if not errors else "failed",
            "provider_execution": "missing evidence",
            "human_blind_review": "missing evidence",
            "real_project_regression": "missing evidence",
        },
    }
    if not errors:
        try:
            payload["ir"] = build_ir(skill_dir)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            payload["errors"] = [f"IR 导出失败：{exc}"]
    _write_or_print(payload, args.output)
    return 1 if payload["errors"] else 0


def _build_release(args: argparse.Namespace) -> int:
    source = Path(args.skill_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    errors, warnings = check(source)
    if errors:
        for error in errors:
            print(f"错误：{error}")
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_base = output_dir / f"{source.name}-v1.0.0"
    with tempfile.TemporaryDirectory(prefix="legal-meta-release-") as temp:
        staging = Path(temp) / source.name
        ignored = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "work", "dist"}
        for path in source.rglob("*"):
            relative = path.relative_to(source)
            if any(part in ignored or part.endswith(".pyc") for part in relative.parts):
                continue
            destination = staging / relative
            if path.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            elif path.is_file() and not path.is_symlink():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
        zip_path = Path(str(archive_base) + ".zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(staging.rglob("*")):
                if path.is_file():
                    info = zipfile.ZipInfo(str(path.relative_to(staging.parent)).replace("\\", "/"))
                    info.date_time = (2020, 1, 1, 0, 0, 0)
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, path.read_bytes())
        tar_path = Path(str(archive_base) + ".tar.gz")
        with tar_path.open("wb") as raw_archive:
            with gzip.GzipFile(fileobj=raw_archive, mode="wb", mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w") as archive:
                    for path in sorted(staging.rglob("*")):
                        if path.is_file():
                            info = archive.gettarinfo(str(path), arcname=str(path.relative_to(staging.parent)))
                            info.mtime = 1577836800
                            info.uid = 0
                            info.gid = 0
                            info.uname = ""
                            info.gname = ""
                            with path.open("rb") as handle:
                                archive.addfile(info, handle)
    checksums = "".join(
        f"{sha256_file(path)}  {path.name}\n"
        for path in (zip_path, tar_path)
    )
    (output_dir / "SHA256SUMS").write_text(checksums, encoding="utf-8")
    (output_dir / "SBOM.spdx.json").write_text(
        json.dumps(
            {
                "spdxVersion": "SPDX-2.3",
                "SPDXID": "SPDXRef-DOCUMENT",
                "name": source.name,
                "documentNamespace": "https://chenshi.ai/legal-meta-skill/sbom/v1.0.0",
                "packages": [{"SPDXID": "SPDXRef-Package", "name": source.name, "versionInfo": "1.0.0", "licenseConcluded": "Apache-2.0", "licenseDeclared": "Apache-2.0", "externalRefs": [{"referenceType": "purl", "referenceLocator": "pkg:generic/legal-meta-skill@1.0.0"}]}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output_dir": str(output_dir), "warnings": warnings}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="legal-meta-skill 稳定命令入口")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("skill_dir")

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("skill_dir")
    audit_parser.add_argument("--output", default="-")

    export_parser = subparsers.add_parser("export-ir")
    export_parser.add_argument("skill_dir")
    export_parser.add_argument("--output", required=True)

    route_parser = subparsers.add_parser("evaluate-route")
    route_parser.add_argument("skill_dir")
    route_parser.add_argument("--cases", required=True)
    route_parser.add_argument("--output", required=True)
    route_parser.add_argument("--observed-results")
    route_parser.add_argument("--audit-mode", action="store_true")

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--intake", required=True)
    create_parser.add_argument("--target-parent", required=True)

    release_parser = subparsers.add_parser("build-release")
    release_parser.add_argument("skill_dir")
    release_parser.add_argument("--output-dir", required=True)

    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("--input", required=True)
    migrate_parser.add_argument("--output", required=True)

    args = parser.parse_args()
    try:
        if args.command == "validate":
            return _validate(Path(args.skill_dir).resolve())
        if args.command == "audit":
            return _audit(args)
        if args.command == "export-ir":
            output = Path(args.output)
            if not output.is_absolute():
                output = Path(args.skill_dir).resolve() / output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(build_ir(Path(args.skill_dir).resolve()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"已导出法律 Skill IR：{output}")
            return 0
        if args.command == "evaluate-route":
            command = [sys.executable, str(ROOT / "scripts/evaluate_trigger_cases.py"), args.skill_dir, "--cases", args.cases, "--output", args.output]
            if args.observed_results:
                command.extend(["--observed-results", args.observed_results])
            if args.audit_mode:
                command.append("--audit-mode")
            return subprocess.run(command, check=False).returncode
        if args.command == "create":
            print(create_skill(json.loads(Path(args.intake).read_text(encoding="utf-8")), Path(args.target_parent)))
            return 0
        if args.command == "build-release":
            return _build_release(args)
        if args.command == "migrate":
            try:
                from scripts.migrate_legal_skill import migrate_intake
            except ModuleNotFoundError:
                from migrate_legal_skill import migrate_intake
            source = Path(args.input).resolve()
            output = Path(args.output).resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(migrate_intake(json.loads(source.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"已迁移 intake：{output}")
            return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}")
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
