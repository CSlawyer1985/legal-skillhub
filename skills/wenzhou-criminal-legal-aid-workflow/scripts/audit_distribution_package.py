#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import re
import tempfile
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree as ET


TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".gitignore"}
ID_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
MOBILE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
CASE_NO_RE = re.compile(r"[（(]\d{4}[）)].{0,16}(?:刑初|刑终|刑申|刑再|刑诉|刑援)\d+号")
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
CP_NS = "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}"


def xml_text(data: bytes) -> str:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return data.decode("utf-8", "ignore")
    return "\n".join((node.text or "") for node in root.iter() if node.tag in {W_NS + "t", W_NS + "instrText"})


def privacy_hits(label: str, text: str, denylist: list[str]) -> list[str]:
    hits: list[str] = []
    if ID_RE.search(text):
        hits.append(f"{label}: 疑似居民身份证号")
    if MOBILE_RE.search(text):
        hits.append(f"{label}: 疑似个人手机号")
    if CASE_NO_RE.search(text):
        hits.append(f"{label}: 疑似真实案件编号")
    for token in denylist:
        if token and token in text:
            hits.append(f"{label}: 命中私有禁用词")
    return hits


def audit_ooxml(path: Path, denylist: list[str]) -> list[str]:
    errors: list[str] = []
    try:
        with ZipFile(path) as zf:
            names = set(zf.namelist())
            if any(name.startswith(("word/media/", "word/embeddings/", "xl/media/", "xl/embeddings/")) for name in names):
                errors.append(f"{path}: 含图片或嵌入对象，发布前须人工确认并移除签章/证件")
            if any("comments" in name or "people" in name for name in names):
                errors.append(f"{path}: 含批注或人员信息部件")
            for name in sorted(names):
                if not name.endswith(".xml"):
                    continue
                data = zf.read(name)
                decoded = data.decode("utf-8", "ignore")
                if re.search(r"<w:(?:ins|del)(?:\s|>)|<w:commentRangeStart(?:\s|>)", decoded):
                    errors.append(f"{path}!{name}: 含修订或批注锚点")
                if name == "docProps/core.xml":
                    try:
                        root = ET.fromstring(data)
                        creator = root.find(DC_NS + "creator")
                        modifier = root.find(CP_NS + "lastModifiedBy")
                        if creator is not None and (creator.text or "").strip():
                            errors.append(f"{path}: creator 元数据未清空")
                        if modifier is not None and (modifier.text or "").strip():
                            errors.append(f"{path}: lastModifiedBy 元数据未清空")
                    except ET.ParseError:
                        errors.append(f"{path}: core.xml 无法解析")
                visible = xml_text(data)
                errors.extend(privacy_hits(f"{path}!{name}", visible, denylist))
                if path.suffix.lower() == ".docx" and name.startswith("word/"):
                    for line in visible.splitlines():
                        match = re.match(r"^\s*答\s*[:：]\s*(\S.+)$", line)
                        if match and not match.group(1).startswith("{{"):
                            errors.append(f"{path}!{name}: 模板答复栏疑似已有内容")
    except BadZipFile:
        errors.append(f"{path}: 不是有效 OOXML 文件")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a Skill distribution package for common privacy leaks.")
    parser.add_argument("root", type=Path)
    parser.add_argument("--denylist", type=Path, help="Optional private denylist, one token per line; do not ship it.")
    args = parser.parse_args()
    root = args.root.resolve()
    denylist: list[str] = []
    if args.denylist:
        denylist = [line.strip() for line in args.denylist.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root)
        if any(part in {".git", "__pycache__"} for part in rel.parts):
            continue
        if path.suffix.lower() in {".docx", ".xlsx"}:
            errors.extend(audit_ooxml(path, denylist))
        elif path.name.endswith((".docx.b64.txt", ".xlsx.b64.txt")):
            try:
                payload = base64.b64decode("".join(path.read_text(encoding="ascii").split()), validate=True)
                suffix = ".xlsx" if path.name.endswith(".xlsx.b64.txt") else ".docx"
                with tempfile.NamedTemporaryFile(suffix=suffix) as fh:
                    fh.write(payload)
                    fh.flush()
                    errors.extend(audit_ooxml(Path(fh.name), denylist))
            except Exception as exc:
                errors.append(f"{path}: 嵌入模板无法解码或审计：{exc}")
        elif path.suffix.lower() in TEXT_SUFFIXES:
            errors.extend(privacy_hits(str(path), path.read_text(encoding="utf-8", errors="ignore"), denylist))
    if errors:
        raise SystemExit("分发包隐私审计失败：\n- " + "\n- ".join(dict.fromkeys(errors)))
    print(f"PASS: {root}")


if __name__ == "__main__":
    main()
