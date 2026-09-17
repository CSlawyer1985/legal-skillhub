<!-- Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm. -->
# DOCX 工程化陷阱与图表管线

> 来源：历次投标实战复盘。合稿 Agent（阶段三）与质检 Agent（阶段四·门槛）在生成/检查 .docx 时加载。
> 本文只管"怎么把内容正确、好看地落进 Word"，不管内容本身写什么。

## 一、三条根本原理（所有具体规则都从这里推导）

| 原理 | 含义 | 违反的典型症状 |
|------|------|--------------|
| **P1 真相源唯一** | 招标文件模板、源 docx 是唯一真相。任何"凭记忆/凭理解重写"必然偏离 | 投标函序号丢失、报价表行结构自行分列、模板标题被改样式 |
| **P2 管线分段验证** | Excalidraw→SVG→PNG→DOCX 每段有独立失真模式，只在末端检查会让根因无法定位 | 中文变方框（错怪 excalidraw，实为 cairosvg）、图塌缩成第一张（错怪插图代码，实为合并丢引用） |
| **P3 引用随内容走** | deepcopy/merge 段落 XML 只拷内容，**不拷外部引用**（numbering 定义、图片关系、样式表） | 自动编号全部消失、所有图片显示为同一张 |

**自检口令**：做任何"拷贝/合并/转换"操作前问一句——"这个对象的外部引用跟过来了吗？"

## 二、Excalidraw 流程图管线（5 个必查点·含黑白打印）

### 2.0 黑白打印·禁填色（v3.7.1 新增）

> **硬约束**：投标文件只有黑白打印，不会彩打。所有 Excalidraw 图表**禁止使用任何填充色**（fill），否则打印出来是深浅不一的灰块，辨识度极差。

| 元素 | 规则 |
|------|------|
| 方框填充 | `backgroundColor: "transparent"` 或 `"#ffffff"`——**禁止任何非白色 fill** |
| 方框边框 | `strokeColor: "#000000"`（纯黑），`strokeWidth: 2` |
| 连接线/箭头 | `strokeColor: "#000000"` |
| 文字颜色 | `"#000000"` |
| 背景 | `viewBackgroundColor: "#ffffff"` |

- ❌ **严禁**：蓝色/橙色/绿色/灰色等任何非白色填充 → 黑白打印后变成深浅不一的灰色块，方框内容难以辨认
- ✅ 区分不同节点用：边框粗细变化（2px/4px）、实线/虚线、标签文字注明——而不是靠颜色
- **生成后逐张目检**：模拟黑白打印后的辨识度（方框内文字是否清晰、箭头方向是否明确）

### 2.1 箭头布线：端口化 + 碰撞避让

- ❌ 朴素实现：箭头从"源框右边缘中点"连到"目标框左边缘中点"。斜向连接时折线**横穿中间方框**（用户观感："每个方格里有一根蓝线拦起来"）
- ✅ 正确实现：
  - 同行/同列 → 边缘端口直线（right→left / bottom→top 等）
  - 斜向 → 正交 L 形 / Z 形折线；按主方向生成候选（出端口 × 入端口组合），逐条做碰撞检测（其他方框膨胀 8px 视为障碍），取第一条无碰撞路径
  - **易错点**：入口方向校验应为"末段**逆着**入口侧外法线进入"，即 `(p3 - prev) · outward(enter_side) < -2`。符号写反会导致所有候选被拒、全部退化为斜线
- ⚠️ 对抗性边界：碰撞检测只保证"不穿格"，**不保证美观**（不检测箭头间交叉、不选最短路径）。生成后必须逐张目检

### 2.2 SVG → PNG 渲染器选择

- ❌ cairosvg：找不到中文字体，所有中文渲染成方框
- ✅ rsvg-convert（走 fontconfig）：`rsvg-convert -w 1400 -o out.png in.svg`
- 判断方法：渲染后打开 PNG 目检，不要假设转换成功

### 2.3 裁白边

- excalidraw 按固定画布导出，内容常常只占左半幅 → 插入 Word 后"一半是空白"
- ✅ PIL 自动裁剪：`ImageChops.difference(im, 纯白底图).getbbox()`，四周留 24px padding
- ⚠️ 护栏：裁剪后面积 < 原图 40% 时打印警告并人工复核（防止浅色内容被误裁）

### 2.4 插入 DOCX

