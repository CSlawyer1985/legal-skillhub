# 右键神器

**【macOS Only】律师桌面效率基础设施**

> 把重复一千次的格式操作，变成右键一次。

---

## 为什么律师需要这个

你的一天里有多少次——

- 打开同事改过的合同，**修订痕迹、批注、混乱字体**混在一起，得花十分钟手动接受修订、统一格式
- 客户发来的起诉材料是 Markdown/扫描件，要**转 Word、调格式**才能提交法院
- 证据清单表格太宽，打印出来被截断，得**手动拆表或调页面方向**
- 接到新案子，**选中企业名称、复制、打开浏览器、粘贴到天眼查**——五步才能查到对方底细
- 助理整理的 Excel 表格，字体大小不一、列宽参差不齐，**逐行逐列调格式**
- 合同定稿后，**打开 Word → 另存为 → 选 PDF**，三步才能提交电子版

这些不是工作，是腱鞘炎creator。

这个项目把律师日常最高频的 9 个文件操作，塞进 macOS 右键菜单。**选中文件 → 右键 → 完成。** 不用打开任何应用。

---

## 能做什么

### 一、格式急救（3 个）

| 工具 | 场景 | 效果 |
|------|------|------|
| **word整理** | 同事改过的合同/起诉状，修订痕迹+批注+混乱字体 | 一键接受所有修订、删除批注、统一格式 |
| **Excel格式整理** | 助理做的证据清单/费用表，格式不统一 | 统一字体、自动列宽、加边框、冻结首行 |
| **MD整理** | 用 Obsidian/备忘录写的案件笔记，要提交或分享 | 统一 Markdown 格式、自动编号、清理多余空行 |

### 二、文档转换（4 个）

| 工具 | 场景 | 效果 |
|------|------|------|
| **word转PDF** | 合同/律师函定稿，提交法院或发给客户 | 右键直接转 PDF，不打开 Word |
| **MD转Word** | 用 Markdown 写的起诉状/法律意见，要提交法院 | 直接转 .docx，保留标题层级和列表格式 |
| **PDF转MD** | 收到对方律师的 PDF 答辩状，要提取文字引用 | 智能转 Markdown，保留段落结构 |
| **Word表格横排** | 证据清单/案件信息表太宽，竖向打印被截断 | 自动将表格所在页设为横向，其余保持纵向 |

### 三、信息生成（1 个）

| 工具 | 场景 | 效果 |
|------|------|------|
| **生成信息图** | 案件时间线/法律关系图/证据链梳理，要放进 PPT 或打印 | 自动生成可视化信息图（HTML+PDF），支持时间线、层级图、对比表 |

### 四、信息查询（1 个）

| 工具 | 场景 | 效果 |
|------|------|------|
| **查询天眼查** |  anywhere 看到企业名称，想查股权结构/涉诉信息 | **选中文字 → 右键 → 查询天眼查**，直接跳转搜索页 |

---

## 工具联用：原子组合，想象力是上限

每个工具都是原子级的，但组合起来就能覆盖真实工作流。下面是几个典型场景，感受一下：

### 场景一：处理对方发来的 PDF 答辩状

```
PDF转MD  →  MD整理  →  MD转Word
```

对方律师发来 PDF 答辩状，你要在自己的上诉状里引用原文。
**原来：** 手动复制粘贴 + 调格式 + 排版。
**现在：** 三次右键，第一次转 Markdown，第二次整理格式，第三次直接出 Word。

### 场景二：同事改过的合同，要发给客户

```
word整理  →  word转PDF
```

合伙人用修订模式改了一版合同，你确认无误后要发 PDF 给客户。
**原来：** 打开 Word → 全选接受修订 → 删批注 → 调格式 → 另存 PDF。
**现在：** 两次右键，干净 PDF 直接出来。

### 场景三：助理用 Markdown 写了起诉状，要提交法院

```
MD整理  →  MD转Word  →  word转PDF
```

助理在 Obsidian 里写好了起诉状草稿，法院要求 Word + PDF。
**原来：** 复制到 Word → 格式崩了 → 手动修 → 转 PDF。
**现在：** 三次右键，原样出来。

### 场景四：把对方的合同变成可视化分析

```
PDF转MD  →  MD整理  →  生成信息图
```

收到对方律师发来的合同，想要快速了解结构、重点条款分布。
**原来：** 手动翻阅，整理要点，PPT 排版。
**现在：** 三次右键，直接出一张结构清晰的信息图。

### 场景五：合同里看到对方企业名称，想查底细

```
选中企业名称 → 查询天眼查
```

在 Word 合同或 PDF 材料里看到对方公司名称，想查股权结构、涉诉信息、关联企业。
**原来：** 复制名称 → 打开浏览器 → 打开天眼查 → 粘贴搜索。
**现在：** 选中文字 → 右键 → 查询天眼查，直接跳转到搜索页。

> **提示：** 以上流程不需要连续操作——可以先做前几步，下次有空再做后面的。工具之间是松耦合的，按需组合。

---

## 安装

### 方式一：AI 助手一键安装（推荐）

