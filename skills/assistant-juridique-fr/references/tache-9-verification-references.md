# 任务9——参考文献核查

> **环境前提**：COWORK 或 CHAT_CU **为强制要求**——本任务通过 XML 编辑产生带注释的镜像文档，无 filesystem 则无法完成。在 CHAT 模式下，**立即中断**并要求启用 computer use 或切换到 Cowork。如文档超过15页或含超过15条引用（存在上下文窗口饱和风险及跨会话续办需要），建议使用 COWORK。

## 目标

核查文档中所有法律引用的存在性和准确性。产出与原文**镜像的 Word 文档**，以批注形式标注每次核查的结果。

## ⛔ 绝对禁止——交付物格式

**绝不产出独立的综合报告、关于引用的“说明”文档，或与原文分离的汇总文档。** 交付物**仅限**保留全文的源文档（或其 Word 转换版），以**Word 批注**（`w:comment`）形式插入文档 XML。如交付文件不含 (a) 原文全部文本及 (b) 附着于引用段落上的 Word 批注，则交付物不合规，必须重做。

汇总表（第4阶段）附加于**镜像文档末尾**、原文之后——它绝不单独构成交付物。

## 核心原则

**未找到来源 ≠ 来源虚假。** 未找到的正当原因：付费访问、数字化前（约2000年前）、轻微引用错误、Legifrance 数据库覆盖不全。绝不将引用定性为“虚假”——只能标注“未找到”或“未核实”。

## 流程

### 第0阶段——文档准备

**执行：**
1. 在工作目录中识别源文档
2. 如为 PDF：通过 `soffice.py --headless --convert-to docx` 转换为 Word（镜像文档将为带批注的 Word）
3. 如为 Word：直接在副本上工作
4. 用 `python scripts/office/unpack.py [source].docx unpacked/` 解压文档
5. 镜像文档将在流程结束时由该 `unpacked/` 目录重建

**⚠️ 镜像文档即源文档本身，附增 Word 批注。不是通过 docx-js 从零创建的新文档。**

### 第1阶段——穷尽提取

通读整个文档。提取**所有**法律引用（正文、脚注、参考书目、附录）。以 `scripts/extract_references.py --file [document]` 启动提取，该脚本自动检测引用（判例、法典条文、法律/法令、学说）及其位置，然后人工补充未落入检测模式的引用。

对每条提取的引用建立记录：
- **位置**：第X条脚注、正文第 Y 页、参考书目
- **提取文本**：精确引文（5-15词）
- **类型**：JURIS_CASS、JURIS_CE、JURIS_CA_TJ、JURIS_TA_CAA、JURIS_CONST、CODE_ARTICLE、LOI_DECRET、DOCTRINE、SOURCE_ETRANGERE、AUTRE
- **规范化引用**：依 `references/format-citations.md` 的规范形式 + 确信度代码（🟢🟡🟠🔴）
- **优先级**：P1（引用>3次或在引言/结论中）、P2（引用1-3次）、P3（仅参考书目）

**去重**：如同一规范化引用出现在多处，一次核查即可。结果传播至所有出现处。

### 第2阶段——核查

按优先级顺序（P1 → P2 → P3）核查每条去重后的唯一引用。

**按类型路由：**

| 类型 | 主要工具 | 查询策略 | 回退 |
|---|---|---|---|
| JURIS_CASS | `rechercher_jurisprudence_judiciaire` | 上诉案号，NUM_AFFAIRE 字段，EXACTE | web_search |
| JURIS_CE | `rechercher_jurisprudence_administrative` | 请求编号，NUM_AFFAIRE 字段，EXACTE | web_search |
| JURIS_CA_TJ | `rechercher_jurisprudence_judiciaire` | 过滤法院 + RG 编号 | web_search |
| JURIS_TA_CAA | `rechercher_jurisprudence_administrative` | 过滤法院 + 请求编号 | web_search |
| JURIS_CONST | `rechercher_decisions_constitutionnelles` | 决定编号 | web_search |
| CODE_ARTICLE | `rechercher_code` | 精确法典 + 条号，NUM_ARTICLE 字段，EXACTE | web_search |
| LOI_DECRET | `rechercher_dans_texte_legal` | 文本编号 | web_search |
| DOCTRINE | `doctrine_search.py`（HAL + OpenAlex + Isidore）再 web_search | 作者 + 短标题，或 DOI；预期可验证标识符 | web_search |
| SOURCE_ETRANGERE | web_search | 按可用标识符检索 | — |

