# YC SaaS 起草器——决策矩阵

将咨询表回答和始终适用的默认项映射到 YC 表格版 SaaS 协议的特定修改。分为四个部分：

A. 始终适用的默认项——适用于每份草稿
B. 条件性决定——由咨询表回答驱动
C. 变量替换——占位符替换
D. 交由律师处理——在备忘录中标记供律师审查

---

## A. 始终适用的默认项

无论咨询表如何回答，这 17 项修改均适用于每份草稿。

### A1. 订购表标题

- **YC 原文：** "SAAS SERVICES ORDER FORM"
- **操作：** 改为 "ORDER FORM NUMBER ONE"

### A2. 协议名称

- **YC 原文：** "SAAS SERVICES AGREEMENT"（标题）和 "This SaaS Services Agreement ('Agreement')"（序言）
- **操作：** 改为 "CUSTOMER AGREEMENT"（标题）和 "This Customer Agreement ('Agreement')"（序言）。将全文所有 "SaaS Services Agreement" 替换为 "Customer Agreement"。

### A3. 序言日期

- **YC 原文：** "this _______ day of ________, 2015"
- **操作：** 将年份更新为当前年份。用 `effective_date` 咨询表值填写日期字段，或留为 `[TBD — Effective Date]`。

### A4. 第 1.1 节——SLA 引用始终开启

- **YC 原文：** "in accordance with the Service Level Terms attached hereto as Exhibit B. *[OPTIONAL]*"
- **操作：** 删除 `[OPTIONAL]` 标记。保留 SLA 引用——附件 B 始终附上。

### A5. 第 1.2 节——支持引用附件 B

- **YC 原文：** "in accordance with the terms set forth in Exhibit C. *[OPTIONAL:...]*"
- **操作：** 将 "Exhibit C" 改为 "Exhibit B"（合并后的附件）。删除 `[OPTIONAL:...]` 注记。SLA 和支持条款均位于单一的附件 B 中。

### A6. 第 2.2 节——出口管制清理

- **YC 原文：** 包含出口限制措辞，后随 `*[Note: export and government rights clauses are typically less important for pure hosted solutions...]*`
- **操作：** 保留全部出口管制和 FAR/DFAR 措辞。仅删除方括号注记。

### A7. 第 2.3 节——删除客户赔偿条款

- **YC 原文：** "[Customer hereby agrees to indemnify and hold harmless Company against any damages, losses, liabilities, settlements and expenses (including without limitation costs and attorneys' fees) in connection with any claim or action that arises from an alleged violation of the foregoing or otherwise from Customer's use of Services.]" 后随 `*[Note: many larger customers resist these types of indemnity clauses...]*`
- **操作：** 删除整个方括号赔偿条款和方括号注记。该措辞在谈判中总是被划掉——主动移除可以避免不必要的红线并展现专业性。

### A8. 第 2.5 节——添加数据隐私与安全

- **YC 原文：** YC 模板中不存在此节。
- **操作：** 使用 supplementary-language.md 中 `#DATA-PRIVACY` 的逐字文本插入新的第 2.5 节。这至关重要——现代 SaaS 协议不应缺少数据隐私条款。

### A9. 第 3.3 节——数据分析始终开启

- **YC 原文：** 以 "Notwithstanding anything to the contrary, Company shall have the right collect and analyze data..." 开头的方括号段落，带 `*[Note: it is important to determine what data rights are necessary...]*`
- **操作：** 移除段落周围的方括号——该措辞始终包含，并非可选项。删除 `*[Note:...]*`。分析/数据改进权利是标准 SaaS 语言。

### A10. 第 6.1 节——添加排他性保证救济

- **YC 原文：** 第 6 节以 "professional and workmanlike manner" 结束公司保证，然后进入免责声明。
- **操作：** 将第 6 节重构为小节。第 6.1 节是现有的公司保证。在 "professional and workmanlike manner" 之后，插入 supplementary-language.md 中 `#WARRANTY-REMEDY` 的逐字文本。然后是现有的 "EXCEPT AS EXPRESSLY SET FORTH..." 免责声明。

### A11. 第 6.2 节——添加客户保证

- **YC 原文：** 不存在。
- **操作：** 使用 supplementary-language.md 中 `#CUSTOMER-WARRANTY` 的逐字文本插入新的第 6.2 节。

