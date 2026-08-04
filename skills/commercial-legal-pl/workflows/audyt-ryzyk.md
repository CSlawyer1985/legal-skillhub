# 工作流：风险审计（独立）

> _全局规则：`references/rdzen-ktzr.md`（R1 援引 · R2 门禁 · R3 角色 · R4 画像 · R5 格式）。_

对合同进行独立的法律与商业风险审计。范围小于完整分析——**只聚焦于风险**，不涉及 essentialia、完整性检查清单和内部逻辑。

当用户说“检查风险”、“审计”、“这里有什么危险的”、“我面临什么风险”、“检查陷阱”时，使用本工作流。

---

## 第 0 步：律所记忆

分析前检查律所记忆——可能已有关于该案件或相对方的先前记录。

1. `list_categories()`——如果记忆为空：跳过本步其余部分，进入第 1 步
2. 如果记忆非空：
   - `recall("nazwa kontrahenta")`——如果在合同中可见
   - `recall("typ umowy")`——例如“NDA”、“body leasing”、“SaaS”
   - `recall("kluczowe ryzyka")`——例如“cap odpowiedzialności”、“non-solicitation”

简要显示命中结果（最多 5 条）：

```
📋 Pamięć kancelarii — kontekst sprawy:
[wpis 1]
[wpis 2]
...
```

如无命中——**跳过本部分，不告知用户**。进入第 1 步。

---

## 第 1 步：风险识别

带着对典型风险领域的关注阅读合同。打开 `references/zlote-reguly.md`，作为审视合同文本的过滤器。

**条文援引（R1）：** 每援引一个条文前 `verify_article()`——或在 MCP 缺失时标注 `[NIEZWERYFIKOWANE]`（未核实）。报告中错误的条文编号是实质性错误。法院判决案号**不得凭记忆给出**——如想援引判例，描述裁判要旨而不给案号，或标注 `[SYGNATURA NIEZWERYFIKOWANA]`（案号未核实）。

### 需检查的典型风险领域

**责任与违约金：**
- 无责任上限（cap）
- 无限 lucrum cessans（可得利益损失）
- 试图排除故意过错（无效——《民法典》第 473 条第 2 款）
- 违约金与违约行为不相称
- 竞业禁止无对价（无对价时——条款可能不生效或违反善良风俗）

**著作权（IT 合同）：**
- 未列明使用领域（无此——不发生处分效力，《著作权法》第 41 条第 2 款）
- 无反 copyleft 条款（收购含 GPL/AGPL 软件的风险）
- 转让人无 IP 洁净性保证
- 权利转移时点不明确

**定义与逻辑：**
- 未定义即使用的概念
- 定义相互矛盾
- 定义与正文使用不一致

**代表与授权：**
- 未指明签署人的授权依据（KRS / 授权委托书）
- 当事方信息不完整（缺少 KRS/NIP）

**解约与退出：**
- 无解约条款（《民法典》第 746 条赋予随时解约权，但若未约定解约期限和后果，一方将面临损害赔偿请求的风险）
- 无退出程序（材料、数据返还，WIP 结算）
- 解约权不对称（仅一方可解约）

**RODO：**
- 无《RODO》第 28 条委托处理协议即处理数据
- 无次级处理者清单
- 无数据返还/删除程序

**法律定性依据与重新定性：**
- body leasing 中——无明确排除《劳动法典》第 22 条第 1 款，专家（Specjalista）无自主性（被重新定性为劳动关系的风险）
- 承揽合同（umowa o dzieło）中——无成果标的（被重新定性为委托合同、承担 ZUS 社保后果的风险）

**保密：**
- 无合同结束后的保密期
- 无排除情形（公开信息、独立开发的信息）
- 无违约金（难以执行）

**争议解决：**
- 管辖法院不便（无正当理由的境外管辖）
- 外国法（如为波兰合同——不必要的复杂化）
- 仲裁条款未明确仲裁机构

---

## 第 2 步：风险分级

为每个识别出的风险分配等级：

| 等级 | 标准 |
|---|---|
| 🔴 **严重（KRYTYCZNY）** | 可能导致：合同或其部分无效；无限责任；著作权丧失；对客户以意外规模进行强制执行；行政处罚 |
| 🟠 **高（WYSOKI）** | 重大财务风险（>合同价值的 10%）或运营风险；订立后难以补救；需立即谈判 |
| 🟡 **中（ŚREDNI）** | 值得改进；潜在解释问题；特定条款不生效 |
| 🟢 **低（NISKI）** | 细微不准确；文体建议；改进项 |

---

## 第 3 步：输出格式

```
## AUDYT RYZYK — [Nazwa umowy/projektu]

### 🔴 RYZYKA KRYTYCZNE

#### 1. [Krótki tytuł ryzyka] — § X ust. Y
**Opis:** [konkretnie co jest źle, dlaczego ryzykowne]
**Skutek:** [co może się stać — egzekucja, nieważność, kara, utrata praw]
**Rekomendacja:** [konkretna naprawa]
**Klauzula z bazy:** `references/baza-klauzul/XX-yyy.md`

#### 2. [...]

### 🟠 RYZYKA WYSOKIE

#### 1. [...]

### 🟡 RYZYKA ŚREDNIE

#### 1. [...]

### 🟢 RYZYKA NISKIE

#### 1. [...]

---

## OCENA BEZPIECZEŃSTWA: XX/100

[2-3 zdania uzasadnienia — co wpłynęło na ocenę]

**Werdykt:** [DO PODPISANIA z drobnymi poprawkami / DO NEGOCJACJI / DO GRUNTOWNEJ PRZERÓBKI / NIE PODPISYWAĆ]

---

*Analiza ma charakter pomocniczy i nie zastępuje oceny radcy prawnego prowadzącego sprawę.*
```

---

## 安全评分量表

| 分数 | 描述 | 结论 |
|---|---|---|
| 85–100 | 很好；细微改进 | 可签署，附带细微修改 |
| 70–84 | 良好；个别领域需谈判 | 需谈判（1–3 项 🟠 风险） |
| 50–69 | 一般；存在重大风险 | 需谈判（数项 🟠 或 1 项 🔴） |
| 30–49 | 较差；须彻底重写 | 须彻底重写 |
| 0–29 | 危险；现有形式不得签署 | 不得签署 |

每项 🔴 约扣 15–20 分，每项 🟠 约扣 5–10 分，🟡 约扣 1–3 分，🟢 约扣 0.5 分。

---

## 从条款库中选择条款以修复风险

审计后，建议用条款库中的**具体条款**修复最严重的风险。格式：

```
### Klauzule z bazy KTZR do uzupełnienia

🔴 RYZYKO 1 (nieograniczona odpowiedzialność)
→ Zastosuj: `references/baza-klauzul/11-odpowiedzialnosc.md` — wariant z capem 12 mies. wynagrodzenia

🔴 RYZYKO 2 (brak klauzuli anty-copyleft)
→ Zastosuj: `references/baza-klauzul/08-prawa-autorskie-ip.md` (wariant z gwarancjami czystości IP)

🟠 RYZYKO 3 (brak okresu poufności po umowie)
→ Zastosuj: `references/baza-klauzul/09-poufnosc.md` — model warstwowy okresów poufności (10 lat / bezterminowo dla tajemnicy przedsiębiorstwa)
```

此处不粘贴条款全文（除非用户要求）——只展示**到哪里去找**。

---

**STOP。展示报告并询问：**“你希望我为所标示的哪个风险生成修改后的条款？”
