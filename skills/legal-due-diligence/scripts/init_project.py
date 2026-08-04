#!/usr/bin/env python3
"""
法律尽职调查项目初始化脚本 v26.4.29.1545

用法:
    python3 init_project.py \
        --path /path/to/project \
        --target "目标公司全称" \
        --client "委托人名称" \
        [--base-date 2026-03-20] \
        [--purpose "股权收购"] \
        [--law-firm "XX律师事务所"] \
        [--lawyers "张三,李四"] \
        [--uscc 91110108MA0074PN30]    # 记录统一社会信用代码，写入 project-info.md

功能:
    1. 在指定路径创建项目目录
    2. 生成 project-info.md（项目基本信息与进度跟踪）
    3. 生成 working-paper.md（10章合一的完整底稿，单一文件）
    4. 创建 report/ 与 raw/chineselaw/ 目录
    5. 初始化完成后提示使用 yd-enterprise-info 拉取工商数据

注意：本脚本不再内置元典 API 调用，工商数据获取请使用独立 skill：
    ~/.claude/skills/yd-enterprise-info/scripts/yd_enterprise_info.py
"""

import argparse
from datetime import date
from pathlib import Path

# 10大调查板块
CHAPTERS = [
    ("1", "公司基本信息与主体资格",
     "目标公司的设立、存续、基本工商登记信息、公司章程及历次变更情况。",
     [
         "审阅目标公司提供的营业执照、公司章程等文件",
         "查询国家企业信用信息公示系统",
     ]),
    ("2", "股权结构与股东信息",
     "目标公司的股权结构、各股东出资情况、历次股权变动、股权上的权利限制。",
     [
         "审阅股东名册、出资证明、验资报告等文件",
         "审阅历次股权转让协议及相关决议",
         "查询股权质押、冻结信息",
     ]),
    ("3", "公司治理与组织结构",
     "目标公司的组织架构、董监高人员、三会运作情况、内部管理制度。",
     [
         "审阅组织结构图、董监高任职文件",
         "审阅历次股东会、董事会、监事会会议文件",
         "审阅内部管理制度",
     ]),
    ("4", "核心资产",
     "目标公司的不动产、主要动产、知识产权及其权利负担情况。",
     [
         "审阅不动产权属证明文件",
         "审阅设备清单及购买凭证",
         "查询知识产权登记信息",
         "查询不动产登记信息（抵押、查封）",
     ]),
    ("5", "业务经营与合同管理",
     "目标公司的主营业务、核心合同、客户及供应商、业务资质。",
     [
         "审阅业务介绍资料及主要合同",
         "审阅业务资质证照",
         "分析客户及供应商集中度",
     ]),
    ("6", "财务与税务",
     "目标公司的财务状况（侧重法律合规性审查）、税务登记及合规情况。",
     [
         "审阅财务报表及审计报告",
         "审阅纳税申报资料",
         "核查银行账户信息",
     ]),
    ("7", "劳动人事管理",
     "目标公司的劳动用工情况、社保公积金缴纳、内部人事制度、劳动争议。",
     [
         "审阅员工名册及劳动合同样本",
         "审阅社保公积金缴纳凭证",
         "审阅员工手册及内部人事制度",
         "审阅竞业限制、保密协议",
     ]),
    ("8", "重大债权债务与担保",
     "目标公司的银行借款、重大应付款项、对外担保、应收账款。",
     [
         "审阅银行借款合同及担保合同",
         "审阅应付款项明细及对应合同",
         "审阅对外担保合同及相关决议",
         "审阅应收账款明细及账龄分析",
     ]),
    ("9", "诉讼、仲裁与行政处罚",
     "目标公司涉及的未决/已决诉讼仲裁、行政处罚及潜在法律纠纷。",
     [
         "审阅目标公司提供的诉讼/仲裁案件材料",
         "查询中国裁判文书网",
         "查询中国执行信息公开网",
         "查询信用中国",
         "查询国家企业信用信息公示系统",
     ]),
    ("10", "其他重要文件",
     "目标公司的对外投资、关联交易、环保安全生产、其他与交易相关的重要事项。",
     [
         "审阅对外投资相关资料",
         "审阅关联方名单及关联交易协议",
         "审阅环保、安全生产相关文件",
     ]),
]


def generate_chapter_section(num: str, name: str, scope: str, methods: list[str]) -> str:
    """生成单章底稿内容块"""
    methods_str = "\n".join(f"- [ ] {m}" for m in methods)
    return f"""
---

## 第{num}章 {name}

> **状态**：⬜ 未开始 　**最后更新**：

### {num}.1 调查范围与方法

**调查范围**：{scope}

**调查方法**：
{methods_str}
- [ ] 其他：

### {num}.2 已获取材料清单

| 序号 | 材料名称 | 形式 | 日期/期间 | 备注 |
|------|---------|------|----------|------|
| 1 | | | | |

### {num}.3 未获取/待补充材料

| 序号 | 材料名称 | 重要程度 | 状态 | 影响说明 |
|------|---------|---------|------|---------|
| 1 | | 🔴高/🟡中/🟢低 | 未催 | |

### {num}.4 调查发现

> 每项发现注明来源："经查阅[文件名称]，……"；涉及金额、日期等必须精确引用；仅记录客观事实。

[待撰写]

### {num}.5 风险提示

| 序号 | 风险事项 | 等级 | 事实依据 | 法律依据 | 处理建议 |
|------|---------|------|---------|---------|---------|
| 1 | | 🔴/🟡/🟢 | | | |

> 🔴高=可能导致交易失败或重大损失 | 🟡中=可能影响交易条件 | 🟢低=可通过常规措施解决

### {num}.6 律师备忘

> 此部分为律师内部工作记录，**不会出现在最终报告**中。

[待记录]
"""


