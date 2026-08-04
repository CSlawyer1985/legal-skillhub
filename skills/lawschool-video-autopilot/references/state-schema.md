# video_state.json Schema

```json
{
  "target_total": 20,
  "done_count": 0,
  "completed": [],
  "current": "课程名称",
  "current_url": "https://lawschool.lawyerpass.com/course/detail?courseId=xxx",
  "current_dur_mins": 31.75,
  "queue": [
    {
      "title": "课程名称",
      "dur": "1小时12分29秒",
      "mins": 72.48
    }
  ],
  "queue_index": 0,
  "notify_group": "<wecom group space id>",
  "notify_channel": "openclaw-wecom-bot",
  "target_id": "<Chrome targetId from browser snapshot>",
  "list_page_url": "https://lawschool.lawyerpass.com/course/list"
}
```

## Field Notes

| Field | Description |
|---|---|
| `target_total` | Total number of courses to complete |
| `done_count` | How many have been completed so far |
| `completed` | Array of completed course titles |
| `current` | Title of the currently playing course |
| `current_url` | Full URL of the currently playing course |
| `current_dur_mins` | Duration in minutes (for logging) |
| `queue` | Ordered list of upcoming courses (sort by `mins` ascending) |
| `queue_index` | Next index to pop from `queue` |
| `notify_group` | Wecom group space ID for notifications |
| `notify_channel` | Always `openclaw-wecom-bot` |
| `target_id` | Chrome tab targetId — get from browser snapshot |
| `list_page_url` | Course listing page URL |

## Getting `target_id`

Use `browser snapshot` with `profile=chrome`. The `targetId` appears in the response. Copy it to the state file. It persists as long as the Chrome tab stays open.

## Updating the State File

Always update atomically (write entire file). Update after:
- Starting a new course: set `current`, `current_url`, `current_dur_mins`
- Completing a course: increment `done_count`, push to `completed`, increment `queue_index`
