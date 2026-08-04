---
name: litigation-deadline-calendar
description: >
  根据排期令为诉讼和仲裁期限制作日历。解析 PDF 排期令、识别关键日期、使用适用规则（科罗拉多 CRCP、联邦 FRCP，或 AAA/JAMS 的仲裁论坛规则）计算向后期限，并生成可导入 Outlook 或 Google 日历的 .ics 日历文件。

  每当用户提及以下内容时使用本技能：诉讼期限、排期令、案件管理令、期限日历制作、发现期限、庭审准备期限、仲裁排期，或任何与计算或跟踪法院或仲裁期限相关的内容。当用户上传看似法院排期令或仲裁排期令的 PDF 时也触发。
metadata:
  author: "Dave Marcus"
  license: "mit"
  version: "2026-05-12"
---

# 诉讼期限日历（Litigation Deadline Calendar）

本技能接收排期令（PDF 上传）、确定适用的程序规则、提取关键日期、计算所有向后期限，并生成用户可导入 Outlook 或 Google 日历的 .ics 日历文件。

## 快速开始工作流

1. **收集信息**（来自用户）
2. **解析排期令** PDF
3. **核验规则**仍然现行
4. **使用脚本计算期限**
5. **生成 .ics 文件**并交付给用户

---

## 步骤 1：收集信息

向用户询问以下内容。他们可能提前提供其中一些；填入您已有的内容并询问其余部分。

**必需：**
- 排期令 PDF（上传的文件）
- 事项名称（用户希望它在日历条目上如何显示，如"Smith v. Jones Co."）
- 程序类型：**litigation**（诉讼）或 **arbitration**（仲裁）

**如为诉讼：**
- 辖区：**先尝试从排期令确定。** 寻找法院名称、案号格式或页眉以识别辖区。常见模式：
  - "District Court, ___ County, Colorado" → 科罗拉多
  - "United States District Court" → 联邦
  - "Superior Court of California" → 加利福尼亚
  - 法院标题中的州名 → 该州
  如果排期令清楚识别了辖区，与用户确认："This appears to be a [State] case based on the court name. Can you confirm?"
  如果**无法从 PDF 确定辖区**，始终明确询问用户。**绝不猜测或默认。** 未提供辖区时工具将报错。
- 送达方式：**electronic**（电子，默认）、**mail**（邮寄）、**hand**（人工）或 **fax**（传真）。送达方式对期限计算的影响因辖区而异：
  - 科罗拉多：电子送达加 0 天，邮寄加 3 天
  - 联邦：电子送达加 0 天，邮寄加 3 天
  - 加利福尼亚：电子送达加 2 个法院日，邮寄加 5 天（州外 10 天）
  - 纽约：电子送达加 5 天，邮寄加 5 天（州外 6 天）
  - 佛罗里达：电子送达加 0 天，邮寄加 5 天
  - 佐治亚/马萨诸塞/新泽西：电子送达加 3 天，邮寄加 3 天
  - 得克萨斯/伊利诺伊/宾夕法尼亚/俄亥俄：电子送达加 0 天，邮寄加 3 天
  对加利福尼亚和纽约的邮寄送达，还询问送达是州内还是州外（州内用"mail"，州外用"mail_out_of_state"）。

**如为仲裁：**
- 论坛：AAA Commercial、AAA Employment、JAMS Comprehensive 或 JAMS Streamlined

**可选（但先检查已保存的偏好）：**
- 日历应用：**Outlook**（默认）或 **Google Calendar**。这控制 .ics 输出格式。Google 日历模式使用确定性 UID（因此重新导入会去重）、省略 VTIMEZONE 和 VALARM 块（Google 会忽略它们），并使用 LF 行尾。
  **持久化：** 在询问之前，检查 CLAUDE.md 中是否有已保存的 `calendar_app` 偏好（如 `calendar_app: google` 或 `calendar_app: outlook`）。如果找到，静默使用 — 不要重新询问。如果未找到，询问用户使用哪个日历应用并将其选择保存到 CLAUDE.md，以便延续到未来会话。CLAUDE.md 条目示例：`calendar_app: google`
