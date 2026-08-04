#!/usr/bin/env python3
"""独立表格版式校验子进程（全部表格全部行cantSplit+首行tblHeader+禁固定行高）。
用法: validate_layout_extra_t2.py <docx_dir>  exit 0/3"""
import sys, zipfile
from pathlib import Path
def main():
    for dx in sorted(Path(sys.argv[1]).glob("0*.docx")):
        with zipfile.ZipFile(dx) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        if "<w:trHeight" in xml: print(f"HOLD-LAYOUT: {dx.name}表格含固定行高"); return 3
        n_tr = xml.count("<w:tr ") + xml.count("<w:tr>")
        n_cant = xml.count("<w:cantSplit")
        if n_tr and n_cant < n_tr:
            print(f"HOLD-LAYOUT: {dx.name}表格行cantSplit不足({n_cant}/{n_tr})"); return 3
        n_tbl = xml.count("<w:tbl>") + xml.count("<w:tbl ")
        n_hdr = xml.count("<w:tblHeader")
        if n_tbl and n_hdr < n_tbl:
            print(f"HOLD-LAYOUT: {dx.name}表格缺跨页重复表头({n_hdr}/{n_tbl})"); return 3
    print("VALID: 全表禁拆+首行重复表头+零固定行高"); return 0
if __name__ == "__main__": sys.exit(main())
