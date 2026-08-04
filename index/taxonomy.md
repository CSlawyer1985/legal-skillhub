# Legal SkillHub 标签体系（Taxonomy）

> **版本**：v0.1（2026-08-04）
> **地位**：本文件是标签体系的唯一权威定义。`build_index.py` 按本文件生产标签；网站筛选器按本文件展示。
> **治理规则**：标签代码（slug）保持稳定；中文显示名可改；新增枚举值追加于本文件并递增版本号；法域/许可/风险三维度的自动分类结果必须经复核才可视为已审核。

---

## 〇、设计原则

1. **标签不是越多越好**。信息分四类：分类标签（筛选）、结构化字段（排序/程序处理）、描述字段（解释）、关系字段（关联）。只有"用户会据此筛选 + 同一取值重复适用 + 取值稳定 + 可形成受控词表"的信息才做标签。
2. **三层元数据**：
   - A. 前台核心筛选标签（首页可筛）
   - B. 前台详情信息（详情页展示，不做筛选）
   - C. 后台治理元数据（JSON 保留，不上前台）
3. **三层发布标准**：T1 基础收录（全量）→ T2 可公开展示（全量）→ T3 可信 Skill（人工精选）。
4. **主+次结构**：任务、领域允许主 1 + 次 ≤5；法域 1-4；角色 ≤2。不确定记置信度（high/medium/low）。

---

## 一、legal_task 工作任务（首屏筛选）

> 回答"这个 Skill 帮我完成什么工作"。主 1 + 次 ≤5。

| 代码 | 中文 | 说明 | 高频信号 |
|------|------|------|----------|
| legal-research | 法律检索 | 法规/案例/监管文件检索、引证核查 | 检索、法条、案例库、search |
| legal-analysis | 法律研究 | 争议问题研究、比较法、立法沿革 | 研究、分析、memo |
| doc-reading | 文件阅读 | 摘要、要素提取、时间线、主体识别 | 摘要、提取、summary、extract |
| contract-work | 合同工作 | 起草、审查、红线、比较、履约 | 合同、contract、起草、审查 |
| litigation | 诉讼仲裁 | 案情分析、诉讼策略、证据、文书 | 诉讼、仲裁、起诉、litigation |
| due-diligence | 尽职调查 | 公司/资产/诉讼/合规/知产尽调 | 尽调、due diligence |
| compliance | 合规管理 | 风险识别、政策制定、监管报告 | 合规、compliance |
| legal-writing | 法律写作 | 备忘录、意见书、函件、报告 | 意见书、memo、letter |
| knowledge-mgmt | 知识管理 | 分类、归档、模板管理 | 知识库、模板 |
| client-project | 客户与项目管理 | 访谈、报价、进度、计费 | 谈案、计费、billing |
| calculation | 计算与量化 | 利息、赔偿、期限、费用 | 计算、calculator |
| education | 教学培训 | 案例教学、题目生成、模拟训练 | 法考、刷题、quiz、培训 |
| translation | 翻译本地化 | 法律翻译、术语校对 | 翻译、translation |
| quality-control | 质量控制 | 事实核查、引用核查、一致性审查 | 核查、verify |
| automation | 自动化执行 | 批量处理、文件生成、系统录入 | 批量、自动化 |

## 二、area_of_law 法律领域（首屏筛选）

> 回答"处理哪一类法律问题"。主 1 + 次 ≤5。**与工作任务正交**："合同审查"是任务不是领域；"施工合同审查" = 领域（建工+合同法） × 任务（合同审查）。

