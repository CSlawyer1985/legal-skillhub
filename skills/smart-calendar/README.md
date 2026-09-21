**English** · [中文](README.zh-CN.md)

# smart-calendar

An agent skill for macOS that turns spoken-language / screenshot task descriptions into
structured, formal entries in Apple Calendar / Reminders (synced across devices via iCloud),
and auto-generates project-grouped weekly reports.

Apple Calendar / Reminders is the source of truth; the local `tasks.json` is a rebuildable
cache. An optional launchd "loop" runs a daily sync and a Friday report unattended, guarded
by a structural gate and a failure notification.

Built around the [Loop Engineering](https://addyosmani.com/blog/loop-engineering/) pattern:
one automation + one skill + one state file + one structural gate. Pure Python stdlib +
AppleScript, zero third-party dependencies. MIT licensed.

> The skill produces Chinese-language output by default (tags 工作/生活 = work/life, Chinese
> weekly reports). The mechanics are language-agnostic; report titles and tags are configurable.

## Single-machine edition

Each Mac keeps its own local task database (`~/.smart-calendar/tasks.json`). Calendar events and
reminders themselves sync across your Apple devices via iCloud, but this skill's metadata
(formal title / tags / project / task type) does **not** sync across machines. Multi-machine
coordination is out of scope for this edition.

## Install

Drop the whole `smart-calendar/` folder into your agent's skills directory (Claude Code shown):

```bash
cp -r /path/to/smart-calendar ~/.claude/skills/
# or symlink:
ln -s /path/to/smart-calendar ~/.claude/skills/smart-calendar
```

The data directory `~/.smart-calendar/` is created on first run.

## First-run setup

1. **Grant Automation permission.**
   The first AppleScript call against Calendar / Reminders triggers a macOS permission prompt.
   You must allow it, or all writes fail. To re-check later: *System Settings → Privacy &
   Security → Automation* → find your host app (Terminal / iTerm / Claude Code / your agent
   process) → ensure both Calendar and Reminders are checked.

2. **Create the Apple lists / calendars** (required — the skill routes by them):
   ```bash
   # In Reminders.app create two lists: 工作 (work) and 生活 (life)
   # In Calendar.app create two iCloud calendars: 工作 and 生活
   # then verify:
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py list-reminder-lists
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py list-calendars
   ```
   `--tag-major work` routes to the 工作 list/calendar; `life` routes to 生活. To use different
   names, set `work_lists` / `life_lists` / `work_calendars` / `life_calendars` via `set-config`,
   e.g. `set-config --key work_lists --value '["Work"]'`.

3. **Set the weekly-report output directory** (required for file output; otherwise console-only):
   ```bash
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
     --key weekly_report.output_dir --value "/path/to/your/report/folder"
   ```

4. **Configure the report title** (optional):
   ```bash
   # Default title is "个人工作周报" (personal weekly report); no change needed for personal use.
   # For a team prefix (title becomes "{team_name}{report_title}"):
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
     --key weekly_report.team_name --value "Team"
   python3 ~/.claude/skills/smart-calendar/scripts/task_manager.py set-config \
     --key weekly_report.report_title --value "Weekly Report"
   ```

## Verify install

```bash
python3 ~/.claude/skills/smart-calendar/scripts/smoke_test.py
```

The smoke test creates a test reminder and calendar event, runs queries / updates, generates a
sample report, then cleans up. All green = install OK. It uses an isolated temp data dir, so it
will not touch your real config or tasks.

## Trigger examples

Hand the agent free-form input like:

- "Finish the A-project draft and send it to the collaborator by tomorrow"
- "Team review meeting next Wednesday 2-4pm, topic: project B"
- "Move that checklist's due date to Friday"
- "Generate this week's report"
- Drop in a chat / email screenshot and let the agent OCR + parse it

The agent will: parse input → extract structured fields → confirm with you → produce formal
wording → check for time conflicts → write to Apple Calendar / Reminders → save metadata.

## How it works (source-of-truth model)

```
                    [write]
user / agent ───────────────────────► Apple Reminders / Calendar
                                          │
                                          │ list/calendar name = the major tag (work/life)
                                          │ description/body tail = a metadata block
                                          │ (project, task_type, aux_tags, formal_title)
                                          │
                      iCloud device sync ◄┘
                                          │
                    [read / sync]         ▼
tasks.json ◄──────────────────────  Mac / iPhone
(local cache, rebuildable)
```

- The **major tag** (work/life) is carried physically by which Apple list/calendar an item lives
  in — not by a hidden field. Move an item between lists on your iPhone and the next `sync`
  reclassifies it automatically.
- **Secondary tags + metadata** ride in a metadata block appended to the reminder body / event
  description, so they sync with the item itself across devices.
- `sync` rebuilds `tasks.json` from Apple at any time (auto-backs up the previous cache first).

## Optional: enable the automatic loop (daily sync + Friday report)

> Off by default. The skill works fine called on demand by your agent. Enable the launchd
> heartbeat below if you want unattended "daily sync + Friday report".
>
> This is the minimum viable [Loop Engineering](https://addyosmani.com/blog/loop-engineering/)
> setup: one automation (launchd) + one skill + one state file (`loop-state.json`) + one gate
> (structural assertions).

**Two heartbeat commands** (also runnable manually anytime):
```bash
python3 .../scripts/task_manager.py loop-tick --mode daily    # daily sync
python3 .../scripts/task_manager.py loop-tick --mode weekly   # sync + generate report
python3 .../scripts/task_manager.py loop-status               # inspect loop health
```

**Schedule via launchd** (daily 18:00 + Friday 17:00):
```bash
# 1. Find your python3 absolute path
which python3                       # e.g. /opt/homebrew/bin/python3

# 2. Edit the two templates, replacing {{PYTHON3}} and {{SKILL_PATH}}
#    {{SKILL_PATH}} = absolute path to task_manager.py
vi templates/com.smartcalendar.daily.plist.template
vi templates/com.smartcalendar.weekly.plist.template

# 3. Copy into LaunchAgents and load
cp templates/com.smartcalendar.daily.plist.template  ~/Library/LaunchAgents/com.smartcalendar.daily.plist
cp templates/com.smartcalendar.weekly.plist.template ~/Library/LaunchAgents/com.smartcalendar.weekly.plist
launchctl load -w ~/Library/LaunchAgents/com.smartcalendar.daily.plist
launchctl load -w ~/Library/LaunchAgents/com.smartcalendar.weekly.plist

# disable:
launchctl unload -w ~/Library/LaunchAgents/com.smartcalendar.daily.plist
launchctl unload -w ~/Library/LaunchAgents/com.smartcalendar.weekly.plist
```

**How failures surface:** every failed tick posts a macOS notification (Basso sound) and writes
`last_error` into `loop-state.json`. Run `loop-status` every few days to scan `history` and
confirm the loop is healthy — the minimum habit against a silently-failing loop.

> Don't treat it as fire-and-forget: the loop syncs and drafts for you, but report content and
> task classification still need your periodic review. The loop lowers mechanical cost, not
> judgment cost.

## Files

| Path | Purpose |
|---|---|
| `SKILL.md` | Skill entry point; defines the agent flow (Chinese) |
| `README.md` / `README.zh-CN.md` | English / Chinese docs |
| `scripts/task_manager.py` | Core controller (CLI, incl. sync / loop-tick) |
| `scripts/smoke_test.py` | Smoke test (92 checks) |
| `references/applescript_api.md` | AppleScript API reference |
| `templates/weekly_report.md` | Report template (reference; report is currently code-assembled) |
| `templates/com.smartcalendar.daily.plist.template` | launchd template for the daily sync loop |
| `templates/com.smartcalendar.weekly.plist.template` | launchd template for the weekly report loop |

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SMART_CALENDAR_DATA_DIR` | `~/.smart-calendar` | Data directory; can point at iCloud Drive or elsewhere (not recommended for multi-machine sync) |

## Version

v1.1 · single-machine · Apple-source-of-truth (sync) + optional launchd loop. No cross-machine
coordination.

## License

MIT — see [LICENSE](LICENSE).
