# 第 0 层——解析与规范化

第 0 层是基础。其后每一层都依赖它。第 0 层不作任何判定；它产出规则各层赖以运行的解析记录。

## 输入

来自预警：被筛查名称、匹配名称、名单名称、名单版本（可选）、上游匹配分数（可选）、任何次级标识符、名单条目详情（名单条目的全文，包括别名、标识符、履历字段）。

## 输出

具有以下结构的解析记录：

```
screened_name_parse:
  script: Latin | Cyrillic | Arabic | Han | Hangul | Hebrew | Thai | Greek | Devanagari | mixed | other
  language_hint: detected source language (e.g., en, es, ar, fa, ru, zh, ko)
  naming_convention: Hispanic | Portuguese | Arabic | Russian | East_Asian | Indonesian_Burmese | Western_default | ambiguous
  components:
    anchor: [list of anchor strings]
    non_anchor: [list of non-anchor strings]
  parse_confidence: high | low

matched_name_parse:
  [same shape]

listed_party_type: individual | entity | vessel | aircraft | unknown
screened_party_type: provided | user_confirmed | inferred | unknown
listed_aliases_parsed: [list of {alias, parse} entries from the list entry]
identifiers_on_listed_entry: dict of identifier type to list of values (passport, national_id, tax_id, registration_number, dob, pob, nationality, address)
identifiers_on_screened_party: same shape
```

## 第 1 步：文字检测

检测每个名称的文字。筛选中大多数名称是拉丁文字，即使底层名称是阿拉伯语、波斯语、俄语、中文——因为筛查系统进行转写。观察原始字符。

如两个名称均为拉丁文字，但语言提示（见第 2 步）表明其中一个或两个是对非拉丁来源的转写，相应标注 `language_hint`，并将转写变体视为第 3 层考量。

如一个名称是原生文字而另一个是拉丁文字（如名单条目包含阿拉伯文字别名，而被筛查名称是拉丁转写），记录两者并使用语言感知匹配路径。

## 第 2 步：语言提示

对拉丁文字名称，使用语言标记推断可能的源语言：

- **西班牙语标记**：两个姓氏、以 "de la"、"del" 开头的姓氏、"García"、"Martínez"、"López"、"González"、常见名如 "José"、"María"
- **葡萄牙语/巴西标记**：姓氏 "da Silva"、"Santos"、"Oliveira"、"Pereira"；名如 "João"、"Ricardo"；葡萄牙语拼写模式（"ão"、"ç"）
- **阿拉伯语标记**：冠词 "Al-"、"El-"、"Bin"、"Ibn"、"Abu"、"Umm"；名字如 "Mohammed/Muhammad/Mohamed/Mohamad"、"Ahmed/Ahmad"、"Hassan"、"Khalid/Khaled"、"Yousef/Yusuf"
- **波斯语/伊朗标记**："Reza"、"Hossein"、"Mahdi"、"Mehdi"、以 "-zadeh"、"-pour"、"-nia"、"-i" 结尾的姓氏
- **俄语/斯拉夫标记**：以 "-ovich"、"-evich"、"-ovna"、"-evna" 结尾的父名；以 "-ov"、"-ev"、"-sky"、"-skaya" 结尾的姓氏
- **东亚标记**（中文）：单音节姓氏 "Wang"、"Li"、"Zhang"、"Chen"、"Liu"、"Yang"、"Huang"、"Wu"、"Zhao"
- **韩语标记**：姓氏 "Kim"、"Lee"、"Park"、"Choi"、"Jung"、"Kang"
- **越南语标记**：姓氏 "Nguyen"、"Tran"、"Le"、"Pham"、"Hoang"
- **印尼/马来标记**：单名常见；冠词 "bin"/"binti"；名字如 "Muhammad"、"Siti"

这些标记是启发式的。当一个名称有多个可能来源（如 "Ali"——阿拉伯语、波斯语、土耳其语、南亚），记录歧义而非选择其一。

## 第 3 步：命名惯例分类

使用 `naming-conventions.md` 将语言提示映射到命名惯例。如标记冲突或缺失，将惯例标为 `ambiguous` 并将 `parse_confidence` 设为 `low`。

## 第 4 步：结构解析

对每个名称，按惯例将组成部分分为锚点（承载身份）和非锚点（语境）。惯例参考文件定义每种惯例的规则。示例：

