# 引用格式——ECCC

ECCC 引用精确、层级化，在结构上不同于国际刑事法院（ICC）的引用。本参考将相关惯例编码化，以便可以机械地对照检查输出。

## 两个组成部分

对任何案件特定文件，必须出现两项识别信息：

1. **案件档案编号**——文件登记所在的案卷。
2. **文件编号**——该案卷内特定提交文件的字母数字标识符。

两者均为必要。只给出标题和日期、但不给出任一标识符的引用是不完整的。

## 案件档案编号的构成

格式：

```
[案件编号]/[初始提交日期，日-月-年]/ECCC/[分庭或办公室]
```

示例：

- `001/18-07-2007/ECCC/TC` —— 001 号案件，2007 年 7 月 18 日初始提交，审判分庭
- `002/19-09-2007/ECCC/TC` —— 002 号案件，2007 年 9 月 19 日初始提交，审判分庭
- `002/19-09-2007/ECCC/SCC` —— 同一案卷在最高法庭分庭
- `002/19-09-2007-ECCC/SCC` —— 偶见标点变体；两种形式指同一案卷
- `003/07-09-2009/ECCC/OCIJ` —— 003 号案件，共同调查法官办公室
- `004/07-09-2009/ECCC/OCIJ` —— 004 号案件，与 OCIJ 相同的初始提交日期（003 和 004 号案件共用初始提交日期，因为它们源自第二次初始提交）

分庭/办公室后缀表明文件登记时由哪个机构持有案卷。同一案件随进展在各办公室之间流转（OCIJ → TC → SCC）；案件档案编号后缀反映当前受理该案的机构。

## 文件编号的构成

字母前缀编码程序阶段：

| 前缀 | 阶段 | 示例 |
|---|---|---|
| **A** | 共同检察官提交文件（初始提交、补充提交） | `A1`、`A2` |
| **B** | 早期案件管理文件 | `B1`、`B2` |
| **C** | OCIJ 调查阶段提交文件和命令 | `C1`、`C20`、`C160/4` |
| **D** | OCIJ 提交文件、决定和命令（包括结案令） | `D99`（001 号案件结案令）、`D427`（002 号案件结案令）、`D266`（003 号案件驳回令）、`D267`（003 号案件结案令/起诉书）、`D381`（004 号案件驳回令）、`D382`（004 号案件结案令/起诉书）、`D359`（004/02 号案件驳回令）、`D360`（004/02 号案件结案令）、`D308/3`（004/01 号案件驳回令——Im Chaem）。D 系列不限于结案令：涵盖调查阶段 OCIJ 的所有提交文件和决定（如 `D48`、`D49`、`D181` 是 003 号案件 OCIJ 关于属人管辖权的决定）。 |
| **E** | 审判分庭提交文件、决定和判决 | `E1`（审判分庭初始提交文件）、`E188`（001 号案件审判判决，2010 年 7 月 26 日）、`E141`、`E163/5`、`E284/4/8`、`E313`（002/01 号案件审判判决，2014 年 8 月 7 日）、`E465`（002/02 号案件审判判决，2018 年 11 月 16 日） |
| **F** | 最高法庭分庭提交文件、决定和判决 | `F28`（001 号案件上诉判决，2012 年 2 月 3 日）、`F36`（002/01 号案件上诉判决，2016 年 11 月 23 日）、`F76`（002/02 号案件上诉判决，2022 年 12 月 23 日） |

**E3 子系列——证据中的证物。** 在审判分庭阶段，`E3` 文件编号指主证物清单；个别证物引用为 `E3/[编号]`（如 `E3/4392`）。当判决引用 `E3/4392` 时，这是已被采纳为证据的证物（通常是证人陈述、调查中查封的文件、专家报告或照片），而非分庭的实质性提交文件。须与构成审判分庭决定、命令和提交文件的其他 `E[编号]` 提交文件区分。

子编号使用斜杠。`E163/5/1/13` 是审判分庭提交文件 E163 内四个嵌套层级的子文件。每个斜杠都是附于其左侧文件上的子文件。

文件版本后缀：
- 无后缀——档案版本（底层提交文件为机密时，通常是公开删节版）
- `-Public` 或 `-Redacted`——明确的公开版本
- `-Confidential` 或 `-Conf`——机密版本，限制分发
- `-Strictly Confidential`——分发限制最严格的类别
- `-EN`、`-FR`、`-KH`——语言后缀（英语/法语/高棉语）

引用时，如有公开删节版，优先使用。如果引用依赖公开版本中没有的机密内容，输出必须说明这一点。

## 分庭与办公室——缩写

| 缩写 | 机构 |
|---|---|
| **OCP** | 共同检察官办公室 |
| **OCIJ** | 共同调查法官办公室 |
| **PTC** | 预审分庭 |
| **TC** | 审判分庭 |
| **SCC** | 最高法庭分庭 |
| **DSS** | 辩护支持科 |
| **VSS** | 被害人支持科 |
| **OA** | 行政办公室 |

## 被告姓名惯例

ECCC 使用柬埔寨姓名顺序：**姓氏大写，随后是名字**。

