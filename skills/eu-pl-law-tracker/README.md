# EU/PL Law Tracker（欧盟/波兰法律跟踪器）

用于分析欧盟法规及波兰相关法案/草案状态的技能。

## 结构

- `SKILL.md`——操作说明。
- `references/`——来源、标识符模式、可信度、报告模板。
- `scripts/`——用于识别和提取数据的辅助 CLI 脚本。

## 脚本快速使用

```bash
python scripts/eu_law_identify.py --query "CBAM" --aliases references/regulation-aliases.yaml
python scripts/eu_law_parse.py --input-file path/to/act.txt
python scripts/legal_date_extractor.py --input-file path/to/act.txt
python scripts/relation_extractor.py --input-file path/to/act.txt
```

脚本结果仅作为辅助，务必在官方来源中验证。

## 在 VS Code 中从 ZIP 安装技能

技能归档位于：

- `D:\eu-pl-law-tracker\.vscode\eu-pl-law-tracker.zip`

安装简要步骤：

1. 关闭 VS Code（建议）。
2. 将 ZIP 解压到文件夹：
   - `C:\Users\grzeg\AppData\Roaming\Code\User\prompts\skills\eu-pl-law-tracker`
3. 检查文件是否存在：
   - `C:\Users\grzeg\AppData\Roaming\Code\User\prompts\skills\eu-pl-law-tracker\SKILL.md`
4. 重新启动 VS Code，并在 Copilot Chat 中开始新的对话。

完整说明见 [.vscode/README.MD](.vscode/README.MD) 文件。

