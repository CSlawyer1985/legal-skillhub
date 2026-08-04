# 工作流：客户冷启动（新客户入职引导）

> _全局规则：`references/rdzen-ktzr.md`（R1 援引 · R2 门禁 · R3 角色 · R4 画像 · R5 格式）。_

**目标：** 对新客户进行快速、结构化的访谈（10-15 分钟），据此形成*客户画像*，供 Claude 之后处理其事务时使用。画像有助于将建议语境化——没有画像，Claude 只能在*“泛化 B2B”*基础上工作，通常效果不如基于真实客户画像。

**灵感：** Anthropic `claude-for-legal`（commercial-legal、employment-legal）的*“cold-start interview”*。已适配波兰 B2B IT 和中小企业市场。

**触发词：** 律所新客户、*“onboarding”*、*“客户画像”*、*“与客户的首次会谈”*、*“为特定客户配置 Claude”*、*“保存客户偏好”*。

**输出：** 用户私有结构中的 `profile/klient-[nazwa-roboczej-nazwy].md` 文件（文件夹已 gitignore，不提交到公开仓库）。画像是*活文档*——在合作过程中持续更新。

**声明：** 访谈具有信息性和操作性，服务于律所工作。不替代对客户具体事务的法律意见。画像用于将建议语境化，而非自动生成法律决策。

## 访谈结构（10-15 分钟）

访谈有 6 个部分，每部分 1-3 分钟。问题可以按任意顺序提出——重要的是最终有材料可填写画像的每一部分。

### 第 1 部分：客户商业画像（2-3 分钟）

问题：

1. *„贵方商业上从事什么？"*（行业、商业模式）
2. *„公司处于什么发展阶段？"*（pre-seed / seed / A 轮及以上 / 成熟 / 企业集团）
3. *„规模多大？"*（人数、年营业额、相对方数量）
4. *„贵方在本地、区域、全国还是国际范围经营？"*
5. *„行业是否存在监管限制？"*（KSC/NIS2、RODO 特别要求、MIFID、MAR、医疗行业、能源行业、教育行业）

**对 Claude 工作的意义：** 行业和发展阶段决定默认的语气（正式对比伙伴式）、详细程度（初创企业想要简短，企业集团想要文档化），以及监管语境。

### 第 2 部分：典型事务与相对方（2-3 分钟）

问题：

1. *„贵方最常遇到哪些类型的合同？"*（NDA、body leasing、实施、许可、SaaS、分销、代理、雇佣、B2B）
2. *„典型的相对方是谁？"*（行业、规模——大型企业、中型 B2B、小型、消费者）
3. *„是否有定期合作的相对方？"*（及其特征——*„通常咄咄逼人"*、*„通常合理"*、*„总是试图加塞 X"*）
4. *„贵方有自己的合同范本，还是通常用对方的范本？"*

**对 Claude 工作的意义：** Claude 可以主动建议客户行业典型的条款类型。了解*谁在谈判桌对面*，有助于选择合同的基调（强硬对比让步）。

### 第 3 部分：风险偏好（2-3 分钟）

问题：

1. *„贵方如何定义法律风险容忍度？"*（保守 / 均衡 / 进取）
2. *„贵方是否经历过诉讼或仲裁争议？"*（何种、结果如何）
3. *„贵方对典型风险条款是否有政策？"*——责任上限（cap）、赔偿（indemnifikacja）、违约金、竞业禁止
4. *„是否有贵方从不接受的条款？"*（deal breakers，交易破坏因素）
5. *„是否有贵方在自己的合同中始终坚持的条款？"*（must-have，必备条款）

**对 Claude 工作的意义：** 客户的风险偏好影响建议。*保守型*客户获得更严格的保护条款；*进取型*客户获得带谈判施压要素的合同。

### 第 4 部分：升级与决策（1-2 分钟）

问题：

1. *„贵方一侧谁是合同决策人？"*（CEO / CFO / 法务负责人 / 创始人）
2. *„超过什么阈值的事项需要决策人介入？"*（金额、对经营的影响、时间）
3. *„涉及贵公司事务时应把谁纳入沟通？"*（除主要联系人外——例如税务问题找会计、实施问题找 IT 经理）
4. *„贵方在其他领域与哪些律所/顾问合作？"*（如相关——例如房产事务找公证人、税务顾问）

**对 Claude 工作的意义：** Claude 可以指出某事务需要升级到决策人或其他顾问；也知道引用谁作为*„依据 X 先生/女士的意见"*。

### 第 5 部分：沟通风格与格式（1-2 分钟）

问题：

1. *„贵方期望律所采用何种沟通风格？"*（正式、伙伴式、重要事务带正式要素的伙伴式）
2. *„工作事务中，贵方偏好书面沟通（电子邮件、DMS）还是口头沟通（电话、视频）？"*
3. *„贵方期望文件采用何种形式？"*——Word（.docx）、PDF、两者；经典排版（Times New Roman）还是更现代（Arial）；合同排版的偏好
4. *„贵方使用法律设计（关键条款表格、目录、示意图）吗？"*——见 `references/legal-design.md`
5. *„贵方期望技术性解释（带注释的条款），还是偏好无元评论的干净合同？"*

