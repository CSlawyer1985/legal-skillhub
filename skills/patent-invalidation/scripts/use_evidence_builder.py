#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
use_evidence_builder.py —— 使用公开类证据链模板生成器
========================================================

PatSeek 与本技能其他工具主要服务"专利文献类"证据；**使用公开**类证据
（销售 / 展会 / 宣传册 / 产品 / 技术文献 / 网络公开）由本工具专责。

为什么需要它：
    使用公开类证据能否被采信，**关键在证据链是否闭合、是否达到"高度盖然性"**
    （参见 references/证据组合与证明标准.md §三）。单份销售发票或一份宣传册
    几乎一定被合议组认为"指向模糊"；只有"产品+合同+发票+物流+检测报告"等
    多维度证据相互印证、且每条都有"形式合法性"（公证/认证/时间戳/原件），
    才可能被认定。

    本工具按"使用公开类型"输出对应的**证据链模板**：每条证据占位 + 待填项
    + 形式合法性提示 + 闭合性自检清单。

子命令:
    template  <type> [--out F]   生成指定类型的证据链模板（markdown）
    checklist                    打印通用证据链闭合性自检清单
    types                        列出所有支持的证据类型

支持的证据类型:
    sale        销售类（产品 + 合同 + 发票 + 物流 + 实物 + 检测报告）
    exhibition  展会类（展位 + 宣传册 + 媒体 + 记录）
    literature  技术文献类（论文 + 引用 + 手册）
    standard    标准类（标准号 + 发布 + 引用）
    web         网络公开类（URL + 公证 + 时间戳）
    all         一次输出全部类型模板

使用前提:
    无外部依赖（仅 Python 标准库）
