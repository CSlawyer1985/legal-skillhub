# 国际武器贸易条例（ITAR）技能

> ⚠️ **免责声明：** 本技能基于 22 CFR 第 120-130 部分和既定的 DDTC 监管实践提供信息性指导。它不构成法律意见。ITAR 违规会带来严重的刑事和民事处罚。对涉及出口许可证申请、自愿披露、执法行动或复杂管辖确定的事项，请咨询合格的出口管制律师或您的授权官员（Empowered Official）。

---

## 1. 本技能做什么？

ITAR 合规技能将 Claude 转化为具备《国际武器贸易条例》（22 CFR 第 120-130 部分）深厚知识的美国国防出口管制专家顾问，该条例由美国国务院国防贸易管制局（DDTC）管理。本技能涵盖完整的 ITAR 合规生命周期——从确定物项是否受美国军需品清单（USML）管制，到管理违规行为的自愿自我披露。

本技能支持八个核心工作流：管辖确定（ITAR 与 EAR）、DDTC 注册指导、出口许可（DSP-5、DSP-73、DSP-94）、技术援助协议（TAA）和制造许可协议（MLA）的起草与审查、外籍人士的视同出口规则和技术控制计划（TCP）、22 CFR 第 129 部分下的军火经纪条例、22 CFR § 127.12 下的自愿自我披露（VSD）程序，以及包括授权官员角色在内的合规方案设计。

所有回答都引用与问题相关的具体 CFR 部分和章节（例如"22 CFR § 124.1"或"22 CFR § 120.41"）。输出格式随任务调整：差距评估用结构化分析表、注册和许可用分步检查清单、TAA/MLA 起草用逐条指导、一般问题用附 CFR 引用的清晰散文。

本技能由三份详细的参考文件支撑——全部 21 类 USML 类别描述、涵盖所有许可证类型和豁免的许可指南，以及包含完整 VSD 流程、处罚框架和 TCP 模板的合规方案参考——按需加载以保持回答精确高效。

---

## 2. 目标受众

| 受众                                   | 如何使用本技能                                                                |
| ------------------------------------------ | ------------------------------------------------------------------------------------- |
| **出口合规经理**             | 进行差距评估、起草 TCP、管理许可证组合、准备 VSD 申报   |
| **授权官员（EO）**              | 了解签署义务、管辖确定、DDTC 注册职责 |
| **国防制造商**                  | 对照 USML 对产品分类、确定注册要求、规划 TAA    |
| **法律顾问（出口管制）**         | 起草 TAA/MLA 条款、分析处罚敞口、就 VSD 策略提供意见               |
| **人力资源与安全团队**                  | 实施视同出口管制、筛查外籍人士、维护 TCP 程序   |
| **物流与运输团队**           | 出口前确认许可证有效性、了解豁免和记录保存      |
| **业务发展团队**             | 了解国际合作伙伴关系的 ITAR 影响以及 FMS 与 DCS 决策  |
| **初创企业和商业航天公司** | 确定两用和航天技术的 ITAR 与 EAR 管辖               |

---

## 3. 常见使用场景

### 管辖与分类

- "我们的军用级天线是受 ITAR 还是 EAR 管制？"
- "22 CFR § 120.41 下的特别设计测试是否适用于我们的复合材料？"
- "我如何向 DDTC 提交商品管辖（CJ）请求？"
- "哪个 USML 类别涵盖具备瞄准能力的无人机系统？"

### DDTC 注册

- "根据 22 CFR § 122.1，谁需要向 DDTC 注册？"
- "带我逐步走一遍 DS-2032 注册流程"
- "年度注册费是多少，如何续期？"
- "我们收购了一家新子公司——需要更新我们的 DDTC 注册吗？"

### 出口许可

- "硬件出口的 DSP-5 申请需要什么信息？"
- "何时可以用 DSP-73 代替 DSP-5？"
- "ITAR 出口许可证通常会附加什么条件？"
- "这笔转让是否符合 22 CFR § 126.5 下的加拿大豁免？"

### TAA 和 MLA 起草

- "起草一项涵盖再转让禁令的技术援助协议条款"
- "22 CFR § 124.9 要求的强制性 TAA 条款有哪些？"
- "MLA 与 TAA 有何不同，我何时需要每一种？"
- "我们的 TAA 范围已变化——DDTC 的修订流程是什么？"

