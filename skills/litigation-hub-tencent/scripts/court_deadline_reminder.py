#!/usr/bin/env python3
"""
法院期限提醒统一调度脚本
读取 deadline-rules.json 规则库，根据文书类型自动匹配期限规则，
生成日历事件 + 本机电脑提醒（系统通知 + 桌面 Markdown 文件）+ QQ 邮件（微信送达）（三条线）。

用法:
  python3 court_deadline_reminder.py setup <案号> <案由> <文书类型> <关键字标签...> <送达日期> <法院>
  python3 court_deadline_reminder.py setup --json '<parsed_document_json>'
  python3 court_deadline_reminder.py notify <uid_hash> <rule_id> <before_days>
  python3 court_deadline_reminder.py cleanup <uid_hash>

设计原则（第一性原理）：
  - 保全类（冻结/查封）必须提前30天提醒，不可以等到最后几天
  - 上诉类期限短（5-15天），提醒密集（2天前 + 当天）
  - 缴费/答辩等中等期限，适度提醒
  - 所有提醒一律三条线：日历 + 本机电脑提醒（系统通知 + 桌面 Markdown 文件）+ QQ 邮件（微信送达）
"""

import sys
import os
import json
import hashlib
import subprocess
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

# ============================================================
#  平台检测
# ============================================================
if sys.platform == 'darwin':
    PLATFORM = 'macos'
elif sys.platform == 'win32':
    PLATFORM = 'windows'
else:
    PLATFORM = 'linux'

# 常量
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_FILE = os.path.join(os.path.dirname(SKILL_DIR), 'references', 'deadline-rules.json')
SMTP_SKILL_DIR = os.path.expanduser("~/.workbuddy/skills/imap-smtp-email")
SMTP_SCRIPT = os.path.join(SMTP_SKILL_DIR, "scripts", "smtp.js")
EMAIL_DATA_DIR = os.path.expanduser("~/.court-email")
NODE_BIN = shutil.which("node") or "/usr/local/bin/node"
TO_EMAIL = os.environ.get("COURT_SMS_EMAIL", "YOUR_QQ_EMAIL@qq.com")


def _uid(case_no):
    return hashlib.md5(case_no.encode()).hexdigest()[:8]


def _escape_ps(s):
    return s.replace('"', '""').replace('\n', ' ')


def _weekday(dt):
    return ['周一','周二','周三','周四','周五','周六','周日'][dt.weekday()]


# ============================================================
#  规则匹配
# ============================================================

def load_rules():
    with open(RULES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def match_rule(document_type, tags, doc_title=""):
    """
    根据文书类型和关键字标签匹配期限规则。
    返回匹配到的 rule dict，或 None。
    """
    rules_data = load_rules()
    for rule in rules_data['rules']:
        match = rule.get('match', {})
        r_type = match.get('document_type', '')
        r_tags = match.get('tags', [])

        # document_type 必须匹配
        if document_type != r_type:
            continue

        # tags：任一关键词在 tags 列表或文书标题中出现即匹配
        if not r_tags:
            return rule  # 无 tags 限制，直接匹配

        all_text = ' '.join(tags) + ' ' + doc_title
        for tag in r_tags:
            if tag in all_text:
                return rule

    return None


# ============================================================
#  系统通知
# ============================================================

def send_system_notification(title, message):
    if PLATFORM == 'macos':
        t = title.replace('"', '\\"')
        m = message.replace('"', '\\"')
        script = f'display notification "{m}" with title "{t}"'
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.scpt', delete=False, encoding='utf-8')
        f.write(script); f.close()
        subprocess.run(['osascript', f.name], capture_output=True)
        os.remove(f.name)
    elif PLATFORM == 'windows':
        t = _escape_ps(title); m = _escape_ps(message)
        ps = f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show("{m}","{t}")'
        subprocess.run(['powershell','-NoProfile','-Command',ps], capture_output=True)


# ============================================================
#  QQ 邮件
# ============================================================

def send_qq_email(subject, body):
    if not os.path.exists(SMTP_SCRIPT):
        print(f"❌ smtp.js 未找到"); return False
    env = os.environ.copy()
    for k in ['HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy','no_proxy']:
        env.pop(k, None)
    env['NO_PROXY'] = '*'
    cmd = [NODE_BIN, SMTP_SCRIPT, 'send', '--to', TO_EMAIL,
           '--subject', subject, '--body', body, '--priority', 'high']
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=SMTP_SKILL_DIR, env=env, timeout=30)
    if r.returncode != 0:
        print(f"❌ 邮件发送失败: {r.stderr}"); return False
    print(f"✅ QQ 邮件已发送 → {TO_EMAIL}")
    return True


