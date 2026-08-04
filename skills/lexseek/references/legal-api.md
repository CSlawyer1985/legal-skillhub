# 法律 API 接口

本 Skill 通过调用外部法律 API 获取数据。

## 基础信息

- **Base URL**: 通过环境变量 `LEXSEEK_API_URL` 配置（默认：https://api.lexseek.cn）
- **认证方式**: API Key，通过 Header `apikey` 传递

## 法条查询接口

**接口**: `POST /api/v1/skills/search-law`

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| query | string | 否 | 向量搜索关键词（**应使用关键词分割，不是长句**） |
| k | number | 否 | 返回结果数量限制，默认 10 |
| legalId | string | 否 | 法律 ID |
| legalName | string | 否 | 法律名称（如"中华人民共和国民法典"） |
| articleType | string | 否 | 条文类型（l1, l2, l3, l4, l5） |
| page | number | 否 | 分页页码 |
| isEffective | boolean | 否 | 是否只返回有效条文 |
| invalidDateFilter | object | 否 | 失效日期过滤 |
| publishDateFilter | object | 否 | 发布日期过滤 |
| effectiveDateFilter | object | 否 | 生效日期过滤 |

**重要提示**:
- `query` 参数应该使用关键词分割，例如：`'合同法 违约责任 损失赔偿'`，而不是使用长句搜索
- 关键词之间用空格分隔

### articleType 参数说明

| 值 | 说明 |
|----|------|
| l1 | 编 |
| l2 | 分编 |
| l3 | 章 |
| l4 | 节 |
| l5 | 条 |

## 搜索脚本用法

### 基础用法

```bash
cd lexseek

# 向量搜索（使用关键词，不是长句）
node scripts/lexseek.js search --query "劳动合同 解除 补偿"

# 指定返回数量
node scripts/lexseek.js search --query "合同违约" --k 5

# 只返回有效条文
node scripts/lexseek.js search --query "婚姻法" --is-effective
```

### 高级用法

```bash
# 法律名称过滤
node scripts/lexseek.js search --query "工伤" --legal-name "中华人民共和国劳动合同法"

# 法律 ID 过滤
node scripts/lexseek.js search --query "赔偿" --legal-id "law_001"

# 条文类型过滤 (l1=编, l2=章, l3=节, l4=条, l5=款)
node scripts/lexseek.js search --query "合同" --article-type l5

# 语义搜索关键词（空格分隔）
node scripts/lexseek.js search --query "违约金 损害赔偿"

# 分页查询
node scripts/lexseek.js search --query "民事" --page 2 --k 10
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--query` | 向量搜索关键词（应使用关键词分割，不是长句） | `--query "劳动合同 解除 补偿"` |
| `--k` | 返回结果数量 | `--k 5` |
| `--legal-name` | 法律名称过滤 | `--legal-name "中华人民共和国民法典"` |
| `--legal-id` | 法律 ID 过滤 | `--legal-id "law_001"` |
| `--article-type` | 条文类型 (l1, l2, l3, l4, l5) | `--article-type l4` |
| `--page` | 分页页码 | `--page 2` |
| `--is-effective` | 只返回有效条文 | `--is-effective` |

## 错误响应

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMS",
    "message": "参数错误"
  }
}
```

## 通用错误码

| 错误码 | 说明 |
|--------|------|
| INVALID_PARAMS | 参数错误 |
| UNAUTHORIZED | 未授权 |
| NOT_FOUND | 资源不存在 |
| SERVER_ERROR | 服务器内部错误 |
