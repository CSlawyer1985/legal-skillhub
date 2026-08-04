# 模块B：要素式起诉状起草

## B1. 覆盖案由（34个专属模板 + 1个通用模板）

本模块支持34个专属起诉状模板 + 1个通用民事起诉状的起草；其中 3 个为行政起诉状，其余为民事起诉状或民事类通用模板：

| 序号 | 案由                               | 模板文件                                         |
| :--: | :--------------------------------- | :----------------------------------------------- |
|  00  | **通用民事起诉状**（非标案由使用） | `assets/template-00-general-civil.md`            |
|  01  | 民间借贷纠纷                       | `assets/template-01-private-lending.md`          |
|  02  | 离婚纠纷                           | `assets/template-02-divorce.md`                  |
|  03  | 买卖合同纠纷                       | `assets/template-03-sales-contract.md`           |
|  04  | 金融借款合同纠纷                   | `assets/template-04-financial-loan.md`           |
|  05  | 物业服务合同纠纷                   | `assets/template-05-property-service.md`         |
|  06  | 银行信用卡纠纷                     | `assets/template-06-credit-card.md`              |
|  07  | 机动车交通事故责任纠纷             | `assets/template-07-traffic-accident.md`         |
|  08  | 劳动争议纠纷                       | `assets/template-08-labor-dispute.md`            |
|  09  | 融资租赁合同纠纷                   | `assets/template-09-finance-lease.md`            |
|  10  | 保证保险合同纠纷                   | `assets/template-10-guarantee-insurance.md`      |
|  11  | 证券虚假陈述责任纠纷               | `assets/template-11-securities-fraud.md`         |
|  12  | 继承纠纷                           | `assets/template-12-inheritance.md`              |
|  13  | 行政纠纷（行政起诉状）             | `assets/template-13-administrative.md`           |
|  14  | 医疗损害责任纠纷                   | `assets/template-14-medical-dispute.md`          |
|  15  | 房屋买卖合同纠纷                   | `assets/template-15-real-estate.md`              |
|  16  | 公司企业纠纷                       | `assets/template-16-company-equity.md`           |
|  17  | 建设工程施工合同纠纷               | `assets/template-17-construction-contract.md`    |
|  18  | 知识产权侵权纠纷                   | `assets/template-18-intellectual-property.md`    |
|  19  | 人格权与网络侵权纠纷               | `assets/template-19-personality-internet.md`     |
|  20  | 征地拆迁纠纷（行政起诉状）         | `assets/template-20-land-demolition.md`          |
|  21  | 环境污染责任纠纷                   | `assets/template-21-environmental-protection.md` |
|  22  | 涉外民商事纠纷                     | `assets/template-22-foreign-related.md`          |
|  23  | 保险理赔纠纷                       | `assets/template-23-insurance-claim.md`          |
|  24  | 基金投资纠纷                       | `assets/template-24-fund-investment.md`          |
|  25  | 私募基金纠纷                       | `assets/template-25-private-fund.md`             |
|  26  | 信托纠纷                           | `assets/template-26-trust-dispute.md`            |
|  27  | 房屋租赁合同纠纷                   | `assets/template-27-house-lease.md`              |
|  28  | 人身损害赔偿纠纷                   | `assets/template-28-personal-injury.md`          |
|  29  | 专利侵权纠纷                       | `assets/template-29-patent-dispute.md`           |
|  30  | 商业秘密侵权纠纷                   | `assets/template-30-trade-secret.md`             |
|  31  | 公司解散清算纠纷                   | `assets/template-31-company-dissolution.md`      |
|  32  | 政府信息公开纠纷（行政起诉状）     | `assets/template-32-government-info.md`          |
|  33  | 涉外送达程序纠纷                   | `assets/template-33-foreign-service.md`          |
|  34  | 消费权益纠纷                       | `assets/template-34-consumer-rights.md`          |

## B2. 三步工作流

**收敛上下文接收**: 若从 `shared-intent-convergence.md` 收敛协议进入（输入开头含`【意图收敛摘要】`），案由已由收敛确定，跳过第一步的案由识别，直接进入第二步追问，并用摘要中已提取事实预填追问项。

### 第一步：案由识别

收到案情描述后，判断属于以下哪个案由。各案由与模板对应关系参见上表（B1），通用场景自动切换通用模板。

