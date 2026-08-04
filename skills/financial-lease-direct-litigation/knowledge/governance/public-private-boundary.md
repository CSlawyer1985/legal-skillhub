---
title: 公共与付费模块边界
created: 2026-07-13
updated: 2026-07-14
type: governance
lane: public
source_status: reviewed_methodology
privacy_status: reviewed
attribution: 李时瑀律师
---

# 公共与付费模块边界

## 公共范围

公共层仅包含普通直租的材料可读性、案型识别、合同审查、起诉材料结构、证据目录、缺失材料清单、DOCX 质量、代理词结构、法律意见书结构以及通用的隐私和法源门禁。

## 不进入公共层

- 售后回租；
- 融资租赁转分期；
- 第三方融资；
- 混合结构或证据冲突案件；
- 个案事实、案件正文、客户信息和任何可反向识别的材料；
- 未完成现行法原文核验的确定性法律结论。

## 路由规则

公共工作流发现非直租信号时，只输出 `HOLD-ROUTE`、待核事实和建议的专业模块名称，不展开付费模块的方法正文。材料无法可靠读取时输出 `HOLD-MATERIAL-READABILITY`，不得把未读内容归类为缺失。公共检索不得回退到私有源，也不得进行跨源搜索。

## 关联

- [[types/ordinary-direct-lease|普通直租识别]]
- [[integration/gbrain-public-query|公共检索隔离]]
- [[governance/attribution-and-release|署名与发布门禁]]
