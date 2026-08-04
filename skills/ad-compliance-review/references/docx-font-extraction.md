# DOCX 文件字体元数据解析模块

> 用途：当用户提供的广宣物料为 `.docx` 格式时，执行本模块提取文档内部 XML 中存储的字体名称，并与 `font-copyright-table.md` 进行版权风险比对。此为字体主动识别机制的**补充能力**，覆盖"文本字符串扫描"无法发现的隐藏字体信息。

---

## 一、背景：为什么需要 DOCX 字体解析

`.docx` 文件是 ZIP 压缩包，内部包含多个 XML 文件。字体名称存储在 XML 节点属性中，**并不总是出现在用户在 Word 中看到的文本内容里**。仅对提取后的纯文本做字符串匹配会遗漏以下情况：

- 用户未在文案中写入字体名称，但文档实际排版使用了有版权风险的字体
- 样式模板（如企业模板）预置了特定字体但文案本身不提及

**本模块通过解析 DOCX 内部 XML，补齐"文本层扫描"无法覆盖的字体信息。**

---

## 二、DOCX 中字体信息的三个存储位置

| 上级 ZIP 路径 | 对应 XML 元素 | 说明 |
|:---|:---|:---|
| `word/document.xml` | `<w:rPr>` → `<w:rFonts>` | 段落/文字级别的直接字体引用（最高优先级） |
| `word/styles.xml` | `<w:rFonts>` | 样式定义中的字体（标题/正文等样式的默认字体） |
| `word/theme/theme1.xml` | `<a:majorFont>` / `<a:minorFont>` | 主题字体方案（标题/正文主题字体） |

### 提取的字体属性

每个 `<w:rFonts>` / `<a:latin>` / `<a:ea>` 节点可取以下属性：

| 属性 | 含义 | 示例值 |
|:---|:---|:---|
| `w:ascii` | ASCII/西文字体 | `Times New Roman` |
| `w:hAnsi` | High ANSI 字体 | `Calibri` |
| `w:eastAsia` | 东亚（中文/日文/韩文）字体 | `汉仪旗黑` |
| `w:cs` | 复杂脚本字体 | `Arial` |
| `w:asciiTheme` | 主题引用（西文） | `majorHAnsi` |
| `w:eastAsiaTheme` | 主题引用（东亚） | `majorEastAsia` |

**重点关注** `w:eastAsia` 属性——中文广告物料中使用的中文字体通常会出现在此。

---

## 三、完整提取脚本

以下 Python 脚本在 Bash 中通过 `python << 'PYEOF' ... PYEOF` 方式执行。

