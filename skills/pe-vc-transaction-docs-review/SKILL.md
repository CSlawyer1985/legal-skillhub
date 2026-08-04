---
name: pe-vc-transaction-docs-review
slug: pe-vc-transaction-docs-review
version: 0.1.14
displayName: "[Gardner's Vault] PE/VC私募交易文件审阅"
summary: "面向未上市公司股权融资，覆盖初稿、红线稿、跨文件冲突、市场惯例与重大问题清单。"
tags: ["法律", "PE/VC", "股权融资", "交易文件审阅"]
homepage: "https://github.com/hoangkiann-debug/PE_VC_transaction_docs_review"
description: "面向未上市公司股权融资的专业交易文件审阅能力。适用于境内人民币架构及红筹/VIE 美元架构（尽管当前使用比例有所下降）；支持公司/创始人方、投资人、领投/跟投及战略投资人等不同立场；可审阅首轮整套文件初稿，跟踪后续多轮红线版本，并核验跨文件之间的冲突；可输出完整的修改意见与建议、修订后版本、问题清单以及 Major Issue List（重大问题清单）等；突出优势是结合大量同类市场项目的统计数据，对于同一核心条款，不仅可提示市场主流做法与写法，还能提供不同做法的大致市场采用比例，并进一步给出相应的谈判建议。适用于增资协议、认购协议、股东协议、公司章程、SPA、SHA、IRA、M&A/M&AA、term sheet、side letter及Track Changes。基金设立备案、纯AMAC事项、破产重整投资、单独许可/BD合同及已上市公司证券争议不属于主要适用范围，除非与本次未上市公司投融资协议审阅直接相关。"
license: Apache-2.0
metadata:
  slug: "pe-vc-transaction-docs-review"
  version: "0.1.14"
  display-name: "[Gardner's Vault] PE/VC私募交易文件审阅"
  summary: "面向未上市公司股权融资，覆盖初稿、红线稿、跨文件冲突、市场惯例与重大问题清单。"
  tags: "法律, PE/VC, 股权融资, 交易文件审阅"
  short-description: "PE/VC未上市公司股权融资文件审阅与谈判辅助"
  creator: "Gardner's Vault"
  maintainer: "Gardner's Vault"
  copyright-holder: "Jiang Tao"
  homepage: "https://github.com/hoangkiann-debug/PE_VC_transaction_docs_review"
  support: "https://github.com/hoangkiann-debug/PE_VC_transaction_docs_review/issues"
  wechat-public-account: "加德纳的宝匣"
  last-reviewed: "2026-07-22"
  languages: "zh-CN, en"
---

# [Gardner's Vault] PE/VC私募交易文件审阅

## 创建与维护

- 创建者及官方维护者：Gardner's Vault
- 版权主体：Jiang Tao
- 官方仓库及问题反馈：https://github.com/hoangkiann-debug/PE_VC_transaction_docs_review
- 公众号：加德纳的宝匣

## 核心定位

面向未上市公司股权融资的专业交易文件审阅能力：

- 适用于境内人民币架构及红筹/VIE 美元架构（尽管当前使用比例有所下降）；
- 支持公司/创始人方、投资人、领投/跟投及战略投资人等不同立场；
- 可审阅首轮整套文件初稿，跟踪后续多轮红线版本，并核验跨文件之间的冲突；
- 可输出完整的修改意见与建议、修订后版本、问题清单以及 Major Issue List（重大问题清单）等；
- 相较一般能力的突出优势在于：结合大量同类市场项目的统计数据，对于同一核心条款，不仅可提示市场主流做法与写法，还能提供不同做法的大致市场采用比例，并进一步给出相应的谈判建议。

市场比例只作为谈判背景，不是法律要求。内部数据保留精确值用于计算和核验；用户可见输出默认四舍五入到整数百分比，并使用“约”“大约”或“不足1%”，不展示无必要的小数位。只有用户明确要求精确口径时，才提供精确值并同时说明样本期间和统计边界。法律效力、可执行性及监管问题必须另行核验现行一手法律依据。

