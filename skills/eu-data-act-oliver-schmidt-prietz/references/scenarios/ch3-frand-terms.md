# ch3-frand-terms

**锚点：** 数据持有者 × 第三章 × 第 8 条 FRAND。凡数据持有者负有（依第 5 条或依其他欧盟或成员国法律）向数据接收者提供数据的义务时，规范该安排的横向合同条款框架。多数第三章起草工作由此开始，因为第 8 条在协议条款层面设定实体标准，而后第 9 条设定价格。

**进入路径：**

- "起草我们的第三章义务要求我们提供的数据共享条款。"
- "我们如何为下游接收者构建对此数据集的 FRAND 访问安排？"
- "接收者说我们的访问条件具有歧视性。我们如何回应？"
- "我们负有 [行业性文书] 项下的强制共享义务。我们可以施加哪些合同条款？"
- "这些访问条件是否符合第 8 条？"

**相邻卡片（如事实指向，改走以下路径）：**

- 接收者专门挑战价格而非条款：`ch3-compensation-challenge.md`。
- 争议为第 13 条下 B2B 合同中被单方强加条款的不公平性：`ch4-unfairness-challenge.md`。
- 数据持有者考虑以商业秘密为由扣留数据而非约定条款：`ch2-trade-secret-stages-1-2.md`（第二章梯子适用于商业秘密数据；第三章仍规范所共享数据的商业条款）。
- 数据接收者是依第 5 条行事的 DMA 指定守门人：`ch2-art5-third-party.md`（尚未起草；依第 5 条第 3 款，守门人被排除在第 5 条第三方之外）。

---

## 典型事实模式

数据持有者在企业对企业关系中负有向数据接收者提供数据的义务。该义务或产生于用户依《数据法案》第 5 条提出的请求，或产生于另一项经引用而触发第三章（第 12 条第 1 款）的欧盟或成员国法律共享义务。双方正在协商，或即将协商规范数据提供安排的合同。

数据持有者通常希望使补偿最大化、保持对范围和使用的控制，并避免为其他接收者依非歧视义务援引的条款开创先例。数据接收者通常希望获得可预测的访问、透明的定价，以及免受会掏空访问权的条款之害。双方均在作为兜底的第 13 条不公平性控制下运作，该控制在任何 FRAND 合规起草之后依然存续（第 8 条第 2 款）。

数据通常是混合的：某些类别可能受商业秘密保护（触发第 8 条第 6 款和第二章梯子），某些可能涉及个人数据（触发 GDPR 叠加），部分可随时获得，部分不可。

---

## 关键纪律

以下三项是第 8 条起草的承重纪律。三者须同时坚守。

- **补偿方向是接收者向持有者。** 第三章是不对称的。数据接收者为获得数据而向数据持有者支付。方向颠倒的草稿（将持有者视为付费方，或视为有义务免费提供除非例外适用）错误陈述了基本经济关系。补偿的例外是第 9 条第 4 款（中小企业或非营利研究接收者：仅成本，无加成）和第 9 条第 6 款（依其他欧盟或成员国法律降低或免除补偿）。见 `references/gotchas.md` 条目 15。
- **FRAND 是四项义务，不是口号。** 第 8 条第 1 款课以公平、合理、非歧视**且**透明四项义务。它们累积适用，各自具有独立的操作性内容。某一条款可能在抽象意义上合理，但仍在可比接收者之间构成歧视（第 8 条第 3 款），或透明但仍不公平（第 13 条叠加）。四项义务须分别检验。
- **第 13 条不公平性不被第 8 条合规所取代。** 第 8 条第 2 款明文规定：涉及数据访问和使用，或数据相关义务违约的责任与救济的合同条款，如依第 13 条意义不公平，或减损用户第二章权利，则不具约束力。起草 FRAND 合规条款并不排除第 13 条黑名单和灰名单；两种制度并行适用于同一合同。

---

## 七步走

### 第 1 步：范围核查

核实《数据法案》适用。运行第 1 条第 2/3 款范围核查、第 1 条第 6 款排除（刑事执法、海关、税收、国家安全、自愿公私安排、特定欧盟法律文书）。就第三章触发而言，特别确认存在提供数据的义务——依第 5 条或依另一欧盟或成员国法律文书。无义务则第三章不触发；自愿共享仍不受第 8 条约束（序言第 42 段末句："自愿数据共享不受这些规则影响"）。

