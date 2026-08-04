---
name: "eu-ai-act-high-risk-classifier-oliver-schmidt-prietz"
description: "对 AI 系统在欧盟 AI 法案第 6 条下是否属于高风险的深度评估，以委员会的 Art. 6(5) 分类指南草案（一般原则 + 附件 I + 附件 III）为依据。覆盖附件 I 产品安全路径、全部八个附件 III 领域及工作示例、Art. 6(3) 例外及其个人画像再例外，以及 Art. 25 准提供者陷阱。输出结构化决策块、实务备忘录和 JSON 交换工件。"
metadata:
  author: "Oliver Schmidt-Prietz"
  license: "agpl-3.0"
  version: "2026-06-09"
---

# 欧盟 AI 法案高风险分类

对 AI 系统在 **AI 法案第 6 条**（条例 (EU) 2024/1689）下是否属于**高风险**的深度评估，以欧盟委员会 2026 年发布供利益相关方咨询的 Art. 6(5) 分类指南草案（一般原则、附件 I、附件 III）为依据。

## 免责声明（会话开始时展示，不阻止）

> **重要：**本技能提供基于欧盟 AI 法案（条例 (EU) 2024/1689）和委员会发布供利益相关方咨询的 Art. 6(5) 分类指南草案（一般原则、附件 I、附件 III）的结构化高风险分类指导。委员会指南无约束力；权威解释属于欧盟法院。这不是法律意见。最终分类决定应涉及具备 AI 法案专业知识的合格法律顾问。

---

## 何时使用本技能

- 用户已得出结论（通过宽泛风险层级分流或其他方式）高风险是可能层级，需要**深度评估**。
- 高风险裁决影响重大（FRIA 可能适用、第三章合格评定制度、上市后监控、欧盟数据库注册）。
- 用户明确要求附件 I 或附件 III 分析。
- 用户不确定边缘 AI 系统是否属于高风险，需要以委员会指南为依据的推理。

如果 AI 系统尚未跨全部五个风险层级（禁止 / 高风险 / GPAI / 有限 / 最小）分流，先做该广度优先分流，再进行下文的附件 I / 附件 III 深度分析。对不带分类裁决的纯条款查询问题，直接用引用的法规文本回答，而非运行完整深度评估。

---

## 生效日期（按 AI Omnibus 2026）

| 规定 | 原日期（第 113 条） | **推迟日期（AI Omnibus）** |
|-----------|--------------------------|----------------------------------|
| Art. 6(2) + 附件 III 义务 | 2026 年 8 月 2 日 | **2027 年 12 月 2 日** |
| Art. 6(1) + 附件 I 义务 | 2027 年 8 月 2 日 | **2028 年 8 月 2 日** |
| 第 111(2) 条遗留截止 | 2026 年 8 月 2 日 | **2027 年 12 月 2 日** |

引用链见 [references/ai-omnibus-timeline-postponements.md](references/ai-omnibus-timeline-postponements.md)。

---

## 所需输入

开始前，向用户收集：

1. **系统描述** —— 它做什么、谁构建了它、谁使用它、提供者声明的预期用途是什么。
2. **预期用途证据** —— 使用说明、技术文档、促销材料、服务条款、销售材料。按一般原则指南 ¶¶10-13，提供者的构架很重要。
3. **部署背景** —— 行业（机械、医疗、就业、教育、执法等），用户是提供者、部署者、进口商还是分销商。
4. **修改状态** —— 用户是原始提供者，还是对第三方系统进行了微调 / 改牌 / 实质性修改（第 25 条陷阱）。

如果其中任何一项缺失，继续前询问。基于不完整信息的分类必须标记为初步。

---

## 决策树

按顺序运行五个步骤。每个步骤要么以裁决终止，要么为下一步提供输入。

### 步骤 1 —— AI 系统门控（第 3(1) 条）

确认技术满足第 3(1) 条 AI 系统定义。如果不满足（例如无推断、无学习、无自主性的纯规则软件），AI 法案不适用 → 以**不在 AI 法案范围内**终止。参考：见委员会关于人工智能系统定义的指南，C(2025) 5053（与本高风险指南分开）。

### 步骤 2 —— 预期用途构架（第 3(12) 条；一般原则 ¶¶10-13）

记录提供者声明的预期用途。应用 **GPAI / 多用途陷阱**测试：

- 如果提供者的材料将系统呈现为广泛适用于许多情境，且不持续排除高风险用途 → 预期用途被**视为**涵盖高风险用途（¶12）。
- 仅在服务条款中断言排除高风险用途是**不够的**，如果其他材料（促销、示例、产品定位）表明此类用途可行且合理可预见（¶12）。
- 捕获但排除在本评估之外：第 3(13) 条“合理可预见的滥用”——按定义在预期用途之外。

