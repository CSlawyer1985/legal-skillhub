---
name: cue-credit-diligence
description: "【金融AI调研】用Cue跑企业信用尽调深度研究。覆盖工商全景、司法风险、失信被执行、股权穿透、对外担保圈排查，多源公开数据交叉验证。适用于金融信贷审批、供应链金融准入、商务合作尽调。"
description_zh: "【金融AI调研】用Cue跑企业信用尽调深度研究。覆盖工商全景、司法风险、失信被执行、股权穿透、对外担保圈排查，多源公开数据交叉验证。适用于金融信贷审批、供应链金融准入、商务合作尽调。"
license: MIT
metadata:
  source: cuecue.cn/playbook
  scene: "信贷尽调"
  generated_from: /api/playbook
---

# Cue「信贷尽调」研究 skill

加载本 skill 后，你可以用 Cue 跑这个场景的深度研究（多源公开数据交叉、结论带来源链接）。

## 何时用
信贷尽调：企业尽调、信披与监管、财务与业绩。

## 当前可用搭子（仅供理解；运行时以 live 为准）
  - 企业全景画像：一键穿透企业的工商、股权、财务与经营全维基本面，评估业务模式与合作适配性、挖掘供应链金融与产业债机会，产出可用于内部决策
  - 潜在高净值客群挖掘：锁定“潜在有钱人”。精准提取区域内上市公司的股权激励和战略配售人员名单，核算其潜在资产规模，助你抢占大宗交易与高端理财商
  - 集团战略分析：拆解巨头黑箱。穿透分析大型集团（如比亚迪、华为）的全产业链版图与全球政策风险，输出战略仪表盘，为跨国对标或深度尽调提供一
  - 企业财务尽调助手：针对非上市主体公开财务数据缺失，做合规校验、缺口补全与异动穿透，识别潜在错报与业务风险，产出可用于风控汇报的财务分析底稿
  - 对公授信预尽调：多源穿透授信企业的主体真实性、股权关联、经营持续性与合规风险，自动补全公开披露盲区，产出可上初审会、带证据链的预尽调底稿
  - 预尽调企业初筛：仅需一个企业名称，自动穿透股权链、实控人关系网、上下游关键决策人及合规红线，输出客户经理可直接带出去见客的预尽调初筛底稿

## 准备 Cue runner（首次用时，幂等）
本 skill 不自带脚本，靠 Cue 开源 runner 跑研究。先确认 runner 是否就绪：
- 若你已安装 `cue-skills`（或本 skill 来自整包发布）→ 直接用其中的 `cue-research/scripts/research_run.py`，**跳过本节**。
- 否则克隆开源仓（含 cue-research + cue-buddy 全套依赖），**有则更新、无则克隆**（GitHub 不通走镜像）：
  ```bash
  if [ -d ~/.cue/cue-skills/.git ]; then
    git -C ~/.cue/cue-skills pull --ff-only
  else
    git clone https://github.com/sensedeal/cue-skills ~/.cue/cue-skills \
      || git clone https://gitee.com/sensedeal/cue-skills ~/.cue/cue-skills
  fi
  ```
  之后 runner = `~/.cue/cue-skills/cue-research/scripts/research_run.py`。需 `git` + `python3`（runner 仅用标准库）。

## 怎么跑（搭子是动态的，运行时查 live）
1. **拉本场景当前搭子**：`GET https://cuecue.cn/api/playbook`，找 `secondary_category == "信贷尽调"` 的 scene，读 `buddies[]`（每个有 `template_id`/`title`/`goal`）。若该场景当前不在返回里（临时未达展示门槛）→ 告知用户暂不可用。
2. **选一个搭子**：**委托 cue-research 的匹配逻辑**（其 `+match`/Stage-2：对 `goal` 做语义匹配、把用户的具体主体从匹配中剥离、弱命中先列 ≤2 候选确认）——不要只按字面 title 关键词裸选。取选中搭子的 `template_id`。
3. **确认 credits（强制）**：跑深度研究消耗 credits。运行前显式问用户「将用搭子 X 跑【主体】，耗 credits，是否继续？」并等确认。
4. **跑**：`python3 ~/.cue/cue-skills/cue-research/scripts/research_run.py --query "<用户主体/问题>" --template-id <template_id>`（用上一节就绪的 runner 路径；已装 cue-skills 则用你本地的 `cue-research/scripts/research_run.py`）。深度研究 3–15 分钟；长跑 live 流常不带报告段，用 replay 取最终报告。 读 runner 末行 `RESULT ok|empty`：`empty` → 告知用户本次未取到内容、可换主体/搭子重试，**不要编造**。
5. **回报**：把带来源链接的报告交给用户，不去掉来源、不杜撰。

## 前置
- Cue 账号 API key（cue CLI 登录后在 `~/.cue/config.json`，runner 自动读）；新账号送免费积分（注册 50 + 每天 10），可先免费试。
- `git` + `python3`（自举 runner 用；runner 仅标准库）。
- 跑深度研究**消耗 credits**；只覆盖公开数据，不替代尽调/法律/核保。
