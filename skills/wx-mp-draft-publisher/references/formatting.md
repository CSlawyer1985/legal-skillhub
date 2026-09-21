<!-- Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm. -->
# WeChat Publisher — Formatting Specifications

## Reference Article

All formatting is based on the reference WeChat article:
`https://mp.weixin.qq.com/s/jBo8mR2asNwWJXH8hsexsQ`

Verified via browser `window.getComputedStyle()` on `#js_content > p`.

## Typography

### Paragraph (body text)

```css
font-family: "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif;
font-size: 15px;
color: #333;
line-height: 2.0;   /* 2em × 15px */
margin: 13px 8px;   /* top/bottom: 13px, left/right: 8px */
padding: 0;
white-space: normal;
box-sizing: border-box;
```

### Bold text

```css
font-size: 15px;     /* same as body */
font-weight: 700;    /* bold */
color: #333;         /* same as body */
```

No size or color change — only weight differs from body text.

**标题加粗的识别（重要）**：标题的加粗不一定写在 run 级。WPS / 部分生成器的 docx 用**自定义段落样式**（`heading 1/2/3`）表达标题——`<w:pStyle w:val="000046"/>` 之类随机字符串 ID，`styles.xml` 里对应 `<w:name w:val="heading 1"/>`，run 级无 `<w:b>`，加粗靠段落样式继承。若脚本只扫 run 级 `<w:b>` 或只认数字 pStyle ID，这类标题会整片丢失加粗。

诊断时务必**同时查 `word/styles.xml`**：按 `w:styleId` 找到对应 `<w:name>`，确认是否含 `heading`。判定规则见 `publish.js` 的 `headingStyleIds` 映射（`isHeadingStyle` 兼容数字 ID 与自定义字符串 ID 两类）。交叉验证可用 mammoth 的 `convertToHtml`（会输出 `<h1>/<h2>/<h3>`）。

### Images

```html
<p style="text-align:center;margin:13px 0;">
  <img src="{cdn_url}" style="max-width:100%;display:inline-block;" />
</p>
```

No left/right margin on images to keep them full-width.

### Container (outer wrapper — not used in current approach)

The reference page's `rich_media_area_primary_inner` is centered with:
- `width: 677px`
- `margin: 0 auto` (page-level centering by WeChat)

Individual `<p>` tags have `margin: 13px 8px` — both paragraph spacing and side spacing come from this single property. No outer container wrapper is needed.

## Brand Palette & Decorative Styles（金色左划线标题 + 深蓝表头）

为对齐"权威 + 高级"的律所品牌调性，文章统一使用以下色板（定义在 `publish.js` 顶部常量，严禁文章内散落 magic color）：

| 角色 | 常量 | 色值 | 用途 |
|------|------|------|------|
| 金 | `GOLD` | `#C9A227` | 标题左划线金条 |
| 深蓝 | `DEEP_BLUE` | `#1A3A6B` | 表头底色 |
| 深蓝边 | `DEEP_BLUE_BORDER` | `#15335c` | 表头边框 |
| 斑马纹 | `ZEBRA` | `#F4F6FA` | 表格数据行交替底色（浅） |
| 表格细边 | `TABLE_BORDER` | `#e6e6e6` | 表格单元格边框（浅灰） |

### Titles — 金色左划线

所有标题段落（大标题 paraIndex===1 / `isHeadingStyle` 自定义 heading / `isCnChapter` 中文「一、二、三」式章节且无 heading 样式）统一加：

```css
border-left: 3px solid #C9A227;   /* 金条：细而克制 */
padding-left: 10px;
```

普通正文段落**不加**金条。金线细（3px）+ 留白足 → 显高级；切勿粗金条满铺（会变"营销/喜庆感"）。

### Table — 深蓝表头 + 斑马纹

docx `<w:tbl>` 由 `parseTable()` 渲染（v1.3.0 起，旧版整段丢弃）。markdown 由 `styleMarkdownHTML()` 渲染。两者统一规范：

