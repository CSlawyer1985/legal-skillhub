# 工作流：援引与关联一致性核实

> _全局规则：`references/rdzen-ktzr.md`（R1 援引 · R2 门禁 · R3 角色 · R4 画像 · R5 格式）。_

专门用于检测长合同（通常 15 页以上）中**援引错误和内部不一致**的两阶段工作流。针对一个典型问题：模型能很好地单独阅读每个条款，但较难发现**远距离片段之间的关系**——长上下文中的注意力稀释（attention dilution）效应。

## 何时运行本工作流

**自动触发**（Claude 自行决定）：
- 合同超过 15 页或超过 5,000 词
- 合同超过 15 个条款
- 合同包含超过 10 处条款间援引（“§ X ust. Y”）
- 初步分析（完整分析的第 3 阶段）发现超过 3 处不一致

**用户要求时**：
- “检查这份合同中的援引”
- “条款编号是否对得上”
- “检查内部一致性”
- “编号是否有错误”

**作为独立运行**（无完整分析）——完整程序
**作为内嵌的第 3 阶段**（在 `pelna-analiza.md` 框架内）——简化呈现，但方法相同

## 为何两阶段

**注意力稀释**问题即使在 200K 窗口下也不会消失。模型“看到”整份合同，但其注意力**并不均匀**——远距离片段之间的关系（例如 § 18 援引 § 2 中的定义）比单个条款的内容更难被追踪。

解决方案：**将盘点与核实分离**。

- **PASS 1（第一遍）**是纯清单——模型不分析，只列举。迫使它**完整遍历**文档而不试图推理。
- **PASS 2（第二遍）**是逐一核实——模型**单独检查每个援引**，以表格形式强制对每个要点进行显式核实（而非相信上下文记忆）。

这种方法的强制效果：如果“§ 8 ust. 3”援引有误，模型**必须看到它**，因为它必须将 § 8 ust. 3 的具体内容填入表格。

---

## PASS 1：盘点（清单，而非分析）

### 第 1.1 步：合同结构盘点

列出合同的**所有条款**，附简短说明（最多 1 句）其规制内容。另加附件。

**输出格式：**

```
## INWENTARYZACJA STRUKTURY

### Paragrafy
| § | Tytuł | Liczba ustępów | Krótki opis (1 zdanie) |
|---|-------|----------------|------------------------|
| § 1 | Definicje | 12 | Słownik 12 terminów używanych w umowie |
| § 2 | Przedmiot umowy | 4 | Świadczenie usług IT przez Usługodawcę na rzecz Usługobiorcy |
| § 3 | Wynagrodzenie | 6 | Stawka godzinowa 250 PLN, faktury miesięczne, termin 14 dni |
| ... | ... | ... | ... |

### Załączniki
| Nr | Tytuł | Wzmiankowany w § | Obecny w pakiecie? |
|----|-------|------------------|--------------------|
| 1 | Specyfikacja techniczna | § 2 ust. 1 | ✅ TAK |
| 2 | Wzór timesheet | § 4 ust. 3 | ❓ Niejasne (nie widzę w przekazanym materiale) |
| ... | ... | ... | ... |
```

### 第 1.2 步：援引盘点

列出合同中的**所有援引**——条款间援引、对附件的援引、语义性援引。

**三个类别：**

**A. 明确援引**（指向具体编辑单元）：
- “§ X”、“§ X ust. Y”、“§ X ust. Y pkt Z”
- “Załącznik nr X”（附件 X）

**B. 语义性援引**（需要解释）：
- “上述条款”
- “本条款”
- “上文所指出”
- “除 § X 另有规定外”（z zastrzeżeniem § X）
- “除……所述情形外”（z wyłączeniem przypadków, o których mowa w...）

**C. 对定义的援引**（首字母大写的术语）：
- “Strona”、“Wykonawca”、“Usługodawca”、“Specjalista”、“System”、“Utwór”等

**输出格式：**

