---
name: legal-review
description: 核验 AI 生成的法律法规和案例引用的准确性。利用元典 Open API 对法规、法条、案例进行逐条比对。当用户提及"复核""核查""核验""验证法律引用""review citation""fact-check legal""verify legal"时，或 AI 生成了包含法律法规、案例时触发。
metadata:
  author: 李伯阳律师（wx：legal-lby）
  version: 1.0.1
---

# 法律复核 Skill

**在生成法律文本时，实时核验每一项引用，发现错误立即修正，确保输出内容准确可靠。**

> 作者：**李伯阳律师**（微信：legal-lby）

## 工作方式

本 Skill 是 AI（你）在生成法律文本时的**内置质量检查机制**：

1. 你在生成或润色法律文本时，每引用一条法规、法条或案例，**立即**调用对应脚本核验
2. 核验通过 → 继续生成；核验不通过 → 用 `data.content` 中的权威原文替换后输出
3. 最终呈现给用户的文本，已经是经过核验的准确内容

## 激活检查 —— API Key

每次激活时，先检查 `YUANDIAN_API_KEY` 是否可用：

```bash
python -c "import os; print('已配置' if os.environ.get('YUANDIAN_API_KEY') else '未配置')"
```

如果未配置，引导用户完成以下步骤：

1. 告知用户需要在 https://open.chineselaw.com/profile 创建 API Key
2. 获取用户提供的 Key
3. 帮用户写入 skill 根目录的 `.env` 文件（推荐）：
   ```
   YUANDIAN_API_KEY=sk_xxx...
   ```
   或将 Key 设置为系统环境变量
4. 确认配置生效后，开始执行任务

## 脚本总览

| 脚本 | 用途 | 核验内容 |
|------|------|----------|
| `verify_regulation.py` | 按名称核验法规是否存在 | 名称、时效性、效力级别、发布/实施日期 |
| `verify_provision.py` | 按法规+条号核验法条原文 | 条号准确性、措辞比对 |
| `verify_case.py` | 按案号核验案例 | 案号、法院、案件类别、裁判日期 |
| `semantic_search.py` | 语义检索辅助查证 | 模糊引用时查找最相关法条/案例 |

---

## verify_regulation.py —— 核验法规

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--name` | string | 是 | 法规名称，如 `中华人民共和国民法典` |
| `--refer-date` | string | 否 | 参考日期 `YYYY-MM-DD`，用于确定当时生效的版本 |

### 用法

```bash
python skills/legal-review/scripts/verify_regulation.py --name "中华人民共和国民法典"
python skills/legal-review/scripts/verify_regulation.py --name "中华人民共和国刑法" --refer-date "2020-01-01"
```

### 返回示例（成功）

```json
{
  "status": "correct",
  "type": "法规",
  "citation": "中华人民共和国民法典",
  "data": {
    "name": "中华人民共和国民法典",
    "validity": "现行有效",
    "effect_level": "法律",
    "issue_date": "2020-05-28",
    "effective_date": "2021-01-01",
    "issuing_body": "全国人民代表大会",
    "document_number": "中华人民共和国主席令第45号"
  },
  "generated": {
    "name": "中华人民共和国民法典"
  }
}
```

### 返回示例（未找到）

```json
{
  "status": "not_found",
  "type": "法规",
  "citation": "中华人民共和国不正当地得利法",
  "message": "未查询到相关内容"
}
```

### AI 使用指引

- `status: "correct"` → 法规存在，用 `data` 中的信息确认引用准确
- `status: "not_found"` → 名称可能错误，检查后修正
- `data.validity` 为 `失效`/`已被修改` 时，应提醒用户法规状态并建议引用现行版本

---

## verify_provision.py —— 核验法条

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--law` | string | 是 | 法规名称，如 `中华人民共和国民法典` |
| `--article` | string | 是 | 条号，如 `第一千零七十六条` |
| `--generated-text` | string | 否 | AI 生成的原文，传入后自动比对措辞 |
| `--refer-date` | string | 否 | 参考日期 `YYYY-MM-DD` |

### 用法

```bash
# 仅核验条号是否存在
python skills/legal-review/scripts/verify_provision.py \
  --law "中华人民共和国民法典" \
  --article "第一千零七十六条"

# 核验条号 + 比对原文措辞
python skills/legal-review/scripts/verify_provision.py \
  --law "中华人民共和国民法典" \
  --article "第一千零七十六条" \
  --generated-text "夫妻双方自愿离婚的，应当签订书面离婚协议..."
```

### 返回示例（完全匹配）

```json
{
  "status": "correct",
  "type": "法条",
  "citation": "《中华人民共和国民法典》第一千零七十六条",
  "data": {
    "law_name": "中华人民共和国民法典",
    "article": "第一千零七十六条",
    "title": "中华人民共和国民法典第一千零七十六条",
    "content": "　夫妻双方自愿离婚的，应当签订书面离婚协议，并亲自到婚姻登记机关申请离婚登记。\n　离婚协议应当载明双方自愿离婚的意思表示和对子女抚养、财产以及债务处理等事项协商一致的意见。",
    "validity": "现行有效",
    "effect_level": "法律",
    "issue_date": "2020-05-28",
    "effective_date": "2021-01-01"
  },
  "generated": {
    "law": "中华人民共和国民法典",
    "article": "第一千零七十六条",
    "text": "夫妻双方自愿离婚的，应当签订书面离婚协议，并亲自到婚姻登记机关申请离婚登记。"
  },
  "match": "exact"
}
```

