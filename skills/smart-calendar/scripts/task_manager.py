#!/usr/bin/env python3
"""
smart-calendar 核心控制器
负责：Apple日历/提醒事项操作、数据持久化、冲突检测、标签管理、周报生成
"""

import argparse
import json
import os
import subprocess
import uuid
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
from typing import Optional

# ── 配置 ──────────────────────────────────────────
# 数据目录可通过 SMART_CALENDAR_DATA_DIR 覆盖，用于指向 iCloud Drive 或测试隔离。
DATA_DIR = Path(os.environ.get(
    "SMART_CALENDAR_DATA_DIR",
    Path.home() / ".smart-calendar"
))
TASKS_FILE = DATA_DIR / "tasks.json"
CONFIG_FILE = DATA_DIR / "config.json"

# v4.0：默认目标 = 工作列表 / 工作日历（与 work_lists/work_calendars[0] 一致）。
# 这两个常量只在 target_list_for_major_tag / target_calendar_for_major_tag 的 fallback
# 路径用（当 work_lists/work_calendars 配置为空时）。正常路径通过 --tag-major + 配置决定。
DEFAULT_CALENDAR = "工作"
DEFAULT_REMINDER_LIST = "工作"

# 周报期号锚点：2026 年第一个周五（2026-01-02）。
# 期号 = (今日 - 锚点).days // 7 + 1，跨机一致。
REPORT_EPOCH_FRIDAY = date(2026, 1, 2)

# 标签别名表：英文 → 中文规范形式。
# 任何写入路径都过 normalize_tag()，保证 tasks.json 落盘的 tag 是中文。
# SKILL.md 里 agent 可以用 work / life，自动归一化为 工作 / 生活。
TAG_ALIASES = {
    "work": "工作", "Work": "工作", "WORK": "工作",
    "life": "生活", "Life": "生活", "LIFE": "生活",
}


def normalize_tag(tag: str) -> str:
    """把英文别名归一化为中文规范标签。未识别的 tag 原样返回。"""
    if not tag:
        return tag
    return TAG_ALIASES.get(tag.strip(), tag.strip())


def normalize_tags(tags: list) -> list:
    """对一个 tag 列表去重 + 归一化，保留原顺序。"""
    seen = set()
    out = []
    for t in tags or []:
        norm = normalize_tag(t)
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out


# ── 方向 B：Apple 真源 ─────────────────────────────────
# 主标签（工作 / 生活）由 Apple 列表 / 日历名物理承载。
# 配置 work_lists / work_calendars / life_lists / life_calendars 定义
# 哪些 Apple 列表 / 日历名算"工作"、哪些算"生活"。白名单允许多个名字
# （迁移期支持旧 "Work" 日历继续算工作）。

_DEFAULT_WORK_LISTS = ["工作"]
_DEFAULT_LIFE_LISTS = ["生活"]
_DEFAULT_WORK_CALENDARS = ["工作", "Work"]
_DEFAULT_LIFE_CALENDARS = ["生活"]


def get_major_tag_config() -> dict:
    """读 work_lists / life_lists / work_calendars / life_calendars 配置，含默认值兜底。"""
    config = load_config()
    return {
        "work_lists": config.get("work_lists", _DEFAULT_WORK_LISTS),
        "life_lists": config.get("life_lists", _DEFAULT_LIFE_LISTS),
        "work_calendars": config.get("work_calendars", _DEFAULT_WORK_CALENDARS),
        "life_calendars": config.get("life_calendars", _DEFAULT_LIFE_CALENDARS),
    }


def infer_major_tag_from_list(list_name: str) -> Optional[str]:
    """根据 Reminder 所在列表名推断主标签。返回 '工作' / '生活' / None。"""
    if not list_name:
        return None
    cfg = get_major_tag_config()
    if list_name in cfg["work_lists"]:
        return "工作"
    if list_name in cfg["life_lists"]:
        return "生活"
    return None


def infer_major_tag_from_calendar(calendar_name: str) -> Optional[str]:
    """根据 Event 所在日历名推断主标签。返回 '工作' / '生活' / None。"""
    if not calendar_name:
        return None
    cfg = get_major_tag_config()
    if calendar_name in cfg["work_calendars"]:
        return "工作"
    if calendar_name in cfg["life_calendars"]:
        return "生活"
    return None


def target_list_for_major_tag(major_tag: str) -> str:
    """主标签 → 该用哪个 Reminder 列表写入（取白名单第一个）。"""
    cfg = get_major_tag_config()
    if major_tag == "工作":
        return cfg["work_lists"][0] if cfg["work_lists"] else DEFAULT_REMINDER_LIST
    if major_tag == "生活":
        return cfg["life_lists"][0] if cfg["life_lists"] else DEFAULT_REMINDER_LIST
    return DEFAULT_REMINDER_LIST


def target_calendar_for_major_tag(major_tag: str) -> str:
    """主标签 → 该用哪个 Calendar 日历写入（取白名单第一个）。"""
    cfg = get_major_tag_config()
    if major_tag == "工作":
        return cfg["work_calendars"][0] if cfg["work_calendars"] else DEFAULT_CALENDAR
    if major_tag == "生活":
        return cfg["life_calendars"][0] if cfg["life_calendars"] else DEFAULT_CALENDAR
    return DEFAULT_CALENDAR


# ── metadata block 序列化 / 解析 ─────────────────────
# Apple event description / reminder body 末尾追加一段 metadata block，承载
# project / task_type / aux_tags / formal_title 等元数据。块格式：
#
#   [用户可见的备注]
#
#   ────────────────────
#   smart-calendar metadata (do not edit)
#   {"v":1,"project":"A 项目","task_type":"文件审阅","aux_tags":["紧急"],"formal_title":"..."}
#
# 解析容错：找不到 block 不报错（iPhone 手动任务的情况）。

_META_FENCE = "────────────────────"
_META_HEADER = "smart-calendar metadata (do not edit)"
_META_VERSION = 1


def serialize_metadata_block(user_notes: str, meta: dict) -> str:
    """把用户可见备注 + metadata dict 拼成完整的 description / body 文本。"""
    payload = {"v": _META_VERSION}
    for k in ("project", "task_type", "aux_tags", "formal_title"):
        if meta.get(k):
            payload[k] = meta[k]
    json_line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    parts = []
    if user_notes:
        parts.append(user_notes.rstrip())
        parts.append("")
    parts.append(_META_FENCE)
    parts.append(_META_HEADER)
    parts.append(json_line)
    return "\n".join(parts)


def parse_metadata_block(body: str) -> tuple:
    """从 description / body 解析 metadata。返回 (user_notes, meta_dict)。
    找不到 metadata 块时 meta_dict 为空 dict，user_notes 为原始 body。
    """
    if not body:
        return "", {}
    lines = body.split("\n")
    # 反向找 fence 行
    fence_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == _META_FENCE:
            fence_idx = i
            break
    if fence_idx is None:
        return body, {}
    # fence 后下一行应该是 header
    if fence_idx + 1 >= len(lines) or _META_HEADER not in lines[fence_idx + 1]:
        return body, {}
    # header 后下一行（或几行）应该是 JSON
    if fence_idx + 2 >= len(lines):
        return body, {}
    json_text = "\n".join(lines[fence_idx + 2:]).strip()
    try:
        meta = json.loads(json_text)
    except json.JSONDecodeError:
        # metadata 块不完整或损坏 — 把整段当作 user_notes 返回，等用户自行修复
        return body, {}
    # user_notes = fence 之前的内容，去掉尾随空行
    user_notes = "\n".join(lines[:fence_idx]).rstrip()
    return user_notes, meta