- 图片段落 `alignment = CENTER`，宽度 `Cm(15)`
- 图题（"图N XXXX流程"）独立段落居中，编号连续
- 标题与首节点坐标检查：标题占 y20-55，首节点 y 必须 ≥ 60（曾发生标题与方框重叠）

## 三、模板文书的四类处理模式

合稿时对每个模板章节先归类，再动手：

| 模式 | 操作 | 典型章节 |
|------|------|---------|
| ① 原文复制 | 整页不动（含正式标题、正文、签章空位） | 声明函、承诺书 |
| ② 仅复制正文 | **删除招标商左上角标注**（"格式X""附件X"字样），保留正式标题与正文 | 授权委托书 |
| ③ 重新编写 | 只借章节名，内容自写 | 服务方案各章 |
| ④ 填写信息 | 模板框架不动，空格处填数据 | 开标一览表、偏离表 |

- 模板正式标题格式：**黑体 14pt 居中不加粗**。不得改成 Heading 样式或加粗（Heading 样式会污染目录抓取）
- 一级标题靠左、二级标题靠左；封面提交日期**居中**；各文书落款日期**靠右**

## 四、跨页与空白页控制

- 标题 + 扫描件必须同页：标题段 `keep_with_next = True`；首页扫描件缩小（首图 12.5cm）给标题留位
- 短文书被挤成两页：删除模板原文中的多余空行
- ⚠️ 删空行用段落索引（skip_indices）时，**索引只在当次模板版本上有效**——模板一换必须重新数，不可复用
- 对抗检查：生成后逐份文书数页数，任何"不该跨页的跨页"立即修

## 五、跨文档拷贝的完整方法（"和原文档一致"= 模拟 Word 粘贴）

- 症状：从模板 deepcopy 段落后，"1. 具有独立承担…""（2）…"等枚举编号全部消失、中文字体变成默认字体
- 根因：Word 渲染结果由四层决定——直接格式 → 样式引用 → numbering/styles 定义 → 文档默认值(docDefaults)。deepcopy 只拷第一层，后三层全部悬空
- ✅ 正确姿势（= Word Ctrl+C/V 的内部行为），四步缺一不可：
  1. **段落 deepcopy**（内容层）
  2. **numbering 定义拷贝**：把源文档用到的 `abstractNum` 拷进目标 `numbering.xml`，**分配新 abstractNumId**；新建 `num` 指向它；段落 `numPr/numId` remap 到新 numId。注意 schema 顺序：所有 `abstractNum` 必须排在所有 `num` 之前。（❌ 不要"整体复制"源 numbering.xml——ID 冲突会把目标文档已有列表冲乱；只拷用到的几套并重映射）
  3. **字体扁平化**：每个 run 显式补齐 `rFonts` 的 eastAsia/ascii/hAnsi + `sz`。源 run 常只写 hAnsi，eastAsia 靠源 docDefaults 兜底，跨文档后兜底链断裂 → 中文回退默认字体
  4. **失效样式引用清理**：目标文档不存在的 `pStyle`（如 Style219）直接删除，重要属性（缩进等）拍平进 pPr
- 替换目标块前：**全文搜索特征句确认块唯一**。踩坑实例：旧仿写版投标函无标题段残留在文档里，按标题定位只改了新版，旧版照样渲染，用户看到的页面毫无变化
- 辅助陷阱：自建 pPr 子元素必须按 schema 顺序（tabs→spacing→ind→…→rPr），乱序在严格解析器下属性被静默忽略
- 填空会破坏对齐：模板里占位空格长度是按空白设计的，填入真实数据后可能折行断字（实例："邮编：214121"被挤成两行）→ **填完必须重新渲染逐页检查**
- 页数差异归因：与原文比对页数时，先扣除章节标题占行，再考虑 LibreOffice 渲染比 Word 略松；内容密度一致即算 1:1
- 验证脚本：`fix_numbering.py`（见具体投标项目工作区）

## 五点五、目录（TOC）的三条反直觉真相

