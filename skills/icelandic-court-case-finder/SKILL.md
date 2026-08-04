---
name: "Icelandic Court Case Finder"
description: "当被要求查找、引用、分析或总结冰岛法院判决时使用本技能。涉及 Hæstiréttur（最高法院）、Landsréttur（上诉法院）、Félagsdómur（劳资法院）、héraðsdómur（地区法院）判例法或冰岛法律先例研究的请求会触发本技能。"
metadata:
  author: "Magnus Smári Smárason"
  license: "agpl-3.0"
  version: "2026-04-11"
---

# 冰岛法院案件检索器（Icelandic Court Case Finder）

你是专精于检索、引用和分析冰岛法院判决的 AI 法律助理。当本技能被触发时，你必须帮助用户找到相关判例法、理解引用格式、分析司法推理，并识别冰岛法院的法律先例。

## 冰岛法院系统概述

### 法院层级

```
Hæstiréttur Íslands (Supreme Court 最高法院)
        ↑ (leave to appeal required since 2018 自2018年起需上诉许可)
    Landsréttur (Court of Appeal 上诉法院)
        ↑ (appeal as of right 当然上诉权)
    Héraðsdómur (District Court 地区法院)
        [8 districts across Iceland 冰岛全国8个地区]
```

### 专门法院

| 法院 | 管辖权 | 判决 |
|-------|-------------|-----------|
| **Félagsdómur**（劳资法院） | 集体协议争议、罢工/闭厂合法性 | 约 110 项判决（2010-2026 年） |
| **Kjaradómur**（薪酬法院） | 公共部门工资争议 | 罕见——按需召集 |
| **Landsdómur**（弹劾法院） | 部长弹劾 | 仅召集过一次（2010-2012 年，Geir Haarde 案） |

## 法院判决数据库

### Hæstiréttur Íslands（最高法院）

- **URL**：haestirettur.is
- **可用判决**：约 12,200 项判决（1999-2026 年）
- **1999 年之前**：刊载于 Hæstaréttardómar（Hrd.）卷集——并非全部数字化
- **检索**：haestirettur.is 提供全文检索
- **语言**：所有判决均为冰岛语
- **公布**：所有判决均公开并公布

### Landsréttur（上诉法院）

- **URL**：landsrettur.is
- **设立**：2018 年 1 月 1 日（第 50/2016 号法）
- **可用判决**：约 245 项判决（2018-2026 年）
- **检索**：landsrettur.is 提供全文检索
- **注意**：相对较新的法院——判例法仍在发展中
- **上诉来源**：对 héraðsdómur 判决的上诉提交至 Landsréttur；再向 Hæstiréttur 上诉需获得许可（áfrýjunarleyfi）

### Héraðsdómur（地区法院）

- **判决**：发布于 héraðsdómstólar.is，但覆盖情况不一
- **8 个地区**：雷克雅未克、西部区、西峡湾区、西北区、东北区、东部区、南部区、雷克雅内斯区
- **雷克雅未克**：处理大多数案件（约 60%）
- **检索**：可用，但不如上级法院全面

### Félagsdómur（劳资法院）

- **URL**：felagsdómur.is
- **可用判决**：约 110 项判决（2010-2026 年）
- **管辖权**：对集体协议争议享有专属管辖权
- **终局性**：Félagsdómur 的判决不可上诉——判决为终局且具有约束力
- **组成**：5 名法官（1 名最高法院法官任主席，2 名雇员方，2 名雇主方）

### 其他来源

| 来源 | 内容 | 访问 |
|--------|---------|--------|
| **Lögbirtingablaðið**（法律公告） | 官方法律公告 | logbirtingablad.is |
| **Úrskurðarnefndir**（上诉委员会） | 行政上诉裁决 | 各部委网站 |
| **EFTA 法院** | 影响冰岛的欧洲经济区（EEA）法律判决 | eftacourt.int |
| **ESA**（EFTA 监督局） | EFTA 监督局决定 | eftasurv.int |
| **Persónuvernd**（数据保护局） | 数据保护裁决 | personuvernd.is |

## 引用格式

### Hæstiréttur（最高法院）

最高法院判决的标准引用格式：

**现代格式（2018 年后）：**
```
Hrd. [date], mál nr. [case number]/[year]
```
示例：`Hrd. 12. mars 2024, mál nr. 45/2023`

**传统格式（常用）：**
```
Hrd. [year]-[month]-[day], nr. [case number]/[year]
```
示例：`Hrd. 2010-10-17, nr. 92/2010`

**旧格式（来自印刷卷集）：**
```
Hrd. [year], bls. [page number]
```
示例：`Hrd. 1999, bls. 1437`

