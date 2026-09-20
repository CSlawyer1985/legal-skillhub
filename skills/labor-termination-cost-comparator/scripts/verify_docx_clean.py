#!/usr/bin/env python3
"""检查 DOCX 是否含批注、修订、隐藏文字、敏感元数据或密钥模式。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


FORBIDDEN_XML_MARKERS = {
    "comments_part": ("word/comments.xml",),
    "comment_ranges": ("w:commentRangeStart", "w:commentRangeEnd", "w:commentReference"),
    "tracked_changes": ("w:ins", "w:del", "w:moveFrom", "w:moveTo", "w:trackChange"),
    "hidden_text": ("w:vanish",),
}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{20,}"),
]


def inspect_docx(path: Path, mode: str) -> dict:
    findings: list[dict[str, str]] = []
    if not path.is_file():
        return {"status": "blocked", "file": str(path), "findings": [{"kind": "missing_file", "detail": "文件不存在"}]}
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            for kind, markers in FORBIDDEN_XML_MARKERS.items():
                if kind == "comments_part":
                    if any(name in names for name in markers):
                        findings.append({"kind": kind, "detail": "存在 Word 批注部件"})
                    continue
                for name in names:
                    if not name.endswith(".xml"):
                        continue
                    text = archive.read(name).decode("utf-8", errors="replace")
                    for marker in markers:
                        if marker in text:
                            findings.append({"kind": kind, "detail": f"{name} 含 {marker}"})
            for name in names:
                if not name.endswith(".xml"):
                    continue
                text = archive.read(name).decode("utf-8", errors="replace")
                for pattern in SECRET_PATTERNS:
                    if pattern.search(text):
                        findings.append({"kind": "secret_pattern", "detail": f"{name} 命中敏感凭证模式"})
                if mode == "customer" and (re.search(r"(?i)(?:^|[\\\\/])Users[\\\\/]", text) or "提示词" in text):
                    findings.append({"kind": "internal_metadata_or_path", "detail": f"{name} 含客户版不应出现的内部路径或过程文字"})
    except (OSError, zipfile.BadZipFile) as exc:
        return {"status": "blocked", "file": str(path), "findings": [{"kind": "invalid_docx", "detail": str(exc)}]}

    status = "pass" if not findings else "block"
    return {"status": status, "file": str(path), "mode": mode, "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 DOCX 清洁交付边界")
    parser.add_argument("docx", help="待检查 DOCX")
    parser.add_argument("--mode", choices=["customer", "workpaper"], default="customer")
    args = parser.parse_args()
    result = inspect_docx(Path(args.docx), args.mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
