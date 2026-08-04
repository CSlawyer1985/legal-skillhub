---
name: eu-pl-law-tracker

description: >
  欧盟法律文书及实施欧盟法规（如 PPWR、CBAM、EUDR、ESPR、CSRD、CSDDD、
  GPSR、AI 法案、电池法规、生态设计）的波兰法案和草案的搜索、下载和分析。
  当用户需要法律地位、适用日期、过渡条款、法案关系、合规义务以及
  附法律依据和官方来源的报告时使用。

metadata:
  author: "Grzegorz Skuza"
  license: "mit"
  version: "2026-07-12"
---

# EU/PL Law Tracker（欧盟/波兰法律跟踪器）

## 目标

确定欧盟法规以及相关波兰法案或草案的法律地位。基于官方来源工作，首选 EUR-Lex、欧盟官方公报、ELI、RCL、ISAP、法律公报（Dziennik Ustaw）、波兰议会（Sejm）和 gov.pl。

本技能涵盖 PPWR、CBAM、EUDR、ESPR、CSRD、CSDDD、GPSR、AI 法案、电池法规、生态设计等欧盟法规及其他行业性文书。不要将分析仅限于 PPWR。

## 绝对原则

1. 不要凭记忆编造 CELEX 编号、ELI、议会印件编号、项目编号或日期。如果缺乏可靠来源，标注缺口。
2. 不要将法律草案称为现行法律。
3. 不要将新闻稿、FAQ 或律所页面视为法律文书的替代品。
4. 对于欧盟条例，检查波兰是否已通过或正在审议确保其适用的条款：主管机构、制裁、程序、登记册、检查、费用、报告义务。
5. 将每个生效日期、适用日期、废止日期或义务期限与具体条款和来源挂钩。
6. 如果来源相互矛盾，优先顺序为：欧盟官方公报、EUR-Lex、法律公报（Dziennik Ustaw）、ISAP，然后才是 RCL、Sejm、gov.pl 和辅助来源。
7. 始终区分：现行法律、草案、非约束性官方材料、辅助来源和分析结论。

## 工作流

### 1. 识别法规

- 如果用户提供缩写，检查 `references/regulation-aliases.yaml`。
- 如果提供 CELEX，直接使用它。
- 如果提供文书编号，在 EUR-Lex 中搜索。
- 如果提供主题，识别最可能的文书并标注置信度级别。
- 如果存在多个可能的文书，显示候选列表并指明使用哪个作为主要文书。

示例输入：`PPWR`、`CBAM`、`32025R0040`、`2023/956 号条例`、`包装和包装废弃物`、`欧盟外水泥进口`。

### 2. 下载并核验欧盟文书

首选顺序：

1. EUR-Lex / 官方公报。
2. ELI `data.europa.eu/eli/...`。
3. EUR-Lex 文档信息。
4. EUR-Lex 立法程序。
5. 欧委会、通知、FAQ——仅作辅助。

至少确定：

- CELEX，
- ELI，
- 完整的波兰语和英语标题，
- 文书类型：条例、指令、决定、授权法案、实施法案，
- 文书状态，
- 文件日期、发布日期、生效日期和适用日期，
- 立法程序，
- 被废止、被修改的文书、实施法案、授权法案、合并版本和勘误。

如果使用编码工具，使用脚本：

- `scripts/eu_law_identify.py`——识别缩写、别名、CELEX 或文书编号。
- `scripts/eu_law_parse.py`——从下载的文本中提取最终条款、日期和关系。
- `scripts/legal_date_extractor.py`——从文书文本中提取期限和日期。
- `scripts/relation_extractor.py`——对法律关系进行分类。

### 3. 检查最终条款

始终检查文书的末尾条款和全文，而不只是摘要。在 `references/final-provisions-keywords.md` 中搜索短语。

对每个结果提供：条款、款、条款类型、规范含义、日期、主体、实际后果和来源。

### 4. 映射相关文书

将关系分类为：

- `repeals`——废止一项文书，
- `amends`——修改一项文书，
- `supplements`——授权法案补充主文书，
- `implements`——实施法案执行主文书，
- `corrigendum`——勘误，
- `consolidated_version`——合并版本，
- `procedure`——立法程序，
- `national_adaptation`——波兰配套条款，
- `national_sanctions`——波兰制裁条款，
- `competent_authority`——国家主管机构。

### 5. 检查波兰的状态

对每项欧盟文书确定：

- 波兰是否已通过配套法律或条例，
- RCL 中是否有政府草案，
- 草案是否已提交议会（Sejm），
- 文书是否已在法律公报（Dziennik Ustaw）上公布，
- ISAP 是否将该文书显示为现行、已废止或正在修改，
- 是否已指定主管机构，
- 是否存在制裁、程序、登记册、报告或检查义务，
- 是否存在 gov.pl 材料，但将其标记为非约束性。

使用 `references/polish-law-sources.md` 选择来源，使用 `references/legal-search-patterns.md` 构建查询。

### 6. 分类可信度

使用 `references/legal-reliability-rules.md`。将每个结果标记为以下类别之一：

- `现行法律来源`，
- `文书的官方版本`，
- `文书草案`，
- `非约束性官方材料`，
- `辅助来源`，
- `未确认`。

### 7. 准备报告

默认使用 `references/report-template.md` 中的结构。

## 简短回答格式

如果用户不要求完整报告，按以下布局回答：

- `法规`——识别了什么。
- `欧盟状态`——来源、CELEX/ELI、日期。
- `最终条款`——最重要的条款和后果。
- `波兰状态`——现行文书/草案/缺口。
- `需监测内容`——授权法案、实施法案、波兰条款、期限。
- `来源`——链接和可信度类别。

## 参考文件

- `references/source-map.md`——欧盟和波兰来源地图。
- `references/regulation-aliases.yaml`——法规别名和示例 CELEX。
- `references/eurlex-identifiers.md`——CELEX、ELI、官方公报、程序和链接模式。
- `references/polish-law-sources.md`——RCL、ISAP、Sejm、法律公报、gov.pl。
- `references/legal-search-patterns.md`——欧盟/波兰搜索查询。
- `references/legal-reliability-rules.md`——来源层级和分类。
- `references/report-template.md`——报告模板。
