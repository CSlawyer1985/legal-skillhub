"""
技术交底书智能解析模块 (Module A)
支持格式：Word (.docx), PDF (.pdf), 纯文本 (.txt), Markdown (.md), XML (.xml)
功能：自动提取技术领域、技术问题、技术方案、技术特征、实施例、有益效果
"""

import re
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# 尝试导入可选依赖
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


@dataclass
class DisclosureElements:
    """技术交底书结构化要素"""
    tech_field: str = ""                    # 技术领域文本
    tech_field_ipc: List[str] = None        # 推荐IPC分类号列表
    tech_problems: List[str] = None          # 技术问题列表
    tech_scheme: str = ""                    # 技术方案文本
    tech_features: List[str] = None          # 技术特征列表
    examples: List[Dict] = None              # 实施例列表（含参数）
    beneficial_effects: List[Dict] = None    # 有益效果列表（带问题关联）
    compliance_warnings: List[Dict] = None    # 合规警告

    def __post_init__(self):
        if self.tech_field_ipc is None:
            self.tech_field_ipc = []
        if self.tech_problems is None:
            self.tech_problems = []
        if self.tech_features is None:
            self.tech_features = []
        if self.examples is None:
            self.examples = []
        if self.beneficial_effects is None:
            self.beneficial_effects = []
        if self.compliance_warnings is None:
            self.compliance_warnings = []


@dataclass
class ST26Sequence:
    """WIPO ST.26 序列表结构化要素"""
    sequence_id: int = 0                     # 序列ID
    seqid_no: str = ""                       # 序列标识号
    length: int = 0                           # 序列长度
    molecule_type: str = ""                   # 分子类型 (DNA/RNA/AA)
    organism: str = ""                        # 源生物体
    division: str = ""                       # 部分号
    features: List[Dict] = None               # 特性注释
    sequence_data: str = ""                  # 序列数据
    warnings: List[str] = None                # 警告/问题

    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class ST26SequenceListing:
    """WIPO ST.26 完整序列表"""
    application_number: str = ""
    filing_date: str = ""
    applicant_file_reference: str = ""
    applicant_name: str = ""
    invention_title: str = ""
    sequence_total_quantity: int = 0
    sequences: List[ST26Sequence] = None
    validation_warnings: List[str] = None

    def __post_init__(self):
        if self.sequences is None:
            self.sequences = []
        if self.validation_warnings is None:
            self.validation_warnings = []

    def to_dict(self) -> Dict:
        return {
            "application_number": self.application_number,
            "filing_date": self.filing_date,
            "applicant_file_reference": self.applicant_file_reference,
            "applicant_name": self.applicant_name,
            "invention_title": self.invention_title,
            "sequence_total_quantity": self.sequence_total_quantity,
            "sequences": [
                {
                    "sequence_id": s.sequence_id,
                    "seqid_no": s.seqid_no,
                    "length": s.length,
                    "molecule_type": s.molecule_type,
                    "organism": s.organism,
                    "division": s.division,
                    "features": s.features,
                    "sequence_data": s.sequence_data,
                    "warnings": s.warnings
                }
                for s in self.sequences
            ],
            "validation_warnings": self.validation_warnings
        }

    def to_dict(self) -> Dict:
        return {
            "tech_field": self.tech_field,
            "tech_field_ipc": self.tech_field_ipc,
            "tech_problems": self.tech_problems,
            "tech_scheme": self.tech_scheme,
            "tech_features": self.tech_features,
            "examples": self.examples,
            "beneficial_effects": self.beneficial_effects,
            "compliance_warnings": self.compliance_warnings
        }


class IPCKeywordDict:
    """IPC分类号关键词映射库（示例，完整版需扩充）"""

    IPC_KEYWORDS = {
        "A23F3/00": ["茶叶", "茶", "咖啡", "苦味", "涩味", "提取", "浸提", "茶多酚", "儿茶素"],
        "A23F3/06": ["茶叶加工", "绿茶", "红茶", "普洱", "发酵", "干燥", "萎凋"],
        "A23F3/08": ["茶叶提取物", "茶汤", "茶粉", "速溶茶", "浓缩茶"],
        "A23L2/00": ["饮料", "果汁", "碳酸饮料", "功能性饮料", "提取物"],
        "A61K36/00": ["中药", "植物提取", "天然产物", "黄酮", "皂苷", "多糖"],
        "C12N1/00": ["微生物", "发酵", "酶解", "酵母", "细菌", "真菌"],
        "C12N9/00": ["酶", "蛋白酶", "淀粉酶", "纤维素酶", "果胶酶", "酶活性"],
        "B01D11/00": ["提取", "萃取", "分离", "纯化", "吸附", "离子交换"],
        "B01D15/00": ["色谱", "层析", "分离", "纯化", "大孔树脂", "凝胶"],
        "G06F9/00": ["程序", "软件", "算法", "数据处理", "计算机", "系统"],
        "G06N3/00": ["人工智能", "神经网络", "深度学习", "机器学习", "模型", "训练"],
        "H04W4/00": ["通信", "无线", "网络", "物联网", "5G", "蓝牙", "WiFi"],
    }

    # IPC分类含义
    IPC_DESCRIPTIONS = {
        "A23F3/00": "茶叶/咖啡的加工或制备",
        "A23F3/06": "茶叶为基料的饮料",
        "A61K36/00": "含植物材料的医药配剂",
        "C12N9/00": "酶",
    }

    @classmethod
    def match_ipc(cls, text: str) -> List[Tuple[str, str]]:
        """基于文本匹配IPC分类号"""
        matched = []
        text_lower = text.lower()
        for ipc, keywords in cls.IPC_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    desc = cls.IPC_DESCRIPTIONS.get(ipc, "")
                    matched.append((ipc, desc))
                    break
        return list(set(matched))


