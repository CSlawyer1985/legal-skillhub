---
name: wenzhou-criminal-legal-aid-workflow
description: 办理中国大陆刑事法律援助案件的全流程文书与归档辅助，覆盖指派接收、分阶段会见、阅卷、认罪认罚、庭审、结案和回访。默认模板适配温州地区；其他地区须先导入当地模板包。用于真实刑事法援工作，不用于普通收费委托案件。
---

# 刑事法律援助全流程 Skill

作者：李鸿鸿，浙江光正大律师事务所。

本 Skill 由李鸿鸿律师开发。作者署名用于作品归属和专业品牌识别，不代表具体案件由作者承办、审核或提供法律意见；使用者必须显式填写当前案件的承办律师和律师事务所；记录律师应据实填写，未填时现有生成器沿用该案承办律师，须复核，不以作者身份代填。

本 Skill 将刑事法援案件从接到指派到结案归档拆成可核验的材料链。默认 `wenzhou` 模板包中的会见笔录、阅卷笔录、庭审笔录等格式，依据温州地区法律援助中心提供或要求的模板整理；不得把温州格式宣称为全国统一格式。

## 不可突破的边界

- 先确认案件阶段、办案进度和羁押状态，再决定材料组合；不得由罪名推断阶段。
- 认罪认罚见证笔录只在审查起诉、审判阶段生成；侦查阶段触发「认罪认罚」时生成器直接报错，权利告知情况应记入该阶段会见笔录。
- 案件承办通报是对外提交法援中心的材料：未提供记录时留空；提供了 `case_progress_entries` 时只填入律师核实的条目，不得预填示例或虚构承办行为。
- 模板按填充方式校验：原温州模板使用配套原文锚点；其他地区新模板可在 manifest.renderers 中选择 placeholders，只校验变量，不要求温州原句。替换母版后须运行 `scripts/validate_template_pack.py` 并试生成复核。
- 调查取证、庭前会议等情况说明先核实程序是否发生；未发生时据实说明。缺少材料不等于没有发生，不得补造取证或会议事实。
- 归档前先识别本次法援承办覆盖的诉讼阶段及该阶段的起点文书：审查起诉阶段以起诉意见书为起点，审判阶段以起诉书为起点。两者处于前后不同的阶段位置，不得因名称相近而机械合并。
- 只使用用户确认或原始材料载明的事实。不得虚构身份号码、日期、地点、答复、案情、认罪认罚态度、辩护意见或裁判结果。
- OCR 和 AI 摘要只作线索；关键字段保留“材料记载 / 用户确认 / 待核实”状态。
- 取保候审、未羁押或监视居住时，必须使用真实的非看守所地点和直接联系口径，不得残留“在押、回押、通过看守所转达”等措辞。
- 审判阶段的法院与公诉机关分别填写；不得从法院名称自动推断检察院。
- 罪名解释在生成前以现行权威法源核验。内置常见罪名库只提供基础会见说明；数额标准、司法解释、竞合和个案量刑仍须当次核验。未收录且未填写 `charge_legal_basis` 时停止生成。
- 模板中所有答复栏默认留空。生成结果是律师工作底稿，须由承办律师逐项复核后使用。
- 对外提交的正式文书不得出现 AI 工作过程痕迹：填报依据、材料来源说明、待核对提醒、OCR 或扫描件字样等只写入内部工作底稿与复核清单，不进文书正文与备注；备注类栏目无实际内容时留空。
- 情况说明按当地法援中心模板制式逐条简明出具；未经承办律师要求，不把情况说明扩展为归档目录全部项目的材料清点清单。侦查阶段归档组合包含单独的调查取证情况说明，正文须由承办律师据实核实后提供。
- 温州默认模板包生成文书时，正文及表格正文统一为仿宋_GB2312 四号（14 磅），文书主标题为黑体三号（16 磅），段落采用固定值 28.5 磅行距。其他地区应在当地模板包 `manifest.json` 中设置并复核本地格式。
- 法援案件不得套用普通收费委托合同或普通客户授权材料。

涉及受援人材料、模板导入、AI读取或对外发布前，先读 [隐私与安全门](references/privacy-and-safety.md) 和 [AI合规使用门](references/ai-compliance-gate.md)。

