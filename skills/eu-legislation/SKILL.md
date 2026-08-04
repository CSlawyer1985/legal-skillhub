---
name: "EU-Legislation"
description: "访问欧盟法律。从 EUR-Lex 检索和获取指令、条例、条约和欧洲法院判例法。"
allowed-tools: Bash(curl:*), WebFetch
metadata:
  author: "Malik Taiar"
  license: "agpl-3.0"
  version: "2026-04-15"
---

# 欧盟立法与判例法

直接访问欧盟法律。从 EUR-Lex 检索和获取指令、条例、决定、条约和欧洲法院判例法。

## 能力

| 行动                                    | 方法          |
|-------------------------------------------|-----------------|
| **检索立法/判例法**           | EUR-Lex 检索  |
| **文档信息、状态、修改**  | EUR-Lex /ALL/   |
| **程序历史**                     | EUR-Lex /HIS/   |
| **国内转化状态**         | EUR-Lex /NIM/   |
| **国内转化全文**      | 官方国家数据库（27 个成员国） |

---

## 方法 1：EUR-Lex 检索（语义检索）

**最适合：** 按概念、主题或关键词查找文档。

### URL 模式

```
https://eur-lex.europa.eu/search.html?scope=EURLEX&text=QUERY&lang=LANG&type=quick&locale=LOCALE
```

### 语言（全部 24 种欧盟官方语言）

| 语言    | 代码 | 本地名称        |
|-------------|------|--------------------|
| 保加利亚语   | bg   | Български          |
| 捷克语       | cs   | Čeština            |
| 丹麦语      | da   | Dansk              |
| 荷兰语       | nl   | Nederlands         |
| 英语     | en   | English            |
| 爱沙尼亚语    | et   | Eesti keel         |
| 芬兰语     | fi   | Suomi              |
| 法语      | fr   | Français           |
| 德语      | de   | Deutsch            |
| 希腊语       | el   | Ελληνικά           |
| 克罗地亚语    | hr   | Hrvatski           |
| 匈牙利语   | hu   | Magyar             |
| 爱尔兰语       | ga   | Gaeilge            |
| 意大利语     | it   | Italiano           |
| 拉脱维亚语     | lv   | Latviešu valoda    |
| 立陶宛语  | lt   | Lietuvių kalba     |
| 马耳他语     | mt   | Malti              |
| 波兰语      | pl   | Polski             |
| 葡萄牙语  | pt   | Português          |
| 罗马尼亚语    | ro   | Română             |
| 斯洛伐克语      | sk   | Slovenčina         |
| 斯洛文尼亚语   | sl   | Slovenščina        |
| 西班牙语     | es   | Español            |
| 瑞典语     | sv   | Svenska            |

`lang=` 和 `locale=` 参数均使用代码。

### 文档类型（表单）

阅读检索结果时，从“Form”字段识别文档类型：

| 表单                              | 类型     | 描述                    |
|-----------------------------------|----------|--------------------------------|
| 判决（Judgment）                          | JUDG     | 欧洲法院/普通法院判决   |
| 总顾问意见（Opinion of the Advocate General）   | OPIN_AG  | AG 结论                 |
| 指令（Directive）                         | DIR      | 欧盟指令                   |
| 条例（Regulation）                        | REG      | 欧盟条例                  |
| 决定（Decision）                          | DEC      | 欧盟决定                    |
| 条约（Treaty）                            | TREATY   | 欧盟条约                      |
| 提案（Proposal）                          | PROP     | 委员会提案            |

**注：** 优先使用**不含** FM_CODED 筛选的宽泛检索以捕获更多结果。改为通过阅读结果中的 Form 字段筛选。

### 示例

```
# 宽泛检索（推荐——捕获所有文档类型）
https://eur-lex.europa.eu/search.html?scope=EURLEX&text=cookies+consent&lang=en&type=quick&locale=en

# 法语检索
https://eur-lex.europa.eu/search.html?scope=EURLEX&text=protection+donnees&lang=fr&type=quick&locale=fr

# 检索 CSRD
https://eur-lex.europa.eu/search.html?scope=EURLEX&text=CSRD&lang=en&type=quick&locale=en
```

