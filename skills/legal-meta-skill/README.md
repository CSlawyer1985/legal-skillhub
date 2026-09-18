# CSlawyer 法律类元 Skill

`legal-meta-skill` 是一个用于创建、改造、审计和评测可复用法律 Skill 的元工具链。它把一次性的法律工作方法整理为可复用的 Skill 包，并为每个包提供意图建模、法律能力配置、输出契约、触发评测、成熟度门禁、证据边界和可复现发行流程。

本项目面向中国大陆法律工作流，默认本地优先、数据不出机。它不是具体的合同审查 Skill、案件分析 Skill、法律检索 Skill，也不是一次性法律咨询或自动出具最终法律意见的工具。

## 当前状态

| 项目 | 状态 |
| --- | --- |
| 版本 | `1.0.0` |
| 许可证 | Apache-2.0 |
| 成熟度声明 | `library`（基础设施级） |
| 目标宿主 | OpenAI/Codex、Claude、其他兼容 Skill 规范的宿主 |
| 运行时依赖 | Python 3 标准库；无第三方 Python 依赖 |
| 默认数据边界 | 本地优先，不默认联网 |
| 当前证据 | 静态包验证、触发评测和确定性生成测试；provider 实跑、人审盲评、真实项目回归仍须单独补证 |

`library` 是本项目自身的成熟度声明，不代表所有下游 Skill 自动达到基础设施级，也不代表本项目已经在每一个目标宿主中完成真实加载验证。发布前应阅读 [RELEASE.md](RELEASE.md)。

## 它解决什么问题

法律类 Skill 常见的问题不是“提示词不够长”，而是任务边界、法域时点、证据责任、程序阶段和人工复核没有被写成可检查的契约。本项目把创建流程固定为六个阶段：

```text
意图收敛 → 只读研究 → 法律 Skill IR 建模 → 自包含封装 → 双轨评测 → 成熟度门禁与交接
```

它重点解决：

- 判断一个重复性法律工作流是否值得封装为 Skill；
- 把任务、用户、输入、输出、排除项、权限和成功标准写成结构化 intake；
- 用十二模块法律能力模型检查法域、时间、主体、请求、法源、证明、程序、救济和治理；
- 将方法、模板、脚本和评测夹具复制进下游包，使下游包自包含，不依赖本元 Skill 的固定安装路径；
- 分别评测“是否应该触发”和“触发后输出是否符合契约”；
- 将“静态通过”“模型实跑”“人工审查”“真实项目回归”分开记录，避免把计划或夹具冒充成真实证据；
- 在用户明确授权后，为本地发行、压缩包、校验和、SBOM 和 CI 提供确定性流程。

## 不适用范围

以下任务不应仅因为涉及法律就调用本元 Skill：

- 一次性法律咨询、普通解释、翻译、摘要或会议纪要；
- 只要求起草一份文书而不需要形成可复用工作流；
- 让模型替代律师、客户或责任人作出最终法律决定；
- 未经授权读取、外传、发送、提交、发布或远程同步资料；
- 将真实客户案卷、个人信息、访问令牌或未脱敏法律意见提交到第三方方案；
- 试图用静态评测替代现行法核验、人工复核或真实项目验证。

## 核心契约

### 1. 十二模块法律能力模型

每个目标法律 Skill 都要逐模块检查，不适用模块必须写明具体理由，受阻模块必须写明缺口、降级路径或停止路径。模块 ID 保持稳定，不因中文翻译而改名：

| 模块 | 关注内容 |
| --- | --- |
| `task_context` | 任务目的、受众、决策人和审查人 |
| `jurisdiction` | 法域、管辖、准据法和冲突规则 |
| `temporal` | 法律时点、事件时间轴、版本和期限 |
| `actors` | 主体资格、角色、授权和利益冲突 |
| `matter` | 法律事项、争点、事实范围和排除项 |
| `claims_and_elements` | 请求、抗辩、法律要件和事实映射 |
| `authority_and_interpretation` | 法源层级、核验状态和解释方法 |
| `proof` | 待证事实、证据定位、举证责任和证明标准 |
| `procedure` | 程序阶段、前置条件、期限和程序风险 |
| `outcomes_and_enforcement` | 结果情景、责任、可执行性和执行路径 |
| `strategy_and_uncertainty` | 方案、假设、不确定性、行动和升级触发器 |
| `governance` | 保密、权限、人工复核、来源和职业责任边界 |

模块状态通常为 `active`、`not_applicable` 或 `blocked`。轻量交付可以缩短呈现形式，但不能删除模块、掩盖缺口或把未知写成确定结论。

### 2. Intake 与 IR