### 返回示例（措辞不匹配）

```json
{
  "status": "incorrect",
  "type": "法条",
  "citation": "《中华人民共和国民法典》第一千零七十六条",
  "data": {
    "law_name": "中华人民共和国民法典",
    "article": "第一千零七十六条",
    "content": "　夫妻双方自愿离婚的，应当签订书面离婚协议，并亲自到婚姻登记机关申请离婚登记。"
  },
  "generated": {
    "law": "中华人民共和国民法典",
    "article": "第一千零七十六条",
    "text": "夫妻双方自愿离婚的，口头协议离婚即可。"
  },
  "match": "different",
  "discrepancy": "生成文本与权威原文不符"
}
```

### 返回示例（未找到）

```json
{
  "status": "not_found",
  "type": "法条",
  "citation": "《中华人民共和国民法典》第九千九百条",
  "message": "未查询到相关内容"
}
```

### AI 使用指引

- `match: "exact"` → 措辞完全正确，放心引用
- `match: "partial"` 或 `match: "different"` → **立即修正**，将生成文本替换为 `data.content` 中的权威原文
- `not_found` → 检查条号是否写错（常见错误：记错条号、混淆不同法规的条号）

---

## verify_case.py —— 核验案例

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--ah` | string | 是 | 案号，如 `（2021）京01刑终263号` |
| `--type` | string | 否 | 案例类型：`ptal`（普通案例，默认）/ `qwal`（权威案例） |

### 用法

```bash
# 核验普通案例
python skills/legal-review/scripts/verify_case.py --ah "（2021）京01刑终263号"

# 核验权威案例
python skills/legal-review/scripts/verify_case.py --ah "（2023）鲁02民辖终472号" --type qwal
```

### 返回示例（成功）

```json
{
  "status": "correct",
  "type": "案例",
  "case_type": "普通案例",
  "citation": "（2021）京01刑终263号",
  "data": {
    "case_number": "（2021）京01刑终263号",
    "title": "刘磊盗窃二审刑事裁定书",
    "court": "北京市第一中级人民法院",
    "case_category": "刑事案件",
    "trial_procedure": "二审案件",
    "judgment_date": "2021年04月29日",
    "document_type": "裁定书",
    "cause_of_action": "盗窃罪",
    "region_province": "北京",
    "content": "……"
  },
  "generated": {
    "case_number": "（2021）京01刑终263号"
  }
}
```

### 返回示例（未找到）

```json
{
  "status": "not_found",
  "type": "案例",
  "citation": "（2099）京01刑终999号",
  "message": "未查询到相关内容"
}
```

### AI 使用指引

- `status: "correct"` → 案例存在，用 `data` 中的信息核对案由、法院、裁判日期与你的引用是否一致
- `status: "not_found"` → 案号可能写错（常见错误：括号格式、数字写错、法院简称错误）
- 注意括号格式：中文括号 `（` 和 `）`，注意全半角

---

## semantic_search.py —— 语义检索（辅助）

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--type` | string | 是 | 检索类型：`law`（法律法规）/ `case`（案例） |
| `--query` | string | 是 | 检索文本，描述你要找的内容 |
| `--top-k` | int | 否 | 返回数量，默认 5，最大 45 |
| `--validity` | string | 否 | 时效性过滤（仅 law）：`现行有效`/`失效`/`已被修改` |
| `--effect-level` | string | 否 | 效力级别过滤（仅 law）：`法律`/`司法解释`/`行政法规`/等 |
| `--case-type` | string | 否 | 案件类别过滤（仅 case）：`刑事案件`/`民事案件`/等 |
| `--case-start` | string | 否 | 结案起始日期（仅 case），`YYYY-MM-DD` |
| `--case-end` | string | 否 | 结案截止日期（仅 case），`YYYY-MM-DD` |

### 用法

```bash
# 查找相关法条
python skills/legal-review/scripts/semantic_search.py \
  --type law \
  --query "入户盗窃 数额较大 量刑标准" \
  --validity "现行有效"

# 查找相关案例
python skills/legal-review/scripts/semantic_search.py \
  --type case \
  --query "买卖合同逾期付款违约金" \
  --case-type "民事案件" \
  --top-k 3
```

### 返回示例

```json
{
  "status": "correct",
  "type": "law",
  "query": "入户盗窃 数额较大 量刑标准",
  "count": 3,
  "results": [
    {
      "ftid": "...",
      "fgtitle": ["中华人民共和国刑法(2023修正)"],
      "num": "第二百六十四条",
      "content": "　盗窃公私财物，数额较大的，或者多次盗窃、入户盗窃、携带凶器盗窃、扒窃的，处三年以下有期徒刑、拘役或者管制，并处或者单处罚金……",
      "sxx": "现行有效",
      "effect1": "法律",
      "score": 0.8923
    }
  ]
}
```

### AI 使用指引

- 当不确定应引用哪条法规、或想确认是否有更贴切的规定时使用
- 不要直接用检索结果替代引用，应找到准确的法条后再用 `verify_provision.py` 核验

## 脚本通用约定

- 优先从环境变量 `YUANDIAN_API_KEY` 读取密钥，未设置则自动读取 skill 根目录下的 `.env` 文件
- 所有脚本支持 `--help` 查看参数说明
- 输出 JSON 到 stdout
- 退出码：成功 0，失败非 0
- 仅使用 Python 标准库，**无外部依赖**

## 环境要求

- Python 3.8+
- 网络访问 `https://open.chineselaw.com/open/*`
- 有效的元典 Open API Key