```python
import zipfile
import xml.etree.ElementTree as ET
import sys

docx_path = sys.argv[1] if len(sys.argv) > 1 else "input.docx"

# ─── 1. 定义命名空间 ───
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'

# 字体属性名与含义映射
FONT_ATTR_MAP = {
    'ascii':      '西文(ASCII)',
    'hAnsi':      '西文(hAnsi)',
    'eastAsia':   '东亚(中日韩)',
    'cs':         '复杂脚本',
    'asciiTheme': '主题引用-西文',
    'eastAsiaTheme': '主题引用-东亚',
}

def extract_theme_fonts(z, path="word/theme/theme1.xml"):
    """从主题文件中提取 majorFont/minorFont 的 latin + ea 字体名"""
    result = {}
    try:
        with z.open(path) as f:
            tree = ET.parse(f)
            root = tree.getroot()
            for fs in root.iter(f'{{{A}}}fontScheme'):
                name = fs.get(f'{{{A}}}name', '(untitled)')
                fonts = {}
                for role in ('majorFont', 'minorFont'):
                    for el in fs.iter(f'{{{A}}}{role}'):
                        for child in el:
                            tag = child.tag.split('}')[-1]
                            if tag == 'latin':
                                fonts[f'{role}_latin'] = child.get('typeface', '')
                            elif tag == 'ea':
                                fonts[f'{role}_ea'] = child.get('typeface', '')
                result[name] = fonts
        return result
    except KeyError:
        return {}

def extract_doc_fonts(z):
    """提取 document.xml 和 styles.xml 中的所有字体引用"""
    found = {}  # {font_value: [来源文件]}
    
    for xml_entry in ['word/document.xml', 'word/styles.xml']:
        try:
            with z.open(xml_entry) as f:
                tree = ET.parse(f)
                root = tree.getroot()
        except KeyError:
            continue
        
        for rFonts in root.iter(f'{{{W}}}rFonts'):
            for attr_local, attr_meaning in FONT_ATTR_MAP.items():
                val = rFonts.get(f'{{{W}}}{attr_local}')
                if val and val.strip():
                    key = val.strip()
                    if key not in found:
                        found[key] = set()
                    found[key].add(xml_entry)
    return found

# ─── 2. 执行提取 ───
with zipfile.ZipFile(docx_path) as z:
    doc_fonts    = extract_doc_fonts(z)
    theme_fonts  = extract_theme_fonts(z)

# ─── 3. 合并所有字体（去重） ───
all_fonts = set(doc_fonts.keys())
for scheme, ft in theme_fonts.items():
    for v in ft.values():
        if v:
            all_fonts.add(v)

# ─── 4. 字体版权风险库（精简版，完整库见 font-copyright-table.md） ───
RISK_LIB = {
    '微软雅黑': ('北京北大方正电子有限公司', '★★★ 阻断', 'S级·微软雅黑版权归方正'),
    '方正':     ('北京北大方正电子有限公司', '★★★ 阻断', 'S级·全系列须正版授权'),
    '汉仪':     ('北京汉仪创新科技股份有限公司', '★★★ 阻断', 'S级·全系列须正版授权'),
    '华康':     ('华康字库(威锋数位)', '★★★ 阻断', 'A级·全系列须正版授权'),
    '华文':     ('常州华文印刷技术有限公司', '★★★ 阻断', 'A级·全系列须正版授权'),
    '造字工房': ('潍坊造字工房文化创意有限公司', '★★★ 阻断', 'A级·全系列须正版授权'),
    '字魂':     ('上海字魂网络科技有限公司', '★★★ 阻断', 'A级·全系列须正版授权'),
    '锐字':     ('上海锐线创意设计有限公司', '★★★ 阻断', 'A级·全系列须正版授权'),
    '蒙纳':     ('蒙纳(Monotype)', '★★ 预警', 'B级·全球字库巨头'),
    '文鼎':     ('文鼎科技', '★★ 预警', 'B级·台湾老牌字库'),
    '中易':     ('北京中易中标电子信息技术有限公司', '★★ 预警', 'B级'),
    '文悦':     ('文悦科技(北京)有限公司', '★★ 预警', 'B级'),
    '叶根友':   ('杭州贤书阁文化创意有限公司', '★★ 预警', 'B级·150+套全系列'),
    '喜鹊':     ('喜鹊造字(叶天宇)', '★★ 预警', 'B级·收费商用'),
    '三极':     ('三极字库', '★★ 预警', 'B级'),
    '品索':     ('品索字库', '★★ 预警', 'B级'),
    '新蒂':     ('新蒂字体(Senty)', '★★ 预警', 'B级'),
    '蔡云汉':   ('蔡云汉', '★ 提示', 'C级·个人品牌'),
    '禹卫':     ('禹卫', '★ 提示', 'C级·个人品牌'),
    '默陌':     ('默陌', '★ 提示', 'C级·个人设计师'),
    '庞中华':   ('庞中华', '★ 提示', 'C级·著名书法家'),
    '丁卯':     ('丁卯', '★ 提示', 'C级·个体字库'),
}

# ─── 5. 风险比对与输出 ───
print("=" * 60)
print("DOCX 字体元数据解析报告")
print("=" * 60)

# 5a. 按来源分类输出
print("\n【一、文档内直接引用的字体 (document.xml / styles.xml)】")
if doc_fonts:
    for fnt in sorted(doc_fonts.keys()):
        sources = '、'.join(doc_fonts[fnt])
        print(f"  - {fnt}  （来源：{sources}）")
else:
    print("  （未在文档/样式中定义字体）")

print("\n【二、主题字体 (theme1.xml)】")
if theme_fonts:
    for scheme, ft in theme_fonts.items():
        print(f"  Scheme: {scheme}")
        for role, fnt in sorted(ft.items()):
            if fnt:
                print(f"    {role}: {fnt}")
else:
    print("  （无主题字体定义）")

# 5b. 去重合并 + 风险比对
print("\n【三、字体版权风险比对】")
print("-" * 60)

# 排除主题引用占位符（如 majorEastAsia）
THEME_PLACEHOLDERS = {'majorEastAsia', 'majorHAnsi', 'minorEastAsia', 'minorHAnsi',
                       'majorBidi', 'minorBidi', 'majorFont', 'minorFont'}

hit_count = 0
clean_count = 0
for fnt_name in sorted(all_fonts):
    if fnt_name in THEME_PLACEHOLDERS:
        continue  # 跳过占位符，由下方"未解析"提示
    
    matched = False
    for kw, (owner, star, note) in RISK_LIB.items():
        if kw in fnt_name:
            print(f"  ⚠ [{star}] {fnt_name}")
            print(f"     → 权利主体: {owner}")
            print(f"     → 说明: {note}")
            print(f"     → 处置: {'须提供正版商用授权凭证' if '★★★' in star else '须核实商用授权状态'}")
            hit_count += 1
            matched = True
            break
    
    if not matched:
        # 检查是否为低风险字体
        safe_fonts = {'Calibri', 'Cambria', 'Arial', 'Times New Roman', 'Courier', 
                      'Courier New', '宋体', 'SimSun', '黑体', 'SimHei', '楷体', 'KaiTi',
                      '思源黑体', '思源宋体', 'Source Han Sans', 'Source Han Serif',
                      '阿里巴巴普惠体', 'HarmonyOS Sans'}
        if fnt_name in safe_fonts:
            print(f"  ✓ {fnt_name} → 通用/免费字体，无风险")
            clean_count += 1
        else:
            print(f"  ? {fnt_name} → 未命中风险库 → [转人工] 核实授权状态")
            clean_count += 1

print("-" * 60)
print(f"  命中风险字体: {hit_count} 个")
print(f"  安全/待确认:   {clean_count} 个")

# 5c. 主题引用未解析提示
theme_refs = [f for f in all_fonts if f in THEME_PLACEHOLDERS]
if theme_refs:
    print(f"\n  ⚡ 注意: 以下为主题引用占位符，实际字体已解析在上方主题字体列表中: {', '.join(sorted(theme_refs))}")

print("\n" + "=" * 60)
print("解析完成。将上述命中结果纳入审查报告的「字体风险扫描结果」栏。")
```

