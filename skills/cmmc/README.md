# CMMC 2.0 Skill

> **免责声明：** 本 skill 基于 32 CFR Part 170、NIST SP 800-171 Rev 2 及相关 DFARS 条款，就 CMMC 2.0 要求提供信息性指引。它不构成法律意见，也不替代与注册执业机构（RPO）或经认证的第三方评估机构（C3PAO）的接洽。CMMC 认证决定、SPRS 分数提交和 DIBCAC 评估答复涉及重大的法律和合同义务——高风险合规事项请咨询合格的 CMMC 专业人士。

---

## 1. 该 Skill 做什么？

本 skill 将 Claude 转变为专家级 **CMMC 2.0 注册执业人员和 NIST SP 800-171 实施顾问**，为国防承包商、分包商及其 IT 和合规团队提供覆盖完整 CMMC 2.0 合规生命周期的深入、结构化指引。它涵盖最终 CMMC 2.0 规则（**32 CFR Part 170**，2024 年 12 月生效）及所有配套监管文件：**NIST SP 800-171 Rev 2**、**NIST SP 800-172** 以及 **DFARS 条款 252.204-7012/7019/7020/7021**。

该 skill 精准处理 CMMC 的三级框架，区分**第 1 级**要求的 17 项实践（FCI 保护，FAR 52.204-21 自评估）、**第 2 级**要求的 110 项实践（CUI 保护，NIST SP 800-171，非关键项目为三年期 C3PAO 评估或自评估），以及**第 3 级**的强化要求（APT 抵御，NIST SP 800-172 实践，DIBCAC 政府评估）。建议始终限定于适用级别和合同中具体的 DFARS 条款。

核心能力之一是 **SPRS 分数计算**——该 skill 逐步讲解供应商绩效风险系统（SPRS）评分方法，从 110 分起步，对每项未达标（NOT MET）实践应用逐项扣分，得出带整改优先级的估算分数。它还支持**系统安全计划（SSP）起草**，生成完全结构化的 SSP 部分，包含实践编号、要求陈述、实施描述、责任角色、关联系统和证据工件——正是 C3PAO 和 DIBCAC 评估员所期望的格式。

该 skill 还密切关注国防工业基础（DIB）中最常见的合规陷阱：使评估负担膨胀的范围蔓延、CUI 未向分包商传递、非 FIPS 验证的加密、MFA 缺口（最常失败的实践——IA.L2-3.5.3）、DIBNET 事件报告时限，以及在 CUI 中使用非 FedRAMP 云服务。它在每次评估中主动揭示这些问题。

---

## 2. 目标受众

| 受众 | 使用方式 |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **国防承包商（总包）** | 级别确定、差距评估、SSP 起草、SPRS 分数计算、传递义务管理 |
| **国防分包商** | 理解 DFARS 7021 传递要求、第 1/2 级就绪、CUI 处理范围界定 |
| **IT 和安全团队（DIB）** | 全部 110 项 NIST SP 800-171 要求的实践级实施指引 |
| **合规经理** | POA&M 编制、整改路线图、审计准备、C3PAO 接洽就绪 |
| **合同和法律团队** | DFARS 条款识别、分包商传递语言、FCI 与 CUI 范围分析 |
| **RPO 和 CMMC 顾问** | 差距评估框架、SSP 模板、客户评估工具 |
| **CISO 和风险官** | SPRS 分数管理、风险优先级排序、国防部合同网络安全战略 |
| **云和基础设施团队** | CUI 的 FedRAMP 授权要求、FIPS 140-2/3 验证、飞地设计 |

---

## 3. 常见用例

### 级别确定和合同范围界定

- _"我们刚收到一份新的国防部 RFP。DFARS 252.204-7021 要求我们达到哪个 CMMC 级别？"_
- _"DFARS 7019 项下的自评估与 DFARS 7021 项下的 C3PAO 评估有什么区别？"_
- _"我们同时处理 FCI 和 CUI。我们需要第 1 级、第 2 级还是第 3 级？"_
- _"我们的总包商将 CMMC 第 2 级传递给我们。这要求我们做什么？"_

