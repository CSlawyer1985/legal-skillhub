---
name: bidding-compliance-engine
version: "2.0.0"
description: 招标文件合规审查引擎。当用户上传招标文件并要求审查、合规检查、风险分析，或说"审查招标文件"、"检查合规性"、"合规审查"、"招标文件有没有问题"时触发。不适用于招标文件起草、翻译或一般性问答。基于11步协作链路，实现文本提取→结构化解析→公平竞争审查→废标条款审查→资格条件审查→技术参数合规→招标程序与评标合规→合同条款风险→合同与程序合规→反垄断与专项审查→报告生成的全流程自动化审查。审查规则依据《招标文件公平竞争合法合规性审查表》v0520版编制，覆盖13大类45+审查事项，共95条规则。
author: 恭喜  # 招标文件合规审查专家
---

# 招标文件公平竞争合法合规性审查引擎

## 概述

基于ima Skills架构的招标文件合规审查系统，审查规则依据《招标文件公平竞争合法合规性审查表（校对版0520）》编制，将业务规则落盘为8个YAML规则文件（共95条规则），通过Python规则引擎执行匹配，实现审查流程可审计、可复现、可版本管理。

### 审查依据
- 国务院令第783号《公平竞争审查条例》
- 《公平竞争审查条例实施办法》（99号令）
- 《招标投标领域公平竞争审查规则》（2024年第16号令）
- 发改法规〔2025〕1358号《关于印发《招标人主体责任履行指引》的通知》
- 福建省人民代表大会常务委员会公告〔十四届〕第三十一号
- 闽发改法规〔2023〕53号《关于印发《加强工程项目招标投标领域监管工作方案》的通知》
- 《招标投标法》及实施条例

## 核心能力

### 能力1：文本提取与结构化
- 支持PDF（含OCR）、DOCX、TXT格式
- 启发式章节识别，输出结构化JSON

### 能力2：八维合规扫描（与审查表13大类对应）

| 扫描维度 | 规则文件 | 规则数 | 对应审查表类别 |
|----------|---------|--------|---------------|
| 公平竞争审查 | fair_competition_rules.yml | 28 | 一至七类（事项1.1-7.5） |
| 废标条款审查 | disqualify_rules.yml | 8 | 一/二类+废标条款 |
| 资格条件审查 | qualification_rules.yml | 8 | 三类（事项3.1-3.4） |
| 技术参数合规 | technical_rules.yml | 8 | 四类（事项4.1-4.4） |
| 招标程序与评标合规 | bidding_procedure_rules.yml | 16 | 八/九类（事项8.1-9.8） |
| 合同条款风险 | contract_rules.yml | 7 | 十类部分（合同风险） |
| 合同与程序合规 | contract_compliance_rules.yml | 11 | 十/十一类（事项10.1-11.5） |
| 反垄断与专项审查 | antitrust_rules.yml | 9 | 十二/十三类（事项12.1-13.5） |

### 公平竞争审查（28条规则）覆盖范围
- **一、所有制与组织形式限制**（3条）：所有制形式限制、组织形式限制、隶属关系限制
- **二、地域与市场准入限制**（4条）：本地分支机构、本地纳税/社保、本地业绩、本地准入障碍
- **三、资质资格与业绩条件**（4条）：资质超标、业绩超标、奖项偏向、人员过度
- **四、技术标准与品牌指定**（4条）：技术参数指向、标准唯一性、检测认证、样品偏向
- **五、评分标准与权重设置**（4条）：评分不量化、权重不合理、价格评分、评审公正性
- **六、其他排斥限制情形**（4条）：所有制挂钩、强制进场、原件提交、强制到场
- **七、保证金收取规范性**（5条）：投标保证金、无依据保证金、退还条件、履约保证金、工程质量保证金

### 能力3：审查报告生成
- 自动判定审查结论（通过/有条件通过/不通过）
- 按8个审查维度和严重等级统计
- 每条问题含条款定位、证据、整改建议、法规依据、审查事项编号

## 执行工作流

当用户上传招标文件并要求合规审查时，按以下步骤执行：

### Phase 1：文件接入
1. 接收用户上传的招标文件，确定文件路径
2. 生成唯一项目ID（如 `PRJ-YYYYMMDD-NNN`）
3. 创建项目目录结构：
   ```
   {output_root}/{project_id}/
   ├── artifacts/    # 中间产物（raw_text.txt, tender.json, issue_list.json）
   ├── audit/        # 审计日志
   └── output/       # 最终报告
   ```
4. 调用文本提取脚本：
   ```bash
   python3 {SKILL_DIR}/scripts/extract_text.py \
     --file_path "{文件路径}" \
     --project_id {项目ID} \
     --enable_ocr true \
     --output_dir {项目目录}/artifacts
   ```
