---
title: 融资租赁普通直租实务知识库
created: 2026-07-13
updated: 2026-07-14
type: index
lane: public
source_status: reviewed_methodology
privacy_status: reviewed
attribution: 李时瑀律师
---

# 融资租赁普通直租实务知识库

本地公共知识库聚焦普通直租型融资租赁纠纷，提供从材料读取到可编辑 DOCX 交付的可复用工作流。内容是方法与模板，不构成针对具体案件的法律意见。

## 快速入口

- [[playbooks/material-intake-and-readability|材料接收与可读性门禁]]
- [[types/ordinary-direct-lease|普通直租识别]]
- [[playbooks/contract-review|直租合同审查]]
- [[playbooks/litigation-materials-drafting|起诉材料格式化起草]]
- [[playbooks/evidence-catalog|证据目录组成]]
- [[playbooks/missing-material-checklist|用户缺失材料清单]]
- [[playbooks/docx-quality-gate|DOCX 质量门禁]]
- [[playbooks/agency-statement|代理词结构]]
- [[playbooks/legal-opinion|法律意见书结构]]

## 争点与法源

- [[issues/transaction-authenticity|交易真实性与合同链]]
- [[issues/rent-default-remedies|租金、违约与救济衔接]]
- [[issues/ownership-return|所有权、取回与价值清算]]
- [[issues/guarantee-liability|保证责任审查]]
- [[authorities/legal-authority-boundary|法律依据门禁]]
- [[authorities/verified-financing-lease-anchors|已核验融资租赁法源锚点]]

## 治理与检索

- [[governance/public-private-boundary|公共与付费模块边界]]
- [[governance/attribution-and-release|署名与发布门禁]]
- [[integration/gbrain-public-query|GBrain 公共源隔离检索]]
- [[cases/anonymized-patterns|匿名样本聚合模式]]

使用前先完成材料可读性和案型路由；若材料无法可靠读取，输出 `HOLD-MATERIAL-READABILITY`；若出现售后回租、融资转分期、第三方融资或结构冲突，输出 `HOLD-ROUTE` 并停止公共工作流。
