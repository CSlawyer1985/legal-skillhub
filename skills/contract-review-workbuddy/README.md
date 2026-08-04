# 合同智能审查 Skill (contract-review) v3.0

中文合同智能风险审查工具，支持 PDF / Word / 图片 / 纯文本，通过"规则引擎 + LLM 语义审查"双轨机制识别合同风险。
v3.0 新增：安全风险拦截、历史版本对比、Word 报告生成、硬件自适应调度、更新检测提醒。

## 🆕 v3.0 新特性（2026-07-13）

- 🛡️ **安全风险拦截**：自动拦截 `.exe/.bat/.ps1/.vbs/.cmd/.com/.scr/.hta/.reg/.zip/.rar/.7z/.tar/.gz/.iso/.dmg/.apk/.jar` 等 10+ 类危险文件，阻止伪装扩展名攻击
- 📊 **历史版本对比**：保留每次审查记录，对比新旧合同版本，只高亮新增风险点（合同谈判多轮刚需）
- 📝 **Word 报告一键生成**：审查结果直接生成带删除线+下划线+批注的 `.docx`，发给业务方直接修订
- ⚡ **硬件自适应调度**：自动检测 CPU/内存容量，动态调整 OCR 并行度和 LLM 超时，不拖累用户电脑
- 🔔 **更新检测提醒**：每次运行异步检查 GitHub 新版本，有新版本时友好提示（每 7 天提醒一次）
- 📬 **反馈邮箱**：添加官方反馈邮箱 njskills@agent.qq.com

## 快速开始

```bash
# 1. pip 安装
pip install -e .

# 2. 运行首次向导
python scripts/main.py --first-time

# 3. 审查合同（基础）
python scripts/main.py 合同文件.pdf

# 4. 审查并生成 Word 报告
python scripts/main.py 买卖合同.pdf --format docx --output 报告.docx

# 5. 对比历史版本
python scripts/main.py 合同_v2.pdf --diff ~/.contract-review/history/xxxx_last.json

# 6. 查看历史记录
python scripts/main.py --history

# 7. 查看硬件配置
python scripts/main.py --show-hardware

# 8. 检查更新
python scripts/main.py --check-update
```

## 参数列表

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `file` | 合同文件路径 | - |
| `--type, -t` | 合同类型 | 自动识别 |
| `--role, -r` | 审查视角（甲方/乙方/双方）| 双方 |
| `--output, -o` | 输出文件路径 | report.md |
| `--format, -f` | 输出格式（markdown/json/docx）| markdown |
| `--scope` | 审查范围 | 全面审查 |
| `--no-llm` | 跳过 LLM 审查 | false |
| `--text, -x` | 直接传入合同文本 | - |
| `--install-ollama` | 安装 Ollama 本地模型 | - |
| `--first-time` | 首次使用向导 | - |
| `--verbose, -v` | 显示详细日志 | false |
| `--history` | 查看历史审查记录 | - |
| `--diff` | 对比历史报告（v3.0） | - |
| `--show-hardware` | 显示硬件信息（v3.0） | - |
| `--check-update` | 检查更新（v3.0） | - |

## 三种运行模式

| 模式 | 说明 | 需要 |
|------|------|------|
| 🥇 **Ollama 本地** | 完全本地运行，隐私最优 | 下载 Ollama + 模型（约4-8GB） |
| 🥈 **OpenAI API** | 效果最佳 | OpenAI API 密钥 |
| 🥉 **规则引擎** | 开箱即用，无需额外配置 | 无（推荐新手） |

## 安全特性（v3.0 增强）

### 🚫 禁止文件类型拦截

自动识别并阻止以下危险文件上传（可执行文件、宏文档、压缩包等）：

| 类别 | 禁止后缀 | 风险说明 |
|------|---------|---------|
| Windows 可执行/批处理 | `.bat` `.cmd` `.ps1` `.vbs` `.exe` `.dll` `.lnk` `.msi` | 可能包含恶意代码 |
| Office 二进制文档 | `.doc` `.xls` `.ppt` `.xlsm` `.docm` `.pptm` | 可能包含宏病毒 |
| 压缩包/安装包 | `.zip` `.rar` `.7z` `.tar` `.gz` `.iso` `.dmg` `.apk` `.jar` | 解压后可能包含恶意内容 |
| 脚本文件 | `.sh` `.com` `.scr` `.hta` `.reg` | 可能执行危险操作 |
| 系统缓存 | `.DS_Store` `.log` `.tmp` | 无意义且可能泄露信息 |

### 🔒 魔术字节深度校验

不仅检查扩展名，还读取文件头的魔术字节，防止恶意文件伪装成 PDF/图片格式。

### 🛡️ 其他安全机制

1. **文件大小限制**：单文件最大 50MB，防止 DoS 攻击
2. **YAML 安全加载**：使用 `safe_load` 防止反序列化攻击
3. **正则安全检查**：限制正则表达式长度，防止 ReDoS 攻击
4. **个人信息脱敏**：报告中的身份证号、手机号自动替换为 ***
5. **日志隐私保护**：不输出完整文件路径和合同原文到日志

## 版本对比功能说明

