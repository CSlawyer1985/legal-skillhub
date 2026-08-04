---
name: lawyer-legal-knowledge-distillation-geo
description: Distill authorized legal cases, legal books, courses, and lawyer practice experience into auditable legal skills, then optionally create a privacy-safe GEO publication pack. Use when asked to 蒸馏案件、法律书籍或实务经验, build a lawyer workflow skill, sublate existing knowledge skills, or prepare verified public legal knowledge for AI citation. Do not use for ordinary case advice, unauthorized client files, unverified law summaries, or direct external publication.
---

# 律师专用法律知识蒸馏与 GEO 发布

把案件、法律书籍、课程和律师实务经验转化为可追溯、可执行、可测试、可迭代的法律 Skill；只有经过独立授权与脱敏验收的公开知识，才能继续进入 GEO 发布层。

## 不可变原则

1. **私域证据层、验证知识层、公开投影层必须物理分离。** 原始案件材料和答案键永不进入公开包。
2. **事实、证据、法律、经验和推论分别标注。** 不把来源中的观点写成现行法，也不把个人经验包装成普遍规则。
3. **先建立 SSOT，再生成文书、Skill 或 GEO 内容。** 派生物不得反向覆盖唯一事实源。
4. **审查与批准分离。** 起草者不能自我批准，测试通过不等于安装、晋升或外部发布获批。
5. **GEO 只优化表达和可发现性，不改变法律命题。** 排名、引用或转化不得保证。
6. **默认一键跑到本地候选包。** 只在授权不清、材料不可读、现行法不明或外部发布前停下。

## 适用模式

| 模式 | 典型输入 | 核心产物 |
|---|---|---|
| `case-distillation` | 已获授权的案件卷宗、时间线、裁判文书 | 类型案件流程、证据链、路由、模板与回归集 |
| `legal-source-distillation` | 法律书籍、论文、课程、公开法源 | 原子知识记录、法源图谱、可执行研究/办案 Skill |
| `practice-experience-distillation` | 律师复盘、访谈、检查清单、隐性经验 | 条件化经验规则、失败模式、人工判断点 |
| `mixed-distillation` | 案件、法源与实务材料的组合 | 统一 SSOT 与分层 Skill 包 |
| `public-geo-projection` | 已验证且获公开授权的知识核心 | FAQ、知识卡、结构化数据草案、查询集与测量报告 |

若用户只是要求处理当前案件、检索法条或写普通文书，应调用对应法律 Skill，而不是启动本蒸馏流水线。

## 启动检查

开始前读取 `PIPELINE_STATE.md`。存在未完成记录时，从最后一个已验证检查点继续，不从头重跑。

建立本次 `distillation-plan.json`，至少写明：

- 输入类型、授权人、允许用途和禁止用途；
- 私域根、构建根、公开投影根，三者不得重合；
- 基准截止日和需要验证的现行法日期；
- 答案键、历史成品和冻结基线的隔离方式；
- 计划产物、审查席位、终止条件和外部发布状态。

任一字段无法确认时使用相应 HOLD，不猜测授权。

## 十二阶段流水线（阶段 0–11）

### 阶段 0：授权、权利与只读基线

1. 识别材料所有者、委托边界、版权/许可、保密义务和允许用途。
2. 原件、答案键、历史成品和冻结基线只读；所有新产物进入独立 staging。
3. 记录文件清单、大小、哈希和读取状态，不把绝对路径写入交付包。
4. 未获案件处理授权时进入 `HOLD-AUTHORIZATION`；版权或公开许可不明时进入 `HOLD-RIGHTS`。

详见 `references/01-授权来源与只读基线.md`。

### 阶段 1：材料清点、可读性与来源定位

1. 按自然边界切分材料，保留页码、段落、文件哈希、时间和来源类别。
2. 对扫描件执行 OCR 后抽样核验；关键数字、日期、主体、条款和引文必须回看原页。
3. 输出 inventory、readability report 和 provenance ledger。
4. 不可读、缺页或来源断裂时进入 `HOLD-READABILITY` 或 `HOLD-PROVENANCE`。

### 阶段 2：按材料类型路由并形成全局理解

- **案件**：建立人物/主体、请求、抗辩、事件、证据、程序、法源七类索引。
- **书籍/课程**：先做结构、主旨、术语、作者假设、时代局限和反方观点的全局图。
- **实务经验**：记录讲述者角色、样本范围、适用地区、时间窗口和幸存者偏差。
- **混合材料**：先分源提取，再在验证知识层合并，不在私域层直接拼接。

