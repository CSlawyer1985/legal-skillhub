# 诉讼期限日历（Litigation Deadline Calendar）

一个根据排期令为诉讼和仲裁期限制作日历的插件。

## 它的功能

上传一份排期令 PDF，此插件将：

1. 询问您辖区或仲裁论坛（它绝不猜测）
2. 解析排期令并提取所有关键日期
3. 核验适用的程序规则仍然现行，并提供来源 URL 以便您自行检查
4. 计算向后期限（送达发现的最后一天、专家披露、动议答复日期等）
5. 生成可导入 Outlook 的 .ics 日历文件

## 支持的辖区与论坛

**诉讼（内置规则）：**
- 科罗拉多（CRCP）— 完整的第 6 条时间计算、发现、专家和动议期限
- 联邦（FRCP）— 含 3 天电子送达增加
- 其他州 — 运行时从官方来源查询

**仲裁（内置规则）：**
- AAA 商业仲裁规则
- AAA 雇佣仲裁规则
- JAMS 综合仲裁规则
- JAMS 简化仲裁规则

技能将始终询问适用哪个辖区或论坛。它不默认任何辖区。

## 规则核验与来源

每次技能运行时，它都会搜索近期规则修订，以确认内置规则仍然现行。然后提供官方规则文本的来源 URL，以便您独立核验期限。来源在核验步骤期间和最终输出中与计算的期限一同出现。

## 安装

此插件直接从 GitHub 安装到 Claude Cowork — 无需编码。

**要求：** 带 Cowork 访问权限的 Claude Desktop（Pro、Team 和 Enterprise 套餐包含）。

**第 1 步：打开 Claude Desktop 并切换到 Cowork**

启动 Claude Desktop 应用并点击 **Cowork** 选项卡。

**第 2 步：打开 Customize 菜单**

点击左侧边栏中的 **Customize**。

**第 3 步：将此仓库添加为市场（marketplace）**

点击 **+** 按钮，然后选择 **Add marketplace from GitHub**。输入此仓库 URL：

```
https://github.com/djmarcuslaw/litigation-deadline-calculator-claude
```

**第 4 步：安装插件**

市场加载后，您会看到列出的 **Litigation Deadline Calendar** 插件。点击 **Install**。

就这样。插件自动激活 — 无需进一步设置。

## 使用方法

说类似这样的话：
- "Calendar the deadlines from this scheduling order"
- "I need to set up deadline tracking for a new case"
- "Parse this scheduling order and give me an .ics file"

技能将引导您提供事项名称、辖区/论坛以及要邀请的任何与会者。

## 日历条目格式

所有条目遵循格式：**[Matter Name] — [Deadline Description]**

示例："Smith v. Jones Co. — Last Day to Serve Interrogatories"

## 提醒

每个日历条目包含每个期限前 7 天和 1 天的自动提醒。

## 重要免责声明

这些期限是根据排期令和适用规则计算的。它们应由律师独立核验。地方法规、法官特定实践和修订后的排期令可能影响实际期限。本工具仅供参考，不构成法律意见。

## 许可证

MIT © Dave Marcus 2026

**非商业优先**：对个人、学术和开源使用免费。请勿出售本技能或将其纳入付费产品 — 请改为链接回来！
