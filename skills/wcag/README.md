# 网页内容无障碍指南（WCAG）技能

> **免责声明：** 本技能基于 W3C WCAG 文档提供教育与咨询性指引。不构成法律意见。合规声明、无障碍声明和法律合规认定必须涉及合格的无障碍专家和法律顾问。WCAG 由 W3C 网页无障碍倡议（WAI）制定，并会持续修订——始终对照 w3.org/WAI/WCAG 上现行的规范性规范进行核实。

---

## 1. 本技能做什么？

本技能将 Claude 转变为**网页内容无障碍指南（WCAG）**——由网页无障碍倡议（WAI）制定的 W3C 数字无障碍国际标准——的专家顾问。它为在网页、移动端和数字内容中实施 WCAG 的开发者、设计师、产品负责人、QA 工程师和合规团队提供结构化的、逐标准的指引。

技能涵盖三项规范性 W3C 建议书：**WCAG 2.0**（2008 年）、**WCAG 2.1**（2018 年）和 **WCAG 2.2**（2023 年 10 月）。它以全部四项 POUR 原则为基础——可感知（Perceivable）、可操作（Operable）、可理解（Understandable）、稳健（Robust）——并掌握完整的成功标准集：WCAG 2.0 有 38 项标准，WCAG 2.1 新增 17 项，WCAG 2.2 再新增 9 项（并删除了 SC 4.1.1 解析）。它还提供 WCAG 3.0 工作草案及其新的青铜/白银/黄金（Bronze/Silver/Gold）评分模型的预览。

除标准解释外，技能还提供可立即实施的输出：含严重性和元素引用的无障碍审计问题表、合规审查、与 WAI-ARIA 作者实践指南键盘约定匹配的 ARIA 模式、对比度计算、含违规和修正示例的代码注释审查，以及符合欧盟网页无障碍指令模式的无障碍声明。它还将 WCAG 映射到全球法律格局——EN 301 549（欧盟 EAA）、第 508 条、英国 PSBAR 2018、AODA 和 ADA 第三编判例法——使合规团队能够了解各法域在法律上要求哪个 WCAG 版本和级别。

---

## 2. 目标受众

| 受众 | 使用方式 |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **前端开发者** | 逐标准代码修正、ARIA 模式实施、键盘交互模式（APG）、对比度检查、HTML 语义标记指引 |
| **UX 与视觉设计师** | 颜色对比要求（SC 1.4.3、1.4.11）、焦点指示器设计（SC 2.4.7、2.4.11）、触控目标尺寸（SC 2.5.8）、认知无障碍（SC 3.3.x） |
| **QA 与无障碍测试人员** | 审计方法论、辅助技术（AT）+ 浏览器配对、自动化工具选择、人工测试清单、逐标准测试程序 |
| **产品负责人与经理** | 合规级别选择、范围界定、整改优先级排序、发布门禁无障碍标准 |
| **合规与法务团队** | 各法域法律要求、无障碍声明起草、合规声明措辞、WCAG 版本与法律映射 |
| **内容作者与编辑** | 替代文本撰写、链接文本质量、标题结构、字幕要求、语言属性 |
| **无障碍顾问** | 详细标准指引、充分技术与失败技术引用、咨询性技术、跨版本兼容性分析 |
| **欧盟/英国公共部门团队** | EN 301 549、欧盟网页无障碍指令（2016/2102）、欧洲无障碍法案（EAA，指令 2019/882）合规 |

---

## 3. 常见用例

### 无障碍审计与差距评估

- 对我们的电子商务结账流程运行 WCAG 2.1 AA 无障碍审计差距评估
- 生成审计问题表，含标准编号、问题描述、元素引用、严重性和整改步骤
- 我们的自动化 axe 扫描得到这些发现——按 WCAG 标准分类并确定整改优先级
- 我们可能在哪项 WCAG 2.2 AA 标准上失败，而此前并未对照 WCAG 2.1 检查？
- 找出会阻碍屏幕阅读器用户使用的最严重 WCAG 2.1 AA 失败项

### 标准解释与实施指引

- 解释 SC 1.4.3 对比度（最低）——4.5:1 究竟是什么意思，我如何计算？
- SC 2.4.11 焦点不被遮挡要求什么？如何修复遮挡聚焦元素的粘性页眉？
- 带我了解实施 SC 3.3.8 无障碍认证——CAPTCHA 的什么替代方案算无障碍？
- SC 4.1.2 对自定义选项卡面板小部件要求哪些 ARIA 角色和属性？
- 解释 SC 2.5.7 拖拽动作与 SC 2.5.8 目标尺寸之间的区别——两者都是 WCAG 2.2 新增

