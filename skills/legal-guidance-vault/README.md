# 这是什么？

Legal Vault 是一个 Claude 技能，为您的法律指导提供长期记忆——无论发生在哪里。在任何会议、Slack 话题、电子邮件或 Google Doc 之后，您都可以请 Claude 将其归档。Claude 提取法律相关内容，生成简短的结构化摘要并保存。任何内容存储前都经您审查和确认。

从那时起，您可以请 Claude 按主题、问题、产品、参与人或大致时间找到该指导——哪怕一年之后。

## 您可以归档什么

- 会议——Claude 从 Granola（您的 AI 会议记录器）拉取笔记并提取法律实质内容。
- Slack 话题——将话题 URL 粘贴到 Claude，或对任何消息用 :file-cabinet: 表情回应，Claude 会自动找到它。
- 电子邮件——粘贴 Gmail 链接或描述邮件（"Kirkland 关于生物识别同意的备忘录"），Claude 会找到并提取。对外部律师备忘录和意见书效果最佳。
- Google Docs——粘贴文档 URL。Claude 会询问是归档整个文档还是仅归档法律相关部分。

## 开始前需要什么

1. Cowork

Claude 桌面应用。它是运行技能的载体。

2. Granola（用于会议归档）

Granola 是一个免费 Mac 应用，记录并总结您的会议。它与 Google 日历集成并从您的电脑捕获音频——没有机器人加入您的通话。在 granola.so 下载。用您的工作 Google 账户登录。

3. 已连接的账户（用于 Slack、Gmail 和 Drive）

Slack、Gmail 和 Google Drive 必须先连接到 Cowork，Claude 才能访问它们。连接方式如下：

1. 在您的 Mac 上打开 Claude Desktop。
2. 点击左下角的插头图标（⚡）打开集成。
3. 在列表中找到 Slack、Gmail 和 Google Drive。
4. 点击每个旁边的 Connect（连接）并完成在打开的浏览器窗口中进行的登录流程。

如果之后连接断开（如 Claude 说无法访问 Slack），回到集成并重新连接。每个服务只需做一次。

4. 技能文件

一个名为 "legal-guidance-vault.skill" 的文件——由分享本指南的人提供。双击安装一次。

## 安装（仅一次）

### 第 1 步——导入现有会议笔记（可选）

如果您有来自 @meetingnotes 模板的 Google Drive 会议笔记，先批量导入。从与本指南相同的 Drive 文件夹下载 legal-guidance-vault-import.skill 并双击安装。然后请 Claude："从 Drive 导入我现有的会议笔记。"只运行一次。

### 第 2 步——安装 Granola

从 granola.so 下载并打开 Granola。用您的 Google 账户登录并授予日历和麦克风权限。

### 第 3 步——安装技能

双击 "legal-guidance-vault.skill"。Cowork 会要求您确认——点击 Install（安装）。

## 如何归档

### 从会议（Granola）

会议结束后，告诉 Claude："归档我与 [团队/人员] 的会议。"Claude 在 Granola 中找到它、提取法律实质内容、向您展示草稿，并在您确认后保存。

您也可以只说"归档我上一次会议"，Claude 会识别并在继续前确认标题。

要将其设置为每日或每周自动扫描，告诉 Claude："为 Granola 会议笔记设置每日/每周扫描。"Claude 会配置一个每天/每周提示您的定时任务。[此处查看示例说明]

### 从 Slack——手动

复制任何 Slack 话题的链接（右键点击消息 → Copy link）并粘贴到 Claude，附上"archive this thread"（归档此话题）。Claude 获取话题及周围频道上下文、综合完整交流内容（包括业务背景）、向您展示草稿，并在确认后保存。

### 从 Slack——表情扫描（设置一次）

对任何 Slack 消息用 :file-cabinet: 表情回应，将其标记为待归档。要处理已标记的消息，告诉 Claude："scan for my emoji-flagged Slack threads"（扫描我标记了表情的 Slack 话题）。Claude 找到所有您用该表情回应的消息、获取每个话题，并逐个呈现供审查。

