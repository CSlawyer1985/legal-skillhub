---
name: regulatory-matter-workspace
description: 管理事项工作区 —— 创建、列表、切换、关闭或脱离当前事项（实务层级）。在多客户实务需要把一个客户的上下文与其他客户隔离时，或某实质技能需要知道当前是哪个事项时使用。
metadata:
  displayName: 监管事项管理
  argument-hint: <new | list | switch | close | none> [slug]
---

# /matter-workspace

实务人士跨多个客户和事项工作。事项工作区把一个客户或事项的上下文与所有其他事项分开。本技能管理这些工作区。

## 子命令

- `regulatory-matter-workspace new <slug>` —— 创建新事项工作区，跑短访谈，写 `matter.md`
- `regulatory-matter-workspace list` —— 列事项及其状态和当前标记
- `regulatory-matter-workspace switch <slug>` —— 设当前事项
- `regulatory-matter-workspace close <slug>` —— 归档事项（移到 `$LEGAL_AGENT_PROFILE_HOME/regulatory-legal/matters/_archived/`，**绝不**删除）
- `regulatory-matter-workspace none` —— 脱离任何当前事项，仅在实务层级上下文工作

## 指令

1. 读 `$LEGAL_AGENT_PROFILE_HOME/regulatory-legal/profile.md` —— 确认 `## 事项工作区` 节已填写。如 `启用` 是 `✗`，告诉用户："事项工作区关。你被配置为单客户的企业内部法务实务，所以插件自动从实务层级上下文工作。如果你实际跨多客户工作，重跑 `regulatory-cold-start-interview --redo` 并选私人执业设置。否则你完全不需要 `/matter-workspace`。"**不要**报错 —— 关闭状态是企业内部法务用户的预期状态
2. 用下面的文件管理逻辑
3. 在 `$ARGUMENTS` 第一个参数上分发：
   - `new` → 跑访谈，写 `$LEGAL_AGENT_PROFILE_HOME/regulatory-legal/matters/<slug>/matter.md`，初始化 `history.md` 和 `notes.md`
   - `list` → 枚举 `$LEGAL_AGENT_PROFILE_HOME/regulatory-legal/matters/*/matter.md`，打印表，标当前事项
   - `switch` → 更新实务层级 `profile.md` 中 `当前事项:` 行
   - `close` → 移 `$LEGAL_AGENT_PROFILE_HOME/regulatory-legal/matters/<slug>/` 到 `$LEGAL_AGENT_PROFILE_HOME/regulatory-legal/matters/_archived/<slug>/`，在 `history.md` 记关闭日期
   - `none` → 设 `当前事项:` 为 `none —— 仅实务层级上下文`
4. 给用户看什么变了，写入前确认

## 注释

- 除非实务层级 `profile.md` 中 `跨事项上下文` 是 `开启`，本技能绝不跨事项读
- 归档不是删除 —— 关闭事项保留可读用于保留期 / 利益冲突
- slug 是小写带连字符。归档和活跃 slug 重用时，归档的保留在 `_archived/<slug>/`

---

多客户实务人士（私人执业 —— 独立律师、小所、大所）跨多个事项工作。一个事项的上下文**不能**漏到另一个。本技能是让这条规则真实的细文件管理层。

**默认状态是关闭的**。企业内部法务用户永远不见 —— 他们只在实务层级跑。事项工作区在私人执业用户的冷启动启用，或通过编辑实务层级 `profile.md` 中 `## 事项工作区`。如 `启用` 是 `✗`，本技能不跑；它解释关闭状态并向真的需要事项隔离的用户建议 `regulatory-cold-start-interview --redo`。

## 存储布局

所有事项数据在：

```
$LEGAL_AGENT_PROFILE_HOME/regulatory-legal/
├── profile.md                       # 实务层级业务规范
└── matters/
    ├── <slug>/
    │   ├── matter.md                # 客户、对方、事项类型、关键事实、覆盖
    │   ├── history.md               # 事件、决策、草稿、复核的日期日志
    │   ├── notes.md                 # 自由笔记
    │   └── outputs/                 # 本事项的技能输出（可选子目录）
    └── _archived/
        └── <slug>/                  # 已关闭事项 —— 可读但不当前
```

slug 是小写带连字符。例如：`acme-msa-2026`、`zenith-renewal`、`vendor-xyz-nda`。

## 当前事项在业务规范中

实务层级 `profile.md` 中 `## 事项工作区` 下的 `当前事项:` 行是单一事实来源。切换事项编辑这一行。**没有**单独的状态文件。

## 子命令逻辑

### `new <slug>`

