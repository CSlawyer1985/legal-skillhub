#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
顾问单位法律服务工作记录 - 本地服务 (stdlib only)
提供网页前端 + REST API：记录的增删改查、单位管理、DOCX/Excel 报告生成。
数据持久化于 data/records.json（本地文件，保密可控）。
"""
import json
import os
import sys
import threading
import contextlib
import uuid
import fcntl
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "records.json")
WEB_DIR = os.path.join(BASE_DIR, "web")
DEFAULT_PORT = int(os.environ.get("COUNSEL_LOG_PORT", "8765"))

# 「未分类单位」视图标识：前端以该值作为 unit 查询/提交，后端识别后将其归一化为空单位，
# 归入"未分类单位"（即 unit 不在 units 列表中、尚未指定归属的记录）。
UNCATEGORIZED = "__uncategorized__"

lock = threading.Lock()

sys.path.insert(0, BASE_DIR)
import report as report_mod  # noqa: E402


# --------------------------------------------------------------------------- #
# 数据存取
# --------------------------------------------------------------------------- #
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"units": [], "records": [], "unit_meta": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"units": [], "records": [], "unit_meta": {}}
        data.setdefault("units", [])
        data.setdefault("records", [])
        # unit_meta 记录各单位的服务期限（依据律师服务合同）：
        # {"单位名称": {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}
        data.setdefault("unit_meta", {})
        # 兼容旧数据：units 内可能存在对象（{name,...}）形态，统一规整为字符串名称
        cleaned = []
        for u in data["units"]:
            if isinstance(u, dict):
                nm = (u.get("name") or "").strip()
                if nm:
                    cleaned.append(nm)
                    if nm not in data["unit_meta"]:
                        data["unit_meta"][nm] = {
                            "start_date": (u.get("start_date") or "").strip(),
                            "end_date": (u.get("end_date") or "").strip(),
                        }
            elif isinstance(u, str) and u.strip():
                cleaned.append(u.strip())
        data["units"] = cleaned
        return data
    except Exception:
        return {"units": [], "records": [], "unit_meta": {}}


def save_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    # 跨进程文件锁：避免网页 HTTP 服务与 capture.py 自动捕获脚本并发写冲突
    lockf = os.path.join(DATA_DIR, ".write.lock")
    with open(lockf, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)


@contextlib.contextmanager
def _locked_data():
    """在文件锁内完成 load -> 修改 -> 原子写，与 capture.py 共用同一把 .write.lock。
    跨进程互斥、无死锁：本进程仅持有一把锁，且不在持锁期间嵌套调用自身。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    lockf = os.path.join(DATA_DIR, ".write.lock")
    with open(lockf, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        data = load_data()
        try:
            yield data
        finally:
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, DATA_FILE)


def now_iso():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def filter_records(data, unit=None, date_from=None, date_to=None):
    recs = data["records"]
    if unit:
        if unit == UNCATEGORIZED:
            # 未分类单位：unit 不在已有单位列表中（含已删除单位后置空的记录）
            recs = [r for r in recs if r.get("unit") not in data["units"]]
        else:
            recs = [r for r in recs if r.get("unit") == unit]
    if date_from:
        recs = [r for r in recs if r.get("date", "") >= date_from]
    if date_to:
        recs = [r for r in recs if r.get("date", "") <= date_to]
    # 按日期升序，同日按创建时间升序，保证序号稳定
    recs.sort(key=lambda r: (r.get("date", ""), r.get("created_at", "")))
    return recs


