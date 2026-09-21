# 模块化知识路由

## 审查顺序

1. 形成合同画像并通过分类确认门。
2. 对已配置结构触发器的类型，先核对交易文件、资金、出资和程序事实；命中 P0 时仅当 finding 的 `output_kind` 与 `prohibited_outputs` 精确匹配，或本 finding 显式声明 `directed_block`，才阻断该项动作。被阻断项记录为 `directed_blocked`，其他合规方向或无依赖条款继续。
3. 调用 `scripts/knowledge/select_active_assets.py`，按主类型、辅类型、分类置信度、我方角色和场景标签取得分层结果。
4. 依次使用全局规则、主大类 `active` 原则卡、具体类型 `active` 原则卡与模块；候选大类卡只返回影子元数据，不返回正文。
5. 先读原则卡，明确审查目标、判断坐标、默认倾向、推翻因素和法律硬边界。
6. 再核对合同现有条款的机制，而不是只检索相似句子。
7. 形成 review plan 后，选择强保护、平衡或让步变体，并按具体事实重新起草。
8. 检查模块依赖、冲突和跨条款联动，再应用真实 Word 修订。
9. 完成 DOCX 工程门和语义一致性复核。

## 三层继承与覆盖

- 全局事实真实性、法律强制性、用户授权和文档完整性边界不可覆盖。
- 具体类型规则只在明确适用范围内优先于大类默认倾向。
- 大类硬边界与具体类型规则发生实质冲突时，不静默覆盖；记录 `rule_conflict` 并转人工判断。
- P0 仍只按 finding 的精确输出或显式 `directed_block` 定向阻断。
- 大类卡中的 `module_index` 只作议题导航；实际模块仍必须通过具体类型、角色、场景和 `active` 状态筛选。

选择器返回 `global_rules_applied`、`domain_principle`、`type_principles`、`modules`、`coverage_level`、`coverage_notice` 和 `shadow_domain_metadata`。`coverage_level` 为 `global_only`、`domain_only` 或 `domain_and_type`。为兼容旧调用，`principles` 继续作为 `type_principles` 的同值别名。

主大类只有在高置信且角色已知，或通过 `--confirmed-domain-code` 明确确认后才可执行。混合合同只执行主大类；`secondary_domain_codes` 仅提示，不加载辅大类正文。EC-10 当前为 `gap` 卡，即使显式确认也只能保持 `global_only`。

## 原则卡与条款模块分工

原则卡回答“为什么这样判断、什么会改变判断”；条款模块回答“在给定前提下可以如何落文”。两者不得合并成没有来源、没有前提的固定答案。

条款模块至少包含：

`module_id、version、type_id、clause_group、review_objective、failure_mode、roles、scene_tags、requiredness、assumptions、placeholders、variants、dependencies、conflicts、source_ids、source_family_ids、approval_status、reviewer、reviewed_at、legal_checked_at`。

## 联动组

下列机制默认成组审查：

- 付款、开票、交付与验收；
- 变更、工期、解除与违约；
- 保密、数据处理与知识产权；
- 责任限制、违约金、赔偿与保险；
- 到期、续期、退出、交接与数据迁移。

选择某一模块变体后，必须检查其 `dependencies` 和 `conflicts`。缺失依赖时补入配套机制或降低动作强度；冲突无法消除时升级人工判断。

`module_group_catalog.json` 记录联动顺序和一致性检查位，`template_catalog.json` 记录 DOCX 结构骨架。每项辅助资产独立走状态机；类型激活不等于其母版、联动组、触发器或经验卡自动获批。`candidate`、`lawyer_approved`、`regression_passed` 均不得进入正式运行。

股权转让另有 `trigger_catalog.json` 和 `experience_catalog.json`。其中 `active` 资产可用于正式审查，其余状态仅供律师校验和回归测试。

## 没有 active 资产时

若已有 `active` 大类卡但没有 `active` 具体类型资产，返回 `domain_only`，只用大类判断框架，不输出未批准的类型条款正文。若大类卡也未激活，则返回 `global_only` 和 `blocked_need_approval`，继续使用现有原则型审查资料；不得读取候选正文、不得声称命中母版、不得自行提升资产状态。
