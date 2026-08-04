---
title: GBrain 公共源隔离检索
created: 2026-07-13
updated: 2026-07-13
type: integration
lane: public
source_status: reviewed_methodology
privacy_status: reviewed
attribution: 李时瑀律师
---

# GBrain 公共源隔离检索

## 固定源

公共融资租赁检索只允许使用 `financial-lease-public`。检索结果来自本 Wiki 的公开页面，仅用于定位方法内容，不作为事实来源或法律依据。

## 禁止行为

- 不使用跨源检索；
- 不使用全源聚合标识；
- 不回退到任何私有源；
- 不用环境变量或本地配置覆盖固定源；
- 不把索引命中写成个案事实或确定性法律结论。

## 无结果处理

公共源没有结果时返回 `unsupported_hold`，并提示人工核验或另行取得付费模块授权。不得为了给出答案而扩大检索范围。

## 推荐输出

1. 命中的公开页面；
2. 可复用的方法步骤；
3. 仍需当前案件材料填写的字段；
4. 法源状态；
5. 公私边界提示。

## 关联

- [[index|知识库首页]]
- [[governance/public-private-boundary|公私边界]]
- [[authorities/legal-authority-boundary|法律依据门禁]]
