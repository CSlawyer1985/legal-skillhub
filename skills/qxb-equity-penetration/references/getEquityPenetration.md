# 查询企业股权穿透

## 接口

`getEquityPenetration`

## 描述

查询企业的股权结构，包括直接股东（工商数据源）和间接股东（多层穿透），每个间接股东附带最短路径层级和具体穿透路径。

## 请求路径

`POST /skill/ent/public/enterprise/getEquityPenetration`

## 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ename | string | 否 | 企业名称（与eid二选一） |
| eid | string | 否 | 企业ID（与ename二选一） |

传 ename 时会自动解析为 eid，如果无法精确匹配会自动取搜索结果第一个。

## 返回字段

| 字段 | 类型 | 说明 |
|------|------|------|
| ename | string | 企业名称（实际查询的企业） |

### directShareholders - 直接股东

| 字段 | 类型 | 说明 |
|------|------|------|
| total | number | 直接股东总数（工商数据源） |
| items | array | 直接股东列表，按持股比例排序，最多10个 |
| items[].name | string | 股东名称 |
| items[].stockPercent | string | 持股比例，如 `65.00%`，无数据时为 `-` |

### indirectShareholders - 间接股东

| 字段 | 类型 | 说明 |
|------|------|------|
| total | number | 间接股东总数 |
| items | array | 间接股东列表，最多100个 |
| items[].name | string | 股东名称 |
| items[].stockPercent | string | 持股比例，如 `12.50%`，无数据时为 `-` |
| items[].shortestLevel | number | 最短层级（从目标企业到该股东的最短路径层数） |
| items[].shortestPath | array | 最短路径的具体层级节点列表 |
| items[].shortestPath[].name | string | 路径节点名称（企业或人名） |
| items[].shortestPath[].percent | string | 该节点的持股比例 |

## 示例代码

```typescript
import { createClient } from '../src'

const client = createClient()
const result = await client.getEquityPenetration('深圳市腾讯计算机系统有限公司')

console.log('企业名称:', result.ename)
console.log('直接股东数:', result.directShareholders.total)
for (const s of result.directShareholders.items) {
  console.log(`  ${s.name} - ${s.stockPercent}`)
}

console.log('间接股东数:', result.indirectShareholders.total)
for (const s of result.indirectShareholders.items.slice(0, 5)) {
  console.log(`  ${s.name} - ${s.stockPercent} (${s.shortestLevel}层)`)
}
```

## 返回示例

```json
{
  "status": "1",
  "message": "操作成功",
  "data": {
    "ename": "深圳市某某科技有限公司",
    "directShareholders": {
      "total": 5,
      "items": [
        {
          "name": "张三",
          "stockPercent": "65.00%"
        },
        {
          "name": "深圳市某某投资有限公司",
          "stockPercent": "35.00%"
        }
      ]
    },
    "indirectShareholders": {
      "total": 12,
      "items": [
        {
          "name": "李四",
          "stockPercent": "32.50%",
          "shortestLevel": 2,
          "shortestPath": [
            { "name": "目标企业", "percent": "100%" },
            { "name": "深圳市某某投资有限公司", "percent": "65.00%" },
            { "name": "李四", "percent": "50.00%" }
          ]
        },
        {
          "name": "北京某某集团有限公司",
          "stockPercent": "17.50%",
          "shortestLevel": 3,
          "shortestPath": [
            { "name": "目标企业", "percent": "100%" },
            { "name": "深圳市某某投资有限公司", "percent": "35.00%" },
            { "name": "上海某某控股有限公司", "percent": "60.00%" },
            { "name": "北京某某集团有限公司", "percent": "29.17%" }
          ]
        }
      ]
    }
  }
}
```
