# 招标文件公平竞争合法合规性审查报告

**项目编号**: {{ project_id }}
**审查日期**: {{ review_date }}
**审查结论**: {% if conclusion == "pass" %}✅ 通过{% elif conclusion == "conditional_pass" %}⚠️ 有条件通过{% else %}❌ 不通过{% endif %}

---

## 一、审查结论摘要

| 统计项 | 数量 |
|--------|------|
| 问题总数 | {{ summary.total_issues }} |
| 🔴 高风险 | {{ summary.high_count }} |
| 🟡 中风险 | {{ summary.medium_count }} |
| 🟢 低风险 | {{ summary.low_count }} |

### 审查结论
{% if conclusion == "pass" %}
本次审查未发现重大合规风险，招标文件基本符合相关法规要求，建议按程序推进。
{% elif conclusion == "conditional_pass" %}
本次审查发现 {{ summary.medium_count }} 项中等风险和 {{ summary.high_count }} 项高风险问题，建议对高风险问题进行修改后重新审查，中等风险问题建议在发布前完成整改。
{% else %}
本次审查发现 {{ summary.high_count }} 项高风险问题，招标文件存在明显合规风险，必须修改后重新审查。
{% endif %}

### 问题分布（按审查维度）

| 审查维度 | 对应审查表类别 | 问题数 |
|----------|---------------|--------|
| 公平竞争审查 | 第一部分（事项1.1-7.5） | {{ summary.category_distribution.get("fair_competition", 0) }} |
| 废标条款审查 | 第一/二部分交叉 | {{ summary.category_distribution.get("compliance_mandatory", 0) }} |
| 资格条件审查 | 第三类（事项3.1-3.4） | {{ summary.category_distribution.get("qualification", 0) }} |
| 技术参数合规 | 第四类（事项4.1-4.4） | {{ summary.category_distribution.get("technical_spec", 0) }} |
| 招标程序与评标合规 | 第八/九类（事项8.1-9.8） | {{ summary.category_distribution.get("bidding_procedure", 0) }} |
| 合同条款风险 | 第十类（事项10.1-10.6） | {{ summary.category_distribution.get("contract_terms", 0) }} |
| 合同与程序合规 | 第十/十一类（事项10.1-11.5） | {{ summary.category_distribution.get("contract_compliance", 0) }} |
| 反垄断与专项审查 | 第十二/十三类（事项12.1-13.5） | {{ summary.category_distribution.get("antitrust_special", 0) }} |

---

## 二、问题清单

{% for issue in issues %}
### {{ issue.issue_id }}: {{ issue.title }}

| 项目 | 内容 |
|------|------|
| **风险等级** | {% if issue.severity == "high" %}🔴 高{% elif issue.severity == "medium" %}🟡 中{% else %}🟢 低{% endif %} |
| **审查模块** | {{ issue.category }} |
| **规则编号** | {{ issue.rule_id }} |
| **审查事项** | {{ issue.get("check_item", "") }} |
| **条款位置** | {{ issue.clause_ref }} |
| **证据** | {{ issue.evidence }} |
| **整改建议** | {{ issue.suggestion }} |
| **法规依据** | {{ issue.get("legal_basis", "") }} |

{% endfor %}

---

## 三、高风险问题汇总

{% set high_issues = issues | selectattr("severity", "equalto", "high") | list %}
{% if high_issues %}
| 序号 | 问题编号 | 标题 | 条款位置 | 整改建议 |
|------|---------|------|---------|---------|
{% for issue in high_issues %}
| {{ loop.index }} | {{ issue.issue_id }} | {{ issue.title }} | {{ issue.clause_ref }} | {{ issue.suggestion[:50] }}... |
{% endfor %}
{% else %}
无高风险问题。
{% endif %}

---

## 四、审查依据

- 《中华人民共和国招标投标法》
- 《中华人民共和国招标投标法实施条例》
- 《公平竞争审查条例》（国务院令第783号）
- 《公平竞争审查条例实施办法》（99号令）
- 《招标人主体责任履行指引》（发改法规〔2025〕1358号）
- 《必须招标的工程项目规定》（发改委等八部门令第16号，2024）
- 《中华人民共和国反垄断法》
- 《中华人民共和国反不正当竞争法》
- 《中华人民共和国政府采购法》及其实施条例
- 闽十四届人大常委会公告第31号
- 闽发改法规〔2023〕53号
- 相关行业法规及标准

---

## 五、声明

1. 本报告基于招标文件文本的自动化审查生成，仅供参考。
2. 审查结果不替代专业法律意见，建议重要问题咨询法律顾问。
3. 本报告由 ima 招标文件合规审查系统自动生成，审查过程可追溯、可审计。
4. 审查规则依据《招标文件公平竞争合法合规性审查表》v0520版编制，覆盖13大类45+审查事项。

---

*报告生成时间: {{ review_date }}*
*系统版本: ima-bidding-compliance-engine v2.0*
*审查规则数: 95条（8个规则文件）*
