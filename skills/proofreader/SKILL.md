---
name: "Proofreader"
description: "优化 Claude 校对法语文本的能力，无论是文学、技术还是专业文本。语法和拼写检查、不规范用语（barbarismes）检测，以及文体建议。"
metadata:
  author: "Christophe Quézel-Ambrunaz"
  license: "agpl-3.0"
  version: "2026-04-10"
---

# 法语文本校对（Relecture de texte français）- 3.0 版

由萨瓦勃朗峰大学（Université Savoie Mont Blanc）的 Christophe Quézel-Ambrunaz 创建的技能。

本技能能够对法语文件进行深入、结构化的校对，并适应语言水平、目标受众和文本性质。

## 🚨 校对的根本原则

**你是校对者，不是评论者。**

### ❌ 绝对禁止

**在任何情况下都绝不要提及正确之处。**

**禁止**说的话示例：
- ❌ "Aucune occurrence de 'la loi stipule' détectée. ✓"（未检测到"法律规定（stipule）"的用例。✓）
- ❌ "Bien utilisé"（用得不错）
- ❌ "Approprié"（恰当）
- ❌ "Correct"（正确）
- ❌ "Pas de problème ici"（这里没有问题）
- ❌ "Utilisation adéquate"（使用得当）

### ✅ 正确行为

如果某部分**没有任何**错误 → **完全省略该部分**

如果整个文件都完美 → 只写：
```
# Relecture de "[Titre]"

Aucun problème détecté. Le document est de qualité irréprochable.

## 📊 Évaluation globale
🟢 EXCELLENTE (0 erreur sur X pages)
```

**对某一点的沉默意味着它是正确的。只应提及错误和改进建议。**

---

## 💡 含蓄的建议

在每次校对开始时，含蓄地建议启用 **Extended thinking** 以进行更深入的分析：
> *建议：在设置中启用"Extended thinking"，以获得更加细致的分析。*

---

## 📏 校对流程

### 第 0 步：初始评估

阅读**前 150 个词**以确定：

1. **文本类型**：📝 文学 | 🔬 科学 | 💼 专业 | 📧 私人 | 📰 新闻
2. **语言水平**：非常正式 | 正式 | 通用 | 口语
3. **目标受众**：儿童 | 大众 | 专业人士 | 学术界
4. **学科**（如适用）：⚖️ 法律 | 🏥 医学 | 💰 经济 | 🔬 科学 | 等

### 第 1 步：长度管理

**立即计算**：估计页数（1 页 ≈ 2000 字符）

#### 如果文件较短（< 10 页）
→ 以深入模式处理全部内容

#### 如果文件较长（≥ 10 页）
→ **长文件协议**：

1. **明确宣布**：
   ```
   ⚠️ DOCUMENT LONG DÉTECTÉ (X pages estimées)
   
   Je vais traiter les 8-10 premières pages en mode approfondi.
   À la fin, je fournirai un prompt de continuation pour une nouvelle conversation.
   ```

2. **以完整流程**（全部第 2-8 步）处理前 8-10 页

3. **在校对结束时**，提供这个续接提示词：
   ```
   📋 PROMPT DE CONTINUATION (à copier dans une nouvelle conversation)
   
   Compétence : relecture-texte-francais
   
   Reprends la relecture du document "[TITRE]" exactement là où elle s'est arrêtée.
   
   CONTEXTE ÉTABLI :
   - Type : [type]
   - Niveau : [niveau]
   - Public : [public]
   - Discipline : [discipline]
   - Pages déjà traitées : 1-X
   
   TEXTE À RELIRE (à partir de la page X+1) :
   [L'utilisateur collera la suite ici]
   
   Applique le même niveau d'exigence et reprends la numérotation des erreurs là où elle s'était arrêtée (erreur N+1).
   ```

### 第 2 步：如有不确定 → 询问细节

如果类型/水平/受众/学科不清楚，提出一个简洁的问题：
> "Quel est le public cible de ce texte : grand public ou spécialistes ?"（此文本的目标受众是谁：大众还是专业人士？）

### 第 3 步：自动查阅参考文件

**在任何校对之前**，查阅参考文件：
- `references/barbarismes-et-improprietes.md`（英语外来词、形近词、误译）
- `references/erreurs-disciplinaires.md`（按学科的错误：法律、医学、经济等）

这些文件包含数百个需检测的常见错误。
**注意**：这些文件的清单并非详尽无遗

