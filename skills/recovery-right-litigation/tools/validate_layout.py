#!/usr/bin/env python3
"""九文书类别与OOXML版式硬门v4：namespace-aware XML树解析（ElementTree），
带任意属性的w:p/w:r/w:tbl/w:tr/w:tc一律入检；解析失败或可见run缺格式=fail-closed。
用法: validate_layout.py <目录> | --selftest
exit 0=PASS, 3=FAIL。--selftest：十二例（八变异+四正例）（原四类+段落属性+run属性）全须exit3且正例exit0。"""
import sys, re, zipfile, tempfile, shutil, subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NINE = ["01-民事起诉状","02-证据目录","03-合同审查方案","04-材料缺失清单","05-代理词",
        "06-法律意见书","07-诉讼案件办案方案工作底稿","08-质证预案","09-条件性正式质证意见生成门"]
TITLE = {"01":"民事起诉状","02":"证据目录","03":"合同与担保链审查方案","04":"材料缺失清单","05":"代理词",
         "06":"法律意见书","07":"诉讼案件办案方案工作底稿","08":"质证预案","09":"条件性正式质证意见生成门"}
COLS = ["组号","证据名称","证据来源","证明内容","页数","原件情况"]
COMBO_LINE = {("Songti SC","28"):"560",("Heiti SC","36"):"720",("Heiti SC","30"):"600",
              ("Heiti SC","28"):"560",("Heiti SC","21"):"320"}
def p_text(p):
    return "".join(t.text or "" for t in p.iter(f"{W}t"))
def runs_of(p):
    out = []
    for r in p.iter(f"{W}r"):
        txt = "".join(t.text or "" for t in r.findall(f"{W}t"))
        if not txt: continue
        rPr = r.find(f"{W}rPr")
        f = s = None
        if rPr is not None:
            rf = rPr.find(f"{W}rFonts")
            if rf is not None: f = rf.get(f"{W}eastAsia")
            sz = rPr.find(f"{W}sz")
            if sz is not None: s = sz.get(f"{W}val")
        out.append((f, s))
    return out
def line_of(p):
    pPr = p.find(f"{W}pPr")
    if pPr is None: return None
    sp = pPr.find(f"{W}spacing")
    if sp is None: return None
    return (sp.get(f"{W}lineRule"), sp.get(f"{W}line"))
def check_paras(name, paras, in_table, fails):
    for i, p in enumerate(paras):
        rs = runs_of(p)
        if not rs: continue
        if in_table:
            for combo in set(rs):
                if combo != ("Songti SC","22"): fails.append(f"{name}: 表格段{i}非宋体11pt: {combo}")
            if line_of(p) != ("exact","400"): fails.append(f"{name}: 表格段{i}行距{line_of(p)}≠(exact,400)")
        else:
            combos = set(rs)
            if None in {c[0] for c in combos} or None in {c[1] for c in combos}:
                fails.append(f"{name}: 段{i}存在缺字体/字号的可见run（fail-closed）"); continue
            if len(combos) > 1: fails.append(f"{name}: 段{i}混合字体/字号{sorted(combos)}"); continue
            combo = combos.pop()
            if combo not in COMBO_LINE: fails.append(f"{name}: 段{i}非法组合{combo}"); continue
            if line_of(p) != ("exact", COMBO_LINE[combo]):
                fails.append(f"{name}: 段{i}行距{line_of(p)}≠(exact,{COMBO_LINE[combo]})")