**回退顺序**：OpenLegi（失败则改写查询）→ web_search → 仍为阴性：状态 NON_TROUVEE。

**对每条已核查引用确定状态：**

| 表情 | 状态 | 含义 |
|---|---|---|
| ✅ | SOURCE_DIRECTE_CONFORME | 经 OpenLegi 或官方网站找到，元数据一致 |
| 🔵 | SOURCE_INDIRECTE_CONFORME | 经学说数据库或二手来源找到 |
| ⚠️ | ERREUR_CITATION | 已找到但存在显著分歧（日期、编号、法院、内容） |
| ❌ | NON_TROUVEE | 检索后未能定位（≠ 虚假） |

**元数据验证**（OpenLegi 判例）：
- 法院：精确匹配
- 日期：容差±1天
- 上诉案号/请求编号：严格匹配
- 如存在分歧：状态为 ERREUR_CITATION，在批注中记录差异

### 第3阶段——镜像文档批注（Word 批注）

**⚠️ 本阶段使用已解压文档的 XML 编辑（见 docx skill 的“Editing Existing Documents”部分）。不要通过 docx-js 创建新文档。**

**强制技术顺序：**

1. **通过 docx skill 的 `comment.py` 脚本创建每条批注**：
   ```bash
   python scripts/comment.py unpacked/ [id] "[预转义 XML 的批注文本]"
   ```
   - `[id]`：唯一数字标识符（0、1、2…），每条批注递增
   - 批注文本须预转义（XML 实体：`&amp;`、`&#x2019;` 等）

2. **在 `unpacked/word/document.xml` 中围绕含引用的段落插入标记**：
   ```xml
   <w:commentRangeStart w:id="[id]"/>
   <!-- 文档中含引用的现有段落 -->
   <w:commentRangeEnd w:id="[id]"/>
   <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="[id]"/></w:r>
   ```
   - `w:commentRangeStart` 和 `w:commentRangeEnd` 标记是 `<w:r>` 的**兄弟元素**（siblings），绝不可置于 `<w:r>` 内部。
   - 使用 `str_replace` 工具在 XML 中插入标记——**此步骤不要编写 Python 脚本**。

   **⚠️ 强制规则——位于脚注中的引用：**
   如待批注的引用位于脚注中（存于 `footnotes.xml`），批注**必须**锚定在 `document.xml` 中的注释引用调用处——即包含对应 `<w:footnoteReference w:id="N"/>` 的 `<w:r>`——而**非** `footnotes.xml`。读者在正文中看到注释调用，而非注释本身；因此批注必须附着在该层级才可见。批注文本须提及相关注释编号（例如“注释第12条——”。

3. **保存内容类型**——`comment.py` 脚本不会自动执行此操作。核实 `[Content_Types].xml`（位于 `unpacked/` 目录根）包含 `comments.xml` 的 Override。如缺失，予以添加：
   ```bash
   # 核实
   grep -q "comments+xml" unpacked/\[Content_Types\].xml && echo "OK" || echo "MANQUANT"
   ```
   如 MANQUANT，通过 `str_replace` 在 `unpacked/[Content_Types].xml` 中 `</Types>` 之前插入：
   ```xml
   <Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
   ```
   **无此条目，Word 会静默忽略所有批注——`comments.xml` 文件存在但不可见。**

