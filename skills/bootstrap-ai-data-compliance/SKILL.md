---
name: bootstrap-ai-data-compliance
description: 律师驱动的 AI 数据合规冷启动工作流：律师描述 AI+产业合规需求后，Skill 四步引导完成冷启动——产业信息收集 → 知识库构建 → 数据流图与评估报告 → 以《生成式AI行业网络数据安全风险评估工作手册》为指引的进企调研前文件包。适用于内部律师或 AI 协作代理快速搭建任意 AI 产业（客服/知识助手/营销生成/合同审查/医疗等）的数据合规项目；不用于自动出具正式法律意见、绕过律师复核、未经授权开展外部检索或处理非本项目数据。
author: 马也
license: MIT
---

# AI数据合规冷启动（四步工作流 v0.3.0-candidate）

## 工作方式：四步冷启动

> **`--target` 语义**：所有命令的 `--target` 均指向**项目根目录**（任意空目录即可，如 `./projects/ai-companion`）；工作区为 `<target>/ai_compliance/`。不要传 `ai_compliance` 子目录本身，否则会嵌套一层。

律师收到 AI+产业合规需求后，按以下四步引导完成冷启动：

### 第一步：产业信息收集（对话式引导）

1. 律师用自然语言描述产业工作流程（业务用例、数据来源、模型供应商、用户范围等）。
2. Skill 按问题集逐项询问，补充缺失信息：
   - `python scripts/flow.py intake --target <项目目录> --question-set <产业> --project-id <编号>`
   - `python scripts/flow.py intake-record --target <项目目录> --question-id <编号> --answer <回答>`
3. 信息足够（必填问题答完）或律师表示"没有更多信息"时收口：
   - `python scripts/flow.py intake-close --target <项目目录>`
   - 收口后生成 intake.json，作为后续所有步骤的事实基础。

### 第二步：构建知识库（引用复用）

1. 从原论文库/实务文章库/法律法规库按产业关键词筛选，生成引用索引（不复制文件）：
   - `python scripts/flow.py kb-build --target <项目目录>`
2. 产业特有资料引导律师补充：
   - `python scripts/flow.py kb-add --target <项目目录> --collection <论文库/实务文章库/法律法规库> --source <资料路径>`

### 第三步：数据流图 + 评估报告

1. Skill 基于 intake 自动生成通用产业全景模型 JSON：
   - `python scripts/flow.py model-generate --target <项目目录>`
   - 模型 meta 含 `industry`（问题集标识）与 `scene`（产业场景标识，默认=industry；用 generic 问题集但需要专属 DFD 场景视图的项目，手动把 meta.scene 改为专属标识，如 `ai-companion`）。**注意：重跑 model-generate 会重置 meta，需重设 scene。**
   - RF-01（风险关注）答案自动解析注入模型 risks（certainty="客户陈述"），进入访谈重点核查问题与评估报告风险清单。
2. 渲染三层流程图 + 数据流图与评估报告（HTML）：
   - `python scripts/flow.py render --target <项目目录>`
   - 渲染全部基于 diagram-design 规范（vendor/diagram-design/），模型结构见 `assets/model/generic-industry-model.schema.json`：
     - `process-map.html`：**三层流程图（标准交付）**，Swimlane 类型（业务/技术/数据 3 泳道 × 阶段列），`scripts/processmap_builder.py` 直接从模型生成——stages→列、三层节点→泳道格、layerLinks→层间映射（业务→数据自动链式化为 业务→技术→数据，避免穿过技术层）。节点 factStatus="待核实" 视为无状态（不显示）。
     - `data-flow-map.html`：**数据流图（标准交付）**，Data flow 类型（角色泳道 × 阶段列），`scripts/dataflow_builder.py`，场景视图查找顺序 `meta.scene` → `meta.industry` → 零售模板回退（回退时显式警告，不静默）。场景视图 `assets/dfd-scenes/<scene>-dataflow.json`。
     - **几何自检（自动门禁）**：render 后自动跑 `scripts/verify_geometry.py`——检测箭头 path 穿节点矩形、accent label 压节点，发现即失败（与 self_check.py 互补：self_check 管 HTML 契约，verify_geometry 管几何布局）。
     - `评估报告.html`：**深度评估报告**，`_build_report_html(model, intake)` 从 intake 事实 + 模型生成 6 节（业务全景/重点合规义务核对/核心风险分析/合规差距与行动建议/已发生风险事件/待核验事项）；义务核对表按关键词命中自动标注现状（存在缺口/已有机制/待核实），法规引用为元典核验条款。
     - `process-map.svg` / `data-flow-map.svg`：保留的原 panorama/拓扑视角 SVG（兜底，非标准交付）。

### 数据流图（角色泳道视图）场景视图填写指南

新增产业时按以下约定填写 `assets/dfd-scenes/<industry>-dataflow.json`（参照 `retail-ecommerce-dataflow.json`）：

- **lanes**（角色泳道，≤4）：如 用户/客户、数据平台、专业人员、治理/合规。每条含 3 字母 `key` 与两行 `name`。
- **steps**（阶段列，≤6）：数据生命周期阶段（采集→存储→处理→训练→推理→退出）。**恰好 1 个阶段声明 `focal: true`**（核心风险点）。
- **nodes**（节点，每格一个）：`lane` + `step` 定位；`sub`（数据转换说明）、`tool`（系统/载体）；`chips: {in, out}` 用数据类型码（WB/DB/TB/FL/LS）标记入/出数据形态；治理/归档节点可用 `color`（≤3 个自定义色）；**恰好 1 个节点声明 `focal: true`**（接收关键移交的节点）。
- **arrows**（流，≤12）：`style` 为 `muted`（标准移交）/`trigger`（治理/审核触发，虚线）/`accent`（**恰好 1 条**，带 `label`，关键移交）/`link`（对外交付）。同泳道水平直连，同阶段跨泳道垂直直连，跨两者走正交直角。
- 渲染器 fail-fast：泳道/阶段/流数量、focal 唯一性、芯片码合法性任一不满足即报错不出图。