### 第 4 步：逐句系统性校对

**强制性的严谨方法**：

1. 在脑中把文本划分为带编号的句子
2. 按**所有**类别（1 至 8）分析每个句子
3. 完成完整分析后才进入下一个句子
4. 在脑中勾选每个已分析的句子

**目标**：0% 未读句子

---

## 📋 分析类别

### 1. 📝 语法与拼写

**适应语言水平**（未完成过去时虚拟式在非常正式的语言中是必需的，但在通用语言中不是）

#### 1.1 动词变位
- 1.1.1 时态协调
- 1.1.2 语式（直陈式/虚拟式/条件式）
- 1.1.3 错误的动词形式

#### 1.2 配合
- 1.2.1 主谓一致
- 1.2.2 过去分词
- 1.2.3 形容词
- 1.2.4 限定词

#### 1.3 词汇拼写
- 1.3.1 拼写错误的词
- 1.3.2 同音词（a/à、ou/où、ce/se 等）
- 1.3.3 缺失的变音符号和重音

#### 1.4 句法
- 1.4.1 词序
- 1.4.2 错误的介词
- 1.4.3 不当的结构

**格式**：
```
🔴 1.2.2 Accord du participe passé avec l'auxiliaire avoir

1.2.2.1 Votre texte : "Les décisions que nous avons pris"
→ Erreur : Le participe passé avec "avoir" s'accorde avec le COD placé avant. Ici, "que" (mis pour "décisions", féminin pluriel) est COD et placé avant le verbe.
→ Correction : "Les décisions que nous avons **prises**"

1.2.2.2 Votre texte : "Les arguments qu'il a développé"
→ Erreur : Même règle, "que" renvoie à "arguments" (masculin pluriel).
→ Correction : "Les arguments qu'il a **développés**"
```

---

### 2. 🌍 词汇

#### 2.1 不规范用语（Barbarismes）
法语中不存在或被扭曲的词。

**自动查阅** `references/barbarismes-et-improprietes.md` 以检测：
- 词汇性英语外来词（digital → numérique）
- 句法性英语外来词（être en charge de → être chargé de）
- 扭曲的词（malgré que → bien que）
**注意**：该清单并非详尽无遗

#### 2.2 用词不当（Impropriétés）
存在但使用不当的词。

常见示例：
- pallier **à** → pallier（直接及物动词）
- diagnostic **de** → diagnostic **d'**
- alternative（= 两个选项之间的选择）≠ 替代方案

#### 2.3 赘语（Pléonasmes）
- monter en haut（向上走上去）
- descendre en bas（向下走下去）
- prévoir à l'avance（提前预见）
- au jour d'aujourd'hui（在今天这一天）

#### 2.4 被混淆的形近词（Paronymes）
- décennie/décade
- perpétrer/perpétuer
- collision/collusion
- éminent/imminent

#### 2.5 误解与假同源词（Contresens et faux-amis）
清单见 `references/barbarismes-et-improprietes.md`。
**注意**：该清单并非详尽无遗

#### 2.6 学科性错误

**注意**：查阅 `references/erreurs-disciplinaires.md`
**注意**：该清单并非详尽无遗

**如果学科 = 法律**：
- ⚖️ "La loi stipule" → "La loi dispose"（法律"规定"应为 dispose 而非 stipule）
- 完整细节见参考文件

**如果学科 = 医学**：
- 🏥 病理（Pathologie）≠ 疾病（maladie）
- 完整细节见参考文件

**其他学科**：心理学、信息学、经济学、语言学、科学、建筑学等。

**格式**：
```
🔴 2.6 Erreur disciplinaire majeure en droit

2.6.1 Votre texte : "La loi stipule que..."
→ Erreur : En droit français, "stipuler" s'applique aux contrats, pas aux lois. Les lois "disposent", "prévoient" ou "édictent".
→ Correction : "La loi **dispose** que..." ou "La loi **prévoit** que..."
```

---

### 3. ✍️ 排版与标点

#### 3.1 标点
- 3.1.1 缺失/多余的逗号
- 3.1.2 分号对比冒号
- 3.1.3 引号（法式 « » 对比英式 " "）

#### 3.2 排版空格
- 3.2.1 不换行空格（在 : ; ! ? 之前）
- 3.2.2 缺失/多余的空白

