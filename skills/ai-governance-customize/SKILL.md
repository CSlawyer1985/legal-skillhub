---
name: ai-governance-customize
description: 对 AI 治理合规 profile 做单点调整——不需要重跑整个 cold-start 访谈。可调公司基础信息、AI 活动角色（Provider/Deployer）、监管足迹、红线清单、用例注册表、供应商立场、政策承诺、备案状态、集成状态 9 大节中的任意子项。 用户说"改我的 [某项]""更新一下 ai-governance profile""调一下红线""微调供应商立场""customize"时触发。 本 skill 仅覆盖中国大陆 AI 治理法规——其他法域 AI 治理请走当地服务或律所。
metadata:
  displayName: 智治配置调整
  argument-hint: '[--section <名称> | 描述要改的事]'
---

# AI 治理合规-业务规范 单点调整

## 何时触发

用户希望微调 AI 治理 profile 中的某一项——监管足迹、红线、供应商立场、用例注册表条目、备案状态、政策承诺——但不想从头跑 cold-start，也不想手改 markdown。

## 业务规范 resolver 状态判定

读取以下两份文件：

```text
$LEGAL_AGENT_PROFILE_HOME/ai-governance-legal/profile.md
$LEGAL_AGENT_PROFILE_HOME/company-profile.md
```

按 profile 当前状态选择行为：

- **profile 不存在 / 含 `[待填写]`** → 停止，告诉用户："你还没跑 setup。请先运行 `ai-governance-cold-start-interview`——customize 是用来微调**已有** profile 的，不是用来从零开始的。"
- **paused at**（含 `<!-- SETUP PAUSED AT: -->`） → 停止，告诉用户："上次访谈停在了某一步。请先回到 `ai-governance-cold-start-interview` 把暂停部分完成，再来 customize。"
- **已填充** → 继续 What to do。

绝对不允许在 profile 仍含 `[待填写]` 时用 customize 的逐项流程"代替" cold-start——customize 是一次改一项，cold-start 是把整个画像放在一起问。

## What to do

### Step 1：列出可调项映射

按以下分组列出当前值（一句话摘要），让用户挑一项：

- **公司基础信息**——名称、主营业务、规模、市场、上市状态、合规负责人 *（共享 profile：来自 `$LEGAL_AGENT_PROFILE_HOME/company-profile.md`，会影响所有业务 cluster + ai-governance 集群）*
- **AI 活动角色**——Provider / Deployer / 两者；AI 系统数量估计；种子文档参考样本
- **监管足迹**——ICP / 算法推荐 / 深度合成 / 生成式 AI / 人脸识别 / PIPL / 数据安全 / 拟人化互动 / 伦理审查 / 内容标识中哪些适用
- **红线清单**——公司明确禁止的 AI 用例或行为（这是 `ai-governance-use-case-triage` 一票否决的源头）
- **用例注册表（种子）**——已批准 / 在审 / 已禁用的 AI 用例及其触发法规与分类
- **供应商 AI 立场**——训练数据使用 / 数据境内存储 / 立场等级（严格 / 标准 / 基准）/ 升级联系人
- **AI 政策承诺**——现有政策 / 覆盖范围 / 人工审核要求 / AI 内容标识 / 员工培训 / 政策更新日期
- **备案状态**——算法备案 / 生成式 AI 服务备案 / 人脸信息备案 / AI 伦理委员会
- **集成状态**——元典法规库 / 案例库 / 企业信息库可用性 / 协同工具 / 文档平台

提示用户："想改哪一项？挑一个分组，或直接用自己的话描述要改的内容。"**不要**一次问完全部，也不要主动建议改某一项——除非用户已经先说明了方向。

### Step 2：单点改动

用户选定一项后：

1. 显示当前值（精确到要改的子项）。
2. 询问新值。
3. 解释下游影响（命中哪些 ai-governance-* skill / 哪些工作流会随之变化）。
4. 显示精确 diff 等待确认。
5. 确认后写入 profile。