### 第四步：手册指引文件包

以《生成式人工智能行业网络数据安全风险评估工作手册》为指引，生成进企实地调研前全套文件：
- `python scripts/flow.py field-pack --target <项目目录> --project-name <名称>`

**最终成果目录**：render 与 field-pack 完成后，最终交付物（全景交付.html + 7 份 Word）自动聚合至 `<target>/ai_compliance/07_final_deliverables/`；其余文件（SVG 兜底、模型 JSON、kb 索引、intake 等）为过程性产物，保留在各自目录。
- 产出 7 份：
  1. 信息调研表（手册附录1，107 项，★必查标注）
  2. 风险识别表（手册附录2，319 指标，★必查标注）
  3. 访谈提纲（5 角色 × 12–14 问，含追问要点/证据锚点 + 模型注入的本场景重点核查问题）
  4. 进企前文件与证据清单（8 主题分类 + 证据标准/获取渠道 + 现场核查动作）
  5. 数据资产盘点清单（字段级，进企第一动作）
  6. 现场核查表（系统演示/日志抽查/安全测试）
  7. 保密承诺与进场授权函（两份文书模板）
- ★必查标注：由模型风险清单关键词自动推导（`scripts/word_builder.py` REQUIRED_KEYWORDS）。
- 法律依据列：按来源表/安全子类映射现行有效条款（元典核验，2026-08-20；`word_builder.py` SURVEY_LAW_MAP / LAW_BASIS_RULES）。
- 适用性裁剪：intake 答案确认"不涉及"时（无跨境/无生物识别/不面向未成年人），相关项状态标"不适用（理由）"，不物理删除、可恢复。
- 领域扩充：`assets/field-extensions.json` 规则库——AI 嵌入领域（医疗健康范例已建）命中 match 关键词时，自动向 01/02 追加领域专项调研项/评估指标及领域法规说明；新增领域按 JSON 内结构复制扩展。
- 数据源：原知识库 `04_handbook_structured/`（手册已结构化 CSV）。

## 原有状态机命令（内部能力，保留兼容）

以下命令为 v0.2.0 状态机保留（用于已有项目的证据中台/候选交付/验收归档）：

```bash
python scripts/flow.py init|adopt|preflight|advance|status|validate|package|validate-config|law-update|migrate ...
```

## 强制边界

<!-- skill-lint:constraint AIDC-001 -->
- 禁止覆盖原始资料、正式成果和既有归档；同名异内容时停止并报告冲突。

<!-- skill-lint:constraint AIDC-002 -->
- 只允许“文件明确记载 / 多个文件归纳 / 需律师确认 / 无直接法源 / 客户事实待核实”五类证据标签。

<!-- skill-lint:constraint AIDC-003 -->
- 客户事实门禁未通过时，只输出缺失项；禁止生成候选风险结论或候选交付包。

<!-- skill-lint:constraint AIDC-004 -->
- 只生成候选材料；禁止自动生成或标记正式法律意见，候选材料必须显示“候选版／需律师确认”。

<!-- skill-lint:constraint AIDC-005 -->
- 默认仅使用本地资料。外部检索必须另获授权，且不得发送项目正文、客户资料或非公开业务信息。

<!-- skill-lint:constraint AIDC-006 -->
- 活跃配置、索引和交付包只记录项目相对路径；不得写入操作者电脑绝对路径。

<!-- skill-lint:constraint AIDC-007 -->
- 论文、公众号、工作手册和实务指南不得单独证明强制性法律义务。

<!-- skill-lint:constraint AIDC-008 -->
- 生产器不得给自己签发最终通过状态；只有独立验证器检查真实产物后，才能确认完成。

## 停止条件

- intake 必填问题未答完且未强制收口时，停在第一步。
- 原知识库目录不可用时，停止 kb-build/field-pack。
- 模型 risks/sources 引用未收录法源时，标"待补充"，不虚构。
- 律师复核状态不明确时，所有评估材料保持候选状态。

## 验收

- 四步端到端验收：`python scripts/run_coldstart_acceptance.py --target-root <临时目录>`
- 原有三场景回归：`python scripts/run_acceptance.py --bci-source-root <知识库根>`
- 三轮稳定性：`python scripts/run_stability.py --bci-source-root <知识库根>`
- 数据流图几何自检（独立门禁）：`python scripts/verify_geometry.py <data-flow-map.html>`（render 已自动执行；正负样本验证：穿节点 HTML 应 FAIL exit=3）

## 真实场景测试（首次/新领域跑四步时）

用户以业务描述开场（一句话即可，如"帮我启动一个AI数据合规项目，产品是XX"）后，按四步完整运行。执行时：

1. 每个命令执行后检查产物真实性：Word 用 python-docx 抽查表格行数与关键列（调研表 106+ 行、风险表 319+ 行、访谈提纲含 5 角色问题表与重点核查段）；HTML 图跑 `vendor/diagram-design/scripts/self_check.py`。
2. 问题台账：将运行中的命令报错、产物异常、逻辑偏差、缺漏项记录到项目 `workspace/测试问题台账.md`，每条标注【现象/根因假设/严重程度】。
3. 领域规则：若场景触发未建领域（如拟人化互动类 AI 的深度合成/未成年人保护），在测试报告中标注"待补领域规则"，按 `ai-data-compliance-field-rules` 的 SKILL.md 步骤补充。
4. 测试结束输出测试报告：四步产物清单、通过/失败项、问题清单、对 Skill 的改进建议。
