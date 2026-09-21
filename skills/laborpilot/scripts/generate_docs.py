#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文书生成器 v3：生成并校验 JLS 版式的律师复核初稿或最终提交版。

参考模板：assets/template-仲裁申请书.docx / template-证据清单.docx。
Pandoc 完成内容转换后，由标准库 OOXML 修正器确定性应用并校验 JLS 版式。

用法：python3 generate_docs.py --case case.json --output 案件根目录 --types 仲裁申请书 --strict
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from zipfile import BadZipFile

from docx_style import PROFILE_ID, apply_jls_style, validate_jls_docx

SKILL_DIR = Path(__file__).parent.parent
ASSETS = SKILL_DIR / "assets"
DELIVERY_DIRS = {
    "lawyer_review_draft": "01_律师复核初稿",
    "final_submission": "02_最终提交版",
}
DELIVERY_LABELS = {
    "lawyer_review_draft": "律师复核初稿",
    "final_submission": "最终提交版",
}
DOC_PREFIXES = {"仲裁申请书": "02", "证据清单": "03", "行动清单": "04"}
DOC_DISPLAY_NAMES = {"仲裁申请书": "劳动仲裁申请书", "证据清单": "证据目录", "行动清单": "待补材料与行动清单"}

# 中文数字日期
CN_NUM = {"0":"〇","1":"一","2":"二","3":"三","4":"四","5":"五","6":"六","7":"七","8":"八","9":"九"}

def cn_date(d=None):
    """2026-08-21 → 二〇二六年八月二十一日"""
    if d is None:
        d = date.today()
    y = "".join(CN_NUM[c] for c in str(d.year))
    m = d.month
    if m < 10:
        mon = CN_NUM[str(m)]
    elif m == 10:
        mon = "十"
    else:
        mon = "十" + CN_NUM[str(m % 10)]
    day = d.day
    if day < 10:
        dd = CN_NUM[str(day)]
    elif day == 10:
        dd = "十"
    elif day < 20:
        dd = "十" + CN_NUM[str(day % 10)]
    elif day == 20:
        dd = "二十"
    elif day < 30:
        dd = "二十" + CN_NUM[str(day % 10)]
    elif day == 30:
        dd = "三十"
    else:
        dd = "三十" + CN_NUM[str(day % 10)]
    return f"{y}年{mon}月{dd}日"


def compact_prose(value):
    """把事实与理由整理为连续正文，不保留 Markdown 分点。"""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def table_cell(value):
    """转义 Markdown 表格中的控制字符。"""
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def output_stem(doc_type, delivery_status, version):
    label = DELIVERY_LABELS[delivery_status]
    if doc_type == "行动清单":
        label = "律师复核稿"
    return f"{DOC_PREFIXES[doc_type]}_{DOC_DISPLAY_NAMES[doc_type]}_{label}_v{version}"


PANDOC_MISSING = (
    "未找到 Pandoc，无法生成 .docx。请先安装：https://pandoc.org\n"
    "macOS: brew install pandoc\n"
    "Debian/Ubuntu: apt install pandoc"
)


def md_to_docx(md_file: Path, docx_file: Path, ref_doc: Path = None):
    """pandoc md→docx,可指定参考样式文档。"""
    cmd = ["pandoc", str(md_file), "-o", str(docx_file),
           "--from=markdown", "--to=docx", "-V", "lang=zh-CN"]
    if ref_doc and ref_doc.exists():
        cmd.extend(["--reference-doc", str(ref_doc)])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return False, PANDOC_MISSING
    return r.returncode == 0, r.stderr