### 分页

- 第 1 页：无 `&page` 参数
- 第 2 页起：添加 `&page=2`、`&page=3` 等

---

## 方法 2：EUR-Lex 文档页面（高级）

### URL 模式

将 `{CELEX}` 替换为 CELEX ID（如 `32016R0679`）。

| 页面            | URL 模式                    | 内容                                    |
|-----------------|--------------------------------|--------------------------------------------|
| **全文**   | `/TXT/?uri=CELEX:{CELEX}`      | 文档文本                              |
| **全部信息**    | `/ALL/?uri=CELEX:{CELEX}`      | 相关文档、修改、附件       |
| **程序**   | `/HIS/?uri=CELEX:{CELEX}`      | 立法程序历史              |
| **转化** | `/NIM/?uri=CELEX:{CELEX}`      | 国内实施情况（指令）       |

### 基础 URL

```
https://eur-lex.europa.eu/legal-content/{LANG}/{PAGE}/?uri=CELEX:{CELEX}
```

### 示例

**GDPR——全部信息：**
```
https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32016R0679
```

**吹哨人指令——国内转化：**
```
https://eur-lex.europa.eu/legal-content/EN/NIM/?uri=CELEX:32019L1937
```

**CSRD——程序历史：**
```
https://eur-lex.europa.eu/legal-content/EN/HIS/?uri=CELEX:32022L2464
```

---

## 你可以找到什么

### /ALL/ 页面（文档信息）

- **法律状态**：现行有效、已修改、已废止
- **合并版日期**
- **ELI**：欧洲立法标识符
- **修改**：哪些法律文件修改了本法
- **被谁修改**：附日期的修改文件列表
- **被谁更正**：勘误
- **相关文档**：附件、提案、意见

### /NIM/ 页面（国内实施）

- **各成员国的转化状态**
- 实施该指令的**国内措施**
- **国内立法链接**
- **转化期限**

> **重要**：EUR-Lex /NIM/ 指向国内文本的链接常显示“Texte non disponible”（文本不可用）。此时，使用**官方国家法律数据库**（见下文）获取实际文本。

### /HIS/ 页面（程序）

- **立法程序**（普通、特别）
- **委员会提案**
- **议会审议**
- **理事会立场**
- **最终通过日期**

---

## 交叉引用核验

欧盟法律包含大量交叉引用。**始终核验被引文本**以提供准确回答。

### 引用类型

| 引用类型                      | 示例                          | 如何核验                                                                      |
|-------------------------------------|----------------------------------|------------------------------------------------------------------------------------|
| 内部条款                    | “Article 21”（第 21 条）                     | 重读全文                                                              |
| 外部法律文件                        | “Regulation (EU) 2016/679”（欧盟条例）       | GoodLegal API 或 EUR-Lex /TXT/                                                     |
| 附件                               | “Annex I, Part B”（附件一 B 部分）                | EUR-Lex /ALL/ 页面                                                                 |
| 实施性文件（《欧洲联盟运行条约》第 291 条）    | “Commission Implementing Regulation”（委员会实施条例） | EUR-Lex /ALL/ →“Internal procedures based on this legislative basic act”（基于此项立法基础文件的内部程序）       |
| 授权性文件（《欧洲联盟运行条约》第 290 条）       | “Commission Delegated Regulation”（委员会授权条例） | EUR-Lex /ALL/ →“Internal procedures based on this legislative basic act”       |
| 欧洲法院判例法                       | “Case C-xxx/xx”（案件 C-xxx/xx）                  | EUR-Lex /ALL/ →“Affected by case”（受案件影响）                                                 |

### 核验工作流

