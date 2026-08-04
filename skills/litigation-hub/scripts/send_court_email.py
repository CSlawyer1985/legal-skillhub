#!/usr/bin/env python3
"""
法院开庭 QQ 邮件提醒发送脚本。
由 launchd 在开庭前1天触发调用，通过 imap-smtp-email skill 的 smtp.js 发送 QQ 邮件。

用法:
  python3 send_court_email.py <uid_hash>
  # <uid_hash> 由 court_calendar.py 创建时生成，用于查找对应的邮件 JSON 数据文件

数据文件位置: ~/.court-email/<uid_hash>.json
"""

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path

# imap-smtp-email skill 路径
SMTP_SKILL_DIR = os.path.expanduser("~/.workbuddy/skills/imap-smtp-email")
SMTP_SCRIPT = os.path.join(SMTP_SKILL_DIR, "scripts", "smtp.js")
EMAIL_DATA_DIR = os.path.expanduser("~/.court-email")

# 收件人通过环境变量配置，回退占位符
TO_EMAIL = os.environ.get("COURT_SMS_EMAIL", "YOUR_QQ_EMAIL@qq.com")
NODE_BIN = shutil.which("node") or "/usr/local/bin/node"


def load_email_data(uid_hash):
    """读取邮件数据 JSON"""
    data_file = os.path.join(EMAIL_DATA_DIR, f"{uid_hash}.json")
    if not os.path.exists(data_file):
        print(f"❌ 邮件数据文件不存在: {data_file}")
        return None
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def send_email(data):
    """
    通过 imap-smtp-email 的 smtp.js 发送 QQ 邮件。
    需要清理系统代理环境变量（如用户已配置代理会影响本地请求）。
    """
    if not os.path.exists(SMTP_SCRIPT):
        print(f"❌ smtp.js 未找到: {SMTP_SCRIPT}")
        return False

    subject = data.get('subject', '开庭提醒')
    body = data.get('body', '')

    # 清理系统代理环境变量，避免影响本地 SMTP 连接
    env = os.environ.copy()
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'no_proxy']:
        env.pop(key, None)
    env['NO_PROXY'] = '*'

    cmd = [
        NODE_BIN,
        SMTP_SCRIPT,
        'send',
        '--to', TO_EMAIL,
        '--subject', subject,
        '--body', body,
        '--priority', 'high',
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=SMTP_SKILL_DIR, env=env, timeout=30)

    if result.returncode != 0:
        print(f"❌ 邮件发送失败: {result.stderr}")
        return False

    print(f"✅ QQ 邮件已发送 → {TO_EMAIL}")
    print(f"   主题: {subject}")
    return True


def delete_email_data(uid_hash):
    """清理邮件数据文件（用于重建前清理）"""
    data_file = os.path.join(EMAIL_DATA_DIR, f"{uid_hash}.json")
    if os.path.exists(data_file):
        os.remove(data_file)
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print("用法: python3 send_court_email.py <uid_hash>")
        print("示例: python3 send_court_email.py a1b2c3d4")
        sys.exit(1)

    uid_hash = sys.argv[1]

    # cleanup 模式：删除邮件数据文件
    if uid_hash == '--cleanup' and len(sys.argv) >= 3:
        deleted = delete_email_data(sys.argv[2])
        print(f"{'✅ 已清理' if deleted else '❌ 未找到数据'} {sys.argv[2]}")
        return

    # 读取数据
    data = load_email_data(uid_hash)
    if not data:
        sys.exit(1)

    # 发送邮件
    success = send_email(data)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
