# TSA 网络安全合规技能

> 面向关键基础设施所有者与运营者的 Claude 技能，助其应对 TSA 安全指令要求——涵盖现行指令及 2024 年 11 月 NPRM 下的管道、货运铁路、客运铁路、公共交通和公交运营者。

---

## 1. 本技能做什么？

TSA 合规技能将 Claude 变成关键交通基础设施领域的 TSA 网络安全指令专家顾问。它提供结构化、可操作的指引，用于实施和维持对 TSA 安全指令的合规——从适用性确定和差距评估，到 CIP/COIP 起草、架构设计审查、事件响应规划及 IRP 测试计划。

本技能涵盖**截至 2026 年生效的现行 TSA 安全指令系列**：
- **SD Pipeline-2021-01G** 和 **SD Pipeline-2021-02F** ——管道运营者
- **SD 1580-21-01E** ——货运铁路运营者
- **SD 1582-21-01E** ——公共交通和客运铁路运营者

它还涵盖**2024 年 11 月 NPRM**（拟议规则制定通知），该 NPRM 将把现行指令正式化为永久联邦法规，包括其与 NIST CSF 2.0 和 CISA 跨部门网络安全绩效目标（CPG）的对齐。

---

## 2. 目标受众

- **关键基础设施运营者** ——被 TSA 指定为受覆盖实体的管道公司、货运铁路、客运铁路机构、交通管理当局和公交运营者
- **运输运营者的 CISO 与安全团队** ——管理 TSA 指令合规计划
- **OT/ICS 安全工程师** ——在运营技术环境中实施四个技术安全领域（网络分段、访问控制、持续监控和补丁管理）
- **合规与监管事务团队** ——负责向 TSA 和 CISA 提交 CIP、CAP 和事件报告
- **GRC 分析师** ——对照 TSA 指令要求进行差距评估
- **法律顾问与高管**（责任高管 Accountable Executives）——监督 TSA 合规义务
- **顾问** ——支持管道或铁路客户完成 TSA 指令实施

---

## 3. 常见用例

| 用例 | 示例提示 |
|----------|---------------|
| **适用性检查** | “我们是天然气管道运营者。我们是否受 TSA 安全指令约束？这对我们意味着什么？” |
| **差距评估** | “对照 TSA SD Pipeline-2021-02 要求，对我们的网络安全计划进行差距评估。” |
| **CIP 起草** | “帮我为我们的管道 OT 环境起草一份网络安全实施计划（CIP）。” |
| **事件报告** | “我们在 IT 网络上检测到勒索软件。它尚未到达我们的 SCADA。我们需要向 CISA 报告吗？” |
| **IRP 测试** | “按 TSA 指令，我们需要每年测试哪些 IRP 目标，以及如何记录？” |
| **OT 分段** | “如何为我们的管道 SCADA 环境实施所要求的 IT/OT 网络分段？” |
| **ADR 指引** | “带我了解 TSA 合规的架构设计审查应涵盖什么。” |
| **CAP 起草** | “帮我构建一份网络安全评估计划提交给 TSA。” |
| **NPRM 影响** | “如果 TSA 2024 年 11 月的 NPRM 按提案定稿，对我们来说会有什么变化？” |
| **CISA CPG 对齐** | “CISA 的跨部门 CPG 如何映射到我们的 TSA 指令要求？” |

---

## 4. 如何使用本技能

技能安装到 Claude 后，只要您询问 TSA 安全指令、TSA 网络安全合规、管道网络安全、铁路或交通网络安全、运输领域的 OT/ICS 安全、CIP/COIP、CAP、向 CISA 的事件报告或 2024 年 NPRM，它就会自动激活。您无需按名称引用该技能。

### 最佳效果提示

**说明您的行业和运营者类型** ——管道（燃气或液体）、货运铁路、客运铁路、交通管理当局或公交。各行业和指令系列的要求不同。

**描述您当前的 OT/IT 环境** ——是否已有 IT/OT 分离、运行哪些 SCADA/ICS 系统、当前监控能力如何。

**说明您的指令状态** ——您是已被指定的受覆盖实体吗？适用哪项指令？是否已提交 CIP？

### 示例交互

```
您：    我们是天然气管道运营者。TSA 刚刚通知我们受 SD Pipeline-2021-02 覆盖。
        我们有带 HMI、历史数据库和远程现场 RTU 的 SCADA 系统。我们的 IT 和 OT
        网络共享同一子网。我们从哪里开始？

Claude：考虑到您刚刚被指定，这里有一条按优先级排序的路径：
        1. 立即指定您的网络安全协调员——供 TSA 和 CISA 24/7 联系。
           向 TSA 提交联系信息。
        2. 建立 CISA 事件报告机制——确保团队知晓在识别到任何 CCS
           受侵后的 24 小时内报告。
        3. 首先解决您的最高风险差距：扁平化 IT/OT 网络。
           这直接违反领域 1。您需要在企业 IT 与 SCADA 网络之间
           设置防火墙或 DMZ——这是 CIP 提交前的最优先补救事项。
        4. 起草涵盖全部四个领域、IRP、ADR 和 CAP 的 CIP。
           每个 CIP 部分需要包含以下内容……
```