### A12. 第 6.3 节——添加测试版产品免责声明

- **YC 原文：** 不存在。
- **操作：** 使用 supplementary-language.md 中 `#BETA-DISCLAIMER` 的逐字文本插入新的第 6.3 节。必须全部大写。

### A13. 第 7 节——赔偿始终包含

- **YC 原文：** "*[OPTIONAL: many start-up companies choose not to offer indemnity as a starting point...]*"
- **操作：** 删除可选项注记。赔偿始终包含——省略它表明公司对自己的知识产权缺乏信心。

### A14. 第 7 节——从专利范围中移除"美国"

- **YC 原文：** "infringement by the Service of any United States patent or any copyright"
- **操作：** 改为 "infringement by the Service of any patent or any copyright"。移除地域限制是交易对手几乎总是要求的标准红线。

### A15. 第 8 节——删除谈判注记

- **YC 原文：** `*[Note: Liability limitations are frequently heavily negotiated in larger deals...]*`
- **操作：** 删除该注记。默认责任条款保持原样。

### A16. 第 9 节——替换营销措辞

- **YC 原文：** "[The parties shall work together in good faith to issue at least one mutually agreed upon press release within 90 days of the Effective Date, and Customer otherwise agrees to reasonably cooperate with Company to serve as a reference account upon request.]" 和 `*[OPTIONAL:...]*`
- **操作：** 用 supplementary-language.md 中 `#MARKETING-DEFAULT` 的逐字文本替换整个方括号句子和可选项注记。这是始终开启的，而非可选项。

### A17. 附件——合并 B + C，删除附件 C

- **YC 原文：** 附件 B（服务水平条款）和附件 C（支持条款）作为独立附件。
- **操作：** 用 supplementary-language.md 中 `#EXHIBIT-B-CONSOLIDATED` 的单一合并附件替换两者。删除全文所有对 "Exhibit C" 的引用。附件 A（SOW）仍按下方 B3 为条件性。

### A18. 删除所有批注

- **操作：** 移除整个文档中所有 `*[Note:...]*`、`*[OPTIONAL:...]*`、`[OPTIONAL]` 和其他斜体起草指引。这些都不应出现在输出中。

---

## B. 条件性决定

这些修改取决于咨询表回答。

### B1. 订购表——服务描述

- **咨询表字段：** `product_description`
- **YC 原文：** "[Name and briefly describe services here] (the 'Service(s)')."
- **操作：** 用咨询表中的产品描述替换方括号占位符。描述应宽泛、简洁且基于事实。格式："[Company] develops and makes available [product_description] (the 'Service(s)')."

### B2. 订购表——服务费用

- **咨询表字段：** `fee_type`、`fee_details`、`service_capacity`、`overage_terms`
- **YC 原文：** "$______________ per month, payable in advance, subject to the terms of Section 4 herein."
- **操作：** 使用 supplementary-language.md 中 `#FEE-EXAMPLES` 中匹配 `fee_type` 的模式编写服务费用行。用 `fee_details` 填写金额。这是唯一使用编写（而非逐字）语言的部分。
- **服务容量：** 如果 `fee_type` 为 per_seat、usage、minimum_plus_overage、prepaid_capacity、tiered 或 hybrid → 保留 "Service Capacity" 行并从咨询表填写。如果为 flat 或 performance → 删除 "Service Capacity" 行和超额注记。

### B3. 订购表——实施服务

- **咨询表字段：** `implementation_services`
- **如果为 true：** 保留订购表中的 "Implementation Services" 和 "Implementation Fee" 部分。保留附件 A（SOW）。用 `implementation_fee` 填写费用。在备忘录中标记："实施服务已包含——与法律顾问讨论定制交付物的知识产权归属。"
- **如果为 false：** 从订购表中删除 "Implementation Services" 段落和 "Implementation Fee" 行。完全删除附件 A。从第 1.1 节文本中移除 "Implementation Services"。从第 6 节保证措辞中移除 "and Implementation Services"。

### B4. 订购表——试点期

