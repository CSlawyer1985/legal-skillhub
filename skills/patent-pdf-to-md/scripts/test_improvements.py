#!/usr/bin/env python3
"""单元测试：验证无效决定书独立子文件夹和Markdown智能分段优化。

测试覆盖：
1. _build_base_name_office_action: 不同案件编号生成不同base_name
2. _ensure_unique_base_name: 碰撞检测和自动追加后缀
3. _format_body_content: 智能分段逻辑
4. _clean_ocr_in_body: 优化后的段落边界检测
5. 案件编号提取鲁棒性
"""
import os
import sys
import tempfile
import shutil

# 确保可以导入项目模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from patent_extractor.office_action_parser import (
    OfficeActionParser, OfficeActionInfo, detect_office_action_type,
    DOC_TYPE_INVALIDATION,
)
from patent_extractor.markdown_generator import MarkdownGenerator
from patent_extractor.json_generator import JSONGenerator
from patent_extractor.main import (
    _build_base_name_office_action,
    _ensure_unique_base_name,
    _sanitize_filename,
)


# ============================================================
# 测试1: 无效决定书不同案件编号生成不同 base_name
# ============================================================

def test_invalidation_different_case_numbers():
    """不同案件编号的无效决定书应生成不同的 base_name。"""
    info1 = OfficeActionInfo(
        doc_type='无效宣告请求审查决定书',
        发明创造名称='测试专利1',
        申请号='201420522729.0',
        决定日='2016年08月31日',
        案件编号='5W110364',
        决定号='35918',
    )
    info2 = OfficeActionInfo(
        doc_type='无效宣告请求审查决定书',
        发明创造名称='测试专利2',
        申请号='201420522729.0',
        决定日='2018年05月29日',
        案件编号='5W114080',
        决定号='36200',
    )

    name1 = _build_base_name_office_action(info1)
    name2 = _build_base_name_office_action(info2)

    assert name1 != name2, f'不同案件编号应生成不同base_name: {name1} vs {name2}'
    assert '5W110364' in name1, f'base_name1应包含案件编号5W110364: {name1}'
    assert '5W114080' in name2, f'base_name2应包含案件编号5W114080: {name2}'
    print('PASS: test_invalidation_different_case_numbers')


def test_invalidation_fallback_to_decision_number():
    """案件编号缺失时，应使用决定号作为兜底。"""
    info = OfficeActionInfo(
        doc_type='无效宣告请求审查决定书',
        发明创造名称='测试专利',
        申请号='201420522729.0',
        决定日='2016年08月31日',
        案件编号='',  # 案件编号缺失
        决定号='35918',  # 应使用决定号兜底
    )

    name = _build_base_name_office_action(info)
    assert '35918' in name, f'案件编号缺失时应使用决定号兜底: {name}'
    print('PASS: test_invalidation_fallback_to_decision_number')


def test_invalidation_fallback_to_dispatch_number():
    """案件编号和决定号均缺失时，应使用发文序号作为最后兜底。"""
    info = OfficeActionInfo(
        doc_type='无效宣告请求审查决定书',
        发明创造名称='测试专利',
        申请号='201420522729.0',
        决定日='2016年08月31日',
        案件编号='',
        决定号='',
        发文序号='2025042600034190',
    )

    name = _build_base_name_office_action(info)
    assert '2025042600034190' in name, f'案件编号和决定号均缺失时应使用发文序号兜底: {name}'
    print('PASS: test_invalidation_fallback_to_dispatch_number')


def test_same_case_number_same_base_name():
    """相同案件编号的无效决定书应生成相同的 base_name。"""
    info1 = OfficeActionInfo(
        doc_type='无效宣告请求审查决定书',
        发明创造名称='测试专利',
        申请号='201420522729.0',
        决定日='2016年08月31日',
        案件编号='5W110364',
        决定号='35918',
    )
    info2 = OfficeActionInfo(
        doc_type='无效宣告请求审查决定书',
        发明创造名称='测试专利',
        申请号='201420522729.0',
        决定日='2016年08月31日',
        案件编号='5W110364',
        决定号='35918',
    )

    name1 = _build_base_name_office_action(info1)
    name2 = _build_base_name_office_action(info2)

    assert name1 == name2, f'相同案件编号应生成相同base_name: {name1} vs {name2}'
    print('PASS: test_same_case_number_same_base_name')


# ============================================================
# 测试2: _ensure_unique_base_name 碰撞检测
# ============================================================

