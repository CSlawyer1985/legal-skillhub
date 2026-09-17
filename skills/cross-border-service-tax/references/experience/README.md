# 经验库使用说明 — cross-border-service-tax

> 经验库是本 Skill 的"双循环学习系统",把每次办案的新发现沉淀为可复用的 YAML 条目。

---

## 一、目录结构

```
experience/
├── README.md            ← 本文件(字段规范+写入流程)
├── _config.yaml         ← 配置(auto_capture/加载门槛/升级门)
├── _index.yaml          ← 自动索引(复用时先读这个,勿手改)
├── <scenario_key>.yaml  ← 主经验文件(provisional/verified 条目)
├── _incoming/           ← 草稿暂存区(模型生成的待入库草稿)
├── _pending/            ← 待验证经验区(draft,低置信度,默认不加载)
└── _versions/           ← 自动快照(入库前备份)
```

---

## 二、YAML 字段规范

单条经验的字段:

```yaml
id: <小写kebab-case唯一标识,如 royalty-hk-7pct>
scenario_key: <场景键,如 royalty-treatment / pe-service-183days / beneficial-owner>
status: <draft | provisional | verified | deprecated>   # 模型最高只能 provisional;deprecated 用于税收口径已被废止/推翻的经验(保留历史,不再用)
confidence: <low | medium | high>
conclusion: <一句话结论>
detail: <可选,详细说明>
sources:                  # 必填,非空列表,且 confidence=high 时须 ≥2 个**独立**来源(同条款的多个表述不算独立)
  - <法条/协定条文/公告文号>
captured_at: <YYYY-MM-DD>
last_verified: <可选,YYYY-MM-DD,最近一次人工复核日期>
verified_by: <可选,none | model | tax_advisor | lawyer>  # verified 须 tax_advisor/lawyer
ref_count: <可选,整数,被引用次数(升级门用)>
override_of: <可选,旧经验id,标记为口径变更覆盖>
search_queries: <可选,列表,有效检索式>
```

> **关于 `deprecated`**:税收协定会修订、口径会变。当一条经验对应的口径被废止/推翻(如协定版本变更、立法修改),**不要删除该经验**——改为:
> 1. status = `deprecated`
> 2. 新写一条新经验(不同 id),用 `override_of: <旧 id>` 标记替代关系
> 3. 旧经验保留,以便回溯"该口径曾经成立、何时被推翻"
> exp_lint 会把超 stale_warning_months 未复核的 verified 经验报 warning;`deprecated` 状态可豁免该警告(避免每次过期都被反复报)

---

## 三、写入流程

1. **判断是否有新发现**(见 SKILL.md Step 6 的信号清单);无则跳过
2. **生成草稿**:写成单条 YAML,保存到 `_incoming/<YYYY-MM-DD>-<slug>.yaml`
   - status 只能填 `provisional` 或 `draft`(模型不得自封 verified)
   - sources 必填
3. **调用入库脚本**:
   ```bash
   python scripts/exp_upsert.py references/experience/_incoming/<草稿>.yaml
   ```
   - 退出码 0 = 成功
   - 退出码 3 = schema 错误 → 修正后重试
   - 退出码 4 = 冲突拒绝 → 加 `override_of` 后重试
4. 非零退出**不得谎称"已沉淀"**

---

## 四、复用流程

1. 分析前先读 `_index.yaml`(轻量),看本案 `scenario_key` 有无匹配
2. 有匹配(status=verified 或 provisional 且 confidence 达 `_config.yaml` 门槛)→ 深读对应 YAML
3. 引用时**必须带 sources**;引用 provisional **必须标注「[待验证经验]」**
4. provisional 累计被引用 ≥ `_config.yaml` 的 `provisional_review_threshold`(默认3)→ 提示用户强制复核

---

## 五、升级与维护

- **升级**:用户确认经验正确后,改 status=verified、verified_by=tax_advisor/lawyer(须人工)
- **定期维护**:`python scripts/exp_lint.py` 检查过期/低质/一致性
- **渲染**:`python scripts/exp_render.py` 生成人类可读视图
- 强烈建议对 `experience/` 启用 git,每次入库前 commit

### 质量门规则(exp_lint.py,2026-08-11 加强)