```
## INWENTARYZACJA ODESŁAŃ

### A. Odesłania jednoznaczne (suma: N)

| # | Lokalizacja źródłowa | Tekst odesłania |
|---|---------------------|-----------------|
| 1 | § 4 ust. 2 | "zgodnie z § 3 ust. 1" |
| 2 | § 5 ust. 3 | "Wynagrodzenie określone w § 3" |
| 3 | § 8 ust. 4 | "Załącznik nr 2 (Wzór Timesheet)" |
| ... | ... | ... |

### B. Odesłania semantyczne (suma: N)

| # | Lokalizacja źródłowa | Tekst odesłania |
|---|---------------------|-----------------|
| 1 | § 5 ust. 4 | "Powyższe nie wyłącza..." |
| 2 | § 9 ust. 2 | "z zastrzeżeniem ust. 3" |
| ... | ... | ... |

### C. Odesłania do definicji (suma: N)

Lista wszystkich terminów z wielkiej litery używanych w treści (z liczbą wystąpień):
- "Strona" (12×), "Wykonawca" (45×), "Specjalista" (8×), "System" (23×) itd.
```

### 第 1.3 步：定义盘点

从“§ 定义”（或其他位置）列出**所有已定义术语**：

**输出格式：**

```
## INWENTARYZACJA DEFINICJI

| # | Termin | Lokalizacja definicji | Definicja (skrót) |
|---|--------|----------------------|-------------------|
| 1 | "Strona" | § 1 ust. 1 | Usługodawca lub Usługobiorca |
| 2 | "Specjalista" | § 1 ust. 5 | Pracownik Usługodawcy oddelegowany na podstawie umowy |
| 3 | "System" | § 1 ust. 8 | Oprogramowanie objęte Umową |
| ... | ... | ... | ... |
```

### STOP 1——盘点确认

> **向用户提问：** *“盘点已完成。附件清单是否完整？是否有我应该考虑但看不到的文件？我们进入核实阶段（Pass 2）吗？”*

没有这一 STOP，可能会去核验“不存在”的附件援引——而附件实际存在，只是未交给 Claude。

---

## PASS 2：核实（逐项单独进行）

### 第 2.1 步：明确援引的核实

针对 Pass 1 表格 A 中的**每一个**援引——在表格中核实：

```
## WERYFIKACJA ODESŁAŃ JEDNOZNACZNYCH

| # | Źródło | Odesłanie | Cel istnieje? | Treść celu (skrót) | Pasuje do kontekstu? | Status |
|---|--------|-----------|---------------|--------------------|--------------------|--------|
| 1 | § 4 ust. 2 | "zgodnie z § 3 ust. 1" | ✅ TAK | "Wynagrodzenie netto wynosi 250 PLN za godzinę" | ✅ TAK | ✅ OK |
| 2 | § 5 ust. 3 | "Wynagrodzenie określone w § 3" | ✅ TAK | § 3 reguluje wynagrodzenie (cały paragraf) | ✅ TAK | ✅ OK |
| 3 | § 8 ust. 4 | "Załącznik nr 2 (Wzór Timesheet)" | ❓ Załącznik wzmiankowany, ale nie w pakiecie | — | — | ⚠️ DO POTWIERDZENIA |
| 4 | § 12 ust. 1 | "kary umowne, o których mowa w § 9 ust. 3" | ✅ TAK | "Kara umowna za naruszenie poufności..." | ❌ NIE — § 9 ust. 3 reguluje karę za POUFNOŚĆ, a § 12 mówi o karze za ZWŁOKĘ | 🔴 BŁĄD ODESŁANIA |
| 5 | § 15 ust. 2 | "zgodnie z § 17" | ❌ NIE — ostatni paragraf to § 16 | — | — | 🔴 ODESŁANIE NIEISTNIEJĄCE |
| 6 | § 11 ust. 4 | "wskazane w §___" | — | — | — | 🔴 PUSTE POLE ODESŁANIA |
```

**状态类别：**

- ✅ **OK**——援引正确，目标存在，目标内容与语境相符
- ⚠️ **待确认**——目标存在，但解释不明确（例如语义性援引，或附件不在文件中）
- 🔴 **援引错误**——目标存在，但其内容与援引语境不符
- 🔴 **援引不存在**——所援引的条款/款次/项在合同中不存在
- 🔴 **空白字段**——作者留下未填写的占位符（罕见，但确有发生）

### 第 2.2 步：语义性援引的核实

每个语义性援引都需要**语境解读**——“上述”、“本”、“所指”具体指什么。