# ============================================================
#  日历事件 / .ics 文件
# ============================================================

def _generate_ics(summary, description, deadline_dt, uid_hash, prefix="deadline"):
    deadline_str = deadline_dt.strftime('%Y%m%d')
    now_utc = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    def _c(s): return s.replace('\\','\\\\').replace(';','\\;').replace(',','\\,').replace('\n','\\n')
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//court-sms//CN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
DTSTART;VALUE=DATE:{deadline_str}
DTEND;VALUE=DATE:{(deadline_dt+timedelta(days=1)).strftime('%Y%m%d')}
DTSTAMP:{now_utc}
SUMMARY:{_c(summary)}
DESCRIPTION:{_c(description)}
BEGIN:VALARM
TRIGGER:-P1D
ACTION:DISPLAY
DESCRIPTION:{_c(summary)}
END:VALARM
END:VEVENT
END:VCALENDAR"""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    path = os.path.join(desktop, f"{prefix}_{uid_hash}.ics")
    with open(path, 'w', encoding='utf-8') as f: f.write(ics)
    print(f"  📅 .ics 文件 → {path}")
    return path


def _macos_create_calendar(summary, description, deadline_dt, location=""):
    ds = deadline_dt.strftime("%Y年%m月%d日")
    s = summary.replace('"', '\\"')
    desc = description.replace('\n','\\n').replace('"','\\"')
    loc = (location or '').replace('"', '\\"')
    script = (
        f'tell application "Calendar"\n'
        f'  tell calendar "工作"\n'
        f'    make new event at end with properties {{'
        f'summary:"{s}", start date:date "{ds} 00:00:00", '
        f'end date:date "{ds} 23:59:59", description:"{desc}", '
        f'location:"{loc}", allday event:true}}\n'
        f'  end tell\nend tell')
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.scpt', delete=False, encoding='utf-8')
    f.write(script); f.close()
    r = subprocess.run(['osascript', f.name], capture_output=True, text=True)
    os.remove(f.name)
    if r.returncode == 0:
        print(f"  📅 Apple Calendar: {summary}")
        return True
    print(f"  ⚠️ Calendar 失败: {r.stderr}")
    return False


def create_calendar_event(summary, description, deadline_dt, uid_hash, location=""):
    if PLATFORM == 'macos':
        ok = _macos_create_calendar(summary, description, deadline_dt, location)
        if not ok:
            _generate_ics(summary, description, deadline_dt, uid_hash)
    else:
        _generate_ics(summary, description, deadline_dt, uid_hash)


# ============================================================
#  定时任务调度
# ============================================================

def _macos_schedule(label, alarm_date, python_exe, args):
    plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{label}.plist")
    esc_args = ' '.join(f'<string>{xml_escape(a)}</string>' for a in args)
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
    <key>Label</key><string>{xml_escape(label)}</string>
    <key>ProgramArguments</key>
    <array><string>{xml_escape(python_exe)}</string>{esc_args}</array>
    <key>StartCalendarInterval</key>
    <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer>
    <key>Month</key><integer>{alarm_date.month}</integer><key>Day</key><integer>{alarm_date.day}</integer></dict>
    <key>StandardOutPath</key><string>{xml_escape(EMAIL_DATA_DIR)}/{xml_escape(label)}.log</string>
    <key>StandardErrorPath</key><string>{xml_escape(EMAIL_DATA_DIR)}/{xml_escape(label)}-err.log</string>
</dict></plist>'''
    os.makedirs(os.path.dirname(plist_path), exist_ok=True)
    with open(plist_path, 'w') as f: f.write(content)
    r = subprocess.run(['launchctl','load', plist_path], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ⚠️ launchd 失败: {r.stderr}"); return False
    print(f"  ✅ launchd: {label} → {alarm_date.strftime('%Y-%m-%d')} 09:00")
    return True


def _windows_schedule(label, alarm_date, python_exe, args):
    tr = f'"{python_exe}" {" ".join(f"{a}" for a in args)}'
    cmd = ['schtasks','/Create','/SC','ONCE','/TN',label,'/TR',tr,
           '/ST','09:00','/SD',alarm_date.strftime('%Y-%m-%d'),'/F']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        print(f"  ⚠️ schtasks 失败: {r.stderr}"); return False
    print(f"  ✅ schtasks: {label} → {alarm_date.strftime('%Y-%m-%d')} 09:00")
    return True


def schedule_task(label, alarm_date, args):
    """args: 传给本脚本 notify 模式的参数列表"""
    py_args = [SKILL_DIR + '/court_deadline_reminder.py', 'notify'] + args
    if PLATFORM == 'macos':
        return _macos_schedule(label, alarm_date, sys.executable, py_args)
    elif PLATFORM == 'windows':
        return _windows_schedule(label, alarm_date, sys.executable, py_args)
    else:
        print(f"  ⚠️ {PLATFORM} 暂不支持系统定时")
        return False


# ============================================================
#  主流程：根据规则设置提醒
# ============================================================

def setup_reminders(case_no, case_type, document_type, tags, received_date_str, court_name, doc_title="", dry_run=False):
    """
    根据规则库匹配期限，设置日历 + 本机电脑提醒（系统通知 + 桌面 Markdown 文件）+ QQ 邮件（微信送达）。
    dry_run=True 时仅输出提醒计划，不实际创建。

    参数:
      case_no: 案号
      case_type: 案由
      document_type: 文书类型（判决书/裁定书/传票/举证通知书/受理通知书 等）
      tags: 关键字标签列表，用于精确匹配（如['冻结','银行存款']）
      received_date_str: 送达日期 YYYY-MM-DD
      court_name: 法院名称
      doc_title: 文书原标题（辅助匹配）
    """
    uid_hash = _uid(case_no)
    received = datetime.strptime(received_date_str, "%Y-%m-%d")

    # 1. 匹配规则
    rule = match_rule(document_type, tags, doc_title)
    if not rule:
        print(f"⚠️ 未找到匹配的期限规则: type={document_type} tags={tags}")
        print("   文书已归档，但不设置自动提醒。请手动确认是否需要设置期限。")
        return False

    rule_id = rule['id']
    deadline_info = rule['deadline']
    reminders = rule['reminders']
    deadline_days = deadline_info['value']
    description = deadline_info['description']
    deadline_dt = received + timedelta(days=deadline_days)
    note = rule.get('note', '')

    # 法定节假日顺延（从 china-holidays.json 读取）
    try:
        from holiday_utils import adjust_deadline, holidays_in_range
        original_deadline = deadline_dt.strftime("%Y-%m-%d")
        adjusted = adjust_deadline(original_deadline)
        if adjusted != original_deadline:
            deadline_dt = datetime.strptime(adjusted, "%Y-%m-%d")
        # 检查期限内是否包含长假，提示用户
        hols = holidays_in_range(received.strftime("%Y-%m-%d"), adjusted)
        if hols:
            print(f"  📅 期限内含法定节假日: {', '.join(hols)}（可能影响实际可用工作日）")
    except (ImportError, FileNotFoundError, Exception):
        pass  # holiday_utils 不可用或文件缺失时不阻塞提醒

    os.makedirs(EMAIL_DATA_DIR, exist_ok=True)

    print(f"📋 期限规则匹配: {rule_id}")
    print(f"   动作: {description}")
    print(f"   期限: {deadline_days}{deadline_info['unit']}（截止 {deadline_dt.strftime('%Y-%m-%d')}）")
    if note:
        print(f"   💡 {note}")

    # 2. 创建日历事件（dry_run 时跳过）
    cal_title_tmpl = rule.get('calendar', {}).get('title', '⏰ 期限截止')
    cal_title = cal_title_tmpl.replace('{case_type}', case_type).replace('{case_no}', case_no)
    cal_desc = f"案号：{case_no}\n案由：{case_type}\n法院：{court_name}\n\n{description}\n截止：{deadline_dt.strftime('%Y年%m月%d日')}"
    if dry_run:
        print(f"  📅 🟡 日历事件: {cal_title}")
    else:
        create_calendar_event(cal_title, cal_desc, deadline_dt, uid_hash)

    # 3. 为每个 reminder 创建定时任务（系统通知 + QQ 邮件）+ 写入邮件数据
    weekdays = ['周一','周二','周三','周四','周五','周六','周日']
    for rem in reminders:
        before_days = rem['before_days']
        level = rem['level']
        label_tmpl = rem['label']
        label = label_tmpl.replace('{case_type}', case_type)

        alarm_date = deadline_dt - timedelta(days=before_days)

        # 邮件数据
        subject = f"{'🚨' if level=='critical' else '⏰'} {label}"
        body = f"""您好，