### 代码审查与 ARIA 实施

- 审查这个 React 模态组件是否存在 WCAG 2.1 AA 违规
- 展示可展开和折叠的手风琴组件的正确 ARIA 模式
- 我的自动补全组合框没有被 NVDA 正确播报——我缺少哪些 ARIA 属性？
- 用所有 WCAG 失败项注释这个 HTML 表单，并提供修正版本
- 我应该使用什么 ARIA 实时区域模式向屏幕阅读器用户播报"商品已加入购物车"？

### 合规与无障碍声明

- 为我们的英国公共部门网站起草 WCAG 2.1 AA 级无障碍声明
- 无障碍声明必须包含什么才能符合欧盟网页无障碍指令？
- 我们声明 WCAG 2.1 AA 合规，但未通过 SC 1.2.4 字幕（实时）——如何记录此例外？
- WCAG 2.0 AA、2.1 AA 和 2.2 AA 合规声明有什么区别？
- 未通过一项 AA 标准的网站还能声明部分合规吗？

### 法律与监管映射

- 欧洲无障碍法案（EAA）对私营公司要求哪个 WCAG 版本和级别？
- 将 WCAG 要求映射到适用于欧盟、美国、英国、加拿大和澳大利亚的法律
- 我们的产品在欧盟使用——2025 年 6 月的 EAA 截止期限适用于我们吗？
- EN 301 549 与 WCAG 2.1 有什么关系，哪些章节涵盖网页内容？
- 客户说他们的 ADA 和解协议要求 WCAG 2.1 AA——这实际意味着什么？

### 测试方法论

- WCAG 2.1 AA 审计的推荐测试方法论是什么？
- 哪些自动化工具能发现最多的 WCAG 失败项，它们的局限是什么？
- 全面测试应使用哪些屏幕阅读器和浏览器组合？
- 如何在 320 CSS 像素下测试 SC 1.4.10 重排？
- 文本间距小书签测试什么？我如何用它测试 SC 1.4.12？

### WCAG 2.2 新标准

- WCAG 2.2 的所有新成功标准有哪些？哪些是 AA 级？
- 我们目前符合 WCAG 2.1 AA——要达到 WCAG 2.2 AA 还需要哪些额外工作？
- 解释 WCAG 2.2 中三项与焦点相关的新标准（SC 2.4.11、2.4.12、2.4.13）
- SC 4.1.1 解析在 WCAG 2.2 下仍然需要吗？
- SC 3.3.7 重复输入如何影响多步骤表单和结账流程？

---

## 4. 如何使用本技能

### 安装

1. 从 `WCAG - Claude Skill/` 文件夹下载 `wcag.skill` 文件
2. 在 Claude 中进入 **Settings → Skills**
3. 上传 `.skill` 文件
4. 技能会在相关对话中自动激活——无需特殊命令

### 触发技能

技能会自动触发于任何数字无障碍问题，即使未明确提及"WCAG"或"skill"。激活它的示例短语：

- _"Why is my site failing accessibility checks?"_（为什么我的网站没有通过无障碍检查？）
- _"What contrast ratio does this text need?"_（这段文本需要什么对比度？）
- _"My screen reader isn't reading the modal correctly"_（我的屏幕阅读器没有正确朗读模态框）
- _"We need to comply with EN 301 549 for the EU market"_（我们需要符合 EN 301 549 才能进入欧盟市场）
- _"Write an accessibility statement for our website"_（为我们的网站撰写无障碍声明）
- _"What changed in WCAG 2.2?"_（WCAG 2.2 有什么变化？）
- _"How do I make this dropdown keyboard accessible?"_（如何让这个下拉菜单支持键盘访问？）
- _"We got an ADA demand letter about our website's accessibility"_（我们收到了一封关于网站无障碍问题的 ADA 律师函）

### 示例提示词

```
"Run a WCAG 2.2 AA gap assessment for a SaaS web application. Known
issues include: no skip link, some icon buttons without accessible names,
drag-only sortable lists, a CAPTCHA with no alternative on the login page,
and colour-only required field indicators on forms."
```