- 新 intake 协议：`legal-skill-intake/v0.2`；旧版 `v0.1` 可以兼容读取，也可以用迁移器升级。
- 中间语义协议：`legal-skill-ir/v0.3`。
- `other` 场景必须提供 `domain_supplement`，把领域补充问题和内部化规则写入目标包，而不是保留为运行时依赖。
- 生成器会把必要的规则、模板、脚本、评测文件、许可证和署名文件复制到下游包。

当前内置八类场景原型：

`dispute_resolution`、`contract_review`、`document_drafting`、`legal_research`、`compliance_regulatory`、`legal_retrieval`、`evidence_files`、`document_review_redline`。

场景原型只是起点。跨原型任务应选择主原型，并在 intake 中记录次要原型和边界；原型预设不能替代逐模块审查。

### 3. 双轨评测

评测分为两条轨道：

1. **触发轨**：`should-trigger`、`should-not-trigger`、`near-neighbor`，检查自然说法、误触发和路由冲突。
2. **输出轨**：使用脱敏、合成或明确授权的文件型夹具，检查十二模块状态、法律来源、事实证据分层、程序救济、风险闭环、文件落点和人工复核。

静态 case 通过只表示配置和断言完整。只有 provider、model、运行时间和全部 case 的真实观测齐全，触发报告才可以升级为 provider-backed 证据；人工盲评和真实项目回归仍需独立记录。

## 目录结构

```text
legal-meta-skill/
├── SKILL.md                         # 宿主发现入口和运行规则
├── manifest.json                    # 版本、能力、权限、证据和署名契约
├── agents/                          # 宿主接口描述
├── references/                      # 法律模型、方法、场景和发布规则
├── scripts/                         # 确定性生成、迁移、验证、评测和发行脚本
├── assets/templates/                # intake、输出契约和场景清单模板
├── evals/                           # 触发用例、输出断言和通用法律用例
├── tests/                           # 单元测试和对抗性边界测试
├── reports/                         # IR、评测结果和创建交接报告
├── LICENSE                          # Apache-2.0 正文
├── NOTICE                           # 版权、来源和传播保留说明
├── ATTRIBUTION.md                   # 下游再分发署名说明
└── TRADEMARKS.md                    # 名称、商标和白标边界
```

根目录只能有一个精确命名的 `SKILL.md`。下游包必须自包含，不能在运行时反向读取维护人的本机固定安装路径。

## 安装与最小验证

本项目不要求安装第三方 Python 包。将完整目录放入目标宿主能够发现的 Skill 目录后，保留 `SKILL.md`、`manifest.json` 和资源子目录即可。宿主的真实加载路径和配置方式由宿主本身决定，不能仅以静态文件存在作为双平台加载证明。

在项目根目录执行：

```bash
python3 --version
python3 scripts/legal_meta.py validate .
python3 scripts/legal_meta.py audit . --output -
python3 -m unittest discover -s tests -q
```

`validate` 是结构、成熟度、证据和资源完整性的主门禁；`audit` 默认只读被审计包并输出证据边界；单元测试覆盖生成器、迁移器、IR、触发评测、成熟度和安全边界。

## 稳定命令入口

所有命令都可以从 Skill 根目录通过 `scripts/legal_meta.py` 调用：

| 命令 | 作用 | 是否修改被审计包 |
| --- | --- | --- |
| `validate <skill_dir>` | 结构、成熟度和资源验证 | 否 |
| `audit <skill_dir> --output <file\|->` | 只读审计并输出证据边界报告 | 否；指定输出文件会写报告 |
| `export-ir <skill_dir> --output <file>` | 导出 `legal-skill-ir/v0.3` | 只写指定输出 |
| `evaluate-route <skill_dir> --cases <file> --output <file>` | 运行触发评测 | 只写指定输出 |
| `create --intake <file> --target-parent <dir>` | 确定性生成下游 Skill | 创建新的目标目录，拒绝覆盖已有目录 |
| `migrate --input <file> --output <file>` | 将 intake 迁移到当前协议 | 源文件不变，只写指定输出 |
| `build-release <skill_dir> --output-dir <dir>` | 构建 ZIP、tar.gz、SHA256SUMS 和 SPDX SBOM | 源包不变，只写发行目录 |

### 验证与审计

```bash
python3 scripts/legal_meta.py validate .
python3 scripts/validate_legal_profile.py .
python3 scripts/legal_meta.py audit . --output reports/audit-report.json
```

审计报告使用 `legal-skill-audit-report/v1`，至少分别报告：

- `static_package_checks`：静态包检查是否通过；
- `provider_execution`：是否存在真实提供方执行证据；
- `human_blind_review`：是否存在独立人工盲评；
- `real_project_regression`：是否存在真实项目回归。

