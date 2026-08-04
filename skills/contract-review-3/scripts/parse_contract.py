#!/usr/bin/env python3
"""
合同解析脚本 - Phase 0
功能：从文本中提取合同结构化信息
"""

import re
from typing import Dict, List, Optional

class ContractParser:
    """合同解析器"""
    
    # 合同基本信息提取模式
    PATTERNS = {
        'contract_name': [
            r'合同名称[：:]\s*(.+)',
            r'《([^》]+)》',
            r'编号[：:]?\s*([A-Z0-9-]+)',
        ],
        'party_a': [
            r'甲方[（(]?[^)]*?[）)]?\s*[：:]\s*(.+)',
            r'委托方[（(]?[甲]?[）)]?\s*[：:]\s*(.+)',
            r'出卖方[：:]\s*(.+)',
            r'买受方[：:]\s*(.+)',
            r'出租方[：:]\s*(.+)',
            r'发包方[：:]\s*(.+)',
        ],
        'party_b': [
            r'乙方[（(]?[^)]*?[）)]?\s*[：:]\s*(.+)',
            r'受托方[（(]?[乙]?[）)]?\s*[：:]\s*(.+)',
            r'买受方[：:]\s*(.+)',
            r'出卖方[：:]\s*(.+)',
            r'承租方[：:]\s*(.+)',
            r'承包方[：:]\s*(.+)',
        ],
        'signing_date': [
            r'签署日期[：:]\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)',
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
        ],
        'contract_amount': [
            r'[金总]额[：:]\s*([¥￥]?\s*[\d,]+[\.\d]*\s*(?:元|万|亿)?)',
            r'人民币\s*([¥￥]?\s*[\d,]+[\.\d]*)',
        ],
    }
    
    # 常见关键条款关键词
    KEY_CLAUSE_KEYWORDS = {
        '付款条款': ['付款', '支付', '价款', '报酬', '费用', '收费'],
        '违约条款': ['违约', '违约金', '赔偿', '损失', '责任'],
        '保密条款': ['保密', '机密', '信息披露', '限制使用'],
        '知识产权条款': ['知识产权', '专利', '版权', '著作权', '权属'],
        '争议解决条款': ['争议', '仲裁', '诉讼', '管辖', '法院'],
        '终止条款': ['终止', '解除', '期满', '届满', '失效'],
        '不可抗力条款': ['不可抗力', '自然灾害', '政府行为'],
        '变更条款': ['变更', '修改', '补充', '更新'],
    }
    
    def __init__(self, text: str):
        """初始化解析器"""
        self.text = text
        self.lines = text.split('\n')
        
    def parse(self) -> Dict:
        """执行完整解析"""
        return {
            'basic_info': self.extract_basic_info(),
            'structure': self.extract_structure(),
            'key_clauses': self.extract_key_clauses(),
            'statistics': self.get_statistics(),
        }
    
    def extract_basic_info(self) -> Dict[str, str]:
        """提取基本信息"""
        info = {}
        text = self.text
        
        for field, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    info[field] = match.group(1).strip()
                    break
                    
        return info
    
    def extract_structure(self) -> List[Dict]:
        """提取合同结构（章节/条款列表）"""
        structure = []
        current_chapter = None
        current_section = None
        
        for i, line in enumerate(self.lines):
            line = line.strip()
            if not line:
                continue
                
            # 章节标题（数字 + 条/章/节）
            chapter_match = re.match(r'^(第[一二三四五六七八九十百零\d]+[章条节款])[：:\s]*(.*)', line)
            if chapter_match:
                title = chapter_match.group(1)
                content = chapter_match.group(2).strip()
                current_chapter = {
                    'level': 1,
                    'title': title,
                    'content': content,
                    'line_start': i + 1,
                    'line_end': i + 1,
                }
                structure.append(current_chapter)
                continue
                
            # 继续收集上一条的内容
            if current_chapter and len(line) > 10:
                current_chapter['content'] += ' ' + line
                current_chapter['line_end'] = i + 1
                
        return structure
    
    def extract_key_clauses(self) -> Dict[str, List[Dict]]:
        """提取关键条款"""
        clauses = {name: [] for name in self.KEY_CLAUSE_KEYWORDS}
        
        for clause_type, keywords in self.KEY_CLAUSE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in self.text:
                    # 找到包含关键词的句子
                    sentences = re.split(r'[。；\n]', self.text)
                    for sent in sentences:
                        if keyword in sent and len(sent) > 10:
                            clauses[clause_type].append({
                                'keyword': keyword,
                                'content': sent.strip(),
                            })
                            break  # 每个类型只取第一个匹配
                            
        # 移除空列表
        return {k: v for k, v in clauses.items() if v}
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'total_chars': len(self.text),
            'total_lines': len(self.lines),
            'has_party_a': bool(self.extract_basic_info().get('party_a')),
            'has_party_b': bool(self.extract_basic_info().get('party_b')),
            'has_amount': bool(self.extract_basic_info().get('contract_amount')),
            'key_clauses_count': len([v for v in self.extract_key_clauses().values() if v]),
        }


def main(text: str) -> Dict:
    """主入口"""
    parser = ContractParser(text)
    return parser.parse()


if __name__ == '__main__':
    # 测试
    sample = """
    咨询服务合同
    
    合同编号：ZX-2024-001
    委托方（甲方）：大兴安岭农村商业银行股份有限公司
    受托方（乙方）：知恒律师事务所
    
    第一条 服务内容
    乙方为甲方提供二级资本债赎回相关法律咨询服务。
    
    第二条 服务费用
    甲方应向乙方支付咨询服务费用人民币50万元。
    
    第三条 违约责任
    任何一方违约应承担相应法律责任。
    """
    result = main(sample)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
