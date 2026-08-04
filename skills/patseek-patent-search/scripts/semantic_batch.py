#!/usr/bin/env python3
"""Run independent PatSeek semantic angles serially with durable checkpoints."""

from __future__ import annotations

import argparse
import getpass
import importlib.util
import json
import os
import re
import time
from pathlib import Path


CLIENT_PATH = Path(__file__).with_name("patseek_client.py")
MIN_SUBMIT_INTERVAL = 60.0


def load_client():
    spec = importlib.util.spec_from_file_location("patseek_batch_client", CLIENT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def load_tasks(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("任务文件为空")
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            payload = payload.get("tasks")
        tasks = payload if isinstance(payload, list) else None
    except json.JSONDecodeError:
        tasks = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("任务文件必须是JSON数组、含tasks的对象或JSONL")
    seen = set()
    normalized = []
    for index, task in enumerate(tasks, 1):
        if not isinstance(task, dict):
            raise ValueError(f"第{index}项不是对象")
        task_id = str(task.get("id") or "").strip()
        query = str(task.get("query") or "").strip()
        if not task_id or not query:
            raise ValueError(f"第{index}项必须包含非空id和query")
        if task_id in seen:
            raise ValueError(f"任务id重复: {task_id}")
        seen.add(task_id)
        normalized.append({"id": task_id, "query": query})
    return normalized


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return cleaned[:100] or "task"


def append_checkpoint(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("status") == "succeeded" and record.get("id"):
            completed.add(str(record["id"]))
    return completed


def write_result(output_dir: Path, task_id: str, payload: dict) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{safe_name(task_id)}.json"
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, target)
    return target


def wait_for_task(client, api_key: str, remote_task_id: str, timeout: int) -> dict:
    elapsed = 0
    last = {}
    while elapsed < timeout:
        interval = client.task_poll_interval(elapsed)
        time.sleep(interval)
        elapsed += interval
        last = client.query_task(api_key, remote_task_id, include_partial=True)
        status = last.get("status")
        received = (last.get("progress") or {}).get("received", 0)
        print(f"  [{elapsed}s] status={status}, received={received}", flush=True)
        if status in {"succeeded", "failed", "cancelled"}:
            return last
    return {
        "status": "timeout",
        "task_id": remote_task_id,
        "progress": last.get("progress") or {},
        "error": f"轮询超过{timeout}秒",
    }


def run_batch(client, api_key: str, tasks: list[dict], checkpoint: Path, output_dir: Path, interval: float, timeout: int) -> int:
    if interval < MIN_SUBMIT_INTERVAL:
        raise ValueError("相邻语义任务提交间隔不得少于60秒")
    done = completed_ids(checkpoint)
    last_submit = None
    failures = 0
    for task in tasks:
        if task["id"] in done:
            print(f"[跳过] {task['id']} 已成功保存", flush=True)
            continue
        if last_submit is not None:
            remaining = interval - (time.monotonic() - last_submit)
            if remaining > 0:
                time.sleep(remaining)
        last_submit = time.monotonic()
        try:
            submitted = client.semantic_search_async_submit(api_key, task["query"])
            remote_id = str(submitted.get("task_id") or "")
            append_checkpoint(checkpoint, {
                "id": task["id"], "status": "submitted", "task_id": remote_id,
                "timestamp": time.time(),
            })
            if not remote_id:
                raise RuntimeError("提交响应缺少task_id")
            result = client.query_task(api_key, remote_id, include_partial=True) if submitted.get("status") == "succeeded" else wait_for_task(client, api_key, remote_id, timeout)
            status = result.get("status")
            received = (result.get("progress") or {}).get("received", len(result.get("result") or []))
            if status == "succeeded":
                result_path = write_result(output_dir, task["id"], result)
                append_checkpoint(checkpoint, {
                    "id": task["id"], "status": "succeeded", "task_id": remote_id,
                    "received": received, "result_file": str(result_path), "timestamp": time.time(),
                })
                print(f"[完成] {task['id']}: {received} 条 -> {result_path}", flush=True)
            else:
                failures += 1
                append_checkpoint(checkpoint, {
                    "id": task["id"], "status": status or "failed", "task_id": remote_id,
                    "received": received, "error": result.get("error"), "timestamp": time.time(),
                })
                print(f"[失败] {task['id']}: status={status}, received={received}", flush=True)
        except Exception as exc:
            failures += 1
            append_checkpoint(checkpoint, {
                "id": task["id"], "status": "client_error", "error": str(exc), "timestamp": time.time(),
            })
            print(f"[失败] {task['id']}: {type(exc).__name__}: {exc}", flush=True)
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="PatSeek串行语义批处理（带断点和结果持久化）")
    parser.add_argument("tasks", type=Path, help="JSON/JSONL任务文件；每项包含id和query")
    parser.add_argument("--checkpoint", type=Path, required=True, help="追加式脱敏JSONL检查点")
    parser.add_argument("--output-dir", type=Path, required=True, help="逐任务完整结果目录")
    parser.add_argument("--interval", type=float, default=60.0, help="提交起点间隔，最少60秒")
    parser.add_argument("--timeout", type=int, default=300, help="单任务轮询超时秒数")
    args = parser.parse_args()
    key = os.environ.get("PATSEEK_API_KEY", "") or getpass.getpass("PatSeek API key: ")
    if not key:
        raise SystemExit("PatSeek API key is required")
    try:
        tasks = load_tasks(args.tasks)
        return run_batch(load_client(), key, tasks, args.checkpoint, args.output_dir, args.interval, args.timeout)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
