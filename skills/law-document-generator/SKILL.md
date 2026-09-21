---
name: law-document-generator
description: 法律文书生成工具——生成律师事务所介绍信（调取卷宗）、律师事务所函（告知代理）、人口信息查询全套文书（授权委托书+查询申请表），并自动管理文号编号。当用户提到"介绍信"、"所函"、"人口信息查询"、"调取卷宗"、"授权委托书"、"出具文书"、"律所文书"、"查询户籍信息"、"律师函"、"法律文书"、"查人口信息"等法律文书相关请求时，必须使用本技能。本技能提供完整脚本，不要自己重写。
metadata:
  default-enabled: false
---

# 法律文书生成工具

本技能提供四大功能模块。**首次使用**必须先录入律师个人信息，之后所有文书自动填充。

---

## 前置：用户信息配置

**首次使用**：询问用户以下信息并填入 `scripts/user_config.json`：

| 字段 | 说明 | 示例 |
|------|------|------|
| name | 律师姓名 | 胡玥凡 |
| law_firm | 律师事务所全称 | 上海友安律师事务所 |
| license_number | 律师执业证号 | 13101201810022078 |
| phone | 手机号 | 18930747656 |
| office_phone | 律所座机 | 021-31902436 |
| address | 律所地址 | 上海市宝山区友谊路39号-10 |
| output_dir | 文档输出目录（不指定则默认 law-docs/） | C:\Users\xxx\法律文书 |
| numbering_file | 编号文件路径（默认与output_dir同级） | 同左 |

config_path = `<skill-path>/scripts/user_config.json`

> 提示：用 python `<skill-path>/scripts/user_config.py` 可查看当前配置。修改可直接编辑 JSON 或要求"更新我的信息"。

### 信息录入后展示摘要

```
已保存您的信息：
- 姓名：XXX
- 律所：XXX
- 执业证号：XXX
- 电话：XXX
```

---

## 模块一：介绍信（调取卷宗）

### 何时使用

用户需要去法院档案室调取已归档案件卷宗时。

### 询问信息

| 字段 | 说明 |
|------|------|
| 法院名称 | 如"上海市第二中级人民法院" |
| 案号 | 如"（2026）沪02民终5705号" |
| 当事人 | 如"左明、上海华豹保安服务有限公司" |
| 案由 | 如"劳动合同纠纷" |

> 用户可能一次性提供多个案件。询问是否合并到一页A4上（上下两半，中间虚线裁切）。

### 执行命令

单案件：
```bash
python <skill-path>/scripts/gen_intro_letter.py \
  --user-config <skill-path>/scripts/user_config.json \
  --court-name "法院名称" --case-number "案号" \
  --parties "当事人" --cause "案由" \
  --output-dir "输出目录"
```

多案件合并到一页A4：
```bash
python <skill-path>/scripts/gen_intro_letter.py \
  --user-config <skill-path>/scripts/user_config.json \
  --output-dir "输出目录" \
  --combine \
  --case "法院1|案号1|当事人1|案由1" \
  --case "法院2|案号2|当事人2|案由2"
```

### 格式

- 先写`介 绍 信`标题，再写文号
- 文号：`〔年份〕律所简称介字第XXX号`，自动编号
- 每张为 A5横版（21cm × 14.8cm），合并时一张A4上下各一份，中间虚线裁切线
- 字体：标题15pt黑体，正文11pt仿宋，自动缩放确保不溢出
- 正文："兹介绍XXX律师（执业证号：XXX）前往贵院调取已归档的以下案件诉讼卷宗"

---

## 模块二：律师事务所函（告知代理）

### 何时使用

律师已接受委托，需向法院发函告知代理关系。

### 询问信息

| 字段 | 说明 |
|------|------|
| 法院名称 | 如"上海市宝山区人民法院" |
| 原告/申请人 | 委托方当事人 |
| 被告/被申请人 | 相对方 |
| 案号 | 如"（2025）沪0113民初39627号" |
| 案由 | 劳动合同纠纷 |
| 代理阶段 | 一审/二审/仲裁/执行 |
| 代理律师 | 默认取配置中的律师姓名 |