```
## WERYFIKACJA ODESŁAŃ SEMANTYCZNYCH

| # | Źródło | Odesłanie | Co konkretnie powinno być? | Co rzeczywiście jest w tym miejscu? | Status |
|---|--------|-----------|---------------------------|------------------------------------|--------|
| 1 | § 5 ust. 4 | "Powyższe nie wyłącza..." | Postanowienia § 5 ust. 1-3 (o obowiązkach) | § 5 ust. 1-3 mówią o obowiązkach Stron — pasuje | ✅ OK |
| 2 | § 9 ust. 2 | "z zastrzeżeniem ust. 3" | § 9 ust. 3 | § 9 ust. 3 istnieje i wprowadza wyjątek | ✅ OK |
| 3 | § 14 ust. 1 | "wskazane wyżej" | Niejasne — przed § 14 jest § 13 o poufności, ale § 14 mówi o wypowiedzeniu | Brak logicznego nawiązania | ⚠️ NIEJASNE |
```

### 第 2.3 步：定义核实

```
## WERYFIKACJA DEFINICJI

### Definicje zdefiniowane, ale NIEUŻYWANE w treści ("zombie definitions")
- "Materiały Marketingowe" (§ 1 ust. 7) — definicja jest, ale w żadnym paragrafie nie znajduję użycia. **Do usunięcia lub do wykorzystania.**

### Terminy UŻYWANE z wielkiej litery, ale NIEZDEFINIOWANE
- "Konsultant" (używany w § 8 ust. 2) — brak definicji w § 1. **Domysł:** chodzi o Specjalistę, ale to wymaga ujednolicenia. 🔴
- "Punkt Kontroli" (używany w § 11 ust. 3) — brak definicji. ⚠️

### Niespójność pisowni (terminy używane raz z wielką, raz z małą literą)
- "Specjalista" / "specjalista" — w § 1, 4, 5 z wielkiej, w § 8 ust. 4 z małej. Sprawdzić czy świadome rozróżnienie. ⚠️

### Definicje powtórzone (ten sam termin zdefiniowany dwa razy z różnym znaczeniem)
- "Strona" — zdefiniowany w § 1 ust. 1 (Usługodawca/Usługobiorca) i ponownie w § 13 ust. 2 (w kontekście postępowania sądowego "Strona Postępowania"). Niespójność. 🔴
```

### 第 2.4 步：金额、日期、术语一致性核实

```
## WERYFIKACJA SPÓJNOŚCI

### Kwoty i procenty

| Wartość | Miejsca występowania | Spójność |
|---------|---------------------|----------|
| Stawka godzinowa | Preambuła: "250 PLN" / § 3 ust. 1: "250 zł netto" / Załącznik nr 1: "260 PLN" | 🔴 NIESPÓJNE |
| Cap odpowiedzialności | § 11 ust. 2: "100% rocznego wynagrodzenia" | OK (jedno miejsce) |
| Kara umowna za zwłokę | § 9 ust. 1: "0,5% za dzień" / § 12 ust. 3: "0,5% miesięcznego wynagrodzenia" | ⚠️ Różne podstawy obliczenia — sprawdzić zamierzenie |

### Daty i terminy

| Wartość | Miejsca występowania | Spójność |
|---------|---------------------|----------|
| Data zawarcia | Preambuła: "12-05-2026" | OK |
| Początek świadczenia | § 2 ust. 3: "od 1 czerwca 2026" / Harmonogram (Załącznik nr 1): "od 15 maja 2026" | 🔴 NIESPÓJNE |
| Okres wypowiedzenia | § 14 ust. 1: "3 miesiące" / § 14 ust. 2 (przy naruszeniu): "30 dni" | OK (różne podstawy wypowiedzenia) |

### Terminologia i nazwy stron

| Termin | Lokalizacje | Spójność |
|--------|-------------|----------|
| Nazwa strony pierwszej | Preambuła: "Usługodawca" / § 4 ust. 2: "Wykonawca" / § 8: "Spółka" | 🔴 NIESPÓJNE |
| Określenie usługi | "Usługi" / "Świadczenie" / "Czynności" | ⚠️ Wymaga ujednolicenia |
```

---

## 最终报告