确认时间挂钩。第三章适用于 2025 年 9 月 12 日之后生效的欧盟或成员国法律项下义务（第 50 条第四款）。此前生效文书项下的共享义务不在第三章范围内；此时合同条款游离于第 8 条框架之外。

### 第 2 步：章节识别

第三章。第 8 条规范条件，第 9 条规范补偿。第 10 条提供争议解决途径。第 12 条第 1 款是将（欧盟或成员国法律项下的）第三方共享义务纳入第三章的适用范围条款。

当第 5 条（用户指示的第三方共享）为触发点时，第二章和第三章同时触发。第二章规范用户和第三方的权利；第三章规范数据持有者与数据接收者之间的商业条款。两章相互作用，互不取代。

当就特定条款主张第四章不公平性时，分析在第 13 条下并行进行（见 `ch4-unfairness-challenge.md`）。第 8 条第 2 款明确交叉引用。

### 第 3 步：角色映射

须逐主体映射。在输出中以表格呈现。

| 主体 | 《数据法案》角色 | GDPR 角色（如涉个人数据） | 其他 |
|--------|---------------|----------------------------------------|-------|
| 数据持有者 | 数据持有者（第 2 条第 13 款） | 通常为控制者 | 对某些数据类别，可能依指令 (EU) 2016/943 及《数据法案》第 2 条第 19 款为商业秘密持有者 |
| 数据接收者 | 数据接收者（第 2 条第 14 款） | 接收个人数据时为控制者；或作为代表用户的服务提供者接收时为处理者 |  |
| 用户（如第 5 条为触发点） | 用户（第 2 条第 12 款） | 非数据主体时为序言第 34 段下的控制者（`references/gotchas.md` 条目 3）；为自然人时为数据主体 |  |
| 受影响的数据主体（如用户或接收者为企业） |  | 数据主体 |  |

当数据接收者为中小企业或非营利研究组织时，在角色映射行标注；这将改变第 9 条第 4 款的测算（仅成本，无加成）。第 9 条第 4 款例外有其自身的合格检验（无中小企业合作伙伴或关联企业；见第 9 条第 4 款），须按事实审查。

### 第 4 步：事实类别分拣

卡片特有的数据分类维度。其中多项直接输入第 8 条和第 9 条。

- **商业秘密数据与非商业秘密数据。** 触发第 8 条第 6 款例外：依第 8 条提供数据的义务"不应强制披露商业秘密"，除非欧盟法律另有规定（包括授权附带保障措施披露的第 4 条第 6 款和第 5 条第 9 款）。当第 5 条为触发点时，第二章梯子适用于商业秘密数据；第 8 条仍规范（附带保障措施）所共享任何数据的商业条款。
- **个人数据与非个人数据。** 决定 GDPR 叠加（第 1 条第 5 款桥梁）。混合数据集（序言第 7 段）要求个人数据成分基于有效的 GDPR 法律依据处理；数据接收者作为控制者或处理者的角色本身即是需要明示处理的合同条款。
- **数量、格式、性质。** 第 9 条第 3 款允许补偿取决于这些因素。将数据按数量区间和格式类别分拣是构建符合第 9 条的定价结构的前提。
- **成本基础。** 第 9 条第 2 款第 a 项指向提供数据所产生的成本（格式化、通过电子方式传播、存储）。第 9 条第 2 款第 b 项指向收集和生产方面的投资。这是输入补偿的两条成本线；持有者须以足够细节识别两者以满足第 9 条第 7 款。
- **接收者可比类别。** 第 8 条第 3 款非歧视是针对可比类别的接收者检验的。数据持有者须识别其以何种条款服务哪些类别的接收者，因为数据持有者负有在收到有理由的请求时证明不存在歧视的责任（第 8 条第 3 款第二句）。

### 第 5 步：逐项适用第 8 条

第 8 条第 1 款分解为四项实体义务加第四章交叉引用。每项独立。