| 代码 | 中文 | 高频信号 |
|------|------|----------|
| general-civil | 民商综合 | 民法典、民事 |
| contract-law | 合同法 | 合同、contract、违约 |
| corporate | 公司商事 | 公司法、股权、治理、LLC、并购 |
| investment-ma | 投融资并购 | PE/VC、投资、并购、融资 |
| securities | 证券资本 | 证券、SEC、上市、Reg D |
| banking-finance | 银行金融 | 银行、信贷、AML、KYC |
| insurance | 保险 | 保险、insurance、理赔 |
| real-estate | 房地产 | 房地产、不动产、real estate |
| construction | 建工基建 | 建设工程、施工、construction、EPC |
| ip | 知识产权 | 专利、商标、著作权、patent、trademark |
| data-privacy | 数据隐私网安 | GDPR、PIPL、个人信息、数据合规、CCPA |
| ai-tech-law | AI 与科技法 | AI Act、算法、AIGC |
| labor | 劳动社保 | 劳动、工伤、社保、employment、EEOC |
| tax | 税法 | 税、增值税、个税、tax、IRS |
| antitrust | 反垄断 | 垄断、antitrust、competition |
| consumer | 消费者 | 消费者、消保、consumer、FTC |
| advertising | 广告电商 | 广告法、虚假宣传、电商 |
| intl-trade | 国际贸易海关 | 出口管制、制裁、EAR、OFAC、海关 |
| environmental | 环境气候 | 环境、环评、EPA、NEPA、EIR |
| life-sciences | 食药生命科学 | FDA、药品、医疗器材、510k |
| administrative | 行政监管 | 行政处罚、行政许可、行政法 |
| criminal | 刑事 | 刑事、量刑、辩护、criminal |
| civil-procedure | 民事诉讼 | 民诉、管辖、执行、FRCP |
| arbitration-adr | 仲裁与 ADR | 仲裁、调解、ICC、AAA、mediation |
| bankruptcy | 破产重组 | 破产、重整、清算、Chapter |
| family | 家事继承 | 婚姻、离婚、继承、遗嘱、divorce |
| public-rights | 公益人权 | 人权、human rights、公益 |
| intl-foreign | 涉外国际法 | 跨境、国际、cross-border、涉外 |
| legal-profession | 法律职业与律所管理 | 律所、律师管理、计费 |
| general | 综合跨领域 | 兜底 |

## 三、jurisdiction 法域（首屏筛选，1-4 个）

### 3.1 枚举（开放，可追加）

| 代码 | 中文 | 代码 | 中文 |
|------|------|------|------|
| china | 中国大陆 | uk | 英国 |
| hk | 中国香港 | de | 德国 |
| us | 美国（通用） | jp | 日本 |
| us-de | 美国·特拉华 | kr | 韩国 |
| us-ca | 美国·加州 | sg | 新加坡 |
| us-ny | 美国·纽约 | br | 巴西 |
| us-tx | 美国·德州 | in | 印度 |
| eu | 欧盟 | ca | 加拿大 |
| fr | 法国 | au | 澳大利亚 |
| international | 国际条约·跨境 | multi | 多法域比较 |
| general | 法域中立（兜底，需复核） | | |

### 3.2 判定规则

- **us 不常规拆分联邦/州**；仅当出现显式信号（Delaware、California/CCPA、New York、Texas）时追加子标签，与 us 共存。
- **eu 与成员国并存不互斥**：欧盟立法（GDPR、AI Act）→ eu；法国本土程序（assignation、tribunal、Légifrance）→ fr；法国 GDPR 落地 → eu+fr。
- **multi ≠ general**：multi = 主动比较 ≥2 个具名法域；general = 纯方法论、不绑定具名法律（兜底值，必须复核）。

### 3.3 判定优先级链（冲突时）

```
CN 专属词 → FR 专属词 → EU 专属词 → US 专属词 → 其他国别词 → 中文无信号回退 china → general
```

### 3.4 信号词三级权重（w3=具名法律 / w2=机构程序专名 / w1=通用词）

- **china**：w3 民法典、劳动合同法、个人信息保护法、数据安全法、广告法、公司法（中文语境）、法释〔；w2 最高人民法院、最高人民检察院、国务院、仲裁委、北大法宝、威科先行、指导案例；w1 人民法院、中国法院、中国法律
- **us**：w3 FRCP、FRBP、FRE、U.S.C.、C.F.R.、SOX、HIPAA、CCPA/CPRA、Title VII、ADA、ADEA、OWBPA、DTSA、IRC、Section 501(c)、30(b)(6)；w2 SEC、EEOC、FinCEN、IRS、FDA（美国语境）、FTC、OFAC、Delaware、Bluebook、Restatement；w1 U.S.、federal court、state law
- **eu**：w3 GDPR、AI Act、MiCA、NIS2、DORA、DMA、DSA、ePrivacy、Data Act；w2 EDPB、EMA、European Commission、DPO、SCC；w1 欧盟、European Union、EU/EEA
- **fr**：w3 Code civil、Code de commerce、RGPD（法语语境）、assignation en référé；w2 Judilibre、Légifrance、Conseil d'État、Cour de cassation、tribunal judiciaire、tribunal de commerce、作者后缀 -selim-brihi/-amaury-fouret/-christophe-quezel-ambrunaz；w1 tribunal、法国
- **其他**：uk（UK/England/Wales）、de（BGB/Bundesgericht）、jp（Japan）、kr（韩国/law.go.kr）、sg（Singapore）、br（Brazil/LGPD）、in（India/DPDP）、ca（Canada）、au（Australia）、hk（Hong Kong）
- **international**：UNCITRAL、New York Convention、CISG、WTO、跨境、cross-border

