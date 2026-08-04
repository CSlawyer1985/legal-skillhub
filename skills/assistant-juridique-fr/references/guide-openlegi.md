# OpenLegi 使用指南

## 介绍

OpenLegi 是一个 MCP（模型上下文协议）服务器，提供对 Legifrance 官方数据库的直接访问。它是本技能处理所有可通过 Legifrance 获取的文本和判决时的**优先来源**。

**基本原则**：通过 OpenLegi 访问的任何来源均被视为**可靠**（Legifrance 官方数据）。反幻觉核验因此聚焦于结果与其用途之间的适配性，而非来源本身的可靠性。

## 可用性与加载

### 检测
在每项需要在官方数据库中检索的任务开始时，通过 `tool_search` 以“OpenLegi legifrance”之类的查询加载 OpenLegi 工具。

### 如果 OpenLegi 不可用
- 完全切换至基于可靠来源的 **web_search**（见 `sources-fiables.md`）
- 告知用户：“OpenLegi 工具在本会话中不可用。检索将通过 web_search 在官方来源上进行。结果可能不够精确。”
- **绝不阻塞任务**：OpenLegi 不可用不得妨碍本技能的执行。

## 可用工具（12 个）

### 1. `OpenLegi:lister_codes_juridiques`
**用途**：获取全部 67 部可用法典的完整清单。
**参数**：无。
**何时使用**：在使用 `rechercher_code` 之前确认法典的准确名称（名称必须完全准确）。

### 2. `OpenLegi:rechercher_code`
**用途**：在特定法典内检索条款。
**参数**：
- `code_name`（必填）：法典的准确名称（如有疑问使用 `lister_codes_juridiques`）
- `search`（必填）：检索词
- `champ`：ALL（默认）、TITLE、NUM_ARTICLE、ARTICLE、TEXTE
- `page_number`、`page_size`：分页
- `sort`：PERTINENCE（默认）、DATE_ASC、DATE_DESC
- `type_recherche`：TOUS_LES_MOTS_DANS_UN_CHAMP（默认）、EXACTE、UN_DES_MOTS、AUCUN_DES_MOTS、AUCUNE_CORRESPONDANCE_A_CETTE_EXPRESSION

**返回数据**：
- 条款标识符（LEGIARTI）、条款 CID
- **法律状态**（VIGUEUR 现行有效、ABROGE 已废止等）——**为时间核验目的必须系统利用**
- **生效开始日期**、**生效结束日期**——同上
- 条款编号、法典内完整路径
- 条款全文
- 被引用的条款
- **Légifrance 链接**（须提取并无任何变造地转载到交付物中）

**提示**：要按确切编号检索条款，使用 `champ: "NUM_ARTICLE"` 和 `type_recherche: "EXACTE"`。

### 3. `OpenLegi:rechercher_jurisprudence_judiciaire`
**用途**：在司法判例（最高法院、上诉法院）中检索。
**参数**：
- `search`（必填）：检索词
- `champ`：ALL、TITLE、ABSTRACTS、TEXTE、NUM_AFFAIRE
- `juridiction_judiciaire`：按法院过滤（JSON 数组）
- `publication_bulletin`：按公报发表过滤
- `panorama`：设为 `true` 仅获取元数据（避免庞大的全文）
- `page_number`、`page_size`：分页
- `sort`：PERTINENCE（默认）、DATE_ASC、DATE_DESC

**返回数据**：
- 标识符（JURITEXT）、法院、审判组织、性质
- 案件编号、判决日期、裁判结果
- 分类框架、摘要、被引用文本
- 全文（除非 `panorama: true`）
- **Légifrance 链接**（须提取并无任何变造地转载到交付物中）

**提示**：要按上诉编号检索，使用 `champ: "NUM_AFFAIRE"` 和 `type_recherche: "EXACTE"`。

### 4. `OpenLegi:rechercher_jurisprudence_administrative`
**用途**：在行政判例（最高行政法院、行政上诉法院、行政法院）中检索。
**参数**：与司法判例类似，另加：
- `publication_recueil`：按《勒邦汇编》发表过滤
**返回数据**：结构相同，标识符为 CETATEXT。
**排序**：PERTINENCE（默认）、DATE_ASC、DATE_DESC

### 5. `OpenLegi:rechercher_decisions_constitutionnelles`
**用途**：检索宪法委员会的决定。
**参数**：类似，可用 `panorama`。
**排序**：PERTINENCE、DATE_ASC、DATE_DESC

### 6. `OpenLegi:rechercher_decisions_cnil`
**用途**：检索 CNIL 的决定。
**参数**：类似，可用 `nature_delib` 按审议类型过滤。
**排序**：PERTINENCE、DATE_ASC、DATE_DESC