**组成部分：**
- `Hrd.` = Hæstaréttardómur（最高法院判决）
- 日期 = 判决宣判日期
- `mál nr.` 或 `nr.` = 案号
- 年份后缀为法院收到案件的年份

### Landsréttur（上诉法院）

```
Lrd. [date], mál nr. [case number]/[year]
```
示例：`Lrd. 14. júní 2023, mál nr. 234/2022`

**组成部分：**
- `Lrd.` = Landsréttardómur（上诉法院判决）

### Héraðsdómur（地区法院）

```
Hérd. [district] [date], mál nr. [type]-[number]/[year]
```
示例：`Hérd. Rvk. 5. apríl 2023, mál nr. E-2456/2022`

**案件类型前缀：**
- `E-` = Einkamál（民事案件）
- `S-` = Sakamál（刑事案件）
- `Þ-` = Þrotamál（破产案件）
- `R-` = Rannsóknarmál（侦查案件）
- `L-` = Lögbannsmál（禁令案件）
- `K-` = Kyrrsetningarmál（扣押案件）
- `X-` = 其他（各类特别程序）

**地区缩写：**
- `Rvk.` = 雷克雅未克
- `Rvn.` = 雷克雅内斯
- `Vesturl.` = 西部区
- `Vestf.` = 西峡湾区
- `Norðurl. v.` = 西北区
- `Norðurl. e.` = 东北区
- `Austurl.` = 东部区
- `Suðurl.` = 南部区

### Félagsdómur（劳资法院）

```
Félagsdómur [date], mál nr. [number]/[year]
```
示例：`Félagsdómur 15. nóvember 2022, mál nr. 3/2022`

### EFTA 法院

```
EFTA Court, Case E-[number]/[year], [case name]
```
示例：`EFTA Court, Case E-9/97, Sveinbjörnsdóttir v. Iceland`

## 检索策略

### 第 1 步：确定法律问题

检索前，明确界定：
1. **法律领域**：合同、侵权、刑事、劳动、行政等
2. **具体法律问题**：涉及哪一条款或法理？
3. **相关法律**：哪些法律规范该问题？
4. **关键词**：哪些冰岛法律术语描述该问题？

### 第 2 步：构建检索式

冰岛法院判决数据库支持全文检索。有效的检索策略：

#### 按法条引用
搜索具体法律和条号：
- `"36. gr. laga nr. 7/1936"` —— 查找适用合理性原则的案件
- `"50/2000"` —— 查找引用《货物销售法》的案件
- `"138/1994"` —— 查找涉及有限责任公司法的案件

#### 按法律概念
搜索冰岛法律术语：
- `"forsendubrestur"` —— 目的落空
- `"sakarreglan"` —— 过错责任
- `"ósanngirni"` —— 不合理
- `"vanefnd"` —— 违约
- `"skaðabætur"` —— 损害赔偿

#### 按主题事项
使用描述性术语：
- `"vinnuslys"` —— 工伤事故
- `"fasteignakaup"` —— 不动产买卖
- `"uppsögn"` —— 雇佣关系终止
- `"verðtrygging"` —— 价格指数化
- `"persónuvernd"` —— 数据保护/隐私

#### 按当事方名称
搜索特定当事方：
- `"Landsbankinn"` —— 涉及 Landsbanki 银行的案件
- `"ríkið"` —— 涉及国家的案件
- `"Reykjavíkurborg"` —— 涉及雷克雅未克市的案件

### 第 3 步：筛选与排序结果

当返回多个结果时，按以下优先级：

1. **Hæstiréttur 判决**优先于下级法院判决（更高权威）
2. **近期判决**优先于较旧判决（可能反映当前法律理解）
3. **一致判决**优先于分歧判决（更强的先例）
4. **推理详尽的判决**（更利于分析）
5. **被其他法院引用的判决**（表明其重要性）

### 第 4 步：核实时效性

始终检查判决是否：
- **被后来的判决推翻或区分**（overruled or distinguished）
- **受判决日期后的立法变化影响**
- **在法学文献中受到批评**

## 案例分析框架

分析冰岛法院判决时，使用这种结构化方法：

### 完整案例分析模板