- **表头（首行）**：深蓝底 `#1A3A6B` + 白字 `#ffffff` + 加粗 `700` + 居中
- **数据行**：斑马纹交替 —— 奇数行 `#F4F6FA`、偶数行 `#ffffff`
- **单元格**：细灰边 `1px solid #e6e6e6` + `padding:8px 10px` + `vertical-align:top`（数据）/ `middle`（表头）
- 表格整体：`border-collapse:collapse; width:100%; margin:13px 0; font-size:13px`

```html
<!-- 表头行 -->
<tr style="background:#1A3A6B;">
  <th style="border:1px solid #15335c;padding:8px 10px;text-align:center;color:#ffffff;font-weight:700;font-size:13px;vertical-align:middle">检索方式</th>
</tr>
<!-- 数据行（斑马纹） -->
<tr style="background:#F4F6FA;">
  <td style="border:1px solid #e6e6e6;padding:8px 10px;text-align:left;color:#333;font-size:13px;vertical-align:top">MCP 检索</td>
</tr>
```

> 约定：表格**首行即表头**。无表头行时首行仍会被染深蓝，需在后台手动去色或约定首行为表头。图片在表格单元格内暂不渲染（仅取文本）。

## Image Processing

Applied by `preprocessImage()` using `sharp`:

```javascript
// In publish.js
preprocessImage(inputPath) {
  1. Read image with sharp
  2. Resize: max width 1080px (maintain aspect ratio)
  3. Rounded corners: use composite with rounded SVG mask (max radius 10px, or
     Math.min(10, width/height * 0.02))
  4. Drop shadow: composite with blurred SVG shadow (blur σ=6, opacity 10%)
  5. Format: match original (png/jpeg)
  6. Output: {inputPath}_processed.{ext}
}
```

## WeChat API

- **Base URL**: `https://api.weixin.qq.com/cgi-bin/`
- **Image upload**: `POST /cgi-bin/media/uploadimg?access_token={token}`
- **Draft create**: `POST /cgi-bin/draft/add?access_token={token}`
- **Draft update**: `POST /cgi-bin/draft/update?access_token={token}`
- **Draft list**: `POST /cgi-bin/draft/batchget?access_token={token}`
- **Draft delete**: `POST /cgi-bin/draft/delete?access_token={token}`

All requests use JSON payloads with `Content-Type: application/json; charset=utf-8`.
Image uploads use `multipart/form-data`.

### Required draft fields

```json
{
  "title": "文章标题 (max 64 chars)",
  "author": "{{发布者署名}}（取 WECHAT_AUTHOR 环境变量，未配置则留空）",
  "digest": "摘要 (title truncated to 54 chars)",
  "content": "完整 HTML 正文",
  "content_source_url": "",
  "thumb_media_id": "封面图片 media_id (required!)",
  "need_open_comment": 1,
  "only_fans_can_comment": 0
}
```

## Draft Management

The script uses an **atomic update** strategy for duplicates (since v1.4.0, see troubleshooting.md 坑位 5):
1. Before creating, search existing drafts by title (`batchget` + filter)
2. If a match is found, call `draft/update` **in place** with the returned `{ media_id, index }` — 旧稿保留，无丢稿窗口
3. If no match, call `draft/add` to create new

> ⚠️ 严禁 delete-then-create：旧版先 `deleteDraft` 再 `_createDraft`，中间窗口若新建失败（限流/超限/网络）旧稿永久丢失。`updateDraft` 永远优先。

## 参数定稿记录（2026-08-26，用户拍板）

排版参数是**用户偏好**，以本文记录为准；改动必须走「先改 → 发布 → 用户确认 → 固化」闭环（见 SKILL.md 排版铁律 3）。

| 参数 | 值 | 说明 |
|------|-----|------|
| 正文行距 `line-height` | **2.0** | 曾试 1.75，用户拍板改回 2.0 |
| 正文字号 | 15px | 固定 |
| 正文颜色 | #333 | 固定 |
| 段距 `margin` | 13px 8px | 序号列举段落与正文同款，无特殊间距 |
| footer 简历行距 | **1.5** | footer.html 简历 section 内显式 `line-height:1.5` |
| 表格行距 | 1.6 | 表格内专用，不随正文变 |