详见 `references/02-三类材料提取协议.md`。

### 阶段 3：盲测与答案键隔离

案件型或有既有成品的任务必须：

1. 冻结回溯测试截止点；
2. 将答案键、裁判结果、既有结论和提示性文件移出起草者可见范围；
3. 先生成独立答案，再由验收席对照答案键；
4. 把泄漏、越界读取和后见之明偏差记入审计记录。

答案键边界无法证明时进入 `HOLD-ANSWER-KEY`。

### 阶段 4：多镜头并行提取

至少使用下列六个镜头；可以并行，但必须输出到候选池：

1. **规则与框架**：法律构成、程序路径、决策树。
2. **事实与证据**：证明对象、证据组合、反证和缺口。
3. **案例与变体**：成功路径、失败路径、不同事实组合。
4. **实务动作**：触发条件、步骤、输出、升级点。
5. **反例与误用**：失效场景、诱饵事实、常见混淆。
6. **术语与法源**：概念、同义词、法域、效力层级和时效。

本阶段宁可多提取，不直接晋升 Skill。每个候选都保留来源定位和候选状态。

### 阶段 5：原子知识记录与 SSOT

将候选转为 `templates/atomic-knowledge-record.schema.json` 约束的原子记录。每条记录只能表达一个可判断命题或一个可执行动作，至少包含：

- 来源类型、定位、哈希和截止日；
- 命题、适用条件、执行步骤、证据和法源；
- 置信度、隐私等级、权利状态、失败模式；
- 候选状态和可公开投影字段。

状态只能是 `candidate`、`verified`、`rejected`、`human_review_required` 或 `hold`。被淘汰记录进入 `rejected/` 并保留理由，禁止静默删除。

### 阶段 6：法律四重验证与候选晋升

每个候选逐项验证：

1. **L1 来源忠实度**：命题能否被准确定位和复核，是否遗漏关键限定。
2. **L2 法源与时效**：现行有效性、效力层级、法域、施行/废止/修订状态是否明确。
3. **L3 可复现与边界**：能否在至少两个独立样本或反事实变体中成立，失效条件是否显式。
4. **L4 原创增量与误用风险**：相较常识或已有 Skill 是否带来可执行增量，是否会诱发未经授权执业、过度承诺或隐私泄露。

L1/L2 失败不得晋升；L3/L4 不明进入人工复核。详见 `references/03-法律四重验证与候选晋升.md`。

### 阶段 7：构造 Skill、链接图与输出契约

按“触发、输入、动作、输出、边界、证据、升级”构造每个 Skill：

- description 同时覆盖应触发和不应触发语义；
- 新案型先清点已验证领域基线的全部门禁，并在 Sublation 矩阵中逐项作出 `保留`、`强化`、`替换`、`组合` 或 `舍弃`；donor 门禁与决策记录必须一一对应，漏项、重复或无证据舍弃均进入 `HOLD-BASELINE-INHERITANCE`；
- 动作必须可执行，输出必须通过 `templates/output-contract.schema.json`；本 RC 只允许 `court_submission` 与 `professional_service` 两类产物；
- 每类输出明确 audience、source SSOT、允许字段、脱敏规则、升级门和失败状态；派生物必须 `write_back=false`；
- 法院提交件、专业服务件和治理 sidecar 使用不同物理目录，治理记录不得进入法院可见文本；
- 相邻 Skill 建立 `precedes`、`requires`、`conflicts_with`、`supports`、`supersedes` 链接；
- 法律结论附法源状态，经验性结论附样本边界；
- 人工判断点不得伪装成自动化确定结论。

#### 可选诉讼可视化扩展

案件型子 Skill 只有在用户明确请求时，才可按 `trigger=on_request` 路由诉讼可视化。该能力使用 `professional_service.litigation_visualization` 子配置，仍属于既有 `professional_service` 产物类，不新增顶层产物类别。

