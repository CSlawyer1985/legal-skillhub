"""结构化JSON生成模块。

将解析后的专利信息组织为层级JSON结构，字段名随专利类型自适应。

本模块的核心功能是将 PatentInfo 对象中的原始解析数据，转换为具有层级结构的
JSON字典，便于后续序列化存储或转换为Markdown文档。JSON结构的设计遵循中国
专利文档的标准格式，包含著录项目、摘要、权利要求书、说明书（含子章节）等
核心部分。

主要处理逻辑：
1. 根据专利类型（发明/实用新型/外观设计）自适应字段名
2. 将说明书子章节中的段落号（如[0001]）拆分为结构化的段落对象
3. 记录OCR相关的元信息，标识文本来源
"""

# json: 用于将Python字典序列化为JSON格式写入文件
# logging: 用于记录模块运行时的日志信息
# os: 用于创建输出目录等文件系统操作
# re: 用于正则表达式匹配，主要在段落号拆分时使用
import json
import logging
import os
import re
from typing import Dict, List

# PatentInfo: 专利信息数据类，包含从PDF中解析出的所有结构化信息
from .section_parser import PatentInfo
# OfficeActionInfo: 审查文件信息数据类
from .office_action_parser import OfficeActionInfo

# 使用模块专属的logger，便于在日志中区分来源
logger = logging.getLogger('patent_extractor')


