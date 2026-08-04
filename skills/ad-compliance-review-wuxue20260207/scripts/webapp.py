#!/usr/bin/env python3
"""
广告公司 AI 合规审查 —— 在线自助提交页（零依赖，纯标准库）

客户自己打开网页 → 上传历史文案目录（或粘贴） → 自动生成合规体检报告。
完全自助、零获客人力，是天然的获客钩子。

用法：
  python scripts/webapp.py [--port 8000]
浏览器打开 http://127.0.0.1:8000

实现：复用 review.py（审查核心）与 generate_report.py（报告渲染），不引入任何第三方依赖。
"""
import os
import sys
import html
import json
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(BASE, "sample_data", "demo_client")
ACTIVE_CLIENT = CLIENT  # 实际生效的客户词库目录（main 中按 --client 覆盖）
MAX_BODY = 3 * 1024 * 1024  # 单次提交上限 3 MB，超过给出明确提示

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review import load_client_terms, validate_client_dir  # noqa: E402
from generate_report import analyze, build_html, esc  # noqa: E402

esc = html.escape  # 兼容别名


def friendly_error_html(title, cause, fix):
    """生成面向普通用户的友好错误页（可直接在 iframe 内渲染）。"""
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>提交遇到问题</title></head>
<body style="margin:0;background:#f4f6f9;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1f2d3d;">
<div style="max-width:760px;margin:0 auto;padding:32px 20px;">
  <div style="height:6px;background:#E24B4A;border-radius:4px;"></div>
  <h1 style="font-size:20px;margin:18px 0 4px;">提交遇到问题</h1>
  <div style="background:#fff;border:1px solid #f3c9c9;border-radius:12px;padding:20px;margin-top:16px;">
    <div style="font-size:15px;font-weight:700;color:#a32d2d;">{esc(title)}</div>
    <div style="font-size:13px;color:#5f5e5a;margin-top:10px;line-height:1.8;"><b>可能原因：</b><br>{esc(cause)}</div>
    <div style="font-size:13px;color:#36506e;margin-top:12px;line-height:1.8;background:#eef4fd;border-left:4px solid #378ADD;padding:10px 14px;border-radius:6px;"><b>建议操作：</b><br>{esc(fix)}</div>
  </div>
  <button onclick="history.back()" style="margin-top:16px;border:1px solid #378ADD;background:#378ADD;color:#fff;border-radius:10px;padding:11px 18px;font-size:14px;cursor:pointer;">返回重新提交</button>