以下案件的期限即将到来：

━━━━━━━━━━━━━━━━━━
{label}
━━━━━━━━━━━━━━━━━━

案号：{case_no}
案由：{case_type}
法院：{court_name}
动作：{description}
期限截止：{deadline_dt.strftime('%Y年%m月%d日')}（{weekdays[deadline_dt.weekday()]}）
剩余天数：{before_days} 天

{note}

━━━━━━━━━━━━━━━━━━
此邮件由 court-sms 自动发送。
"""

        data = {
            "uid_hash": uid_hash, "rule_id": rule_id, "before_days": before_days,
            "subject": subject, "body": body,
            "case_no": case_no, "case_type": case_type, "label": label,
            "deadline": deadline_dt.strftime('%Y-%m-%d'),
        }
        data_file = os.path.join(EMAIL_DATA_DIR, f"{uid_hash}-{before_days}d.json")

        # 定时任务（dry_run 时跳过，不写文件）
        if not dry_run:
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            task_label = f"mm-{rule_id}-{before_days}d-{uid_hash}" if PLATFORM == 'windows' else f"com.mm.{rule_id}-{before_days}d-{uid_hash}"
            schedule_task(task_label, alarm_date, [uid_hash, str(before_days)])

    print()
    if dry_run:
        print(f"🟡 提醒计划（尚未创建，等待确认）:")
    else:
        print(f"✅ 全部提醒已设置")
    print(f"   📅 日历事件: {cal_title}")
    print(f"   🔔 系统通知: {len(reminders)} 次提醒")
    print(f"   📧 QQ 邮件（微信送达）: {len(reminders)} 封 → {TO_EMAIL}")
    for rem in reminders:
        alarm = deadline_dt - timedelta(days=rem['before_days'])
        print(f"      · {alarm.strftime('%Y-%m-%d')} 09:00 — {rem['label'].replace('{case_type}', case_type)}")

    return True


def send_notification(uid_hash, before_days):
    """由 launchd/schtasks 调用，发送通知+邮件"""
    data_file = os.path.join(EMAIL_DATA_DIR, f"{uid_hash}-{before_days}d.json")
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}"); return False

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    send_system_notification(data['label'], f"案号：{data['case_no']}\n案由：{data['case_type']}")
    print(f"✅ 系统通知: {data['label']}")
    # 本机电脑提醒：桌面 Markdown 文件（持久化，不依赖通知是否弹出）
    try:
        from court_utils import generate_desktop_md_reminder
        md_lines = [
            f"**案件：{data['case_no']}**",
            f"**案由：{data['case_type']}**",
            f"**事项：{data['label']}**",
            f"**期限截止：{data.get('deadline', '（见日历事件）')}**",
        ]
        md_path = generate_desktop_md_reminder(
            "⏰ 期限提醒",
            md_lines,
            filename_hint=f"期限提醒_{uid_hash}_{before_days}d",
        )
        print(f"  📄 桌面提醒文件已生成：{md_path}")
    except Exception as e:
        print(f"  ⚠️ 桌面提醒文件生成失败（不影响通知/邮件）: {e}")
    send_qq_email(data['subject'], data['body'])
    return True


def cleanup(uid_hash):
    """清理所有相关提醒"""
    rules_data = load_rules()
    # 收集所有可能的 rule_id + before_days 组合
    candidates = set()
    for rule in rules_data['rules']:
        for rem in rule['reminders']:
            candidates.add((rule['id'], rem['before_days']))

    for rule_id, before_days in candidates:
        if PLATFORM == 'macos':
            label = f"com.mm.{rule_id}-{before_days}d-{uid_hash}"
            plist = os.path.expanduser(f"~/Library/LaunchAgents/{label}.plist")
            if os.path.exists(plist):
                subprocess.run(['launchctl','unload',plist], capture_output=True)
                os.remove(plist); print(f"  🗑️ {label}")
        elif PLATFORM == 'windows':
            label = f"mm-{rule_id}-{before_days}d-{uid_hash}"
            subprocess.run(['schtasks','/Delete','/TN',label,'/F'], capture_output=True, timeout=10)
            print(f"  🗑️ {label}")

        # 清理日志
        for sfx in ['.log','-err.log']:
            lp = os.path.join(EMAIL_DATA_DIR, f"{'mm-' if PLATFORM=='windows' else 'com.mm.'}{rule_id}-{before_days}d-{uid_hash}{sfx}")
            if os.path.exists(lp): os.remove(lp)

    # 清理邮件数据文件
    for f in Path(EMAIL_DATA_DIR).glob(f"{uid_hash}-*d.json"):
        os.remove(str(f)); print(f"  🗑️ {f.name}")


# ============================================================
#  CLI
# ============================================================

def main():
    if len(sys.argv) < 2:
        print(f"平台: {PLATFORM}")
        print("用法:")
        print("  # 命令行参数")
        print(f"  python3 {os.path.basename(__file__)} setup <案号> <案由> <文书类型> <标签...> <送达日期> <法院>")
        print("  例: ... setup '(2025)苏0411刑初1号' '诈骗罪' '裁定书' '冻结,银行存款' '2026-07-07' 'xx法院'")
        print()
        print("  # JSON 模式（推荐）")
        print(f"  python3 {os.path.basename(__file__)} setup --json '{{...}}'")
        print()
        print("  # dry-run 模式（仅查看计划，不创建）")
        print(f"  python3 {os.path.basename(__file__)} setup --dry-run ...")
        print()
        print(f"  python3 {os.path.basename(__file__)} notify <uid_hash> <before_days>")
        print(f"  python3 {os.path.basename(__file__)} cleanup <uid_hash>")
        sys.exit(1)

    cmd = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    if cmd == 'setup':
        if '--json' in sys.argv:
            idx = sys.argv.index('--json')
            data = json.loads(sys.argv[idx+1])
            setup_reminders(
                data.get('case_no',''), data.get('case_type',''),
                data.get('document_type',''), data.get('tags',[]),
                data.get('received_date',''), data.get('court_name',''),
                data.get('doc_title',''), dry_run=dry_run)
        elif len(sys.argv) >= 7:
            case_no, case_type, doc_type = sys.argv[2], sys.argv[3], sys.argv[4]
            tags = [t.strip() for t in sys.argv[5].split(',') if t.strip()]
            received = sys.argv[6]
            court = sys.argv[7] if len(sys.argv) > 7 else ''
            setup_reminders(case_no, case_type, doc_type, tags, received, court, dry_run=dry_run)
        else:
            print("❌ 参数不足"); sys.exit(1)

    elif cmd == 'notify' and len(sys.argv) >= 4:
        send_notification(sys.argv[2], int(sys.argv[3]))

    elif cmd == 'cleanup' and len(sys.argv) >= 3:
        cleanup(sys.argv[2])

    else:
        print("❌ 参数错误"); sys.exit(1)


if __name__ == "__main__":
    main()
