# 加州消费者隐私法（CCPA/CPRA）技能

> **免责声明：**本技能提供基于加州消费者隐私法（Cal. Civ. Code 第 1798.100 条及以下）和加州隐私权法（第 24 号提案）文本，连同 CPPA 条例和已发布执法指引的信息性指引。它不构成法律意见。对涉及重大合规风险、CPPA 调查应对、集体诉讼敞口或复杂数据共享安排的事项，请咨询在加州执业的有资质隐私律师。

---

## 1. 本技能做什么？

本技能将 Claude 转变为加州全面隐私法框架的专家顾问——涵盖 **加州消费者隐私法（CCPA）**（2020 年 1 月 1 日生效）和**加州隐私权法（CPRA）**（2023 年 1 月 1 日生效）。CPRA 大幅修订并扩展了 CCPA，创建了独立的加州隐私保护局（CPPA），并引入了本技能全面覆盖的新权利和义务。

本技能处理 CCPA/CPRA 合规工作的全部范围：确定企业是否达到法定门槛、指导消费者权利工作流设计、起草隐私通知和退出机制、对数据接收方分类（服务提供商、承包商和第三方）、就敏感个人信息（SPI）处理提供建议，以及评估 CPPA 执法机制下的罚款敞口。

本技能的一个关键优势是其对 **CPRA 新增内容**的覆盖——更正权、限制 SPI 使用权、数据最小化和目的限制义务、保留期披露要求、承包商分类，以及强制性网络安全审计和风险评估义务。这些 CPRA 时代的变化正是许多企业仍存在重大差距之处，尤其是那些在 2023 年之前完成初始 CCPA 合规工作的企业。

**自 2026 年 1 月 1 日起**，两个主要的 CPRA 监管项目已上线：

- **网络安全审计**：处理对消费者安全构成重大风险的 PI 的企业必须进行年度网络安全审计。2025 年定稿的条例现已生效。
- **风险评估**：企业在处理高风险 PI 前必须进行并记录风险评估。CPPA 可随时要求提交这些评估。

**同样于 2026 年 1 月 1 日生效**：CPPA 定稿了其**自动化决策技术（ADMT）**条例。消费者现在有权退出产生重大决策的 ADMT、访问关于自动化处理的信息，并请求人工审查。企业**必须在 2027 年 1 月 1 日前**实施 ADMT 退出机制。

本技能还纳入 **2026 年 CPPA 执法先例**——包括创纪录的 275 万美元迪士尼罚款、110 万美元 PlayOn Sports 行动和 37.5 万美元福特汽车和解——帮助用户理解当前执法姿态并校准自身的罚款敞口。

本技能还提供 **CCPA/GDPR 比较分析**，使全球隐私团队能够将现有欧盟合规控制映射到加州要求并识别美国特有差距——避免重复工作，同时捕捉实质差异（例如退出模式与同意的选择加入模式，或数据泄露的私人诉讼权）。

---

## 2. 1.4.0 版新增内容（2026 年 7 月）

| 更新 | 详情 |
|--------|--------|
| **ADMT 规则现已生效** | CPPA 定稿了 ADMT 条例；2026 年 1 月 1 日生效（此前列为“待定规则制定”） |
| **ADMT 合规期限** | 企业必须在 **2027 年 1 月 1 日**前实施 ADMT 退出机制 |
| **网络安全审计现已生效** | 年度网络安全审计要求自 2026 年 1 月 1 日起生效（此前为“待定最终规则制定”） |
| **风险评估现已生效** | 风险评估提交要求自 2026 年 1 月 1 日起生效 |
| **迪士尼 275 万美元罚款** | 史上最大的 CCPA 执法行动——儿童数据、退出失败、广告科技数据共享 |
| **PlayOn Sports 110 万美元罚款** | 未经授权与第三方共享消费者 PI |
| **福特汽车 37.5 万美元罚款** | 未在要求时限内处理删除和访问请求 |

---

## 3. 目标受众

| 受众 | 如何使用本技能 |
|----------|----------------------|
| **隐私律师和 DPO** | 门槛分析、权利工作流设计、供应商合同审查、执法风险评估 |
| **合规经理** | 对照 CCPA/CPRA 要求的差距评估、补救路线图、审计准备 |
| **内部法律团队** | 起草隐私通知、服务提供商协议和退出机制 |
| **产品和工程团队** | 实施全球隐私控制（GPC）信号处理、同意管理、数据删除流水线、ADMT 退出流程 |
| **营销和数据团队** | 理解什么是跨情境行为广告的“出售”或“共享”；SPI 使用限制 |
| **初创企业和中小企业** | 确定门槛是否适用；理解优先义务 |
| **全球隐私团队** | 将 GDPR 控制映射到 CCPA/CPRA；识别美国特有差距和要求 |
| **数据经纪商和广告科技公司** | 理解“出售”和“共享”的宽泛定义；退出机制要求 |
| **AI/ML 团队** | 理解 ADMT 退出义务、人工审查要求以及 2027 年 1 月 1 日合规期限 |

