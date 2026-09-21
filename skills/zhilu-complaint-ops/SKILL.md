---
name: zhilu-complaint-ops
description: 智录·律师经验固化平台（通用框架）。一套做法（收进来→定规矩→存成家底），三种用法（工商投诉/法律咨询/合同审查），一个人用或全所一起用都行。律师配置信息源、台账类型、场景后，自动完成采集→识别→判重→评分→起草→定稿→入库→度量的完整闭环。新场景接入(setup_wizard)：律师拿到新台账时走首次接入5步(拉字段→跑匹配→解读报告→写config→验证)+字段变更3步，全程不碰fieldId。当用户说"跑巡检""有新工单""工商投诉""生成答复""回填答复""智录""逾期""市监""运营度量""周报""月报""办结率""退赔率""知识资产""口径库""golden_corpus""法律咨询口径""口径复用""复核闭环""批量起草""复核入库""每日复跑口径""接入新台账""换台账""新律所接入""字段映射初始化""setup_wizard""field_map 匹配"时触发。
metadata:
  version: 1.6.0
---

# 智录·律师经验固化平台

**核心价值**：一套做法，把律师答过、判过、定过稿的经验存下来，下次同类问题直接接着用——省时间，也把质量稳住。

**不是"帮律师干活的法律AI"，也不替你想案子。** 它做的事很简单：把你攒下的判断经验存下来，系统下次能直接用。

真实生产系统：接真实台账、真实API Key、沉淀真实口径库。

## 通用框架：一套做法，三种用法

### 三步做法

1. **先收进来**：群里的投诉、咨询、合同……自动识别、登记、查重。15分钟→2分钟/件。律师不用再手工录一遍。
2. **再定规矩**：六条查重规则、五个打分维度，把"我怎么判断"写成系统照着算的规矩。老律师的判断，变成人人能用的标准。
3. **存成家底**：律师定稿后存进口径库，下次同类问题自动翻出来。越攒越多，一次答对，往后一直省时间。

**这三步不限法律——换一类事、换一批资料，照样能跑起来。**

### 三种用法

| 用法 | 谁用 | 信息源 | 台账 | 口径库 |
|---|---|---|---|---|
| **工商投诉**（全所一起用） | 全所律师 | 市监群图片→OCR | 钉钉多维表 | 全所共同口径 |
| **法律咨询**（一个人用） | 律师自己 | 业务群文字 | 本地SQLite | 个人口径库 |
| **合同审查**（再接一个） | 律师自己/全所 | 手动录入 | 本地SQLite/钉钉表 | 审查要点口径库 |

**共用的底层**：收进来→定规矩→存成家底 | 自动统计 | 自动出看板——凡是"反复答同类问题"的活都能套。

## 首次接入（setup_wizard）

律师拿到新台账后，对千问办公说**"接入智录"**，Agent 会引导完成以下5步：

1. **Agent 拉字段快照**：`dws aitable field list --base-id <B> --table-id <T> --format json` → 存为 `/tmp/fields.json`
2. **跑 setup_wizard**：`python3 scripts/setup_wizard.py --fields /tmp/fields.json --base-id <B> --table-id <T> --out /tmp/match_report.json`
3. **Agent 解读报告**：
   - `matched`（score≥0.85 且唯一）→ 直接采用
   - `ambiguous` → 用大白话逐条问律师（例："投诉人姓名在哪一列？A 投诉人 B 联系人"）
   - `missing` → 可选字段跳过；必需字段（content/status/deadline）问律师要不要在台账里新建列
4. **Agent 写 config.yaml**：把确认后的 matched 合入 `ledger.field_map`，更新 `ledger.base_id` / `ledger.table_id`
5. **验证**：用新 config 跑一次 `dws aitable record query --limit 3` 确认字段可读

**约束**：setup_wizard.py 纯本地、零外部依赖、不调 dws。律师永远不打开 config.yaml、不碰 fieldId。

## 生产资源