### 差距评估

- _"对我们的情况进行一次 CMMC 2.0 第 2 级差距评估。我们有 Active Directory、仅在邮件上启用 MFA、无正式 SSP，并将 CUI 存储在共享驱动器上。"_
- _"对照第 2 级要求评估我们的访问控制（AC）域实践。"_
- _"如果今天评估，110 项实践中我们最可能失败的是哪些？"_
- _"IG1 覆盖的组织开始准备 CMMC 时最常遗漏哪些实践？"_

### SSP 起草

- _"起草 AC.L2-3.1.3（控制 CUI 流向外部系统）的 SSP 条目。"_
- _"为我们在 AWS 托管的 CUI 环境撰写 SSP 的系统边界描述部分。"_
- _"为所有识别与认证（IA）域实践生成 SSP 条目。"_
- _"审查我们 IA.L2-3.5.3（MFA）的 SSP 条目——它符合文档标准吗？"_

### SPRS 分数计算

- _"计算我们的估算 SPRS 分数。我们有 15 项实践 NOT MET 和 8 项 PARTIAL。"_
- _"哪些 NOT MET 实践的扣分最高？我们应优先整改哪些？"_
- _"我们当前的 SPRS 分数是 -47。6 个月内达到 +80 的现实整改路径是什么？"_

### POA&M 管理

- _"为我们的 12 项 NOT MET 第 2 级实践创建 POA&M，含里程碑和负责人。"_
- _"哪些 POA&M 项目在 CMMC 2.0 规则下要求加快时限？"_
- _"带着未关闭的 POA&M 项目能否获得有条件认证？哪些实践符合条件？"_

### CUI 范围界定和第三方云

- _"我们如何定义 CUI 资产边界？哪些在范围内、哪些在范围外？"_
- _"我们使用 Microsoft 365 Government（GCC High）处理 CUI。这满足 DFARS 7012 吗？"_
- _"我们的云存储提供商已获 FedRAMP Moderate 授权。这覆盖我们的 CUI 处理吗？"_
- _"我们使用 Slack 和 Google Workspace。CUI 可以通过这些系统流动吗？"_

---

## 4. 如何使用该 Skill

### 安装

1. 从本文件夹下载 `cmmc.skill` 文件
2. 在 Claude 中，前往**设置 → 技能**
3. 点击**上传技能**并选择 `cmmc.skill`
4. 该技能在您的 Claude 会话中立即可用

### 触发该 Skill

当您的消息与 CMMC 2.0 或其支撑的监管文件相关时，该技能自动激活。触发示例短语：

- _"CMMC gap assessment"_
- _"CMMC Level 2 readiness"_
- _"NIST SP 800-171 practices"_
- _"CUI protection requirements"_
- _"SPRS score calculation"_
- _"System Security Plan for CMMC"_
- _"DFARS 252.204-7021 compliance"_
- _"C3PAO assessment preparation"_
- _"FCI protection requirements"_
- _"DIBCAC audit readiness"_

### 示例提示

```
"我们是一家 75 人的国防分包商。我们依据一份含 DFARS 252.204-7021 的
国防部合同处理 CUI。我们从未做过 CMMC 评估。带我逐步确定我们的
第 2 级就绪状态，并为全部 17 个 CMMC 域生成差距评估表。"
```

```
"计算我们的估算 SPRS 分数。以下 110 项实践的状态为：
[MET/PARTIAL/NOT MET 列表]。确定使 SPRS 分数提升最大化的
10 项最高价值整改行动。"
```

```
"为以下实践起草完整的 SSP 部分：AC.L2-3.1.1、
AC.L2-3.1.2、AC.L2-3.1.3。我们的环境是本地 Windows
Server AD 域，含 40 台处理 CUI 的工作站。"
```

```
"我们使用 AWS GovCloud 存储 CUI。这对 DFARS 7012
合规足够吗？需要哪些具体的 AWS 服务和配置？"
```

```
"我们的总包商告知我们，他们将 CMMC 第 2 级传递给我们，
因为我们作为分包商处理 CUI 设计文件。这对我们的
时间表、评估类型和合同义务意味着什么？起草我们应在
分包合同中预期的传递条款。"
```

