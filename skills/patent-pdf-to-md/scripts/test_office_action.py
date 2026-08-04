#!/usr/bin/env python3
"""测试审查文件独立JSON/Markdown结构"""
from patent_extractor.json_generator import JSONGenerator
from patent_extractor.markdown_generator import MarkdownGenerator
from patent_extractor.office_action_parser import OfficeActionInfo

gen = JSONGenerator()

# 审查意见通知书
info1 = OfficeActionInfo(
    doc_type='审查意见通知书',
    发明创造名称='测试发明',
    申请号='202510345296.9',
    申请人='测试公司',
    审查次数='第一次',
    审查员='张三',
    通知书首页事项='1.应申请人提出的请求...',
    结论性意见='该申请不具备创造性',
)
json1 = gen.generate_office_action(info1, is_image_based=True)
assert '著录项目' not in json1, '审查意见通知书不应有著录项目'
assert json1['申请号'] == '202510345296.9', '申请号应为顶层字段'
assert json1['通知书首页事项'] == '1.应申请人提出的请求...', '通知书首页事项应存在'
print('审查意见通知书 JSON OK')

# 驳回决定
info2 = OfficeActionInfo(
    doc_type='驳回决定',
    发明创造名称='测试发明2',
    申请号='202510345297.0',
    申请人='测试公司2',
    驳回依据='专利法第22条第3款',
    针对的申请文件='原始申请文件',
    审查员代码='12345',
)
json2 = gen.generate_office_action(info2, is_image_based=True)
assert '著录项目' not in json2, '驳回决定不应有著录项目'
assert json2['驳回依据'] == '专利法第22条第3款', '驳回依据应为顶层字段'
assert json2['审查员代码'] == '12345', '审查员代码应为顶层字段'
print('驳回决定 JSON OK')

# 复审决定书
info3 = OfficeActionInfo(
    doc_type='复审决定书',
    发明创造名称='测试发明3',
    申请号='202510345298.1',
    复审请求人='测试公司3',
    决定号='123456',
    决定日='2025年03月20日',
    合议组组长='李四',
    主审员='王五',
    参审员='赵六',
    决定结果='撤销驳回决定',
    法律依据='专利法第22条第3款',
    决定要点='如果...',
    复审决定首页简述='本决定涉及...',
)
json3 = gen.generate_office_action(info3, is_image_based=True)
assert '著录项目' not in json3, '复审决定书不应有著录项目'
assert json3['决定号'] == '123456', '决定号应为顶层字段'
assert json3['合议组']['组长'] == '李四', '合议组应有组长字段'
assert json3['决定摘要'] == '本决定涉及...', '复审决定首页简述应映射为决定摘要'
print('复审决定书 JSON OK')

# 测试Markdown生成
md_gen = MarkdownGenerator()

md1 = md_gen.generate_office_action(json1)
assert '## 审查意见通知书' in md1, '应有审查意见通知书标题'
assert '### 基本信息' in md1, '应有基本信息标题'
assert '### 通知书首页事项' in md1, '应有通知书首页事项标题'
print('审查意见通知书 Markdown OK')

md2 = md_gen.generate_office_action(json2)
assert '## 驳回决定' in md2, '应有驳回决定标题'
assert '### 驳回依据' in md2, '应有驳回依据标题'
assert '### 针对的申请文件' in md2, '应有针对的申请文件标题'
print('驳回决定 Markdown OK')

md3 = md_gen.generate_office_action(json3)
assert '## 复审决定书' in md3, '应有复审决定书标题'
assert '### 合议组' in md3, '应有合议组标题'
assert '### 决定结果' in md3, '应有决定结果标题'
assert '### 决定要点' in md3, '应有决定要点标题'
print('复审决定书 Markdown OK')

print('\nAll tests passed!')
