## 公司诉讼案件指导专家

### Company Litigation Case Guide for China

**CorpClaim CN** 是一个面向中国公司、创业与民商事争议场景的结构化法律分析 Skill。

它不是普通法律问答工具，而是围绕公司类案件中最关键的三个问题展开：

> **案由是什么？
> 请求权基础是什么？
> 需要证明哪些构成要件事实？**

CorpClaim CN is a structured legal analysis Skill for corporate and commercial disputes in China.
It is designed to transform factual descriptions into litigation-ready structures: **case cause, claim basis, elements of proof, evidence checklist, and litigation strategy**.

---

## 核心定位｜Positioning

CorpClaim CN 专注于公司、创业、技术服务、股权、合伙、劳动用工和投资关系识别等高频民商事争议。

它尤其适合：

* 创业者；
* 科技公司；
* 企业经营者；
* 公司股东；
* 技术服务提供方；
* SaaS / 软件外包团队；
* 企业法务、律师与法律产品开发者；
* 希望在咨询律师前先整理案件结构的用户。

CorpClaim CN focuses on corporate and commercial disputes, especially those involving startups, technology services, equity, partnership, labor relationships, IP contracts, and investment-relationship classification.

---

## 为什么不是普通法律问答｜Why It Is Different

普通 AI 法律问答通常会直接回答“能不能起诉”或“适用什么法律”。

CorpClaim CN 更关注诉讼中真正决定案件走向的结构：

1. **案由识别**
   判断案件应落入哪一类民事案由或关系识别模块。

2. **请求权基础分析**
   判断诉讼请求背后的法律基础，而不是只停留在“是什么纠纷”。

3. **构成要件事实拆解**
   将请求权基础拆解成用户必须证明的事实。

4. **证据清单生成**
   区分强证据、补强证据、缺失关键证据和高风险证据。

5. **对方抗辩预测**
   预判对方可能如何反驳，并提示应对证据。

6. **诉讼路径建议**
   判断是否适合立即起诉、先补证据、先协商调解，或需要律师人工复核。

---

## 数据来源与权威性｜Data Basis and Authority

本 Skill 的知识库基于中国民事案由体系、请求权基础分析方法、构成要件事实理论，以及律师对民商事争议解决实务的结构化整理。

其中，案由适用要点、请求权规范和构成要件拆解参考了权威民事案由与请求权规范资料，并经过律师重新整理、压缩、改写和产品化处理。

本项目不会公开上传或复制受版权保护的原始书籍内容。GitHub 中仅保留经律师整理后的结构化规则库。

The knowledge base is built on China’s civil case-cause system, claim-basis methodology, elements-of-proof analysis, and structured legal practice experience.
Original copyrighted materials are not redistributed. The repository only contains structured, rewritten, and productized legal rules.

---

## 准确性设计｜Accuracy-Oriented Design

CorpClaim CN 的准确性来自三层结构控制：

### 1. 案由边界控制

每个模块包含：

* 适用场景；
* 排除场景；
* 易混淆案由；
* 关系识别规则。

### 2. 请求权基础控制

每个案由不只列出“是什么纠纷”，还会匹配：

* 主请求权基础；
* 备选请求权基础；
* 不建议路径；
* 对应诉讼请求。

### 3. 构成要件事实控制

每个请求权基础都会进一步拆解：

* 需要证明的事实；
* 当前证据；
* 缺失证据；
* 举证责任；
* 对方可能抗辩；
* 风险提示。

因此，CorpClaim CN 的目标不是生成“漂亮的法律回答”，而是生成更接近律师办案思维的**诉讼结构分析结果**。

---

## 当前支持模块｜Supported Modules

CorpClaim CN 当前支持以下 10 个核心模块：

1. **民间借贷纠纷**
   Private Lending Disputes

2. **合伙合同纠纷**
   Partnership Contract Disputes

3. **技术服务合同纠纷**
   Technology Service Contract Disputes

4. **买卖合同纠纷**
   Sales Contract Disputes

5. **不当得利纠纷**
   Unjust Enrichment Disputes

6. **网络服务合同纠纷**
   Online Service Contract Disputes