**参考文件：** 各案由模块速览位于 `references/` 目录，如 `references/case-01-private-lending.md`

### 第二步：关键信息追问

**原则：一次性追问，等齐了再写。**

#### 通用必填项

**原告信息：** 姓名、性别、身份证号/统一社会信用代码、联系电话、住所地、经常居住地、是否有委托诉讼代理人

**被告信息：** 姓名、性别、身份证号/统一社会信用代码、联系电话、住所地

**送达地址：** 地址、收件人、电话、是否接受电子送达

#### 各案由专项追问清单

各案由具体的追问清单详见 `references/` 目录下的对应模块速览文件。例如 `references/case-01-private-lending.md` 中详细列出了民间借贷纠纷每个表格行（Row）的填写要求和追问项。

#### 追问话术模板

```
我确认这是【案由】，准备动笔。还需要您确认几个信息：

1. 【问题1】——【为什么需要这个信息】
2. 【问题2】——【为什么需要这个信息】
3. 【问题3】——【为什么需要这个信息】

您告诉我后我直接生成完整的起诉状给您。
```

#### 关键注意点

- **数据一致性核对**：用户说"儿子10岁"但出生年份2005年→实际21岁，主动计算并核实
- **日常用语转化**："净身出户"→具体财产分配方案；"感觉他出轨了"→追问具体证据
- **身份证号/手机号校验**：身份证18位、手机11位，不足则追问
- **"有借条"vs"口头约定"**：证明力不同，追问具体形式

### 第三步：模板填充与输出

#### 输出边界

- 最终输出起诉状草稿或 DOCX 生成说明时，必须附加 `references/shared-disclaimer.md` 的免责声明要点。
- 必须明确标注：起诉状草稿仅供参考，提交法院前建议由执业律师审核。
- 不得承诺立案、胜诉、赔偿金额或法院裁判结果。

#### 技术环境

优先使用 `python-docx` 包；未安装时，`scripts/generate_complaint_docx.py` 会自动使用 Python 标准库生成最小可打开的 `.docx`：

```bash
pip install python-docx
```

可执行脚本入口：

```bash
python scripts/generate_complaint_docx.py --case 01 --dry-run
python scripts/generate_complaint_docx.py --case 01 --output private-lending.docx
python scripts/generate_complaint_docx.py --case 01 --data examples/private-lending-data.json --output private-lending-filled.docx
```

#### 从零创建 DOCX

设计原则：`assets/template-*.md` 是起诉状的结构描述文件（纯文本 Markdown），不是加密 DOCX。运行时读取对应模板理解表格模块划分，再读取 `references/case-*.md` 获得精确的行数列数和追问规则，用 python-docx 从零构建 DOCX。

**创建流程：**

1. 按 B1 映射读取 `assets/template-{编号}-{slug}.md` 了解表格模块划分（当事人信息 / 诉讼请求 / 事实和理由 / 证据清单等）
2. 读取对应 `references/case-{编号}-{slug}.md` 获得每模块的精确行数、列数、标签文字和追问项
3. `doc = Document()` 创建空白文档
4. 添加标题「民事起诉状」+ 副标题「（案由）」
5. 按 `case-*.md` 的模块结构逐模块创建表格，左列写标签，右列预填占位符
6. 用下方的通用填充函数将用户信息填入右列单元格

**通用创建代码：**

```python
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def create_element_complaint_docx(modules, output_path):
    """
    从零创建要素式起诉状 DOCX。
    modules: [(module_title, rows), ...]
        rows: [(label, placeholder), ...] —— 每行 (左列标签, 右列占位)
    """
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = '仿宋'
    style.font.size = Pt(12)
    style.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), '仿宋')

    # 标题
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run('民事起诉状')
    run.font.size = Pt(16)
    run.bold = True

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = subtitle.add_run('（{{案由}}）')
    run2.font.size = Pt(14)

    # 逐模块建表
    for mod_title, rows in modules:
        if mod_title:
            h = doc.add_paragraph()
            h.add_run(mod_title).bold = True
        table = doc.add_table(rows=len(rows), cols=2, style='Table Grid')
        for i, (label, placeholder) in enumerate(rows):
            table.cell(i, 0).text = label
            table.cell(i, 1).text = placeholder  # 占位，后续用 fill_cell_clear 替换

    doc.save(output_path)
    return doc
```

