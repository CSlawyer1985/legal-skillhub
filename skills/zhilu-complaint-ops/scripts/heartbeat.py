#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智录 cron 心跳（每次执行必打的"我跑过了"标记，与"有没有新数据"的水位解耦）。

用法:
  python3 heartbeat.py --job intake [--batch-id batch_20260910_1600_scheduled]
  python3 heartbeat.py --show            # 打印当前所有 job 心跳 + 距上次运行小时数

设计:
  维护一个独立文件 zhilu_heartbeat.json（不与 intake_state*.json 混写，避免采集/看板并发覆盖）。
  结构: {"<job>": {"last_run_at": "<ISO 本地时间>", "runs": <int>, "last_batch_id": "<可选>", "tz": "Asia/Shanghai"}}
  每次运行只更新自己那一个 job 的键，读-改-写用整文件覆盖即可（单 job 单写者）。

健康监控检查1 读本文件的 intake.last_run_at，而不是读已废弃的 intake_state.json.checkpoint。
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
HB_PATH = os.path.normpath(os.path.join(HERE, '..', 'zhilu_heartbeat.json'))

# Asia/Shanghai 固定 +08:00（无夏令时），避免依赖系统 tz 数据库
CN_TZ = timezone(timedelta(hours=8))


def load_hb():
    if os.path.exists(HB_PATH):
        try:
            with open(HB_PATH, encoding='utf-8') as f:
                d = json.load(f)
            if isinstance(d, dict):
                return d
        except (ValueError, OSError):
            pass
    return {}


def stamp(job, batch_id):
    now = datetime.now(CN_TZ)
    hb = load_hb()
    ent = hb.get(job) if isinstance(hb.get(job), dict) else {}
    ent['last_run_at'] = now.isoformat(timespec='seconds')
    ent['runs'] = int(ent.get('runs', 0)) + 1
    if batch_id:
        ent['last_batch_id'] = batch_id
    ent['tz'] = 'Asia/Shanghai'
    hb[job] = ent
    tmp = HB_PATH + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(hb, f, ensure_ascii=False, indent=2)
    os.replace(tmp, HB_PATH)
    print(f"[heartbeat] {job} -> {ent['last_run_at']} (第{ent['runs']}次) 已写 {HB_PATH}")
    return 0


def show():
    hb = load_hb()
    now = datetime.now(CN_TZ)
    if not hb:
        print('(尚无心跳记录)')
        return 0
    for job, ent in hb.items():
        ts = ent.get('last_run_at')
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                hours = (now - dt).total_seconds() / 3600.0
                extra = f"  距今 {hours:.1f}h"
            except ValueError:
                extra = ''
        else:
            extra = ''
        print(f"  {job}: {ts}  第{ent.get('runs','?')}次  batch={ent.get('last_batch_id','-')}{extra}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--job', help='intake | dashboard | inspection | health ...')
    ap.add_argument('--batch-id', default=None)
    ap.add_argument('--show', action='store_true', help='仅打印当前心跳状态')
    args = ap.parse_args()

    if args.show:
        return show()
    if not args.job:
        print('需要 --job <name> 或 --show', file=sys.stderr)
        return 2
    return stamp(args.job, args.batch_id)


if __name__ == '__main__':
    raise SystemExit(main())
