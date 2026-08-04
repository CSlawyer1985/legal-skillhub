---
name: lexmage-constructionlaw-js2
description: Lexmage《建设工程施工合同司法解释（二）》一体化工程法律技能。接收案情简介、合同、起诉状、答辩状、代理词、法律意见、裁判文书、证据材料或专业文章，自动识别法释〔2026〕12号带来的规则变化和法律适用问题，并在快速扫描、深度审查、合同体检、文书纠偏、文章校准、角色策略和新旧规则对照中选择合适工作流。用户说“按建工解释二审查”“看看哪里变了”“修改这份工程文书/合同”“站在发包人或承包人角度给建议”“检查技能更新”或不知道该选择哪种模式时使用。
---

# Lexmage《建工解释二》一体化技能

## 定位

这是面向 SkillHub、WorkBuddy、TRAE Work 等客户端封装的单 Skill 版本。它把总控、六种专业工作流、共享知识库和更新检查规则放在一个目录内。

把 `references/suite/skills/` 下的各个 `SKILL.md` 视为本技能的内部工作流文件，不要求用户分别安装，也不要把内部路径暴露给用户。

## 启动规则

除纯更新请求外，每次任务先完整读取：

1. `references/suite/skills/construction-contract-ii-router/SKILL.md`
2. `references/suite/skills/construction-contract-ii-router/references/common-protocol.md`
3. `references/suite/skills/construction-contract-ii-router/references/knowledge-base/00-知识库导航与使用边界.md`
4. `references/suite/skills/construction-contract-ii-router/references/knowledge-base/01-总论-到底改了什么.md`

然后由总控选择一个主模式，必要时选择不超过两个辅助模式，并完整读取相应内部工作流：

- 快速扫描：`references/suite/skills/construction-contract-ii-quick-scan/SKILL.md`
- 深度审查：`references/suite/skills/construction-contract-ii-deep-review/SKILL.md`
- 合同体检：`references/suite/skills/construction-contract-ii-contract-check/SKILL.md`
- 文书纠偏：`references/suite/skills/construction-contract-ii-document-corrector/SKILL.md`
- 文章校准：`references/suite/skills/construction-contract-ii-article-calibrator/SKILL.md`
- 角色策略：`references/suite/skills/construction-contract-ii-role-strategy/SKILL.md`

用户要求检查、升级或更新本技能时，读取并执行 `references/update-policy.md`，不要进入普通法律审查模式。

## 使用原则

1. 用户不需要知道模式名称。先给实质结果，再简要说明采用的审查方式。
2. 先审时间效力，再审主体、合同效力、请求权、金额、证据和程序。
3. 不以“实际施工人”等标签替代具体法律身份和请求权构成。
4. 不把关键词命中写成法律要件已经满足。
5. 区分规范结论、事实判断、证据判断、风险评估和策略建议。
6. 信息不足时先按已知事实提供分情形方向，再追问最多五个会改变结论的问题。
7. 用户要求修改文件时，完成可直接使用的修改稿或替换文本，不只给原则性建议。
8. 对现行法律、后续案例、地方规则或程序期限存在变化可能时，先检索有权机关最新来源。

## 知识库纪律

- 需要逐字引用《建工解释二》时，只读取 `references/suite/skills/construction-contract-ii-router/references/knowledge-base/official/01-法释2026-12号全文.md`。
- 答记者问用于解释背景，典型案例用于说明事实组合，不得把它们扩张为条文未规定的一般规则。
- 对外披露法源时使用最高人民法院及其他有权机关公开来源。
- 不披露商业讲座、付费出版物、客户材料或内部研究语料名称。
- 法律基准和版本信息见 `references/suite/skills/construction-contract-ii-router/references/version.md`。

## 交付质量

交付前执行 `references/suite/skills/construction-contract-ii-router/references/final-quality-gate.md`。

对于具体案件，默认在结尾提示输出属于研究与工作辅助，应由使用者结合完整证据、现行法和主管法院实践复核。完整免责声明和来源边界见 `references/legal/`。
