---
name: "normalisation-juridique-fr-christophe-quezel-ambrunaz"
description: >-
  
  "Normalisation juridique FR"（法语法律文本规范化）技能会清理以法律法语撰写的 Word 文档。它区分两种处理机制：确定性更正（弯引号、法式书名号引号、不换行空格、引用中的不换行空格——art. 1240、n° 21-12.345、50 %——序数词 1ère → 1re、œ 连字、"法律用 dispose 而非 stipule"、英语外来词直译），直接应用；以及判断性改写（"et"前的逗号、空洞的三段式、夸张的套语、协调统一），以 Word 修订形式呈现，供你接受。每项更改都被记录并以汇总表形式返还：可以逐字回退——"撤销 3、7-10"。引用的规范化纯属形式性。可在 Cowork 中或对 Word 文件操作。
metadata:
  author: "Christophe Quézel-Ambrunaz"
  license: "agpl-3.0"
  version: "2026-06-18"
---

# 法语法律语言规范化（Normalisation du langage juridique français）——v1.0

与 Christophe Quézel-Ambrunaz 共同设计的技能。它**直接修正**法律 Word 文档，自主运行，然后在对话中返回一份**紧凑**且**可逆**的**汇总表**。

## 指导原则

两种修改机制，绝不可混淆：

1. **确定性规范化**——排版、不换行空格、撇号、引号、具有唯一修正方式的用词不当（*stipuler→disposer*）、无歧义的英语外来词、引用形式。安全，由 `scripts/normaliser.py` 自动应用。
2. **判断性改写**——*et* 前的逗号（视语境）、空洞的三段式、空洞的强调、语境性英语外来词、引用容忍度。它们需要智能阅读：由**你**在 `references/` 文件的指引下决定并作出。

**确定性**规范化**直接应用，不开启修订跟踪**——以免加重审阅负担；其可逆性完全由**登记册**（`défais`）保证。只有**判断性改写**才以 **Word 修订**（`w:ins`/`w:del`）形式作出：这些是唯一需要审查的，用户在 Word 中接受或拒绝它们，登记册也允许撤销它们。通过 `--track-lexical` 选项（默认关闭）可将跟踪扩展到确定性词汇表。

**关于引用的根本性护栏**：引用（references）的规范化**纯属形式性**（缩写、顺序、空格）。绝不修改引用的实质内容（法院、日期、编号），绝不编造。如对准确性有疑问，予以提示，不要"修正"。

## 环境与委派

- 需要 **Cowork** 或 **computer use**：作出修订需要对 `.docx` 进行 XML 编辑。在无文件的简单聊天中，请求提供文件和适当的环境。
- **OOXML 机制委派给 `docx` 技能**（始终可用）：`scripts/office/unpack.py` → 编辑 `word/document.xml`（以及 `footnotes.xml`/`endnotes.xml`）→ `scripts/office/pack.py` → 验证；`scripts/comment.py` 用于批注；`scripts/accept_changes.py` 用于生成清洁版本。`w:ins`/`w:del` 的确切模式见 `docx` 的 SKILL.md。修订作者："Claude — normalisation"（除非另有指示）。

## 工作流

### 1. 范围界定（仅一次、简短的打断）

确定目标 `.docx` 文件和**范围**：仅正文，或正文 + 脚注 + 参考书目（默认：**全部**，已由用户确认）。如文件为 `.doc`，先转换（`docx/scripts/office/soffice.py`）。

### 2. 通读全文

提取文本（`docx` 的 `extract-text`）并在任何修改前**通读全文**。阅读服务于**判断**机制；确定性机制则由脚本处理，无需人工通读。

### 3. 确定性扫描（脚本）

```bash
python scripts/normaliser.py apply \
  --in "<document.docx>" \
  --out "<document — normalisé.docx>" \
  --registry "<.normjur/registre.json>" \
  --scope all          # all | body | body+notes
```

脚本**直接**应用确定性规则（排版和可靠词汇），**不开启修订跟踪**，写出修正后的 `.docx` 和 **JSON 登记册**。`--track-lexical` 选项用于将词汇修改以修订形式作出。规则细节：`references/typographie.md`、`references/lexique-juridique.md`、`references/anglicismes.md`（"安全核心"部分）。

### 4. 判断扫描（你，针对已修正的文档）

依据 `references/marqueurs-ia.md`、`references/anglicismes.md`（"语境性"部分）和 `references/citations-reflex.md`，通过 `docx` 模式以 **Word 修订**形式作出判断性改写。对**每项**改写，在登记册中记录一条判断条目：

```bash
python scripts/registre.py add-jugement \
  --registry "<.normjur/registre.json>" \
  --cle emphase --libelle "Emphase creuse réécrite" --categorie stylistique \
  --avant "<texte d'origine>" --apres "<texte réécrit>" --wids "101,102"
```

