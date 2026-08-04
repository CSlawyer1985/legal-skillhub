# 工作流：服务规则生成器（冷启动 → 访谈 → 骨架 → 内容）

> _全局规则：`references/rdzen-ktzr.md`（R1 援引 · R2 门禁 · R3 角色 · R4 画像 · R5 格式）。_

> **R3 — LAIK：** 服务规则相关的额外信号：“我必须发布服务规则”、“我是商店所有者”、“我想开设一家商店”。

电子服务规则（u.ś.u.d.e.，DSA）的交互式生成器。工作流**始终以 3 个诊断性问题开始**——以选择正确的路径。随后逐一提问进行访谈，展示待确认的结构骨架，然后才生成完整内容。

## 三条路径

| 路径 | 适用场景 | 条款数 | 访谈问题数 |
|---|---|---|---|
| **通用（Ogólny）** | B2B、专业服务、无商店和 SaaS | 约 10 | 4 |
| **SaaS** | B2B/B2C、平台/应用程序、订阅、SLA | 约 18 | 7 |
| **电子商务（E-commerce）** | B2C/混合、商店、商品或数字内容 | 约 22 | 9 |

---

## 第 0 阶段：冷启动（诊断——3 个问题）

**不要一次性询问所有内容。** 逐一提问，等待回答。

### 诊断问题 1/3

> 在我们开始之前——几个问题，以便我选择正确的路径。
>
> **你的服务规则的主要使用者是谁？**
> a) 仅限公司/经营者（B2B）
> b) 消费者——自然人（B2C）
> c) 混合——公司和消费者都有

### 诊断问题 2/3

回答后询问：

> **服务规则所涵盖的服务主要涉及什么？**
> a) 通过互联网销售产品/商品（网上商店）
> b) 访问网络/移动平台或应用程序（SaaS、marketplace、门户）
> c) 托管、服务器、域名、电子邮件
> d) 在线专业服务/中介/咨询
> e) 其他（请描述）

### 诊断问题 3/3

回答后询问：

> **什么样的付费模式？**
> a) 订阅（月付/年付）
> b) 一次性购买/按交易付费
> c) 佣金模式/success fee（成功费）
> d) 免费或 freemium

### 路径选择

在 3 个回答之后宣布路径：

```
Na podstawie Twoich odpowiedzi wybieram ścieżkę [NAZWA]:
— [jedno zdanie uzasadnienia]

Zaraz zadam Ci [N] pytań szczegółowych. Lecimy?
```

**选择规则：**
- B2C + 商店/商品/数字内容 → **电子商务**
- B2C + 平台/应用程序 → **电子商务**（u.p.k. 适用于平台）
- 混合 + 商店 → **电子商务**（消费者 = 弱势一方，适用更高标准）
- 混合 + 平台/应用程序（非商店）→ **SaaS** ⚠️ 平台拥有消费者用户——在 SaaS 中加入“§ 撤回权”条款（在线订立合同的 u.p.k. 第 27 条），并在“§ 最后条款”中加入 ODR 部分
- B2B + 商店/商品销售 → **电子商务** ⚠️ 省略“§ 10 撤回权”和“§ 11 例外”——不适用于 B2B 交易；保留《民法典》的瑕疵担保（第 556 条及以下），不加消费者条款
- B2B + 平台/SaaS/托管/域名 → **SaaS**
- B2B + 专业服务/中介/其他 → **通用**
- B2C + 托管/域名/电子邮件 → **SaaS** ⚠️ 加入“§ 撤回权”（u.p.k. 第 27 条）和“§ 最后条款”中的 ODR 部分——购买托管的消费者受 u.p.k. 的全面保护
- 混合 + 托管/域名 → **SaaS** ⚠️ 同上
- 有疑问 → 直接询问，而非猜测

**STOP。等待确认（“开始”/“好”/路径修正）。**

---

## 第 1A 阶段：访谈——通用路径（4 个问题）

逐一提问，等待回答。

**P1.** 你的公司/业务的完整名称和注册地？

**P2.** 服务规则所涵盖的服务或网站叫什么？涉及什么——用一句话描述。

**P3.** 用户一方的义务和禁止事项主要有哪些？（例如禁止发送垃圾邮件、禁止转售、禁止开设虚假账户）

**P4.** 你如何处理付款——用户何时付款、以何种方式？是订阅制、一次性，还是免费服务？

最后一个回答之后 → **第 2A 阶段**。

---

## 第 1B 阶段：访谈——SaaS 路径（7 个问题）

逐一提问，等待回答。

**P1.** 公司的完整名称和平台/应用程序的名称？

**P2.** 订阅模式是什么？有哪些可用套餐——名称及其内容？有免费试用套餐吗？