```
阅读欧盟文本
    │
    ├─► 发现“Article X”（第 X 条）引用？
    │       └─► WebFetch 同一文档，提取第 X 条
    │
    ├─► 发现“Directive/Regulation XXXX/XXX”（指令/条例）引用？
    │       └─► 用 CELEX ID 调 GoodLegal API
    │           或 WebFetch EUR-Lex /TXT/ 页面
    │
    ├─► 发现“Annex”（附件）引用？
    │       └─► WebFetch EUR-Lex /ALL/ 页面
    │           查找“Annexes”（附件）部分
    │
    └─► 需要相关/实施性文件？
            └─► WebFetch EUR-Lex /ALL/ 页面
                查找：
                -“Implemented by”（由……实施）
                -“Delegated acts”（授权性文件）
                -“Related documents”（相关文档）
                -“Based on”（基于……）
```

### 用 /ALL/ 查找相关文档

/ALL/ 页面展示完整的文档生态：

```
https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:{CELEX}
```

**要查找的内容：**

| EUR-Lex 标签                                              | 包含                                                          |
|-----------------------------------------------------------|-------------------------------------------------------------------|
| **法律基础**                                            | 条约（第 290、291 条）、上位立法                |
| **基于此项立法基础文件的内部程序** | 实施性文件（《欧洲联盟运行条约》第 291 条）和授权性文件（第 290 条） |
| **被谁修改**                                            | 附日期和受影响分项的修改文件                |
| **修改谁**                                               | 本文档修改的法律文件                                    |
| **被谁更正**                                           | 勘误（按语言的更正）                        |
| **后续相关文书**                         | 后续立法、相关文件                               |
| **受案件影响**                                       | 解释此法律文件的欧洲法院判决                              |
| **合并文本**                                      | 含全部修改的合并版链接                  |

**注：** 实施性文件（统一适用条件）和授权性文件（补充/修改非必要要素）常合并归入“Internal procedures”（内部程序）之下。

### 示例：回答法律问题

```
用户问：“指令 20XX/XXX 下的处罚是什么？”

步骤 1：获取全文
        → GoodLegal API："320XXLXXXX"

步骤 2：查找处罚条款（如第 30 条）
        → WebFetch EUR-Lex /TXT/ 页面，提取第 30 条
        → 找到：“Member States shall lay down penalties...”（成员国应规定处罚……）
        → 引用第 5 条（义务）和第 10 条（报告）

步骤 3：核验内部引用
        → WebFetch 同一页面，提取第 5 条和第 10 条
        → 第 5 条：主要合规义务
        → 第 10 条：通知要求

步骤 4：检查外部引用
        → 第 30 条引用条例 (EU) 20YY/YYY
        → GoodLegal API："320YYRYYYY"
        → 提取相关条款

步骤 5：检查 /ALL/ 中的实施性文件
        → WebFetch EUR-Lex /ALL/?uri=CELEX:320XXLXXXX
        → 找到：委员会实施条例 20ZZ/ZZZ
        → 获取并审查实施细节
```

### 引用链记录

回答法律问题时，记录引用链：

```
**问题：** 指令 20XX/XXX 下的报告义务是什么？

**回答：**
- 第 10 条：72 小时内通知
- 第 11 条：内容要求（见附件二）

**已核验的内部引用：**
- 第 5 条 → 适用范围
- 附件二 → 通知模板

**已核验的外部引用：**
- 条例 20YY/YYY 第 15 条 → 定义
- 委员会实施条例 20ZZ/ZZZ → 技术标准

**来自 /ALL/ 页面的相关文件：**
- 3 项实施条例
- 1 项授权性文件
- 2 项修改文件
```

---

## 决策流程