```
## RAPORT KOŃCOWY WERYFIKACJI ODESŁAŃ I SPÓJNOŚCI

### Statystyki
- Paragrafów: N
- Załączników wymienionych: N (w pakiecie: M, niejasnych: K)
- Odesłań jednoznacznych: N (OK: X, błędów: Y, do potwierdzenia: Z)
- Odesłań semantycznych: N
- Terminów zdefiniowanych: N (używanych: X, "zombie": Y)
- Terminów używanych niezdefiniowanych: N

### KRYTYCZNE BŁĘDY (🔴) — wymagają natychmiastowej korekty
1. § 12 ust. 1 — Błąd odesłania "kary umowne, o których mowa w § 9 ust. 3" — § 9 ust. 3 mówi o INNEJ karze (poufność, nie zwłoka). **Korekta:** zmienić na "§ 9 ust. 1" (kara za zwłokę).
2. § 15 ust. 2 — Odesłanie do nieistniejącego § 17. **Korekta:** ustalić, do czego miało odsyłać — być może § 16 (zmiana ostatnia w trakcie edycji).
3. Stawka godzinowa — niespójność 250/260 PLN między preambułą, § 3 i Załącznikiem nr 1. **Korekta:** ujednolicić.
4. Nazwa strony — niespójność "Usługodawca" / "Wykonawca" / "Spółka". **Korekta:** wybrać jedną nazwę (przy art. 750 KC — "Usługodawca").

### OSTRZEŻENIA (⚠️) — do potwierdzenia z autorem
1. § 8 ust. 4 — Załącznik nr 2 "Wzór Timesheet" wymieniony, ale nie widzę go w pakiecie. Czy istnieje?
2. § 14 ust. 1 — Niejasne odesłanie "wskazane wyżej".
3. § 9 ust. 1 vs § 12 ust. 3 — kary umowne mają różne podstawy obliczenia (% za dzień vs % miesięcznego wynagrodzenia) — świadome rozróżnienie czy błąd?

### MAŁE NIESPÓJNOŚCI (do uporządkowania)
1. Pisownia "Specjalista" / "specjalista" — ujednolicić.
2. Definicja "Materiały Marketingowe" — zdefiniowana, ale nieużywana — usunąć lub wykorzystać.
```

**STOP。询问：** *“报告已完成。我们进入修正存在严重错误的条款（workflows/popraw-fragment.md），还是你想先讨论某些警告？”*

---

## 精简模式——用于短合同（少于 15 页）

如果合同少于 15 页或少于 8 个条款，**不要运行完整的两阶段程序**——以单步进行精简核实：

1. 5 列表格的援引表（明确援引）：位置 / 援引 / 目标存在？/ 相符？/ 状态
2. 已定义术语与使用术语对照表
3. 金额/术语不一致清单

无 STOP。无 Pass 1 / Pass 2。

---

## 本工作流旨在发现的反模式（分阶段编辑合同的典型错误）

1. **编辑后的重新编号**——作者添加了新款次，但未重新编号其他条款中的援引。多人协作时常见。
2. **删除 + 遗留援引**——作者删除了 § 7（例如认为多余），但 § 12 中仍有“zgodnie z § 7”（依据第 7 条）。
3. **定义更名**——术语“Pracownik”在 § 1 中改名为“Specjalista”，但 § 8 和 § 11 中仍是“Pracownik”。
4. **数值只在单处修改**——谈判期间在 § 3 修改了报酬，但序言和附件中仍是旧金额。
5. **附件被提及但缺失**——§ 4 ust. 3 援引“Załącznik nr 2（Timesheet 模板）”，但附件清单（合同末尾）中只有附件 1。
6. **附件已附上但正文未提及**——相反情况：文件包中有附件 4，但合同正文无人援引。无用附件。
7. **援引空白字段**——“zgodnie z §___”——套用模板后忘记填写。
8. **循环援引**——“§ 5 ust. 2 准用于 § 12 ust. 3，但 § 5 ust. 2 另有规定除外”——逻辑错误。
9. **对"已废止"款次的援引**——编辑过程中某款次被标注“(uchylony)”（已废止）或删除，但别处仍援引它。
10. **日期前后不一致**——序言为当前日期 + “§ 期限”为两个月前的日期（模板复制的典型错误）。

## 操作规则——何时 Claude 自行运行本工作流

无需询问用户——当检测到**至少两项**下列情形时：
- 合同超过 15 页或超过 5,000 词
- 超过 15 个条款
- 超过 10 处条款间援引
- 超过 3 处初步不一致
- 表明复杂性的关键词：“Załącznik”（附件）、“z zastrzeżeniem”（但书）、“powyższe”（上述）、“wskazane w”（所指）、“stosuje się odpowiednio”（准用）

在此情形下，在完整分析第 2 阶段（检查清单）之后，Claude 说明：