**P3.** 你提供 SLA（服务等级协议）——承诺可用时间（uptime）吗？如果是：承诺的百分比是多少，未达到时如何处理？

**P4.** AUP 禁止事项清单——用户不得在平台上进行的操作？（典型：垃圾信息、爬取、非法内容、滥用 API）

**P5.** 你是否处理用户的个人数据——账户数据、日志、用户上传的客户数据？你需要委托处理协议（DPA，RODO 第 28 条）吗？

**P6.** 平台是否包含 AI 功能——生成式或分析式？如果是：请简要描述。

**P7.** 用户可以在平台上上传内容吗（UGC：帖子、文件、图片、数据）？平台是否经过审核（moderacja）？

最后一个回答之后 → **第 2B 阶段**。

---

## 第 1C 阶段：访谈——电子商务路径（9 个问题）

逐一提问，等待回答。

**P1.** 商店/网站的完整名称和卖方注册地？

**P2.** 你销售什么——实物商品、数字内容（文件、在线访问）、服务，还是混合？

**P3.** 你接受哪些付款方式？（银行卡、BLIK、转账、PayPal、其他）

**P4.** 有哪些配送方式和大致处理时间？（快递、包裹柜、数字内容用电子邮件）

**P5.** 退货政策——你适用法定的 14 天撤回权（u.p.k. 第 27 条），还是提供更长的期限？

**P6.** 你是否销售非载体交付的数字内容——例如 PDF 文件、在线课程、应用程序访问权？（影响 u.p.k. 第 38 条第 13 项——经消费者同意履行服务后撤回权的排除）

**P7.** 产品中是否有撤回权排除适用的商品——例如录音/录像产品、易腐产品、按消费者定制产品？

**P8.** 你是否处理波兰以外欧盟国家的订单？（影响 VAT OSS 和跨境监管）

**P9.** 偏好的投诉路径——电子邮件、表单，还是其他？你想声明的答复期限是多少？

> ⚠️ **P9 校验：** 在 B2C 关系中，声明的投诉答复期限不应超过 14 个日历日——更长将导致投诉依法律规定被认定成立（u.p.k. 第 7a 条）；对于商品与合同不符的索赔——u.p.k. 第 43d 条第 1 款。如用户指出的期限超过 14 天——告知风险并提出 14 天期限。在比较之前，将以工作日或周计量的期限换算为日历日（1 周 = 7 个日历日；1 个工作日 ≈ 1.4 个日历日）。

最后一个回答之后 → **第 2C 阶段**。

---

## 第 2A 阶段：骨架——通用路径

**打开：** `references/baza-klauzul/20-regulamin-usdde-aup.md`、`references/baza-klauzul/INDEX.md`

展示建议的结构：

```
SZKIELET REGULAMINU — ścieżka Ogólna (~10 §)

§ 1.  Definicje          — pojęcia kluczowe, nazwy stron
§ 2.  Postanowienia ogólne — charakter regulaminu, akceptacja, wymagania techniczne
§ 3.  Zakres usługi      — co obejmuje, czego nie obejmuje
§ 4.  Obowiązki i zakazy użytkownika — lista z P3
§ 5.  Wynagrodzenie i płatności — [model z P4]
§ 6.  Odpowiedzialność usługodawcy — limit, wyłączenia
§ 7.  Reklamacje         — procedura (forma, dane, termin)
§ 8.  Wypowiedzenie i zawieszenie konta
§ 9.  Ochrona danych osobowych — art. 13 RODO, podstawa przetwarzania
§ 10. Postanowienia końcowe — prawo właściwe, sąd, zmiana regulaminu
```

**STOP。询问：**“你接受这个结构吗？有什么要添加或删除的吗？”

---

## 第 2B 阶段：骨架——SaaS 路径

**打开：** `references/baza-klauzul/20-regulamin-usdde-aup.md`、`references/baza-wiedzy/13-regulamin-usdde-hosting-ai.md`、`references/baza-klauzul/INDEX.md`

展示建议的结构。标注 [jeśli...]（如……）的条款仅在适用时启用：