判断的黄金规则：
- ***et* 前的逗号**：绝不机械删除。在合法情形保留（不同主语的从句、插入语结束、"…, et ce, …"、多连词并列）。只删除两个简单并列项之间的错误逗号。
- **三段式**：只收紧**空洞且公式化**的三联句，绝不收紧实质性的列举。
- **全角破折号**：**保留**。脚本只规范化其间距（` — `）。不要替换。
- **动名词迂回说法**和**1990 年拼写协调**：见 `references/marqueurs-ia.md`（§10）和 `references/orthographe-harmonisation.md`。

### 5. 汇总

```bash
python scripts/registre.py recap --registry "<.normjur/registre.json>"
```

将表格（紧凑、**按规则聚合**）粘贴到对话中，随后附上撤销邀请语（见下文）。

### 6. 最终验证（强制）

- 验证完整性：`python scripts/registre.py verify --registry … --doc "<corrigé.docx>"`（幂等性、计数、通过 `docx/scripts/office/validate.py` 的 OOXML 有效性）。
- 检查**没有任何文体改写改变含义**，且**没有任何引用被破坏**。对于长文档或敏感文档，将此检查委派给一个审查差异的子代理。

## 登记册

在对话之外写入的 `JSON` 文件（位于文档旁的 `.normjur/` 中）；对话中只显示聚合表格。模式：见 `references/registre-schema.md`。每项修改都归属于一个编号为 `n` 的**规则组**，并带有组内序号 `i`。确定性组先编号（固定顺序），判断组随后，按你添加的顺序编号。

## 汇总表（规定格式）

```
| N° | Règle                                | Type        | Occ. | Exemple (avant → après)        |
|----|--------------------------------------|-------------|------|--------------------------------|
| 1  | Apostrophes courbes                  | détermin.   |  42  | l'article → l’article          |
| 2  | Insécables (; : ! ? « »)             | détermin.   |  37  | art. 9 ; → art. 9 ;            |
| 5  | stipuler → disposer (loi/texte)      | détermin.   |   3  | la loi stipule → la loi dispose|
| 7  | Emphase creuse resserrée             | STYLISTIQUE |   5  | « il importe de souligner… » → …|
```

将 **STYLISTIQUE（文体）** 行突出显示（用户应能首先检查主观性登记项）。最后附上：

> 如需撤销更改，请例如回复：**défais 3, 7-10, 12**（整组）或 **défais 7.2**（单次出现）。**refais** 用于恢复。

## 撤销语法

用户以自然语言回复；解释并执行：

```bash
python scripts/registre.py undo "3, 7-10, 12" \
  --registry "<.normjur/registre.json>" \
  --in "<document.docx — ORIGINAL>" \
  --out "<document — normalisé.docx>"
```

- `défais 3` → 停用整个第 3 组；`défais 7-10` → 第 7 至 10 组；`défais 7.2` → 第 7 组的第 2 次出现。
- 机制：对于**确定性**组，脚本**从原稿重建**文档，仅重新应用仍处于激活状态的规则/出现——干净的可逆性，无漂移。对于**判断**组，脚本**拒绝**相应的修订（记录的 `w:id`）。
- `refais 7` 重新激活该组；`défais tout` / `refais tout` 用于全局切换。

每次 `undo`/`redo` 后，重新显示更新后的 `recap` 表格（紧凑）。

## 语境节约

绝不把登记册内容倒进对话：只有聚合表格出现在其中。"前 → 后"示例**被截断**（约 40 个字符）。对于大文档，判断扫描时按部分处理，但只在对话中写入合并后的汇总。

## 参考文件

- `references/marqueurs-ia.md`——法语中 AI 写作痕迹及其处理（撇号、*et* 前逗号、三段式、强调、破折号、空洞套语）。
- `references/anglicismes.md`——安全核心（脚本）/ 语境性（判断）/ 保留的**白名单**术语。
- `references/lexique-juridique.md`——法律用词不当（*stipuler/disposer*、*juridiction/justice*、*arrêt/jugement*……）。
- `references/typographie.md`——撇号、不换行空格（采用的方案）、引号、破折号、大写重音。
- `references/citations-reflex.md`——SNE 2022 RefLex 规范、容忍度、按多数用法协调。
- `references/orthographe-harmonisation.md`——按多数用法进行 1990 年拼写协调（判断）。
- `references/registre-schema.md`——登记册的 JSON 模式。

## 已知局限（v1.0，如相关应如实告知用户）

- 脚本插入修订针对**单个 *run*** 内出现的情形。跨越多个 *run* 的出现记录为"需手动作出"：通过 `docx` 模式处理。
- 大写重音和歧义语法属于**判断**，而非脚本。
- 通过 `w:id` 拒绝判断修订，只有在用户尚未在 Word 中接受/拒绝这些修订时才可靠；在此情形下，切换为从登记册读取的 `après → avant` 替换。
