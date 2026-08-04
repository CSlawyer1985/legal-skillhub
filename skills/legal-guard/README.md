# 🛡️ Legal Guard: Your Digital Agent's Contract Firewall

### Stop Accidental Signatures. Enforce Human Oversight.

**Legal Guard** is a specialized skill for OpenClaw agents that prevents AI from autonomously binding you or your company to legal and financial obligations. It transforms "automated convenience" into "secured collaboration" by enforcing a strictly controlled human-in-the-loop workflow for all signature and contract-related actions.

---

## Why Legal Guard?

AI agents are incredibly efficient at navigating web flows — including DocuSign, Terms of Service gates, and subscription sign-ups. Without guardrails, an agent might interpret "Go ahead" as permission to click "Sign" without you ever seeing the fine print. A free trial auto-converts to a paid plan. A CLA transfers your IP. A changed ToS slips in an arbitration clause.

**Legal Guard creates a hard stop before any of that happens.**

---

## Key Features

- **Broad Trigger Detection**: Catches signature requests, ToS acceptance gates, free-trial sign-ups with payment info, CLA prompts, Terms update banners, and Web3 wallet signing requests — not just DocuSign.
- **Mandatory Executive Summary**: Before any action, the agent must extract and present:
  - Parties, financial commitment, contract duration, auto-renewal terms
  - Key obligations for both sides
  - IP ownership and assignment clauses
  - Governing law, termination conditions, dispute resolution
  - Red flags: non-circumvention, exclusivity, unusual liability
- **Tier 3 Authorization Protocol**: Requires an explicit `/approve <id> allow-once` command — conversational "OK" or "looks good" is never sufficient.
- **Reject Path**: `/approve <id> deny` stops the action and optionally drafts a declination for you.
- **Urgency Awareness**: Surfaces expiry timers prominently without ever using deadline pressure to lower the approval bar.
- **Approval Audit Trail**: Logs the approval ID in the reply after signing so you always have a record.

---

## Real-World Scenarios

### 1. DocuSign Inbox Triage
**Problem**: You have dozens of vendor contracts. Your agent reads them for you — but you don't want it clicking "Sign" just because the content looks standard.
**Legal Guard**: Sends you an Executive Summary on Telegram: *"Service Agreement from AWS — $500/mo, auto-renews annually, governed by Washington state law. Approve with `/approve <id> allow-once`."*

### 2. Free Trial Trap
**Problem**: Agent registers for a SaaS tool, enters your card details into a "free 14-day trial." Billing starts on day 15.
**Legal Guard**: Intercepts the checkout step, surfaces the auto-renewal clause and billing date, and waits for explicit approval before submitting.

### 3. GitHub CLA Prompt
**Problem**: Agent opens a PR to an open-source repo. A CLA bot comments asking to sign the contributor agreement. Agent clicks it.
**Legal Guard**: Stops, summarizes the IP assignment terms in the CLA, and requires your explicit `/approve` before proceeding.

### 4. Terms Update Banner
**Problem**: A SaaS app shows "Our terms have changed." Agent dismisses it as a UI popup and clicks Accept.
**Legal Guard**: Recognizes the ToS update gate, reads the new terms, highlights any changed clauses (arbitration, data sharing), and waits for approval.

### 5. Conversational Slip-up
**Problem**: You say "Looks good, go ahead" after reviewing a summary. Agent treats it as permission to sign.
**Legal Guard**: *"I need a formal `/approve <id> allow-once` command for legal actions — a conversational reply is not sufficient."*

---

## Installation

```bash
openclaw skills install legal-guard
```

Or manually: copy the `legal-guard` folder into your OpenClaw workspace `skills/` directory and restart your session.

---

## Usage

The skill activates automatically when the agent detects a triggering context. No extra configuration required.

To respond to an approval request:

```
/approve <id> allow-once      ← approve this action once
/approve <id> allow-always    ← always allow this action type
/approve <id> deny            ← reject the action
```

---

*"Convenience is great, but trust is earned through safety. Legal Guard ensures your agent is always your protector, never your liability. 🐾"*

---
---

