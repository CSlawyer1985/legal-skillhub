#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同审查辅助系统 - 主程序入口
集成条款提取、风险识别、差异比对、意见生成功能
支持Word文档生成和邮件发送
"""

import sys
import os
from typing import Optional, List
import json

# 导入核心模块
from scripts.contract_review import ContractReviewer, ReviewResult
from scripts.word_generator import WordGenerator
from scripts.email_sender import EmailSender, create_email_template


class ContractReviewApp:
    """合同审查应用主类"""
    
    def __init__(self):
        self.reviewer = ContractReviewer()
        self.word_gen = WordGenerator()
        self.email_sender = None
        self.current_result = None
    
    def setup_email(self, smtp_server: str, smtp_port: int, 
                   username: str, password: str):
        """配置邮件发送功能"""
        self.email_sender = EmailSender(
            smtp_server, smtp_port, username, password
        )
    
    def review_contract(self, contract_text: str) -> dict:
        """
        审查合同
        
        Args:
            contract_text: 合同文本内容
        
        Returns:
            审查结果字典
        """
        print("正在审查合同...")
        
        # 执行审查
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
                    'risk_analysis': self._get_risk_analysis(c),
                    'suggestion': c.suggestion
                }
                for c in result.clauses
            ],
            'risks': result.risks,
            'suggestions': result.suggestions
        }
        
        self.current_result = result_dict
        print("✓ 合同审查完成")
        
        return result_dict
    
    def _get_risk_analysis(self, clause) -> str:
        """获取风险分析（简化版）"""
        if clause.risk_level.value == '高风险':
            return '该条款可能存在法律风险，建议重点审核'
        elif clause.risk_level.value == '中风险':
            return '该条款表述不够明确，建议进一步澄清'
        else:
            return '该条款基本合规'
    
    def generate_word_report(self, output_path: str) -> str:
        """
        生成Word审查报告
        
        Args:
            output_path: 输出文件路径
        
        Returns:
            生成的文件路径
        """
        if not self.current_result:
            raise ValueError("请先执行合同审查")
        
        print("正在生成Word报告...")
        
        # 创建新的Word生成器
        self.word_gen = WordGenerator()
        
        # 生成报告
        file_path = self.word_gen.generate_review_report(
            self.current_result, output_path
        )
        
        print(f"✓ Word报告已生成：{file_path}")
        return file_path
    
    def compare_contract_versions(self, old_text: str, new_text: str) -> str:
        """
        对比合同版本差异
        
        Args:
            old_text: 旧版本合同文本
            new_text: 新版本合同文本
        
        Returns:
            差异对比文本
        """
        print("正在对比合同版本...")
        
        diff_text = self.reviewer.compare_versions(old_text, new_text)
        
        # 保存差异到Word文档
        if self.word_gen:
            self.word_gen.add_diff_comparison(diff_text)
        
        print("✓ 版本对比完成")
        return diff_text
    
    def send_email(self, 
                  recipient: str,
                  subject: Optional[str] = None,
                  body: Optional[str] = None,
                  attachment_path: Optional[str] = None,
                  cc_list: Optional[List[str]] = None) -> bool:
        """
        发送审查报告邮件
        
        Args:
            recipient: 收件人邮箱
            subject: 邮件主题（可选）
            body: 邮件正文（可选）
            attachment_path: 附件路径
            cc_list: 抄送列表
        
        Returns:
            是否发送成功
        """
        if not self.email_sender:
            print("✗ 邮件功能未配置，请先调用 setup_email()")
            return False
        
        if not self.current_result:
            print("✗ 请先执行合同审查")
            return False
        
        # 使用默认模板 if subject or body not provided
        if not subject or not body:
            subject, body = create_email_template(
                self.current_result['contract_type'],
                self.current_result['parties']
            )
        
        print(f"正在发送邮件给 {recipient}...")
        
        success = self.email_sender.send_review_report(
            recipient, subject, body, attachment_path, cc_list
        )
        
        if success:
            print("✓ 邮件发送成功")
        else:
            print("✗ 邮件发送失败")
        
        return success
    
    def print_review_summary(self):
        """打印审查结果摘要"""
        if not self.current_result:
            print("无审查结果")
            return
        
        print("\n" + "="*60)
        print(f"合同类型：{self.current_result['contract_type']}")
        print(f"当事人：{', '.join(self.current_result['parties'])}")
        print(f"审查条款数：{len(self.current_result['clauses'])}")
        print(f"发现风险：{len(self.current_result['risks'])} 项")
        print("="*60 + "\n")


def main():
    """主函数 - 命令行交互界面"""
    print("="*60)
    print("合同审查辅助系统 v1.0")
    print("支持：条款提取 | 风险识别 | 差异比对 | 意见生成")
    print("输出：Word文档 | 邮件发送")
    print("="*60 + "\n")
    
    app = ContractReviewApp()
    
    # 示例：审查一份合同
    if len(sys.argv) > 1:
        # 从文件读取合同
        contract_file = sys.argv[1]
        if os.path.exists(contract_file):
            with open(contract_file, 'r', encoding='utf-8') as f:
                contract_text = f.read()
            
            # 执行审查
            result = app.review_contract(contract_text)
            app.print_review_summary()
            
            # 生成Word报告
            output_file = '审查报告.docx'
            app.generate_word_report(output_file)
            
            print(f"\n✓ 审查完成，报告已保存至：{output_file}")
        else:
            print(f"✗ 文件不存在：{contract_file}")
    else:
        print("用法：python main.py [合同文件路径]")
        print("\n示例合同文本：")
        
        # 示例合同
        sample_contract = """
        甲方：深圳某某科技有限公司
        乙方：北京某某技术服务公司
        
        第一条 标的物
        乙方为甲方开发一套管理软件系统。
        
        第二条 价款与支付
        合同总价款为人民币100万元，分三期支付。
        
        第三条 履行期限
        乙方应在合同签订后6个月内完成系统开发。
        
        第四条 违约责任
        任何一方违约，需向守约方支付合同总价30%的违约金。
        
        第五条 争议解决
        双方因本合同发生争议，应友好协商解决；协商不成的，提交甲方所在地人民法院诉讼解决。
        """
        
        # 执行审查
        result = app.review_contract(sample_contract)
        app.print_review_summary()
        
        # 生成Word报告
        output_file = '示例审查报告.docx'
        app.generate_word_report(output_file)
        
        print(f"\n✓ 示例审查完成，报告已保存至：{output_file}")


if __name__ == '__main__':
    main()
