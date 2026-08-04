# Agent Commercial Contract

**English** | [中文](#中文版本)

---

## English Version

**Tagline**: The Legal Layer for Agent-to-Agent Commerce

**Category**: Automation / Legal Tech

**Version**: 1.0.0

---

### What is it?

Agent Commercial Contract is a comprehensive smart contract framework that enables AI agents to autonomously negotiate, sign, execute, and enforce commercial agreements. It provides the legal and financial infrastructure necessary for agent-to-agent commerce.

---

### Core Capabilities

**Contract Management**
- Create legally-binding contracts from templates or custom terms
- Multi-party digital signatures with cryptographic verification
- Automated contract lifecycle (draft → signed → active → completed)
- Milestone-based execution with deliverable tracking
- Full audit trail of all contract events

**Agent Identity & Authentication**
- Cryptographic identity system with public/private key pairs
- Digital signature generation and verification
- API key-based authentication
- Capability-based access control

**Escrow & Payment**
- Automated payment holding in secure escrow accounts
- Milestone-based fund release mechanisms
- Refund and dispute handling
- Multi-currency support
- Complete transaction history

**Dispute Resolution**
- Structured dispute raising with evidence submission
- Arbitrator assignment (human or AI)
- Evidence verification with cryptographic hashing
- Automated compensation calculation
- Resolution enforcement

---

### When to Use This Skill

**AI Agent Marketplaces**
Build marketplaces where AI agents can buy and sell services with automatic contract enforcement.

**Multi-Agent Collaboration**
Enable multiple agents to work together on projects with clear terms, milestone-based payments, and automated conflict resolution.

**API-as-a-Service Networks**
Create networks where agents monetize their APIs with usage tracking, billing automation, and SLA enforcement.

**Data Exchange Platforms**
Build secure platforms for agents to buy/sell datasets with quality guarantees, escrow protection, and provenance tracking.

---

### Quick Start

**Installation**:
```bash
npm install agent-commercial-contract
```

**Basic Usage**:
```typescript
import AgentCommercialContract from 'agent-commercial-contract';

const sdk = new AgentCommercialContract();

// Register agents
const provider = await sdk.identity.registerAgent('Provider AI', ['data-processing']);
const consumer = await sdk.identity.registerAgent('Consumer AI', ['analytics']);

// Create contract with escrow
const result = await sdk.createContractWithEscrow(
  provider.data.identity,
  consumer.data.identity,
  {
    title: 'Data Processing Service',
    service: { type: 'data-processing', specification: '...' },
    payment: { amount: 5000, currency: 'USD', structure: 'milestone' },
    timeline: { duration: 30 },
  }
);
```

**CLI Commands**:
```bash
# Register agent
agent-contract agent register --name "My Agent" --capabilities "data-processing"

# Create contract
agent-contract contract create \
  --provider agent_xxx \
  --consumer agent_yyy \
  --title "Service Agreement" \
  --amount 1000 \
  --with-escrow

# View dashboard
agent-contract dashboard --agent agent_xxx
```

---

### Integration with AI Agents

**Autonomous Agent Workflow**:
```typescript
class AutonomousAgent {
  constructor(private sdk: AgentCommercialContract) {}

  async offerService() {
    await this.sdk.identity.registerAgent('My Service Bot', ['data-processing']);
  }

  async acceptContract(contractId: string) {
    const contract = this.sdk.contracts.getContract(contractId);
    if (this.canFulfill(contract)) {
      const signature = this.generateSignature(contract);
      await this.sdk.contracts.signContract({
        contractId,
        agentId: this.agentId,
        signature,
        credentials: this.credentials,
      });
    }
  }

  async deliverWork(contractId: string, milestoneId: string) {
    await this.sdk.completeMilestoneAndPay(contractId, milestoneId, this.agentId);
  }
}
```

---

### Security & Best Practices

**Cryptographic Security**:
- RSA 2048-bit keys for digital signatures
- SHA-256 hashing for evidence integrity
- Secure key storage recommendations
- API key rotation support

**Legal Enforceability**:
- Digital signatures legally binding
- Jurisdiction specification in contracts
- Audit trails for compliance
- Dispute resolution mechanisms

**Best Practices**:
- Never commit private keys to version control
- Use environment variables for sensitive data
- Implement key rotation policies
- Maintain comprehensive audit logs
- Test contracts in staging environment first

---

### API Reference

**ContractManager**:
- `createContract()` - Create new contract
- `signContract()` - Sign with digital signature
- `activateContract()` - Activate signed contract
- `completeContract()` - Mark as completed

**EscrowManager**:
- `createEscrow()` - Create escrow account
- `deposit()` - Deposit funds
- `release()` - Release payment
- `refund()` - Process refund

**DisputeManager**:
- `raiseDispute()` - Raise dispute
- `submitEvidence()` - Submit evidence
- `resolveDispute()` - Resolve with ruling

---

### Dependencies

- TypeScript: Type-safe development
- nanoid: Unique ID generation
- better-sqlite3: Local contract storage (optional)
- jsonwebtoken: JWT authentication
- chalk: CLI output formatting
- commander: CLI framework

---

### Support

- **GitHub**: https://github.com/ZhenRobotics/agent-commercial-contract
- **Documentation**: Full API docs and guides
- **Issues**: Bug reports and feature requests

---

### License

MIT License - Free for commercial and personal use

---

<a name="中文版本"></a>

## 中文版本

**标语**: AI Agent 商业交易的法律层

**分类**: 自动化 / 法律科技

**版本**: 1.0.0

---

### 这是什么？

Agent Commercial Contract 是一个综合性智能合约框架，使 AI Agent 能够自主协商、签署、执行和强制执行商业协议。它为 Agent 之间的商业交易提供必要的法律和金融基础设施。

---

### 核心能力

**合同管理**
- 从模板或自定义条款创建具有法律约束力的合同
- 带加密验证的多方数字签名
- 自动化合同生命周期（草稿 → 已签署 → 活跃 → 完成）
- 基于里程碑的执行与可交付成果跟踪
- 所有合同事件的完整审计追踪

**Agent 身份与认证**
- 具有公钥/私钥对的加密身份系统
- 数字签名生成和验证
- 基于 API 密钥的认证
- 基于能力的访问控制

**托管与支付**
- 在安全托管账户中自动保管付款
- 基于里程碑的资金释放机制
- 退款和纠纷处理
- 多币种支持
- 完整的交易历史

**纠纷解决**
- 结构化的纠纷提出与证据提交
- 仲裁员分配（人工或 AI）
- 使用加密哈希的证据验证
- 自动补偿计算
- 决议执行

---

### 何时使用此 Skill

**AI Agent 市场**
构建 AI Agent 可以买卖服务的市场，具有自动合同执行功能。

**多 Agent 协作**
使多个 Agent 能够在项目上协作，具有明确的条款、基于里程碑的付款和自动冲突解决。

**API 即服务网络**
创建 Agent 将其 API 货币化的网络，具有使用跟踪、自动计费和 SLA 执行。

**数据交换平台**
构建 Agent 买卖数据集的安全平台，具有质量保证、托管保护和来源跟踪。

---

### 快速开始

**安装**：
```bash
npm install agent-commercial-contract
```

**基本用法**：
```typescript
import AgentCommercialContract from 'agent-commercial-contract';

const sdk = new AgentCommercialContract();

// 注册 Agent
const provider = await sdk.identity.registerAgent('提供者 AI', ['数据处理']);
const consumer = await sdk.identity.registerAgent('消费者 AI', ['分析']);

// 创建带托管的合同
const result = await sdk.createContractWithEscrow(
  provider.data.identity,
  consumer.data.identity,
  {
    title: '数据处理服务',
    service: { type: 'data-processing', specification: '...' },
    payment: { amount: 5000, currency: 'USD', structure: 'milestone' },
    timeline: { duration: 30 },
  }
);
```

**CLI 命令**：
```bash
# 注册 Agent
agent-contract agent register --name "我的 Agent" --capabilities "data-processing"

# 创建合同
agent-contract contract create \
  --provider agent_xxx \
  --consumer agent_yyy \
  --title "服务协议" \
  --amount 1000 \
  --with-escrow

# 查看仪表板
agent-contract dashboard --agent agent_xxx
```

---

### 与 AI Agent 集成

**自主 Agent 工作流**：
```typescript
class AutonomousAgent {
  constructor(private sdk: AgentCommercialContract) {}

  async offerService() {
    await this.sdk.identity.registerAgent('我的服务机器人', ['数据处理']);
  }

  async acceptContract(contractId: string) {
    const contract = this.sdk.contracts.getContract(contractId);
    if (this.canFulfill(contract)) {
      const signature = this.generateSignature(contract);
      await this.sdk.contracts.signContract({
        contractId,
        agentId: this.agentId,
        signature,
        credentials: this.credentials,
      });
    }
  }

  async deliverWork(contractId: string, milestoneId: string) {
    await this.sdk.completeMilestoneAndPay(contractId, milestoneId, this.agentId);
  }
}
```

---

### 安全性与最佳实践

**加密安全**：
- 用于数字签名的 RSA 2048 位密钥
- 用于证据完整性的 SHA-256 哈希
- 安全密钥存储建议
- API 密钥轮换支持

**法律可执行性**：
- 数字签名具有法律约束力
- 合同中的司法管辖区规范
- 用于合规的审计追踪
- 纠纷解决机制

**最佳实践**：
- 切勿将私钥提交到版本控制
- 使用环境变量存储敏感数据
- 实施密钥轮换策略
- 维护全面的审计日志
- 先在测试环境中测试合同

---

### API 参考

**ContractManager（合同管理器）**：
- `createContract()` - 创建新合同
- `signContract()` - 使用数字签名签署
- `activateContract()` - 激活已签署的合同
- `completeContract()` - 标记为已完成

**EscrowManager（托管管理器）**：
- `createEscrow()` - 创建托管账户
- `deposit()` - 存入资金
- `release()` - 释放付款
- `refund()` - 处理退款

**DisputeManager（纠纷管理器）**：
- `raiseDispute()` - 提出纠纷
- `submitEvidence()` - 提交证据
- `resolveDispute()` - 以裁决解决

---

### 依赖项

- TypeScript：类型安全开发
- nanoid：唯一 ID 生成
- better-sqlite3：本地合同存储（可选）
- jsonwebtoken：JWT 认证
- chalk：CLI 输出格式化
- commander：CLI 框架

---

### 支持

- **GitHub**: https://github.com/ZhenRobotics/agent-commercial-contract
- **文档**: 完整的 API 文档和指南
- **问题**: 错误报告和功能请求

---

### 许可证

MIT 许可证 - 可免费用于商业和个人用途

---

**为 AI Agent 提供法律和金融自主权** 🤖⚖️
