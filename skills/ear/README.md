# 出口管理条例（EAR）技能

> **免责声明：** 本技能基于由美国商务部产业与安全局（BIS）管理的 15 CFR 第 730-774 部分提供信息性指导。它不构成法律意见或正式的出口管制分类。具有重大合规后果的 ECCN 认定、许可证要求分析和受限方筛查决定，应由合格的出口管制律师或持照出口合规专业人员审查。本技能不涉及 ITAR（22 CFR 第 120-130 部分）——如果您的物项可能受 ITAR 管辖，请向 DDTC 提交商品管辖（CJ）请求。

---

## 1. 本技能做什么？

本技能赋予 Claude 在**《出口管理条例》（EAR）**——15 CFR 第 730-774 部分——方面的全面专业知识，该条例由美国商务部产业与安全局（BIS）依据《2018 年出口管制改革法》（ECRA，50 U.S.C. § 4801 起）授权管理。EAR 管辖两用物项——商品、软件和技术（非由美国另一机构独家管控者）的出口、再出口和境内转移。

本技能实施完整的八步 EAR 合规工作流：管辖确定（EAR 与 ITAR 的审查顺序）、涵盖全部 10 个 CCL 类别（0-9）和 5 个产品组（A-E）的 ECCN 分类、通过第 738 部分商业国家图表的许可证要求分析、涵盖全部 14 项许可证例外（LVS、GBS、CIV、TMP、RPL、GOV、TSU、ENC、TSR、APP、BAG、AVS、ACE、GFT）的许可证例外评估、第 744 部分下的最终用户和最终用途管制（含全部五份受限方清单）、§ 736.2(b)(3) 下的外国直接产品规则（FDPR）、§ 734.13 下的视同出口规则、§ 734.4 下的最低含量（de minimis）阈值、第 748 部分下的 SNAP-R 许可证申请、第 762 部分下的记录保存，以及涵盖有效合规方案全部七项要素的出口合规方案（ECP）设计。

每项回应都引用具体的部分和章节（如"§ 740.17"、"15 CFR § 736.2(b)(1)"）。本技能严格区分"出口"、"再出口"和"（境内）转移"（依 §§ 734.14-734.16），并在任何分类分析之前适用正确的审查顺序。它涵盖第 764 部分下的完整执法制度，包括民事和刑事处罚、自愿自我披露（VSD）程序以及处罚减轻因素。

本技能面向出口商、制造商、科技公司、大学和研究机构、货运代理以及合规专业人员，为其提供结构化的分类分析、受限方筛查指导、许可证例外适用性审查、FDPR 影响评估和 ECP 差距分析——全部附精确的法规引用。

---

## 2. 目标受众

| 角色                                  | 如何使用本技能                                                                         |
| ------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 出口管制经理               | ECCN 分类、许可证要求分析、ECP 差距审查、VSD 准备            |
| 贸易合规团队                | 受限方筛查指导、交易红旗审查、国家图表分析       |
| 法律顾问                         | 法律意见的法规引用、FDPR 范围分析、处罚敞口评估      |
| 科技公司                  | 外籍雇员的视同出口分析、软件/技术 ECCN 分类 |
| 半导体与国防制造商 | 先进芯片 FDPR（实体清单 FDPR）、第 3 类分类、CCL 0-9 分析             |
| 大学科研办公室           | 基础研究排除、视同出口合规、出版管制                 |
| 货运代理与物流        | EEI 申报义务（第 758 部分）、许可证文件、托运人指示函      |
| 合规审计师                   | 七要素 ECP 评估、记录保存审计（第 762 部分）、培训计划审查            |

---

## 3. 常见使用场景

### ECCN 分类

- "对这款带 AES-256 加密的网络安全设备进行分类——它的 ECCN 是什么？"
- "我们的机器学习加速器芯片是归入 3A090 还是其他 ECCN？"
- "我们出口生物试剂。CCL 第 1 类中哪些 ECCN 可能适用？"
- "我们的软件执行信号处理。带我走一遍将其归入 CCL 第 5 类的流程。"
- "这个物项不在 CCL 上。我们能确认它是 EAR99 以及仍有哪些限制适用吗？"

