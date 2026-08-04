# NIST AI 风险管理框架（AI RMF）技能

> ⚠️ **免责声明：**本技能提供基于 NIST AI 100-1（2023 年 1 月）及配套 AI RMF Playbook 的信息性指引。AI RMF 是一个自愿性、非规定性的框架。它不构成法律意见，也不替代适用 AI 法规（如 EU AI Act）项下的合规义务。对影响基本权利、安全系统或受监管行业的高风险 AI 部署，请咨询合格的律师和领域专家。

---

## 1. 本技能做什么？

NIST AI RMF 技能将 Claude 转变为具有 NIST AI 风险管理框架（AI RMF 1.0）全面知识的专家级 AI 风险管理顾问。该框架于 2023 年 1 月作为 NIST AI 100-1 发布，提供一种结构化、以成果为导向的方法，用于在整个 AI 生命周期——从设计和开发到部署、监控和退役——中识别、评估和管理 AI 风险。

本技能覆盖 AI RMF 的全部四个核心功能：GOVERN（6 个类别，21 个子类别）、MAP（5 个类别）、MEASURE（4 个类别）和 MANAGE（4 个类别）——共 19 个类别。每个回答都引用具体功能和类别（例如“GOVERN 1.1”或“MAP 3.2”），而非仅引用功能名称。本技能还涵盖 AI RMF Playbook 对每个类别的建议行动，使组织能够直接从框架理解走向实际实施步骤。

本技能的一个核心特征是 AI RMF 定义的七项可信赖性属性：可问责与透明、可解释与可解读、公平与偏见可控、隐私增强、可靠、韧性、安全、安全与网络韧性、有效与已验证。本技能在评估特定 AI 系统、构建风险登记簿或确定应优先实施框架的哪些类别时，将这些属性作为评估透镜。

本技能支持 AI 风险画像构建——同时构建当前画像（组织今天所处的位置）和目标画像（组织需要达到的位置），并进行差距分析和有优先级的补救路线图。它还涵盖 AI 风险登记簿设计、AI 事件响应规划（与 MANAGE 3.x 对齐）以及与 EU AI Act、ISO 42001:2023 和 NIST CSF 2.0 的跨框架对齐。框架的自愿性和非规定性贯穿始终：本技能提供结构化指引，而不暗示存在单一的强制实施路径。

---

## 2. 目标受众

| 受众 | 如何使用本技能 |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **AI 治理团队** | 构建 AI 治理政策（GOVERN 功能）、定义风险容忍度、分配问责 |
| **首席 AI 官 / 首席风险官** | 制定组织 AI 风险画像、向董事会汇报、将 AI 风险对齐到企业风险管理 |
| **AI/ML 工程师** | 理解 MAP 和 MEASURE 要求、实施偏见测试、可解释性和稳健性评估 |
| **隐私与法律团队** | 处理隐私增强和可问责可信赖性属性、驾驭跨框架义务 |
| **安全团队** | 评估 AI 系统的对抗性 ML 威胁（规避、投毒、提取攻击） |
| **合规经理** | 进行 AI RMF 差距评估、构建补救路线图、记录合规证据 |
| **产品经理** | 在部署前理解 AI 功能的风险背景（MAP 功能） |
| **高管与董事会** | 从战略层面理解 AI 风险、接收与 GOVERN 功能对齐的 AI 风险简报 |
| **受监管行业团队** | 将 AI RMF 对齐到行业特定 AI 法规（EU AI Act、金融服务 AI 指引） |

---

## 3. 常见用例

### 组织差距评估

- “为我们的组织在全部四个功能上开展 AI RMF 差距评估”
- “对照全部 19 个 AI RMF 类别评估我们当前的状态，并识别优先差距”
- “我们没有正式的 AI 治理——GOVERN 功能应该从哪里开始？”
- “为我们的 AI 风险管理项目构建当前画像和目标画像”

### AI 治理与政策（GOVERN 功能）

- “起草一份与 GOVERN 1.1–1.7 对齐的组织级 AI 风险管理政策”
- “AI RMF 在 GOVERN 2.x 下推荐什么样的问责结构？”
- “我们应该如何定义和传达我们的 AI 风险容忍度（GOVERN 1.3）？”
- “为 GOVERN 3.x 起草一份带角色和职责的 AI 治理章程”

### 风险背景与识别（MAP 功能）

- “我们正在部署一个 AI 驱动的信用评分系统——带我过一遍 MAP 1.x 背景建立”
- “我们如何在 MAP 3.x 下将 AI 风险映射到受影响的利益相关方？”
- “MAP 5.x 对刻画包括偏见在内的 AI 危害可能性说了什么？”
- “帮助我们记录 AI 系统的预期用例和部署环境”

### 风险分析与测量（MEASURE 功能）

