# -*- coding: utf-8 -*-
"""
Agent输出JSON验证器 (output_validator.py)

功能：自动验证审查Agent输出的JSON格式是否符合规范
版本：v2.0 (2026-05-10) - 适配 checking-cn-patent-format 的13个Agent
用途：在第4步Agent完成后、第5步合并前调用，确保数据质量

使用方法：
    python output_validator.py --work-dir "<work_dir>" --timestamp "<timestamp>" --extracted-text "<work_dir>/extracted_text_<timestamp>.txt"
    python output_validator.py --file "<json_file>" --extracted-text "<work_dir>/extracted_text_<timestamp>.txt"
"""

import json
import os
import re
import sys
import io
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except (AttributeError, io.UnsupportedOperation):
    pass


class OutputValidator:
    """Agent输出验证器 - 适配13个审查Agent"""

    REQUIRED_FIELDS = ['section', 'context', 'action_type', 'issue', 'suggestion']

    CONDITIONAL_REQUIRED_FIELDS = {
        'replace': ['old_text', 'new_text'],
        'delete': ['old_text'],
    }

    OPTIONAL_FIELDS = ['paragraph_index', 'claim_number', 'highlight_text',
                       'old_text', 'new_text', 'occurrence', 'rule_id',
                       'severity', 'figure_id', 'marker_number']

    VALID_ACTION_TYPE = ['comment', 'replace', 'delete']

    VALID_SECTIONS = [
        '摘要', '权利要求书', '说明书', '说明书附图',
        '摘要附图', '全文'
    ]

    MAX_CONTEXT_LENGTH = 200

    def __init__(self, extracted_text_path: Optional[str] = None):
        self.extracted_text = None
        if extracted_text_path and os.path.exists(extracted_text_path):
            with open(extracted_text_path, 'r', encoding='utf-8') as f:
                self.extracted_text = f.read()

        self.validation_result = {
            'is_valid': True,
            'total_items': 0,
            'valid_items': 0,
            'invalid_items': 0,
            'warnings': [],
            'errors': [],
            'auto_fixes': []
        }

    def validate_file(self, file_path: str) -> Dict:
        print(f"\n验证文件: {os.path.basename(file_path)}")

        if not os.path.exists(file_path):
            self._add_error('FILE_NOT_FOUND', f'文件不存在: {file_path}')
            return self.validation_result

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self._add_error('JSON_PARSE_ERROR', f'JSON解析错误: {str(e)}')
            return self.validation_result
        except Exception as e:
            self._add_error('FILE_READ_ERROR', f'文件读取错误: {str(e)}')
            return self.validation_result

        if not isinstance(data, list):
            self._add_error('INVALID_ROOT_TYPE', f'根元素应为数组(list)，实际为{type(data).__name__}')
            return self.validation_result

        if len(data) == 0:
            self._add_error('EMPTY_ARRAY', '输出数组为空，该Agent未产生任何审查结果。可能原因：LLM调用返回空内容、Agent prompt与文档不匹配、或并行执行时的资源竞争。此问题将导致对应审查维度完全缺失（false negative风险：高）')
            return self.validation_result

        self.validation_result['total_items'] = len(data)

        for i, item in enumerate(data):
            self._validate_item(item, index=i + 1)

        self._generate_summary()

        return self.validation_result

    def _validate_item(self, item: Dict, index: int):
        item_valid = True
        action_type = item.get('action_type', 'comment')

        for field in self.REQUIRED_FIELDS:
            if field not in item or item[field] is None:
                self._add_item_error(index, '', 'MISSING_FIELD', f'缺少必填字段: {field}')
                item_valid = False
            elif isinstance(item[field], str) and len(item[field].strip()) == 0:
                self._add_item_error(index, '', 'EMPTY_FIELD', f'必填字段为空字符串: {field}')
                item_valid = False

        if action_type in self.CONDITIONAL_REQUIRED_FIELDS:
            for field in self.CONDITIONAL_REQUIRED_FIELDS[action_type]:
                if field not in item or item[field] is None or item[field] == '':
                    self._add_item_error(index, '', 'MISSING_CONDITIONAL_FIELD',
                                         f'{action_type}类型缺少必填字段: {field}')
                    item_valid = False

        if 'section' in item:
            if item['section'] not in self.VALID_SECTIONS:
                self._add_item_warning(index, '', 'UNKNOWN_SECTION',
                                       f"章节名称不在标准列表中: '{item['section']}'")

        if 'context' in item and item['context']:
            context = str(item['context'])

            if len(context) > self.MAX_CONTEXT_LENGTH:
                self._add_item_error(index, '', 'CONTEXT_TOO_LONG',
                                     f"context长度{len(context)}字符，超过{self.MAX_CONTEXT_LENGTH}字符限制")
                item['context'] = context[:self.MAX_CONTEXT_LENGTH - 3] + '...'
                self._auto_fix(index, '', 'CONTEXT_TOO_LONG_TRUNCATED',
                               f'已截断context至{self.MAX_CONTEXT_LENGTH}字符')

            if '\n' in context or '\r' in context:
                self._add_item_error(index, '', 'CONTEXT_CONTAINS_NEWLINE',
                                     'context包含换行符，将导致review_adder.py匹配失败')
                item['context'] = context.replace('\n', ' ').replace('\r', ' ')
                self._auto_fix(index, '', 'NEWLINE_REMOVED',
                               '已移除context中的换行符（注意：应拆分为多条审查意见）')

            if self.extracted_text:
                clean_context = context.replace('...', '').replace('……', '').strip()
                if clean_context and clean_context not in self.extracted_text:
                    self._add_item_warning(index, '', 'CONTEXT_NOT_IN_DOCUMENT',
                                           f"context未在文档文本中找到: '{context[:50]}...'")

        if 'old_text' in item and item['old_text']:
            old_text = str(item['old_text'])

            if '\n' in old_text or '\r' in old_text:
                self._add_item_error(index, '', 'OLD_TEXT_CONTAINS_NEWLINE',
                                     'old_text包含换行符，将导致review_adder.py匹配失败')

            if 'context' in item and item['context']:
                if old_text not in str(item['context']):
                    self._add_item_error(index, '', 'OLD_TEXT_NOT_IN_CONTEXT',
                                         'old_text不是context的子串，将导致review_adder.py匹配失败')

        if 'new_text' in item and item['new_text']:
            new_text = str(item['new_text'])
            if '\n' in new_text or '\r' in new_text:
                self._add_item_error(index, '', 'NEW_TEXT_CONTAINS_NEWLINE',
                                     'new_text包含换行符，docx中无法通过替换插入新段落')

        if 'highlight_text' in item and item['highlight_text']:
            ht = str(item['highlight_text'])
            if 'context' in item and item['context']:
                if ht not in str(item['context']):
                    self._add_item_error(index, '', 'HIGHLIGHT_NOT_IN_CONTEXT',
                                         'highlight_text不是context的子串')

        if 'occurrence' in item and item['occurrence'] is not None:
            occ = item['occurrence']
            if not isinstance(occ, int) or occ < 1:
                self._add_item_error(index, '', 'INVALID_OCCURRENCE',
                                     f'occurrence必须为正整数，实际为: {occ}')
            elif occ > 5:
                self._add_item_warning(index, '', 'HIGH_OCCURRENCE',
                                       f'occurrence值为{occ}，可能因前序操作失效，建议改用comment类型')

        if 'issue' in item and item['issue']:
            issue_str = str(item['issue'])
            control_char_pattern = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
            if control_char_pattern.search(issue_str):
                self._add_item_error(index, '', 'ISSUE_CONTAINS_CONTROL_CHARS',
                                     'issue包含ASCII控制字符，将导致XML解析崩溃')
                item['issue'] = control_char_pattern.sub('', issue_str)
                self._auto_fix(index, '', 'CONTROL_CHARS_REMOVED',
                               '已移除issue中的控制字符')

            emoji_pattern = re.compile(
                r'[\U0001F300-\U0001F9FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F\U0001F600-\U0001F64F\U0001F680-\U0001F6FF]')
            if emoji_pattern.search(issue_str):
                self._add_item_warning(index, '', 'ISSUE_CONTAINS_EMOJI',
                                       'issue包含emoji符号，可能导致XML解析问题')

        if 'suggestion' in item and item['suggestion']:
            sug_str = str(item['suggestion'])
            control_char_pattern = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
            if control_char_pattern.search(sug_str):
                self._add_item_error(index, '', 'SUGGESTION_CONTAINS_CONTROL_CHARS',
                                     'suggestion包含ASCII控制字符，将导致XML解析崩溃')
                item['suggestion'] = control_char_pattern.sub('', sug_str)
                self._auto_fix(index, '', 'SUGGESTION_CONTROL_CHARS_REMOVED',
                               '已移除suggestion中的控制字符')

        # 【BUG-001修复】检测文本字段中是否包含Unicode转义序列
        unicode_escape_pattern = re.compile(r'\\u[0-9a-fA-F]{4}')
        for field_name in ['context', 'highlight_text', 'old_text', 'new_text', 'issue', 'suggestion']:
            field_val = item.get(field_name)
            if field_val and isinstance(field_val, str):
                if unicode_escape_pattern.search(field_val):
                    self._add_item_warning(index, '', 'UNICODE_ESCAPE_IN_TEXT',
                                           f'{field_name}包含Unicode转义序列(\\uXXXX)，应使用原始UTF-8字符。merge_reviews.py会自动规范化，但建议Agent从源头避免。')

        if item_valid:
            self.validation_result['valid_items'] += 1
        else:
            self.validation_result['invalid_items'] += 1

    def _add_error(self, code: str, message: str):
        self.validation_result['is_valid'] = False
        self.validation_result['errors'].append({
            'code': code,
            'message': message,
            'level': 'error'
        })

    def _add_warning(self, code: str, message: str):
        self.validation_result['warnings'].append({
            'code': code,
            'message': message,
            'level': 'warning'
        })

    def _add_item_error(self, index: int, rule_id: str, code: str, message: str):
        self.validation_result['is_valid'] = False
        self.validation_result['errors'].append({
            'code': code,
            'message': f'[#{index}] {rule_id}: {message}',
            'level': 'error',
            'item_index': index,
            'rule_id': rule_id
        })

    def _add_item_warning(self, index: int, rule_id: str, code: str, message: str):
        self.validation_result['warnings'].append({
            'code': code,
            'message': f'[#{index}] {rule_id}: {message}',
            'level': 'warning',
            'item_index': index,
            'rule_id': rule_id
        })

    def _auto_fix(self, index: int, rule_id: str, fix_code: str, message: str):
        self.validation_result['auto_fixes'].append({
            'code': fix_code,
            'message': f'[#{index}] {rule_id}: {message}',
            'item_index': index,
            'rule_id': rule_id
        })

    def _generate_summary(self):
        total = self.validation_result['total_items']
        valid = self.validation_result['valid_items']
        invalid = self.validation_result['invalid_items']

        self.validation_result['summary'] = {
            'file_status': 'PASS' if self.validation_result['is_valid'] else 'NEEDS_FIX',
            'item_pass_rate': f"{(valid / total * 100):.1f}%" if total > 0 else "N/A",
            'error_count': len([e for e in self.validation_result['errors'] if e.get('level') == 'error']),
            'warning_count': len(self.validation_result['warnings']),
            'auto_fix_count': len(self.validation_result['auto_fixes'])
        }

    def print_report(self):
        print("\n" + "=" * 60)
        print("Agent输出验证报告")
        print("=" * 60)

        status = '通过' if self.validation_result['is_valid'] else '需要修复'
        print(f"\n总体状态: {status}")
        print(f"   总条目数: {self.validation_result['total_items']}")
        print(f"   有效条目: {self.validation_result['valid_items']}")
        print(f"   无效条目: {self.validation_result['invalid_items']}")

        summary = self.validation_result.get('summary', {})
        if summary:
            print(f"   通过率: {summary.get('item_pass_rate', 'N/A')}")

        if self.validation_result['errors']:
            print(f"\n错误 ({len(self.validation_result['errors'])}项):")
            for err in self.validation_result['errors'][:10]:
                print(f"   [{err['code']}] {err['message']}")
            if len(self.validation_result['errors']) > 10:
                print(f"   ... 还有{len(self.validation_result['errors']) - 10}项错误")

        if self.validation_result['warnings']:
            print(f"\n警告 ({len(self.validation_result['warnings'])}项):")
            for warn in self.validation_result['warnings'][:10]:
                print(f"   [{warn['code']}] {warn['message']}")

        if self.validation_result['auto_fixes']:
            print(f"\n自动修复 ({len(self.validation_result['auto_fixes'])}项):")
            for fix in self.validation_result['auto_fixes']:
                print(f"   {fix['message']}")

        print("\n" + "=" * 60 + "\n")