### 管辖确定（EAR 与 ITAR）

- "这个卫星组件受 EAR 还是 ITAR 管辖？我如何适用审查顺序？"
- "我们的产品是从一个已被 CJ 转至 EAR 的 USML 物项设计的。我们的分类是什么？"
- "我何时应分别向 BIS 提交 CCATS 请求、向 DDTC 提交 CJ 请求？"

### 许可证要求分析

- "我们向中国出口 3A001 电子产品。国家图表怎么说，我们需要许可证吗？"
- "在当前 E:2 管制下，我们能对向俄罗斯的加密软件出口使用 ENC 许可证例外吗？"
- "对发往 D:1 国家组的 NS 管制物项，有哪些许可证例外可用？"
- "TMP 许可证例外是否涵盖我们送往印度参加展会的设备？"
- "带我走一遍对阿联酋 5E002 技术出口的国家图表检查。"

### 受限方筛查

- "我们的客户出现在实体清单上。适用什么许可证要求，有无任何例外可用？"
- "被拒人员清单、实体清单和未验证清单之间有什么区别？"
- "当中间收货人出现在 MEU 清单上时，我们如何处理交易？"
- "描述我们应该培训销售团队的 § 732.6 红旗指标。"
- "我们如何进行合规的最终用途检查，何时必须取得最终用途证书？"

### 外国直接产品规则（FDPR）

- "如果我们外国制造的芯片是用美国设备制造的，实体清单 FDPR 是否适用？"
- "我们使用美国原产 EDA 软件在美国境外生产半导体。一般 FDPR 是否适用？"
- "解释 2022 年先进计算 FDPR 及其如何影响我们面向中国的产品线。"

### 视同出口

- "我们正在聘用一名中国工程师来从事我们的 3E001 技术工作。我们需要视同出口许可证吗？"
- "根据 § 734.13，什么算作向外籍人士'释放'技术？"
- "视同再出口与视同出口有何不同，何时适用？"

### 出口合规方案

- "按七要素框架审查我们的 ECP。我们有书面政策但没有培训记录。"
- "为我们的采购团队起草一份受限方筛查政策。"
- "我们发现了潜在的违规行为。带我们走一遍自愿自我披露（VSD）流程。"
- "根据第 762 部分，我们必须保留哪些记录，保留多长时间？"

---

## 4. 如何使用本技能

### 安装

1. 从本文件夹下载 `ear.skill`。
2. 在 Claude 中，进入**设置 → 技能（Settings → Skills）**。
3. 点击**上传技能（Upload Skill）**并选择 `ear.skill`。
4. 该技能现在在您的所有 Claude 会话中生效。

### 触发技能

当 EAR 相关话题出现时，本技能自动激活。无需特殊命令。可触发它的示例短语：

- _"ECCN classification"_（ECCN 分类）或 _"Commerce Control List"_（商业管制清单）
- _"EAR99 determination"_（EAR99 认定）或 _"dual-use export"_（两用出口）
- _"BIS licence"_（BIS 许可证）、_"licence exception ENC"_（ENC 许可证例外）、_"SNAP-R application"_（SNAP-R 申请）
- _"Entity List"_（实体清单）、_"denied party screening"_（被拒方筛查）、_"Unverified List"_（未验证清单）
- _"Foreign Direct Product Rule"_（外国直接产品规则）或 _"deemed export"_（视同出口）
- _"15 CFR Part 740"_、_"Country Chart"_（国家图表）、_"Order of Review"_（审查顺序）
- _"export compliance programme"_（出口合规方案）、_"voluntary self-disclosure"_（自愿自我披露）

### 示例提示词

```
Classify the following item under the EAR. It is a commercial network router with integrated
AES-256 and RSA-2048 encryption, capable of 100Gbps throughput. We sell it to commercial
ISPs globally. Start with the Order of Review, determine ECCN or EAR99, and identify
any licence requirements for exports to China, India, and UAE.
```
（按 EAR 对以下物项分类。它是一款集成 AES-256 和 RSA-2048 加密、支持 100Gbps 吞吐量的商用网络路由器。我们向全球商业 ISP 销售它。从审查顺序开始，确定 ECCN 或 EAR99，并识别向中国、印度和阿联酋出口的任何许可证要求。）