- “我们应该为 AI 系统的有效性和可靠性跟踪哪些指标（MEASURE 2.x）？”
- “我们如何测量算法偏见——AI RMF 引用了哪些公平性指标？”
- “MEASURE 3.x 对随时间监控 AI 风险有什么要求？”
- “为我们的面向客户的推荐系统构建一张 AI 可信赖性记分卡”

### 风险应对与管理（MANAGE 功能）

- “起草一份与 MANAGE 3.x 对齐的 AI 事件响应计划”
- “MANAGE 2.x 对 AI 风险处置策略的资源投入有什么要求？”
- “我们如何记录风险处置成果并将经验教训反馈回 GOVERN？”
- “我们检测到模型漂移——带我过一遍 MANAGE 3.x 响应工作流”

### AI 风险登记簿

- “构建一份与 AI RMF 对齐的 AI 风险登记簿模板”
- “帮助我们为医学影像 AI 系统记录风险，带可能性/影响评分”
- “对一个人脸识别系统，最受风险威胁的可信赖性属性是什么？”
- “为对抗性 ML 威胁向我们的 AI 风险登记簿添加新条目”

### 跨框架对齐

- “将 AI RMF 四个功能映射到 EU AI Act 对高风险 AI 系统的要求”
- “ISO 42001:2023 如何与 NIST AI RMF 对齐？”
- “将 AI RMF 类别映射到 NIST CSF 2.0 子类别”
- “我们遵守 ISO 27001——AI RMF 如何扩展我们现有的风险管理？”

---

## 4. 如何使用本技能

### 安装

1. 从本文件夹下载 `nist-ai-rmf.skill`
2. 在 Claude 中，前往 **设置 → 技能**
3. 点击 **上传技能** 并选择 `nist-ai-rmf.skill`
4. 该技能现在在所有 Claude 会话中激活

### 触发技能

当你提出 NIST AI RMF 或 AI 风险管理主题时，本技能自动激活。无需特殊命令。触发本技能的自然语言短语示例：

- _"We need to implement the NIST AI RMF"_
- _"AI risk management framework"_
- _"GOVERN function AI"_
- _"AI trustworthiness assessment"_
- _"How do we manage bias in our AI system?"_
- _"AI incident response"_
- _"Map AI RMF to EU AI Act"_
- _"Build an AI risk register"_
- _"AI risk profile"_

### 示例提示

```
We are a financial services firm planning to deploy an AI model to automate loan
decisions. Conduct a full AI RMF gap assessment across GOVERN, MAP, MEASURE, and
MANAGE functions. For each of the 19 categories, rate our starting position as
Not Started and provide the top 3 suggested actions we should take first.
```

```
Our AI team has built a hiring algorithm that screens CVs. Walk me through the MAP
function context establishment, identify which trustworthiness properties are most
at risk for this use case, and recommend specific MEASURE metrics we should track
for fairness and bias.
```

```
Draft an organisational AI Risk Management Policy covering all six GOVERN categories.
The policy should define our AI risk tolerance, assign accountability structures,
establish cross-functional team obligations, and reference applicable regulations
including the EU AI Act.
```

```
We detected that our customer churn prediction model has significantly degraded
in accuracy after a data pipeline change. Walk me through the MANAGE 3.x incident
response workflow: trigger conditions, containment, stakeholder notification,
remediation steps, documentation, and how to update our risk register.
```

```
Build an AI risk register for our three AI systems: (1) a product recommendation
engine, (2) a fraud detection model, and (3) an automated contract review tool.
For each system, identify the top AI risks, map them to trustworthiness properties,
and assign likelihood, impact, and treatment actions.
```

---

## 5. 技能实现细节

### 架构

```
plugins/nist-ai-rmf/
└── skills/
    └── nist-ai-rmf/
        ├── SKILL.md                        # 核心技能——AI RMF 结构、全部 4 个功能
        │                                   #   19 个类别、7 项可信赖性属性、3 个常见
        │                                   #   工作流（差距评估、风险登记簿、事件
        │                                   #   响应）、响应格式规则
        └── references/
            ├── rmf-core.md                 # 全部 19 个类别及完整子类别描述
            │                               #   和 Playbook 建议行动（GOVERN/MAP/MEASURE/MANAGE）
            └── rmf-profiles.md             # AI 风险画像概念（当前/目标）、如何构建
                                            #   画像、可信赖 AI 指标和指示符、
                                            #   跨框架映射（ISO 42001、EU AI Act、NIST CSF）
```

### SKILL.md 中包含什么