- **咨询表字段：** `pilot`
- **如果为 true：** 保留 "Pilot Use" 部分。用 `pilot_duration` 填写试点期，用 `pilot_fee` 填写试点使用费。如果费用为 $0，写 "$0 (no charge)"。
- **如果为 false：** 从订购表中删除整个 "Pilot Use" 部分，包括试点期和试点使用费行。

### B5. 第 2.1 节——分发式软件许可

- **咨询表字段：** `distributed_software`
- **YC 原文：** "Company hereby grants Customer a non-exclusive, non-transferable, non-sublicensable license to use such Software during the Term only in connection with the Services." 后随 `*[OPTIONAL:...]*`
- **如果为 true：** 保留许可句子。删除可选项注记。
- **如果为 false：** 删除许可句子和可选项注记。纯云端 SaaS 不分发软件。

### B6. 第 3.2 节——衍生数据所有权

- **咨询表字段：** `customer_owns_derivatives`
- **YC 原文：** "Customer shall own all right, title and interest in and to the Customer Data[, as well as any data that is based on or derived from the Customer Data and provided to Customer as part of the Services]" 后随 `*[OPTIONAL:...]*`
- **如果为 true：** 保留方括号措辞（移除方括号，保留文本）。删除可选项注记。客户拥有原始数据 + 衍生输出。
- **如果为 false：** 完全移除方括号措辞。删除可选项注记。客户仅拥有原始客户数据。在备忘录中标记："客户不拥有衍生数据——预计交易对手会就此点进行谈判。"

### B7. 第 5.1 节——自动续约

- **咨询表字段：** `auto_renewal`、`renewal_notice_days`
- **YC 原文：** "automatically renewed for additional periods of the same duration... unless either party requests termination at least thirty (30) days prior to the end of the then-current term."
- **如果 auto_renewal: true、notice: 30：** 保持原样。
- **如果 auto_renewal: true、notice: 60：** 将 "thirty (30) days" 改为 "sixty (60) days"。
- **如果 auto_renewal: true、notice: 90：** 将 "thirty (30) days" 改为 "ninety (90) days"。
- **如果 auto_renewal: false：** 用 supplementary-language.md 中 `#NO-AUTO-RENEWAL` 的逐字文本替换第 5.1 节。

### B8. 第 5.2 节——终止时数据检索

- **咨询表字段：** `data_retention_days`
- **YC 原文：** "[Upon any termination, Company will make all Customer Data available to Customer for electronic retrieval for a period of thirty (30) days, but thereafter Company may, but is not obligated to, delete stored Customer Data.]" 和 `*[Confirm appropriate language...]*`
- **操作：** 移除段落周围的方括号——该措辞始终包含。删除 `*[Confirm...]*` 注记。将 "thirty (30) days" 替换为 `data_retention_days` 中的值（如 "sixty (60) days"）。本节始终存在。

### B9. 第 9 节——准据法

- **咨询表字段：** `governing_law`
- **YC 原文：** "State of [California]"
- **操作：** 将 "[California]" 替换为咨询表中的州（源自 `principal_place_of_business`）。默认：加利福尼亚。

### B10. 第 9 节——营销表述调整

- **咨询表字段：** `marketing_formulation`
- **如果为 "default"：** 不变——使用始终适用的默认营销措辞（#MARKETING-DEFAULT）。
- **如果为 "more"：** 在备忘录中标记："用户要求超出默认范围的扩大营销权利。律师应起草适当的新闻稿或参考客户措辞。"
- **如果为 "less"：** 在备忘录中标记："用户要求更严格的营销措辞。律师应审查并可能移除或缩小默认营销条款。"

### B11. 附件 B——可用性承诺

- **咨询表字段：** `availability_tier`
- **操作：** 在合并后的附件 B 中，将 `[99.9]` 占位符替换为所选层级。相应调整信用表第一行：如果为 99.95%，0% 信用行变为 "99.95 - 100.0%"，5% 行从 "99.0 - 99.94%" 开始。如果为 99.99%，类似调整。

### B12. 附件 B——支持详情

- **咨询表字段：** `support_email`、`support_phone`、`support_hours`、`communication_tool`
- **操作：** 按照 supplementary-language.md 中 `#EXHIBIT-B-CONSOLIDATED` 的变量表替换合并后附件 B 中的所有支持占位符。如果 `communication_tool` 为 "none"，从联系渠道表中移除 COMMUNICATION TOOL 列。

