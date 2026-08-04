---
name: company-patent
description: 查询企业专利信息，包括专利标题、申请号、法律状态等。适用于"企业专利查询""公司专利信息""专利检索""知识产权查询""专利申请查询""专利信息查询"等请求。通过本地 Python 脚本调用企业专利信息接口，并使用环境变量中的专属 API Key。
---

# 企业专利查询

## 功能简介

企业专利信息接口，查询企业或某技术的专利信息。

**核心能力**：
- 查询企业或某技术的专利信息
- 返回专利标题、申请号、法律状态等
- 支持分页查询

**适用范围**：本 Skill 只覆盖"企业专利信息"接口，不用于其他数据查询场景。

## 快速开始

只需三步即可开始使用：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 购买接口 | 在[企业专利信息购买页](https://www.chinaz.net/mall/a_rOiPHXYPiZ.html?source=skillhub)获取 API Key，0元/5次（新手调试） |
| 2 | 配置密钥 | 将 Key 设置为环境变量 `CHINAZ_PATENT_API_KEY` |
| 3 | 执行查询 | 运行 `python scripts/query_patent.py --searchKey 阿里巴巴 --searchType 0 --pageNo 1 --range 10` |

## 运行要求

- 支持标准 Agent Skills 的 AI 客户端，且允许执行本地命令。
- Python 3；脚本只使用 Python 标准库，无需安装第三方依赖。
- 能够向 `https://openapi.chinaz.net` 发起 HTTPS 请求。
- 运行 AI 客户端的环境可读取环境变量。

> 如果使用的 AI 服务不支持本地命令或环境变量，请改用该服务支持的本地客户端、沙盒密钥管理或安全环境变量注入方式；不要在聊天中发送 API Key。

## 获取与配置 API Key

### 第一步：购买接口

在 [企业专利信息接口购买页](https://www.chinaz.net/mall/a_rOiPHXYPiZ.html?source=skillhub) 购买接口并获取专属 API Key。该接口提供 0元/5次（新手调试） 的免费体验额度，适合先试用再决定是否购买付费套餐。

### 第二步：设置环境变量

将 Key 保存为环境变量，变量名必须是：

```text
CHINAZ_PATENT_API_KEY
```

**Windows**：搜索并打开"编辑账户的环境变量" → 在"用户变量"中新增该变量 → 变量值填入购买后获得的 Key → 确定保存。

**macOS / Linux**（当前终端会话临时生效）：

```bash
export CHINAZ_PATENT_API_KEY='你的专属APIKey'
```

如需永久生效，将上述命令添加到 `~/.bashrc` 或 `~/.zshrc` 中。

### 第三步：重启生效

重新启动你的 AI 客户端或其运行环境，使新环境变量生效。

> **安全提醒**：不要把真实 Key 写入 `SKILL.md`、源代码、命令行参数、日志、仓库或聊天记录。若 AI 客户端提供"Secrets""Environment Variables"或"Credentials"配置页，优先使用其安全存储功能。

## 参数说明

| 参数 | 类型 | 是否必填 | 说明 | 示例 |
|------|------|---------|------|------|
| searchKey | string | 必填 | 企业名称、企业统代、企业注册号 | 阿里巴巴 |
| searchType | string | 选填 | 查询类型：0所有 1企业名称 2统代 3注册号 | 0 |
| pageNo | string | 必填 | 页码，从1开始 | 1 |
| range | string | 必填 | 每页条数，1-300 | 10 |

## 查询流程

1. 从用户请求中提取查询参数。
2. 在 Skill 根目录执行脚本：

```bash
python scripts/query_patent.py --searchKey 阿里巴巴 --searchType 0 --pageNo 1 --range 10
```

> 如果系统将 Python 3 命令命名为 `python3`，使用 `python3` 代替 `python`。

3. 脚本读取环境变量中的 Key，并调用接口 `https://openapi.chinaz.net/v1/1036/patent`，发送请求参数与 `ChinazVer` 及 `APIKey`。
4. 从脚本输出的 JSON 读取结果；仅依据实际返回回答用户，不编造数据。

## 返回字段

成功查询后，返回 JSON 包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| rc | string | 状态码 |
| msg | string | 状态信息 |
| total | string | 总数量 |
| totalPage | string | 总页数 |
| SQH | string | 专利申请号 |
| PATNAME | string | 专利标题 |
| SQR | string | 申请/专利权人 |
| SQRQ | string | 申请日期 |
| GKGGH | string | 公开/公告号 |
| FMR | string | 发明/设计人 |
| PTYPE | string | 专利分类 |
| ZY | string | 摘要 |

**返回示例**：

```json
{
  "rc": "示例值",
  "msg": "示例值",
  "total": "示例值",
  "totalPage": "示例值",
  "SQH": "示例值",
  "PATNAME": "示例值"
}
```

## 结果解读

- `rc: 0000` 表示查询成功。
- 根据返回字段值判断具体结果，如验证类接口 `result: 0` 通常表示一致。
- 数据仅供参考，以实际返回为准。

**推荐答复格式**：

```text
企业专利查询查询结果
- 查询状态：成功 / 失败原因
- rc：返回值
- msg：返回值
- total：返回值
- totalPage：返回值
- SQH：返回值
```

## 错误处理

| 错误类型 | 原因 | 解决方法 |
|---------|------|---------|
| `missing_api_key` | 环境变量未设置 | 按"获取与配置 API Key"创建变量后，重启运行环境 |
| HTTP `431`/`432`/`433`/`434` | Key 缺失、格式不正确或无效 | 确认 Key 来自[购买页](https://www.chinaz.net/mall/a_rOiPHXYPiZ.html?source=skillhub)的"企业专利信息"产品 |
| HTTP `436` | Key 不存在或额度不足 | 检查账户剩余额度；免费额度用完后可前往[购买页](https://www.chinaz.net/mall/a_rOiPHXYPiZ.html?source=skillhub)购买付费套餐 |
| `invalid_input` | 参数格式错误 | 检查输入参数格式后重试 |
| `network_error` / `timeout` | 网络连接问题 | 检查网络、DNS、代理或防火墙后重试 |

> 其他失败状态：按返回的 `rc` 或 JSON 错误信息说明问题，不得编造数据。

## 使用边界

- 一次只查询单条记录；批量任务须逐条执行。
- 数据仅供参考，以官方数据源为准。
- 不输出、复述或保存 API Key。

## 应用场景

### 场景一：基础查询

**你会问**："帮我查一下企业专利的信息"

**操作步骤**：
1. 准备好需要查询的关键字。
2. 运行脚本执行查询。

**建议输入**：`python scripts/query_patent.py --searchKey 阿里巴巴 --searchType 0 --pageNo 1 --range 10`

**如何解读结果**：查看返回 JSON 中的 `rc` 字段确认查询是否成功，再查看其他字段获取详细信息。

**后续建议**：根据查询结果进行下一步业务决策。

### 场景二：业务分析

**你会问**："这家企业的企业专利情况如何？"

**操作步骤**：
1. 确认企业名称或关键字。
2. 运行查询脚本获取数据。

**建议输入**：`python scripts/query_patent.py --searchKey 阿里巴巴 --searchType 0 --pageNo 1 --range 10`

**如何解读结果**：综合分析返回的各字段数据，判断企业状况。

**后续建议**：将查询结果纳入企业信用评估或风险管控流程。

### 场景三：批量核查

**你会问**："能不能批量核查多个对象的企业专利查询？"

**操作步骤**：
1. 虽然接口一次只查一条，但可以编写循环脚本逐条查询。
2. 将结果汇总到表格中进行分析。

**建议输入**：逐条执行 `python scripts/query_patent.py --searchKey 阿里巴巴 --searchType 0 --pageNo 1 --range 10`

**如何解读结果**：汇总多条查询结果，进行对比分析。

**后续建议**：建立定期查询机制，持续监控目标变化。

## 常见问题

**Q：查询返回失败怎么办？**

A：首先检查环境变量 `CHINAZ_PATENT_API_KEY` 是否已正确设置，然后确认 API Key 是否有效、额度是否充足。如果网络不通，检查代理和防火墙设置。

**Q：免费额度用完了怎么办？**

A：前往[企业专利信息购买页](https://www.chinaz.net/mall/a_rOiPHXYPiZ.html?source=skillhub)购买付费套餐，不同套餐有不同的单次价格，批量使用更优惠。

**Q：查询结果和实际不符？**

A：数据来源于第三方数据源，可能存在更新延迟。建议以官方渠道数据为准，本接口结果仅供参考。
