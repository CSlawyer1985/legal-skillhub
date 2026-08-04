# founder-agreement-drafting

一个 [Claude](https://claude.com/claude-code) **技能（skill）**，将**创始人/联合创始人协议**的起草与
审查转化为可重复的方法——即锁定共同创办公司的人之间**股权、成熟（vesting）、知识产权所有权、角色、
决策机制、僵局解决和离任**安排的文件（或一组条款）。

法域无关，以**特拉华 C 型公司**默认结构为锚点，将争议率最高的条款作为一等公民处理——股权分配、
反向成熟与 83(b) 计时、现在时态知识产权转让、离任机制，以及大多数工具忽略的僵局条款。

## 功能

以**两种模式**运行。

**起草模式（DRAFT）**——五个阶段、十四个步骤，从信息收集到签署：

| 阶段 | 产出 |
| --- | --- |
| **1 — 信息收集与创始人画像** | 创始人-角色图谱、实体/法域确定、贡献清单 |
| **2 — 股权与成熟架构** | 附带*书面理由*的分配方案（而非虚假计算器）、成熟时间表、83(b) 标记、加速 |
| **3 — 核心条款起草** | 知识产权转让、角色与僵局、离任与回购、转让/优先购买权，以及配套条款——落入正确的文件 |
| **4 — 冲突与阻碍分级** | 期望条款 vs 阻碍条款，以及利益分歧点路由至独立律师 |
| **5 — 签署前定稿** | “干净、可投资的股东名册”尽职调查预演；未决阻碍作为交割条件关闭 |

**审查模式（REVIEW）**——对照 18 条条款清单和红旗扫描审查既有协议，输出分级缺口报告
（严重 / 重要 / 可选）。

贯穿每一步的主线：**成熟才是机制，分配不是；记录理由，而非只记数字；现在时态知识产权转让，
否则免谈；每份股份在离任时都必须有归属；在僵局发生之前设计僵局条款；把条款写进正确的文件，
并让它们干净地到期。**

## 安装

将文件夹放入你的 Claude 技能目录：

```bash
git clone https://github.com/sboghossian/founder-agreement-drafting.git \
  ~/.claude/skills/founder-agreement-drafting
```

然后在 Claude Code 中以 `/founder-agreement-drafting` 调用，或直接描述一桩创始人交易，它会
被诸如 *"draft a founders' agreement"、"split equity between founders"、"set up founder
vesting"、"founder IP assignment"、"founder deadlock clause"、"review this founders'
agreement"* 等表述触发。

## 文件

- **`SKILL.md`** ——可执行工作流（技能本身）。
- **`REFERENCE.md`** ——研究基础，含每一条条款、判例法（*Stanford v. Roche*）、股权分配数据
  （Wasserman / NBER）、法域表（特拉华 / LLC / 英国 / MENA）以及一手来源引注。

## 范围

这是一套**起草方法，不构成法律、税务或财务意见。**它告诉你每项创始人条款*应当落在哪里*以及
*应当如何表现*——它**不**认证某项条款在你的法域可执行，不裁决谁“配”获得更多股权，也不推荐
税务选择。它像公司律师那样，为**企业整体**起草：**每位创始人在签署前都应获得独立律师。**
法域特定条款（竞业禁止可执行性、MENA 本土丧失机制、LLC 利润权益税务、83(b) 决策）均标记为
需当地/税务律师处理，而非直接提供。向公共 AI 工具发送的提示词不享有特权保护；请使用脱敏占位符。

## 致谢

出自 **[HAQQ Legal AI](https://haqq.ai)** 的开放法律技能系列，由 **Abbas**（首席法务官）发起。
本方法综合自公开最佳实践来源——Y Combinator、Cooley GO、Clerky、Carta、Orrick、Wilson Sonsini、
SeedLegals、Noam Wasserman / HBS 以及指名判例（全部引注于 `REFERENCE.md`）。由 **Stephane
Boghossian**（HAQQ Legal AI 增长主管）打包为 Claude 技能。

## 许可证

[AGPL-3.0](./LICENSE)。任何人将本方法构建为托管或分发产品，必须开源衍生作品。
