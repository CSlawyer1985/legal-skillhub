# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
#!/usr/bin/env python3
"""委托代理合同填空 — 以本所已签《委托代理合同》为标准模板存档，
仅替换当事人信息与律所专属占位符，条款与格式一字不动。用法：
  python3 fill_retainer_deheng.py <标准模板.docx> <输出.docx> --vars <JSON>

模板中 {{〔…〕}} 形式的律所专属占位符（本所收款账号 / 律所联系人 / 律所联系电话 /
承办律师姓名）从 private/lawyer-profile.json 回填，也可用 --vars 同名键覆盖。
"""
import sys, json, argparse
from pathlib import Path
from docx import Document

# 发布物中律所专属值零残留：模板里是「〔…〕」占位符，真实值来自 private/（不进发布副本）或 --vars
PROFILE = Path(__file__).resolve().parent.parent / "private" / "lawyer-profile.json"

# 模板占位符 → private/lawyer-profile.json 的字段名
PLACEHOLDERS = {
    "〔本所收款账号〕": "律所银行账号",
    "〔律所联系人〕": "律所联系人",
    "〔律所联系电话〕": "律所联系电话",
    "〔承办律师姓名〕": "查询人姓名",
}


def load_profile():
    if PROFILE.exists():
        try:
            return json.loads(PROFILE.read_text(encoding="utf-8"))
        except Exception as e:
            raise SystemExit(f"❌ 私有配置解析失败：{PROFILE}：{e}")
    return {}


def fill(template, out, vars_):
    doc = Document(template)

    # 0) 律所专属占位符回填（--vars 优先，其次 private/lawyer-profile.json）
    profile = load_profile()
    leftover = []
    for p in doc.paragraphs:
        for r in p.runs:
            for ph, key in PLACEHOLDERS.items():
                if ph in r.text:
                    val = vars_.get(key) or profile.get(key)
                    if val:
                        r.text = r.text.replace(ph, val)
                    elif ph not in leftover:
                        leftover.append(ph)
    if leftover:
        print(f"⚠️ 未提供值，合同仍留占位符 {'、'.join(leftover)}"
              f"——请用 --vars 传入或在 private/lawyer-profile.json 配置")

    # 0) 收费条款覆盖（可选，按案件协商收费时使用）
    #    vars 可选键：基础代理费数字（如 "5000"）、基础代理费大写（如 "伍仟"）、
    #    删除风险代理费条款（true 时整段删除 "2、风险代理费…"）
    fee_num = vars_.get("基础代理费数字")
    fee_cap = vars_.get("基础代理费大写")
    if fee_num or fee_cap:
        for p in doc.paragraphs:
            if p.text.strip().startswith("1、基础代理费"):
                for r in p.runs:
                    if fee_num:
                        r.text = r.text.replace("7000", fee_num)
                    if fee_cap:
                        r.text = r.text.replace("柒仟", fee_cap)
    if vars_.get("删除风险代理费条款"):
        for p in list(doc.paragraphs):
            if p.text.strip().startswith("2、风险代理费"):
                p._element.getparent().remove(p._element)

    # 1) 全局 run 级替换（替换模板占位符，完整长词，安全）
    global_rep = {
        "〔甲方名称〕": vars_["甲方名称"],
        "〔对方案由〕": vars_["对方案由"],
    }
    for p in doc.paragraphs:
        for r in p.runs:
            for old, new in global_rep.items():
                if old in r.text:
                    r.text = r.text.replace(old, new)

    # 2) 甲方邮寄地址：只改第一处（第二处是乙方/律所地址），整段重写保留首 run 格式
    done_addr = False
    for p in doc.paragraphs:
        if done_addr:
            break
        t = p.text.strip()
        if t.startswith("邮寄地址"):
            first = p.runs[0]
            for r in p.runs[1:]:
                r.text = ""
            first.text = "邮寄地址：" + vars_["甲方地址"]
            done_addr = True

    # 3) 甲方联系人及电话：只改第一处（第二处是乙方/律所联系方式），整段重写保留首 run 格式
    firm_contact = profile.get("律所联系人") or ""
    done_contact = False
    for p in doc.paragraphs:
        if done_contact:
            break
        t = p.text.strip()
        if not t.startswith("联系人及电话"):
            continue
        if "〔律所联系人〕" in t or (firm_contact and firm_contact in t):
            continue                      # 这是乙方（律所）那处，不动
        first = p.runs[0]
        for r in p.runs[1:]:
            r.text = ""
        first.text = ("联系人及电话：" + vars_["甲方联系人"]
                      + "  联系电话：" + vars_["甲方联系电话"])
        done_contact = True

    doc.save(out)
    print(f"✅ {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("out")
    ap.add_argument("--vars", required=True)
    a = ap.parse_args()
    fill(a.template, a.out, json.loads(a.vars))