4. **重新压缩**文档：
   ```bash
   python scripts/office/pack.py unpacked/ [AAAA-MM-JJ]-miroir-verif-[nom-doc].docx --original [source].docx
   ```

**每条批注文本的格式：**
```
[表情] [状态]
规范化引用：[规范形式]
链接：[来源 URL——Legifrance、HAL、Cairn 等]
摘录：[来源的相关段落，2-4句，或文本较长时摘要]
```

**示例：**

```
✅ SOURCE_DIRECTE_CONFORME
规范化引用：Cass. Ass. plén., 9 mai 1984, n° 79-16.612
链接：https://www.legifrance.gouv.fr/juri/id/JURITEXT000007013411
摘录：“Attendu que nul ne peut réclamer d'un tiers la réparation de son propre dommage en invoquant un droit dont il ne peut justifier la titularité…”——关于同居伴侣及损害赔偿之诉的立场转变。
```

```
⚠️ ERREUR_CITATION
规范化引用：Cass. civ. 1re, 20 sept. 2017, n° 16-19.109
说明：文档引用为“Cass. civ. 1re, 20 sept. 2017, n° 16-19.019”——准确上诉案号为 16-19.109。
链接：https://www.legifrance.gouv.fr/juri/id/JURITEXT000035617604
摘录：关于缺陷产品制度与普通法衔接的判决。
```

```
❌ NON_TROUVEE
规范化引用：CA Lyon, 3e ch., 12 mars 2019, n° RG 17/05432 🟡
说明：在 Legifrance 及 web_search 中均未定位。可能原因：判决未数字化、RG 编号错误、或该法院该时期数据库覆盖不全。
```

### 第4阶段——汇总表

在镜像文档末尾添加汇总表：

| 编号 | 位置 | 规范化引用 | 状态 | 备注 |
|---|---|---|---|---|
| 1 | 注释1 | Cass. civ. 1re, 12 juill. 2023, n° 21-12.345 | ✅ | — |
| 2 | 注释3 | Art. 1240 C. civ. | ✅ | 自2016年10月1日起施行 |
| … | … | … | … | … |

表末统计：
- 已核查引用总数
- 按状态分布（✅ / 🔵 / ⚠️ / ❌）
- 按类型分布（判例 / 法规 / 学说）

### 跨会话持久化（仅 COWORK）

COWORK 模式下，镜像文档随时写入工作目录。如会话中断：
- 部分镜像文档保留在项目目录中
- 恢复时，检测现有镜像文档（`miroir-verif-` 前缀）
- 识别已批注（已存在的批注）及待处理的引用
- 从第一条未批注的引用继续

### 与任务10的耦合

如任务9和10同时执行，核查批注（本任务）与统一化批注（任务10）共存于同一镜像文档。以前缀区分：
- `[✅/🔵/⚠️/❌]` 用于核查
- `[📐]` 用于统一化（见任务10）

## 交付

### 第5阶段——交付前自检

**交付镜像文件前，务必核实三个累积条件全部满足：**

1. **全文**：镜像文档包含源文档全部文本（通过长度比较或段落抽样核实）
2. **Word 批注**：`unpacked/word/comments.xml` 文件存在，且每条已核查引用至少含一个 `<w:comment>`
3. **文本标记**：`unpacked/word/document.xml` 包含与每条批注对应的 `<w:commentRangeStart>` 和 `<w:commentRangeEnd>`

**如任一条件不满足，交付物不合规。不交付——先修正。**

快速检查命令：
```bash
grep -c "w:comment " unpacked/word/comments.xml
grep -c "w:commentRangeStart" unpacked/word/document.xml
```
两个数字必须 ≥ 已核查引用数。

### 命名

命名：`[AAAA-MM-JJ]-miroir-verif-[nom-doc].docx`
如与任务10耦合：`[AAAA-MM-JJ]-miroir-verif-harmo-[nom-doc].docx`
