#!/usr/bin/env python3
"""T4构建器（合同8644715d…）：同案独立冻结07为唯一语义输入→A01-A09锚（64位节hash+精确字符区间）
→case-views.json+view-spec.json。用法: build_t4.py --root . --t3-root <T3根> --vis-enabled
exit 0=OK / 3=HOLD-VIS"""
import sys, os, json, re, hashlib
from pathlib import Path

CONTRACT_SHA = "8644715d0a145b06ae9387939d9f850d4b8ca1c252eb67076c30fe12665feae2"
MD = "07-诉讼案件办案方案工作底稿.md"
DOCX = "07-诉讼案件办案方案工作底稿.docx"
ANCHOR_TITLES = ["第一节　主体与角色","第二节　合同与交易链","第三节　履行与交付链","第四节　款项与余额",
                 "第五节　通知抗辩与期间","第六节　要件-事实-证据矩阵","第七节　证据索引",
                 "第八节　诉讼阶段计划","第九节　风险与暂停事项"]
VIEW_MAP = {"01-主体关系图": ["A01","A02"],
            "02-关键事件时间线": ["A02","A03","A04","A05"],
            "03-要件证据矩阵": ["A04","A06","A07"],
            "04-阶段计划与风险": ["A08","A09"]}
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hold(msg): print(f"HOLD-VIS: {msg}"); return 3

def extract_anchors(text):
    """返回A01-A09锚：exact char ranges + sha256(section utf8 bytes)。区间=节标题行首→下一节标题行首/文末。"""
    anchors = []
    idxs = []
    for i, title in enumerate(ANCHOR_TITLES):
        m = re.search(rf"^## {re.escape(title)}$", text, re.M)
        if not m: return None, f"缺节:{title}"
        idxs.append(m.start())
    if idxs != sorted(idxs): return None, "节序错乱"
    for i, title in enumerate(ANCHOR_TITLES):
        start = idxs[i]
        end = idxs[i+1] if i+1 < 9 else len(text)
        seg = text[start:end]
        anchors.append({"anchor_id": f"A{i+1:02d}", "title": title,
            "char_start": start, "char_end": end,
            "sha256": hashlib.sha256(seg.encode("utf-8")).hexdigest(),
            "hash_algorithm": "sha256-file-section-utf8/v1"})
    return anchors, None

def table_all(seg):
    rows = []
    for line in seg.splitlines():
        if line.startswith("|") and not re.match(r"^\|[\s\-|]+\|$", line):
            cells = [c.strip().replace("**","") for c in line.strip("|").split("|")]
            rows.append(cells)
    return rows
def table_rows(seg):
    rows = table_all(seg)
    return rows[1:] if rows else []  # 数据行（跳表头与分隔行）
def section_summary(seg):
    """表格节→数据行自然中文摘要（表头字段名=值）＋节内散文行全文；散文节→实质行。全文零截断。
    双口径表（表头含『口径』且≥2数据行）前置忠实摘要行（依节内纪律行）。"""
    rows = table_all(seg)
    outs = []
    if len(rows) >= 2:
        hdr = rows[0]
        if any("口径" in h for h in hdr) and len(rows) >= 3:
            outs.append("本节登记双口径余额，最终以对账核定为准（依本节纪律行）")
        for r in rows[1:]:
            outs.append("，".join(f"{hdr[j]}={r[j]}" if j < len(hdr) and hdr[j] else r[j]
                                   for j in range(len(r)) if r[j]))
    for l in seg.splitlines()[1:]:
        ls = l.strip()
        if ls and not ls.startswith("## ") and not ls.startswith("|"):
            outs.append(ls.replace("**",""))
            if rows and len(outs) > len(rows):  # 表格节只补散文行
                pass
            if not rows:
                break
    return outs

def date_lines(seg):
    out = []
    for line in seg.splitlines():
        if line.startswith("|"):
            cells = [c.strip().replace("**","") for c in line.strip("|").split("|")]
            if re.match(r"^[\s\-|]*$", "".join(cells)): continue
            pl = "，".join(c for c in cells if c)
        else:
            pl = line.strip().lstrip("0123456789.、- ").replace("**","")
        for m in re.finditer(r"\d{4}[-年]\d{1,2}[-月]\d{1,2}日?", line):
            out.append({"date": m.group(0).replace("年","-").replace("月","-").replace("日",""),
                        "text": pl})
            break
    return out

