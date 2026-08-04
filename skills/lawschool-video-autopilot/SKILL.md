---
name: lawschool-video-autopilot
description: Automate online law course video watching on 律师云学院 (lawschool.lawyerpass.com). Use when a user needs to automatically play through a list of training videos, handle course enrollment ("选修并学习"), detect video completion, switch to the next course, and send progress notifications. Supports both 培训计划 (training plan) courses and 课程广场 (course square) free-choice courses. Requires Chrome browser connected via OpenClaw Browser Relay.
---

# 律师云学院视频自动播放

Automates video playback across multiple courses on lawschool.lawyerpass.com using the `browser` tool (Chrome profile via Browser Relay) and a persistent state file + cron job for long-running monitoring.

## Architecture

- **State file** (`video_state.json`): tracks progress, current video, queue
- **Cron job** (`video-check-loop`): fires every 8 minutes, checks video status, switches when done
- **Browser tool**: `profile=chrome`, `targetId` from state file

## Quick Start

1. Read `references/workflow.md` for the full step-by-step procedure
2. Read `references/known-issues.md` for critical gotchas before starting

## Key Facts

- **Site**: `https://lawschool.lawyerpass.com`
- **Course list page**: `/course/list`
- **Course detail URL**: `/course/detail?courseId=<id>`
- **Card selector**: `app-lesson-card.square-item`
- **Video element**: `document.querySelector('video')`

## Getting courseId (critical)

Course cards use Angular Router — no `href` on `<a>` tags. Intercept `history.pushState`:

```js
let captured = '';
const orig = window.history.pushState.bind(window.history);
window.history.pushState = function(s, t, url) { captured = url; orig(s, t, url); };
[...document.querySelectorAll('app-lesson-card.square-item')]
  .find(c => c.textContent.includes('课程标题关键词'))
  ?.querySelector('a')?.click();
return captured; // returns "/course/detail?courseId=d5b19f94..."
```

Then `navigate` to `https://lawschool.lawyerpass.com` + captured path.

## Enrollment Gate (⚠️ critical)

Some courses from 课程广场 require enrollment before video appears:

```js
// Step 1: Check and click enrollment button
const btn = [...document.querySelectorAll('button, a, [class*=btn]')]
  .find(el => el.textContent.includes('选修并学习'));
if (btn) { btn.click(); return 'clicked_enroll'; }
return 'no_enroll_btn';
```

If clicked → wait 3s → confirm dialog:

```js
const confirm = [...document.querySelectorAll('button, [class*=btn], [class*=confirm]')]
  .find(el => el.textContent.match(/确定|确认|OK/));
confirm?.click();
```

Wait 3s more, then `video.play()`.

## Video Status Check

```js
const v = document.querySelector('video');
if (!v) return JSON.stringify({ found: false, url: location.href });
return JSON.stringify({
  found: true,
  ct: Math.round(v.currentTime),
  dur: Math.round(v.duration),
  paused: v.paused,
  ended: v.ended,
  url: location.href
});
```

**Completion condition**: `ended === true` OR `ct >= dur - 3`
> Note: Some videos stop with `ended=false` but `ct === dur` — always check both.

## Cron Job Setup

```json
{
  "schedule": { "kind": "every", "everyMs": 480000 },
  "sessionTarget": "isolated",
  "payload": { "kind": "agentTurn", "timeoutSeconds": 120 }
}
```

**⚠️ Do NOT use everyMs < 300000 (5 min)** — causes API rate limit errors.

## State File Schema

See `references/state-schema.md` for the full `video_state.json` schema.
Use `scripts/lawschool_init_state.py` to generate an initial state file.

## Notifications

Use `message` tool on every video complete and every video start:
- Complete: `✅ 播完：{title}（{done}/{total}）`
- Start: `▶ 开始：{title}，{duration}，第{done+1}/{total}门`
- All done: `🎉 全部{total}门完成！`

## Reference Files

| File | When to read |
|---|---|
| `references/workflow.md` | Full step-by-step setup and monitoring loop |
| `references/state-schema.md` | State file fields and update rules |
| `references/known-issues.md` | Before starting — critical gotchas |