1. 子 Skill 先冻结 `L2-05` 诉讼方案工作底稿，并按 `templates/L2-05-ANCHOR-CONTRACT-v1.json` 保留九个稳定语义区；缺失内容必须登记为 `empty_hold`，不得回到原始案卷猜填。
2. 从冻结底稿派生不复制事实文本的 anchor-map，再生成 `templates/litigation-visualization-handoff-v1.schema.json` 约束的 handoff。底稿、anchor contract、anchor-map、母 Skill、子 Skill、下游 Skill 和 validators 均须绑定版本与 SHA-256。
3. 运行 `scripts/validate_litigation_visualization_handoff.py`。新蒸馏子 Skill 的 `capability_status` 默认为 `hold`；只有底稿冻结、账本完整、隐私授权、下游 semantic spec 验证和独立语义复核五门全部通过时，单次 run 才可令 `render_allowed=true`。
4. 下游 `litigation-visualization-cn` 独立消费 handoff；母 Skill 和案型子 Skill 不得内置 renderer、渲染依赖或第二套事实模型。v1 只允许 `case_process_flow` 与 `claim_evidence_matrix`。
5. anchor-map、handoff、验证报告和 release receipt 是治理 sidecar，必须与用户可见图件物理分离；可视化不得反写 L2、SSOT、法院件或既有九文书。
6. 隐私、法源、定位、validator 哈希或独立复核任一不闭合，即保持 `HOLD-OUTPUT-CONTRACT`、`HOLD-PRIVACY`、`HOLD-LEGAL`、`HOLD-PROVENANCE` 或 `HOLD-E2E`，禁止渲染和外发。

完整契约、锚点、角色分工和晋升门见 `references/10-诉讼方案底稿与可视化扩展契约.md`。

输出契约缺失、产物类别未登记或试图反写 SSOT 时进入 `HOLD-OUTPUT-CONTRACT`。任何新增产物类别必须另走一次 Sublation、回归和用户授权，不得在本 RC 中隐式扩展。详见 `references/09-领域基线继承与产物门禁.md`。

### 阶段 8：压力测试与独立验收

每个 Skill 至少包含：

- 3 条 `should_trigger`；
- 3 条 `should_not_trigger`，其中至少 1 条应触发相邻 Skill；
- 2 条 `edge_case`；
- 1 条隐私诱饵、1 条过期法源诱饵、1 条误用诱饵；
- 案件型 Skill 另做答案键盲测和事实变体回归。

案件型 Skill 还必须通过以下硬门：

1. **领域基线覆盖**：donor inventory 与 Sublation 决策集合完全相等，`missing_gate_ids=[]` 且 `duplicate_gate_ids=[]`；否则 `HOLD-BASELINE-INHERITANCE`。
2. **法院件纯净度**：排除明确填充占位符后，法院可见文本中的 `SSOT`、`P0`、`L1`、`L2`、`cutoff`、`HOLD` 等治理词命中为 0，未解析占位符和非中文异常命中为 0；否则 `HOLD-COURT-TEXT`。
3. **DOCX 稳定性**：只要输出 DOCX，就必须固定字体双遍渲染，逐页像素哈希完全一致，稀疏页为 0，并检查可编辑性、OOXML、表格和外部关系；否则 `HOLD-RENDER`。
4. **真实任务 E2E**：至少完成一套完整九文书案和一套应正确触发 HOLD 的个案；构建席与验收席不同，答案键保持隔离；否则 `HOLD-E2E`。
5. **产物分层**：法院提交件、专业服务件、治理 sidecar 不得混装，输出契约和实际目录必须一致；否则 `HOLD-OUTPUT-CONTRACT`。

未达阈值时回到阶段 5–7 重建，不只修改 description。验收席不得读取起草推理过程，只读取输入许可、产物和验收标准。

### 阶段 9：Sublation 扬弃

对原创基底、仓颉方法和 GEO 方法逐项作出：`保留`、`强化`、`替换`、`组合` 或 `舍弃`。每项必须记录证据、对法律工作的影响和回归测试；不得以“已合并”代替比较。

使用 `templates/Sublation比较矩阵.md`，完整规则见 `references/05-Sublation扬弃矩阵.md`。

### 阶段 10：GEO 公开投影与测量

仅处理 `privacy_class=public`、`rights_status=cleared`、四重验证通过且获得独立发布授权的记录。

1. 从验证知识层生成直接回答、分层标题、步骤、表格、FAQ、定义和知识卡。
2. 生成 JSON-LD 与 `llms.txt` 草案，但不得伪造组织、作者、评价、统计或法源信息。
3. 建立自然问题、同义改写、反向问题和边界问题组成的查询集。
4. 在多个引擎、多个时间点重复测量“是否被引用、引用是否忠实、来源是否吸收”。
5. 把可见性指标与法律正确性、客户转化、排名承诺分开报告。