典型例子：

- *AI 活动角色 Deployer → 两者（新增 Provider 维度）：* "`ai-governance-aia-generation` 现在会按 per-system 双维度判断；`ai-governance-inventory` 在新增 AI 系统时会问角色；备案触发判定（算法 / 生成式 AI 服务）适用范围扩大。tradeoff：合规义务清单增加，建议同步走一次 `ai-governance-reg-gap-analysis` 复核现有系统是否漏掉 Provider 侧义务。"
- *新增红线条目（"公共场所人脸识别识别个体身份"）：* "`ai-governance-use-case-triage` 后续遇到此类用例直接结论为不审批；已批准的同类用例需要追溯——建议同步走 `ai-governance-policy-monitor` --sweep 扫描是否已落入实际部署。"
- *监管足迹新增 "人脸识别"：* "`ai-governance-aia-generation` 现在评估范围加入《人脸识别办法》第 5 / 9 / 10 / 13 / 15 条；`ai-governance-vendor-ai-review` 13 项条款审查含人脸信息境内存储 + 单独同意要求；`ai-governance-inventory` 分类时新增"人脸识别"监管类型选项；"
- *供应商立场等级 标准 → 严格：* "`ai-governance-vendor-ai-review` 现在 13 项条款审查门槛抬高——训练数据默认 opt-out、数据境内存储强制要求、Sub-processor 事前同意、审计权独立保留；既有已签合同与新立场的偏离会进入 review 队列。"
- *备案状态 算法备案 → 已完成：* "`ai-governance-inventory` 中相关系统状态同步；`ai-governance-policy-monitor` 不再把算法备案列为漂移项；`ai-governance-reg-gap-analysis` 已完成项目从差距清单移除。"

### Step 3：共享 profile 改动的跨集群 提示

如果改的是 `company-profile.md` 中的共享字段（公司名、行业、规模、市场、上市状态）：

1. 写入 `$LEGAL_AGENT_PROFILE_HOME/company-profile.md`。
2. 明确提示："本次改动影响所有业务 cluster——commercial 的合同主体信息 / privacy 的数据控制者身份 / regulatory 的 watchlist 适用 / employment 的雇主主体 / ai-governance 的 AI 服务提供者身份。建议同步走一次 `ai-governance-policy-monitor` --sweep 检查跨集群 一致性。"

### Step 4：收尾

写完后说一句："已完成。下次 ai-governance-* skill 的输出会反映这次改动。还有其他要调的吗？随时可以再跑 `ai-governance-customize`。"

## Guardrails