| 正确 | 错误 |
|---|---|
| KAING Guek Eav alias Duch | Duch Kaing |
| NUON Chea | Chea Nuon |
| KHIEU Samphan | Samphan Khieu |
| IENG Sary | Sary Ieng |
| IENG Thirith | Thirith Ieng |
| MEAS Muth | Muth Meas |
| IM Chaem | Chaem Im |
| AO An | An Ao |
| YIM Tith | Tith Yim |

在案件标题中，形式为 `Prosecutor v. [姓氏] [名字]`。别名以“alias”跟随：`Prosecutor v. KAING Guek Eav alias Duch`。

## 分案引用——002、002/01、002/02 号案件

002 号案件被审判分庭分拆为两个独立的审判部分。随意引用会产生歧义。

- **002 号案件**——原始案卷，用于分拆前的文件（结案令、起诉书、早期审判分庭提交文件）以及影响两个部分提交的文件。
- **002/01 号案件**——第一个审判部分。人口迁移期间（第一阶段和第二阶段）以及在 Toul Po Chrey 犯下的危害人类罪。判决 2014 年 8 月 7 日（E313）。上诉判决 2016 年 11 月 23 日（F36）。
- **002/02 号案件**——第二个审判部分。对占族人和越南人的灭绝种族罪、强迫婚姻、对佛教徒的待遇、内部清洗、四个工地和三个安全中心（包括 S-21）。审判判决 2018 年 11 月 16 日（E465）。上诉判决 2022 年 12 月 23 日（F76；上诉于 2022 年 9 月 22 日口头宣判，完整书面判决于 2022 年 12 月 23 日公布——引用 F76 时使用 2022 年 12 月 23 日日期）。

引用分拆前发布的文件时，使用“Case 002”。引用分拆后发布、仅涉及其一部分的文件时，视情况使用“Case 002/01”或“Case 002/02”。文件编号本身不随部分改变——002/02 号案件中的审判分庭提交文件仍使用与更广泛的 002 号案件相同的编号序列中的 E 前缀。

## 内部规则——修订纪律

ECCC 内部规则已修订十次。现行修订为修订 10（2022 年 10 月 27 日）。2010 年的决定适用了较早的修订；其解释的规则可能在编号、措辞或两者上都不同于名义标识相同的现行规则。

引用纪律：

- 始终说明所引用申请之日的现行修订：`Internal Rules (Rev. 9), Rule 23 bis(1)`
- 关于现行规则的命题，引用修订 10
- 关于审判分庭在 2014 年于修订 8 下所持立场的命题，引用修订 8

内部规则各修订及其日期清单见 `foundational-texts.md`。

## 基础文本——简称

- **《联合国-柬埔寨协定》** —— `UN-Cambodia Agreement, Article 9`（管辖权）；`Article 13`（被告权利）
- **《ECCC 法》（经修订）** —— `ECCC Law, Article 3 new`（柬埔寨刑法罪行）、`Article 4`（灭绝种族罪）、`Article 5`（危害人类罪）、`Article 6`（对 1949 年《日内瓦公约》的严重破坏）、`Article 7`（破坏文化财产）、`Article 29 new`（个人责任形式——注意“new”后缀表示 2004 年修订后重新编号的条文）
- **《内部规则》（修订 X）** —— `Internal Rules (Rev. 10), Rule 23 quater(1)`

《ECCC 法》某些条文上出现的“new”后缀表示该条文被 2004 年修订重新编号或替换。部分来源省略“new”；严谨形式包含它。

## 实操示例

问题：如何引用 002/02 号案件审判分庭在第 3445 段对针对占族人的灭绝种族罪要件的分析。

内容已核验的引用：

> *Prosecutor v. NUON Chea and KHIEU Samphan* (Case 002/02), Trial Chamber, "Trial Judgment", E465, 16 November 2018, para. 3445.

如仅核验存在性（文件存在于 E465、2018 年 11 月 16 日，但未检索段落文本）：

> *Prosecutor v. NUON Chea and KHIEU Samphan* (Case 002/02), Trial Chamber, "Trial Judgment", E465, 16 November 2018 (existence verified; paragraph content not retrieved in this session).

## 当引用无法完成时

如果核验后你无法识别文件编号，或无法确认日期或分庭，则该引用尚不构成引用。要么收窄主张，要么告知用户缺失什么并请其提供来源。

## 规范参考表——常被引用的权威文件

ECCC 自身的《ECCC 指南，第 2 卷：判例》公布了权威的“常被引用的权威文件及其缩写”表。以下条目摘自该表（法院发布，第一层级）。引用 ECCC 重要文件时，优先使用法院自身使用的缩写形式。

### 法律框架

| 长引用 | 简称 |
|---|---|
| Agreement between the UN and the Royal Government of Cambodia… (entered into force 29 April 2005, 2329 U.N.T.S. 117) | **UN-RGC Agreement** |
| Law on the Establishment of Extraordinary Chambers… (as amended 27 October 2004, NS/RKM/1004/006) | **ECCC Law** |
| Internal Rules (Rev. 10), as revised on 27 October 2022 | **Internal Rules** |