def ensure_data_dir():
    """确保数据目录存在，并初始化默认配置"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]", encoding="utf-8")
    if not CONFIG_FILE.exists():
        default_config = {
            "tags": ["工作", "生活"],
            "weekly_report": {
                "enabled": True,
                "output_dir": "",
                "generate_day": "friday",
                "generate_time": "17:00",
                "team_name": "",
                "report_title": "个人工作周报"
            },
            "first_run": True
        }
        CONFIG_FILE.write_text(json.dumps(default_config, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config() -> dict:
    """加载配置"""
    ensure_data_dir()
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_config(config: dict):
    """保存配置（原子写入）"""
    ensure_data_dir()
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CONFIG_FILE)


def load_tasks() -> list:
    """加载所有任务"""
    ensure_data_dir()
    try:
        return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_tasks(tasks: list):
    """保存任务列表（原子写入）"""
    ensure_data_dir()
    tmp = TASKS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(TASKS_FILE)


# ── AppleScript 执行器 ─────────────────────────────

def run_applescript(script: str) -> str:
    """执行 AppleScript，返回输出或抛出异常"""
    ensure_data_dir()

    # 如果脚本操作 Calendar，先确保应用已启动
    if 'tell application "Calendar"' in script:
        subprocess.run(["open", "-a", "Calendar"], capture_output=True)
        import time
        time.sleep(1.5)

    # 将脚本中的特殊字符转义以安全传递
    # 方法：写入临时文件后执行
    tmp = DATA_DIR / f"tmp_{uuid.uuid4().hex}.scpt"
    try:
        tmp.write_text(script, encoding="utf-8")
        # timeout 180s — 大型 Reminders / Calendar 库下，首次 sync 可能慢
        result = subprocess.run(
            ["osascript", str(tmp)],
            capture_output=True,
            text=True,
            timeout=180
        )
        if result.returncode != 0:
            raise RuntimeError(f"AppleScript error: {result.stderr}")
        return result.stdout.strip()
    finally:
        if tmp.exists():
            tmp.unlink()


def escape_for_applescript(s: str) -> str:
    """将字符串转义为AppleScript安全格式。

    顺序很重要：必须先转义反斜杠，再转义双引号，否则双引号转义产生的 \\ 会被
    再次转义成 \\\\，导致 AppleScript 解析出字面量的 \\"。换行符在 AppleScript
    字符串字面量里非法，需要用 " & linefeed & " 拼接。
    """
    if not s:
        return ""
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', '" & linefeed & "')
    return s


# ── 日历操作 ──────────────────────────────────────

def list_calendars() -> list:
    """列出所有日历名称"""
    script = '''
tell application "Calendar"
    if not running then launch
    set calList to {}
    repeat with c in calendars
        set end of calList to (name of c)
    end repeat
    set AppleScript's text item delimiters to linefeed
    return calList as string
end tell
'''
    out = run_applescript(script)
    return [x.strip() for x in out.split("\n") if x.strip()]


def create_calendar_event(title: str, start: str, end: str,
                          calendar_name: str = DEFAULT_CALENDAR,
                          notes: str = "", location: str = "",
                          metadata: Optional[dict] = None) -> str:
    """
    创建日历事件
    时间格式: "YYYY-MM-DD HH:MM"
    metadata: 可选 dict，会序列化为 metadata block 追加到 description 末尾
    返回事件UID
    """
    # 如果提供了 metadata，把它序列化进 description
    if metadata:
        notes = serialize_metadata_block(notes, metadata)

    title_e = escape_for_applescript(title)
    notes_e = escape_for_applescript(notes)

    # 构造AppleScript date
    script = f'''
tell application "Calendar"
    if not running then launch
    set calName to "{escape_for_applescript(calendar_name)}"
    set targetCal to first calendar whose name is calName
    set startDate to date "{start}:00"
    set endDate to date "{end}:00"
    set newEvent to make new event at end of events of targetCal with properties {{summary:"{title_e}", start date:startDate, end date:endDate, description:"{notes_e}"}}
    return uid of newEvent
end tell
'''
    return run_applescript(script)


def update_calendar_event(event_uid: str, title: Optional[str] = None,
                          start: Optional[str] = None, end: Optional[str] = None,
                          notes: Optional[str] = None) -> str:
    """更新日历事件"""
    props = []
    if title is not None:
        props.append(f'summary:"{escape_for_applescript(title)}"')
    if start is not None:
        props.append(f'start date:(date "{start}:00")')
    if end is not None:
        props.append(f'end date:(date "{end}:00")')
    if notes is not None:
        props.append(f'description:"{escape_for_applescript(notes)}"')

    prop_str = ", ".join(props)
    script = f'''
tell application "Calendar"
    if not running then launch
    set ev to first event whose uid is "{event_uid}"
    set properties of ev to {{{prop_str}}}
    return "updated"
end tell
'''
    return run_applescript(script)


def delete_calendar_event(event_uid: str) -> str:
    """删除日历事件"""
    script = f'''
tell application "Calendar"
    if not running then launch
    set ev to first event whose uid is "{event_uid}"
    delete ev
    return "deleted"
end tell
'''
    return run_applescript(script)


def list_events_in_range(start_date: str, end_date: str) -> list:
    """
    列出指定日期范围内的日历事件，**仅扫白名单内的日历**（避免节假日 / 订阅日历干扰）。
    返回 [{uid, title, start, end, calendar}]
    start/end 为 datetime 对象（系统时区，naive）
    """
    cfg = get_major_tag_config()
    target_calendars = list(set(cfg["work_calendars"] + cfg["life_calendars"]))
    if not target_calendars:
        return []
    or_conds = " or ".join(f'name of c = "{escape_for_applescript(n)}"' for n in target_calendars)
    script = f'''
tell application "Calendar"
    if not running then launch
    set startD to date "{start_date} 00:00:00"
    set endD to date "{end_date} 23:59:59"
    set resultList to {{}}
    repeat with c in calendars
        if {or_conds} then
            set calNm to name of c
            repeat with ev in (every event of c whose start date ≥ startD and start date ≤ endD)
                set sD to start date of ev
                set eD to end date of ev
                set evInfo to (uid of ev) & "|" & (summary of ev) & "|" & ¬
                    (year of sD as string) & "|" & (month of sD as integer as string) & "|" & (day of sD as string) & "|" & ¬
                    (hours of sD as string) & "|" & (minutes of sD as string) & "|" & ¬
                    (year of eD as string) & "|" & (month of eD as integer as string) & "|" & (day of eD as string) & "|" & ¬
                    (hours of eD as string) & "|" & (minutes of eD as string) & "|" & calNm
                set end of resultList to evInfo
            end repeat
        end if
    end repeat
    set AppleScript's text item delimiters to linefeed
    return resultList as string
end tell
'''
    out = run_applescript(script)
    events = []
    for line in out.split("\n"):
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 13)
        if len(parts) >= 13:
            try:
                start_dt = datetime(int(parts[2]), int(parts[3]), int(parts[4]),
                                    int(parts[5]), int(parts[6]))
                end_dt = datetime(int(parts[7]), int(parts[8]), int(parts[9]),
                                  int(parts[10]), int(parts[11]))
                events.append({
                    "uid": parts[0],
                    "title": parts[1],
                    "start": start_dt,
                    "end": end_dt,
                    "calendar": parts[12] if len(parts) > 12 else "",
                })
            except (ValueError, IndexError):
                continue
    return events


# ── sync 用的批量拉取（含 description / body）─────
# 选用 @@R@@ / @@F@@ 作为记录 / 字段分隔符 — 用户输入里几乎不可能出现，
# 比 unicode 控制字符更可靠跨 encoding。

_SYNC_RECORD_SEP = "@@R@@"
_SYNC_FIELD_SEP = "@@F@@"


def _fetch_events_for_sync(calendar_names: list, start_date: str, end_date: str) -> list:
    """
    拉指定日历范围内的事件（含 description）。
    返回 [{uid, title, start_dt, end_dt, calendar, description}]
    """
    if not calendar_names:
        return []
    or_conds = " or ".join(f'name of c = "{escape_for_applescript(n)}"' for n in calendar_names)
    script = f'''
tell application "Calendar"
    if not running then launch
    set startD to date "{start_date} 00:00:00"
    set endD to date "{end_date} 23:59:59"
    set out to ""
    repeat with c in calendars
        if {or_conds} then
            set calNm to name of c
            repeat with ev in (every event of c whose start date ≥ startD and start date ≤ endD)
                set sD to start date of ev
                set eD to end date of ev
                set descTxt to ""
                try
                    set descTxt to description of ev
                    if descTxt is missing value then set descTxt to ""
                end try
                set out to out & (uid of ev) & "{_SYNC_FIELD_SEP}" & (summary of ev) & "{_SYNC_FIELD_SEP}" & ¬
                    (year of sD as string) & "-" & (month of sD as integer as string) & "-" & (day of sD as string) & " " & (hours of sD as string) & ":" & (minutes of sD as string) & "{_SYNC_FIELD_SEP}" & ¬
                    (year of eD as string) & "-" & (month of eD as integer as string) & "-" & (day of eD as string) & " " & (hours of eD as string) & ":" & (minutes of eD as string) & "{_SYNC_FIELD_SEP}" & ¬
                    calNm & "{_SYNC_FIELD_SEP}" & descTxt & "{_SYNC_RECORD_SEP}"
            end repeat
        end if
    end repeat
    return out
end tell
'''
    out = run_applescript(script)
    events = []
    if not out:
        return events
    for rec in out.split(_SYNC_RECORD_SEP):
        rec = rec.strip()
        if not rec or _SYNC_FIELD_SEP not in rec:
            continue
        parts = rec.split(_SYNC_FIELD_SEP, 5)
        if len(parts) < 6:
            continue
        try:
            sy, sm, sd_hm = parts[2].split("-", 2)
            sd, hm = sd_hm.split(" ")
            sh, smin = hm.split(":")
            start_dt = datetime(int(sy), int(sm), int(sd), int(sh), int(smin))
            ey, em, ed_hm = parts[3].split("-", 2)
            ed, ehm = ed_hm.split(" ")
            eh, emin = ehm.split(":")
            end_dt = datetime(int(ey), int(em), int(ed), int(eh), int(emin))
        except (ValueError, IndexError):
            continue
        events.append({
            "uid": parts[0],
            "title": parts[1],
            "start_dt": start_dt,
            "end_dt": end_dt,
            "calendar": parts[4],
            "description": parts[5],
        })
    return events


def _fetch_reminders_for_sync(list_names: list) -> list:
    """
    拉指定列表里的所有提醒事项（含 body）。
    返回 [{id, name, list, due, completed, body}]
    """
    if not list_names:
        return []
    # 构造 OR 条件：name of rlist = "X" or name of rlist = "Y" ...
    # 比 "is in wanted" + list-as-string 转换快很多（37 条 reminder 上经验差异 60s vs 0.5s）
    or_conds = " or ".join(f'name of rlist = "{escape_for_applescript(n)}"' for n in list_names)
    # 只拉 completed is false 的 reminder。Reminders.app 端谓词过滤比 Python 端过滤快得多
    # （实测：不过滤需要 4.5 分钟扫几百条历史 reminder；只拉 active 几秒内完成）。
    # 已完成的 reminder 不进 tasks.json — Apple 真源仍在，需要时手动查看。
    script = f'''
tell application "Reminders"
    set out to ""
    repeat with rlist in lists
        if {or_conds} then
            set listN to name of rlist
            repeat with rem in (every reminder of rlist whose completed is false)
                set bodyTxt to ""
                try
                    set bodyTxt to body of rem
                    if bodyTxt is missing value then set bodyTxt to ""
                end try
                set dueStr to ""
                try
                    set dD to due date of rem
                    if dD is not missing value then
                        set dueStr to (year of dD as string) & "-" & (month of dD as integer as string) & "-" & (day of dD as string) & " " & (hours of dD as string) & ":" & (minutes of dD as string)
                    end if
                end try
                set out to out & (id of rem) & "{_SYNC_FIELD_SEP}" & (name of rem) & "{_SYNC_FIELD_SEP}" & listN & "{_SYNC_FIELD_SEP}" & dueStr & "{_SYNC_FIELD_SEP}" & "0" & "{_SYNC_FIELD_SEP}" & bodyTxt & "{_SYNC_RECORD_SEP}"
            end repeat
        end if
    end repeat
    return out
end tell
'''
    out = run_applescript(script)
    reminders = []
    if not out:
        return reminders
    for rec in out.split(_SYNC_RECORD_SEP):
        rec = rec.strip()
        if not rec or _SYNC_FIELD_SEP not in rec:
            continue
        parts = rec.split(_SYNC_FIELD_SEP, 5)
        if len(parts) < 6:
            continue
        reminders.append({
            "id": parts[0],
            "name": parts[1],
            "list": parts[2],
            "due": parts[3] if parts[3] else None,
            "completed": parts[4] == "1",
            "body": parts[5],
        })
    return reminders


def sync_tasks_from_apple(months_back: int = 6, months_forward: int = 3,
                          dry_run: bool = False) -> dict:
    """
    从 Apple Calendar / Reminders 重建 tasks.json。
    扫白名单内的列表 / 日历（work_lists + life_lists + work_calendars + life_calendars）。
    Calendar 事件按时间窗口（过去 N 月 + 未来 M 月）；Reminder 取所在列表全量。

    每次 sync 前备份 tasks.json → tasks.json.bak。
    dry_run=True 时只返回结果不写盘。
    """
    cfg = get_major_tag_config()
    target_lists = list(set(cfg["work_lists"] + cfg["life_lists"]))
    target_calendars = list(set(cfg["work_calendars"] + cfg["life_calendars"]))

    now = datetime.now()
    start_date = (now - timedelta(days=months_back * 30)).strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=months_forward * 30)).strftime("%Y-%m-%d")

    print(f"[sync] 扫描列表: {target_lists}")
    print(f"[sync] 扫描日历: {target_calendars}（{start_date} ~ {end_date}）")

    apple_reminders = _fetch_reminders_for_sync(target_lists)
    apple_events = _fetch_events_for_sync(target_calendars, start_date, end_date)
    print(f"[sync] 拉到 {len(apple_reminders)} 条 reminder + {len(apple_events)} 条 event")

    # 保留旧 tasks.json 的 task_id（按 reminder_id / event_uid 反查），避免每次 sync 改 task_id
    old_tasks = load_tasks()
    rem_id_to_task = {t["reminder_id"]: t for t in old_tasks if t.get("reminder_id")}
    evt_uid_to_task = {t["calendar_event_id"]: t for t in old_tasks if t.get("calendar_event_id")}

    new_tasks = []
    seen_keys = set()
    now_iso = datetime.now(timezone.utc).astimezone().isoformat()

    def _build_task(rem=None, evt=None):
        """从 Apple 端记录构造 task 记录。"""
        # 主标签由所在 list / calendar 推断
        major = None
        if rem:
            major = infer_major_tag_from_list(rem["list"])
        elif evt:
            major = infer_major_tag_from_calendar(evt["calendar"])
        tags = [major] if major else []

        # 解析 metadata block
        body = rem["body"] if rem else (evt["description"] if evt else "")
        user_notes, meta = parse_metadata_block(body)

        # 复用旧 task_id（若有），否则新生成
        existing = None
        if rem and rem["id"] in rem_id_to_task:
            existing = rem_id_to_task[rem["id"]]
        elif evt and evt["uid"] in evt_uid_to_task:
            existing = evt_uid_to_task[evt["uid"]]
        task_id = existing["task_id"] if existing else str(uuid.uuid4())
        created_at = existing["created_at"] if existing else now_iso

        title = rem["name"] if rem else (evt["title"] if evt else "")
        parsed = (existing or {}).get("parsed", {})
        parsed["title"] = title
        if meta.get("project"):
            parsed["project"] = meta["project"]
        if meta.get("task_type"):
            parsed["task_type"] = meta["task_type"]
        if rem and rem.get("due"):
            # Apple 端 due date 同步进 parsed.deadline_date
            try:
                d, t = rem["due"].split(" ")
                y, m, dy = d.split("-")
                parsed["deadline_date"] = f"{y}-{int(m):02d}-{int(dy):02d}"
                if t:
                    parsed["deadline_time"] = t
            except (ValueError, IndexError):
                pass
        if evt:
            parsed["start_datetime"] = evt["start_dt"].strftime("%Y-%m-%d %H:%M")
            parsed["end_datetime"] = evt["end_dt"].strftime("%Y-%m-%d %H:%M")

        # 次标签（aux_tags）合并进 tags
        if meta.get("aux_tags"):
            tags = list(tags) + [t for t in meta["aux_tags"] if t not in tags]

        status = "active"
        if rem and rem.get("completed"):
            status = "completed"

        return {
            "task_id": task_id,
            "user_input": (existing or {}).get("user_input", title),
            "parsed": parsed,
            "formal_title": meta.get("formal_title", "") or (existing or {}).get("formal_title", title),
            "formal_notes": user_notes,
            "calendar_event_id": evt["uid"] if evt else (existing or {}).get("calendar_event_id"),
            "reminder_id": rem["id"] if rem else (existing or {}).get("reminder_id"),
            "tags": normalize_tags(tags),
            "created_at": created_at,
            "updated_at": now_iso,
            "status": status,
        }

    # 先处理 Reminders
    for rem in apple_reminders:
        key = ("rem", rem["id"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        new_tasks.append(_build_task(rem=rem))

    # 再处理 Events（已被 reminder 覆盖的双轨任务，由后续逻辑合并；目前简化为各自成 task）
    for evt in apple_events:
        key = ("evt", evt["uid"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        new_tasks.append(_build_task(evt=evt))

    summary = {
        "scanned_reminders": len(apple_reminders),
        "scanned_events": len(apple_events),
        "new_task_count": len(new_tasks),
        "old_task_count": len(old_tasks),
        "dry_run": dry_run,
    }

    if not dry_run:
        # 备份旧 tasks.json
        if TASKS_FILE.exists():
            bak = TASKS_FILE.with_suffix(".json.bak")
            bak.write_text(TASKS_FILE.read_text(encoding="utf-8"), encoding="utf-8")
            summary["backup"] = str(bak)
        save_tasks(new_tasks)

    return summary


# ── 提醒事项操作 ──────────────────────────────────

def list_reminder_lists() -> list:
    """列出所有提醒事项列表"""
    script = '''
tell application "Reminders"
    set listNames to {}
    repeat with rlist in lists
        set end of listNames to (name of rlist)
    end repeat
    set AppleScript's text item delimiters to ","
    return listNames as string
end tell
'''
    out = run_applescript(script)
    return [x.strip() for x in out.split(",") if x.strip()]


def create_reminder(title: str, due_date: Optional[str] = None,
                    list_name: str = DEFAULT_REMINDER_LIST,
                    notes: str = "", priority: int = 0,
                    metadata: Optional[dict] = None) -> str:
    """
    创建提醒事项
    due_date 格式: "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM"
    priority: 0=无, 1=高, 2=中, 3=低
    metadata: 可选 dict，会序列化为 metadata block 追加到 body 末尾
    返回提醒事项ID（名称+ID组合）
    """
    if metadata:
        notes = serialize_metadata_block(notes, metadata)

    title_e = escape_for_applescript(title)
    notes_e = escape_for_applescript(notes)
    list_e = escape_for_applescript(list_name)

    date_clause = ""
    if due_date:
        if len(due_date) == 10:  # 只有日期
            date_clause = f', due date:date "{due_date} 09:00:00"'
        else:  # 日期+时间
            date_clause = f', due date:date "{due_date}:00"'

    priority_clause = ""
    if priority == 1:
        priority_clause = ', priority:1'
    elif priority == 2:
        priority_clause = ', priority:2'
    elif priority == 3:
        priority_clause = ', priority:3'

    script = f'''
tell application "Reminders"
    set targetList to first list whose name is "{list_e}"
    set newReminder to make new reminder at end of reminders of targetList with properties {{name:"{title_e}"{date_clause}{priority_clause}, body:"{notes_e}"}}
    return (id of newReminder) & "|" & (name of newReminder)
end tell
'''
    result = run_applescript(script)
    # 返回 "id|name"
    return result


def update_reminder(reminder_id: str, title: Optional[str] = None,
                    due_date: Optional[str] = None,
                    notes: Optional[str] = None) -> str:
    """更新提醒事项"""
    props = []
    if title is not None:
        props.append(f'name:"{escape_for_applescript(title)}"')
    if due_date is not None:
        props.append(f'due date:(date "{due_date}:00")')
    if notes is not None:
        props.append(f'body:"{escape_for_applescript(notes)}"')

    prop_str = ", ".join(props)
    script = f'''
tell application "Reminders"
    set rem to first reminder whose id is "{reminder_id}"
    set properties of rem to {{{prop_str}}}
    return "updated"
end tell
'''
    return run_applescript(script)


def delete_reminder(reminder_id: str) -> str:
    """删除提醒事项"""
    script = f'''
tell application "Reminders"
    set rem to first reminder whose id is "{reminder_id}"
    delete rem
    return "deleted"
end tell
'''
    return run_applescript(script)


def list_reminders_in_range(start_date: str, end_date: str) -> list:
    """列出指定日期范围内的提醒事项"""
    script = f'''
tell application "Reminders"
    set startD to date "{start_date} 00:00:00"
    set endD to date "{end_date} 23:59:59"
    set resultList to {{}}
    repeat with rlist in lists
        repeat with rem in (every reminder of rlist whose due date ≥ startD and due date ≤ endD)
            set remInfo to (id of rem) & "|" & (name of rem) & "|" & (due date of rem as string)
            set end of resultList to remInfo
        end repeat
    end repeat
    set AppleScript's text item delimiters to linefeed
    return resultList as string
end tell
'''
    out = run_applescript(script)
    reminders = []
    for line in out.split("\n"):
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 2)
        if len(parts) >= 3:
            reminders.append({
                "id": parts[0],
                "title": parts[1],
                "due": parts[2]
            })
    return reminders


# ── 冲突检测 ──────────────────────────────────────

def check_conflict(check_date: str, check_time: Optional[str] = None,
                   duration_minutes: int = 60) -> list:
    """
    检查指定日期/时间是否有冲突。
    - 给了 check_time：返回与 [check_time, check_time + duration) 真正区间重叠的事件
    - 未给 check_time：返回当天所有事件（按日期粒度判断）
    返回 [{uid, title, start, end, calendar}]，start/end 已格式化为字符串
    """
    if check_time:
        query_start = datetime.strptime(f"{check_date} {check_time}", "%Y-%m-%d %H:%M")
        query_end = query_start + timedelta(minutes=duration_minutes)
    else:
        query_start = datetime.strptime(f"{check_date} 00:00", "%Y-%m-%d %H:%M")
        query_end = datetime.strptime(f"{check_date} 23:59", "%Y-%m-%d %H:%M")

    events = list_events_in_range(
        query_start.strftime("%Y-%m-%d"),
        query_end.strftime("%Y-%m-%d"),
    )

    conflicts = []
    for ev in events:
        ev_start = ev["start"]
        ev_end = ev["end"]
        # 区间重叠判定：start1 < end2 and start2 < end1
        if ev_start < query_end and query_start < ev_end:
            conflicts.append({
                "uid": ev["uid"],
                "title": ev["title"],
                "start": ev_start.strftime("%Y-%m-%d %H:%M"),
                "end": ev_end.strftime("%Y-%m-%d %H:%M"),
                "calendar": ev.get("calendar", ""),
            })

    return conflicts


# ── 标签管理 ──────────────────────────────────────

def get_tags() -> list:
    """获取所有标签"""
    config = load_config()
    return config.get("tags", ["工作", "生活"])


def add_tag(tag: str) -> bool:
    """添加新标签（自动归一化别名）"""
    tag = normalize_tag(tag)
    if not tag:
        return False
    config = load_config()
    tags = config.get("tags", [])
    if tag not in tags:
        tags.append(tag)
        config["tags"] = tags
        save_config(config)
        return True
    return False


def remove_tag(tag: str) -> bool:
    """删除标签（不会删除任务上的该标签，只是从可选列表移除）"""
    tag = normalize_tag(tag)
    config = load_config()
    tags = config.get("tags", [])
    if tag in tags:
        tags.remove(tag)
        config["tags"] = tags
        save_config(config)
        return True
    return False


def set_task_tags(task_id: str, tags: list) -> bool:
    """设置任务的标签（自动归一化别名）"""
    tags = normalize_tags(tags)
    tasks = load_tasks()
    for t in tasks:
        if t["task_id"] == task_id:
            t["tags"] = tags
            t["updated_at"] = datetime.now(timezone.utc).astimezone().isoformat()
            save_tasks(tasks)
            return True
    return False


def get_task_tags(task_id: str) -> list:
    """获取任务的标签"""
    tasks = load_tasks()
    for t in tasks:
        if t["task_id"] == task_id:
            return t.get("tags", [])
    return []


# ── 任务管理 ──────────────────────────────────────

def add_task(task_data: dict) -> str:
    """添加新任务到数据库（tag 自动归一化）"""
    tasks = load_tasks()
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).astimezone().isoformat()

    task_record = {
        "task_id": task_id,
        "user_input": task_data.get("user_input", ""),
        "parsed": task_data.get("parsed", {}),
        "formal_title": task_data.get("formal_title", ""),
        "formal_notes": task_data.get("formal_notes", ""),
        "calendar_event_id": task_data.get("calendar_event_id"),
        "reminder_id": task_data.get("reminder_id"),
        "tags": normalize_tags(task_data.get("tags", [])),
        "created_at": now,
        "updated_at": now,
        "status": "active"
    }
    tasks.append(task_record)
    save_tasks(tasks)
    return task_id


def search_tasks(keyword: str) -> list:
    """按关键词搜索任务"""
    tasks = load_tasks()
    keyword_lower = keyword.lower()
    results = []
    for t in tasks:
        text = f"{t.get('user_input', '')} {t.get('formal_title', '')} {t.get('parsed', {}).get('project', '')} {t.get('parsed', {}).get('title', '')}"
        if keyword_lower in text.lower():
            results.append(t)
    return results


def update_task_field(task_id: str, field: str, value) -> bool:
    """更新任务字段"""
    tasks = load_tasks()
    for t in tasks:
        if t["task_id"] == task_id:
            if field in t:
                t[field] = value
            elif field.startswith("parsed."):
                subfield = field.split(".", 1)[1]
                t["parsed"][subfield] = value
            t["updated_at"] = datetime.now(timezone.utc).astimezone().isoformat()
            save_tasks(tasks)
            return True
    return False


def delete_task(task_id: str) -> bool:
    """删除任务及其关联的日历/提醒事项"""
    tasks = load_tasks()
    for i, t in enumerate(tasks):
        if t["task_id"] == task_id:
            # 删除关联的日历事件
            if t.get("calendar_event_id"):
                try:
                    delete_calendar_event(t["calendar_event_id"])
                except Exception as e:
                    print(f"Warning: failed to delete calendar event: {e}")
            # 删除关联的提醒事项
            if t.get("reminder_id"):
                try:
                    delete_reminder(t["reminder_id"])
                except Exception as e:
                    print(f"Warning: failed to delete reminder: {e}")
            # 从数据库删除
            tasks.pop(i)
            save_tasks(tasks)
            return True
    return False


def get_recent_tasks(limit: int = 10) -> list:
    """获取最近创建的任务"""
    tasks = load_tasks()
    tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return tasks[:limit]


# ── 周报生成 ──────────────────────────────────────

def _local_tz():
    """系统本地时区（datetime.now().astimezone() 自带的 tzinfo）"""
    return datetime.now().astimezone().tzinfo


def _parse_iso_aware(s: str) -> Optional[datetime]:
    """解析 ISO 字符串为 timezone-aware datetime。
    没有时区信息的视为本地时区。返回 None 表示解析失败。"""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_local_tz())
    return dt


def _get_report_week_range(now: datetime = None) -> tuple:
    """
    计算周报时间范围
    返回 (week_start_dt, week_end_dt, week_start_str, week_end_str)
    week_start/end_dt 为 timezone-aware datetime
    范围：上周五 18:00 至 本周五 17:00
    """
    if now is None:
        now = datetime.now().astimezone()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=_local_tz())

    # 上周五 18:00
    days_since_friday = (now.weekday() - 4) % 7  # 0=本周五（或上周五如周一），... 6=本周四
    week_end = now - timedelta(days=days_since_friday)
    week_end = week_end.replace(hour=17, minute=0, second=0, microsecond=0)

    # 上周五 18:00 = 本周五 17:00 - 7天 + 1小时
    week_start = week_end - timedelta(days=7) + timedelta(hours=1)

    return (
        week_start,
        week_end,
        week_start.strftime("%Y-%m-%d %H:%M"),
        week_end.strftime("%Y-%m-%d %H:%M")
    )


def _is_task_in_range(t: dict, week_start: datetime, week_end: datetime) -> bool:
    """判断任务是否在周报时间范围内有活动"""
    for field in ("created_at", "updated_at"):
        dt = _parse_iso_aware(t.get(field, ""))
        if dt is not None and week_start <= dt <= week_end:
            return True

    deadline = t.get("parsed", {}).get("deadline_date", "")
    if deadline:
        # deadline_date 当天 17:00 作为截止时刻（本地时区）
        try:
            d = datetime.strptime(deadline, "%Y-%m-%d").replace(
                hour=17, minute=0, tzinfo=_local_tz())
            if week_start <= d <= week_end:
                return True
        except ValueError:
            pass

    return False


def _is_task_todo(t: dict, week_end: datetime) -> bool:
    """判断任务是否属于'待办'（下周 to-do）"""
    status = t.get("status", "active")
    if status == "completed":
        return False

    deadline = t.get("parsed", {}).get("deadline_date", "")
    if deadline:
        try:
            d = datetime.strptime(deadline, "%Y-%m-%d").replace(
                hour=17, minute=0, tzinfo=_local_tz())
            return d > week_end
        except ValueError:
            return True
    # 无 deadline 但状态未完成 → 视为持续待办
    return True


def _assert_report_output_outside_git(output_path: Path):
    """拒绝将周报写入 Git worktree 内。"""
    resolved = output_path.resolve()
    for directory in (resolved, *resolved.parents):
        if (directory / ".git").exists():
            raise ValueError(f"拒绝将周报写入 Git 仓库内：{resolved}")


def generate_weekly_report(now: datetime = None, output_path: Optional[Path] = None) -> str:
    """
    生成周报（项目-进展-待办三级结构）
    只提取带'工作'标签的任务
    标题、团队名通过 config.weekly_report.{report_title, team_name} 配置
    """
    if now is None:
        now = datetime.now()

    config = load_config()
    wr_config = config.get("weekly_report", {})
    report_title = wr_config.get("report_title", "个人工作周报")
    team_name = wr_config.get("team_name", "")
    # 完整标题 = "{team_name}{report_title}"，team_name 为空时直接用 report_title
    full_title = f"{team_name}{report_title}" if team_name else report_title

    week_start_dt, week_end_dt, week_start_str, week_end_str = _get_report_week_range(now)

    # 期号 = (本周报对应的"本周五" - 锚点周五).days // 7 + 1
    # 跨机算出来必定一致，不依赖任何持久化计数器。
    report_counter = (week_end_dt.date() - REPORT_EPOCH_FRIDAY).days // 7 + 1
    week_end_date = week_end_str[:10]
    year = now.year
    week_num = now.isocalendar()[1]

    tasks = load_tasks()

    # 方向 B：主标签由 Apple list / calendar 物理决定，但 sync 会把推断结果写回 tasks.tags。
    # 所以筛选仍读 tags 字段 — 但这个字段现在保证由 list/calendar 推断而来（sync 维护）。
    # 兼容性：直接 create-reminder/event 走 --tag-major 时也会把主标签写进 tags（task 9 数据迁移会同步）。
    work_tasks = [t for t in tasks if "工作" in t.get("tags", [])]

    # 进展：本周时间范围内有活动的
    progress_tasks = [t for t in work_tasks if _is_task_in_range(t, week_start_dt, week_end_dt)]

    # 待办：下周 to-do
    todo_tasks = [t for t in work_tasks if _is_task_todo(t, week_end_dt)]

    # 按项目分组
    progress_by_project = {}
    for t in progress_tasks:
        proj = t.get("parsed", {}).get("project", "未分类")
        if proj not in progress_by_project:
            progress_by_project[proj] = []
        progress_by_project[proj].append(t)

    todo_by_project = {}
    for t in todo_tasks:
        proj = t.get("parsed", {}).get("project", "未分类")
        if proj not in todo_by_project:
            todo_by_project[proj] = []
        todo_by_project[proj].append(t)

    # 收集所有项目（进展+待办的并集）
    all_projects = sorted(set(list(progress_by_project.keys()) + list(todo_by_project.keys())))

    # ── 生成报告文本 ──────────────────────────────
    lines = []
    lines.append(f"# {full_title}（{week_end_date}）")
    lines.append(f"**（{year}年第{week_num}期 总第{report_counter}期）**")
    lines.append("")
    lines.append(f"**统计周期**：{week_start_str} ~ {week_end_str}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 概览统计
    lines.append("## 一、本周概览")
    lines.append("")
    lines.append(f"- **工作标签任务总数**：{len(work_tasks)}")
    lines.append(f"- **本周进展**：{len(progress_tasks)} 项")
    lines.append(f"- **下周待办**：{len(todo_tasks)} 项")
    lines.append("")

    # 按项目展开
    lines.append("## 二、重点项目进展与待办")
    lines.append("")

    for idx, proj in enumerate(all_projects, 1):
        lines.append(f"### {idx}、{proj}")
        lines.append("")

        proj_progress = progress_by_project.get(proj, [])
        proj_todo = todo_by_project.get(proj, [])

        # 项目概览（如果有的话）
        # 取第一个任务的正式备注作为概览摘要（如果有）
        if proj_progress:
            first_task = proj_progress[0]
            formal_notes = first_task.get("formal_notes", "")
            if formal_notes:
                # 取前200字作为概览
                summary = formal_notes[:200]
                if len(formal_notes) > 200:
                    summary += "..."
                lines.append(f"**【项目概览】** {summary}")
                lines.append("")

        # 进展
        if proj_progress:
            lines.append("**【进展】**")
            lines.append("")
            for t in proj_progress:
                title = t.get("formal_title") or t.get("parsed", {}).get("title", "无标题")
                deadline = t.get("parsed", {}).get("deadline_date", "")
                task_type = t.get("parsed", {}).get("task_type", "")
                status = t.get("status", "active")
                status_label = "已完成" if status == "completed" else "进行中"

                date_prefix = f"（{deadline}）" if deadline else ""
                type_prefix = f"【{task_type}】" if task_type else ""
                lines.append(f"- {type_prefix}**{title}**{date_prefix} —— {status_label}")

                # 如果有正式备注，添加简要说明
                formal_notes = t.get("formal_notes", "")
                if formal_notes and len(formal_notes) > 10:
                    # 取备注前150字作为简要说明
                    brief = formal_notes[:150]
                    if len(formal_notes) > 150:
                        brief += "..."
                    lines.append(f"  - {brief}")
            lines.append("")

        # 待办
        if proj_todo:
            lines.append("**【待办】**")
            lines.append("")
            for t in proj_todo:
                title = t.get("formal_title") or t.get("parsed", {}).get("title", "无标题")
                deadline = t.get("parsed", {}).get("deadline_date", "")
                task_type = t.get("parsed", {}).get("task_type", "")
                priority = t.get("parsed", {}).get("priority", "")

                type_prefix = f"【{task_type}】" if task_type else ""
                date_suffix = f"（截止：{deadline}）" if deadline else "（时间待定）"
                priority_mark = "🔴" if priority == "高" else "🟡" if priority == "中" else "🟢"
                lines.append(f"- {priority_mark} {type_prefix}**{title}**{date_suffix}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # 页脚：team_name 配了则显示，没配则省略
    if team_name:
        lines.append(f"{team_name}（{week_end_date}）")

    report_text = "\n".join(lines)

    # 如果指定了输出路径，写入文件
    if output_path:
        output_path = Path(output_path)
        _assert_report_output_outside_git(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        filename = f"{full_title}（{week_end_date}）.md"
        filepath = output_path / filename
        filepath.write_text(report_text, encoding="utf-8")
        print(f"REPORT_WRITTEN|{filepath}")

    return report_text


# ── Loop Engineering：心跳 / 状态 / gate ─────────────
# A+B loop —— Apple 是真源，loop 让"同步 + 周报"被持续调度、验证、记录。
# 设计原则（对抗 Ralph Wiggum failing-quietly）：
#   1. A+B 是确定性机械操作 → gate = 结构性断言，不用 maker/checker
#   2. cron 模型天然 hard-stop：每次 fire = 一次有界单跑，无 runaway
#   3. 失败必须显式上报（osascript 通知 + last_error 落盘），不 silent
#   4. 幂等：sync 重跑产同样 tasks.json；report 重跑覆盖同文件

LOOP_STATE_FILE = DATA_DIR / "loop-state.json"
LOOP_HISTORY_MAX = 30  # history 滚动保留条数


def load_loop_state() -> dict:
    """加载 loop 状态，不存在则返回初始结构。"""
    ensure_data_dir()
    if not LOOP_STATE_FILE.exists():
        return {
            "schema": 1,
            "last_sync_at": None,
            "last_sync_ok": None,
            "last_sync_summary": None,
            "last_report_at": None,
            "last_report_path": None,
            "last_report_ok": None,
            "last_error": None,
            "tick_count": 0,
            "history": [],
        }
    try:
        return json.loads(LOOP_STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return {"schema": 1, "tick_count": 0, "history": [], "last_error": None}


def save_loop_state(state: dict):
    """原子写入 loop 状态。"""
    ensure_data_dir()
    tmp = LOOP_STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(LOOP_STATE_FILE)


def _notify(title: str, message: str, sound: str = "Basso"):
    """通过 osascript 弹 macOS 通知。失败不抛（通知通道本身不该让 loop 崩）。"""
    # 转义双引号，避免 AppleScript 语法破裂
    t = title.replace('"', '\\"')
    m = message.replace('"', '\\"')
    script = f'display notification "{m}" with title "{t}" sound name "{sound}"'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=15)
    except Exception:
        pass


def _append_history(state: dict, mode: str, ok: bool, note: str, now_iso: str):
    """追加一条 history 并滚动到最多 LOOP_HISTORY_MAX 条。"""
    state.setdefault("history", [])
    state["history"].append({"at": now_iso, "mode": mode, "ok": ok, "note": note})
    if len(state["history"]) > LOOP_HISTORY_MAX:
        state["history"] = state["history"][-LOOP_HISTORY_MAX:]


def _gate_tasks_json_valid() -> bool:
    """gate：tasks.json 能被 json.load 解析（数据未损坏）。"""
    try:
        json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        return True
    except (json.JSONDecodeError, FileNotFoundError):
        return False


def _gate_report_file(filepath: Path) -> tuple:
    """gate：报告文件存在 + size>800 + 含必需段落。返回 (ok, reason)。"""
    if not filepath.exists():
        return False, "报告文件不存在"
    text = filepath.read_text(encoding="utf-8")
    if len(text.encode("utf-8")) <= 800:
        return False, f"报告文件过小（{len(text.encode('utf-8'))} bytes）"
    if "统计周期" not in text:
        return False, "报告缺『统计周期』段"
    if "重点项目进展与待办" not in text:
        return False, "报告缺『重点项目进展与待办』段"
    return True, ""


def run_loop_tick(mode: str) -> int:
    """
    loop 心跳。mode='daily' 跑 sync；mode='weekly' 跑 sync + 周报。
    返回 exit code（0 成功，1 失败）。所有结果写入 loop-state.json。
    """
    state = load_loop_state()
    now_iso = datetime.now(timezone.utc).astimezone().isoformat()
    state["tick_count"] = state.get("tick_count", 0) + 1

    # ── weekly 前置检查：output_dir 必须先配好，否则 fail fast，不浪费一次昂贵的 sync ──
    if mode == "weekly":
        config = load_config()
        output_dir = config.get("weekly_report", {}).get("output_dir", "")
        if not output_dir:
            msg = "weekly_report.output_dir 未配置，无法写周报文件"
            state["last_report_ok"] = False
            state["last_error"] = {"at": now_iso, "mode": "weekly", "message": msg}
            _append_history(state, "weekly", False, msg, now_iso)
            save_loop_state(state)
            _notify("smart-calendar loop", msg)
            print(f"LOOP_TICK_FAILED|{msg}")
            return 1

    # ── daily：sync（weekly 也先跑 sync 拿最新数据）──
    try:
        summary = sync_tasks_from_apple(dry_run=False)
    except Exception as e:
        msg = f"sync 异常: {e}"
        state["last_sync_ok"] = False
        state["last_error"] = {"at": now_iso, "mode": mode, "message": msg}
        _append_history(state, mode, False, msg, now_iso)
        save_loop_state(state)
        _notify("smart-calendar loop", msg)
        print(f"LOOP_TICK_FAILED|{msg}")
        return 1

    if not _gate_tasks_json_valid():
        msg = "sync 后 tasks.json 解析失败（数据可能损坏）"
        state["last_sync_ok"] = False
        state["last_error"] = {"at": now_iso, "mode": mode, "message": msg}
        _append_history(state, mode, False, msg, now_iso)
        save_loop_state(state)
        _notify("smart-calendar loop", msg)
        print(f"LOOP_TICK_FAILED|{msg}")
        return 1

    state["last_sync_at"] = now_iso
    state["last_sync_ok"] = True
    state["last_sync_summary"] = {
        "reminders": summary.get("scanned_reminders", 0),
        "events": summary.get("scanned_events", 0),
        "tasks": summary.get("new_task_count", 0),
    }
    state["last_error"] = None

    if mode == "daily":
        note = f"synced {summary.get('new_task_count', 0)} tasks"
        _append_history(state, "daily", True, note, now_iso)
        save_loop_state(state)
        print(f"LOOP_TICK_OK|daily|{note}")
        return 0

    # ── weekly：在 sync 之上再出周报（output_dir 已在函数开头校验过）──
    output_dir = load_config().get("weekly_report", {}).get("output_dir", "")
    try:
        generate_weekly_report(output_path=Path(output_dir))
    except Exception as e:
        msg = f"周报生成异常: {e}"
        state["last_report_ok"] = False
        state["last_error"] = {"at": now_iso, "mode": "weekly", "message": msg}
        _append_history(state, "weekly", False, msg, now_iso)
        save_loop_state(state)
        _notify("smart-calendar loop", msg)
        print(f"LOOP_TICK_FAILED|{msg}")
        return 1

    # 用 week_end_date 定位刚写出的报告文件（文件名含「（YYYY-MM-DD）」）
    _, week_end_dt, _, _ = _get_report_week_range()
    week_end_date = week_end_dt.strftime("%Y-%m-%d")
    candidates = sorted(Path(output_dir).glob(f"*（{week_end_date}）.md"))
    if not candidates:
        msg = f"周报已生成但找不到 *（{week_end_date}）.md 文件"
        state["last_report_ok"] = False
        state["last_error"] = {"at": now_iso, "mode": "weekly", "message": msg}
        _append_history(state, "weekly", False, msg, now_iso)
        save_loop_state(state)
        _notify("smart-calendar loop", msg)
        print(f"LOOP_TICK_FAILED|{msg}")
        return 1

    report_path = candidates[-1]
    ok, reason = _gate_report_file(report_path)
    if not ok:
        state["last_report_ok"] = False
        state["last_error"] = {"at": now_iso, "mode": "weekly", "message": reason}
        _append_history(state, "weekly", False, reason, now_iso)
        save_loop_state(state)
        _notify("smart-calendar loop", f"周报 gate 失败: {reason}")
        print(f"LOOP_TICK_FAILED|{reason}")
        return 1

    state["last_report_at"] = now_iso
    state["last_report_path"] = str(report_path)
    state["last_report_ok"] = True
    note = f"report → {report_path.name}"
    _append_history(state, "weekly", True, note, now_iso)
    save_loop_state(state)
    _notify("smart-calendar loop", f"周报已生成：{report_path.name}", sound="Glass")
    print(f"LOOP_TICK_OK|weekly|{note}")
    return 0


# ── CLI 入口 ──────────────────────────────────────

def _build_meta_from_args(args) -> dict:
    """从 --meta-* 命令行参数构造 metadata dict。空字段不包含。"""
    meta = {}
    if getattr(args, "meta_project", ""):
        meta["project"] = args.meta_project
    if getattr(args, "meta_task_type", ""):
        meta["task_type"] = args.meta_task_type
    aux_str = getattr(args, "meta_aux_tags", "")
    if aux_str:
        meta["aux_tags"] = [t.strip() for t in aux_str.split(",") if t.strip()]
    if getattr(args, "meta_formal_title", ""):
        meta["formal_title"] = args.meta_formal_title
    return meta


def main():
    parser = argparse.ArgumentParser(description="smart-calendar task manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # create-event
    p_event = subparsers.add_parser("create-event", help="Create calendar event")
    p_event.add_argument("--title", required=True)
    p_event.add_argument("--calendar", default=None, help="覆盖默认日历；不给则按 --tag-major 选")
    p_event.add_argument("--tag-major", choices=["work", "life", "工作", "生活"], default="work",
                         help="主标签 → 决定写入哪个日历（默认 work）")
    p_event.add_argument("--start", required=True, help="YYYY-MM-DD HH:MM")
    p_event.add_argument("--end", required=True, help="YYYY-MM-DD HH:MM")
    p_event.add_argument("--notes", default="")
    p_event.add_argument("--location", default="")
    # 方向 B：metadata block 字段
    p_event.add_argument("--meta-project", default="", help="metadata: project")
    p_event.add_argument("--meta-task-type", default="", help="metadata: task_type")
    p_event.add_argument("--meta-aux-tags", default="", help="metadata: 次标签，逗号分隔")
    p_event.add_argument("--meta-formal-title", default="", help="metadata: formal_title")

    # create-reminder
    p_rem = subparsers.add_parser("create-reminder", help="Create reminder")
    p_rem.add_argument("--title", required=True)
    p_rem.add_argument("--list", default=None, dest="list_name",
                       help="覆盖默认列表；不给则按 --tag-major 选")
    p_rem.add_argument("--tag-major", choices=["work", "life", "工作", "生活"], default="work",
                       help="主标签 → 决定写入哪个列表（默认 work）")
    p_rem.add_argument("--due", help="YYYY-MM-DD or YYYY-MM-DD HH:MM")
    p_rem.add_argument("--notes", default="")
    p_rem.add_argument("--priority", type=int, default=0, choices=[0, 1, 2, 3])
    # 方向 B：metadata block 字段
    p_rem.add_argument("--meta-project", default="", help="metadata: project")
    p_rem.add_argument("--meta-task-type", default="", help="metadata: task_type")
    p_rem.add_argument("--meta-aux-tags", default="", help="metadata: 次标签，逗号分隔")
    p_rem.add_argument("--meta-formal-title", default="", help="metadata: formal_title")

    # check-conflict
    p_conflict = subparsers.add_parser("check-conflict", help="Check time conflicts")
    p_conflict.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_conflict.add_argument("--time", help="HH:MM")
    p_conflict.add_argument("--duration", type=int, default=60)

    # save-task
    p_save = subparsers.add_parser("save-task", help="Save task metadata")
    p_save.add_argument("--task-id", required=True)
    p_save.add_argument("--user-input", default="")
    p_save.add_argument("--parsed-json", default="{}")
    p_save.add_argument("--formal-title", default="")
    p_save.add_argument("--formal-notes", default="")
    p_save.add_argument("--calendar-event-id", default=None)
    p_save.add_argument("--reminder-id", default=None)
    p_save.add_argument("--project", default="")
    p_save.add_argument("--task-type", default="")
    # 方向 B：主标签优先用 --major-tag（work/life/工作/生活），次标签用 --aux-tags
    p_save.add_argument("--major-tag", choices=["work", "life", "工作", "生活", ""], default="",
                        help="主标签 — 建议明确指定")
    p_save.add_argument("--aux-tags", default="", help="次标签（紧急、待审等），逗号分隔")
    # 兼容旧接口：--tags 仍可用，但建议改用 --major-tag + --aux-tags
    p_save.add_argument("--tags", default="", help="[兼容旧接口] 全部标签 — 建议改用 --major-tag + --aux-tags")

    # search
    p_search = subparsers.add_parser("search", help="Search tasks by keyword")
    p_search.add_argument("keyword")

    # update
    p_update = subparsers.add_parser("update", help="Update task field")
    p_update.add_argument("--task-id", required=True)
    p_update.add_argument("--field", required=True)
    p_update.add_argument("--value", required=True)

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete task")
    p_delete.add_argument("--task-id", required=True)

    # list-recent
    p_list = subparsers.add_parser("list-recent", help="List recent tasks")
    p_list.add_argument("--limit", type=int, default=10)

    # weekly-report
    p_report = subparsers.add_parser("weekly-report", help="Generate weekly report")
    p_report.add_argument("--output-dir", default="", help="Output directory for report file")

    # list-calendars
    subparsers.add_parser("list-calendars", help="List available calendars")

    # list-reminder-lists
    subparsers.add_parser("list-reminder-lists", help="List reminder lists")

    # tag management
    subparsers.add_parser("list-tags", help="List all tags")
    p_add_tag = subparsers.add_parser("add-tag", help="Add a new tag")
    p_add_tag.add_argument("tag")
    p_remove_tag = subparsers.add_parser("remove-tag", help="Remove a tag")
    p_remove_tag.add_argument("tag")
    p_set_tags = subparsers.add_parser("set-task-tags", help="Set tags for a task")
    p_set_tags.add_argument("--task-id", required=True)
    p_set_tags.add_argument("--tags", required=True, help="Comma-separated tags")

    # sync — 方向 B：从 Apple 真源重建 tasks.json
    p_sync = subparsers.add_parser("sync", help="Rebuild tasks.json from Apple Calendar/Reminders")
    p_sync.add_argument("--months-back", type=int, default=6)
    p_sync.add_argument("--months-forward", type=int, default=3)
    p_sync.add_argument("--dry-run", action="store_true", help="只 print 不写盘")

    # loop-tick — Loop Engineering 心跳（daily sync / weekly sync+report）
    p_loop = subparsers.add_parser("loop-tick", help="Loop heartbeat: daily sync or weekly sync+report")
    p_loop.add_argument("--mode", choices=["daily", "weekly"], default="daily",
                        help="daily=仅 sync；weekly=sync + 生成周报")

    # loop-status — 查看 loop 状态
    subparsers.add_parser("loop-status", help="Show loop-state.json")

    # config management
    subparsers.add_parser("get-config", help="Show current config")
    p_set_config = subparsers.add_parser("set-config", help="Set config value")
    p_set_config.add_argument("--key", required=True, help="Config key (e.g. weekly_report.enabled)")
    p_set_config.add_argument("--value", required=True)

    args = parser.parse_args()

    if args.command == "create-event":
        major = normalize_tag(args.tag_major)  # work → 工作
        calendar = args.calendar or target_calendar_for_major_tag(major)
        meta = _build_meta_from_args(args)
        uid = create_calendar_event(args.title, args.start, args.end,
                                    calendar, args.notes, args.location,
                                    metadata=meta or None)
        print(f"EVENT_CREATED|{uid}|calendar={calendar}|major={major}")

    elif args.command == "create-reminder":
        major = normalize_tag(args.tag_major)
        list_name = args.list_name or target_list_for_major_tag(major)
        meta = _build_meta_from_args(args)
        result = create_reminder(args.title, args.due, list_name, args.notes, args.priority,
                                 metadata=meta or None)
        print(f"REMINDER_CREATED|{result}|list={list_name}|major={major}")

    elif args.command == "check-conflict":
        conflicts = check_conflict(args.date, args.time, args.duration)
        if conflicts:
            print("CONFLICTS_FOUND")
            for c in conflicts:
                print(f"  - {c['title']} ({c['start']} - {c['end']})")
        else:
            print("NO_CONFLICTS")

    elif args.command == "save-task":
        # 标签构造：优先用 --major-tag + --aux-tags；旧 --tags 作为兜底。
        tags = []
        if args.major_tag:
            tags.append(normalize_tag(args.major_tag))
        if args.aux_tags:
            tags.extend(t.strip() for t in args.aux_tags.split(",") if t.strip())
        if not tags and args.tags:  # 兼容旧接口
            tags = [t.strip() for t in args.tags.split(",") if t.strip()]

        task_data = {
            "user_input": args.user_input,
            "parsed": json.loads(args.parsed_json),
            "formal_title": args.formal_title,
            "formal_notes": args.formal_notes,
            "calendar_event_id": args.calendar_event_id,
            "reminder_id": args.reminder_id,
            "tags": tags,
        }
        if args.project:
            task_data["parsed"]["project"] = args.project
        if args.task_type:
            task_data["parsed"]["task_type"] = args.task_type

        tid = add_task(task_data)
        print(f"TASK_SAVED|{tid}")

    elif args.command == "search":
        results = search_tasks(args.keyword)
        print(f"FOUND {len(results)} TASKS")
        for r in results:
            tags_str = f" [{','.join(r.get('tags', []))}]" if r.get('tags') else ""
            print(f"  [{r['task_id'][:8]}] {r.get('formal_title') or r.get('parsed', {}).get('title', '无标题')}{tags_str} (status: {r.get('status')})")

    elif args.command == "update":
        ok = update_task_field(args.task_id, args.field, args.value)
        print(f"UPDATE_{'OK' if ok else 'FAILED'}")

    elif args.command == "delete":
        ok = delete_task(args.task_id)
        print(f"DELETE_{'OK' if ok else 'FAILED'}")

    elif args.command == "list-recent":
        tasks = get_recent_tasks(args.limit)
        print(f"RECENT {len(tasks)} TASKS")
        for t in tasks:
            tags_str = f" [{','.join(t.get('tags', []))}]" if t.get('tags') else ""
            print(f"  [{t['task_id'][:8]}] {t.get('formal_title') or t.get('parsed', {}).get('title', '无标题')}{tags_str} (created: {t['created_at'][:10]})")

    elif args.command == "weekly-report":
        output_dir = args.output_dir if args.output_dir else None
        report = generate_weekly_report(output_path=Path(output_dir) if output_dir else None)
        if not output_dir:
            print(report)

    elif args.command == "list-calendars":
        cals = list_calendars()
        print("CALENDARS:")
        for c in cals:
            print(f"  - {c}")

    elif args.command == "list-reminder-lists":
        lists = list_reminder_lists()
        print("REMINDER_LISTS:")
        for lst in lists:
            print(f"  - {lst}")

    elif args.command == "list-tags":
        tags = get_tags()
        print("TAGS:")
        for tag in tags:
            print(f"  - {tag}")

    elif args.command == "add-tag":
        ok = add_tag(args.tag)
        print(f"TAG_{'ADDED' if ok else 'EXISTS'}")

    elif args.command == "remove-tag":
        ok = remove_tag(args.tag)
        print(f"TAG_{'REMOVED' if ok else 'NOT_FOUND'}")

    elif args.command == "set-task-tags":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        ok = set_task_tags(args.task_id, tags)
        print(f"TAGS_{'SET' if ok else 'FAILED'}")

    elif args.command == "sync":
        summary = sync_tasks_from_apple(
            months_back=args.months_back,
            months_forward=args.months_forward,
            dry_run=args.dry_run,
        )
        print(f"SYNC_{'DRY_RUN' if args.dry_run else 'DONE'}")
        for k, v in summary.items():
            print(f"  {k}: {v}")

    elif args.command == "loop-tick":
        code = run_loop_tick(args.mode)
        raise SystemExit(code)

    elif args.command == "loop-status":
        state = load_loop_state()
        print(json.dumps(state, ensure_ascii=False, indent=2))

    elif args.command == "get-config":
        config = load_config()
        print(json.dumps(config, ensure_ascii=False, indent=2))

    elif args.command == "set-config":
        config = load_config()
        keys = args.key.split(".")
        target = config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        # 尝试解析为布尔值/整数
        val = args.value
        if val.lower() in ("true", "false"):
            val = val.lower() == "true"
        else:
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    pass
        target[keys[-1]] = val
        save_config(config)
        print("CONFIG_UPDATED")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
