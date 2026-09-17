# 平台兼容与推荐

本 Skill 遵循以 `SKILL.md` 为入口、`scripts/` 执行确定性任务、`references/` 按需加载规则、`assets/` 存放模板的通用结构。平台兼容不能只看“能否导入”，还应核对本地文件访问、脚本执行、依赖工具、权限和案件数据去向。

## 推荐顺序

| 平台 | 兼容级别 | 推荐用途 | 主要差异 |
|---|---|---|---|
| Codex Desktop / CLI | 完整验证 | 真实案件扫描、生成和归档 | 本 Skill 的开发、回归测试和 `agents/openai.yaml` 均以此为首要环境 |
| WorkBuddy | 推荐入口 | 普通律师调用和现场演示 | 必须确认运行壳可访问案件目录并执行本地 Python；否则只能降级为指导模式 |
| Claude Code | 标准兼容 | 长卷宗理解和复杂流程分析 | 支持 `SKILL.md`、脚本和配套文件；首次真实案件使用前应跑完整测试 |
| Gemini CLI | 标准兼容 | 跨平台本地运行 | Skill 激活和 shell 执行可能需要逐次授权 |
| OpenCode | 需轻量适配 | 开源环境及模型切换 | 目录名应与 Skill name 一致，并开放 skill、read、bash 和案件目录权限 |
| 纯网页聊天平台 | 仅限脱敏演示 | 教学、说明和脱敏样例 | 不适合依赖本地案卷扫描、Poppler/Tesseract或真实受援人材料的任务 |
| SkillHub | 分发渠道 | 发布、下载和版本更新 | SkillHub不是实际案件运行环境，最终能力取决于导入后的Agent和本机工具 |

## 统一能力门槛

完整运行需要平台同时具备：

1. 发现并加载根目录 `SKILL.md`，能按相对路径读取 `references/` 和 `assets/`。
2. 可以在本机执行 Python 3.9+，并安装 `python-docx`。
3. 可以访问用户明确指定的案件目录，并将输出写入案件工作目录而不是 Skill 包。
4. 有文字层PDF时可调用 `pdftotext`；扫描PDF/图片OCR时可调用 Poppler和Tesseract中文模型。
5. 能限制网络和外部目录权限，不把真实案件材料自动上传或写入公共示例。

完整运行并不等于允许云端模型读取真实案件材料。若平台的模型上下文、插件、日志、记忆、外部 API 或自动化外发无法由承办律师和律所控制，只能执行本地脚本、脱敏演示或操作指导。

若只满足第1项，平台只能执行“指导模式”：说明流程、列字段和生成清单，不能声称已经扫描案卷或生成本地文件。

## 安装与调用

### Codex Desktop / CLI

将完整 Skill 目录放入或链接到 Codex 的用户或项目 skills 目录。通过 `$wenzhou-criminal-legal-aid-workflow` 显式调用最稳妥，也可由 description 自动触发。首次运行先执行：

```bash
python3 scripts/check_platform_compatibility.py --platform codex
python3 scripts/doctor.py
```

### WorkBuddy

导入完整 ZIP 或完整目录，不能只复制 `SKILL.md`。先确认 WorkBuddy 可访问用户选择的案件目录并执行本地 Python；如不能执行，必须明确告诉用户当前只提供操作指导。

### Claude Code

建议安装目录：

```text
~/.claude/skills/wenzhou-criminal-legal-aid-workflow/
```

可显式调用 `/wenzhou-criminal-legal-aid-workflow`。安装后先运行平台兼容检查和测试，不把 Claude Code 的扩展型 frontmatter 写回公共核心入口，以免降低其他平台兼容性。

### Gemini CLI

可使用 `gemini skills install` 或 `gemini skills link` 安装完整目录，再用 `/skills list` 核对发现状态。Skill 激活和 shell 权限请求应由用户确认，不能绕过平台权限门。

### OpenCode

安装目录名使用：

```text
wenzhou-criminal-legal-aid-workflow
```

可放入 `.opencode/skills/`、`~/.config/opencode/skills/` 或其兼容的 `.agents/skills/`。确认所选 Agent 允许加载 skill、读取材料、执行 bash/Python以及访问项目外案件目录。

## Agent差异的处理原则

- 业务真相只有一份：阶段判断、起点文书、日期状态、隐私门和模板映射全部保留在核心 Skill 中。
- 平台差异只处理安装路径、触发方式、权限、可用工具和输出展示，不复制核心业务规则。
- 能执行脚本时优先运行确定性脚本；不能执行时不得让模型手工模拟“已经运行”的结果。
- 禁止 Agent 自动向外部邮箱、网盘、消息系统、办案机关、当事人或证人发送、上传或写入案件信息；任何外部动作须由承办律师逐次确认。
- Agent没有主动读取某个reference时，应由 `SKILL.md` 的场景路由明确要求读取，不依赖模型自行猜测。
- 模型更换后至少测试：阶段路由、无台账时间线、未羁押口径、法院/公诉机关分离、模板生成、隐私审计和错误提示。

## 自检命令

```bash
python3 scripts/check_platform_compatibility.py --platform codex
python3 scripts/check_platform_compatibility.py --platform claude
python3 scripts/check_platform_compatibility.py --platform gemini
python3 scripts/check_platform_compatibility.py --platform opencode
```

自检只能证明文件和本地依赖存在，不能代替真实权限验证，也不能证明输出已经经过律师复核。
