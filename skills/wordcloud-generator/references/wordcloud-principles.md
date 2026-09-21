<!-- Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm. -->

# 词云图第一性原理 · 深度参考

本文件是 `wordcloud-generator` 技能的底层认知沉淀。面向需要改脚本、排查怪现象、
或理解"为什么这么写"的场景。

## 目录
1. 词云的本质：一个约束布局问题
2. 蒙版语义反直觉（核心坑，含源码证据）
3. 形状蒙版怎么生成（14 种内置模板 + 自定义图片）
4. 配色：类别调色板 / colormap / 命名主题
5. 密度控制：repeat 与字号
6. 程序化校验成品
7. 背景模式（透明/深色/自定色）
8. 照片自动抠图：rembg 集成
9. 文字蒙版（text-as-mask，微词云「自定义文字」）
10. 中英文双语支持
11. CJK 文字蒙版物理上限（德恒无锡实测）

---

## 1. 词云的本质：一个约束布局问题

词云 = 在画布上放置一组词，满足：
- 字号 ∝ 权重（词频/重要性）
- 词之间不重叠
- （可选）词只能落在蒙版允许的区域内

`wordcloud` 库的布局算法：按权重从大到小，每个词从中心开始螺旋向外找第一个
能放下的空位。所以大词占据中心，小词填充边缘——这天然给出"视觉重心"。

蒙版不改变字号逻辑，只改变"允许落子的棋盘"。

## 2. 蒙版语义反直觉（核心坑，含源码证据）

**错误直觉**：`mask==255` 的地方是形状内部，词应该填进去。
**实际行为**：词落在 `mask==0` 的地方。

源码证据（wordcloud 1.9.x，`wordcloud.py`）：

```python
# _get_bolean_mask：True 当且仅当像素 == 255
boolean_mask = mask == 255          # 形状内部(255) -> True

# _generate 内部：把蒙版当基线偏移叠加到"已画区域"上
img_array = np.asarray(img_grey) + boolean_mask   # 形状内部凭空 +1
occupancy.update(img_array, x, y)
```

采样器 `sample_position` 找"累积占用最低"的框。因为形状内部被 `+1` 基线抬了一截，
反而比外部（基线 0）更"满"，于是词优先落进基线为 0 的外部区域。

**纠正规则（写进脚本的 `_filled_to_mask`）**：
传入"形状内部=True"的布尔网格后，必须做 `mask = (~filled) * 255`，
即**内部 0、外部 255**。这样词才会填进形状。

> 验证实验：同义词云，圆形蒙版(255在内部)→ 词 0% 在内部；反之为(0在内部)→
> 词 25%+ 在内部、外部 0%。详见主对话 2026-08-06 排障记录。

## 3. 形状蒙版怎么生成

统一约定：先得到 `filled`（形状内部=True 的布尔网格），再 `_filled_to_mask`
转成 wordcloud 需要的 `内部0/外部255`。

### 基础形状
- **爱心**（参数方程，无需外部依赖）：
  ```
  x = 16 sin³t
  y = 13 cos t − 5 cos2t − 2 cos3t − cos4t
  ```
  归一化到 [0,1] 后留 5% 边距；**y 轴要翻转**（`(1−y)*size`），让两个圆瓣朝上。
  用 `matplotlib.path.Path.contains_points` 判定网格点是否在多边形内。
- **圆形**：`(X−cx)²+(Y−cy)² ≤ r²`，r = size×0.46。
- **星形**：内外半径交替的多边形顶点（ratio=0.45），`contains_points` 判定。

### 几何形状（正 n 边形）
- **菱形 / 三角形 / 五边形 / 六边形**：共用 `make_polygon_mask(n_sides, rot)`，
  通过 `MPath.contains_points` 判定点是否在正 n 边形内。默认 rot=π/2 使一个顶点朝上。

### 图标形状（向量谓词光栅化）
- **圆环 (ring)**：外圆 r=size×0.46 减去内圆 r×0.55 的环形区域。
- **云朵 (cloud)**：6 个重叠圆形的并集 + 底部截断（ny≤0.82），模拟云的蓬松感。
- **水滴 (drop)**：底部圆（中心(0.5,0.45), r=0.30）+ 顶部三角形（顶点(0.5,0.95),
  底边(0.2,0.45)-(0.8,0.45)）的并集。用符号叉积做向量化的点在三角形内判定。
- **箭头 (arrow)**：向上箭头 = 矩形杆部(y∈[0.10,0.55], x∈[0.38,0.62]) +
  三角头部(y∈[0.55,0.92], 宽度线性收缩到顶点)。