"""
import argparse
import os
import sys
from datetime import datetime


# ── 模板库 ────────────────────────────────────────────────

TEMPLATES = {
    "sale": {
        "title": "使用公开（销售类）证据链模板",
        "intro": (
            "**核心要件**：证明在目标专利申请日（有优先权的，优先权日）前，"
            "被控/对比产品已通过**销售合同/发票/物流/实物**形成可追溯的完整链路。"
        ),
        "evidence_chain": [
            {
                "name": "产品实物/照片",
                "description": "产品本体或照片，含型号/规格/外观可识别的标识",
                "source": "请求人留存 / 公证购买",
                "form_legality": "建议公证购买并封存（公证处出具购买公证书）",
            },
            {
                "name": "销售合同",
                "description": "购销合同，含产品型号/规格/数量/价格/签署日期",
                "source": "请求人档案 / 客户配合提供",
                "form_legality": "原件 + 公证复印件；合同方主体资格证明",
            },
            {
                "name": "发票",
                "description": "增值税专用发票或普通发票，含产品/金额/开票日期",
                "source": "税务机关 / 财务档案",
                "form_legality": "原件 + 公证复印件；可申请税务系统核验",
            },
            {
                "name": "物流凭证",
                "description": "送货单 / 运单 / 物流公司证明 / 签收记录",
                "source": "物流公司 / 客户档案",
                "form_legality": "原件 + 公证；物流公司盖章证明",
            },
            {
                "name": "银行流水/收款记录",
                "description": "对公账户收款记录，与发票/合同金额对应",
                "source": "请求人财务档案",
                "form_legality": "银行盖章 + 公证",
            },
            {
                "name": "产品宣传册/技术手册",
                "description": "销售时附随的产品宣传册或技术手册",
                "source": "请求人 / 客户档案",
                "form_legality": "原件 + 公证；记录发行日期/版本",
            },
            {
                "name": "检测报告",
                "description": "第三方检测机构对产品技术指标的检测报告",
                "source": "请求人 / 第三方机构",
                "form_legality": "原件 + 公证；机构资质证明",
            },
        ],
        "closing_checks": [
            "时间：所有证据日期**早于目标专利申请日/优先权日**（硬门槛）",
            "主体：合同/发票/物流各方主体明确可追溯",
            "金额：合同金额 ≈ 发票金额 ≈ 银行流水金额（三者一致）",
            "产品：型号/规格/数量在所有证据中可对应",
            "形式：每份证据均做**原件公证**（最稳）/或公证复印件",
            "链条：7 项证据**至少 4-5 项**齐备且相互印证（单点证据不采）",
        ],
    },
    "exhibition": {
        "title": "使用公开（展会类）证据链模板",
        "intro": (
            "**核心要件**：证明在目标专利申请日前，对比产品/技术已在公开展会"
            "**展览、展示、宣传、演示**，且展会为**对公众开放**（非内部展）。"
        ),
        "evidence_chain": [
            {
                "name": "展会官方公告/招展书",
                "description": "展会主办方/官网发布的展会时间、地点、主题、参展企业名录",
                "source": "展会官网 / 主办方",
                "form_legality": "官网截图 + 公证（建议做网页公证）",
            },
            {
                "name": "展位图/展位号",
                "description": "请求人展位的位置图、展位号、展位面积",
                "source": "主办方 / 请求人档案",
                "form_legality": "主办方盖章 + 公证",
            },
            {
                "name": "参展合同/付款凭证",
                "description": "与主办方签订的参展合同、付款发票/收据",
                "source": "请求人财务档案",
                "form_legality": "原件 + 公证",
            },
            {
                "name": "宣传册/展品资料",
                "description": "展会现场发放的产品宣传册、技术资料",
                "source": "请求人 / 现场拍摄",
                "form_legality": "现场拍摄视频/照片（带时间戳）+ 公证",
            },
            {
                "name": "现场照片/视频",
                "description": "展位、展品、宣传册、人员等的现场影像",
                "source": "请求人 / 第三方摄影",
                "form_legality": "原始文件 + 公证（建议公证员现场见证拍摄）",
            },
            {
                "name": "媒体报道",
                "description": "展会期间或展后，第三方媒体对展会的报道（含展品）",
                "source": "媒体网站 / 行业杂志",
                "form_legality": "网站截图 + 公证（注明发布时间与原始 URL）",
            },
            {
                "name": "参展人员证/入场记录",
                "description": "参展人员的工作证、参展证、入场记录",
                "source": "请求人 / 主办方",
                "form_legality": "原件 + 公证",
            },
        ],
        "closing_checks": [
            "时间：展会**开始日 + 结束日**均早于目标专利申请日/优先权日",
            "公开性：展会**对公众开放**（非内部展、非定向邀请展）",
            "主体：请求人在展会的**主体资格**（参展合同）明确",
            "产品：宣传册/展品/视频能直接**看到对比产品**及其技术特征",
            "形式：现场照片/视频/网页均做**公证**（建议公证员现场见证）",
            "链条：6 项证据**至少 4 项**齐备且相互印证",
        ],
    },
    "literature": {
        "title": "使用公开（技术文献类）证据链模板",
        "intro": (
            "**核心要件**：证明在目标专利申请日前，对比技术方案已通过**论文、"
            "手册、会议、标准、教材**等公开技术文献**完整公开**。"
            "（注：PatSeek 检索结果多为专利文献，技术文献多走 CNKI/万方/IEEE 等）"
        ),
        "evidence_chain": [
            {
                "name": "论文/期刊文章",
                "description": "学术期刊或会议论文，含作者、机构、DOI、发表日",
                "source": "CNKI / 万方 / IEEE / ScienceDirect / ACM DL",
                "form_legality": "原件（带版权页 + ISSN）+ 公证复印件",
            },
            {
                "name": "书籍/教材/手册",
                "description": "正式出版的技术书籍，含 ISBN、出版社、出版日",
                "source": "图书馆 / 出版社官网",
                "form_legality": "原件（带版权页 + ISBN）+ 公证；建议提供在版编目（CIP）数据",
            },
            {
                "name": "标准/规范",
                "description": "国家/行业/团体标准，含标准号、发布机构、实施日",
                "source": "全国标准信息公共服务平台 / 各行业标准化机构",
                "form_legality": "标准文本原件（带标准号 + 发布机构章）+ 公证",
            },
            {
                "name": "会议演讲/PPT",
                "description": "学术/行业会议的演讲稿、PPT、海报",
                "source": "会议官网 / 主办方 / 作者主页",
                "form_legality": "网站截图（含 URL + 发布时间）+ 公证",
            },
            {
                "name": "学位论文",
                "description": "硕博论文，含作者、学校、答辩日、收录日",
                "source": "CNKI / 万方 / ProQuest",
                "form_legality": "原件（含学校盖章页）+ 公证",
            },
            {
                "name": "产品技术手册/白皮书",
                "description": "厂家发布的产品手册、白皮书、技术资料",
                "source": "厂家官网 / 客户档案",
                "form_legality": "原件 + 公证；含版本号 + 发布日期",
            },
        ],
        "closing_checks": [
            "时间：所有文献**发表日/出版日/发布日**早于目标专利申请日/优先权日",
            "可获取：文献能**公开获取**（图书馆、官网、CNKI 等），非内部资料",
            "完整性：含**版权页**（对图书）/ **ISSN/ISBN**（对期刊/图书）/ **标准号**（对标准）",
            "形式：原件 + 公证复印件合议组最易采信",
            "内容：文献**完整公开**对比技术方案（不能只摘要不核心）",
            "链条：5 项证据**至少 2-3 项**齐备（如单篇即可独立公开，对比文件单用即可）",
        ],
    },
    "standard": {
        "title": "使用公开（标准类）证据链模板",
        "intro": (
            "**核心要件**：证明在目标专利申请日前，对比技术方案已被**国家/行业/"
            "团体标准**采纳并公开发布。标准证据效力高，但需注意**标准必要专利"
            "（SEP）抗辩**与**实施许可**问题。"
        ),
        "evidence_chain": [
            {
                "name": "标准文本",
                "description": "标准全文，含标准号、名称、范围、规范性引用文件",
                "source": "全国标准信息公共服务平台（std.samr.gov.cn）",
                "form_legality": "原件（带标准号 + 发布机构章）+ 公证",
            },
            {
                "name": "标准发布公告",
                "description": "发布机构的官方公告（含发布日、实施日）",
                "source": "发布机构官网 / 报刊",
                "form_legality": "官网截图 + 公证（注明发布时间）",
            },
            {
                "name": "标准编制说明",
                "description": "标准编制过程中的送审稿、报批稿、编制说明",
                "source": "发布机构 / 起草单位",
                "form_legality": "原件 + 公证；可显示技术方案演化的关键证据",
            },
            {
                "name": "标准对应专利披露",
                "description": "如该标准是 SEP（含相关专利），披露对应专利号",
                "source": "标准披露声明 / 知识产权政策",
                "form_legality": "披露文件原件 + 公证",
            },
        ],
        "closing_checks": [
            "时间：标准**发布日期/实施日期**早于目标专利申请日/优先权日",
            "公开性：标准为**公开发布**（非内部规范）",
            "范围：标准**明确公开**对比技术方案（被规范性引用 / 在正文章节）",
            "形式：标准文本 + 公证（标准证据通常被认为证明力强）",
            "关联：如涉案专利与标准相关，注意**专利权人是否在标准制定过程中有禁反言陈述**",
        ],
    },
    "web": {
        "title": "使用公开（网络公开类）证据链模板",
        "intro": (
            "**核心要件**：证明在目标专利申请日前，对比技术方案已通过**网站、"
            "社交媒体、视频平台、电商页面**等公网公开。网络公开易被修改/删除，"
            "**公证**几乎是必须手段。"
        ),
        "evidence_chain": [
            {
                "name": "URL 与发布时间",
                "description": "原始 URL + 网页/帖子/视频的发布时间（含时区）",
                "source": "目标网站 / Wayback Machine (web.archive.org)",
                "form_legality": "**公证员现场访问** + 截图 + 时间戳 + 公证书",
            },
            {
                "name": "网页内容",
                "description": "网页全部可见内容：文字、图片、视频、技术参数、规格表",
                "source": "目标网站",
                "form_legality": "完整截图（不限高度）+ HTML 源码 + 公证",
            },
            {
                "name": "Wayback Machine 历史快照",
                "description": "网页在申请日前的 archive.org 历史快照（独立第三方）",
                "source": "https://web.archive.org",
                "form_legality": "第三方平台证据，可与公证书相互印证",
            },
            {
                "name": "域名/账号归属",
                "description": "网站域名注册信息 / 社交媒体账号归属",
                "source": "WHOIS / 平台账号信息",
                "form_legality": "第三方查询结果 + 公证",
            },
            {
                "name": "发布者身份关联",
                "description": "发布者与请求人/对比产品/对比技术的关联证据",
                "source": "网站声明 / 账号实名 / 历史发布记录",
                "form_legality": "页面截图 + 公证",
            },
        ],
        "closing_checks": [
            "时间：网页/帖子的**发布时间戳**早于目标专利申请日/优先权日",
            "可获取：原始 URL 在申请日后仍可访问（**必须**做公证，否则对方可删除抗辩）",
            "主体：发布者与对比技术/产品的关联明确",
            "内容：网页内容**直接公开**对比技术方案（不能是间接暗示）",
            "形式：公证员**现场访问** + 截图 + 时间戳（电子证据司法解释要求的取证方式）",
            "备份：Wayback Machine 历史快照作为独立第三方印证",
        ],
    },
}


# ── 通用自检清单 ─────────────────────────────────────────

COMMON_CHECKLIST = """
# 证据链通用自检清单（M7 必过）

