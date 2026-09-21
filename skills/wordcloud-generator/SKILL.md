---
name: wordcloud-generator
description: 从第一性原理生成词云图——支持 14 种内置形状模板（含文字蒙版/矩形/PPT 比例）、按类别配色、11 种命名主题、中英文双语分词，输出 PNG。内置 wordcloud 1.9.x 蒙版语义反直觉的关键坑（形状内部必须为 0）。当用户要"做词云图""把文字排成XX形状""爱心/圆形/星形/文字云""可视化高频词/关键词""照片抠图成词云"时触发。
license: MIT
metadata:
  slug: wordcloud-generator
  displayName: 词云图生成器
  version: 1.4.0
  author: 陆凌燕（北京德恒（无锡）律师事务所）
  agent_created: true
---

# 词云图生成器（Word Cloud Generator）

从第一性原理封装的词云生成技能。不是把脚本丢给你，而是把"词云到底是什么、
以及为什么大多数人第一次做形状词云会翻车"这个认知固化进来，让任何形状、任何
数据都能稳定出图。

## 第一性原理

1. **词云是什么**：一个"按权重决定字号、把词塞进画布"的布局问题。大词先放、
   从中心螺旋往外铺；字号 = 权重（频率/重要性）。
2. **蒙版（mask）是什么**：一个限制"词能落在哪"的二进制画布。
3. **唯一的关键坑（必读）**：`wordcloud` 1.9.x 把蒙版当**基线偏移**消费——
   `img_array = img_grey + (mask==255)`。采样器偏好"累积占用最低"的区域，于是
   词实际落在 `mask==0` 的地方。**结论：想让词填进某个形状，形状内部必须设为 0、
   外部设为 255**。直觉上的"mask==255 是形状内部"是错的，反着来会得到空心轮廓。
4. **配色**：每个词可绑定一个类别，按类别上色（color_func）；无类别则用 colormap。
5. **密度**：词少时开 `repeat=True` 让小字补空隙，才能铺满形状（词云不是实心块，
   内部文字覆盖率 30% 左右即已成形）。

## 何时用

- "做个词云图""把这些关键词做成词云"
- "把文字排成爱心/圆形/星形""形状词云"
- "可视化这堆高频词/关键词/国家/标签"
- 本机无专用词云 skill 时，直接用 Python 生成（无需联网）

## 怎么用

依赖（一次性）：`pip install wordcloud matplotlib numpy pillow jieba`；照片自动抠图（可选）需 `pip install "rembg[cpu,cli]"`

```bash
python scripts/wordcloud_gen.py --input data.json --shape heart --output out.png
```

`--input` 支持两种格式：
- `.json`：`[{"word","weight","category"?}]`，或 `{词: 权重}`，或 `{词: {weight, category}}`
- `.txt`：原始文本，自动分词计数（有 jieba 用 jieba，否则正则切分）

`.txt` 模式的进阶参数（`.json` 模式不生效，因为词是用户显式给出的，不过滤）：
- `--stopwords 停用词.txt`：每行一个词，分词后剔除（滤掉"我们/没有/因为"这类双字以上虚词——单字虚词如"的/了"已自动过滤）；自动合并 wordcloud 内置英文停用词。
- `--userdict 词典.txt`：jieba 自定义词典（每行 `词 词频 词性`），让"中国特色社会主义"这类专有名词不被切碎。

```bash
# 原始文本 → 爱心词云（过滤虚词 + 保留专有名词）
python scripts/wordcloud_gen.py --input speech.txt --shape heart \
  --stopwords stopwords.txt --userdict userdict.txt --output out.png
```

`--shape`：内置 14 种模板，无需外部图片：

| 类别 | 形状 | 说明 |
|------|------|------|
| **基础** | `heart` / `circle` / `star` | 爱心、圆形、五角星 |
| **几何** | `diamond` / `triangle` / `pentagon` / `hexagon` | 菱形、三角形、正五边形、正六边形 |
| **图标** | `ring` / `cloud` / `drop` / `arrow` | 圆环、云朵、水滴、向上箭头 |
| **文字蒙版** | `text` + `--text "中国"` | 文字即形状（微词云「自定义文字」），中文/英文皆可，1~3 字最佳 |
| **矩形** | `rect` + `--width 16 --height 9` | PPT 比例矩形（16:9 等） |
| **自定义** | `custom` + `--mask 图片.png` | 任意图片蒙版（白底黑形/黑底白形/透明 PNG 均可，自动判断朝向） |

> **中文文字蒙版警告**
> CJK 字符笔画细、字内空白多，1000×1000px 蒙版下笔画宽度仅 8–40px，词云只能填入
> 极小的词（font-size 2–6），笔画区覆盖率极限 ~50% 且仅为细小杂点。
> `fill_holes=True` 会把字内空白也填没，四字变四块实心方块，认不出原字。
> **中文场景推荐用「品牌大字」模式**（见下）而非文字蒙版。

其它常用参数：`--colors cat.json`（类别→[r,g,b]）、`--colormap viridis`、
`--background white|black|transparent|任意颜色`、`--min-font 6`、`--max-font 100`、
`--repeat/--no-repeat`、`--title "说明文字"`、`--font 字体路径`。

### 品牌大字模式（中文品牌词云推荐方案）

当需要突出"德恒无锡""腾讯""阿里巴巴"等中文品牌名时，**不要用文字蒙版**（CJK 文字
蒙版物理上限详见 [references/wordcloud-principles.md 第 11 节](references/wordcloud-principles.md)）。

**正确做法**：把品牌名作为权重碾压级的词，用 `rect` 或 `circle` 做无蒙版密集云：