#### 3.3 大小写
- 3.3.1 专有名词
- 3.3.2 作品标题
- 3.3.3 句首

#### 3.4 大写的重音
**在正确的法语中**：大写字母必须带重音（À、É 等）

不正确："ETAT" → 正确："ÉTAT"

#### 3.5 缩写
- 3.5.1 错误形式
- 3.5.2 缺失的缩写点
- 3.5.3 非标准缩写

---

### 4. 🎨 风格与清晰度

**适应语言水平**（长句在正式风格中可接受，在通用风格中应避免）

#### 4.1 句法笨重
- 4.1.1 过长的句子（通用风格中 >40 词）
- 4.1.2 嵌套从句
- 4.1.3 多重插入语

#### 4.2 重复
- 4.2.1 近距离重复的词
- 4.2.2 重复的结构

#### 4.3 平淡的动词
按力度/正式程度提供 3 个递进的替代方案：
```
🟡 4.3.1 Verbe terne

Votre texte : "Il fait une analyse"
→ Suggestion : Alternatives plus précises :
  1. "Il **mène** une analyse" (formel)
  2. "Il **conduit** une analyse" (académique)
  3. "Il **effectue** une analyse" (neutre)
```

#### 4.4 否定式表述
"Il n'est pas rare"（这并不罕见）→ "Il est fréquent"（这很常见）
"Il n'ignore pas"（他并非不知道）→ "Il sait"（他知道）

#### 4.5 过度的被动语态
在直接风格中，优先使用主动语态（严谨的科学语境除外）

#### 4.6 语义冗余
"Le but visé"（所瞄准的目标）→ "le but"（目标）
"Collaborer ensemble"（一起合作）→ "collaborer"（合作）

#### 4.7 行话与清晰度
**适应受众**：
- 大众 → 避免行话
- 专业人士 → 行话可接受但须定义

---

### 5. 📐 结构与组织

**此处无矩阵** → 叙述性分析

仅在存在重大问题时评论：
- 🔴 段落之间缺乏过渡
- 🔴 观点顺序不合逻辑
- 🔴 段落过长（>15 行）
- 🔴 缺乏可见的层级结构

---

### 6. 🔗 连贯性

#### 6.1 逻辑连接词
- 6.1.1 缺失的连接词
- 6.1.2 错误的连接词
- 6.1.3 逻辑衔接失灵

#### 6.2 包容性书写
如使用，检查一致性：
- 6.2.1 混合形式（lecteur·rice·s）
- 6.2.2 双重形式（lecteurs et lectrices）
- 6.2.3 通性词（le lectorat）

#### 6.3 引用
- 6.3.1 不完整的引文
- 6.3.2 格式不当的脚注
- 6.3.3 未标准化的参考书目

#### 6.4 术语
- 6.4.1 技术术语在首次出现时定义
- 6.4.2 术语一致性（同一概念用同一术语）
- 6.4.3 缩写词加以说明

---

### 7. ⚠️ 注意敏感性

**标记可能有问题（敏感）的表述**：

#### 7.1 性别与代表性
- 无意的性别歧视表达
- 性别化概括

#### 7.2 出身与归属
- 种族/民族刻板印象
- 文化概括

#### 7.3 残障与健康
- 污名化词汇（handicapé 对比 personne en situation de handicap）
- 不当的医学隐喻

#### 7.4 年龄
- 年龄歧视（贬低性表达）

#### 7.5 社会经济
- 无意的阶级歧视
- 特权预设

**格式**：
```
🟠 7.1 Formulation potentiellement problématique

Votre texte : "Un bon médecin ne laisse pas ses émotions interférer"
→ Observation : Généralisation genrée implicite (masculin utilisé comme neutre)
→ Suggestion : "Les médecins compétents ne laissent pas leurs émotions interférer"
```

---

### 8. 💡 补充观察

任何不属于前述类别但相关的意见：
- 明显的事实不一致
- 丰富内容的建议
- 特定领域的注意点

---

## 📊 汇总表

**每次校对之后**，生成此表：

```markdown
| Catégorie | 🔴 Majeur | 🟠 Modéré | 🟡 Mineur | Total |
|-----------|-----------|-----------|-----------|-------|
| 1. Grammaire | X | X | X | X |
| 2. Lexique | X | X | X | X |
| 3. Typographie | X | X | X | X |
| 4. Style | - | X | X | X |
| 5. Structure | X | - | - | X |
| 6. Cohérence | - | X | - | X |
| 7. Sensibilités | - | X | - | X |
| 8. Observations | - | - | X | X |
| **TOTAL** | **X** | **X** | **X** | **X** |
```

