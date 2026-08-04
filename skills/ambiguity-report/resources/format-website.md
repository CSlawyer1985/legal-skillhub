# 格式——网站（多页面或单页面）

网站渲染器是默认格式。它生成可在本地打开或上传到 Netlify、Vercel、GitHub Pages 或任何静态托管的完整静态网站。

## 两种模式

**多页面（默认）。** 一个链接 HTML 页面文件夹加一个共享的 `style.css`。每个场景都有自己的可引用 URL。适合读者会回访、通过链接分享或逐页打印的参考网站。

```
site/
├── index.html              # Overview + scenario grid
├── statute.html            # Annotated source text
├── scenario-1.html ... scenario-N.html
├── families.html           # Pedagogical defect-family page
├── redrafts.html           # Amendment package
├── methods.html            # Methodology
├── style.css
└── netlify.toml            # Static publish config
```

**单页面。** 一个自包含的 HTML 文件，所有内容通过 JavaScript 交叉链接。左侧粘性法规面板，右侧场景，点击过滤、锚点标签跳转到法规。适合仪表板视图或单个可分享文件。

```
site/
├── index.html              # Self-contained, all-in-one
└── netlify.toml
```

## 调用

```bash
python scripts/generate_site.py \
  --spec <output-dir>/spec.json \
  --out <output-dir>/site \
  --mode multi
```

标志：
- `--spec`：标准规范 JSON 的路径。
- `--out`：生成网站的目标目录。脚本在需要时创建它。
- `--mode`：`multi`（默认）或 `single`。
- `--no-netlify-toml`：如果用户部署到其他地方，跳过 netlify.toml 存根。

该脚本是纯 Python，无外部依赖。使用系统 Python 运行。

## 设计

默认调色板为暖奶油色 + 焦赭色强调。两个对抗面板为板岩蓝（立场 A）和焦赭色（立场 B）。缺陷类别有固定的柔和粉彩调色板。全部可通过规范中的 `design` 块覆盖——见 `data-format.md`。

字体从 Google Fonts 加载：Fraunces（展示）、Inter（界面）、Crimson Pro（衬线正文）。如果部署目标屏蔽外部字体，用户可通过 `design.primary_font`、`design.body_font`、`design.serif_font` 替换并提供自己的字体栈。

## 多页面网站包含什么

**`index.html`** — 概览。带标题和副标题的英雄区、简短引导、场景卡片网格（每个显示编号 + 标题 + 标签行 + 锚点标签 + 类别标签），以及指向主要章节的方块链接。

**`statute.html`** — 源文本作为主要制品渲染。每个可寻址单元是一个带样式的块；被场景锚定的条款获得链接到这些场景的编号徽章。右侧栏"目录"列出所有场景。

**`scenario-N.html`** — 每个场景一个。面包屑、英雄区（编号 + 标题 + 标签行 + 元标签）、情境块、双立场面板（立场 A 对立场 B，带主体名）、分析卡（弱点 + 可能结果）、改写文本醒目框、"锚定于源文本"摘录块、"相关场景"列表（共享类别或锚点的其他场景）以及上一页/下一页导航。

**`families.html`** — 教学式分类。场景中出现的每个缺陷类别都有自己的块，含描述、诊断测试和使用它的场景。

**`redrafts.html`** — 每个拟议修改作为立法修改制品集中收集。每个改写文本块显示问题陈述、以斜体法条语言呈现的提案文本，以及链接回其来源场景。

**`methods.html`** — 方法论、解释规则过滤器、范围说明、额外标记歧义点的覆盖清单。

## 单页面网站包含什么

内容相同，装饰不同。法规面板在宽屏上粘性固定。场景为堆叠卡片。顶部过滤栏切换缺陷类别。锚点标签和徽章按钮通过滚动加高亮交叉链接，而非导航。

JavaScript 内联且自包含——除字体外无外部库。

## 部署到 Netlify

两条路径：

1. **拖放（Netlify Drop）。** 打开 `https://app.netlify.com/drop` 并将 `site/` 文件夹拖到其上。Netlify 在随机子域创建一个免费网站。多页面和单页面模式均适用。
2. **Git 支持部署。** 将 `site/` 文件夹推送到 GitHub 仓库，将 Netlify 链接到该仓库。随附的 `netlify.toml` 将发布目录声明为 `.`，因此 Netlify 直接找到 HTML。

生成的 `netlify.toml` 很精简：

```toml
[build]
  publish = "."

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "SAMEORIGIN"
    X-Content-Type-Options = "nosniff"
```

如果用户想要自定义域名，在部署后在 Netlify 中配置。

## 常见定制

**品牌覆盖。** "使用我们律所的颜色"：
- 将 `design.accent_color` 设置为品牌红/蓝/绿。
- 将 `design.dept_color` 设置为互补的板岩色。
- 将 `design.background_color` 保持奶油色，或者如果律所偏好更冷的观感则设为白色。

**章节名称。** 如果审查针对的是合同（而非法规），用户可能希望重命名导航中的章节：
- "The Statute" → "The Contract"（只改页面链接文本）
- "The Seven Fights" → "The N Issues" 或 "Disputes" 或任何合适的名称

这些目前不受规范控制（标签存在于渲染器中）。未来工作：在 `meta` 中公开导航标签。

**字体替换。** 上传到无外部字体 CDN 访问权限网站的用户可以用系统字体替换 Fraunces / Inter / Crimson Pro。添加到规范：
```json
"design": {
  "primary_font": "Georgia",
  "body_font": "-apple-system, system-ui, sans-serif",
  "serif_font": "Charter, Georgia"
}
```

脚本仅在字体名称看起来像 Google Fonts 候选（CamelCase 单一名称）时才生成 font-face 声明；否则依赖系统字体可用性。

## 语气校准

索引、类别、改写文本和方法页面上的默认引导文案务实而非装饰。如果用户想要更具文学性的文案（"接缝"、"对抗"、"承重"），`meta.page_subtitle` 可以设置为该风格，渲染器会遵循。对于学术受众，考虑收紧为更平实、更干练的散文；渲染器不强加风格。

## 本地测试输出

生成后：

```bash
cd <output-dir>/site
python -m http.server 8000
# open http://localhost:8000
```

这在本地提供网站服务，并确保所有相对链接可解析。打开开发者工具的网络选项卡确认没有 404。
