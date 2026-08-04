# 工作流：合同生成器（5 步，带语境）

> _全局规则：`references/rdzen-ktzr.md`（R1 援引 · R2 门禁 · R3 角色 · R4 画像 · R5 格式）。_

> **R3 — LAIK：** 合同相关的额外信号：“我必须签署一份合同”、“我是[X 公司]的客户”、“看看我能不能签这个”。

以 KTZR 风格生成新合同的 5 步工作流。**每一步都需要用户确认**后再继续。生成器可以在附带**语境**（客户邮件、笔记、brief、参考文件）的情况下工作。

## 接收 brief 与语境

用户提供的最低限度 brief：
- **合同类型**（从清单中选择：IT body leasing、NDA、IT 服务、实施、SaaS、著作权转让、合作、委托、会计服务、和解、债权转让、其他）
- **A 方**（客户——名称、法律形式、KRS/NIP、地址）
- **B 方**（相对方——名称、法律形式、KRS/NIP、地址）
- **关键约定**（标的、报酬、时间、特殊要求）

**附加语境（可选）：** 电子邮件、会议笔记、相对方草稿、参考文件。如果用户提供语境——将其视为**关于事务的事实来源**，但对合同内容不具有约束力。从语境中提取：双方的实际约定、意图、商业风险、双方偏好的术语。

**重要——生成器与任何"现有合同"隔离：** 与分析工作流不同，生成器不将任何现有合同作为基础来阅读。例外：如果用户明确说“参照这份合同”、“以此为模板”。

---

## 第 0/5 步：律所记忆

收到 brief 后——在分析前——就此事检查律所记忆。

1. `list_categories()`——如果记忆为空：跳过本步其余部分，进入第 1 步
2. 如果记忆非空：
   - `recall("nazwa kontrahenta")`——brief 中的 B 方
   - `recall("typ umowy")`——例如“body leasing”、“NDA”、“SaaS”
   - `recall("negocjacje pozycja")`——先前的谈判约定

在第 1 步的相应部分中显示命中结果：

```
### 📋 Pamięć kancelarii — kontekst sprawy
[podsumowanie trafień — co istotne dla tej umowy]
```

如无命中——**跳过本部分**。进入第 1 步。

---

## 第 1/5 步：brief 分析

**打开：** `references/essentialia-mapowanie.md`

分析 brief + 语境。**简洁**作答（最多 1 页）：

1. **法律关系类型**（附依据：《民法典》第 750 条用于服务、第 627 条用于承揽、第 41 条《著作权法》用于许可等）
2. **当事方及其角色**（谁提供什么、谁为什么付费）
3. **关键风险**——该类型合同典型的 top 3 法律风险 + 语境中可能产生的额外风险
4. **缺失信息**——为写出完整合同，brief 中缺什么（金额、期限、使用领域等）
5. **建议**——是凭现有内容继续，还是先补全 brief

同时根据 `essentialia-mapowanie.md` 列出该类型合同的**必备要素**。

**STOP。询问：**“我们可以规划结构了，还是你先补全 brief？”

---

## 第 2/5 步：结构规划

**打开：** `references/baza-klauzul/INDEX.md`

**逐条规划合同结构**。格式：

```
## STRUKTURA UMOWY

§ 1. Przedmiot Umowy
   → klauzule z: `04-przedmiot-umowy.md` (Body Leasing IT)

§ 2. Definicje
   → klauzule z: `03-definicje.md` (Body Leasing IT)
   → definicje do dodania: Specjalista, Timesheet, Utwór, Informacje Poufne

§ 3. Obowiązki Stron
   → klauzule z: `05-obowiazki-stron.md`

§ 4. Wynagrodzenie
   → klauzule z: `06-wynagrodzenie.md`

§ 5. Prawa autorskie
   → klauzule z: `08-prawa-autorskie-ip.md`

[...]

§ N. Postanowienia końcowe
   → klauzule z: `17-postanowienia-koncowe.md`

### Załączniki
- Załącznik nr 1: Wzór Zamówienia
- Załącznik nr 2: Wzór Timesheet
- Załącznik nr 3: Lista Specjalistów
```

**规划规则：**
- **仅使用** KTZR 条款库（`references/baza-klauzul/`）中的条款。不自创新条款。
- 选择与合同类型最接近的来源（例如 body leasing——使用 IT Body Leasing 特定条款，而非通用范本）。
- 在 § 1 中列出**待添加的定义**。
- 列出**附件**，注明具体名称。

**STOP。询问：**“你接受这个结构吗？写草稿前有什么要添加/修改的吗？”

如用户提出修正——采纳并在进入第 3 步前展示**更新后的结构**。

---

## 第 3/5 步：起草

**现在打开（如尚未打开）：** `references/style-redakcyjny.md`——该文件中有 KTZR 的具体句式模式（条件结构、定义、列举、当事方称谓）。**按此风格**起草，而非按通用合同撰写惯例。

基于已确认的结构写出**完整合同**。

### 撰写规则

1. **仅用 KTZR 条款库的条款**——不得即兴发挥。如果结构所需事项在条款库中无相应条款——**停下询问用户**，而非自创。

2. **与语境匹配：**
   - 具体的当事方名称（取自 brief，而非“[Strona A]”占位符）
   - 具体金额/费率/期限（取自 brief）
   - 称谓一致（如果 § 1 用“Usługodawca”，整份合同都用“Usługodawca”）
   - 援引有效（草稿写完后检查每个“§ X ust. Y”）

