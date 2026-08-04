# 全球企业库股东列表 API 参考

> 根据公司ID获取公司的股东信息。
> 接口路径：`POST /agent/search/depth_company/company/shareholder/list`

## python脚本参数

- `--pid`：公司ID（必填），如 `US_12345`

## API请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pid | string | 是 | 公司ID |

## 响应数据

### 外层结构

- code（integer）：响应码，0 表示成功
- msg（string）：响应消息
- data：股东列表数据（见下）
- fee：计费信息（apiCost 本次扣费、accountBalance 账户余额、uuid 调用标识）

### data 字段

- total（integer）：股东总数
- list（array）：股东列表

### list 股东字段

- pid（string）：公司ID
- shareholderId（string）：股东ID
- shareholderName（string）：股东名称
- shareholderType（integer）：股东类型
- shareholderDirect（string）：持股方式（如 "direct"）
- shareholderTotal（string）：持股比例（如 "60.00%"）
