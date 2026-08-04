# 元典开放平台 - 根据企业名称 / 股票简称查询企业详情

> 接口文档来源：https://open.chineselaw.com/api-square/14
> 集成版本：v26.4.25.2039

---

## 1. 接口要点

| 项 | 值 |
|---|---|
| HTTP Method | `GET` |
| 正式 URL | `https://open.chineselaw.com/open/rh_company_info` |
| 备用 URL（文档示例） | `/legal-insight/service/app/dify/company/companyInfo` |
| 鉴权 | Header `X-API-Key: <key>` |
| 入参 | `name`（必填，企业名称/曾用名/股票简称）+ `num`（可选） |
| `num` 规则 | 默认 `2`；`<0` 或 `>50` 时后端置为 `10` |
| 计费 | **10 积分/次** |
| 返回 | `data` 为**列表**，每条 schema 同 `company-detail` |

> ⚠️ 文档 §5 示例 URL 与 §2 不一致；客户端默认用 §2，§2 已实测可用（参 detail 接口经验）。

## 2. 与 `company-detail` 的关系

| 维度 | `company-detail` | `company-info`（本接口） |
|------|-----------------|-------------------------|
| 入参 | `id` 或 `tyshxydm`（精确） | `name`（模糊） |
| 返回 | 单条 | 列表（最多 50 条） |
| 字段 schema | 全中文 key | **完全相同** |
| 适用 | 已确认目标企业的精准查询 | 名称起步、重名核验、股票简称查询 |
| 单价 | 10 积分 / 1 家 | 10 积分 / 最多 50 家 |

**两个接口不互斥**：
- 名称起步流程：先 `company-info` → 人工选定 USCC → （可选）再 `company-detail` 复核
- 唯一命中且已锁定目标时，直接消费 `company-info` 返回的详情即可，不必再调 detail

## 3. 客户端调用

```bash
export CHINESELAW_API_KEY=xxxxxxxx

# 仅按名称
python3 scripts/chineselaw_client.py company-info \
    --name "北京华宇元典信息服务有限公司" \
    --output <项目>/raw/chineselaw/

# 指定候选数
python3 scripts/chineselaw_client.py company-info \
    --name "华宇软件" --num 10 \
    --output <项目>/raw/chineselaw/ --yes
```

## 4. 返回结构

### 4.1 顶层

```json
{
  "status": "success" | "notFound",
  "code": 200 | 201 | 404,
  "message": "...",
  "data": [ {...}, {...} ] | null
}
```

成功判定：`status == "success"` 且 `code in (200, 201)` 且 `len(data) >= 1`。

### 4.2 `data[i]`

每条对象的字段与 `company-detail` 的 `data` **完全一致**（基础标识、工商登记、人员、股东、变更、知识产权、涉诉、风险等），详见 [company-detail.md](company-detail.md) §3.2。

## 5. 在 skill 工作流中的角色

### 5.1 init 阶段（推荐入口）

| 律师已知信息 | 推荐路径 | 说明 |
|------------|---------|------|
| 企业全称 + USCC | `init --uscc XXX` → `company-detail` | 最精准，单价最低（按"目标"算） |
| 仅企业全称 | `init --name-lookup` → `company-info` | 自动列候选 |
| 仅股票简称 | `init --name-lookup --target "华宇软件"` | 同上 |
| 名称模糊 | `chineselaw_client.py company-info --num 10` 多次试 | 增大 `num` |

### 5.2 重名处理流程（核心价值）

1. `init --name-lookup` 拉回 N 条候选
2. 客户端打印每条的：`企业名称 / 统一社会信用代码 / 法定代表人 / 成立日期 / 经营状态 / 注册地址 / 企业类型 / 注册资本`
3. 律师人工辨认目标（关键依据：注册地址、法人姓名、成立日期）
4. 选定后：
   - 在 `project-info.md` 中**手工写入** USCC
   - 或重跑：`init --uscc <选定的 USCC>`（覆盖 init 时也可以加 `--skip-api` 避免再扣 10 积分）
5. 若候选中**无目标企业**，可能原因：
   - 名称不准 → 换"曾用名"或"股票简称"再试
   - 元典库未收录 → 在 §1.6 律师备忘记录"元典库未命中"，转手工查询国家企业信用信息公示系统

### 5.3 写入底稿规范

由 `company-info` 取得的数据，引用模板与 detail 接口**相同**（见 [company-detail.md](company-detail.md) §5），但需在段首额外注明检索方式：

> 经查阅元典开放平台「企业名称检索」接口（检索词：「XXX」，命中 N 条候选，本所律师选定其中第 K 条作为目标企业；调用时间 YYYY-MM-DD HH:MM，原始数据见 `raw/chineselaw/company-info-XXX-<ts>.json`），目标公司基本工商登记信息如下：……

**多条候选未选定时**，禁止直接将列表第 1 条写入底稿。

## 6. 失败与降级

参见 [company-detail.md](company-detail.md) §6，规则相同。补充：

- `data == []`（成功但 0 命中）：实际上文档将其归入 `notFound`（`code=404`），但客户端仍按"未命中"处理
- 多次调用同一名称变体：每次都会扣 10 积分，建议先用较大 `num`（如 10）一次取够候选

## 7. 实测踩坑（v26.4.25.2039 联调）

| 现象 | 复现条件 | 处理 |
|------|---------|------|
| `code=500 status=failed`，无 message | 检索词过短/过宽（如单纯"华宇"） | 后端拒绝模糊词；务必使用至少 4 字以上、含行业/地域识别度的名称 |
| 股票简称可直接命中 | `name="华宇软件"` 命中"北京华宇软件股份有限公司" | 上市公司可用简称起步，省去查全称的步骤 |
| `data` 一直只返 1 条 | 即使 `num=10` 且名称含同名歧义 | 实测元典对"主体匹配度"做了过滤；若需更广候选，建议用关键词组合多次调用 |
| 计费按调用次数计 | 即便 `data == []` 或 500 错误 | 503/500 是否扣费**未确认**，谨慎多试 |
| **company-detail：USCC 含大写 X 时 500** | 例：`9144010135580012X4` → 500；改 `x` → 正常 404 | **传入前统一 `.lower()` USCC 末位**，或对 500 做"大小写自动 fallback"重试。见 §8 |

## 8. 元典数据覆盖局限

实战中发现，并非所有合法企业都在元典库内：

- **新设立 / 地方小微企业**可能尚未进入元典爬取范围
- **已注销企业**仍可能保留在库（如"广州三头六臂商贸有限公司"虽注销也命中）
- **与主名相似但行业差异大的企业**可能漏收（如"广东三头六臂信息科技有限公司"未命中，但同地区"广州三头六臂文化传媒"命中）

**降级建议**：当 `company-info` 返回未找到 / `company-detail` 在已校正大小写后仍 404 时，应：

1. 在 `project-info.md` 的"数据可获取性"段记录"元典库未收录"
2. 转手工查询国家企业信用信息公示系统（https://www.gsxt.gov.cn）
3. 仍按 skill 工作流推进，但第 1/3/4 章数据均需通过原始证照人工录入