class ComplianceChecker:
    """专利申请客体适格性校验器"""

    # 不授权客体关键词（示例，完整版需扩充）
    PROHIBITED_PATTERNS = {
        "疾病诊断方法": ["诊断", "筛查", "检测疾病", "诊断方法", "诊断系统"],
        "疾病治疗方法": ["治疗", "疗法", "治疗方案", "治疗系统", "手术方法"],
        "智力活动规则": ["商业方法", "管理方法", "规则", "制度", "商业模式"],
        "计算机程序": ["程序", "算法本身", "纯软件"],
        "科学发现": ["发现", "规律", "现象"],
    }

    @classmethod
    def check(cls, text: str) -> List[Dict]:
        """检查客体适格性风险"""
        warnings = []
        for subject, keywords in cls.PROHIBITED_PATTERNS.items():
            for kw in keywords:
                if kw in text:
                    warnings.append({
                        "type": "客体适格性风险",
                        "subject": subject,
                        "keyword": kw,
                        "suggestion": cls._get_suggestion(subject)
                    })
        return warnings

    @classmethod
    def _get_suggestion(cls, subject: str) -> str:
        suggestions = {
            "疾病诊断方法": "建议调整为'体外诊断试剂盒的制备方法'或'检测数据处理方法'",
            "疾病治疗方法": "建议调整为'药物制剂的制备方法'或'医疗器械结构'",
            "智力活动规则": "建议增加技术实施手段（硬件+算法的交互），形成技术方案",
            "计算机程序": "仅当程序与硬件结合产生技术效果时方可授权",
            "科学发现": "科学发现本身不授权，需形成技术方案才能申请专利",
        }
        return suggestions.get(subject, "请咨询专利代理师确认修改方向")


def read_document(file_path: str) -> str:
    """
    根据文件扩展名读取文档内容
    :param file_path: 文档路径
    :return: 纯文本内容
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.docx':
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx未安装，请运行: pip install python-docx")
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    elif ext == '.pdf':
        if not PDF_AVAILABLE:
            raise ImportError("pdfplumber未安装，请运行: pip install pdfplumber")
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    elif ext == '.xml':
        # 检查是否为ST.26序列表
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            if root.tag in ["ST26SequenceListing", "st26sequencelisting"]:
                # ST.26格式，提取序列信息
                return extract_st26_as_text(root)
        except Exception:
            pass
        # 非ST.26格式，使用标准XML解析
        return read_xml_document(file_path)

    elif ext == '.st26':
        # 显式的ST.26文件格式
        return read_st26_document(file_path)

    elif ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def read_xml_document(file_path: str) -> str:
    """
    读取并解析XML格式的技术交底书
    :param file_path: XML文件路径
    :return: 纯文本内容（将XML结构化内容转为文本）
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        return xml_to_text(root)
    except ET.ParseError as e:
        raise ValueError(f"XML文件解析失败: {e}")