```
用户请求
    │
    ├─► 需要全文？
    │       └─► GoodLegal API（CELEX ID 或引用）
    │
    ├─► 按概念检索？
    │       └─► 经 WebFetch 用 EUR-Lex 检索
    │           阅读 Form 字段识别文档类型
    │
    ├─► 法律状态 / 修改？
    │       └─► 经 WebFetch 用 EUR-Lex /ALL/ 页面
    │
    ├─► 转化状态？
    │       └─► 经 WebFetch 用 EUR-Lex /NIM/ 页面
    │
    └─► 立法程序？
            └─► 经 WebFetch 用 EUR-Lex /HIS/ 页面
```

---

## 并行检索策略

为全面研究，并行发起多个 WebFetch 调用：

```
# 同时检索第 1-5 页
第 1 页：.../search.html?scope=EURLEX&text=QUERY&lang=en&type=quick&locale=en
第 2 页：.../search.html?scope=EURLEX&text=QUERY&lang=en&type=quick&locale=en&page=2
第 3 页：.../search.html?scope=EURLEX&text=QUERY&lang=en&type=quick&locale=en&page=3
第 4 页：.../search.html?scope=EURLEX&text=QUERY&lang=en&type=quick&locale=en&page=4
第 5 页：.../search.html?scope=EURLEX&text=QUERY&lang=en&type=quick&locale=en&page=5
```

然后按用户需求依据 Form 字段（判决、指令、条例等）筛选结果。

---

## 常用引用

### 立法

| 名称          | CELEX ID    |
|---------------|-------------|
| GDPR          | 32016R0679  |
| AI 法案（AI Act）        | 32024R1689  |
| DSA           | 32022R2065  |
| DMA           | 32022R1925  |
| NIS2          | 32022L2555  |
| 吹哨人指令（Whistleblower） | 32019L1937  |
| ePrivacy      | 32002L0058  |
| CSRD          | 32022L2464  |

### 欧洲法院关键案件

| 名称              | 案件编号 | 主题                    |
|-------------------|-------------|--------------------------|
| Costa v ENEL      | C-6/64      | 优先效力                  |
| Google Spain      | C-131/12    | 被遗忘权    |
| Schrems II        | C-311/18    | 数据传输           |
| Planet49          | C-673/17    | Cookie 同意           |

---

## 输出格式

### 立法
```
**指令 (EU) 2019/1937——吹哨人保护**
状态：现行有效（合并版：25/07/2024）
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L1937

修改：6 项修改文件
转化：27/27 个成员国
```

### 判例法
```
**案件 C-311/18——Schrems II**
日期：16/07/2020
主题：数据传输、隐私盾无效
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62018CJ0311
```

---

## 错误处理

### 无结果
- 尝试不同检索词
- 同时尝试英语和用户语言
- 用 EUR-Lex 检索作为回退
- 检查 CELEX ID 格式

### EUR-Lex 国内文本不可用
EUR-Lex /NIM/ 链接显示“Texte non disponible”或“Text not available”时，遵循下文的**国内转化文本获取**工作流。

---

## 方法 3：国内转化文本

### 问题

EUR-Lex /NIM/ 页面列出国内转化措施，但**实际文本的链接往往失效**（“Texte non disponible”/“Text not available”）。/NIM/ 页面提供：
- 国内措施名称（如“Decreto Legislativo 10 marzo 2023, n. 24”）
- 官方公报引用（如“Gazzetta Ufficiale n. 63 del 15 marzo 2023”）
- 转化期限

### 工作流

```
步骤 1：EUR-Lex /NIM/ 页面
        │
        └─► WebFetch https://eur-lex.europa.eu/legal-content/EN/NIM/?uri=CELEX:{CELEX}
            提取：措施名称、官方公报引用、日期
        │
        ▼
步骤 2：尝试 EUR-Lex 链接
        │
        └─► 点击/获取 /NIM/ 页面上提供的链接
            （如 https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=NIM:202302012）
        │
        ├─► 文本可用？→ 使用它 ✓
        │
        └─► “Texte non disponible”/“Text not available”？
                │
                ▼
步骤 3：官方国家数据库（见下表）
        │
        └─► 使用步骤 1 的措施引用
            在官方国家法律数据库中检索
            （如意大利 Normattiva、法国 Légifrance）
        │
        ├─► 找到文本？→ 使用它 ✓
        │
        └─► 未找到？
                │
                ▼
步骤 4：网络检索（最后手段）
        │
        └─► 使用以下信息检索官方来源：
            - 措施名称 + 编号 + 年份
            - 官方公报引用
            - 按官方政府域名筛选（.gov、.gv、.gouv 等）
```