---

## 5. Skill 实现细节

### 架构

```
cmmc/
├── SKILL.md                      # 核心技能——3 个 CMMC 级别、17 个域、5 个核心
│                                 #   工作流、关键监管引用、常见陷阱
└── references/
    ├── cmmc-practices.md         # 全部 110 项 NIST SP 800-171 实践，映射到 CMMC
    │                             #   域和级别，含实践文本
    ├── cmmc-levels.md            # 第 1/2/3 级比较、评估类型、时间表、
    │                             #   传递规则、自评估与 C3PAO 与 DIBCAC
    └── cmmc-assessment.md        # SPRS 评分方法、C3PAO 评估流程、
                                  #   POA&M 规则、有条件认证、DIBCAC 指引
```

**总计：** 4 个文件约 625 行（SKILL.md + 3 个参考文件）

### SKILL.md 的内容

- **三级框架**——第 1 级（17 项 FCI 实践）、第 2 级（110 项 CUI 实践）、第 3 级（110+ 项 APT 实践），含评估类型
- **17 个 CMMC 域**——所有域缩写和全名
- **五个核心工作流**——差距评估、SSP 起草、SPRS 分数计算、POA&M 管理和 CUI 范围界定
- **关键监管引用表**——从 32 CFR Part 170 到 FAR 52.204-21 的 9 份文件及相关性描述
- **常见陷阱**——范围蔓延、传递缺失、FIPS 验证、MFA 缺口、事件报告、云中 CUI
- **输出格式路由**——6 种任务类型及特定输出格式规范

### 参考文件的内容

| 文件 | 内容 |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cmmc-practices.md` | 全部 110 项 NIST SP 800-171 Rev 2 实践，含实践编号、域、实践陈述和 CMMC 级别分配；第 1 级实践（FAR 52.204-21）单独列出 |
| `cmmc-levels.md` | 第 1/2/3 级深度比较：要求实践、评估类型（自评/C3PAO/DIBCAC）、评估时间表、SPRS 提交要求、对分包商的传递义务、关键 DFARS 条款映射 |
| `cmmc-assessment.md` | SPRS 评分方法及逐项权重表；C3PAO 评估流程各阶段；POA&M 要求及有条件认证的合格实践；第 3 级的 DIBCAC 评估流程 |

### 用于构建该 skill 的输入

| 输入 | 描述 |
| ------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **32 CFR Part 170** | CMMC 2.0 最终规则（2024 年 12 月生效）——权威监管文本 |
| **NIST SP 800-171 Rev 2** | 构成第 2 级实践集的全部 110 项 CUI 保护要求 |
| **NIST SP 800-172** | 第 3 级 APT 抵御的强化安全要求 |
| **DFARS 252.204-7012/7019/7020/7021** | 管辖 CUI 保护、自评估、SPRS 提交和 CMMC 传递的 DFARS 条款 |
| **FAR 52.204-21** | FCI 的基本保护要求（第 1 级基础） |
| **DoD CMMC 评估指南** | 国防部发布的第 1、2、3 级评估方法 |
| **SPRS 方法指引** | 国防部评分表和逐项扣分权重 |
| **DoD CUI 登记册** | 范围界定工作流中引用的权威 CUI 类别清单 |

### Skill 触发短语

`CMMC`、`CMMC 2.0`、`Cybersecurity Maturity Model Certification`、`CMMC Level 1`、`CMMC Level 2`、`CMMC Level 3`、`NIST SP 800-171`、`NIST 800-171`、`CUI`、`Controlled Unclassified Information`、`FCI`、`Federal Contract Information`、`SPRS score`、`System Security Plan`、`SSP`、`POA&M`、`C3PAO`、`DIBCAC`、`DFARS 7012`、`DFARS 7021`、`defense contractor cybersecurity`、`DIB`、`Defense Industrial Base`、`CMMC gap assessment`、`CMMC readiness`、`CUI scoping`、`FedRAMP CUI`

---

## 6. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)

Skill 版本：1.6.2——2026 年 7 月