class JSONGenerator:
    """结构化JSON生成器。

    负责将 PatentInfo 对象转换为层级化的JSON字典结构。生成的JSON结构
    遵循中国专利文档的标准格式，包含以下顶层字段：
    - 专利类型：发明/实用新型/外观设计
    - 公开类型：发明公开/发明授权/实用新型授权等
    - 专利名称（字段名随类型自适应，如"发明名称"/"实用新型名称"）
    - 著录项目：申请号、申请人、发明人等元数据
    - 摘要
    - 权利要求书
    - 说明书（含子章节，每个子章节拆分为段落对象列表）
    - 说明书附图
    - _meta：OCR相关元信息
    """

    def generate(self, patent_info: PatentInfo, images: List[Dict] = None,
                 is_image_based: bool = False) -> Dict:
        """
        生成专利信息的层级JSON结构。

        将 PatentInfo 对象中的各字段组织为标准化的JSON字典，其中说明书子章节
        会被进一步拆分为带段落号的结构化段落对象列表。

        Args:
            patent_info: 解析后的专利信息对象，包含从PDF中提取的全部结构化数据，
                         包括专利类型、名称、著录项目、摘要、权利要求书、说明书等
            images: 提取的说明书附图列表，每个元素为字典，包含图片的文件路径等信息；
                    默认为None，表示无附图
            is_image_based: 是否为图像型PDF（即扫描件），True表示PDF页面为扫描图片
                            需要OCR识别文字；False表示PDF内嵌了可提取的文本层。
                            此标志会被记录到元信息中

        Returns:
            Dict: 层级JSON字典，包含以下顶层键：
                - '专利类型': str，如"发明"、"实用新型"
                - '公开类型': str，如"发明公开"、"发明授权"
                - <名称字段>: str，字段名随专利类型变化（如"发明名称"/"实用新型名称"）
                - '著录项目': dict，包含申请号、申请人等元数据
                - '摘要': str，专利摘要全文
                - '权利要求书': str，权利要求书全文
                - '说明书': dict，包含各子章节的段落对象列表
                - '说明书附图': list，附图信息列表
                - '_meta': dict，OCR相关元信息
        """
        result = {}

        # 专利类型与公开类型
        result['专利类型'] = patent_info.patent_type
        result['公开类型'] = patent_info.publication_type

        # 专利名称（根据类型自适应字段名）
        # 不同类型的专利使用不同的字段名：发明→"发明名称"，实用新型→"实用新型名称"
        name_field = patent_info.name_field
        result[name_field] = patent_info.patent_name

        # 著录项目：包含申请号、公开号、申请人、发明人、分类号等元数据
        result['著录项目'] = patent_info.bibliographic

        # 摘要：专利技术方案的简要概述
        result['摘要'] = patent_info.abstract

        # 权利要求书：定义专利保护范围的法律文本
        result['权利要求书'] = patent_info.claims

        # 说明书（含子章节）：构建说明书的层级结构
        description = {}
        # 说明书标题：通常是专利名称的完整版
        description['说明书标题'] = patent_info.description.get('说明书标题', '')

        # 将含段落号的子章节文本拆分为段落对象列表
        # 专利说明书的子章节包括：技术领域、背景技术、发明内容/实用新型内容、
        # 附图说明、具体实施方式。每个子章节的文本中包含形如[0001]的段落编号，
        # 需要拆分为结构化的段落对象以便后续处理和展示。
        # patent_info.content_field 根据专利类型返回对应字段名：
        #   发明→"发明内容"，实用新型→"实用新型内容"
        for section_key in ['技术领域', '背景技术', patent_info.content_field,
                           '附图说明', '具体实施方式']:
            section_text = patent_info.description.get(section_key, '')
            # 调用 _split_into_paragraphs 将文本拆分为段落对象列表
            description[section_key] = self._split_into_paragraphs(section_text)

        result['说明书'] = description

        # 说明书附图：若未提供附图列表则默认为空列表
        result['说明书附图'] = images or []

        # 元信息：记录OCR相关状态，便于下游判断文本来源
        # is_image_based: 标识是否为扫描件PDF
        # text_source: 文本来源，'ocr'表示OCR识别，'pdf_text'表示直接提取PDF文本层
        result['_meta'] = {
            'is_image_based': is_image_based,
            'text_source': 'ocr' if is_image_based else 'pdf_text',
        }

        return result

    def _split_into_paragraphs(self, text: str) -> List[Dict]:
        """将含段落号[XXXX]的文本拆分为段落对象列表。

        专利说明书中的每个段落都以方括号包裹的四位数字编号开头，如[0001]、[0002]等。
        本方法将连续的文本按段落号拆分为独立的结构化对象，便于后续按段落引用和展示。

        算法思路：
        1. 使用正则表达式 re.split 配合捕获组，将文本按段落号分割，
           同时保留段落号本身（捕获组的作用）
        2. 遍历分割结果，遇到段落号时保存前一个段落并开始新段落
        3. 遇到普通文本时追加到当前段落的缓冲区
        4. 循环结束后保存最后一个段落

        示例：
            输入: "[0001]本发明涉及...[0002]背景技术..."
            输出: [
                {"段落号": "0001", "内容": "本发明涉及..."},
                {"段落号": "0002", "内容": "背景技术..."}
            ]

        Args:
            text: 已清理的文本，段落以[XXXX]段落号分隔；
                  若为空字符串则返回空列表

        Returns:
            List[Dict]: 段落对象列表，每个对象包含：
                - "段落号": str，四位数字编号（如"0001"），仅在有段落号时存在
                - "内容": str，该段落的正文内容
                若文本无段落号，则返回 [{"内容": "..."}]
        """
        if not text:
            return []

        paragraphs = []
        # 按 [XXXX] 段落号分割
        # re.split 的第一个参数 r'(\[\d{4}\])' 中，括号是捕获组，
        # 作用是让分割结果中保留分隔符（即段落号本身）
        # 例如："[0001]你好[0002]世界" → ['', '[0001]', '你好', '[0002]', '世界']
        parts = re.split(r'(\[\d{4}\])', text)

        # 当前正在处理的段落号（去除方括号后的四位数字）
        current_num = None
        # 当前段落的文本内容缓冲区（列表形式，最后用join合并）
        current_content = []

        for part in parts:
            # 判断当前片段是否为段落号（形如[0001]）
            if re.match(r'^\[\d{4}\]$', part):
                # 遇到新的段落号，说明前一个段落已经结束，需要保存
                if current_num is not None or current_content:
                    content = ''.join(current_content).strip()
                    # 只有当内容非空或已有段落号时才创建段落对象
                    if content or current_num is not None:
                        para = {}
                        if current_num is not None:
                            para['段落号'] = current_num
                        para['内容'] = content
                        paragraphs.append(para)
                # 去除方括号，提取纯数字编号（如"[0001]" → "0001"）
                current_num = part[1:-1]
                # 重置内容缓冲区，开始收集新段落的文本
                current_content = []
            else:
                # 普通文本片段，追加到当前段落的内容缓冲区
                current_content.append(part)

        # 保存最后一个段落（循环结束后最后一个段落尚未保存）
        if current_num is not None or current_content:
            content = ''.join(current_content).strip()
            if content or current_num is not None:
                para = {}
                if current_num is not None:
                    para['段落号'] = current_num
                para['内容'] = content
                paragraphs.append(para)

        return paragraphs

    def generate_office_action(self, info: OfficeActionInfo,
                               is_image_based: bool = False) -> Dict:
        """生成审查文件信息的层级JSON结构（分发器）。

        根据文档类型调用对应的独立生成方法，每种审查文件拥有
        完全独立的JSON结构，不再套用专利公开公告的"著录项目"格式。

        Args:
            info: 解析后的审查文件信息对象
            is_image_based: 是否为图像型PDF

        Returns:
            Dict: 层级JSON字典
        """
        if info.doc_type == '审查意见通知书':
            return self._generate_office_action_notification(info, is_image_based)
        elif info.doc_type == '驳回决定':
            return self._generate_rejection_decision(info, is_image_based)
        elif info.doc_type == '复审决定书':
            return self._generate_reexamination_decision(info, is_image_based)
        elif info.doc_type == '无效宣告请求审查决定书':
            return self._generate_invalidation_decision(info, is_image_based)
        else:
            # 未知类型，使用通用格式
            return self._generate_generic_office_action(info, is_image_based)

    def _generate_office_action_notification(self, info: OfficeActionInfo,
                                              is_image_based: bool = False) -> Dict:
        """生成审查意见通知书的独立JSON结构。

        审查意见通知书是审查员对专利申请提出的审查意见通知，
        其结构反映通知书的文档特性：基本信息 → 首页事项 → 对比文件 →
        结论性意见 → 正文。

        JSON结构设计原则：
        - 扁平化顶层字段，不使用"著录项目"子对象
        - 字段顺序遵循文档原文的逻辑顺序
        - 仅包含审查意见通知书实际拥有的字段
        """
        result = {}

        result['文档类型'] = info.doc_type
        result['发明创造名称'] = info.发明创造名称

        # 基本信息（扁平化，不嵌套在"著录项目"下）
        if info.申请号:
            result['申请号'] = info.申请号
        if info.申请人:
            result['申请人'] = info.申请人
        if info.发文日:
            result['发文日'] = info.发文日
        if info.发文序号:
            result['发文序号'] = info.发文序号
        if info.审查次数:
            result['审查次数'] = info.审查次数
        if info.审查员:
            result['审查员'] = info.审查员
        if info.审查部门:
            result['审查部门'] = info.审查部门
        if info.联系电话:
            result['联系电话'] = info.联系电话

        # 通知书首页事项（编号1-9项的完整通知内容）
        if info.通知书首页事项:
            result['通知书首页事项'] = info.通知书首页事项

        # 对比文件
        if info.对比文件:
            result['对比文件'] = info.对比文件

        # 结论性意见
        if info.结论性意见:
            result['结论性意见'] = info.结论性意见

        # 正文
        result['正文'] = info.正文

        # 元信息
        result['_meta'] = {
            'is_image_based': is_image_based,
            'text_source': 'ocr' if is_image_based else 'pdf_text',
        }

        return result

    def _generate_rejection_decision(self, info: OfficeActionInfo,
                                      is_image_based: bool = False) -> Dict:
        """生成驳回决定的独立JSON结构。

        驳回决定是审查员驳回专利申请的正式决定，
        其结构反映驳回决定的文档特性：基本信息 → 首页事项 →
        驳回依据 → 针对的申请文件 → 正文（案由+驳回理由）。

        JSON结构设计原则：
        - 扁平化顶层字段，不使用"著录项目"子对象
        - 驳回依据和针对的申请文件是核心字段，紧跟基本信息
        - 正文通常包含"一、案由"和"二、驳回理由"两个章节
        """
        result = {}

        result['文档类型'] = info.doc_type
        result['发明创造名称'] = info.发明创造名称

        # 基本信息（扁平化）
        if info.申请号:
            result['申请号'] = info.申请号
        if info.申请人:
            result['申请人'] = info.申请人
        if info.发文日:
            result['发文日'] = info.发文日
        if info.审查员:
            result['审查员'] = info.审查员
        if info.审查部门:
            result['审查部门'] = info.审查部门
        if info.审查员代码:
            result['审查员代码'] = info.审查员代码

        # 驳回决定首页事项（编号1-3项的驳回决定首页内容）
        if info.驳回决定首页事项:
            result['驳回决定首页事项'] = info.驳回决定首页事项

        # 驳回依据（核心字段）
        if info.驳回依据:
            result['驳回依据'] = info.驳回依据

        # 针对的申请文件
        if info.针对的申请文件:
            result['针对的申请文件'] = info.针对的申请文件

        # 对比文件
        if info.对比文件:
            result['对比文件'] = info.对比文件

        # 正文
        result['正文'] = info.正文

        # 元信息
        result['_meta'] = {
            'is_image_based': is_image_based,
            'text_source': 'ocr' if is_image_based else 'pdf_text',
        }

        return result

    def _generate_reexamination_decision(self, info: OfficeActionInfo,
                                          is_image_based: bool = False) -> Dict:
        """生成复审决定书的独立JSON结构。

        复审决定书是专利复审委员会对复审请求的审查决定，
        其结构反映复审决定书的文档特性：基本信息 → 合议组 →
        决定摘要 → 决定结果 → 法律依据 → 决定要点 → 正文。

        JSON结构设计原则：
        - 扁平化顶层字段，不使用"著录项目"子对象
        - 决定号、决定日作为首要标识字段
        - 合议组信息单独列出
        - 决定结果、法律依据、决定要点是核心法律字段
        - 正文通常包含"一、案由"和"二、决定理由"两个章节
        """
        result = {}

        result['文档类型'] = info.doc_type
        result['发明创造名称'] = info.发明创造名称

        # 基本信息（扁平化，复审决定书特有字段优先）
        if info.申请号:
            result['申请号'] = info.申请号
        if info.复审请求人:
            result['复审请求人'] = info.复审请求人
        if info.案件编号:
            result['案件编号'] = info.案件编号
        if info.决定号:
            result['决定号'] = info.决定号
        if info.决定日:
            result['决定日'] = info.决定日
        if info.申请日:
            result['申请日'] = info.申请日
        if info.公开日:
            result['公开日'] = info.公开日
        if info.复审请求日:
            result['复审请求日'] = info.复审请求日
        if info.国际主分类号:
            result['国际主分类号'] = info.国际主分类号

        # 合议组
        合议组 = {}
        if info.合议组组长:
            合议组['组长'] = info.合议组组长
        if info.主审员:
            合议组['主审员'] = info.主审员
        if info.参审员:
            合议组['参审员'] = info.参审员
        if 合议组:
            result['合议组'] = 合议组

        # 复审决定首页简述
        if info.复审决定首页简述:
            result['决定摘要'] = info.复审决定首页简述

        # 决定结果（核心字段）
        if info.决定结果:
            result['决定结果'] = info.决定结果

        # 法律依据
        if info.法律依据:
            result['法律依据'] = info.法律依据

        # 决定要点
        if info.决定要点:
            result['决定要点'] = info.决定要点

        # 对比文件
        if info.对比文件:
            result['对比文件'] = info.对比文件

        # 正文
        result['正文'] = info.正文

        # 元信息
        result['_meta'] = {
            'is_image_based': is_image_based,
            'text_source': 'ocr' if is_image_based else 'pdf_text',
        }

        return result

    def _generate_invalidation_decision(self, info: OfficeActionInfo,
                                         is_image_based: bool = False) -> Dict:
        """生成无效宣告请求审查决定书的独立JSON结构。

        无效宣告请求审查决定书结构与复审决定书类似，
        但当事人为无效宣告请求人和专利权人。

        JSON结构设计原则：
        - 扁平化顶层字段，不使用"著录项目"子对象
        - 决定号、决定日作为首要标识字段
        - 合议组信息单独列出
        - 决定结果、法律依据、决定要点是核心法律字段
        - 正文通常包含"一、案由"、"二、决定的理由"、"三、决定"三个章节
        """
        result = {}

        result['文档类型'] = info.doc_type
        result['发明创造名称'] = info.发明创造名称

        # 基本信息（扁平化，无效决定书特有字段优先）
        if info.申请号:
            result['申请号'] = info.申请号
        if info.专利号:
            result['专利号'] = info.专利号
        if info.专利权人:
            result['专利权人'] = info.专利权人
        if info.无效宣告请求人:
            result['无效宣告请求人'] = info.无效宣告请求人
        if info.案件编号:
            result['案件编号'] = info.案件编号
        if info.决定号:
            result['决定号'] = info.决定号
        if info.决定日:
            result['决定日'] = info.决定日
        if info.申请日:
            result['申请日'] = info.申请日
        if info.授权公告日:
            result['授权公告日'] = info.授权公告日
        if info.无效宣告请求日:
            result['无效宣告请求日'] = info.无效宣告请求日
        if info.国际分类号:
            result['国际分类号'] = info.国际分类号

        # 合议组
        合议组 = {}
        if info.合议组组长:
            合议组['组长'] = info.合议组组长
        if info.主审员:
            合议组['主审员'] = info.主审员
        if info.参审员:
            合议组['参审员'] = info.参审员
        if 合议组:
            result['合议组'] = 合议组

        # 无效决定首页简述
        if info.无效决定首页简述:
            result['决定摘要'] = info.无效决定首页简述

        # 决定结果（核心字段）
        if info.决定结果:
            result['决定结果'] = info.决定结果

        # 法律依据
        if info.法律依据:
            result['法律依据'] = info.法律依据

        # 决定要点
        if info.决定要点:
            result['决定要点'] = info.决定要点

        # 对比文件
        if info.对比文件:
            result['对比文件'] = info.对比文件

        # 正文
        result['正文'] = info.正文

        # 元信息
        result['_meta'] = {
            'is_image_based': is_image_based,
            'text_source': 'ocr' if is_image_based else 'pdf_text',
        }

        return result

    def _generate_generic_office_action(self, info: OfficeActionInfo,
                                         is_image_based: bool = False) -> Dict:
        """未知审查文件类型的通用JSON结构。"""
        result = {}

        result['文档类型'] = info.doc_type
        result['发明创造名称'] = info.发明创造名称

        if info.申请号:
            result['申请号'] = info.申请号
        if info.申请人:
            result['申请人'] = info.申请人
        if info.发文日:
            result['发文日'] = info.发文日

        # 正文
        result['正文'] = info.正文

        # 元信息
        result['_meta'] = {
            'is_image_based': is_image_based,
            'text_source': 'ocr' if is_image_based else 'pdf_text',
        }

        return result

    def save(self, data: Dict, output_path: str) -> str:
        """
        将JSON数据保存到文件。

        将内存中的JSON字典序列化为UTF-8编码的JSON文件，自动创建所需的目录结构。
        输出文件使用2空格缩进格式化，便于人工阅读和调试。

        Args:
            data: 要保存的JSON数据字典，通常由 generate() 方法生成
            output_path: 输出文件的绝对或相对路径，例如 "/output/patent.json"

        Returns:
            str: 实际保存的文件路径（与 output_path 相同）
        """
        # 确保输出目录存在，若不存在则自动创建（包括所有中间目录）
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        # 以UTF-8编码写入JSON文件
        # ensure_ascii=False: 允许直接输出中文字符，而非\uXXXX转义序列
        # indent=2: 使用2空格缩进，使JSON文件可读性更好
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON已保存: {output_path}")
        return output_path