### 官方国家法律数据库（全部 27 个欧盟成员国）

来源经 [N-Lex](https://n-lex.europa.eu/n-lex/index)、[欧洲电子司法门户](https://e-justice.europa.eu/6/EN/national_legislation)和[欧洲官方公报论坛](https://op.europa.eu/en/web/forum)核验。

| 国家 | 代码 | 官方数据库 | URL |
|---------|------|-------------------|-----|
| 奥地利 | AT | RIS（法律信息系统） | https://www.ris.bka.gv.at |
| 比利时 | BE | 比利时国家公报（Belgisch Staatsblad / Moniteur Belge） | https://www.ejustice.just.fgov.be |
| 保加利亚 | BG | 国家公报（Държавен вестник） | https://dv.parliament.bg |
| 克罗地亚 | HR | Narodne Novine | https://narodne-novine.nn.hr |
| 塞浦路斯 | CY | CyLaw + 官方公报 | http://www.cylaw.org |
| 捷克 | CZ | 法律汇编（Sbírka zákonů）/ Zákony pro lidi | https://www.zakonyprolidi.cz |
| 丹麦 | DK | Retsinformation | https://www.retsinformation.dk |
| 爱沙尼亚 | EE | Riigi Teataja | https://www.riigiteataja.ee |
| 芬兰 | FI | Finlex | https://www.finlex.fi |
| 法国 | FR | Légifrance | https://www.legifrance.gouv.fr |
| 德国 | DE | 互联网上的法律（Gesetze im Internet） | https://www.gesetze-im-internet.de |
| 希腊 | EL | 政府公报（Εφημερίδα της Κυβερνήσεως，ΦΕΚ） | https://www.et.gr |
| 匈牙利 | HU | 国家法规库（Nemzeti Jogszabálytár） | https://njt.hu |
| 爱尔兰 | IE | 爱尔兰成文法汇编（Irish Statute Book） | https://www.irishstatutebook.ie |
| 意大利 | IT | Normattiva / 官方公报（Gazzetta Ufficiale） | https://www.normattiva.it |
| 拉脱维亚 | LV | Likumi.lv | https://likumi.lv |
| 立陶宛 | LT | e-TAR（法律文件登记处） | https://www.e-tar.lt |
| 卢森堡 | LU | Legilux | https://legilux.public.lu |
| 马耳他 | MT | 马耳他法律（Laws of Malta） | https://legislation.mt |
| 荷兰 | NL | Wetten.overheid.nl | https://wetten.overheid.nl |
| 波兰 | PL | ISAP（众议院） | https://isap.sejm.gov.pl |
| 葡萄牙 | PT | DRE（共和国日报） | https://dre.pt |
| 罗马尼亚 | RO | Legislatie.just.ro | https://legislatie.just.ro |
| 斯洛伐克 | SK | Slov-Lex | https://www.slov-lex.sk |
| 斯洛文尼亚 | SI | PISRS | http://www.pisrs.si |
| 西班牙 | ES | BOE（国家官方公报） | https://www.boe.es |
| 瑞典 | SE | Lagrummet / 瑞典法令汇编 | https://lagrummet.se |

### 国别 URL 模式

#### 意大利（Normattiva）
```
# 按 URN（首选）
https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:YYYY-MM-DD;NUM

# 示例：D.Lgs. 24/2023（吹哨人）
https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2023-03-10;24

# 按官方公报（Gazzetta Ufficiale）
https://www.gazzettaufficiale.it/eli/id/YYYY/MM/DD/XXXXXXXX/sg
```

#### 法国（Légifrance）
```
# 按 JORF 文本编号
https://www.legifrance.gouv.fr/jorf/id/JORFTEXT{NUMBER}

# 按法律编号（检索）
https://www.legifrance.gouv.fr/search/all?tab_selection=all&searchField=ALL&query=loi+{YEAR}-{NUMBER}

# 示例：Loi Waserman 2022-401
https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000045388745
```

#### 德国（互联网上的法律）
```
# 按法律缩写
https://www.gesetze-im-internet.de/{abbrev}/

# 联邦法律公报（BGBl）
https://www.bgbl.de/xaver/bgbl/start.xav
```

#### 西班牙（BOE）
```
# 按 BOE 引用
https://www.boe.es/buscar/doc.php?id=BOE-A-YYYY-NNNNN

# 按法律引用
https://www.boe.es/buscar/act.php?id=BOE-A-YYYY-NNNNN
```

#### 荷兰（Overheid.nl）
```
# 按 BWBR 编号
https://wetten.overheid.nl/BWBR{NUMBER}

# 按国家公报（Staatsblad）引用
https://zoek.officielebekendmakingen.nl/stb-{YEAR}-{NUMBER}
```

#### 波兰（ISAP）
```
# 按 Dz.U. 引用
https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU{YEAR}{NUMBER}
```

### 示例：获取意大利转化文本

```
用户问：“获取吹哨人指令的意大利转化文本”

步骤 1：查看 EUR-Lex /NIM/
        → WebFetch https://eur-lex.europa.eu/legal-content/EN/NIM/?uri=CELEX:32019L1937
        → 找到：“Decreto Legislativo 10 marzo 2023, n. 24”
                 “Gazzetta Ufficiale n. 63 del 15 marzo 2023”

步骤 2：尝试 EUR-Lex 链接
        → WebFetch 提供的链接
        → 结果：“Texte non disponible”

步骤 3：前往 Normattiva（意大利官方数据库）
        → WebFetch https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2023-03-10;24
        → 成功：获取 D.Lgs. 24/2023 全文 ✓

若步骤 3 失败：
步骤 4：网络检索（最后手段）
        → WebSearch "D.Lgs. 24/2023 whistleblowing site:normattiva.it OR site:gazzettaufficiale.it"
```

### 监管机构网站

对**实施指南、解释性指引和常见问题**，还应查看负责该指令的国家监管机构：

| 指令 | 主题 | 主要国家机构 |
|-----------|-------|--------------------------|
| 2019/1937（吹哨人） | 反腐败 | IT：[ANAC](https://www.anticorruzione.it)，FR：[Défenseur des droits](https://www.defenseurdesdroits.fr)，DE：[BfJ](https://www.bundesjustizamt.de) |
| 2016/679（GDPR） | 数据保护 | IT：[Garante Privacy](https://www.garanteprivacy.it)，FR：[CNIL](https://www.cnil.fr)，DE：[BfDI](https://www.bfdi.bund.de) |
| 2022/2555（NIS2） | 网络安全 | IT：[ACN](https://www.acn.gov.it)，FR：[ANSSI](https://www.ssi.gouv.fr)，DE：[BSI](https://www.bsi.bund.de) |

---

## CELEX 格式参考

### 立法：`3{YEAR}{TYPE}{NUMBER}`

| 类型       | 代码 | 示例     |
|------------|------|-------------|
| 指令  | L    | 32019L1937  |
| 条例 | R    | 32016R0679  |
| 决定   | D    | 32021D0914  |

### 判例法：`6{YEAR}{COURT}{NUMBER}`

| 法院            | 代码 | 示例     |
|------------------|------|-------------|
| 欧洲法院 | CJ   | 62018CJ0311 |
| 普通法院    | TJ   | 62022TJ0354 |
| 总顾问意见       | CC   | 62017CC0673 |
