#!/usr/bin/env python3
"""
smart-calendar 冒烟测试
覆盖：列出日历/提醒列表、创建/更新/删除、冲突检测、搜索、标签管理、配置、周报生成

⚠️ 重要：本测试默认使用隔离的临时数据目录（通过 SMART_CALENDAR_DATA_DIR 注入），
不会污染你的真实 ~/.smart-calendar/ 配置和任务库。
如需指向生产数据跑（极少场景），手动 export SMART_CALENDAR_DATA_DIR= 取消隔离。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT = Path("~/.claude/skills/smart-calendar/scripts/task_manager.py").expanduser()
TEST_PREFIX = "【冒烟测试】"

# 远期测试日期：今天 + 5 年。比硬编码 2099 健壮（迁移到未来不会突然失效）
_FUTURE_DATE = (datetime.now() + timedelta(days=365 * 5)).strftime("%Y-%m-%d")

# 隔离的临时数据目录，跑完测试销毁。所有子进程通过 _ENV 继承。
_ISOLATED_DATA_DIR = Path(tempfile.mkdtemp(prefix="sc-smoke-"))
_ENV = {**os.environ, "SMART_CALENDAR_DATA_DIR": str(_ISOLATED_DATA_DIR)}

pass_count = 0
fail_count = 0
errors = []


def run(cmd_args: list) -> tuple:
    """运行 task_manager.py 命令，返回 (stdout, stderr, returncode)。
    timeout 240s — sync 命令在用户已有大量日历事件时可能跑 ~1 分钟，留充足缓冲。"""
    result = subprocess.run(
        ["python3", str(SCRIPT)] + cmd_args,
        env=_ENV,
        capture_output=True,
        text=True,
        timeout=240
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def check(name: str, condition: bool, detail: str = ""):
    """断言并记录结果"""
    global pass_count, fail_count
    if condition:
        pass_count += 1
        print(f"  ✅ {name}")
    else:
        fail_count += 1
        msg = f"❌ {name}"
        if detail:
            msg += f" | {detail}"
        print(f"  {msg}")
        errors.append(msg)


def test_list_calendars():
    print("\n[Test] 列出日历")
    out, err, rc = run(["list-calendars"])
    check("命令成功执行", rc == 0, err)
    check("输出包含 CALENDARS", "CALENDARS:" in out, out[:200])
    # v4.0：默认假设有「工作」日历（setup-lists-and-calendars.md 引导用户建好）
    check("包含「工作」日历", "工作" in out, out[:500])


def test_list_reminder_lists():
    print("\n[Test] 列出提醒列表")
    out, err, rc = run(["list-reminder-lists"])
    check("命令成功执行", rc == 0, err)
    check("输出包含 REMINDER_LISTS", "REMINDER_LISTS:" in out, out[:200])


def test_create_reminder():
    print("\n[Test] 创建提醒事项（v4.0：默认路由到「工作」列表）")
    global test_reminder_id
    title = f"{TEST_PREFIX} 测试提醒-{uuid.uuid4().hex[:6]}"
    # 不指定 --list，让 --tag-major 默认（work）自动选「工作」
    out, err, rc = run([
        "create-reminder",
        "--title", title,
        "--tag-major", "work",
        "--due", f"{_FUTURE_DATE} 23:59",
        "--notes", "冒烟测试备注",
        "--priority", "2"
    ])
    check("命令成功执行", rc == 0, err)
    check("输出包含 REMINDER_CREATED", "REMINDER_CREATED" in out, out)
    check("路由到「工作」", "list=工作" in out, out)
    # 提取 reminder id
    if "|" in out:
        parts = out.split("|")
        if len(parts) >= 2:
            test_reminder_id = parts[1]
    return test_reminder_id


def test_create_event():
    print("\n[Test] 创建日历事件（v4.0：默认路由到「工作」日历）")
    global test_event_id
    title = f"{TEST_PREFIX} 测试会议-{uuid.uuid4().hex[:6]}"
    # 不指定 --calendar，让 --tag-major 默认（work）自动选「工作」日历
    out, err, rc = run([
        "create-event",
        "--title", title,
        "--tag-major", "work",
        "--start", f"{_FUTURE_DATE} 10:00",
        "--end", f"{_FUTURE_DATE} 11:00",
        "--notes", "冒烟测试日历事件"
    ])
    check("命令成功执行", rc == 0, err)
    check("输出包含 EVENT_CREATED", "EVENT_CREATED" in out, out)
    check("路由到「工作」", "calendar=工作" in out, out)
    # v4 输出格式: EVENT_CREATED|<uid>|calendar=工作|major=工作 —— uid 是第 2 个字段
    if "|" in out:
        parts = out.split("|")
        if len(parts) >= 2:
            test_event_id = parts[1]
    return test_event_id


def test_save_task_with_tags():
    print("\n[Test] 保存任务（含标签）到数据库")
    global test_task_id
    parsed = json.dumps({
        "title": "冒烟测试任务",
        "task_type": "文件审阅",
        "project": "测试项目",
        "deadline_date": _FUTURE_DATE,
        "deadline_time": "23:59",
        "priority": "中",
        "related_people": ["测试人员"],
        "notes": "测试备注"
    }, ensure_ascii=False)

    out, err, rc = run([
        "save-task",
        "--task-id", f"smoke-{uuid.uuid4().hex[:8]}",
        "--user-input", "测试输入",
        "--parsed-json", parsed,
        "--formal-title", "冒烟测试正式标题",
        "--formal-notes", "冒烟测试正式备注",
        "--reminder-id", test_reminder_id or "",
        "--calendar-event-id", test_event_id or "",
        "--project", "测试项目",
        "--task-type", "文件审阅",
        "--tags", "工作,紧急"
    ])
    check("命令成功执行", rc == 0, err)
    check("输出包含 TASK_SAVED", "TASK_SAVED" in out, out)
    if "TASK_SAVED|" in out:
        test_task_id = out.split("|")[-1]
    return test_task_id


def test_list_tags():
    print("\n[Test] 列出标签")
    out, err, rc = run(["list-tags"])
    check("命令成功执行", rc == 0, err)
    check("包含默认标签", "工作" in out and "生活" in out, out)


def test_add_tag():
    print("\n[Test] 添加自定义标签")
    out, err, rc = run(["add-tag", "冒烟测试标签"])
    check("命令成功执行", rc == 0, err)
    check("标签添加成功", "TAG_ADDED" in out or "TAG_EXISTS" in out, out)


def test_set_task_tags():
    print("\n[Test] 修改任务标签")
    if not test_task_id:
        print("  ⏭️ 跳过（无 task_id）")
        return
    out, err, rc = run([
        "set-task-tags",
        "--task-id", test_task_id,
        "--tags", "工作,冒烟测试标签"
    ])
    check("命令成功执行", rc == 0, err)
    check("标签设置成功", "TAGS_SET" in out, out)


def test_config_management():
    print("\n[Test] 配置管理")
    # get-config
    out, err, rc = run(["get-config"])
    check("get-config 成功", rc == 0, err)
    check("配置包含标签", "tags" in out, out[:200])
    check("配置包含周报设置", "weekly_report" in out, out[:200])

    # set-config
    out, err, rc = run(["set-config", "--key", "weekly_report.enabled", "--value", "true"])
    check("set-config 成功", rc == 0, err)
    check("配置更新确认", "CONFIG_UPDATED" in out, out)

    # verify
    out, err, rc = run(["get-config"])
    config = json.loads(out)
    check("配置值正确", config.get("weekly_report", {}).get("enabled") is True, out)


def test_conflict_detection():
    print("\n[Test] 冲突检测")
    out, err, rc = run([
        "check-conflict",
        "--date", _FUTURE_DATE,
        "--time", "10:00",
        "--duration", "60"
    ])
    check("命令成功执行", rc == 0, err)
    check("检测到冲突", "CONFLICTS_FOUND" in out, out)


def test_search_task():
    print("\n[Test] 搜索任务")
    out, err, rc = run(["search", "冒烟测试"])
    check("命令成功执行", rc == 0, err)
    check("找到任务", "FOUND" in out and "冒烟测试" in out, out)


def test_list_recent():
    print("\n[Test] 列出最近任务")
    out, err, rc = run(["list-recent", "--limit", "5"])
    check("命令成功执行", rc == 0, err)
    check("输出包含 RECENT", "RECENT" in out, out)


def test_weekly_report_console():
    """测试默认配置下的周报结构（不依赖特定 report_title 字面值）"""
    print("\n[Test] 周报生成（控制台输出，结构检查）")
    out, err, rc = run(["weekly-report"])
    check("命令成功执行", rc == 0, err)
    # 结构性断言：不耦合具体 team_name / report_title 字面值
    check("含 H1 标题", out.lstrip().startswith("# "), out[:200])
    check("H1 含日期戳", any(line.startswith("# ") and "（20" in line for line in out.split("\n")[:5]), out[:200])
    check("含统计周期", "统计周期" in out, out[:500])
    check("含本周概览", "本周概览" in out, out[:500])
    check("含重点项目进展与待办", "重点项目进展与待办" in out, out[:500])


def test_weekly_report_team_name_concat():
    """独立覆盖 team_name + report_title 拼接逻辑，用明显的测试值与生产配置解耦"""
    print("\n[Test] 周报 team_name 拼接")
    # 先记录默认值方便还原（实际不需要还原 — 隔离目录 finally 会整体销毁）
    run(["set-config", "--key", "weekly_report.team_name", "--value", "SMOKE_TEAM"])
    run(["set-config", "--key", "weekly_report.report_title", "--value", "SMOKE_REPORT"])
    out, err, rc = run(["weekly-report"])
    check("命令成功执行", rc == 0, err)
    check("H1 含 SMOKE_TEAMSMOKE_REPORT（拼接）", "SMOKE_TEAMSMOKE_REPORT" in out, out[:200])
    # 还原成默认值，避免影响 test_weekly_report_file 的文件名
    run(["set-config", "--key", "weekly_report.team_name", "--value", ""])
    run(["set-config", "--key", "weekly_report.report_title", "--value", "个人工作周报"])


def test_weekly_report_file():
    print("\n[Test] 周报生成（文件输出）")
    tmp_dir = _ISOLATED_DATA_DIR / "test_reports"
    out, err, rc = run(["weekly-report", "--output-dir", str(tmp_dir)])
    check("命令成功执行", rc == 0, err)
    check("文件已写入", "REPORT_WRITTEN" in out, out)
    # 隔离目录在主流程 finally 里整体清理，无需单独处理


def test_weekly_report_rejects_git_repo():
    print("\n[Test] 周报拒绝写入 Git repo")
    repo_dir = _ISOLATED_DATA_DIR / "git_repo"
    (repo_dir / ".git").mkdir(parents=True)
    output_dir = repo_dir / "reports"
    out, err, rc = run(["weekly-report", "--output-dir", str(output_dir)])
    check("命令被拒绝", rc != 0, out)
    check("错误信息明确", "拒绝将周报写入 Git 仓库内" in err, err)
    check("未生成周报文件", not output_dir.exists(), str(output_dir))


def test_metadata_block_round_trip():
    """方向 B：metadata block 序列化 ↔ 解析往返。纯 Python，不调 AppleScript。"""
    print("\n[Test] metadata block 往返（方向 B）")
    # 通过 import 直接调函数，避免起子进程
    import importlib.util
    spec = importlib.util.spec_from_file_location("tm", str(SCRIPT))
    tm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tm)

    # 完整往返
    notes = "正式备注内容"
    meta = {"project": "A 项目", "task_type": "文件审阅",
            "aux_tags": ["紧急", "待审"], "formal_title": "A 项目方案修订"}
    body = tm.serialize_metadata_block(notes, meta)
    parsed_notes, parsed_meta = tm.parse_metadata_block(body)
    check("user_notes 一致", parsed_notes == notes, repr(parsed_notes))
    check("project 一致", parsed_meta.get("project") == "A 项目", str(parsed_meta))
    check("task_type 一致", parsed_meta.get("task_type") == "文件审阅", str(parsed_meta))
    check("aux_tags 一致", parsed_meta.get("aux_tags") == ["紧急", "待审"], str(parsed_meta))
    check("formal_title 一致", parsed_meta.get("formal_title") == "A 项目方案修订", str(parsed_meta))

    # 无 metadata block 容错（iPhone 手动加的任务）
    parsed_notes, parsed_meta = tm.parse_metadata_block("普通备注")
    check("无 block 时 user_notes 完整", parsed_notes == "普通备注", parsed_notes)
    check("无 block 时 meta 为空", parsed_meta == {}, str(parsed_meta))

    # 主标签推断
    check("「工作」list → 工作", tm.infer_major_tag_from_list("工作") == "工作")
    check("「生活」list → 生活", tm.infer_major_tag_from_list("生活") == "生活")
    check("未知 list → None", tm.infer_major_tag_from_list("提醒事项") is None)
    check("Work 日历 → 工作（兼容）", tm.infer_major_tag_from_calendar("Work") == "工作")
    check("「工作」日历 → 工作", tm.infer_major_tag_from_calendar("工作") == "工作")
    check("「生活」日历 → 生活", tm.infer_major_tag_from_calendar("生活") == "生活")


def test_loop_state_and_gate():
    """Loop Engineering：loop-state 读写 + gate + history 滚动。纯 Python，不调 AppleScript。"""
    print("\n[Test] loop-state + gate（Loop Engineering）")
    import importlib.util
    spec = importlib.util.spec_from_file_location("tm_loop", str(SCRIPT))
    tm = importlib.util.module_from_spec(spec)
    # 关键：让被测模块也用隔离目录（继承 _ENV 里的 SMART_CALENDAR_DATA_DIR）
    os.environ["SMART_CALENDAR_DATA_DIR"] = str(_ISOLATED_DATA_DIR)
    spec.loader.exec_module(tm)
    from pathlib import Path as _P

    # 初始 state 结构
    st = tm.load_loop_state()
    check("初始 schema=1", st.get("schema") == 1, str(st))
    check("初始 tick_count=0", st.get("tick_count") == 0, str(st))
    check("初始 history 空", st.get("history") == [], str(st))

    # tasks.json valid gate
    tm.ensure_data_dir()
    tm.save_tasks([{"task_id": "x"}])
    check("gate: tasks.json 合法→True", tm._gate_tasks_json_valid() is True)
    tm.TASKS_FILE.write_text("{ broken", encoding="utf-8")
    check("gate: tasks.json 损坏→False", tm._gate_tasks_json_valid() is False)
    tm.save_tasks([])  # 复原

    # report file gate
    d = _P(tm.DATA_DIR)
    check("gate: 报告不存在→False", tm._gate_report_file(d / "nope.md")[0] is False)
    small = d / "g_small.md"; small.write_text("# tiny", encoding="utf-8")
    check("gate: 报告过小→False", tm._gate_report_file(small)[0] is False)
    good = d / "g_good.md"
    good.write_text("# 周报\n**统计周期**：a~b\n## 二、重点项目进展与待办\n" + "占位" * 300, encoding="utf-8")
    ok, reason = tm._gate_report_file(good)
    check("gate: 合格报告→True", ok is True, reason)

    # history 滚动到 LOOP_HISTORY_MAX
    st = tm.load_loop_state()
    for i in range(tm.LOOP_HISTORY_MAX + 5):
        tm._append_history(st, "daily", True, f"n{i}", f"2026-01-{i:02d}")
    check(f"history 滚动到 {tm.LOOP_HISTORY_MAX}", len(st["history"]) == tm.LOOP_HISTORY_MAX, str(len(st["history"])))
    check("history 保留最新", st["history"][-1]["note"] == f"n{tm.LOOP_HISTORY_MAX + 4}")

    # state 持久化往返
    st["last_sync_at"] = "2026-06-16T18:00:00+08:00"
    tm.save_loop_state(st)
    st2 = tm.load_loop_state()
    check("state 持久化往返", st2["last_sync_at"] == "2026-06-16T18:00:00+08:00")


def test_loop_tick_daily():
    """Loop Engineering：真跑 loop-tick --mode daily（会调 Apple sync）。"""
    print("\n[Test] loop-tick --mode daily（真 sync）")
    out, err, rc = run(["loop-tick", "--mode", "daily"])
    check("命令成功执行 exit 0", rc == 0, err or out)
    check("输出含 LOOP_TICK_OK|daily", "LOOP_TICK_OK|daily" in out, out)
    # loop-status 验证 state 落盘
    out2, err2, rc2 = run(["loop-status"])
    check("loop-status 成功", rc2 == 0, err2)
    state = json.loads(out2)
    check("last_sync_ok=True", state.get("last_sync_ok") is True, out2[:300])
    check("tick_count 已自增", state.get("tick_count", 0) >= 1, str(state.get("tick_count")))
    check("history 有 daily 记录", any(h.get("mode") == "daily" and h.get("ok") for h in state.get("history", [])), out2[:300])


def test_loop_tick_weekly_failure_gate():
    """Loop Engineering：weekly 但 output_dir 为空 → gate 应拦截 + exit 1 + last_error 落盘。"""
    print("\n[Test] loop-tick weekly gate 失败路径")
    # 临时清空 output_dir 触发失败分支
    run(["set-config", "--key", "weekly_report.output_dir", "--value", ""])
    out, err, rc = run(["loop-tick", "--mode", "weekly"])
    check("gate 失败 exit 1", rc == 1, f"rc={rc} out={out}")
    check("输出含 LOOP_TICK_FAILED", "LOOP_TICK_FAILED" in out, out)
    out2, _, _ = run(["loop-status"])
    state = json.loads(out2)
    check("last_error 已落盘", state.get("last_error") is not None, out2[:300])
    check("sync 成功但 report 失败（精确区分）",
          state.get("last_sync_ok") is True and state.get("last_report_ok") is False, out2[:300])


def test_create_reminder_with_metadata():
    """方向 B：create-reminder 用 --tag-major 路由 + 写 metadata block。会真创建 Apple 端 reminder。"""
    print("\n[Test] create-reminder 含 metadata block（写到「工作」列表）")
    global test_meta_reminder_id
    title = f"{TEST_PREFIX} 方向B测试-{uuid.uuid4().hex[:6]}"
    out, err, rc = run([
        "create-reminder",
        "--title", title,
        "--tag-major", "work",
        "--due", f"{_FUTURE_DATE} 23:59",
        "--notes", "测试备注",
        "--meta-project", "SMOKE_PROJ",
        "--meta-task-type", "测试",
        "--meta-aux-tags", "smoke,direction-b",
        "--meta-formal-title", "SMOKE 正式标题",
    ])
    check("命令成功执行", rc == 0, err)
    check("含 REMINDER_CREATED", "REMINDER_CREATED" in out, out)
    check("路由到「工作」列表", "list=工作" in out, out)
    check("主标签 = 工作", "major=工作" in out, out)
    # 抽取 reminder_id 备清理用
    if "|" in out:
        # 格式: REMINDER_CREATED|<id>|name|list=工作|major=工作
        for piece in out.split("|"):
            if piece.startswith("x-apple-reminder://"):
                test_meta_reminder_id = piece
                break


def test_sync_and_parse():
    """方向 B：sync 从 Apple 拉回测试 reminder，验证 metadata block 被正确解析。"""
    print("\n[Test] sync 从 Apple 真源重建 tasks.json")
    if not test_meta_reminder_id:
        print("  ⏭️ 跳过（无 test_meta_reminder_id）")
        return
    # 跑 sync —— 跨月窗口够大保证覆盖测试 reminder
    out, err, rc = run(["sync", "--months-back", "1", "--months-forward", "1"])
    check("sync 成功", rc == 0, err)
    check("含 SYNC_DONE", "SYNC_DONE" in out, out)

    # 读 tasks.json 验证测试 reminder 被收录 + metadata 被解析
    tasks_file = _ISOLATED_DATA_DIR / "tasks.json"
    if not tasks_file.exists():
        check("tasks.json 已写入", False, "文件不存在")
        return
    tasks = json.loads(tasks_file.read_text(encoding="utf-8"))
    test_task = next((t for t in tasks if t.get("reminder_id") == test_meta_reminder_id), None)
    if test_task is None:
        check("找到刚创建的测试 reminder", False, f"扫了 {len(tasks)} 条但没找到")
        return
    check("找到刚创建的测试 reminder", True)
    check("project 从 metadata 还原", test_task.get("parsed", {}).get("project") == "SMOKE_PROJ", str(test_task.get("parsed")))
    check("task_type 从 metadata 还原", test_task.get("parsed", {}).get("task_type") == "测试", str(test_task.get("parsed")))
    check("formal_title 从 metadata 还原", test_task.get("formal_title") == "SMOKE 正式标题", test_task.get("formal_title"))
    check("formal_notes 仅含用户备注（不含 metadata block）", test_task.get("formal_notes") == "测试备注", test_task.get("formal_notes"))
    check("主标签 = 工作（由所在列表推断）", "工作" in test_task.get("tags", []), str(test_task.get("tags")))
    check("aux_tags 合并进 tags", "smoke" in test_task.get("tags", []) and "direction-b" in test_task.get("tags", []), str(test_task.get("tags")))


def cleanup_test_meta_reminder():
    """方向 B 专用清理：删除 metadata 测试 reminder。"""
    print("\n[Cleanup] 删除方向 B 测试 reminder")
    if not test_meta_reminder_id:
        return
    script = f'''
tell application "Reminders"
    repeat with rlist in lists
        try
            repeat with rem in (every reminder of rlist whose id is "{test_meta_reminder_id}")
                delete rem
            end repeat
        end try
    end repeat
    return "ok"
end tell
'''
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=60)
    print("  ✅ 方向 B 测试 reminder 已清理")


def test_update_task():
    print("\n[Test] 更新任务")
    if not test_task_id:
        print("  ⏭️ 跳过（无 task_id）")
        return
    out, err, rc = run([
        "update",
        "--task-id", test_task_id,
        "--field", "status",
        "--value", "completed"
    ])
    check("命令成功执行", rc == 0, err)
    check("更新成功", "UPDATE_OK" in out, out)


def test_delete_task():
    print("\n[Test] 删除任务")
    if not test_task_id:
        print("  ⏭️ 跳过（无 task_id）")
        return
    out, err, rc = run(["delete", "--task-id", test_task_id])
    check("命令成功执行", rc == 0, err)
    check("删除成功", "DELETE_OK" in out, out)


def cleanup_test_reminder():
    """清理测试提醒事项（遍历所有列表 + try 保护，对大库 / 缺失记录更鲁棒）"""
    print("\n[Cleanup] 删除测试提醒事项")
    if not test_reminder_id:
        return
    script = f'''
tell application "Reminders"
    repeat with rlist in lists
        try
            repeat with rem in (every reminder of rlist whose id is "{test_reminder_id}")
                delete rem
            end repeat
        end try
    end repeat
    return "ok"
end tell
'''
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=60)
    print("  ✅ 测试提醒事项已清理")


def cleanup_test_event():
    """清理测试日历事件"""
    print("\n[Cleanup] 删除测试日历事件")
    if not test_event_id:
        return
    script = f'''
tell application "Calendar"
    if not running then launch
    set ev to first event whose uid is "{test_event_id}"
    delete ev
    return "deleted"
end tell
'''
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=30)
    print("  ✅ 测试日历事件已清理")


def cleanup_test_tag():
    """清理测试标签"""
    print("\n[Cleanup] 删除测试标签")
    out, err, rc = run(["remove-tag", "冒烟测试标签"])
    if rc == 0:
        print("  ✅ 测试标签已清理")


# ── 主流程 ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("smart-calendar 冒烟测试")
    print(f"数据目录（隔离）：{_ISOLATED_DATA_DIR}")
    print("=" * 60)

    # 不再主动 set-config 团队 / 标题 — 让测试跑默认值（team_name=""、
    # report_title="个人工作周报"），断言改为结构性，team_name 拼接逻辑由
    # test_weekly_report_team_name_concat 独立覆盖。

    test_reminder_id = None
    test_event_id = None
    test_task_id = None
    test_meta_reminder_id = None  # 方向 B 测试用

    try:
        # Phase 1: 读取
        test_list_calendars()
        test_list_reminder_lists()
        test_list_tags()

        # Phase 2: 创建
        test_reminder_id = test_create_reminder()
        time.sleep(1)
        test_event_id = test_create_event()
        time.sleep(1)

        # Phase 3: 数据持久化 + 标签
        if test_reminder_id and test_event_id:
            test_save_task_with_tags()
        test_add_tag()
        test_set_task_tags()

        # Phase 4: 配置管理
        test_config_management()

        # Phase 5: 查询与检测
        test_conflict_detection()
        test_search_task()
        test_list_recent()

        # Phase 6: 周报
        test_weekly_report_console()
        test_weekly_report_team_name_concat()
        test_weekly_report_file()
        test_weekly_report_rejects_git_repo()

        # Phase 7: 方向 B — Apple 真源 + metadata block + sync
        test_metadata_block_round_trip()
        test_create_reminder_with_metadata()
        test_sync_and_parse()

        # Phase 8: 更新与删除
        test_update_task()
        test_delete_task()

        # Phase 9: Loop Engineering（loop daily 会重建 tasks.json，故放在用到 smoke task_id 的测试之后；
        #          weekly 失败测试会清空 output_dir，放最后）
        test_loop_state_and_gate()
        test_loop_tick_daily()
        test_loop_tick_weekly_failure_gate()

    finally:
        # 清理 Apple 端测试数据（这些会真的写入 Calendar / Reminders.app，必须清）
        cleanup_test_reminder()
        cleanup_test_event()
        cleanup_test_meta_reminder()  # 方向 B 测试 reminder
        cleanup_test_tag()
        # 销毁隔离的数据目录
        shutil.rmtree(_ISOLATED_DATA_DIR, ignore_errors=True)
        print(f"  ✅ 隔离数据目录已清理：{_ISOLATED_DATA_DIR}")

    # 报告
    print("\n" + "=" * 60)
    print(f"测试结果: {pass_count} 通过, {fail_count} 失败")
    print("=" * 60)

    if errors:
        print("\n失败详情:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("\n🎉 所有冒烟测试通过！")
        sys.exit(0)