### 视同出口和技术控制计划

- "一名外籍人士将需要接触我们的 ITAR 管制设计文件——我们需要什么？"
- "为一家拥有外籍员工雇员的国防制造商起草技术控制计划"
- "哪些国籍的人接触 USML 第八类技术数据需要视同出口许可证？"
- "根据 DDTC 指南，有效的 TCP 需要涵盖什么？"

### 合规方案和处罚

- "DDTC 在有效 ITAR 合规方案中寻找哪些要素？"
- "我们发现了未经许可的出口——自愿自我披露流程是什么？"
- "ITAR 违规的民事和刑事处罚是什么？"
- "为我们的年度内部审计起草一份 ITAR 合规检查清单"

---

## 4. 如何使用本技能

### 安装

1. 从本文件夹下载 `itar.skill`
2. 在 Claude 中，进入**设置 → 技能（Settings → Skills）**
3. 点击**上传技能（Upload Skill）**并选择 `itar.skill`
4. 该技能现在在所有 Claude 会话中生效

### 触发技能

当您提出 ITAR 或美国国防出口管制话题时，本技能自动激活。无需特殊命令。可触发本技能的自然语言短语示例：

- _"Is this item ITAR controlled?"_（这个物项受 ITAR 管制吗？）
- _"We need to share technical data with our UK partner"_（我们需要与英国合作伙伴共享技术数据）
- _"What does DDTC require for registration?"_（DDTC 注册要求什么？）
- _"Explain the deemed export rule"_（解释视同出口规则）
- _"We think we may have had an ITAR violation"_（我们认为我们可能发生了 ITAR 违规）
- _"Draft a TAA for our French licensee"_（为我们的法国被许可方起草 TAA）
- _"What is the USML category for night-vision devices?"_（夜视设备的 USML 类别是什么？）

### 示例提示词

```
We manufacture passive infrared sensors used in both commercial security cameras
and military targeting systems. How do we determine if these are ITAR-controlled,
and what is the process if the jurisdiction is unclear?
```
（我们制造用于商业安防摄像头和军事瞄准系统的被动红外传感器。我们如何确定这些是否受 ITAR 管制，如果管辖不明确，流程是什么？）

```
Our company has just won a contract to provide engineering support to a foreign
military customer. We plan to share design drawings and provide on-site training.
What ITAR authorisation do we need, and how long does it take to obtain?
```
（我们公司刚刚赢得了一份为外国军事客户提供工程支持的合同。我们计划共享设计图纸并提供现场培训。我们需要什么 ITAR 授权，获得它需要多长时间？）

```
One of our engineers, a citizen of Germany, needs access to ITAR-controlled
technical data for a project. Walk me through our deemed export obligations and
what our Technology Control Plan needs to cover.
```
（我们的一名德国籍工程师需要一个项目的 ITAR 管制技术数据接触权限。带我走一遍我们的视同出口义务以及我们的技术控制计划需要涵盖什么。）

```
We discovered that one of our subsidiaries shipped ITAR hardware to a distributor
in Singapore without a DSP-5 licence. What is the voluntary self-disclosure
process and what factors will DDTC consider when determining the penalty?
```
（我们发现我们的一家子公司在没有 DSP-5 许可证的情况下向新加坡的一家分销商发运了 ITAR 硬件。自愿自我披露流程是什么，DDTC 在确定处罚时会考虑哪些因素？）

```
Conduct an ITAR compliance gap assessment against these programme elements:
registration, TCP, training, screening, licence management, record retention,
and internal audits. Format the output as a table with status and recommended actions.
```
（对照以下方案要素进行 ITAR 合规差距评估：注册、TCP、培训、筛查、许可证管理、记录保存和内部审计。以表格格式输出，含状态和建议行动。）

---

## 5. 技能实现细节

### 架构

```
plugins/itar/
└── skills/
    └── itar/
        ├── SKILL.md                        # 核心技能——8 个工作流定义、监管
        │                                   #   结构、回应格式规则、CFR 引用
        └── references/
            ├── usml-categories.md          # 全部 21 类 USML 类别及关键物项、示例、
            │                               #   管辖提示和关键 ITAR 定义
            ├── licensing-guide.md          # 许可证类型（DSP-5/73/94/61、TAA、MLA）、
            │                               #   申请要求、豁免、
            │                               #   FMS 与 DCS 比较、记录保存规则
            └── compliance-program.md       # 合规方案要素、TCP 模板、
                                            #   处罚框架、VSD 流程（4 步）、
                                            #   DDTC 蓝灯（Blue Lantern）计划、审计检查清单
```