GEO 不得接触私域材料。详见 `references/06-GEO公开发布与测量协议.md`。

### 阶段 11：冻结、签名与发布门

1. 验证结构、JSON、隐私、法源状态、测试结果、无符号链接和无缓存文件。
2. 生成文件清单和 SHA-256；由独立席复算。
3. 记录构建、隐私、法律和人工验收四个席位的结论。
4. 本地冻结完成后仍保持 `external_publish_authorized=false`，直到用户单独批准。
5. 安装到正式 Skill 根、同步知识库、对外发布和 GEO 上线均是独立动作。

## HOLD 状态

| 状态 | 触发条件 | 恢复条件 |
|---|---|---|
| `HOLD-AUTHORIZATION` | 案件或材料使用授权不明 | 授权范围被书面确认 |
| `HOLD-RIGHTS` | 版权、许可或公开权不明 | 权利清理完成或改为仅内部使用 |
| `HOLD-PRIVACY` | 私人信息可能进入派生物 | 脱敏、允许清单与独立复核通过 |
| `HOLD-READABILITY` | OCR、缺页或格式导致关键内容不可读 | 修复并抽样复核 |
| `HOLD-ANSWER-KEY` | 答案键隔离或截止点无法证明 | 重建盲测环境 |
| `HOLD-PROVENANCE` | 命题无法定位回原始来源 | 补齐定位或降级为未验证 |
| `HOLD-EVIDENCE` | 证据链不能支持事实命题 | 补证或缩小命题 |
| `HOLD-LEGAL` | 法源效力、时效或法域不明 | 法源复核完成 |
| `HOLD-MISUSE` | 产物可能导致过度承诺或越权使用 | 增加边界、人工升级或舍弃 |
| `HOLD-GEO-FIDELITY` | GEO 表达改变原命题或引用失真 | 回退公开投影并重做 |
| `HOLD-BASELINE-INHERITANCE` | 已验证领域门禁未被逐项处理 | 补齐 donor inventory、决策和回归证据 |
| `HOLD-OUTPUT-CONTRACT` | 输出类别、分层、字段或读写方向不合规 | 修复结构化契约并重建派生物 |
| `HOLD-COURT-TEXT` | 法院件出现治理词、未解析占位符或语言异常 | 清理可见文本并重跑扫描 |
| `HOLD-RENDER` | DOCX 双遍渲染、像素、稀疏页或 OOXML 门失败 | 修复版式并双遍复验 |
| `HOLD-E2E` | 完整九文书案或 HOLD 个案未通过独立 E2E | 补齐盲态任务与独立验收 |
| `HOLD-RELEASE` | 安装、晋升或发布未获独立批准 | 用户明确批准对应动作 |

HOLD 只阻断受影响的下游步骤，不允许删除问题或用低置信度掩盖。

## 角色分离

| 席位 | 职责 | 禁止事项 |
|---|---|---|
| 构建席 | 清点、提取、SSOT、Skill 与测试 | 自我批准、读取被隔离答案键 |
| 隐私席 | 授权边界、脱敏、公开允许清单 | 代替法律席判断实体法正确性 |
| 法律席 | 法源、逻辑、边界、误用风险 | 修改冻结原件、代替用户发布 |
| 验收席 | 盲测、哈希复算、最终人工判断 | 依赖起草者自述替代证据 |
| 用户 | 最终验收、安装、晋升与发布授权 | 可委托执行，但授权必须显式记录 |

席位可由不同代理或人员承担，但同一产物的构建席与最终验收席不得为同一主体。

## 完成定义

只有同时满足以下条件，才可称为“本地候选包完成”：

- 授权、权利、隐私、可读性、来源、法源和误用状态均有记录；
- 原始案件载荷、答案键、个人身份信息、凭据和本机绝对路径均未进入包；
- SSOT、候选、淘汰、测试和 Sublation 轨迹齐全；
- 已验证领域基线逐项覆盖，输出契约与物理分层一致；
- 案件型 Skill 的法院文本、DOCX 双遍渲染和双案例 E2E 门均有可复算证据；
- 所有 JSON 可解析，结构测试和隐私扫描通过；
- 法律正确性与 GEO 可见性指标分开报告；
- 哈希已生成并可独立复算；
- `external_publish_authorized=false`，除非用户另行明确批准。

本地候选包完成不等于正式安装、生产晋升或外部发布。
