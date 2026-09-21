---
name: add-slide-to-deck
description: 往已有原生 PPTX 追加风格一致的新页，加一页或成组多页（如一个新场景）皆可。当用户要求「在这个 PPT 里加一页」「加几页」「追加一个场景」「模仿这个 PPT 的风格加页」时使用。适用于原生可编辑 PPTX（PptxGenJS / PowerPoint 生成），不适用于 ppt-master 的 SVG 整副生成场景。
license: MIT
metadata:
  slug: add-slide-to-deck
  displayName: PPT 加页助手
  version: 1.1.0
  author: 陆凌燕
---

# 往现有 PPTX 追加风格一致的新页

## 路由判断（先做）
- deck 是**原生可编辑 PPTX**（打开 slide XML 有大量文本框）→ 用本 skill（python-pptx 直接追加）
- deck 是 ppt-master SVG 生成 / 用户要整副重做 → 用 ppt-master
- 用户说「用 ppt-master」但 deck 是原生的 → 向用户说明：加一页用 python-pptx 直接追加才能无缝合入，ppt-master 产出的单页无法合进原生文件

## 流程

### 0. 内容提炼（先于一切排版）
skill 只保证「形」像，内容质量靠这一步：
- 要点从源材料（docx / 文章 / 稿件）**忠实提取**：关键数字、URL、操作路径、版本号一个不丢；不虚构、不过度压缩
- 页数由内容定：先按主题分组（痛点 / 选型 / 体验 / 技巧…），每组一页；放不下**拆页不删内容**
- 单卡片要点 ≤5 条，每条 ≤21 字（12pt 防换行，实测依据见第 5 节）
- 句式跟参照页（如「特点：…」「适用：…」前缀风格）；导语一句话点透本页立场
- 图片跟随要点走：每张图对准一个要点，遵守「一页一图」

### 1. 提取现有样式（不要凭记忆猜配色）
```python
# 用托管 venv：~/.workbuddy/binaries/python/envs/default/bin/python（系统 python 缺 pptx）
from pptx import Presentation
import re
p = Presentation(path)
# 全局统计实际用色/字体/字号
for s in p.slides:
    x = s._element.xml
    # srgbClr val / typeface / sz= 出现频次 → 定主色、正文字号
# 逐 shape dump 参照页：位置(inch)、prstGeom、solidFill、run 的 sz/bold/color
```
**参照页选择标准**：选与目标页**同构**的页——要放卡片就找有卡片的页、要放图就找放图的页；无完全同构页时选最接近的，缺的部分从相邻页补。

重点记录页头五件套（**数值每份 PPT 都不同，必须现场量；下面仅示例格式**）：kicker（bold 小字、accent 色、左上角）、标题（最大号 bold 主色）、引导条（accent 色小横条）、导语（灰色正文）、页脚（竖条 + 小字）。逐 shape dump 参照页拿：位置(inch)、prstGeom、solidFill 色、run 的 sz/bold/color。**换一份 PPT 这些值全部重新提取，禁止沿用上次的具体数值。**

### 2. 确定插入位置与编号
逐页打印标题找章节边界（`sh.text_frame.text`），编号顺延**全 deck 最大小节号**（deck 的 kicker 序列可能本身错乱，勿照抄上一页），用 `sldIdLst` 移动到目标位置：
```python
sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst); new_el = ids[-1]
sldIdLst.remove(new_el); sldIdLst.insert(目标索引0基, new_el)
```

### 3. 写新页（要点）
- 版式：`list(prs.slides)[参照页idx].slide_layout`
- 中文字体必须同时设 latin + east-asian，**字体取参照页实测值，不硬编码**（示例里的「微软雅黑」仅因那次 deck 实测用它）：
  ```python
  rPr = run._r.get_or_add_rPr()
  etree.SubElement(rPr, qn('a:ea')).set('typeface', <参照页实测字体>)
  ```
- 列表标记用**椭圆小圆点**（MSO_SHAPE.OVAL 0.08×0.08，颜色取本份 PPT 的 accent 色），不用方块（用户全局偏好：圆点标记）
- 正文 ≥12pt；换行按目标 PPT 实测字宽预估（中文字符数随字号/卡片宽度变，渲染验证后校准）；条目间距、卡片内边距均从参照页量出来
- 卡片样式（底色/标题带高度/白字字号）**照参照页抄**，不自创
- **背景一致性**：参照页 layout 只继承母版元素，**直接画在页面上的全页背景**（顶条、底色块）不会被继承——渲染后对比新旧页底色/页顶元素，有则需重绘
- `sp.shadow.inherit = False`；新文件另存（`_新增xx页.pptx`），不覆盖原件

### 4. 视觉验证（必做）
```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir /tmp/check <pptx>
pdftoppm -f <页码> -l <页码> -r 100 -png /tmp/check/*.pdf /tmp/check/page
```
目检：换行是否挤行、是否超出卡片、页脚是否重叠。注意：本机缺微软雅黑时 LibreOffice 会替换成斜体衬线——这是预览假象，PowerPoint 里正常，不要据此改字体。

### 5. 批量追加多页（场景式，2026-09-04 公证PPT实战补充）
本 skill 同样适用于一次追加成组多页（如一个新场景 5–6 页），流程不变，另注意：

- **插入位置**：多页先 append 到末尾，再用 `sldIdLst` 统一移动到章节边界（如最后一个场景之后、PART 分隔页之前）；移动后打印前后页标题验证（`idx-1 / idx / idx+n` 各查一次）
- **素材来自 docx 时**：`unzip` 取 `word/media/*` 得图片；用 python-docx 按段落 `a:blip` 顺序确定文图对应关系；PIL 读长宽比后**等比居中**放进预留区域，不裁剪不变形
- **图片布局**：竖图（手机截图，宽高比 ~0.5）按 H 定 W（如 H=3.2 → W≈1.6），在右侧区域水平居中；横图按 W=卡宽定 H 垂直居中。遵守「一页一图」铁律——多张截图宁可拆页
- **文案长度预控**：卡片要点文本宽 = 卡宽 − 0.56"，12pt 中文约 **22 字/行**（按 3.74" 实测）；写要点时先控制在 21 字内避免换行挤压。渲染后若发现换行，**优先缩短文案**，不要加大条目间距（间距是量自参照页的）
- **多页编号**：kicker 顺延现有小节号（如 2.17），标题用「（上）（中）（下）」分层；「场景 N」编号顺延最大场景号

### 6. 踩坑记录（2026-09-04）
- **生成脚本重跑前必须 grep 验证**：Edit 工具可能报成功但未落盘（同轮 3 处编辑实测仅 1 处生效）。改完脚本先 `grep` 关键新字符串确认，再跑脚本、再渲染
- **渲染缓存**：重新生成 pptx 后，先 `rm` 旧 PDF 和旧 PNG 再重新转换，否则目检看到的是旧图
- **LibreOffice 预览假象**：中文回退衬线体、字宽与微软雅黑略有差异——只判断换行/出界/重叠，不据此改字体和字号

> 法律科技实务工具 · 维护者陆凌燕律师（北京德恒·无锡）· 关注公众号「鹿鸣于野 UMU」获取更多内容