- 专家人设：具备 NIST AI 100-1 和 Playbook 知识的 NIST AI RMF 1.0 顾问
- 框架概览：两部分结构（第 1 部分 风险框架化，第 2 部分 核心）
- 自愿性和非规定性声明
- 将 6 种任务类型映射到结构化输出的响应格式表（画像/当前状态、行动计划、政策起草、风险登记簿、跨框架映射、问答）
- 引用标准：具体功能 + 类别（例如 MAP 1.5、MEASURE 2.3）
- GOVERN 功能：6 个类别（GV-1 至 GV-6），带重点描述
- MAP 功能：5 个类别（MP-1 至 MP-5），带重点描述
- MEASURE 功能：4 个类别（MS-1 至 MS-4），带重点描述
- MANAGE 功能：4 个类别（MG-1 至 MG-4），带重点描述
- 七项可信赖性属性表，每项属性带关键问题
- 三个常见工作流：差距评估（19 类别评分）、AI 风险登记簿条目结构、事件响应（MANAGE 3.x）

### 参考文件中包含什么

| 文件 | 内容 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `references/rmf-core.md`     | 全部 19 个 AI RMF 类别及完整子类别文本和 Playbook 建议行动：GOVERN（6 个类别，21 个子类别），包括 GV-1（政策/流程）、GV-2（问责）、GV-3（角色）、GV-4（跨职能团队）、GV-5（风险容忍度）、GV-6（监管对齐）；MAP 功能，包括背景建立、科学理解、利益相关方映射、风险优先级排序、危害刻画；MEASURE 功能，包括测量方法、可信赖性评估、风险跟踪、反馈机制；MANAGE 功能，包括风险优先级排序、处置策略、监控与调整、经验教训 |
| `references/rmf-profiles.md` | AI 风险画像概念（当前画像与目标画像）；6 步画像构建方法论；可信赖 AI 特征的指标和指示符——准确性/有效性（精确率、召回率、AUC-ROC、校准、分布外性能）、公平性/偏见（人口统计均等、均等化几率、反事实公平性、差异影响比率、分组报告）、可解释性（SHAP、LIME、反事实解释、模型卡、显著性图）、稳健性/可靠性（对抗准确性、投毒韧性、输入扰动敏感性、可用性、模型漂移检测）、隐私（差分隐私、k-匿名、联邦学习、成员推断抗性）、安全性（对抗性 ML 威胁）；与 ISO 42001:2023、EU AI Act 和 NIST CSF 2.0 的跨框架映射 |

### 用于构建技能的输入

| 输入 | 详情 |
| ------------------------------ | --------------------------------------------------------------------------- |
| 主要文件 | NIST AI 100-1 —— AI 风险管理框架 1.0（2023 年 1 月） |
| 配套文件 | NIST AI RMF Playbook —— 每个子类别的建议行动 |
| 发布机构 | 美国国家标准与技术研究院（NIST） |
| 框架类型 | 自愿性、非规定性、以成果为导向 |
| 可信赖性属性 | NIST AI 100-1 第 1 部分定义的 7 项属性 |
| 跨框架：AI 法规 | EU AI Act（欧盟条例 (EU) 2024/1689）——高风险 AI 系统要求 |
| 跨框架：AI 管理 | ISO/IEC 42001:2023 —— AI 管理系统 |
| 跨框架：网络安全 | NIST CSF 2.0 —— 功能和子类别映射 |
| 跨框架：ISMS | ISO/IEC 27001:2022 —— 面向将 ISMS 扩展到 AI 的组织 |
| 偏见指标 | EEOC“4/5 规则”（差异影响比率 ≥0.8）；标准公平性指标 |
| 隐私指标 | 差分隐私（ε 参数）；k-匿名；联邦学习 |
| 可解释性方法 | SHAP、LIME、反事实解释、模型卡 |
| 对抗性 ML | 规避攻击（FGSM、PGD）、投毒、模型提取 |
| 漂移检测 | PSI（群体稳定性指数）、KS 检验 |

### 技能触发短语

`NIST AI RMF`、`AI Risk Management Framework`、`NIST AI 100-1`、`AI RMF 1.0`、
`GOVERN function`、`MAP function`、`MEASURE function`、`MANAGE function`、
`AI trustworthiness`、`trustworthy AI`、`AI governance`、`AI risk profile`、
`AI risk register`、`AI risk management`、`responsible AI`、`AI bias management`、
`algorithmic fairness`、`AI explainability`、`AI transparency`、`model drift`、
`adversarial ML`、`AI safety`、`AI incident response`、`AI reliability`、
`AI security`、`AI privacy`、`GOVERN 1.1`、`MAP 1.5`、`MEASURE 2.3`、`MANAGE 3.x`、
`EU AI Act alignment`、`ISO 42001`、`AI RMF playbook`、`AI lifecycle risk`、
`AI deployment risk`、`GV-1`、`MP-1`、`MS-1`、`MG-1`

---

## 6. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)

技能版本：1.6.2 —— 2026 年 7 月