## 四、user_role 使用者角色（首屏筛选，≤2）

lawyer 律师 / paralegal 律师助理 / in-house 法务 / compliance-officer 合规人员 / judiciary 司法人员 / gov-legal 政府法制 / executive 公司管理者 / hr 人力资源 / investor 投资人员 / scholar 研究人员 / student 法学师生 / public 普通公众

> 弱信号维度，默认低置信；区分 designed_for（主要为谁设计）与 professional_required（是否要求专业背景）。

## 五、compatibility 兼容平台（首屏筛选）

claude-code / codex / universal-markdown 通用 Markdown skill / openclaw / other-cli 其他 CLI Agent / unknown 未知

> 本项目 skill 绝大多数为通用 Markdown skill；部分 Skill 声明了平台兼容标记（如 metadata.openclaw → openclaw 标记）。

## 六、input_type 输入类型（首屏筛选，≤3）

nl-question 自然语言问题 / contract 合同 / litigation-doc 诉讼文书 / judgment 判决书 / statute 法规 / evidence 证据材料 / corporate-doc 公司文件 / spreadsheet 表格 / pdf PDF / docx Word / xlsx Excel / image 图片 / webpage 网页 URL / batch 批量文件

## 七、output_type 输出类型（首屏筛选，≤3）

research-report 研究报告 / memo 备忘录 / legal-opinion 法律意见书 / contract-draft 合同或条款 / review-report 审查意见 / redline 红线稿 / risk-list 风险清单 / dd-report 尽调报告 / litigation-doc 诉讼文书 / evidence-list 证据目录 / timeline 时间线 / issues 争议焦点 / case-summary 案例摘要 / statute-list 法规清单 / compliance-report 合规报告 / checklist 检查表 / calculation 计算结果 / data-table 数据表格 / json JSON / slides 演示文稿 / letter 函件 / advice 操作建议

## 八、verification 验证状态（首屏筛选，徽章制）

> 不打总分，逐项独立。

| 代码 | 中文 | 达成条件 |
|------|------|----------|
| collected | 已收录未审核 | 默认状态 |
| metadata-reviewed | 元数据已审核 | LLM 复核或人工复核过标签 |
| install-verified | 安装已验证 | 人工实测安装成功 |
| sample-tested | 示例已运行 | 示例任务实际跑通 |
| legal-reviewed | 法律专业已审核 | 法律专业人员审核内容 |

## 九、高级筛选维度

### 9.1 industry 行业
finance 金融 / insurance 保险 / real-estate 房地产 / construction 建筑 / manufacturing 制造 / energy 能源 / internet 互联网 / ai 人工智能 / healthcare 医疗医药 / education 教育 / retail 消费零售 / ecommerce 电商 / government 政府 / professional-services 专业服务 / general 综合

### 9.2 workflow_stage 工作阶段
intake 客户接洽 / fact-collection 事实收集 / doc-organizing 文件整理 / issue-spotting 问题识别 / researching 法律检索 / analyzing 分析论证 / strategizing 策略制定 / drafting 起草 / reviewing 审核修改 / negotiating 谈判 / filing 申报提交 / pretrial 庭前准备 / trial 庭审 / enforcement 执行 / contract-mgmt 履约管理 / ongoing-compliance 持续合规 / archiving 结项归档

### 9.3 skill_type 技能类型（程序化判定）
instruction 指令型 / prompt-template 模板型 / checklist 清单型 / workflow 工作流型 / tool-wrapper 工具封装 / code-package 代码包 / knowledge-pack 知识包 / hybrid 混合

> 结构映射优先级：含 scripts ≥2 → code-package/tool-wrapper；含 references ≥3 → knowledge-pack；含 assets 模板 ≥2 → prompt-template；仅 SKILL.md(±LICENSE) → instruction；满足 ≥2 强条件 → hybrid。

### 9.4 automation_level 自动化等级
L0 知识参考（仅规则模板） / L1 单次辅助（单次输入生成） / L2 结构化工作流（预设步骤连续处理） / L3 工具调用（搜索/文件/API） / L4 有限自主（规划-执行-检查-重试）

### 9.5 deployment 部署方式
download 下载 skill 包 / git-clone / remote-command 远程安装命令 / copy-prompt 复制提示词 / none 无需安装

### 9.6 data_security 数据处理
处理位置：local 完全本地 / local-external-model 本地+外部模型 / cloud 云端 / unknown 未确认
权限（按 scripts 内容检测）：file-read / file-write / network / shell / api-call / external-submit