def xml_to_text(element: ET.Element, indent: str = "") -> str:
    """
    将XML元素递归转换为纯文本，保留结构化信息
    :param element: XML元素
    :param indent: 缩进层级
    :return: 纯文本内容
    """
    text_parts = []

    # 获取元素的标签名作为上下文标记
    tag = element.tag if element.tag else ""

    # 处理文本内容
    if element.text and element.text.strip():
        text_parts.append(element.text.strip())

    # 处理子元素
    for child in element:
        child_tag = child.tag if child.tag else ""

        # 根据标签名添加适当的上下文
        if child_tag in ["invention_name", "技术名称", "发明名称"]:
            text_parts.append(f"\n发明名称：{child.text if child.text else ''}")

        elif child_tag in ["tech_field", "技术领域"]:
            text_parts.append(f"技术领域：{child.text if child.text else ''}")

        elif child_tag in ["tech_field_ipc", "IPC分类号"]:
            ipc_text = xml_to_text(child, indent + "  ")
            text_parts.append(f"IPC分类号：{ipc_text}")

        elif child_tag in ["tech_problem", "技术问题", "problem"]:
            text_parts.append(f"要解决的技术问题：{child.text if child.text else ''}")

        elif child_tag in ["tech_scheme", "技术方案", "scheme"]:
            text_parts.append(f"技术方案：{child.text if child.text else ''}")

        elif child_tag in ["tech_feature", "技术特征", "feature"]:
            text_parts.append(f"技术特征：{child.text if child.text else ''}")

        elif child_tag in ["beneficial_effect", "有益效果", "effect"]:
            text_parts.append(f"有益效果：{child.text if child.text else ''}")

        elif child_tag in ["example", "实施例", "example_case"]:
            text_parts.append(f"\n实施例：{xml_to_text(child, indent + '  ')}")

        elif child_tag in ["inventor", "inventors", "发明人"]:
            text_parts.append(f"发明人：{child.text if child.text else ''}")

        elif child_tag in ["completion_date", "完成日期", "发明完成日期"]:
            text_parts.append(f"发明完成日期：{child.text if child.text else ''}")

        elif child_tag in ["patent_type", "专利类型", "申请类型"]:
            text_parts.append(f"专利类型：{child.text if child.text else ''}")

        elif child_tag in ["application_region", "申请地域", "拟申请地域"]:
            text_parts.append(f"拟申请地域：{child.text if child.text else ''}")

        elif child_tag in ["job_invention", "职务发明"]:
            text_parts.append(f"职务发明：{child.text if child.text else ''}")

        elif child_tag in ["background", "背景技术", "现有技术描述"]:
            text_parts.append(f"现有技术描述：{xml_to_text(child, indent + '  ')}")

        elif child_tag in ["defect", "缺陷", "现有技术缺陷"]:
            text_parts.append(f"现有技术缺陷：{xml_to_text(child, indent + '  ')}")

        elif child_tag in ["drawing", "附图", "附图说明"]:
            text_parts.append(f"附图说明：{xml_to_text(child, indent + '  ')}")

        elif child_tag in ["claim_suggestion", "权利要求建议"]:
            text_parts.append(f"权利要求建议：{xml_to_text(child, indent + '  ')}")

        elif child_tag in ["statement", "声明", "权属声明"]:
            text_parts.append(f"权属声明：{xml_to_text(child, indent + '  ')}")

        elif child_tag == "list" or child_tag in ["items", "item_list"]:
            # 处理列表结构
            list_text = xml_to_text(child, indent + "  ")
            if list_text.strip():
                text_parts.append(list_text)

        elif child_tag == "item":
            # 列表项
            item_text = xml_to_text(child, indent + "  ")
            if item_text.strip():
                text_parts.append(f"- {item_text}")

        else:
            # 其他标签递归处理
            child_text = xml_to_text(child, indent + "  ")
            if child_text.strip():
                text_parts.append(child_text)

        # 处理尾随文本
        if child.tail and child.tail.strip():
            text_parts.append(child.tail.strip())

    return "\n".join(text_parts)


