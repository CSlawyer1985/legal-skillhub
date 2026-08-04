---
name: cue-legal-research
description: "【金融AI调研】用Cue跑法律合规深度尽调。覆盖企业合规风险体检、关联方制裁暴露核查、境外诉讼案例检索、中外法律对比、监管问询答复，300+公开数据源交叉验证。适用于金融风控合规、投融资法务、跨境金融交易。"
description_zh: "【金融AI调研】用Cue跑法律合规深度尽调。覆盖企业合规风险体检、关联方制裁暴露核查、境外诉讼案例检索、中外法律对比、监管问询答复，300+公开数据源交叉验证。适用于金融风控合规、投融资法务、跨境金融交易。"
license: MIT
metadata:
  source: cuecue.cn/playbook
  scene: "法律与行研"
  generated_from: /api/playbook
---

# Cue「法律与行研」研究 skill

加载本 skill 后，你可以用 Cue 跑这个场景的深度研究（多源公开数据交叉、结论带来源链接）。

## 何时用
法律与行研：信披与监管、企业尽调、产业链与研报。

## 当前可用搭子（仅供理解；运行时以 live 为准）
  - 企业合规风险体检：进场前穿透职务发明纠纷、VIE 异常、历史对赌与隐性舆情，对标发审问询与合规红线，产出红旗预警报告、访谈提纲与底稿索取目
  - 监管问询答复案例库：穿透交易所审核动态，针对非标合规问题匹配已过会企业的问询原文与回复样本，产出可直接复用的答辩口径与证据框架。
  - 境外诉讼案例库：中国企业出海，最怕在别人地盘上吃官司。围绕一个主题检索主要法域的公开判例与监管公告，归纳诉因、判决倾向与对中国主体的合规
  - 疑难法律实操案例库：遇到拿不准的法律问题，先看别人怎么判、怎么办。围绕一个争议点检索公开裁判文书、监管问答与实务案例，归纳裁判要点、争议焦点
  - 国内法规调研：快速检索国内法律法规与行政令原文，梳理立法背景与合规要点，覆盖金融监管、工商登记、司法涉诉等多源公开数据。
  - 关联方制裁暴露核查：从股权穿透扩出关联主体集，逐个核查OFAC/欧盟/新加坡制裁名单，产出主体-关系-命中/未命中-来源的暴露底稿。
  - 立案调查案例库：被立案的上市公司，都栽在哪些事由上？基于官方公告拉网式排查指定类型的立案调查案例，把核心事由结构化归类，帮你建一个可检索
  - 中外法律对比：围绕一个法律议题横跨多法域取法条原文与学术文献,做比较法分析——各法域规则异同、立法背景与学界观点,产出带原文出处与引文

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
1. **拉本场景当前搭子**：`GET https://cuecue.cn/api/playbook`，找 `secondary_category == "法律与行研"` 的 scene，读 `buddies[]`（每个有 `template_id`/`title`/`goal`）。若该场景当前不在返回里（临时未达展示门槛）→ 告知用户暂不可用。
2. **选一个搭子**：**委托 cue-research 的匹配逻辑**（其 `+match`/Stage-2：对 `goal` 做语义匹配、把用户的具体主体从匹配中剥离、弱命中先列 ≤2 候选确认）——不要只按字面 title 关键词裸选。取选中搭子的 `template_id`。
3. **确认 credits（强制）**：跑深度研究消耗 credits。运行前显式问用户「将用搭子 X 跑【主体】，耗 credits，是否继续？」并等确认。
4. **跑**：`python3 ~/.cue/cue-skills/cue-research/scripts/research_run.py --query "<用户主体/问题>" --template-id <template_id>`（用上一节就绪的 runner 路径；已装 cue-skills 则用你本地的 `cue-research/scripts/research_run.py`）。深度研究 3–15 分钟；长跑 live 流常不带报告段，用 replay 取最终报告。 读 runner 末行 `RESULT ok|empty`：`empty` → 告知用户本次未取到内容、可换主体/搭子重试，**不要编造**。
5. **回报**：把带来源链接的报告交给用户，不去掉来源、不杜撰。

## 前置
- Cue 账号 API key（cue CLI 登录后在 `~/.cue/config.json`，runner 自动读）；新账号送免费积分（注册 50 + 每天 10），可先免费试。
- `git` + `python3`（自举 runner 用；runner 仅标准库）。
- 跑深度研究**消耗 credits**；只覆盖公开数据，不替代尽调/法律/核保。