### 7. `OpenLegi:rechercher_dans_texte_legal`
**用途**：在 LODA 数据库（法律、法令、政令、部令）中检索。
**参数**：
- `search`（必填）：检索词
- `text_id`：特定文本的标识符，用于在其内部检索
- `champ`、`page_number`、`page_size`
- `sort`：PERTINENCE、PUBLICATION_DATE_DESC、PUBLICATION_DATE_ASC、SIGNATURE_DATE_DESC、SIGNATURE_DATE_ASC
- `type_recherche`

**⚠️ 注意**：排序参数与法典和判例的不同。

### 8. `OpenLegi:recherche_journal_officiel`
**用途**：在《法兰西共和国官方公报》中检索。
**参数**：
- `search`（必填）：检索词
- `max_results`：最大结果数
- `text_types`：按文本类型过滤（JSON 数组，如 `["LOI", "DECRET"]`）。见 `lister_natures_textes_jorf`
- `emetteurs`、`ministeres`：按签发机关/部委过滤
- `date_publication`：按日期过滤
- `sort`：PERTINENCE、SIGNATURE_DATE_DESC、SIGNATURE_DATE_ASC、PUBLI_DATE_DESC、PUBLI_DATE_ASC
- `champ`、`type_recherche`

**关键注意**：必须系统适用 SKILL.md 规则 5（JORF 来源的定性）。核验每个文件的性质并定性其法律效力。

### 9. `OpenLegi:dernier_journal_officiel`
**用途**：获取最近发布的官方公报。
**参数**：
- `nb_jo`：返回的公报数量
- `llm_formatter`：为 LLM 优化的格式化

### 10. `OpenLegi:lister_natures_textes_jorf`
**用途**：列出 JORF 中可用的 86 种文本性质。
**何时使用**：确定 `recherche_journal_officiel` 的 `text_types` 参数的有效值。

### 11. `OpenLegi:lister_emetteurs_jorf`
**用途**：列出 JORF 检索可用的签发机关/机关。
**何时使用**：按特定签发机关过滤 JORF 检索。

### 12. `OpenLegi:rechercher_conventions_collectives`
**用途**：在集体协议（KALI 数据库）中检索。
**参数**：与 `rechercher_dans_texte_legal` 类似，可用 `panorama`。
**排序**：PERTINENCE、DATE_ASC、DATE_DESC

## 按响应类型提取 Légifrance 链接

任何 OpenLegi 响应都在其元数据中包含一个 Légifrance 链接。该链接是交付物中所转载链接的**唯一合法来源**：绝不可凭记忆或类比重建。下表按 OpenLegi 工具汇总了预期 URL 模式及响应中可找到该链接的字段。

| OpenLegi 工具 | 预期 URL 模式 | 核心标识符 |
|---|---|---|
| `rechercher_code` | `https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI…` | `LEGIARTI…` 或 `条款 CID` |
| `rechercher_jurisprudence_judiciaire` | `https://www.legifrance.gouv.fr/juri/id/JURITEXT…` | `JURITEXT…` |
| `rechercher_jurisprudence_administrative` | `https://www.legifrance.gouv.fr/ceta/id/CETATEXT…` | `CETATEXT…` |
| `rechercher_decisions_constitutionnelles` | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT…` 或专门页面 | `JORFTEXT…` |
| `rechercher_decisions_cnil` | `https://www.legifrance.gouv.fr/cnil/id/CNILTEXT…` | `CNILTEXT…` |
| `rechercher_dans_texte_legal` (LODA) | `https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI…` 或 `…/loda/id/LEGITEXT…` | `LEGIARTI…` 或 `LEGITEXT…` |
| `recherche_journal_officiel` | `https://www.legifrance.gouv.fr/jorf/id/JORFTEXT…` | `JORFTEXT…` |
| `rechercher_conventions_collectives` (KALI) | `https://www.legifrance.gouv.fr/conv_coll/id/KALITEXT…` | `KALITEXT…` |

**提取规则**：

1. 在 OpenLegi 响应中识别“Légifrance 链接”（或等效）字段。
2. **逐字**转载该链接，不作任何修改。
3. **绝不**根据猜出的标识符构建链接，也不得转用先前会话的标识符。

**响应中缺少链接时**：将该引用标注为“待核验”或改为非人称表述（见 `references/principes-cardinaux.md`）。

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

**⚠️** 使用无效排序会引发明确错误。有疑问时使用 PERTINENCE（始终有效）。

## 最优检索策略