def test_ensure_unique_no_conflict():
    """无冲突时返回原始 base_name。"""
    tmpdir = tempfile.mkdtemp()
    try:
        result = _ensure_unique_base_name('test-name', tmpdir)
        assert result == 'test-name', f'无冲突时应返回原始base_name: {result}'
    finally:
        shutil.rmtree(tmpdir)
    print('PASS: test_ensure_unique_no_conflict')


def test_ensure_unique_with_conflict():
    """有冲突时自动追加后缀。"""
    tmpdir = tempfile.mkdtemp()
    try:
        # 创建冲突文件
        with open(os.path.join(tmpdir, 'test-name.json'), 'w') as f:
            f.write('{}')

        result = _ensure_unique_base_name('test-name', tmpdir)
        assert result == 'test-name_2', f'冲突时应追加_2后缀: {result}'
        assert result != 'test-name', '冲突时不应返回原始base_name'
    finally:
        shutil.rmtree(tmpdir)
    print('PASS: test_ensure_unique_with_conflict')


def test_ensure_unique_multiple_conflicts():
    """多个冲突时递增后缀。"""
    tmpdir = tempfile.mkdtemp()
    try:
        # 创建多个冲突文件
        for suffix in ['', '_2', '_3']:
            with open(os.path.join(tmpdir, f'test-name{suffix}.json'), 'w') as f:
                f.write('{}')

        result = _ensure_unique_base_name('test-name', tmpdir)
        assert result == 'test-name_4', f'多个冲突时应递增后缀到_4: {result}'
    finally:
        shutil.rmtree(tmpdir)
    print('PASS: test_ensure_unique_multiple_conflicts')


def test_ensure_unique_nonexistent_dir():
    """输出目录不存在时返回原始 base_name。"""
    result = _ensure_unique_base_name('test-name', '/nonexistent/path')
    assert result == 'test-name', f'目录不存在时应返回原始base_name: {result}'
    print('PASS: test_ensure_unique_nonexistent_dir')


# ============================================================
# 测试3: Markdown 智能分段逻辑
# ============================================================

def test_format_body_content_preserves_existing_paragraphs():
    """已有空行分段的文本应保留原有分段。"""
    gen = MarkdownGenerator()
    text = '第一段内容。\n\n第二段内容。'
    result = gen._format_body_content(text)
    assert '第一段内容。\n\n第二段内容。' == result, '应保留已有空行分段'
    print('PASS: test_format_body_content_preserves_existing_paragraphs')


def test_format_body_content_short_text_unchanged():
    """较短的文本（<200字符）不应被分段。"""
    gen = MarkdownGenerator()
    text = '这是一段较短的文本，不需要进行分段处理。'
    result = gen._format_body_content(text)
    assert result == text, f'短文本不应被修改: {result}'
    print('PASS: test_format_body_content_short_text_unchanged')


def test_format_body_content_splits_at_paragraph_start():
    """长文本中句号后跟段落起始标记时应分段。"""
    gen = MarkdownGenerator()
    text = (
        '本发明涉及一种图像识别方法，该方法包括图像获取和预处理步骤。'
        '根据权利要求1所述的方法，其特征在于包括以下步骤：'
        '首先获取待识别的图像数据。'
        '基于深度学习模型对图像进行特征提取和分类。'
        '通过后处理模块对分类结果进行优化。'
        '综上所述，本发明提供了一种高效的图像识别方案。'
    )
    result = gen._format_body_content(text)
    # 应在"根据权利要求"前分段
    assert '\n\n' in result, f'长文本应在段落起始标记处分段: {result[:100]}...'
    assert '根据权利要求' in result, '分段后应保留段落起始标记'
    print('PASS: test_format_body_content_splits_at_paragraph_start')


def test_format_body_content_no_split_on_continuation():
    """句号后跟续行词时不应分段。"""
    gen = MarkdownGenerator()
    text = (
        '本发明提供了一种数据处理装置。'
        '其特征在于包括数据采集模块和数据处理模块。'
    )
    result = gen._format_body_content(text)
    # "其特征在于"是续行词，不应分段
    assert '\n\n' not in result, f'续行词后不应分段: {result}'
    print('PASS: test_format_body_content_no_split_on_continuation')


def test_format_body_content_empty_text():
    """空文本应原样返回。"""
    gen = MarkdownGenerator()
    assert gen._format_body_content('') == ''
    assert gen._format_body_content(None) is None
    print('PASS: test_format_body_content_empty_text')


def test_split_by_sentence_boundary_basic():
    """基本句号后分段测试。"""
    gen = MarkdownGenerator()
    text = '第一句话结束。根据专利法的规定，第二句话开始。基于上述理由，第三句话。'
    result = gen._split_by_sentence_boundary(text)
    assert len(result) >= 2, f'应至少分为2段: {result}'
    print('PASS: test_split_by_sentence_boundary_basic')


