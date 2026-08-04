# OpenLegi 使用指南

## 简介

OpenLegi 是一个 MCP（Model Context Protocol，模型上下文协议）服务器，提供对 Legifrance 官方数据库的直接访问。它是本技能针对所有可通过 Legifrance 访问的文本和决定的**优先来源**。

**基本原则**：通过 OpenLegi 访问的任何来源均被视为**可靠**（Legifrance 官方数据）。反幻觉核查因而关注结果与用途之间的适配性，而非来源本身的可靠性。

## 可用性与加载

### 检测
在每项需要查询官方数据库的任务开始时，通过 `tool_search` 以“OpenLegi legifrance”之类的查询加载 OpenLegi 工具。

### 若 OpenLegi 不可用
- 完全切换至**web_search**并使用可靠来源（见 `sources-fiables.md`）
- 告知用户：“本会话中 OpenLegi 工具不可用。检索通过 web_search 在官方来源上进行。结果可能不如原先精确。”
- **绝不阻塞任务**：OpenLegi 不可用不得妨碍技能的执行。

## 可用工具（12 个）

### 1. `OpenLegi:lister_codes_juridiques`
**用途**：获取 67 部可用法典的完整列表。
**参数**：无。
**何时使用**：在使用 `rechercher_code` 之前识别法典的准确名称（名称必须 EXACT 精确）。

### 2. `OpenLegi:rechercher_code`
**用途**：在特定法典内检索条文。
**参数**：
- `code_name`（必填）：法典的准确名称（有疑问时使用 `lister_codes_juridiques`）
- `search`（必填）：检索词
- `champ`：ALL（默认）、TITLE、NUM_ARTICLE、ARTICLE、TEXTE
- `page_number`、`page_size`：分页
- `sort`：PERTINENCE（默认）、DATE_ASC、DATE_DESC
- `type_recherche`：TOUS_LES_MOTS_DANS_UN_CHAMP（默认）、EXACTE、UN_DES_MOTS、AUCUN_DES_MOTS、AUCUNE_CORRESPONDANCE_A_CETTE_EXPRESSION

**返回数据**：
- 条文标识符（LEGIARTI）、条文 CID
- **法律状态**（VIGUEUR 有效、ABROGE 废止等）——**为时间核查系统性利用**
- **生效起始日期**、**生效结束日期**——同上
- 条文号、在法典中的完整路径
- 条文全文
- 所引用的条文
- **Légifrance 链接**（提取并原样复制到交付物中，不加改动）

**提示**：要按准确编号检索条文，使用 `champ: "NUM_ARTICLE"` 和 `type_recherche: "EXACTE"`。

### 3. `OpenLegi:rechercher_jurisprudence_judiciaire`
**用途**：检索司法判例（最高法院、上诉法院）。
**参数**：
- `search`（必填）：检索词
- `champ`：ALL、TITLE、ABSTRACTS、TEXTE、NUM_AFFAIRE
- `juridiction_judiciaire`：按法院过滤（JSON 数组）
- `publication_bulletin`：按《公报》发表过滤
- `panorama`：`true` 仅返回元数据（避免冗长的全文）
- `page_number`、`page_size`：分页
- `sort`：PERTINENCE（默认）、DATE_ASC、DATE_DESC

**返回数据**：
- 标识符（JURITEXT）、法院、审理组成、性质
- 案号、判决日期、裁判结果
- 分类计划、摘要、所引文本
- 全文（除非 `panorama: true`）
- **Légifrance 链接**（提取并原样复制到交付物中，不加改动）

**提示**：要按上诉编号检索，使用 `champ: "NUM_AFFAIRE"` 和 `type_recherche: "EXACTE"`。

### 4. `OpenLegi:rechercher_jurisprudence_administrative`
**用途**：检索行政判例（最高行政法院、行政上诉法院、行政法院）。
**参数**：与司法判例类似，另加：
- `publication_recueil`：按《勒邦汇编》（Recueil Lebon）发表过滤
**返回数据**：结构相同，标识符为 CETATEXT。
**排序**：PERTINENCE（默认）、DATE_ASC、DATE_DESC

### 5. `OpenLegi:rechercher_decisions_constitutionnelles`
**用途**：检索宪法委员会的决定。
**参数**：类似，可用 `panorama`。
**排序**：PERTINENCE、DATE_ASC、DATE_DESC

### 6. `OpenLegi:rechercher_decisions_cnil`
**用途**：检索法国国家信息与自由委员会（CNIL）的决定。
**参数**：类似，可用 `nature_delib` 按审议类型过滤。
**排序**：PERTINENCE、DATE_ASC、DATE_DESC

### 7. `OpenLegi:rechercher_dans_texte_legal`
**用途**：在 LODA 数据库（法律、法令、命令、部令）中检索。
**参数**：
- `search`（必填）：检索词
- `text_id`：特定文本的标识符，用于在文本内部检索
- `champ`、`page_number`、`page_size`
- `sort`：PERTINENCE、PUBLICATION_DATE_DESC、PUBLICATION_DATE_ASC、SIGNATURE_DATE_DESC、SIGNATURE_DATE_ASC
- `type_recherche`