```
"Review this React component for WCAG 2.1 AA violations and provide
the corrected version with inline comments explaining each fix:

<div onClick={handleClick} class='btn'>Submit</div>
<div class='error' style='color:red'>Please fix errors above</div>
<img src='logo.png'>
<div role='checkbox'>Accept terms</div>"
```

```
"Draft a WCAG 2.1 Level AA accessibility statement for a UK public
sector organisation. Include: conformance claim, scope, known
non-conformances (SC 1.2.4 live captions not provided, SC 2.4.5
no site search), alternatives available, date of last assessment,
and complaints procedure as required by PSBAR 2018."
```

```
"Map WCAG 2.1 AA to the accessibility laws that apply to us. We sell
software to: federal agencies in the US, enterprises in the EU,
public sector bodies in the UK, and large organisations in Ontario,
Canada. For each jurisdiction, tell us the required WCAG version,
level, applicable law, and compliance deadline."
```

```
"Our development team needs a practical WCAG 2.2 AA testing checklist.
For each criterion, include: what to test, which automated tool covers
it, which AT + browser combination to use for manual testing, and the
most common failure pattern."
```

---

## 5. 技能实现细节

### 架构

```
plugins/wcag/skills/wcag/
├── SKILL.md                        # Main skill: WCAG version history, POUR principles,
│                                   # full success criteria tables (2.0, 2.1, 2.2) with
│                                   # common failures, conformance levels, audit workflows,
│                                   # accessibility statement requirements, ARIA usage
│                                   # principles, contrast ratio calculation, global
│                                   # legal framework mapping, response format routing
└── references/
    └── criteria-detail.md          # Full WCAG 2.2 success criteria detailed reference:
                                    # sufficient techniques, failure techniques, advisory
                                    # techniques, ARIA key patterns, WCAG 2.2 new criteria
                                    # summary, automated testing tools comparison,
                                    # manual testing checklist, screen reader + browser
                                    # pairings, bookmarklets and extensions

WCAG - Claude Skill/
├── WCAG-README.md                  # This file
└── wcag.skill                      # Standalone installable skill file
```

### SKILL.md 包含的内容

- **YAML frontmatter**，含技能名称、描述，以及覆盖所有 WCAG 相关主题的宽泛自动触发短语
- **WCAG 版本表**——2.0（2008 年）、2.1（2018 年）、2.2（2023 年 10 月）、3.0（工作草案），含状态、主要新增内容和向后兼容说明
- **法律语境**——WCAG 作为欧盟 EAA、EN 301 549、第 508 条、英国《平等法》、AODA、ADA 第三编的技术基础
- **响应格式路由表**——任务类型到输出格式（标准解释、审计、合规审查、差距评估、无障碍声明、代码审查、法律映射、一般问题）
- **完整 POUR 标准表**——WCAG 2.0、2.1 和 2.2 的全部 A 级和 AA 级成功标准，含 SC 编号、级别（A/AA）、要求和常见失败项
- **合规级别**——A（最低）、AA（通用法律基准）、AAA（增强），并说明各自的法定相关性
- **审计工作流**——7 步完整无障碍审计方法论（自动化、键盘、屏幕阅读器、对比度、缩放/重排、认知、文档）
- **无障碍声明**——必需要素，含合规声明、范围、已知不合规项、替代方案、日期、联系方式、投诉程序
- **ARIA 使用原则**——五项关键规则，包括"无 ARIA 胜于劣质 ARIA"、ARIA 第一规则、各角色的必需属性、APG 键盘模式、实时区域
- **对比度计算**——SC 1.4.3（4.5:1 常规文本、3:1 大号文本）和 SC 1.4.11（3:1 UI 组件）的公式和阈值
- **全球法律框架映射**——9 法域表（EN 301 549、EAA、欧盟网页无障碍指令、第 508 条、ADA、英国 PSBAR 2018、《平等法》、AODA、澳大利亚 DDA），含要求的 WCAG 版本和级别

### 参考文件包含的内容

