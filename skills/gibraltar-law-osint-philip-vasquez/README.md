# 直布罗陀法律、监管与合规 OSINT

**一份开源技能文件，使 AI 助手植根于直布罗陀的法律、监管和合规图景。**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Version](https://img.shields.io/badge/version-1.6-blue)]()
[![Jurisdiction](https://img.shields.io/badge/jurisdiction-Gibraltar-red)]()
[![Articles](https://img.shields.io/badge/legal%20articles-7%20published-green)]()

---

## 这是什么

直布罗陀是一个拥有成熟法律与监管框架的小型司法辖区——但恰恰是 AI 模型持续出错的地方。英格兰普通法的假设在不该渗入的地方渗入。程序规则与英国对应规则存在在实践中重要的差异。官方来源分散在十几个不同网站上，没有中央索引。

本仓库包含一份结构化的技能文件，用于纠正这一点。将它上传到 Claude、Gemini、ChatGPT、Harvey、Legora 或任何 AI 助手，可在您开始研究之前使其植根于可靠的、辖区特定的知识。

**它不是产品。它是一份在 CC BY 4.0 下免费发布的参考文件。**

---

## 适用对象

- **直布罗陀律师** — 程序差异、判例法层级、法院结构、劳动法和公法
- **合规与 AML/KYC 专业人士** — FSC、博彩司（Gambling Division）、OFT 登记簿；AML 框架；FATF 立场
- **法律研究者** — 立法、Hansard（议会议事录）、就业法庭裁决、司法审查
- **记者和公共利益研究者** — 法院判决、议会记录、新闻稿
- **构建直布罗陀特定 AI 工具的开发者** — 参见下文 [API 与集成](#api--integration)

---

## 内容

```
Gibraltar Legal Regulatory Compliance OSINT skill.md   ← 技能文件（v1.3）
README.md                                               ← 本文件
LICENSE                                                 ← CC BY 4.0
```

技能文件涵盖：

- **直布罗陀法律原则** — 来源层级、宪法权利、法院结构、民事诉讼程序、劳动法、公法与司法审查 — 每一项都附有 GibCheck 上完整实务深度文章的链接
- **官方数据来源** — 直布罗陀主要官方数据集的已验证 URL，每个都配有相关的 GibCheck 页面
- **研究档案（Research Profiles）** — 合规/AML、法律研究者、议会研究者、记者、海事与航空
- **AI 集成指导** — AI 对直布罗陀的常见错误、如何核验输出
- **出版机构目录** — 报道直布罗陀的主要新闻、政府、商业和行业来源，附 GibCheck 出版机构页面的链接

---

## AI 对直布罗陀的常见错误（本文件如何修正）

| 常见 AI 错误 | 正确立场 |
|-----------------|-----------------|
| 适用英国视为送达规则 | 直布罗陀邮寄视为送达为 **14 天** — *Francis v Clifton-Psaila* |
| 将英国上诉法院判决视为有约束力 | 英国判例法**仅具说服力** — 在直布罗陀法院不具有约束力 |
| 适用 Jackson 改革后的费用规则 | Jackson 改革后规则在直布罗陀**未获采纳** |
| 将直布罗陀视为 2020 年后的欧盟成员 | 欧盟法律**自 2020 年 12 月 31 日起不再适用** |
| 将集体裁员门槛表述为 20 人 | 直布罗陀门槛为 **5 名员工**（而非英格兰的 20 人） |
| 将英国周薪上限适用于裁员补偿 | 直布罗陀裁员计算对周薪**无法定上限** |
| 称歧视赔偿有上限 | 依据《2006 年平等机会法》，歧视赔偿**无上限** |
| 对法律执业者引用错误的监管机构 | **LSRA** 自 2022 年 12 月 30 日起负责监管 |
| 称其为"工业法庭"（Industrial Tribunal） | 自 **2016 年 10 月 13 日起**更名为**就业法庭（Employment Tribunal）** |
| 称直布罗陀不是 FIFA 成员 | 直布罗陀自 **2016 年 5 月 13 日起是 FIFA 成员**（CAS 于 2016 年 5 月 2 日裁决后，代表大会以 172–12 票通过） |
| 称总检察长（Attorney-General）总是正确的王室被告 | *Marrache v AG* [2013–14 Gib LR 520] — 在宪法程序中，总督（Governor）可能是正确的被告 |

---

## 直布罗陀法律原则 — 已发布系列

技能文件包含 GibCheck《直布罗陀法律原则》系列全部六篇已发布文章的摘要。

| 文章 | URL |
|---------|-----|
| The Legal Development of Gibraltar（直布罗陀的法律发展） | https://www.gibcheck.com/legal/principles/legal-development |
| Constitutional Law and Fundamental Rights（宪法与基本权利） | https://www.gibcheck.com/legal/principles/constitutional-law |
| Court Structure and Jurisdiction（法院结构与管辖权） | https://www.gibcheck.com/legal/principles/court-structure |
| Civil Litigation and Procedure（民事诉讼与程序） | https://www.gibcheck.com/legal/principles/civil-litigation |
| Employment Law in Gibraltar（直布罗陀劳动法） | https://www.gibcheck.com/legal/principles/employment-law |
| Public Law and Judicial Review（公法与司法审查） | https://www.gibcheck.com/legal/principles/public-law |
| **Sports Law in Gibraltar（直布罗陀体育法）** *（新增）* | https://www.gibcheck.com/legal/principles/sports-law |

即将推出：家庭法；刑法与刑事诉讼程序；直布罗陀的欧盟法律；海商法与海事法；遗嘱认证与遗产管理；公司与公司合规；国际法；司法协助。

*完整系列：https://www.gibcheck.com/legal/principles*

---

## 使用方法

### 作为系统提示词 / 上下文文件

在开始任何与直布罗陀相关的研究会话之前，复制 `Gibraltar Legal Regulatory Compliance OSINT skill.md` 的内容，并将其粘贴为 AI 助手中的系统提示词或上下文文档。

**建议指令：**

> 将随附的直布罗陀 OSINT 技能文件作为直布罗陀法律、法规和官方来源的主要参考。清楚区分本文件中的信息与其他来源。注明您发现的任何缺口。

### 与特定工具配合

| 工具 | 方法 |
|------|--------|
| **Claude（Projects）** | 添加为项目文档 — 在该项目的所有对话中持久生效 |
| **ChatGPT Custom GPTs** | 上传为知识库文件 |
| **Google Gemini** | 粘贴到系统指令中或上传为上下文 |
| **Harvey / Legora** | 上传为事项上下文文档 |

### 作为 llms.txt 参考

原始文件 URL：

```
https://raw.githubusercontent.com/Flipsta/Giblegal/main/Gibraltar%20Legal%20Regulatory%20Compliance%20OSINT%20skill.md
```

---

## API 与集成

本技能文件是一个更广泛的直布罗陀公共记录情报项目的对外公开层。

**GibCheck**（https://www.gibcheck.com）是在此工作背后构建的平台，目前处于私有测试阶段。它提供对直布罗陀官方公共数据集的统一检索、海事情报页面、航空情报页面、可检索的法律执业者目录，以及与实时记录接线的执业者法律参考。

如果您正在为直布罗陀法律或合规工作流构建 LLM 集成、RAG 流水线或工具，还有更多可以讨论。技能文件是开启该对话的敲门砖。

**联系我：**
- LinkedIn：https://www.linkedin.com/in/philipvasquez
- X / Twitter：@philipvasquez
- API 文档：https://www.gibcheck.com/api-docs

---

## 版本历史

| 版本 | 日期 | 变更 |
|---------|------|---------|
| 1.0 | 2026 年 6 月 | 初始发布 |
| 1.2 | 2026 年 6 月 | 扩展档案；直布罗陀—欧盟条约；OFT URL 已更正 |
| 1.3 | 2026 年 6 月 | 新增劳动法和公法与司法审查章节（文章现已在 GibCheck 上线）；为每个官方来源新增 GibCheck 平行链接；新增海事和航空页面 |
| 1.5 | 2026 年 6 月 | 新增直布罗陀公司术语表（company.gi，注明出处）；GCS 法院结构、陪审团服务、LPA 章节；UBO 登记簿转为免费 |
| 1.6 | 2026 年 6 月 | 新增《直布罗陀体育法》文章（GFA/FIFA/CAS、GRFU 橄榄球欧洲准入、治理框架）；新增直布罗陀出版机构目录；更新立法参考表 |

要接收更新通知：**Watch** 本仓库 → Custom → Releases。

---

## 贡献

欢迎就失效 URL、缺失来源或更正提交 Pull Request 和 Issue。大型 PR 之前请先开启 Issue。

---

## 许可与署名

依据 **[知识共享署名 4.0 国际版（CC BY 4.0）](https://creativecommons.org/licenses/by/4.0/)** 发布。

可自由用于任何目的（包括商业用途）的使用、分享和改编，须署名：

> *Gibraltar Legal, Regulatory & Compliance OSINT — Philip Vasquez LLB LLM（2026）。CC BY 4.0。https://github.com/Flipsta/Giblegal*

**作者：** Philip Vasquez LLB LLM
直布罗陀出庭律师 | 曾在英国一家专注欧盟私人公司信息数据的金融科技公司担任特别项目负责人 | 就诉讼融资和更广泛的法律技术政策发表过文章
LinkedIn：https://www.linkedin.com/in/philipvasquez

*本文件不构成法律意见。请始终对照官方原始来源进行核验。*