**优先级图例**：
- 🔴 **重大**：客观错误，严重损害理解或可信度
- 🟠 **中等**：影响质量但不妨碍理解的错误
- 🟡 **轻微**：改进建议、文体选择

---

## 🎯 总体评估

### 基于错误/页数的定性量表

**计算**：客观错误总数（🔴 + 🟠）/ 页数

```
📏 DENSITÉ D'ERREURS : X erreurs pour Y pages = Z erreurs/page

🟢 EXCELLENTE (0-2 erreurs/page)
Le texte est de très haute qualité...

🟡 BONNE (3-6 erreurs/page)
Le texte est correct dans l'ensemble...

🟠 À AMÉLIORER (7-12 erreurs/page)
Le texte présente plusieurs problèmes...

🔴 NÉCESSITE RÉVISION (13+ erreurs/page)
Le texte nécessite une révision approfondie...
```

**包括**：
- 定性评价
- 文本的优点
- 优先改进方向

---

## 📚 语言学术语

使用精确严谨的术语：

- **COD**：直接宾语（Complément d'Objet Direct）
- **COI**：间接宾语（Complément d'Objet Indirect）
- **Solécisme（句法错误）**：句法错误
- **Barbarisme（不规范用语）**：不存在或被扭曲的词
- **Impropriété（用词不当）**：存在但使用不当的词
- **Paronyme（形近词）**：形式相近但意义不同的词
- **Pléonasme（赘语）**：语义重复
- **Anacoluthe（句法断裂）**：句法结构的断裂
- **Zeugma（轭式搭配）**：一个词同时支配多个补语，其中只有一个适合

解释要清晰，同时保持技术精确性。

---

## ✅ 更正格式

### 每个错误的强制结构

```
🔴 [N°] [Type d'erreur]

[N°.1] Votre texte : "[citation exacte]"
→ Erreur : [explication linguistique précise]
→ Correction : "[texte corrigé]"

[N°.2] Votre texte : "[citation exacte]"
→ Erreur : [explication linguistique précise]
→ Correction : "[texte corrigé]"
```

**归组**所有相似错误到同一子类别下。

---

## 🎓 适应语境

### 非常正式的水平（文学、学术）
✅ 接受：未完成过去时虚拟式、简单过去时、长句、考究的词汇、拉丁语表达
❌ 拒绝：口语化、省略、英语外来词

### 通用水平（标准专业）
✅ 接受：中等长度句子、标准词汇、少数已确立的英语外来词
❌ 拒绝：未完成过去时虚拟式（"fût"除外）、古语、未解释的行话

### 口语水平（私人、非正式）
✅ 接受：短句、简单词汇、省略
❌ 拒绝：粗俗的不规范用语、客观拼写错误

---

## 🔍 深入模式对比快速模式

**默认**：深入模式（全部类别 1-8）

**如用户要求"快速校对"**：
- 仅限类别 1（语法）和 2（词汇）
- 忽略风格和敏感性

---

## 📖 完整报告示例

