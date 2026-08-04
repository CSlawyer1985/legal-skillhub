#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件发送模块
支持SMTP发送审查报告
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
import os


class EmailSender:
    """邮件发送器"""
    
    def __init__(self, smtp_server: str = 'smtp.qq.com', 
                 smtp_port: int = 587,
                 username: str = '',
                 password: str = ''):
        """
        初始化邮件发送器
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            username: 发件人邮箱
            password: 邮箱密码或授权码
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_review_report(self, 
                          recipient: str,
                          subject: str,
                          body: str,
                          attachment_path: Optional[str] = None,
                          cc_list: Optional[List[str]] = None) -> bool:
        """
        发送审查报告
        
        Args:
            recipient: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文
            attachment_path: 附件路径（审查报告Word文档）
            cc_list: 抄送列表
        
        Returns:
            是否发送成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = recipient
            msg['Subject'] = subject
            
            if cc_list:
                msg['Cc'] = ', '.join(cc_list)
            
            # 添加邮件正文
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 添加附件
            if attachment_path and os.path.exists(attachment_path):
                self._attach_file(msg, attachment_path)
            
            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # 启用TLS加密
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                # 收件人列表
                recipients = [recipient]
                if cc_list:
                    recipients.extend(cc_list)
                
                server.sendmail(self.username, recipients, msg.as_string())
            
            print(f"邮件发送成功：{recipient}")
            return True
            
        except Exception as e:
            print(f"邮件发送失败：{str(e)}")
            return False
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """添加附件"""
        filename = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)
    
    def send_bulk_reports(self, 
                          recipients: List[str],
                          subject: str,
                          body: str,
                          attachment_path: Optional[str] = None) -> dict:
        """
        批量发送审查报告
        
        Args:
            recipients: 收件人列表
            subject: 邮件主题
            body: 邮件正文
            attachment_path: 附件路径
        
        Returns:
            发送结果统计
        """
        results = {
            'success': 0,
            'failed': 0,
            'failed_recipients': []
        }
        
        for recipient in recipients:
            if self.send_review_report(recipient, subject, body, attachment_path):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['failed_recipients'].append(recipient)
        
        return results


def create_email_template(contract_type: str, parties: List[str]) -> tuple:
    """
    创建邮件模板
    
    Args:
        contract_type: 合同类型
        parties: 当事人列表
    
    Returns:
        (主题, 正文) 元组
    """
    subject = f"【合同审查报告】{contract_type}"
    
    body = f"""
尊敬的审查人员：

您好！

附件为{contract_type}的审查报告，请查收。

合同当事人：
"""
    
    for i, party in enumerate(parties, 1):
        body += f"{i}. {party}\n"
    
    body += """
审查要点：
1. 请重点关注高风险条款
2. 建议与对方协商修改不利条款
3. 确保合同条款符合公司利益

如有疑问，请随时联系。

此致
敬礼！

AI辅助审查系统
"""
    
    return subject, body


if __name__ == '__main__':
    # 测试代码
    sender = EmailSender(
        smtp_server='smtp.qq.com',
        smtp_port=587,
        username='test@qq.com',
        password='your_password'
    )
    
    # 创建测试邮件
    subject, body = create_email_template(
        contract_type='软件开发合同',
        parties=['甲方：深圳某某科技', '乙方：北京某某技术']
    )
    
    # 发送邮件（需要真实邮箱和密码）
    # sender.send_review_report(
    #     recipient='recipient@example.com',
    #     subject=subject,
    #     body=body,
    #     attachment_path='test_review_report.docx'
    # )
    
    print("邮件模块测试完成")