**⚠️ 注意**：排序参数与法典和判例不同。

### 8. `OpenLegi:recherche_journal_officiel`
**用途**：检索法兰西共和国《官方公报》（Journal Officiel）。
**参数**：
- `search`（必填）：检索词
- `max_results`：最大结果数
- `text_types`：按文本类型过滤（JSON 数组，例如 `["LOI", "DECRET"]`）。见 `lister_natures_textes_jorf`
- `emetteurs`、`ministeres`：按发布机关／部委过滤
- `date_publication`：按日期过滤
- `sort`：PERTINENCE、SIGNATURE_DATE_DESC、SIGNATURE_DATE_ASC、PUBLI_DATE_DESC、PUBLI_DATE_ASC
- `champ`、`type_recherche`

**关键注意**：系统性地适用 SKILL.md 的规则 5（JORF 来源定性）。核查每份文件的性质并定性其法律效力范围。

### 9. `OpenLegi:dernier_journal_officiel`
**用途**：获取最新出版的《官方公报》。
**参数**：
- `nb_jo`：要返回的 JO 份数
- `llm_formatter`：面向 LLM 优化的格式

### 10. `OpenLegi:lister_natures_textes_jorf`
**用途**：列出 JORF 中可用的 86 种文本性质。
**何时使用**：识别 `recherche_journal_officiel` 的 `text_types` 参数的有效值。

### 11. `OpenLegi:lister_emetteurs_jorf`
**用途**：列出 JORF 检索可用的发布机关／主管机构。
**何时使用**：按特定发布机关过滤 JORF 检索。

### 12. `OpenLegi:rechercher_conventions_collectives`
**用途**：检索集体协议（KALI 数据库）。
**参数**：与 `rechercher_dans_texte_legal` 类似，可用 `panorama`。
**排序**：PERTINENCE、DATE_ASC、DATE_DESC

## 按响应类型提取 Légifrance 链接

每条 OpenLegi 响应都在其元数据中包含一个 Légifrance 链接。该链接是交付物中要复制的链接的**唯一合法来源**：绝不凭记忆或类比重建。下表按 OpenLegi 工具汇总了预期的 URL pattern 和响应中可找到它的字段。

| OpenLegi 工具 | 预期 URL pattern | 枢轴标识符 |
|---|---|---|
| `rechercher_code` | `https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI…` | `LEGIARTI…` 或 `CID 条文` |
| `rechercher_jurisprudence_judiciaire` | `https://www.legifrance.gouv.fr/juri/id/JURITEXT…` | `JURITEXT…` |
| `rechercher_jurisprudence_administrative` | `https://www.legifrance.gouv.fr/ceta/id/CETATEXT…` | `CETATEXT…` |
| `rechercher_decisions_constitutionnelles` | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT…` 或专用页面 | `JORFTEXT…` |
| `rechercher_decisions_cnil` | `https://www.legifrance.gouv.fr/cnil/id/CNILTEXT…` | `CNILTEXT…` |
| `rechercher_dans_texte_legal`（LODA） | `https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI…` 或 `…/loda/id/LEGITEXT…` | `LEGIARTI…` 或 `LEGITEXT…` |
| `recherche_journal_officiel` | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT…` | `JORFTEXT…` |
| `rechercher_conventions_collectives`（KALI） | `https://www.legifrance.gouv.fr/conv_coll/id/KALITEXT…` | `KALITEXT…` |

**提取规则**：

1. 在 OpenLegi 响应中识别“Lien Légifrance”（Légifrance 链接）字段（或等效字段）。
2. **逐字**复制该链接，不加修改。
3. **绝不**根据猜测的标识符构建链接，也不得沿用先前会话的标识符。

**若 OpenLegi 响应中缺少链接**：将该引用标记为“待核查”或转换为无人称表述（见 `references/principes-cardinaux.md`）。

## 排序参数——汇总

| 数据库 | 可用排序 |
|------|-----------------|
| 法典（`rechercher_code`） | PERTINENCE、DATE_ASC、DATE_DESC |
| 司法判例 | PERTINENCE、DATE_ASC、DATE_DESC |
| 行政判例 | PERTINENCE、DATE_ASC、DATE_DESC |
| 宪法决定 | PERTINENCE、DATE_ASC、DATE_DESC |
| CNIL 决定 | PERTINENCE、DATE_ASC、DATE_DESC |
| LODA（`rechercher_dans_texte_legal`） | PERTINENCE、PUBLICATION_DATE_DESC/ASC、SIGNATURE_DATE_DESC/ASC |
| JORF（`recherche_journal_officiel`） | PERTINENCE、SIGNATURE_DATE_DESC/ASC、PUBLI_DATE_DESC/ASC |
| 集体协议 | PERTINENCE、DATE_ASC、DATE_DESC |