**调用示例（民间借贷）：**

```python
modules = [
    ("当事人信息", [
        ("原告", "姓名：  性别：  出生日期：  民族：  联系电话：  住所地：  证件号码："),
        ("被告", "姓名：  性别：  出生日期：  民族：  联系电话：  住所地："),
        ("送达地址", "地址：  收件人：  电话：  是否接受电子送达："),
    ]),
    ("诉讼请求", [
        ("1. 借款本金", "人民币  元"),
        ("2. 利息", "自  年  月  日起按年利率  %计算至实际清偿日"),
        ("3. 实现债权费用", "律师费  元、保全费  元等"),
        ("4. 诉讼费", "由被告承担"),
    ]),
    ("事实和理由", [
        ("借款合意", "双方于  年  月  日达成借款合意（借条/借款合同/微信记录），约定……"),
        ("款项交付", "原告于  年  月  日通过（银行转账/微信/现金）交付  元"),
        ("借款期限", "约定借款期限自  年  月  日至  年  月  日"),
        ("还款情况", "被告还款情况：……"),
        ("催收情况", "逾期后原告于  年  月  日通过（微信/短信/电话）催收"),
    ]),
    ("证据清单", [
        ("1", "借条/借款合同"),
        ("2", "银行转账记录/微信转账截图"),
        ("3", "催收记录（短信/微信聊天记录）"),
        ("4", "原告身份证复印件"),
    ]),
]
doc = create_element_complaint_docx(modules, "民间借贷纠纷-民事起诉状-张三诉李四.docx")

# —— 以下用通用填充函数将真实数据填入右列 ——
fill_cell_clear(doc.tables[0].cell(0, 1),
    ["张三，男，1985年3月15日生，汉族，138XXXX，住北京市朝阳区XX路XX号，11010119850315XXXX"])
fill_cell_clear(doc.tables[0].cell(1, 1),
    ["李四，男，1982年7月20日生，汉族，139XXXX，住北京市海淀区XX路XX号"])
# ... 逐格填充
doc.save("民间借贷纠纷-民事起诉状-张三诉李四.docx")
```

> 各案由的精确 modules 结构请查阅 B1 对应的 `references/case-{编号}-{slug}.md` 文件。

#### 通用填充函数

```python
from docx import Document
import shutil, os

def fill_cell_clear(cell, texts_list):
    """清空单元格所有内容，重新填入多行文本"""
    # 第一步：清空所有段落文本
    for para in cell.paragraphs:
        for run in para.runs:
            run.text = ''
    if not texts_list:
        return
    # 第二步：移除多余的空白段落（保留第一个）
    while len(cell.paragraphs) > 1:
        last_para = cell.paragraphs[-1]
        last_para._element.getparent().remove(last_para._element)
    # 第三步：填入数据
    p0 = cell.paragraphs[0]
    p0.text = texts_list[0]  # 直接设置文本（自动清空原有 run）
    for ti in range(1, len(texts_list)):
        cell.add_paragraph(texts_list[ti])

def fill_paragraph(doc, keyword, new_text):
    """修改文档段落（用于具状人/日期）"""
    for para in doc.paragraphs:
        if keyword in para.text:
            for run in para.runs:
                run.text = ''
            if para.runs:
                para.runs[0].text = new_text
            return True
    return False
```

#### 通用填充规则

1. **标题不动** — 第一行"民事起诉状"、第二行"（案由）"保持原样
2. **左列不动** — 表格左列是字段标签，不改
3. **内容填右列** — 具体列号因案由而异（见各案由模块速览）
4. **勾选处理**：选中项`☐`改成`☑`，未选项保持`☐`不变
5. **日期格式**：YYYY年MM月DD日

#### 具状人/日期修改（右对齐）

