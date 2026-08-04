# baozheng-skills — 一站式法律服务平台

法律咨询 + 要素式/通用起诉状起草 + 刑事专项材料辅助 + 深度法条分析与法规检索。通过 22类法律领域覆盖矩阵明确每类问题的当前承接等级、主路由和模板升级缺口。

## 功能特性

| 能力 | 说明 | 规模 |
|:---|:---|:---|
| 法律咨询 | 模块A 四步深度分析（事实梳理→法律定性→法条检索→风险提示） | 22 类领域 |
| 起诉状起草 | 模块B 要素式/通用起诉状，支持 DOCX 生成 | 35 个模板（34 专属 + 1 通用） |
| 法条分析 | 模块C 四步深度分析 + 六步法规检索增强工作流 | flk.npc.gov.cn API 优先 + AI 知识库降级 |
| 刑事辅助 | 模块D 控告/取保/辩护/附带民事/羁押沟通 | 5 类专项材料 |
| 意图收敛 | 渐进式 3 轮状态机 + 直跳规则 + 混合意图自动拆解 | 6 大领域集群 |
| 质量门禁 | Logic Doctor 五维自检 + 10 类异常容错 + 诉讼时效追踪 | 含连续失败熔断 |

## 文件结构

```
baozheng-skills/
├── SKILL.md              # 运行入口（路由表 + 边界说明，~743 Token）
├── README.md             # 本文件
├── faq.md                # 常见问题解答（27 题）
├── requirements.txt      # Python 外部依赖（CodeBuddy 自动检测安装）
├── scripts/
│   ├── flk_npc_client.py              # flk.npc.gov.cn API 客户端（6端点全覆盖）
│   ├── law_search_engine.py           # 双通道法条检索引擎（API优先+AI降级+熔断+验证）
│   ├── generate_complaint_docx.py     # 起诉状 DOCX 生成脚本
│   ├── limitation_calculator.py       # 诉讼时效计算器（17条规则+四级预警）
│   ├── damage_calculator.py           # 损害赔偿计算器（5类赔偿+法条引用）
│   ├── validate_examples.py           # 样例质量门禁脚本
│   └── validate_category_coverage.py  # 类别覆盖矩阵门禁脚本
├── tests/
│   └── test_generate_complaint_docx.py
├── examples/
│   └── *-data.json                   # 40 个填充样例（35 个起诉状模板 + 5 个刑事材料）
├── references/
│   ├── module-a-consultation.md      # 模块A：法律咨询（4步深度分析流程）
│   ├── module-b-complaint.md         # 模块B：要素式起诉状（35模板，含民事/行政）
│   ├── module-c-analysis.md          # 模块C：法条分析+法规检索（C0-C3）
│   ├── module-d-criminal.md          # 模块D：刑事专项材料辅助（5类材料）
│   ├── shared-category-coverage.md   # 公共：22类法律领域覆盖矩阵
│   ├── shared-statute-engine.md      # 公共：法条检索策略（flk.npc.gov.cn API 优先 + AI 知识库降级）
│   ├── shared-error-handling.md      # 公共：10类异常容错处理（含连续失败熔断）
│   ├── shared-limitation-periods.md  # 公共：诉讼时效速查
│   ├── shared-disclaimer.md          # 公共：全局免责声明
│   ├── shared-activation-rules.md    # 强制激活规则
│   ├── shared-intent-convergence.md  # 公共：渐进式意图收敛协议（3轮状态机）
│   ├── shared-task-decomposition.md  # 公共：自动任务拆解（混合意图依赖排序）
│   └── case-00-general-civil.md ~ case-34-consumer-rights.md
└── assets/
    ├── template-00-general-civil.md ~ template-34-consumer-rights.md
    ├── criminal-accusation-template.md
    ├── bail-application-template.md
    ├── criminal-defense-opinion-template.md
    ├── criminal-incidental-civil-template.md
    └── detention-family-communication-template.md
```

## 快速开始

### 0. 安装依赖

```bash
pip install -r requirements.txt
```

依赖清单：`requests`（flk API 客户端）、`python-docx`（DOCX 生成，缺失时自动降级为纯标准库输出）。

### 1. 起草起诉状

```bash
# 列出全部可用案由
python scripts/generate_complaint_docx.py --list

# 用示例数据填充并生成 DOCX（输出到当前目录或指定路径）
python scripts/generate_complaint_docx.py --case 01 --data examples/private-lending-data.json --output private-lending-filled.docx
```