步骤 2 的输出：一个干净、成文的预期用途陈述，供步骤 3 和 4 使用。

### 步骤 3 —— Art. 6(1) / 附件 I 分支

在步骤 4**之前**完整应用此分支。两个分支不互斥：系统可以同时在 Art. 6(1) 和 Art. 6(2) 下属于高风险（此时适用 Art. 6(1) 合格评定整合——见第 8(2) 条和第 102-109 条）。

#### 3a. AI 系统是附件 I 下的产品 / 安全组件吗？

对照附件 I AI 法案所列的欧盟协调立法筛选（机械、玩具、电梯、ATEX、无线电设备、压力设备、游乐船、缆车、燃气器具、MDR、IVDR、汽车、航空等）。区分：

- **AI 系统本身是受监管产品**（¶30）：独立投放市场、有自身预期用途、直接受监管。示例：条例 (EU) 2023/1230 下的机械相关软件。
- **AI 系统是受监管产品的安全组件**（¶31）。

如果两者都不适用 → 跳到步骤 4。

#### 3b. 安全组件双管测试（第 3(14) 条；¶¶32-49）

应用**两个**替代情形——任一满足即可：

**情形 (i) —— 安全功能（基于意图，¶¶35-37）**
如果提供者的预期用途是预防或减轻对健康、安全或财产的风险，系统构成安全组件。使用此检查清单（来自 ¶37 框）：

- **预防功能**（任一）：对导致伤害的情形的监控/检测；维护/检查检测；伤害预防；对另一安全系统的监督。
- **减轻功能**（任一）：对身体伤害的控制或限制；后果减轻（例如安全停止）；对另一安全系统的控制。
- **非安全功能**：性能优化、服务效率、用户决策自动化、舒适/便利、非安全方面的质量控制。

完整分类体系和工作示例见 [references/safety-function-checklist.md](references/safety-function-checklist.md)。

**情形 (ii) —— 失败或故障（基于后果，¶¶38-43）**
如果系统的失败或故障可能危及健康、安全或财产，系统构成安全组件。失败模式包括：错误输出（假阳性/假阴性）、功能/可用性丧失、性能不稳定/漂移、时间/延迟错误、导致危险控制决策的错误分类。可能性必须超出理论层面（¶39）。

¶46 的工作示例：
- 电梯：关门 / 障碍物检测 AI → 通过失败构成安全组件（效率意图，但故障伤及人员）。
- 车辆：车道辅助 AI → 通过失败构成安全组件。
- 农业：化学喷洒目标 AI → 附近有人时通过失败构成安全组件。
- 智能恒温器（¶48 脚注 5）：不是安全组件，除非它控制儿童锁或围绕弱势用户运行。

步骤 3b 的输出：如果 (i) 或 (ii) 满足 → 继续步骤 3c。否则，这不是安全组件 → 跳到步骤 4。

#### 3c. 第三方合格评定要求（¶¶50-59）

查阅相关附件 I 法律行为要求的合格评定程序：

- **模块 B、C1、C2、D、D1、E、E1、F、F1、G、H、H1（决定 768/2008/EC）** → 涉及公告机构 → 要求第三方合格评定 → **是**。
- **模块 A**（纯内部控制）且无协调标准条件 → 非第三方 → **否**。
- **以强制适用协调标准为条件的模块 A**（例如《玩具安全条例》《机械条例》《无线电设备条例》） → 仍分类为高风险；使用模块 A 的选项是程序灵活性，而非逃避高风险分类的自由裁量（¶57；《玩具安全条例》序言 15）。

如果模块为 A 且无强制协调标准条件 → 不在 Art. 6(1) 下构成高风险。

#### 3d. A 节与 B 节区分（附件 I；第 2(2) 条）

如果 3a + 3b + 3c 全部为是 → **Art. 6(1) 下高风险**。记录：
- 附件 I 引用（具体法律行为）。
- 该法律行为是否在附件 I **A 节**（基于 NLF）——完整的第三章要求适用。
- 或 **B 节**（其他欧盟协调立法，例如航空、汽车）——按第 2(2) 条仅第 6(1)、102-109、112 条适用。

完整映射见 [references/annex-i-section-a-vs-b.md](references/annex-i-section-a-vs-b.md)。

### 步骤 4 —— Art. 6(2) / 附件 III 分支

#### 4a. 映射到八个附件 III 领域

