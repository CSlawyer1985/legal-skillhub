# 自然语言指令解析（Instruction Playbook）

> 输入 `instruction`，输出 `report_level` + `extra_focus[]` + 各模块 depth。

---

## 关键词 → 报告级别

| 关键词 | report_level |
|---|---|
| 摘要/简版/简要/看看/大致 | summary |
| 标准版/常规尽调/尽调（默认） | standard |
| 完整版/全面版/深度尽调/全方位/详尽 | full |

## 关键词 → 额外关注

| 关键词 | extra_focus |
|---|---|
| 诉讼/司法/涉诉/裁判/被告/原告 | litigation → B5/B6 deep |
| 知识产权/IP/商标/专利/著作权 | ip → B7 deep |
| 财务/业绩/利润/营收/资产负债 | finance → B9 deep |
| 重整/预重整/破产/退市/立案/处分 | restructuring → B10 deep |
| 反垄断/经营者集中 | antitrust → B5 + 反垄断局公示 |
| 出海/涉外/跨境 | overseas → B11 + 涉外合规 |
| 上市公司/证券/股票 | listed → B9 deep |
| 环保/排污/ESG | esg → B11 deep |
| 谈客户/接法律顾问/切入/常法/专项 | engagement → 强制启用第八节"法律顾问切入备忘录" |

## 默认深度

| 模块 | summary | standard | full |
|---|---|---|---|
| B1 工商基础 | quick | standard | deep |
| B2 股东/实控人/投资 | quick | standard | deep |
| B3 董监高 | quick | standard | deep |
| B4 经营异常/严重违法 | standard | standard | deep |
| B5 司法风险 | quick | standard | deep |
| B6 执行/失信/限高 | standard | standard | deep |
| B7 知识产权 | quick | standard | deep |
| B8 行政处罚 | quick | standard | deep |
| B9 上市专项 | standard | deep | deep |
| B10 重整/监管 | standard | standard | deep |
| B11 舆情 | quick | standard | deep |

## 触发全部 deep

- "完整版/全面版/全方位/深度尽调/详尽" → 全部 deep

## 强制模块（无论级别）

- **数据对齐基准表**（第三节）— 永远生成
- **利益冲突审查**（第十节）— 永远生成，缺失阻断
- **免责声明**（第十二节）— 永远生成