# 工作流：合同完整分析（5 个阶段）

> _全局规则：`references/rdzen-ktzr.md`（R1 援引 · R2 门禁 · R3 角色 · R4 画像 · R5 格式）。_

5 阶段合同分析工作流。**在每个阶段之后停下，等待用户修正**，然后再进入下一阶段。这不是一次性（one-shot）输出——这是对话。

## Express 模式（可选）

如果用户明确说“无需询问全部完成”、“express 模式”、“5 个阶段一次性全部完成”——在一次回复中完成所有阶段，但每个阶段仍作为带标题的独立部分。否则，逐阶段推进。

---

## 第 0/5 阶段：律所记忆

分析前检查律所记忆——关于该案件或相对方的先前记录可能改变分析优先级。

1. `list_categories()`——如果记忆为空：跳过本阶段其余部分，进入第 1 阶段
2. 如果记忆非空：
   - `recall("nazwa kontrahenta")`——如果在合同中可见
   - `recall("typ umowy")`——例如“body leasing”、“NDA”、“wdrożenie”（实施）
   - `recall("ryzyka negocjacje")`——谈判立场、先前标注的风险

在第 1 阶段前显示命中结果：

```
📋 Pamięć kancelarii — kontekst sprawy:
[podsumowanie trafień — max 5 wpisów, tylko co istotne dla tej analizy]
```

如无命中——**跳过本部分**。进入第 1 阶段。

---

## 第 1/5 阶段：Essentialia negotii（必要要素）

**打开：** `references/essentialia-mapowanie.md`

映射五个要素：合同类型、当事方、标的、报酬、时间。然后，根据参考文件中的映射，列出**该类型合同的必要要素**。

**输出格式：**

```
## ETAP 1/5: ESSENTIALIA NEGOTII

- **Typ:** [...]
- **Strony:** [Strona A] (rola) / [Strona B] (rola)
- **Przedmiot:** [zwięźle, 1-2 zdania]
- **Wynagrodzenie:** [model + kwota/stawka + termin]
- **Czas:** [określony/nieokreślony + szczegóły]

### Krytyczne elementy dla tego typu umowy
- [...]
- [...]
```

**STOP。询问：**“你确认这个映射吗？在完整性检查清单之前有什么要添加/修正的吗？”

---

## 第 2/5 阶段：完整性检查清单（15 项）

**打开：** `references/checklist-15.md`

逐一通过全部 15 项。为每项标注状态（✅ / ⚠️ / ❌ / ➖）并附简短理由（1-2 句）。

**输出格式：**

```
## ETAP 2/5: CHECKLIST KOMPLETNOŚCI (15 punktów)

1. **Preambuła i data** — ✅ Data dd-mm-rrrr, Gdańsk, prawidłowa struktura.
2. **Strony i reprezentacja** — ⚠️ Brak numeru KRS po stronie Zamawiającego; reprezentacja przez prokurenta bez wskazania prokury.
3. **Definicje** — ❌ Brak definicji "Specjalista" mimo używania w treści.
[...]
15. **Postanowienia końcowe** — ✅ Wszystko OK.

### Wynik: X/15 punktów spełnionych
```

最后指出**需要修复的 TOP 3 缺漏**。

**STOP。询问：**“进入内部逻辑检查，还是你想先修正某个缺漏？”

---

## 第 3/5 阶段：内部逻辑与一致性

检查合同内部一致性：

1. **未定义的概念**——每个首字母大写的词都必须有定义
2. **当事方称谓不一致**——例如一个条款中用“Wykonawca”（执行方），另一个条款中用“Zleceniobiorca”（受托人）
3. **错误的内部援引**——在 § 5 根本没有第 3 款的地方写“zgodnie z § 5 ust. 3”（依据 § 5 第 3 款）
4. **孤立附件**——序言中列出但正文未援引 / 被援引但缺失
5. **期限不一致**——例如同一事项一处写“30 dni”（30 天），另一处写“miesiąc”（一个月）
6. **规定重复**——同一条款出现在两处

### ⚠️ 长合同的自动触发条件

**语言模型在长文档中存在已知的丢失关联倾向**（attention dilution——注意力稀释，模型的注意力在长上下文中并不均匀，尤其对远距离片段之间的关系）。

**检查是否满足以下至少两项：**
- 合同超过 15 页或超过 5,000 词
- 超过 15 个条款
- 正文中超过 10 处条款间援引（“§ X ust. Y”）
- 初步分析（上述步骤 1-6）发现超过 3 处不一致
- 表明复杂性的关键词：“Załącznik”（附件）、“z zastrzeżeniem”（但书）、“powyższe”（上述）、“stosuje się odpowiednio”（准用）