```
We are a semiconductor company. We manufacture chips outside the US using US-origin EDA
tools (Category 3E001 technology) and equipment (3B001). Our chips are designed to support
advanced AI training workloads. Analyse our FDPR exposure — both General FDPR and
Entity List FDPR — if we have customers on the Entity List.
```
（我们是一家半导体公司。我们使用美国原产 EDA 工具（第 3 类 3E001 技术）和设备（3B001）在美国境外制造芯片。我们的芯片设计用于支持先进的 AI 训练工作负载。如果我们有客户在实体清单上，分析我们的 FDPR 敞口——包括一般 FDPR 和实体清单 FDPR。）

```
We've discovered that our sales team shipped 5E002 encryption technology to a distributor
in the UAE without obtaining a licence. The distributor then reexported to Iran.
Walk us through our voluntary self-disclosure obligations, the factors BIS considers
in penalty mitigation (§ 764.5), and the steps to prepare the VSD package.
```
（我们发现销售团队在未取得许可证的情况下将 5E002 加密技术发运给阿联酋的一家分销商。该分销商随后再出口到伊朗。带我们走一遍自愿自我披露义务、BIS 在处罚减轻中考虑的因素（§ 764.5），以及准备 VSD 材料的步骤。）

```
We are hiring 12 foreign nationals (7 Chinese nationals, 3 Indian nationals, 2 Russian
nationals) to work in our R&D division on projects involving 3E001 military electronics
technology and 4E001 computer technology. Conduct a deemed export analysis and identify
which hires require a BIS licence before we allow access to controlled technology.
```
（我们将聘用 12 名外籍人士（7 名中国籍、3 名印度籍、2 名俄罗斯籍）在我们的研发部门从事涉及 3E001 军用电子技术和 4E001 计算机技术的项目。进行视同出口分析，并确定在我们允许其接触受管制技术之前，哪些聘用需要 BIS 许可证。）

```
Perform a gap analysis of our Export Compliance Programme against the seven-element
BIS framework. We have: a written export compliance policy, a designated EMPOC, and
a Consolidated Screening List integration in our ERP. We do not have: a formal training
programme, a recordkeeping procedure, an audit schedule, or a VSD procedure.
```
（对我们的出口合规方案对照 BIS 七要素框架进行差距分析。我们已有：书面出口合规政策、指定的 EMPOC，以及 ERP 中的综合筛查清单集成。我们没有：正式培训计划、记录保存程序、审计安排或 VSD 程序。）

---

## 5. 技能实现细节

### 架构

```
ear/
├── SKILL.md                          # 核心技能——8 步 EAR 工作流、全部 CCL 类别、
│                                     #   国家组、许可证例外概览、
│                                     #   受限方清单、FDPR、视同出口、
│                                     #   第 748 部分许可、第 762 部分记录保存
└── references/
    ├── license-exceptions.md         # 全部 14 项许可证例外（LVS 至 GFT）的完整
    │                                 #   条件、限制和记录保存要求
    ├── ccl-eccn-guide.md             # 详细的 ECCN 查询方法论、全部 10 个 CCL
    │                                 #   类别及关键 ECCN、商业国家图表
    │                                 #   用法，以及管辖确定指导
    └── compliance-program.md         # ECP 设计（7 要素）、执法制度
                                      #   （民事/刑事处罚）、VSD 流程、
                                      #   FDPR 深入探讨、视同出口合规、
                                      #   以及 BIS 处罚指南
```

### SKILL.md 中的内容