- **法定下限拒绝降低。** 用户要求降低法定义务（如把"PIPL 第 55 条强制 PIA"改成"自愿评估"、把"人脸信息单独同意"改成"概括同意"、把"算法备案触发条件"放宽到法定阈值之下）→ 拒绝。解释"这是法定下限，不能通过 profile customize 越过——profile 是公司**自定义**的高线/红线，法定义务是**底线**。"
- **未施行法规结论不可降级。** 用户要求把《人工智能拟人化互动服务管理暂行办法》（2026-07-15 尚未施行）的相关 profile 项标"不适用"或删除 → 拒绝。解释"该办法 2026-07-15 施行，目前虽未生效但提前布局必要——`ai-governance-use-case-triage` 在施行前会标 `[尚未施行 - 复核于施行后]`，不直接禁止涉及拟人化互动的用例。"
- **不可删除 section。** 用户说"删掉某段"时，改为写 `[暂不配置]` + 一句话解释这会让对应 skill 的行为退化为缺省（如未配置红线 → use-case-triage 仅靠法定红线把关；未配置供应商立场 → vendor-ai-review 按基准立场审查）。
- **flag 内部不一致。** 改动后若出现自相矛盾（例：角色声明 Deployer 但用例注册表里有自研生成式 AI 系统；监管足迹勾选"人脸识别"但用例注册表中无人脸识别用例；供应商立场严格但已签合同接受了训练数据默认 opt-in）→ 停下来 surface 这个矛盾，并问用户希望保留哪一边。**不要**自动调整另一边——profile 是用户的画像，矛盾决策权在用户。
- **flag guardrail 降级。** `[需核验]` 标签、`[需审查]` 标签、来源 attribution 标签、`[尚未施行 - 复核于施行后]` 标签、非律师 attorney-confirmation 门、备案触发提示——这些是 load-bearing，**不允许**通过 customize 关闭。如果用户要求关闭，解释"这一项保护的是 [审查质量 / 来源可追溯 / 法规时效正确性 / 非律师场景 attorney-confirmation / 法定义务履行证据链]，关闭后下游 skill 输出会失去 [对应保护]——你确认要降级吗？"——只有用户显式确认理解 tradeoff 后才能写入（且必须在 profile 中明示标注"已降级，原因：[用户说明]"）。
- **一次改一项。** 用户给一组 4-5 项变更时，先列出来，逐项确认。不要试图一次写完——customize 的价值就是单点改动 + 显式 diff + 明示下游影响。
- **写入前精确 diff。** 改动落盘前以 `-`/`+` 形式展示精确 diff（不是含糊"我会把它改成..."），等用户回 "确认"/"yes" 后再写。
- **不要重跑 cold-start。** customize 不会重新问 9 大节、不重新核监管框架、不重新核连接器。这些是 cold-start `--check-integrations` 或 `--redo` 的活。
- **共享 profile 改动 surface 跨集群 影响**。`company-profile.md` 中的字段被多个 cluster 共用，改动必须明示影响范围。

## 升级 / 决策门

非律师调改具有法律后果的字段（监管足迹勾选 / 取消、红线条目增删、供应商立场等级、备案状态确认、用例注册表分类升降）：customize 在写入前提醒"该调整会改变 [对应 ai-governance-* skill] 的输出口径——你是律师还是已与律师复核过该调整？"——非律师且无律师复核时停下等待用户明确同意。涉及法定义务履行证据链的字段（备案完成日期、PIA 评估保留期限、伦理审查决议）必须有律师复核记录。

## 输出

外发性：本 skill 不产生外发文件。所有改动落盘到 profile，profile 是内部资产。

**工作成果头部**（按 profile 角色 + 法域）：

- 律师 + 中国法：`保密 / 内部法律分析 — 在法律顾问指导下准备`
- 律师 + 其他法域：本 skillpack 不覆盖（请走当地工具或律所）
- 非律师：`内部记录 — 法务复核前不作为正式法律意见`
- 外发：去工作成果头（profile 是内部资产，不外发）

## 交接

完成 customize 后按改动内容建议下一步：

- 改了**红线 / 用例注册表** → 建议 `ai-governance-policy-monitor --sweep` 扫描历史评估输出是否落入新红线
- 改了**监管足迹 / 备案状态** → 建议 `ai-governance-reg-gap-analysis` 复核现有系统是否漏掉新增义务
- 改了**供应商立场** → 建议对已签合同走 `ai-governance-vendor-ai-review` 复审
- 改了**政策承诺** → 建议 `ai-governance-policy-starter` 起草政策修订草稿 + 法务复核
- 改了**company-profile.md 共享字段** → 跨集群 影响，提示用户在 commercial / privacy / regulatory / employment / legal-research-cn 各自下一次工作前留意

## 不做的

- **不**起草 PIA / DPA / 合规评估正文（那是 `ai-governance-aia-generation` / `ai-governance-vendor-ai-review` 的活）。
- **不**做法规检索（那是 `ai-governance-reg-gap-analysis` / `legal_research.search_laws` 的活）。
- **不**生成对外通知（gateway 永不直接外发；通知预览走 `legal_notification_preview` MCP 工具）。
- **不**修改本目录之外的文件（`commercial-legal/profile.md` 等其他 cluster profile 由对应 customize skill 改）。
- **不**绕过法定下限或未施行法规标记——这些是硬性，customize 没有授权。