```python
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_right_align(para):
    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pPr = para._element.find(qn('w:pPr'))
    if pPr is None:
        pPr = OxmlElement('w:pPr')
        para._element.insert(0, pPr)
    jc = pPr.find(qn('w:jc'))
    if jc is None:
        jc = OxmlElement('w:jc')
        pPr.append(jc)
    jc.set(qn('w:val'), 'right')

# 修改具状人段落
for para in doc.paragraphs:
    if "具状人" in para.text:
        for run in para.runs:
            run.text = ""
        if para.runs:
            para.runs[0].text = f"具状人(签字、盖章): {原告姓名}"
        set_right_align(para)
        break

# 修改日期段落
for para in doc.paragraphs:
    if "日期" in para.text:
        for run in para.runs:
            run.text = ""
        if para.runs:
            para.runs[0].text = f"日期：{起诉日期}"
        set_right_align(para)
        break
```

#### 文件命名规则

```
{案由}-民事起诉状-{原告名}诉{被告名}.docx
```

示例：`民间借贷纠纷-民事起诉状-李四诉张三.docx`

#### 自检清单（发出前必查）

1. ☐ 案由判断正确？
2. ☐ 所有关键信息已获取？
3. ☐ 原告信息完整？（姓名/性别/出生日期/民族/联系电话/住所地/证件号码）
4. ☐ 被告信息完整？
5. ☐ 送达地址已填？
6. ☐ 各案由特有的诉讼请求项已填？
7. ☐ 各案由特有的事实和理由项已填？
8. ☐ 具状人签字+日期已更新？
9. ☐ 证据清单已填？
10. ☐ 文件命名符合规则？
11. ☐ ☑勾选正确？（选中项为☑，未选项保持☐）

## B3. 异常场景处理

#### 3.1 用户描述模糊时

情况：用户只说"帮我写诉状"但不给具体案情。

```
我帮您写起诉状，需要先确认两个信息：
1. 您遇到的是什么类型的纠纷？（比如：借钱不还/离婚/买卖纠纷/租房纠纷/劳动纠纷/交通事故等）
2. 能简单描述一下事情经过吗？
```

如果用户继续模糊：

```
我理解您比较着急，但诉状需要根据具体情况来写，信息越详细，写出来的诉状越精准。
您最少需要告诉我：
（1）对方（被告）是谁？
（2）发生了什么事？
（3）您想要什么结果？
```

#### 3.2 用户描述指向多个案由（竞合）

情况：如"买东西对方没给货也不退钱"——可能同时涉及买卖合同纠纷和不当得利。

**处理方式：** 判断哪个案由对用户最有利，告知选择权。

```
根据您的描述，这个情况可能涉及两种法律关系：
1. **买卖合同纠纷** — 主张继续履行或解除合同返还货款
2. **不当得利纠纷** — 主张返还已支付的货款

买卖合同纠纷适用于您有明确合同约定的情况，能主张违约金；
不当得利适用于合同无效或不存在的情况。

建议按**买卖合同纠纷**处理，证据要求更明确。
如不确定，可按买卖合同+不当得利预备性请求一并主张。
```

#### 3.3 用户同时提出多个独立纠纷

情况：如"朋友欠我5万不还，同时我们又因装修合同吵了"

**处理方式：** 不同法律关系不能合并起诉，需分别立案。

```
您提到的两个问题涉及**不同的法律关系**，不能放在同一份起诉状中：
1. **民间借贷纠纷** — 朋友的5万借款
2. **承揽合同纠纷** — 装修合同争议

需要分别起草两份起诉状。我们先处理哪个？
```

#### 3.4 用户要求做胜诉承诺

情况：用户问"我这个情况能胜诉吗？"

**处理方式：** 坚决不做胜诉承诺，改为客观分析。

```
根据法律规定，律师/法律助手不能对案件结果做出承诺。
我帮您分析一下这个案子的有利因素和风险点：

**有利因素：**
- 您有明确的借条和转账记录
- 对方已逾期超过半年

**风险提示：**
- 注意3年诉讼时效是否已过
- 对方名下有无可供执行的财产

是否起诉、胜诉与否，最终由法院根据证据判决。
建议您携带完整材料咨询执业律师获取专业意见。
```

#### 3.5 用户请求非民事起诉状文书

情况：用户请求刑事辩护词、刑事控告材料、行政复议申请、涉外文书等不适合直接套用民事起诉状模板的文书。

**处理方式：** 先识别是否存在民事赔偿或民事诉讼请求；可提供基础法律分析、材料清单和流程指引，但不得把刑事辩护词等文书强行套入民事起诉状模板。

