# 得理案例检索 API 详细说明与策略指南

## 一、API 基本信息

- **端点**：`https://platform.delilegal.com/api/v1/generice/case/list`
- **鉴权**：`Authorization: Bearer YOUR_API_KEY`
- **方法**：POST
- **Content-Type**：application/json

## 二、请求参数

### 2.1 请求体（扁平结构，无 condition 嵌套）

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `pageNo` | int | 否 | 页码，默认 1 |
| `pageSize` | int | 否 | 每页条数，默认 10，最大10条 |
| `sortField` | string | 否 | 排序字段：`"correlation"`（相关性）/ `"time"`（时间） |
| `sortOrder` | string | 否 | 排序方向：`"desc"`（降序）/ `"asc"`（升序） |
| `query` | string | 否 | 检索条件（自然语言：如法律问题、争议焦点、案情描述等），与 `longText` 二选一 |
| `longText` | string | 否 | 长文本语义匹配（案件材料内容），与 `query` 二选一 |

> ⚠️ **重要**：新版 API 请求体为扁平结构，**不使用 `condition` 嵌套对象**。旧版的 `condition.keywords/causeNameArr/courtLevelArr` 等字段已废弃。

### 2.2 响应结构

```json
{
    "success": true,
    "code": 0,
    "msg": "ok",
    "body": {
        "data": [ ... ],
        "totalCount": 100,
        "totalPage": 10,
        "queryId": "xxx"
    }
}
```

### 2.3 data 数组中的案例对象主要字段

| 字段名 | 说明 |
|-------|------|
| `title` | 案件名称 |
| `caseNumber` | 案号 |
| `cause` | 案由 |
| `court` | 审理法院 |
| `levelOfTrial` | 审理程序（一审/二审/再审） |
| `judgementType` | 文书类型（判决书/裁定书等） |
| `judgementDate` | 裁判日期 |
| `publishTypeName` | 公布类型（指导性案例/典型案例等） |
| `content` | 内容摘要 |
| `highlights` | 高亮摘要（含 `<em>` 标签，需过滤） |

## 三、请求示例

### 3.1 关键词检索（最常用）

```json
{
    "pageNo": 1,
    "pageSize": 10,
    "sortField": "correlation",
    "sortOrder": "desc",
    "query": "小产权房买卖合同无效"
}
```

### 3.2 按时间倒序检索

```json
{
    "pageNo": 1,
    "pageSize": 20,
    "sortField": "time",
    "sortOrder": "desc",
    "query": "伞形信托合同效力营业信托纠纷"
}
```

### 3.3 长文本语义匹配

```json
{
    "pageNo": 1,
    "pageSize": 10,
    "sortField": "correlation",
    "sortOrder": "desc",
    "longText": "原告与被告于2023年3月签订借款合同，借款金额120万元，约定年利率10%，借款期限12个月。被告到期未还款，原告起诉要求偿还本金及利息..."
}
```

## 四、脚本调用方式

技能内置了 `scripts/search_cases.py` 检索脚本，支持以下参数：

```bash
# 基础关键词检索
python3 scripts/search_cases.py "民间借贷利率上限" --size 10

# 按时间排序
python3 scripts/search_cases.py "劳动合同违法解除" --sort-field time --sort-order desc --size 20

# 长文本匹配
python3 scripts/search_cases.py --long-text "案件材料文本..."

# 翻页
python3 scripts/search_cases.py "检索条件（自然语言）" --page 2 --size 10
```

| 参数 | 说明 |
|------|------|
| `keyword` | 检索条件（与 --long-text 二选一） |
| `--long-text` | 长文本语义匹配 |
| `--page` | 页码 |
| `--size` | 每页条数 |
| `--sort-field` | 排序字段：correlation（相关性）/ time（时间） |
| `--sort-order` | 排序方向：desc（降序）/ asc（升序） |

## 五、类案检索报告场景下的检索策略

### 5.1 检索层级优先级（按《统一法律适用指导意见》）

由于新版 API 为通用检索，通过关键词精细化来定向覆盖各级法院：

| 优先级 | 目标 | 关键词策略 |
|:------:|------|------|
| 1 | 指导性案例 | `"[争议焦点] 最高人民法院 指导性案例"` |
| 2 | 最高人民法院案例 | `"[争议焦点] 最高人民法院"` |
| 3 | 本省高级法院案例 | `"[争议焦点] [省份]高级人民法院"` |
| 4 | 上一级法院及本院 | `"[争议焦点] [市级法院名]"` |

### 5.2 关键词调整策略

- **结果过多（>100）**：细化关键词，增加争议焦点、法院名等限定词
- **结果过少（<5）**：扩展同义词（如"小产权房"↔"农村房屋"↔"集体土地建设房屋"），或使用更泛化的检索词

### 5.3 长文本匹配策略

当用户提供了案件材料文件时：
1. 先解析文件内容（提取文本）
2. 使用 `--long-text` 参数传入案件事实描述
3. API 会基于语义相似度匹配最相似的裁判文书

### 5.4 API Key 配置

如未配置 API Key，脚本会提示：
> config.json 中的 apikey 尚未配置，请前往 https://platform.delilegal.com 创建 API Key

此时须告知用户按提示操作，不执行后续检索。