### 特殊模板
- **矩形 (rect)**：按 `--width/--height` 比例画居中矩形，用于 PPT 尺寸（如 16:9）。
  大边映射到可用区域(size×90%)，小边等比缩放。
- **文字蒙版 (text)**：用 PIL 渲染文字为黑色、白底灰度图 → `gray<128` 为形状内部。
  字号自动缩放至画布 80% 以内；支持中文（CJK 字体）和英文（同一字体含 Latin）。
  详见第 9 节。

### 自定义图片（智能读图）
- **自定义图片**：不再要求用户手动准备"黑底白形"。`make_custom_mask`
  自动判朝向：
  - 透明 PNG（alpha 通道存在且有半透明/透明像素）→ 不透明区 = 形状；
  - 不透明图 → 取四角亮度中位数当背景代理：四角亮则"深像素=形状"（`gray<128`），
    四角暗则"浅像素=形状"（`gray>128`）；
  - 仍统一 `_filled_to_mask` 反相成"内部0/外部255"。
  `--mask-mode light|dark|alpha` 可强制朝向，应对自动判错的复杂背景照片。

## 4. 配色：类别调色板 / colormap / 命名主题

`color_func(word, font_size, position, orientation, random_state)` 在每个词绘制时
被调用，返回 (r,g,b)。

- 词带 `category` → 用类别调色板（如欧洲蓝/亚太绿…），对每个词固定基色 + 小抖动
  （±18）增加层次。
- 无类别 → 用 matplotlib colormap 按词序均匀取色；或统一深灰。
- 自定义类别色：`--colors cat.json` = `{"欧洲":[65,105,225], ...}`。

### 命名主题 (`--theme`)
11 种预设配色方案，一键切换风格。实现为 `THEMES` 字典：
```python
THEMES = {
    "rainbow": ("gist_rainbow", None),   # colormap only
    "warm":     ("autumn", None),
    "cool":     ("cool", None),
    "ocean":    ("winter", None),
    "forest":   ("summer", None),
    "sunset":   ("plasma", None),
    "festive":  ("Set1", None),
    "mono":     ("Greys", None),
    "business": (None, { ... }),          # category palette only
    "lucky":    (None, { ... }),
}
```
值 = `(colormap_name | None, category_palette | None)`。有分类数据时 palette 覆盖
DEFAULT_PALETTE；无分类数据时 colormap 覆盖 `--colormap` 默认值。两者可同时提供。

## 5. 密度控制：repeat 与字号

词云不是实心色块，文字间必有留白。让形状"看起来被字铺满"：

- `repeat=True`：词不够时，按权重递减重复绘制，小字补空隙。52 个词可填到 ~33%。
- `min_font_size=6`：允许更小的填充字。
- `max_font_size`：最大词字号（视觉锚点）。
- `relative_scaling=0.32`：权重对字号的影响占比（低→大小更均匀，高→头部更突出）。

权衡：repeat 越高越满但同词重复多；追求"干净学术感"可关 repeat、接受稍疏。

## 6. 程序化校验成品

无法肉眼看图时，用 `wc.to_array()`（渲染数组，与蒙版同坐标系）比对：

```python
arr = wc.to_array()                       # (H,W,3) RGB, 背景白
mask_big = resize(mask, arr.shape[::-1]) # 蒙版缩放到渲染分辨率
filled = mask_big == 0                    # 形状内部
text   = (arr < 240).any(axis=-1)        # 非白 = 有字
inside  = text[filled].mean()             # 应 > 0.30
outside = text[~filled].mean()            # 应 ≈ 0
```

`inside>30% 且 outside≈0` 即判定为"实心形状、背景干净"。

> **校验法的背景依赖**：上面的 `arr<240` 判据只适用于**白底**。透明/深色背景时
> 背景像素本身 <240（透明底全黑、黑底也暗），会误判为"满屏是字"。
> - 透明背景：应直接读 PNG 的 alpha 通道（`Image.open(png).split()[3]`），有
>   `alpha<255` 的像素即透明生效。
> - 深色背景：用"亮像素"判据（`img.max(axis=-1) > 60`）代表文字。
> 另外 `wc.to_array()` 始终返回 RGB、**不含 alpha**，透明性只能在最终 PNG 上验证。

## 7. 背景模式（透明/深色/自定色）

`WordCloud(background_color=...)` 不接受字符串 `"transparent"`，透明需用
`background_color=None` + `mode="RGBA"`，且 matplotlib 的 `savefig` 必须
`transparent=True` 并显式 `fig.patch.set_alpha(0); ax.patch.set_alpha(0)`，
否则 figure 默认白底会把透明区填白。深色/自定色则用 `facecolor=<颜色>` 且不透明。

