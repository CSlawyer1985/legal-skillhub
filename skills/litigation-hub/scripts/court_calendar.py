#!/usr/bin/env python3
"""
法院开庭日历创建脚本（macOS / Windows 双平台）
融合自 court-notice skill 的日历写入逻辑，适配 court-sms 工作流。

用法:
  # CLI 模式
  python3 court_calendar.py <案号> <案由> <YYYY-MM-DD HH:MM> <地点> [日历名称] [PDF链接]

  # Python 模块模式
  from court_calendar import create_court_calendar, delete_court_events, parse_hearing_info_from_pdf

依赖: pypdf (pip install pypdf)

平台支持:
  - macOS: AppleScript + Apple Calendar + launchd
  - Windows: PowerShell + Outlook/Toast通知 + 任务计划程序
  - Linux: 仅邮件通知（无系统日历集成）
"""

import sys
import os
import re
import json
import hashlib
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape
from court_utils import generate_desktop_md_reminder

# ============================================================
#  平台检测
# ============================================================

def _get_platform():
    """返回平台标识: 'macos' | 'windows' | 'linux'"""
    s = sys.platform
    if s == 'darwin':
        return 'macos'
    elif s == 'win32':
        return 'windows'
    else:
        return 'linux'

PLATFORM = _get_platform()


# ============================================================
#  平台无关 — 公共工具
# ============================================================

def _escape_ps(s):
    """转义 PowerShell 字符串"""
    return s.replace('"', '""').replace('\n', ' ')

def _uid(case_no):
    return hashlib.md5(case_no.encode()).hexdigest()[:8]

def _fmt_date(dt):
    return dt.strftime("%Y年%m月%d日")

def _fmt_time(dt):
    return dt.strftime("%Y年%m月%d日 %H:%M")

def _weekday(dt):
    return ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][dt.weekday()]

def _desc(case_no, case_type, location):
    return f"案号：{case_no} - 案由：{case_type} - 开庭地点：{location}"


# ============================================================
#  macOS 实现
# ============================================================

def _macos_create_calendar_event(summary, start_str, end_str, desc,
                                  location, calendar_name, pdf_url):
    """AppleScript 无弹窗写入日历"""
    if pdf_url:
        script = (
            f'tell application "Calendar"\n'
            f'    tell calendar "{calendar_name}"\n'
            f'        make new event at end with properties {{'
            f'summary:"{summary}", '
            f'start date:date "{start_str}", '
            f'end date:date "{end_str}", '
            f'description:"{desc}", '
            f'location:"{location}", '
            f'url:"{pdf_url}"'
            f'}}\n    end tell\nend tell'
        )
    else:
        script = (
            f'tell application "Calendar"\n'
            f'    tell calendar "{calendar_name}"\n'
            f'        make new event at end with properties {{'
            f'summary:"{summary}", '
            f'start date:date "{start_str}", '
            f'end date:date "{end_str}", '
            f'description:"{desc}", '
            f'location:"{location}"'
            f'}}\n    end tell\nend tell'
        )

    f = tempfile.NamedTemporaryFile(mode='w', suffix='.scpt', delete=False, encoding='utf-8')
    f.write(script)
    f.close()
    result = subprocess.run(['osascript', f.name], capture_output=True, text=True)
    os.remove(f.name)
    if result.returncode != 0:
        print(f"  AppleScript error: {result.stderr}")
        return False
    return True


def _macos_delete_calendar_events(case_no, calendar_name):
    script = (
        f'tell application "Calendar"\n'
        f'    set calEvents to every event of calendar "{calendar_name}" '
        f'whose description contains "{case_no}"\n'
        f'    repeat with evt in calEvents\n        delete evt\n    end repeat\n'
        f'end tell'
    )
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.scpt', delete=False, encoding='utf-8')
    f.write(script)
    f.close()
    subprocess.run(['osascript', f.name], capture_output=True, text=True)
    os.remove(f.name)


