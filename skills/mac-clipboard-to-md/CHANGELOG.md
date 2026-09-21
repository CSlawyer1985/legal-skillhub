# Changelog

## 2026-05-23 — v1.1.1

### Fixed
- **换行符修复**：AppleScript 中作为换行符的 `return`（CR）全部替换为 `linefeed`（LF），解决生成文件在现代 Markdown 编辑器（Obsidian / VS Code / GitHub）中挤成一行的 P0 问题
- **写入安全性修复**：`brain-dump.applescript` 的 `echo` 替换为 `printf '%s'`，避免 shell 解释特殊字符串（`-n`/`-e`）或反斜杠导致的边界 case
- **行分割健壮性**：`work-record.applescript` 改用 AppleScript 原生 `paragraphs` 分割行，自动兼容 CR / LF / CRLF 三种换行符格式，不再依赖外部命令
- **路径展开**：`install.py` 添加 `os.path.expanduser`，支持 `~` 开头的路径
- **占位路径优化**：路径占位符由 `/Users/你的用户名/` 改为 `~/`，默认路径改为 `~/Desktop/...` 确保直接回车可用
- **SKILL.md Phase 6b 手动指引**：从 `sed`+硬编码行号改为 `grep -n` 按内容搜索路径占位符，不再依赖行号；同时为 brain-dump 补全指引
- **SKILL.md Phase 4 选项优化**：默认路径从占位符改为 `~/Desktop/...` 和 `~/用户目录/...`，直接可选可用路径
- **install.py 异常兜底**：`refresh_services()` 添加 try/except，`pbs` 和 `killall` 不可用时不会崩
- **install.py 正则兼容**：`read_template` fallback 正则同时支持 `/Users/...` 和 `~/...` 格式

### Changed
- **README 重构**：新增安装流程图（Mermaid），拆分为中英文双文档（`README.md` + `README.en.md`），完善安装指引和参数说明
- **install.py 交互模式优化**：新增桌面/用户目录两个默认选项，回车即可用，不会拿到占位符

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
