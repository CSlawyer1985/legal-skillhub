#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTHOR: WorkBuddy (agent_created)
"""对比「上游原版分词器」与「现行版本」的修订标记质量，证明本地补丁只改善不劣化。

什么时候要跑：
  1) 改了 `vendor/` 里的任何代码之后（改完必跑，别凭印象说"应该没问题"）
  2) 上游发新版、准备替换 vendor 之前——先看新版的标记质量是否反而更差
  3) 怀疑「修订版里冒出了没动过的字」时，用它定位是不是分词边界问题

判据三条，缺一不可（任一条不过即退出码 1）：
  ① 现行版 ins/del 标记数 **不增加**（增加了说明 diff 变碎）
  ② `mod_fallback` **不增加**（增加说明整段回退变多，是变差）
  ③ `verify_tracked.py` 七项仍全 PASS（accept-all == NEW、reject-all == OLD）
另外会打印关键用例的**标记内容逐字**，供人工确认"删的正好是该删的那几个字"。

用法:
  python3 regress_trackdiff.py                    # 用默认工作目录 /tmp
  python3 regress_trackdiff.py --workdir /tmp/x
  python3 regress_trackdiff.py --upstream /path/to/upstream/compare_docx_tracked.py

背景（本地补丁 1）：上游 `TOK_RE = r'\\s+|\\w+|[^\\w\\s]+'` 末尾的 `+` 会把连续标点
粘成一个不可分 token，导致中文文书里「），」→「）。」这类相邻标点变化被误报为
"删一块 + 插一块"，把两版里都在同一位置的括号、句号标成修订。详见 UPSTREAM.md。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)          # 脚本在 scripts/ 下，vendor 在上一级
VENDOR = os.path.join(SKILL_ROOT, "vendor")
CUR = os.path.join(VENDOR, "compare_docx_tracked.py")
ORIG = os.path.join(VENDOR, "compare_docx_tracked_upstream.py")
VERIFY = os.path.join(VENDOR, "verify_tracked.py")

CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
DOCRELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""
SETTINGS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>"""


def make_docx(path, paras):
    """造最小可用 docx。每段一个 run（run 内不再拆），模拟真实排版。"""
    body = "".join(
        '<w:p><w:r><w:rPr><w:rFonts w:ascii="宋体" w:eastAsia="宋体"/></w:rPr>'
        '<w:t xml:space="preserve">%s</w:t></w:r></w:p>' % t for t in paras
    )
    doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>%s<w:sectPr/></w:body></w:document>" % body
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CT)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/document.xml", doc)
        z.writestr("word/settings.xml", SETTINGS)
        z.writestr("word/_rels/document.xml.rels", DOCRELS)   # 上游必读，缺了 KeyError


def marks(p):
    if not os.path.exists(p):
        return -1, -1        # -1 = 没产出，判据会抓成异常而不是当成 0
    xml = zipfile.ZipFile(p).read("word/document.xml").decode("utf-8")
    return xml.count("<w:ins "), xml.count("<w:del ")


def revision_text(p):
    from xml.etree import ElementTree as ET

    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    root = ET.fromstring(zipfile.ZipFile(p).read("word/document.xml").decode("utf-8"))
    ins, dels = [], []
    for node in root.iter():
        tag = node.tag.split("}")[1]
        if tag == "ins":
            ins.append("".join((t.text or "") for t in node.iter(W + "t")))
        elif tag == "del":
            dels.append("".join((t.text or "") for t in node.iter(W + "delText")))
    return ins, dels