def _macos_schedule_notification(uid_hash, label, case_no, case_type, hearing_time, location, alarm_dt, hour, minute):
    """launchd 定时任务：到提醒时间运行 court_calendar.py hearing-notify 子命令（弹通知 + 生产桌面 MD）"""
    plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{label}.plist")
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'court_calendar.py')
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{xml_escape(label)}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{xml_escape(sys.executable)}</string>
        <string>{xml_escape(script_path)}</string>
        <string>hearing-notify</string>
        <string>{xml_escape(case_no)}</string>
        <string>{xml_escape(case_type)}</string>
        <string>{xml_escape(hearing_time)}</string>
        <string>{xml_escape(location)}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>{hour}</integer>
        <key>Minute</key><integer>{minute}</integer>
        <key>Month</key><integer>{alarm_dt.month}</integer>
        <key>Day</key><integer>{alarm_dt.day}</integer>
    </dict>
</dict>
</plist>'''
    os.makedirs(os.path.dirname(plist_path), exist_ok=True)
    with open(plist_path, 'w') as f:
        f.write(content)
    subprocess.run(['launchctl', 'load', plist_path], capture_output=True)


def _macos_pop_notification(title, message, sound="Glass"):
    """立即弹出系统通知（不依赖定时任务，用于创建时即时反馈）

    苹果系统原生方式：osascript -e 'display notification "..." with title "..."'
    """
    t = title.replace('"', '\\"')
    m = message.replace('"', '\\"')
    script = f'display notification "{m}" with title "{t}" sound name "{sound}"'
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️ 系统通知弹出失败: {result.stderr}")
        return False
    return True


def _macos_schedule_email_script(uid_hash, label, alarm_dt, python_exe, script_dir, email_dir, hour, minute):
    plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{label}.plist")
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{xml_escape(label)}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{xml_escape(python_exe)}</string>
        <string>{xml_escape(script_dir)}/send_court_email.py</string>
        <string>{xml_escape(uid_hash)}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>{hour}</integer>
        <key>Minute</key><integer>{minute}</integer>
        <key>Month</key><integer>{alarm_dt.month}</integer>
        <key>Day</key><integer>{alarm_dt.day}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{xml_escape(email_dir)}/{xml_escape(uid_hash)}-email.log</string>
    <key>StandardErrorPath</key>
    <string>{xml_escape(email_dir)}/{xml_escape(uid_hash)}-email-err.log</string>
</dict>
</plist>'''
    os.makedirs(os.path.dirname(plist_path), exist_ok=True)
    with open(plist_path, 'w') as f:
        f.write(content)
    result = subprocess.run(['launchctl', 'load', plist_path], capture_output=True, text=True)
    return result.returncode == 0


def _macos_unload_reminder(uid_hash, modes=('', '-email')):
    for suffix in modes:
        label = f"com.mm.court{suffix}-{uid_hash}"
        plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{label}.plist")
        if os.path.exists(plist_path):
            subprocess.run(['launchctl', 'unload', plist_path], capture_output=True)
            os.remove(plist_path)
        # 清理日志
        email_dir = os.path.expanduser("~/.court-email")
        for log_suffix in ['.log', '-err.log']:
            lp = os.path.join(email_dir, f"{uid_hash}-email{log_suffix}")
            if os.path.exists(lp):
                os.remove(lp)


# ============================================================
#  Windows 实现
# ============================================================

# ============================================================
#  .ics 日历文件生成（Windows/Linux 兜底，双击导入任意日历）
# ============================================================

def _generate_ics_file(summary, start_dt, end_dt, desc, location, alarm_dt,
                       case_no, uid_hash):
    """生成 .ics 日历文件，保存到桌面。适用于 Windows / Linux / 任意日历软件。"""
    from datetime import timezone

    # iCalendar 使用 UTC 时间
    start_utc = start_dt.strftime('%Y%m%dT%H%M%SZ')
    end_utc = end_dt.strftime('%Y%m%dT%H%M%SZ')
    now_utc = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    # 清理特殊字符
    def _clean(s):
        return s.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//court-sms//CN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
