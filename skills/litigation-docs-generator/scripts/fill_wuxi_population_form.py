# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
#!/usr/bin/env python3
"""无锡制式《律师、基层法律服务工作者因代理诉讼、仲裁查询人口信息业务申请表》（附件2）填空。

以陆律师提供的无锡市公安局制式表原件为标准模板，仅填查询人（律师）信息、介绍信编号、
被查询人信息（最多 5 行，未用满时在首个空白行「姓名」栏写「以下为空」，符合表末注记），
表格版式、勾选项、承诺条款一字不动。律师签字行与日期行、查询结果接收行**留白**供手签。

用法：
  python3 fill_wuxi_population_form.py <标准模板.docx> <输出.docx> --vars '<JSON>'

vars 字段：
  查询人姓名 / 公民身份号码 / 联系电话 / 执业证号   可省略——省略时读 private/lawyer-profile.json
                                                    （模板本身只有「〔…〕」占位符，不含任何真实个人信息）
  介绍信编号        选填，与所函/律所介绍信文号一致
  查询事由          默认「诉讼」
  被查询人          [{"姓名":"李四","性别":"男","出生日期":"1990.1.1",
                     "公民身份号码":"","其他查询要素":""}, …]   最多 5 条
                    缺身份证号时该栏留空（这正是调取人口信息的场景）

示例：
  python3 fill_wuxi_population_form.py assets/无锡-查询人口信息业务申请表-附件2.docx \
    "out/附件2 查询人口信息业务申请表.docx" \
    --vars '{"介绍信编号":"德恒（无锡）民（2026）字第12号",
             "被查询人":[{"姓名":"李四","性别":"男","出生日期":"1990.1.1"}]}'
"""
import os
import json
import argparse
from pathlib import Path
from docx import Document

MAX_ROWS = 5          # 模板中被查询人信息共 5 个数据行（R4–R8）
MARK = "以下为空"
DATA_ROW0 = 4         # 数据行起始行号
COLS = {              # 数据行列位：姓名 / 性别 / 出生日期 / 公民身份号码 / 其他查询要素
    "姓名": 1, "性别": 2, "出生日期": 3, "公民身份号码": 4, "其他查询要素": 7,
}
QUERY_COLS = {        # 查询人（律师）信息列位
    "姓名": (0, 2), "公民身份号码": (0, 6),
    "联系电话": (1, 2), "执业证号": (1, 6),
}
# 发布物中个人信息为零：模板里只有占位符，真实值来自 private/（不进发布副本）或 --vars
PROFILE = Path(__file__).resolve().parent.parent / "private" / "lawyer-profile.json"
PLACEHOLDER = "〔"


def load_profile():
    """读取本机私有配置（private/lawyer-profile.json）。不存在则返回空 dict。"""
    if PROFILE.exists():
        try:
            return json.loads(PROFILE.read_text(encoding="utf-8"))
        except Exception as e:
            raise SystemExit(f"❌ 私有配置解析失败：{PROFILE}：{e}")
    return {}


def _set_cell(cell, text):
    """改写单元格文本，保留首个 run 的字体格式。"""
    p = cell.paragraphs[0]
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(text)