将系统的预期用途与八个领域逐一交叉核对。使用对应的分领域参考文件：

| # | 领域 | 参考 |
|---|------|-----------|
| 1 | 生物识别 | [annex-iii-area-1-biometrics.md](references/annex-iii-area-1-biometrics.md) |
| 2 | 关键基础设施 | [annex-iii-area-2-critical-infrastructure.md](references/annex-iii-area-2-critical-infrastructure.md) |
| 3 | 教育和职业培训 | [annex-iii-area-3-education.md](references/annex-iii-area-3-education.md) |
| 4 | 就业、员工管理和个体经营准入 | [annex-iii-area-4-employment.md](references/annex-iii-area-4-employment.md) |
| 5 | 基本私人服务和公共服务及福利的获取和享有 | [annex-iii-area-5-essential-services.md](references/annex-iii-area-5-essential-services.md) |
| 6 | 执法 | [annex-iii-area-6-law-enforcement.md](references/annex-iii-area-6-law-enforcement.md) |
| 7 | 移民、庇护和边境管控管理 | [annex-iii-area-7-migration.md](references/annex-iii-area-7-migration.md) |
| 8 | 司法和民主程序的行政 | [annex-iii-area-8-justice-democracy.md](references/annex-iii-area-8-justice-democracy.md) |

对每个有用例匹配的领域，捕获具体的附件 III 子点（例如招聘为 Nr. 4(a)）。

#### 4b. 应用 Art. 6(3) 例外过滤器

如果步骤 4a 中有用例匹配，检查 AI 系统是否**仅**执行以下窄类别之一（Art. 6(3)）：

- **(a) 窄程序性任务** —— 严格程序性，对结果无影响。
- **(b) 改进先前完成的人类活动** —— 细化人类已作出的决定。
- **(c) 检测决策模式或偏差** —— 不替代或不影响先前完成的人类评估。
- **(d) 与附件 III 用例相关的评估的准备性任务**。

见 [references/art-6-3-exception-decision-tree.md](references/art-6-3-exception-decision-tree.md)。

#### 4c. 应用个人画像再例外（Art. 6(3) 末句）

如果系统对自然人进行**个人画像**（GDPR 第 4(4) 条——为评估个人方面而自动化处理个人数据），Art. 6(3) 例外被**排除**，系统**属于**高风险。

#### 4d. 例外适用时的成文义务（Art. 6(4)）

如果例外适用 → 非高风险，但提供者必须：
- 在投放市场 / 投入使用前记录推理（Art. 6(4)）。
- 按第 49(2) 条在欧盟数据库中注册系统。

### 步骤 5 —— 第 25 条实质性修改陷阱

如果用户不是原始提供者，而是在修改、微调或改牌现有 AI 系统，标记第 25(1) 条：

- (a) 将自身名称/商标放在现有高风险系统上。
- (b) 对现有高风险系统的实质性修改。
- (c) 修改非高风险系统（包括 GPAI）的预期用途，使其在第 6 条下成为高风险。

如果任一适用 → 用户成为具有完整第三章义务的高风险系统的**提供者**。随后进行角色认定步骤（按第 3 条和第 25 条的提供者 / 部署者 / 进口商 / 分销商）。委员会正在准备单独的第 25 条指南；本技能仅标记。

见 [references/art-25-substantial-modification-flag.md](references/art-25-substantial-modification-flag.md)。

---

## 输出工件

除非用户明确要求子集，否则产生全部三个工件。

### 工件 1 —— 结构化决策块（终端）

```
═══════════════════════════════════════════
EU AI Act — High-Risk Classification Result
═══════════════════════════════════════════
High-risk verdict:        [YES — Art. 6(1) Annex I | YES — Art. 6(2) Annex III Nr. X | NO]
Basis:                    [Safety function / Failure-based / Annex III use-case match]
Annex I citation:         [Legal act + Section A/B] (if applicable)
Annex III citation:       [Nr. X.<sub>] (if applicable)
Art. 6(3) exception:      [N/A | Applied — limb (a/b/c/d) | Excluded by profiling re-exception]
Art. 25 trap:             [Not triggered | Watch — modifying existing system]
Effective date:           [2 December 2027 (Annex III) | 2 August 2028 (Annex I)]
Documentation duty:       [Art. 6(4) (if Art. 6(3) applied) | Chapter III + Art. 11 technical docs]
═══════════════════════════════════════════
```

### 工件 2 —— 实务备忘录（1-2 页叙述）