DTSTART:{start_utc}
DTEND:{end_utc}
DTSTAMP:{now_utc}
SUMMARY:{_clean(summary)}
DESCRIPTION:{_clean(desc)}
LOCATION:{_clean(location)}
BEGIN:VALARM
TRIGGER:-P1D
ACTION:DISPLAY
DESCRIPTION:明天开庭：{_clean(summary)}
END:VALARM
END:VEVENT
END:VCALENDAR"""

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    ics_path = os.path.join(desktop, f"开庭提醒_{uid_hash}.ics")

    os.makedirs(desktop, exist_ok=True)
    with open(ics_path, 'w', encoding='utf-8') as f:
        f.write(ics)

    print(f"  📅 .ics 日历文件已生成：{ics_path}")
    print(f"  💡 双击此文件即可导入系统日历 / Outlook / Google Calendar")
    return ics_path


# ============================================================
#  Windows 实现
# ============================================================

def _windows_create_calendar_event(summary, start_dt, end_dt, desc, location, calendar_name):
    """通过 PowerShell 创建 Outlook 日历事件"""
    start_s = start_dt.strftime('%Y-%m-%dT%H:%M:%S')
    end_s = end_dt.strftime('%Y-%m-%dT%H:%M:%S')
    summary_esc = _escape_ps(summary)
    desc_esc = _escape_ps(desc)
    loc_esc = _escape_ps(location)

    ps_script = f'''
$outlook = New-Object -ComObject Outlook.Application
$namespace = $outlook.GetNamespace("MAPI")
$calendar = $namespace.GetDefaultFolder(9)
$appt = $calendar.Items.Add("IPM.Appointment")
$appt.Subject = "{summary_esc}"
$appt.Body = "{desc_esc}"
$appt.Start = [DateTime]"{start_s}"
$appt.End = [DateTime]"{end_s}"
$appt.Location = "{loc_esc}"
$appt.ReminderSet = $true
$appt.ReminderMinutesBeforeStart = 1440
$appt.Save()
Write-Output "OK"
'''

    result = subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_script],
        capture_output=True, text=True, timeout=30
    )
    if 'OK' not in result.stdout:
        print(f"  Outlook error: {result.stderr}")
        return False
    return True


def _windows_delete_calendar_events(case_no, calendar_name):
    """通过 PowerShell 删除旧 Outlook 事件"""
    case_esc = _escape_ps(case_no)
    ps_script = f'''
$outlook = New-Object -ComObject Outlook.Application
$namespace = $outlook.GetNamespace("MAPI")
$calendar = $namespace.GetDefaultFolder(9)
$items = $calendar.Items
$items.IncludeRecurrences = $false
$toDelete = @()
foreach ($item in $items) {{
    if ($item.Class -eq 26 -and $item.Body -match "{case_esc}") {{
        $toDelete += $item
    }}
}}
foreach ($item in $toDelete) {{
    $item.Delete()
}}
Write-Output ($toDelete.Count)
'''
    subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_script],
        capture_output=True, text=True, timeout=30
    )


def _windows_schedule_notification(uid_hash, label, notification_text, alarm_dt, hour, minute):
    """通过 schtasks 创建计划任务（提前1天弹通知）"""
    time_str = f"{alarm_dt.strftime('%Y-%m-%d')}T{hour:02d}:{minute:02d}:00"
    task_name = label
    ps_cmd = (
        f'powershell -NoProfile -Command '
        f'"'
        f'Add-Type -AssemblyName System.Windows.Forms; '
        f'[System.Windows.Forms.MessageBox]::Show('
        f'\\"{notification_text}\\", \\"开庭提醒\\")'
        f'"'
    )

    cmd = [
        'schtasks', '/Create', '/SC', 'ONCE',
        '/TN', task_name, '/TR', ps_cmd,
        '/ST', f"{hour:02d}:{minute:02d}",
        '/SD', alarm_dt.strftime('%Y-%m-%d'),
        '/F'
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=15)


def _windows_schedule_email_script(uid_hash, label, alarm_dt, python_exe, script_dir, hour, minute):
    """通过 schtasks 创建计划任务（提前1天发邮件）"""
    task_name = label
    send_script = os.path.join(script_dir, 'send_court_email.py')
    cmd = [
        'schtasks', '/Create', '/SC', 'ONCE',
        '/TN', task_name, '/TR', f'"{python_exe}" "{send_script}" "{uid_hash}"',
        '/ST', f"{hour:02d}:{minute:02d}",
        '/SD', alarm_dt.strftime('%Y-%m-%d'),
        '/F'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.returncode == 0


def _windows_unload_reminder(uid_hash, modes=('', '-email')):
    for suffix in modes:
        task_name = f"mm-court{suffix}-{uid_hash}"
        subprocess.run(['schtasks', '/Delete', '/TN', task_name, '/F'],
                       capture_output=True, text=True, timeout=10)
        # 清理数据文件
        email_dir = os.path.expanduser("~/.court-email")
        for fn in [f"{uid_hash}.json", f"{uid_hash}-email.log", f"{uid_hash}-email-err.log"]:
            fp = os.path.join(email_dir, fn)
            if os.path.exists(fp):
                os.remove(fp)


# ============================================================
#  平台无关 — 外观接口
# ============================================================

def create_calendar_event(summary, start_dt, end_dt, desc, location,
                          calendar_name="工作", pdf_url=None, case_no="", uid_hash=""):
    if PLATFORM == 'macos':
        start_str = start_dt.strftime("%Y年%m月%d日 %H:%M:%S")
        end_str = end_dt.strftime("%Y年%m月%d日 %H:%M:%S")
        return _macos_create_calendar_event(summary, start_str, end_str,
                                            desc, location, calendar_name, pdf_url)
    elif PLATFORM == 'windows':
        # 先尝试 Outlook COM，失败则降级为 .ics 文件
        ok = _windows_create_calendar_event(summary, start_dt, end_dt,
                                             desc, location, calendar_name)
        if not ok:
            print("  ⚠️ Outlook 不可用，将生成 .ics 日历文件作为兜底")
            alarm_dt = start_dt - timedelta(days=1)
            _generate_ics_file(summary, start_dt, end_dt, desc, location,
                               alarm_dt, case_no, uid_hash)
        return ok
    else:
        # Linux 等平台：生成 .ics 文件
        alarm_dt = start_dt - timedelta(days=1)
        _generate_ics_file(summary, start_dt, end_dt, desc, location,
                           alarm_dt, case_no, uid_hash)
        return False


def delete_calendar_events(case_no, calendar_name="工作"):
    if PLATFORM == 'macos':
        _macos_delete_calendar_events(case_no, calendar_name)
    elif PLATFORM == 'windows':
        _windows_delete_calendar_events(case_no, calendar_name)


def schedule_notification(uid_hash, alarm_dt, hour, minute,
                          case_no=None, case_type=None, hearing_time=None, location=None):
    """提前1天提醒调度（跨平台）。macOS 通过 launchd 跑 hearing-notify 子命令弹通知+桌面MD。"""
    if PLATFORM == 'macos' and case_no and case_type and hearing_time:
        label = f"com.mm.court-{uid_hash}"
        _macos_schedule_notification(uid_hash, label, case_no, case_type, hearing_time, location or '', alarm_dt, hour, minute)
    elif PLATFORM == 'windows':
        label = f"mm-court-{uid_hash}"
        from datetime import timedelta
        start_dt = alarm_dt + timedelta(days=1)
        loc = location or ''
        notif_text = (
            f"⚖️ 明日上午{start_dt.strftime('%H点%M分')}开庭：{case_type or ''}\\n"
            f"案号：{case_no or ''}\\n地点：{loc}"
        )
        _windows_schedule_notification(uid_hash, label, notif_text, alarm_dt, hour, minute)


def pop_notification(title, message, sound="Glass"):
    """立即弹出系统通知（创建时即时反馈，跨平台）"""
    if PLATFORM == 'macos':
        return _macos_pop_notification(title, message, sound)
    elif PLATFORM == 'windows':
        t = _escape_ps(title); m = _escape_ps(message)
        ps = f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show("{m}","{t}")'
        r = subprocess.run(['powershell','-NoProfile','-Command',ps], capture_output=True)
        return r.returncode == 0
    else:
        print(f"  ℹ️ {PLATFORM} 不支持即时弹窗（已生成桌面提醒文件兜底）")
        return False


def hearing_notify(case_no, case_type, hearing_time_str, location):
    """由 launchd 在目标提醒时间（开庭前 1 天）调用：弹系统通知 + 生成桌面 Markdown 提醒文件。

    本函数是被动调用的——不是在创建日历事件时调用，而是 launchd 到时间才触发。
    用户要求：创建日历时不需要提醒，到了目标提醒时间才弹通知+放桌面 MD。
    """
    start_dt = datetime.strptime(hearing_time_str, "%Y-%m-%d %H:%M")

    # 1. 弹系统通知
    pop_notification(
        "⚖️ 开庭提醒",
        f"明日上午{start_dt.strftime('%H点%M分')}开庭：{case_type}\n"
        f"案号：{case_no}\n地点：{location}",
    )

    # 2. 桌面 Markdown 提醒文件（含材料清单）
    md_lines = [
        f"**开庭日期：{_fmt_date(start_dt)}（{_weekday(start_dt)}）**",
        f"**开庭时间：{start_dt.strftime('%H:%M')}**",
        f"**案由：{case_type}**",
        f"**案号：{case_no}**",
        f"**地点：{location or '（待确认）'}**",
        "",
        "## 需准备材料",
        "- [ ] 传票 / 出庭通知书",
        "- [ ] 证据原件（借条、收据、合同、银行流水、转账记录、聊天记录等）",
        "- [ ] 委托手续（授权委托书、所函、执业证复印件）",
        "- [ ] 答辩/代理词、举证清单（如有）",
        "- [ ] 身份证 / 主体资格证明",
    ]
    md_path = generate_desktop_md_reminder(
        "⚠️ 开庭提醒",
        md_lines,
        filename_hint=f"开庭提醒_{start_dt.strftime('%Y-%m-%d_%H%M')}",
    )
    print(f"🔔 系统通知已弹出")
    print(f"📄 桌面提醒文件已生成：{md_path}")


def schedule_email_task(uid_hash, alarm_dt, python_exe, script_dir, email_dir, hour, minute):
    if PLATFORM == 'macos':
        label = f"com.mm.court-email-{uid_hash}"
        return _macos_schedule_email_script(uid_hash, label, alarm_dt,
                                            python_exe, script_dir, email_dir, hour, minute)
    elif PLATFORM == 'windows':
        label = f"mm-court-email-{uid_hash}"
        return _windows_schedule_email_script(uid_hash, label, alarm_dt,
                                              python_exe, script_dir, hour, minute)
    else:
        return False


def unload_reminders(uid_hash):
    if PLATFORM == 'macos':
        _macos_unload_reminder(uid_hash)
    elif PLATFORM == 'windows':
        _windows_unload_reminder(uid_hash)


# ============================================================
#  主流程
# ============================================================

def create_court_calendar(case_no, case_type, hearing_time, location,
                          calendar_name="工作", pdf_url=None):
    """
    创建日历事件 + 系统通知 + QQ邮件提醒（跨平台）。

    创建时：仅写入系统日历 + 调度提醒任务，不弹通知、不生成桌面 MD。
    目标提醒时间（开庭前 1 天）才触发：弹系统通知 + 在桌面生成 Markdown 提醒文件。

    流程：
    1. 写入系统日历（macOS Apple Calendar / Windows Outlook）
    2. 调度提醒任务（launchd / schtasks），到点自动运行 hearing-notify 子命令
       → 弹系统通知 + 桌面生成 Markdown 提醒文件（含需准备材料清单）
    3. QQ 邮件通知（发到 YOUR_QQ_EMAIL@qq.com，微信送达）
    """
    start_dt = datetime.strptime(hearing_time, "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(hours=2)
    alarm_dt = start_dt - timedelta(days=1)
    uid_hash = _uid(case_no)

    summary = f"⚖️ 开庭：{case_type}"
    desc = _desc(case_no, case_type, location)

    # 1. 系统日历
    cal_ok = create_calendar_event(summary, start_dt, end_dt, desc,
                                   location, calendar_name, pdf_url,
                                   case_no=case_no, uid_hash=uid_hash)
    if cal_ok:
        print(f"  ✅ 日历事件已创建：{summary}")
    else:
        print(f"  ⚠️ 日历创建失败（不影响后续提醒）")

    # 2. 调度提醒（到目标提醒时间才弹通知 + 生产桌面 MD，创建时不弹）
    schedule_notification(uid_hash, alarm_dt,
                          start_dt.hour, start_dt.minute,
                          case_no=case_no, case_type=case_type,
                          hearing_time=hearing_time, location=location)
    print(f"  ⏰ 本机电脑提醒已设置（{_fmt_date(alarm_dt)} {start_dt.hour:02d}:{start_dt.minute:02d} 弹通知+桌面MD）")

    # 3. QQ 邮件提醒（提前1天）
    email_ok = schedule_email_reminder(case_no, case_type, hearing_time,
                                       location, pdf_url, uid_hash)
    if email_ok:
        print(f"  📧 QQ 邮件提醒已设置 → YOUR_QQ_EMAIL@qq.com")

    return True


def schedule_email_reminder(case_no, case_type, hearing_time, location,
                            pdf_url=None, uid_hash=None):
    """设置开庭前1天 QQ 邮件通知（跨平台）"""
    if uid_hash is None:
        uid_hash = _uid(case_no)

    start_dt = datetime.strptime(hearing_time, "%Y-%m-%d %H:%M")
    alarm_dt = start_dt - timedelta(days=1)

    location_display = location if location else '（待确认）'
    pdf_info = f"\nPDF链接：{pdf_url}" if pdf_url else ""

    subject = f"⚖️ 开庭提醒：【{case_type}】明天 {_fmt_time(start_dt)}"
    body = f"""您好，