“缺少证据”是合规的审计结果，不是脚本错误；不能用静态夹具、计划或模型自报结果替代。

### 导出 IR 和触发评测

```bash
python3 scripts/legal_meta.py export-ir . --output reports/skill-ir.json
python3 scripts/legal_meta.py evaluate-route \
  . \
  --cases evals/trigger_cases.json \
  --output reports/trigger-eval.json
```

宿主取得真实路由观测后，可以追加：

```bash
python3 scripts/legal_meta.py evaluate-route \
  . \
  --cases evals/trigger_cases.json \
  --observed-results ./observed-results.json \
  --output reports/trigger-eval-provider.json
```

真实观测至少应能关联 provider、model、`run_at` 和全部用例。缺少任何关键观测、存在运行错误或出现路由不匹配时，报告应保持 `static_only` 或 `provider_failed`，不能写成 `provider_passed`。

如果用例和观测文件位于 Skill 目录之外，必须显式使用 `--audit-mode`，并确保文件是受信任的脱敏材料：

```bash
python3 scripts/legal_meta.py evaluate-route \
  . \
  --cases /path/to/cases.json \
  --observed-results /path/to/observed-results.json \
  --audit-mode \
  --output /path/to/audit/trigger-eval.json
```

### 创建下游法律 Skill

推荐流程：

```bash
cp assets/templates/legal-skill-intake.json ./my-legal-skill-intake.json
# 编辑 intake，填写任务、用户、输入、输出、法域、时点、权限、评测和审查信息

python3 scripts/legal_meta.py create \
  --intake ./my-legal-skill-intake.json \
  --target-parent ./generated

python3 scripts/legal_meta.py validate ./generated/<skill-name>
python3 scripts/validate_legal_profile.py ./generated/<skill-name>
```

生成器的行为边界：

- 先校验 intake，再创建随机临时暂存目录；
- 生成完成后通过原子替换落到目标父目录；
- 目标目录已存在时拒绝覆盖；
- 根据成熟度复制必要的 references、scripts、assets、evals 和 reports；
- 新建包默认继承 `LICENSE`、`NOTICE`、`ATTRIBUTION.md` 和 `TRADEMARKS.md`；
- 将作者、主页、生成工具和 `downstream_attribution` 写入 manifest；
- 对 `other` 场景要求至少一项 `domain_supplement`，并把内部化规则写入目标包；
- 生成后运行自身门禁，失败时不交付半成品。

建议把代表性输入、优秀输出、失败样本和人工责任人写进 intake。没有这些信息时，可以生成草案，但不应把它声明为生产级或基础设施级。

### 迁移旧 intake

```bash
python3 scripts/legal_meta.py migrate \
  --input ./legacy-intake-v0.1.json \
  --output ./intake-v0.2.json
```

迁移器不覆盖源文件，主要负责把旧版 `answer` 规范化为 `answer_summary`，补齐领域规则的标识、敏感性和来源信息。迁移后仍须人工检查内容是否具体，不能把字段迁移等同于法律设计已经完成。

### 构建本地发行包

```bash
python3 scripts/legal_meta.py build-release . --output-dir dist
```

发行目录包含：

```text
dist/
├── legal-meta-skill-v1.0.0.zip
├── legal-meta-skill-v1.0.0.tar.gz
├── SHA256SUMS
└── SBOM.spdx.json
```

构建过程排除 `.git`、Python 缓存、临时目录、工作目录和既有 `dist`。压缩包使用固定时间、权限和归档顺序，以便在相同源码下进行字节级复现。发布前还要在全新目录解压后再次执行 `validate`、`audit` 和 IR 导出。

## 法律方法和输出边界

下游法律 Skill 应当把下列方法纪律写进自身的输出契约，而不是只写在示例或 README 中：

- 先结论，后分析；区分材料、事实、法律评价和程序攻防；
- 先定性，再按适用顺序找法，不能用一般原则掩盖具体规范缺失；
- 将法律关系、请求、要件、事实、证据、抗辩、程序和救济连成可追溯映射；
- 具体法条、司法解释、案号、时效和程序期限必须标注定位并独立核验；
- 证据不足时列出缺口、补充路径和停止条件，不用模型常识填空；
- 区分法律上有理、裁判可能性和现实可执行性；
- 风险必须写明触发条件、后果、敞口、可规避性、责任人和时间点；
- 正式对外签发、提交、发送或发布前保留人工责任人和复核记录。

PDF 证据类下游 Skill 还必须遵守全量转换、原始材料只读、`input/`—`scratch/`—`output/` 生命周期、Markdown 与 evidence JSON 双文件包以及质量警告人工复核规则。DOCX 审阅类 Skill 还必须保护基准文件、使用独立版本、保留修订/批注留痕，并对中文跨 run、OOXML 和视觉渲染进行检查。