def main(target):
    root = Path(target); fails = []
    found = {p.stem: p for p in root.rglob("0*.docx")}
    for name in NINE:
        if name not in found: fails.append(f"九类缺失: {name}"); continue
        try:
            xml_bytes = zipfile.ZipFile(found[name]).read('word/document.xml')
            tree = ET.fromstring(xml_bytes)
        except Exception as e:
            fails.append(f"{name}: 解析失败(fail-closed): {e}"); continue
        body = tree.find(f"{W}body")
        if body is None: fails.append(f"{name}: 无body"); continue
        num = name[:2]
        full_text = p_text(body)
        if TITLE[num] not in full_text[:300]: fails.append(f"{name}: 类别标题未在文首")
        # sectPr：页面与边距
        sect = body.find(f"{W}sectPr")
        pgSz = sect.find(f"{W}pgSz") if sect is not None else None
        if pgSz is None: fails.append(f"{name}: 无pgSz")
        else:
            w = int(pgSz.get(f"{W}w")); h = int(pgSz.get(f"{W}h")); orient = pgSz.get(f"{W}orient")
            if num == "02":
                if not (abs(w-16838)<=2 and abs(h-11906)<=2 and orient=="landscape"):
                    fails.append(f"{name}: 02须精确A4横向16838×11906+orient（现{w}×{h},{orient}）")
            else:
                if not (abs(w-11906)<=2 and abs(h-16838)<=2): fails.append(f"{name}: 非精确A4纵向({w}×{h})")
                if orient == "landscape": fails.append(f"{name}: 不应横向")
        pgMar = sect.find(f"{W}pgMar") if sect is not None else None
        if pgMar is None: fails.append(f"{name}: 无pgMar")
        else:
            v = {k: int(pgMar.get(f"{W}{k}")) for k in ("top","bottom","left","right")}
            if abs(v["top"]-1440)>2 or abs(v["bottom"]-1440)>2: fails.append(f"{name}: 上/下边距({v['top']}/{v['bottom']})")
            if abs(v["left"]-1797)>3 or abs(v["right"]-1797)>3: fails.append(f"{name}: 左/右边距({v['left']}/{v['right']})")
        # 结构遍历：全树段落（含sdt/修订等标准容器后代），parent map按表格祖先分区
        parent_map = {c: pa for pa in tree.iter() for c in pa}
        def in_tbl(node):
            cur = parent_map.get(node)
            while cur is not None:
                if cur.tag == f"{W}tbl": return True
                cur = parent_map.get(cur)
            return False
        all_paras = list(body.iter(f"{W}p"))
        check_paras(name, [q for q in all_paras if not in_tbl(q)], False, fails)
        check_paras(name, [q for q in all_paras if in_tbl(q)], True, fails)
        tables = body.findall(f"{W}tbl") or [tb for tb in body.iter(f"{W}tbl")]
        tables = list(body.iter(f"{W}tbl"))
        # 02专项（XML树逐位）
        if num == "02":
            all_trs = [tr for tbl in tables for tr in tbl.iter(f"{W}tr")]
            n_hdr = sum(1 for tr in all_trs if tr.find(f"{W}trPr") is not None and tr.find(f"{W}trPr").find(f"{W}tblHeader") is not None)
            n_cs  = sum(1 for tr in all_trs if tr.find(f"{W}trPr") is not None and tr.find(f"{W}trPr").find(f"{W}cantSplit") is not None)
            n_ht  = sum(1 for tr in all_trs if tr.find(f"{W}trPr") is not None and tr.find(f"{W}trPr").find(f"{W}trHeight") is not None)
            if n_hdr != 1: fails.append(f"{name}: tblHeader须恰1（现{n_hdr}）")
            if n_cs != len(all_trs): fails.append(f"{name}: cantSplit须全{len(all_trs)}行（现{n_cs}）")
            if n_ht: fails.append(f"{name}: 存在固定行高{n_ht}处")
            if not tables: fails.append(f"{name}: 无表格")
            else:
                first_tr = next(iter(tables[0].iter(f"{W}tr")), None)
                cells = [p_text(tc) for tc in first_tr.findall(f"{W}tc")] if first_tr is not None else []
                if cells != COLS: fails.append(f"{name}: 首表首行列序≠严格六列（现{cells}）")
    if fails:
        for f in fails[:30]: print("FAIL:", f)
        print(f"INVALID: {len(fails)}"); return 3
    print("VALID: 九类+页面边距+树解析逐段逐run+02严格列序 全过(namespace-aware)"); return 0
def _mut(dx, fn):
    src = zipfile.ZipFile(dx); items = {n: src.read(n) for n in src.namelist()}; src.close()
    items["word/document.xml"] = fn(items["word/document.xml"].decode("utf-8")).encode("utf-8")
    with zipfile.ZipFile(dx,"w") as z:
        for n,b in items.items(): z.writestr(n,b)