### 与通用合同审阅的区别

本 Skill 的差异不在于多列几类风险，而在于形成五个相互校验的闭环：

1. **条款审阅闭环**：从风险定位直接走到可粘贴的完整修改条款、强弱替代方案和 Fallback，不停在原则性提醒。
2. **市场谈判闭环**：把核心条款的历史采用方向和整数概数转化为谈判位置、让步顺序和可接受区间，同时与法律结论严格分开。
3. **整套文件闭环**：同时检查主协议、股东协议、章程和配套文件中的定义、金额、股权、权利及争议解决冲突，而不是逐份孤立审阅。
4. **多轮谈判闭环**：用稳定 Issue ID 追踪已接受、部分接受、已拒绝、重新开启和新增问题，不因版本变化丢失谈判历史。
5. **个性化但不污染闭环**：允许用户固化长期偏好，但项目事实、特殊让步和保密信息不会自动变成下一项目的规则。

## 快速开始

用户无需配置或逐个运行本 Skill 的脚本。先读取用户指令和文件包，只询问文件中无法判断的必要信息。

最简单的用法：上传交易文件后直接说：

> 请使用 $pe-vc-transaction-docs-review 审阅这些文件。

只上传文件并说“审一下这套融资文件”“比较这两版协议”或英文的 “Review this financing document package” 时，也应隐式调用本 Skill。Skill 先自动识别可判断的信息，再一次性询问仍然缺少的审阅立场、交易架构、版本基线和交付方式，不要求用户学习脚本或提示词工程。

### 普通用户直接照抄

不熟悉专业术语时，无需理解下方内部流程，按需要复制其中一句即可：

- **第一次审整套文件**：`请从公司及创始方立场审一下这些融资文件。先告诉我最重要的问题；每个问题说明风险、怎么改、市场通常怎么做。看不懂或缺少的文件请直接告诉我下一步。`
- **审对方发回的修改稿**：`请把本轮文件和上一版比较，告诉我哪些问题已经解决、哪些还在、哪些是对方新加的，并更新重大问题清单。`
- **只问一个核心条款**：`请从投资人立场分析这条反稀释条款，说明风险、建议写法、替代方案，以及不同做法的大致市场采用比例。`

常用交付物的白话含义：

- **问题清单**：本轮发现的全部重要问题，以及每个问题的修改建议；
- **Major Issue List（重大问题清单）**：只保留需要双方重点谈判、需要客户决策的事项；
- **批注稿**：在Word中逐条加入审阅意见，但不改原文；
- **红线稿**：直接展示建议删改的协议版本，只有用户明确要求时制作。

默认先交付“问题清单 + 重大问题清单建议”。用户不用指定模板，也不用运行脚本；Agent 应按 `references/output-templates.md` 自动选择模板，并在交付前运行对应检查。

### 默认低门槛模式

- 用户只需上传文件并说“审一下”。Agent 先识别文种、语言、架构、适用法律、版本和可交付能力，不要求用户填写完整入项表。
- 只有两个缺口可以阻止对应的立场性判断：无法判断代表哪一方；后续红线稿需要判断接受/拒绝状态但缺少上一版或既有立场。其余信息优先从文件推断，并在输出开头列明假设。
- 若立场暂不明确，仍可先做中性的文件地图、可读性检查、版本识别和风险点定位；若版本基线缺失，仍可做当前文本风险审阅，但不得推断对方谈判状态。
- 默认交付为按风险排序的问题清单加 Major Issue List 建议。只有用户明确要求时，才增加原生批注、完整红线稿或其他重型交付。

英文及边缘场景可直接使用：

- `Review this Series A package from the investor's perspective and flag cross-document conflicts.`
- `Compare the current redline against the prior clean version and update the Major Issue List.`
- `Review the readable files first, list every unreadable or missing document, and state what remains unverified.`

### 多轮对话中的持续触发