### 2. 法律咨询

向 AI 描述案情即可触发模块A，例如：

> "我借给朋友 10 万块钱，过了 2 年还没还，能起诉吗？"

AI 会按四步流程分析：事实梳理 → 法律定性 → 法条检索（AI训练知识，建议人工核验）→ 风险提示。

### 3. 法条查询

> "分析民法典第577条" → 触发模块C C1 四步深度分析
> "检索劳动合同法涉及的法规" → 触发模块C C2 六步法规检索

### 4. 刑事辅助

> "朋友被刑事拘留了，家属怎么沟通？" → 触发模块D D8 羁押家属沟通提纲

## 架构概览

```
用户输入
  │
  ├─ 意图清晰（领域+行为词齐全）→ 直跳目标模块
  │
  ├─ 意图模糊 → shared-intent-convergence.md（3轮收敛状态机）
  │              S_R1(领域) → S_R2(意图) → S_R3(细节) → S_DISPATCHED
  │
  ├─ 混合意图 → shared-task-decomposition.md（自动拆解+依赖排序）
  │
  └─ 3轮未收敛 → 兜底 module-a A2 通用咨询

四大模块：
  module-a 法律咨询   module-b 起诉状起草
  module-c 法条分析   module-d 刑事辅助

公共复用：
  shared-statute-engine     法条检索（flk.npc.gov.cn API 优先 + AI 知识库降级）
  shared-error-handling     10类异常容错（含熔断）
  shared-limitation-periods 诉讼时效速查
  shared-disclaimer         全局免责声明
  shared-activation-rules   强制激活规则
  shared-category-coverage  22类覆盖矩阵
```

## DOCX 生成验证

```bash
python scripts/generate_complaint_docx.py --list
python scripts/generate_complaint_docx.py --case 01 --dry-run
python scripts/generate_complaint_docx.py --case 01 --data examples/private-lending-data.json --dry-run
python scripts/generate_complaint_docx.py --case 01 --output private-lending.docx
python scripts/generate_complaint_docx.py --case 01 --data examples/private-lending-data.json --output private-lending-filled.docx
python scripts/validate_examples.py
python scripts/validate_category_coverage.py
python -m unittest discover -s tests
```

说明：脚本优先使用 `python-docx`；环境未安装该包时，会自动使用 Python 标准库生成基础 `.docx` 文件。CodeBuddy 加载技能时将自动检测 `requirements.txt` 并提示安装缺失依赖。

## 验证与测试

### 验证脚本

| 脚本 | 检查内容 | 通过标准 |
|:---|:---|:---|
| `scripts/validate_examples.py` | 40 个 examples 字段完整性 + 案由专属质量规则 | 全部 OK，无 missing |
| `scripts/validate_category_coverage.py` | 22 类法律领域覆盖 + 路由完整性 + 版本标记 | 全部 OK，无 missing |

### 单元测试

```bash
python -m unittest tests.test_generate_complaint_docx -v
```

10 个测试用例覆盖：
- case↔template↔example 三元组自动发现（民事≥34 + 刑事≥5）
- 模板解析、JSON 填充、DOCX 生成全链路
- 全部 35 个民事 case + 5 个刑事材料逐一验证
- 样例质量门禁 + 类别覆盖门禁
- 悬空引用检测（旧路径不残留）

> 测试映射自动推导：`setUpClass` 基于 `discover_cases` + `{slug}-data.json` 命名约定，新增案由零维护成本。

## 常见问题

详见 [faq.md](faq.md)，按六大类组织 27 个高频问题：

1. 技能功能（Q1-Q4）
2. 起诉状相关（Q5-Q13）
3. 法条查询相关（Q14-Q16）
4. 刑事案件相关（Q17-Q18）
5. 意图收敛与任务拆解（Q19-Q22）
6. 技术使用（Q23-Q27）

## 版本记录

| 版本 | 日期 | 变更 |
|:---|:---|:---|
| 1.0.1 | 2026-07-03 | **文档补全**：新增 `faq.md`（27 题）；README 补全功能特性、快速开始、架构概览、验证与测试、常见问题章节；测试文件重构为自动推导映射（删除 45 行手工字典，`setUpClass` 基于 `discover_cases` + `{slug}-data.json` 自动推导，新增案由零维护）。当前覆盖 22 类法律领域、35 个起诉状模板（34 专属 + 1 通用）、5 类刑事专项材料、40 个填充样例。 |