def selftest(target):
    root = Path(target).resolve()
    src = next((d for d in [root/"e2e/docx", root] if list(Path(d).glob("0*.docx"))), None)
    if src is None: print("SELFTEST-FAIL: 无正例DOCX"); return 1
    def case(label, doc, fn, expect):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)/"docs"; shutil.copytree(src, d)
            if fn: _mut(d/doc, fn)
            rc = main(d) if False else subprocess.run([sys.executable,"-B",__file__,str(d)],capture_output=True).returncode
            ok = rc == expect
            print(f"selftest[{label}]: exit={rc} 期望{expect} {'OK' if ok else 'FAIL'}")
            return ok
    NSDECL = 'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    def add_ns(x):
        return x.replace('<w:document ', '<w:document ' + NSDECL, 1) if "w14" not in x else x
    ok = True
    ok &= case("正例", None, None, 0)
    ok &= case("02任意横版+1twip边距", "02-证据目录.docx", lambda x: re.sub(r'w:bottom="\d+"','w:bottom="1"',re.sub(r'<w:pgSz[^/]*/>','<w:pgSz w:w="20000" w:h="10000" w:orient="landscape"/>',x)), 3)
    ok &= case("02列序调换", "02-证据目录.docx", lambda x: x.replace(">组号<",">__T__<",1).replace(">证据名称<",">组号<",1).replace(">__T__<",">证据名称<",1), 3)
    ok &= case("字体全改Arial", "01-民事起诉状.docx", lambda x: x.replace('w:eastAsia="Songti SC"','w:eastAsia="Arial"'), 3)
    ok &= case("字号行距全改", "01-民事起诉状.docx", lambda x: x.replace('<w:sz w:val="28"','<w:sz w:val="20"').replace('w:line="560"','w:line="240"'), 3)
    ok &= case("段落属性+坏样式", "01-民事起诉状.docx", lambda x: add_ns(x).replace('<w:p>','<w:p w14:paraId="12345678">').replace('w:eastAsia="Songti SC"','w:eastAsia="Arial"'), 3)
    ok &= case("run属性+坏样式", "01-民事起诉状.docx", lambda x: add_ns(x).replace('<w:r>','<w:r w14:textId="12345678">').replace('<w:sz w:val="28"','<w:sz w:val="20"'), 3)
    ok &= case("属性但样式正确(合法)", "01-民事起诉状.docx", lambda x: add_ns(x).replace('<w:p>','<w:p w14:paraId="0A0B0C0D">').replace('<w:r>','<w:r w14:textId="0A0B0C0D">'), 0)
    def wrap_sdt(x):
        return re.sub(r'(<w:p>.*?</w:p>)', r'<w:sdt><w:sdtContent>\1</w:sdtContent></w:sdt>', x, flags=re.S)
    def wrap_ins(x):
        return re.sub(r'(<w:r>.*?</w:r>)', r'<w:ins w:id="1" w:author="审校" w:date="2026-01-01T00:00:00Z">\1</w:ins>', x, flags=re.S)
    ok &= case("坏样式+sdt段落包装", "01-民事起诉状.docx", lambda x: wrap_sdt(x.replace('w:eastAsia="Songti SC"','w:eastAsia="Arial"').replace('<w:sz w:val="28"','<w:sz w:val="20"').replace('w:line="560"','w:line="240"')), 3)
    ok &= case("坏样式+ins run包装", "01-民事起诉状.docx", lambda x: wrap_ins(x.replace('w:eastAsia="Songti SC"','w:eastAsia="Arial"').replace('<w:sz w:val="28"','<w:sz w:val="20"')), 3)
    ok &= case("合法sdt包装(样式正确)", "01-民事起诉状.docx", wrap_sdt, 0)
    ok &= case("合法ins包装(样式正确)", "01-民事起诉状.docx", wrap_ins, 0)
    print("LAYOUT-SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1
if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest(sys.argv[2] if len(sys.argv)>2 else "."))
    sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "."))