### 9.7 risk_level 风险等级
low 低（格式/摘要/教学） / medium 中（检索/初步分析/辅助审查） / high 高（法律意见/诉讼策略/合规判断/期限判断）
附：human_review_required 布尔（法律类默认 true）

### 9.8 language 语言（BCP47）
zh-CN / en（内容 CJK 密度检测，不用 frontmatter language 字段）

### 9.9 maintenance 维护状态
active / stale / archived / unknown（来源平台更新时间推定，默认 unknown）

## 十、license 授权（首屏徽章色）

### 10.1 规范化枚举（SPDX 短标识）

apache-2.0 / mit / mit-0 / cc-by-4.0 / cc-by-nc / cc-by-nc-nd-4.0 / cc-by-nc-sa-4.0 / agpl-3.0 / gpl-3.0 / proprietary / declared-only 仅声明 / undeclared 未声明

### 10.2 取值优先级

```
LICENSE 文件内容嗅探 > frontmatter 顶层 license（清洗小写、去尾随符号）
> metadata.license 嵌套 > 按具体 Skill 文件的授权声明推定
> undeclared
```

> **"没写许可证"不能视为开源。**

### 10.3 license_risk 四级色（卡片徽章）

| 等级 | 颜色 | 含义 |
|------|------|------|
| open | 绿 | MIT/Apache/CC-BY 等宽松许可 |
| copyleft | 黄 | AGPL/GPL 传染性许可 |
| restrictive-nc | 橙 | CC-NC 系（禁止商业使用） |
| undeclared | 红 | 未声明授权（保留所有权利，已署名，权利人联系即下架） |

## 十一、增强标签

| 代码 | 类型 | 说明 |
|------|------|------|
| freshness | 布尔徽章 | 正文引用 2024-2026 年法规/公告 → "含新法" |
| curated | 布尔徽章 | 入选学习中心案例解剖 → ★精选 |

## 十二、关系字段（relations）

| 关系 | 说明 | 本项目数据来源 |
|------|------|----------------|
| alternatives 替代 | 内容重复或高度相似的其它 skill | 内容完全一致仅命名不同的版本 |
| complements 互补 | 配套 skill | 同一 skill 家族中的协作组件 |
| derived_from 派生 | 改编自 | 内容相同或高度相似的不同收录版本 |

## 十三、标签数量限制

- 主工作任务：1 个；次工作任务：≤5
- 主法律领域：1 个；次法律领域：≤5
- 法域：1-4 个
- 适用角色：≤2
- 输入/输出类型：各 ≤3
- 卡片正面展示标签：≤5（其余进详情页）

---

**变更记录**
- v0.1（2026-08-04）：首版。

## 十四、质量评价拆分（不合并总分）

> **原则**：不制造虚假的客观性——每个维度独立成徽章/字段，有数据才上线，禁止过早合并为一个"质量总分"。

### 14.1 当前已上线的维度

| 维度 | 字段 | 测量对象 | 数据来源 |
|------|------|----------|----------|
| **结构完整度**（0-5） | `structure_score` | 包结构：references/scripts/LICENSE/描述长度/文件数，每项 1 分 | 程序化（probe_structure） |
| **元数据完整度** | T1/T2 字段覆盖率 | name/desc/法域/领域/任务/语言/授权等字段是否齐全 | 程序化（管线产出） |
| **验证状态** | `verification.status` | 已收录 / 元数据已审核 / 安装已验证 / 示例已运行 / 法律已审核 | 流程标记 |

### 14.2 后续按数据来源逐批上线（不一次性铺空维度）

| 维度 | 需要的数据 | 当前状态 |
|------|-----------|----------|
| 安装验证 | 人工实测安装 | 未开始（可对精选 T3 Skill 实测） |
| 任务成功率 | 评测集（evals/）+ 有/无 Skill 基线对比 | 未开始 |
| 法律准确性 | 法律专业人员审核 | 未开始 |
| 引用准确性 | 法条/案例引用抽查 | 未开始 |
| 输出稳定性 | 多次运行输出一致性测试 | 未开始 |
| 安全扫描 | 脚本权限/外联/危险调用静态扫描 | 部分数据已有（data_security 字段），可升级为徽章 |
| 维护活跃度 | 更新时间/版本记录 | 数据不全，暂缓 |

### 14.3 界面约定

- 首页排序"结构完整度"与卡片 `X/5` 分数**仅反映包结构**，不暗示任务质量或法律准确性
- 详情页以独立徽章呈现各维度（当前：结构完整度 + 验证状态），不合并总分