def generate_arbitration(case, claims):
    """仲裁申请书——严格按律师定稿格式。"""
    lines = []
    # 标题
    lines.append("劳动仲裁申请书")
    lines.append("")
    # 当事人信息仅保留文书必要要素；示例和模板不要求身份证号、个人住址。
    lines.append(f"申请人：{case.get('申请人','【申请人姓名】')}，{case.get('性别','【性别】')}，"
                f"{case.get('出生年月','【年月日】')}出生，{case.get('民族','汉族')}。"
                f"联系电话：{case.get('电话','【电话】')}。")
    lines.append("")
    lines.append(f"被申请人：{case.get('被申请人','【公司名称】')}，"
                f"住所地：{case.get('被申请人地址','【注册地址】')}。"
                + (f"统一社会信用代码：{case.get('统一社会信用代码')}。" if case.get('统一社会信用代码') else ""))
    lines.append("")
    # 仲裁请求(律师格式:一、二、三中文编号)
    cn = ["一","二","三","四","五","六","七","八","九","十",
          "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十"]
    lines.append("仲裁请求：")
    lines.append("")
    for i, c in enumerate(claims):
        if c.get("金额"):
            item = f"请求裁决被申请人支付申请人{c['事项']}{c['金额']:,.2f}元"
            if c.get("计算式"):
                item += f"（{c['计算式']}）"
            item += "；"
        else:
            item = f"请求裁决被申请人{c['事项']}；"
        num = cn[i] if i < len(cn) else str(i + 1)
        lines.append(f"{num}、{item}")
    lines.append("")
    # 事实与理由(律师格式:段落体,不用markdown标题)
    lines.append("事实与理由：")
    lines.append("")
    lines.append(compact_prose(case.get("事实与理由", case.get("事实概要", "【按时间轴组织，不添加未确认事实】"))))
    lines.append("")
    # 落款(律师格式:中文数字日期)
    lines.append("此致")
    lines.append("")
    lines.append(f"{case.get('仲裁委','【劳动人事争议仲裁委员会】')}")
    lines.append("")
    lines.append(f"申请人：{case.get('申请人','【申请人签名】')}")
    lines.append("")
    lines.append(cn_date())
    return "\n".join(lines)


def generate_evidence_list(case, evidence_items):
    """证据清单——严格按律师定稿格式。"""
    lines = []
    # 标题(含案件信息)
    applicant = case.get("申请人", "【申请人】")
    respondent = case.get("被申请人", "【被申请人】")
    cause = case.get("案由", "【案由】")
    lines.append(f"{applicant}与{respondent}{cause}一案")
    lines.append("")
    lines.append("证据目录")
    lines.append("")
    # 表格(律师格式:5列,不用争点卡列)
    lines.append("| 序号 | 证据名称 | 来源 | 页码 | 证明目的 |")
    lines.append("|---:|---|---|---|---|")
    for i, e in enumerate(evidence_items, 1):
        lines.append(f"| {i} | {table_cell(e.get('名称'))} | {table_cell(e.get('来源'))} | "
                    f"{table_cell(e.get('页码'))} | {table_cell(e.get('证明目的'))} |")
    lines.append("")
    # 落款
    lines.append(f"提交人：{case.get('申请人','【申请人签名】')}")
    lines.append("")
    lines.append(f"提交时间：{cn_date()}")
    return "\n".join(lines)


def generate_action_list(case, actions):
    """行动清单——律师内部工作文件。"""
    lines = []
    lines.append("待补材料与行动清单")
    lines.append("")
    lines.append("一、需向当事人核实的事实")
    lines.append("")
    lines.append("| 优先级 | 问题 | 影响的请求 | 状态 |")
    lines.append("|---|---|---|---|")
    for a in actions.get("核实", []):
        lines.append(f"| {table_cell(a.get('优先级'))} | {table_cell(a.get('问题'))} | {table_cell(a.get('影响'))} | 待核实 |")
    lines.append("")
    lines.append("二、待补证据")
    lines.append("")
    lines.append("| 优先级 | 材料 | 持有人 | 证明目的 | 状态 |")
    lines.append("|---|---|---|---|---|")
    for a in actions.get("证据", []):
        lines.append(f"| {table_cell(a.get('优先级'))} | {table_cell(a.get('材料'))} | {table_cell(a.get('持有人'))} | {table_cell(a.get('证明目的'))} | 待收集 |")
    lines.append("")
    lines.append("三、金额与程序核对")
    lines.append("")
    lines.append("| 事项 | 当前口径 | 风险／后果 | 状态 |")
    lines.append("|---|---|---|---|")
    for a in actions.get("核对", []):
        lines.append(f"| {table_cell(a.get('事项'))} | {table_cell(a.get('口径'))} | {table_cell(a.get('风险'))} | 待核对 |")
    lines.append("")
    return "\n".join(lines)


# 文档类型 → 生成函数 + 参考样式
DOC_REGISTRY = {}

def _register():
    ref_arb = ASSETS / "template-仲裁申请书.docx"
    ref_evd = ASSETS / "template-证据清单.docx"
    DOC_REGISTRY["仲裁申请书"] = (generate_arbitration, ref_arb)
    DOC_REGISTRY["证据清单"] = (generate_evidence_list, ref_evd)
    DOC_REGISTRY["行动清单"] = (generate_action_list, None)