```
您提出的【XX问题】不适合直接使用民事起诉状模板生成。
建议您：
（1）先确认是否存在可单独主张的民事赔偿、合同、侵权或财产返还请求
（2）如涉及刑事案件，我可以提供基础法律框架、流程节点和材料清单参考
（3）正式辩护文书、控告材料或提交机关前的版本，建议由对应领域执业律师审核

对于重大刑事案件或已被采取强制措施的案件，建议尽快委托律师介入。
```

#### 3.6 用户不愿提供个人信息

情况：用户拒绝提供姓名、身份证号等信息。

**处理方式：** 告知信息的必要性，提供替代方案。

```
以下信息是起诉状**必备**的，缺少无法立案：
- 原告姓名+身份证号 — 法院立案必须实名
- 被告姓名/名称 — 否则法院无法确定被告

如果您暂时不方便提供真实姓名，我可以：
（1）先给您**法律咨询意见**，不生成正式诉状
（2）用"XXX"替代生成**参考草稿**，您自己填入真实信息
```

#### 3.7 模板文件损坏或缺失

情况：assets/目录下模板文件（.md格式）被误删或损坏。

**处理方式：**

1. 使用通用模板作为兜底方案（如果有备份）
2. 告知用户无法生成docx格式，改为输出**纯文本/RTF格式起诉状**供用户手动排版
3. 引导用户重新下载Skill包获取完整模板

---

## B4. 常见坑点与防范（Pitfalls）

### 数据一致性

- 用户给的年龄和出生日期可能矛盾，每次自己算一遍当前年龄核实
- 身份证号/手机号位数不足时追问完整号码

### 日常用语转法律语言

- "净身出户" → 具体财产分配方案
- "催款" → 转化为正式法律用语"主张债权"或"催收欠款"
- "一毛没还" → "未偿还任何本金或利息"
- "感觉他出轨了" → 不是法律证据，追问具体证据形式

### 模板填充技术

- **不要用查找替换**（文本被拆分到多个run中），用清空重写法
- 具状人和日期**必须右对齐**
- 标题**不动**（第一行+第二行）

---

## B5. 通用民事起诉状起草（非标准案由）

当用户描述的案由**不在34个专属模板范围内**时，使用通用民事起诉状模板（`assets/template-00-general-civil.md`）生成起诉状。

### 适用场景示例

| 场景                | 说明                          |
| :------------------ | :---------------------------- |
| 服务合同纠纷        | 中介/咨询/培训等服务费拖欠    |
| 相邻关系纠纷        | 采光/噪音/漏水等邻里纠纷      |
| 产品责任纠纷        | 产品质量缺陷导致人身/财产损害 |
| 名誉权/隐私权纠纷   | 网络诽谤/隐私泄露             |
| 合伙协议纠纷        | 合伙经营亏损/退伙/解散清算    |
| 承揽合同/运输合同等 | 其他无名合同纠纷              |

### 通用起诉状工作流程

#### 第一步：案由确认与告知

告知用户该案由不属于34个专属模板范围，将使用通用模板：

```
您描述的【服务合同纠纷】不在34个专属模板范围内，
我将使用**通用民事起诉状模板**为您起草，格式为传统段落式，
需手动撰写事实和理由内容。
```

#### 第二步：关键信息追问

**通用必填项：**

1. **原告信息** — 姓名、性别、出生日期、民族、工作单位、住所地、联系方式、证件号码
2. **被告信息** — 姓名/名称、性别、出生日期（自然人）、住所地
3. **委托诉讼代理人** — 如有则追问代理人信息
4. **诉讼请求** — 具体请求什么（请求类型+金额+计算方式）
5. **事实经过** — 争议发生的时间线、关键节点
6. **法律依据** — 用户是否清楚适用的法律（如有，追问具体法条）
7. **证据情况** — 有什么证据（合同、收据、聊天记录、转账凭证等）
8. **管辖法院** — 应向哪个法院起诉（被告住所地/合同履行地/侵权行为地等）
9. **被告人数** — 确定副本份数

#### 第三步：模板填充

通用模板为纯段落格式（非表格），填充方式与要素式不同：