### SKILL.md 中的内容

- 专家角色定义：具备 22 CFR 第 120-130 部分知识的 ITAR 合规顾问
- 将任务类型映射到输出格式的回应格式表（管辖分析、注册、许可、TAA/MLA、差距评估、VSD、问答）
- 监管结构概览：全部 10 个 CFR 部分（120-130）及标题和关键内容
- 8 个详细的核心工作流，附逐步指导和 CFR 引用
- 受禁运和受限制国家清单（22 CFR § 126.1）
- 参考文件加载说明

### 参考文件中的内容

| 文件                               | 内容                                                                                                                                                                                                                                                                                                                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `references/usml-categories.md`    | 全部 21 类 USML 类别（I-XXI）及物项描述、关键定义（防务物项 § 120.31、防务服务 § 120.32、技术数据 § 120.33、特别设计 § 120.41）、USML 与 CCL 管辖判定提示、商品管辖流程                                                                                                         |
| `references/licensing-guide.md`    | 所有许可证/协议类型及 CFR 引用和使用场景；DSP-5 申请模块和处理时间；DSP-73 条件；强制性 TAA 条款（§ 124.9）；MLA 与 TAA 比较；选定豁免（§§ 126.4、126.5、126.7、125.4）；FMS 与 DCS 比较；5 年记录保存要求（§ 122.5）                                                |
| `references/compliance-program.md` | 7 项合规方案要素（含授权官员角色）；TCP 模板（10 个部分）；当事方筛查要求（DDTC、OFAC、BIS 清单）；民事处罚（每次违规 1,369,000 美元）、刑事处罚（100 万美元罚款、20 年监禁）；4 步 VSD 流程；减轻和加重因素；DDTC 蓝灯最终用途监控；合规就绪检查清单 |

### 用于构建技能的输入

| 输入                    | 详情                                                        |
| ------------------------ | ------------------------------------------------------------- |
| 主要法规       | 22 CFR 第 120-130 部分（ITAR）                                   |
| 管理机构 | DDTC，美国国务院                                  |
| USML                     | 22 CFR § 121.1 —— 全部 21 类                            |
| 许可 CFR 部分      | 第 123 部分（硬件）、第 124 部分（TAA/MLA）、第 125 部分（技术数据）     |
| 处罚权限        | 22 USC § 2778；22 CFR 第 127 部分                                |
| VSD 框架            | 22 CFR § 127.12                                               |
| 军火经纪规则          | 22 CFR 第 129 部分                                               |
| 注册             | 22 CFR 第 122 部分；DS-2032                                      |
| 视同出口           | 22 CFR § 120.50；§ 120.62（美国人）                        |
| 条约框架        | 澳大利亚、英国、加拿大防务贸易合作条约      |
| 相关制度          | 《出口管理条例》（EAR），15 CFR 第 730-774 部分 |

### 技能触发短语

`ITAR`、`International Traffic in Arms`（国际武器贸易）、`USML`、`United States Munitions List`（美国军需品清单）、`DDTC`、
`DSP-5`、`DSP-73`、`TAA`、`Technical Assistance Agreement`（技术援助协议）、`MLA`、`Manufacturing License Agreement`（制造许可协议）、
`defense article`（防务物项）、`defense service`（防务服务）、`technical data export`（技术数据出口）、`deemed export`（视同出口）、`foreign national access`（外籍人士接触）、
`Commodity Jurisdiction`（商品管辖）、`CJ determination`（CJ 确定）、`ITAR registration`（ITAR 注册）、`export control`（出口管制）、
`22 CFR`、`voluntary self-disclosure`（自愿自我披露）、`Technology Control Plan`（技术控制计划）、`TCP`、`Empowered Official`（授权官员）、
`brokering regulations`（军火经纪条例）、`ITAR vs EAR`、`USML category`（USML 类别）、`Part 129`（第 129 部分）、`DDTC registration`（DDTC 注册）

---

## 6. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)

技能版本：1.6.2 —— 2026 年 7 月