def parse_xml_disclosure(file_path: str) -> DisclosureElements:
    """
    直接解析XML格式的技术交底书，提取核心要素
    :param file_path: XML文件路径
    :return: DisclosureElements结构化要素对象
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"XML文件解析失败: {e}")

    elements = DisclosureElements()

    # 定义命名空间（支持带命名空间和不带命名空间的XML）
    ns = {'ns': 'http://www.example.com/patent-disclosure'}

    # 尝试提取发明名称
    invention_name = find_xml_text(root, ["invention_name", "技术名称", "发明名称", "名称"])
    if invention_name:
        # 发明名称作为技术领域的一部分
        elements.tech_field = invention_name

    # 提取技术领域
    tech_field = find_xml_text(root, ["tech_field", "技术领域"])
    if tech_field:
        elements.tech_field = tech_field

    # 提取IPC分类号
    ipc_codes = find_xml_list(root, ["tech_field_ipc", "IPC分类号", "ipc_codes", "ipc"])
    elements.tech_field_ipc = ipc_codes

    # 提取技术问题
    tech_problems = find_xml_list(root, ["tech_problem", "技术问题", "problems", "problem"])
    elements.tech_problems = tech_problems

    # 提取技术方案
    tech_scheme = find_xml_text(root, ["tech_scheme", "技术方案", "scheme"])
    elements.tech_scheme = tech_scheme

    # 提取技术特征
    tech_features = find_xml_list(root, ["tech_feature", "技术特征", "features", "feature"])
    elements.tech_features = tech_features

    # 提取实施例
    examples = find_xml_examples(root)
    elements.examples = examples

    # 提取有益效果
    effects = find_xml_effects(root)
    elements.beneficial_effects = effects

    # 合规性校验
    full_text = xml_to_text(root)
    elements.compliance_warnings = ComplianceChecker.check(full_text)

    return elements


def find_xml_text(element: ET.Element, tags: List[str]) -> str:
    """
    在XML元素中查找指定标签的文本内容
    :param element: XML元素
    :param tags: 可能的标签名列表
    :return: 文本内容
    """
    for tag in tags:
        found = element.find(f".//{tag}")
        if found is not None and found.text:
            return found.text.strip()
    return ""


def find_xml_list(element: ET.Element, tags: List[str]) -> List[str]:
    """
    在XML元素中查找指定标签的列表内容
    :param element: XML元素
    :param tags: 可能的标签名列表
    :return: 字符串列表
    """
    result = []

    for tag in tags:
        found = element.find(f".//{tag}")
        if found is not None:
            # 处理直接文本
            if found.text and found.text.strip():
                result.append(found.text.strip())

            # 处理子元素列表
            for child in found:
                if child.text and child.text.strip():
                    result.append(child.text.strip())
                # 处理嵌套列表项
                for sub_child in child:
                    if sub_child.text and sub_child.text.strip():
                        result.append(sub_child.text.strip())

    return result


def find_xml_examples(element: ET.Element) -> List[Dict]:
    """
    在XML元素中查找实施例
    :param element: XML元素
    :return: 实施例列表
    """
    examples = []

    example_tags = ["example", "examples", "实施例", "example_case", "example_cases"]

    for tag in example_tags:
        found = element.find(f".//{tag}")
        if found is not None:
            for idx, ex in enumerate(found.findall("item") if found.find("item") is not None else [found], 1):
                example = {
                    "index": idx,
                    "description": "",
                    "params": {}
                }

                # 提取描述
                desc = ex.find("description") or ex.find("描述") or ex.find("内容")
                if desc is not None and desc.text:
                    example["description"] = desc.text.strip()[:200]
                elif ex.text:
                    example["description"] = ex.text.strip()[:200]

                # 提取参数
                params = ex.find("params") or ex.find("参数")
                if params is not None:
                    for param in params:
                        param_name = param.tag
                        if param.text and param.text.strip():
                            example["params"][param_name] = [param.text.strip()]

                if example["description"]:
                    examples.append(example)

    return examples[:5]


def find_xml_effects(element: ET.Element) -> List[Dict]:
    """
    在XML元素中查找有益效果
    :param element: XML元素
    :return: 有益效果列表
    """
    effects = []

    effect_tags = ["beneficial_effect", "beneficial_effects", "有益效果", "effects", "effect", "技术效果"]

    for tag in effect_tags:
        found = element.find(f".//{tag}")
        if found is not None:
            for idx, ef in enumerate(found.findall("item") if found.find("item") is not None else [found], 1):
                effect = {
                    "index": idx,
                    "description": "",
                    "associated_problem": ""
                }

                desc = ef.find("description") or ef.find("描述") or ef.find("内容")
                if desc is not None and desc.text:
                    effect["description"] = desc.text.strip()
                elif ef.text:
                    effect["description"] = ef.text.strip()

                if effect["description"]:
                    effects.append(effect)

    return effects[:10]


def read_st26_document(file_path: str) -> str:
    """
    读取并解析WIPO ST.26格式的序列表文件
    :param file_path: ST.26 XML文件路径
    :return: 纯文本内容
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        return extract_st26_as_text(root)
    except ET.ParseError as e:
        raise ValueError(f"ST.26 XML文件解析失败: {e}")


def extract_st26_as_text(root: ET.Element) -> str:
    """
    将ST.26 XML内容转换为纯文本
    :param root: ST.26 XML根元素
    :return: 纯文本内容
    """
    text_parts = []

    # 基本信息
    text_parts.append("=== WIPO ST.26 序列表 ===")

    app_num = get_st26_text(root, ["ApplicationNumber", "application-number"])
    if app_num:
        text_parts.append(f"申请号: {app_num}")

    filing_date = get_st26_text(root, ["FilingDate", "filing-date"])
    if filing_date:
        text_parts.append(f"申请日期: {filing_date}")

    title = get_st26_text(root, ["InventionTitle", "invention-title"])
    if title:
        text_parts.append(f"发明名称: {title}")

    applicant = get_st26_text(root, ["ApplicantName", "applicant-name"])
    if applicant:
        text_parts.append(f"申请人: {applicant}")

    total_qty = get_st26_text(root, ["SequenceTotalQuantity", "sequence-total-quantity"])
    text_parts.append(f"序列总数: {total_qty}")

    text_parts.append("")

    # 序列详情
    sequence_elements = root.findall(".//SequenceData") or root.findall(".//sequenceData")
    for idx, seq_elem in enumerate(sequence_elements, 1):
        text_parts.append(f"--- 序列 {idx} ---")

        seq_id = seq_elem.get("sequenceID") or seq_elem.get("sequenceId") or str(idx)
        text_parts.append(f"序列ID: {seq_id}")

        seqid_no = get_st26_text(seq_elem, ["SEQIDNO", "seqid-no"])
        if seqid_no:
            text_parts.append(f"序列标识号: {seqid_no}")

        length = get_st26_text(seq_elem, ["Length", "length"])
        if length:
            text_parts.append(f"长度: {length}")

        molecule_type = get_st26_text(seq_elem, ["MoleculeType", "molecule-type"])
        if molecule_type:
            text_parts.append(f"分子类型: {molecule_type}")

        organism = get_st26_text(seq_elem, ["Organism", "organism"])
        if organism:
            text_parts.append(f"生物体: {organism}")

        # 序列数据
        seq_data_elem = seq_elem.find(".//seq-data") or seq_elem.find(".//SeqData")
        if seq_data_elem is not None and seq_data_elem.text:
            seq_data = seq_data_elem.text.strip()
            # 格式化序列，每行一定长度
            lines = [seq_data[i:i+70] for i in range(0, len(seq_data), 70)]
            text_parts.append("序列数据:")
            text_parts.extend(lines)

        text_parts.append("")

    return "\n".join(text_parts)