| 文件 | 内容 |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `references/criteria-detail.md` | 按指南（1.1–4.1）分组的 WCAG 2.2 全部 A 级和 AA 级成功标准的详细条目；充分技术（WCAG 技术代码：G、H、ARIA、F）；每个标准的常见失败技术代码（F 代码）；按小部件类型的 ARIA 必需属性（accordion 手风琴、alert 警报、autocomplete 自动补全、button 按钮、checkbox 复选框、combobox 组合框、dialog 对话框、menu 菜单、progressbar 进度条、radio 单选、slider 滑块、tablist 选项卡、tooltip 工具提示）；SC 4.1.3 ARIA 实时区域模式（aria-live、role="status/alert/log"、aria-atomic）；WCAG 2.2 新标准汇总表（9 项新 SC、删除的 SC）；自动化测试工具对比（axe-core、Lighthouse、WAVE、IBM Equal Access、Pa11y、Colour Contrast Analyser）及百分比覆盖率；人工测试清单（10 步）；屏幕阅读器 + 浏览器配对表；小书签和浏览器扩展参考 |

### 用于构建技能的资料

| 来源 | 说明 |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **WCAG 2.0 W3C 建议书（2008 年 12 月）** | 基础性 61 项标准，分布于 12 条指南和 4 项原则 |
| **WCAG 2.1 W3C 建议书（2018 年 6 月）** | 17 项新增标准，覆盖移动端、低视力和认知无障碍 |
| **WCAG 2.2 W3C 建议书（2023 年 10 月）** | 9 项新标准（SC 2.4.11–13、2.5.7–8、3.2.6、3.3.7–8、3.3.9）；删除 SC 4.1.1 |
| **WCAG 2.2 理解文档（W3C WAI）** | 每项标准的充分技术、咨询性技术和失败技术 |
| **WAI-ARIA 作者实践指南（W3C）** | 所有主要小部件类型的键盘交互模式和必需 ARIA 属性 |
| **EN 301 549（2021 年，ETSI）** | 针对 ICT 产品和服务的欧洲标准，引用 WCAG 2.1 AA（第 9–11 章） |
| **欧盟网页无障碍指令 2016/2102** | 欧盟公共部门 WCAG 2.1 AA 要求和无障碍声明义务 |
| **欧洲无障碍法案（EAA）——指令 2019/882** | 通过 EN 301 549 对私营部门的 WCAG 2.1 AA 要求；2025 年 6 月合规截止期限 |
| **第 508 条修订标准（36 CFR Part 1194）** | 按 E205 的美国联邦 WCAG 2.0 AA 要求 |
| **英国 PSBAR 2018 与《平等法 2010》** | 英国公共和私营部门 WCAG 2.1 AA 预期 |
| **AODA 网页标准** | 安大略省大型私营组织 WCAG 2.0 AA（自 2021 年起） |
| **axe-core、WAVE、Lighthouse、IBM Equal Access** | 自动化测试工具能力映射与局限分析 |

### 技能触发短语

`WCAG` · `Web Content Accessibility Guidelines` · `WCAG 2.0` · `WCAG 2.1` · `WCAG 2.2` · `WCAG 3.0` · `accessibility audit`（无障碍审计） · `accessibility conformance`（无障碍合规） · `POUR principles`（POUR 原则） · `success criteria`（成功标准） · `conformance level A AA AAA`（合规级别 A AA AAA） · `colour contrast`（颜色对比度） · `keyboard accessibility`（键盘无障碍） · `screen reader compatibility`（屏幕阅读器兼容性） · `focus indicator`（焦点指示器） · `focus visible`（焦点可见） · `skip navigation`（跳过导航） · `alt text`（替代文本） · `ARIA` · `accessible name`（无障碍名称） · `EN 301 549` · `European Accessibility Act`（欧洲无障碍法案） · `EAA accessibility`（EAA 无障碍） · `EU Web Accessibility Directive`（欧盟网页无障碍指令） · `ADA website accessibility`（ADA 网站无障碍） · `accessibility statement`（无障碍声明） · `WCAG gap assessment`（WCAG 差距评估） · `WCAG audit`（WCAG 审计） · `mobile accessibility`（移动端无障碍） · `cognitive accessibility`（认知无障碍） · `WCAG 2.2 new criteria`（WCAG 2.2 新标准） · `touch target size`（触控目标尺寸） · `dragging movements`（拖拽动作） · `accessible authentication`（无障碍认证） · `redundant entry`（重复输入） · `reflow 320px`（320px 重排） · `non-text contrast`（非文本对比度） · `text spacing`（文本间距） · `content on hover or focus`（悬停或聚焦时的内容）

---

## 6. 作者

**Hemant Naik**
[LinkedIn](https://www.linkedin.com/in/tanaji-naik/) · [hemant.naik@gmail.com](mailto:hemant.naik@gmail.com)