**⚠️** 使用无效排序会触发明确错误。有疑问时使用 PERTINENCE（始终有效）。

## 最优检索策略

### 检索具体法典条文
1. `rechercher_code`，使用准确的 `code_name`＋`search` ＝ 条文号＋`champ: "NUM_ARTICLE"`＋`type_recherche: "EXACTE"`
2. 核查元数据中的法律状态（VIGUEUR／ABROGE）和日期
3. 如条文在法典中找不到：通过 `lister_codes_juridiques` 核查法典的准确名称
4. **从响应中提取 Légifrance 链接**并复制到交付物中。

### 主题判例检索
1. `rechercher_jurisprudence_judiciaire`（或 `_administrative`），使用主题关键词＋`sort: "DATE_DESC"` 获取近期决定
2. 对大批量检索：使用 `panorama: true` 获取元数据而不获取全文
3. 对未找到的决定，用 `web_search` 在 Judilibre 或 Arianeweb 上补充

### 按编号检索具体判决
1. `rechercher_jurisprudence_judiciaire`，使用 `champ: "NUM_AFFAIRE"`＋`type_recherche: "EXACTE"`＋`search` ＝ 上诉编号
2. 如找不到：尝试在 Judilibre 或 Legifrance 上 web_search
3. **核查检索编号与返回判决之间的一致性**（在响应内容本身中）——这是必不可少的预防措施，典型事故是两个编号相近的判决被混淆。

### JORF 法律动态监测
1. `recherche_journal_officiel`，使用检索词＋`sort: "PUBLI_DATE_DESC"`＋按需的 `text_types` 过滤
2. 仅限规范性文本：`text_types: ["LOI", "DECRET", "ORDONNANCE", "ARRETE"]`
3. **始终定性**返回文档的性质（SKILL.md 规则 5）

### 法律文本检索（LODA）
1. `rechercher_dans_texte_legal`，使用检索词＋`sort: "PUBLICATION_DATE_DESC"` 获取最新文本
2. 如已知文本标识符：使用 `text_id` 在特定文本内部检索

## 错误处理

### 排序错误
若出现“Tri 'X' invalide”（排序“X”无效）错误消息：核查上文的排序表，并为相关数据库使用正确的排序。

### 法典名称错误
若出现关于法典名称的错误消息：使用 `lister_codes_juridiques` 获取准确名称。

### 空结果
- 核查拼写和检索词
- 尝试 `type_recherche: "UN_DES_MOTS"`（更宽松）
- 扩大检索字段（`champ: "ALL"`）
- 补充切换至 web_search

### 连接错误
若 OpenLegi 完全不可访问：
- 告知用户
- 切换至 web_search＋可靠来源
- 不阻塞任务执行

## 与技能规则的集成

### 反幻觉

- OpenLegi 结果直接来自 Legifrance：**来源可靠**。
- 核查针对**适配性**（是否正确的文本用于正确的用途？）、**时间状态**（文本是否有效？）和**链接可溯源性**（交付物中复制的 Légifrance 链接是否确实来自当前会话中获得的 OpenLegi 响应？）。
- 禁止杜撰引用仍然绝对：使用 OpenLegi 去寻找，绝不用于“确认”一条想象出来的引用。
- 禁止凭记忆重建 Légifrance 链接同样绝对。链接从 OpenLegi 响应中提取，别无他处。
- 在任何交付之前，以强制性的四列结构化表格（引注、工具＋标识符、相关文本摘录、✓／✗／改写）形式执行 `references/checklist-pre-livraison.md`，逐条实际引注进行。在 COWORK／CHAT_CU 中，`scripts/verify_links.py` 生成表格；在 CHAT（及降级模式）中，表格根据 OpenLegi 卡片页手工制作。交付以明确说出收尾公式为条件。

### 频繁重新编号与修改

法典和合并文本不断演变。技能**在任何情况下**都不得推定条文号或文本版本的稳定性，即使是“经典到极点”的条文：

- 《民法典》旧第 1382 条和第 1384 条经 2016 年 2 月 10 日第 2016-131 号命令变为第 1240 条和第 1242 条——<https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000032004939>。
- 《民法典》第 1242 条第 4 款——<https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006437058>——（父母责任）经 2025 年 6 月 23 日第 2025-568 号法律大幅修改——<https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051782996>。
- 历次重新编纂在所有法典中都会产生类似的重新编号。

**系统性地**通过 `rechercher_code` 核查有效文本版本（法律状态、生效起始／结束日期）。当文本最近经历过可能影响推理的修改时，明确注明适用版本。

### 时间适用性（SKILL.md 规则 4）

- **系统性利用** OpenLegi 返回的“法律状态”“生效起始日期”“生效结束日期”元数据。
- 未经核查这些字段，绝不引用条文。

### JORF 定性（SKILL.md 规则 5）

- **系统性核查** `recherche_journal_officiel` 结果中文档的性质。
- 在引注中定性其法律效力范围（规范性 vs 议会工作文件 vs 行政性）。
