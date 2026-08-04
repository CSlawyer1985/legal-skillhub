#!/usr/bin/env python3
"""
lawschool_init_state.py

Helper to create video_state.json for lawschool-video-autopilot skill.
Run this once before starting the cron monitoring loop.

Usage:
    python lawschool_init_state.py \
        --target-id <chrome_target_id> \
        --notify-group <wecom_group_id> \
        --total 20 \
        --output video_state.json

The script creates a starter state file with an empty queue.
Add courses manually or use the browser to scrape the course list.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def parse_duration_minutes(dur_str: str) -> float:
    """Parse duration string like '1小时12分29秒' -> 72.48 minutes."""
    if not dur_str:
        return 9999.0
    hours = int(m.group(1)) if (m := re.search(r'(\d+)小时', dur_str)) else 0
    mins = int(m.group(1)) if (m := re.search(r'(\d+)分', dur_str)) else 0
    secs = int(m.group(1)) if (m := re.search(r'(\d+)秒', dur_str)) else 0
    return hours * 60 + mins + secs / 60


def main():
    parser = argparse.ArgumentParser(description='Initialize video_state.json')
    parser.add_argument('--target-id', required=True, help='Chrome tab targetId')
    parser.add_argument('--notify-group', required=True, help='Wecom group space ID')
    parser.add_argument('--total', type=int, default=20, help='Total courses to complete')
    parser.add_argument('--done', type=int, default=0, help='Already completed count')
    parser.add_argument('--output', default='video_state.json', help='Output file path')
    args = parser.parse_args()

    state = {
        "target_total": args.total,
        "done_count": args.done,
        "completed": [],
        "current": None,
        "current_url": None,
        "current_dur_mins": 0,
        "queue": [],
        "queue_index": 0,
        "notify_group": args.notify_group,
        "notify_channel": "openclaw-wecom-bot",
        "target_id": args.target_id,
        "list_page_url": "https://lawschool.lawyerpass.com/course/list"
    }

    out = Path(args.output)
    out.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"✅ Created {out.resolve()}")
    print(f"   Next: populate the 'queue' array with course objects {{title, dur, mins}}")
    print(f"   Then navigate to the first course and set 'current' + 'current_url'")


if __name__ == '__main__':
    main()