def extract_tech_field(text: str) -> Tuple[str, List[str]]:
    """
    提取技术领域并匹配IPC分类号
    :param text: 文档全文
    :return: (技术领域文本, IPC分类号列表)
    """
    # 尝试从"技术领域"段落提取
    tech_field_pattern = r'技术领域[：:]\s*(.+?)(?:\n|$)'
    match = re.search(tech_field_pattern, text)
    if match:
        tech_field = match.group(1).strip()
    else:
        # 取前200字作为技术领域
        tech_field = text[:200].replace('\n', ' ').strip()

    # 匹配IPC分类号
    ipc_matches = IPCKeywordDict.match_ipc(text)
    ipc_codes = [ipc for ipc, _ in ipc_matches]

    return tech_field, ipc_codes


def extract_tech_problems(text: str) -> List[str]:
    """
    提取技术问题
    :param text: 文档全文
    :return: 技术问题列表
    """
    problems = []

    # 从"要解决的技术问题"段落提取
    problem_patterns = [
        r'要解决的技术问题[：:]\s*(.+?)(?:\n|$)',
        r'发明目的[：:]\s*(.+?)(?:\n|$)',
        r'技术问题[：:]\s*(.+?)(?:\n|$)',
    ]

    for pattern in problem_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # 拆分多个问题（按数字序号或分号）
            items = re.split(r'[；;]|\d+[.、]', match)
            for item in items:
                item = item.strip()
                if item and len(item) > 5:
                    problems.append(item)

    # 去重
    return list(dict.fromkeys(problems))


def extract_tech_scheme_features(text: str) -> Tuple[str, List[str]]:
    """
    提取技术方案和技术特征
    :param text: 文档全文
    :return: (技术方案文本, 技术特征列表)
    """
    scheme = ""
    features = []

    # 从"技术方案"或"发明内容"段落提取
    scheme_patterns = [
        r'技术方案[：:]\s*(.+?)(?:\n\n|\n##|\Z)',
        r'发明内容[：:]\s*(.+?)(?:\n\n|\n##|\Z)',
        r'具体实施方式[：:]\s*(.+?)(?:\n\n|\n##|\Z)',
    ]

    for pattern in scheme_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            scheme = match.group(1).strip()
            break

    # 提取技术特征（基于关键词）
    feature_keywords = ["包括", "特征在于", "步骤为", "结构为", "所述", "其特征是", "具体为"]
    for para in text.split('\n'):
        for kw in feature_keywords:
            if kw in para and len(para) > 10:
                features.append(para.strip())
                break

    return scheme, features[:20]  # 最多保留20个特征


def extract_examples(text: str) -> List[Dict]:
    """
    提取实施例
    :param text: 文档全文
    :return: 实施例列表（含关键参数）
    """
    examples = []

    # 提取参数（温度、时间、压力、配比等）
    param_patterns = {
        "温度": r'(\d+(?:\.\d+)?)\s*℃',
        "时间": r'(\d+(?:\.\d+)?)\s*(?:小时|分钟|秒|h|min|s)',
        "压力": r'(\d+(?:\.\d+)?)\s*(?:MPa|bar|atm|kPa)',
        "比例": r'(\d+(?:\.\d+)?)\s*[:：]\s*(\d+(?:\.\d+)?)',
        "粒径": r'(\d+(?:\.\d+)?)\s*(?:mm|cm|目|μm)',
    }

    # 从"实施例"段落提取
    example_sections = re.split(r'实施例[一二二三4-9\d]*[.、:：]', text)

    for i, section in enumerate(example_sections[1:], 1):  # 跳过第一个空段落
        if len(section) < 20:
            continue

        example = {
            "index": i,
            "description": section[:200].strip(),  # 取前200字
            "params": {}
        }

        # 提取参数
        for param_name, pattern in param_patterns.items():
            matches = re.findall(pattern, section, re.IGNORECASE)
            if matches:
                example["params"][param_name] = matches

        examples.append(example)

    return examples[:5]  # 最多5个实施例


