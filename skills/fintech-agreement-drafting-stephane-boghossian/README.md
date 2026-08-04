# fintech-agreement-drafting

一个 [Claude](https://claude.com/claude-code) **技能**，将资深金融科技律师的起草方法转化为**起草与定稿复杂的多支柱受监管支付协议**的可复现、端到端工作流——从接案到签署。

贯穿全文的示例是一个打包了**代理现金存取、QR 支付、钱包电子支付和市场整合**的支付框架，其中持牌支付服务提供商（PSP）在若干条各自带有自身监管特征的服务线上与相对方合作。该方法可泛化适用于任何受监管的多服务金融科技合同。

## 它的功能

按**五个阶段和十四个步骤**推进事项：

| 阶段 | 您的产出 |
| --- | --- |
| **1 — 接案与监管映射** | 活动—许可对照矩阵、已解决的灰色地带分类、真实当事方角色图 |
| **2 — 架构** | 框架加子协议结构；隔离的市场 |
| **横切主题 — 监管/商业平衡** | 可谈判与不可谈判的界线；比例化、按序的控制 |
| **3 — 核心条款起草** | 权限、资金池机制、硬编码的监管上限、合规/数据/审计、责任——全部跟随*控制权* |
| **4 — 执行障碍分诊** | 决策包（障碍 → 路径 → 回退 → 后果） |
| **5 — 迭代与定稿** | 分版带修订追踪的轮次、签署前合规/一致性检查，以及以先决条件收尾未决障碍 |

贯穿每一步的主线：**起草一个字之前先映射监管边界；权限、金钱和责任各自跟随控制权；为支柱独立性而构建结构；找到监管机构接受的最低摩擦结构；并以先决条件诚实地排序。**

## 安装

将文件夹放入您的 Claude 技能目录：

```bash
git clone https://github.com/sboghossian/fintech-agreement-drafting.git \
  ~/.claude/skills/fintech-agreement-drafting
```

然后在 Claude Code 中以 `/fintech-agreement-drafting` 调用它，或仅描述一笔受监管的支付交易，它会被诸如"draft a PSP/agent agreement"、"structure this multi-pillar deal"、"is this QR flow P2P or acquiring?"、"review this fintech contract for compliance."之类的表述触发。

## 文件

- **`SKILL.md`** — 可执行的工作流（技能本身）。
- **`REFERENCE.md`** — 技能所操作化的来源手册原文。

## 范围

这是一种**起草方法，而非法律或监管意见。** 它告诉您特定许可条款（佣金上限、代理上限、KYC 分配、允许的活动、通知义务）*应当*存在于合同中的*何处*，以及*它们应当如何表现* — 它**不**提供它们的取值。每一项都必须与管辖许可文件的实际条款或决定挂钩，且产出需要合格法律和当地监管审查。向公开 AI 工具发出的提示不具有特权；请使用抽象化的占位符开展工作。

## 致谢

方法论作者：**Abbas，[HAQQ Legal AI](https://haqq.ai) 首席法务官**，源自手册 *"Drafting & Finalising a Complex Multi-Pillar Fintech Agreement."* 由 **Stephane Boghossian**（HAQQ Legal AI 增长负责人）打包为 Claude 技能。

## 许可证

[AGPL-3.0](./LICENSE)。任何将本方法构建为托管或分发产品的人都必须开源其衍生作品。