_register()


def main():
    ap = argparse.ArgumentParser(description="文书生成器 v3（JLS 版式及交付分层）")
    ap.add_argument("--case", required=True, help="案件数据JSON")
    ap.add_argument("--output", required=True, help="案件根目录；DOCX 将按交付层级进入独立子目录")
    ap.add_argument("--work-dir", help="内部 Markdown 工作目录；默认 <案件根目录>/.casework/drafting")
    ap.add_argument("--types", required=True, help="用户明确要求的文书类型，逗号分隔")
    ap.add_argument("--delivery-status", choices=sorted(DELIVERY_DIRS), default="lawyer_review_draft")
    ap.add_argument("--version", type=int, default=1, help="输出文件版本号，默认 1")
    ap.add_argument("--approved-by", help="最终提交版必须记录作出提交决定的律师姓名")
    ap.add_argument("--strict", action="store_true", help="兼容参数；正式 DOCX 始终按严格模式生成")
    args = ap.parse_args()

    if args.version < 1:
        ap.error("--version 必须为正整数。")
    if args.delivery_status == "final_submission" and not (args.approved_by or "").strip():
        ap.error("最终提交版必须通过 --approved-by 记录律师提交决定。")

    data = json.loads(Path(args.case).read_text(encoding="utf-8"))
    case = data.get("case", {})
    claims = data.get("claims", [])
    evidence = data.get("evidence", [])
    actions = data.get("actions", {})

    case_root = Path(args.output)
    out_dir = case_root / DELIVERY_DIRS[args.delivery_status]
    work_dir = Path(args.work_dir) if args.work_dir else case_root / ".casework" / "drafting"
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    if not types:
        ap.error("--types 至少指定一种文书。")
    unknown = sorted(set(types) - set(DOC_REGISTRY))
    if unknown:
        ap.error("不支持的文书类型：" + "、".join(unknown))
    if args.delivery_status == "final_submission" and "行动清单" in types:
        ap.error("行动清单属于内部工作文件，不得生成最终提交版。")

    planned = []
    for doc_type in types:
        stem = output_stem(doc_type, args.delivery_status, args.version)
        planned.extend([work_dir / f"{stem}.md", work_dir / f"{stem}_版式验证.json", out_dir / f"{stem}.docx"])
    existing = [path for path in planned if path.exists()]
    if existing:
        ap.error("为避免覆盖既有版本，以下目标已存在：\n" + "\n".join(str(path) for path in existing))
    if shutil.which("pandoc") is None:
        print(PANDOC_MISSING, file=sys.stderr)
        raise SystemExit(1)
    failures = []

    for doc_type in types:
        gen_fn, ref_doc = DOC_REGISTRY[doc_type]

        if doc_type == "仲裁申请书":
            md_content = gen_fn(case, claims)
        elif doc_type == "证据清单":
            md_content = gen_fn(case, evidence)
        elif doc_type == "行动清单":
            md_content = gen_fn(case, actions)
        else:
            continue

        stem = output_stem(doc_type, args.delivery_status, args.version)
        md_file = work_dir / f"{stem}.md"
        report_file = work_dir / f"{stem}_版式验证.json"
        docx_file = out_dir / f"{stem}.docx"
        md_file.write_text(md_content, encoding="utf-8")
        ok, err = md_to_docx(md_file, docx_file, ref_doc)
        if ok:
            try:
                apply_jls_style(docx_file, doc_type, args.delivery_status)
                findings = validate_jls_docx(docx_file, doc_type, args.delivery_status)
                report = {
                    "status": "pass" if not findings else "blocked",
                    "profile": PROFILE_ID,
                    "document_type": doc_type,
                    "delivery_status": args.delivery_status,
                    "approved_by": (args.approved_by or "").strip() or None,
                    "document_path": str(docx_file.resolve()),
                    "findings": findings,
                }
                report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                if findings:
                    raise ValueError("\n".join(findings))
            except (OSError, ValueError, BadZipFile) as exc:
                ok, err = False, str(exc)
        if ok:
            print(f"  OK {doc_type} ({docx_file.stat().st_size}B) → {docx_file}")
        else:
            failures.append(f"{doc_type}: {err.strip() or 'Pandoc 转换失败'}")
            if docx_file.exists():
                docx_file.unlink()

    if failures:
        print("文书转换失败：\n" + "\n".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print(f"\n→ {out_dir}")


if __name__ == "__main__":
    main()
