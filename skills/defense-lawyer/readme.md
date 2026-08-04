# Defense Lawyer - AI辩护律师助手

[English](#english) | [中文](#chinese)

---

<a name="english"></a>
## English

> AI-powered criminal defense assistant for Chinese legal system

**Version**: 0.1.0 | **License**: MIT

### What is Defense Lawyer?

Defense Lawyer is an AI-powered assistant designed specifically for **criminal defense** in the **Chinese legal system**. It provides comprehensive support for lawyers and legal professionals in case analysis, strategy formulation, and legal document generation.

### Core Features

- **Case Analysis** - Comprehensive case evaluation with conviction and sentencing risk assessment
- **Defense Strategy** - Formulate innocence defense, lesser crime defense, or sentencing defense strategies
- **Evidence Assessment** - Analyze authenticity, legality, and relevance of evidence (three-property test)
- **Legal Research** - Retrieve laws, judicial interpretations, guiding cases, and precedents
- **Document Generation** - Auto-generate defense statements, legal opinions, and appeal petitions
- **Sentencing Analysis** - Identify mitigating factors and assess probation possibilities

### Quick Start

#### Installation

```bash
# Install from source
pip install openclaw-defense-lawyer

# Or clone repository
git clone https://github.com/ZhenRobotics/openclaw-defense-lawyer.git
cd openclaw-defense-lawyer
pip install -e .
```

#### Basic Usage

```python
import asyncio
from datetime import datetime
from defense_lawyer import DefenseLawyer, CriminalCase, Client, Evidence

async def main():
    # Initialize defense lawyer assistant
    lawyer = DefenseLawyer()

    # Define case information
    case = CriminalCase(
        case_id="2024-CASE-001",
        case_name="Zhang Theft Case",
        case_type="Theft",
        charge="Theft Crime",
        incident_date=datetime(2024, 1, 15),
        incident_location="Beijing Chaoyang District Mall",
        case_description="Defendant stole a mobile phone worth 5,000 RMB...",
        proceeding_stage="First instance",
        statutory_penalty="Up to three years imprisonment, criminal detention, or public surveillance",
    )

    # Define client information
    client = Client(
        name="Zhang",
        gender="Male",
        age=28,
        detention_status="Arrested",
        confession_status="Plea bargaining",
        remorse_level="Deep remorse",
        compensation_made=True,
        victim_forgiveness=True,
    )

    # Define evidence
    evidences = [
        Evidence(
            evidence_id="E001",
            evidence_type="Audio-visual material",
            evidence_name="Mall surveillance video",
            relevance="Direct evidence",
            authenticity="Authentic",
            legality="Legal",
            probative_value="Strong",
        ),
    ]

    # 1. Case analysis
    analysis = await lawyer.analyze_case(case, client, evidences)
    print(f"Conviction risk: {analysis.conviction_risk}")
    print(f"Sentencing risk: {analysis.sentencing_risk}")

    # 2. Formulate defense strategy
    strategy = await lawyer.formulate_defense_strategy(case, client, evidences)
    print(f"Strategy type: {strategy.strategy_type}")

    # 3. Sentencing analysis
    sentencing = await lawyer.analyze_sentencing(case, client)
    print(f"Probation possibility: {sentencing.suspended_sentence_possibility}")

    # 4. Generate defense statement
    doc = await lawyer.generate_defense_statement(case, client, strategy)
    with open("defense_statement.md", "w", encoding="utf-8") as f:
        f.write(doc.markdown_content)

asyncio.run(main())
```

### Use Cases

#### Scenario 1: Initial Case Assessment

```python
assessment = await lawyer.quick_assessment(case, client)
print(f"Conviction risk: {assessment['conviction_risk']}")
print(f"Recommended strategy: {assessment['recommended_strategy']}")
```

#### Scenario 2: Trial Preparation

```python
package = await lawyer.complete_defense_package(case, client, evidences)
# Includes: case analysis, strategy, sentencing analysis, defense statement, legal research
```

#### Scenario 3: Evidence Cross-Examination

```python
for evidence in prosecution_evidences:
    assessment = await lawyer.assess_evidence(evidence)
    print(f"Score: {assessment.overall_score}/100")
    print(f"Cross-examination strategies: {assessment.challenge_strategies}")
```

### Testing

```bash
# Run complete test suite
python3 test_complete.py

# Run example
python3 example.py
```

**Test Coverage**: 7/7 modules passing (100%)

### Python Advantages

| Feature | Python | JavaScript |
|---------|--------|------------|
| PDF Processing | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Document Generation | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Data Analysis | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Legal Databases | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### Disclaimer

**What Defense Lawyer Can Do:**
- Provide professional case analysis and recommendations
- Assist in formulating defense strategies
- Generate legal document drafts
- Provide legal research and case references

**What Defense Lawyer Cannot Do:**
- Replace professional legal judgment
- Guarantee specific litigation outcomes
- Provide formal legal opinions
- Replace attorney courtroom defense

**Important**: This system serves as a legal assistance tool only. All outputs require review by licensed attorneys before use.

### Roadmap

**v0.2.0** (2026 Q2)
- Real legal database API integration
- Support for 50+ common crimes
- Civil case support
- LaTeX format document output

**v0.3.0** (2026 Q3)
- Multi-jurisdiction legal differences
- Case similarity analysis
- Visualization of sentencing charts
- Team collaboration features

### License

MIT License - See [LICENSE](LICENSE)

### Links

- **GitHub**: https://github.com/ZhenRobotics/openclaw-defense-lawyer
- **Issues**: https://github.com/ZhenRobotics/openclaw-defense-lawyer/issues
- **Author**: Justin Wang (code@zhenrobot.com)

---

<a name="chinese"></a>
## 中文

> AI驱动的刑事辩护专业助手 - 为中国法律体系量身定制

**版本**: 0.1.0 | **许可证**: MIT

### Defense Lawyer 是什么？

Defense Lawyer 是一个专为**刑事辩护**设计的AI助手系统，针对**中国法律体系**，为律师和法律工作者提供全面的案件分析、辩护策略制定和法律文书生成支持。

### 核心功能

- **案件分析** - 全面的案件事实总结、法律适用分析、定罪/量刑风险评估
- **辩护策略** - 制定无罪辩护、罪轻辩护、量刑辩护等多种策略
- **证据评估** - 分析证据的真实性、合法性、关联性（证据三性）
- **法律研究** - 检索相关法律法规、司法解释、指导性案例和判例
- **文书生成** - 自动生成辩护词、法律意见书、上诉状等法律文书
- **量刑分析** - 识别从轻减轻情节，分析缓刑可能性，提出量刑建议

### 快速开始

#### 安装

```bash
# 从 PyPI 安装
pip install openclaw-defense-lawyer

# 或者克隆仓库
git clone https://github.com/ZhenRobotics/openclaw-defense-lawyer.git
cd openclaw-defense-lawyer
pip install -e .
```

#### 基础用法

```python
import asyncio
from datetime import datetime
from defense_lawyer import DefenseLawyer, CriminalCase, Client, Evidence

async def main():
    # 初始化辩护律师助手
    lawyer = DefenseLawyer()

    # 定义案件信息
    case = CriminalCase(
        case_id="2024-刑初-001",
        case_name="张某盗窃案",
        case_type="盗窃罪",
        charge="盗窃罪",
        incident_date=datetime(2024, 1, 15),
        incident_location="北京市朝阳区某商场",
        case_description="被告人张某在商场盗窃手机一部，价值人民币5000元...",
        proceeding_stage="一审阶段",
        statutory_penalty="三年以下有期徒刑、拘役或者管制",
    )

    # 定义当事人信息
    client = Client(
        name="张某",
        gender="男",
        age=28,
        detention_status="逮捕",
        confession_status="认罪认罚",
        remorse_level="深刻悔罪",
        compensation_made=True,
        victim_forgiveness=True,
    )

    # 定义证据
    evidences = [
        Evidence(
            evidence_id="E001",
            evidence_type="视听资料",
            evidence_name="商场监控视频",
            relevance="直接证据",
            authenticity="真实",
            legality="合法",
            probative_value="强",
        ),
    ]

    # 1. 案件分析
    analysis = await lawyer.analyze_case(case, client, evidences)
    print(f"定罪风险: {analysis.conviction_risk}")
    print(f"量刑风险: {analysis.sentencing_risk}")

    # 2. 制定辩护策略
    strategy = await lawyer.formulate_defense_strategy(case, client, evidences)
    print(f"策略类型: {strategy.strategy_type}")

    # 3. 量刑分析
    sentencing = await lawyer.analyze_sentencing(case, client)
    print(f"缓刑可能性: {sentencing.suspended_sentence_possibility}")

    # 4. 生成辩护词
    doc = await lawyer.generate_defense_statement(case, client, strategy)
    with open("辩护词.md", "w", encoding="utf-8") as f:
        f.write(doc.markdown_content)

asyncio.run(main())
```

### 使用场景

#### 场景1：初次会见后的案情评估

```python
assessment = await lawyer.quick_assessment(case, client)
print(f"定罪风险: {assessment['conviction_risk']}")
print(f"建议策略: {assessment['recommended_strategy']}")
```

#### 场景2：准备庭审材料

```python
package = await lawyer.complete_defense_package(case, client, evidences)
# 包含：案件分析、辩护策略、量刑分析、辩护词、法律研究
```

#### 场景3：证据质证准备

```python
for evidence in prosecution_evidences:
    assessment = await lawyer.assess_evidence(evidence)
    print(f"评分: {assessment.overall_score}/100")
    print(f"质证策略: {assessment.challenge_strategies}")
```

### 测试

```bash
# 运行完整测试套件
python3 test_complete.py

# 运行示例
python3 example.py
```

**测试覆盖**: 7/7 模块全部通过 (100%)

### Python 优势

| 功能 | Python | JavaScript |
|------|--------|------------|
| PDF 处理 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 法律文书生成 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 数据分析 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 法律数据库 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### 免责声明

**Defense Lawyer 能做什么：**
- 提供专业的案件分析和辅助建议
- 协助制定辩护策略和方案
- 生成法律文书草稿
- 提供法律研究和判例参考

**Defense Lawyer 不能做什么：**
- 替代专业律师的法律判断
- 保证任何具体的诉讼结果
- 提供正式的法律意见
- 替代律师的庭审辩护

**重要提示**：本系统仅作为法律工作辅助工具，所有输出内容需要专业律师审核后使用。

### 发展路线图

**v0.2.0**（2026年第二季度）
- 集成真实的法律法规数据库API
- 增加更多罪名支持（50+常见罪名）
- 支持民事案件分析
- LaTeX 格式法律文书输出

**v0.3.0**（2026年第三季度）
- 多地区法律差异支持
- 判例相似度智能分析
- 可视化量刑分析图表
- 团队协作功能

### 许可证

MIT License - 详见 [LICENSE](LICENSE)

### 链接

- **GitHub**: https://github.com/ZhenRobotics/openclaw-defense-lawyer
- **问题反馈**: https://github.com/ZhenRobotics/openclaw-defense-lawyer/issues
- **作者**: Justin Wang (code@zhenrobot.com)

---

**为法律工作者赋能** ⚖️

*让AI成为每位辩护律师的得力助手*