- **台账**: base `<你的台账BaseID>` / table `<你的台账表ID>`（接入时由 setup_wizard 自动填入）
- **信息源**: 钉钉群/微信群/邮箱/手动录入（由律师在 config.yaml 中配置）
- **config**: `{skill_dir}/config.yaml`（台账fieldId映射 + 场景配置，由 setup_wizard 生成）
- **引擎脚本**: `{skill_dir}/scripts/`（step1 OCR / step3 评分 / step4 起草 / step5 巡检 / dedup_upsert 六键判重 / completeness 数据完整度 / refresh_dashboard 看板 / heartbeat 心跳 / metrics 运营度量 / ledger_io 台账读取 / batch_draft 批量起草 / review_apply 复核入库 / setup_wizard 首次配置 / shadow_event_ledger 影子事件账本）
- **影子配置**: `{skill_dir}/shadow_config.json`（影子模式开关）
- **影子状态**: `{skill_dir}/intake_state_v2.json`
- **影子账本**: `{skill_dir}/shadow_event_ledger.jsonl`（只追加，不写生产台账）
- **口径库（知识资产）**: `{skill_dir}/golden_corpus.json`（随律师定稿增长，含入库时间/入库律师/复用次数/关联工单数/质量评分）
- **API Key**: 读 `~/.qwenworkcn/complaint-workflow-prod/.env` 的 `LLM_API_KEY`/`OCR_API_KEY`，**绝不硬编码进任何文件或命令**

## 关键约束（每次执行前必读）

1. **managed-DWS**：此环境脚本内 subprocess 调 dws 不生效（返回 pending 占位符）。台账读写必须由 Agent 直接在 Bash 工具发 `dws ...` 命令，数据落地临时文件后，引擎脚本用 `--data` 本地模式计算。dws 多条命令可用换行链接在同一 Bash 调用里。
2. **AI 起草硬信息会幻觉**：年份/金额/时限须人工核对。法条引用可靠。写回前清理年份类错误。
3. **AI 立场偏消费者**：退款金额/时限承诺须业务核实+法务定稿后方可对外。企业客户投诉不适用《消保法》，立场需人工纠正。每份初稿顶部加"⚠️AI初稿偏消费者立场须核实"提示。
4. **特殊件人工升级**：涉视障/心理危机/舆情(三轨并投)/大额(>5000)的工单，评分模型抓不住，须人工判断升级，不能只看分数。
5. **Phase 1影子模式**：补充证据/二次来件只写本地`shadow_event_ledger.jsonl`，不得更新生产台账、不得改状态、不得写最终答复、不得重开工单。
6. **关闭旧自动结案**：结案词、手机号、姓名或引用图只能形成影子候选；需用户明确确认后，才人工回填。
7. **脚本纯本地**：`step3_risk_score.py`和`step5_daily_check.py`必须传`--data`；在线模式和`--push`已禁用。DWS读取、写入和发送均由Agent顶层执行并回读验证。
8. **命名口径：对外用"市监投诉"**：面向市监局、管理层或对外文档时，统一使用**"市监投诉"**，不用"工商投诉"（机构已改制为市场监督管理局）。**例外**：本 skill 的触发词、台账实名及历史字段值保留"工商投诉"原文，不得改写。

## 操作手册

### A. 有新工单（识别入库）

1. `dws chat +chat-messages --group <cid> --limit 20 --format json --jq '...'` 拉最新消息，定位市监人员发的图片消息（含 resourceRefs）
2. `dws chat +messages-resource-url --resource-id <mediaId> --type mediaId --open-conversation-id <cid> --message-id <msgId>` 取 downloadUrl → `curl -o` 下载图片
3. `export OCR_API_KEY=$(...)` 后 `python3 scripts/step1_ocr_intake.py --image <img> --out <json>`
4. 富化：投诉类型映射到枚举（虚假宣传/隐私泄露/自动续费/退款纠纷/服务质量/合同纠纷/价格欺诈/其他）；渠道=12315平台；收到日期=消息日期；截止日期=OCR值或收到+15天；从群跟进对话提取处理状态与跟进记录
   - **工单类型判定**：智录**只入库 `12315消费者投诉`**。出现"信访编号/来访/上访"→ `信访`；出现"协查函/调查函"→ `监管协查函`。**这两类都不入库**。
   - **12315原始编号归档**：若 OCR 投诉编号是 12315 国家平台号（形如 `1330110...`/纯数字长串≥20位），存入 raw_12315_no 字段，标题按 `WS-MMDD-NNN` 规范另发。