---

## C. 变量替换

所有占位符映射到咨询表字段。

| YC 占位符 | 咨询表字段 | 缺失时默认 |
|---|---|---|
| `[Company, Inc.]`（序言 + 签署，2 处） | `company_name` | `[TBD — Company Name]` |
| `[COMPANY NAME]`（订购表页眉） | `company_name`（大写） | `[TBD — COMPANY NAME]` |
| `[Customer]`（签署栏） | `customer_name` | `[TBD — Customer Name]` |
| `Customer:`（订购表顶部） | `customer_name` | `[TBD — Customer Name]` |
| `[Name and briefly describe services here]` | `product_description` | `[TBD — Service Description]` |
| `$______________ per month` | 由 `fee_type` + `fee_details` 编写 | `[TBD — Service Fees]` |
| `[One] Year` | `initial_term` | `One` |
| `$____________`（实施费） | `implementation_fee` | `[TBD — Implementation Fee]` |
| `[Sixty (60) days]`（试点期） | `pilot_duration` | `[TBD — Pilot Period]` |
| `[$XXX]`（试点费） | `pilot_fee` | `[TBD — Pilot Fee]` |
| `[California]`（准据法） | `governing_law` | California |
| `thirty (30) days`（续约通知，第 5.1 节） | `renewal_notice_days` | thirty (30) |
| `thirty (30) days`（数据检索，第 5.2 节） | `data_retention_days` | thirty (30) |
| `place of business at _______` | （不收集） | `[TBD — Company Address]` |
| `Service Capacity: ________` | `service_capacity` | `[TBD — Service Capacity]` 或按 B2 删除 |
| `[99.9]`（附件 B 可用性） | `availability_tier` | 99.9 |
| `[support@company.com]`（附件 B，2 处） | `support_email` | `[TBD — Support Email]` |
| `[phone number]`（附件 B） | `support_phone` | `[TBD — Support Phone]` |
| `[Shared Company channel]`（附件 B） | `communication_tool` | 如为 none 则移除列 |
| `[9:00 am Pacific Time]` | `support_hours`（开始） | 9:00 am Pacific Time |
| `[5:00 pm Pacific Time]` | `support_hours`（结束） | 5:00 pm Pacific Time |

**咨询期间未收集的字段**（账单地址、订购表上的联系信息等）留为带清晰标签的 `[TBD — description]`。备忘录列出所有 TBD 事项。

---

## D. 交由律师处理

这些事项在律师备忘录中标记供律师审查。本 skill 不解决它们——它识别问题并解释为什么法律顾问应参与。

### D1. DPA（数据处理附录）

- **触发：** 始终标记。第 2.5 节数据隐私措辞引用了 DPA。
- **备忘录文本：** "几乎肯定需要数据处理附录（DPA），特别是任一方在国际运营或处理加州居民个人数据时。DPA 起草应单独处理——使用 dpa-drafter skill。"

### D2. 实施服务知识产权归属

- **触发：** `implementation_services: true`
- **备忘录文本：** "已包含实施服务。定制开发、上线和培训工作会产生知识产权归属问题——谁拥有定制交付物？必须在发送前与法律顾问解决。考虑是否需要带知识产权转让条款的单独工作说明书。"

### D3. 衍生数据所有权

- **触发：** `customer_owns_derivatives: false`
- **备忘录文本：** "在当前草稿下，客户不拥有衍生数据。这是常见的谈判点——交易对手的律师可能会主张其数据生成的所有输出的所有权。与法律顾问讨论可接受的折中立场。"

### D4. 客户内容上的机器学习训练

- **触发：** `ml_trains_on_content: true`
- **备忘录文本：** "公司在客户内容上训练机器学习模型。第 3.3 节的数据权利措辞必须由法律顾问审查，以确认其（a）准确描述公司的实际数据实践，（b）为训练使用提供充分的法律依据，以及（c）在谈判中经得起客户审视。"

### D5. 数据保留时间表

- **触发：** 始终标记。
- **备忘录文本：** "数据保留期依第 5.2 节设定为终止后 [X] 天。法律顾问应核对该期限是否与公司的实际数据基础设施、任何监管保留要求和客户预期一致。"