</div></body></html>"""


PAGE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>广告文案合规体检 · 在线提交</title></head>
<body style="margin:0;background:#f4f6f9;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1f2d3d;">
<div style="max-width:760px;margin:0 auto;padding:32px 20px;">
  <div style="height:6px;background:linear-gradient(90deg,#378ADD,#1D9E75);border-radius:4px;"></div>
  <h1 style="font-size:22px;margin:18px 0 4px;">广告文案合规体检</h1>
  <div style="color:#5f5e5a;font-size:13px;">上传贵司历史文案，一键生成合规风险报告（基于《广告法》通用红线）</div>

  <div style="background:#fff;border:1px solid #e6ebf2;border-radius:12px;padding:20px;margin-top:18px;">
    <label style="display:block;font-size:13px;font-weight:600;margin-bottom:6px;">客户 / 公司名称</label>
    <input id="name" placeholder="如：星澜美妆" style="width:100%;box-sizing:border-box;padding:10px;border:1px solid #cfd8e3;border-radius:8px;font-size:14px;">

    <label style="display:block;font-size:13px;font-weight:600;margin:16px 0 6px;">上传文案目录 / 文件</label>
    <input id="files" type="file" multiple webkitdirectory
      style="width:100%;box-sizing:border-box;padding:8px;border:1px dashed #cfd8e3;border-radius:8px;background:#fafbfc;font-size:13px;color:#5f5e5a;">
    <div style="font-size:12px;color:#9aa7b8;margin-top:6px;">支持选择整个文件夹（.txt / .md，每行一条文案）；也可手动多选文件。</div>

    <div style="font-size:13px;font-weight:600;margin:16px 0 6px;">或粘贴文案（每行一条）</div>
    <textarea id="paste" rows="5" placeholder="星澜精华是市面上最好用的修护产品，治疗各类肌肤问题，全网最低价！"
      style="width:100%;box-sizing:border-box;padding:10px;border:1px solid #cfd8e3;border-radius:8px;font-size:13px;resize:vertical;"></textarea>

    <button id="go" style="margin-top:16px;width:100%;border:0;background:#378ADD;color:#fff;
      border-radius:10px;padding:13px;font-size:15px;font-weight:600;cursor:pointer;">生成合规体检报告</button>
    <div id="msg" style="font-size:13px;margin-top:10px;min-height:18px;"></div>
  </div>

  <div id="result" style="margin-top:22px;"></div>
  <div style="font-size:11px;color:#9aa7b8;margin-top:24px;text-align:center;">
    本报告由 AI 合规体检工具自动生成 · 免费版使用通用广告法基线，接入贵司专属词库请与我们联系。
  </div>
</div>

<script>
function collectDocs() {
  var docs = [];
  var skipped = 0;
  var files = document.getElementById('files').files;
  var promises = [];
  for (var i = 0; i < files.length; i++) {
    var f = files[i];
    if (!/\\.(txt|md)$/i.test(f.name)) { skipped++; continue; }
    (function(file){
      promises.push(file.text().then(function(t){
        docs.push({src: file.name, text: t});
      }).catch(function(){ skipped++; }));  // 单个文件读取出错不阻断整体提交
    })(f);
  }
  return Promise.all(promises).then(function(){
    var paste = document.getElementById('paste').value.trim();
    if (paste) {
      paste.split(/\\n|\\r\\n|\\r/).forEach(function(line){
        line = line.trim();
        if (line) docs.push({src: '粘贴文案', text: line});
      });
    }
    return {docs: docs, skipped: skipped};
  });
}

document.getElementById('go').onclick = function(){
  var msg = document.getElementById('msg');
  var result = document.getElementById('result');
  var name = document.getElementById('name').value || '贵司';
  msg.style.color = '#378ADD';
  msg.textContent = '正在扫描文案，请稍候…（大目录可能需要几秒）';
  result.innerHTML = '';

  collectDocs().then(function(res){
    var docs = res.docs, skipped = res.skipped;
    if (!docs.length) {
      msg.style.color = '#E24B4A';
      msg.textContent = skipped > 0
        ? '未发现可分析的文案：所选文件中没有 .txt/.md 文本，或文件读取失败。请确认文件类型，或直接在文本框粘贴文案（每行一条）。'
        : '未找到可分析的文案：请上传 .txt/.md 文件，或直接在下方文本框粘贴（每行一条）。';
      return;
    }
    fetch('/analyze', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: name, docs: docs})
    }).then(function(r){
      return r.text().then(function(html){
        msg.style.color = r.ok ? '#1D9E75' : '#E24B4A';
        msg.textContent = r.ok
          ? (skipped > 0 ? '报告已生成 ✓（已跳过 ' + skipped + ' 个不支持的文件）' : '报告已生成 ✓')
          : '已收到请求，但服务返回了提示，请查看下方说明。';
        var box = document.createElement('div');
        box.style.cssText = 'border:1px solid #e6ebf2;border-radius:12px;overflow:hidden;background:#fff;';
        var bar = document.createElement('div');
        bar.style.cssText = 'padding:10px 14px;background:#f7f9fc;border-bottom:1px solid #e6ebf2;display:flex;gap:10px;';
        var dl = document.createElement('button');
        dl.textContent = '下载报告 (HTML/PDF)';
        dl.style.cssText = 'border:1px solid #378ADD;background:#378ADD;color:#fff;border-radius:8px;padding:8px 14px;font-size:13px;cursor:pointer;';
        dl.onclick = function(){
          var b = new Blob([html], {type:'text/html'});
          var a = document.createElement('a');
          a.href = URL.createObjectURL(b);
          a.download = name + '_合规体检报告.html';
          a.click();
        };
        bar.appendChild(dl);
        var ifr = document.createElement('iframe');
        ifr.srcdoc = html;
        ifr.style.cssText = 'width:100%;height:1000px;border:0;display:block;';
        box.appendChild(bar);
        box.appendChild(ifr);
        result.appendChild(box);
      });
    });
  }).catch(function(){
    msg.style.color = '#E24B4A';
    msg.textContent = '无法连接到合规体检服务。请确认服务正在运行（已执行 python webapp.py 且无报错），或检查网络后重试。';
  });
};
</script>
</body></html>"""