| 检查项 | 级别 | 说明 |
|---|---|---|
| sources 为空 | ❌ error | 引用必带出处 |
| status/confidence 非法 | ❌ error | 枚举值校验 |
| **id 跨文件重复** | ❌ error | 经验 id 全局唯一(同 id 重新 upsert 同 scenario_key 是合法的,如 ref_count 更新) |
| **confidence=high 但 sources<2** | ❌ error | **核心防线:高置信须≥2个独立来源,防正反馈污染** |
| source_count(若提供)与 sources 长度不一致 | ❌ error | 冗余字段防漂移 |
| status=verified 但 verified_by=none/model | ⚠️ warning | 须专业人士确认 |
| provisional 引用≥门槛且未复核 | ⚠️ warning | 升级门触发(默认3次),提示用经典案例库交叉验证 |
| verified 超 stale_warning_months 未复核 | ⚠️ warning | 法条/口径会变(默认12个月,配置驱动) |
| _pending 超 pending_retention_days | ⚠️ warning | 待验证区超期(默认90天,配置驱动) |

**CLI 用法**:
```bash
python scripts/exp_lint.py                      # 全库扫描
python scripts/exp_lint.py --file xxx.yaml      # 单文件检查(入库前自检)
python scripts/exp_lint.py --strict             # 严格模式(warning也算失败,用于CI门禁)
python scripts/exp_lint.py --json               # JSON 输出(机器可读,便于集成)
```

**入库时双重防护(exp_upsert.py)**:入库前也会校验 confidence↔sources、id 唯一性,违规条目在入库阶段即被拒绝(退出码3),不会进入经验库。

---

## 六、典型 scenario_key

> 本清单与 `assets/经典案例库/` 的 scenario_key 对齐(经验库的每条经验应能溯源到经典案例库的对应案例)。

| scenario_key | 场景 | 对应案例 | 经验 id |
|---|---|---|---|
| `pe-seconded-employees` | 派遣员工 PE(员工归属测试) | CC12 | pe-seconded-employees-no-pe |
| `offshore-repair-no-wht` | 境外维修/劳务发生地 | CC-A2 验收案例3 | offshore-repair-no-wht |
| `foreign-tax-credit-indirect` | 间接抵免(还原下层归属税) | EX-02 | ftc-indirect-impute-and-carryforward |
| `tax-sparing-credit` | 税收饶让(视同已缴) | EX-05 | ftc-sparing-not-exempt |
| `overseas-loss-carryforward` | 境外亏损分国弥补 | EX-06 | ftc-overseas-loss-per-country |
| `bo-red-chip-shell` | 红筹导管受益所有人 | CC01/CC07/CC23 | bo-red-chip-shell-denied |
| `sub-license-hk-intermediary-bo-denied` | 转许可受益所有人 | CC17 | bo-sub-license-transfer-obligation |
| `transfer-pricing` | 转让定价 7 形态 | EX-09~15 | transfer-pricing-7-patterns |
| `indirect-transfer-recharacterization` | 间接转让重新定性 | CC10/CC15 | indirect-transfer-recharacterization |
| `settlement-payment-recharacterized-as-royalty` | 和解金重定性 | CC16 | settlement-recharacterized-as-royalty |
| `mixed-contract-split` | 混合合同分劈 | CC06/CC21 | mixed-contract-split-rule |
| `non-exclusive-distribution-vs-royalty` | 非独家分销 | CC20 | non-exclusive-distribution-not-royalty |
| `equipment-purchase-embedded-installation-pe-withholding` | 嵌入式安装服务 PE | CC22 | equipment-embedded-installation-pe |

> **重要说明(2026-08-12 crit 复查发现)**:"对应案例"列是**经验库的分类视角**——把多个相似案件归为一族,与每个 CC 案自身的 `scenario_key` **不是 1:1 对应**。例如:
> - `bo-red-chip-shell` 族覆盖 CC01/CC07/CC23,但 CC07 自身 `scenario_key` 是 `embedded-royalty-in-goods`
> - `mixed-contract-split` 族覆盖 CC06/CC21,但 CC21 自身 `scenario_key` 是 `mixed-contract-license-and-design-service`
> - `indirect-transfer-recharacterization` 族覆盖 CC10/CC15,但 CC15 自身 `scenario_key` 是 `overseas-merger-indirect-transfer-china-equity`
>
> **正确用法**:用本表找经验库(分类视角);用案例汇编的 `## ccxx` 锚点找具体案件的原始 `scenario_key`(案件视角)。两者维度不同。
>
> 新增经验时,优先复用上表 key;若为新场景,自拟 key 须在前 5 位用 `xxx-` 体现所属维度,并在此表登记。

---

*经验库版本: 2026-08-11(首批 13 条种子经验入库,涵盖 PE/维修/抵免/饶让/亏损/受益所有人/转让定价/重新定性/混合合同/分销/嵌入式服务)*