```
SZKIELET REGULAMINU — ścieżka SaaS (~18 §)

§ 1.  Definicje          — Platforma, Plan Abonamentowy, SLA, AUP, Konto, Użytkownik
§ 2.  Zawarcie umowy     — moment rejestracji, e-mail aktywacyjny, wiek / status prawny
§ 3.  Zakres usługi      — opis Platformy, moduły, środowisko produkcyjne vs. testowe
§ 4.  Plany abonamentowe — [nazwy z P2], zakres, upgrades / downgrades
§ 5.  AUP               — zakazy użytkowania [lista z P4]
§ 6.  Konto użytkownika  — hasło, bezpieczeństwo, odpowiedzialność za konto
§ 7.  Wynagrodzenie i płatności — pre-paid, faktury VAT, skutki braku płatności
§ 8.  SLA               — dostępność [% z P3], czasy reakcji, Wada Krytyczna / Istotna / Kosmetyczna [jeśli P3 podano]
§ 9.  Dane osobowe i powierzenie — art. 13 RODO + DPA art. 28 [jeśli P5 = tak]
§ 10. Prawa własności intelektualnej — platforma = własność usługodawcy; dane użytkownika = własność użytkownika
§ 11. Treści użytkownika (UGC) — licencja, moderacja, notice & action [jeśli P7 = tak]
§ 12. Moduły AI          — zakres, wyłączenia odpowiedzialności za output [jeśli P6 = tak]
§ 13. Odpowiedzialność   — cap (ostatnie 12 mies. abonamentu), wyłączenie szkód pośrednich
§ 14. Zawieszenie i usunięcie konta — przesłanki, wind-down, eksport danych
§ 15. Wypowiedzenie      — przez każdą ze stron, okresy
§ 16. Zmiana regulaminu  — tryb, okres wyprzedzenia, brak akceptacji
§ 17. Reklamacje         — procedura, [___] dni roboczych
§ 18. Postanowienia końcowe — prawo polskie, sąd, klauzula salwatoryjna
```

**STOP。询问：**“你接受这个结构吗？标有 [jeśli...] 的哪些条款适用于你的平台？有什么要添加或删除的吗？”

---

## 第 2C 阶段：骨架——电子商务路径

**打开：** `references/baza-klauzul/20-regulamin-usdde-aup.md`、`references/baza-klauzul/INDEX.md`

展示建议的结构。标注 [jeśli...]（如……）的条款仅在适用时启用：

```
SZKIELET REGULAMINU — ścieżka E-commerce (~22 §)

§ 1.  Dane sprzedawcy    — art. 8 ust. 3 u.ś.u.d.e.: firma, adres, NIP, e-mail, telefon
§ 2.  Definicje          — Sklep, Towar, Treść Cyfrowa, Konsument, Konto, Zamówienie
§ 3.  Zasady korzystania ze Sklepu — wymagania techniczne, zakazy
§ 4.  Rejestracja i Konto [jeśli sklep ma konta]
§ 5.  Składanie Zamówień — procedura, moment zawarcia umowy sprzedaży
§ 6.  Ceny i Płatności   — metody [z P3], waluta, termin
§ 7.  Dostawa            — metody [z P4], koszty, termin, ryzyko utraty towaru
§ 8.  Realizacja         — potwierdzenie, anulowanie, niedostępność towaru
§ 9.  Treści Cyfrowe     — dostarczenie, moment wykonania, zgoda konsumenta na natychmiastowe spełnienie [jeśli P2/P6]
§ 10. Prawo Odstąpienia  — 14 dni (art. 27 u.p.k.), formularz, zwrot płatności
§ 11. Wyjątki od Prawa Odstąpienia — [lista z P7 + art. 38 u.p.k.] [jeśli dotyczy]
§ 12. Rękojmia           — odpowiedzialność za wady towaru (art. 43a–43g u.p.k. dla B2C; art. 556 i n. KC dla B2B)
§ 13. Reklamacje         — procedura [z P9], termin, co zawierać zgłoszenie
§ 14. Gwarancja          — kto udziela, czas, zakres [jeśli dotyczy]
§ 15. Oceny i Komentarze [jeśli sklep ma system opinii]
§ 16. Ochrona Danych Osobowych — art. 13 RODO, cel i podstawa przetwarzania
§ 17. Pliki Cookies i śledzenie
§ 18. Odpowiedzialność   — ograniczenia po stronie sprzedawcy (nie dot. roszczeń konsumenta z rękojmi)
§ 19. Zamówienia transgraniczne — VAT, prawo właściwe dla konsumentów UE [jeśli P8 = tak]
§ 20. Pozasądowe Rozwiązywanie Sporów — ODR (https://commission.europa.eu/consumers/odr), UOKIK
§ 21. Zmiana Regulaminu  — tryb, skuteczność wobec zamówień złożonych przed zmianą
§ 22. Postanowienia Końcowe — prawo polskie, sąd, klauzula salwatoryjna
```

**STOP。询问：**“你接受这个结构吗？标有 [jeśli...] 的哪些条款适用于你的商店？有什么要添加或删除的吗？”

---

## 第 3 阶段：生成服务规则

**打开：** `references/style-redakcyjny.md`、`references/baza-klauzul/20-regulamin-usdde-aup.md`、按 `INDEX.md` 所需的 `references/baza-klauzul/` 中的文件

基于已确认的骨架，逐条生成服务规则。

### 撰写规则