### 检索特定法典条款
1. 使用 `rechercher_code`，`code_name` 准确 + `search` = 条款编号 + `champ: "NUM_ARTICLE"` + `type_recherche: "EXACTE"`
2. 核验元数据中的法律状态（VIGUEUR/ABROGE）和日期
3. 如在法典中找不到条款：通过 `lister_codes_juridiques` 核验法典的准确名称
4. **从响应中提取 Légifrance 链接**并转载到交付物中。

### 主题式判例检索
1. 使用 `rechercher_jurisprudence_judiciaire`（或 `_administrative`），主题关键词 + `sort: "DATE_DESC"` 获取近期判决
2. 大量检索时：使用 `panorama: true` 获取元数据而不取全文
3. 未找到的判决，用 `web_search` 在 Judilibre 或 Arianeweb 上补充

### 按编号检索特定判决
1. 使用 `rechercher_jurisprudence_judiciaire`，`champ: "NUM_AFFAIRE"` + `type_recherche: "EXACTE"` + `search` = 上诉编号
2. 如未找到：尝试在 Judilibre 或 Legifrance 上 web_search
3. **核验所检索编号与返回判决之间的吻合性**（在响应内容本身中）——这是关键预防措施，典型事故是混淆两个编号相近的判决。

### JORF 法律动态监测
1. 使用 `recherche_journal_officiel`，检索词 + `sort: "PUBLI_DATE_DESC"` + 按需 `text_types` 过滤
2. 仅规范性文本：`text_types: ["LOI", "DECRET", "ORDONNANCE", "ARRETE"]`
3. **始终定性**返回文件的性质（SKILL.md 规则 5）

### 法律文本检索（LODA）
1. 使用 `rechercher_dans_texte_legal`，检索词 + `sort: "PUBLICATION_DATE_DESC"` 获取最新
2. 如已知文本标识符：使用 `text_id` 在特定文本内部检索

## 错误处理

### 排序错误
如出现“排序 'X' 无效”错误信息：核验上表并针对相关数据库使用正确的排序。

### 法典名称错误
如出现关于法典名称的错误信息：使用 `lister_codes_juridiques` 获取准确名称。

### 空结果
- 核验拼写和检索词
- 尝试 `type_recherche: "UN_DES_MOTS"`（更宽松）
- 扩大检索范围（`champ: "ALL"`）
- 切换至 web_search 作为补充

### 连接错误
如果 OpenLegi 完全无法访问：
- 告知用户
- 切换至 web_search + 可靠来源
- 不阻塞任务执行

## 与技能规则的集成

### 反幻觉

- OpenLegi 结果直接来自 Legifrance：**可靠来源**。
- 核验聚焦于**适配性**（这是用于正确用途的正确文本吗？）、**时间状态**（文本现行有效吗？）和**链接可追溯性**（交付物中转载的 Légifrance 链接确实来自当前会话中获得的 OpenLegi 响应吗？）。
- 禁止捏造引用的规定仍是绝对的：使用 OpenLegi 去**查找**，绝不用其来“确认”一个想象出来的引用。
- 禁止凭记忆重建 Légifrance 链接的规定同样是绝对的。链接从 OpenLegi 响应中提取，而非其他任何地方。
- 任何交付之前，以强制性的四列结构化表格（引用、工具 + 标识符、相关文本摘录、✓ / ✗ / 改写）形式，逐条实际引用执行 `references/checklist-pre-livraison.md`。在 COWORK / CHAT_CU 模式下，`scripts/verify_links.py` 生成该表格；在 CHAT（及降级模式）下，根据 OpenLegi 卡片手工制作表格。交付以明确念出收尾语为条件。

### 频繁的重新编号与修改

法典和综合文本不断演变。本 skill **在任何情况下**都不得臆断条款编号或措辞的稳定性，即使是“超级经典”条款：

- 《民法典》旧第 1382 和 1384 条因 2016 年 2 月 10 日第 2016-131 号法令变为第 1240 和 1242 条——<https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000032004939>。
- 《民法典》第 1242 条第 4 款——<https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006437058>——（父母责任）已被 2025 年 6 月 23 日第 2025-568 号法律实质性修改——<https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051782996>。
- 此后的法典重构在所有法典中都产生了类似的重新编号。

**必须系统核验**现行措辞，通过 `rechercher_code`（法律状态、生效开始/结束日期）。当文本经历过可能影响论证的近期修改时，明确注明适用的版本。

### 时间适用性（SKILL.md 规则 4）

- **必须系统利用** OpenLegi 返回的“法律状态”“生效开始日期”“生效结束日期”元数据。
- 未经核验这些字段，绝不引用任何条款。

### JORF 定性（SKILL.md 规则 5）

- **必须系统核验** `recherche_journal_officiel` 结果中文件的性质。
- 在引用中定性其法律效力（规范性 vs 议会工作文件 vs 行政性）。