---

## 四、在审查工作流中的集成规则

### 触发条件

当同时满足以下条件时，在 Step2（风险识别）阶段**自动执行**本模块：

| 条件 | 说明 |
|:---|:---|
| 用户提供的物料文件扩展名为 `.docx` | 通过文件路径后缀判断 |
| 文件存在于本地磁盘 | 先 `ls` 确认文件存在 |

### 执行步骤

1. 将脚本写入临时文件或以 heredoc 方式传入 Python（推荐后者，不落盘）
2. 调用 `"C:/Program Files/Python312/python.exe" << 'PYEOF' ... PYEOF`
3. 读取 stdout 输出，提取"三、字体版权风险比对"段落的命中项
4. 将命中字体名、权利主体、星级写入审查报告 `## 一、审查基本信息` 的「字体风险扫描结果」栏
5. 对应的 ★★★ 项同时追加到 `## 二、风险识别结果` 中（维度标注为「字体版权」）

### 输出映射规则

```
stdout: ⚠ [★★★] 汉仪旗黑
       → 权利主体: 北京汉仪创新科技股份有限公司

报告输出:
  字体风险扫描结果：
  - "汉仪旗黑" → 北京汉仪创新科技(S级·全系列) → ★★★ 阻断，须正版商用授权

  风险识别结果（追加）：
  - [★★★] 字体版权｜"汉仪旗黑"属汉仪(S级·全系列)，须正版商用授权
```

### 多重覆盖原则

本模块的提取结果与以下两项**并行叠加**，不互斥：
- 用户⑤中手动声明的字体（SKILL.md 交互规则第⑤项）
- 文本内容中出现的字体名称字符串（SKILL.md 字体主动识别机制）

同一个字体若被多个来源命中，只报告一次即可。

---

## 五、常见边界情况处理

| 场景 | 表现 | 处理方式 |
|:---|:---|:---|
| DOCX 文件损坏/无法打开 | Python 抛异常 | 仅输出「字体风险扫描结果: 文件无法解析，[转人工]核实」 |
| 主题引用占位符（majorEastAsia 等） | 不是真实字体名 | 脚本已跳过，不输出为风险项 |
| 文档仅含西文字体（Calibri 等） | 无中文字体风险 | 正常输出"通用/免费字体，无风险" |
| Python 命令不可用 | 无 python/python3 | 降级：跳过 DOCX 字体解析，仅做文本字符串扫描 |
| 字体名命中多个关键词 | 如"方正汉仪混排" | 注意：上述脚本用 `if kw in fnt_name` + `break` 仅匹配第一个；若需全量匹配，去掉 `break` |
| 文档定义了字体但用户可能在另一台电脑查看（字体回退） | 实际渲染字体 ≠ 定义字体 | 本模块基于文档**定义**扫描，不依赖渲染环境，此回退不影响扫描结果 |

---

## 六、与现有 skill 的衔接点

| 现有机制 | 本模块增量 |
|:---|:---|
| SKILL.md 第42行：Step2 字体主动识别——扫描输入物料文本 | **补充**：若物料为 .docx，额外解析 XML 元数据 |
| SKILL.md 第73行：要点F "主动扫描输入物料中出现的字体名称" | **补充**：扫描范围从"文本字符串"扩展到"文档元数据" |
| references/font-copyright-table.md | 复用同一个版权库进行比对，保持星级一致 |
| 报告输出格式 | 不新增字段，直接写入现有「字体风险扫描结果」栏 |

---

## 七、版本记录

| 日期 | 版本 | 变更 |
|:---|:---|:---|
| 2026-07-06 | v1.0 | 初版，基于「医疗器械广告违规测试样本.docx」中发现的"汉仪旗黑"漏扫问题创建 |