在支持 WorkBuddy Skill 的 AI 助手中说：

> 「帮我安装右键工具」
> 「全部安装」
> 「只装 word整理 和 查询天眼查」

AI 自动完成依赖检测、脚本安装、右键菜单注册。

### 方式二：手动安装

```bash
cd ~/.workbuddy/skills/右键神器
python3 scripts/install.py --all
```

安装特定工具：
```bash
python3 scripts/install.py --tools word整理 docx2pdf 查询天眼查
```

查看可用工具：
```bash
python3 scripts/install.py --list
```

---

## 前置依赖

| 依赖 | 用途 | 安装命令 |
|------|------|---------|
| Python 3.8+ | 运行脚本 | macOS 自带或 `brew install python` |
| python-docx | word整理、MD转Word | `pip3 install python-docx` |
| lxml | word整理 | `pip3 install lxml` |
| pandoc | word整理、生成信息图 | `brew install pandoc` |
| openpyxl | Excel格式整理 | `pip3 install openpyxl` |
| pdfplumber | PDF转MD | `pip3 install pdfplumber` |
| pdf2image | PDF转MD | `pip3 install pdf2image` |
| pytesseract | PDF转MD | `pip3 install pytesseract` |
| Pillow | PDF转MD | `pip3 install Pillow` |
| poppler | PDF转MD | `brew install poppler` |
| tesseract | PDF转MD | `brew install tesseract` |
| tesseract-lang | PDF转MD（中文OCR） | `brew install tesseract-lang` |
| Node.js | 查询天眼查 | `brew install node` |
| LibreOffice | docx2pdf | `brew install --cask libreoffice` |

install.py 会在安装前自动预检，缺失时给出明确提示。

---

## API Key 配置

以下工具需要 API Key：

| 工具 | 需要 API Key | 支持的供应商 |
|------|-------------|-------------|
| 生成信息图 | DeepSeek 或 千问 | DeepSeek、千问 |
| MD整理 | DeepSeek 或 千问 | DeepSeek、千问 |

### 配置方式（推荐：AI 对话引导）

通过 AI 助手安装时，AI 会在对话中询问你的 API Key，自动完成配置。**无需手动编辑文件。**

### 手动配置（可选）

```bash
# 查看当前配置状态
python3 scripts/configure.py --status

# 配置生成信息图 - DeepSeek
python3 scripts/configure.py infographic --set-key deepseek_api_key=sk-your-key

# 配置生成信息图 - 通义千问
python3 scripts/configure.py infographic --set-key qwen_api_key=sk-your-key

# 配置 MD整理
python3 scripts/configure.py md-cleaner --set-key api_key=sk-your-key

# 批量配置（JSON 方式）
python3 scripts/configure.py infographic --json '{"deepseek_api_key":"sk-xxx","qwen_api_key":"sk-yyy"}'
```

获取 API Key：
- **DeepSeek**: https://platform.deepseek.com/
- **通义千问**: https://dashscope.aliyun.com/

### 运行时行为

- **已配置 API Key** → 正常执行
- **未配置 API Key** → 静默退出（不弹窗、不报错），记录到日志 `~/.rightclick-creator/logs/`

---

##  uninstall

```bash
# 卸载单个工具
python3 scripts/install.py --uninstall word整理

# 全部清除
rm -rf ~/.rightclick-creator
rm -rf ~/Library/Services/word整理.workflow
rm -rf ~/Library/Services/Word表格横排.workflow
rm -rf ~/Library/Services/Excel格式整理.workflow
rm -rf ~/Library/Services/word转PDF.workflow
rm -rf ~/Library/Services/MD转Word.workflow
rm -rf ~/Library/Services/生成信息图.workflow
rm -rf ~/Library/Services/PDF转MD.workflow
rm -rf ~/Library/Services/MD整理.workflow
rm -rf ~/Library/Services/查询天眼查.workflow
/System/Library/CoreServices/pbs -flush
killall Finder
```

---

## 技术原理

本工具严格遵循 [macOS 右键工具开发天条](https://github.com/MarvinLann/rightclick-creator)（技术原理页面），核心流程：

1. **种子复制**：用 `cp -R` 复制已验证的 Automator workflow（绝不从零创建）
2. **脚本注入**：用 `plistlib` 修改 workflow 内的 `COMMAND_STRING`（绝不用 sed/echo/cat）
3. **路径统一**：所有 Python 脚本统一安装到 `~/.rightclick-creator/tools/`
4. **服务注册**：`pbs -flush` + `killall Finder` 刷新右键菜单缓存

---

## 扩展新工具

1. 在 Automator 中创建并验证新 workflow
2. 复制 Python 脚本到 `scripts/tools/{新工具}/`
3. 在 `references/tools_catalog.json` 中添加配置
4. 重新运行 `install.py`

---

## License

Apache 2.0

---

## 联系作者

有功能建议、Bug 反馈或合作需求，欢迎扫码添加微信交流：

<div align="center">
  <img src="assets/兰律师二维码.jpg" alt="微信联系" width="200"/>
</div>

<p align="center">律师 × 开发者｜让法律工作的每一步都少一点摩擦</p>