def extract_beneficial_effects(text: str) -> List[Dict]:
    """
    提取有益效果
    :param text: 文档全文
    :return: 有益效果列表（带问题关联）
    """
    effects = []

    # 从"有益效果"段落提取
    effect_patterns = [
        r'有益效果[：:]\s*(.+?)(?:\n\n|\n##|\Z)',
        r'技术效果[：:]\s*(.+?)(?:\n\n|\n##|\Z)',
        r'优点[：:]\s*(.+?)(?:\n\n|\n##|\Z)',
    ]

    for pattern in effect_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            # 拆分多个效果
            items = re.split(r'[；;]|\d+[.、]', match)
            for i, item in enumerate(items, 1):
                item = item.strip()
                if item and len(item) > 5:
                    effects.append({
                        "index": i,
                        "description": item,
                        "associated_problem": ""  # 待后续关联技术问题
                    })

    return effects[:10]  # 最多10个效果


def parse_disclosure_document(file_path: str) -> DisclosureElements:
    """
    解析技术交底书，提取核心要素
    :param file_path: 交底书文件路径（支持.docx/.pdf/.txt/.md）
    :return: 结构化核心要素对象
    """
    # 1. 读取文档
    text = read_document(file_path)

    # 2. 提取各维度要素
    tech_field, ipc_codes = extract_tech_field(text)
    tech_problems = extract_tech_problems(text)
    tech_scheme, tech_features = extract_tech_scheme_features(text)
    examples = extract_examples(text)
    beneficial_effects = extract_beneficial_effects(text)

    # 3. 合规性校验
    compliance_warnings = ComplianceChecker.check(text)

    # 4. 构建返回对象
    elements = DisclosureElements(
        tech_field=tech_field,
        tech_field_ipc=ipc_codes,
        tech_problems=tech_problems,
        tech_scheme=tech_scheme,
        tech_features=tech_features,
        examples=examples,
        beneficial_effects=beneficial_effects,
        compliance_warnings=compliance_warnings
    )

    return elements


# 示例用法
if __name__ == "__main__":
    # 注意：实际使用时传入真实文件路径
    # elements = parse_disclosure_document("技术交底书.docx")
    # print(elements.to_dict())

    print("技术交底书智能解析模块 (Module A)")
    print("支持格式: Word (.docx), PDF (.pdf), TXT (.txt), Markdown (.md), XML (.xml)")
    print("\n使用方法:")
    print("  from parse_disclosure import parse_disclosure_document")
    print("  elements = parse_disclosure_document('交底书.docx')")
    print("  print(elements.to_dict())")
    print("\nXML格式支持:")
    print("  from parse_disclosure import parse_xml_disclosure")
    print("  elements = parse_xml_disclosure('交底书.xml')")
    print("  print(elements.to_dict())")
    print("\nWIPO ST.26序列表支持:")
    print("  from parse_disclosure import parse_st26_sequence_listing")
    print("  listing = parse_st26_sequence_listing('序列.st26.xml')")
    print("  print(listing.to_dict())")


# =============================================================================
# WIPO ST.26 核苷酸/氨基酸序列表解析模块
# WIPO Standard ST.26 for Nucleotide and Amino Acid Sequence Listings
# =============================================================================

# 标准核苷酸代码
ST26_NUCLEOTIDE_CODES = set('atgcuwnrykmsbdhv-')
# 简并核苷酸: n(任意), w(a/t), r(a/g), y(t/c), k(g/t), m(a/c), s(g/c), b(c/g/t), d(a/g/t), h(a/c/t), v(a/c/g)
# 标准氨基酸代码 (20种)
ST26_AMINO_ACID_CODES = set('acdefghiklmnpqrstvwy')
# 蛋白质氨基酸单字母代码


def is_valid_nucleotide_sequence(sequence: str) -> bool:
    """
    验证是否为有效的核苷酸序列
    :param sequence: 序列字符串
    :return: 是否有效
    """
    seq_clean = sequence.lower().replace('\n', '').replace(' ', '').replace('\t', '')
    if not seq_clean:
        return False
    return all(c in ST26_NUCLEOTIDE_CODES for c in seq_clean)


def is_valid_amino_acid_sequence(sequence: str) -> bool:
    """
    验证是否为有效的氨基酸序列
    :param sequence: 序列字符串
    :return: 是否有效
    """
    seq_clean = sequence.upper().replace('\n', '').replace(' ', '').replace('\t', '')
    if not seq_clean:
        return False
    return all(c in ST26_AMINO_ACID_CODES for c in seq_clean)