5. 确认 `extraction_meta.json` 中 `status` 为 `success` 后进入 Phase 2

### Phase 2：结构化解析
1. 调用结构化解析脚本：
   ```bash
   python3 {SKILL_DIR}/scripts/parse_structure.py \
     --raw_text_path {项目目录}/artifacts/raw_text.txt \
     --project_id {项目ID} \
     --output_dir {项目目录}/artifacts
   ```
2. 确认 `tender.json` 生成后初始化空的问题清单：
   ```bash
   echo '{"project_id":"{项目ID}","issues":[],"issue_count":0}' > {项目目录}/artifacts/issue_list.json
   ```
3. 进入 Phase 3

### Phase 3：八维合规扫描（依次执行，问题追加不覆盖）

**Step 3a：公平竞争审查（覆盖审查表第一部分：事项1.1-7.5）**
```bash
python3 {SKILL_DIR}/scripts/run_rules_engine.py \
  --tender_json {项目目录}/artifacts/tender.json \
  --rules {SKILL_DIR}/references/rules/fair_competition_rules.yml \
  --issue_list {项目目录}/artifacts/issue_list.json \
  --output {项目目录}/artifacts/issue_list.json \
  --log {项目目录}/audit/fair_competition.log \
  --scan_type fair_competition \
  --project_id {项目ID}
```

**Step 3b：废标条款审查**
```bash
python3 {SKILL_DIR}/scripts/run_rules_engine.py \
  --tender_json {项目目录}/artifacts/tender.json \
  --rules {SKILL_DIR}/references/rules/disqualify_rules.yml \
  --issue_list {项目目录}/artifacts/issue_list.json \
  --output {项目目录}/artifacts/issue_list.json \
  --log {项目目录}/audit/disqualify_check.log \
  --scan_type disqualify_check \
  --project_id {项目ID}
```

**Step 3c：资格条件审查**
```bash
python3 {SKILL_DIR}/scripts/run_rules_engine.py \
  --tender_json {项目目录}/artifacts/tender.json \
  --rules {SKILL_DIR}/references/rules/qualification_rules.yml \
  --issue_list {项目目录}/artifacts/issue_list.json \
  --output {项目目录}/artifacts/issue_list.json \
  --log {项目目录}/audit/qualification_check.log \
  --scan_type qualification_check \
  --project_id {项目ID}
```

**Step 3d：技术参数合规**
```bash
python3 {SKILL_DIR}/scripts/run_rules_engine.py \
  --tender_json {项目目录}/artifacts/tender.json \
  --rules {SKILL_DIR}/references/rules/technical_rules.yml \
  --issue_list {项目目录}/artifacts/issue_list.json \
  --output {项目目录}/artifacts/issue_list.json \
  --log {项目目录}/audit/technical_spec.log \
  --scan_type technical_spec_match \
  --project_id {项目ID}
```

**Step 3e：招标程序与评标合规（覆盖审查表第八/九类：事项8.1-9.8）**
```bash
python3 {SKILL_DIR}/scripts/run_rules_engine.py \
  --tender_json {项目目录}/artifacts/tender.json \
  --rules {SKILL_DIR}/references/rules/bidding_procedure_rules.yml \
  --issue_list {项目目录}/artifacts/issue_list.json \
  --output {项目目录}/artifacts/issue_list.json \
  --log {项目目录}/audit/bidding_procedure.log \
  --scan_type bidding_procedure \
  --project_id {项目ID}
```

**Step 3f：合同条款风险**
```bash
python3 {SKILL_DIR}/scripts/run_rules_engine.py \
  --tender_json {项目目录}/artifacts/tender.json \
  --rules {SKILL_DIR}/references/rules/contract_rules.yml \
  --issue_list {项目目录}/artifacts/issue_list.json \
  --output {项目目录}/artifacts/issue_list.json \
  --log {项目目录}/audit/contract_terms.log \
  --scan_type contract_terms_risk \
  --project_id {项目ID}
```

**Step 3g：合同与程序合规（覆盖审查表第十/十一类：事项10.1-11.5）**
```bash
python3 {SKILL_DIR}/scripts/run_rules_engine.py \
  --tender_json {项目目录}/artifacts/tender.json \
  --rules {SKILL_DIR}/references/rules/contract_compliance_rules.yml \
  --issue_list {项目目录}/artifacts/issue_list.json \
  --output {项目目录}/artifacts/issue_list.json \
  --log {项目目录}/audit/contract_compliance.log \
  --scan_type contract_compliance \
  --project_id {项目ID}
```

