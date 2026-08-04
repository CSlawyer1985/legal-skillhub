# 工作流：律所配置（Konfiguracja kancelarii）

一次性访谈，生成 `practice-profile.md` 文件——供所有工作流读取的律所持久化配置。由管理员（律所合伙人/所有者，或其授权的助理）运行。

**何时运行：**
- 律所首次部署该技能时
- 执业画像、专长或标准发生变化后
- 组织中多人使用该技能且需要一致配置时

**时间：** 15–20 分钟。请具体作答——越精确，技能越能贴合你的律所。

**输出：** 一份可直接复制到技能根目录的 `practice-profile.md` 文件。该文件已被 gitignore——不会进入公开仓库。

---

## 访谈进行规则

- 分节提问——每节之后等待回答，再继续
- 不询问客户数据、案件案号或任何个人数据
- 如果管理员回答“标准”或“典型”——适用波兰 B2B IT 律所的市场默认值
- 用回答来构建 `practice-profile.md`——不存储在会话记忆中

---

## 第 1/5 节——执业画像

**问题：**

1. **主要合同类型：** 哪些合同类型占律所工作量的 80% 以上？（例如 IT body leasing、NDA、SaaS、ERP 实施、著作权转让、和解、B2B 雇佣合同）

2. **代理立场：** 律所最常代理哪一方？
   - 委托方 / 客户（服务购买方）
   - 执行方 / 供应商（服务提供方）
   - 双方（视案件而定）

3. **市场：** 律所的客户画像：
   - B2B / B2C / 混合
   - 国内 / 国际（如为 INT——涉及哪些法域？）
   - 客户规模：中小企业 / 企业集团 / 初创企业 / 混合

4. **专长行业：** 除 IT 外，还有哪些额外行业？（例如 fintech、medtech、电子商务、房地产）

**STOP——等待第 1 节的回答。**

---

## 第 2/5 节——风险阈值

**问题：**

1. **律所风格：** 你如何描述律所的风险态度？
   - **保守型**——始终以最大程度的保障为出发点，对任何偏离标准之处均进行谈判
   - **温和型**——标准 B2B 市场；对超出阈值以上的风险进行谈判
   - **进取型**——以促成交易为导向；在客户知情决策时接受较高风险

2. **绝对 RED（红线）：** 哪些情形始终无需谈判即阻断合同？示例（勾选并补充）：
   - [ ] 无责任上限，或 cap（上限）低于 X 个月报酬
   - [ ] 试图排除故意过错（《民法典》第 473 条第 2 款）
   - [ ] 著作权转让时无使用领域
   - [ ] 无正当理由的境外管辖
   - [ ] 其他：___

3. **完整分析 vs 快速分诊的阈值：** 从多少金额起，你总是做完整分析（而非快速分诊）？

**STOP——等待第 2 节的回答。**

---

## 第 3/5 节——默认谈判立场

**问题：**

1. **责任上限（cap）：** 律所推荐以何种 cap 作为谈判起点？
   - 例如“12 个月净报酬”/“合同价值”/“取决于合同金额”

2. **保密：** 律所标准做法中，合同结束后的保密期是多久？
   - 例如“普通信息 3 年，商业秘密无期限”

3. **RODO：** 律所的默认立场：
   - 代理数据控制者（委托处理方）
   - 代理处理者（接收数据方）
   - 双方

4. **争议解决：** 偏好的争议解决场所？
   - 普通法院（以哪一方住所地为管辖？）
   - 仲裁（何种仲裁机构？）
   - 视金额和当事方而定

5. **违约金：** 律所是否标准地在每份合同中提出违约金条款，还是仅在客户要求时？

**STOP——等待第 3 节的回答。**

---

## 第 4/5 节——风格与格式

**问题：**

1. **法律设计：** 你偏好何种输出格式？
   - **Classic（经典）**——传统法律格式，无表格和方框（Times New Roman）
   - **Light legal design（轻量法律设计）**——Arial、关键条款表格、细微强调（KTZR 标准）

