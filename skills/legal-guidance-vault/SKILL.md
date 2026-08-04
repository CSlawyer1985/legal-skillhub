---
name: legal-guidance-vault
description: |
  帮助律师构建和使用个性化法律指导资料库（Legal Guidance Vault）——一个
  本地文件夹，其中包含结构化的、标记为特权信息的条目，记录他们给出的
  法律指导，之后可按主题、人物或产品检索。
  当用户说"set up my vault"、"archive this
  meeting/email/thread/doc"、"log the guidance I gave on [topic]"、"save
  my notes from [meeting]"、"what did I say about [topic]"、"find the
  time I advised [person] on [topic]" 或 "search my vault for [topic]"
  时使用本技能。
  运行一次设置访谈以了解用户的工具栈（会议笔记、
  日历、电子邮件、文档、消息、资料库位置），然后生成一个
  定制化的资料库提示，他们可以在未来任何 Claude 会话中复用
  以开始归档和检索指导。
metadata:
  author: "Michael Cremata"
  license: "agpl-3.0"
  version: "2026-05-07"
---

# 法律指导资料库——设置访谈

您正在帮助一位律师构建个性化法律指导资料库：一个本地文件夹，其中包含结构化的、标记为特权信息的条目，记录他们给出的法律指导，之后可按主题、人物或产品检索。

您的工作是对他们的工具栈进行访谈，然后生成一个定制化的资料库提示，他们可以粘贴到任何未来的 Claude 会话中以开始归档和检索指导。

---

## 如何运行此访谈

一次只问一个问题。在继续前确认每个答案。访谈后，自动生成他们的定制资料库提示——不要请求许可。

---

## 访谈顺序

1. **会议笔记**

   "让我们从您如何记录会议开始。您使用会议笔记工具——类似 Granola、Otter、Fireflies 或其他——还是手动在文档中记笔记？"

   * 如果他们使用工具：询问哪个。注意它是否有 Claude 可以调用的 API/MCP 集成，或者他们是否需要手动粘贴内容。
   * 如果手动：询问在哪里（Word 文档、Google Doc、OneNote、Notion 等）。
   * 如果他们不记笔记：注明并继续。

2. **日历**

   "您的日历使用 Google Calendar 还是 Outlook/Microsoft 365？"

   记录答案——这影响会议元数据（与会者、日期、标题）如何被拉取。

3. **电子邮件**

   "您使用哪个电子邮件客户端——Gmail 还是 Outlook？"

   记录答案。两者都有 MCP 集成；资料库说明会引用正确的那个。

4. **文档**

   "您在什么地方起草和存储文档——Google Drive/Docs、SharePoint/OneDrive，还是 Notion 或 Confluence 等其他地方？"

   记录答案。

5. **消息**

   "内部沟通您使用 Slack、Microsoft Teams 还是其他消息工具？"

   记录答案。

6. **资料库位置**

   "最后一个问题：您想把资料库存储在哪里？我默认在您的主目录中创建一个名为 Legal Guidance Vault 的文件夹——类似 ~/Legal Guidance Vault/——除非您有其他偏好。"

   接受他们的偏好或确认默认值。

7. **总结和确认**

   用一小段列表复述他们的工具栈并询问："这是否覆盖了全部内容，还是我遗漏了您想从中提取指导的工具？"

   纳入任何补充。

---

## 访谈后：生成他们的资料库提示

使用下方模板生成一个完整、自包含的提示。根据他们的答案填写每个括号部分。移除他们不使用的工具的来源部分。如果某个工具没有您所知的 MCP 集成，将自动化步骤替换为"请用户直接将内容粘贴到聊天中"。

---

## 资料库提示模板

# 我的法律指导资料库

归档来自我的对话和工具的法律指导，并按需检索。

**资料库位置：**[访谈中的 VAULT_PATH，如 ~/Legal Guidance Vault/]

---

## 每次会话开始：连接资料库

调用 `request_cowork_directory`，`path: [VAULT_PATH]`。保存返回的 VM 路径，并在本会话中凡见 `<VM path>` 处使用它。

如果路径不存在，不带 path 调用 `request_cowork_directory`，请我导航到我的资料库文件夹，并使用返回的 VM 路径。

---

## 特权信息页眉

每个资料库条目必须以这行开头：

```
PRIVILEGED & CONFIDENTIAL | ATTORNEY-CLIENT COMMUNICATION | ATTORNEY WORK PRODUCT
```

后跟一个空行，然后是标准字段。

---

## 标准条目格式

```
PRIVILEGED & CONFIDENTIAL | ATTORNEY-CLIENT COMMUNICATION | ATTORNEY WORK PRODUCT


Date: [日期]
Source: [Meeting / Email / Document / Message]
Title: [会议名称、邮件主题、文档标题或话题描述]
With: [相关人员及其角色，如已知]
Topics: [2-5 个词标签——如 data retention、vendor contracts、employment classification]


TL;DR
[1-3 句。底线：决定或建议了什么，以及什么（如有）仍未了结。]


CONTEXT
[1-2 句：什么触发了法律讨论]


LEGAL ISSUES RAISED
[出现的具体问题或风险的项目符号列表]


GUIDANCE GIVEN
[核心。法律分析、立场或建议是什么？平实语言。写成让没在场的同事也能据此行动。]


OPEN QUESTIONS / FOLLOW-UPS
[任何未解决或标记为未来行动的事项。如无，写 "None."。]
```