def test_split_preserves_continuation():
    """续行词后不分段。"""
    gen = MarkdownGenerator()
    text = '本发明涉及一种方法。其特征在于包括步骤A。所述步骤A包括子步骤。'
    result = gen._split_by_sentence_boundary(text)
    # "其特征在于"和"所述"是续行词，不应分段
    assert len(result) == 1, f'续行词后不应分段，应为1段: {result}'
    print('PASS: test_split_preserves_continuation')


# ============================================================
# 测试4: _clean_ocr_in_body 优化后的段落边界检测
# ============================================================

def test_clean_ocr_preserves_numbered_paragraphs():
    """编号开头的行应被视为新段落。"""
    parser = OfficeActionParser()
    text = '前一段内容结束。\n1.第一项内容说明。\n2.第二项内容说明。'
    result = parser._clean_ocr_in_body(text)
    # "1."开头的行应被识别为新段落
    assert '\n\n' in result or '1.第一项' in result, f'编号开头的行应被视为新段落: {result}'
    print('PASS: test_clean_ocr_preserves_numbered_paragraphs')


def test_clean_ocr_preserves_keyword_paragraphs():
    """段落起始关键词开头的行应被视为新段落。"""
    parser = OfficeActionParser()
    text = '前一段内容结束。\n根据专利法第22条的规定。\n基于上述理由。'
    result = parser._clean_ocr_in_body(text)
    # "根据"和"基于"开头的行应被识别为新段落
    assert '根据专利法' in result, '应保留"根据"关键词'
    print('PASS: test_clean_ocr_preserves_keyword_paragraphs')


def test_clean_ocr_merges_mid_sentence_breaks():
    """句子中间的换行应被合并。"""
    parser = OfficeActionParser()
    text = '本发明涉及一种图像\n识别方法，包括以下\n步骤。'
    result = parser._clean_ocr_in_body(text)
    assert '图像识别方法' in result, f'句子中间换行应被合并: {result}'
    assert '\n' not in result or result.count('\n') <= 1, f'合并后不应有多余换行: {result}'
    print('PASS: test_clean_ocr_merges_mid_sentence_breaks')


def test_clean_ocr_preserves_blank_line_separation():
    """空行分隔的段落应保留。"""
    parser = OfficeActionParser()
    text = '第一段内容。\n\n第二段内容。'
    result = parser._clean_ocr_in_body(text)
    assert '\n\n' in result, f'空行分隔的段落应保留: {result}'
    print('PASS: test_clean_ocr_preserves_blank_line_separation')


# ============================================================
# 测试5: 案件编号提取鲁棒性
# ============================================================

def test_extract_case_number_standard_format():
    """标准格式案件编号提取。"""
    parser = OfficeActionParser()
    parser.info = OfficeActionInfo(doc_type=DOC_TYPE_INVALIDATION)
    parser.full_text = '案件编号 第5W110364号'
    parser._is_mineru_single_page = False
    parser._extract_invalidation_fields()
    assert parser.info.案件编号 == '5W110364', f'标准格式案件编号提取失败: {parser.info.案件编号}'
    print('PASS: test_extract_case_number_standard_format')


def test_extract_case_number_pipe_format():
    """管道分隔格式案件编号提取。"""
    parser = OfficeActionParser()
    parser.info = OfficeActionInfo(doc_type=DOC_TYPE_INVALIDATION)
    parser.full_text = '案件编号 | 5W114080'
    parser._is_mineru_single_page = False
    parser._extract_invalidation_fields()
    assert parser.info.案件编号 == '5W114080', f'管道格式案件编号提取失败: {parser.info.案件编号}'
    print('PASS: test_extract_case_number_pipe_format')


def test_extract_case_number_colon_format():
    """冒号分隔格式案件编号提取。"""
    parser = OfficeActionParser()
    parser.info = OfficeActionInfo(doc_type=DOC_TYPE_INVALIDATION)
    parser.full_text = '案件编号：5W110364'
    parser._is_mineru_single_page = False
    parser._extract_invalidation_fields()
    assert parser.info.案件编号 == '5W110364', f'冒号格式案件编号提取失败: {parser.info.案件编号}'
    print('PASS: test_extract_case_number_colon_format')


# ============================================================
# 测试6: 端到端 Markdown 生成验证
# ============================================================