5. **多键判重门禁（写入前必做）**：把台账快照与候选工单各落成临时 JSON，运行 `python3 scripts/dedup_upsert.py --ledger <台账快照.json> --incoming <候选.json> --state intake_state.json --out decisions.json`。脚本按 **K1 12315编号 / K2 投诉编号 / K3 手机+佐证 / K4 姓名+金额+类型 / K5 函号 / K6 姓名+内容近重** 六键确定性判定，输出 `updates / creates / skipped`。Agent 据此执行：对 `updates` 用 `dws record update` 追加跟进；对 `creates` 才走 `dws record create`。命中即同案，绝不另起一行。
6. python 内联 import step3 评分函数算五维分（legal/amount/spread/urgency/repeat）。
7. `dws aitable record create --base-id ... --table-id ... --records '[{"cells":{...}}]'` 写入（fieldId 见 config.yaml；内容含 ASCII 单引号会破坏传参，先替换为全角'）

### B. 跑巡检

1. `dws aitable record query --base-id ... --table-id ... --limit 50` 拉全量 → 投影成引擎格式落地 `/tmp/ledger.json`
2. `python3 scripts/step5_daily_check.py --data /tmp/ledger.json`
3. 报告五档：无跟进/临期(3天内)/逾期/**数据待补全**(缺联系方式或截止日期)/**疑似已解决·待确认结案**，逾期件最优先。

### C. 生成答复

1. 取目标工单内容
2. `export LLM_API_KEY`，python 调 `step4.draft_with_llm(key, case, retrieve_similar(corpus, content))`

**对外答复硬约束**：

- **分层输出**：【快速响应版】≤50字 + 【内部参考版】不限长度
- **长度上限**：对外回复 ≤100字，每句 ≤20字
- **闭环公式**：`[处理结果确认] + [用户状态说明]`
- **禁模板化敷衍表述**
- **禁内部指引混入对外话术**
- **禁报告式结构**
- **无法满足须说明限制条件**
- **口径提取前过滤测试数据**

3. 顶部加"⚠️AI初稿偏消费者立场须核实"提示，清理年份幻觉
4. `dws aitable record update --records '[{"recordId":...,"cells":{...}}]'` 写回 AI建议答复字段

### D. 回填最终答复（口径进化）

1. 用户定稿后 `dws aitable record update` 写最终答复字段，处理状态改"已完结"，追加跟进记录
2. 优质定稿追加进 `golden_corpus.json`（字段：case_content/ai_suggestion/golden_reply/投诉类型）

## 复核闭环（每日循环）

把"AI 起草→人工定稿→沉淀口径"从一次性动作升级成**每天自我强化的闭环**。

**状态机**（`复核状态` 单选字段）：

```
待起草 ──batch_draft──▶ 已起草待复核 ──人工改定稿+通过──▶ 已复核待入库 ──review_apply──▶ 已入库
                              ▲                                                     │
                              └────────── 次日 batch_draft --redraft-open ◀─────────┘
```

**每日四阶段循环**：

1. **采集后即时起草**：`dws aitable record query` 落台账快照 → `python3 scripts/batch_draft.py --data <快照.json> --corpus golden_corpus.json --out /tmp/drafts.json`。对 `待起草/复核状态空` 的未完结工单逐件取相似口径 + 起草，标 `已起草待复核`。
2. **人工复核**（唯一人工动作）：看 AI 初稿，直接改成本次定稿、把 `复核状态` 改 `已复核待入库`。
3. **每日收尾入库**（EOD）：`python3 scripts/review_apply.py --data <快照.json> --corpus golden_corpus.json --updates /tmp/updates.json` **先 dry-run 预览**，确认后加 `--apply` 真追加 `golden_corpus.json`（写前自动 `.bak` 备份，按 case_content 去重、幂等）。
4. **次日用新库复跑**：`python3 scripts/batch_draft.py --redraft-open ...` 对仍未完结的工单，按昨夜变大后的口径库重新起草。

**硬性门禁**：`AI 起草 ≠ 定稿`。batch_draft 只出初稿进复核队列，**绝不自动改处理状态/写最终答复/落库**；只有人工标记"已复核待入库"的件才被 review_apply 写进 golden_corpus。

## 自动化运行

系统处于Phase 1影子运行：新工单可自动入库；补充证据、二次来件、客服结果和结案候选只做影子判断，需人工确认后才可回填生产台账。

核心定时任务：

- **双向采集**（工作日 08/10/12/14/16点）：
  - 方向A 新工单入库：市监人员明确的新投诉图片经OCR、评分后可直接入库。
  - 方向B/C 补充证据、客服结果和结案表达：Phase 1只生成影子事件和候选匹配，需人工确认后走D流程。
  - 方向D 客服群转发的新投诉：仍可按现有规则入库，匹配不明时进入影子判断。
  - 防重复：六键判重门禁——命中任一即视为同案、只追加跟进不新建。
  - 影子输入：`python3 scripts/shadow_event_ledger.py --events <events.json> --cases <cases.json> --config shadow_config.json --ledger shadow_event_ledger.jsonl`
- **每日巡检告警**（工作日 08:30）：算逾期/临期/在办/**待补全**/**疑似已解决·待确认结案** → 只推承办人本人单聊，绝不发群
- **看板刷新**（工作日 16:30，静默）：Agent 用 `dws aitable record query --format json` 落盘台账快照，再跑 `python3 scripts/refresh_dashboard.py --ledger <快照.json> --corpus golden_corpus.json`——产出 dashboard_data.json、ledger_engine.json、**metrics.json** 并生成 HTML 看板。
- **数据完整度门禁**：`completeness.py` 定义"未完结工单缺 联系方式 或 截止日期 = 待补全"。诉求金额可合法为 0，不算缺失。
- **cron 心跳 + 系统健康监控**（每日 09:00，静默/仅失败告警）：`heartbeat.py --job <intake|health>` 写心跳。健康监控检查采集心跳、巡检/看板文件 mtime(>48h)、OCR/LLM API Key，异常只发承办人本人。
- **P1 运营度量+知识资产**（`metrics.py`，确定性引擎）：`compute(raw_records, today, window_start, window_end)` 输出办结时长/办结率/退赔率/二次投诉率/周趋势；`compute_knowledge_metrics(corpus_path)` 输出口径库条数/复用次数/覆盖类型数/律师工作量。**周月报和看板都必须取 metrics.py 的输出，禁止让大模型手算指标**。