### 执行命令

```bash
python <skill-path>/scripts/gen_law_firm_letter.py \
  --user-config <skill-path>/scripts/user_config.json \
  --court-name "法院" --plaintiff "原告" --defendant "被告" \
  --case-number "案号" --cause "案由" --stage "一审" \
  --output-dir "输出目录"
```

### 格式

- 文号：`〔年份〕律所简称民字第XXXX号`，自动编号
- 页边距：上3.7/下3.5/左2.8/右2.6，仿宋正文16pt
- 落款含律所地址和电话

---

## 模块三：人口信息查询全套文书

### 何时使用

代理诉讼案件，需查询被告/被查询人的户籍人口信息。生成：
1. 授权委托书（委托人=原告当事人）
2. 人口信息查询申请表（查询人姓名留空供手签）
3. 被查询人信息清单（txt，供写介绍信用）

### 询问信息

| 字段 | 说明 |
|------|------|
| 原告/委托人姓名 | 委托律师查询的当事人 |
| 原告/委托人身份证号 | 18位 |
| 被查询人姓名 | 逐个询问 |
| 被查询人身份证号 | 逐个询问 |

> 多个被查询人时，每人生成委托书1页+申请表1页，同一docx文件按页分隔。

### 执行命令

单被告：
```bash
python <skill-path>/scripts/gen_population_query.py \
  --user-config <skill-path>/scripts/user_config.json \
  --plaintiff-name "原告" --plaintiff-id "身份证" \
  --defendant "被查询人" --defendant-id "身份证" \
  --output-dir "输出目录"
```

多被告：
```bash
python <skill-path>/scripts/gen_population_query.py \
  --user-config <skill-path>/scripts/user_config.json \
  --plaintiff-name "原告" --plaintiff-id "身份证" \
  --defendants "姓名1|身份证1" --defendants "姓名2|身份证2" \
  --output-dir "输出目录"
```

### 格式

- 授权委托书：委托人=原告当事人，受托人=律所+律师信息，被查询人信息
- 查询申请表：单位信息填全，但**查询人姓名留空**（供手签）
- 宋体14pt，表格形式
- 同时输出 `.txt` 格式被查询人清单

---

## 模块四：自动编号管理

编号存储在 `numbering.json` 中，与输出目录同级。结构：

```json
{
  "year": 2026,
  "firm_abbr": "友安",
  "counters": {
    "intro_letter": 2,
    "law_firm_letter": 5,
    "contract": 46
  }
}
```

类型与格式：

| 文书类型 | 文号格式 | 示例 |
|---------|---------|------|
| 介绍信 | `〔年份〕律所简称介字第XXX号` | 〔2026〕友安介字第001号 |
| 所函 | `〔年份〕律所简称民字第XXXX号` | 〔2026〕友安民字第0001号 |
| 委托合同 | `（年份）律所简称民字第XX号` | （2026）沪友安民字第01号 |

- 律所简称从名称中提取（如"上海友安律师事务所"→"友安"）
- 每次生成自动+1，跨年重置

---

## 通用规则

1. 文书禁止使用\*号（计算公式除外），列举用·→等符号，强调用加粗
2. "此致"空两格（首行缩进），法院名称顶格
3. 委托代理人信息：地址=律所地址，电话=律师手机号
4. 所有正式法律文书发给用户时用 **Word（.docx）版本**
5. 文件命名：`YYYYMMDD_文书类型_当事人名.docx`

## 前提依赖

需要 `python-docx` 和 `lxml` 库。如缺失：
```bash
pip install python-docx lxml
```

## 脚本目录

所有脚本在 `scripts/` 目录下：
- `user_config.py` — 用户信息管理
- `gen_intro_letter.py` — 介绍信生成
- `gen_law_firm_letter.py` — 所函生成
- `gen_population_query.py` — 人口信息查询生成
