#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同审查辅助系统 - 完整集成版 v2.0
集成所有优化功能，支持多种输入输出格式
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import argparse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入核心模块
from scripts.contract_review import ContractReviewer, RiskLevel
from scripts.enhanced_review import EnhancedContractReviewer
from scripts.word_generator import WordGenerator
from scripts.output_generator import OutputGenerator
from scripts.email_sender import EmailSender, create_email_template
from scripts.file_parser import FileParser, SmartFileParser
from scripts.law_search import LawSearch


class ContractReviewSystem:
    """合同审查系统主类"""
    
    def __init__(self, use_llm: bool = False, api_key: Optional[str] = None, use_law_kb: bool = True):
        """
        初始化系统
        
        Args:
            use_llm: 是否使用LLM增强审查
            api_key: LLM API密钥
            use_law_kb: 是否使用法律知识库
        """
        # 核心组件
        self.use_llm = use_llm
        if use_llm:
            self.reviewer = EnhancedContractReviewer(use_llm=True, api_key=api_key)
            if api_key:
                self.reviewer.setup_llm('openai', api_key)
        else:
            self.reviewer = ContractReviewer()
        
        # 文件解析器
        self.file_parser = SmartFileParser()
        
        # 输出生成器
        self.output_generator = OutputGenerator()
        
        # 邮件发送器
        self.email_sender = None
        
        # 法律知识库
        self.use_law_kb = use_law_kb
        self.law_searcher = LawSearch() if use_law_kb else None
        
        # 数据库
        self.db_path = 'review_history.db'
        self._init_database()
        
        # 当前审查结果
        self.current_result = None
        
        print("="*60)
        print("合同审查辅助系统 v2.1")
        print("="*60)
        print("✓ 条款提取    ✓ 风险识别    ✓ 差异比对")
        print("✓ 意见生成    ✓ 多格式输出  ✓ 邮件发送")
        if use_llm:
            print("✓ LLM增强    ✓ AI审查意见")
        if use_law_kb:
            print("✓ 法律知识库  ✓ 法律依据检索")
        print("="*60)
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_name TEXT,
                contract_type TEXT,
                parties TEXT,
                review_date TEXT,
                risk_count INTEGER,
                clause_count INTEGER,
                output_file TEXT,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_email(self, smtp_server: str, smtp_port: int, username: str, password: str):
        """配置邮件发送"""
        self.email_sender = EmailSender(smtp_server, smtp_port, username, password)
        print("✓ 邮件功能已配置")
    
    def review_file(self, file_path: str, contract_type: Optional[str] = None) -> Dict:
        """
        审查合同文件
        
        Args:
            file_path: 合同文件路径
            contract_type: 合同类型（可选）
        
        Returns:
            审查结果
        """
        print(f"\n正在审查文件: {file_path}")
        
        # 解析文件
        print("正在解析文件...")
        try:
            contract_text = self.file_parser.parse(file_path)
            print(f"✓ 文件解析成功 ({len(contract_text)} 字符)")
        except Exception as e:
            print(f"✗ 文件解析失败: {e}")
            return None
        
        # 执行审查
        print("正在执行审查...")
        if isinstance(self.reviewer, EnhancedContractReviewer):
            result = self.reviewer.enhanced_review(contract_text, contract_type)
        else:
            result = self.reviewer.review(contract_text)
        
        # 转换为字典格式
        result_dict = {
            'contract_type': result.contract_type,
            'parties': result.parties,
            'clauses': [
                {
                    'clause_type': c.clause_type,
                    'content': c.content,
                    'risk_level': c.risk_level.value,
                    'risk_analysis': '基于规则分析',
                    'suggestion': c.suggestion
                }
                for c in result.clauses
            ],
            'risks': result.risks,
            'suggestions': result.suggestions,
            'legal_references': []
        }
        
        self.current_result = result_dict
        
        # 检索相关法律条文
        if self.use_law_kb and self.law_searcher:
            print("正在检索相关法律条文...")
            self._add_legal_references(result_dict)
        
        # 保存到数据库
        self._save_to_history(file_path, result_dict)
        
        return result_dict
    
    def review_text(self, contract_text: str, contract_type: Optional[str] = None) -> Dict:
        """
        审查合同文本
        
        Args:
            contract_text: 合同文本内容
            contract_type: 合同类型（可选）
        
        Returns:
            审查结果
        """
        print("\n正在审查合同文本...")
        
        # 执行审查
        if isinstance(self.reviewer, EnhancedContractReviewer):
            result = self.reviewer.enhanced_review(contract_text, contract_type)
        else:
            result = self.reviewer.review(contract_text)
        
        # 转换为字典格式
        result_dict = {
            'contract_type': result.contract_type,
            'parties': result.parties,
            'clauses': [
                {
                    'clause_type': c.clause_type,
                    'content': c.content,
                    'risk_level': c.risk_level.value,
                    'risk_analysis': '基于规则分析',
                    'suggestion': c.suggestion
                }
                for c in result.clauses
            ],
            'risks': result.risks,
            'suggestions': result.suggestions,
            'legal_references': []
        }
        
        self.current_result = result_dict
        
        # 检索相关法律条文
        if self.use_law_kb and self.law_searcher:
            print("正在检索相关法律条文...")
            self._add_legal_references(result_dict)
        
        # 保存到数据库
        self._save_to_history('text_input', result_dict)
        
        return result_dict
    
    def _add_legal_references(self, result_dict: Dict):
        """添加相关法律条文参考"""
        legal_keywords = [
            "违约金", "违约责任", "保密", "知识产权", "不可抗力",
            "争议解决", "解除合同", "损害赔偿", "格式条款",
            "保密义务", "竞业限制", "服务期", "试用期", "社会保险"
        ]
        
        all_clauses_text = " ".join([c['content'] for c in result_dict['clauses']])
        legal_refs = {}
        
        for kw in legal_keywords:
            if kw.lower() in all_clauses_text.lower():
                results = self.law_searcher.search(kw, top_k=2)
                if results:
                    law_name = results[0]['file'].replace('.docx', '')
                    legal_refs[kw] = {
                        'law': law_name,
                        'snippet': results[0]['snippet']
                    }
        
        result_dict['legal_references'] = legal_refs
        if legal_refs:
            print(f"✓ 找到 {len(legal_refs)} 条相关法律条文")
    
    def _save_to_history(self, file_name: str, result: Dict):
        """保存审查记录到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO review_history 
            (contract_name, contract_type, parties, review_date, risk_count, clause_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            file_name,
            result['contract_type'],
            json.dumps(result['parties'], ensure_ascii=False),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            len(result['risks']),
            len(result['clauses']),
            'completed'
        ))
        
        conn.commit()
        conn.close()
    
    def export_report(self, output_path: str, format: str = 'docx') -> str:
        """
        导出审查报告
        
        Args:
            output_path: 输出文件路径
            format: 输出格式 ('docx', 'pdf', 'html', 'md')
        
        Returns:
            生成的文件路径
        """
        if not self.current_result:
            print("✗ 请先执行合同审查")
            return None
        
        print(f"正在生成{format.upper()}格式报告...")
        
        try:
            file_path = self.output_generator.generate(
                self.current_result, 
                output_path, 
                format
            )
            print(f"✓ 报告已生成: {file_path}")
            return file_path
        except Exception as e:
            print(f"✗ 报告生成失败: {e}")
            return None
    
    def send_report_email(self, recipient: str, 
                         subject: Optional[str] = None,
                         body: Optional[str] = None,
                         attachment_path: Optional[str] = None):
        """发送审查报告邮件"""
        if not self.email_sender:
            print("✗ 邮件功能未配置，请先调用 setup_email()")
            return False
        
        if not self.current_result:
            print("✗ 请先执行合同审查")
            return False
        
        # 使用默认模板
        if not subject or not body:
            subject, body = create_email_template(
                self.current_result['contract_type'],
                self.current_result['parties']
            )
        
        print(f"正在发送邮件到 {recipient}...")
        
        return self.email_sender.send_review_report(
            recipient, subject, body, attachment_path
        )
    
    def compare_versions(self, old_file: str, new_file: str) -> str:
        """
        对比合同版本
        
        Args:
            old_file: 旧版本文件路径
            new_file: 新版本文件路径
        
        Returns:
            差异对比文本
        """
        print("\n正在对比合同版本...")
        
        # 解析文件
        old_text = self.file_parser.parse(old_file)
        new_text = self.file_parser.parse(new_file)
        
        # 执行对比
        diff_text = self.reviewer.compare_versions(old_text, new_text)
        
        print("✓ 版本对比完成")
        return diff_text
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """获取审查历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, contract_name, contract_type, review_date, risk_count, clause_count
            FROM review_history
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'contract_name': row[1],
                'contract_type': row[2],
                'review_date': row[3],
                'risk_count': row[4],
                'clause_count': row[5]
            })
        
        return history
    
    def print_summary(self):
        """打印审查摘要"""
        if not self.current_result:
            print("无审查结果")
            return
        
        print("\n" + "="*60)
        print(f"合同类型：{self.current_result['contract_type']}")
        print(f"当事人：{', '.join(self.current_result['parties'])}")
        print(f"审查条款数：{len(self.current_result['clauses'])}")
        print(f"发现风险：{len(self.current_result['risks'])} 项")
        
        # 统计风险等级
        high_risks = sum(1 for c in self.current_result['clauses'] if '高' in c['risk_level'])
        medium_risks = sum(1 for c in self.current_result['clauses'] if '中' in c['risk_level'])
        
        print(f"  - 高风险：{high_risks} 项")
        print(f"  - 中风险：{medium_risks} 项")
        print("="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='合同审查辅助系统')
    parser.add_argument('-f', '--file', help='合同文件路径')
    parser.add_argument('-t', '--text', help='合同文本内容')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-fmt', '--format', default='docx', 
                       choices=['docx', 'pdf', 'html', 'md'],
                       help='输出格式')
    parser.add_argument('--llm', action='store_true', help='使用LLM增强审查')
    parser.add_argument('--api-key', help='LLM API密钥')
    parser.add_argument('--email', help='发送邮件到指定地址')
    
    args = parser.parse_args()
    
    # 创建系统实例
    system = ContractReviewSystem(use_llm=args.llm, api_key=args.api_key)
    
    # 审查合同
    if args.file:
        result = system.review_file(args.file)
    elif args.text:
        result = system.review_text(args.text)
    else:
        # 使用示例合同
        sample_contract = """
        甲方：深圳某某科技有限公司
        乙方：北京某某技术服务公司
        
        第一条 项目内容
        乙方为甲方开发一套管理软件系统。
        
        第二条 合同价款
        合同总价款为人民币100万元，分三期支付。
        
        第三条 履行期限
        乙方应在合同签订后6个月内完成系统开发。
        
        第四条 违约责任
        任何一方违约，需向守约方支付合同总价30%的违约金。
        
        第五条 争议解决
        双方因本合同发生争议，应友好协商解决；协商不成的，提交甲方所在地人民法院诉讼解决。
        """
        result = system.review_text(sample_contract)
    
    if result:
        system.print_summary()
        
        # 导出报告
        output_file = args.output or f'审查报告.{args.format}'
        system.export_report(output_file, args.format)
        
        # 发送邮件
        if args.email:
            system.send_report_email(args.email, attachment_path=output_file)
        
        print(f"\n✓ 审查完成！")
        print(f"报告已保存至: {output_file}")
    
    # 显示历史记录
    print("\n最近审查记录:")
    history = system.get_history(5)
    for h in history:
        print(f"  [{h['review_date']}] {h['contract_type']} - {h['contract_name']}")


if __name__ == '__main__':
    main()