def fill(template, out, v):
    doc = Document(template)
    if len(doc.tables) < 1:
        raise SystemExit("❌ 模板中未找到表格")
    t = doc.tables[0]
    people = v.get("被查询人") or []
    if not people:
        raise SystemExit("❌ 未提供被查询人（vars.被查询人 为空）")
    if len(people) > MAX_ROWS:
        raise SystemExit(f"❌ 被查询人 {len(people)} 名，超出模板 {MAX_ROWS} 行上限，"
                         f"请分表填写或联系公安换表")

    # 1) 查询人（律师）信息——优先级：--vars > private/lawyer-profile.json > 模板现值
    profile = load_profile()
    profile_key = {"姓名": "查询人姓名", "公民身份号码": "查询人公民身份号码",
                   "联系电话": "查询人联系电话", "执业证号": "律师执业证号"}
    for key, (r, c) in QUERY_COLS.items():
        val = v.get(key) or profile.get(profile_key[key])
        if val:
            _set_cell(t.cell(r, c), val)
    # 2) 查询事由（默认沿用模板「诉讼」）
    if v.get("查询事由"):
        _set_cell(t.cell(2, 2), v["查询事由"])
    # 3) 介绍信（公函）编号——追加到表头上方段落末尾，保留原格式
    if v.get("介绍信编号"):
        for p in doc.paragraphs:
            if "介绍信（公函）编号" in p.text and p.runs:
                p.runs[-1].text = p.runs[-1].text.rstrip() + v["介绍信编号"]
                break

    # 4) 被查询人信息：逐行填写，其余行清空，首个空行标「以下为空」
    for i in range(MAX_ROWS):
        r = DATA_ROW0 + i
        if i < len(people):
            person = people[i]
            for key, col in COLS.items():
                _set_cell(t.cell(r, col), person.get(key) or "")
        else:
            for col in COLS.values():
                _set_cell(t.cell(r, col), MARK if col == COLS["姓名"] and i == len(people) else "")
        # 末行若恰好填满，则需要额外的空行标「以下为空」——模板无空行时提示
    if len(people) == MAX_ROWS:
        print("⚠️ 被查询人占满全部 5 行，模板已无空白行可标「以下为空」，请留意公安窗口要求")

    doc.save(out)

    n = len(people)
    errs = self_check(out, v, n)
    if errs:
        os.remove(out)
        raise SystemExit("❌ self_check 未通过，已放弃生成：\n  - " + "\n  - ".join(errs))
    tail = (f"「{MARK}」标记就位" if n < MAX_ROWS
            else "已占满全部行（无空行可标「以下为空」，请留意公安窗口要求）")
    print(f"✅ self_check 通过：查询人信息 + {n} 名被查询人 + {tail}")
    print(f"✅ {out}")


def self_check(path, v, n):
    errs = []
    t = Document(path).tables[0]

    # 1) 被查询人逐格核对，且不得残留模板旧案数据
    allowed = set()
    for person in v["被查询人"]:
        allowed |= {x for x in person.values() if x}
    allowed |= {MARK, ""}
    for i in range(MAX_ROWS):
        r = DATA_ROW0 + i
        for key, col in COLS.items():
            got = t.cell(r, col).text.strip()
            if got not in allowed:
                errs.append(f"第 {r} 行「{key}」栏出现非本案数据：{got!r}（旧案残留？）")

    # 2) 被查询人逐行比对（顺序 + 内容）
    for i, person in enumerate(v["被查询人"]):
        r = DATA_ROW0 + i
        for key, col in COLS.items():
            want = (person.get(key) or "").strip()
            got = t.cell(r, col).text.strip()
            if got != want:
                errs.append(f"第 {i + 1} 名被查询人「{key}」不一致：实际 {got!r} vs 预期 {want!r}")

    # 3) 「以下为空」标记位置正确（紧随最后一个被查询人的首个空行）
    if n < MAX_ROWS:
        got = t.cell(DATA_ROW0 + n, COLS["姓名"]).text.strip()
        if got != MARK:
            errs.append(f"首个空行「姓名」栏应为「{MARK}」，实际 {got!r}")

    # 4) 查询人信息不得为空、也不得残留占位符（姓名 / 联系电话 / 执业证号）
    for key in ("姓名", "联系电话", "执业证号"):
        r, c = QUERY_COLS[key]
        got = t.cell(r, c).text.strip()
        if not got:
            errs.append(f"查询人「{key}」栏为空")
        elif PLACEHOLDER in got:
            errs.append(f"查询人「{key}」栏仍是占位符 {got!r}——"
                        f"请用 --vars 传入，或在 private/lawyer-profile.json 配置")

    # 5) 被查询人栏不得残留占位符
    for i in range(MAX_ROWS):
        for col in COLS.values():
            got = t.cell(DATA_ROW0 + i, col).text.strip()
            if PLACEHOLDER in got:
                errs.append(f"被查询人第 {DATA_ROW0 + i} 行残留占位符 {got!r}")

    # 6) 律师签字行、查询结果接收行须保留
    full = "\n".join("".join(c.text for c in row.cells) for row in t.rows)
    for kw in ("申请律师", "保密义务承诺", "本申请事项的查询结果已于"):
        if kw not in full:
            errs.append(f"承诺/接收行文字被破坏：{kw}")
    return errs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("out")
    ap.add_argument("--vars", required=True)
    a = ap.parse_args()
    fill(a.template, a.out, json.loads(a.vars))