# --------------------------------------------------------------------------- #
# HTTP 处理器
# --------------------------------------------------------------------------- #
class Handler(BaseHTTPRequestHandler):
    server_version = "CounselLog/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("[counsel-log] %s - %s\n" % (self.address_string(), fmt % args))

    def _respond(self, status, content_type, body, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, obj, status=200):
        self._respond(status, "application/json; charset=utf-8",
                      json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _send_file(self, data, filename, mimetype):
        # RFC 6266: ASCII 回退名 + UTF-8 编码的 filename*，解决中文文件名 header 编码问题
        ext = os.path.splitext(filename)[1] or ""
        safe = "report" + ext
        disp = 'attachment; filename="%s"; filename*=UTF-8\'\'%s' % (safe, quote(filename))
        self._respond(200, mimetype, data, extra={
            "Content-Disposition": disp
        })

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _serve_static(self, rel):
        fp = os.path.normpath(os.path.join(WEB_DIR, rel))
        if not fp.startswith(WEB_DIR) or not os.path.isfile(fp):
            self._respond(404, "text/plain; charset=utf-8", b"404 Not Found")
            return
        mime = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".ico": "image/x-icon",
        }.get(os.path.splitext(fp)[1], "application/octet-stream")
        with open(fp, "rb") as f:
            self._respond(200, mime, f.read())

    # ---------------- GET ---------------- #
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/api/health":
            self._send_json({"status": "ok"})
            return

        if path == "/api/units":
            with lock:
                data = load_data()
            unc = sum(1 for r in data["records"] if r.get("unit") not in data["units"])
            self._send_json({"units": data["units"], "unit_meta": data.get("unit_meta", {}),
                             "uncategorized_count": unc})
            return

        if path.startswith("/api/records/") and len(path.split("/")) == 4:
            rid = path.rsplit("/", 1)[-1]
            with lock:
                data = load_data()
                rec = next((r for r in data["records"] if r.get("id") == rid), None)
            if not rec:
                self._send_json({"error": "记录不存在"}, 404)
                return
            self._send_json({"record": rec})
            return

        if path == "/api/records":
            unit = qs.get("unit", [None])[0]
            date_from = qs.get("from", [None])[0]
            date_to = qs.get("to", [None])[0]
            with lock:
                data = load_data()
                recs = filter_records(data, unit, date_from, date_to)
            out = []
            for i, r in enumerate(recs, 1):
                item = dict(r)
                item["seq"] = i
                out.append(item)
            self._send_json({"count": len(out), "total_hours": round(sum(float(r.get("hours") or 0) for r in recs), 2), "records": out})
            return

        if path == "/api/report":
            fmt = (qs.get("format", ["docx"])[0]).lower()
            unit = qs.get("unit", [None])[0]
            date_from = qs.get("from", [None])[0]
            date_to = qs.get("to", [None])[0]
            split = qs.get("split", ["0"])[0] in ("1", "true", "yes")
            try:
                with lock:
                    data = load_data()
                    recs = filter_records(data, unit, date_from, date_to)
                unit_label = (unit if unit != UNCATEGORIZED else "未分类单位") or "全部顾问单位"
                unit_meta = data.get("unit_meta", {})
                if unit:
                    # 单单位分表导出：仅该单位的工作明细（不含单位列）
                    if fmt == "excel":
                        payload = report_mod.build_excel(recs, unit_label, date_from, date_to,
                                                        show_unit_col=False, unit_meta=unit_meta)
                        self._send_file(payload, "顾问单位法律服务工作记录（%s）分表.xlsx" % unit,
                                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    else:
                        payload = report_mod.build_docx(recs, unit_label, date_from, date_to,
                                                        show_unit_col=False, unit_meta=unit_meta)
                        self._send_file(payload, "顾问单位法律服务工作记录（%s）分表.docx" % unit,
                                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                elif split:
                    # 拆分模式：首张为总表概览，其后为各单位工作明细分表
                    if fmt == "excel":
                        payload = report_mod.build_excel(recs, unit_label, date_from, date_to,
                                                        split_by_unit=True, unit_order=data["units"],
                                                        unit_meta=unit_meta)
                        self._send_file(payload, "顾问单位法律服务工作记录（总表+分表）.xlsx",
                                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    else:
                        payload = report_mod.build_docx(recs, unit_label, date_from, date_to,
                                                        split_by_unit=True, unit_order=data["units"],
                                                        unit_meta=unit_meta)
                        self._send_file(payload, "顾问单位法律服务工作记录（总表+分表）.docx",
                                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                else:
                    # 总表导出：仅列示各单位的服务对象名称与服务期限，不含工作明细
                    if fmt == "excel":
                        payload = report_mod.build_excel([], unit_label, date_from, date_to,
                                                        overview=True, unit_order=data["units"],
                                                        unit_meta=unit_meta)
                        self._send_file(payload, "顾问单位法律服务工作记录总表（单位一览）.xlsx",
                                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    else:
                        payload = report_mod.build_docx([], unit_label, date_from, date_to,
                                                        overview=True, unit_order=data["units"],
                                                        unit_meta=unit_meta)
                        self._send_file(payload, "顾问单位法律服务工作记录总表（单位一览）.docx",
                                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            except Exception as e:
                import traceback as _tb
                sys.stderr.write("[report-error] %s\n%s\n" % (e, _tb.format_exc()))
                self._send_json({"error": "报告生成失败：" + str(e)}, 500)
            return

        if path == "/":
            self._serve_static("index.html")
            return

        self._serve_static(path.lstrip("/"))

    # ---------------- POST ---------------- #
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/api/units":
            name = (body.get("name") or "").strip()
            if not name:
                self._send_json({"error": "单位名称为空"}, 400)
                return
            with _locked_data() as data:
                if name not in data["units"]:
                    data["units"].append(name)
                    meta = data.setdefault("unit_meta", {})
                    if name not in meta:
                        meta[name] = {}
                    meta[name]["start_date"] = (body.get("start_date") or "").strip()
                    meta[name]["end_date"] = (body.get("end_date") or "").strip()
            self._send_json({"units": data["units"], "unit_meta": data.get("unit_meta", {})})
            return

        if path == "/api/records":
            rec = self._validate_record(body)
            if "error" in rec:
                self._send_json(rec, 400)
                return
            with _locked_data() as data:
                data["records"].append(rec)
                if rec["unit"] and rec["unit"] not in data["units"]:
                    data["units"].append(rec["unit"])
            self._send_json({"record": rec}, 201)
            return

        self._send_json({"error": "not found"}, 404)

    # ---------------- PUT ---------------- #
    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/api/units":
            old = (body.get("old") or "").strip()
            new = (body.get("new") or "").strip()
            if not old:
                self._send_json({"error": "原单位名称为空"}, 400)
                return
            if not new:
                self._send_json({"error": "新单位名称不能为空"}, 400)
                return
            if new == old:
                self._send_json({"units": (load_data())["units"]})
                return
            with _locked_data() as data:
                if old not in data["units"]:
                    self._send_json({"error": "原单位不存在"}, 404)
                    return
                if new in data["units"]:
                    self._send_json({"error": "已存在同名单位"}, 400)
                    return
                # 重命名：units 列表 + 所有该单位记录的 unit 字段 + unit_meta 键
                data["units"] = [new if u == old else u for u in data["units"]]
                meta = data.setdefault("unit_meta", {})
                if old in meta:
                    meta[new] = meta.pop(old)
                for r in data["records"]:
                    if r.get("unit") == old:
                        r["unit"] = new
            self._send_json({"units": data["units"], "unit_meta": data.get("unit_meta", {})})
            return

        if path == "/api/units/meta":
            # 仅更新某单位的服务期限（开始/结束日期），不影响工作记录
            name = (body.get("name") or "").strip()
            if not name:
                self._send_json({"error": "单位名称为空"}, 400)
                return
            with _locked_data() as data:
                if name not in data["units"]:
                    self._send_json({"error": "单位不存在"}, 404)
                    return
                meta = data.setdefault("unit_meta", {})
                if name not in meta:
                    meta[name] = {}
                meta[name]["start_date"] = (body.get("start_date") or "").strip()
                meta[name]["end_date"] = (body.get("end_date") or "").strip()
            self._send_json({"units": data["units"], "unit_meta": data.get("unit_meta", {})})
            return

        if path.startswith("/api/records/"):
            rid = path.rsplit("/", 1)[-1]
            with _locked_data() as data:
                idx = next((i for i, r in enumerate(data["records"]) if r.get("id") == rid), None)
                if idx is None:
                    self._send_json({"error": "记录不存在"}, 404)
                    return
                # 部分更新：仅覆盖请求体中提供的字段，保留其余原有字段，避免清空未提交字段
                merged = dict(data["records"][idx])
                for k in ("unit", "date", "content", "hours", "followup", "remark", "lawyer"):
                    if k in body:
                        merged[k] = body[k]
                err = self._validate_merged(merged)
                if err:
                    self._send_json(err, 400)
                    return
                # 规整工时为 float，保持与新增/capture 一致，避免编辑后以字符串写入
                try:
                    merged["hours"] = round(float(merged.get("hours") or 0), 2)
                except Exception:
                    merged["hours"] = 0
                merged["updated_at"] = now_iso()
                if merged.get("unit") == UNCATEGORIZED:
                    merged["unit"] = ""
                data["records"][idx] = merged
                if merged["unit"] and merged["unit"] not in data["units"]:
                    data["units"].append(merged["unit"])
            self._send_json({"record": merged})
            return
        self._send_json({"error": "not found"}, 404)

    # ---------------- DELETE ---------------- #
    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/api/units":
            name = (body.get("name") or "").strip()
            mode = (body.get("mode") or "keep_records").strip()
            if not name:
                self._send_json({"error": "单位名称为空"}, 400)
                return
            if mode not in ("keep_records", "delete_records"):
                self._send_json({"error": "mode 只能是 keep_records 或 delete_records"}, 400)
                return
            with _locked_data() as data:
                if name not in data["units"]:
                    self._send_json({"error": "单位不存在"}, 404)
                    return
                data["units"] = [u for u in data["units"] if u != name]
                meta = data.setdefault("unit_meta", {})
                meta.pop(name, None)
                if mode == "delete_records":
                    # 彻底删除该单位的所有工作记录
                    removed = sum(1 for r in data["records"] if r.get("unit") == name)
                    data["records"] = [r for r in data["records"] if r.get("unit") != name]
                else:
                    # 仅移除单位标签，记录保留并归入"未分类单位"
                    removed = 0
                    for r in data["records"]:
                        if r.get("unit") == name:
                            r["unit"] = ""
            self._send_json({"units": data["units"], "unit_meta": data.get("unit_meta", {}),
                             "removed_records": removed, "mode": mode})
            return

        if path.startswith("/api/records/"):
            rid = path.rsplit("/", 1)[-1]
            with _locked_data() as data:
                before = len(data["records"])
                data["records"] = [r for r in data["records"] if r.get("id") != rid]
                if len(data["records"]) == before:
                    self._send_json({"error": "记录不存在"}, 404)
                    return
            self._send_json({"ok": True, "deleted": 1})
            return
        self._send_json({"error": "not found"}, 404)

    # ---------------- OPTIONS ---------------- #
    def do_OPTIONS(self):
        self._respond(204, "text/plain", b"")

    # ---------------- 校验 ---------------- #
    @staticmethod
    def _validate_record(body, partial=False):
        err = {"error": "参数缺失"}
        unit = (body.get("unit") or "").strip()
        date = (body.get("date") or "").strip()
        content = (body.get("content") or "").strip()
        if not partial:
            if not unit:
                return {"error": "顾问单位不能为空"}
            if not date:
                return {"error": "日期不能为空"}
            if not content:
                return {"error": "律师工作内容不能为空"}
        try:
            hours = float(body.get("hours") or 0)
        except Exception:
            return {"error": "工作时间必须为数字（小时）"}
        if hours < 0:
            return {"error": "工作时间不能为负数"}
        # 前端以 sentinel 表示"未分类单位"，此处归一化为空单位存储
        if unit == UNCATEGORIZED:
            unit = ""
        rec = {
            "id": body.get("id") or uuid.uuid4().hex,
            "unit": unit,
            "date": date,
            "content": content,
            "hours": round(hours, 2),
            "followup": (body.get("followup") or "").strip(),
            "remark": (body.get("remark") or "").strip(),
            "lawyer": (body.get("lawyer") or "").strip(),
            "created_at": body.get("created_at") or now_iso(),
            "updated_at": now_iso(),
        }
        return rec

    @staticmethod
    def _validate_merged(m):
        unit = (m.get("unit") or "").strip()
        date = (m.get("date") or "").strip()
        content = (m.get("content") or "").strip()
        if not unit:
            return {"error": "顾问单位不能为空"}
        if not date:
            return {"error": "日期不能为空"}
        if not content:
            return {"error": "律师工作内容不能为空"}
        try:
            hours = float(m.get("hours") or 0)
        except Exception:
            return {"error": "工作时间必须为数字（小时）"}
        if hours < 0:
            return {"error": "工作时间不能为负数"}
        return None


def run():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        save_data({"units": [], "records": [], "unit_meta": {}})
    # 单条连接最长处理 30s，避免客户端保持连接不释放时线程被永久占用
    Handler.timeout = 30
    # 使用多线程服务：单条卡死/慢请求不再拖垮整个服务（此前单线程 HTTPServer
    # 在任一连接被挂起时会导致全部请求无响应）。
    server = ThreadingHTTPServer(("127.0.0.1", DEFAULT_PORT), Handler)
    print("顾问单位法律服务工作记录服务已启动: http://127.0.0.1:%d/" % DEFAULT_PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    run()