闭环：信息源新工单→自动入库→巡检盯逾期→告警到钉钉→律师定稿→口径沉淀(golden_corpus)→经验可复用。

## 验证

- 评分：台账 record count 与群工单数一致；五维分=各维度之和
- 巡检：逾期件截止日期<今日
- 起草：法条引用准确，无年份幻觉，退款承诺带"须核实"提示

## 平台扩展：法律咨询口径固化

**智录**是"律师经验固化平台"的第一个落地场景（工商投诉工单），验证了三层架构的可行性。第二个场景——**法律咨询口径固化**（`legal-consult-corpus`）——将同一架构应用于业务群法律咨询，处理"同类问题反复答"的痛点。

### 共享三层架构

**自动化层**（采集+匹配）
- 智录：市监群图片→OCR→工单入库→六键判重
- 法律咨询：业务群文字→咨询识别→领域分类→口径匹配

**智能化层**（分类+起草）
- 智录：五维风险评分→AI起草答复→律师定稿
- 法律咨询：法律领域分类→AI起草回复→律师定稿

**经验固化层**（口径沉淀+复用追踪）
- 智录：golden_corpus.json（投诉答复口径）→办结率/退赔率度量
- 法律咨询：consult_corpus.json（咨询回复口径）→复用率/覆盖率度量

### 平台化愿景

**任何"重复问答→经验沉淀"的法律场景都可用此架构**：

1. **识别重复模式**：某类问题反复出现，律师每次都重新组织语言
2. **建立台账**：结构化记录问题/答复/定稿/复用情况
3. **沉淀口径库**：高质量定稿入库，追踪复用次数与质量评分
4. **度量引擎**：确定性计算复用率/覆盖率/增长率等指标
5. **看板可视化**：单文件HTML展示KPI/趋势/分布

示例场景：
- 合同审查常见问题（审查要点/风险点/修改建议口径库）
- 劳动人事咨询（入离职/考勤/薪酬常见问题口径库）
- 数据合规咨询（GDPR/个人信息保护常见问题口径库）
- IP侵权投诉（商标/专利/著作权投诉处理口径库）

架构核心：**数据源/触发词/法律领域/起草风格均可配置**，新场景只需定义 config.yaml + 口径库结构 + 度量指标，即可复用采集→匹配→起草→定稿→沉淀→度量的完整闭环。