- 同一事项中，用户说“继续审”“这是下一轮”“更新问题清单”或上传新版本时，保持本 Skill 激活，沿用已确认的事项轮廓和 Issue ID，但重新核验当前文件、版本和本轮范围。
- 用户中途改变审阅立场、交易架构、适用法律或交付模式时，重新进入相应入项门槛；先确认变更，再生成新的立场性建议，不把上一立场自动带入。
- 用户切换到另一项目或明确说“这是新项目”时，重置事项轮廓和版本链；除非用户明确授权，不沿用上一项目的事实、文件或谈判结论。

### 触发优先级

1. 用户显式调用 `$pe-vc-transaction-docs-review` 时直接触发。
2. 用户上传未上市公司融资交易文件并要求审阅、比较、批注或更新问题清单时隐式触发。
3. 仅出现“回购”“反稀释”等单个词时，须同时存在融资交易文件或明确的PE/VC语境；纯法律资讯、基金备案或上市公司证券事项不触发。
4. 文件损坏、加密或OCR失败不会取消触发；改为执行可读性预检，列出替代材料并继续处理其他可读文件。

### 个性化审阅偏好

- 本 Skill 可以按用户自己的职业经验和条款尺度定制，但不会在用户不知情时自动把单个项目的处理结果变成永久规则。
- 用户可以直接说明长期偏好，也可以复制并填写 `assets/review-preferences-template.md`，在每次审阅时与交易文件一并提供；可编辑的本地或 GitHub 版本也可将其作为固定偏好文件维护。
- 适用优先级为：本次明确指令和当前项目事实 > 用户偏好表 > 本 Skill 的默认立场与市场参考。偏好不能覆盖现行法律核验、文件事实或明确的风险披露要求。
- 只有用户明确确认“以后都按这个标准”时，才把本次形成的新尺度写回长期偏好表；项目特有的估值、金额、对方名称、特殊让步和保密信息不得自动写入长期偏好。

### 用户可见流程

1. 上传文件并说明“审一下”、代表哪一方或想要的交付物；文件中能判断的信息无需重复填写。
2. 只在必要时一次性回答缺失问题，例如审阅立场或哪一份是上一版。
3. 接收按风险排序的问题、修改建议和约定的批注、修订稿或 Major Issue List；如有不可读文件或待核验事项，会同时收到明确下一步。

下方16步是 Agent 的内部质量流程，不要求用户逐步操作、选择脚本或阅读全部参考文件。

### 运行条件

- 日常调用无需用户安装或配置脚本；由 Agent 按需调用 Skill 内工具。
- 文本、可搜索PDF和Word文件可直接处理；扫描PDF的OCR为可选能力，工具不可用时按 `references/faq-and-troubleshooting.md` 降级。
- 核心文件审阅、市场数据查询和一致性检查均可在本地完成，不依赖境外API；外部法律或企业信息连接器仅为可选核验能力，不影响现有文件的基础审阅。
- 运行前可由 Agent 执行 `python3 scripts/runtime_self_check.py --format json`；核心能力未就绪时使用 `RUNTIME-001`，可选能力缺失时按功能降级，不把整项工作误判为失败。
- Word原生批注依赖缺失时，不自行联网安装软件；继续生成完整批注计划，并明确说明本轮未生成原生批注文件。只有用户明确授权安装依赖后，才尝试补齐该能力。
- 脚本是确定性加速与校验工具，不是完成核心审阅的前提。脚本不可用时，Agent 仍须直接阅读可见正文，按条款清单人工建立文件地图、问题清单、重大问题清单、市场背景和修改建议；仅暂停必须依赖工具的OCR、Word原生批注或大规模自动比对，并清楚说明限制。
- 所有可控的外部只读请求统一以30秒为单次上限、最多自动重试2次；权限、登录、验证码、付费或参数错误不重试。超时后立即转为本地审阅，不阻塞整项工作。

### 首轮整套文件审阅

推荐提示词：

> 请从公司及创始方立场审阅这套人民币A轮融资文件。先检查文件版本和整套文件冲突，再输出问题清单、Word批注和重大争议清单。市场数据请作为谈判参考，法律问题请核验现行依据。