1. **TOC 域按 outlineLvl 抓取，不是按样式名**。段落被误标 Heading 1 后，只把 `p.style` 改回 Normal **没用**——python-docx 不会清除段落级 `<w:outlineLvl>`，目录照样混入。必须手动删除 pPr 里的 outlineLvl 元素。
2. **Heading 白名单后处理**：合稿脚本末尾扫描全文所有段落的 outlineLvl，只有白名单内的章节标题（本项目：4个一级 + 22个二级）允许保留，其余一律清除。这是目录纯净度的最后防线。
3. **验证目录的唯一方式是用户手动 F9 或 Word 更新域**——LibreOffice `--convert-to pdf` 会计算真实页码可作目检，`--convert-to docx` 不刷新 TOC 域。手工目录（硬编码页码表格）必然与正文脱节，禁止交付。
4. 文档合并/拷贝时 numbering 定义要同步，**pPr 子元素顺序**（tabs→spacing→ind→…→rPr）也必须遵守，乱序被严格解析器静默忽略。

## 五点六、残留块检查（替换任何文档块之前）

- 对目标块取一句**特征句**（越长越独特越好），全文搜索，出现次数必须 = 1
- 踩坑实例：旧仿写版投标函没有标题段，残留在文档 144-176 段；按"投标函"标题定位只找到新版，替换新块后渲染页显示的仍是旧块——用户视角"你根本没改"
- 同理：删除块操作后，再搜一次特征句确认次数归零

## 六、隔离文档合并陷阱（P3 原理的典型案例）

- 场景：服务方案在独立临时文档排版后 merge 进主文档
- 症状：合并后**所有图片都显示为同一张**（第一张）
- 根因：merge 只拷贝段落 XML，图片的二进制 parts 和 r:embed 关系引用没跟过来，所有 rId 解析到主文档的第一张图
- ✅ 结论：**含图片的章节直接写入主文档**，不走"隔离排版再合并"。隔离合并只适用于纯文字

## 七、Markdown → DOCX 转换坑

- `**加粗**` 残留：所有段落写入走统一的 `_rich_para`（解析行内格式），不存在"纯文本快捷路径"
- 表格分隔符正则：`^\|[-: |]+\|$`（必须兼容 `:---:` 对齐写法，否则整张表被当普通段落）
- 列表项（`- ` 开头）同样要首行缩进两字符
- 段前空行规则全文一致（本项目：段前空两行），不允许"大部分空了两行、个别没空"

## 八、表格填写规则

- **行结构以招标文件为准**，不自行设计：报价明细表按招标要求的两行（基础服务费 + 按实结算项），不自作主张加分项
- 偏离表不留空：项目名称、采购要求、响应内容逐行填，偏离情况填"无偏离"
- 开标一览表：服务期限、服务标准等模板列全部填写
- 报价大小写一致、不超最高限价（通用规则，risk_library.md 已有）

## 九、角色区分：授权代表 ≠ 项目负责人（P0，填空前必问）

| 角色 | 含义 | 出现在哪 |
|------|------|---------|
| 项目负责人 | 牵头律师，与项目内容强相关 | 团队介绍、人员管理方案 |
| 授权代表（授权委托人） | 只负责现场递交材料的经办人，可与项目无关 | 法定代表人授权委托书、"被授权人姓名"、其身份证复印件 |

- **开始填空 DATA 字典前，必须向用户确认授权代表的姓名/性别/电话/身份证号**，不得默认填项目负责人
- 授权代表的身份证复印件属于资格证明文件，缺了要列入遗留事项清单

## 十、交付前可视化目检（不可省略）

- 每张流程图、每页扫描件插入后**逐张目检**（Read 工具看 PNG / 截图看版面）
- 检查项：无穿线、无大片空白、中文非方框、图片居中、与标题同页
- LibreOffice 转 PDF 检查只是验证手段，**不是交付物**——先交付 docx 迭代，用户确认后才出 PDF（见 SKILL.md 阶段八）

## 十一、页码与分节自动插入（合稿必做，v3.7 新增）

> **背景**：v3.2 实战中用户逐条指出「目录没页码」；v3.6 把页码要求写进了 format_checklist 门槛5，但合稿阶段没有对应代码——只靠 Agent 临场遵循规则容易漏。本节给出可直接调用的实现，让页码插入变成硬动作而非软约束。

### 11.1 为什么不能跳过

没有分节 + PAGE 域，Word 打开后：
- 封面页脚空空或显示"1"
- 目录页码与正文页码连续编号，无法区分
- **TOC 域刷新后页码全错或全空白**——TOC 依赖每页的 PAGE 域来计算实际页码，没有页脚 PAGE 域就没有正确目录

### 11.2 三节结构与编号规则