---

## 4. 常见用例

### 企业适用性与门槛分析
- *“我们公司需要遵守 CCPA 吗？我们是一家年经常性收入 1800 万美元、8 万用户的 SaaS 初创企业。”*
- *“我们是非营利组织。CCPA 适用于我们吗？”*
- *“我们将用户数据出售给广告商，占收入的 45%——我们触发了哪条 CCPA 门槛？”*
- *“CPRA 对我们公司的适用方式与 CCPA 不同吗？”*

### 消费者权利工作流
- *“带我过一遍根据 CCPA 处理删除权请求的分步流程。”*
- *“回应知情权请求前需要什么样的身份验证？”*
- *“删除权有哪些例外？我们可以为防欺诈保留数据吗？”*
- *“我们如何处理针对从第三方收到的数据的更正权请求？”*
- *“回应限制 SPI 使用权请求的时间线是什么？”*

### 隐私通知和政策起草
- *“为我们的移动应用注册屏幕起草一份符合 CCPA 的收集时隐私通知。”*
- *“根据 CPRA，我们的隐私政策必须包含什么才算合规？”*
- *“为我们的主页写一份‘Do Not Sell or Share My Personal Information’链接通知。”*
- *“起草一份‘Limit the Use of My Sensitive Personal Information’披露。”*

### 供应商和数据接收方分类
- *“我们的分析供应商根据 CCPA 是服务提供商还是第三方？”*
- *“服务提供商合同必须包含什么才能防止披露被视为出售？”*
- *“根据 CPRA，服务提供商和承包商有什么区别？”*
- *“我们与广告交易平台共享数据——这构成出售还是共享？”*

### SPI 与退出机制设计
- *“我们收集精确地理位置数据。SPI 处理如何改变我们的义务？”*
- *“我们必须接受哪些信号作为有效的退出？全球隐私控制算吗？”*
- *“设计我们的出售和共享退出工作流，包括 GPC 信号处理。”*
- *“我们什么时候需要‘Limit Use of SPI’链接，什么时候需要‘Do Not Sell or Share’链接？”*

### ADMT 合规（期限：2027 年 1 月 1 日）
- *“我们用 ML 模型做信贷决策。ADMT 适用吗？我们需要在 2027 年 1 月前做什么？”*
- *“根据 CPPA 条例，我们的 ADMT 退出机制必须是什么样的？”*
- *“我们的招聘流程使用自动化筛选工具。ADMT 规则如何影响我们？”*
- *“我们必须为自动化决策提供哪些人工审查权利？”*

### 执法、罚款与 GDPR 对齐
- *“如果我们被发现漏掉了 1 万名消费者的退出信号，我们的罚款敞口是多少？”*
- *“我们已有 GDPR 合规项目。为 CCPA 我们还需要哪些额外步骤？”*
- *“为我们的隐私团队制作一份 CCPA/CPRA 与 GDPR 义务的并排比较。”*
- *“迪士尼罚款 275 万美元——我们的广告科技数据共享会面临类似行动吗？”*
- *“我们错过了 500 个访问请求的 45 天期限。我们的敞口是什么？”*

---

## 5. 如何使用本技能

### 安装
1. 从本文件夹下载 `ccpa.skill` 文件
2. 在 Claude 中，前往 **设置 → 技能**
3. 点击 **上传技能** 并选择 `ccpa.skill`
4. 该技能立即在你的 Claude 会话中激活

### 触发技能
当你的消息涉及 CCPA 或 CPRA 主题时，本技能自动激活。无需特殊命令。会触发它的示例短语：

- *"Is this CCPA compliant?"*
- *"We need to add a Do Not Sell link — what does it need to say?"*
- *"Help me design our consumer rights request process."*
- *"Does sharing data with our ad network count as a sale under California law?"*
- *"What SPI categories does CPRA add?"*
- *"Run a CCPA gap assessment on our current privacy practices."*
- *"Draft a service provider agreement clause for our data processor."*
- *"Compare CCPA and GDPR for our compliance team."*
- *"Do we need an ADMT opt-out mechanism?"*
- *"What do the 2026 CPPA enforcement actions mean for us?"*

### 示例提示

```
"We're a B2C e-commerce company with $30M revenue and 120,000 California 
customers. Run a CCPA/CPRA gap assessment against our current practices: 
we have a privacy policy, no 'Do Not Sell' link, and we use Google Analytics 
and Facebook Pixel."
```

```
"Draft a CCPA-compliant at-collection privacy notice for our mobile app 
sign-up screen. We collect: name, email, phone, precise location, and 
browsing history within the app. We share data with advertising partners."
```

```
"A California consumer submitted a Right to Delete request through our 
website 30 days ago and we haven't responded. Walk me through what we 
must do now, what exceptions might apply, and what our penalty exposure is."
```

