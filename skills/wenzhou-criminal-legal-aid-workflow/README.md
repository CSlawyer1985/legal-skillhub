# 刑事法律援助全流程 Skill

一个从法律援助指派接收，推进到会见、阅卷、认罪认罚、庭审、结案和回访的刑事法援工作流 Skill。

作者：李鸿鸿｜浙江光正大律师事务所  
发布版本：2026.09.10.1

本次模板资产未改版，模板包 manifest 中的版本号独立于上述 Skill 发布版本。

> 作者与责任边界：本 Skill 由李鸿鸿律师开发，用于作品署名和专业品牌识别，不代表具体案件由作者承办、审核或提供法律意见；不代表浙江光正大律师事务所、温州市法律援助中心、司法行政机关或办案机关的官方系统、正式意见或统一模板。技术安全扫描和自动测试通过，不等于本 Skill、任何 AI 平台或云服务获得律师保密、个人信息、数据安全或国家秘密合规认证。

首次使用请读 [使用指引](docs/使用指引.md)：按需求查找调用示例、准备材料、归档顺序和常见问题。本次在原有全流程基础上小修归档事实填充、缺项提示和 PDF 切割，保留既有模板与办案流程。

## 解决什么问题

刑事法援不是“生成一份漂亮文书”，而是让阶段、事实、模板、会见、阅卷、庭审和归档形成可以复核的材料链。本 Skill 把三个办案阶段和进度事件映射为文书组合，同时设置三道硬门：不得虚构事实、不得混用阶段、不得泄露受援人信息。

## 核心特点

- 真实业务：覆盖侦查、审查起诉、审判及归档/回访。
- 开箱即用：自带经脱敏的温州地区模板包和确定性生成脚本。
- 可推广：办案逻辑与地区模板解耦，其他地区通过 `manifest.json` 替换整套母版。
- 合规安全：模板答复栏清空，私章、律师证号、个人手机号和受援人信息移除；发布前可自动扫描 OOXML、元数据、图片和常见敏感模式。自动审计只是常见泄露模式初筛，不能替代人工逐页检查、模板来源授权审查或真实案件数据合规评估。
- 承办通报据实填写：没有输入记录时留空；提供 case_progress_entries 时仅填入律师核实的条目，不预填承办行为。温州固定表格超行时提前报错，不静默丢弃；当地变量模板以逐行文本填入，须人工复核分页。
- 模板分类校验：原温州模板检查配套锚点；当地新模板可选择 placeholders 变量填充，不要求温州原句。模板更换后须验证并试生成；校验失败产物隔离到「未通过校验-勿用」，成功重跑时提示历史隔离文件。
- 阶段硬门：认罪认罚见证笔录仅在审查起诉、审判阶段生成，侦查阶段触发即报错并提示改记入会见笔录。
- 专业校验：区分法院与公诉机关；识别未羁押口径；罪名法律依据须先核验。
- 阶段化归档：以起诉意见书标识审查起诉阶段起点，以起诉书标识审判阶段起点，并区分程序行为、实际收件和行政结案日期。
- 固定排版：温州模板输出正文仿宋_GB2312 四号、主标题黑体三号、固定行距 28.5 磅，并由生成器写入文档属性。
- 无台账恢复：可只读扫描本地PDF、扫描件、DOCX和文本材料，生成带来源定位与核实状态的候选流程台账。
- 易用性增强：提供环境自检、中文错误建议、无落盘预览、按文书类型差异化的律师复核清单、5分钟上手和FAQ。
- 跨平台分层：明确 Codex、WorkBuddy、Claude Code、Gemini CLI、OpenCode和纯网页平台的运行级别，并提供机器可读兼容性自检。
- 常见罪名库：首批内置23个常见法援罪名的基础法条说明，覆盖侵犯财产、人身权利、公共安全和社会管理秩序；未收录罪名继续执行人工核验门。

## 目录

