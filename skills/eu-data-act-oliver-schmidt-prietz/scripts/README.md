# scripts/

欧盟数据法技能的开发与发布工具。两个工具均为纯 Python 3（无第三方依赖），并从 `SKILL.md` 中引用。

- **`check_house_style.py`** —— 对照技能的内部风格规则（破折号、被禁止的连接词、序言、营销语言）对生成的备忘录、信函或起草交付物进行 lint 检查。
  用法：`python3 scripts/check_house_style.py <path-to-output>`。

- **`validate_sources.py`** —— 在发布前验证来源层（`sources/`）。
  用法：`python3 scripts/validate_sources.py --verbose`。

规范的、始终最新的版本位于技能的 GitHub 仓库中。
