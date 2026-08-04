#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
要素式文书一键生成器 v3 - 主入口

核心改进：使用区域定位的填充策略，避免跨区域误填
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional, Dict, List, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

from file_parser import FileParser
from case_classifier import CaseClassifier
from template_manager import TemplateManager
from content_extractor import ContentExtractor
from template_filler import TemplateFiller


class ElementLawsuitGenerator:
    """要素式文书一键生成器"""

    def __init__(self, local_template_dir=None, local_example_dir=None, 
                 output_dir=None, config_dir=None):
        if config_dir is None:
            config_dir = os.path.join(BASE_DIR, 'configs')
        if output_dir is None:
            output_dir = os.path.join(BASE_DIR, 'output')
        
        self.config_dir = config_dir
        self.output_dir = output_dir
        self.local_template_dir = local_template_dir
        self.local_example_dir = local_example_dir
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.parser = FileParser()
        self.classifier = CaseClassifier(config_dir)
        self.template_mgr = TemplateManager(
            cache_dir=os.path.join(BASE_DIR, 'template_cache'),
            config_dir=config_dir,
            local_template_dir=local_template_dir
        )
        self.extractor = ContentExtractor(config_dir)

    def generate(self, file_path, case_type_override=None, doc_type_override=None):
        """一键生成要素式文书"""
        result = {
            "success": False, "output_path": "", "case_type": "", "doc_type": "",
            "confidence": 0.0, "template_used": "", "extracted_data": {},
            "errors": [], "warnings": [],
        }
        
        try:
            print(f"[1/6] 解析文件: {file_path}")
            text = self.parser.parse(file_path)
            if not text or not text.strip():
                result["errors"].append("文件内容为空")
                return result
            
            print(f"[2/6] 识别案由和文书类型")
            if case_type_override:
                case_type = case_type_override
                doc_type = doc_type_override or self._infer_doc_type(text)
                confidence = 1.0
            else:
                case_type, doc_type, confidence = self.classifier.classify(text)
                if confidence < 0.3:
                    result["warnings"].append(f"案由识别置信度较低({confidence})，建议人工确认")
            
            result["case_type"] = case_type
            result["doc_type"] = doc_type
            result["confidence"] = confidence
            
            if case_type == "未知":
                result["errors"].append("无法识别案由，请手动指定")
                return result
            
            print(f"[3/6] 获取模板")
            template_filename = self.classifier.get_template_filename(case_type, doc_type)
            template_path = self.template_mgr.get_template(case_type, doc_type)
            if not template_path:
                result["errors"].append(f"未找到模板: {template_filename}")
                return result
            result["template_used"] = template_filename
            
            print(f"[4/6] 提取关键要素")
            extracted = self.extractor.extract(text, case_type, doc_type)
            result["extracted_data"] = extracted
            
            print(f"[5/6] 构建区域化填充数据")
            fill_data = self._build_fill_data(extracted, case_type, doc_type)
            
            print(f"[6/6] 填充模板")
            output_filename = self._generate_output_filename(case_type, doc_type)
            filler = TemplateFiller(template_path, self.output_dir)
            output_path = filler.fill(fill_data, output_filename)
            
            result["success"] = True
            result["output_path"] = output_path
            print(f"  → 生成成功: {output_path}")
            
        except Exception as e:
            result["errors"].append(f"生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return result

    def _infer_doc_type(self, text):
        _, doc_type, _ = self.classifier.classify(text)
        return doc_type

    def _build_fill_data(self, extracted: Dict, case_type: str, doc_type: str) -> Dict:
        """
        构建区域化填充数据 - 根据文书类型动态映射区域
        """
        fill_data = {
            'section_fills': [],
            'checkbox_ops': [],
            'text_replacements': {},
        }
        
        parties = extracted.get('parties', {})
        signature = extracted.get('signature', {})
        
        # 根据文书类型确定区域映射
        DOC_TYPE_CONFIG = {
            '民事起诉状': {
                'party1_section': '原告', 'party1_key': 'plaintiff',
                'party2_section': '被告', 'party2_key': 'defendant',
                'request_section': '诉讼请求', 'reason_section': '事实与理由',
                'signature_label': '具状人', 'agent_section': '委托诉讼代理人',
            },
            '民事答辩状': {
                'party1_section': '答辩人', 'party1_key': 'plaintiff',
                'party2_section': None, 'party2_key': None,
                'request_section': '答辩事项', 'reason_section': '事实与理由',
                'signature_label': '答辩人', 'agent_section': '委托诉讼代理人',
            },
            '刑事自诉状': {
                'party1_section': '自诉人', 'party1_key': 'plaintiff',
                'party2_section': '被告人', 'party2_key': 'defendant',
                'request_section': '诉讼请求', 'reason_section': '事实与理由',
                'signature_label': '具状人', 'agent_section': '诉讼代理人',
            },
            '行政起诉状': {
                'party1_section': '原告', 'party1_key': 'plaintiff',
                'party2_section': '被告', 'party2_key': 'defendant',
                'request_section': '诉讼请求', 'reason_section': '事实与理由',
                'signature_label': '具状人', 'agent_section': '委托诉讼代理人',
            },
            '国家赔偿申请书': {
                'party1_section': '赔偿请求人', 'party1_key': 'plaintiff',
                'party2_section': '赔偿义务机关', 'party2_key': 'defendant',
                'request_section': '赔偿请求', 'reason_section': '事实与理由',
                'signature_label': '赔偿请求人', 'agent_section': '委托代理人',
            },
            '刑事自诉答辩状': {
                'party1_section': '答辩人', 'party1_key': 'plaintiff',
                'party2_section': None, 'party2_key': None,
                'request_section': '答辩意见', 'reason_section': None,
                'signature_label': '答辩人', 'agent_section': '辩护人',
            },
            '行政答辩状': {
                'party1_section': '答辩人', 'party1_key': 'plaintiff',
                'party2_section': None, 'party2_key': None,
                'request_section': '答辩事项', 'reason_section': None,
                'signature_label': '答辩人', 'agent_section': '委托诉讼代理人',
            },
            '国家赔偿答辩状': {
                'party1_section': '答辩人', 'party1_key': 'plaintiff',
                'party2_section': None, 'party2_key': None,
                'request_section': '答辩意见', 'reason_section': None,
                'signature_label': '答辩人', 'agent_section': '委托诉讼代理人',
            },
            '第三人意见陈述书': {
                'party1_section': '第三人', 'party1_key': 'plaintiff',
                'party2_section': None, 'party2_key': None,
                'request_section': '诉讼请求', 'reason_section': '事实与理由',
                'signature_label': '陈述人', 'agent_section': '委托诉讼代理人',
            },
        }
        
        config = DOC_TYPE_CONFIG.get(doc_type, DOC_TYPE_CONFIG['民事起诉状'])
        
        # 通用自然人字段
        NATURAL_PERSON_FIELDS = [
            ('name', '姓名：'), ('birthdate', '出生日期：'), ('ethnicity', '民族：'),
            ('work_unit', '工作单位：'), ('position', '职务：'), ('phone', '联系电话：'),
            ('address', '住所地（户籍所在地）：'), ('residence', '经常居住地：'),
            ('id_type', '证件类型：'), ('id_number', '证件号码：'),
        ]
        
        # 通用法人字段
        LEGAL_PERSON_FIELDS = [
            ('name', '名称：'), ('address', '住所地（主要办事机构所在地）：'),
            ('legal_person', '法定代表人 / 负责人：'), ('phone', '联系电话：'),
            ('credit_code', '统一社会信用代码：'),
        ]
        
        # === 当事人1区域 ===
        party1 = parties.get(config['party1_key'], {})
        if party1 and party1.get('type') == 'natural':
            fields = {}
            for key, label in NATURAL_PERSON_FIELDS:
                if party1.get(key):
                    fields[label] = party1[key]
            fill_data['section_fills'].append({
                'section': f'{config["party1_section"]}_自然人',
                'fields': fields,
                'checkboxes': {},
            })
            # 性别勾选框
            gender = party1.get('gender', '')
            if gender:
                fill_data['checkbox_ops'].append({
                    'section': f'{config["party1_section"]}_自然人',
                    'paragraph_contains': '性别',
                    'before_checkbox': gender,
                    'check': True,
                })
        elif party1 and party1.get('type') == 'legal':
            fields = {}
            for key, label in LEGAL_PERSON_FIELDS:
                if party1.get(key):
                    fields[label] = party1[key]
            fill_data['section_fills'].append({
                'section': f'{config["party1_section"]}_法人',
                'fields': fields,
                'checkboxes': {},
            })
        
        # === 当事人2区域 ===
        if config.get('party2_section') and config.get('party2_key'):
            party2 = parties.get(config['party2_key'], {})
            if party2 and party2.get('type') == 'natural':
                fields = {}
                for key, label in NATURAL_PERSON_FIELDS:
                    if party2.get(key):
                        fields[label] = party2[key]
                fill_data['section_fills'].append({
                    'section': f'{config["party2_section"]}_自然人',
                    'fields': fields,
                    'checkboxes': {},
                })
                gender = party2.get('gender', '')
                if gender:
                    fill_data['checkbox_ops'].append({
                        'section': f'{config["party2_section"]}_自然人',
                        'paragraph_contains': '性别',
                        'before_checkbox': gender,
                        'check': True,
                    })
            elif party2 and party2.get('type') == 'legal':
                fields = {}
                for key, label in LEGAL_PERSON_FIELDS:
                    if party2.get(key):
                        fields[label] = party2[key]
                fill_data['section_fills'].append({
                    'section': f'{config["party2_section"]}_法人',
                    'fields': fields,
                    'checkboxes': {},
                })
            elif party2 and party2.get('type') == 'organ':
                # 赔偿义务机关等
                fields = {}
                if party2.get('name'):
                    fields['名称：'] = party2['name']
                if party2.get('address'):
                    fields['住所地：'] = party2['address']
                if party2.get('legal_person'):
                    fields['法定代表人 / 负责人：'] = party2['legal_person']
                if party2.get('phone'):
                    fields['联系电话：'] = party2['phone']
                fill_data['section_fills'].append({
                    'section': config['party2_section'],
                    'fields': fields,
                    'checkboxes': {},
                })
        
        # === 代理人区域 ===
        agent = parties.get('agent', {})
        if agent:
            has_agent = agent.get('has_agent', False)
            fields = {}
            checkboxes = {}
            checkboxes['有'] = has_agent
            if not has_agent:
                checkboxes['无'] = True
            if has_agent:
                if agent.get('name'):
                    fields['姓名：'] = agent['name']
                if agent.get('unit'):
                    fields['单位：'] = agent['unit']
                if agent.get('position'):
                    fields['职务：'] = agent['position']
                if agent.get('phone'):
                    fields['联系电话：'] = agent['phone']
                authority = agent.get('authority', '')
                if authority == '特别授权':
                    checkboxes['特别授权'] = True
                elif authority == '一般授权':
                    checkboxes['一般授权'] = True
                else:
                    checkboxes['无'] = True
            fill_data['section_fills'].append({
                'section': config['agent_section'],
                'fields': fields,
                'checkboxes': checkboxes,
            })
        
        # === 诉讼请求/答辩事项/赔偿请求区域 ===
        case_specific = extracted.get('case_specific', {})
        if case_specific and config.get('request_section'):
            request_fields = {}
            REQUEST_FIELD_MAP = {
                '本金金额': '截至', '利息金额': '截至', '标的总额': '标的总额',
                '诉讼请求概括': '诉讼请求', '答辩事项概括': '答辩事项',
                '赔偿请求概括': '赔偿请求',
            }
            for key, label in REQUEST_FIELD_MAP.items():
                if case_specific.get(key):
                    request_fields[label] = case_specific[key]
            if request_fields:
                fill_data['section_fills'].append({
                    'section': config['request_section'],
                    'fields': request_fields,
                    'checkboxes': {},
                })
        
        # === 事实与理由区域 ===
        if case_specific and config.get('reason_section'):
            reason_fields = {}
            REASON_FIELD_MAP = {
                '合同签订情况': '合同签订情况', '出借人': '出借人', '借款人': '借款人',
                '约定借款金额': '约定', '实际提供金额': '实际提供', '约定期限': '约定期限',
                '逾期时间': '逾期时间', '已还本金': '已还本金', '已还利息': '已还利息',
                '请求依据合同约定': '合同约定', '请求依据法律规定': '法律规定',
                '事实与理由概括': '事实与理由',
            }
            for key, label in REASON_FIELD_MAP.items():
                if case_specific.get(key):
                    reason_fields[label] = case_specific[key]
            if reason_fields:
                fill_data['section_fills'].append({
                    'section': config['reason_section'],
                    'fields': reason_fields,
                    'checkboxes': {},
                })
        
        # === 约定管辖区域 ===
        if case_specific and case_specific.get('管辖约定'):
            fill_data['section_fills'].append({
                'section': '约定管辖和诉前保全',
                'fields': {'合同条款及内容：': case_specific['管辖约定']},
                'checkboxes': {},
            })
        
        # === 勾选框操作 ===
        checkbox_ops = self._build_checkbox_ops(extracted, case_type, doc_type)
        fill_data['checkbox_ops'] = checkbox_ops
        
        # === 签名 ===
        sig_label = config.get('signature_label', '具状人')
        if signature.get('signer'):
            fill_data['text_replacements'][f'{sig_label}（签字、盖章）：'] = \
                f'{sig_label}（签字、盖章）：{signature["signer"]}'
        
        return fill_data
    def _build_checkbox_ops(self, extracted: Dict, case_type: str, doc_type: str = '民事起诉状') -> List[Dict]:
        """
        构建精确的勾选框操作
        
        关键：要区分"是/否"等通用勾选框在不同区域的含义
        """
        ops = []
        parties = extracted.get('parties', {})
        
        # 根据文书类型确定当事人section名
        DOC_TYPE_SECTIONS = {
            '民事起诉状': ('原告', '被告'),
            '民事答辩状': ('答辩人', None),
            '刑事自诉状': ('自诉人', '被告人'),
            '行政起诉状': ('原告', '被告'),
            '国家赔偿申请书': ('赔偿请求人', None),
            '刑事自诉答辩状': ('答辩人', None),
            '行政答辩状': ('答辩人', None),
            '国家赔偿答辩状': ('答辩人', None),
            '第三人意见陈述书': ('第三人', None),
        }
        p1_section, p2_section = DOC_TYPE_SECTIONS.get(doc_type, ('原告', '被告'))
        
        # 当事人1性别勾选
        plaintiff = parties.get('plaintiff', {})
        if plaintiff and plaintiff.get('type') == 'natural':
            gender = plaintiff.get('gender', '')
            if gender:
                ops.append({
                    'section': f'{p1_section}_自然人',
                    'paragraph_contains': '性别',
                    'before_checkbox': gender,
                    'check': True,
                })
        
        # 当事人2性别勾选
        if p2_section:
            defendant = parties.get('defendant', {})
            if defendant and defendant.get('type') == 'natural':
                gender = defendant.get('gender', '')
                if gender:
                    ops.append({
                        'section': f'{p2_section}_自然人',
                        'paragraph_contains': '性别',
                        'before_checkbox': gender,
                        'check': True,
                    })
        
        # 根据案由添加特定勾选框
        if case_type == '民间借贷纠纷':
            case_specific = extracted.get('case_specific', {})
            
            # 是否有管辖约定
            if case_specific.get('管辖约定'):
                ops.append({
                    'section': '',  # 全局搜索
                    'paragraph_contains': '有无仲裁',
                    'before_checkbox': '有',
                    'check': True,
                })
            
            # 是否诉前保全 - 否
            ops.append({
                'section': '',
                'paragraph_contains': '诉前保全',
                'before_checkbox': '否',
                'check': True,
            })
        
        return ops

    def _generate_output_filename(self, case_type, doc_type):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{doc_type}-{case_type}-要素式_{timestamp}.docx"


def main():
    parser = argparse.ArgumentParser(description='要素式文书一键生成器')
    parser.add_argument('file', help='输入文书文件路径')
    parser.add_argument('--output-dir', '-o', default=None)
    parser.add_argument('--local-templates', '-t', default=None)
    parser.add_argument('--case-type', '-c', default=None)
    parser.add_argument('--doc-type', '-d', default=None)
    parser.add_argument('--config-dir', default=None)
    
    args = parser.parse_args()
    
    generator = ElementLawsuitGenerator(
        local_template_dir=args.local_templates,
        output_dir=args.output_dir,
        config_dir=args.config_dir,
    )
    
    result = generator.generate(
        args.file,
        case_type_override=args.case_type,
        doc_type_override=args.doc_type,
    )
    
    print("\n" + "=" * 60)
    print("生成结果")
    print("=" * 60)
    for k, v in result.items():
        if k not in ('extracted_data',):
            print(f"  {k}: {v}")
    
    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