面向 DPO / AI 合规官的 Markdown 备忘录。章节：
1. **受评估系统** —— 名称、提供者/部署者、预期用途（经清理的步骤 2 陈述）。
2. **裁决与推理** —— 哪个分支（6(1) 或 6(2)）、哪个子测试触发它、委员会指南的哪个段落是锚点。
3. **引用** —— 委员会指南的显式段落号和对应的条款号。
4. **下一步** —— 标记裁决触发的后续工作：角色认定（提供者 / 部署者 / 进口商 / 分销商）、将适用的第三章义务映射到该角色、产生正式合规报告。
5. **开放问题** —— 定稿前需要法律顾问输入的任何事项。

### 工件 3 —— JSON 交换工件

跨技能交换 JSON。模式（匹配现有仓库约定）：

```json
{
  "skill": "ai-act-high-risk",
  "version": "1.0",
  "assessed_at": "2026-MM-DD",
  "system_name": "<provider-supplied name>",
  "intended_purpose": "<cleaned Step 2 statement>",
  "verdict": "high_risk" | "not_high_risk" | "exempt_art_6_3",
  "basis": {
    "article": "6(1)" | "6(2)" | null,
    "annex": "I" | "III" | null,
    "annex_item": "Nr. X" | "Nr. Y.<sub>" | null,
    "section_a_or_b": "A" | "B" | null
  },
  "art_6_3_exception": {
    "applied": true | false,
    "limb": "a" | "b" | "c" | "d" | null,
    "profiling_excluded": true | false
  },
  "art_25_trap_flag": true | false,
  "effective_date": "2027-12-02" | "2028-08-02",
  "citations": [
    {"source": "Commission Guidelines Annex III ¶123"},
    {"source": "Annex III Nr. 4(a) AI Act"}
  ],
  "next_steps": ["role-determination", "obligation-mapping", "compliance-report"]
}
```

---

## 参考

- [art-6-general-principles.md](references/art-6-general-principles.md) —— 委员会的一般原则（¶1-14、¶448-451）。
- [art-6-1-annex-i-guidelines.md](references/art-6-1-annex-i-guidelines.md) —— 委员会的附件 I 部分（¶15-62）。
- [art-6-2-annex-iii-guidelines.md](references/art-6-2-annex-iii-guidelines.md) —— 委员会的附件 III 部分（¶63-447）。
- [safety-function-checklist.md](references/safety-function-checklist.md) —— 来自 ¶37 框的安全功能分类体系。
- [annex-i-section-a-vs-b.md](references/annex-i-section-a-vs-b.md) —— A 节（NLF）与 B 节（其他）映射。
- 8 个分领域附件 III 文件（见步骤 4a 表）。
- [art-6-3-exception-decision-tree.md](references/art-6-3-exception-decision-tree.md) —— 带工作示例的例外过滤器。
- [art-25-substantial-modification-flag.md](references/art-25-substantial-modification-flag.md) —— 准提供者陷阱。
- [ai-omnibus-timeline-postponements.md](references/ai-omnibus-timeline-postponements.md) —— 推迟引用链。

## 后续活动

高风险深度评估通常位于更大工作流中。本技能产生裁决后，自然的下一步是：

- **宽泛风险层级分流** —— 如果系统尚未跨全部五个层级筛选（禁止 / 高风险 / GPAI / 有限 / 最小），先做。
- **条款问答** —— 对任何 AI 法案条款问题，直接从引用的法规文本和委员会指南回答。
- **角色认定** —— 提供者 / 部署者 / 进口商 / 分销商，包括第 25 条准提供者陷阱。
- **义务映射** —— 高风险裁决确定后，按角色和风险层级映射第三章义务。
- **正式合规报告** —— 将分类理由和义务矩阵汇编为可审计记录。
- **初步分流** —— 当完整 Art. 6 深度尚不必要时，15-25 分钟快速评估是较轻的替代方案。

## 变更日志

见 [CHANGELOG.md](CHANGELOG.md)。

## 欧盟 AI 法案套件的一部分

本技能可独立工作，但它设计为与我的其他欧盟 AI 法案技能互锁——可单独安装任何一项，或一起使用以实现端到端工作流：

- **EU AI Act Quick Assessment** —— 15-25 分钟初步分流
- **EU AI Act System Classifier** —— 跨全部五个层级的风险层级分类
- **EU AI Act Role Determination** —— 提供者 / 部署者 / 进口商 / 分销商（含第 25 条）
- **EU AI Act Obligations Mapper** —— 按角色和风险层级的义务
- **EU AI Act Examination Report Generator** —— 可审计合规报告
- **EU AI Act Knowledge Base** —— 对法案 + 委员会指南的问答

每项都可作为单独技能获得——只安装你需要的。