# 场景取材于真实文书：A/G 是实际遇到过的"标点相邻"与"句内整串删除"
CASES = [
    ("A. 标点相邻·逗号变句号",
     ["货款（计100万元），如发生争议甲方应予以返还。如乙方逾期支付。"],
     ["货款（计100万元）。如乙方逾期支付。"]),
    ("B. 纯插入", ["甲方签字。"], ["甲方签字并按手印。"]),
    ("C. 数字改动", ["合同价款总额为100万元整。"], ["合同价款总额为150万元整。"]),
    ("D. 句首标点变化", ["已完成。如果乙方违约，甲方有权解约。"], ["已完成，如果乙方违约，甲方有权解约。"]),
    ("E. 百分比与英文混排", ["乙方持有30%股权（ABC Ltd.）。"], ["乙方持有35%股权（ABC Ltd.）。"]),
    ("F. 连续标点", ["款项已付清！！"], ["款项已付清！"]),
    ("G. 句内整串删除",
     ["即四成货款（计100万元），如发生争议甲方应予以返还货款及定金，并赔偿违约金5万元。如乙方逾期支付。"],
     ["即四成货款（计100万元）。如乙方逾期支付。"]),
    ("H. 整段删除", ["第一段。", "第二段应当删除。", "第三段。"], ["第一段。", "第三段。"]),
    ("I. 标点全角半角互换", ["甲方：张三（签字）"], ["甲方:张三(签字)"]),
]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser(description="上游原版 vs 现行版本：修订标记质量回归")
    ap.add_argument("--workdir", default="/tmp/trackdiff_regress", help="临时工作目录")
    ap.add_argument("--upstream", default=ORIG, help="上游原版脚本路径（默认取 vendor/compare_docx_tracked_upstream.py）")
    args = ap.parse_args()

    if not os.path.exists(args.upstream):
        sys.exit("找不到上游原版：%s\n若已丢失，请从 https://github.com/stephenlzc/docx-trackdiff "
                 "取 scripts/compare_docx_tracked.py" % args.upstream)
    if not os.path.exists(CUR):
        sys.exit("找不到现行版本：%s" % CUR)

    work = args.workdir
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    shutil.copy(args.upstream, os.path.join(work, "comparer_orig.py"))
    shutil.copy(CUR, os.path.join(work, "comparer_punct.py"))
    shutil.copy(VERIFY, os.path.join(work, "verify.py"))
    os.chdir(work)

    def tok(path, name):
        src = open(path, encoding="utf-8").read()
        m = re.search(r"TOK_RE = re\.compile\(r'(.*)'\)", src)
        return "%s %s" % (name, m.group(1) if m else "(未找到)")

    print("=" * 94)
    print("回归：上游原版 vs 现行版本")
    print("  " + tok(args.upstream, "原版 "))
    print("  " + tok(CUR, "现行 "))
    print("=" * 94)
    print("%-26s %-18s %-18s %s" % ("用例", "原版 ins/del/fb", "现行 ins/del/fb", "结论"))
    print("-" * 94)

    fails = []
    for name, old_paras, new_paras in CASES:
        make_docx("o.docx", old_paras)
        make_docx("n.docx", new_paras)
        row = {}
        for tag, script in (("orig", "comparer_orig.py"), ("cur", "comparer_punct.py")):
            out = "out_%s.docx" % tag
            if os.path.exists(out):
                os.remove(out)
            r = run([sys.executable, script, "o.docx", "n.docx", out,
                     "--author", "回归测试", "--date", "2026-09-16T00:00:00Z"])
            m = re.search(r"'mod_fallback':\s*(\d+)", r.stdout)
            fb = int(m.group(1)) if m else -1
            i, d = marks(out)
            v = run([sys.executable, "verify.py", out, "o.docx", "n.docx"])
            row[tag] = dict(ins=i, dele=d, fb=fb, verify=(v.returncode == 0))
        o, n = row["orig"], row["cur"]
        ok = (n["ins"] >= 0 and o["ins"] >= 0
              and n["ins"] <= o["ins"] and n["dele"] <= o["dele"]
              and n["fb"] <= o["fb"] and n["verify"])
        if not ok:
            fails.append(name)
        print("%-26s %-18s %-18s %s"
              % (name, "%d / %d / %d" % (o["ins"], o["dele"], o["fb"]),
                 "%d / %d / %d" % (n["ins"], n["dele"], n["fb"]),
                 "✅ 不劣" if ok else "❌ 变差"))

    print("-" * 94)
    print("\n【标记内容逐字对比（关键用例）】")
    for name in (CASES[0][0], CASES[6][0]):
        cand = [c for c in CASES if c[0] == name][0]
        print("\n### " + name)
        for tag, label, script in (("orig", "原版", "comparer_orig.py"),
                                   ("cur", "现行", "comparer_punct.py")):
            make_docx("o.docx", cand[1])
            make_docx("n.docx", cand[2])
            out = "cmp_%s.docx" % tag
            if os.path.exists(out):
                os.remove(out)
            run([sys.executable, script, "o.docx", "n.docx", out,
                 "--author", "回归测试", "--date", "2026-09-16T00:00:00Z"])
            ins, dels = revision_text(out)
            print("   %s：" % label)
            for x in ins:
                print("      <ins> %r" % x)
            for x in dels:
                print("      <del> %r" % x)
            if not ins and not dels:
                print("      （无标记）")

    print("\n" + "=" * 94)
    if fails:
        print("❌ 有 %d 个用例变差：%s" % (len(fails), fails))
        return 1
    print("✅ 全部 %d 个用例：标记数不增加、fallback 不增加、verify 全 PASS" % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