> *“合同较长且包含许多条款间援引。语言模型在长文档中存在已知的丢失关联倾向（attention dilution）。我建议在风险审计之前进行专门的援引核实——这是两阶段程序（盘点 + 核实）。需要 5-10 分钟。你接受吗？”*

---

## 当 Claude 本身不够用时——以 NotebookLM 作为补充

经验表明，对于**30 页以上、援引网络非常密集**的合同，即使标准 Claude 中的两阶段核实工作流也可能漏掉某些错误。在此类情形下，**NotebookLM（Google）**会给出明显更好的结果——出于一个具体的架构原因。

### 为何 NotebookLM 在长文档中更强

**1. RAG 架构而非纯粹的长上下文**——NotebookLM 用 embeddings 将文档索引为分块，并在每个问题上检索与查询相关的具体片段。对于*“§ 8 ust. 3 具体包含什么”*这样的问题，模型获得围绕 § 8 ust. 3 的**集中语境**，而非 30 页分散的注意力。

**2. 强制来源引用**——每次作答，NotebookLM 都会展示其依据的**文档具体片段**。这迫使模型真正查看文档，而非从上下文记忆推断。这是 Claude 两阶段工作流试图程序化强制实现之事的架构化版本。

**3. 多问题场景下“漏检率”更低**——一个会话中可以提出 20-30 个问题，每个都获得全新检索。在标准 Claude 中，对话不断增长，上下文随之“稀释”。

### 何时建议客户/自己转到 NotebookLM

如果在 Claude 中运行核实工作流之后出现以下情形，Claude 应**自行建议**转用 NotebookLM：

- 合同超过 30 页（经验阈值——超过该阈值，即使两阶段流程也不够）
- 出现工作流未发现全部问题的**怀疑**（例如用户手动发现的不一致，即使它不在报告中）
- 合同包含超过 30 处条款间援引
- 合同有超过 5 个附件，正文中多个条款援引这些附件
- 合同经过**多次编辑**（谈判、多轮修改）——此情形下重新编号的风险很高

### Claude 向用户传达的信息

> *“Claude 中的核实工作流发现了 X 个错误，但以这份合同的长度（Y 页、Z 处援引），我建议再在 NotebookLM（Google）中检查一次。NotebookLM 基于 RAG 架构——索引文档并检索具体片段——这使其在超长合同中具有更高的准确性。建议向 NotebookLM 提出的问题（需要 2-3 次调用）：*
> *1. „Wymień wszystkie odesłania międzyparagrafowe w umowie i zweryfikuj każde."（列出合同中所有条款间援引并逐一核实。）*
> *2. „Wymień wszystkie terminy używane z wielkiej litery i sprawdź, czy każdy jest zdefiniowany w § Definicje."（列出所有首字母大写的术语，检查每个是否在§ 定义中有定义。）*
> *3. „Sprawdź spójność kwot, dat i terminologii pomiędzy preambułą, treścią umowy i załącznikami."（检查序言、合同正文和附件之间金额、日期和术语的一致性。）*
> *在 NotebookLM 中检查后，请带回结果——我们将与我的报告比对，并综合出完整的修正清单。”*

### 为何在 NotebookLM 中调用 2-3 次

NotebookLM 也并非完美——原因有二：

**A. 分块（chunking）并不总是尊重法律结构**——NotebookLM 以启发式方式划分文档（每块约 500-1000 token）。它可能将 § 8 ust. 3 与 § 8 的其他部分分开，从而破坏局部语境。因此，不同措辞的问题会命中不同的片段。

**B. 关于整体一致性的问题与 RAG 相悖**——*“这份合同在术语上是否内部一致”*需要整体性视角，而 RAG 只检索片段。因此，问题必须**分解**（术语单独问、金额单独问、日期单独问）——这就产生上述 2-3 次调用。

### Claude → NotebookLM → Claude 工作流

超长合同的最强路径：

1. **Claude（本技能）**——5 阶段完整分析 + Pass 1/Pass 2 核实工作流
2. **NotebookLM**——2-3 次专门用于检查援引、术语、金额的调用
3. **回到 Claude**——综合两份报告、解决冲突、结合 `references/baza-klauzul/` 中的相应条款拟定修正清单

NotebookLM **不替代**本技能——它在超长合同内部一致性核实这一狭窄但重要的层面补充技能。全部学理层面（`references/baza-wiedzy/`）、条款层面（`references/baza-klauzul/`）、文体层面（`references/style-redakcyjny.md`）以及 agent 式工作流仍保留在 Claude 中。