开始实质审阅前，应当从用户指令或文件中明确：

- 文件范围及是否为首轮整套审阅；
- 审阅立场；
- 人民币境内、境外美元直持或VIE架构；
- 适用法律及争议解决地；
- 交付模式：报告、批注、两者兼有，或用户明确要求的红线稿；
- 是否生成 Major Issue List；
- 输出语言。

### 后续红线稿审阅

推荐提示词：

> 请比较本轮对方红线稿与上一版，并结合上一轮问题清单，区分已接受、部分接受、拒绝、重新开启和新增问题，更新重大争议清单并在当前稿加入批注。

后续轮次还应确认：当前稿、上一版、上一轮问题清单/批注计划、原 Major Issue List、对方回复材料及本轮审阅范围。没有上一版或既有立场时，不得把文本变化直接判断为“已接受”或“已拒绝”。

## 典型使用案例

### 案例一：人民币融资，公司/创始方首轮审阅

- 输入：增资协议、股东协议、章程及交割文件。
- 重点：回购义务主体、创始人责任上限、反稀释、投资人否决权、注册资本缴纳及章程一致性。
- 输出：按风险排序的问题清单、市场数据、完整修改条款、Fallback及 Major Issue List。

### 案例二：美元架构，投资人侧整套审阅

- 输入：Share Subscription Agreement、Shareholders Agreement、M&A及VIE文件（如适用）。
- 重点：交割条件、清算优先、董事席位、保护性条款、信息权、创始人限制及境内外文件衔接。
- 输出：英文批注或报告；涉及中国法律相关事项，请咨询执业中国律师；涉及非中国法管辖事项，请咨询相应法域的执业律师。

### 案例三：第二轮对方红线稿

- 输入：当前红线稿、上一版、上一轮问题清单及谈判回复。
- 重点：识别已解决事项、表面接受但实质削弱的修改、重新开启事项和新增风险。
- 输出：增量审阅意见、更新后的 Word 批注和保持编号稳定的 Major Issue List。

### 案例四：复杂或不完整文件包

- 输入：扫描PDF、加密文件、缺少章程或缺少上一版的红线稿。
- 处理：可OCR则先OCR；加密或无法读取的文件明确标记为未实质审阅；缺少关键基线时只做有限审阅，不推断缺失文件“没有问题”。
- 输出：已审阅范围、未审阅文件、限制说明及继续完成所需材料。

## 核心工作流

### 按需读取规则

- 不一次性通读或加载全部 `references/`；先读取入项、质量门和保密三份必需文件，再按本次架构、立场、条款和交付模式选择其余资料。
- 大型JSON资料优先用 `scripts/benchmark_lookup.py` 或 `scripts/legal_authority_lookup.py` 精确查询，不把整个数据文件放入上下文。
- 只有出现相应问题时才读取OCR、连接器、VIE、红线跟踪或完整交付样例；单文件、单条款任务不加载无关模块。
- 每一步只保留与当前文件、当前条款和当前轮次有关的结果，避免不同项目或不同版本相互污染。

### 参考资料三层导航

| 层级 | 何时读取 | 文件 |
|---|---|---|
| 必读基础层 | 每个事项开始时 | `references/intake-and-routing.md`、`references/review-quality-gates.md`、`references/matter-profile-and-confidentiality.md` |
| 场景工作层 | 只按本次架构、立场、轮次和交付读取 | `references/rmb-structure-playbook.md` 或 `references/offshore-structure-playbook.md`；`references/party-side-positions.md`；后续稿读取 `references/multi-round-review.md`；交付读取 `references/output-templates.md` |
| 深度核验层 | 只有相关问题出现时 | 市场数据、法律依据、条款清单、压力测试、OCR、连接器、完整示例及评测文件 |

大型JSON只通过查询脚本读取；第一次使用需要看完整“上传到交付”过程时，直接读取 `references/complete-output-example.md` 的第0至第8节，无需浏览其余参考文件。