def validate_agent_output(json_file_path: str, extracted_text_path: Optional[str] = None,
                          auto_save: bool = False) -> Tuple[bool, Dict]:
    validator = OutputValidator(extracted_text_path)
    result = validator.validate_file(json_file_path)
    validator.print_report()

    if auto_save and result.get('auto_fixes'):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"已保存自动修复后的文件: {json_file_path}")
        except Exception as e:
            print(f"保存修复文件失败: {e}")

    return result['is_valid'], result


def validate_all_agents(work_dir: str, timestamp: str,
                        extracted_text_path: Optional[str] = None) -> Dict:
    results = {}
    all_passed = True

    for i in range(1, 14):
        file_name = f'reviews_agent{i}_{timestamp}.json'
        file_path = os.path.join(work_dir, file_name)

        if os.path.exists(file_path):
            is_valid, result = validate_agent_output(file_path, extracted_text_path)
            results[f'agent{i}'] = {
                'file': file_name,
                'is_valid': is_valid,
                'result': result
            }
            if not is_valid:
                all_passed = False
        else:
            results[f'agent{i}'] = {
                'file': file_name,
                'is_valid': True,
                'result': {'note': '文件不存在，可能该Agent无输出'}
            }

    return {
        'all_passed': all_passed,
        'agents': results
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Agent输出JSON验证器 v2.0 (checking-cn-patent-format)')
    parser.add_argument('--file', '-f', help='单个JSON文件路径')
    parser.add_argument('--work-dir', '-w', help='工作目录路径（批量验证）')
    parser.add_argument('--timestamp', '-t', help='时间戳（配合--work-dir使用）')
    parser.add_argument('--extracted-text', '-e', help='文档提取文本路径（用于context验证）')
    parser.add_argument('--auto-save', action='store_true', help='自动保存修复后的文件')

    args = parser.parse_args()

    if args.file:
        is_valid, _ = validate_agent_output(args.file, args.extracted_text, args.auto_save)
        exit(0 if is_valid else 1)
    elif args.work_dir and args.timestamp:
        result = validate_all_agents(args.work_dir, args.timestamp, args.extracted_text)
        exit(0 if result['all_passed'] else 1)
    else:
        parser.print_help()
        exit(1)
