# 法律数据源 API 配置指南

## 元典开放平台

**官网**: https://open.chineselaw.com/
**活动**: 2026年4月27日至2026年7月26日，每月赠送50,000积分权益包

### 注册与获取 API Key

1. 访问 https://open.chineselaw.com/ 注册账号
2. 登录后进入控制台，创建应用
3. 获取 API Key

### MCP 配置

```json
{
  "mcpServers": {
    "yuandian-mcp-server": {
      "command": "npx",
      "args": ["-y", "yuandian-mcp-server"],
      "env": {
        "YUANDIAN_API_KEY": "你的_api_key"
      }
    }
  }
}
```

### 可用 MCP Tools

| Tool 名称 | 功能 | 分类 |
|-----------|------|------|
| `yuandian_law_vector_search` | 法律法规语义检索 | 法律法规 |
| `yuandian_case_vector_search` | 案例语义检索 | 案例文书 |
| `yuandian_rh_enterpriseSearch` | 企业信息查询 | 企业信息 |
| `yuandian_list_apis` | 查看所有可用接口 | 工具 |
| `yuandian_get_api_document` | 查看接口文档 | 工具 |

### 直接 API 调用

如果不使用 MCP，也可直接调用 REST API：

```python
import requests

# 法律法规语义检索
url = "https://open.chineselaw.com/open/law_vector_search"
headers = {
    "X-API-Key": "你的_api_key",
    "Content-Type": "application/json; charset=utf-8",
}
payload = {
    "query": "入户盗窃",
    "fatiao_filter": {
        "sxx": ["现行有效"],
        "law_start": "2020-01-01",
    },
    "return_num": 20,
}

response = requests.post(url, json=payload, headers=headers, timeout=60)
print(response.json())
```

### 响应格式

```json
{
    "msg": "成功(返回结构化数据)",
    "code": 201,
    "extra": {
        "fatiao": [
            {
                "ftid": "法条ID",
                "fgid": "法规ID",
                "fgtitle": "法规名称",
                "num": "法条编号",
                "content": "法条内容",
                "sxx": "现行有效",
                "effect1": "法律",
                "score": 0.95
            }
        ]
    }
}
```

---

## 北大法宝 MCP

**官网**: https://mcp.pkulaw.com/
**优惠**: 新用户首月免费使用部分服务

### 注册与获取 Token

1. 访问 https://mcp.pkulaw.com/ 注册/登录
2. 进入控制台 → 应用管理 → 创建应用
3. 密钥管理 → 生成 Token
4. MCP服务购买 → 选择需要的服务（新用户免费1月）

### MCP 配置

```json
{
  "mcpServers": {
    "pkulaw-law-search": {
      "type": "streamable-http",
      "streamable": true,
      "url": "https://apim-gateway.pkulaw.com/mcp-law-search-service",
      "headers": {
        "Authorization": "Bearer 你的_access_token"
      }
    },
    "pkulaw-case-search": {
      "type": "streamable-http",
      "streamable": true,
      "url": "https://apim-gateway.pkulaw.com/mcp-case-search-service",
      "headers": {
        "Authorization": "Bearer 你的_access_token"
      }
    }
  }
}
```

### 可用服务

| 服务名称 | 功能 | 月调用量参考 |
|----------|------|------------|
| 检索法律法规-语义 | 自然语言语义检索法规 | 1294万+ |
| 检索法律法规-关键词 | 精确关键词检索法规 | 15万+ |
| 精准查找法条-关键词 | 精确法条号查询 | 14万+ |
| 修正生成幻觉-法条 | AI幻觉法条校正 | 9万+ |
| 法宝超链 | 法律元素自动标引 | 12万+ |
| 法条识别与溯源 | 从文本识别法规 | 10万+ |
| 案号识别与溯源 | 案号精准定位案例 | 643万+ |
| 检索司法案例-关键词 | 关键词检索案例 | 36万+ |
| 检索司法案例-语义 | 自然语言语义检索案例 | 1007万+ |

---

## 数据使用建议

### 场景匹配

| 使用场景 | 推荐数据源 | 推荐方式 |
|----------|-----------|---------|
| 法律法规快速检索 | 元典 | 语义检索 |
| 精确法条查询 | 北大法宝 | 关键词检索 |
| 案号查证 | 北大法宝 | 案号溯源 |
| 案例全文检索 | 北大法宝 | 语义/关键词 |
| 类案批量分析 | 元典+北大法宝 | 双源交叉 |
| AI法条幻觉校正 | 北大法宝 | 修正生成幻觉 |

### 成本控制

- 元典每月5万积分，优先级最高（活动期间）
- 北大法宝新用户首月免费，可配合使用
- 对于高频查询，可按需购买北大法宝付费服务

### 注意事项

1. 中国裁判文书网自2025年起公开文书数量减少，建议多源交叉验证
2. 元典开放平台API返回的是法条级检索结果，非全文法规
3. 需要全文法规时，获取 fgid 后调用法规详情接口
4. 北大法宝Token需妥善保管，泄露可能产生费用