---

## 5. 技能实施细节

### 架构

```
tsa-compliance/
├── SKILL.md                              # 核心技能逻辑与工作流
└── references/
    ├── tsa-directives-overview.md        # 全部指令系列、修订历史、NPRM、框架映射
    ├── tsa-crmp-requirements.md          # CRMP 组件（CIP、IRP、ADR、CAP）+ 四个技术领域
    └── tsa-incident-reporting.md         # 事件报告程序、CISA 联系、时限、ISAC 信息
```

### SKILL.md 中的内容

- **角色**：专注于交通关键基础设施的 TSA 网络安全合规专家顾问
- **输出格式矩阵**：将任务类型映射到特定输出格式
- **按行业的指令覆盖**：管道、货运铁路、交通/客运铁路、航空、公交
- **关键网络系统（CCS）定义**：IT/OT 范围、指定方法
- **核心要求**：事件报告、网络安全协调员、差距审查
- **CRMP 四个组件**：CIP/COIP、IRP、ADR、CAP——含全部必要要素
- **四个技术领域**：网络分段、访问控制、监控、补丁管理
- **5 个核心工作流**：适用性确定、差距评估、CIP/COIP 起草、事件响应、政策生成
- **2024 年 NPRM 概述**：拟议变更及与 NIST CSF 2.0 和 CISA CPG 的对齐

### 参考文件中的内容

| 文件 | 内容 |
|------|----------|
| `tsa-directives-overview.md` | 全部现行指令系列（管道、货运铁路、交通）及修订历史；NPRM 摘要；关键定义；框架映射表 |
| `tsa-crmp-requirements.md` | 详细 CIP/COIP 章节要求；IRP 要素和测试要求；ADR 流程；CAP 要素；全部四个领域的 OT 特定实施指引 |
| `tsa-incident-reporting.md` | 24 小时 CISA 报告义务；CISA 联系；何种情况须报告；初始报告格式；后续报告；ISAC 列表；CIRCIA 重叠 |

### 用于构建技能的资料

- **TSA 安全指令** ——SD Pipeline-2021-01 和 02 系列；SD 1580-21-01；SD 1582-21-01（基于公开可得的摘要和《联邦公报》通知）
- **TSA 2024 年 11 月 NPRM** ——《加强地面运输网络安全》
- **CISA 跨部门网络安全绩效目标** ——IT 和 OT CPG 基线
- **NIST CSF 2.0** ——TSA NPRM 中引用，用于年度基于档案的评估
- **NIST SP 800-82** ——ICS/OT 安全指南（参考性引用）
- **IEC 62443** ——OT/ICS 安全标准（参考性引用）
- **GAO 关于 TSA 地面运输网络安全的报告**（GAO-25-107947）

### 技能触发短语

`TSA Security Directive` · `SD Pipeline-2021` · `SD 1580-21-01` · `SD 1582-21-01` · `TSA cybersecurity` · `pipeline cybersecurity compliance` · `Critical Cyber Systems` · `CCS` · `Cybersecurity Coordinator` · `Cybersecurity Implementation Plan` · `CIP` · `COIP` · `CIRP` · `IRP testing` · `Architecture Design Review` · `ADR` · `Cybersecurity Assessment Plan` · `CAP` · `CRMP` · `CISA 24-hour reporting` · `OT segmentation TSA` · `rail cybersecurity directive` · `transit cybersecurity` · `TSA NPRM 2024` · `transportation critical infrastructure`

---

## 6. 关于 SSI 的重要说明

TSA 安全指令依 49 CFR Part 1520 被列为**敏感安全信息（SSI）**。TSA 指令全文不公开。本技能基于公开披露的摘要、《联邦公报》通知、TSA 新闻稿以及 DHS/CISA 出版物。受覆盖实体直接从 TSA 获得实际指令文本，应以官方指令作为合规义务的权威来源。

---

## 7. 作者

**技能设计者：** Hemant Naik
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)
**构建工具：** Claude（Anthropic），使用 Claude Skills 框架
**日期：** 2026 年 3 月
**技能版本：** 1.6.2
**标准覆盖：** TSA SD Pipeline-2021-01G、SD Pipeline-2021-02F、SD 1580-21-01E、SD 1582-21-01E、2024 年 11 月 NPRM