**如果满足以上至少两项**——不要做 1-2 句的简化分析，**打开 `workflows/weryfikacja-spojnosci-odeslan.md`** 并执行其两阶段程序（盘点 → 核实）。这需要 5-10 分钟，但能发现单次遍历捕捉不到的错误。

向用户说明：

> *“合同较长且包含许多条款间援引。语言模型在长文档中会丢失关联——我建议进行专门的援引核实（两阶段工作流：盘点 + 逐一检查）。需要 5-10 分钟。你接受吗？”*

如果用户同意——以完整形式运行 `weryfikacja-spojnosci-odeslan.md`（Pass 1 → STOP → Pass 2 → 报告）。将报告结果整合进第 3 阶段，替代下面的标准格式。

如果用户不同意或合同较短——执行下面的标准分析。

### 标准输出格式（短合同）

```
## ETAP 3/5: LOGIKA WEWNĘTRZNA

### Niezdefiniowane pojęcia
- "Timesheet" (§ 5 ust. 2) — używane bez definicji
- "Wada Krytyczna" (§ 8) — definicja brakuje

### Niespójność nazewnictwa
- ✅ Spójne ("Usługodawca" w całej umowie)

### Odesłania wewnętrzne
- ❌ § 6 ust. 4 odsyła do "§ 4 ust. 5" — § 4 ma tylko 3 ustępy

### Załączniki
- ⚠️ Załącznik nr 2 (wzór Timesheet) wymieniony w treści, nie wymieniony w wykazie załączników

### Powtórzenia
- ⚠️ Kara umowna za zwłokę w § 9 ust. 2 i § 13 ust. 1 — sprawdzić czy świadome rozróżnienie czy duplikat
```

**STOP。询问：**“进入风险审计，还是先修复逻辑问题？”

---

## 第 4/5 阶段：风险审计

识别所有法律和商业风险。每项附等级和位置。

**等级：**
- 🔴 **严重（KRYTYCZNY）**——可能导致合同无效、无限责任、权利丧失或被对方强制执行
- 🟠 **高（WYSOKI）**——重大财务或运营风险，需立即谈判
- 🟡 **中（ŚREDNI）**——值得改进，但不是交易破坏因素
- 🟢 **低（NISKI）**——细微不准确，文体改进

**输出格式（每项风险）：**

```
🔴 KRYTYCZNY | § 11 ust. 2 — Nieograniczona odpowiedzialność
Brak limitu odpowiedzialności Wykonawcy. W razie szkody z winy zwykłej Wykonawca odpowiada w pełnym zakresie, łącznie z lucrum cessans.
**Rekomendacja:** Dodać cap (np. 12 mies. wynagrodzenia), wyłączyć lucrum cessans, zastrzec wyjątek winy umyślnej (art. 473 § 2 KC). Klauzule do użycia: `references/baza-klauzul/11-odpowiedzialnosc.md`.
```

最后给出**安全评分（0–100）**+ 理由。

**STOP。询问：**“进入建议环节，还是你想先讨论某项风险？”

---

## 第 5/5 阶段：总结与建议

**输出格式：**

```
## ETAP 5/5: PODSUMOWANIE I REKOMENDACJE

### TOP 3 do naprawy
1. **[Problem]** — `[paragraph]` — rekomendowana klauzula z: `[plik z bazy]`
2. [...]
3. [...]

### Sugerowane zmiany terminologiczne
- "Zleceniobiorca" → "Wykonawca" (spójność z § 1)
- [...]

### Ogólna ocena umowy
[2-3 zdania: czy umowa jest do podpisania, do negocjacji, do gruntownej przeróbki]
```

**在最后（仅此处）：**

> *Analiza ma charakter pomocniczy i nie zastępuje oceny radcy prawnego prowadzącego sprawę.*

---

## agent 行为——当用户中断工作流时怎么办

- 如果用户在第 2 阶段后写“修改 § 5 ust. 3”——中断工作流，执行 `workflows/popraw-fragment.md`，然后询问“从第 3 阶段继续分析吗？”
- 如果用户在某个阶段后写“够了”/“谢谢”——结束，不催促
- 如果用户粘贴另一份合同——这是新任务，从头重新启动工作流
- 如果用户索要条款库中的条款——引导到 `references/baza-klauzul/` 中的相应文件，然后返回工作流