def generate_working_paper(args) -> str:
    """生成完整底稿（10章合一）"""
    header = f"""# 法律尽职调查底稿

> **目标公司**：{args.target}
> **委托人**：{args.client}
> **调查基准日**：{args.base_date}
> **调查目的**：{args.purpose}
> **经办律师**：{args.lawyers}
> **律师事务所**：{args.law_firm}
> **底稿创建日期**：{date.today().isoformat()}

---

## 使用说明

- 本底稿为10章合一的完整文件，按顺序撰写或按需跳章均可
- 逐章完成后请将状态更新为 ✅ 已完成
- **§X.6 律师备忘** 为内部记录区，不进入最终报告
- 如项目特别复杂需要拆分文件，请告知律师另行安排
"""
    chapters = "".join(
        generate_chapter_section(num, name, scope, methods)
        for num, name, scope, methods in CHAPTERS
    )
    return header + chapters


def generate_project_info(args) -> str:
    """生成项目信息文件"""
    chapters_rows = "\n".join(
        f"| 第{num}章 | {name} | ⬜ 未开始 | |"
        for num, name, _, _ in CHAPTERS
    )
    uscc_row = f"| **统一社会信用代码** | {args.uscc} |\n" if getattr(args, "uscc", "") else ""
    return f"""# 法律尽职调查项目信息

## 基本信息

| 项目 | 内容 |
|------|------|
| **目标公司** | {args.target} |
{uscc_row}| **委托人** | {args.client} |
| **调查基准日** | {args.base_date} |
| **调查目的** | {args.purpose} |
| **律师事务所** | {args.law_firm} |
| **经办律师** | {args.lawyers} |
| **项目创建日期** | {date.today().isoformat()} |

## 章节进度

| 章节 | 名称 | 状态 | 完成日期 |
|------|------|------|---------|
{chapters_rows}

## 工作日志

| 日期 | 工作内容 | 经办人 |
|------|---------|-------|
| {date.today().isoformat()} | 项目初始化 | |
"""


def main():
    parser = argparse.ArgumentParser(description="法律尽职调查项目初始化")
    parser.add_argument("--path", required=True, help="项目存放路径")
    parser.add_argument("--target", required=True, help="目标公司全称")
    parser.add_argument("--client", required=True, help="委托人名称")
    parser.add_argument("--base-date", default=date.today().isoformat(), help="调查基准日 (YYYY-MM-DD)")
    parser.add_argument("--purpose", default="[待填写]", help="调查目的")
    parser.add_argument("--law-firm", default="[待填写]", help="律师事务所名称")
    parser.add_argument("--lawyers", default="[待填写]", help="经办律师姓名（多个用逗号分隔）")
    parser.add_argument("--uscc", default="", help="目标公司统一社会信用代码（可选；记录到 project-info.md）")

    args = parser.parse_args()

    project_path = Path(args.path)
    project_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ 创建项目目录：{project_path}")

    # project-info.md
    info_path = project_path / "project-info.md"
    info_path.write_text(generate_project_info(args), encoding="utf-8")
    print(f"✅ 生成项目信息：project-info.md")

    # working-paper.md（10章合一）
    wp_path = project_path / "working-paper.md"
    wp_path.write_text(generate_working_paper(args), encoding="utf-8")
    print(f"✅ 生成底稿文件：working-paper.md（10章合一）")

    # report/ 目录
    (project_path / "report").mkdir(exist_ok=True)
    print(f"✅ 创建报告目录：report/")

    # raw/chineselaw/ 目录（用于存放外部 API 原始响应）
    raw_dir = project_path / "raw" / "chineselaw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ 创建原始数据目录：raw/chineselaw/")


    print(f"\n{'='*50}")
    print(f"🎉 项目初始化完成！")
    print(f"📁 项目路径：{project_path}")
    print(f"📋 目标公司：{args.target}")
    print(f"👤 委托人：{args.client}")
    print(f"📅 基准日：{args.base_date}")
    if args.uscc:
        print(f"🆔 USCC：{args.uscc}")
    print(f"\n📝 下一步：")
    print(f"   1. 使用 yd-enterprise-info 拉取目标公司工商数据：")
    if args.uscc:
        print(f"      python3 ~/.claude/skills/yd-enterprise-info/scripts/yd_enterprise_info.py \\")
        print(f"        base-info --tyshxydm {args.uscc} --output {project_path}/raw/chineselaw/ --yes")
        print(f"      （以及 brand, patent, litigation-doc 等，详见 yd-enterprise-info 的 chapter-mapping.md）")
    else:
        print(f"      先检索目标公司：")
        print(f"      python3 ~/.claude/skills/yd-enterprise-info/scripts/yd_enterprise_info.py \\")
        print(f"        search-company --name \"{args.target}\"")
        print(f"      获取 USCC 后再拉详细数据（详见 yd-enterprise-info skill）")
    print(f"   2. 使用 draft 模式逐章撰写底稿：")
    print(f"      示例：请帮我撰写第1章的底稿，材料在 [路径]")


if __name__ == "__main__":
    main()
