# 法海风控 API 参考文档

## 环境配置

| 配置项 | 值 |
|--------|-----|
| Base URL | `https://api.fahaicc.com` |
| 接口版本 | `vip`（高精版） |
| 授权码 | 由用户通过 `--auth-code` 参数传入，不内置 |

## 鉴权机制

所有接口均使用相同的鉴权方式：

1. 获取当前毫秒级时间戳 `rt` = `str(int(time.time() * 1000))`
2. 计算签名 `sign` = `MD5(authCode + rt)`
3. 将 `authCode`、`rt`、`sign` 作为 URL 查询参数传递

**授权码获取：** 用户须自行提供授权码。未提供授权码时，脚本输出提示"授权码开通可联系我们010-62502608"，不执行接口调用。

---

## 一、企业司法数据列表查询

### 请求

- **方法**: GET
- **URL**: `{BASE_URL}/{VERSION}/query/{domain}`
- **参数**:

| 参数 | 位置 | 说明 |
|------|------|------|
| authCode | query | 用户提供的授权码 |
| rt | query | 毫秒级时间戳 |
| sign | query | MD5(authCode + rt) |
| args | query | JSON 字符串，包含 keyword/pageno/range/dataType |

### args 参数说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词（企业名称、统一社会信用代码等） |
| pageno | int | 是 | 页码，从 1 开始 |
| range | int | 是 | 每页条数 |
| dataType | string | 否 | 维度代码，留空则查询该领域所有维度；多个用逗号分隔 |

### 领域代码（domain）

| 代码 | 含义 |
|------|------|
| sifa | 司法（涉诉） |
| sat | 税务 |
| epb | 环保 |
| custom | 海关 |
| credit | 信用 |
| fda | 食药监 |
| pbc | 央行（人民银行） |
| bid | 招投标 |
| media | 媒体 |
| zhaopin | 招聘 |
| pledge | 质押 |
| mortgage | 抵押 |
| zyzb | 经营指标 |

### 司法领域（sifa）常见维度代码

| 代码 | 含义 |
|------|------|
| cpws | 裁判文书 |
| zxgg | 执行公告 |
| sswdjg | 失信被执行人 |
| sfpm | 司法拍卖 |
| ktgg | 开庭公告 |
| ajgg | 案件公告 |

> 其他领域的维度代码请参考法海官方接口文档，或通过 domain 不指定 dataType 的方式查询全部维度。

### 响应字段

| 字段 | 说明 |
|------|------|
| code | "s" 表示成功，其他表示失败 |
| msg | 失败时的错误信息 |
| totalCount | 命中总数 |
| pageNo | 当前页码 |
| totalPageNum | 总页数 |
| {dataType}Count | 各维度的命中数量（如 cpwsCount） |
| allList | 当前页条目列表 |

### allList 条目字段

| 字段 | 说明 |
|------|------|
| dataType | 维度类型 |
| title | 标题 |
| sortTimeString | 时间 |
| entryId | **条目唯一标识，用于详情查询** |
| body | 摘要内容 |

---

## 二、案件详情查询

### 请求

- **方法**: GET
- **URL**: `{BASE_URL}/{VERSION}/{detail_api}/{dimension}`
- **参数**:

| 参数 | 位置 | 说明 |
|------|------|------|
| authCode | query | 用户提供的授权码 |
| rt | query | 毫秒级时间戳 |
| sign | query | MD5(authCode + rt) |
| id | query | 从列表查询结果中获取的 entryId |

### detail_api 路径类型选择

| 路径类型 | 适用场景 |
|----------|----------|
| export | **涉诉领域（sifa）及所有 VIP/高精版领域**（默认） |
| entry | 非涉诉标准版（涉税/环保/信用等标准版） |

> 当前 Skill 使用 VIP 高精版，所有领域详情查询均使用 `export` 路径。

### dimension 参数

dimension 必须与列表查询时条目的 `dataType` 一致（如 cpws、zxgg 等）。

### 响应字段

| 字段 | 说明 |
|------|------|
| code | "s" 表示成功，其他表示失败 |
| msg | 失败时的错误信息 |
| totalCount | 详细记录条数 |
| searchSeconds | 查询耗时（秒） |
| {dimension} | 详情数据列表，key 与 dimension 同名（如 "cpws": [...]） |

---

## 典型工作流

```
1. 确认授权码
   - 如用户未提供授权码 → 输出"授权码开通可联系我们010-62502608"，终止流程
   - 如用户提供了授权码 → 继续下一步

2. 查询列表
   python3 fahai_query.py --auth-code "授权码" --keyword "企业名称" --domain sifa --data-type cpws

3. 从返回结果 allList 中获取 entryId

4. 查询详情
   python3 fahai_details.py --auth-code "授权码" --entry-id "上一步获取的entryId" --dimension cpws
```