1. 确认 slug 没在 `matters/<slug>/` 或 `matters/_archived/<slug>/` 中存在。如重用，让用户挑别的
2. 跑访谈：
   - **客户**（我们代表的当事人，或企业内部法务的内部业务单元）
   - **对方**（另一方 —— 可多个）
   - **事项类型**（读插件业务规范拿典型类别；监管合规法务：立法 ｜ 评议期 ｜ 内规差异整改 ｜ 监管问询 ｜ 处罚回应 ｜ 长期话题 ｜ 其他）
   - **保密级别**（标准 ｜ 加强 ｜ 净室隔离 —— 加强在跨事项设置中促额外小心）
   - **关键事实**（2–5 句：本事项是关于什么、利益相关方是谁、什么是利害关系）
   - **事项特定的对实务手册的覆盖**（例如"客户要求 24 月责任上限，不是 12"、"对方是战略伙伴 —— 关系保持的语气"）
   - **关联事项**（任何相关事项的 slug）
3. 用下面的模板写 `matters/<slug>/matter.md`
4. 用一条"已开"条目初始化 `matters/<slug>/history.md`
5. 创建空 `matters/<slug>/notes.md`
6. **不**自动切到新事项。问："要现在切到 `<slug>` 吗？（`regulatory-matter-workspace switch <slug>`）"

### `list`

枚举 `matters/*/matter.md`。读每文件 frontmatter 或前几行抽状态。打印表：

| Slug | 客户 | 事项类型 | 状态 | 开始日期 | 当前 |
|---|---|---|---|---|---|

用 `*` 标当前事项。如有归档，在单独"归档"标题下含 `_archived/*`。

### `switch <slug>`

1. 确认 `matters/<slug>/matter.md` 存在。不存在，提议 `regulatory-matter-workspace new <slug>`
2. 把实务层级 `profile.md` 中 `当前事项:` 行编辑为 `当前事项: <slug>`
3. 给用户看 `matter.md` 摘要确认是在对的事项上

### `close <slug>`

1. 确认 `matters/<slug>/` 存在
2. 在 `matters/<slug>/history.md` 追加今天日期的"已关"条目
3. 移 `matters/<slug>/` → `matters/_archived/<slug>/`
4. 如已关闭的是当前事项，把 `当前事项:` 设为 `none —— 仅实务层级上下文`

### `none`

把实务层级 `profile.md` 中 `当前事项:` 设为 `none —— 仅实务层级上下文`。和用户确认。

## `matter.md` 模板

```markdown
[工作秘密标识 —— 按 ## 谁在用这个插件 + shared/header-by-role.md 选定]

# 事项：[客户] —— [简短描述]

**Slug**：[slug]
**开始日期**：[YYYY-MM-DD]
**状态**：进行中
**保密级别**：[标准 / 加强 / 净室隔离]

---

## 当事人

**客户**：[名]
**对方**：[名(s)]

## 事项类型

[立法 ｜ 评议期 ｜ 内规差异整改 ｜ 监管问询 ｜ 处罚回应 ｜ 长期话题 ｜ 其他 —— 一行理由]

## 关键事实

[2–5 句。本事项是关于什么。利益相关方是谁。什么是利害关系。与默认实务手册不同之处。]

## 事项特定覆盖

*与实务层级实务手册的任何偏离，仅适用于本事项。*

- [例如"责任上限：客户要求 24 月，不是公司标准 12"]
- [例如"语气：关系保持 —— 对方是战略伙伴"]
- [例如"适用法：必须中国法（指定上海仲裁），不是境外法"]

## 关联事项

- [slug —— 一行为何相关]

## 保密说明

[如果加强或净室隔离，描述为何。谁可看事项文件。即使跨事项上下文全局开，本事项跨事项上下文是否被允许。]
```

## `history.md` 初始化

```markdown
# 历史：[客户] —— [简短描述]

仅追加事件日志。最新在顶。

---

## [YYYY-MM-DD] —— 事项已开

访谈完成。Slug：`[slug]`。状态：进行中。
[超出 matter.md 值得保留的初始上下文 —— 例如"为响应 [对方] 提交的来文合同草稿而开"]
```

## 跨事项上下文

实务层级 `profile.md` 有一个 `跨事项上下文:` 标志。关时（默认），事项 A 中的技能**绝不**读任何其他 `matters/B/` 中的文件。本设置存在就是为这个保密保证。

开时，技能可能跨事项目录读，**仅在**用户明确要求时（例如"比较我们在最近五个供应商事项中关于责任上限的立场"）。即使开，默认仅加载当前事项除非用户要跨事项视图。

## 本技能不做的事

- **跑利益冲突核查**。利益冲突是实务人士 / 律所的工作；访谈抓取用户声明的内容
- **执行保留期**。关闭归档事项；不删除。保留政策在范围外
- **自动路由输出**。实质技能决定写哪里；本技能告诉它**哪个目录**是当前的，不是放什么进去
- **决定跨事项是否合适**。读标记并遵守