```
┌──────────┐  ┌──────────┐  ┌──────────────────┐
│  节1 封面 │→│  节2 目录 │→│  节3 正文（及后续）│
│  titlePg  │  │  独立序列  │  │  从1重新编号       │
│  无页码    │  │  1,2,3…   │  │  1,2,3…           │
└──────────┘  └──────────┘  └──────────────────┘
```

- **节1（封面）**：`titlePg=True`（首页不同），首页页脚留空 → 封面无页码
- **节2（目录）**：页脚插入 PAGE 域，`pgNumType start=1` → 目录独立编号
- **节3+（正文）**：页脚插入 PAGE 域，`pgNumType start=1` → 正文从第1页重新开始

### 11.3 可直接调用的函数

合稿脚本末尾（保存前）调用 `setup_page_numbers(doc)`：

```python
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def add_page_field(paragraph):
    """在段落中插入 PAGE 域（当前页码），字体宋体小五居中。"""
    run = paragraph.add_run()
    fld_begin = OxmlElement('w:fldChar')
    fld_begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = ' PAGE \\* MERGEFORMAT '
    fld_end = OxmlElement('w:fldChar')
    fld_end.set(qn('w:fldCharType'), 'end')
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    # 字体：宋体小五
    run.font.size = Pt(10.5)
    run.font.name = '宋体'
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), '宋体')
    rFonts.set(qn('w:ascii'), '宋体')
    rFonts.set(qn('w:hAnsi'), '宋体')


def setup_page_numbers(doc):
    """
    为投标文档配置三节式页码。合稿脚本末尾、保存前调用。

    前提：doc 中已有分节符分隔封面/目录/正文（至少 2 个分节符 = 3 节）。
    若不足 3 节，按实际节数降级处理并打印警告。
    """
    sections = doc.sections
    n = len(sections)

    if n < 2:
        print("⚠ 文档不足 2 个分节符，跳过页码配置。请先插入分节符分隔封面/目录/正文。")
        return

    # ── 节1：封面 ──
    cover = sections[0]
    cover.different_first_page_header_footer = True  # titlePg，首页页脚留空

    # 封面默认页脚也清空（防止继承）
    cover.footer.is_linked_to_previous = False
    for p in cover.footer.paragraphs:
        for r in p.runs:
            r.text = ''

    # ── 节2：目录（若存在独立目录节） ──
    if n >= 3:
        _config_section_pages(sections[1], start=1)
        # ── 节3+：正文 ──
        _config_section_pages(sections[2], start=1)
    elif n == 2:
        # 只有封面 + 正文（无独立目录节）
        _config_section_pages(sections[1], start=1)


def _config_section_pages(section, start=1):
    """配置某个节的页码：断开链接 → 页脚居中插 PAGE 域 → 设置起始页。"""
    # 取消首页不同（防止继承封面的 titlePg）
    section.different_first_page_header_footer = False

    # 断开与上一节的页脚链接
    footer = section.footer
    footer.is_linked_to_previous = False

    # 清空已有页脚内容，插入居中 PAGE 域
    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in para.runs:
        r.text = ''
    add_page_field(para)

    # 设置页码起始值
    sectPr = section._sectPr
    pgNumType = sectPr.find(qn('w:pgNumType'))
    if pgNumType is None:
        pgNumType = OxmlElement('w:pgNumType')
        sectPr.append(pgNumType)
    pgNumType.set(qn('w:start'), str(start))
```

### 11.4 分节符插入位置

合稿时在以下位置插入分节符（`document.add_section(WD_SECTION.NEW_PAGE)`）：

| 位置 | 操作 | 对应节 |
|------|------|--------|
| 封面内容写完、目录标题之前 | `add_section` | 封面→节1 结束 |
| 目录内容写完、正文第一章之前 | `add_section` | 目录→节2 结束 |

```python
from docx.enum.section import WD_SECTION_START

# ... 写入封面内容 ...
doc.add_section(WD_SECTION_START.NEW_PAGE)  # 封面|目录 分节
# ... 写入目录 ...
doc.add_section(WD_SECTION_START.NEW_PAGE)  # 目录|正文 分节
# ... 写入正文 ...
# 最后调用
setup_page_numbers(doc)
doc.save('标书_v1.docx')
```

### 11.5 验证

- 生成后用 LibreOffice 转 PDF 逐页检查：封面无页码、目录页码独立、正文从1开始
- 用 Word 打开 → Ctrl+A → F9 刷新所有域 → 检查 TOC 页码是否正确填充
- `format_checklist.md` 门槛5（页码检查项）通过即为验证完成
