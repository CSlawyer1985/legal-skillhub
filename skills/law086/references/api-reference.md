# 案件云 Open API 参考 (V2.0)

## 目录

- [认证与通用规范](#认证与通用规范)
- [Dashboard](#dashboard)
- [Cases 案件](#cases-案件)
- [Case Files 案件附件](#case-files-案件附件)
- [Calendar 日程](#calendar-日程)
- [Clients 客户](#clients-客户)
- [Records 记录](#records-记录)
- [Projects 项目](#projects-项目)
- [Finance 财务](#finance-财务)
- [Search & Enums 搜索与枚举](#search--enums-搜索与枚举)
- [Contracts 合同](#contracts-合同)
- [V1 兼容说明](#v1-兼容说明)
- [Scope 权限对照表](#scope-权限对照表)

---

## 认证与通用规范

### 请求认证

所有请求在 Header 中携带 PAT Token：

```
Authorization: Bearer {PAT_TOKEN}
```

Token 以 `law086_pat_` 开头，在 OA「个人设置 > AI管理」中生成。

### Base URL

从环境配置读取 `API_BASE_URL`，例如 `https://open.law086.com/api/v1`

### 响应格式

```json
{"code": 0, "msg": "", "data": {...}}
```

| code | 含义 | 处理方式 |
|------|------|----------|
| 0 | 成功 | 读取 data |
| 1 | 业务错误 | 展示 msg |
| 2 | 认证失败 | 提示重新生成 PAT |
| 3 | 权限不足 | 提示重新勾选 scope |

> **重要**: code 为**整数**，前端须用 `==` 宽松比较：`res.code == "0"`。禁止 `===` 严格比较。

### 请求编码

POST/PUT 请求体含中文时，须先写入临时文件再用 `curl -d @file` 发送（避免 Windows GBK 编码问题）。

```bash
echo '{"title":"开庭","htime":"2026-04-15 14:00:00"}' > /tmp/open_req.json
curl -s -X POST "{BASE}/calendar" -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" -d @/tmp/open_req.json
```

### 分页约定

分页接口返回标准 Laravel 分页结构：

| 字段 | 说明 |
|------|------|
| data | 数据列表 |
| current_page | 当前页码 |
| per_page | 每页条数 |
| total | 总条数 |
| last_page | 末页页码 |

### 数据可见范围

| 角色 | 可见范围 |
|------|---------|
| 个人空间本人 | 全部个人数据 |
| 团队/律所管理员或拥有者 | 本 org 下全部数据 |
| 团队/律所普通成员 | 只能看自己参与的数据（RelatedWorker 过滤） |
| 律所拥有者（顶层律所 org + OWNER 角色，全所范围始终开启） | **读 + 写端点均跨子团队**：读端点（GET）全所可见；编辑端点（PATCH/PUT/上传）可操作全所任意记录（保留记录自身 org_id）；新建端点（POST /cases、/clients、/projects、/calendar、/contracts）支持可选请求参数 `org_id`（hashid）把记录归属到本所内任意子团队。 |

> **律所拥有者全所范围（Firm-Scope PAT，始终开启）**：
> - **读端点**：全所可见（顶层律所 + 所有直接子团队 org）。
> - **编辑端点**：owner 可跨子团队编辑/上传任意记录；编辑**不改归属**（保留记录自身 org_id），成员校验用记录自身 org。
> - **新建端点**：`POST /cases`、`POST /clients`、`POST /projects`、`POST /calendar`、`POST /contracts` 支持可选请求参数 `org_id`（hashid）。owner 可指定归属到本所内任意子团队，解码后校验 ∈ 全所集合，不在则报错 `"目标组织不在本所范围"`；未传默认 PAT 绑定 org。
> - **非 owner**（普通成员/团队管理员）PAT 行为零变化：读只看本 org/自己参与；写端点传非自身 org 会报错 `"目标组织不在本所范围"`。
> - owner 角色被撤销后最多 60s 内（子树 Redis 缓存 TTL）收缩为单 org。
> - 组织结构目前仅支持扁平一层（顶层律所 + 直接子团队）；多级团队（律所→部门→小组）递归展开为二期，不在本期支持范围。
> - 跨子团队 host/assit 改派未开放（update 不暴露 host/assit 字段）。

---

## Dashboard

### GET /dashboard - 每日概览

Scope: `dashboard.read`

返回当前用户当日的待办事项、日程、案件统计等摘要信息。

**参数**: 无

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| todo_count | int | 待办事项数 |
| today_records | array | 今日日程列表 |
| case_stats | object | 案件统计（在办/结案/归档数量） |
| unread_count | int | 未读消息数 |

> 注: 具体字段以实际返回为准，该端点为汇总视图。

---

## Cases 案件

### GET /cases - 案件列表

Scope: `cases.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 按案件名称搜索 |
| g_status | int | 否 | 案件状态: 1=在办, 2=结案, 3=归档 |
| type | int | 否 | 案件类型: 1=民事, 2=商事, 3=仲裁, 4=刑事, 5=行政 |
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页条数，默认 20 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 案件 ID（hashid） |
| case_name | string | 案件名称 |
| case_code | string | 案件编号 |
| c_num | string | 内部案号 |
| g_status | int | 状态 (1=在办, 2=结案, 3=归档) |
| type | int | 类型 (1=民事, 2=商事, 3=仲裁, 4=刑事, 5=行政) |
| org_id | int | 组织 ID |
| pr_time | string | 立案日期 |
| stage_text | string | 当前阶段文本 |
| degree | int | 等级 (0=次要, 1=一般, 2=重要) |
| created_at | string | 创建时间 |
| org_name | string | **仅顶层律所 owner（全所范围）返回**，案件所属团队名（来自 `Org.name`）。普通成员/子团队管理员的响应不包含此字段 |

### GET /cases/{code} - 案件详情

Scope: `cases.read`

返回完整案件信息，包含当事人、阶段、受理单位等。路径参数使用 `case_code`（非 id）。

**参数**: 路径参数 `code` = `case_code`（必填）

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 案件 ID（hashid） |
| case_name | string | 案件名称 |
| case_code | string | 案件编号 |
| c_num | string | 内部案号 |
| type | int | 案件类型 |
| g_status | int | 案件状态 |
| anyou | string | 案由 |
| stage_text | string | 当前阶段 |
| pr_time | string | 立案日期 |
| j_time | string | 结案日期 |
| g_time | string | 归档日期 |
| c_amount | decimal | 标的额 |
| w_fee | decimal | 代理费 |
| charge_desc | string | 收费说明 |
| case_mark | string | 案件备注 |
| unit_name | string | 受理单位名称 |
| unit_type | int | 受理单位类型 (1=法院, 2=检察院, 3=公安机关, 4=仲裁机构, 5=调解机构, 6=鉴定机构, 7=行政机构) |
| org_id | int | 组织 ID |
| degree | int | 等级 |
| fee_type | int | 收费类型 (1=定额, 2=风险, 3=计时, 4=计件, 5=免费) |
| process | string | 案件程序 |
| anhao | string | 案号 |
| privyc | array | 当事人列表 |
| privyc[].type | int | 1=委托方(原告), 2=对方(被告) |
| privyc[].name | string | 名称 |
| privyc[].c_type | int | 当事人细类 |
| privyc[].dsr_type | int | 1=个人, 2=单位 |
| privyc[].card_num | string | 证件号码 |
| privyc[].phone | string | 联系电话 |
| privyc[].address | string | 地址 |
| cl_id | string | 关联客户 ID（hashid，可为 null） |
| link_pr | string | 关联项目 ID（hashid，可为 null） |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| org_name | string | **仅顶层律所 owner（全所范围）返回**，案件所属团队名（来自 `Org.name`）。普通成员/子团队管理员的响应不包含此字段 |

### PATCH /cases/{code} - 更新案件

Scope: `cases.write` | **高危操作，需二次确认**

V2 将 V1 的 PUT 改为 PATCH，路径参数使用 `case_code`（明文字符串，非数字 id 也非 hashid）。

> **律所拥有者可跨子团队编辑**：owner 的 PAT 可 PATCH 全所（顶层律所 + 直接子团队 org）任意案件；编辑不改归属（保留案件自身 org_id）。非 owner 只能编辑本 org 且自己参与的案件。

**参数**（仅以下字段可更新，传入其它字段会被静默忽略）:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| process_code | int | 否 | 审理程序代码（只允许 GET /enums 返回的合法值） |
| case_mark | string | 否 | 案件备注（允许清空） |
| anhao | string | 否 | 案号（最大 128 字） |
| degree | int | 否 | 等级: 0=次要, 1=一般, 2=重要（只允许这三个值） |
| charge_desc | string | 否 | 收费描述（最大 100 字，允许清空） |
| current_stage_id | string | 否 | 当前阶段 ID（hashid 编码，必须属于当前案件，切换该阶段为当前活跃阶段） |
| anyou | string | 否 | 案由（最大 64 字） |
| unit_name | string | 否 | 受理单位名称（最大 128 字）⚠️ **必须与 `unit_type` 同时提供** |
| unit_type | int | 否 | 受理单位类型: 1=法院, 2=检察院, 3=公安机关, 4=仲裁机构, 5=调解机构, 6=鉴定机构, 7=行政机构 ⚠️ **必须与 `unit_name` 同时提供** |
| stage_text | string | 否 | 阶段文本（不可传空值，新增或激活该阶段为当前阶段） |

> **不可更新字段**：`status`、`g_status`（结案/归档）、`host`/`assit`（律师团队）、`fee_type` 等属独立业务流程，需在 OA 网页端操作，Open API 不开放。这些字段即使传入也会被忽略。
>
> 至少提供一个字段。更新前须向用户展示变更摘要并确认。`unit_name` 与 `unit_type` 必须同时提供，单独传任一项不会写入。

**响应**: 返回更新后的案件完整数据（同 GET /cases/{code} 的 data 结构）。

### POST /cases - 创建案件

Scope: `cases.write`

创建新案件。走**直接 POST + enums 引导**范式（不走 create-form 两步流程）。创建前应先调用 `GET /enums` 获取枚举字典（取 `case_type` 案件类型、`case_unit_type` 受理单位类型等），并向用户展示人类可读的确认信息后再提交。

> **律所拥有者可跨子团队建案**：owner 的 PAT 传可选请求参数 `org_id`（hashid）可把新案件归属到本所内任意子团队（案件与主办 related_worker 均归属目标 org）；不在全所集合则报错 `"目标组织不在本所范围"`；未传默认归属 PAT 绑定 org。非 owner 传非自身 org 同样报错。

**请求头**:

```
Authorization: Bearer {PAT_TOKEN}
Content-Type: application/json
```

**路径**: `POST /cases`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | int | 是 | 案件类型: 1=民事, 2=商事, 3=仲裁, 4=刑事, 5=行政（只允许这五个值） |
| privyc_data | string | 是 | 当事人 JSON 字符串（见下方子结构表），至少一个对象含非空 `name` |
| case_name | string | 否 | 案件名。留空时系统按当事人"原告名 诉 被告名"自动拼接，识别不出原被告用"类型+日期"兜底 |
| c_num | string | 否 | 内部案号，留空系统自动按组织序号生成 |
| anyou | string | 否 | 案由（最大 64 字） |
| anhao | string | 否 | 案号（最大 128 字） |
| degree | int | 否 | 等级: 0=次要, 1=一般, 2=重要 |
| charge_desc | string | 否 | 收费描述（最大 100 字） |
| c_amount | number | 否 | 标的额（数字） |
| w_fee | number | 否 | 代理费（数字） |
| process_code | int | 否 | 审理程序代码（参考 GET /enums） |
| case_mark | string | 否 | 案件备注 |
| pr_time | string | 否 | 委托时间 (YYYY-MM-DD)，默认当天 |
| stage_text | string | 否 | 初始阶段文本 |
| org_id | string | 否 | **律所拥有者专属**：目标组织 ID（hashid），把新案件归属到本所内任意子团队；不在全所集合则报错「目标组织不在本所范围」；未传默认 PAT 绑定 org。非 owner 只能传自身 org（或不传） |

**`privyc_data` 子结构**（JSON 数组，序列化为字符串传入）:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 至少一个对象非空 | 当事人名称 |
| type | int | 否 | 1=委托方/原告方, 2=对方/被告方（决定自动案件名拼接） |
| short_name | string | 否 | 简称 |
| c_type | int | 否 | 当事人细类 |
| dsr_type | int | 否 | 1=个人, 2=单位 |
| sex | int | 否 | 性别 |
| nation | string | 否 | 民族 |
| card_num | string | 否 | 证件号码 |
| phone | string | 否 | 联系电话 |
| email | string | 否 | 邮箱 |
| address | string | 否 | 地址 |
| legal_man | string | 否 | 法定代表人 |
| mark | string | 否 | 备注 |

> **自动生成（客户端不要传）**：`case_code`、`c_num`（留空时按组织序号生成）、案件名（未传 `case_name` 时拼接）、主办律师 related_worker（自动 = PAT 调用者，使创建后案件对创建人可见）。

**成功响应**:

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "case_code": "aBcDeFgH12345678",
    "c_num": "AJ20260616001",
    "id": "J3GGbB3j",
    "case_name": "张三 诉 李四"
  }
}
```

**错误响应**:

| 错误消息 | 说明 |
|---------|------|
| 案件类型无效，只允许 1-5 | `type` 缺失或不在合法范围 |
| 当事人名称不能为空 | `privyc_data` 为空或所有对象 name 均为空 |
| 案由长度不能超过 64 | `anyou` 超长 |
| 案号长度不能超过 128 | `anhao` 超长 |

> 缺少 `cases.write` scope 时返回 `code:"3"`（权限不足）。

**curl 示例**:

```bash
echo '{"type":1,"privyc_data":"[{\"name\":\"张三\",\"type\":1},{\"name\":\"李四\",\"type\":2}]","anyou":"借款纠纷"}' > /tmp/case_req.json
curl -s -X POST "{BASE}/cases" \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d @/tmp/case_req.json
```

### GET /cases/{code}/stages - 案件阶段列表

Scope: `cases.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 路径参数，case_code |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 阶段 ID（hashid） |
| cid | string | 案件 ID（hashid） |
| name | string | 阶段名称 |
| type | int | 类型 |
| active | int | 是否当前阶段 (1=是) |
| index | int | 排序序号 |

---

## Case Files 案件附件

> 案件附件管理，支持上传、列表和获取文件链接。文件存储在阿里云 OSS。

### POST /cases/{code}/files - 上传文件到案件

Scope: `cases.write`

使用 `multipart/form-data` 上传文件。`file` 字段为必填的文件内容。

> **律所拥有者可跨子团队上传**：owner 的 PAT 可对全所任意案件上传附件（保留案件自身 org_id）。非 owner 只能上传到本 org 且自己参与的案件。

**请求参数** (multipart/form-data):

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 上传的文件 |
| folder_id | int | 否 | 文件夹 ID，默认 0 |
| record_id | int | 否 | 关联记录 ID，默认 0 |

**文件限制**:
- 允许的文件类型: `jpg,jpeg,bmp,png,rar,zip,7z,doc,docx,rtf,txt,xls,xlsx,pdf,mp3,m4a,ppt,pptx,eml,csv`
- 文件大小: 最大 10MB
- 文件名: 最大 128 字符
- 超出限制时返回错误提示，建议到 OA 网页端上传

**成功响应**:

```json
{
  "code": 0,
  "msg": "提交成功",
  "data": {
    "id": "J3GGbB3j",
    "file_name": "合同扫描件",
    "ext": "pdf",
    "save_path": "/uploads/cfile/20260609/abc123.pdf",
    "file_url": "https://law086com.oss-cn-hangzhou.aliyuncs.com/uploads/cfile/20260609/abc123.pdf"
  }
}
```

**错误响应**:

| 错误消息 | 说明 |
|---------|------|
| 案件不存在或无权限访问 | case_code 无效或无权操作该案件 |
| 请选择要上传的文件 | 未提供 file 字段 |
| 文件大小超过10MB限制，请到 OA 网页端上传 | 文件超过 10MB |
| 该文件类型不支持上传，请到 OA 网页端上传 | 扩展名不在白名单中 |
| 文件名称超过128字符限制，请到 OA 网页端上传 | 文件名过长 |

### GET /cases/{code}/files - 案件附件列表

Scope: `cases.read`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| folder_id | int | 否 | 按文件夹筛选 |
| limit | int | 否 | 每页条数，默认 20 |
| page | int | 否 | 页码，默认 1 |

**成功响应**:

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "current_page": 1,
    "data": [
      {
        "id": "J3GGbB3j",
        "file_name": "合同扫描件",
        "ext": "pdf",
        "save_path": "/uploads/cfile/20260609/abc123.pdf",
        "d_uid": "Xk9mN2pL",
        "created_at": "2026-06-09 14:30",
        "file_url": "https://law086com.oss-cn-hangzhou.aliyuncs.com/uploads/cfile/20260609/abc123.pdf"
      }
    ],
    "total": 1,
    "per_page": 20,
    "last_page": 1
  }
}
```

### GET /cases/{code}/files/{fileId}/url - 获取文件访问链接

Scope: `cases.read`

返回文件的访问 URL。`fileId` 为 hashid 编码的文件 ID。

**成功响应**:

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "file_url": "https://law086com.oss-cn-hangzhou.aliyuncs.com/uploads/cfile/20260609/abc123.pdf",
    "file_name": "合同扫描件.pdf",
    "ext": "pdf"
  }
}
```

**错误响应**:

| 错误消息 | 说明 |
|---------|------|
| 案件不存在或无权限访问 | case_code 无效或无权访问 |
| 文件不存在 | fileId 无效或文件不属于该案件 |

---

## Calendar 日程

### GET /team/members - 团队成员列表

Scope: `calendar.read`

返回当前组织下所有有效成员。**个人空间下不可用**（返回错误）。

**参数**: 无

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| uid | string | 成员 UID（hashid 编码，用于 `GET /calendar?uids=` 参数） |
| real_name | string | 成员姓名 |

**响应示例**:
```json
{
  "code": 0,
  "data": [
    {"uid": "aB3xKp", "real_name": "张三"},
    {"uid": "mN9wRq", "real_name": "李四"}
  ]
}
```

### GET /calendar - 日程列表

Scope: `calendar.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 (YYYY-MM-DD) |
| end_date | string | 否 | 结束日期 (YYYY-MM-DD) |
| is_team | int | 否 | 团队视图: 0=个人(默认), 1=团队 |
| uids | string | 否 | 指定团队成员，逗号分隔的 hashid（来自 `GET /team/members` 返回的 uid 字段，如 `aB3xKp,mN9wRq`） |
| type | int | 否 | 关联类型筛选: 0=不关联, 1=案件, 2=项目, 3=客户 |
| linkid | string | 否 | 关联资源 ID（hashid），配合 type 使用，筛选指定案件/项目/客户的记录 |
| hstatus | int | 否 | 状态: 0=待办, 1=已办 |
| keyword | string | 否 | 按标题搜索 |
| limit | int | 否 | 每页条数，默认 20 |

> **注意**: 不要使用 `today=1` 或 `this_week=1` 快捷参数，服务端过滤不精确。应始终用 `start_date`/`end_date` 传入具体日期范围。

**按实体查记录**: 通过 `type`+`linkid` 组合筛选，可查看案件/项目/客户的关联记录：

```bash
# 查案件的办案记录
GET /calendar?type=1&linkid={case_hashid}

# 查项目的关联记录
GET /calendar?type=2&linkid={project_hashid}

# 查客户的关联记录
GET /calendar?type=3&linkid={client_hashid}
```

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 日程 ID（hashid 编码） |
| rcode | string | 日程编码 |
| title | string | 日程标题 |
| content | string | 日程内容 |
| htime | int | 开始时间戳 |
| endtime | int | 结束时间戳（0 表示无结束时间） |
| htime_text | string | 开始时间文本（YYYY-MM-DD HH:mm） |
| endtime_text | string | 结束时间文本 |
| huser | string | 主办人 UID（hashid 编码） |
| huser_text | string | 主办人姓名 |
| assit | string | 协办人 UID 列表（hashid 编码，逗号分隔） |
| assit_text | string | 协办人姓名（逗号分隔） |
| type | int | 关联类型: 0=不关联, 1=案件, 2=项目, 3=客户 |
| type_text | string | 关联类型文本：不关联/案件/项目/客户 |
| linkid | string | 关联资源 ID（hashid 编码） |
| hstatus | int | 状态: 0=待办, 1=已办 |
| hstatus_text | string | 状态文本：待办/已办 |
| time_cost | int | 时间花费（小时，保留1位小数） |
| time_cost_text | string | 时间花费可读格式，如 "1.5小时"、"0小时" |
| case_name | string | 关联案件名称（仅 type=1 时有值） |
| allday | int | 是否全天: 0=否, 1=是 |
| remind_time | string | 提醒时间 |
| repeat_rule | string/json | 重复规则 |
| is_private | int | 是否私密: 0=否, 1=是 |
| add_uid | string | 创建人 UID（hashid 编码） |
| stage | string | 阶段 ID（hashid 编码，0 表示无阶段） |
| created_at | string | 创建时间 |

> **展示建议**: 优先使用 `htime_text`/`endtime_text` 显示时间，`huser_text`/`assit_text` 显示负责人，`type_text`+`case_name` 显示关联信息。这些字段已由后端处理好，无需二次转换。

### POST /calendar - 创建日程

Scope: `calendar.write`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 日程标题（最大 200 字符，不可为空） |
| htime | string | 是 | 开始时间 (YYYY-MM-DD HH:mm) |
| endtime | string | 是 | 结束时间 (YYYY-MM-DD HH:mm)，必须 >= htime |
| content | string | 否 | 日程内容 |
| linkid | string | 否 | 关联案件/项目/客户的 ID（hashid） |
| type | int | 是 | 关联类型: 0=不关联, 1=案件, 2=项目, 3=客户（只允许这四个值） |
| rtype | string | 否 | 工作摘要/分类 |
| time_cost | int | 否 | 时间花费（分钟），必须 >= 0 |
| hstatus | int | 否 | 状态: 0=待办(默认), 1=已办（只允许这两个值） |
| assit | string | 否 | 协办人UID列表，逗号分隔的 hashid（来自 GET /team/members，如 "aB3xKp,mN9wRq"） |
| huser | string | 否 | 主办人 UID（hashid，单人，来自 GET /team/members）。⚠️ **仅律所拥有者可用**，用于"派活/指派主办"场景；非 owner 传入会被忽略（主办人恒为调用者本人）。详见下方「主办人指派规则」 |
| allday | int | 否 | 是否全天: 0=否, 1=是 |
| remind_time | string | 否 | 提醒时间 |
| org_id | string | 否 | **律所拥有者专属**：目标组织 ID（hashid），把新日程归属到本所内任意子团队；不在全所集合则报错「目标组织不在本所范围」；未传默认 PAT 绑定 org。非 owner 只能传自身 org（或不传） |

> **律所拥有者跨子团队关联案件（type=1）**：owner 关联全所内任意子团队的案件时**无需传 `org_id`**，后端会自动把新日程归属到案件所在子团队（待办归属跟随案件）；协办人(assit)校验按案件自身 org（属于案件所在子团队才合法）。非 owner 仍按原严格校验——关联案件必须 ∈ 自身 org，否则报「关联案件不存在或不属于当前组织」。

**主办人指派规则（仅律所拥有者）**：

`POST /calendar` 创建待办/办案记录时，**主办人（`huser`）**默认 = 调用者本人。律所拥有者（顶层律所 org + OWNER 角色）可指定主办人，使被指定的员工成为待办主办并能在「我的待办」中看到。确定优先级（owner 身份下）：

1. 传了 `huser`（hashid，来自 `GET /team/members`）→ 解码并校验属于目标 org 后使用
2. 未传 `huser` 但传了 `assit` → `huser` = `assit` 解码后的第一个员工
3. 都没传 → 回落调用者本人

| 身份/场景 | `huser` 取值 | 说明 |
|-----------|--------------|------|
| 律所拥有者 + 传 `huser` | 传入值（解码+校验后） | 精确指定主办，**推荐用于派活场景**（与 `PUT /calendar/{id}` 行为一致） |
| 律所拥有者 + 未传 `huser` + 传 `assit` | `assit` 第一个员工 | 兜底场景，多人协办时取第一个 |
| 律所拥有者 + 都没传 | 调用者本人 | 兼容现状 |
| 非 owner（普通成员/团队管理员） | 调用者本人（**忽略 `huser` 参数**） | 即使传了 `huser` 也会被丢弃 |
| 个人空间（`org_id=0`） | 调用者本人 | 不允许指定他人 |

> **说明**：
> - `add_uid`（创建人）始终 = 调用者，记录"谁派发的"，不受 `huser` 影响。
> - owner 派活后**不**把 owner 加入 `assit`，仅 `huser=员工`（owner 靠全所视图查看该待办）。
> - 同时传 `huser` 和 `assit` 时，`huser` 参数优先。
> - 指定不属于目标 org 的员工时按现有规则拒绝（与 `assit` 校验一致）。

**响应**: 返回创建的日程数据（含自动生成的 rcode）。

### PUT /calendar/{id} - 更新日程/记录

Scope: `calendar.write`

**这是日程和办案记录的统一更新入口**，支持更新所有字段。`PATCH /records/{id}` 已废弃，所有更新操作统一使用此端点。

> **律所拥有者可跨子团队编辑**：owner 的 PAT 可更新全所任意日程/记录（保留记录自身 org_id）；成员校验按记录自身 org。非 owner 只能更新本 org 且自己参与的记录。
>
> **跨子团队改关联案件（type=1）**：owner 通过 `linkid`+`type:1` 把记录改关联到全所内任意子团队的案件时，记录自身 org_id **保持不变**（不跟随新案件），但后端允许跨子团队建立关联。非 owner 改关联案件仍按原严格校验（目标案件必须 ∈ 记录自身 org）。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 路径参数，日程/记录 ID（hashid） |
| title | string | 否 | 标题（不可传空值） |
| htime | string | 否 | 开始时间（格式必须合法） |
| endtime | string | 否 | 结束时间（必须 >= htime） |
| content | string | 否 | 内容（允许清空） |
| hstatus | int | 否 | 状态: 0=待办, 1=已办（只允许这两个值） |
| time_cost | int | 否 | 时间花费（分钟），必须 >= 0 |
| linkid | string | 否 | 关联资源 ID（hashid） |
| type | int | 否 | 关联类型 |
| huser | string | 否 | 主办人 UID（hashid，单人，来自 GET /team/members），不传则不变。⚠️ 只能指定一个主办人 |
| assit | string | 否 | 协办人UID列表，逗号分隔的 hashid（来自 GET /team/members），传空字符串清空，不传则不变 |
| stage | string | 否 | 案件阶段 ID（hashid，来自 GET /cases/{code}/stages），传空字符串清空 |

> 至少提供一个更新字段。

**响应**: 返回更新后的完整数据（含 `stage_name`、`huser_text`、`assit_text` 等）。

---

## Clients 客户

### GET /clients - 客户列表

Scope: `clients.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 按名称/编号/联系方式搜索 |
| mark | int | 否 | 标识: 1=单位, 2=个人 |
| type | int | 否 | 类型: 1=签约, 2=意向, 3=潜在, 4=终止 |
| degree | int | 否 | 等级: 1=次要, 2=一般, 3=重要, 4=核心 |
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页条数，默认 20 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 客户 ID（hashid） |
| name | string | 客户名称 |
| code | string | 客户编码 |
| c_num | string | 客户编号 |
| mark | int | 标识: 1=单位, 2=个人 |
| type | int | 类型: 1=签约, 2=意向, 3=潜在, 4=终止 |
| degree | int | 等级 |
| contact | string | 联系方式 |
| address | string | 地址 |
| industry | string | 行业 ID（逗号分隔） |
| org_id | int | 组织 ID |
| created_at | string | 创建时间 |

### GET /clients/{code} - 客户详情

Scope: `clients.read`

路径参数使用客户 `code`（非 id）。

**参数**: 路径参数 `code` = 客户编码（必填）

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 客户 ID（hashid） |
| name | string | 客户名称 |
| code | string | 客户编码 |
| c_num | string | 客户编号 |
| mark | int | 标识: 1=单位, 2=个人 |
| type | int | 类型: 1=签约, 2=意向, 3=潜在, 4=终止 |
| degree | int | 等级 |
| contact | string | 联系方式 |
| address | string | 地址 |
| card_num | string | 证件号码 |
| industry | string | 行业 |
| from | int | 来源分类 ID |
| from_text | string | 来源文本 |
| c_start_time | string | 合同起始日期 |
| c_end_time | string | 合同终止日期 |
| org_id | int | 组织 ID |
| created_at | string | 创建时间 |

### GET /clients/{code}/contacts - 客户联系人

Scope: `clients.read`

获取指定客户下的联系人列表。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 路径参数，客户编码 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 联系人 ID |
| name | string | 联系人姓名 |
| mobile | string | 手机号 |
| phone | string | 座机号 |
| email | string | 邮箱 |
| address | string | 地址 |
| position | string | 职位 |
| cl_id | string | 所属客户 ID（hashid） |
| is_default | int | 是否默认联系人 |

### PATCH /clients/{code} - 更新客户

Scope: `clients.write`

> **律所拥有者可跨子团队编辑**：owner 的 PAT 可 PATCH 全所任意客户（保留客户自身 org_id）。非 owner 只能编辑本 org 且自己参与的客户。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 客户名称（不可传空值，最大 200 字） |
| mark | int | 否 | 标识: 1=单位, 2=个人（只允许这两个值） |
| type | int | 否 | 类型: 1=签约, 2=意向, 3=潜在, 4=终止（只允许这四个值） |
| degree | int | 否 | 等级: 1=次要, 2=一般, 3=重要, 4=核心（只允许这四个值） |
| address | string | 否 | 地址（最大 500 字） |
| description | string | 否 | 描述/备注（最大 2000 字） |
| contact | string | 否 | 联系方式（最大 100 字） |
| card_num | string | 否 | 证件号码/统一社会信用代码（最大 50 字） |
| industry | string | 否 | 行业 ID |
| from | int | 否 | 来源分类 ID |
| from_text | string | 否 | 来源文本（最大 100 字） |
| legal_per | string | 否 | 法人代表（单位，最大 50 字） |
| sex | int | 否 | 性别: 0=未知, 1=男, 2=女（只允许这三个值） |
| nation | string | 否 | 民族（个人，最大 30 字） |
| c_start_time | string | 否 | 合同起始日期 |
| c_end_time | string | 否 | 合同终止日期（必须 >= c_start_time） |

**响应**: 返回更新后的客户详情（同 GET /clients/{code}）。

### GET /clients/create-form - 获取客户创建表单 schema

Scope: `clients.write`

返回客户创建所需的完整表单结构，包含枚举选项、行业树、自定义字段定义等。AI 创建客户前必须先调用此端点获取 schema。

**参数**: 无

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| form_schema | object | 表单 schema 定义 |
| form_schema.sections | array | 表单分区列表（3个分区） |

**sections 分区结构**:

1. **basic** - 客户基本信息
   - mark (enum, 必填): 客户标识，1=单位, 2=个人
   - name (string, 必填): 客户名称
   - c_num (string): 客户编号，留空自动生成
   - type (enum, 必填): 合作状态，1=签约, 2=意向, 3=潜在, 4=终止
   - degree (enum): 客户重要性，1=次要, 2=一般, 3=重要, 4=核心
   - industry (cascade): 所属行业（树形结构）
   - from_text (string): 客户来源
   - c_start_time (date): 合同起始时间
   - c_end_time (date): 合同结束时间
   - contact (string): 联系电话
   - description (string): 备注
   - 单位专属字段 (depends_on mark=1): address, legal_per, card_num
   - 个人专属字段 (depends_on mark=2): nation, sex, card_num_personal, address_personal

2. **custom** - 自定义信息
   - custom_tag (multi_select): 分类标签
   - dynamic_fields: 组织自定义字段定义（动态生成）

3. **contacts** - 联系人信息（可多个）
   - name, sex, mobile, email, job, address, remark

### POST /clients - 创建客户

Scope: `clients.write`

创建新客户。创建前应先调用 `GET /clients/create-form` 获取表单 schema 并展示确认信息。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 客户名称 |
| mark | int | 是 | 客户标识: 1=单位, 2=个人 |
| type | int | 否 | 合作状态: 1=签约, 2=意向, 3=潜在, 4=终止 |
| degree | int | 否 | 客户重要性: 1=次要, 2=一般, 3=重要, 4=核心 |
| c_num | string | 否 | 客户编号，留空系统自动生成 |
| industry | string | 否 | 行业 ID（逗号分隔或级联数组） |
| from_text | string | 否 | 客户来源 |
| c_start_time | string | 否 | 合同起始时间 (YYYY-MM-DD) |
| c_end_time | string | 否 | 合同结束时间 (YYYY-MM-DD) |
| contact | string | 否 | 联系电话 |
| description | string | 否 | 备注 |
| address | string | 否 | 地址（单位地址或住所地） |
| legal_per | string | 否 | 法定代表人（单位 mark=1） |
| card_num | string | 否 | 证件号码/统一社会信用代码 |
| sex | int | 否 | 性别: 0=男, 1=女（个人 mark=2） |
| nation | string | 否 | 民族（个人 mark=2） |
| card_num_personal | string | 否 | 证件号码（个人 mark=2，自动映射到 card_num） |
| address_personal | string | 否 | 住所地（个人 mark=2，自动映射到 address） |
| custom_fields | string | 否 | 自定义字段 JSON `{"{id}":"value"}` |
| custom_tag | string/array | 否 | 分类标签 |
| clcontact_data | string | 否 | 联系人 JSON 数组 `[{"name":"xxx","mobile":"xxx"}]` |
| org_id | string | 否 | **律所拥有者专属**：目标组织 ID（hashid），把新客户归属到本所内任意子团队；不在全所集合则报错「目标组织不在本所范围」；未传默认 PAT 绑定 org。非 owner 只能传自身 org（或不传） |

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 新客户 ID（hashid） |
| code | string | 客户编码（用于后续查询） |
| c_num | string | 客户编号 |
| name | string | 客户名称 |

---

## Records 记录

通过记录 ID 直接查询单条记录详情。**所有更新操作已统一到 `PUT /calendar/{id}`**。

### GET /records/{id} - 记录详情

Scope: `records.read`

**参数**: 路径参数 `id` (必填, hashid 编码)

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 记录 ID (hashid) |
| title | string | 标题 |
| content | string | 内容 |
| htime | int | 开始时间（Unix 时间戳） |
| htime_text | string | 开始时间文本 (YYYY-MM-DD HH:mm) |
| endtime | int | 结束时间（Unix 时间戳） |
| endtime_text | string | 结束时间文本 |
| hstatus | int | 状态: 0=待办, 1=已办 |
| hstatus_text | string | 状态文本 |
| type | int | 关联类型: 0=不关联, 1=案件, 2=项目, 3=客户 |
| type_text | string | 关联类型文本 |
| huser | string | 负责人 uid (hashid) |
| huser_text | string | 负责人姓名 |
| assit | string | 协助人 uid 列表 (hashid, 逗号分隔) |
| assit_text | string | 协助人姓名列表 (逗号分隔) |
| time_cost | int | 时间花费（小时，保留1位小数） |
| time_cost_text | string | 时间花费可读格式，如 "1.5小时" |
| linkid | string | 关联 ID (hashid) |
| stage | string | 阶段 ID (hashid) |
| stage_name | string | 阶段名称 |
| creator_name | string | 创建人姓名 |

### PATCH /records/{id} - 更新记录（已废弃）

> **已废弃**，所有更新操作统一使用 `PUT /calendar/{id}`。该端点仍可用但不再迭代新功能。

---

## Projects 项目

### GET /projects - 项目列表

Scope: `projects.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 按项目名称/编号搜索 |
| pr_status | int | 否 | 项目状态: 1=进行中, 2=已结束 |
| pr_type | int | 否 | 项目类型（category ID） |
| degree | int | 否 | 等级: 0=次要, 1=一般, 2=重要 |
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页条数，默认 20 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 项目 ID（hashid） |
| pr_code | string | 项目编号 |
| pr_name | string | 项目名称 |
| pr_status | int | 状态: 1=进行中, 2=已结束 |
| pr_status_text | string | 状态文本 |
| pr_type | int | 项目类型（category ID） |
| pr_type_text | string | 项目类型文本 |
| degree | int | 等级: 0=次要, 1=一般, 2=重要 |
| degree_text | string | 等级文本 |
| start_time | string | 开始时间 |
| end_time | string | 结束时间 |
| client_name | string | 关联客户名称 |
| host_text | string | 负责人姓名 |
| created_at | string | 创建时间 |

### GET /projects/{code} - 项目详情

Scope: `projects.read`

通过 `pr_code` 获取项目详情，包含项目团队、关联客户及联系人。

**参数**: 路径参数 `code` = `pr_code`（必填）

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 项目 ID（hashid） |
| pr_code | string | 项目编号 |
| pr_name | string | 项目名称 |
| pr_status | int | 状态: 1=进行中, 2=已结束 |
| pr_status_text | string | 状态文本 |
| pr_type | int | 项目类型（category ID） |
| pr_type_text | string | 项目类型文本 |
| degree | int | 等级: 0=次要, 1=一般, 2=重要 |
| degree_text | string | 等级文本 |
| start_time | string | 开始时间 |
| end_time | string | 结束时间 |
| stage_text | string | 当前阶段 |
| require_des | string | 需求描述 |
| funding | decimal | 经费 |
| mark | string | 备注 |
| workers | array | 项目团队成员 |
| workers[].uid | string | 成员 UID（hashid） |
| workers[].name | string | 成员姓名 |
| workers[].role | int | 角色ID: 8=负责人, 9=协助人 |
| workers[].role_text | string | 角色文本 |
| client | object | 关联客户信息（含联系人），无关联客户时为 null |
| client.id | string | 客户 ID（hashid） |
| client.code | string | 客户编码 |
| client.name | string | 客户名称 |
| client.contacts | array | 客户联系人列表 |
| created_at | string | 创建时间 |

### PATCH /projects/{code} - 更新项目

Scope: `projects.write`

> **律所拥有者可跨子团队编辑**：owner 的 PAT 可 PATCH 全所任意项目（保留项目自身 org_id）。非 owner 只能编辑本 org 且自己参与的项目。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pr_name | string | 否 | 项目名称（不可传空值，最大 200 字） |
| pr_type | int | 否 | 项目类型（category ID） |
| pr_status | int | 否 | 状态: 1=进行中, 2=已结束（只允许这两个值） |
| start_time | string | 否 | 开始时间 |
| end_time | string | 否 | 结束时间（必须 >= start_time） |
| stage_text | string | 否 | 当前阶段 |
| require_des | string | 否 | 需求描述（最大 2000 字） |
| funding | decimal | 否 | 经费 |
| degree | int | 否 | 等级: 0=次要, 1=一般, 2=重要（只允许这三个值） |
| mark | string | 否 | 备注（最大 500 字） |

> 至少提供一个字段。

**响应**: 返回更新后的项目完整详情。

### GET /projects/create-form - 获取项目创建表单 schema

Scope: `projects.write`

返回项目创建所需的完整表单结构，包含项目类型树、客户列表、自定义字段、收费参数等。AI 创建项目前必须先调用此端点获取 schema。

**参数**: 无

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| form_schema | object | 表单 schema 定义 |
| form_schema.sections | array | 表单分区列表（6个分区） |

**sections 分区结构**:

1. **basic** - 项目基本信息
   - pr_name (string, 必填): 项目名称
   - pr_type (cascade, 必填): 项目类型（树形结构，取最后一级 ID）
   - pr_status (enum, 必填): 项目状态，1=进行中, 2=已结束
   - funding (number, 必填): 项目经费（元）
   - start_time (date): 开始时间，默认今天
   - end_time (date): 结束时间，默认今天+1年
   - stage_text (string): 当前阶段
   - p_num (string): 项目编号，留空自动生成
   - degree (enum): 紧急程度，0=次要, 1=一般, 2=重要
   - mark (string): 备注

2. **custom** - 自定义信息
   - custom_tag (multi_select): 分类标签
   - dynamic_fields: 组织自定义字段定义（动态生成）

3. **client** - 关联客户
   - cl_id (select): 关联已有客户（下拉选项为当前律师的客户列表）

4. **contacts** - 项目联系人（可多个）
   - name, mobile, email, address, remark

5. **fee** - 收费信息
   - fee_type_list (multi_enum): 收费方式（1=定额, 2=风险, 3=计时, 4=计件, 5=免费）
   - c_amount (number): 标的额
   - fee_subject (string): 标的物
   - w_fee (number): 代理费
   - charge_desc (string): 收费简介
   - fee_mark (string): 收费备注
   - charge_data (grouped): 各收费方式的具体参数（JSON 数组）

6. **receivables** - 应收款信息（可多个）
   - title (string): 款项名称
   - r_amount (number): 应收金额
   - r_date (date): 约定收款日期
   - remark (string): 备注

### POST /projects - 创建项目

Scope: `projects.write`

创建新项目。创建前应先调用 `GET /projects/create-form` 获取表单 schema 并展示确认信息。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pr_name | string | 是 | 项目名称 |
| pr_type | int/array | 是 | 项目类型 ID（级联数组自动取最后一级） |
| pr_status | int | 是 | 项目状态: 1=进行中, 2=已结束 |
| funding | number | 是 | 项目经费 |
| start_time | string | 否 | 开始时间 (YYYY-MM-DD)，默认今天 |
| end_time | string | 否 | 结束时间 (YYYY-MM-DD)，默认今天+1年 |
| stage_text | string | 否 | 当前阶段 |
| p_num | string | 否 | 项目编号，留空系统自动生成 |
| degree | int | 否 | 紧急程度: 0=次要, 1=一般, 2=重要 |
| mark | string | 否 | 备注 |
| cl_id | int/string | 否 | 关联客户 ID |
| custom_fields | string | 否 | 自定义字段 JSON |
| custom_tag | string/array | 否 | 分类标签 |
| clcontact_data | string | 否 | 联系人 JSON 数组 |
| charge_data | string | 否 | 收费配置 JSON 数组 |
| receive_data | string | 否 | 应收款 JSON 数组 |
| org_id | string | 否 | **律所拥有者专属**：目标组织 ID（hashid），把新项目归属到本所内任意子团队；不在全所集合则报错「目标组织不在本所范围」；未传默认 PAT 绑定 org。非 owner 只能传自身 org（或不传） |

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 新项目 ID（hashid） |
| pr_code | string | 项目编码（用于后续查询） |
| p_num | string | 项目编号 |
| pr_name | string | 项目名称 |

---

## Finance 财务

> **版本要求**: 高阶版及以上套餐才可使用财务相关接口。

### GET /finance - 财务记录列表

Scope: `finance.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | int | 否 | 状态: 1=待认领, 2=审核中, 3=已通过 |
| charge_type | string | 否 | 收费类型（模糊匹配） |
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页条数，默认 20 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 记录 ID（hashid） |
| org_id | int | 组织 ID |
| status | int | 状态: 1=待认领, 2=审核中, 3=已通过 |
| status_text | string | 状态文本 |
| payer | string | 付款方 |
| to_payer | string | 收款方 |
| amount | decimal | 金额 |
| currency | string | 币种 |
| charge_type | string | 费用类型 |
| check_no | string | 支票号 |
| confirm_uid | string | 确认人 UID（hashid） |
| confirm_uid_text | string | 确认人姓名 |
| sk_date | string | 收款日期 |
| files | array | 关联文件 |

### GET /finance/{id} - 财务记录详情

Scope: `finance.read`

**参数**: 路径参数 `id`（hashid，必填）

**响应**: 返回单条财务记录的完整字段。

### GET /finance/receivables - 应收款列表

Scope: `finance.read`

返回符合条件的全部数据（不分页）。日期筛选范围最长 1 年。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| linktype | string | 否 | 关联类型，逗号分隔: 1=案件, 2=项目, 3=客户（默认全部） |
| linkid | string | 否 | 关联资源 ID（hashid），配合 linktype 使用 |
| receivable_status | string | 否 | 应收款状态，逗号分隔: 1=全部未收回, 2=部分收回, 3=全部收回 |
| title | string | 否 | 款项名称模糊搜索（同 keyword） |
| keyword | string | 否 | 同 title |
| link_keyword | string | 否 | 关联资源名称搜索（案件名/项目名/客户名） |
| amount_ys | string/json | 否 | 应收金额范围 `{"start":0,"end":99999}` |
| sk_uid | string | 否 | 收款人 UID（hashid） |
| yd_time_range | string/json | 否 | 约定收款日期范围 `{"start":"2026-01-01","end":"2026-12-31"}`（最长1年） |
| ss_time_range | string/json | 否 | 实收日期范围 `{"start":"2026-01-01","end":"2026-12-31"}`（最长1年） |
| amount_ss | string/json | 否 | 实收金额范围 `{"start":0,"end":99999}`（仅已收款记录） |

**响应 data 字段**:

```json
{
  "data": [
    {
      "id": "hashid",
      "org_id": "hashid",
      "linktype": 1,
      "linktype_text": "案件",
      "linkid": "hashid",
      "linkid_text": "案件名称",
      "linkid_info": {"name": "案件名称", "code": "CASE001"},
      "title": "律师费",
      "r_amount": "50000.00",
      "status": 1,
      "status_text": "全部未收回",
      "amount_r": 30000,
      "d_amount": "20000.00",
      "actual_amount": 30000,
      "pending_amount": "20000.00",
      "is_overdue": 1,
      "record_list": [
        {
          "id": "hashid",
          "amount": 30000,
          "kp_amount": 0,
          "kp_date": null,
          "r_date": "2026-03-01",
          "date_r": "2026-03-01",
          "uid": 10,
          "uid_text": "张律师",
          "status": 2,
          "status_text": "已收款",
          "title": "律师费【第1笔】",
          "overdue_status": 1
        }
      ]
    }
  ],
  "sum": {
    "r_amount": 50000,
    "actual_amount": 30000,
    "pending_amount": 20000,
    "amount_r": 30000,
    "record_amount": 30000
  }
}
```

### GET /finance/receivables/{id} - 应收款详情

Scope: `finance.read`

**参数**: 路径参数 `id` (必填，hashid)

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 应收款 ID（hashid） |
| linktype | int | 关联类型: 1=案件, 2=项目, 3=客户 |
| linkid | string | 关联资源 ID（hashid） |
| title | string | 款项名称 |
| r_amount | decimal | 应收金额 |
| status_text | string | 状态: 待收款/部分收款/已收完 |
| total_amount | decimal | 应收总额 |
| received_amount | decimal | 已收总额 |
| remaining_amount | decimal | 剩余应收 |
| payment_records | array | 收款记录列表 |
| case_info | object | 案件信息（linktype=1时） |
| client_info | object | 客户信息（linktype=3 或案件关联时） |
| project_info | object | 项目信息（linktype=2时） |

### GET /finance/receiverecord - 收款记录列表

Scope: `finance.read`

返回符合条件的全部数据（不分页）。日期筛选范围最长 1 年。与 OA receiverecord 列表逻辑一致。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| record_status | string | 否 | 收款记录状态，逗号分隔（1=待收款, 2=已收款）。注意：`status` 参数不用于筛选 |
| overdue_status | int | 否 | 过期状态: 1=未过期, 2=已过期 |
| linktype | string | 否 | 关联类型，逗号分隔: 1=案件, 2=项目, 3=客户 |
| uid | int | 否 | 收款人 UID |
| title | string | 否 | 款项名称模糊搜索 |
| link_keyword | string | 否 | 关联资源名称搜索 |
| kp_date | string/json | 否 | 开票日期范围 `{"start":"...","end":"..."}`（最长1年） |
| yd_time_range | string/json | 否 | 约定收款日期范围（最长1年） |
| ss_time_range | string/json | 否 | 实收日期范围（最长1年） |
| amount_ys | string/json | 否 | 应收金额范围 |
| amount_ss | string/json | 否 | 实收金额范围 |
| orderBy | string | 否 | 排序字段，默认 `date_r desc` |

> **参数说明**: `record_status` 筛选收款记录状态（receiverecord.status）；应收款状态请使用 `receivable_status`。`status` 参数在此端点不参与筛选。

**响应 data 字段**:

```json
{
  "data": [
    {
      "id": "hashid",
      "receivable_id": "hashid",
      "linkid": "hashid",
      "linktype": 1,
      "linktype_text": "案件",
      "linkid_text": "案件名称",
      "linkid_code": "CASE001",
      "title": "律师费【第1笔】",
      "amount": 30000,
      "kp_amount": 0,
      "kp_date": null,
      "r_date": "2026-03-01",
      "date_r": "2026-03-01",
      "uid": 10,
      "uid_text": "张律师",
      "status": 2,
      "status_text": "已收款",
      "overdue_status": 1,
      "remark": "",
      "amount_r": 30000,
      "d_amount": 20000,
      "receivable_actual_amount": 30000,
      "receivable_pending_amount": 20000,
      "record_actual_amount": 30000,
      "record_pending_amount": 0,
      "firm_apply": {
        "fbid_code": 0,
        "fbid_status": 0,
        "fbid_status_text": "-",
        "frid_status": 0,
        "frid_status_text": "-"
      }
    }
  ],
  "sum": {
    "r_amount": 50000,
    "amount_r": 30000,
    "d_amount": 20000,
    "actual_amount": 30000,
    "pending_amount": 20000
  }
}
```

### GET /finance/receiverecord/{id} - 收款记录详情

Scope: `finance.read`

**参数**: 路径参数 `id` (必填，hashid)

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 记录 ID（hashid） |
| linkid | string | 应收款 ID（hashid） |
| amount | decimal | 收款金额 |
| kp_amount | decimal | 开票金额 |
| kp_date | string | 开票日期 |
| r_date | string | 约定收款日期 |
| date_r | string | 实际收款日期 |
| uid | int | 收款人 UID |
| status | int | 状态 |
| status_text | string | 状态文本 |
| overdue_status | int | 过期状态: 1=未过期, 2=已过期 |
| remark | string | 备注 |
| receivable_title | string | 所属应收款项名称 |
| r_amount | decimal | 所属应收款总额 |
| link_info | object | 关联资源信息（案件/项目/客户） |

### PUT /finance/receiverecord/{id} - 更新收款记录

Scope: `finance.write`

> **注意**：该端点目前**不跨子团队**——按记录父级 receivable 的 org_id 与 PAT 主 org_id 等值校验。律所拥有者也只能更新本 org（PAT 绑定 org）下的收款记录；跨子团队编辑为二期。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 路径参数，记录 ID（hashid） |
| amount | decimal | 否 | 收款金额 |
| kp_amount | decimal | 否 | 开票金额 |
| kp_date | string | 否 | 开票日期（传空清空） |
| r_date | string | 否 | 约定收款日期（传空清空） |
| date_r | string | 否 | 实际收款日期（有值自动设为已收款，无值自动设为待收款） |
| uid | int | 否 | 收款人 |
| remark | string | 否 | 备注 |
| status | int | 否 | 状态（不传时由 date_r 自动推断） |

> 至少提供一个字段。更新后自动同步父表应收款的计算字段。

### GET /finance/summary - 财务摘要

Scope: `finance.read`

返回当前组织维度的财务汇总数据。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 `YYYY-MM-DD` |
| end_date | string | 否 | 结束日期 `YYYY-MM-DD` |
| case_id | int | 否 | 按案件筛选 |

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| total_receivable | decimal | 应收总额 |
| total_received | decimal | 已收总额 |
| total_expense | decimal | 支出总额 |
| total_receivable_remaining | decimal | 剩余应收 |
| by_status | object | 按状态分组: pending/partial/paid 各含 count 和 amount |
| by_case | array | 案件应收 Top 10（含 case_id, case_name, total_amount, received_amount, remaining_amount） |
| by_month | array | 近6个月收款趋势（含 month 和 amount） |

---

## Search & Enums 搜索与枚举

### GET /search - 统一搜索

Scope: `cases.read`

跨资源搜索案件名称、当事人、案号等。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| type | string | 否 | 搜索范围: case=案件(默认), client=客户, all=全部 |
| limit | int | 否 | 返回条数，默认 10 |

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| cases | array | 匹配的案件列表（含 id, case_name, type, g_status） |
| clients | array | 匹配的客户列表（含 id, name, mark） |

### GET /enums - 枚举数据字典

Scope: 任意已授权 scope

返回系统中所有枚举定义，供客户端缓存使用。

**参数**: 无

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| case_type | object | 案件类型: {1:"民事案件", 2:"商事案件", 3:"仲裁案件", 4:"刑事案件", 5:"行政案件"} |
| case_g_status | object | 案件状态: {1:"在办", 2:"结案", 3:"归档"} |
| case_fee_type | object | 收费类型: {1:"定额收费", 2:"风险收费", 3:"计时收费", 4:"计件收费", 5:"免费"} |
| case_unit_type | object | 受理单位: {1:"法院", 2:"检察院", 3:"公安机关", 4:"仲裁机构", 5:"调解机构", 6:"鉴定机构", 7:"行政机构"} |
| case_degree | object | 案件等级: {0:"次要", 1:"一般", 2:"重要"} |
| case_ja_status | object | 结案状态: {0:"其它", 1:"达成诉求", 2:"部分达成诉求", 3:"未达成诉求", 4:"未委托", 5:"终止委托"} |
| record_type | object | 记录关联类型: {0:"不关联", 1:"案件", 2:"项目", 3:"客户"} |
| record_hstatus | object | 记录状态: {0:"待办", 1:"已办"} |
| client_mark | object | 客户标识: {1:"单位", 2:"个人"} |
| client_type | object | 客户类型: {1:"签约", 2:"意向", 3:"潜在", 4:"终止"} |
| client_degree | object | 客户等级: {1:"次要", 2:"一般", 3:"重要", 4:"核心"} |
| finance_status | object | 财务状态: {1:"待认领", 2:"审核中", 3:"已通过"} |
| receivable_type | object | 应收类型: {1:"合同律师费", 2:"计量收费", 3:"风险收费", 4:"代付费用", 5:"协商增收"} |

---

## Contracts 合同

### GET /contracts - 合同列表

Scope: `contracts.read`

返回当前用户有权查看的所有合同（不分页，全量返回）。

**数据权限**：
- **普通员工**：返回自己跟进的客户或项目关联的合同（通过 RelatedWorker）
- **管理员**：返回组织下所有合同；支持 `follow_uid` 指定跟进人筛选
- **律所拥有者（顶层律所 org + OWNER 角色，全所范围始终开启）**：返回范围展开为「顶层律所 + 所有直接子团队 org」下的全部合同（扁平一层）；跨子团队合同的客户/项目姓名解析仍遵循 CM-1（按 `member_role.org_id` 维度过滤）。详见「认证与通用规范 > 数据可见范围」。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| client_keyword | string | 否 | 按关联客户名称搜索（用户明确提到"客户"时使用） |
| project_keyword | string | 否 | 按关联项目名称搜索（用户明确提到"项目"时使用） |
| keyword | string | 否 | 模糊搜索（同时匹配客户名称和项目名称，不确定是客户还是项目时使用） |
| follow_uid | string | 否 | 指定跟进人筛选（hashid，仅管理员可用，传入后按该员工的客户/项目过滤） |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 合同 ID（hashid） |
| code | string | 合同编码 |
| title | string | 合同名称 |
| amount | number | 合同金额（元），可能为 null |
| num | string | 合同编号 |
| part_a | string | 签约甲方 |
| part_b | string | 签约乙方 |
| sign_at | string | 起始日期 |
| sign_at_text | string | 起始日期（YYYY-MM-DD） |
| end_time | string | 终止日期 |
| end_time_text | string | 终止日期（YYYY-MM-DD） |
| cp_content | string | 合作内容 |
| fee_terms | string | 重要条款 |
| status | int | 合作状态: 1=未执行, 2=履行中, 3=已终止 |
| status_text | string | 状态文本 |
| period | int | 合同期限（年） |
| is_extend | int | 是否自动延期 |
| extend_at | string | 自动延期期限 |
| cl_id | string | 关联客户 ID（hashid） |
| pr_id | string | 关联项目 ID（hashid） |
| case_id | string | 关联案件 ID（hashid） |
| add_uid | string | 创建者 ID（hashid） |
| client | object | 关联客户信息（id/code/name），可能为 null |
| project | object | 关联项目信息（id/pr_code/name），可能为 null |

**示例请求**:

```bash
# 查看所有合同
GET /contracts

# 模糊搜索（不确定是客户还是项目）
GET "/contracts?keyword=华为"

# 明确按客户名称搜索
GET "/contracts?client_keyword=华为"

# 明确按项目名称搜索
GET "/contracts?project_keyword=建筑工程"

# 管理员按跟进人筛选
GET "/contracts?follow_uid=J3GGbB3j"
```

**示例响应**:

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "id": "abc123",
      "code": "aBcDeFgH12345678",
      "title": "法律服务委托合同",
      "amount": 50000,
      "status": 2,
      "status_text": "履行中",
      "sign_at_text": "2024-01-15",
      "end_time_text": "2025-01-15",
      "cp_content": "提供法律顾问服务",
      "client": {"id": "xyz789", "code": "cL12345678", "name": "某某公司"},
      "project": null
    }
  ]
}
```

---

### POST /contracts - 创建合同

Scope: `contracts.write`

创建一份新合同。`cl_id` 和 `pr_id` 至少填一个。所有 ID 支持 hashid 或数字格式。

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 合同名称（最长 128 字） |
| cl_id | string | 条件必填 | 关联客户 ID（与 pr_id 至少填一个） |
| pr_id | string | 条件必填 | 关联项目 ID（与 cl_id 至少填一个） |
| case_id | string | 否 | 关联案件 ID |
| num | string | 否 | 合同编号 |
| part_a | string | 否 | 签约甲方 |
| part_b | string | 否 | 签约乙方 |
| amount | number | 否 | 合同金额（元） |
| cp_content | string | 否 | 合作内容 |
| fee_terms | string | 否 | 重要条款 |
| sign_at | string | 否 | 起始日期（YYYY-MM-DD） |
| end_time | string | 否 | 终止日期（YYYY-MM-DD） |
| period | int | 否 | 合同期限（年） |
| status | int | 否 | 合作状态: 1=未执行, 2=履行中, 3=已终止 |
| is_extend | int | 否 | 是否自动延期 |
| extend_at | string | 否 | 自动延期期限 |
| org_id | string | 否 | **律所拥有者专属**：目标组织 ID（hashid），把新合同归属到本所内任意子团队；不在全所集合则报错「目标组织不在本所范围」；未传默认 PAT 绑定 org。非 owner 只能传自身 org（或不传） |

**归属校验**：普通员工只能关联自己跟进的客户/项目，管理员只能关联本组织的客户/项目。律所拥有者可关联全所内任意子团队的客户/项目。

**示例请求**:

```bash
POST /contracts
{
  "title": "法律服务委托合同",
  "cl_id": "xyz789",
  "amount": 50000,
  "part_a": "某某公司",
  "sign_at": "2024-01-15",
  "end_time": "2025-01-15",
  "status": 2
}
```

**示例响应**:

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "id": "abc123",
    "code": "aBcDeFgH12345678",
    "title": "法律服务委托合同"
  }
}
```

---

### PATCH /contracts/{code} - 更新合同

Scope: `contracts.write`

更新指定合同的部分字段。路径参数使用合同 `code`（非 id）。

**数据权限**：普通员工只能更新自己跟进的客户/项目关联的合同，管理员可更新组织下所有合同。**律所拥有者可跨子团队编辑**全所任意合同（保留合同自身 org_id；变更 cl_id/pr_id 时新客户/项目必须 ∈ 全所集合）。

**请求参数**（均可选，支持部分更新）:

| 参数 | 类型 | 说明 |
|------|------|------|
| title | string | 合同名称（不可清空） |
| cl_id | string | 关联客户 ID（传空字符串清空） |
| pr_id | string | 关联项目 ID（传空字符串清空） |
| case_id | string | 关联案件 ID（传空字符串清空） |
| num | string | 合同编号 |
| part_a | string | 签约甲方 |
| part_b | string | 签约乙方 |
| amount | number | 合同金额 |
| cp_content | string | 合作内容 |
| fee_terms | string | 重要条款 |
| sign_at | string | 起始日期 |
| end_time | string | 终止日期 |
| period | int | 合同期限 |
| status | int | 合作状态: 1, 2, 3 |
| is_extend | int | 是否自动延期 |
| extend_at | string | 自动延期期限 |

**归属校验**：变更 cl_id/pr_id 时会校验新客户/项目的归属权。

**示例请求**:

```bash
PATCH /contracts/aBcDeFgH12345678
{
  "status": 3,
  "amount": 60000
}
```

**示例响应**:

```json
{
  "code": 0,
  "msg": "更新成功",
  "data": null
}
```

---

## V1 兼容说明

### 端点变更

| V1 | V2 | 变化 |
|----|----|------|
| PUT /cases/{id} | PATCH /cases/{id} | 方法改为 PATCH |
| GET /calendar | GET /calendar | 新增 isTeam 团队视图参数 |
| POST /calendar | POST /calendar | 无变化 |
| POST /documents/generate | (保留) | V2 不再迭代，仍可用 |

### Scope 变更

| V1 Scope | V2 Scope | 说明 |
|----------|----------|------|
| cases.read | cases.read | 无变化 |
| cases.write | cases.write | 无变化 |
| calendar.sync | calendar.read + calendar.write | 拆分为读写两个 |
| documents.generate | documents.generate | 保留，V2 不迭代 |
| finance.read | finance.read | 无变化 |
| (新增) | clients.read | V2 新增 |
| (新增) | clients.write | V2 新增 |
| (新增) | projects.read | V2 新增 |
| (新增) | projects.write | V2 新增 |
| (新增) | dashboard.read | V2 新增 |

> 旧 `calendar.sync` 等效于同时拥有 `calendar.read` + `calendar.write`。

### V2 新增端点

- GET /dashboard
- GET /team/members (团队成员列表)
- POST /cases (创建案件)
- PATCH /cases/{id} (替代 PUT)
- GET /cases/{id}/stages
- PUT /calendar/{id}
- DELETE /calendar/{id}
- GET /clients
- GET /clients/{id}
- GET /clients/{id}/contacts
- GET /clients/create-form
- POST /clients
- GET /projects
- GET /projects/{code}
- GET /projects/create-form
- POST /projects
- PATCH /projects/{code}
- GET /finance/receivables
- GET /finance/receivables/{id}
- GET /finance/receiverecord
- GET /finance/receiverecord/{id}
- PUT /finance/receiverecord/{id}
- GET /finance/summary
- GET /search
- GET /enums

---

## Scope 权限对照表

| Scope | 说明 | 涉及端点 |
|-------|------|----------|
| cases.read | 查看案件列表、详情、搜索 | GET /cases, GET /cases/{id}, GET /cases/{id}/stages, GET /search |
| cases.write | 创建、更新案件 | POST /cases, PATCH /cases/{id} |
| calendar.read | 查看日程和团队成员 | GET /team/members, GET /calendar |
| calendar.write | 创建/更新/日程 | POST /calendar, PUT /calendar/{id}, DELETE /calendar/{id} |
| clients.read | 查看客户信息和联系人 | GET /clients, GET /clients/{id}, GET /clients/{id}/contacts |
| clients.write | 更新客户信息、创建客户 | PATCH /clients/{id}, GET /clients/create-form, POST /clients |
| projects.read | 查看项目列表和详情 | GET /projects, GET /projects/{code} |
| projects.write | 更新项目信息、创建项目 | PATCH /projects/{code}, GET /projects/create-form, POST /projects |
| finance.read | 查看财务记录和摘要 | GET /finance, GET /finance/{id}, GET /finance/receivables, GET /finance/receivables/{id}, GET /finance/receiverecord, GET /finance/receiverecord/{id}, GET /finance/summary |
| finance.write | 更新收款记录 | PUT /finance/receiverecord/{id} |
| dashboard.read | 每日概览 | GET /dashboard |
| documents.generate | 生成文书模板 | POST /documents/generate (V1 保留) |
| contracts.read | 查看合同列表 | GET /contracts |
| contracts.write | 创建、更新合同 | POST /contracts, PATCH /contracts/{code} |
