# 法律 MCP 配置指南

> 本集群技能依赖华宇元典和北大法宝两个法律数据MCP实现双源核验。
> 以下是不同平台的配置方法。


### 离线法规库

当MCP服务全部不可用时，可使用  目录下的离线法规库作为参考。
该库收录了社区法律服务最高频引用的核心法规节选（民法典、劳动合同法、刑事诉讼法等），
标注了提取日期和官方来源链接。

> ⚠️ 离线法规库可能不是最新版本，使用前请通过国家法律法规数据库核验。

---

## 一、需要配置的MCP服务

| MCP服务 | 用途 | 配置方式 |
|---------|------|---------|
| **北大法宝（pkulaw）** | 法规原文查询 + 司法案例检索 + 法条精确查询 | OAuth自动 / API Key手动 |
| **华宇元典（yuandian）** | 法规向量检索 + 案例语义检索 + 企业司法风险扫描 | API Key手动 |

---

## 二、各平台配置方法

### 方案A：WorkBuddy（法律元力平台）

**北大法宝** — OAuth自动授权，无需手动填Key：
1. WorkBuddy → 连接器管理 → 搜索「北大法宝」
2. 点击连接，浏览器跳转  登录
3. 用 [mcp.pkulaw.com](https://mcp.pkulaw.com) 账号授权
4. 授权完成后连接器状态变为「已连接」

**华宇元典** — 需申请API Key后手动配置：
1. 访问 [open.chineselaw.com](https://open.chineselaw.com) 注册并获取API Key
2. WorkBuddy → 连接器管理 → 搜索「华宇元典」→ 连接
3. 或手动写入 （见方案C）

### 方案B：Hermes Agent

在  中配置：

```yaml
mcp_servers:
  pkulaw:
    type: http
    url: https://apim-gateway.pkulaw.com/mcp-law-search-service
    headers:
      Content-Type: application/json
      Authorization: Bearer <PLACEHOLDER_北大法宝_Token>

  yuandian-law:
    type: http
    url: https://open.chineselaw.com/mcp/law/stream
    headers:
      Content-Type: application/json
      Authorization: Bearer <PLACEHOLDER_元典_API_KEY>

  yuandian-case:
    type: http
    url: https://open.chineselaw.com/mcp/case/stream
    headers:
      Content-Type: application/json
      Authorization: Bearer <PLACEHOLDER_元典_API_KEY>

  yuandian-company:
    type: http
    url: https://open.chineselaw.com/mcp/company/stream
    headers:
      Content-Type: application/json
      Authorization: Bearer <PLACEHOLDER_元典_API_KEY>
```

### 方案C：通用 mcp.json 格式

适用于Codex、Claude Code、Cursor等支持MCP的平台：

```json
{
  "mcpServers": {
    "pkulaw": {
      "type": "http",
      "url": "https://apim-gateway.pkulaw.com/mcp-law-search-service",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer <PLACEHOLDER_北大法宝_Token>"
      }
    },
    "yuandian-law": {
      "type": "http",
      "url": "https://open.chineselaw.com/mcp/law/stream",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer <PLACEHOLDER_元典_API_KEY>"
      }
    },
    "yuandian-case": {
      "type": "http",
      "url": "https://open.chineselaw.com/mcp/case/stream",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer <PLACEHOLDER_元典_API_KEY>"
      }
    },
    "yuandian-company": {
      "type": "http",
      "url": "https://open.chineselaw.com/mcp/company/stream",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer <PLACEHOLDER_元典_API_KEY>"
      }
    }
  }
}
```

---

## 二·五、方案D：WorkBuddy 单一命名空间（当前默认）

在 WorkBuddy 平台，华宇元典与北大法宝通常以**单一 MCP 命名空间**接入，工具名带  前缀，与方案B/C 的「三独立 MCP（yuandian_law_*/case_*/company_*）」命名不同。技能已支持自动适配（见总控路由「MCP工具名自适应」），此处给出真实工具名映射供排障：

| 能力 | 方案B/C 工具名 | WorkBuddy 当前默认工具名 |
|------|--------------|------------------------|
| 法规向量检索 |  |  |
| 案例向量检索 |  |  |
| 案例详情 |  |  |
| 企业工商信息 |  |  |
| 用户余额/探活 | （无直接对应） |  |
| 幻觉检测 | （无直接对应） |  |
| 北大法宝法条检索 |  |  |
| 北大法宝案例检索 |  |  |

> 若调用报错「工具不存在」，先用  /  确认当前环境真实暴露的工具名前缀，再据此适配。

---

## 三、前置条件（401/403排障）

### 北大法宝
在 [mcp.pkulaw.com](https://mcp.pkulaw.com) → 我的应用 → **订阅**以下5个服务：
- 法规-关键词
- 法规-语义
- 案例-关键词
- 案例-语义
- 精准法条-关键词

未订阅时会返回401/403。

### 华宇元典
- 在 [open.chineselaw.com](https://open.chineselaw.com) 注册账号
- 获取API Key（Bearer Token）
- 确认账号有对应模块的调用额度
- 三个子服务（law / case / company）共用同一个API Key，需分别配置

---

## 四、可用工具速览

### 北大法宝（5个工具）

| 工具 | 用途 | 对应技能中的使用场景 |
|------|------|-------------------|
|  | 法条语义检索 | 根据案情描述找法律依据 |
|  | 法条精确查询 | 已知条款号取原文核验 |
|  | 法规列表 | 关键词查出相关法规 |
|  | 案例语义检索 | 找类似案例参考 |
|  | 案例列表（深度版） | 类案研判，含25+字段 |

### 华宇元典

| 模块 | 工具示例 | 用途 |
|------|---------|------|
| **law**（法规） |  | 法规向量语义检索 |
| **case**（案例） |  | 案例向量语义检索 |
| |  | 案例详情（判决要素） |
| **company**（企业） |  | 企业工商信息+司法全景 |
| |  | 被执行信息 |
| |  | 法院公告 |
| |  | 行政处罚 |
| | 等20+工具 | 诉讼/执行/失信/冻结等 |

---

## 五、技能中的双源核验机制

本集群技能在Step 2（法律检索）中执行双源核验：

```
第1层：法条检索
  1.1 华宇元典MCP → 查法规
  1.2 北大法宝MCP → 交叉核验同一法条
```

核验结论标注方式：
- **双源确认** ✅：两源一致
- **存在差异** ⚠️：两源不一致，记录差异
- **单源检索**：只有一个MCP可用
- **未检索到**：两个MCP均查不到

> 配置完成后，技能会自动调用MCP进行检索和核验。如某个MCP不可用，技能会自动降级为单源检索并标注。

## MCP工具链级联降级

当法规查询链路任一环节失败时，按以下顺序自动降级：

| 步骤 | 方式 | 说明 |
|:----:|:-----|:------|
| ① | 华宇元典MCP | 首选，在线检索完整法规+案例 |
| ② | 北大法宝MCP | 次选，双源交叉验证 |
| ③ | 法律法规知识库「法律法规」 | 搜索已收录的法规摘要和裁判观点 |
| ④ | 本地离线法规库 | references/离线法条精华.md（32 部核心法规摘要合并，离线兜底）+ 法律法规知识库在线检索调取法条/案例/省域细则 |
| ⑤ | 法律原则回复 | 依据AI训练数据中的法律常识作答 |
| ⑥ | 引导用户自行查询 | 告知用户到国家法律法规数据库 flk.npc.gov.cn 查询 |

> 每步失败自动切换下一步，不中断用户流程。MCP和法规数据库均不可用时，自动降级到本地离线法规库。
