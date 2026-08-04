---
name: global-company-shareholder-zh
description: 调取全球企业资料库查询股东信息以及实际受益所有人（Beneficial Owner），梳理企业股权架构、投资关联关系，协助销售、风控人员摸清企业真实管控背景。
metadata: {"version":"1.0.2","homepage":"https://www.upkuajing.com","clawdbot":{"emoji":"🏛️","requires":{"bins":["python"],"env":["UPKUAJING_API_KEY"]},"primaryEnv":"UPKUAJING_API_KEY"}}
---

# 全球企业库股东查询

使用跨境魔方开放平台API从全球企业库数据查询公司股东信息。

## 概述

本技能提供对跨境魔方全球企业库股东信息的查询。通过公司ID（pid）获取股东列表，包含股东ID、名称、类型、持股方式和持股比例。

**前置条件**：需要传入公司ID（pid）作为参数。如果用户没有公司ID，应先使用 **global-company-search** 技能搜索目标公司获取pid，再使用本技能。

## 脚本运行

### 环境准备

1. **检查 Python**：`python --version`
2. **安装依赖**：`pip install -r requirements.txt`

脚本目录：`scripts/*.py`
运行示例：`python scripts/*.py`

**重要**：始终使用直接脚本调用，如 `python scripts/company_shareholder_list.py`。**不要使用** shell 复合命令如 `cd scripts && python company_shareholder_list.py`

### 股东列表查询 (`company_shareholder_list.py`)
- **返回粒度**：每条股东记录为一行
- **适用场景**：查询指定公司的股东信息
- **示例**：
  - "查询US_12345公司的股东有哪些"
  - "获取pid为US_12345的公司的股东详情"
- **参数**：查看参数说明 [股东列表 API](references/company-shareholder-list-api.md)

## API密钥与充值
使用此技能需要API密钥。API密钥保存在 `~/.upkuajing/.env` 文件中：
```bash
cat ~/.upkuajing/.env
```
**文件内容示例**：
```
UPKUAJING_API_KEY=your_api_key_here
```
### **未设置API密钥**
请先检查 `~/.upkuajing/.env` 文件是否有 UPKUAJING_API_KEY;
如果未设置 UPKUAJING_API_KEY API密钥，请提示并让用户选择：
1. 用户有，由用户提供(手动添加到 ~/.upkuajing/.env 文件)
2. 用户没有，你可使用接口进行申请（`auth.py --new_key`），申请到新密钥后，会自动保存到 ~/.upkuajing/.env
等待用户选择；

### **账户充值**
如果调用接口响应账户余额不足时，需说明并引导用户进行账户充值：
1. 创建充值订单（`auth.py --new_rec_order`）
2. 根据订单响应，发送支付页面URL给用户，引导用户打开地址付款，付款成功后告诉你；

### **获取账户信息**
可通过此脚本，获取UPKUAJING_API_KEY对应的账户信息 `auth.py --account_info`

## API密钥与跨境魔方账号
- 新申请的API密钥：在[跨境魔方开放平台](https://developer.upkuajing.com/)注册、登录后进行账号绑定

## 费用

**所有API调用都会产生费用**，不同接口计费方式不同。

**最新价格**：用户可访问 [详细价格说明](https://www.upkuajing.com/web/openapi/price.html)
或者使用：`python scripts/auth.py --price_info`（返回接口完整定价）

### 查询计费规则

按**调用次数**计费，每次查询一个公司的股东信息：
- 每次API调用产生一次费用
- **执行前必须：**
  1. 告知用户本次查询会产生费用
  2. 停止，等待用户在独立消息中明确确认后，再执行脚本

### 费用确认原则

**任何会产生费用的操作，都必须先告知、等待用户明确确认，不得在告知的同一条消息中直接执行。**

## 工作流程

### 决策指南

| 用户意图 | 使用API |
|---------|--------|
| "查询US_12345公司的股东有哪些" | 股东列表查询 |
| 用户只有公司名称，没有pid | global-company-search（先搜索公司获取pid，再使用本技能） |

## 使用示例

### 查询股东列表

**用户请求**："查询US_12345公司的股东"
```bash
python scripts/company_shareholder_list.py --pid US_12345
```

## 错误处理

- **API密钥无效/不存在**：检查 `~/.upkuajing/.env` 文件中的 `UPKUAJING_API_KEY`
- **余额不足**：引导用户充值
- **参数无效**：**必须先查看 references/ 目录下的对应 API 文档**，从文档中获取正确的参数名称和格式，不要猜测

### API Documentation Reference

- 股东列表：查看 [references/company-shareholder-list-api.md](references/company-shareholder-list-api.md)

## 最佳实践

1. **查看API文档**：
   - **执行查询前，必须先查看对应的 API 参考文档**
   - 查看 [references/company-shareholder-list-api.md](references/company-shareholder-list-api.md)
   - 不要猜测参数名称，从文档中获取准确的参数名称和格式

2. **查询参数**：
   - 公司ID（pid）为必填参数。如果用户提供的是公司名称而非pid，应先使用 **global-company-search** 搜索目标公司获取pid。公司ID也可以从其他全球企业库搜索技能获取。

## 注意事项
- 股东记录用 `shareholderId` 作为唯一标识
- 持股比例以字符串形式返回，包含百分号（如 "60.00%"）
- `total` 字段表示股东总数
- 文件路径在所有平台上都使用正斜杠
- **禁止输出技术参数格式**：不要在回复中展示代码样式的参数，应将其转换为自然语言
- **不要估算或猜测每次调用的费用** — 使用 `python scripts/auth.py --price_info` 获取准确定价信息
- **不要**猜测参数名称，从文档中获取准确的参数名称和格式

## 相关技能

其他您可能会用到的跨境魔方技能：

- global-company-search — 全球企业库找公司
- global-company-person-search — 全球企业库找人
- global-company-employee — 全球企业库员工查询
- global-company-person-colleague — 全球企业库同事查询
- global-company-person-alumni — 全球企业库校友查询
- global-company-person-experience — 全球企业库工作经历查询
- global-company-person-education — 全球企业库教育经历查询
- global-company-person-school-detail — 全球企业库学校详情查询
- linkedin-person-search — 领英找人
- linkedin-company-search — 领英找公司
- upkuajing-global-company-people-search — 全来源统一的企业与人物搜索
- upkuajing-customs-trade-company-search — 海关贸易企业搜索
- upkuajing-contact-info-validity-check — 联系方式有效性检测
- phone-validity-check — 电话号码有效性检测
- email-validity-check — 邮箱地址有效性检测
- domain-validity-check — 域名有效性检测