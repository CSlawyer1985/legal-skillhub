# PatSeek API 接口参考

> 本文档供 skill 调用时参考，包含完整的接口规范、参数说明和错误码。

## 基本信息

| 项目 | 值 |
|---|---|
| 基础 URL | `https://patseek.cn` |
| 协议 | HTTPS |
| 认证方式 | Bearer Token（`Authorization` 请求头） |
| 内容类型 | `application/json` |

## 认证

API Key 格式：`ps_` + 32 位十六进制字符串（如 `ps_0931e2efa48df3aa2596de57c27d9449`）

```
Authorization: Bearer ps_<API_KEY>
```

⚠️ **示例 Key 可能已过期或积分耗尽，请使用自己申请的 Key。**

### 如何获取 API Key

1. 访问 [https://patseek.cn](https://patseek.cn) 注册/登录
2. 进入「个人中心 → API Key 管理」
3. 点击「创建新 Key」，复制保存（只显示一次）
4. 在调用时通过 `-H "Authorization: Bearer ps_你的Key"` 或环境变量 `PATSEEK_API_KEY` 传入

| 状态码 | 含义 | 处理方式 |
|---|---|---|
| 401 | Key 缺失或无效 | Key 格式错误或已过期，请重新申请 |
| 402 | 积分不足 | 登录 patseek.cn 充值积分 |
| 403 | Key 已被禁用 | 联系平台管理员 |

## 积分消耗

| 接口 | 消耗 |
|---|---|
| 专利详情 `GET /v1/patent/{id}` | 1 积分 |
| Bool 检索 `POST /v1/search` | 2 积分 |
| 语义检索（异步） | 10 积分 |

## 频率限制

| 接口 | 限制 |
|---|---|
| 专利详情 | 60 次/分钟 |
| Bool 检索 | 30 次/分钟 |
| 语义检索提交 | 5 次/分钟 |
| 任务查询/列表/取消 | 120 次/分钟 |

## 接口详情

### 1. Bool 关键词检索

**POST** `/v1/search`

请求体:
```json
{ "query": "低空空域 AND 无人机", "page": 1, "page_size": 20 }
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `query` | string | 是 | 检索表达式 |
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页条数 1-100，默认 20 |

query 格式支持布尔运算、字段前缀和组合检索，详见 `query_syntax.md`：

**布尔运算符：**
- `A B` 或 `A AND B` — 所有词都必须出现
- `A OR B` — 任一出现即命中
- `(A OR B) C` — 括号控制优先级

**字段前缀：**
- `AP=(...)` — 申请人（match_phrase）
- `IPC=(...)` — IPC 分类号（只用前 4 位，如 H01M）
- `PID=(...)` — 公开号（term 精确）
- `AN=(...)` — 申请号（13 位去末位校验位）
- `AD` / `PD` — 申请日/公开日（range，支持 >=、>、<、<=、=、范围）
- `NOT=(...)` — 排除（must_not）

**示例：**
- 关键词 AND: `低空空域 AND 无人机`
- 关键词 OR: `人工智能 OR 机器学习`
- 申请人限定: `AP=(华为) 5G`
- IPC 领域: `IPC=(H01M) 固态电池`
- 日期范围: `AD>=2020`
- 组合: `AP=(比亚迪) IPC=(H01M) AD>=2020`
- 排除: `固态电池 NOT=(液态)`

响应: `{ total, total_pages, current_page, page_size, has_next, has_prev, patent_list: [...] }`

### 2. 专利详情

**GET** `/v1/patent/{identifier}`

传入公开号或申请号，返回与 Bool 检索相同的 `SearchResponse` 结构，`patent_list` 含 0 或 1 条结果。

### 3. 语义检索（异步任务）

**POST** `/v1/semantic/async`

请求体: `{ "query": "技术描述" }`

并发限制: 同一 Key 最多 3 个并发任务，全局最多 10 个。

响应: `{ task_id, status, type, cache_hit, credits_charged, credits_remaining, created_at, expires_at }`

### 4. 查询任务状态/结果

**GET** `/v1/tasks/{task_id}?include_partial=true|false`

任务状态流转: `pending → running → succeeded | failed | cancelled`

轮询策略:
- 前 10 秒: 每 2 秒
- 10-60 秒: 每 5 秒
- 60 秒后: 每 10 秒

### 5. 取消任务

**DELETE** `/v1/tasks/{task_id}`

响应: `{ task_id, status: "cancelling" }`

### 6. 列出任务历史

**GET** `/v1/tasks?limit=20`

## 专利字段

### Bool 检索字段
pid, appnum, title, ipcs, appdate, pubdate, applicant, abstract, claims, figures, cited_cnt, description

### 语义检索字段
pid, similarity, title, ipcs, appdate, pubdate, applicant, abstract, claims, figures, cited_cnt
（无 appnum 和 description；claims 可能被截断，需用 `/v1/patent/{pid}` 补全）

## 错误码

| HTTP | code | 说明 |
|---|---|---|
| 401 | MISSING_API_KEY | 未提供 Authorization |
| 401 | INVALID_API_KEY | Key 无效 |
| 402 | INSUFFICIENT_CREDITS | 积分不足 |
| 403 | KEY_DISABLED | Key 已禁用 |
| 404 | TASK_NOT_FOUND | 任务不存在 |
| 409 | TASK_ALREADY_TERMINATED | 任务已终止 |
| 429 | TASK_LIMIT_EXCEEDED | 并发超限 |
| 429 | — | 频率限制 |
| 500 | TASK_SUBMIT_FAILED | 任务创建失败 |
| 503 | DB_UNAVAILABLE | 数据库不可用 |