1. 读取 `references/review-quality-gates.md`、`references/intake-and-routing.md` 和 `references/matter-profile-and-confidentiality.md`，先完成事项识别和必要信息门槛；如用户提供审阅偏好表，再读取并按上述优先级应用。需要跨会话、长文件包或多轮续审时，用 `scripts/review_checkpoint.py init` 建立不含条款正文的进度文件。
2. 使用 `scripts/build_document_map.py` 建立整套文件地图。文件名只能作为文种、语言、架构和版本的初步线索，最终以正文为准。
3. 使用 `scripts/extract_contract_text.py` 提取全部范围内文件。提取为空或失败时，使用 `scripts/ocr_pdf.py` 自动选择macOS Vision或跨平台OCRmyPDF/Tesseract路径；也可在macOS直接使用 `scripts/ocr_pdf_macos.py`。仍不可读的文件必须标记为未实质审阅，并按 `references/faq-and-troubleshooting.md` 告知用户可执行的下一步。
4. 多文件项目使用 `scripts/build_package_matrix.py` 检查定义、金额、股权比例、权利安排和争议解决的候选冲突，再回到协议正文确认。
5. 根据主协议正文确定输出语言：中文文件使用中文，英文文件默认使用英文；保留原文中的定义、条款编号和法律术语。
6. Track Changes审阅使用 `scripts/extract_contract_text.py --scope track-changes`。优先阅读 `changed_paragraphs` 的修改前后文本；修改量过大时，先让用户选择全面、核心条款或 Major Issue List 聚焦模式。
7. 后续轮次读取 `references/multi-round-review.md`。没有原生修订标记但存在两份清洁稿时，可用 `scripts/compare_contract_versions.py <prior> <current>` 提取条款级差异，并人工确认低置信度匹配、拆分、合并和移位。
8. 外部连接器可能参与时，读取 `references/connector-degradation-policy.md`；目标主体事实影响审阅时，读取 `references/entity-and-diligence-data-layer.md`。准确区分已连接、已配置但未验证和不可用。
9. 按架构读取：人民币境内使用 `references/rmb-structure-playbook.md`；境外美元直持/VIE使用 `references/offshore-structure-playbook.md`。
10. 对照 `references/clause-review-checklists.md`、`references/recent-practice-stress-tests-2024-2026.md` 和 `references/negotiation-pattern-stress-tests.md`，把每个相关条款族标记为已审、无关、缺文件或暂缓。
11. 使用 `references/market-benchmarks-2024-2025.md`、`references/benchmark-data.json` 或 `scripts/benchmark_lookup.py` 查询市场背景。结构化数据固定包含23个唯一主题；交付前由 `scripts/validate_skill_consistency.py` 检查JSON可解析、主题无缺失/重复、必需字段完整。2025数据为主要锚点；2024与2025口径可比时使用两年平均；不可比时仅用2025并在内部记录。对外呈现按整数百分比概述，精确值只用于内部计算和核验。
12. 法律效力或可执行性问题读取 `references/legal-authority-protocol.md`、`references/legal-authorities.json`、`references/prc-law-risk-notes.md` 和 `references/article-digest.md`，并用 `scripts/legal_authority_lookup.py` 核验效力层级、状态、定位和日期。二手文章不是一手法律依据。
13. 按用户立场使用 `references/party-side-positions.md`。
14. 按 `references/output-templates.md` 和 `references/comment-only-review-mode.md` 交付；需要查看成品形态时读取 `references/complete-output-example.md`。Word批注必须锚定当前可见正文中的唯一原文片段，并另存输出文件，不覆盖源文件。
15. 首轮重大问题生成 Major Issue List；后续轮次使用 `scripts/update_major_issue_list.py` 保持 Issue ID 稳定并更新状态。状态必须遵循用户指定口径；对方在收到我方立场后返还的版本中明确保留争议文本时，标记为 Rejected，而不是 Open。
16. 交付前使用 `scripts/validate_issue_log.py`、`scripts/validate_major_issue_list.py` 和 `scripts/validate_skill_consistency.py` 完成适用的质量检查；再依据 `assets/review-completion-gate-template.json` 建立本事项总质检配置，并运行 `scripts/validate_review_completion.py`。只有状态为 `passed` 时才可无保留地表述“审阅完成”；`passed_with_limitations` 必须在交付首页突出披露限制；`blocked` 时不得作出任何完成表述。使用进度文件时同步标记已完成阶段和产物。中断后先运行 `scripts/review_checkpoint.py resume` 核验源文件指纹，再从首个未完成或已失效阶段继续，不重复已完成的外部动作。