## 使用流程

面向首次使用的律师，先提供 [使用指引](docs/使用指引.md)，帮助确定需求、材料和交付范围。

先读 [5分钟快速上手](references/quick-start.md)，再按以下流程操作：

1. 有流程台账时，以台账和原始材料交叉核对字段；没有台账时，先按 [无台账材料时间线](references/material-timeline.md) 扫描本地材料，生成待核实候选时间线。
2. 读取 [字段结构](references/field_schema.json)，只把已经核实的字段写入案件JSON。
3. 判断是否使用默认温州模板包。其他地区先按 [模板包替换指南](references/template-pack-guide.md) 建立当地模板包并验证。
4. 根据 [分阶段办理与归档规则](references/workflow.md) 确定文书组合。
5. 查看 [常见罪名基础说明库](references/charge-library-guide.md)。已收录罪名仍需确认法源适用时间；未收录罪名须把本案核验后的简明说明写入 `charge_legal_basis`。
6. 先用 `--dry-run` 预览，再运行生成器。生成后按自动附带的律师复核清单检查事实、机构、阶段、羁押口径、签名栏、版式和未替换变量。

```bash
python3 scripts/generate_criminal_legal_aid_set.py \
  --input /path/to/case.json \
  --output-dir ./output \
  --mode current \
  --template-pack wenzhou
```

`references/case_example.json` 是不含任何真实受援人数据的字段样例：先复制到案件工作目录、填写已核实字段后再作为 `--input` 使用，不要把真实案件 JSON 回写进 Skill 包。

使用外部地区模板包：

```bash
python3 scripts/generate_criminal_legal_aid_set.py \
  --input /path/to/case.json \
  --output-dir ./output \
  --mode current \
  --template-pack-dir /path/to/local-template-pack
```

## 模式

- `current` / `initial`：当前阶段基础材料。
- `archive`：生成结案归档文书；委托手续、会见笔录等基础材料使用已有原件，不重复生成。新收指派仍通过 `current` / `initial` 分阶段准备基础文书；办案中法律意见、辩护词等继续按本工作流办理。
- `all`：当前阶段全部可用材料及已触发的事件材料。

进度可通过 `progress`、`events` 或布尔字段触发，例如：`认罪认罚`、`归档`、`判决后回访`、`取保候审`、`未羁押`。其中 `认罪认罚`（认罪认罚见证笔录）仅在审查起诉、审判阶段生效；`取保候审`、`未羁押`、`监视居住` 不产生文书，只切换会见笔录的非羁押口径。

## 模板与平台

- Word、Excel 母版放在 `assets/template-packs/<pack-id>/`，属于输出资产；替换说明放在 `references/`，属于操作规则。
- 每个 Office 母版同时附带 `.b64.txt` 文本副本；发布平台过滤二进制文件时，生成器会自动还原母版。更换模板后须运行 `scripts/encode_template_assets.py` 更新副本。
- 每个模板包用 `manifest.json` 绑定标准文书键和实际文件名。生成器不依赖某个平台的 Skill 安装机制，可由支持本地文件与 Python 的主流 Agent 调用。
- 默认温州模板包只对列明的法律援助中心启用；其他地区不得仅改机构名称后直接使用，应替换当地会见、阅卷、庭审和归档模板。
- 导入不同 Agent 前读取 [平台兼容与推荐](references/platform-compatibility.md)。若平台不能执行本地脚本或访问案件目录，只能提供指导，不得声称已经扫描或生成文件。不得自动向外部邮箱、网盘、消息系统、办案机关、当事人或证人发送、上传或写入案件信息；任何外部动作须经承办律师逐次确认。

## 交付前质量门

运行：

```bash
python3 scripts/doctor.py
python3 scripts/check_platform_compatibility.py --platform codex
python3 scripts/validate_charge_library.py
python3 scripts/audit_distribution_package.py .
python3 scripts/validate_template_pack.py assets/template-packs/wenzhou
```

随后对生成的 DOCX 逐页渲染检查：无裁切、重叠、表格破损、旧案内容、个人私章、律师证号、真实受援人信息或未替换变量。

遇到环境、OCR、加密PDF、字体或地区模板问题，查看 [常见问题](references/faq.md)。