### 实务指示

| 长引用 | 简称 |
|---|---|
| Practice Direction ECCC/01/2007/Rev. 8 (7 March 2012) — Filing of Documents | **PD on the Filing of Documents** |
| Practice Direction 02/2007/Rev. 1 (27 October 2008) — Victim Participation | **PD on Victim Participation** |
| Practice Direction ECCC/03/2007/Rev. 1 (29 April 2008) — Protective Measures | **PD on Protective Measures** |

### 001 号案件——KAING Guek Eav alias Duch

| 文件 | 编号 | 日期 | 简称 |
|---|---|---|---|
| 起诉 Duch 的结案令 | **D99** | 2008 年 8 月 8 日 | Case 001, Closing Order |
| 对结案令上诉的决定 | **D99/3/42** | 2008 年 12 月 5 日 | Case 001, Decision on Closing Order Appeal |
| 判决 | **E188** | 2010 年 7 月 26 日 | Case 001, Judgment |
| 上诉判决 | **F28** | 2012 年 2 月 3 日 | Case 001, Appeal Judgment |

### 002 号案件——分拆前文件（Nuon Chea、Khieu Samphan、Ieng Sary、Ieng Thirith）

| 文件 | 编号 | 日期 | 简称 |
|---|---|---|---|
| 结案令 | **D427** | 2010 年 9 月 15 日 | Case 002, Closing Order |
| 对 Khieu Samphan 就结案令上诉的决定 | **D427/4/15** | 2011 年 1 月 21 日 | Case 002, Decision on Closing Order Appeal (Khieu Samphan) |
| 对 Nuon Chea 和 Ieng Thirith 就结案令上诉的决定 | **D427/2/15 & D427/3/15** | 2011 年 2 月 15 日 | Case 002, Decision on Closing Order Appeals (Nuon Chea and Ieng Thirith) |
| 对 Ieng Sary 就结案令上诉的决定 | **D427/1/30** | 2011 年 4 月 11 日 | Case 002, Decision on Closing Order Appeal (Ieng Sary) |

### 002/01 号案件（Nuon Chea、Khieu Samphan）

| 文件 | 编号 | 日期 | 简称 |
|---|---|---|---|
| 判决 | **E313** | 2014 年 8 月 7 日 | Case 002/01, Judgment |
| 上诉判决 | **F36** | 2016 年 11 月 23 日 | Case 002/01, Appeal Judgment |

### 002/02 号案件（Nuon Chea、Khieu Samphan）

| 文件 | 编号 | 日期 | 简称 |
|---|---|---|---|
| 判决 | **E465** | 2018 年 11 月 16 日 | Case 002/02, Judgment |
| 上诉判决 | **F76** | 2022 年 12 月 23 日 | Case 002/02, Appeal Judgment |

### 003 号案件——MEAS Muth

| 文件 | 编号 | 日期 | 简称 |
|---|---|---|---|
| 驳回案件令 | **D266** | 2018 年 11 月 28 日 | Case 003, Dismissal Order |
| 结案令（起诉书） | **D267** | 2018 年 11 月 28 日 | Case 003, Closing Order (Indictment) |
| 对结案令上诉的考量 | **D266/27 & D267/35** | 2021 年 4 月 7 日 | Case 003, Considerations on Closing Order Appeals |

### 004 号案件——YIM Tith

| 文件 | 编号 | 日期 | 简称 |
|---|---|---|---|
| 驳回案件令 | **D381** | 2019 年 6 月 28 日 | Case 004, Dismissal Order |
| 结案令（起诉书） | **D382** | 2019 年 6 月 28 日 | Case 004, Closing Order (Indictment) |
| 对结案令上诉的考量 | **D381/45 & D382/43** | 2021 年 9 月 17 日 | Case 004, Considerations on Closing Order Appeals |

### 004/01 号案件——IM Chaem

| 文件 | 编号 | 日期 | 简称 |
|---|---|---|---|
| 结案令（理由）——驳回 | **D308/3** | 2017 年 7 月 10 日 | Case 004/01, Dismissal Order |
| 对结案令上诉的考量 | **D308/3/1/20** | 2018 年 6 月 28 日 | Case 004/01, Considerations on Closing Order Appeal |

### 004/02 号案件——AO An

| 文件 | 编号 | 日期 | 简称 |
|---|---|---|---|
| 驳回案件令 | **D359** | 2018 年 8 月 16 日 | Case 004/02, Dismissal Order |
| 结案令（起诉书） | **D360** | 2018 年 8 月 16 日 | Case 004/02, Closing Order (Indictment) |
| 对结案令上诉的考量 | **D359/24 & D360/33** | 2019 年 12 月 19 日 | Case 004/02, Considerations on Closing Order Appeals |

**整个表格的来源**：ECCC，《柬埔寨法院特别法庭指南，第 2 卷：判例》，“常被引用的权威文件及其缩写”，见 `https://eccc.gov.kh/sites/default/files/Guide_Vol_2_Manuscript_EN_latest.pdf`。