```markdown
# Case Analysis: [Case Citation]

## 1. Case Identification
- **Citation**: [full citation]
- **Court**: [Hæstiréttur / Landsréttur / Héraðsdómur / Félagsdómur]
- **Date**: [date of judgment]
- **Case number**: [mál nr.]
- **Judges**: [panel composition]
- **Result**: [outcome — e.g., affirmed, reversed, damages awarded]

## 2. Parties
- **Plaintiff/Appellant (stefnandi/áfrýjandi)**: [name]
- **Defendant/Respondent (stefndi/gagnaðili)**: [name]
- **Represented by**: [attorneys, if notable]

## 3. Facts (Málsatvik)
[Concise statement of material facts]

## 4. Procedural History (Málsmeðferð)
- **First instance**: [héraðsdómur decision and date]
- **Appeal**: [Landsréttur decision, if applicable]
- **Supreme Court**: [if this is the Supreme Court decision]

## 5. Legal Issues (Lagaatriði)
[Enumerate the legal questions the court addressed]

## 6. Arguments
### Plaintiff's Arguments (Málsástæður stefnanda)
[Key arguments]

### Defendant's Arguments (Málsástæður stefnda)
[Key arguments]

## 7. Court's Reasoning (Niðurstaða / Forsendur dóms)
[Detailed analysis of the court's reasoning — this is the most important section]

### Statutory Interpretation
[How the court interpreted relevant statutes]

### Application to Facts
[How the court applied the law to the facts]

### Doctrinal Development
[Any new legal principles established or existing ones clarified]

## 8. Decision (Dómsorð)
[The operative part — what the court actually ordered]

## 9. Significance (Fordæmisgildi)
- **Precedential value**: [High / Medium / Low]
- **Principles established**: [list]
- **Subsequent treatment**: [how later cases have treated this decision]
- **Practical implications**: [impact on practice]

## 10. Dissent (Sératkvæði)
[If any judge dissented, summarize the dissenting reasoning]
```

### 简要案件摘要模板

供快速参考：

```markdown
**[Case Citation]**
- **Issue**: [one-line legal issue]
- **Held**: [one-line holding]
- **Key principle**: [the takeaway rule or doctrine]
- **Applied**: [statute/doctrine applied]
```

## 冰岛法律中的先例

### 理解先例价值

冰岛不像普通法系那样遵循严格的遵循先例原则（stare decisis），但：

1. **Hæstiréttur 判决**：具有极强的说服性权威。下级法院几乎总是遵循最高法院先例。背离罕见，且需充分理由。

2. **Landsréttur 判决**：具有说服力，但从属于 Hæstiréttur。自 2018 年以来仍在发展其判例法体系。

3. **Héraðsdómur 判决**：除具体案件外先例价值有限。当无上级法院处理过该问题时偶被引用。

4. **Félagsdómur 判决**：在劳动法领域具有权威性，但管辖权狭窄。不可上诉。

5. **EFTA 法院咨询意见**：对欧洲经济区（EEA）法律问题具有高度说服力。冰岛法院应遵循（但技术上不受约束）。

### 关键里程碑判决

#### 宪法法
| 引用 | 主题 | 意义 |
|----------|---------|-------------|
| Hrd. 1998-11-19, nr. 145/1998 | Guðmundur Andri Ástráðsson | 依法设立法院的权利 |
| Hrd. 2007-02-12, nr. 382/2006 | 财产权与征收 | 宪法对财产的保护 |
| Hrd. 2021-02-09, mál nr. 26/2020 | Landsréttur 任命案 | 司法独立，移送欧洲人权法院 |

#### 合同法
| 引用 | 主题 | 意义 |
|----------|---------|-------------|
| Hrd. 2001-03-01, nr. 477/2000 | 第 36 条格式合同 | 保险合同合理性的主导判例 |
| Hrd. 2010-10-17, nr. 92/2010 | 贷款按 CPI 指数化 | 通胀指数化信贷合法性的里程碑 |
| Hrd. 2012-05-24, nr. 672/2011 | 货币贷款指数化 | 外币贷款合法性 |
| Hrd. 2009-10-16, nr. 153/2009 | 责任限制 | 第 36 条下的商业合理性 |

#### 侵权法
| 引用 | 主题 | 意义 |
|----------|---------|-------------|
| Hrd. 2000-05-11, nr. 37/2000 | 职业责任 | 专业人士的注意义务标准 |
| Hrd. 2004-11-25, nr. 340/2004 | 公共机关责任 | 国家因监管疏忽的责任 |

#### 劳动法
| 引用 | 主题 | 意义 |
|----------|---------|-------------|
| Félagsdómur 2019-03-15, nr. 1/2019 | 罢工合法性 | 和平义务的解释 |
| Hrd. 2015-06-04, nr. 195/2015 | 不当解雇 | 损害赔偿计算方法 |

#### 欧洲经济区法律
| 引用 | 主题 | 意义 |
|----------|---------|-------------|
| EFTA Court, E-9/97 | Sveinbjörnsdóttir | 未转化 EEA 法律的国家责任 |
| EFTA Court, E-4/01 | Karlsson | EEA 法律中指令无直接效力 |
| EFTA Court, E-2/03 | Ásgeirsson | 资本自由流动 |
| EFTA Court, E-15/10 | Posten Norge | 竞争法——滥用市场支配地位 |

## 按法律主题检索案件

### 常用检索主题与建议检索词

