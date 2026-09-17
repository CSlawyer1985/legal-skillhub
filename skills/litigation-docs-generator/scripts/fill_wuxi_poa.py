# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
#!/usr/bin/env python3
"""无锡制式《案件当事人授权委托书》（附件1）填空。

以陆律师提供的无锡市公安局制式表原件为标准模板，仅填当事人/受托人信息，
版式、文字、下划线位置一字不动。委托人签名行与日期行**留白**（供当事人手签）。

用法：
  python3 fill_wuxi_poa.py <标准模板.docx> <输出.docx> --vars '<JSON>'

vars 字段：
  委托人类型        自然人 / 法人（默认 自然人）
  委托人姓名        自然人=姓名；法人=单位名称                      【必填】
  委托人证件号      自然人=公民身份号码；法人=统一社会信用代码（可空，留空则留手写位）
  法定代表人姓名    法人时填（可空）
  法定代表人证件号  法人时填（可空）
  律师姓名                                                          【必填】
  律师执业证号                                                      【必填】
  律所全称                                                          【必填】
  授权事项          如「张三与李四民间借贷纠纷」                    【必填】

示例：
  python3 fill_wuxi_poa.py assets/无锡-案件当事人授权委托书-附件1.docx \
    "out/05-4 案件当事人授权委托书（人口信息查询）.docx" \
    --vars '{"委托人类型":"自然人","委托人姓名":"张三","委托人证件号":"320200199001011234",
             "律师姓名":"张三","律师执业证号":"1XXXXXXXXXXXXXXX",
             "律所全称":"示例律师事务所","授权事项":"张三与李四民间借贷纠纷"}'
"""
import sys
import json
import argparse
from docx import Document

BLANK = "____________"   # 未提供的可选项保留原表手写位
BOX, CHECK = "□", "☑"


def _rewrite(paragraph, text):
    """整段重写为 text，保留首 run 的字体格式，清空其余 run。"""
    if not paragraph.runs:
        paragraph.add_run(text)
        return
    paragraph.runs[0].text = text
    for r in paragraph.runs[1:]:
        r.text = ""


def _find(doc, *keywords):
    """按关键词定位段落（全部命中才返回），防止模板行序变化后错填。"""
    for p in doc.paragraphs:
        t = p.text.replace("\u3000", " ")
        if all(k in t for k in keywords):
            return p
    return None


def fill(template, out, v):
    doc = Document(template)
    is_person = v.get("委托人类型", "自然人") != "法人"

    # --- 委托人分支：只勾选本类型，另一分支保留空框 ---
    if is_person:
        p = _find(doc, "自然人", "公民身份号码")
        if p is None:
            raise SystemExit("❌ 未找到自然人分支段落，模板可能已变更")
        _rewrite(p, f"{CHECK}自然人：（姓名，公民身份号码）："
                    f"{v['委托人姓名']}，{v.get('委托人证件号') or BLANK}；")
        p2 = _find(doc, "法人", "统一社会信用代码")
        if p2 is not None and p2.text.strip().startswith(CHECK):
            _rewrite(p2, p2.text.replace(CHECK + "法人", BOX + "法人", 1))
    else:
        p = _find(doc, "法人", "统一社会信用代码")
        if p is None:
            raise SystemExit("❌ 未找到法人分支段落，模板可能已变更")
        _rewrite(p, f"{CHECK}法人：（单位名称、统一社会信用代码，法人代表姓名、公民身份号码）："
                    f"{v['委托人姓名']}，{v.get('委托人证件号') or BLANK}，"
                    f"法定代表人{v.get('法定代表人姓名') or BLANK}，"
                    f"{v.get('法定代表人证件号') or BLANK}；")
        p2 = _find(doc, "自然人", "公民身份号码")
        if p2 is not None and p2.text.strip().startswith(CHECK):
            _rewrite(p2, p2.text.replace(CHECK + "自然人", BOX + "自然人", 1))

    # --- 受托人：勾「律师」、填姓名/执业证号/律所名称 ---
    p = _find(doc, "姓名：", "执业证")
    if p is None:
        raise SystemExit("❌ 未找到受托人段落，模板可能已变更")
    _rewrite(p, f"姓名：{v['律师姓名']}，{CHECK}律师、{BOX}基层法律服务工作者执业证书编号："
                f"{v['律师执业证号']}，律师事务所、基层法律服务所名称{v['律所全称']}。")

    # --- 授权委托事项 ---
    p = _find(doc, "本人同意授权由受托人代理")
    if p is None:
        raise SystemExit("❌ 未找到授权委托事项段落，模板可能已变更")
    _rewrite(p, f"本人同意授权由受托人代理{v['授权事项']}诉讼案件（仲裁事务）。")

    # --- 委托人签名行、日期行：保持留白，不动 ---
    doc.save(out)

    # --- 自检 ---
    errs = self_check(out, v, is_person)
    if errs:
        import os
        os.remove(out)
        raise SystemExit("❌ self_check 未通过，已放弃生成：\n  - " + "\n  - ".join(errs))
    print(f"✅ self_check 通过：委托人/受托人/授权事项已填，签名与日期行留白")
    print(f"✅ {out}")


def self_check(path, v, is_person):
    errs = []
    d2 = Document(path)
    full = "\n".join(p.text for p in d2.paragraphs)

    # 1) 必填值全部落盘
    for key in ("委托人姓名", "律师姓名", "律师执业证号", "律所全称", "授权事项"):
        if v[key] not in full:
            errs.append(f"字段未写入：{key}={v[key]}")
    # 2) 勾选状态正确（本类型勾选、另一类型留空框）
    want, other = ("自然人", "法人") if is_person else ("法人", "自然人")
    if CHECK + want not in full:
        errs.append(f"应勾选未勾选：{want}")
    if CHECK + other in full:
        errs.append(f"误勾选了非本类型分支：{other}")
    # 3) 签名行、日期行不得被填
    if "委托人（签名捺印/盖章）" not in full:
        errs.append("签名行文字被破坏")
    # 4) 未提供的可选项应保留手写位
    if not v.get("委托人证件号") and is_person and BLANK not in full:
        errs.append("未提供证件号时未保留手写位")
    return errs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("out")
    ap.add_argument("--vars", required=True)
    a = ap.parse_args()
    fill(a.template, a.out, json.loads(a.vars))