> 来源: references/证据组合与证明标准.md；本清单为"高度盖然性"证据的最低标准。

## 一、时间节点（死线）

- [ ] **所有证据公开日 / 销售日 / 出版日 / 展会日 / 标准发布日均早于目标专利申请日**（有优先权的，早于优先权日）
- [ ] 时间证据可在多份证据间**相互印证**（如销售合同日期 ≈ 发票日期 ≈ 物流日期）
- [ ] 时间证据**有第三方可验证**（银行流水、税务记录、媒体报道、Wayback Machine 等）

## 二、证据形式合法性

- [ ] 域外证据经**所在国公证 + 中国驻该国使领馆认证**（或依条约简化）
- [ ] 外文证据附**规范中文译本**（译文与原文一致）
- [ ] 网络公开证据**经公证员现场访问取证**（截图 + 时间戳 + 公证书）
- [ ] 使用公开类证据**经公证购买 / 公证取样**
- [ ] 图书类非专利文献附**版权页 + ISBN + 原件**

## 三、证据链闭合性（多维度相互印证）

- [ ] **至少 3-5 份证据**形成完整链条（单点证据通常不采信）
- [ ] 各证据的**主体 / 客体 / 时间 / 地点 / 内容**可对应
- [ ] 金额、数量、型号、规格等关键数据**在不同证据中一致**
- [ ] 至少有**一份独立第三方证据**（如媒体报道、银行流水、检测报告）