依赖：`pip install wordcloud matplotlib numpy pillow jieba`（照片自动抠图可选加 `rembg[cpu,cli]`）
中文字体：脚本自动探测 PingFang/STHeiti/Hiragino 等，缺失会警告（词可能变方框）。
Python 要求：>=3.11,<3.14（受 rembg 限制；不含 rembg 时 >=3.8 即可）。

## 8. 照片自动抠图：rembg 集成

普通照片（人物/物品，背景杂乱）不能直接当蒙版——`make_custom_mask` 的灰度二值化
会被复杂背景糊掉。集成 [rembg](https://github.com/danielgatis/rembg)（纯本地、MIT，
输出透明 PNG）后，可一键把照片转成干净剪影再当蒙版。

- 加 `--auto-cutout` 即触发。脚本逻辑（`main()` 内）：
  1. 若源图**已有透明度**（透明 PNG 剪影）→ 直接当蒙版，跳过抠图；
  2. 否则 `from rembg import remove; remove(Image.open(path).convert("RGB"))`
     → 得到透明 PNG，临时落盘，`--mask-mode` 强制 `alpha`；抠图报错则警告并退回原图；
  3. `rembg` 未安装 → 警告并退回原图，不中断。
- 临时抠图文件用完即删（`tmp_mask_path`），不留垃圾。
- 首次运行自动下载 u2net 模型（~170MB），缓存在 `~/.u2net`，之后本地复用。
  中国大陆若下载慢/失败，可给 `U2NET_HOME` 指向已下好的模型目录，或换镜像源。
- 跨平台：macOS（Apple Silicon 走 onnxruntime 原生 arm64，CPU）、Windows（x64，CPU；
  N 卡可加 CUDA）均可用。要求 Python >=3.11,<3.14。
- 安装：`pip install "rembg[cpu,cli]"`（与脚本同处受管 venv，不污染本机）。

## 9. 文字蒙版（text-as-mask，微词云「自定义文字」）

**核心能力**：把一段文字（中文或英文）渲染成蒙版形状，词云填进文字轮廓内。
这是微词云最标志性的功能之一（"自定义文字/字母"，建议 1~3 个字）。

### 实现流程 (`make_text_mask`)
1. 创建 size×size 白底灰度图 (`Image.new("L", ..., 255)`)。
2. 加载字体：优先用 `find_chinese_font()` 返回的 CJK 字体（PingFang 等），
   该字体同时包含 Latin 字形 → 中文英文都能正确渲染。字体缺失时回退 PIL 默认字体（仅英文）。
3. **字号自适应**：从 `size×0.90` 开始，用 `textbbox` 测量文字尺寸；
   若超出画布 80% 可用区域则等比缩小。保证文字居中且不溢出。
4. 用黑色 (`fill=0`) 在白底上绘制居中文字。
5. `gray < 128` → 形状内部布尔网格 → `_filled_to_mask` 反相。

### 使用
```bash
# 中文文字蒙版
python scripts/wordcloud_gen.py --input data.json --shape text --text "中国" \
  --theme lucky --output china.png

# 英文文字蒙版
python scripts/wordcloud_gen.py --input data.json --shape text --text "LOVE" \
  --theme warm --output love.png
```

### 注意事项
- 字数越多字号越小；1~3 字效果最佳（微词云经验值）。超过 5 个字的文字会很小，
  建议拆成多张拼合。
- CJK 字体对中英文都有效；纯英文环境也可指定英文字体路径 `--font`。
- 文字蒙版的内部覆盖率较低（~5~10%），因为笔画本身占画布比例小——这是正常的，
  词云只落在笔画区域内。

## 10. 中英文双语支持

### 分词策略 (`count_text`, 受 `--lang` 控制)

| 模式 | 分词器 | 停用词 | 小写化 | 适用场景 |
|------|--------|--------|--------|----------|
| `auto`（默认） | jieba（若可用） | EN STOPWORDS + CN_STOPWORDS | 否 | 中英混合文本 |
| `zh` | jieba | EN + CN 停用词 | 否 | 纯中文 |
| `en` | 正则 `[A-Za-z]+` | 仅 EN STOPWORDS | 是 | 纯英文 |

### 中文停用词表 (`CN_STOPWORDS`)
内置 ~80 个高频虚词（的/了/和/是/在/我/有/就/不/人/都/一/一个/上/也/
很/到/说/要/去/你/会/着/没有/看/好/自己/这/那/与/及/我们/你们/他们/
她们/它们/这个/那个/这些/那些/因为/所以/如果/但是/而且/然后/已经/可以/
应该/需要/通过/对于/关于/以及/或者/这种/那种/一些/这样/那样/什么/怎么/
为什么/一个/一种/进行/成为/由于/根据/按照），仅作用于 `.txt` 模式。

### `.json` 模式不受影响
JSON 模式用户显式列出每个词及其权重，脚本不做分词、不过滤停用词，
因此 `--lang` 对 JSON 无效（也不应生效——用户给的词就是最终词集）。

### 字体兼容性
`find_chinese_font()` 探测的系统字体（PingFang / STHeiti / Hiragino / Songti / NotoSansCJK）
均包含完整 CJK + Latin 字形集。同一字体文件可同时渲染中文和英文单词，
无需为不同语言切换字体。

## 11. CJK 文字蒙版物理上限（德恒无锡实测，2026-08-07）

### 问题陈述

用户要求"把德恒无锡四个字做成词云"——即文字蒙版法：用文字笔画作蒙版，词填进笔画内。
经过 15+ 轮迭代验证，此法对 CJK 四字在工程上**不可行**。

### 物理约束

```
词云蒙版尺寸（脚本固定值）: 1000 × 1000 px
"德恒无锡" 四字渲染区域（font_scale=0.95）: 约 950 × 250 px
每个字宽度: 约 237 px
每个字笔画宽度（膨胀前）: 8–30 px
经过 binary_dilation(iterations=16) 后笔画宽度: 40–100 px

词的最小包围盒:
  font_size=2   →  ~6×14 px  (能塞进笔画)
  font_size=10  →  ~30×70 px (笔画勉强塞得下)
  font_size=20  →  ~60×140 px (笔画塞不下)
  font_size=60  →  ~180×420 px (远超笔画宽度)
```

**结论**：笔画区只能容纳 font_size≤10 的极小词。在 ~105 个输入词中，
至少 80% 因字号过大而无法落进笔画区，导致笔画区覆盖率天花板约 50%，
且剩余可落子的全是 2–6 号小词，视觉上呈"彩色碎点"而非"文字形状"。

### 实测数据（德恒无锡，多次迭代平均）

| 参数 | 膨胀=12, no fill | 膨胀=18, no fill | 膨胀=22, fill_holes |
|------|----------|-----------|-------------|
| 蒙版填充率 | 35.2% | 38.8% | 47.3% |
| 笔画区文字覆盖率 | 11.7% | 48.6% | 49.3% |
| 四字可辨认 | ❌ 太稀 | ❌ 彩色碎点 | ❌ 四块方块 |
| "锡"字两撇 | 不可见 | 不可见 | N/A（字已成方块）|

### fill_holes 的破坏性

`binary_fill_holes(thick)` 会把字内封闭空白区填满：
- "德"的心底下方空间 → 消失 → 德变完整方块
- "恒"的一与亙之间的空隙 → 消失 → 恒变方块
- "无"的字内自然空隙 → 消失 → 无变方块
- "锡"的日字内部 → 消失 → 锡变方块

结果：四个**实心方块**，认不出是"德恒无锡"。虽然在技术指标上（蒙版填充率 47%，
覆盖 49%）"不错"，但从**认读角度**已完全失败。

### 为什么英文可以

- "LOVE"：每个字母结构简单、笔画粗、内部几乎无封闭空白区
- "IBM"：sans-serif 块状字母、3 个字符、无中文式复杂内部结构
- 以上字母即使 fill_holes 后，字形轮廓仍能认出原字母

对照：CJK 字符同时要求**笔画区分**（如"土"与"士"）和**结构辨识**（如"德"与"得"），
这两点恰好是 fill_holes 所摧毁的。

### 正确的 CJK 品牌词云做法

不用文字蒙版，用"品牌大字"模式：

1. JSON 中将品牌名设为 400–600 权重（其他词 10–30）
2. 用 `--shape rect` 或 `--shape circle` 铺满画布
3. 纯白底（`--background white`）
4. 品牌名自动成为最大最突出的词（可读），其余词密集填充四周

```bash
python scripts/wordcloud_gen.py \
  --input brand.json --shape rect \
  --colors categories.json \
  --min-font 2 --max-font 140 --max-words 3000 \
  --background white --repeat \
  --output brand-cloud.png
```

### 教训沉淀

这条教训来自 2026-08-07 德恒无锡项目 15+ 轮迭代，耗时数小时：
- **不要假设英文字母蒙版经验适用于 CJK**。
- 文字蒙版仅适合 1–3 个字母（英文首字母缩写）或极粗体数字。
- 遇到"中文品牌名词云"需求，直接引导用户选品牌大字模式。
- `fill_holes=True` 是 CJK 文字蒙版的"终极自杀按钮"——字的结构辨识完全丧失。
- 深色底 + 外部水印的合成中，前景背景色会盖住水印，需要额外透明化处理。