7. **知识产权合同纠纷**
   Intellectual Property Contract Disputes

8. **劳动争议纠纷**
   Labor Disputes

9. **股东纠纷**
   Shareholder and Equity Disputes

10. **投资合同纠纷（复合案由）**
    Investment Relationship Classifier
    用于将“投资”事实进一步识别为股东纠纷、合伙合同纠纷、民间借贷纠纷、不当得利纠纷或其他真实法律关系。

---

## 适合处理的典型问题｜Typical Questions

你可以这样问：

```text
我给朋友的创业项目投了20万元，说好给我股权，但没有工商变更，也没有签代持协议。后来项目有收入，对方不承认我是股东。我应该是什么案由？请求权基础是什么？
```

```text
我和朋友一起做 SaaS 项目，我出钱，他负责技术开发。项目上线后有收入，但他不让我看后台，也不分账。我该怎么主张权利？
```

```text
我找外包团队开发小程序，已经支付3万元，但交付的系统无法使用，也没有通过验收。我应该怎么起诉？
```

```text
我卖了一批设备给对方，有订单、物流签收和对账单，对方拖着不付款，说设备质量有问题。我该准备哪些证据？
```

---

## 使用方式｜How to Use

### 方式一：导入 QClaw / 龙虾 / Agent 工具

1. 下载本仓库 ZIP；
2. 上传到支持 Skill / Agent 的工具；
3. 使用 `skill/SKILL.md` 作为系统指令；
4. 使用 `data/case-database.md` 作为知识库；
5. 使用 `templates/` 中的模板规范输入与输出。

### 方式二：复制到自定义 AI 助手

你也可以将以下内容复制到支持系统提示词的工具中：

* `skill/SKILL.md`
* `data/case-database.md`

适用工具包括：

* QClaw / 腾讯龙虾；
* LobeChat；
* ChatGPT 自定义 GPT；
* Dify；
* Coze；
* FastGPT；
* 其他支持知识库和系统提示词的 AI Agent 工具。

---

## 文件结构｜Repository Structure

```text
CorpClaim-CN/
├── README.md
├── skill/
│   └── SKILL.md
├── data/
│   └── case-database.md
└── templates/
    ├── case-intake-template.md
    └── litigation-report-template.md
```

---

## 输出结构｜Output Structure

CorpClaim CN 默认输出：

1. 初步结论；
2. 案由判断；
3. 请求权基础分析；
4. 构成要件事实表；
5. 证据清单；
6. 对方可能抗辩；
7. 诉讼路径建议；
8. 是否建议律师人工复核；
9. 免责声明。

---

## 作者｜Maintainer

本项目由中国执业律师维护，聚焦：

* 公司法；
* 合伙纠纷；
* 股权纠纷；
* 技术服务合同；
* 知识产权合同；
* 民商事争议解决；
* 创业公司法律风险控制。

如果你使用 CorpClaim CN 后，仍然对以下问题不放心：

* 案由是否准确；
* 请求权基础是否选对；
* 构成要件事实是否完整；
* 证据链是否足够；
* 起诉状如何组织；
* 对方抗辩如何应对；
* 是否适合起诉、调解或谈判；

可以联系作者进行律师人工复核。

### 联系方式｜Contact

* 微信 / WeChat：yeh-attorney
* 邮箱 / Email：yxklvshi@163.com
* 执业地区 / Jurisdiction：中国·上海
* 业务方向 / Practice Areas：公司法、民商事诉讼、股权纠纷、技术服务合同、创业公司法律服务

---

## 免责声明｜Disclaimer

CorpClaim CN 仅用于中国民事诉讼准备、案件结构整理和法律信息辅助，不构成律师正式法律意见，不保证案件结果。

AI 生成内容可能存在遗漏、错误或不适用于具体案件的情况。复杂案件、金额较大案件、涉及股权、控制权、知识产权、劳动关系或重大商业利益的案件，建议咨询执业律师。

CorpClaim CN is for legal information organization and litigation-preparation assistance only. It does not constitute formal legal advice and does not guarantee litigation outcomes.