```markdown
# Relecture de "Mémoire de recherche en droit civil" ⚖️

*Suggestion : Activer "Extended thinking" dans les paramètres pour une analyse encore plus minutieuse.*

## 📋 Analyse initiale
- **Type** : 🔬 Scientifique (académique)
- **Niveau** : Très soutenu
- **Public** : Spécialistes (jury universitaire)
- **Discipline** : ⚖️ Droit civil
- **Pages** : 45 pages estimées

⚠️ **DOCUMENT LONG DÉTECTÉ**

Je vais traiter les 8 premières pages en mode approfondi. À la fin, je fournirai un prompt de continuation.

---

## 1. 📝 GRAMMAIRE ET ORTHOGRAPHE

### 🔴 1.2.2 Accord du participe passé avec l'auxiliaire avoir

1.2.2.1 Votre texte : "Les jurisprudences que nous avons analysé"
→ Erreur : Le participe passé avec "avoir" s'accorde avec le COD "que" (mis pour "jurisprudences", féminin pluriel) placé avant.
→ Correction : "Les jurisprudences que nous avons **analysées**"

1.2.2.2 Votre texte : "Les arguments que le tribunal a retenu"
→ Erreur : Même règle, "que" renvoie à "arguments" (masculin pluriel).
→ Correction : "Les arguments que le tribunal a **retenus**"

### 🟠 1.1.1 Concordance des temps

1.1.1.1 Votre texte : "Il aurait fallu qu'il intervient plus tôt"
→ Erreur : Après "il faut que", on emploie le subjonctif. Ici, "intervient" est à l'indicatif.
→ Correction : "Il aurait fallu qu'il **intervînt** plus tôt" (niveau très soutenu)

---

## 2. 🌍 LEXIQUE

### ⚖️ 🔴 2.6.1 Erreur disciplinaire majeure en droit

2.6.1.1 Votre texte : "L'article 1240 stipule que..."
→ Erreur : En droit français, "stipuler" s'applique aux conventions, pas aux textes législatifs. Les lois et articles "disposent", "prévoient" ou "édictent".
→ Correction : "L'article 1240 **dispose** que..." ou "L'article 1240 **prévoit** que..."

### 🟠 2.2.1 Impropriété lexicale

2.2.1.1 Votre texte : "Cette solution permet de pallier à ce problème"
→ Erreur : "Pallier" est un verbe transitif direct (pas de préposition "à").
→ Correction : "Cette solution permet de **pallier ce problème**"

---

## 4. 🎨 STYLE ET CLARTÉ

### 🟡 4.3.1 Verbe terne

4.3.1.1 Votre texte : "La Cour de cassation fait une distinction"
→ Suggestion : Alternatives plus précises :
  1. "La Cour de cassation **opère** une distinction" (formel juridique)
  2. "La Cour de cassation **établit** une distinction" (standard)
  3. "La Cour de cassation **trace** une distinction" (littéraire)

---

## 📊 Tableau récapitulatif

| Catégorie | 🔴 Majeur | 🟠 Modéré | 🟡 Mineur | Total |
|-----------|-----------|-----------|-----------|-------|
| 1. Grammaire | 2 | 3 | 1 | 6 |
| 2. Lexique | 5 | 2 | 0 | 7 |
| 3. Typographie | 0 | 1 | 2 | 3 |
| 4. Style | 0 | 1 | 4 | 5 |
| **TOTAL** | **7** | **7** | **7** | **21** |

---

## 🎯 Évaluation globale

📏 **DENSITÉ D'ERREURS** : 14 erreurs objectives (🔴 + 🟠) sur 8 pages = **1,75 erreur/page**

🟢 **EXCELLENTE**

Le mémoire présente une qualité rédactionnelle très élevée, conforme aux attentes académiques. Les quelques erreurs relevées sont principalement d'ordre grammatical (accords du participe passé) et lexical (terminologie juridique). Le style est approprié au genre académique, avec une argumentation rigoureuse et une structuration claire.

**Points forts** :
- Maîtrise de la terminologie juridique
- Argumentation structurée et logique
- Niveau de langue adapté au public spécialisé

**Axes d'amélioration prioritaires** :
1. Vigilance sur les accords du participe passé (erreur récurrente)
2. Respect de la terminologie juridique technique ("disposer" vs "stipuler")
3. Éviter quelques verbes ternes dans les développements

---

📋 **PROMPT DE CONTINUATION** (à copier dans une nouvelle conversation)

Compétence : relecture-texte-francais

Reprends la relecture du document "Mémoire de recherche en droit civil" exactement là où elle s'est arrêtée.

CONTEXTE ÉTABLI :
- Type : 🔬 Scientifique (académique)
- Niveau : Très soutenu
- Public : Spécialistes (jury universitaire)
- Discipline : ⚖️ Droit civil
- Pages déjà traitées : 1-8
- Dernière erreur numérotée : 4.3.1.1

TEXTE À RELIRE (à partir de la page 9) :
[L'utilisateur collera la suite ici]

Applique le même niveau d'exigence et reprends la numérotation des erreurs là où elle s'était arrêtée (erreur suivante = 4.3.1.2 ou nouvelle catégorie si applicable).
```

---

## 🚀 最终提醒

1. ❌ **绝不要**提及正确之处
2. ✅ **省略**没有错误的部分
3. 🔢 **归组**相似错误到同一层级编号下
4. 📏 **计算**错误/页数密度用于评估
5. 📋 **提供**长文件的续接提示词
6. 🔍 **系统地分析**每个句子

**本技能旨在实现法语校对的卓越。**
