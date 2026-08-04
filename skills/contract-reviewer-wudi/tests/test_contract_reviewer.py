#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
contract-reviewer-wudi 单元测试

运行方式：
    cd ~/.qclaw/skills/contract-reviewer-wudi
    python3 -m pytest tests/ -v
"""

import json
import sys
import unittest
from pathlib import Path

# 添加 scripts 目录到路径
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from preflight_check import validate_schema, detect_json_format, normalize_changes


class TestJSONSchema(unittest.TestCase):
    """测试 JSON schema 验证"""

    def test_valid_revision(self):
        """测试有效的修订条目"""
        data = {
            'revisions': [
                {'paragraph_index': 0, 'original_text': 'test', 'revised_text': 'modified'}
            ],
            'comments': []
        }
        errors = validate_schema(data)
        self.assertEqual(len(errors), 0)

    def test_empty_revised_text(self):
        """测试空的修订文本"""
        data = {
            'revisions': [
                {'paragraph_index': 0, 'original_text': 'test', 'revised_text': ''}
            ],
            'comments': []
        }
        errors = validate_schema(data)
        self.assertGreater(len(errors), 0)
        self.assertIn('revised_text 为空', errors[0])

    def test_empty_comment_text(self):
        """测试空的批注内容"""
        data = {
            'revisions': [],
            'comments': [
                {'paragraph_index': 0, 'highlight_text': 'test', 'comment': ''}
            ]
        }
        errors = validate_schema(data)
        self.assertGreater(len(errors), 0)
        self.assertIn('comment 为空', errors[0])

    def test_missing_paragraph_index(self):
        """测试缺少段落索引"""
        data = {
            'revisions': [
                {'original_text': 'test', 'revised_text': 'modified'}
            ],
            'comments': []
        }
        errors = validate_schema(data)
        self.assertGreater(len(errors), 0)
        self.assertIn('缺少 paragraph_index', errors[0])


class TestJSONFormatDetection(unittest.TestCase):
    """测试 JSON 格式检测"""

    def test_standard_format(self):
        """测试标准格式"""
        data = {
            'revisions': [],
            'comments': []
        }
        fmt = detect_json_format(data)
        self.assertEqual(fmt, 'correct')

    def test_flat_format(self):
        """测试扁平格式"""
        data = {
            'changes': []
        }
        fmt = detect_json_format(data)
        self.assertEqual(fmt, 'flat')

    def test_unknown_format(self):
        """测试未知格式"""
        data = {
            'unknown_key': []
        }
        fmt = detect_json_format(data)
        self.assertEqual(fmt, 'unknown')


class TestJSONNormalization(unittest.TestCase):
    """测试 JSON 格式转换"""

    def test_flat_to_standard(self):
        """测试扁平格式转换"""
        flat = {
            'changes': [
                {
                    'paragraph_index': 0,
                    'original_text': 'test',
                    'revised_text': 'modified'
                }
            ]
        }
        normalized = normalize_changes(flat)
        
        # 扁平格式的 changes 会被转换为 revisions
        self.assertIn('revisions', normalized)
        self.assertIn('comments', normalized)
        self.assertEqual(len(normalized['revisions']), 1)
        # comments 应该为空（因为没有 comment 字段）
        self.assertEqual(len(normalized['comments']), 0)


class TestChineseQuotes(unittest.TestCase):
    """测试中文引号处理"""

    def test_chinese_quotes_in_json(self):
        """测试 JSON 中的中文引号"""
        # 这个测试验证之前修复的 bug
        text_with_quotes = '建议修订为"任何时候均可解除"'
        
        # 应该能正常序列化
        json_str = json.dumps({'text': text_with_quotes}, ensure_ascii=False)
        
        # 应该能正常反序列化
        loaded = json.loads(json_str)
        self.assertEqual(loaded['text'], text_with_quotes)


class TestParagraphMatching(unittest.TestCase):
    """测试段落匹配逻辑"""

    def test_exact_match(self):
        """测试精确匹配"""
        from preflight_check import try_match
        
        para_text = "第十二条 违约金条款"
        original = "违约金条款"
        
        score, reason = try_match(para_text, original)
        self.assertGreaterEqual(score, 100)
        self.assertIn('完整匹配', reason)

    def test_partial_match(self):
        """测试部分匹配"""
        from preflight_check import try_match
        
        para_text = "第十二条 违约金条款，每日按合同总金额的0.5%计算"
        original = "违约金条款"
        
        score, reason = try_match(para_text, original)
        self.assertGreaterEqual(score, 100)

    def test_no_match(self):
        """测试无匹配"""
        from preflight_check import try_match
        
        para_text = "第十二条 违约金条款"
        original = "完全不同的文本"
        
        score, reason = try_match(para_text, original)
        self.assertEqual(score, 0)


if __name__ == '__main__':
    unittest.main()