- **身份和范围**：面向 BIS/15 CFR 第 730-774 部分的专家型 EAR 合规顾问角色
- **回应格式表**：按任务区分的输出格式——ECCN 分类、许可证分析、筛查、ECP 审查、一般问题
- **EAR 框架概览**：BIS 权限、ECRA 引用、全部 15 CFR 部分编号及主题
- **第 1 步——管辖确定**：ITAR 审查顺序、CJ 请求、CCATS 请求
- **第 2 步——ECCN 分类**：ECCN 格式、全部 10 个 CCL 类别、5 个产品组、管制理由、EAR99 认定
- **第 3 步——许可证要求分析**：国家图表机制、国家组（A:1-E:2）
- **第 4 步——许可证例外概览**：全部 14 项例外及其符号、名称和范围
- **第 5 步——最终用户/最终用途管制**：全部 5 份受限方清单、CSL、大规模杀伤性武器禁令、红旗指标
- **第 6 步——特别专题**：视同出口、FDPR（一般和实体清单）、最低含量规则、美国人管制
- **第 7 步——许可（第 748 部分）**：SNAP-R 门户、BIS-748P、审查时限、咨询意见
- **第 8 步——记录保存（第 762 部分）**：5 年保留要求和记录类型

### 参考文件中的内容

| 文件                    | 内容                                                                                                                                                                                                                                                                                                                               |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `license-exceptions.md` | 全部 14 项许可证例外的完整条件、资格标准、限制、通知/报告要求和记录保存义务：LVS、GBS、CIV、APP、TSR、TMP、RPL、GOV、TSU、ENC、BAG、AVS、ACE、GFT                                                                                                        |
| `ccl-eccn-guide.md`     | ECCN 查询方法论；全部 10 个 CCL 类别的详细覆盖及代表性 ECCN；商业国家图表使用逐步说明；ITAR/EAR 审查顺序决策树的管辖确定；CCATS 和 CJ 请求流程                                                                                          |
| `compliance-program.md` | 七要素 ECP 设计框架；BIS 民事处罚指南（每次违规最高 130 万美元）和刑事处罚（最高 20 年）；VSD 流程和减轻因素；FDPR 深入探讨（一般 FDPR、华为 FDPR、2022-2023 年先进芯片管制）；视同出口和视同再出口合规程序；BIS 审计准备 |

### 用于构建技能的输入

| 来源                                                          | 描述                                                                |
| --------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 15 CFR 第 730-774 部分（EAR）                                      | 完整法规文本——包括 CCL（第 774 部分补充第 1 号）在内的全部部分 |
| 《2018 年出口管制改革法》（ECRA）                        | 法定权限，50 U.S.C. § 4801 起                              |
| BIS 商业国家图表                                      | 第 738 部分补充第 1 号——许可证要求矩阵                     |
| BIS 实体清单、被拒人员清单、未验证清单、MEU 清单 | 现行受限方清单（第 744 部分补充第 4、6、7 号）           |
| BIS 红旗指标（§ 732.6）                               | 关于可疑交易指标的已发布指导                    |
| OFAC SDN 清单                                                   | 并行的 OFAC 筛查要求                                        |
| BIS 行政执行令                           | 第 766 部分下的处罚指导和 VSD 先例                         |

### 技能触发短语

`EAR compliance`（EAR 合规）、`Export Administration Regulations`（出口管理条例）、`ECCN classification`（ECCN 分类）、`Commerce Control List`（商业管制清单）、
`CCL category`（CCL 类别）、`EAR99`、`BIS licence`（BIS 许可证）、`Bureau of Industry and Security`（产业与安全局）、`dual-use export`（两用出口）、
`licence exception ENC`（ENC 许可证例外）、`licence exception TMP`（TMP 许可证例外）、`SNAP-R application`（SNAP-R 申请）、`Form BIS-748P`（BIS-748P 表格）、
`Entity List`（实体清单）、`Denied Persons List`（被拒人员清单）、`Unverified List`（未验证清单）、`Military End-User List`（军事最终用户清单）、
`Consolidated Screening List`（综合筛查清单）、`Foreign Direct Product Rule`（外国直接产品规则）、`FDPR`、`deemed export`（视同出口）、
`deemed reexport`（视同再出口）、`§ 734.13`、`de minimis rule`（最低含量规则）、`Country Chart`（国家图表）、`Order of Review`（审查顺序）、
`ITAR vs EAR`、`Commodity Jurisdiction`（商品管辖）、`CCATS`、`export compliance programme`（出口合规方案）、
`voluntary self-disclosure`（自愿自我披露）、`Part 762 recordkeeping`（第 762 部分记录保存）、`EAR red flags`（EAR 红旗）

---

## 6. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)

技能版本：1.6.2 —— 2026 年 7 月