1. **公平。** 法规未作正面定义。序言第 61 段将公平锚定于"严重偏离良好商业实践"，用于第 13 条不公平性检验；第 8 条公平义务精神相同，但在合同订立阶段运作，而非作为事后无效化。公平条款是不滥用数据持有者相对于接收者的结构性地位的条款。具体的第 13 条不公平性检验在任何第四章分析的第 5 步另行进行。
2. **合理。** 合理性既适用于非价格条款，也适用于价格。对价格，第 9 条第 1 款和第 9 条第 2 款提供操作性内容。对非价格条款，合理性对照双方合法利益解读：持有者的投资回收和持续数据生成（序言第 46 段），以及接收者对数据价值的有效获取（序言第 47 段）。
3. **非歧视。** 第 8 条第 3 款。持有者不得在可比类别的数据接收者之间实行歧视，包括合作伙伴或关联企业。经有理由的请求，持有者必须无不当迟延地向接收者提供显示不存在歧视的信息。一旦接收者提出有理由的质疑，举证责任即落在数据持有者身上（序言第 45 段）。以客观理由证明正当的差异不构成歧视（序言第 45 段第三句）。
4. **透明。** 第 8 条第 1 款将透明作为独立义务课以要求。第 9 条第 7 款为其在补偿方面赋予操作性内容：持有者应向接收者提供充分详细载明补偿计算基础的信息，以使接收者能够评估对第 9 条第 1-4 款的合规。对非价格条款，透明意味着清晰披露访问条件、允许使用范围，以及接收者必须实施的任何技术或组织措施。
5. **第 13 条不公平性兜底（第 8 条第 2 款）。** 涉及数据访问和使用，或数据相关义务违约或终止的责任与救济的合同条款，如依第 13 条意义不公平，则不具约束力。起草 FRAND 合规条款并不穷尽第 13 条核查；第 13 条第 4 款黑名单和第 13 条第 5 款灰名单并行适用。运行之。
6. **第 8 条第 4 款用户请求前置条件。** 数据持有者不得向数据接收者提供数据（包括以排他方式），除非用户依第二章提出请求。当第三章触发点为第 5 条时，用户请求本身即满足该条件。当第三章触发点为另一欧盟或成员国法律时，义务依该法产生而非凭用户请求；第 8 条第 4 款限制特别适用于第 5 条共享，不阻碍其他文书强制要求的共享。
7. **第 8 条第 5 款信息最小化。** 任何一方均无义务提供超出核实合同条款或本条例或其他适用欧盟或成员国法律合规所必需的信息。这封顶了持有者依第 8 条第 3 款和第 9 条第 7 款的披露义务，也封顶了接收者在任何审计或合规条款下的报告义务。
8. **第 12 条第 2 款反减损。** 减损第三章、变更其效果或排除其适用、损害一方（或适用时用户）利益的合同条款不具约束力。包括试图将合同抬出第三章范围的合同法律选择条款。

### 第 6 步：跨制度关卡核查

- **GDPR 叠加（如涉个人数据则加载）。** 阅读 `references/gates/gdpr-overlay.md`。数据接收者通常成为其接收的个人数据的控制者（或代表用户的处理者）；合同必须载明这一点及相应的法律依据。当第 5 条下用户非数据主体时，第 4 条第 12 款和第 5 条第 7 款以存在有效的 GDPR 法律依据为披露条件（见 `references/gotchas.md` 条目 3）。
- **商业秘密指令叠加（如任何数据被主张为商业秘密则加载）。** 阅读 `references/gates/trade-secrets-directive.md`。第 8 条第 6 款不要求披露商业秘密；当数据持有者同意共享商业秘密数据时，第 4 条第 6 款 / 第 5 条第 9 款保障措施适用，FRAND 条款必须容纳这些保障措施（保密、访问限制、技术和组织措施）。第 9 条下的补偿可包括实施这些保障措施的成本。
- **DMA 守门人排除（本卡仅警示）。** 第 5 条第 3 款将守门人排除在第 5 条合格第三方之外。当第三章触发点为第 5 条且接收者是 DMA 指定守门人或为其行事时，共享根本不合法；第 8 条起草无实际意义。产出前运行 `references/gates/dma-gatekeeper.md`。当第三章触发点为另一欧盟或成员国法律（非第 5 条）时，守门人排除不直接触发；行业性法律可能有其自身限制。
- **行业性特别法（仅警示）。** 当共享义务产生于行业性文书（金融服务数据、车辆远程信息处理、健康数据、能源数据、农业数据）时，行业性文书是共享义务的主要来源，第三章是叠加其上的横向层。第 9 条第 6 款明确允许其他欧盟或成员国法律排除补偿或规定较低补偿。运行 `references/gates/sectoral-lex-specialis.md` 以识别任何行业性叠加。
- **成员国实施法律（仅警示）。** 第 10 条下争议解决机构在成员国层面认证。运行 `references/gates/member-state.md` 以确认何机构主管，以及该成员国是否已通知第 37 条主管机关。