def test_invalidation_markdown_has_paragraph_breaks():
    """无效决定书Markdown正文应有段落分隔。"""
    gen = JSONGenerator()
    md_gen = MarkdownGenerator()

    info = OfficeActionInfo(
        doc_type='无效宣告请求审查决定书',
        发明创造名称='测试专利',
        申请号='201420522729.0',
        专利号='CN204119349U',
        专利权人='测试公司',
        无效宣告请求人='请求人A',
        案件编号='5W110364',
        决定号='35918',
        决定日='2016年08月31日',
        决定结果='宣告专利权全部无效',
        法律依据='专利法第22条第3款',
        决定要点='如果一项权利要求...',
        正文={
            '一、案由': (
                '本无效宣告请求涉及专利号为CN204119349U的实用新型专利。'
                '根据专利法第45条的规定，请求人向专利复审委员会提出了无效宣告请求。'
                '基于上述理由，请求人认为该专利不符合专利法的相关规定。'
                '综上所述，合议组作出了如下决定。'
            ),
            '二、决定的理由': '决定理由内容。',
            '三、决定': '宣告专利权全部无效。',
        },
    )

    json_data = gen.generate_office_action(info, is_image_based=True)
    md_content = md_gen.generate_office_action(json_data)

    # 验证Markdown结构
    assert '## 无效宣告请求审查决定书' in md_content
    assert '### 基本信息' in md_content
    assert '5W110364' in md_content
    assert '### 正文' in md_content
    assert '#### 一、案由' in md_content

    # 验证正文中有段落分隔（长文本应在"根据"和"基于"前分段）
    body_section = md_content.split('#### 一、案由')[1].split('####')[0]
    assert '\n\n' in body_section.strip(), f'正文应有段落分隔: {body_section[:200]}'
    print('PASS: test_invalidation_markdown_has_paragraph_breaks')


def test_reexamination_markdown_structure():
    """复审决定书Markdown结构完整性验证。"""
    gen = JSONGenerator()
    md_gen = MarkdownGenerator()

    info = OfficeActionInfo(
        doc_type='复审决定书',
        发明创造名称='测试发明',
        申请号='202510345298.1',
        复审请求人='测试公司',
        案件编号='1F778674',
        决定号='123456',
        决定日='2025年03月20日',
        合议组组长='李四',
        主审员='王五',
        参审员='赵六',
        决定结果='撤销驳回决定',
        法律依据='专利法第22条第3款',
        决定要点='如果...',
        复审决定首页简述='本决定涉及...',
        正文={
            '一、案由': '案由内容。',
            '二、决定理由': '决定理由内容。',
        },
    )

    json_data = gen.generate_office_action(info, is_image_based=True)
    md_content = md_gen.generate_office_action(json_data)

    assert '## 复审决定书' in md_content
    assert '1F778674' in md_content
    assert '### 合议组' in md_content
    print('PASS: test_reexamination_markdown_structure')


# ============================================================
# 运行所有测试
# ============================================================

if __name__ == '__main__':
    tests = [
        # 无效决定书独立子文件夹
        test_invalidation_different_case_numbers,
        test_invalidation_fallback_to_decision_number,
        test_invalidation_fallback_to_dispatch_number,
        test_same_case_number_same_base_name,
        # 碰撞检测
        test_ensure_unique_no_conflict,
        test_ensure_unique_with_conflict,
        test_ensure_unique_multiple_conflicts,
        test_ensure_unique_nonexistent_dir,
        # Markdown智能分段
        test_format_body_content_preserves_existing_paragraphs,
        test_format_body_content_short_text_unchanged,
        test_format_body_content_splits_at_paragraph_start,
        test_format_body_content_no_split_on_continuation,
        test_format_body_content_empty_text,
        test_split_by_sentence_boundary_basic,
        test_split_preserves_continuation,
        # OCR段落边界检测
        test_clean_ocr_preserves_numbered_paragraphs,
        test_clean_ocr_preserves_keyword_paragraphs,
        test_clean_ocr_merges_mid_sentence_breaks,
        test_clean_ocr_preserves_blank_line_separation,
        # 案件编号提取
        test_extract_case_number_standard_format,
        test_extract_case_number_pipe_format,
        test_extract_case_number_colon_format,
        # 端到端验证
        test_invalidation_markdown_has_paragraph_breaks,
        test_reexamination_markdown_structure,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f'FAIL: {test.__name__}: {e}')
            failed += 1

    print(f'\n{"=" * 60}')
    print(f'测试结果: {passed} 通过, {failed} 失败, 共 {len(tests)} 个')
    print(f'{"=" * 60}')
    if failed > 0:
        sys.exit(1)