def run_analysis(name, docs):
    """docs: [(src, text), ...]  -> 报告 HTML 或 None"""
    if not docs:
        return None
    terms = load_client_terms(ACTIVE_CLIENT)
    results, level_count, cat_count, term_count = analyze(docs, terms)
    return build_html(name, results, level_count, cat_count, term_count, top=10)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, ctype, body):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index", "/index.html"):
            self._send(200, "text/html; charset=utf-8", PAGE)
        else:
            self._send(404, "text/plain; charset=utf-8", "not found")

    def do_POST(self):
        if self.path == "/analyze":
            try:
                raw = self.headers.get("Content-Length", "")
                try:
                    n = int(raw) if raw.strip() else 0
                except ValueError:
                    self._send(200, "text/html; charset=utf-8",
                               friendly_error_html("提交数据长度异常",
                                   "请求头中的内容长度无法识别（可能被网络代理截断或浏览器异常）。",
                                   "请刷新页面后重试；若仍失败，多为网络中断，请检查连接后重试。"))
                    return
                if n == 0:
                    self._send(200, "text/html; charset=utf-8",
                               friendly_error_html("未收到任何内容",
                                   "浏览器没有把文案数据发送过来。",
                                   "请重新选择文件或粘贴文案后再点击「生成合规体检报告」。"))
                    return
                if n > MAX_BODY:
                    self._send(200, "text/html; charset=utf-8",
                               friendly_error_html("提交内容过大",
                                   f"本次上传约 {n // 1024} KB，超过了单次 {MAX_BODY // 1024 // 1024} MB 的上限。",
                                   "请分批次上传，或先清理超大文件（如整本书、长日志、压缩包内的文本）。"))
                    return
                body = self.rfile.read(n)
                try:
                    data = json.loads(body or b"{}")
                except json.JSONDecodeError:
                    self._send(200, "text/html; charset=utf-8",
                               friendly_error_html("提交数据格式错误",
                                   "浏览器发送的数据不是有效的格式（非标准 JSON）。",
                                   "请刷新页面后重试；若使用旧版浏览器，建议更换为最新版 Chrome / Edge。"))
                    return
                name = (data.get("name") or "贵司").strip()
                docs = [
                    (str(d.get("src", "")), str(d.get("text", "")))
                    for d in data.get("docs", [])
                    if str(d.get("text", "")).strip()
                ]
                if not docs:
                    self._send(200, "text/html; charset=utf-8",
                               friendly_error_html("没有可分析的文案",
                                   "收到的内容里没有可识别的文案（仅支持 .txt / .md，且内容不能为空）。",
                                   "请确认文件为 .txt 或 .md 文本；或直接在下方文本框粘贴文案（每行一条），再点生成。"))
                    return
                try:
                    html = run_analysis(name, docs)
                except Exception as e:
                    self._send(200, "text/html; charset=utf-8",
                               friendly_error_html("分析过程出现异常",
                                   f"系统在扫描文案时出错：{esc(str(e))[:200]}",
                                   "请尝试：① 去掉可疑文件后重试；② 分批上传；③ 直接粘贴文案。如持续出现，请联系我们并附上出错的文案。"))
                    return
                self._send(200, "text/html; charset=utf-8", html)
            except Exception as e:
                self._send(200, "text/html; charset=utf-8",
                           friendly_error_html("服务处理失败",
                               f"服务未预期地中断：{esc(str(e))[:200]}",
                               "请稍后重试；若反复出现，请重启服务（重新运行 python webapp.py）或联系我们。"))
        else:
            self._send(404, "text/plain; charset=utf-8", "not found")

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser(description="合规体检在线提交页")
    ap.add_argument("--port", type=int, default=8000, help="监听端口")
    ap.add_argument("--client", default=None,
                    help="客户资料目录（含 banned_words.md / brand.md）；缺省用内置 demo_client")
    args = ap.parse_args()

    # 显式校验客户目录：与 review.py / generate_report.py 行为一致
    # 致命（不存在/非目录）-> 报错退出；目录存在但缺词表 -> 警告后回退内置基线
    client_dir = args.client or CLIENT
    ok, msg = validate_client_dir(client_dir)
    if not ok:
        print("【错误】" + msg, file=sys.stderr)
        sys.exit(2)
    if msg:
        print(msg, file=sys.stderr)
    global ACTIVE_CLIENT
    ACTIVE_CLIENT = client_dir
    print(f"合规体检在线页已启动： http://127.0.0.1:{args.port}  (Ctrl+C 停止)")
    print(f"当前使用客户词库： {client_dir}")
    HTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