以下案件即将开庭，请提前做好准备：

━━━━━━━━━━━━━━━━━━
⚖️ 开庭提醒
━━━━━━━━━━━━━━━━━━

案号：{case_no}
案由：{case_type}
时间：{_fmt_time(start_dt)}（{_weekday(start_dt)}）
地点：{location_display}
{pdf_info}

━━━━━━━━━━━━━━━━━━
此邮件由 court-sms 自动发送，请以传票原件为准。
"""

    # 邮件数据文件（通用）
    email_dir = os.path.expanduser("~/.court-email")
    os.makedirs(email_dir, exist_ok=True)
    data = {"uid_hash": uid_hash, "subject": subject, "body": body,
            "case_no": case_no, "hearing_time": hearing_time, "location": location}
    with open(os.path.join(email_dir, f"{uid_hash}.json"), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 平台特定的定时任务
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ok = schedule_email_task(uid_hash, alarm_dt, sys.executable, script_dir,
                             email_dir, start_dt.hour, start_dt.minute)
    return ok


def delete_email_reminder(case_no, uid_hash=None):
    """清理邮件提醒"""
    if uid_hash is None:
        uid_hash = _uid(case_no)

    unload_reminders(uid_hash)

    email_dir = os.path.expanduser("~/.court-email")
    data_file = os.path.join(email_dir, f"{uid_hash}.json")
    if os.path.exists(data_file):
        os.remove(data_file)


def delete_court_events(case_no, calendar_name="工作"):
    """清理日历事件（跨平台）"""
    delete_calendar_events(case_no, calendar_name)


def parse_hearing_info_from_pdf(pdf_path):
    """从传票/出庭通知 PDF 提取开庭信息（平台无关）"""
    try:
        from pypdf import PdfReader
    except ImportError:
        print("⚠️ pypdf 未安装，无法解析 PDF 提取开庭信息。")
        print("   安装: pip install pypdf")
        return {}

    try:
        reader = PdfReader(pdf_path)
        text = "".join(page.extract_text() + "\n" for page in reader.pages)
    except Exception as e:
        print(f"⚠️ PDF 读取失败: {e}")
        return {}

    result = {}

    result['case_no'] = m.group(0).strip() if (m := re.search(r'（(\d{4})[^）]*\d+号', text)) else None
    result['case_type'] = m.group(1).strip() if (m := re.search(r'案　?由[：:]\s*(.+)', text)) else None

    m = re.search(r'(应到时间[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日[^\n]{0,10}(\d{1,2})[：:](\d{2}))', text)
    if m:
        result['hearing_time'] = f"{m.group(2)}-{m.group(3).zfill(2)}-{m.group(4).zfill(2)} {m.group(5)}:{m.group(6)}"
    else:
        m = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日[^0-9\n]{0,10}\d{1,2}[：:]\d{2})', text)
        if m:
            dm = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日.*?(\d{1,2})[：:](\d{2})', m.group(1))
            result['hearing_time'] = f"{dm.group(1)}-{dm.group(2).zfill(2)}-{dm.group(3).zfill(2)} {dm.group(4)}:{dm.group(5)}" if dm else None
        else:
            result['hearing_time'] = None

    loc_m = re.search(r'(应到处所[：:]\s*(.+))', text)
    if loc_m:
        result['location'] = loc_m.group(2).strip()
    else:
        loc_m = re.search(r'开庭地点[：:]\s*(.+)', text)
        result['location'] = loc_m.group(1).strip() if loc_m else None

    return result


def should_create_calendar(doc_title, doc_type_label):
    for kw in ['传票', '出庭', '开庭', '应诉通知书']:
        if kw in doc_title or kw in doc_type_label:
            return True
    return False


# ===== CLI =====

def main():
    if len(sys.argv) < 2:
        print(f"平台: {PLATFORM}")
        print()
        print("用法:")
        print("  # 创建日历 + 提醒")
        print(f"  python3 court_calendar.py <案号> <案由> <YYYY-MM-DD HH:MM> <地点> [日历名称] [PDF链接]")
        print(f"  示例: python3 court_calendar.py '（2026）沪01民初1234号' '民间借贷纠纷' '2026-04-24 10:00' '上海市第一中级人民法院 第八法庭' '工作'")
        print()
        print("  # PDF 解析模式")
        print(f"  python3 court_calendar.py parse <pdf_path>")
        print()
        print("  # 本机电脑提醒（由 launchd 在提醒时间自动调用，一般不需手动执行）")
        print(f"  python3 court_calendar.py hearing-notify <案号> <案由> <YYYY-MM-DD HH:MM> <地点>")
        sys.exit(1)

    # --- hearing-notify 子命令（launchd 到提醒时间调用） ---
    if sys.argv[1] == 'hearing-notify':
        if len(sys.argv) < 5:
            print("❌ hearing-notify 参数不足，需：<案号> <案由> <YYYY-MM-DD HH:MM> [地点]")
            sys.exit(1)
        hearing_notify(sys.argv[2], sys.argv[3], sys.argv[4],
                       sys.argv[5] if len(sys.argv) > 5 else '')
        return

    if sys.argv[1] == 'parse' and len(sys.argv) >= 3:
        info = parse_hearing_info_from_pdf(sys.argv[2])
        print("=== PDF 开庭信息提取结果 ===")
        for k, v in info.items():
            print(f"  {k}: {v if v else '（未找到）'}")
        return

    if len(sys.argv) < 5:
        print("❌ 创建日历需要至少 4 个参数：<案号> <案由> <YYYY-MM-DD HH:MM> <地点>")
        sys.exit(1)

    case_no = sys.argv[1]
    case_type = sys.argv[2]
    hearing_time = sys.argv[3]
    location = sys.argv[4]
    calendar_name = sys.argv[5] if len(sys.argv) > 5 else "工作"
    pdf_url = sys.argv[6] if len(sys.argv) > 6 else None

    delete_court_events(case_no, calendar_name)
    delete_email_reminder(case_no)

    success = create_court_calendar(case_no, case_type, hearing_time,
                                    location, calendar_name, pdf_url)
    if success:
        print(f"\n✅ 全部设置完成")
        print(f"  📅 ⚖️ 开庭：{case_type}")
        print(f"  📍 {location}")
        print(f"  🕙 {hearing_time}")
        print(f"  🔔 系统 {PLATFORM} 提前1天提醒")


if __name__ == "__main__":
    main()
