# 波兰商事合同（Polskie Umowy Gospodarcze）

**展示 Claude 在波兰合同中可以如何工作的示例。**
可作为律师实用 AI 工具应有样貌的起点。

诞生于本所（**Kancelaria Radców Prawnych Żurawska Piotrowski i Wspólnicy**，[ktzr.pl](https://ktzr.pl)），基于 B2B、IP 与 IT 合同的日常执业实践。

> ⚠️ **声明：** 本 skill 不替代法律意见，它是辅助律师工作的操作性工具，每项具体事务均须由具备资格的人员单独核实。

## 我们为何发布

关于 AI 在波兰法律科技（Legaltech）中的讨论很多，尤其在会议和社交媒体帖文中，但真正能在律所日常执业中发挥作用的实际落地要少得多。

我们认为最好的工具并非来自会议演讲或咨询性质的 PoC，而是来自日常使用。我们为自己做事、投入使用、在过程中改进，当它开始发挥作用时——与他人分享。

这里我们从具体事项入手，即 B2B、IP 和 IT 合同的编辑起草，将其封装为 Claude skill 并公开展示——不是为了宣布*“KTZR 的正式生产工具”*，而是为了展示一种可行的处理方式，对批评、分叉和讨论保持开放。

或许对某些人而言，它：
- 提供了如何为另一法律领域或另一律所构建自有 skill 的思路
- 引发*“波兰语的 claude-for-legal 应当是什么样”*的讨论，因为目前 Anthropic 生态主要面向美国/英国普通法

如你愿意参与（issues、PR、评论、分叉、为其他领域制作你自己的版本），皆受欢迎。

## 开始前值得了解的内容

为避免失望，几点坦诚的声明：

- **Skill 只包含我们知识库和工作流的一部分。** 完整版本保留在内部，因为法律顾问的职业保密义务（《法律顾问法》第 3 条）要求所有涉及客户具体事务、案例研究或客户画像的内容不得外泄。**我们所发布的是示例，不是*“唯一正确”*的范本。**

- **Skill 的效果取决于你自己与它的协作**——经典的 *garbage in, garbage out*（垃圾进，垃圾出）在此尤为显著，因此最佳效果来自针对自身实践的迭代改进：你将自有条款加入 `references/baza-klauzul/`，将自有规则加入 `references/zlote-reguly.md`，并添加自己的工作流。我们的这套仅构成起点。

- **Skill 不是通用范本**——它基于一家律所的设计决策，因此如果你的执业方式不同，尽可大胆分叉并按你的实践调整。

- **范围有限**，仅限 B2B、IP 和 IT 合同，不涉及刑法、行政法、税法、家事法，也不涉及法院程序。

- **Skill 尚未进入 `claude-plugins-community`**——目前请直接从我们的仓库安装。

## 内含内容

Skill 有五个实务层次：

| 层次 | 包含内容 | 文件 |
|---|---|---|
| **黄金规则** | 波兰合同编辑起草的 12 条规则：定义控制、结构、语言 | `references/zlote-reguly.md` |
| **KTZR 编辑风格** | 从执业中提炼的具体风格模式：何时用 *„W przypadku"* 而非 *„Jeżeli"*、各类关系的当事方配对、排版 | `references/style-redakcyjny.md` |
| **条款类别分类** | 7 类条款，Adams 的 MSCD 的波兰语对应版本 | `references/kategorie-klauzul.md` |
| **条款库** | 20 个主题文件，含条款范本：当事方、序言、定义、IP、RODO、违约金、和解、SaaS/托管服务规则等 | `references/baza-klauzul/` |
| **学理知识库** | 13 个法律学理分析文件：*lucrum cessans*（可得利益）、RODO、著作权、开源 copyleft、意思表示的解释、电子服务法（u.ś.u.d.e.）/DSA/AI 规则等 | `references/baza-wiedzy/` |

另有 8 个面向典型任务的现成工作流：

| 工作流 | 何时使用 |
|---|---|
| `pelna-analiza.md` | 从客户视角对合同进行完整分析 |
| `triage-szybki.md` | 5-10 分钟内快速分类 GREEN / YELLOW / RED（绿/黄/红） |
| `generator-umow.md` | 从零生成新合同 |
| `popraw-fragment.md` | 完善特定条款 |
| `audyt-ryzyk.md` | 识别相对方合同中的风险 |
| `ocena-2-strony.md` | 以对方视角分析合同（devil's advocate，魔鬼代言人） |
| `cold-start-klienta.md` | 新客户入职引导，10-15 分钟访谈 |
| `weryfikacja-spojnosci-odeslan.md` | 检查 § / ust. / pkt（条/款/项）援引的一致性 |

## 配套工具：legal-cite-pl

该 skill 与 **[legal-cite-pl](https://github.com/apiotrowski-afk/legal-cite-pl)** 搭配效果最佳——它是一个 MCP 服务器，直接从来源（Sejm ELI / EUR-Lex）获取**被援引条文的精确、现行文本**，返回**统一文本**而非原始文本。

当你在 Claude 中接入它（本地 stdio，或 Cloud Run 上的一个 URL）时，skill 援引条文（k.c.、RODO、pr. aut.、u.ś.u.d.e. 等）**会以来源验证替代模型记忆**——援引中的幻觉更少：

```
verify_article("art. 385¹ KC")   → dosłowny tekst przepisu (niedozwolone postanowienia umowne)
verify_article("art. 28 ust. 3 RODO")
```

安装与详情：**[github.com/apiotrowski-afk/legal-cite-pl](https://github.com/apiotrowski-afk/legal-cite-pl)**。

**生态中的其他工具**（波兰 LegalTech 开放工具）：
- **[anon-legal-pl](https://github.com/apiotrowski-afk/anon-legal-pl)** —— 基于 Presidio 的法律文件本地匿名化（PESEL/NIP、案号）。
- **[kancelaria-dms](https://github.com/apiotrowski-afk/kancelaria-dms)** —— 律所 DMS/CRM（Google Workspace）。

## 适用人群

实践中，该 skill 最适合：

- 处理 B2B、IP 和 IT 合同的**法律顾问（radcy prawni）与律师（adwokaci）**
- IT 公司、初创企业、法务部门的**公司内部法务（in-house counsel）**
- 在日常合同工作中使用 **Claude** 的**律师**
- **其他法律类 skill 的作者**——作为结构上的参考示例

法学院学生也会受益，但这不能替代教科书；该工具是用于处理具体条款的。

## 快速上手

### 要求

任选其一：
- [Claude.ai](https://claude.ai/) 账户（Pro 或 Team），用于在 Claude.ai 中作为 skill 使用
- Anthropic API key，用于编程化使用
- [Claude Code](https://www.anthropic.com/claude-code)，用于本地使用

### 安装

**选项 0 —— CLI（最快，支持 40+ 个 agent）**

```bash
npx skills add apiotrowski-afk/commercial-legal-pl
```

适用于 Claude Code、Cursor、Codex 及其他工具。直接从仓库安装。

**选项 1 —— Claude.ai（网页版）**

```bash
git clone https://github.com/apiotrowski-afk/commercial-legal-pl.git
```

然后：Claude.ai → Settings → Skills → Import skill → 指定目录 → 在会话中激活。

**选项 2 —— Claude Code（CLI）**

```bash
git clone https://github.com/apiotrowski-afk/commercial-legal-pl.git \
  ~/.claude/skills/commercial-legal-pl
```

Skill 将在新的 Claude Code 会话中自动加载。

**选项 3 —— 手动指定**

将仓库克隆到任意目录，在 Claude 会话中将 `SKILL.md` 的路径指定为起始上下文。

### 首次使用

三个典型起始场景：

**分析来自相对方的合同：**
> *„客户收到了一份相对方的合同。帮我分析并识别风险。"*

Claude 将加载 `workflows/pelna-analiza.md`，或者——对于更标准的合同——`workflows/triage-szybki.md`。

**生成新合同：**
> *„我需要为一家初创企业生成 NDA（当事方、期限、50k PLN 违约金）。"*

Claude 将加载 `workflows/generator-umow.md` + `baza-klauzul/` 中的相应文件。

**完善条款：**
> *„我有一条这样的责任条款。可以如何改进？"*

Claude 将加载 `workflows/popraw-fragment.md` + `style-redakcyjny.md` + 知识库中的相关文件。

## 架构

```
commercial-legal-pl/
├── SKILL.md                              ← Główny plik wejściowy dla Claude
├── README.md                             ← Ten plik
├── LICENSE                               ← Apache 2.0
├── NOTICE                                ← Standardowa nota Apache
├── .gitignore                            ← Wykluczenia poufnych materiałów
│
├── references/
│   ├── zlote-reguly.md                   ← 12 reguł redakcji
│   ├── style-redakcyjny.md               ← Warstwa 1 + 2 stylu KTZR
│   ├── kategorie-klauzul.md              ← Taksonomia (polski Adams)
│   ├── legal-design.md                   ← Typografia i layout
│   ├── essentialia-mapowanie.md          ← Essentialia negotii dla typów umów
│   │
│   ├── baza-klauzul/                     ← 20 plików tematycznych + INDEX
│   │   ├── 01-oznaczenie-stron.md
│   │   ├── 02-preambuly.md
│   │   ├── 03-definicje.md
│   │   ├── ...
│   │   └── 20-regulamin-usdde-aup.md
│   │
│   └── baza-wiedzy/                      ← 13 plików doktrynalnych + INDEX
│       ├── 01-maintenance-art750-kc.md
│       ├── 02-przeniesienie-praw-oprogramowanie.md
│       ├── ...
│       └── 13-regulamin-usdde-hosting-ai.md
│
├── workflows/                            ← 8 gotowych workflow'ów
│   ├── pelna-analiza.md
│   ├── triage-szybki.md
│   └── ...
│
└── scripts/
    ├── pre-commit-sanitizer.py           ← Hook chroniący przed wyciekiem danych
    └── install-hooks.sh                  ← Bash installer
```

## 灵感与方法

Skill 并非凭空而来——我们借鉴了：

- **Ken Adams**，《合同起草文体手册》（A Manual of Style for Contract Drafting，ABA 2023 年第 5 版）——*„categories of contract language"*（合同语言类别）概念在波兰法律体系中的改编
- **波兰立法技术规则**（波兰部长会议主席 2002 年 6 月 20 日条例）——针对法律文件的 MSCD 国内对应版本，结构层级（条 → 款 → 项 → 目）
- **Bryan Garner** 与 **Joseph Kimble**——应用于波兰法律语言的平实语言运动（plain-language movement）
- **本所执业实践**——在 B2B、IP 与 IT 领域客户日常服务中形成的范本

## 变更日志

| 版本 | 日期 | 更新内容 |
|---|---|---|
| **v0.2** | 2026 年 6 月 4 日 | 新增知识库文件：意思表示解释（最高法院 2024-2025）、u.ś.u.d.e./DSA/AI 服务规则。新增条款：IP 洁净性保证、AI 生成代码保证（warranty）、SLA、IT 退出计划、按月合规的 IT 竞业禁止、托管/SaaS/域名/AI 服务规则。条款库：19 → 20 个文件，知识库：11 → 13 个文件。 |
| **v0.1** | 2026 年 5 月 31 日 | 首次公开发布——黄金规则、条款库（19 个文件）、知识库（11 个文件）、8 个工作流。 |

## 下一步

我们拥有 0.x 版本，即第一次公开迭代，其中还有许多事项待完成——其中一些可能是你贡献力量的绝佳起点：

| 版本 | 状态 | 范围 |
|---|---|---|
| **0.x** | ✅ 已发布 | 波兰语 skill，B2B、IP 与 IT 合同（黄金规则、条款库、知识库、8 个工作流） |
| **1.0** | 🟡 计划 2026 年第三季度 | Anthropic 插件清单格式（兼容性验证），提交至 `claude-plugins-community` |
| **1.1** | 🟢 计划 2026 年第四季度 | 扩展条款库（金融业、B2B 雇佣、电子商务）；带公开 SIP 链接的判例库 |
| **2.0** | 🟢 长期 | 多语言框架，可适配其他大陆法系法域（德国、法国、意大利、西班牙）的模板 |

暂不涉及（有意为之，目前）：
- 刑法、行政法、税法、家事法——这些是其他执业领域
- 法院程序——skill 面向合同编辑起草与分析设计，而非诉讼支持
- skill 的测试套件——在计划清单上，但尚未启动

## 如何共同参与

任何形式的贡献对我们都很有价值：

- **发现了缺漏或错误？** 打开 issue。具体条款、更新的判例、错误的援引尤其宝贵。
- **有新工作流或整个层次的想法？** PR 欢迎。
- **只是想询问或讨论？** 可通过 GitHub Discussions 或直接联系。

每个 PR 在合并前我们都会人工检查，首先关注是否有保密数据。Pre-commit 钩子（`scripts/pre-commit-sanitizer.py`）可在你本地帮助发现这些问题。另外，如果风格遵循[黄金规则](./references/zlote-reguly.md)和[编辑风格](./references/style-redakcyjny.md)会更好；当然如果你提出完全不同的方案，我们也乐于讨论。

## 许可证

**Apache License 2.0**（见 [LICENSE](./LICENSE)）。

你可以自由使用，商业与非商业均可。在使用或修改的文件中保留许可证说明。

## 作者与维护

**Adam Piotrowski** —— 法律顾问（radca prawny），专长 LegalTech、AI 与 IT 合同法。

律师事务所 **Żurawska Piotrowski i Wspólnicy**（[ktzr.pl](https://ktzr.pl)）

GitHub：[@apiotrowski-afk](https://github.com/apiotrowski-afk)

## 职业声明

Skill **不构成法律意见**。它是辅助具备资格的法律从业者（法律顾问、律师或税务顾问）工作的操作性工具，视具体委托范围而定。

每项事务均须由具备资格的人员进行单独分析。KTZR 律师事务所及 Adam Piotrowski 对未经相应法律核实而使用本 skill 的任何后果不承担责任。
