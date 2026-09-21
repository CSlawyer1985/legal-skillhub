# Changelog

## 2026-04-30 — v1.1.0

### Added
- 新增 `SKILL.md`：Claude Code 交互式安装向导，支持 AskUserQuestion 弹窗式问答
- 新增 `scripts/install.py`：自动安装器，通过 plistlib 构造 `.workflow` 包，无需手动操作 Automator
- install.py 新增交互模式：无参数运行时通过问答引导安装
- 新增 `CHANGELOG.md`：版本历史记录
- 新增三种安装方式：自动安装（参数模式）/ 自动安装（交互模式）/ 手动安装 / AI 辅助

### Changed
- Applescript 路径占位符统一为 `Work record.md`
- 更新中英文文档

---

## 2026-02-26 — v1.0.2

### Fixed
- 修复 frontmatter 误判：文件第一行非 `---` 时跳过 frontmatter 扫描，防止正文分割线被识别为 frontmatter 结束
- 修复插入位置：由硬编码第 9 行改为动态定位 frontmatter 结束位置，不再因空行导致错位

---

## 2026-02-07 — v1.0.1

### Changed
- 文档结构优化：README 拆分为中英双语

---

## 2026-02-05 — v1.0.0

### Added
- 首个 GitHub 开源版本
- `work-record.applescript`：静默模式，复制 → 快捷键 → 自动追加到 Work record.md
- `brain-dump.applescript`：交互模式，复制 → 快捷键 → 弹窗输入文件名/标签/描述