要将其设置为每日或每周自动扫描，告诉 Claude："Set up a weekly scan for my :file-cabinet: Slack reactions"（为我的 :file-cabinet: Slack 回应设置每周扫描）。Claude 会配置一个每周提示您的定时任务。[此处查看示例说明]

### 从电子邮件

将 Gmail 链接粘贴到 Claude 并说"archive this email"（归档此邮件）。或描述邮件——"三月份 Wilson Sonsini 关于数据传输问题的意见书"——Claude 会搜索您的收件箱、确认匹配、提取指导并保存。

### 从 Google Doc

粘贴 Google Doc URL 并说"archive this doc"（归档此文档）。Claude 会询问："归档整个文档还是仅相关部分？"无论哪种方式，保存的条目始终包含回到原始文档的链接。

## 如何找到过去的指导

只需自然地询问 Claude：

- "找到我给 Tasks 团队关于 BIPA 的指导。"
- "我关于双方同意说过什么？"
- "我之前处理过 Commerce Platform 的地理扩张吗？"
- "我从外部律师那里收到过关于数据传输的电子邮件指导吗？"
- "我说过关于知识产权归属的什么——大概一年前。"

Claude 搜索您的资料库并返回匹配条目，每条带 TL;DR 和关键指导。如果有多个匹配，它会综合： "您已三次处理这个问题。一致的立场一直是 X。"

## 如何调整或更新技能

只需告诉 Claude："我想更新我的 Legal Vault 技能。我们可以改 [X] 吗？"Claude 会编辑它、向您展示更改内容，并给您一个更新后的 .skill 文件供双击重新安装。

## 提示

选择性归档——只归档您提供或收到值得以后查找的指导的话题、电子邮件和文档。资料库在信号密集时最有用。

资料库是您 Mac 上的纯文本文件。不会对外共享任何内容。

归档 Slack 话题时，Claude 捕获完整对话，包括业务背景——而不仅仅是您的消息。该背景对于理解您为什么说那些话往往至关重要。

对于带长备忘录的外部律师邮件，通常只需归档结论和关键推理就足够了。Claude 会询问您是想要全部内容还是相关部分。

---

## 附录

### Granola 扫描说明

设置一个每周定时任务来扫描我的 Granola 会议笔记。

日程：每周 [周五] [上午 11 点] [山区时间]

每次运行应：

1. 检查 ~/Claude Cowork/Data/legal-guidance-vault/.scan-state.json 状态文件，获取上次运行日期和已归档的会议 ID（首次运行默认 7 天前）
2. 获取自上次运行以来的所有 Granola 会议
3. 过滤掉任何已归档的
4. 向我显示编号列表——会议标题、日期、与会者、一行摘要
5. 询问我想归档哪些到法律指导资料库
6. 对于我选择的每个：显示完整笔记、使用 legal-guidance-vault 技能格式起草资料库条目、与我确认，然后保存到 ~/Claude Cowork/Data/legal-guidance-vault/
7. 用今天的日期和新归档的会议 ID 更新状态文件

使用 legal-guidance-vault 技能作为归档格式，使用 Granola CLI 获取会议。

### Slack 扫描说明

设置一个每周定时任务，扫描我标记了 🗄️ 表情的 Slack 话题。

日程：每周 [周五] [上午 11 点] [山区时间]

我的 Slack ID：[查找方法：在 Slack 中点击您的头像 → Profile → 三点菜单 → Copy member ID]

每次运行应：

1. 检查 ~/Claude Cowork/Data/legal-guidance-vault/.scan-state.json 获取上次 Slack 扫描日期和已归档的话题 ID
2. 搜索 Slack 中自上次扫描以来标记了 🗄️ 的消息——尝试 has::file_cabinet:、has::filing_cabinet: 以及文本中的表情字符，限定在我的消息范围内
3. 过滤掉已归档的话题
4. 向我显示编号列表——频道、日期、参与者、一行摘要
5. 询问我想归档哪些到法律指导资料库
6. 对于我选择的每个：显示完整话题、使用 legal-guidance-vault 技能格式起草资料库条目、与我确认，然后保存到 ~/Claude Cowork/Data/legal-guidance-vault/
7. 更新状态文件而不覆盖其他键（应保留 Granola 扫描数据）

使用 legal-guidance-vault 技能作为归档格式。