1. **KTZR 条款库中的条款**——主要来源：`20-regulamin-usdde-aup.md`。按 `INDEX.md` 从其他文件补充。不得自创条款库之外的条款。

2. **与访谈匹配**——使用具体的服务提供者和服务名称，而非占位符。使用回答中的具体套餐、期限、付款方式。`[___]` 字段**仅在用户未提供数据的地方**保留。

3. **KTZR 风格**——符合 `style-redakcyjny.md`。定义首字母大写。款次编号。援引格式为“§ X ust. Y”。语言正式-法律化，而非营销化。

4. **u.ś.u.d.e. 第 8 条最低要求**——每份服务规则必须包含：
   - 服务提供者信息（公司、地址、NIP、电子邮件、电话）
   - 电子服务的类型和范围
   - 服务提供条件（技术要求）
   - 合同订立和解除的条件
   - 投诉处理程序

5. **电子商务路径——消费者**——每项涉及消费者的条款必须符合 2014 年 5 月 30 日《消费者权利法》。限制消费者权利的条款依法当然无效——不得写入。

### 输出格式

```
REGULAMIN [NAZWA USŁUGI / SKLEPU]
Obowiązuje od: [data — zostaw puste jeśli nie podano]
Wersja: 1.0

§ 1. [TYTUŁ]

1. [Treść ustępu pierwszego]
2. [Treść ustępu drugiego]

§ 2. [TYTUŁ]

1. [Treść]
[...]

---
Kontakt: [dane z wywiadu]
```

生成全部内容之后 → **第 4 阶段（QA）**。

**STOP。询问：**“你希望我现在对服务规则进行 QA 检查吗？”

---

## 第 4 阶段：核实（QA）

按以下方面检查服务规则：

1. **u.ś.u.d.e. 最低要求**——是否满足第 8 条第 3 款第 1–4 项：(a) 服务提供者信息（公司、地址、NIP、电子邮件、电话）；(b) 技术要求；(c) 禁止提供非法内容；(d) 合同订立和解除的条件；(e) 投诉程序
2. **定义**——每个首字母大写的概念在“§ 定义”中都有定义
3. **援引**——每个“§ X ust. Y”都指向存在的条款
4. **`[___]` 字段**——是否残留任何非故意的空白字段
5. **消费者（电子商务和含 B2C 的 SaaS）**——是否有与 u.p.k. 和《民法典》第 385¹ 条相抵触的条款
6. **术语**——整个服务规则中当事方只有一个名称
7. **撤回表单（电子商务 B2C）**——“§ 撤回权”是否包含表单模板或指向 u.p.k. 附件 2 表单的援引（u.p.k. 第 30 条）
8. **信息义务（电子商务和含 B2C 的 SaaS）**——服务规则或页面上指定位置是否覆盖 u.p.k. 第 12 条的最低要求（卖方信息、总价、期限、撤回权、数字内容互操作性）
9. **B2C 投诉（含 B2C 的 SaaS / 电子商务）**——“§ 投诉”中的期限必须是**日历日**，而非工作日；u.p.k. 第 7a 条限定为 14 个日历日（更长 = 投诉依法认定成立）。换算：1 周 = 7 个日历日；1 个工作日 ≠ 1 个日历日。

最终版本之前——门禁。显示问题并**等待回答**：

```
⛔ Przed finalnym regulaminem — potwierdź:
1. Dane podmiotu (nazwa, NIP, adres, KRS) zweryfikowane źródłowo?
2. Cytaty przepisów sprawdzone (verify_article lub ręcznie)?
3. Platforma/sklep B2C czy wyłącznie B2B? (zmienia zakres obowiązków u.p.k.)
4. Prawnik widział draft?
→ „tak, generuj" / lub wskaż co poprawić
```

仅在确认之后——生成。未经确认——在服务规则上方返回 `[DRAFT — DO WERYFIKACJI]`（草稿——待核实）。

例外：“express 模式”或“无需询问直接做”→ 在开头和结尾标注 `[DRAFT — DO WERYFIKACJI]` 生成。

以 ✅ / ⚠️ / ❌ 列表形式返回 QA 结果，然后给出最终服务规则：

```
## WERYFIKACJA REGULAMINU

✅ Minimum art. 8 u.ś.u.d.e. — spełnione (§ 1, § 7, § 17)
⚠️ [ew. uwaga]
❌ [ew. błąd — opisz co poprawiono]

---

## FINALNY REGULAMIN

[czysty tekst, bez komentarzy w treści]
```

---

## 迭代：REDRAFT（重写）

如果用户想在生成后修改某部分：

1. 指出条款和修改内容
2. 从条款库获取相应条款（如需）
3. 进行修改；检查是否破坏了援引、定义、编号
4. 返回**完整的服务规则**——而不仅仅是修改后的部分
