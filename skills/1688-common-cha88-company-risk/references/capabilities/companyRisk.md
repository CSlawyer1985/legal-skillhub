# 公司风险查询指南

## 功能说明

通过 CLI 调用 88查公司风险接口，根据统一社会信用代码（或 companyId）查询企业的风险信息，返回按风险大类（mainType）分组的所有风险记录，包含经营异常、行政处罚、被执行人、失信被执行人、监管措施等。

## 前置条件

- 已配置 AK（未配置时会提示运行 `cli.py configure YOUR_AK`）
- 需要已知统一社会信用代码或 companyId

## CLI 调用

```bash
python3 {baseDir}/cli.py companyRisk --socialCreditCode "信用代码" --page 1 --pageSize 10
```

### 参数说明

| 参数 | 缩写 | 是否必填 | 说明 |
|------|------|----------|------|
| `--socialCreditCode` | `-s` | 与 `--companyId` 二选一 | 统一社会信用代码（18 位，91 开头） |
| `--companyId` | `-c` | 与 `--socialCreditCode` 二选一 | 企业 ID |
| `--page` | `-p` | 否（默认 1） | 页码 |
| `--pageSize` | `-n` | 否（默认 10） | 每页数量 |

### 调用示例

```bash
# 按统一社会信用代码查询
python3 {baseDir}/cli.py companyRisk -s "91441881577945666N"

# 翻页
python3 {baseDir}/cli.py companyRisk -s "91441881577945666N" -p 2 -n 20

# 按 companyId 查询
python3 {baseDir}/cli.py companyRisk -c "1234567"
```

## 接口契约

- **API 路径**：`/api/companyRisk/1.0.0`
- **请求体**：`{"companyId":"","pageSize":"10","page":"1","socialCreditCode":"91441881577945666N"}`
  - 注意：`pageSize` / `page` 在请求体中是字符串。

## 返回结构

API 响应 `data` 字段包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `total` | int | 总风险记录数 |
| `pageNo` | int | 当前页码 |
| `pageSize` | int | 当前页条数 |
| `riskMap` | object | 按风险大类（`mainType`）分组的风险记录 |

`riskMap` 中每条记录字段：

| 字段 | 说明 |
|------|------|
| `mainType` | 风险大类（如：监管措施、司法风险、经营风险） |
| `subType` | 风险子类型（如：经营异常、行政处罚） |
| `level` | 风险等级（高风险/中风险/低风险/提示） |
| `time` | 风险时间（字符串） |
| `timeStamp` | 风险时间戳（毫秒） |
| `companyName` | 企业名称 |
| `socialCreditCode` | 统一社会信用代码 |
| `contentChinese` | 风险详情，JSON 字符串需自行解析 |
| `rowId` | 记录 ID |

## 输出格式

### 成功

`markdown` 字段包含格式化好的风险列表，Agent 直接输出即可。

```json
{
  "success": true,
  "markdown": "# 企业风险查询结果\n**查询关键字：** ...",
  "data": { "data": { "total": 17, "riskMap": {...} } }
}
```

输出包含两部分：
1. **风险概览**：按 `mainType` 聚合，展示每个大类的总数和风险等级分布
2. **各风险大类明细**：分组展示每条风险记录（等级、子类型、时间、企业名、详情）

### 无风险记录

```json
{
  "success": true,
  "markdown": "# 企业风险查询结果\n...\n✅ 未发现风险记录。"
}
```

### 失败 — AK 未配置

```json
{
  "success": false,
  "markdown": "AK 未配置。\n\n运行: `cli.py configure YOUR_AK`"
}
```

### 失败 — 参数缺失

```json
{
  "success": false,
  "markdown": "❌ 参数缺失：必须提供 --socialCreditCode 或 --companyId 至少一个。"
}
```

## Agent 处理流程

```
1. 确认用户已提供统一社会信用代码或 companyId
2. （可选）向用户确认要查询的企业风险，并说明默认查询第 1 页 10 条
3. 执行 python3 {baseDir}/cli.py companyRisk --socialCreditCode <代码> [--page <页码>] [--pageSize <每页>]
4. 检查输出：
   - success=true → 直接输出 markdown 字段（已包含风险概览 + 明细），可追加风险解读
   - success=false → 直接输出 markdown 字段（错误描述）
5. 当 total > pageSize 时，可主动提示用户是否翻页
```

## 异常处理

| 场景 | Agent 应对 |
|------|-----------|
| AK 未配置 | 引导用户执行 `cli.py configure YOUR_AK` 配置 AK |
| 参数缺失 | 提示用户补充 `--socialCreditCode` 或 `--companyId` |
| 信用代码格式错误 | 提示用户检查输入（应为 18 位，91 开头） |
| 接口返回格式异常 | 提示"格式异常，请稍后重试" |
| 限流（429） | 提示"建议 1-2 分钟后重试" |
| 其他运行时异常 | 原样输出错误信息 |