```
"We're a European company with GDPR compliance already in place. Produce 
a side-by-side gap analysis showing what additional steps we need to take 
for CCPA/CPRA compliance."
```

```
"Our website uses cookies for cross-context behavioral advertising via 
a third-party DSP. Does this constitute 'sharing' under CPRA? Do we 
need a 'Do Not Sell or Share' link? Must we honor GPC signals?"
```

```
"We use automated scoring to approve or deny insurance applications. 
The CPPA's ADMT rules are now live. What must we implement, and what 
is our deadline for the consumer opt-out mechanism?"
```

---

## 6. 技能实现细节

### 架构

```
ccpa/
├── SKILL.md                              # 核心技能——门槛、权利、义务、
│                                         #   罚款、退出要求、SPI 规则、
│                                         #   ADMT 规则、网络安全审计/风险
│                                         #   评估义务、2026 年执法案例
└── references/
    ├── consumer-rights-workflows.md      # 每项消费者权利的分步工作流：
    │                                     #   验证、回应、例外、时间线
    └── ccpa-gdpr-comparison.md           # 面向全球合规团队的
                                          #   CCPA/CPRA 与 GDPR 并排比较
```

**总计：**约 450 行，3 个文件（SKILL.md + 2 个参考文件）

### SKILL.md 中包含什么

- **谁必须合规** —— 三条法定门槛（收入、数据量、出售/共享收入），带工作示例
- **关键定义** —— 个人信息、敏感个人信息、出售、共享、服务提供商、承包商、第三方
- **消费者权利表** —— 全部 9 项权利，带法条引用和回应期限，包括 ADMT 退出（2026 年 1 月 1 日生效；合规期限 2027 年 1 月 1 日）
- **关键义务** —— 收集时隐私通知、隐私政策要求、退出机制（包括 ADMT 退出）、数据最小化、保留限制、服务提供商合同要求、网络安全审计义务（2026 年 1 月 1 日生效）、风险评估义务（2026 年 1 月 1 日生效）、ADMT 合规框架
- **罚款与执法** —— CPPA 民事罚款（每次违规 2,500 美元/7,500 美元）、私人诉讼权（每起数据泄露事件每名消费者 100-750 美元）
- **2026 年执法先例** —— 迪士尼 275 万美元（创纪录）、PlayOn Sports 110 万美元、福特汽车 37.5 万美元；执法姿态分析
- **九类工作流** —— 如何帮助处理适用性、权利履行、通知、供应商分类、SPI、退出（包括 ADMT）、GDPR 对齐、差距评估和执法/罚款分析

### 参考文件中包含什么

| 文件 | 内容 |
|------|----------|
| `consumer-rights-workflows.md` | 所有消费者权利的分步工作流；身份验证标准；例外处理（防欺诈、法律义务、言论自由）；回应信函模板；被拒绝请求的升级路径 |
| `ccpa-gdpr-comparison.md` | 覆盖合法基础与退出模式、同意要求、数据主体/消费者权利、数据保留、DPO 与无 DPO 要求、执法机制、私人诉讼权、SPI 与特殊类别数据的并排表格 |

### 用于构建技能的输入

| 输入 | 描述 |
|-------|-------------|
| **Cal. Civ. Code 第 1798.100 条及以下** | 含所有 CPRA 修订的完整 CCPA 法条文本 |
| **CPRA（2020 年第 24 号提案）** | 创建 CPPA 并新增 CPRA 权利/义务的修订文本 |
| **CPPA 条例（2025-2026）** | 最终 CPPA 规则制定，包括 ADMT 条例、网络安全审计规则和风险评估要求（均于 2026 年 1 月 1 日生效） |
| **CPPA 执法行动（2026）** | 迪士尼 275 万美元、PlayOn Sports 110 万美元、福特汽车 37.5 万美元执法令 |
| **GDPR（欧盟条例 (EU) 2016/679）** | 用于比较分析参考文件 |
| **IAPP 和隐私律师指引** | 关键定义（出售、共享、服务提供商）的实务解读 |

### 技能触发短语

`CCPA`、`CPRA`、`California Consumer Privacy Act`、`California Privacy Rights Act`、`Do Not Sell`、`Do Not Share`、`consumer rights California`、`right to delete California`、`right to know California`、`right to correct California`、`sensitive personal information`、`SPI`、`CPPA`、`California privacy`、`opt-out of sale`、`GPC signal`、`Global Privacy Control`、`service provider agreement CCPA`、`CCPA gap assessment`、`CCPA compliance`、`California data privacy`、`CCPA vs GDPR`、`cross-context behavioral advertising`、`automated decision-making California`、`ADMT`、`CPPA enforcement`、`cybersecurity audit CCPA`、`risk assessment CPRA`

---

## 7. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)

技能版本：1.6.2 —— 2026 年 7 月