### 第 7 步：现行法与提案的综合

- **现行法。** 适用法规 (EU) 2023/2854（《数据法案》）第 8 条和第 9 条，第 10 条争议解决可用。逐字文本见 `sources/regulation-2023-2854.md` 第 8 条（第 778-798 行）和第 9 条（第 800-825 行）；操作性序言见序言第 42-51 段。
- **《数字综合》下的拟议修订。** COM(2025) 833 final（2025 年 11 月 19 日）在 FRAND 框架本身方面未实质改变第 8 条或第 9 条。委员会已预告即将出台的关于合理补偿计算的第 9 条第 5 款指南（FAQ Q72：预计 2026 年第二/第三季度，截至 2026 年 5 月尚未通过）。见 `references/gotchas.md` 条目 16 和 `sources/digital-omnibus-amendments-tracker.md`。

输出以现行法为操作性依据。即将出台的第 9 条第 5 款指南被标注但未被依赖。

---

## 决策点

第 5 步和第 6 步之后，分析得出三条路径之一。

1. **第 8 条第 1 款四项义务均已起草且跨制度关卡畅通。** 产出符合 FRAND 的数据共享条款（下文输出路径 1）。
2. **特定条款未通过第 13 条兜底。** 识别未通过条款并重新起草。本卡产出红线稿（下文输出路径 2）而非完整协议。
3. **第三章触发缺失。** 既无第 5 条请求，亦无其他欧盟或成员国法律共享义务时，第三章不适用。该安排属自愿（序言第 42 段）；双方自由缔约，不受第 8 条框架约束。本卡产出简短说明，解释触发缺失并将用户导向标准合同起草。

---

## 输出骨架：路径 1（符合 FRAND 的数据共享条款）

起草输入，默认 Markdown，结构化为数据共享协议的执行条款。长度：视数据复杂程度通常 2 至 4 页。用户按自身模板调整。

结构：

