# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
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
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SKILL_DIR, "..", "config", "user-preferences.json")
def _find_node():
    """定位 node 可执行文件。

    launchd 定时任务的环境 PATH 极简，shutil.which('node') 往往返回 None，
    且 /usr/local/bin/node 在 Apple Silicon 上通常不存在（homebrew 装在
    /opt/homebrew）。故依次探测常见绝对路径，命中即用。"""
    candidates = [
        "/opt/homebrew/bin/node",
        "/usr/local/bin/node",
        "/usr/bin/node",
    ]
    # 用户级版本管理器
    for pattern in [
        os.path.expanduser("~/.nvm/versions/node/*/bin/node"),
        os.path.expanduser("~/.volta/bin/node"),
        os.path.expanduser("~/.workbuddy/binaries/node/versions/*/bin/node"),
    ]:
        import glob
        for p in sorted(glob.glob(pattern), reverse=True):
            candidates.append(p)
    found = shutil.which("node")
    if found:
        return found
    for c in candidates:
        if os.path.exists(c):
            return c
    return "/usr/local/bin/node"  # 最终兜底（可能不存在，但保留报错信息）


NODE_BIN = _find_node()


def _resolve_email():
    """解析 QQ 收件人邮箱。

    优先级：配置文件 config/user-preferences.json 的 court_email
            > 环境变量 COURT_SMS_EMAIL
            > 占位符（最终兜底，不应被真正发送）
    launchd 定时任务不继承 shell 环境变量，故必须将邮箱写入配置文件，
    否则定时触发的 QQ 邮件会静默发往占位符地址而失败。
    """
    # 1. 配置文件（launchd 可直接读取）
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        email = cfg.get('court_email', '').strip()
        if email and 'YOUR_QQ_EMAIL' not in email:
            return email
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    # 2. 环境变量
    env_email = os.environ.get("COURT_SMS_EMAIL", "").strip()
    if env_email and 'YOUR_QQ_EMAIL' not in env_email:
        return env_email
    # 3. 占位符兜底
    return "YOUR_QQ_EMAIL@qq.com"


TO_EMAIL = _resolve_email()


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