在合同谈判多轮场景中，可以使用版本对比功能：

```bash
# 1. 第一轮审查
python scripts/main.py 合同_v1.pdf

# 2. 修改后审查（对比 v1）
python scripts/main.py 合同_v2.pdf --diff ~/.contract-review/history/xxxx_last.json

# 输出示例：
# 🆕 新增 3 个风险点
# ✅ 已解决 2 个风险点
# ⚠️ 等级变化 1 个风险点
```

系统会：
- 自动识别新旧版本的风险点差异
- 只高亮的**新增风险点**
- 列出已解决的风险点
- 标注严重等级变化的风险点

## Word 报告功能说明

使用 `--format docx` 生成带修订痕迹的 Word 报告：

| Word 元素 | 对应含义 |
|----------|---------|
| 删除线（红色） | 风险原文（建议删除/修改） |
| 下划线（绿色） | 修改建议（建议新增内容） |
| 批注样式文本 | 业务方需关注的修改点 |
| 基本信息表格 | 合同基本信息 |
| 评分颜色 | 红色(<50) / 橙色(50-70) / 绿色(>70) |

业务方收到报告后可直接对照修订，无需手动整理。

## 硬件自适应调度说明

系统自动检测用户电脑配置，调整资源分配：

| 硬件等级 | CPU | 内存 | OCR 并行 | LLM 超时 |
|---------|-----|------|---------|---------|
| 低配 | ≤4核 | ≤8GB | 1页/批 | 300s |
| 中配 | 4-8核 | 8-16GB | 4页/批 | 180s |
| 高配 | ≥8核 | ≥16GB | 8页/批 | 120s |

检测信息缓存 1 小时，避免频繁检测。

## 文件结构

```
contract-review/
├── SKILL.md                       ← Skill 定义（v3.0，含完整文档）
├── README.md                      ← 本文件
├── pyproject.toml                 ← pip 安装配置（v3.0.0）
├── requirements.txt               ← 依赖列表（备选安装）
├── references/                    ← 参考文件
│   ├── risk_rules.yaml            ← 26条风险规则
│   ├── contract_types.yaml        ← 10种合同类型定义
│   ├── modification_templates.yaml ← 22个修改范本
│   ├── legal_basis.md             ← 法律法规依据
│   └── compliance_checklist.md     ← 5套合规检查清单
├── scripts/                       ← Python 脚本（v3.0）
│   ├── extract_text.py            ← 多格式文本提取 + 危险文件拦截
│   ├── parse_structure.py         ← 合同结构解析
│   ├── rule_engine.py             ← 规则引擎
│   ├── llm_review.py              ← LLM 审查
│   ├── generate_report.py         ← 报告生成
│   ├── history_manager.py         ← v3.0 历史审查记录
│   ├── docx_generator.py          ← v3.0 Word 报告生成
│   ├── hardware_detector.py       ← v3.0 硬件检测
│   ├── updater.py                 ← v3.0 更新检测
│   └── main.py                    ← 主入口（v3.0）
└── assets/
    └── report_template.md         ← 报告模板
```

## 安装 Ollama（推荐免费方案）

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5:7b
ollama serve

# Windows
# 访问 https://ollama.ai/download 下载 OllamaSetup.exe 安装后：
ollama pull qwen2.5:7b
ollama serve
```

## 评分说明

综合评分（0-100 分，分数越高风险越低）：
- **90-100**：风险较低，可放心签署
- **70-89**：风险中等，建议修改后签署
- **50-69**：风险偏高，需要认真修改
- **0-49**：风险很高，强烈建议咨询律师

**扣分规则**：
- 🔴 严重：-15 分/项
- 🟡 中等：-8 分/项
- 🟢 一般：-3 分/项
- ℹ️ 提示：不扣分

## 免责声明

本报告由 AI 生成，仅供使用者参考，不构成法律意见。对于重大合同（标的额超过 100 万元或涉及核心商业利益），建议咨询专业执业律师。

## 反馈与建议

如有更好建议，欢迎联系：**njskills@agent.qq.com**

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.0 | 2026-07-13 | 增加：安全风险拦截（50+类危险文件，含 exe/bat/ps1/vbs/cmd/scr/hta/reg/zip/rar/7z 等）；增加：历史版本 diff 对比审查（只高亮新增风险）；增加：Word 报告一键生成（删除线/下划线/批注）；增加：硬件自适应性能调度（自动检测 CPU/内存）；增加：Skill 更新检测提醒（每 7 天）；增加：反馈邮箱 njskills@agent.qq.com |
| v2.5.0 | 2026-07-04 | 修复：版本号对齐（统一为 2.5.0） |
| v2.0.0 | 2026-07-04 | 增加：魔术字节校验与文件大小限制；增加：个人信息脱敏；增加：首次使用向导（Ollama 安装）；增加：Ollama 一键安装向导；增加：评分可视化（扣分透明化）；修复：去掉 reportlab/pydantic/jieba 三个未使用依赖 |
| v1.0.0 | 2026-07-02 | 初始版本：支持 PDF/Word/图片/纯文本合同，26条风险规则，双轨审查（规则引擎+LLM），Markdown 报告输出 |