```
DATA-SHARING AGREEMENT (Ch III COMPLIANT)

Parties:
  Data Holder: [legal entity]
  Data Recipient: [legal entity]

Recital A: Trigger for sharing
  [Identification of the obligation. Either: (i) Art. 5 request by user
  [user identity, date]; or (ii) [Union or national law instrument]
  imposing the sharing obligation, citation, effective date.]

Recital B: Categorisation of data
  [Brief description of data categories in scope, separated as
  trade-secret / non-trade-secret, personal / non-personal, raw or
  pre-processed / out-of-scope-derived. Detailed schedule attached.]

1. Scope of data made available
   [Specific data categories. Cross-reference to schedule. Statement
   of exclusions (derived data; data not readily available; data
   covered by Art. 4(6) / 5(9) safeguards under separate annex).]

2. Conditions of access (Art. 8(1))
   2.1 Fair: [description of access modalities. Avoid take-it-or-leave-it
       drafting on non-essential terms.]
   2.2 Reasonable: [permitted use scope. Restrictions read against
       Art. 6(2) where the recipient is an Art. 5 third party.]
   2.3 Non-discriminatory: [statement that the terms are offered to all
       comparable categories of recipients on the same basis;
       identification of any objective reasons for differentiation that
       the holder relies on.]
   2.4 Transparent: [disclosure of the basis for the conditions in
       sufficient detail for the recipient to verify compliance.]

3. Compensation (Art. 9)
   3.1 Compensation: [amount and structure. Recipient pays holder.]
   3.2 Basis of calculation (Art. 9(2)): [costs incurred in making the
       data available, including formatting, dissemination, storage
       (point (a)); investments in collection and production (point (b))
       where applicable.]
   3.3 Dependence on volume, format, nature (Art. 9(3)): [where the
       pricing varies by these factors, the variation is specified.]
   3.4 SME / not-for-profit research recipient (Art. 9(4)): [if the
       recipient qualifies, the compensation does not exceed the
       Art. 9(2)(a) cost base; no margin. Statement of qualifying
       criteria. If the recipient does not qualify, this clause is
       inapplicable; record that explicitly.]
   3.5 Transparency of calculation (Art. 9(7)): [the holder provides
       the recipient with the cost-and-margin breakdown in sufficient
       detail for the recipient to assess compliance with Art. 9(1)-(4).
       Schedule attached.]

4. Non-discrimination challenge procedure (Art. 8(3))
   [On a reasoned request by the recipient that the terms are
   discriminatory, the holder provides without undue delay information
   showing no discrimination, including identification of comparator
   recipients and any objective reasons for differentiation.]

5. Trade-secret safeguards (Art. 8(6), Art. 4(6) or 5(9) where the
   trigger is Art. 5)
   [Identification of trade-secret data. Technical and organisational
   safeguards (confidentiality; access protocols; technical standards).
   Cross-reference to a separate confidentiality annex if needed.]

6. Use restrictions
   [Permitted purposes. Where the trigger is Art. 5, recall that the
   recipient is bound by Art. 6 restrictions (no profiling beyond
   strict necessity; no onward sharing without user contract; no use
   to develop a competing connected product; etc.). Avoid drafting
   that purports to displace Art. 6.]

7. Term, renewal, termination
   [Reasonable notice, no unreasonably short termination. Avoid the
   Art. 13(5)(f) grey-list trap (termination at unreasonably short
   notice).]

8. Liability and remedies
   [Symmetrical, non-discriminatory. Avoid Art. 13(4)(a) (exclude
   liability for intentional or gross negligence) and 13(4)(b)
   (exclude remedies for non-performance). Draft these by reference to
   ordinary contract principles, not as one-sided exclusions.]

9. Dispute settlement (Art. 10)
   [Reference to Art. 10 certified dispute settlement body as an
   option for the parties, without prejudice to court or tribunal
   recourse. Specify a Member State whose dispute body is certified
   if the parties want a defined forum.]

10. Anti-derogation (Art. 12(2))
    [Statement that no term of this agreement derogates from Ch III
    or Ch II rights to the detriment of either party or the user.
    Severability clause carries the standard Art. 13(7) result for
    any term later found unfair.]

Schedules:
  - Data schedule (categorisation by trade-secret / personal /
    readily available)
  - Compensation calculation (cost lines, margin if any, volume
    bands)
  - Trade-secret safeguards annex (if applicable)
```

---

## 输出骨架：路径 2（未通过条款的红线稿）

简短响应。Markdown。引用未通过条款，识别其在第 8 条或第 13 条下的缺陷，提出修订措辞。

结构：

```
The following term in the proposed data-sharing agreement is not
binding as drafted under Art. 8(2) of Regulation (EU) 2023/2854 (Data
Act):

> [Quote the failing term verbatim from the draft.]

The failure is [Art. 13(4)(N) / Art. 13(5)(N) / Art. 8(3)
non-discrimination / Art. 9(4) SME compensation cap / etc.]. [One- or
two-sentence explanation of why the term fails on the regulation's
operative text, with citation.]

Proposed amended language:

> [Replacement clause that addresses the failure while preserving the
> data holder's legitimate commercial interest where possible.]

The amendment cures the specific defect. Other terms of the draft
agreement remain to be reviewed against the full Art. 8 / Art. 13
matrix. See `Output Path 1` for the complete checklist.
```

---

## 输出骨架：路径 3（无第三章触发）

极简短响应。第三章框架不适用。

```
Ch III of the Data Act applies only where the data holder is obliged
to make data available, either under Art. 5 (user-directed third-party
sharing) or under other Union or national law (Art. 12(1)). On the
facts presented, no such obligation has been identified.

Voluntary data sharing remains unaffected by Ch III rules (Recital 42,
last sentence). The parties contract freely. The Art. 8 FRAND
framework, the Art. 9 compensation framework, and the Art. 10 dispute
settlement framework do not apply by force of law.

The Art. 13 Ch IV unfairness control may still apply (Ch IV is not
conditional on a Ch III trigger; it covers any B2B data-related
contractual term between enterprises). Route to
`ch4-unfairness-challenge.md` if the unfairness of a specific term is
in issue.
```