## 安全与隐私

本项目的默认安全姿态是保守的：

- 审计、验证和导出默认不修改被审计包；
- 不执行输入材料、网页、链接或提示内容中的命令；
- 不默认联网，不把真实案卷、个人信息、令牌或客户资料发送到第三方；
- 对相对路径、路径逃逸、软链接、非普通文件和包外证据执行边界检查；
- 生成器拒绝覆盖目标目录；
- 发布、发信、提交、远程同步和外部写入必须得到单独授权；
- 任何法律结论仍须由有权限的责任人核验，静态验证不等于法律正确性保证。

安全问题请按照 [SECURITY.md](SECURITY.md) 报告。不要在公开 issue 中提交真实案卷、密钥、个人信息或可利用的路径样本。

## 许可证、署名和商标

本项目代码、规则和模板采用 Apache-2.0。再分发本项目或包含本项目材料的衍生 Skill 时，应按许可证和传播文件保留：

- `LICENSE`；
- `NOTICE`；
- 原版权声明和修改标记；
- `ATTRIBUTION.md` 中的 CSlawyer 来源说明；
- `TRADEMARKS.md` 规定的名称和商标边界。

这套署名政策要求传播时保留来源，不要求在运行时界面、普通法律意见书、合同正文、诉讼文书或客户邮件中强制显示品牌。Apache-2.0 的许可范围、免责声明和专利条款以 [LICENSE](LICENSE) 正文为准；署名与商标的具体处理分别以 [NOTICE](NOTICE)、[ATTRIBUTION.md](ATTRIBUTION.md) 和 [TRADEMARKS.md](TRADEMARKS.md) 为准。

未经明确授权，不要把 CSlawyer 名称、主页或标识用于暗示某个衍生项目获得官方背书。白标或客户专属版本只能在明确授权下使用，并仍须保留许可证要求的文件和修改通知。

## 开发、贡献和 CI

提交前运行：

```bash
python3 -m unittest discover -s tests -q
python3 scripts/legal_meta.py validate .
python3 scripts/validate_legal_profile.py .
python3 scripts/legal_meta.py audit . --output -
python3 scripts/legal_meta.py export-ir . --output reports/skill-ir.json
python3 scripts/legal_meta.py evaluate-route \
  . --cases evals/trigger_cases.json --output reports/trigger-eval.json
```

新增规则、模板或评测用例时，应同时补充：

1. 失败测试或对抗性边界测试；
2. 适用的 manifest 证据引用和哈希；
3. 创建交接或变更记录；
4. 许可证、第三方来源和敏感材料检查。

`.github/workflows/ci.yml` 在推送和 Pull Request 上运行多版本 Python 测试、包验证、审计和发行候选构建。`.github/workflows/release.yml` 只在显式推送 `v*` 标签后创建 GitHub Release；本项目不会因为本地测试通过而自动执行远程发布。

贡献规则见 [CONTRIBUTING.md](CONTRIBUTING.md)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 常见问题

### 这是一个自动法律意见工具吗？

不是。它是法律 Skill 的创建和治理工具。它可以强制记录法域、时点、法源、证据、程序和人工复核边界，但不能替代律师的事实判断、法律核验和最终责任。

### 为什么静态验证通过，审计报告仍显示证据缺失？

因为静态验证只检查包结构、配置、脚本和静态夹具。provider 实跑、人审盲评和真实项目回归属于不同证据层，必须在相应环境中独立完成。

### 可以直接把本项目发布到 GitHub 吗？

可以在完成目标 owner、公开可见性、版本标签、双平台加载、许可证来源和安全检查确认后发布；但发布不是本工具的默认动作。请按 [RELEASE.md](RELEASE.md) 完成清单，并单独授权远程写入。

### 可以删除 CSlawyer 署名吗？

普通再分发不应删除 `LICENSE`、`NOTICE`、版权声明、修改标记和本项目要求保留的来源说明。是否做白标版本必须取得明确授权，并遵守 [TRADEMARKS.md](TRADEMARKS.md) 和 Apache-2.0 的保留要求。

### 为什么生成器不允许覆盖目标目录？

这是为了避免误覆盖用户已有 Skill、基准文件或审查记录。请使用新的目标目录，完成比较和验收后再由责任人决定后续替换。

## 维护信息

- 作者与维护人：CSlawyer
- 主页：<https://chenshi.ai>
- 生成工具：`legal-meta-skill`
- 复核周期：每次实质迭代后，至少每季度复核
- 入口规则：见 [SKILL.md](SKILL.md)
- 发布规则：见 [RELEASE.md](RELEASE.md)