# 🛡️ Legal Guard：你的 AI Agent 合同防火墙

### 阻止意外签署。强制人工监督。

**Legal Guard** 是一款专为 OpenClaw Agent 设计的 Skill，防止 AI 在未经授权的情况下代你签署合同或接受具有法律约束力的条款。它将"自动化便利"转变为"安全协作"，对所有涉及签名和合同的操作强制执行严格的人工审批流程。

---

## 为什么需要 Legal Guard？

AI Agent 在处理网页流程时效率极高——包括 DocuSign、服务条款确认页、订阅注册等。没有护栏的情况下，Agent 可能把你随口说的"好，继续"理解为签名授权，而你根本没看过合同细节。免费试用自动转为付费套餐。CLA 协议转让了你的知识产权。更新后的服务条款悄悄加入了仲裁条款。

**Legal Guard 在这一切发生之前强制拉闸。**

---

## 核心功能

- **广泛的触发检测**：覆盖签名请求、服务条款确认、含支付信息的免费试用注册、CLA 签署提示、条款更新横幅、Web3 钱包签名请求——不只是 DocuSign。
- **强制执行摘要**：在任何操作执行前，Agent 必须提取并呈现：
  - 签约主体、财务承诺、合同期限、自动续费条款
  - 双方核心义务
  - 知识产权归属与转让条款
  - 管辖法律、终止条件、争议解决方式
  - 风险项：不规避条款、排他性、异常责任限制
- **Tier 3 授权协议**：必须使用 `/approve <id> allow-once` 命令——对话中的"好的"或"没问题"不构成授权。
- **拒绝路径**：`/approve <id> deny` 终止操作，并可选择为你起草拒绝回函。
- **紧急情况感知**：显著提示审批到期时间，但绝不允许截止压力降低审批标准。
- **审计记录**：签署完成后在回复中输出 approval ID，确保操作留有记录。

---

## 真实场景

### 1. DocuSign 收件箱整理
**问题**：你有几十份供应商合同，Agent 帮你阅读——但你不希望它看起来"没问题"就直接点签名。
**Legal Guard 的处理**：通过 Telegram 发送执行摘要：*"AWS 服务协议——月费 $500，每年自动续期，适用华盛顿州法律。请用 `/approve <id> allow-once` 授权。"*

### 2. 免费试用陷阱
**问题**：Agent 注册了一个 SaaS 工具的"14天免费试用"，填写了你的信用卡信息。第15天开始扣费。
**Legal Guard 的处理**：在提交结账页面前拦截，提示自动续费条款和首次扣费日期，等待你明确授权后再提交。

### 3. GitHub CLA 提示
**问题**：Agent 向开源仓库提交 PR，CLA bot 发来评论要求签署贡献者许可协议，Agent 点击了。
**Legal Guard 的处理**：停止操作，总结 CLA 中的 IP 转让条款，等待你的 `/approve` 后再继续。

### 4. 服务条款更新横幅
**问题**：某 SaaS 应用弹出"我们的条款已更新"，Agent 将其视为普通弹窗直接点击接受。
**Legal Guard 的处理**：识别条款更新确认框，读取新条款，标记变更内容（如仲裁条款、数据共享），等待审批。

### 5. 对话式误操作
**问题**：你在看完摘要后说"看起来不错，继续吧"，Agent 将其视为签署授权。
**Legal Guard 的处理**：*"法律操作需要正式的 `/approve <id> allow-once` 命令——对话回复不构成授权。"*

---

## 安装

```bash
openclaw skills install legal-guard
```

或手动安装：将 `legal-guard` 文件夹复制到 OpenClaw 工作区的 `skills/` 目录，重启会话后生效。

---

## 使用方法

当 Agent 检测到触发场景时，该 Skill 自动生效，无需额外配置。

收到审批请求后，使用以下命令响应：

```
/approve <id> allow-once      ← 仅此次授权
/approve <id> allow-always    ← 永久允许此类操作
/approve <id> deny            ← 拒绝此次操作
```

---

*"便利固然美好，但信任建立于安全之上。Legal Guard 确保你的 Agent 永远是你的守护者，而非你的风险来源。🐾"*