---

## 需加载的引用

本卡触发时，引用：

- `sources/regulation-2023-2854.md` 第 8 条（一律引用）；第 9 条（涉补偿时）；第 10 条（涉及争议解决选项时）；第 12 条（第三章义务范围）；第 13 条（第 8 条第 2 款交叉引用）；第 50 条（第三章的时间适用性，第四款）。
- `sources/regulation-2023-2854.md` 序言第 42 段（横向访问规则；自愿共享例外）；序言第 45 段（非歧视；举证责任）；序言第 46 段（合理补偿原则）；序言第 47 段（成本与加成结构）；序言第 49 段（中小企业仅成本上限）；序言第 51 段（计算透明度）。
- `sources/faq-v1-4.md` Q38（委员会关于接收者之间差异的解释）；Q39（委员会关于补偿无上限或下限的解释；中小企业无加成规则）；Q40（委员会关于争议解决覆盖范围的解释）；Q72（委员会关于第 9 条第 5 款指南时间的解释）。一律表述为委员会解释。
- 指令 (EU) 2016/943（《商业秘密指令》），当第 8 条第 6 款商业秘密数据在范围内时。实质性框架见 `references/gates/trade-secrets-directive.md` 关卡文件。

绝不凭训练数据改写法规。从源文件引用。

---

## 交叉引用

- `references/gates/gdpr-overlay.md`（如涉个人数据则加载）。
- `references/gates/trade-secrets-directive.md`（如任何数据被主张为商业秘密则加载；第 8 条第 6 款交叉引用第 4 条第 6 款和第 5 条第 9 款保障制度）。
- `references/gates/dma-gatekeeper.md`（如数据接收者是 DMA 指定守门人或为其行事，且第三章触发点为第 5 条，则加载）。
- `references/gates/sectoral-lex-specialis.md`（仅警示；共享义务产生于行业性文书时加载）。
- `references/gates/member-state.md`（仅警示；用于第 10 条争议解决机构选择和第 37 条主管机关）。
- `references/gotchas.md` 条目 15（第三章补偿是数据接收者向数据持有者；基本经济学核查）。每份第 8 条/第 9 条输出强制检查。
- `references/gotchas.md` 条目 16（第 9 条第 5 款委员会指南即将出台，尚未发布）。每次补偿起草均标注。
- `references/gotchas.md` 条目 3（非数据主体的用户为控制者）、4（"无不当迟延"无数字 SLA）、11（守门人排除是双向的）、19（FAQ 不具权威性）。逐一核查。
- `references/method/analysis-method.md`（七步流程；本卡为其中一例）。
- `references/method/house-style.md`（输出纪律）。
- `sources/digital-omnibus-amendments-tracker.md`（无实质性第 8 条/第 9 条修订；第 9 条第 5 款指南仍待出台）。

---

## 起草者注

使用本卡的操作观察。仅三条。

- **定价透明度是实践中检验最多的义务。** 第 9 条第 7 款要求数据持有者向接收者提供充分详细的计算基础，以允许评估对第 9 条第 1-4 款的合规。骨架式定价（"市场费率"；"成本加成"）不能满足第 9 条第 7 款。持有者须按接收者逐一识别成本线（格式化、传播、存储；如主张，收集和生产投资）和加成（如有，且对第 9 条第 4 款接收者为零）。先起草定价附件，再起草合同条款。
- **非歧视举证责任早早就转移。** 一旦接收者依第 8 条第 3 款提出有理由的请求，数据持有者即负有证明条款不具歧视性的责任。与定价附件在同一工作流中建立可比接收者登记册；它是持有者应对任何第 8 条第 3 款挑战或任何第 10 条争议的防御性证据。序言第 45 段明确将举证责任置于数据持有者。
- **第 9 条第 5 款指南是缺失的一块。** 截至 2026 年 5 月，委员会尚未通过关于合理补偿计算的第 9 条第 5 款指南；依 FAQ Q72，预期通过窗口为 2026 年第二/第三季度。补偿分析仅依赖法规文本和第 8 条公平原则进行。每份输出均须标注指南待出台；用户今天作出的决定在指南落地时可能发生变化。
