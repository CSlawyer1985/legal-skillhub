# USPTO TESS / TSDR——查询语法速查表

## 端点

- **检索（现行界面）：** https://tmsearch.uspto.gov/
- **检索（旧版/高级运算符）：** https://tmsearch.uspto.gov/search/search-information
- **TSDR（状态与档案）：** https://tsdr.uspto.gov/#caseNumber=<SERIAL>&caseType=SERIAL_NO&searchType=statusSearch
- **商标审查程序手册（TMEP）：** https://tmep.uspto.gov/
- **ID 手册（可接受的标识）：** https://idm-tmng.uspto.gov/

## 重要——现行界面 vs 旧版语法

USPTO 于 2023 年底以新检索界面（`tmsearch.uspto.gov`）取代旧版 TESS。旧版 `[BI]`、`[IC]`、`[CC]` 字段标签运算符**在新型自由文本搜索框中无法可靠解析**。它们在**专家检索 / 高级**模式及许多第三方镜像中仍可用，且仍是传达意图最清晰的方式。指示用户时，给出两种形式：

- **新界面（基本检索）：** 用户在自由文本框中输入术语，然后使用表单的筛选标签选择类别、状态和所有人。
- **新界面（专家检索）：** 点击“Expert Search”——旧版标签语法（`marname[BI] AND 009[IC]`）在此可正常解析。
- **旧版运算符（下文）：** 将其作为标准查询呈现，告诉用户粘贴到专家检索中，或手工翻译成基本表单字段。

| 旧版标签 | 新界面基本字段等价物 |
|---|---|
| `[BI]` Basic Index 基本索引 | 自由文本搜索框 |
| `[CM]` Combined Mark 组合商标 | 自由文本搜索框（默认） |
| `[IC]` International Class 国际类别 | “International Class”筛选标签 |
| `[GS]` Goods/Services 商品/服务 | “Goods and Services”筛选 |
| `[ON]` Owner 所有人 | “Owner”筛选 |
| `[LD]` Live/Dead 有效/失效 | “Status”筛选（有效 / 失效 / 全部） |
| `[CC]` Design Code 设计编码 | “Design Code”筛选 |
| `[FD]` Filing Date 申请日 | “Filing Date”日期范围 |
| `[SN]` Serial Number 序列号 | “Serial Number”筛选 |

用户将旧版语法粘贴到基本框后报告零结果时，引导其转用专家检索。

## 字段标签（旧版语法，用于专家检索并作为标准查询形式）

| 标签 | 字段 |
|---|---|
| `[CM]` | 组合商标（默认检索） |
| `[BI]` | 基本索引——商标全文 |
| `[ON]` | 所有人名称 |
| `[GS]` | 商品与服务 |
| `[IC]` | 国际类别 |
| `[CC]` | 设计编码（USPTO） |
| `[LD]` | 有效/失效 |
| `[FD]` | 申请日 |
| `[RD]` | 注册日 |
| `[SN]` | 序列号 |
| `[RN]` | 注册号 |

## 运算符

- `AND`、`OR`、`NOT`
- `*`——右截断通配符（`alpha*`）
- `?`——单字符通配符
- `$`——复数/家族词根
- 精确短语用引号

## 每次初筛的建议查询组合

对第 N 类中的文字商标 `MARKNAME`：

```
1. 精确——全部状态：
   marname[BI] AND `live`[LD] OR `dead`[LD]

2. 目标类别中精确：
   marname[BI] AND N[IC]

3. 语音/拼写错误组（按下文 SOUNDEX 模式构建）：
   (marname OR marqname OR markname OR marcname OR markknayme OR
    marknaim OR marknaem)[BI]

4. 词根/通配符：
   mark*[BI] AND N[IC]

5. 所有人（如已知在先使用人）：
   "Owner Name Inc"[ON]
```

## SOUNDEX 式替换模式

构建语音替代时，沿商标走过以下替换：

| 音素 | 常见拼写 |
|---|---|
| K 音 | c, k, ck, q, ch, qu |
| S 音 | s, c, ss, sc, ps, z |
| F 音 | f, ph, gh |
| J 音 | j, g（e/i 前）, dg, dj |
| 长 A | a, ai, ay, ei, eigh |
| 长 E | e, ee, ea, ie, ei, y |
| 长 I | i, y, ie, igh, uy |
| 长 O | o, oa, ow, oe, ough |
| 长 U | u, oo, ew, ue, oo, ou |
| 弱元音（Schwa） | a, e, i, o, u（任何非重读） |
| 静默 E | 省略 / 加词尾 e |

辅音加倍与省略（一个 R vs 两个；m vs mm）可捕捉大量近似命中。

## 设计编码检索（标志/艺术化商标）

商标含任何视觉要素时，设计编码是强制的。USPTO 设计检索编码手册位于 https://tmdesigncodes.uspto.gov/。常见高流量类别：

- 01.x——天体、自然现象
- 02.x——人类
- 03.x——动物
- 05.x——植物
- 26.x——几何图形和立体（非常常见——圆形、方形、三角形、抽象标志）
- 27.x——书写形式（艺术化字母、字母组合）

对典型的“形状内艺术化文字商标”，组合字母形式编码与几何形状编码，如 `27.03.01[CC] AND 26.01.21[CC]`。

设计编码初筛**不是**供应商图形检索（Corsearch / CompuMark）的替代品——标记该局限。

## TSDR 调取——每个冲突提取什么

对每个潜在冲突商标，从 TSDR 提取：

1. 状态（有效 / 失效，已注册 / 待审 / 已放弃）
2. 所有人（当前——检查转让链条）
3. 类别和完整商品/服务陈述
4. 申请基础（1(a) 使用、1(b) 意图使用、44(d) 外国优先权、44(e) 外国注册、66(a) 马德里）
5. 首次使用日期和首次商业使用日期（如为 1(a)）
6. 审查意见历史（任何引用其他商标的 §2(d) 驳回——为强度提供信息）
7. 放弃声明、翻译、音译
8. 续展 / §8 / §15 状态

档案常可揭示商标是否受争议、是否因修改而范围狭窄，或是否曾为 TTAB 程序的对象。
