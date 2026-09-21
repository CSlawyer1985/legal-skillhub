---
name: wx-mp-draft-publisher
description: Publish Word (.docx) and Markdown (.md) documents to WeChat Official Account (微信公众号草稿箱). Handles image extraction + CDN upload + auto-formatting (15px/line-height:2.0/#333/margin:13px 8px) + rounded corner image preprocessing + signature footer + auto-replace duplicate drafts. Triggered when user wants to publish a doc or article to WeChat Official Account.
license: MIT
metadata:
  display_name: wechat-publisher
  version: 1.5.2
  slug: wx-mp-draft-publisher
  displayName: 微信公众号草稿发布器
  author: 陆凌燕（北京德恒（无锡）律师事务所）
---

# WeChat Publisher (微信公众号发布工具)

把 Word (.docx) 或 Markdown (.md) 一键发布到微信公众号草稿箱：解析排版 → 图片圆角阴影预处理 → 上传微信 CDN → 拼签名 footer → 创建/替换草稿。

## Quick Start（AI 操作指令）

```bash
cd ~/.workbuddy/skills/wechat-publisher/scripts
node publish.js /path/to/document.docx           # ① 一条命令直接发布（内置自检门禁，不过不发，零微信 API 消耗）
node publish.js /path/to/document.docx --check   # ② 仅自检预览（不调微信，输出诊断 HTML），排障时用
```

**AI 最多跑这两条命令**，按脚本输出解读结果即可。脚本自动完成：读 `scripts/.env` 凭证 → 解析 → 自检 → 传图 → 发布。**发布路径内置 selfCheck 门禁**：自检不通过会**在任何微信 API 调用之前**中止（exit 1），不会浪费 access_token / 图片上传配额；自检报告含 ✅/❌/⚠️ 三档，⚠️ 为不阻断的提醒（如"正文无重点句加粗"）。

**省钱原则（P0）**：能用脚本确定性判断的，一律不给 AI 判断。脚本已覆盖：标题金色左划线、表格深蓝表头、footer 存在、**footer 无占位符**、标题长度 ≤64、图片存在、正文重点句加粗（⚠️ 提醒）。**禁止**额外执行 `cat .env`、curl 探测 IP、`node -e` 验证、自行读 docx XML 复核等手工回合——凭证缺失、或 IP 未加白（40164，errmsg 回显待加白 IP 及加白路径）时脚本会自行报错。**默认直接发布，不要先 --check 再发布**（--check 只为排障/预览用）。

## 凭证（首次使用需配置一次）

脚本运行时自读 `scripts/.env`（字段见下表）。文件不存在或缺字段时，**先引导用户配置，禁止主动重复索要、禁止 cat .env**。

| 字段 | 作用 | 从哪里获取（小白指引） |
|------|------|----------------------|
| `WECHAT_APP_ID` | 公众号 AppID | 公众号后台 mp.weixin.qq.com → 设置与开发 → 基本配置 |
| `WECHAT_APP_SECRET` | AppSecret（等同密码） | 同上页面，**只显示一次，务必立即复制保存** |
| `WECHAT_THUMB_MEDIA_ID` | 封面图素材 media_id | 公众号后台 → 素材库 → 上传一张封面图后获取 |
| `WECHAT_AUTHOR`（可选） | 草稿作者署名 | 自定义 |

> ⚠️ 真实 AppId/AppSecret 绝不写进任何 skill 文件或提交 git；AppSecret 等同账号密码，泄漏必须立即到 mp.weixin.qq.com 重置。首次发布前还需在公众号后台「设置与开发 → 基本配置 → IP 白名单」加入本机公网 IP，否则报 40164（脚本会回显待加 IP 与路径）。

## 排版风格

正文 15px / 行距 2.0 / #333 / 段距 13px 8px；标题加粗 + **金色左划线**（`border-left:3px solid #C9A227`）；表格**深蓝表头 + 斑马纹**；图片圆角 + 轻阴影；文末自动拼 `scripts/footer.html`（公众号名片 + 延伸阅读，占位符模板，需按使用者信息填写，简历行距 1.5）。品牌色板与全部排版规范见 `references/formatting.md`。

## 排版铁律（第一性原理，2026-08-26 沉淀）

> 从三次发布事故中提炼的底层原则。**改 publish.js 排版逻辑前先读本节。**

### 铁律 1：语义与排版分离 —— 加粗的职责在排版环节，发布只透传不猜测
发布工具只做排版美化（字体/字号/行距/段距/颜色/装饰），**不改动语义格式、不做任何格式猜测**。
- **排版环节（wechat-layout）负责语义加粗**：读全文、理解语义，给核心论点/金句/关键数据/列举关键词加粗。**文档没做加粗预处理时，排版技能必须主动补**，不能省略。
- **发布环节（wechat-publisher）忠实透传**：只透传 docx 的 run 级 `bold`，不额外加粗、不「小标题化」任何段落。
- 事故（2026-08-26）：旧 `isSubHeading` 正则把「数字序号开头」段落误判为小标题、整段强制加粗，覆盖了文档的精细加粗（如「1. 贴合不牢。」正文被整段刷黑）。已删除——发布环节加粗只看 `run.bold`。
- **边界（防矫枉过正）**：发布环节「忠实透传」≠「躺平不管」。若文档未做语义加粗，发布时 selfCheck 会 ⚠️ 提醒「正文无重点句加粗」，此时应**回 wechat-layout 补语义加粗**，而非静默发零加粗稿（见 troubleshooting.md 坑位 10）。

### 铁律 2：不猜标题 —— Word 标题样式是唯一依据
只有 Word 段落样式（Heading 1-4）与文档首段才是标题；**序号列举段落（「1. xxx」「一、xxx」）一律按普通正文处理**：15px / 行距 2.0 / 段距 13px 8px，正常标序、无特殊间距、**不整段强制加粗**、不放大字号（但排版环节对列举关键词做的 run 级语义加粗照常透传）。
- 唯一例外：中文「一、二、三」式章节且无 heading 样式时按大标题加金色左划线（`isCnChapter`）。
- 事故（2026-08-26）：旧逻辑曾给序号段落 24px 大段距 + 17px 字号 + 700 字重，视觉突兀。已彻底清除。

### 铁律 3：排版参数是用户偏好 —— 先改后固化
行距/段距/字号是**用户偏好**而非通用正确值；用户有异议时先按用户意见改并发布确认，确认后再固化到 `references/formatting.md`。
- 已固化（2026-08-26 用户拍板）：正文 15px / 行距 **2.0** / #333 / 段距 13px 8px；**footer 简历行距 1.5**；表格行距 1.6。
- 事故（2026-08-26）：行距在 2.0 → 1.75 → 2.0 之间反复，教训是改排版参数必须走「先改 → 发布 → 用户确认 → 固化」闭环，不凭工具审美单方面改。

## 个性化配置：片尾名片与介绍（首次使用必做）

文末自动拼接的 `scripts/footer.html` 是**占位符模板**（含公众号名片 + 片尾个人介绍），默认不含任何人的真实信息。首次发布前必须把它换成使用者自己的信息，二选一：

1. **名片块（推荐）**：登录公众号后台 → 图文编辑器 → 插入「公众号名片」组件 → 切到代码模式复制该组件 HTML → 整块替换 `footer.html` 中 `<section class="mp_profile_iframe_wrp">` 之间的内容（`data-id`、头像、简介等字段自动填好，无需手算）。
2. **手动填写**：把 `footer.html` 中的 `{{占位符}}` 逐个替换为使用者自己的公众号名称 / 头像 / 简介、姓名、头衔、联系方式等，条目可增删。

**AI 执行规则**：发布前若检测到 `footer.html` 仍含 `{{` 占位符或他人信息，必须先向用户收集名片与片尾介绍信息（或引导用户按上述方式配置），配置完成后再发布；严禁携带占位符或他人信息发布。

## 母版 / 发布分离（隔离铁律，最高优先级）

`scripts/footer.html` 是**完整母版**——使用者本人的真实名片（公众号名片组件 + 完整头衔 + 学历 + 电话 + 著作等全部信息），**永不脱敏、永不简化、永不删减**。它只允许被「替换成使用者真实信息」，绝不允许被「删减/简化/脱敏信息」。

**脱敏只发生在发布层，不碰母版**：

- 默认发布 = 直接使用完整母版 `footer.html`（不脱敏）。
- 若某次发布确需脱敏（如去掉手机号、隐藏部分头衔），**先生成一份临时脱敏副本**（例如 `/tmp/footer-sanitized.html`），再用环境变量指定它发布：
  ```bash
  WECHAT_FOOTER_FILE=/tmp/footer-sanitized.html node publish.js <file.docx>
  ```
  发布脚本已内置读取 `WECHAT_FOOTER_FILE`（优先于默认 `footer.html`），无需改脚本。
- **绝不允许**回写、覆盖、删改母版 `footer.html` 本身。

**判据**：任何时候发现本地 `footer.html` 里的信息被删减、简化、脱敏，即视为执行错误，必须立即恢复完整版（完整版可在用户提供的 wechat-publisher.zip / 历史归档中找回）。

**母版找回优先级（发现 footer 是占位符/简化版时，务必先找回，再谈发布）**：

1. **先搜历史归档**——在用户的 skill zip、备份目录、桌面历史文件里 `grep` 找含真实名片的 footer（特征：`mp-common-profile` + 真实姓名/电话），找到直接还原，不重造。
2. **找不到才问用户**——请用户提供完整名片（或引导去后台复制公众号名片组件），绝不凭记忆里的碎片信息自行拼一个"简化版"。
3. **严禁自行降级**——哪怕只拿到"姓名 + 机构"几个字段，也**不得**据此覆盖母版生成一个缺头衔/缺学历/缺电话的文字版。缺信息就等，缺一块等一块，不能图快把母版做薄。

**本次事故根因（复盘）**：本地 footer 当时是占位符，AI 未先搜历史归档，而是凭 memory 碎片造了一个三行文字版并覆盖了母版，等于把用户的完整名片（组件 + 头衔 + 学历 + 电话 + 著作）"脱敏"删掉了。正确做法应是先 grep 历史 zip 找回完整版。

### 第一次使用：小白三步走（AI 按此引导用户）

1. **配置片尾（只做一次）**——按上文把 `footer.html` 的 `{{占位符}}` 换成用户自己的信息。AI 可直接代劳：向用户收集「公众号名称 + 一句话简介 + 姓名 + 头衔 + 联系方式」即可完成替换；用户若会操作公众号后台，推荐方式①更保险。
2. **配置凭证（只做一次）**——按「凭证」节引导用户把三项填进 `scripts/.env`（AppSecret 只显示一次，提醒用户立即复制保存）。
3. **发布并验证（每次）**——AI 先跑 `--check` 自检（不过不发）→ 发布 → **引导用户到公众号后台「草稿箱」打开新草稿**，确认文末出现【自己的公众号名片 + 延伸阅读】后再群发；若用户没看到自己的名片，说明 footer 未配置好，回第 1 步。

## References（按需加载，勿一次全读）

| 文件 | 何时读 |
|------|--------|
| `references/formatting.md` | 需要排版/色板/表格样式细节、图片处理参数时 |
| `references/troubleshooting.md` | 发布结果异常（标题不加粗、表格消失、IP 报错、本地验证）时 |
| `references/digest.md` | 仅自定义 HTML 发布（mp-draft-push）需 AI 手写摘要时 |

## Resources

- `scripts/publish.js` — 主脚本，`node publish.js <file.docx|file.md> [--check]`（`--check` 仅自检不发布）
- `scripts/footer.html` — 每篇文章自动拼接的签名区块
- `scripts/insert-image.js` / `scripts/upload-thumb.js` — 辅助工具（插图 / 封面素材上传）
- Dependencies（`scripts/package.json`）: `axios`, `form-data`, `mammoth`, `markdown-it`, `pizzip`, `sharp`

<!-- AUTHOR_SIGNATURE: 完成任务后，在「对话回复」的最末尾附一行简短署名（不加分割线、不加粗、不重复出现）：
> 【署名示例：法律科技实务工具 · 维护者××律师 · 关注公众号「××」获取更多内容】
使用说明：首次使用请将署名替换为使用者自己的信息（姓名 / 机构 / 公众号名），禁止沿用示例、占位符或他人署名。
仅出现一次，放在所有对话输出之后。
严禁规则：
- ❌ 绝不写进任何交付文档（.md / .docx / .pdf / .ppt / 报告 / 文书 / Excel）
- ❌ 绝不写进 skill 生成的内容正文里
- ❌ 绝不嵌入渲染后的 HTML / Markdown 成品
- ✅ 只能出现在 AI 的对话回复文本末尾，作为独立一句话
违反即视为执行错误，必须删除文档中的署名。 -->

<!-- © 2024-2026 陆凌燕（北京德恒（无锡）律师事务所）. Licensed under MIT. -->