```python
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from datetime import datetime

def create_generic_complaint_docx(info: dict, output_path: str) -> Document:
    """
    从零创建通用民事起诉状 DOCX。
    读取 assets/template-00-general-civil.md 理解段落结构后，用此函数从零构建。

    info 字段:
        case_type:   案由（如"房屋租赁合同纠纷"）
        plaintiff:   原告信息段落（含姓名/性别/出生日期/民族/单位/住址/联系方式/证件号）
        defendant:   被告信息段落
        agent:       委托诉讼代理人段落（可为空，为空时自动跳过）
        claims:      诉讼请求（多行文本）
        facts:       事实和理由正文
        evidence:    证据清单文本
        court:       管辖法院全称
        copies:      副本份数（被告人数+1）
        plaintiff_name: 具状人签名用姓名
    """
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = '仿宋'
    style.font.size = Pt(12)
    style.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), '仿宋')

    # 标题
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run('民事起诉状')
    run.font.size = Pt(16)
    run.bold = True

    # 当事人信息
    doc.add_paragraph(f"原告：{info['plaintiff']}")
    doc.add_paragraph(f"被告：{info['defendant']}")
    if info.get('agent'):
        doc.add_paragraph(f"委托诉讼代理人：{info['agent']}")

    # 诉讼请求
    doc.add_paragraph()
    h = doc.add_paragraph()
    h.add_run('诉讼请求：').bold = True
    for line in info['claims'].strip().split('\n'):
        doc.add_paragraph(line.strip())

    # 事实和理由
    doc.add_paragraph()
    h2 = doc.add_paragraph()
    h2.add_run('事实和理由：').bold = True
    doc.add_paragraph(info['facts'])

    # 证据
    doc.add_paragraph()
    h3 = doc.add_paragraph()
    h3.add_run('证据和证据来源，证人姓名和住所：').bold = True
    doc.add_paragraph(info['evidence'])

    # 管辖法院
    doc.add_paragraph()
    doc.add_paragraph(f"此致")
    court_para = doc.add_paragraph(info['court'])
    court_para.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # 副本
    doc.add_paragraph()
    doc.add_paragraph(f"附：本诉状副本 {info['copies']} 份")

    # 具状人 + 日期（右对齐）
    today = datetime.now().strftime("%Y年%m月%d日")
    sign = doc.add_paragraph(f"起诉人：{info['plaintiff_name']}（签字、盖章）")
    sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    date = doc.add_paragraph(today)
    date.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.save(output_path)
    return doc


# ===== 调用示例 =====
info = {
    "case_type": "房屋租赁合同纠纷",
    "plaintiff": "张三，男，1985年3月15日生，汉族，XX公司职员，住北京市朝阳区XX路XX号。联系方式：138XXXXXXXX。证件号码：11010119850315XXXX",
    "defendant": "李四，男，1982年7月20日生，汉族，无业，住北京市海淀区XX路XX号。联系方式：139XXXXXXXX",
    "agent": "",  # 无代理人则留空
    "claims": """(1) 判令被告向原告支付拖欠的租金人民币XX元；
(2) 判令被告支付逾期付款利息（以XX元为基数，按LPR计算，自XX年XX月XX日起至实际清偿之日止）；
(3) 本案诉讼费用由被告承担。""",
    "facts": "（此处根据用户陈述撰写事实经过，按时间线叙述）",
    "evidence": "1. 房屋租赁合同；2. 租金支付记录；3. 催收聊天记录",
    "court": "北京市朝阳区人民法院",
    "copies": "2",
    "plaintiff_name": "张三",
}
create_generic_complaint_docx(info, "房屋租赁合同纠纷-民事起诉状-张三诉李四.docx")
```

#### 第四步：文件命名与输出

```
{案由}-民事起诉状-{原告名}诉{被告名}.docx
```

示例：`房屋租赁合同纠纷-民事起诉状-张三诉李四.docx`

### 通用 vs 要素式模板的区别

