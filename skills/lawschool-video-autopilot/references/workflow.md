# Full Workflow: 律师云学院视频自动播放

## Phase 1: Setup

### 1.1 Collect course list

Navigate to `https://lawschool.lawyerpass.com/course/list`, wait 5s, then get duration info:

```js
[...document.querySelectorAll('*')]
  .filter(el => el.children.length === 0 && el.textContent.trim().match(/\d+分\d+秒|\d+小时/))
  .slice(0, 30)
  .map(el => ({ tag: el.tagName, cls: el.className, text: el.textContent.trim(), parent: el.parentElement?.className }))
```

Sort by duration (shortest first) to maximize courses completed per hour.

### 1.2 Get courseIds for queued courses

For each course title, use the `history.pushState` intercept method (see SKILL.md) to get courseId without navigating away.

### 1.3 Create state file

Write `video_state.json` to workspace (see `references/state-schema.md`).

### 1.4 Navigate to first course and start playback

1. `navigate` to course detail URL
2. Wait 6s
3. Check for enrollment button → handle if present (see SKILL.md "Enrollment Gate")
4. `video.play()`
5. Confirm `paused === false`

### 1.5 Create cron job

```json
{
  "name": "video-check-loop",
  "schedule": { "kind": "every", "everyMs": 480000 },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "timeoutSeconds": 120,
    "message": "<monitoring prompt — see Phase 2>"
  },
  "delivery": { "mode": "none" }
}
```

Notify user: `▶ 开始：{title}，{duration}，第1/{total}门`

---

## Phase 2: Cron Monitoring Loop

Each cron trigger runs an isolated agent with this logic:

```
1. Read video_state.json
2. browser evaluate → get video status
3. Decision:
   - Normal playing (found, !paused, ct < dur-3) → exit silently
   - Paused (!ended, ct < dur-3)                → video.play(), exit
   - Missing (found=false)                       → navigate to current_url, re-enroll if needed, play()
   - Complete (ended || ct >= dur-3)             → switch to next (Phase 3)
```

---

## Phase 3: Switch to Next Course

```
a. done_count++, completed.push(current), queue_index++
b. Send ✅ notification
c. If done_count >= target_total → send 🎉 notification, done
d. Navigate to /course/list, wait 5s
e. Get courseId via history.pushState intercept
f. navigate to /course/detail?courseId=xxx, wait 6s
g. Handle enrollment gate if present
h. video.play()
i. Update state file: current, current_url
j. Send ▶ notification
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Cron runs but no switch | `ct === dur` but `ended=false` | Check `ct >= dur-3`, not just `ended` |
| Cron fails with rate limit | Interval too short | Set `everyMs >= 480000` |
| Video not found after navigate | Enrollment gate blocking | Check for `选修并学习` button first |
| courseId not captured | Angular router, no href | Use `history.pushState` intercept |
| ref clicks fail after page reload | Aria refs expire on reload | Never use refs; always use JS evaluate |