```bash
# 1. 在 JSON 里让品牌名权重 > 400（其他词 10–30）
#    品牌名自动成为最大最突出的视觉锚点
[
  {"word": "德恒无锡", "weight": 600, "category": "品牌"},
  {"word": "跨境投资与并购", "weight": 30, "category": "涉外优势"},
  ...
]

# 2. 纯白底、高密度、品牌红
python scripts/wordcloud_gen.py \
  --input brand.json --shape rect \
  --colors categories.json \
  --min-font 2 --max-font 140 --max-words 3000 \
  --background white --repeat \
  --output brand-cloud.png
```

**效果对比**：
| 方案 | 四字可见 | 版面密度 | 推荐 |
|------|---------|---------|------|
| 文字蒙版 `--shape text --text "德恒无锡"` | ❌ 糊成一团 | ~20% | 不推荐 CJK |
| 自定义蒙版 `--shape custom --mask 图片` | ❌ 看运气 | ~30% | 仅英文推荐 |
| **品牌大字 `--shape rect` + 高权重** | ✅ 清晰可读 | ~35% | **推荐（CJK）** |
| 圆形 `--shape circle` + 高权重 | ✅ 清晰可读 | ~30% | 推荐 |

- **背景**：中国品牌物料优先用**纯白底**（`--background white`）。深色底适合科技/娱乐场景，
  律师/企业/政府物料以白底为准。
- **蒙版朝向（`--shape custom` 时）**：`--mask-mode auto|light|dark|alpha`，默认 `auto` 自动判断图片朝向（见上）。`light`=浅底深形，`dark`=深底浅形，`alpha`=透明 PNG 以不透明区为形。仅当自动判错才手动指定。
- **照片自动抠图（`--auto-cutout`）**：给一张**普通照片**（人物/物品，背景杂乱）而不是干净剪影时，加 `--auto-cutout` 让脚本先用 rembg 自动抠成透明 PNG，再当蒙版——一步到位。`rembg` 未安装时自动警告并退回原图。首次运行会下载模型（~170MB，缓存在 `~/.u2net`）。
- **`--colors` 的生效前提**：仅当数据带 `category` 字段时才按类别上色；数据无 `category` 时该参数被忽略，改由 `--colormap` 按词序取色。
- **输入容错**：缺 `word`、非数字 `weight`、非正 `weight` 的条目会被自动跳过并打印警告，不会中断整个生成；全无效时给出 "no words found"。
- **`--colormap` 非法**：自动回退到 `tab10` 并警告，不会崩。
- **命名主题（`--theme`，微词云「主题」）**：11 种预设配色方案，一键切换风格。
  有分类数据时覆盖类别调色板；无分类时覆盖 colormap。

  | 主题 | 风格 | 适用场景 |
  |------|------|----------|
  | `rainbow` | 彩虹渐变 | 节日、活泼 |
  | `warm` / `sunset` | 暖色/日落 | 庆典、年终 |
  | `cool` / `ocean` | 冷色/海洋 | 商务、专业 |
  | `forest` | 森林绿 | 环保、自然 |
  | `festive` | 多彩撞色 | 节日海报 |
  | `mono` | 灰度单色 | 报告、论文 |
  | `business` | 商务蓝 | 企业报告 |
  | `lucky` | 中国红金 | 春节、庆典 |

- **中英文双语（`--lang`）**：
  - `auto`（默认）：jieba 分词（中文+英文混合文本都能处理），同时过滤中文停用词 + 英文停用词
  - `zh`：强制中文模式，加载中文停用词（的/了/是/在/因为 等 ~80 个高频虚词）
  - `en`：英文正则分词 + 自动小写化 + 英文停用词过滤（适合纯英文文本）
  - `.json` 模式不受影响（用户显式列出的每个词都保留）

## 示例

**文字蒙版（中文"中国" + lucky 主题）：**
```bash
python scripts/wordcloud_gen.py \
  --input data.json --shape text --text "中国" \
  --theme lucky --output wordcloud-china.png
```

**英文圆形词云（lang=en 自动小写）：**
```bash
python scripts/wordcloud_gen.py \
  --input speech.txt --shape circle --lang en \
  --theme ocean --output wordcloud-en.png
```

**PPT 16:9 矩形模板（报告关键词云）：**
```bash
python scripts/wordcloud_gen.py \
  --input report.json --shape rect --width 16 --height 9 \
  --theme business --output wordcloud-ppt.png
```

**照片抠图 → 词云（一步到位）：**
```bash
python scripts/wordcloud_gen.py \
  --input data.json --shape custom \
  --mask 人物照片.jpg --auto-cutout \
  --theme warm --output wordcloud-photo.png
```

复刻本次 53 国爱心词云（欧洲蓝/亚太绿/美洲红/中东深蓝/其他灰）：

## 示例

复刻本次 53 国爱心词云（欧洲蓝/亚太绿/美洲红/中东深蓝/其他灰）：

```bash
python scripts/wordcloud_gen.py \
  --input references/example-53countries.json \
  --shape heart --repeat \
  --output wordcloud-heart-53countries.png \
  --title "Cross-Border Compliance · 可查法域 53 国"
```

# 照片一键抠图成词云：--auto-cutout 让 rembg 先把背景去掉
python scripts/wordcloud_gen.py \
  --input data.json --shape custom \
  --mask 人物照片.jpg --auto-cutout \
  --output wordcloud-photo.png


## 深入

蒙版语义的源码级证据、形状生成数学、配色与密度调参、以及"如何程序化校验
成品是不是实心形状"，见 [references/wordcloud-principles.md](references/wordcloud-principles.md)。

<!-- © 2024-2026 陆凌燕（北京德恒（无锡）律师事务所）. Licensed under MIT. -->
