---
name: labor-issue-analysis
description: 劳动争议争点、请求权或抗辩权基础分析。根据案件事实自动识别法律争点,建立请求/抗辩矩阵,列出构成要件和对方最强反向观点。
license: AGPL-3.0
metadata:
  homepage: https://jinlishan.com/
  author: 金莉珊律师（微信jinlishan_）
  version: 1.4.4
---

# 劳动争议争点分析

1. 读取案件状态和上游材料。
2. 运行 `python3 scripts/build_issue_matrix.py --state <case_state.json> --discover`，从本案任务和事实生成有限的待复核争点候选。需要补充查询时使用 `--query "<案件问题>"`。候选只是内部分析线索，不向用户转交路由器原始输出，不将内置知识按卡片、目录或批量数据交付。
3. 根据代理立场分别建立我方请求/抗辩与对方最强路径,不混用立场。
4. 覆盖劳动关系、合同、解除终止、工资工时、休假、工伤社保、超龄用工、人事争议及程序问题。
5. 每个路径写明构成要件、已知事实、缺口、备选路径和失败后果。
6. 浙江口径节(如有)优先于一般规则引用。
7. 将要件和待证事实交给证据分析。
8. 将经复核的争点组织为矩阵 JSON，运行 `python3 scripts/build_issue_matrix.py --state <case_state.json> --input <争点矩阵.json>`。每个争点必须写明我方路径、构成要件及事实链接、对方最强观点与回应、备选路径或无备选理由、失败后果。待复核候选、空泛占位表述或引用不存在的事实／证据／法源 ID 均不得通过节点。