def parse_st26_sequence_listing(file_path: str) -> ST26SequenceListing:
    """
    解析WIPO ST.26格式的序列表文件
    :param file_path: ST.26 XML文件路径
    :return: ST26SequenceListing结构化对象
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"ST.26 XML文件解析失败: {e}")

    listing = ST26SequenceListing()

    # 解析基本信息
    listing.application_number = get_st26_text(root, [
        "ApplicationNumber", "application-number",
        "ApplicationNumberidentification", "application_number"
    ])

    listing.filing_date = get_st26_text(root, [
        "FilingDate", "filing-date",
        "FilingDateidentification", "filing_date"
    ])

    listing.applicant_file_reference = get_st26_text(root, [
        "ApplicantFileReference", "applicant-file-reference",
        "ApplicantFileReferenceidentification", "applicant_file_reference"
    ])

    listing.applicant_name = get_st26_text(root, [
        "ApplicantName", "applicant-name",
        "ApplicantNameidentification", "applicant_name"
    ])

    listing.invention_title = get_st26_text(root, [
        "InventionTitle", "invention-title",
        "InventionTitleidentification", "invention_title"
    ])

    # 解析序列总数
    total_qty_text = get_st26_text(root, [
        "SequenceTotalQuantity", "sequence-total-quantity",
        "SequenceTotalQuantityidentification", "sequence_total_quantity"
    ])
    try:
        listing.sequence_total_quantity = int(total_qty_text) if total_qty_text else 0
    except ValueError:
        listing.validation_warnings.append("序列总数格式错误")

    # 解析所有序列
    sequence_elements = root.findall(".//SequenceData") or root.findall(".//sequenceData") or []
    for seq_elem in sequence_elements:
        sequence = parse_st26_sequence(seq_elem)
        listing.sequences.append(sequence)

    # ST.26合规性校验
    validate_st26_compliance(listing)

    return listing


def parse_st26_sequence(seq_element: ET.Element) -> ST26Sequence:
    """
    解析单个ST.26序列
    :param seq_element: SequenceData XML元素
    :return: ST26Sequence对象
    """
    seq = ST26Sequence()

    # 获取sequenceID属性
    seq_id_attr = seq_element.get("sequenceID") or seq_element.get("sequenceId") or seq_element.get("sequence_id")
    if seq_id_attr:
        try:
            seq.sequence_id = int(seq_id_attr)
        except ValueError:
            seq.sequence_id = 0

    # 解析各字段
    seq.seqid_no = get_st26_text(seq_element, ["SEQIDNO", "seqid-no", "SEQIDNOidentification", "seqid_no"])
    seq.organism = get_st26_text(seq_element, ["Organism", "organism", "Organismidentification", "organism"])

    # 解析长度
    length_text = get_st26_text(seq_element, ["Length", "length", "Lengthidentification", "length"])
    try:
        seq.length = int(length_text) if length_text else 0
    except ValueError:
        seq.length = 0

    # 解析分子类型
    molecule_type = get_st26_text(seq_element, [
        "MoleculeType", "molecule-type",
        "MoleculeTypeidentification", "molecule_type"
    ])
    seq.molecule_type = normalize_molecule_type(molecule_type)

    # 解析部分号
    seq.division = get_st26_text(seq_element, ["Division", "division", "Divisionidentification", "division"])

    # 解析特性注释
    features_elem = seq_element.find(".//Features") or seq_element.find(".//features")
    if features_elem is not None:
        seq.features = parse_st26_features(features_elem)

    # 解析序列数据
    seq_data_elem = seq_element.find(".//seq-data") or seq_element.find(".//SeqData") or seq_element.find("seq-data")
    if seq_data_elem is not None and seq_data_elem.text:
        seq.sequence_data = seq_data_elem.text.strip()

    # 自动验证序列
    if seq.sequence_data:
        if seq.molecule_type == "DNA" and not is_valid_nucleotide_sequence(seq.sequence_data):
            seq.warnings.append("序列包含非核苷酸字符，可能为RNA或蛋白质")
        elif seq.molecule_type == "RNA" and not is_valid_nucleotide_sequence(seq.sequence_data):
            seq.warnings.append("序列包含非核苷酸字符")
        elif seq.molecule_type == "AA" and not is_valid_amino_acid_sequence(seq.sequence_data):
            seq.warnings.append("序列包含非氨基酸字符")

    return seq


def get_st26_text(element: ET.Element, tags: List[str]) -> str:
    """
    在ST.26元素中查找指定标签的文本内容
    :param element: XML元素
    :param tags: 可能的标签名列表
    :return: 文本内容
    """
    for tag in tags:
        found = element.find(f".//{tag}")
        if found is not None and found.text:
            return found.text.strip()
        # 尝试不带命名空间的查找
        found = element.find(f".//*[local-name()='{tag}']")
        if found is not None and found.text:
            return found.text.strip()
    return ""


def normalize_molecule_type(molecule_type: str) -> str:
    """
    标准化分子类型
    :param molecule_type: 原始分子类型文本
    :return: 标准化后的类型 (DNA/RNA/AA)
    """
    if not molecule_type:
        return ""

    mt_lower = molecule_type.lower().strip()

    if mt_lower in ["dna", "genomic dna", "cdna", "linear dna", "circular dna"]:
        return "DNA"
    elif mt_lower in ["rna", "mrna", "trna", "rrna", "mirna", "linear rna", "circular rna"]:
        return "RNA"
    elif mt_lower in ["aa", "protein", "polypeptide", "amino acid"]:
        return "AA"
    else:
        return molecule_type  # 返回原始值


def parse_st26_features(features_elem: ET.Element) -> List[Dict]:
    """
    解析ST.26特性注释
    :param features_elem: Features XML元素
    :return: 特性列表
    """
    features = []

    # 查找所有FeatureKey
    feature_keys = features_elem.findall(".//FeatureKey") or features_elem.findall(".//featureKey")
    for fk in feature_keys:
        feature = {"name": "", "location": "", "qualifiers": []}

        # 获取特性名称
        name = fk.get("name") or fk.get("Name")
        if name:
            feature["name"] = name

        # 获取位置
        location_elem = fk.find("Location") or fk.find("location")
        if location_elem is not None and location_elem.text:
            feature["location"] = location_elem.text.strip()

        # 获取限定符
        qualifiers = fk.findall(".//Qualifier") or fk.findall(".//qualifier")
        for qual in qualifiers:
            qualifier_name = qual.get("name") or qual.get("Name")
            value_elem = qual.find("Value") or qual.find("value")
            value = value_elem.text.strip() if value_elem is not None and value_elem.text else ""

            if qualifier_name:
                feature["qualifiers"].append({
                    "name": qualifier_name,
                    "value": value
                })

        if feature["name"]:
            features.append(feature)

    return features


def validate_st26_compliance(listing: ST26SequenceListing) -> None:
    """
    WIPO ST.26合规性校验
    :param listing: 序列表对象
    """
    # 检查序列总数一致性
    if listing.sequence_total_quantity != len(listing.sequences):
        listing.validation_warnings.append(
            f"序列总数({listing.sequence_total_quantity})与实际序列数({len(listing.sequences)})不一致"
        )

    # 检查序列ID唯一性
    seq_ids = [s.sequence_id for s in listing.sequences]
    if len(seq_ids) != len(set(seq_ids)):
        listing.validation_warnings.append("存在重复的序列ID")

    # 检查序列数据完整性
    for seq in listing.sequences:
        if not seq.sequence_data:
            listing.validation_warnings.append(f"序列ID {seq.sequence_id} 缺少序列数据")
        if seq.length > 0 and seq.length != len(seq.sequence_data.replace('\n', '').replace(' ', '')):
            listing.validation_warnings.append(
                f"序列ID {seq.sequence_id} 声明长度({seq.length})与实际长度不匹配"
            )

    # 检查必要字段
    if not listing.application_number:
        listing.validation_warnings.append("缺少申请号")

    if not listing.invention_title:
        listing.validation_warnings.append("缺少发明名称")


def convert_to_st26_format(sequences: List[Dict],
                           application_number: str = "",
                           filing_date: str = "",
                           applicant_name: str = "",
                           invention_title: str = "") -> ST26SequenceListing:
    """
    将结构化序列数据转换为ST26SequenceListing对象
    用于从其他格式（如Excel、JSON）导入序列数据生成ST.26文件
    :param sequences: 序列数据列表，每项包含: sequence_id, seqid_no, length, molecule_type, organism, features, sequence_data
    :param application_number: 申请号
    :param filing_date: 申请日期
    :param applicant_name: 申请人名称
    :param invention_title: 发明名称
    :return: ST26SequenceListing对象
    """
    listing = ST26SequenceListing(
        application_number=application_number,
        filing_date=filing_date,
        applicant_name=applicant_name,
        invention_title=invention_title,
        sequence_total_quantity=len(sequences)
    )

    for seq_data in sequences:
        seq = ST26Sequence(
            sequence_id=seq_data.get("sequence_id", 0),
            seqid_no=seq_data.get("seqid_no", ""),
            length=seq_data.get("length", 0),
            molecule_type=normalize_molecule_type(seq_data.get("molecule_type", "")),
            organism=seq_data.get("organism", ""),
            division=seq_data.get("division", ""),
            features=seq_data.get("features", []),
            sequence_data=seq_data.get("sequence_data", "")
        )
        listing.sequences.append(seq)

    validate_st26_compliance(listing)
    return listing