def build_case_views(text, case_id):
    anchors, err = extract_anchors(text)
    if err: return None, err
    seg = {a["anchor_id"]: text[a["char_start"]:a["char_end"]] for a in anchors}
    views = {}
    # 01 主体关系图：A01主体表 + A02交易链行
    parties = [{"text": " / ".join(c for c in r if c), "anchor_ids": ["A01"]} for r in table_rows(seg["A01"])][:8]
    chain = [{"text": l.strip().replace("**","").lstrip("0123456789.、- "), "anchor_ids": ["A02"]}
             for l in seg["A02"].splitlines()[1:] if l.strip() and not l.startswith("## ")][:6]
    views["01-主体关系图"] = {"anchor_ids": VIEW_MAP["01-主体关系图"], "parties": parties, "chain": chain}
    # 02 时间线：A02-A05含日期行
    events = []
    for aid in ("A02","A03","A04","A05"):
        for ev in date_lines(seg[aid]):
            events.append({**ev, "anchor_ids": [aid]})
    events.sort(key=lambda e: e["date"])
    # 无日期事实的节：以首条实质内容行入"未系日期里程碑"（不造日期，保证九锚全被视图使用）
    dated_aids = {aid for e in events for aid in e["anchor_ids"]}
    milestones = []
    for aid in ("A02","A03","A04","A05"):
        if aid not in dated_aids:
            for s_ in section_summary(seg[aid]):
                milestones.append({"text": s_, "anchor_ids": [aid]})
    views["02-关键事件时间线"] = {"anchor_ids": VIEW_MAP["02-关键事件时间线"],
                                  "events": events[:14], "undated_milestones": milestones}
    # 03 要件证据矩阵：A06矩阵表 + A04款项行 + A07索引
    matrix = [{"cells": r[:5], "anchor_ids": ["A06"]} for r in table_rows(seg["A06"])][:10]
    amounts = [{"cells": r[:4], "anchor_ids": ["A04"]} for r in table_rows(seg["A04"])][:6]
    evid = [{"text": l.strip().lstrip("·- "), "anchor_ids": ["A07"]}
            for l in seg["A07"].splitlines()[1:] if l.strip() and not l.startswith("## ")][:4]
    views["03-要件证据矩阵"] = {"anchor_ids": VIEW_MAP["03-要件证据矩阵"],
                              "matrix": matrix, "amounts": amounts, "evidence_index": evid}
    # 04 阶段计划与风险：A08阶段表 + A09风险表（暂停/待核与法条未注入必须可见）
    stages = [{"cells": r[:3], "anchor_ids": ["A08"]} for r in table_rows(seg["A08"])][:8]
    risks = [{"cells": r[:4], "anchor_ids": ["A09"]} for r in table_rows(seg["A09"])][:12]
    if not any("法条" in "".join(r["cells"]) or "法源" in "".join(r["cells"]) for r in risks):
        risks.append({"cells": ["提示","待人工法律复核","全部法条引用未注入","人工终签"], "anchor_ids": ["A09"]})
    views["04-阶段计划与风险"] = {"anchor_ids": VIEW_MAP["04-阶段计划与风险"], "stages": stages, "risks": risks}
    return {"schema": "gaotao.t4.case-view-data.v1", "case_id": case_id,
            "anchors": anchors, "views": views,
            "boundary_note": "全部数据仅取自同案冻结07；待核/暂停口径原样保留；无新增事实或法律结论"}, None

def main():
    a = sys.argv[1:]
    def arg(n): return a[a.index(n)+1] if n in a else None
    root = Path(arg("--root") or ".").resolve()
    t3root = Path(arg("--t3-root") or "").resolve()
    if "--vis-enabled" not in a:
        return hold("VIS未启用（--vis-enabled缺失），拒绝生成任何视图")
    cp = root/"contract/T4-VIS-ACCEPTANCE-CONTRACT.json"
    if not cp.is_file() or fsha(cp) != CONTRACT_SHA: return hold("T4合同副本缺失或哈希失配")
    contract = json.loads(cp.read_text(encoding="utf-8"))
    # 前置：T3联合PASS须先于任何T4写入
    t3ar_p = t3root/"T3-AS-RUN.json"
    if not t3ar_p.is_file(): return hold("T3 AS-RUN缺失")
    t3ar = json.loads(t3ar_p.read_text(encoding="utf-8"))
    if t3ar.get("result") != "PASS" or t3ar.get("stage") != "T3":
        return hold("T3文本门未通过（result≠PASS）")
    if t3ar.get("text_gate_message_id") != contract["prerequisite"]["text_gate_message_id"]:
        return hold("T3文本门消息id不符")
    for c in contract["cases"]:
        fmd = t3root/c["frozen_content_dir"]/MD
        fdx = t3root/c["frozen_content_dir"]/DOCX
        if not fmd.is_file(): return hold(f"冻结07缺失:{c['run_id']}")
        if fmd.is_symlink() or fdx.is_symlink(): return hold("冻结07为symlink")
        if fsha(fmd) != c["frozen_md_sha256"]:
            return hold(f"冻结07与合同哈希不符（篡改或跨案输入）:{c['run_id']}")
        if fdx.is_file() and fsha(fdx) != c["frozen_docx_sha256"]:
            return hold(f"冻结DOCX与合同哈希不符:{c['run_id']}")
        text = fmd.read_text(encoding="utf-8")
        cv, err = build_case_views(text, c["case_id"])
        if err: return hold(f"{c['run_id']}锚提取失败:{err}")
        cv["input"] = {"frozen_md": str(fmd), "frozen_md_sha256": c["frozen_md_sha256"], "run_id": c["run_id"]}
        outd = root/c["output_dir"]; outd.mkdir(parents=True, exist_ok=True)
        (outd/"case-views.json").write_text(json.dumps(cv, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
        spec = {"schema": "gaotao.t4.case-view-spec.v1", "case_id": c["case_id"], "run_id": c["run_id"],
                "views": [{"name": v, "svg": f"{v}.svg", "png": f"{v}.png",
                           "width": 1600, "height": 900, "anchor_ids": VIEW_MAP[v]} for v in VIEW_MAP]}
        (outd/"view-spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
        print(f"BUILD[{c['run_id']}]: 9锚+4视图数据")
    return 0
if __name__ == "__main__": sys.exit(main())
