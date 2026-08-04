# LegalConsult AI — 中国法律咨询AI技能套装

> 基于中国法律知识库，提供合同审查、法律问答、合规检查等AI自动化服务

## 产品定位

帮中小企业和个人用户快速获取法律分析，降低法律咨询成本。

**目标用户**：中小企业主、创业者、个人用户、法务助理。

**核心价值**：选择服务 → 描述问题 → 获取分析，3分钟搞定原本需要请律师咨询¥500-2000的法律分析。

## 功能

| 技能 | 图标 | 说明 |
|------|------|------|
| 合同审查 | 📋 | AI自动审查合同条款，识别法律风险 |
| 法律问答 | ❓ | 中国法律知识问答，覆盖民事/刑事/行政 |
| 企业合规检查 | ✅ | 企业运营合规性全面检查 |
| 劳动争议咨询 | 👷 | 劳动合同、工资、社保、工伤等争议 |
| 知识产权保护 | 🔒 | 商标、专利、著作权、商业秘密保护 |
| 债务催收指导 | 💰 | 欠款追讨、债务纠纷法律指导 |

## 法律知识库

覆盖中国核心法律法规：
- 📜 《民法典》合同编、人格权编
- 👷 《劳动合同法》
- 🏢 《公司法》
- ⚖️ 《合同法》相关条文

## 快速开始

```bash
cd business/skill-bundles/legal-consulting-bundle
pip install -r requirements.txt
copy .env.example .env
py main.py
# 访问 http://localhost:8001
```

## 技术栈

- **后端**: Python FastAPI
- **前端**: HTML + Tailwind CSS
- **LLM**: DeepSeek API（可选，无API时使用内置模板）
- **法律知识库**: Markdown文件

## 商业模式

| 版本 | 价格 | 功能 |
|------|------|------|
| 基础版 | $500 | 3个核心技能 + 安装支持 |
| 专业版 | $2,000 | 全部6个技能 + 1个月技术支持 |
| 企业版 | $5,000 | 全部技能 + 定制化 + 法律知识库更新 |

## API接口

### POST /api/consult
- `skill_type`: 技能类型（contract_review/legal_qa/compliance_check/labor_dispute/ip_protection/debt_collection）
- `question`: 用户问题/描述

### GET /api/skills
列出所有可用技能。

### GET /api/health
健康检查。

## 目录结构

```
legal-consulting-bundle/
├── main.py                    # FastAPI应用
├── requirements.txt           # Python依赖
├── knowledge_base/            # 法律知识库
│   ├── civil_code.md          # 民法典
│   ├── contract_law.md        # 合同法
│   ├── labor_law.md           # 劳动合同法
│   └── company_law.md         # 公司法
├── templates/
│   └── index.html             # Web界面
├── skills/                    # 技能模块（可扩展）
├── config/                    # 配置文件
├── examples/                  # 使用示例
└── README.md                  # 本文件
```

## 复制路径

本技能包模式可复制到其他垂直行业：
1. ⚖️ 法律咨询 ← **本产品**
2. 🐾 兽医诊所 → VetClaw
3. 🏥 中医诊所 → 中医AI助手
4. 📊 财务代理 → 财务自动化
5. 🎓 教育培训 → 教育AI管理

---

**状态**: 💻 代码完成，可运行
**创建时间**: 2026-03-25
**推荐来源**: pending_plan.md P1（垂直技能包方向通过）