- 与会者电子邮件地址（要邀请到日历条目的人）
- 他们已知的任何异常或经法院修改的期限

**内置辖区**（完整规则数据库，含州特定假日、送达天数增加、短期间计算阈值和发现答复期间）：科罗拉多、联邦、加利福尼亚、纽约、得克萨斯、佛罗里达、伊利诺伊、宾夕法尼亚、俄亥俄、佐治亚、新泽西、马萨诸塞。

**其他辖区**：工具将使用保守的联邦式默认值，技能应在计算前进行网络搜索核验该特定州的规则。始终警告用户非内置辖区的期限应独立核验。

将其呈现为简单对话，而非表单。例如：
"您希望事项名称在日历条目上如何显示？"
"这是诉讼还是仲裁？"
"这看起来来自丹佛县地区法院 — 这是科罗拉多州案件吗？"

---

## 步骤 2：解析排期令

使用 Read 工具读取上传的 PDF。提取排期令中提到的每个日期及其代表的内容。要寻找的常见日期：

**诉讼排期令通常包括：**
- 庭审日期
- 发现截止 / 完成日期
- 处分性动议（dispositive motion）期限
- 审前 / 庭审准备会议日期
- 修改诉状期限
- 追加当事人期限
- 原告专家披露期限
- 被告专家披露期限
- 反驳专家披露期限
- 调解期限
- 审前动议（motions in limine）期限
- 拟议陪审团指示期限
- 证人和证据清单期限

**仲裁排期令通常包括：**
- 听证日期
- 发现 / 信息交换截止
- 专家披露期限
- 听证前陈述期限
- 证据交换期限
- 证人清单期限
- 处分性动议期限（如允许）
- 调解期限

解析后，**向用户展示您发现的内容**并请他们在继续前确认。格式化为干净清单：

"以下是我从排期令中提取的内容：
- Trial Date: September 15, 2026
- Discovery Cutoff: July 28, 2026
- Dispositive Motion Deadline: June 15, 2026
[etc.]

这看起来对吗？有遗漏或弄错的吗？"

此确认步骤很重要，因为 PDF 解析可能遗漏日期或误解它们，而此处的错误会级联到每个计算的期限。

---

## 步骤 3：核验规则仍然现行

在计算期限之前，核验规则并提供来源。

**核验程序：**
1. 在网上搜索适用规则的当前文本以及任何近期修订：
   - 对科罗拉多：在 coloradojudicial.gov 上搜索"Colorado Rules of Civil Procedure amendments [current year]"和"CRCP rule changes [current year]"
   - 对联邦：搜索"Federal Rules of Civil Procedure amendments [current year]"
   - 对其他州：搜索"[State] rules of civil procedure [current year]"
   - 对 AAA：搜索"AAA arbitration rules update [current year]"
   - 对 JAMS：搜索"JAMS arbitration rules update [current year]"

2. **核验州假日。** 工具为 12 个州内置了假日函数，但假日可能且确实会变化（州可能新增、重命名或移除假日）。搜索：
   - "[State] legal holidays [current year]"
   - "[State] court holidays [current year]"
   - "[State] court closures [current year]"
   将您找到的内容与脚本将计算的假日比较。如果某州新增、重命名或移除了假日，告诉用户并调整计算。假日弄错可能静默地将期限推移一天。

3. 对内置辖区，将您找到的内容与参考文件及 `scripts/compute_deadlines.py` 中的 `STATE_RULES` 字典比较：
   - 科罗拉多：`references/colorado-crcp.md`
   - 联邦：`references/federal-frcp.md`
   - 仲裁：`references/arbitration-rules.md`
   - 其他内置州：检查脚本中的 `STATE_RULES` 条目

4. 如果发现不一致（在规则或假日中）：
   - 告诉用户："I found that [rule/holiday X] was changed on [date]. The built-in version says [old]; the current version says [new]. I'll use the updated version for this calculation."
   - 使用修正后的规则或假日进行计算。

