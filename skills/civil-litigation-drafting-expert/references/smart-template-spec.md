# 智能模板规范

## 目录

1. 模板语法
2. 通用对象
3. 生成规则
4. 要素式诉辩专项语法
5. 民事起诉状示例骨架
6. 程序申请通用骨架

## 1. 模板语法

- 变量：`{{ variable_name }}`
- 条件：`{% if condition %}...{% endif %}`
- 循环：`{% for item in items %}...{% endfor %}`
- 自动计算：`{{ calc.expression }}`
- 校验：`{{ check.rule_id }}`
- 风险提示只放在生成报告中，不混入提交正文。

模板不得把缺失值替换成虚构内容。阻断值显示为 `【待补：字段及原因】`。

## 2. 通用对象

```text
case: 案号、案由候选、阶段、标的、涉外标识
party[]: 诉讼地位、姓名／名称、统一代码／身份核验状态、住所、送达地址
claim[]: 请求、金额／标的、计算式、请求权基础、可执行性
fact[]: 时间、行为、主体、证据、争议状态
evidence[]: 名称、来源、形式、证明目的、原件状态、真实性争议
procedure: 管辖、程序类型、期限、已送达文书、前置程序
law[]: 名称、条号、引用目的、条件、效力、官方来源、核验日期
risk[]: 等级、触发事实、后果、缓解动作
attachment[]: 名称、份数、页码、对应正文位置
```

## 3. 生成规则

1. 先确定文书目的，再选择字段；不得从固定模板倒推事实。
2. 生成起诉状或答辩状时，先检查法〔2025〕82号所含 67 类现行要素式示范文本是否覆盖该纠纷；命中时吸收其要素与证据指引，但尊重当事人选择，不把使用示范文本作为立案条件。
3. 诉讼请求一项一义，给付对象、数量、期限和费用负担明确。
4. 事实部分围绕请求权构成要件和对方抗辩组织，不按材料杂乱顺序堆叠。
5. 法律依据只引用支持争点所必需的条款，并说明用途。
6. 证据目录与正文事实、请求逐项映射。
7. 附件份数、当事人人数、名称、金额和日期必须跨文书一致。
8. 只生成当事人文书；不得生成带法院印章、法院落款或审判人员署名的文书。

## 4. 要素式诉辩专项语法

命中 `element-pleading-knowledge.json` 的纠纷类型时，建立以下矩阵：

```text
pleading_matrix[]:
  request_or_defense: 请求或答辩结论
  legal_basis: 请求权或抗辩权基础
  elements[]: 必要要件、阻却要件、法律效果
  facts[]: 已证明／拟证明／对方主张／争议中／待核实
  evidence[]: 证据名称、证明目的、形式与真实性状态
  opponent_position: 对方最强观点
  court_question: 法院可能追问
  gap_and_action: 缺口、风险和补证动作
```

规则：

1. 先判断案件是否属于法〔2025〕82号67类，再决定使用普通诉状还是官方要素式逐栏填充稿。
2. 当事人选择要素式文本时，保留现行官方要素和格式设置；内容过长可扩行、附页或在自由填写区补充，不得删除不利字段。
3. 当事人选择普通诉状时，仍用上述矩阵完成内部审查，正文不必机械展示所有表格字段。
4. 不适用栏可填“无”或按官方说明不填；关键事实确实不知道时写“待核实／不知道”，不得推测。
5. 起诉与答辩为对向结构：原告每项请求均应有要件链；被告逐项承认、否认、不知或提出独立抗辩，并说明证据。
6. 调解意愿、电子送达和地址确认不得由AI代为选择或承诺。
7. 不得把法〔2024〕46号的旧表格、旧名称或旧字段作为当前成品。
8. 每一诉请保存`claim_id`；正文中的请求、事实、证据、法律理由和金额计算必须能回指同一`claim_id`。
9. 被告答辩为每一`claim_id`保存`position=admit|deny|partial|unknown`和具体理由；禁止用“一概不认可”替代逐项答辩。
10. 选中`conflicts_with`所列请求时，停止生成并要求改为主位／备位或作出明确选择。

案件输入对象：

```text
element_case:
  dispute: 纠纷名称或ELM编号
  role: plaintiff|defendant
  selected_claims[]: claim_id
  answers{}: question_id -> 已核实事实／待核实
  evidence{}: evidence_id -> 证据名称列表
  responses{}: claim_id -> position + reason
```

## 5. 民事起诉状示例骨架

```text
民事起诉状

原告：{{ plaintiff.full_identity }}
被告：{{ defendant.full_identity }}
{% for third_party in third_parties %}第三人：{{ third_party.full_identity }}{% endfor %}

诉讼请求
{% for claim in claims %}{{ loop.index }}. {{ claim.executable_text }}；{% endfor %}

事实与理由
一、{{ relationship.heading }}
{{ relationship.evidence_anchored_facts }}
二、{{ breach_or_tort.heading }}
{{ breach_or_tort.evidence_anchored_facts }}
三、{{ claim_basis.heading }}
{{ claim_basis.concise_reasoning }}

此致
{{ competent_court.full_name }}

起诉人：{{ plaintiff.signature }}
{{ signing_date }}

附：
1. 起诉状副本 {{ copies }} 份；
{% for item in attachments %}{{ loop.index + 1 }}. {{ item.name }} {{ item.count }}；{% endfor %}
```

生成前校验主体、请求、管辖、前置程序、诉讼时效、金额计算、证据和副本数量。

## 6. 程序申请通用骨架

```text
{{ document.title }}

申请人／异议人／上诉人：{{ applicant.full_identity }}
相对方：{{ counterparty.full_identity }}

请求事项
{% for request in requests %}{{ loop.index }}. {{ request.specific_text }}；{% endfor %}

事实与理由
{{ procedural_trigger.evidence_anchored_facts }}
{{ legal_reasoning.current_verified_basis }}

此致
{{ competent_court.full_name }}

{{ filing_party.role }}：{{ filing_party.real_signature }}
{{ signing_date }}

附：{{ attachments.verified_list }}
```

生成前必须核对申请资格、程序阶段、法定期限、受理法院、明确请求、触发事实、证据、授权和附件份数；签名和日期缺失时保留待填变量。