| 对比维度 | 要素式起诉状                           | 通用民事起诉状                         |
| :------- | :------------------------------------- | :------------------------------------- |
| 格式     | 表格化，逐项勾选填写                   | 段落式，自由行文                       |
| 结构     | 固定模块（说明/当事人/请求/事实/证据） | 传统结构（当事人→请求→事实→证据→法院） |
| 适合场景 | 标准案由，批量处理                     | 任意民事案由，灵活行文                 |
| 技术操作 | 按单元格/行号填充                      | 按段落关键词替换                       |
| 法律术语 | 表格引导，标准化表述                   | 需手动撰写事实理由                     |
| 模板文件 | 对应案由模板文件                       | `assets/template-00-general-civil.md`  |
| 参考文件 | 对应案由模块速览                       | `references/case-00-general-civil.md`  |

---

## B6. FAQ 常见问题解答

### Q1: 这个Skill能帮我打官司吗？

不能。本Skill提供的是**法律咨询意见**和**起诉状起草工具**，不代理案件。AI不能代替律师出庭。具体案件代理需要委托执业律师。

### Q2: 生成的起诉状可以直接提交法院吗？

要素式起诉状填好后**可以作为草稿提交**有管辖权的法院立案。**提交前建议由执业律师审核一遍**，确保诉讼请求、事实理由、证据清单完整无遗漏。通用起诉状需手动完善事实和理由内容。

### Q3: 为什么生成的起诉状有些字段是空的？

追问时用户未提供相关信息，或该信息在特定案由中为可选项。建议尽量补充完整，信息越全越有利于立案。

### Q4: 我描述案情时需要注意什么？

- **尽量详细** — 时间、地点、人物、金额、经过越清楚越好
- **分清当事人** — 谁是原告、谁是被告
- **提供证据类型** — 合同/借条/聊天记录/转账记录/照片等
- **明确诉求** — 想要什么结果（还钱/赔偿/离婚/解除合同等）

### Q5: 起诉需要准备什么材料？

一般需要：起诉状+证据材料+原告身份证明+被告信息。具体以受诉法院要求为准。

### Q6: 起诉要花多少钱？

案件受理费根据诉讼标的额计算（财产案件按比例缴纳），具体标准可查询《诉讼费用交纳办法》。符合条件可申请缓交、减交或免交。

### Q7: 这个Skill的法律依据有多新？

严格依据**中华人民共和国现行有效法律**，法律修订后持续同步更新。本Skill内置 `scripts/flk_npc_client.py`（封装全国人大官方 flk.npc.gov.cn 的 `/law-search/` API），在回答法律问题时优先调用官方 API 获取实时法条数据；API 不可用时降级到 AI 训练知识库，确保法条引用的准确性和时效性。具体适用请以官方最新文本及司法实践为准。

### Q8: 起诉有时间限制吗？

有。**诉讼时效**一般为**3年**（民法典第188条），自知道或应当知道权利受损害之日起计算。劳动争议仲裁时效为**1年**。超过时效可能丧失胜诉权。具体请以法律规定为准。

### Q9: 要素式起诉状和普通起诉状有什么区别？

要素式起诉状是最高人民法院推行的标准化模板，采用**表格形式**逐项勾选填写，结构清晰、立案便捷。普通起诉状是传统**段落式**格式，自由行文但格式不规范可能被退回。本Skill同时支持两种格式。

### Q10: 34个专属模板指的是什么？

本Skill针对34类高频案由分别提供了要素式专属模板（case-01至case-34，其中3类为行政起诉状：case-13/20/32，其余为民事起诉状），涵盖民间借贷、离婚、买卖、金融借款、物业服务、信用卡、交通事故、劳动争议、融资租赁、保证保险、证券虚假陈述、继承、行政诉讼、医疗纠纷、商品房买卖、股权转让、建设工程、知识产权、网络侵权、征地拆迁、环境保护、保险理赔、基金投资、私募基金、信托、房屋租赁、人身损害、专利、商业秘密、公司解散、政府信息、涉外服务、消费权益等。非上述34类的案由使用通用模板（template-00）。

### Q11: 起诉状里的事实和理由怎么写？

遵循"一事一理"原则：

- **事实**按时间线叙述：什么时间、什么人、做了什么事、产生了什么后果
- **理由**引用法律依据：结合事实指出对方违反了哪条法律、应承担什么责任
- 语言简洁、条理清晰、重点突出

### Q12: 没有证据也能起诉吗？

可以起诉，但胜诉可能性较低。**"谁主张谁举证"**是基本原则。建议在起诉前尽量收集相关证据。如果证据被对方掌握，可申请法院责令对方提交。

---
