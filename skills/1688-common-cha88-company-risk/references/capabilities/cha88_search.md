# 企业搜索指南

## 功能说明

通过 CLI 调用 88查企业搜索接口，根据公司名称关键词搜索企业列表，返回匹配企业的基本信息（名称、法人、状态、信用代码等），常用于在仅知道公司名时获取统一社会信用代码，再配合 `companyRisk` 查询风险信息。

## 前置条件

- 已配置 AK（未配置时会提示运行 `cli.py configure YOUR_AK`）
- 用户已提供企业名称关键词

## CLI 调用

```bash
python3 {baseDir}/cli.py cha88_search --keyword "公司名称关键词" --pageNo 1 --pageSize 10
```

### 参数说明

| 参数 | 缩写 | 是否必填 | 说明 |
|------|------|----------|------|
| `--keyword` | `-k` | 是 | 公司名称关键词 |
| `--pageNo` | `-n` | 否（默认 1） | 页码 |
| `--pageSize` | `-s` | 否（默认 10） | 每页数量 |

### 调用示例

```bash
# 搜索企业
python3 {baseDir}/cli.py cha88_search -k "萍乡市能华加油站"

# 翻页
python3 {baseDir}/cli.py cha88_search -k "能华" -n 2 -s 20
```

## 接口契约

- **API 路径**：`/api/companySearch/1.0.0`
- **请求体**：`{"query":"公司名称","pageNo":1,"pageSize":10}`

## 返回结构

API 响应 `data` 字段包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `total` | int | 匹配企业总数 |
| `totalPage` | int | 总页数 |
| `data` | array | 企业列表 |

企业列表中每条记录关键字段：

| 字段 | 说明 |
|------|------|
| `ent_name` | 企业名称（可能含 `<em>` 高亮标记） |
| `legal_name` | 法人代表 |
| `ent_status` | 企业状态（存续/注销等） |
| `reg_cap` | 注册资本 |
| `social_credit_code` | 统一社会信用代码 |
| `es_date` | 成立日期 |
| `ent_type` | 企业类型 |
| `address` | 注册地址 |
| `companyId` | 企业 ID |
| `ability_label_outside` | 能力标签 |

## 输出格式

### 成功

`markdown` 字段包含格式化好的企业搜索列表，Agent 直接输出即可。

```json
{
  "success": true,
  "markdown": "# 企业查询结果：萍乡市能华加油站\n共找到 **10** 家企业...",
  "data": { "data": { "total": 10, "data": [...] } }
}
```

### 无结果

```json
{
  "success": true,
  "markdown": "未找到与「关键词」相关的企业信息。"
}
```

### 失败 — AK 未配置

```json
{
  "success": false,
  "markdown": "AK 未配置。\n\n运行: `cli.py configure YOUR_AK`"
}
```

## Agent 处理流程

```
1. 确认用户已提供公司名称关键词
2. 执行 python3 {baseDir}/cli.py cha88_search --keyword "关键词"
3. 检查输出：
   - success=true → 直接输出 markdown 字段
   - success=false → 直接输出 markdown 字段（错误描述）
4. 如需进一步查询风险，从结果中提取目标企业的 social_credit_code
5. 执行 python3 {baseDir}/cli.py companyRisk --socialCreditCode "信用代码"
```

## 典型组合场景：公司名 → 风险查询

当用户仅提供公司名称，需要查询其风险信息时：

```bash
# 第一步：搜索企业，获取统一社会信用代码
python3 {baseDir}/cli.py cha88_search -k "萍乡市能华加油站"
# 从结果中获取 social_credit_code: 913603136834706924

# 第二步：用信用代码查询风险
python3 {baseDir}/cli.py companyRisk --socialCreditCode "913603136834706924"
```

## 异常处理

| 场景 | Agent 应对 |
|------|-----------|
| AK 未配置 | 引导用户执行 `cli.py configure YOUR_AK` 配置 AK |
| 搜索无结果 | 建议用户换关键词重试，或检查公司名是否有误 |
| 接口返回格式异常 | 提示"格式异常，请稍后重试" |
| 限流（429） | 提示"建议 1-2 分钟后重试" |
| 其他运行时异常 | 原样输出错误信息 |
