---
name: qxb-equity-penetration
description: 基于工商数据源，深度解析企业股权结构。适用于企业并购重组前的股权梳理、投资尽调中的股权穿透、商业合作中的关联方识别等场景，清晰呈现企业股权架构与控制关系，辅助决策者把握企业核心控制脉络。
license: MIT
metadata: { "openclaw": { "requires": { "env": ["QXBENT_API_TOKEN"], "bins": ["node", "npm"] }, "install": [ { "id": "npm-deps", "kind": "node", "package": "axios", "label": "Install Node.js dependencies" } ] } }
---

# 企业股权穿透

## 概述

查询企业的股权结构，可查询直接股东数量、名称及持股比例（按持股比例返回最多10个），以及间接股东数量、名称、持股比例和最短层级（按持股比例返回最多100个）。

## 特性

- 直接股东：按持股比例排序的股东列表（最多10个）
- 间接股东：穿透多层股权关系，展示最短路径和层级（最多100个）
- 路径追溯：每个间接股东都附带完整穿透路径（从目标企业到该股东的每一层节点及比例）

## 快速上手

### 1. 获取 API Token

在 [启信宝会员中心-skill额度](https://www.qixin.com/app-center/home?route=skill-quota) 获取 API Token。

### 2. 配置 Token

设置环境变量 `QXBENT_API_TOKEN`：

**Windows：**
1. 按 `Win + R`，输入 `sysdm.cpl`，按回车
2. 点击"高级" -> "环境变量"
3. 在"用户变量"中点击"新建"
4. 变量名：`QXBENT_API_TOKEN`，变量值：粘贴你的 Token
5. 点击"确定"保存，重启 AI 应用

**Mac/Linux：**
```bash
echo 'export QXBENT_API_TOKEN="your_token_here"' >> ~/.zshrc
source ~/.zshrc
```

### 3. 使用示例

```
帮我查一下蚂蚁集团的股权穿透，看看间接股东有哪些
```

```
查询华为技术有限公司的股东结构
```

```
这家公司的实际控制人是谁？帮我穿透一下股权
```

## API 接口

| 接口名 | 描述 | 参数 |
|--------|------|------|
| getEquityPenetration | 查询企业股权穿透 | ename（企业名称）或 eid（企业ID） |

## 工具权限

- `Bash(node:*)`: 允许执行 Node.js/TypeScript 代码
- `Read`: 允许读取接口文档

## 运行时要求

**Bins**
- `node` (Node.js >= 16.x)
- `npm`

**Env**
- `QXBENT_API_TOKEN` (必需) - 启信宝 API 访问凭证

## 初始化

首次使用时需要安装依赖：

```bash
npm install
```

## 数据说明

- 支持通过企业名称（ename）或企业ID（eid）查询
- 企业名称支持模糊匹配，自动取最佳匹配结果
- 返回数据中包含 `ename` 字段，标识实际查询的企业
- 直接股东数据来源为工商登记信息
- 间接股东通过多层穿透计算得出

## 参考文件

- 接口详细文档：读取 [references/getEquityPenetration.md](./references/getEquityPenetration.md)