```text
wenzhou-criminal-legal-aid-workflow/
├── SKILL.md
├── agents/openai.yaml
├── assets/template-packs/wenzhou/
│   ├── manifest.json
│   ├── *.docx / archive_directory.xlsx
│   └── *.docx.b64.txt / *.xlsx.b64.txt
├── references/
│   ├── field_schema.json
│   ├── case_example.json
│   ├── quick-start.md / faq.md
│   ├── material-timeline.md
│   ├── platform-compatibility.md
│   ├── charge-law-library.json / charge-library-guide.md
│   ├── workflow.md
│   ├── template-pack-guide.md
│   └── privacy-and-safety.md
├── scripts/
│   ├── generate_criminal_legal_aid_set.py
│   ├── extract_case_timeline.py / doctor.py
│   ├── check_platform_compatibility.py
│   ├── validate_charge_library.py
│   ├── validate_template_pack.py
│   ├── encode_template_assets.py
│   └── audit_distribution_package.py
├── docs/
│   └── 产品说明.md
└── tests/
```

## 快速验证

需要 Python 3.9+ 和 `python-docx`。

```bash
python3 scripts/doctor.py
python3 scripts/check_platform_compatibility.py --platform codex
python3 scripts/validate_charge_library.py
python3 scripts/validate_template_pack.py assets/template-packs/wenzhou
python3 scripts/audit_distribution_package.py .
python3 -m unittest discover -s tests -v
```

生成前复制 `references/case_example.json` 到 Skill 包以外的案件目录，填写真实案件参数，再运行：

```bash
python3 scripts/generate_criminal_legal_aid_set.py \
  --input /path/to/case.json \
  --output-dir /path/to/output \
  --mode current \
  --template-pack wenzhou
```

其他地区请先阅读 [地区模板包替换指南](references/template-pack-guide.md)，不要直接套用温州格式。

不同 Agent 的安装路径、触发方式和权限门不同。上传或迁移前请阅读 [平台兼容与推荐](references/platform-compatibility.md)，不要只复制 `SKILL.md` 而遗漏脚本、reference和模板资产。

没有现成流程台账时，先运行本地候选时间线提取：

```bash
python3 scripts/extract_case_timeline.py /path/to/materials \
  --output-dir /path/to/workpaper/timeline
```

识别结果默认均为“待律师核实”，确认后才能填入正式案件JSON。完整操作见 [5分钟快速上手](references/quick-start.md)。

常见罪名的内置范围、法源边界和后续扩充方法见 [常见罪名基础说明库](references/charge-library-guide.md)。律师在 `case.json` 中填写的 `charge_legal_basis` 始终优先于内置说明。

模板包同时保留原始 `.docx/.xlsx` 母版及对应的 `.b64.txt` 嵌入副本。若发布平台过滤 Office 二进制文件，生成器会从文本副本自动还原母版；维护者更换模板后应运行 `python3 scripts/encode_template_assets.py assets/template-packs/<pack-id>` 同步更新嵌入副本。

## 发布与共享

可将完整 Skill 目录或其 ZIP 包上传至 SkillHub 等支持 Skill 的平台，入口文件为根目录 `SKILL.md`。发布前依次完成模板校验、自动测试和分发隐私审计；不要上传真实案件 JSON、生成文书、个人签章、律师证号或个人手机号。公开发布不等于授权任何人将真实卷宗上传至云端模型。

## 面向律师使用的价值

| 使用价值 | 对应设计 |
|---|---|
| 法律专业辅助 | 三阶段材料链、归档节点、罪名核验、法院/公诉机关分离、羁押状态判断 |
| 实用性与易用性 | JSON 输入、确定性生成器、阶段自动选件、运行说明和测试 |
| 地区适配能力 | 核心逻辑与地区模板包分离，支持外部 `--template-pack-dir` |
| 合规与安全 | 受援人零数据分发、元数据清理、私章/证号/手机号移除、自动隐私审计 |

## 重要声明

默认母版依据温州地区法律援助中心提供或要求的格式整理，不代表全国统一标准。其他地区使用前必须导入当地模板并复核当地最新办案、归档和系统上传要求。

本项目是律师工作辅助工具，不代替承办律师对事实、证据、法律、期限、保密、个人信息处理和正式文书的判断。作者只审核公开分发包，不审核使用者具体案件；生成结果必须经当前案件承办律师审阅。