2. **技能回复的正式程度：** 技能应如何称呼你？
   - 正式——“Kancelaria”（律所）/"Zamawiający"（委托方）/不使用直接称谓
   - 半正式——“Państwa kancelaria”（贵所）/“Państwo”（诸位）
   - 操作式——直接，如同律师同事

3. **工作语言：**
   - 仅波兰语
   - 波兰语 + 面向外国客户的英文条款摘要/概要
   - 英文与波兰语并重

4. **分析报告格式：** 报告中应始终包含什么，你不想要什么？

**STOP——等待第 4 节的回答。**

---

## 第 5/5 节——排除事项

**问题：**

1. **律所不办理的案件类型：** 例如劳动法、法院程序、刑事案件、pre-seed 初创企业

2. **律所不服务的客户类型：** 例如消费者、在波兰无实体结构的外国客户、受监管行业（银行、保险）

3. **其他任何**技能应当了解但未问到的律所情况？

**STOP——等待第 5 节的回答。**

---

## 生成 practice-profile.md

收集完 5 节的回答后——按以下格式生成文件。根据回答填充值；无回答 → 采用括号中给出的默认值。

生成时替换：`[DZISIAJ]` → 以 DD.MM.RRRR 格式填写今天的日期；`[lista z odpowiedzi]` → 用所给回答的具体清单；`[odpowiedź]` → 从选项中选择的值或用户的文本。

```markdown
# practice-profile.md
# Konfiguracja kancelarii — plik prywatny (gitignored)
# Wygenerowany przez: workflows/konfiguracja-kancelarii.md
# Data: [DZISIAJ]

## Profil praktyki

Główne typy umów: [lista z odpowiedzi / domyślnie: body leasing IT, NDA, SaaS, wdrożenia]
Reprezentacja: [Zamawiający / Wykonawca / Obustronnie]
Rynek: [B2B krajowy / B2B międzynarodowy / mieszany]
Wielkość klientów: [MŚP / korporacje / mieszane]
Branże specjalizacji: [lista]

## Progi ryzyka

Styl: [Konserwatywny / Umiarkowany / Agresywny / domyślnie: Umiarkowany]
Próg pełnej analizy: [kwota PLN / domyślnie: 100.000 PLN rocznie]

RED bezwzględne (zawsze blokuj bez negocjacji):
- [lista z odpowiedzi]
- [domyślnie: brak cap, wyłączenie winy umyślnej, brak pól eksploatacji przy IP]

## Domyślne pozycje negocjacyjne

Cap odpowiedzialności (punkt wyjścia): [odpowiedź / domyślnie: 12 miesięcy wynagrodzenia netto]
Okres poufności po zakończeniu: [odpowiedź / domyślnie: 3 lata dla informacji zwykłych, bezterminowo dla tajemnicy przedsiębiorstwa]
Pozycja RODO: [Administrator / Podmiot przetwarzający / Obustronnie]
Forum sporów: [odpowiedź / domyślnie: sąd właściwy dla siedziby naszego klienta]
Kary umowne: [standardowo / na żądanie klienta]

## Styl i format

Legal design: [Classic / Light legal design / domyślnie: Light legal design]
Formalność odpowiedzi: [Formal / Semi-formal / Operacyjny / domyślnie: Operacyjny]
Język roboczy: [PL / EN+PL / domyślnie: PL]
Format raportów: [uwagi z odpowiedzi]

## Wykluczenia

Typy spraw poza profilem: [lista z odpowiedzi]
Typy klientów poza profilem: [lista z odpowiedzi]
Uwagi dodatkowe: [odpowiedź do Sekcji 5 pyt. 3]
```

---

## 生成后——管理员操作说明

```
1. Skopiuj wygenerowany blok powyżej do pliku: practice-profile.md
   (w katalogu głównym skilla — tym samym co SKILL.md)

2. Plik jest gitignorowany — nie trafi do repozytorium publicznego.

3. Od tej pory wszystkie workflow czytają practice-profile.md na starcie sesji
   i dostosowują zachowanie do Twojego profilu kancelarii.

4. Aktualizacja profilu: uruchom ponownie ten workflow lub edytuj
   practice-profile.md ręcznie.
```