以上16步各自都是自动保存点。长文件包在每完成一个文件或一个条款族后，还应运行 `scripts/review_checkpoint.py autosave` 记录稳定编号和产物路径；不等待整套审阅结束才保存。确实不适用的阶段使用 `review_checkpoint.py skip --reason` 明确标记，不得让它保持 `pending`；有限完成的阶段使用 `complete --limitation` 记录限制。进度文件不得写入合同正文、批注内容或审阅结论，只保存文件指纹、阶段状态、已完成单元的稳定编号和产物路径。OCR自动尝试全部可用本地引擎后仍失败时，必须立即输出 `OCR-MANUAL-001` 的三项替代材料清单并继续其他文件，不得停在技术错误上。


## 每项审阅意见的最低内容

- 文件、条款号、页码（如可得）及当前原文摘录；
- 问题及风险；
- 我方立场；
- 历史可比项目的市场数据及条款方向；
- 法律依据及核验状态（仅法律/效力问题必需）；
- 可以直接放入协议的完整修改条款；
- 更强、平衡或更轻的替代方案（适用时）；
- 对方不接受首选方案时的 Fallback；
- 需要客户或对方确认的事实。

不得把市场比例表述为法律要求，也不得把征求意见稿、会议纪要、二手文章或未经核验的数据库结果表述为现行有效法律。

## 交付模式

- **完整报告**：执行摘要、谈判优先级、覆盖矩阵、跨文件冲突及问题清单。
- **仅批注**：批注计划或经验证的 Word 原生批注，不修改协议可见正文。
- **报告加批注**：完整报告与逐条批注同时交付。
- **Major Issue List**：仅跟踪实质谈判问题，首轮建立、后续更新。
- **红线稿**：只有用户明确要求时才制作；首轮通常优先使用批注加问题清单。

脚本是内部执行工具，用户无需逐项配置。某项工具不可用时，应继续完成可可靠完成的部分，并按 `references/faq-and-troubleshooting.md` 使用统一问题编号说明：未完成什么、为什么、用户下一步做什么、哪些部分仍可继续。

## 常见问题

### 1. 只上传一份协议可以审吗？

可以，但会明确提示缺少哪些配套文件，以及因此无法完成哪些跨文件一致性判断。

### 2. 必须先告诉你代表哪一方吗？

最好明确。不同立场对回购、反稀释、清算优先、控制权和创始人责任的判断可能相反。文件中无法判断时，只询问这一必要问题。

### 3. 市场比例有什么作用？

用于判断条款是否偏离历史可比项目、主流方案在哪里以及可能的谈判空间，不用于证明条款合法或必然可执行。

### 4. 会直接改动原始Word文件吗？

不会。原生批注写入单独文件，并验证源文件未变、可见正文未变及批注结构有效；需要时可按应用报告回滚批注。

### 5. 没有上一版还能审对方红线稿吗？

可以做当前文本风险审阅，但不能可靠判断对方是否接受了上一轮立场，也不能完整还原版本变化；交付物会明确这一限制。

### 6. 香港、开曼或美国法条款能给最终结论吗？

不能替代相应法域执业律师的专业判断。统一提示为：涉及中国法律相关事项，请咨询执业中国律师；涉及非中国法管辖事项，请咨询相应法域的执业律师。

### 7. 能否按照我自己的审阅习惯长期使用？