5. 如果无法核验（如检索失败）：
   - 告诉用户："I wasn't able to verify whether the [jurisdiction] rules have been updated recently. The built-in rules are current as of early 2026. You may want to independently confirm the key time periods."

**对非内置辖区**（科罗拉多以外的任何州）：
搜索该特定州的民事诉讼规则，重点：
- 时间计算规则（第 6 条等效）
- 发现答复期限
- 专家披露期限
- 简易判决时间线
- 法定假日

将您找到的内容呈现给用户确认后再计算。

**来源引注要求 — 这是强制性的：**
核验规则后，始终向用户提供"Sources"部分，列出他们可以独立检查所应用规则的具体 URL。这至关重要，因为用户管理外部律师，需要能够独立核验规则。格式：

"**Sources for [Jurisdiction] rules used in this calculation:**
- [Rule description]: [URL to official source or authoritative reference]
- [Rule description]: [URL]"

按辖区的首选官方来源：
- 科罗拉多：coloradojudicial.gov 或 courts.state.co.us
- 联邦：law.cornell.edu/rules/frcp 或 uscourts.gov
- AAA：adr.org
- JAMS：jamsadr.com
- 其他州：该州司法机构的官方网站

如果无法为某条规则找到官方来源，明确说明，而非省略引注。

---

## 步骤 4：计算期限

为计算脚本创建输入 JSON 文件。格式为：

```json
{
    "matter_name": "Smith v. Jones Co.",
    "proceeding_type": "litigation",
    "jurisdiction": "colorado",
    "forum": "",
    "service_method": "electronic",
    "scheduling_order_dates": {
        "trial_date": "2026-09-15",
        "discovery_cutoff": "2026-07-28",
        "dispositive_motion_deadline": "2026-06-15",
        "pretrial_conference": "2026-08-15",
        "plaintiff_expert_disclosure": null,
        "defendant_expert_disclosure": null,
        "rebuttal_expert_disclosure": null,
        "amend_pleadings_deadline": "2026-03-15",
        "join_parties_deadline": "2026-03-15",
        "mediation_deadline": "2026-05-01",
        "hearing_date": null,
        "custom_dates": {
            "Motions in Limine": "2026-08-01",
            "Proposed Jury Instructions": "2026-08-01"
        }
    },
    "attendees": ["jane@company.com", "bob@lawfirm.com"]
}
```

排期令中没有的日期用 `null`。脚本将在适用处按规则计算它们（如从庭审日期向后计算专家期限）。

将排期令中不属于标准字段的任何日期添加到 `custom_dates` 并附描述性标签。

### 任何期限条目上的可选字段

计算出的期限 JSON（`compute_deadlines.py` 的输出）支持单个期限条目上的三个可选字段，控制它们在 .ics 日历中的显示：

- **`time`**（字符串，24 小时制 HH:MM）：使事件成为定时事件而非全天。示例：`"time": "08:30"`。如果未提供明确结束时间，事件假定在最后一天 17:00 结束。
- **`timezone`**（字符串，IANA 时区）：定时事件的时区。示例：`"timezone": "America/Denver"`。省略时默认为 `America/Denver`。
- **`duration_days`**（整数）：使事件跨越数天。示例：5 天庭审用 `"duration_days": 5`，始于事件日期。与 `time` 结合时，事件在第 1 天指定时间开始，最后一天 17:00 结束。不与 `time` 结合时，创建多日全天事件。

这些字段对多日庭审或听证之类的事件很有用，或当排期令为会议或期限指定特定时间时。

运行计算：
```bash
python scripts/compute_deadlines.py --input /tmp/input.json --output /tmp/computed.json
```

审阅输出并对计算出的日期做健全性检查：
- 所有日期都落在工作日吗？
- 向后计算的日期在其锚定期限**之前**吗？
- 专家披露期限落在合理顺序中吗？
- 对仲裁：您用的是仲裁规则，而非诉讼规则吗？

---

## 步骤 5：生成 .ics 文件

