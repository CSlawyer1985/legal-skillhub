---
name: image-paginator
description: Slices long images/screenshots into overlapping segments, adds sequence numbers, and auto-arranges them into a paginated PDF with gaps and page numbers. Supports multiple images. (律师证据长截图转PDF)
license: GPL-3.0
metadata:
  author: WUDI
  version: "2.1"
---

# Image Paginator（律师证据长截图转PDF）
> 将长截图/长图智能分页为规范 PDF，支持网格切片、页码标注、微信证据排版

---

## 📌 快速上手（律师场景示例）

**场景：微信聊天截图 → 提交法院的证据 PDF**

```bash
# 1. 律师导出微信聊天记录为长截图
# 2. 一键转换：
python scripts/slice_n_pdf.py "/Users/律师/Desktop/聊天记录.jpg" \
  -d "/Users/律师/Desktop" -o "聊天证据_20250105.pdf" --clean

# 3. 直接提交 PDF，打印存档，或发邮件
open "/Users/律师/Desktop/聊天证据_20250105.pdf"
```

---

## ⚖️ 律师场景专区

### 适用场景

| 场景 | 输入 | 输出 |
|------|------|------|
| 微信聊天证据截图 | 微信长截图（竖向拼接后） | 分页 PDF，含页码+序号 |
| 合同附件超长截图 | 多页合同 PDF 截图拼接 | A4 规范 PDF，可打印 |
| 笔录/判决书截图 | 判决书长截图 | 2×2 网格 PDF，便于阅读 |
| 批量证据材料归档 | 多张证据截图（不同尺寸） | 统一宽度，竖向拼接，分页 |
| 邮件/短信截图证据 | 手机截图 | 带间距 PDF，避免阅读串行 |

### 输入规范建议

- **分辨率**：推荐 1080px 宽，最佳清晰度
- **格式**：PNG / JPG 均可，建议 PNG 保留更多细节
- **多张截图**：按时间顺序传入，自动按顺序拼接
- **不要裁剪**：保持原始宽高比，工具会自动适配

### 输出规范

- **纸张尺寸**：A4（595 × 842 pt）
- **网格布局**：默认 2 列 × 2 行，每页 4 格
- **页码**：底部居中，格式 `- N -`
- **切片编号**：每个格子左上角标注，格式如 `1-1`、`2-3`
- **间距**：格子间默认留 40px 灰色间隙，便于翻页区分
- **尾部合并**：最后一页不足一格时，自动合并到前一页，避免孤零零一行

### 法院提交注意事项

1. 截图完整性：确保聊天记录从头到尾完整，不要断章取义
2. 时间戳：PDF 页码和序号可以快速定位原文位置
3. 尺寸：导出前确认截图宽度统一（建议 1080px），避免 PDF 页面大小不一
4. 合并打印：如有多个案件，可先生成多个 PDF，再合并为一个文件

---

## 📊 效果示意图

### 场景总览
![场景总览](diagram_scenarios.png)

### 律师场景：输入 → 输出
![律师场景对比](diagram_lawyer_beforeafter.png)

> 💡 示意图仅供参考，实际效果取决于截图分辨率和参数设置。

---

## Prerequisites
Required python packages: `Pillow`, `fpdf2`.

## How to use this skill
Execute the python script `scripts/slice_n_pdf.py` via the command line.

### Command Syntax
```bash
python scripts/slice_n_pdf.py <source1> [source2 ...] -d <output_dir> [OPTIONS]
```

### Required Arguments
* `sources` (positional): Path(s) to source image(s). Multiple images will be auto-resized to the same width and concatenated in order.
* `-d` / `--dest`: Directory to save the output PDF.

### Optional Arguments
* `-o` / `--output`: Name of the output PDF file (default: `output.pdf`).
* `--tile`: Height of each tile in pixels (default: `2000`).
* `--bleed`: Bleed / overlap in pixels (default: `200`).
* `--cols`: Grid columns (default: `2`).
* `--rows`: Grid rows (default: `2`).
* `--gutter`: Gap between cells in pixels (default: `40`).
* `--edge`: Page margin in pixels (default: `25`).
* `--no-numbers`: Omit page numbers at the bottom.
* `--clean`: Remove intermediate tile images after build.

### Key Features (v2.1)
1. **Multiple source images**: Pass multiple paths; images auto-resize to uniform width and concatenate vertically.
2. **Sequence numbers**: Each tile has a numbered badge (1, 2, 3…) on the top-left corner.
3. **Gaps between tiles**: Configurable gutter with light gray cell backgrounds for readability.
4. **Consistent page sizes**: All PDF pages share the same dimensions.
5. **Page numbers**: Each page has a centered `- N -` footer (disable with `--no-numbers`).
6. **Adaptive tail merging**: Short tail segments merge into the previous tile to avoid tiny orphans.
7. **Parameter validation**: Auto-checks tile > bleed, cols/rows range (1-10), file existence, etc.

## ⚠️ Important Instructions for the Agent (Guardrails)
1. **Always use `--clean`** by default unless the user specifically asks to keep tiles.
2. **Absolute Paths**: Resolve `~` and relative paths to absolute paths before running.
3. **Multiple images**: When the user provides multiple images, pass all as positional arguments.
4. **DO NOT try to read the output PDF**: The result is binary. Just check STDOUT — if it says `✓ Done`, tell the user the file path.
5. **Always open the PDF** for the user after generation using `open <path>` (macOS).

## Examples

**Single long image:**
```bash
python scripts/slice_n_pdf.py "/Users/bob/Downloads/long_chat.png" \
  -d "/Users/bob/Desktop" -o "chat.pdf" --clean
```

**Multiple images with custom grid:**
```bash
python scripts/slice_n_pdf.py "/Users/bob/Desktop/1.jpg" "/Users/bob/Desktop/2.jpg" \
  -d "/Users/bob/Desktop" -o "combined.pdf" \
  --cols 2 --rows 2 --gutter 40 --clean
```

**Single column, larger tiles:**
```bash
python scripts/slice_n_pdf.py "/abs/path/webpage.jpg" \
  -d "./results" --cols 1 --rows 3 --tile 3000 --gutter 20 --clean
```

---

## 参数速查表

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--tile` | 2000 | 每格切片高度（像素），建议 ≥ 100 且 > --bleed |
| `--bleed` | 200 | 上下切片重叠高度（像素），必须 < tile |
| `--cols` | 2 | 每页网格列数（1-10） |
| `--rows` | 2 | 每页网格行数（1-10） |
| `--gutter` | 40 | 格子间距（像素） |
| `--edge` | 25 | 页面边距（像素） |
| `--no-numbers` | — | 关闭页码 |
| `--clean` | — | 生成后清理临时切片图 |

> ⚠️ **参数校验**：脚本会自动检查 tile > bleed、cols/rows 在合理范围内、文件存在等，发现问题直接报错退出。

---

## 一键安装脚本

```bash
# 方法一：克隆后安装
git clone https://github.com/wux818738-alt/openclaw-skill-image-paginator.git
cd openclaw-skill-image-paginator
bash install.sh

# 方法二：直接下载
curl -fsSL https://github.com/wux818738-alt/openclaw-skill-image-paginator/archive/refs/heads/main.zip -o /tmp/skill.zip
unzip /tmp/skill.zip -d ~/.qclaw/skills/
pip3 install fpdf2 Pillow
```

安装后直接运行（不需要指定完整路径）：
```bash
python ~/.qclaw/skills/image-paginator/scripts/slice_n_pdf.py <图片> -d <输出目录>
```