可以。把常用立场、条款底线、可接受的 Fallback、风险偏好和输出习惯填写到 `assets/review-preferences-template.md`，每次审阅时一并提供，或在自己的本地/GitHub版本中长期维护。Skill 不会自动记住每次项目结果；只有经你明确确认的通用经验才应写回偏好表。

更多高频问题、问题编号、应避免的错误用法和逐步修复方法见 `references/faq-and-troubleshooting.md`。

## 常见错误用法与正确处理

| 错误用法 | 为什么不可靠 | 正确处理 |
|---|---|---|
| 只说“帮我审一下”，但没有文件或可定位文本 | 无法核对条款和版本 | 先提供文件、文件夹或明确条款文本 |
| 只给当前红线稿，却要求判断对方是否接受上一轮意见 | 缺少版本和既有立场基线 | 提供上一版、问题清单或授权有限审阅 |
| 把扫描失败、加密或损坏文件当作“没有问题” | 文件实际未被读取 | OCR、解密后重传，或明确标记为未实质审阅 |
| 把市场采用比例当成法律规定 | 市场惯例不等于法律效力 | 市场数据用于谈判，法律问题另查现行依据 |
| 要求自动覆盖原始Word文件 | 容易破坏源文件和审计链 | 始终另存批注或红线版本并保留验证报告 |
| 用本 Skill 审基金设立备案、已上市公司证券争议或独立BD许可协议 | 超出主要条款体系 | 改用对应专业流程，或先明确仅审与本轮未上市公司融资直接相关的部分 |
| 未经确认跨项目引用其他交易材料 | 可能混淆事项边界 | 默认只使用当前事项材料；跨事项比较需用户明确授权 |

### 边界场景判断

| 场景 | 是否适用 | 处理方式 |
|---|---|---|
| 未上市目标公司计划未来上市，当前审阅本轮融资协议 | 适用 | 审阅特殊权利终止、恢复及Pre-IPO安排 |
| 上市公司作为投资人投资未上市目标公司 | 适用 | 仍以未上市目标公司的本轮股权融资文件为审阅对象 |
| 已上市公司自身的证券发行、并购、对赌或回购争议 | 不适用 | 改用上市公司证券或并购专项流程 |
| 基金设立、备案或纯AMAC合规 | 不适用 | 改用基金设立或资管合规专项流程 |
| side letter、ESOP或VIE文件直接影响本轮融资权利 | 适用 | 纳入文件地图并核验与主协议、章程的一致性 |
| 独立许可、BD或商业合作合同，不影响本轮融资权利 | 不适用 | 改用对应合同审阅流程 |

## 质量与安全边界

- `references/review-quality-gates.md` 是完成标准：文件不可读、后续轮次缺基线却作接受/拒绝结论、或只依据未核验/草案来源作法律结论，均不算审阅完成。
- `scripts/validate_review_completion.py` 是最终完成状态的统一闸门：它汇总事项身份、源文件指纹、16个阶段、问题清单、重大问题清单、跨文件检查、Word批注完整性、交付文件、限制披露及判断性质量复核。该复核由审阅Agent自动填写证据，不要求用户另行操作；任一必需检查失败即返回 `blocked`。
- 已上市公司自身的对赌、回购或证券争议不进入本 Skill；未上市目标公司的Pre-IPO特殊权利安排，以及上市公司作为投资人投资未上市目标公司，仍可适用。
- 涉及中国法律相关事项，请咨询执业中国律师；涉及非中国法管辖事项，请咨询相应法域的执业律师。
- 不默认缺失的披露函、章程、side letter、ESOP、VIE文件或批准文件“没有问题”。
- 企业信息查询结果不能替代交易文件中的正式披露。
- 未经用户明确授权，不跨事项读取或比较其他项目材料。

评估或修改本 Skill 时，读取 `references/evaluation-protocol.md`，使用 `scripts/prepare_blind_evaluation.py` 准备隔离的模拟案例，并用 `scripts/score_blind_evaluation.py` 评分。自动检查不能替代独立律师按六个维度作出的人工质量评分。
