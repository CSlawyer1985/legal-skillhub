#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GMP 合规自助体检 Web 提交页（零依赖获客钩子）

用法:
  python webapp.py --port 8000
  浏览器打开 http://127.0.0.1:8000

客户填写公司名+邮箱、上传GMP资料（或粘贴文本），自动生成 GMP 合规体检报告，
报告内联展示并可打印为 PDF；留邮箱时自动发报告至客户邮箱、推送线索至 CRM/企微、
本地存线索 CSV。SMTP/推送未配置时优雅降级（仅出报告 / 可选存线索）。
"""
import argparse
import csv
import email
import json
import os
import re
import smtplib
import sys
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from review import parse_baseline, evaluate, ChineseArgumentParser, friendly_mail_error, friendly_net_error  # noqa: E402
from generate_report import build_html  # noqa: E402

DEFAULT_BASELINE = os.path.join(SKILL_ROOT, "sample_data", "demo_client")
MAX_UPLOAD = 3 * 1024 * 1024
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

BASE_CSS = """
<style>
  body { font-family: -apple-system, 'Microsoft YaHei', 'PingFang SC', sans-serif; color:#222; max-width:760px; margin:0 auto; padding:24px 18px; line-height:1.6; }
  h1 { font-size:24px; margin-bottom:4px; }
  .sub { color:#666; font-size:14px; margin-bottom:20px; }
  label { display:block; font-weight:600; margin:14px 0 6px; font-size:14px; }
  input[type=text], input[type=email], textarea { width:100%; box-sizing:border-box; padding:10px; border:1px solid #ccc; border-radius:6px; font-size:14px; }
  textarea { height:140px; resize:vertical; }
  .btn { margin-top:18px; padding:12px 22px; background:#1565c0; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:15px; }
  .btn:hover { background:#0d47a1; }
  .note { margin-top:16px; padding:12px 14px; border-radius:6px; background:#e8f5e9; color:#1b5e20; font-size:14px; }
  .err { background:#ffebee; color:#b71c1c; }
  .back { display:inline-block; margin-top:18px; color:#1565c0; text-decoration:none; }
  .box { border:1px solid #eee; border-radius:10px; padding:18px 20px; background:#fafbfc; }
</style>
"""

INDEX_PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>GMP 合规自助体检</title>{css}</head>
<body>
  <h1>GMP 合规自助体检</h1>
  <div class="sub">上传贵司的质量管理 / 信息化方案资料，1 分钟生成合规覆盖度体检报告。</div>
  <form method="post" enctype="multipart/form-data" class="box">
    <label>公司名称</label>
    <input type="text" name="company" placeholder="例如：XX制药有限公司">
    <label>邮箱（用于接收报告，可选）</label>
    <input type="email" name="email" placeholder="name@company.com">
    <label>上传 GMP 资料（.txt / .md，可多选，≤3MB）</label>
    <input type="file" name="file" multiple accept=".txt,.md">
    <label>或粘贴资料文本</label>
    <textarea name="copy" placeholder="把方案/制度文档内容粘贴到这里……"></textarea>
    <button class="btn" type="submit">生成 GMP 合规体检报告</button>
  </form>
  <p class="sub" style="margin-top:18px">本工具基于通用 GMP 合规基线做覆盖度自检，结果仅供参考；重大合规决策请结合专业审计。</p>
</body></html>""".replace("{css}", BASE_CSS)

RESULT_TMPL = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>GMP 合规体检报告 - {COMPANY}</title>{css}</head>
<body>
  {REPORT}
  <div class="note">{NOTE}</div>
  <a class="back" href="/">← 返回，再测一份</a>
</body></html>"""

ERR_TMPL = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>提示</title>{css}</head>
<body>
  <h1>温馨提示</h1>
  <div class="note err"><b>{title}</b><br>{msg}</div>
  <a class="back" href="/">← 返回重试</a>
</body></html>"""


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def is_safe_email(addr):
    if not addr or not EMAIL_RE.match(addr):
        return False
    if any(ch in addr for ch in ("\r", "\n", "\t")):  # 头部注入防护
        return False
    return True


def load_config(name):
    p = os.path.join(SKILL_ROOT, name)
    if os.path.isfile(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def send_mail(to_addr, subject, html, mail_cfg):
    try:
        msg = email.message.EmailMessage()
        msg["Subject"] = subject
        msg["From"] = mail_cfg.get("from", mail_cfg.get("smtp_user", ""))
        msg["To"] = to_addr
        msg.set_content("请使用支持 HTML 的邮件客户端查看 GMP 合规体检报告。")
        msg.add_alternative(html, subtype="html")
        host = mail_cfg["smtp_host"]
        port = int(mail_cfg.get("smtp_port", 465))
        user = mail_cfg.get("smtp_user", mail_cfg.get("from", ""))
        pw = mail_cfg.get("smtp_pass", "")
        with smtplib.SMTP_SSL(host, port, timeout=20) as s:
            s.login(user, pw)
            s.send_message(msg)
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, friendly_mail_error(e)


def push_lead(lead, push_cfg):
    try:
        body = json.dumps(lead, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(push_cfg["url"], data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        for k, v in (push_cfg.get("headers") or {}).items():
            req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status < 400, f"status {resp.status}"
    except Exception as e:  # noqa: BLE001
        return False, friendly_net_error(e)


def save_lead_csv(lead):
    path = os.path.join(SKILL_ROOT, "leads", "leads.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    exists = os.path.isfile(path)
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["time", "company", "email", "scanned_chars", "missing", "high_risk", "source"])
        w.writerow([lead["time"], lead["company"], lead["email"], lead["scanned"],
                    lead["missing"], lead["high_risk"], lead["source"]])


def _safe_name(s, default="submission"):
    """把任意字符串变成可安全用于文件名的短串。"""
    s = (s or default).strip()
    s = re.sub(r'[\\/:*?"<>|]', "_", s)
    s = re.sub(r"\s+", "_", s)
    return s[:40] or default


def persist_submission(company, html, files, ts):
    """把生成的报告与上传文件落到本地磁盘（best-effort），重启不丢失。

    返回已保存项的相对路径列表；失败时返回带原因的描述（不抛异常，不阻塞主流程）。
    """
    saved = []
    try:
        rep_dir = os.path.join(SKILL_ROOT, "reports")
        os.makedirs(rep_dir, exist_ok=True)
        rep_path = os.path.join(rep_dir, f"{ts}_{_safe_name(company)}.html")
        with open(rep_path, "w", encoding="utf-8") as f:
            f.write(html)
        saved.append(f"reports/{os.path.basename(rep_path)}")
    except Exception as e:  # noqa: BLE001
        saved.append(f"报告存盘失败：{e}")
    if files:
        try:
            up_dir = os.path.join(SKILL_ROOT, "uploads")
            os.makedirs(up_dir, exist_ok=True)
            for fname, payload in files:
                up_path = os.path.join(up_dir, f"{ts}_{_safe_name(fname, 'file')}")
                with open(up_path, "wb") as f:
                    f.write(payload)
                saved.append(f"uploads/{os.path.basename(up_path)}")
        except Exception as e:  # noqa: BLE001
            saved.append(f"上传文件存盘失败：{e}")
    return saved


def parse_multipart(body, content_type):
    """用 email 模块解析 multipart/form-data（Python3.13 已移除 cgi）。"""
    raw = b"Content-Type: " + content_type.encode("utf-8", "ignore") + b"\r\n\r\n" + body
    msg = email.message_from_bytes(raw)
    fields, files = {}, []
    for part in msg.walk():
        if part.is_multipart():
            continue
        name = part.get_param("name", header="Content-Disposition")
        if name is None:
            continue
        fname = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        if fname:
            files.append((fname, payload))
        else:
            fields[name] = payload.decode("utf-8", "ignore")
    return fields, files


def do_review(company, text):
    domains = parse_baseline(os.path.join(DEFAULT_BASELINE, "gmp_requirements.md"))
    result = evaluate(domains, text)
    html = build_html(result, company or "贵司")
    missing = sum(1 for d in result["domains"] for i in d["items"]
                  if i["status"] in ("缺失", "部分覆盖"))
    high = sum(1 for d in result["domains"] for i in d["items"]
               if i["status"] in ("缺失", "部分覆盖") and i["risk"] == "高")
    return result, html, missing, high


# ---------------------------------------------------------------------------
# HTTP 处理器
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # 静默默认访问日志
        pass

    def _send(self, code, html):
        body = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, INDEX_PAGE)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        if length > MAX_UPLOAD:
            self._send(413, ERR_TMPL.replace("{css}", BASE_CSS)
                       .replace("{title}", "提交内容过大")
                       .replace("{msg}", "单次上传请控制在 3MB 以内，可分批次提交。"))
            return
        body = self.rfile.read(length) if length else b""
        ctype = self.headers.get("Content-Type", "")
        try:
            fields, files = parse_multipart(body, ctype)
        except Exception as e:  # noqa: BLE001
            self._send(400, ERR_TMPL.replace("{css}", BASE_CSS)
                       .replace("{title}", "解析失败").replace("{msg}", f"表单解析出错：{e}"))
            return

        company = (fields.get("company") or "").strip()
        email_addr = (fields.get("email") or "").strip()
        copy = (fields.get("copy") or "").strip()

        parts = []
        if copy:
            parts.append(copy)
        for _, payload in files:
            parts.append(payload.decode("utf-8", "ignore"))
        text = "\n".join(parts)

        if not text.strip():
            self._send(400, ERR_TMPL.replace("{css}", BASE_CSS)
                       .replace("{title}", "内容为空")
                       .replace("{msg}", "请上传 GMP 资料文件，或在文本框粘贴资料内容。"))
            return

        try:
            _, html, missing, high = do_review(company, text)
        except Exception as e:  # noqa: BLE001
            self._send(500, ERR_TMPL.replace("{css}", BASE_CSS)
                       .replace("{title}", "自检出错").replace("{msg}", f"GMP 自检出错：{e}"))
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved = persist_submission(company, html, files, ts)
        saved_msg = " 本次报告与上传资料已自动存盘（重启不丢失）" + (": " + "、".join(saved) if saved else "")

        note = ""
        if is_safe_email(email_addr):
            mail_cfg = load_config("mail.json")
            if mail_cfg:
                ok, err = send_mail(email_addr, f"GMP合规体检报告 - {company or '贵司'}", html, mail_cfg)
                note = "报告已发送至您的邮箱。" if ok else f"报告发送失败：{err}"
                if ok and mail_cfg.get("notify_to"):
                    send_mail(mail_cfg["notify_to"], f"[新线索] {company} GMP体检",
                              f"公司：{company}\n邮箱：{email_addr}\n缺失项：{missing}，高风险：{high}", mail_cfg)
            else:
                note = "已记录为跟进线索，顾问会尽快与您联系。"
            lead = {
                "time": datetime.now().isoformat(timespec="seconds"),
                "company": company, "email": email_addr,
                "scanned": len(text), "missing": missing,
                "high_risk": high, "source": "gmp-webapp",
            }
            save_lead_csv(lead)
            push = load_config("leads_push.json")
            if push:
                ok2, err2 = push_lead(lead, push)
                note += " 已推送至我们的销售系统。" if ok2 else f" 线索推送提示：{err2}"
        else:
            if email_addr:
                note = "邮箱格式不正确，请检查后重试；您仍可在本页查看报告。"
            else:
                note = "未留邮箱，报告仅供本页查看；如需邮件接收请填写邮箱。"

        note += saved_msg
        out = (RESULT_TMPL.replace("{css}", BASE_CSS)
               .replace("{REPORT}", html).replace("{NOTE}", note)
               .replace("{COMPANY}", company or "贵司"))
        self._send(200, out)


def main():
    ap = ChineseArgumentParser(description="GMP 合规自助体检 Web 服务")
    ap.add_argument("--port", type=int, default=8000, help="监听端口")
    ap.add_argument("--host", default="127.0.0.1", help="监听地址")
    ap.add_argument("--open-browser", action="store_true",
                    help="启动后自动打开默认浏览器（配合双击启动器使用，普通用户无需手动输网址）")
    args = ap.parse_args()
    srv = HTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"GMP 合规自助体检已启动：{url}  (Ctrl+C 停止)")
    if args.open_browser:
        import threading
        import webbrowser
        def _open():
            import time
            time.sleep(1.2)  # 等服务器真正就绪再开浏览器，避免首屏连不上
            try:
                webbrowser.open(url)
            except Exception:  # noqa: BLE001
                print(f"无法自动打开浏览器，请手动访问：{url}")
        threading.Timer(0.4, _open).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