## 四、高度盖然性（行政/民事诉讼通用标准）

- [ ] 证据链**无合理疑点**（专利权人仅质疑但未举反证，不足以否定）
- [ ] **关键事实**（公开时间、公开内容、公开主体）有 2+ 来源印证
- [ ] 不依赖**孤证**（如孤立的销售发票，缺其他证据，几乎不采信）

## 五、与无效理由的对应

- [ ] 每条证据**明确指向**至少一条无效理由（新颖性 / 创造性 / 使用公开）
- [ ] 证据组合**形成完整三步法**（最接近现有技术 + 区别特征 + 结合启示）或**新颖性单篇**
- [ ] **公知常识证据**单独准备（技术词典 / 手册 / 教科书）—— 可在口审辩论终结前补充

## 六、特别警示

- ⚠️ **同样理由和证据**再次提出 → **不予受理**（已处理过的不要再提）
- ⚠️ 域外证据**未公证认证** → 合议组通常**不予采信**
- ⚠️ 使用公开证据**仅含孤证**（如单份发票）→ 几乎**100% 不予采信**
- ⚠️ 申请日后**补交实验数据**证明预料不到效果 → 需与原申请**紧密关联**（《审查指南》第二部分第十章 3.5.1）
- ⚠️ 化学/医药领域**实验数据**缺形式完整性（样品来源/测量条件/实验人员/方法/数据处理）→ 不予采信
"""


# ── 模板渲染 ─────────────────────────────────────────────

def render_template(t: dict, target_patent: str = "", priority_date: str = "") -> str:
    """渲染单个证据链模板为 markdown。"""
    lines = []
    lines.append(f"# {t['title']}")
    lines.append("")
    if target_patent or priority_date:
        lines.append(f"> **目标专利**: {target_patent or '（待填）'}")
        lines.append(f"> **优先权日（时间死线）**: {priority_date or '（待填）'}")
        lines.append("")
    lines.append("## 一、说明")
    lines.append("")
    lines.append(t["intro"])
    lines.append("")
    lines.append("## 二、证据链（逐项提供）")
    lines.append("")
    lines.append("| # | 证据名称 | 内容描述 | 来源 | 形式合法性建议 | 获取状态 |")
    lines.append("|---|---------|---------|------|--------------|---------|")
    for i, e in enumerate(t["evidence_chain"], 1):
        lines.append(f"| {i} | **{e['name']}** | {e['description']} | {e['source']} | {e['form_legality']} | ☐ 待获取 |")
    lines.append("")
    lines.append("## 三、闭合性自检")
    lines.append("")
    for ck in t["closing_checks"]:
        lines.append(f"- [ ] {ck}")
    lines.append("")
    lines.append("---")
    lines.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    return "\n".join(lines)


# ── 子命令 ───────────────────────────────────────────────

def cmd_template(args) -> int:
    if args.type == "all":
        for typ, t in TEMPLATES.items():
            md = render_template(t, args.target or "", args.priority or "")
            if args.out:
                out_path = os.path.join(args.out, f"evidence_{typ}.md")
                os.makedirs(args.out, exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(md)
                print(f"[OK] {typ}: {out_path}")
            else:
                print(md)
                print("\n" + "=" * 60 + "\n")
        return 0
    elif args.type in TEMPLATES:
        t = TEMPLATES[args.type]
        md = render_template(t, args.target or "", args.priority or "")
        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"[OK] 模板已写入: {args.out}")
        else:
            print(md)
        return 0
    else:
        print(f"错误: 未知类型 '{args.type}'。可选: {', '.join(list(TEMPLATES.keys()) + ['all'])}", file=sys.stderr)
        return 1


def cmd_checklist(args) -> int:
    print(COMMON_CHECKLIST)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(COMMON_CHECKLIST)
        print(f"[OK] 自检清单已写入: {args.out}")
    return 0


def cmd_types(args) -> int:
    print("支持的证据类型:\n")
    for typ, t in TEMPLATES.items():
        print(f"  - {typ:12s} {t['title']}")
    print(f"\n  - {'all':12s} 一次输出全部类型模板")
    print(f"\n（共 {len(TEMPLATES)} 种）")
    return 0


# ── CLI 入口 ────────────────────────────────────────────

def main() -> int:
    # v1.0.9: Windows GBK 控制台 print 中文报错，强制 stdout/stderr 为 utf-8
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
    ap = argparse.ArgumentParser(
        description="使用公开类证据链模板生成器（销售/展会/技术文献/标准/网络）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有支持的证据类型
  python use_evidence_builder.py types

  # 生成"销售类"证据链模板（输出到 stdout）
  python use_evidence_builder.py template sale

  # 全部类型输出到 ./evidences/ 目录
  python use_evidence_builder.py template all --out ./evidences

  # 填入目标专利 + 优先权日
  python use_evidence_builder.py template sale \\
      --target CN118658342A --priority 20150310 \\
      --out ./evidences/evidence_sale.md

  # 通用证据链闭合性自检清单
  python use_evidence_builder.py checklist --out ./checklist.md
        """,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_t = sub.add_parser("template", help="生成指定类型的证据链模板")
    p_t.add_argument("type", help="证据类型: sale/exhibition/literature/standard/web/all")
    p_t.add_argument("--out", default="", help="输出文件或目录（默认 stdout）")
    p_t.add_argument("--target", default="", help="目标专利公开号（填入模板顶部）")
    p_t.add_argument("--priority", default="", help="目标专利优先权日 YYYYMMDD（填入模板顶部）")

    p_c = sub.add_parser("checklist", help="打印通用证据链闭合性自检清单")
    p_c.add_argument("--out", default="", help="输出文件（默认 stdout）")

    p_l = sub.add_parser("types", help="列出所有支持的证据类型")

    args = ap.parse_args()
    if args.cmd == "template":
        return cmd_template(args)
    elif args.cmd == "checklist":
        return cmd_checklist(args)
    elif args.cmd == "types":
        return cmd_types(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