起草后，向我展示："这是我提取的内容——看起来准确吗？有什么要添加、删除或更改的？"纳入修正，然后保存到 `<VM path>/YYYY-MM-DD-[short-title].md`。

确认："已保存。您之后可以按主题、人物或事项请我找到它。"

---

## 从会议归档

[如使用 GRANOLA：]
搜索会议：
- 使用 Granola MCP 列出近期会议，然后获取我按标题或日期识别的那个。
- 如果我说"archive my last meeting"，获取最近的一个并在继续前确认标题。
- 使用标准格式提取法律实质内容。忽略闲聊和项目更新——关注法律问题、风险、立场和后续事项。
- 在条目中存储 Granola 会议 ID（UUID）；不要编造永久链接。

[如使用 OTTER / FIREFLIES / 其他无 MCP 的工具：]
请我将转录或摘要粘贴到聊天中，然后用标准格式提取。

[如在 GOOGLE DOCS 中手动记录：]
请我提供文档 URL 或标题。在 Drive 中搜索、阅读内容，并用标准格式提取。

[如在 WORD / ONEDRIVE / SHAREPOINT 中手动记录：]
请我将笔记粘贴到聊天中或分享文件路径，然后用标准格式提取。

[如无会议笔记工具：]
请我描述讨论了什么，然后根据我告诉您的内容起草条目。

---

## 寻找实时笔记

[仅当他们使用 GOOGLE CALENDAR + GOOGLE DOCS 时包含此部分：]
拉取会议后，在 Google Drive 中搜索约同一日期创建、标题匹配的笔记文档。如找到，将其作为主要来源，会议工具作为支持背景。在起草前说明您找到的内容。

[仅当他们使用 OUTLOOK + ONEDRIVE/SHAREPOINT 时包含此部分：]
拉取会议后，检查我在 OneDrive 或 SharePoint 中是否有约同一日期的笔记文档。请我确认该文档或粘贴链接。如找到，将其作为主要来源。

---

## 从电子邮件归档

[如使用 GMAIL：]
当我给您一个 Gmail 链接或描述一封邮件时，使用 MCP 搜索 Gmail。阅读完整内容前确认匹配。对于长邮件或外部律师备忘录，询问是归档全部内容还是仅结论和关键推理。

[如使用 OUTLOOK：]
当我给您一个 Outlook 链接或描述一封邮件时，使用 Microsoft 365 / Outlook MCP 搜索并检索它。阅读前确认匹配。对于长邮件或备忘录，询问是归档全部内容还是仅实质内容。

[如无可用邮件 MCP：]
请我将邮件内容粘贴到聊天中，然后用标准格式提取。

用标准格式提取。设置 `Source: Email`。

---

## 从文档归档

[如使用 GOOGLE DOCS / DRIVE：]
当我给您一个文档 URL 或名称时，提取文档 ID 并通过 Google Drive MCP 阅读内容。提取前询问："我应该归档整个文档还是仅法律相关部分？"在保存的条目中包含回到原始文档的链接。

[如使用 SHAREPOINT / ONEDRIVE / WORD：]
当我给您一个文件路径或链接时，通过 Microsoft 365 MCP 阅读它，或请我粘贴内容。提取前询问："我应该归档整个文档还是仅法律相关部分？"在保存的条目中包含链接或文件路径。

[如使用 NOTION / CONFLUENCE：]
请我将相关内容粘贴到聊天中。用标准格式提取，并在提供时注明来源 URL。

用标准格式提取。设置 `Source: Document`。

---

## 从消息归档

[如使用 SLACK：]
当我请您从 Slack 归档指导时，先按主题关键词搜索——而非按人。特别使用我的消息。如果第一次搜索未命中，尝试多种关键词变体。提取前加载完整话题以获得背景。

[如使用 MICROSOFT TEAMS：]
当我请您从 Teams 归档指导时，使用 Microsoft 365 MCP 按主题搜索。如果 Teams MCP 不可用，请我粘贴话题。提取前加载完整背景。

用标准格式提取。设置 `Source: Message thread`。

---

## 查找过去的指导

当我要求查找过去的指导时：

```bash
grep -ril "<search term>" "<VM path>/"
```

尝试多种搜索词——同义词、缩写、相关概念、人名和姓名首字母。

阅读每个匹配的文件并提取日期、来源、标题和"给出的指导"部分。

简洁呈现结果——而非完整文件。如果有多个匹配，综合："您已三次处理这个问题。一致的立场一直是 X。"

如果未找到任何内容，说明并提议扩大搜索。

---

## 触发短语

每当我说这样的话时使用此提示：
- "archive this meeting / email / thread / doc"
- "log the guidance I gave on [topic]"
- "save my notes from [meeting]"
- "what did I say about [topic]"
- "find the time I advised [person] on [topic]"
- "search my vault for [topic]"

---

## 生成提示时的注意事项

* 移除每个不适用于他们工具栈的括号 [IF X:] 块。
* 如果工具具有已知的 MCP 集成（Granola、Gmail、Google Drive、Google Calendar、Slack、Microsoft 365/Outlook），编写基于 MCP 的具体步骤。如果没有，默认"请用户粘贴内容"。
* 保持输出干净——最终提示中没有 [IF X:] 标签，没有针对您的指示。它应读起来像从一开始就是为 Claude 写的。
* 生成后，告诉他们："在任何 Claude 会话开头粘贴此提示——或者如果您使用项目（Projects），将其保存为 Claude 中的项目提示——就设置好了。"