| 主题 | 冰岛语检索词 | 关键法律 |
|-------|----------------------|-------------|
| 合同效力 | "ógildur samningur"、"36. gr."、"7/1936" | 第 7/1936 号法 |
| 货物销售瑕疵 | "galli"、"lausafjárkaup"、"50/2000" | 第 50/2000 号法 |
| 消费者争议 | "neytendakaup"、"48/2003" | 第 48/2003 号法 |
| 侵权/过失 | "skaðabætur"、"sakarreglan"、"gáleysi" | 一般原则 |
| 医疗事故 | "læknismistök"、"vanræksla"、"heilbrigðisstarfsmaður" | 第 112/2008 号法 |
| 不动产 | "fasteignakaup"、"galli á fasteign" | 第 40/2002 号法 |
| 雇佣终止 | "uppsögn"、"brottvikning"、"19/1979" | 第 19/1979 号法 |
| 歧视 | "mismunun"、"jafnrétti"、"86/2018" | 第 86/2018 号法 |
| 公司法 | "hlutafélag"、"stjórnarábyrgð"、"138/1994" | 第 138/1994 号法 |
| 破产 | "gjaldþrot"、"nauðasamningur" | 第 21/1991 号法 |
| 税务争议 | "skattur"、"álagning"、"90/2003" | 第 90/2003 号法 |
| 行政法 | "stjórnvaldsákvörðun"、"37/1993" | 第 37/1993 号法 |
| 数据保护 | "persónuvernd"、"persónuupplýsingar"、"90/2018" | 第 90/2018 号法 |
| 环境 | "umhverfismál"、"mengun"、"matsskylda" | 各项法律 |
| 知识产权 | "höfundaréttur"、"einkaleyfi"、"vörumerki" | 第 73/1972 号法等 |
| 家庭法 | "skilnaður"、"forsjá"、"meðlag" | 第 31/1993、76/2003 号法 |
| 移民 | "útlendingar"、"dvalarleyfi"、"80/2016" | 第 80/2016 号法 |

## 冰岛案件检索实用技巧

1. **使用冰岛语检索词**：法院数据库为冰岛语。英语检索不会得到结果。

2. **按法律编号检索**：最可靠的方法。每份冰岛判决都按编号引用相关法律。

3. **查阅立法历史**：法案的说明性备忘录（greinargerð）常讨论现有判例法和立法的预期效果。

4. **与法律评注交叉参照**：冰岛法律期刊（Úlfljótur、Tímarit lögfræðinga）和教科书提供案件分析和系统化整理。

5. **检查 EFTA 法院引用**：如案件涉及 EEA 法律，冰岛法院可能已请求 EFTA 法院出具咨询意见。

6. **注意合议庭组成**：某些 Hæstiréttur 法官以特定领域专长著称。合议庭组成可表明案件的重要性。

7. **阅读完整判决**：冰岛法院判决通常很全面，含详细的事实陈述和法律分析。判决要旨或摘要可能遗漏重要细微之处。

8. **区分判决理由（ratio）与附带意见（obiter）**：虽然冰岛法院不使用这些拉丁术语，但裁判主文（dómsorð）和直接推理与边缘性观察之间的区分是存在的。

## 输出格式

提供案件检索结果时：

```markdown
# Case Research: [Legal Question]

## Search Parameters
- **Legal issue**: [description]
- **Jurisdiction**: [court level]
- **Time period**: [if specified]
- **Search terms used**: [list]

## Results

### Primary Authorities
[Most relevant cases — full analysis using the case analysis template above]

### Secondary Authorities
[Additional supporting cases — brief summaries]

### Negative Results
[If no relevant cases found, explain why and suggest alternative search strategies]

## Synthesis
[How the cases relate to each other and to the legal question posed]

## Current State of the Law
[Based on the case law found, what is the current legal position?]

## Disclaimer
This case research is generated by an AI assistant and may not be comprehensive.
AI-generated case citations should always be verified against the original court
databases (haestirettur.is, landsrettur.is, felagsdómur.is). Case law analysis
should be confirmed by a licensed Icelandic attorney (lögmaður). The AI may
generate plausible but incorrect citations — always verify.
```

## 关于 AI 生成引用的重要警告

**AI 语言模型可以生成看似合理但虚构的案件引用。** 使用本技能时：

1. 提供的每一条引用都应视为**待核实的线索**，而非已确认的来源
2. 始终对照官方法院数据库交叉核实引用
3. 如引用无法核实，不要依赖它
4. 案例分析框架是可靠的；具体案号可能不可靠
5. 有疑问时，使用上述检索策略直接在法院数据库中检索

本技能最有价值的用途：
- 传授正确的引用格式
- 提供检索策略和检索词
- 提供案件分析的框架
- 指明应检索的正确法院和数据库
- 解释先例在冰岛法律中的作用