**对 Claude 工作的意义：** Claude 会根据客户的排版偏好和沟通风格调整生成的文档。*“老派”*客户得到 Times 12，*“现代”*客户得到带法律设计的 Arial 11.5。

### 第 6 部分：特定条款与语境（1-2 分钟）

问题：

1. *„贵方有自己的条款范本想使用吗？"*（例如自有保密条款、自有 RODO 条款、自有责任条款）
2. *„是否有贵方内部不可谈判的政策领域？"*（例如*„我们的最惠国（MFN）条款始终适用"*）
3. *„是否有 Claude 应当了解的技术/行业领域？"*（例如*„我们始终使用开源，因此知识产权条款必须考虑 copyleft 许可"*）
4. *„是否有贵方从不涉足的领域？"*（例如*„我们从不承接博彩/军工/加密货币行业的合同"*）

**对 Claude 工作的意义：** 客户的*“硬性规则”*不可动摇——Claude 不应质疑，只需适用。*“软性偏好”*可在具体事务中协商。

## 输出：客户画像结构

访谈后，Claude 按以下结构生成 `profile/klient-[nazwa].md` 文件（仅私有——不公开发布）：

```markdown
# Profil klienta: [Nazwa]

**Status:** robocza wersja po cold-start z dnia [data]
**Aktualizacja:** [data ostatniej aktualizacji]

## Sekcja 1: Profil biznesowy
- Sektor: [...]
- Skala: [...]
- Etap rozwoju: [...]
- Zasięg: [...]
- Ograniczenia regulacyjne: [...]

## Sekcja 2: Typowe sprawy i kontrahenci
- Najczęstsze typy umów: [...]
- Typowi kontrahenci: [...]
- Stałe relacje (i charakterystyka): [...]
- Wzór własny vs cudzy: [...]

## Sekcja 3: Profil ryzyka
- Tolerancja: [konserwatywny / wyważony / agresywny]
- Historia sporów: [...]
- Polityki co do typowych klauzul:
  - Cap odpowiedzialności: [...]
  - Indemnifikacja: [...]
  - Kary umowne: [...]
  - Zakaz konkurencji: [...]
- Deal breakers: [...]
- Must-haves: [...]

## Sekcja 4: Eskalacja
- Osoba decyzyjna: [...]
- Próg eskalacji: [...]
- Stakeholders do informowania: [...]
- Inni doradcy: [...]

## Sekcja 5: Komunikacja i format
- Styl: [...]
- Forma komunikacji roboczej: [...]
- Format dokumentów: [...]
- Legal design: [tak / nie / tylko dla X]
- Komentarze w dokumentach: [tak / nie]

## Sekcja 6: Specyficzne klauzule i konteksty
- Wzory własne: [...]
- Hard rules: [...]
- Konteksty technologiczne / branżowe: [...]
- Branże wykluczone: [...]

## Historia spraw (uzupełniana w toku)
- [data] — [krótki opis sprawy] — [wynik / status]

## Notatki dodatkowe
[notatki ad-hoc po rozmowach]
```

## 操作规则：如何使用画像

1. **每件新事务前**，Claude 阅读客户画像——将建议语境化。
2. **每件重要事务后**，Claude 或主办律师更新*“Historia spraw”（案件历史）*部分——随着时间推移，画像越来越丰富。
3. **每 6-12 个月**，画像应与客户一起复审（简短 check-in，15-20 分钟）——偏好可能随公司发展而变化。

## 操作规则：何时运行冷启动

- ✅ 律所新客户（最初 1-2 件事务）
- ✅ 既有客户，但 Claude 此前未用于处理其事务
- ✅ 客户发生重大变化（新管理层、新一轮融资、商业模式变化）
- ❌ 已有画像且画像仍然有效的长期客户（距上次更新不足 12 个月）

## 技能内的关联

- `references/zlote-reguly.md`——KTZR 黄金规则的语境，不受客户画像影响而改变
- `references/style-redakcyjny.md`——KTZR 风格，不变；客户画像调整的是*强度*（例如是否采用法律设计）
- `references/legal-design.md`——*„classic-clean"*（经典简洁）对比 *„light legal design"*（轻量法律设计）模式的选择取决于客户画像（第 5 部分）
- `workflows/triage-szybki.md`——分诊可考虑客户画像（对保守型客户的红灯信号，对进取型客户可能是黄灯）
- `workflows/pelna-analiza.md`——完整分析始终考虑客户画像

## 最终声明

客户画像是*律所的工作工具*，不是对客户的承诺。具体事务的决策始终结合当时情况作出，不受画像中所记一般偏好的约束。画像使工作更便捷，但不会替代工作本身。