**Step 3h：反垄断与专项审查（覆盖审查表第十二/十三类：事项12.1-13.5）**
```bash
python3 {SKILL_DIR}/scripts/run_rules_engine.py \
  --tender_json {项目目录}/artifacts/tender.json \
  --rules {SKILL_DIR}/references/rules/antitrust_rules.yml \
  --issue_list {项目目录}/artifacts/issue_list.json \
  --output {项目目录}/artifacts/issue_list.json \
  --log {项目目录}/audit/antitrust_special.log \
  --scan_type antitrust_special \
  --project_id {项目ID}
```

### Phase 4：报告生成
1. 调用报告生成脚本：
   ```bash
   python3 {SKILL_DIR}/scripts/render_report.py \
     --project_id {项目ID} \
     --tender_json {项目目录}/artifacts/tender.json \
     --issue_list {项目目录}/artifacts/issue_list.json \
     --template {SKILL_DIR}/assets/compliance_report.md \
     --output {项目目录}/output/compliance_report.md
   ```
2. 读取 `compliance_report_meta.json` 获取审查结论

### Phase 5：结果交付
1. 向用户展示审查结论摘要（结论 + 问题统计）
2. 列出高风险问题清单
3. 将完整报告文件提供给用户下载

## 快捷方式

端到端一键执行（适用于所有步骤）：
```bash
python3 {SKILL_DIR}/scripts/run_compliance_check.py \
  --file_path "{文件路径}" \
  --project_id {项目ID} \
  --output_root ./output
```

## 操作原则

1. **链路不可跳步**：必须从 Phase 1 开始，依次执行到 Phase 4
2. **失败即停**：任何 Phase 执行失败，立即向用户报告错误，不继续下一步
3. **问题追加不覆盖**：Phase 3 的 8 个扫描步骤是追加关系，每个步骤的输出包含前面所有步骤的结果
4. **审计日志必须记录**：每个步骤的 `--log` 参数必须指向项目审计目录
5. **项目ID唯一**：每次审查使用唯一的项目ID，避免结果混淆
6. **审查表编号可追溯**：每条规则均标注 `check_item` 字段，对应审查表事项编号

## 技术依赖

- Python 3.12+
- PyYAML（规则文件解析）
- Jinja2（报告模板渲染）
- pdfplumber（PDF文本提取，可选）
- python-docx（DOCX文本提取，可选）
- pytesseract + Tesseract（OCR，可选）

## 规则库概览

| 规则文件 | 路径 | 规则数 | 审查维度 | 对应审查表 |
|---------|------|--------|---------|-----------|
| 公平竞争审查规则 | references/rules/fair_competition_rules.yml | 28 | 公平竞争 | 第一部分 事项1.1-7.5 |
| 废标条款审查规则 | references/rules/disqualify_rules.yml | 8 | 实质性条款 | 第一/二部分交叉 |
| 资格条件审查规则 | references/rules/qualification_rules.yml | 8 | 投标人资格 | 第三类 事项3.1-3.4 |
| 技术参数合规规则 | references/rules/technical_rules.yml | 8 | 技术规格 | 第四类 事项4.1-4.4 |
| 招标程序与评标规则 | references/rules/bidding_procedure_rules.yml | 16 | 招标/评标程序 | 第八/九类 事项8.1-9.8 |
| 合同条款风险规则 | references/rules/contract_rules.yml | 7 | 合同风险 | 第十类部分 |
| 合同与程序合规规则 | references/rules/contract_compliance_rules.yml | 11 | 合同/信息合规 | 第十/十一类 事项10.1-11.5 |
| 反垄断与专项规则 | references/rules/antitrust_rules.yml | 9 | 反垄断/专项 | 第十二/十三类 事项12.1-13.5 |
| **合计** | | **95** | | **覆盖13大类45+事项** |

## 文件结构

```
bidding-compliance-engine/
├── SKILL.md                           # 本文件 - Skill定义与工作流
├── scripts/
│   ├── extract_text.py                # 文本提取（PDF/DOCX/TXT）
│   ├── parse_structure.py             # 章节结构化解析
│   ├── run_rules_engine.py            # 通用规则引擎
│   ├── render_report.py               # 审查报告生成
│   └── run_compliance_check.py        # 端到端一键执行入口
├── references/
│   └── rules/
│       ├── fair_competition_rules.yml       # 公平竞争审查（28条）
│       ├── disqualify_rules.yml             # 废标条款审查（8条）
│       ├── qualification_rules.yml          # 资格条件审查（8条）
│       ├── technical_rules.yml              # 技术参数合规（8条）
│       ├── bidding_procedure_rules.yml      # 招标程序与评标合规（16条）
│       ├── contract_rules.yml               # 合同条款风险（7条）
│       ├── contract_compliance_rules.yml    # 合同与程序合规（11条）
│       └── antitrust_rules.yml              # 反垄断与专项审查（9条）
└── assets/
    └── compliance_report.md        # 审查报告Jinja2模板
```
