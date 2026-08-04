# legal-due-diligence

中国法律尽职调查 Skill 分享版。

- 版本：v26.4.29.1545
- 适用环境：Claude Code
- 运行要求：Python 3.10+

## 这个 Skill 是做什么的

这是一个用于中国法律尽职调查工作的写作型 Skill，覆盖完整工作流：

- 项目初始化
- 尽调底稿逐章撰写
- 完整性检查
- 尽调报告生成

支持的核心场景包括：

- 法律尽调
- 尽调底稿撰写
- DD 报告生成
- 公司主体尽调项目管理

## 与 yd-enterprise-info 的协作关系

本版本起，企业信息查询已从 legal-due-diligence 中**独立拆分**为单独 Skill：[yd-enterprise-info](https://github.com/malnlda/yd-enterprise-info)。

- legal-due-diligence 专注于尽调工作流（结构化写作、底稿、报告）
- yd-enterprise-info 专注于调用元典开放平台（22 个企业信息接口，支持翻页）

在尽调过程中，当需要查询目标公司公开信息时（股东、专利、商标、诉讼、变更记录等），通过 yd-enterprise-info skill 调用对应接口获取，再将数据写入底稿。

推荐安装方式（同时安装两个 Skill）：

```bash
# 将两个文件夹均放入 Skills 目录并分别重命名
~/.claude/skills/legal-due-diligence/
~/.claude/skills/yd-enterprise-info/
```

## 目录结构

```text
legal-due-diligence-v26.4.29.1545/
├── SKILL.md
├── README.md
├── assets/
│   ├── report-template.md
│   └── working-paper-template.md
├── references/
│   ├── report-standards.md
│   ├── section-guide.md
│   ├── external-apis.md                          # 外部数据源索引（指向 yd-enterprise-info）
│   └── chineselaw/
│       └── enterprise-endpoints-summary.md       # 元典企业信息接口速查表
└── scripts/
    └── init_project.py                           # 项目初始化脚本
```

## 安装方法

### 方法一：手动复制安装

1. 将文件夹 `legal-due-diligence-v26.4.29.1545` 复制到你的 Claude Skills 目录。
2. **建议将文件夹重命名为 `legal-due-diligence`**，以保持与 Skill 名称一致。

常见目录示例：

```bash
~/.claude/skills/
```

安装后的目标结构建议如下：

```text
~/.claude/skills/legal-due-diligence/
├── SKILL.md
├── README.md
├── assets/
├── references/
└── scripts/
```

### 方法二：作为分享包保存

如果你只是想留档或转发，可以直接保留当前目录名 `legal-due-diligence-v26.4.29.1545`；
真正用于本地调用时，再改名为 `legal-due-diligence` 更稳妥。

## 使用方式

当用户提到下列需求时，可以调用本 Skill：

- 尽职调查
- 尽调
- 底稿
- due diligence
- DD报告
- 尽调报告
- 法律尽调

## 四种工作模式

### 1. init：初始化尽调项目

用途：
- 创建项目目录
- 生成 `project-info.md`
- 生成 `working-paper.md`
- 创建 `report/` 目录

示例：

```text
帮我初始化一个尽调项目：
- 目标公司：广州XX农业科技有限公司
- 委托人：深圳XX投资有限公司
- 路径：[项目存放路径]
- 基准日：2026-03-20
- 目的：股权收购
```

### 2. draft：撰写底稿

用途：
- 根据材料撰写某一章底稿
- 将内容写入 `working-paper.md`

示例：

```text
请帮我撰写第2章"股权结构与股东信息"的底稿。
材料路径：/path/to/materials/02-股权/
```

如需查询目标公司公开信息（如股东、专利、商标等），可先通过 yd-enterprise-info skill 调用接口，再将返回数据写入底稿。

### 3. check：检查底稿完整性

用途：
- 检查 10 章结构是否完整
- 汇总缺失材料
- 汇总风险点
- 给出后续工作建议

示例：

```text
底稿写得差不多了，帮我做一次完整性检查。
```

### 4. report：生成尽调报告

用途：
- 将底稿转化为正式法律尽职调查报告
- 输出至 `report/` 目录

示例：

```text
底稿已全部完成，请帮我生成尽调报告。
```

## 使用提醒

### 1. 路径占位符需要自行替换

本分享版中的示例路径：

```text
路径：[项目存放路径]
```

这是占位写法，**使用时请替换为你自己的本机目录**，例如你实际准备存放项目的路径。

### 2. 示例公司名称均为占位示例

文档中的公司名、委托人名称、字段模板等均为示例或占位内容，使用时请按项目实际情况替换。

### 3. 这是分享版，不含真实项目材料

本包仅包含：
- Skill 说明
- 模板文件
- 参考资料
- 初始化脚本

不包含任何真实客户、真实项目或真实尽调底稿。

## 主要文件说明

- `SKILL.md`：Skill 主说明文件
- `scripts/init_project.py`：项目初始化脚本
- `assets/working-paper-template.md`：底稿模板
- `assets/report-template.md`：报告模板
- `references/section-guide.md`：分章节调查指南（各章含 yd-enterprise-info 调用提示）
- `references/report-standards.md`：报告转化和语言规范
- `references/external-apis.md`：外部数据源索引（指向 yd-enterprise-info skill）
- `references/chineselaw/enterprise-endpoints-summary.md`：元典企业信息接口速查表（22 个接口）

## 企业信息查询（需配合 yd-enterprise-info）

本版本已将企业信息查询能力完全委托给独立 Skill [yd-enterprise-info](https://github.com/malnlda/yd-enterprise-info)，支持：

- 股东与核心成员（`base-info`）
- 变更记录（`change`）
- 专利、软著、商标、ICP 备案（`patent` / `soft-right` / `brand` / `website`）
- 对外投资、对外担保、股权质押与冻结
- 诉讼文书、行政处罚、失信被执行人等 22 个接口

所有接口均支持**自动翻页**，不受旧接口 10 条返回限制。

使用时在对话中同时唤起两个 Skill 即可，API Key 通过环境变量配置在 yd-enterprise-info 中：

```bash
export CHINESELAW_API_KEY=你的_api_key
```

## 适合谁用

适合以下用户：

- 中国执业律师
- 律所实习生 / 初年级律师
- 需要标准化尽调工作流的法律团队
- 希望把底稿与报告写作流程结构化的人

## 注意事项

- 本 Skill 偏重法律尽调的**结构化写作与输出规范**。
- 财务、税务、评估等专业问题，仍建议结合对应专业意见使用。
- 公开信息查询结果可能存在延迟或遗漏，实际项目中仍应注意交叉核验。

## 版本说明

当前分享版为：`v26.4.29.1545`

- v26.4.29.1545：企业信息查询拆分为独立 Skill（yd-enterprise-info）；支持 22 个接口自动翻页；section-guide.md 各章新增 yd-enterprise-info 调用提示
- v26.4.25.2039：新增元典「按名称/股票简称检索」接口（`company-info`）；init 支持 `--name-lookup` 智能路由
- v26.4.25.2006：新增元典「按 id/USCC 详情」接口（`company-detail`）
- v26.4.20：基础版本（4 模式 + 10 章工作流）

如后续继续迭代，建议同步维护：
- `metadata.version`
- 文件夹版本号
- 压缩包文件名
- README 中的版本说明
