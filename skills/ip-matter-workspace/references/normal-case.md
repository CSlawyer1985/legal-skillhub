# 正常样例：商标维权事项创建与切换

## 输入

用户执行以下操作序列：
1. `matter-workspace-cn new huayuan-trademark-enforcement`
2. 建档面谈中提供：
   - 委托人：华远科技有限公司
   - 对方当事人：明达商贸有限公司
   - 事项类型：商标维权
   - 保密级别：一般
   - 关键事实：华远公司发现明达公司在同类商品上使用近似商标，已发函要求停止使用但未获回应，现拟提起商标侵权诉讼。
   - 事项专属覆盖：无
   - 关联事项：无
3. 用户确认切换：`matter-workspace-cn switch huayuan-trademark-enforcement`

## 期望行为

1. 系统确认 slug `huayuan-trademark-enforcement` 不存在于活跃和归档目录。
2. 执行完整建档面谈，逐项收集委托人、对方当事人、事项类型、保密级别、关键事实、覆盖设置和关联事项。
3. 写入 `matters/huayuan-trademark-enforcement/matter.md`，内容包含：
   - 委托人：华远科技有限公司
   - 对方当事人：明达商贸有限公司
   - 事项类型：商标维权
   - 保密级别：一般
   - 关键事实完整记录
   - 状态：活跃
4. 创建 `history.md` 初始记录，日期为当日。
5. 创建空 `notes.md`。
6. 不自动切换，询问用户是否切换。
7. 用户确认切换后，更新执业层级配置的 `活跃事项:` 为 `huayuan-trademark-enforcement`。
8. 展示 matter.md 摘要供确认。

## 期望输出要点

- matter.md 中事项类型标注为"商标维权"（非美国法下的 "trademark enforcement"）
- matter.md 中保密级别使用"一般"（非 "standard"）
- 路径使用 `<工作区根目录>/matters/huayuan-trademark-enforcement/` 格式
- history.md 初始记录包含创建日期和 slug

## 应触发的人工 gate 或来源标签

- 建档面谈中事项类型为"商标维权"，对应法律来源为《商标法》(2019修正) 第57条，应可通过 references/cn-legal-sources.md 查询
- 无 `[模型知识 — 需核验]` 标记（商标维权类型的法律依据已确认现行有效）
- 写入文件前需用户确认
