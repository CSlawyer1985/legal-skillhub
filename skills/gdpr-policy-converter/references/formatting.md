# 排版规范与文档生成

## 交付物形式

- 最终交付为 .docx（用 scripts/build_docx.py 生成），简单文档：无封面、无页眉页脚
- 双语分段：**一段英文接一段中文**交替排版，逐段对应，便于使用者参考、阅读和核对；不使用编号标签、不带【中文】【英文】等标记
- 蓝字批注：重大风险/需进一步工作（DPIA、TIA 等）处以蓝色字体（RGB 0000FF）在对应条款下做简要批注，以【提示】开头
- 红色加粗：待核实事项（不确定来源、假设点）
- 文档结尾必须附免责声明段

## 排版参数

| 项目 | 参数 |
|---|---|
| 中文字体 | 宋体，小四（12pt） |
| 英文字体 | Times New Roman |
| 行距 | 1.5 倍 |
| 段后 | 0.5 行 |
| 首行缩进 | 2 字符（中文按字符，英文按 2 字符宽） |
| 小标题 | 加粗；层级用「一、」「（一）」中文序号体系 |

## build_docx.py 用法

输入为 JSON 文件（UTF-8），结构：

```json
{
  "title_en": "Privacy Policy",
  "title_cn": "隐私政策",
  "date": "Last updated: [日期]",
  "blocks": [
    {"type": "h1", "en": "1. Who We Are", "cn": "一、我们是谁"},
    {"type": "para", "en": "...", "cn": "..."},
    {"type": "note", "text": "【提示】..."},
    {"type": "todo", "text": "【待核实】..."},
    {"type": "disclaimer"}
  ]
}
```

- `h1/h2`：双语标题（中英各一行，无缩进，加粗）
- `para`：先英文段后中文段，各 1.5 倍行距、段后 0.5 行、首行缩进 2 字符
- `note`：蓝字段落（不缩进，字号小四）
- `todo`：红色加粗段落（不缩进）
- `disclaimer`：自动插入免责声明（中英双语）

运行：

```bash
python3 scripts/build_docx.py input.json output.docx
```

字体实现细节：中文宋体通过 w:eastAsia 设置，英文 Times New Roman 通过 w:ascii/hAnsi；首行缩进 2 字符用 w:ind w:firstLineChars="200"；段后 0.5 行用 w:spacing w:afterLines="50"（Word 原生"段后 X 行"语义）。
