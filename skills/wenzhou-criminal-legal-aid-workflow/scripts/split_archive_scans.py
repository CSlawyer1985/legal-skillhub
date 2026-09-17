#!/usr/bin/env python3
"""按确认页码提取归档 PDF；原文件只读，输出位置由使用者指定。
规则：[{"name":"通知书","from":1,"to":2},{"name":"会见材料","pages":[3,7,8]}]
页码从 1 起；pages 按指定顺序组合。已有同名文件不覆盖。
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path
from pypdf import PdfReader, PdfWriter

FORBIDDEN = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def sanitize_name(name):
    if not isinstance(name, str):
        raise ValueError("切割名称必须是文字。")
    cleaned = FORBIDDEN.sub("－", name).strip().rstrip(".")
    if not cleaned:
        raise ValueError("切割名称不能为空。")
    return cleaned


def parse_plan(spec, total, out, allow_overlap):
    if not isinstance(spec, list) or not spec:
        raise ValueError("spec 必须是非空数组。")
    plan, names, seen, overlaps = [], set(), set(), set()
    for item in spec:
        if not isinstance(item, dict):
            raise ValueError("每项切割规则必须是对象。")
        name = sanitize_name(item.get("name", ""))
        filename = name + ".pdf"
        normalized = unicodedata.normalize("NFC", filename).casefold()
        if normalized in names:
            raise ValueError(f"重复输出文件名（含清理后重名）：{filename}")
        names.add(normalized)
        target = out / filename
        if target.exists() or target.is_symlink():
            raise ValueError(f"目标已存在，未覆盖：{target}")
        if "pages" in item:
            if "from" in item or "to" in item:
                raise ValueError(f"{name}: pages 不能与 from/to 同用。")
            pages = item["pages"]
            if not isinstance(pages, list) or not pages:
                raise ValueError(f"{name}: pages 必须是非空页码数组。")
        else:
            start, end = item.get("from"), item.get("to")
            if type(start) is not int or type(end) is not int:
                raise ValueError(f"{name}: from/to 必须为整数页码。")
            if not 1 <= start <= end <= total:
                raise ValueError(f"{name}: 页码 {start}-{end} 超出范围（1-{total}）。")
            pages = list(range(start, end + 1))
        if any(type(p) is not int or not 1 <= p <= total for p in pages):
            raise ValueError(f"{name}: 页码必须为 1-{total} 范围内整数。")
        for page in pages:
            if page in seen:
                overlaps.add(page)
            seen.add(page)
        plan.append((target, pages))
    if overlaps and not allow_overlap:
        raise ValueError(f"重复分配页码：{sorted(overlaps)}；确需复用时加 --allow-overlap。")
    return plan, sorted(set(range(1, total + 1)) - seen), sorted(overlaps)


def split(src, spec, out, allow_overlap=False):
    if not src.is_file():
        raise ValueError(f"输入不存在或不是文件：{src}")
    reader = PdfReader(str(src))
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError("PDF 已加密，请使用已获授权的本地解密工作副本；本工具不保存密码。")
    total = len(reader.pages)
    if total == 0:
        raise ValueError("输入 PDF 没有页面。")
    if out.exists() and not out.is_dir():
        raise ValueError(f"输出位置不是文件夹：{out}")
    plan, missing, overlaps = parse_plan(spec, total, out, allow_overlap)
    # 全部输入及目标先验证。源文件同名目标也在此被拦截。
    existed = out.exists()
    out.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        with tempfile.TemporaryDirectory(prefix=".archive-staging-", dir=out) as td:
            staged = []
            for index, (target, pages) in enumerate(plan):
                writer = PdfWriter()
                for page in pages:
                    writer.add_page(reader.pages[page - 1])
                tmp = Path(td) / f"{index}.pdf"
                with tmp.open("wb") as handle:
                    writer.write(handle)
                if len(PdfReader(str(tmp)).pages) != len(pages):
                    raise ValueError(f"{target.name}: 写入后页数校验失败。")
                staged.append((tmp, target))
            # 同一文件系统硬链接独占交付；同名文件出现时也不会覆盖。
            for tmp, target in staged:
                os.link(tmp, target)
                created.append(target)
    except Exception:
        for target in reversed(created):
            target.unlink()
        if not existed:
            try:
                out.rmdir()
            except OSError:
                pass
        raise
    for target, pages in plan:
        print(f"完成 {target.name} ← 页码 {pages}（{len(pages)}页）")
    if overlaps:
        print(f"已显式允许重复分配页码：{overlaps}")
    if missing:
        print(f"未分配页码：{missing}；请核对是否有意排除。")
    else:
        print(f"全部 {total} 页已分配完毕。")
    print("上传前请核对栏目、页序、页数与签章。")


def main():
    parser = argparse.ArgumentParser(description="按归档栏目提取 PDF，全部规则先验证，不覆盖已有文件。")
    parser.add_argument("--input", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output-dir", required=True, help="使用者指定的输出文件夹，可在原材料旁")
    parser.add_argument("--allow-overlap", action="store_true", help="明确允许同一页被多次分配")
    args = parser.parse_args()
    src = Path(args.input).expanduser().resolve()
    out = Path(args.output_dir).expanduser().resolve()
    spec = json.loads(Path(args.spec).expanduser().read_text(encoding="utf-8"))
    split(src, spec, out, args.allow_overlap)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"切割失败，未交付本次切割文件：{exc}", file=sys.stderr)
        raise SystemExit(2) from None