运行日历生成。如果用户指定 Google 日历，添加 `--google` 标志：

```bash
# Outlook / Apple Calendar（默认）：
python scripts/generate_ics.py --input /tmp/computed.json --output /path/to/output/[matter_name]_deadlines.ics

# Google Calendar：
python scripts/generate_ics.py --input /tmp/computed.json --output /path/to/output/[matter_name]_deadlines.ics --google
```

Google 日历模式产出针对 Google 导入行为优化的文件：确定性 UID（重新导入会更新而非重复）、无 VTIMEZONE 块（Google 使用自己的时区数据库）、无 VALARM 条目（Google 忽略它们并应用自己的默认提醒），以及 LF 行尾。

输出文件应放入用户的工作区文件夹，文件名基于事项名称的描述性命名。

**在交付文件之前，向用户展示摘要：**

"以下是我为 [Matter Name] 计算的期限：

[List each deadline with date, description, and rule basis]

**关键期限**（以 !!! 标记）需要特别关注。

.ics 文件包含每个期限前 7 天和 1 天的提醒。
[如为 Google 日历模式：]注意：Google 日历使用自己的默认提醒，不会导入自定义提醒设置。
[如已指定与会者：]导入文件时，日历邀请将发送给 [names]。

**重要：** 这些期限是根据排期令和适用规则计算的。它们应由律师独立核验，尤其是地方法规和任何可能修改期限的后续命令。

**所应用规则的来源：**
[List each source URL used — same sources provided in Step 3]"

然后提供 .ics 文件链接。来源应始终出现在最终输出中，使用户紧邻期限即可获得，而不仅仅是在对话更早处、他们可能滚动略过的地方。

---

## 参考文件

读取这些参考文件以获取计算中使用的详细规则：

- **科罗拉多 CRCP 规则**：`references/colorado-crcp.md`
  - 辖区为科罗拉多时读取
  - 涵盖第 6 条（时间计算）、第 26/33/34/36 条（发现）、第 56 条（简易判决）

- **联邦 FRCP 规则**：`references/federal-frcp.md`
  - 辖区为联邦时读取
  - 关键区别：FRCP 对所有期间计算所有天数；电子送达加 3 天

- **仲裁规则**：`references/arbitration-rules.md`
  - 程序类型为仲裁时读取
  - 涵盖 AAA Commercial、AAA Employment、JAMS Comprehensive、JAMS Streamlined
  - 关键：不要把诉讼时间计算规则适用于仲裁

---

## 日历条目格式

所有日历条目遵循此格式：
**[Matter Name] — [Deadline Description]**

示例：
- Smith v. Jones Co. — Trial Date
- Smith v. Jones Co. — Last Day to Serve Interrogatories
- Smith v. Jones Co. — Plaintiff Expert Disclosure Deadline
- Smith v. Jones Co. — Arbitration Hearing

事项名称始终放在前面，使不同案件的条目在拥挤的日历中可视觉区分。

---

## 边界情况与警告

**排期令优先于默认规则：**
如果排期令设定的期限与规则会产生的不同（如更短的发现期），始终使用排期令日期。只对排期令中未指定的期限使用基于规则的计算。

**仲裁不是诉讼：**
如果用户说"arbitration"，绝不要适用 CRCP 或 FRCP 时间计算规则。仲裁期限来自仲裁员的命令和论坛规则。如果仲裁员的命令以引用方式纳入任何诉讼规则，向用户说明，但仍按仲裁员指定的方式适用它们。

**地方法规：**
对联邦案件，地方法规可能显著改变期限（尤其是简易判决答复和审前程序）。向用户标记："Federal courts often have local rules that modify these default deadlines. Check the local rules for [district] to verify."

**修订后的排期令：**
如果用户提到排期令已被修订，索取最新版本。较早版本可能含有已被取代的日期。

**已过的期限：**
如果任何计算的期限早于今天，突出标记："WARNING: [Deadline] computed as [date], which has already passed. Verify this is correct or whether an extension was granted."