- **西班牙语，"Maria Gonzalez Lopez"** → 锚点：["Gonzalez"]（父系姓氏），非锚点：["Maria"、"Lopez"]（名、母系姓氏）。母系姓氏重要但为次要。
- **西班牙语，"Jose Andrea Coronado"** → 锚点：["Coronado"]，非锚点：["Jose"、"Andrea"]
- **阿拉伯语，"Abu Bakr Mohammad bin Abdullah al-Tikriti"** → 锚点：["Mohammad"、"Abdullah"]（本名 + 父系纳斯布），非锚点：["Abu Bakr"（库尼亚）、"al-Tikriti"（尼斯巴）]
- **俄语，"Vladimir Vladimirovich Petrov"** → 锚点：["Petrov"]，非锚点：["Vladimir"（名）、"Vladimirovich"（父名）]。注意：中间部分是父名，而非西方意义上的中间名。
- **东亚，"Wang Wei"** → 锚点：["Wang"]（姓氏，在前），非锚点：["Wei"]（名）
- **西方默认，"John Robert Smith"** → 锚点：["Smith"]，非锚点：["John"、"Robert"]

当名称只有一个词素（如印尼单名惯例），该单一词素即为锚点。解析置信度为 `low`，因为核验选项有限。

## 第 5 步：解析置信度

将 `parse_confidence` 设为：

- **`high`**：语言标记清晰、惯例无歧义、组成部分角色被确信地分配
- **`low`**：存在以下任一情形：惯例模糊；名称结构不符合推断的惯例；来源不明的单一词素；转写产生不符合任何标准模式的结构

`low` 解析置信度会在后续层禁用该名称对的结构不匹配假阳性规则（FP-2、FP-6）。理由：我们不会基于不信任的解析自动排除。

## 第 6 步：别名清点

从名单条目中提取每个别名（又名 a.k.a.、曾用名 f.k.a.、现用名 n.k.a.、低质量别名、强别名）。按与主名称相同的方式通过第 1-4 步解析每个别名。

这一点很重要，因为：
1. 实际匹配可能是针对别名，而非名单主名称。识别是哪一个。
2. 某些别名在表面上看起来像假阳性候选（丢弃或重排名称组成部分），但实际上代表了名单当事人为人所知的方式。如果名单当事人有记录在案的别名 "Jose Andrea"（无姓氏），则针对该当事人匹配 "Jose Andrea" *不*是 FP-2 情形——该别名是真实的。

## 第 7 步：标识符清点

清点每一侧的所有标识符：

- **出生日期**：完整（日/月/年）、部分（仅年份、年-月、年份范围）或缺失。注意多个 DOB（名单条目通常有多个）。
- **出生地**：城市 + 国家、仅国家或缺失。可能有多个 POB（当事人曾在多个地方居住）。记录 POB 时，同时按 `place-name-equivalences.md` 记录城市或国家的任何记录在案的替代名称——例如，名单 POB "Leningrad, USSR" 记录时附替代名 "St. Petersburg" 和继承国 "Russia"。这使第 2 层的 POB 比较对历史更名具有韧性。
- **国籍/公民身份**：列出全部，如标明主要国籍则注明。注意双重国籍。
- **国家身份证号码**：护照、国民身份证、税号、驾照。捕获签发机构和号码。
- **对实体**：注册号、注册国、注册地址、税号、LEI。
- **对船舶**：IMO 编号、MMSI、船旗国、曾用名、曾挂船旗。

标识符清点直接输入第 2 层。任何一侧缺失标识符意味着相应第 2 层规则无法触发——这是保守默认。

## 第 8 步：类型确定

`listed_party_type` 直接来自名单条目的类型字段。大多数主要名单显式标注此字段（SDN_TYPE = "Individual"、"Entity"、"Vessel"、"Aircraft"）。

`screened_party_type` 来源优先级：

1. **Provided（提供）**——在预警输入中给出。照用。置信度：高。
2. **User_confirmed（用户确认）**——交互模式下，如未提供则向用户询问一次。使用该回答。置信度：高。
3. **Inferred（推断）**——批处理模式下未提供时使用。使用结构线索（实体后缀 "LLC"、"Ltd"、"S.A."、"GmbH"、"OAO"；船舶线索 "M/V"、"M/T"、"S.S."）。无线索时默认 "individual" 但标注为 `inferred`。置信度：低。
4. **Unknown（未知）**——推断完全无信号时。

后续层的类型不匹配规则尊重此置信度。FP-1（类型不匹配）要求两侧均为高置信度类型——绝不在 `inferred` 类型上触发。

## 输出

按本文件顶部定义产出解析记录。该记录被其后每一层引用，并包含在最终审计输出中。