3. **§ 定义中的定义：**
   - 正文中每个首字母大写的术语必须在此有定义
   - 定义按字母顺序排列
   - 定义格式：“术语”——说明（……）。

4. **KTZR 黄金规则优先于条款库**——例如如果条款库的条款含有“zgodnie z § 5”（依据第 5 条）的援引，而你的结构中 § 5 是别的内容——修正援引。

5. **条文援引——强制核实：** 条款中引用的每个条文（例如“《民法典》第 473 条第 2 款”、“RODO 第 28 条”）→ 写入条文内容前调用 `verify_article()`。如 MCP 不可用 → 在援引处附注 `[NIEZWERYFIKOWANE]`（未核实）。条文内容的幻觉会使草稿丧失资格。

### 输出格式

```
UMOWA [TYP]

zawarta w dniu [data] w [miejscu], pomiędzy:

[Strona A z pełnymi danymi i reprezentacją]
— zwaną dalej "[Rola]"

a

[Strona B z pełnymi danymi i reprezentacją]
— zwaną dalej "[Rola]"

Strony postanawiają, co następuje:

§ 1. Przedmiot Umowy

[Treść klauzuli z bazy, dopasowana]

§ 2. Definicje

W rozumieniu niniejszej Umowy:
1. „Termin1" — opis (...);
2. „Termin2" — opis (...);
[...]

[Treść klauzuli z bazy, dopasowana]

[...]

§ N. Postanowienia końcowe

1. [Klauzula salwatoryjna]
2. [Forma zmian]
3. [Załączniki]
4. [Egzemplarze]
5. [Wejście w życie]

___________________            ___________________
[Strona A]                     [Strona B]

Załączniki:
1. [Nazwa załącznika]
2. [...]
```

**STOP。询问：**“进入完整性核实，还是你想先修改草稿中的某处？”

---

## 第 4/5 步：完整性核实

**打开：** `references/checklist-15.md`

用 **15 项检查清单**核对草稿。每项：✅ / ⚠️ / ❌ / ➖（N/D——不适用）。然后：

1. **缺失要素**——应有而没有的
2. **合同类型评注**——是否有该类型特有的要素（取自 `essentialia-mapowanie.md`）缺失
3. **冗余要素**——哪些是多余的，可以删除
4. **建议**——质量控制前应补充什么

然后**补写缺失的条款**（完整文本，取自条款库），并返回**带修正的完整草稿**（不只是修改处——完整文本，可直接继续加工）。

**STOP。询问：**“进入质量控制，还是你想再添加/修改什么？”

---

## 第 5/5 步：质量控制（QA）

进行最终检查：

1. **定义一致性**——每个大写使用的术语 = § 1 中有定义
2. **内部援引**——每个“§ X ust. Y”都指向存在的条款
3. **术语**——一个概念 = 一个术语
4. **附件**——序言/结尾列出的每个附件也在正文中被援引
5. **编号**——条款、款次、项编号一致
6. **当事方信息**——KRS、NIP、REGON、地址完整且格式正确
7. **日期与期限**——日期完整（dd-mm-rrrr），期限单位统一（天 / 工作日）
8. **KTZR 黄金规则**——逐一核对 12 条规则

返回合同的**最终版本**——仅合同文本，**正文中无评论**。QA 评论单独放在最终版本之前，格式如下：

```
## KONTROLA JAKOŚCI

✅ Wszystkie definicje spójne (sprawdzono 12 terminów)
✅ Odesłania wewnętrzne — 8/8 prowadzą do istniejących przepisów
⚠️ Termin "Dni Robocze" w § 5 ust. 3 — w § 1 zdefiniowano jako "dni od pn. do pt. z wyłączeniem dni ustawowo wolnych"; sprawdź zgodność
[...]
```

---

## 最终门禁

向用户显示以下问题并**等待回答**后再生成：

```
⛔ Przed finalną wersją — potwierdź:
1. Dane stron (KRS/NIP/adresy) zweryfikowane źródłowo?
2. Cytowane przepisy sprawdzone (verify_article lub ręcznie)?
3. Prawnik prowadzący sprawę widział ten draft?

→ „tak, generuj finalną wersję" / lub wskaż co poprawić
```

仅在确认之后——生成。未经确认——在文档上方返回 `[DRAFT — DO WERYFIKACJI]`（草稿——待核实）并停下。

例外：如果用户说了“express 模式”或“无需询问直接做”——生成，但在文档开头和结尾标注 `[DRAFT — DO WERYFIKACJI]`。

---

## 最终合同

[可直接粘贴进文件的干净文本，正文中无评论]

---

## 迭代：REDRAFT（重写）

如果第 5 步后用户想修改草稿（“修改 § 4——添加价格调整”、“删除 X 条款”、“添加 non-solicitation”）：

1. 打开条款库中的相应文件，取用条款
2. 在最终文本中作出修改
3. 重新运行第 5 步（QA）——检查修改是否破坏了援引、定义、编号
4. 再次返回完整草稿

---

## 特殊模式：带语境生成

如果用户提供了**语境**（电子邮件、笔记、相对方草稿、商业 brief）——在**第 1 步**添加以下部分：

```
### Z kontekstu wyciągnąłem
- Ustalenie 1: [...]
- Ustalenie 2: [...]
- Preferowana terminologia stron: "Klient" zamiast "Zamawiający"
- Ryzyko zidentyfikowane przez Twojego klienta: [...]
```

这有助于用户在开始撰写前核实你是否正确理解了语境。在后续步骤中考虑语境中的约定（金额、术语、风险），但不得将语境内容复制进合同——合同始终由 KTZR 条款构成。
