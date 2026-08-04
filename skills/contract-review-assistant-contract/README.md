# 合同检查智能小助手 (Contract Review Assistant)

> 一键式中文合同风险体检：把合同丢进来，产出结构化 Markdown 风险审查报告。
> One-click risk review for Chinese-language contracts, powered by the PRC Civil Code.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Skill Version](https://img.shields.io/badge/version-1.0.0-green.svg)](CHANGELOG.md)

---

## 一句话简介 / Summary

**中文**：基于《民法典》合同编，对买卖、服务、合作、租赁、保密、劳动、借款、技术IP 等各类合同执行结构化审查，自动识别高风险条款、缺失必备要素、合规红线、金额/日期矛盾与笔误，并支持签名笔迹初步比对，最终输出带风险评分与修订建议的 Markdown 报告。

**English**: A reusable Skill that reviews Chinese-language contracts against the PRC Civil Code. It detects high-risk clauses, missing essential terms, compliance red lines, amount/date inconsistencies and typos, offers basic signature verification, and produces a scored Markdown risk report with revision suggestions.

---

## 功能特性 / Features

- **完整性检查**：对照通用必备要素与各类合同要点，逐项标注缺失条款及影响。
- **风险条款识别**：14 类高风险条款目录（单方加重责任、完全免责、管辖不明、任意解除、权属不清、自动续约等），含等级与修改建议。
- **合法合规性审查**：核查格式条款提示义务、违约金 30% 酌减参考线、定金 ≤20%、租赁 ≤20 年等法定红线。
- **歧义与笔误检测**：确定性脚本自动比对金额前后矛盾（兼容中文大写与阿拉伯写法，含财务大写壹贰叁）、占位符、条款跳号、日期格式。
- **签名笔迹比对**：提供签名图片时调用多模态能力做基础筛查（相似度 + 置信度），并明确声明非司法鉴定。
- **结构化报告**：含综合风险评分（封顶 100）与等级（低/中/高/极高）、按等级降序的风险清单、P0–P2 修订建议与签署结论。

---

## 适用场景 / When to Use

- 收到一份合同，想快速知道"有没有坑、能不能签"。
- 关心违约金、管辖、免责、保密、IP 归属等条款是否公平合规。
- 需要一份可交付的合同风险报告或谈判要点清单。
- 需要对比合同签署件上的签名与样本签名。

**不适用**：纯合同起草（无审查意图）、非合同的一般法律咨询。

---

## 使用示例 / Examples

> "审查合同" / "帮我看下这份合同有没有风险" / "合同体检"
> "这份技术服务协议违约金是不是太高了" / "对比一下这两个签名是不是同一个人"

工作流（详见 `SKILL.md`）：
1. 识别合同类型与审查立场（甲方/乙方/中立）。
2. 运行 `scripts/contract_check.py` 抽取结构性事实。
3. 完整性 → 风险条款 → 合规 → 歧义笔误 → 签名 五维审查。
4. 输出带评分与修订建议的 Markdown 报告。

---

## 安装 / Installation

**方式一（本地用户级，已生效）**
技能已位于 `~/.workbuddy/skills/contract-review-assistant/`，对话中输入触发词即可调用。

**方式二（导入 zip）**
将 `contract-review-assistant.zip` 在 WorkBuddy 的技能管理中导入安装。

**方式三（SkillHub 上架后）**
在 SkillHub 搜索 `contract-review-assistant` 一键安装。

---

## 目录结构 / Structure

```
contract-review-assistant/
├── SKILL.md                      # 技能主文件（触发词 + 8 步工作流）
├── README.md                     # 本文件（上架清单内容）
├── _skillhub_meta.json           # SkillHub 上架元数据
├── LICENSE                       # MIT
├── CHANGELOG.md                  # 版本记录
├── scripts/
│   └── contract_check.py         # 确定性检查（标准库，无依赖）
├── references/
│   ├── contract-basics.md        # 民法典要点 + 必备要素 + 各类合同速查
│   ├── risk-catalog.md           # 14 类高风险条款目录
│   └── report-format.md          # 报告结构 + 评分口径 + 签名比对说明
└── assets/
    ├── report_template.md        # 报告 Markdown 骨架
    ├── icon.png                  # 256×256 上架图标（PNG）
    ├── icon.svg                  # 图标矢量源文件
    ├── screenshot-1.png          # SkillHub 预览图：风险审查报告样例
    └── screenshot-2.png          # SkillHub 预览图：对话式体检演示
```

---

## 依赖 / Dependencies

- Python 3.8+（仅使用标准库 `re` / `json` / `sys` / `argparse`，**无需 pip 安装任何包**）。

---

## 法律免责声明 / Legal Disclaimer

本技能提供**合同审查辅助**，所有结论基于规则与通用法律知识的自动化分析，**不构成法律意见**，也不能替代执业律师的专业判断。涉及重大交易、争议或诉讼，请提示用户咨询具备资质的律师。签名笔迹比对为基础筛查，**非司法鉴定**，关键场景须由专业鉴定机构确认。

---

## 版本 / Version

当前版本 `1.0.0`，详见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证 / License

[MIT](LICENSE) —— 可自由使用、修改与分发。
