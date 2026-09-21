#!/usr/bin/env python3
"""
directory-index — 生成目录索引（Markdown 或 HTML）
扫描目录 → 生成索引文件 → (HTML 模式) 起服务器 → 打开浏览器

用法: python3 generate_index.py /path/to/dir --format md|html [--max-depth N] [--port 8427] [--no-open] [--tags '{}']
"""

import os
import sys
import json
import subprocess
import signal
import urllib.parse
import http.server
import argparse
import fnmatch
import platform
import html
from datetime import datetime

# ── 平台检测 ──────────────────────────────────────
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'

# ── 文件类型配置 ──────────────────────────────────────

FILE_TYPES = {
    '.xlsx': {'icon': 'XLS',  'css': 'icon-xlsx', 'label': 'Excel'},
    '.xlsm': {'icon': 'XLS',  'css': 'icon-xlsx', 'label': 'Excel'},
    '.xls':  {'icon': 'XLS',  'css': 'icon-xlsx', 'label': 'Excel'},
    '.csv':  {'icon': 'CSV',  'css': 'icon-xlsx', 'label': 'CSV'},
    '.docx': {'icon': 'DOC',  'css': 'icon-docx', 'label': 'Word'},
    '.doc':  {'icon': 'DOC',  'css': 'icon-docx', 'label': 'Word'},
    '.pdf':  {'icon': 'PDF',  'css': 'icon-pdf',   'label': 'PDF'},
    '.md':   {'icon': 'MD',   'css': 'icon-md',    'label': 'Markdown'},
    '.eml':  {'icon': 'EML',  'css': 'icon-eml',   'label': '邮件'},
    '.pptx': {'icon': 'PPT',  'css': 'icon-ppt',   'label': 'PPT'},
    '.ppt':  {'icon': 'PPT',  'css': 'icon-ppt',   'label': 'PPT'},
    '.txt':  {'icon': 'TXT',  'css': 'icon-txt',   'label': '文本'},
    '.png':  {'icon': 'IMG',  'css': 'icon-img',   'label': '图片'},
    '.jpg':  {'icon': 'IMG',  'css': 'icon-img',   'label': '图片'},
    '.jpeg': {'icon': 'IMG',  'css': 'icon-img',   'label': '图片'},
    '.gif':  {'icon': 'IMG',  'css': 'icon-img',   'label': '图片'},
    '.mp4':  {'icon': 'VID',  'css': 'icon-vid',   'label': '视频'},
    '.mp3':  {'icon': 'AUD',  'css': 'icon-aud',   'label': '音频'},
    '.zip':  {'icon': 'ZIP',  'css': 'icon-zip',   'label': '压缩包'},
    '.json': {'icon': 'JSON', 'css': 'icon-md',    'label': 'JSON'},
    '.html': {'icon': 'HTM',  'css': 'icon-md',    'label': 'HTML'},
    '.py':   {'icon': 'PY',   'css': 'icon-md',    'label': 'Python'},
}

DEFAULT_TYPE = {'icon': 'FILE', 'css': 'icon-default', 'label': '文件'}

TAG_STYLES = {
    'readonly': {'bg': '#fff', 'color': '#000', 'label': '只读'},
    'main':     {'bg': '#fff', 'color': '#000', 'label': '主文件'},
    'backup':   {'bg': '#fff', 'color': '#000', 'label': '备份'},
    'pending':  {'bg': '#fff', 'color': '#000', 'label': '待确认'},
}

# 默认跳过的目录（大型/无意义目录树）
SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv',
    '.next', '.nuxt', 'dist', 'build', '.cache',
    '.tox', '.mypy_cache', '.pytest_cache', '.hg',
}


def get_file_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    return FILE_TYPES.get(ext, DEFAULT_TYPE)


def get_size_str(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def match_tags(rel_path, tags_rules):
    """根据 glob 规则匹配标签"""
    matched = []
    basename = os.path.basename(rel_path)
    for tag_name, patterns in tags_rules.items():
        for pattern in patterns:
            if fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(rel_path, pattern):
                matched.append(tag_name)
                break
    return matched


def scan_directory(base_dir, tags_rules=None, max_depth=None):
    """扫描目录，返回结构化文件树（带 depth 信息）"""
    if tags_rules is None:
        tags_rules = {}

    entries = []
    skipped_dirs = []       # [(rel_path, reason), ...]
    skipped_depth = []      # 因为深度限制跳过的目录

    def _natural_sort_key(s):
        """自然排序 key：'2.0' 排在 '10.0' 前面"""
        import re
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

    def _scan(dirpath, rel_prefix='', depth=0):
        # 深度限制
        if max_depth is not None and depth > max_depth:
            return

        try:
            items = sorted(os.listdir(dirpath), key=_natural_sort_key)
        except PermissionError:
            skipped_dirs.append((rel_prefix or os.path.basename(dirpath), '权限不足'))
            return

        # 分离目录和文件
        dirs = []
        files = []
        for item in items:
            if item.startswith('.'):
                continue
            full = os.path.join(dirpath, item)
            rel = os.path.join(rel_prefix, item) if rel_prefix else item
            if os.path.isdir(full):
                # 跳过大型/无意义目录
                if item in SKIP_DIRS:
                    skipped_dirs.append((rel, f'默认跳过（{item}）'))
                    continue
                # 深度限制预检：如果下一层超限，记录并跳过
                if max_depth is not None and depth + 1 > max_depth:
                    skipped_depth.append(rel)
                    continue
                dirs.append((item, full, rel))
            else:
                files.append((item, full, rel))

        for name, full, rel in files:
            size = os.path.getsize(full)
            ftype = get_file_type(name)
            tags = match_tags(rel, tags_rules)
            # 排除自己生成的 index 文件
            if name.startswith('INDEX_') and (name.endswith('.html') or name.endswith('.py') or name.endswith('.md')):
                continue
            entries.append({
                'type': 'file',
                'name': name,
                'rel': rel,
                'depth': depth,
                'size': size,
                'size_str': get_size_str(size),
                'file_type': ftype,
                'tags': tags,
            })

        for name, full, rel in dirs:
            old_len = len(entries)
            _scan(full, rel, depth + 1)
            # 记录这个目录下有多少文件
            sub_count = len(entries) - old_len
            entries.insert(old_len, {
                'type': 'dir',
                'name': name,
                'rel': rel,
                'depth': depth,
                'file_count': sub_count,
            })

    _scan(base_dir)
    return entries, skipped_dirs, skipped_depth


# ── Markdown 生成 ──────────────────────────────────────

def generate_markdown(entries, dir_name, base_dir, skipped_dirs=None, skipped_depth=None):
    """生成 Markdown 索引页面（按目录层级用递进标题）"""
    file_count = sum(1 for e in entries if e['type'] == 'file')
    dir_count = sum(1 for e in entries if e['type'] == 'dir')
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    md_lines = [
        f'# {dir_name} · 文件索引',
        '',
        f'> {file_count} 个文件 · {dir_count} 个目录 · 生成于 {now}',
        '',
    ]

    # 跳过提示（带原因）
    if skipped_dirs:
        md_lines.append('> **已跳过的目录：**')
        for rel, reason in skipped_dirs:
            md_lines.append(f'> - `{rel}` — {reason}')
        md_lines.append('')
    if skipped_depth:
        md_lines.append(f'> **因深度限制未展开：** {", ".join(f"`{d}`" for d in skipped_depth)}')
        md_lines.append('')

    # 按目录层级递进
    for entry in entries:
        if entry['type'] == 'dir':
            depth = entry['depth']
            # 层级映射：depth 0→##, 1→###, 2→####, 3+→#####
            heading_level = min(2 + depth, 5)
            hashes = '#' * heading_level
            md_lines.append(f'{hashes} 📂 {entry["name"]} ({entry["file_count"]} 个文件)')
            md_lines.append('')
        else:
            ft = entry['file_type']
            tags = entry.get('tags', [])
            tag_strs = []
            for tag in tags:
                style = TAG_STYLES.get(tag, None)
                if style:
                    tag_strs.append(style['label'])
                else:
                    tag_strs.append(tag)
            tag_display = ' '.join(f'`{t}`' for t in tag_strs)

            size_str = entry['size_str']
            name = entry['name']

            # 深层文件加缩进
            indent = '  ' * entry['depth'] if entry['depth'] > 0 else ''
            line = f'{indent}- **{name}** — {ft["label"]} · {size_str}'
            if tag_display:
                line += f' · {tag_display}'
            md_lines.append(line)

    md_lines.append('')
    md_lines.append('---')
    md_lines.append(f'*由 directory-index skill 自动生成 · {now}*')
    md_lines.append('')

    return '\n'.join(md_lines)


# ── HTML 生成 ──────────────────────────────────────

def generate_html(entries, dir_name, base_dir, skipped_dirs=None, skipped_depth=None, port=8427):
    """生成 HTML 页面（可折叠树形结构，支持多层嵌套）"""
    file_count = sum(1 for e in entries if e['type'] == 'file')
    dir_count = sum(1 for e in entries if e['type'] == 'dir')
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # 构建树形结构
    tree = build_tree(entries)

    # 跳过目录提示（带原因）
    skip_notes = []
    if skipped_dirs:
        skip_items = ''.join(
            f'<div class="skip-item"><code>{html.escape(rel, quote=True)}</code> — {html.escape(reason, quote=True)}</div>'
            for rel, reason in skipped_dirs
        )
        skip_notes.append(f'<div class="skip-section"><strong>已跳过的目录：</strong>{skip_items}</div>')
    if skipped_depth:
        depth_items = ', '.join(f'<code>{html.escape(d, quote=True)}</code>' for d in skipped_depth)
        skip_notes.append(f'<div class="skip-section"><strong>因深度限制未展开：</strong>{depth_items}</div>')
    skip_note_html = f'<div class="skip-note">{"".join(skip_notes)}</div>' if skip_notes else ''

    # 统计
    total_size = sum(e['size'] for e in entries if e['type'] == 'file')
    total_size_str = get_size_str(total_size)

    # 渲染树
    tree_html = render_tree_html(tree)

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(dir_name, quote=True)} · 文件索引</title>
<script>
// 自动跳转：如果通过 file:// 打开且服务器正在运行，自动跳转到服务器地址
if (window.location.protocol === 'file:') {{
  fetch('http://localhost:{port}/health', {{ method: 'GET', mode: 'no-cors', cache: 'no-store' }})
    .then(function() {{
      window.location.href = 'http://localhost:{port}/';
    }})
    .catch(function() {{
      // 服务器未运行，保持当前页面并显示提示
    }});
}}
</script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #fff; color: #111; line-height: 1.6;
  }}
  .header {{
    border-bottom: 1px solid #000; padding: 16px 24px;
    position: sticky; top: 0; background: #fff; z-index: 100;
  }}
  .header h1 {{ font-size: 18px; font-weight: 600; }}
  .header .meta {{ font-size: 12px; color: #666; margin-top: 2px; }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 20px 24px 60px; }}
  .stats {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .stat-card {{ border: 1px solid #000; padding: 12px 20px; text-align: center; flex: 1; min-width: 100px; }}
  .stat-num {{ font-size: 22px; font-weight: 700; }}
  .stat-label {{ font-size: 11px; color: #666; }}
  .skip-note {{ font-size: 12px; color: #666; margin-bottom: 16px; padding: 10px 14px; border: 1px solid #ccc; }}
  .skip-section {{ margin-bottom: 6px; }}
  .skip-item {{ margin-left: 8px; margin-top: 2px; font-size: 11px; }}
  .toolbar {{ display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }}
  .toolbar button {{
    font-size: 12px; padding: 5px 12px;
    border: 1px solid #000; background: #fff; color: #111; cursor: pointer;
  }}
  .toolbar button:hover {{ background: #111; color: #fff; }}
  .search-box {{
    width: 100%; padding: 8px 14px; margin-bottom: 16px;
    border: 1px solid #000; font-size: 13px; background: #fff; outline: none;
  }}
  .tree-node {{ margin-bottom: 2px; }}
  .dir-header {{
    display: flex; align-items: center; gap: 8px;
    padding: 8px 12px; background: #f5f5f5;
    border: 1px solid #000; cursor: pointer; user-select: none;
    transition: background 0.15s;
  }}
  .dir-header:hover {{ background: #eee; }}
  .dir-arrow {{ font-size: 10px; color: #666; width: 16px; text-align: center; transition: transform 0.2s; }}
  .dir-arrow.collapsed {{ transform: rotate(-90deg); }}
  .dir-name {{ font-size: 14px; font-weight: 600; }}
  .dir-count {{ font-size: 11px; color: #666; margin-left: auto; }}
  .dir-children {{
    margin-left: 16px; padding-left: 12px;
    border-left: 1px solid #ccc; overflow: hidden;
    transition: max-height 0.2s ease;
  }}
  .dir-children.collapsed {{ max-height: 0 !important; padding: 0; margin: 0; border-left: none; overflow: hidden; }}
  .file-card {{
    background: #fff; border: 1px solid #000;
    padding: 10px 16px; margin-bottom: 4px;
    display: flex; align-items: center; gap: 12px;
  }}
  .file-card:hover {{ background: #f9f9f9; }}
  .file-icon {{
    width: 32px; height: 32px; border: 1px solid #000;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700; flex-shrink: 0;
  }}
  .icon-xlsx, .icon-docx, .icon-pdf, .icon-md, .icon-eml,
  .icon-ppt, .icon-img, .icon-vid, .icon-aud, .icon-zip, .icon-txt, .icon-default {{
    background: #fff; color: #000;
  }}
  .file-info {{ flex: 1; min-width: 0; }}
  .file-name {{
    font-size: 14px; font-weight: 500; color: #000;
    cursor: pointer; text-decoration: none;
    display: inline-block;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 500px;
    background: none; border: none; padding: 0; font-family: inherit;
  }}
  .file-name:hover {{ text-decoration: underline; }}
  .file-desc {{ font-size: 12px; color: #666; margin-top: 1px; }}
  .file-meta {{ display: flex; align-items: center; gap: 8px; flex-shrink: 0; }}
  .file-size {{ font-size: 11px; color: #666; border: 1px solid #ccc; padding: 2px 8px; }}
  .tag {{
    font-size: 10px; padding: 2px 8px;
    border: 1px solid #000; font-weight: 500; background: #fff; color: #000;
  }}
  .btn-reveal {{
    font-size: 11px; color: #111; background: none;
    border: 1px solid #000; padding: 3px 10px; cursor: pointer;
  }}
  .btn-reveal:hover {{ background: #111; color: #fff; }}
  .toast {{
    position: fixed; bottom: 24px; left: 50%;
    transform: translateX(-50%) translateY(60px);
    background: #111; color: #fff;
    padding: 10px 20px; font-size: 13px;
    opacity: 0; transition: all 0.3s;
    z-index: 999; pointer-events: none;
  }}
  .toast.show {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
  .hidden {{ display: none !important; }}
</style>
</head>
<body>
<div class="header">
  <h1>{html.escape(dir_name, quote=True)} · 文件索引</h1>
  <div class="meta">点击文件名用默认应用打开 · 右侧「定位」在资源管理器/Finder 中显示 · 生成于 {now}</div>
</div>
<div class="container">
  <div id="server-banner" style="display:none;background:#fff3cd;border:1px solid #000;color:#111;padding:10px 16px;margin-bottom:16px;font-size:13px">
    服务器未运行 — 点击文件名或「定位」无法使用。请先启动服务器：<code style="background:#f5f5f5;padding:2px 6px;border:1px solid #ccc">python3 INDEX_*.py</code>
  </div>
  <div class="stats">
    <div class="stat-card"><div class="stat-num">{file_count}</div><div class="stat-label">文件</div></div>
    <div class="stat-card"><div class="stat-num">{dir_count}</div><div class="stat-label">目录</div></div>
    <div class="stat-card"><div class="stat-num">{total_size_str}</div><div class="stat-label">总大小</div></div>
  </div>
  {skip_note_html}
  <input class="search-box" type="text" placeholder="搜索文件名..." oninput="filterFiles(this.value)">
  <div class="toolbar">
    <button onclick="toggleAll(false)">全部展开</button>
    <button onclick="toggleAll(true)">全部折叠</button>
  </div>
  {tree_html}
</div>
<div class="toast" id="toast"></div>
<script>
// 检测是否通过 file:// 协议直接打开
if (window.location.protocol === 'file:') {{
  document.addEventListener('DOMContentLoaded', function() {{
    var banner = document.getElementById('server-banner');
    if (banner) {{
      banner.style.display = 'block';
      banner.innerHTML = '当前通过本地文件打开，点击文件无法使用。<br>请通过服务器访问：<code style="background:#f5f5f5;padding:2px 6px;border:1px solid #ccc">http://localhost:{port}/</code>（或重新运行生成脚本自动打开）';
    }}
  }});
}}
function openFile(path) {{
  if (window.location.protocol === 'file:') {{
    showToast('请通过 http://localhost:{port}/ 访问以使用此功能');
    return;
  }}
  fetch('/open?path=' + path)
    .then(r => r.json())
    .then(d => {{
      if (d.status === 'ok') showToast('已打开: ' + decodeURIComponent(path).split('/').pop());
      else showToast('打开失败: ' + (d.message || '未知错误'));
    }})
    .catch(() => {{
      showToast('服务器未响应，请先启动服务器');
      showServerDown();
    }});
}}
function revealFile(path) {{
  fetch('/reveal?path=' + path)
    .then(r => r.json())
    .then(d => {{
      if (d.status === 'ok') showToast('已在 Finder 中定位');
      else showToast('定位失败: ' + (d.message || '未知错误'));
    }})
    .catch(() => {{
      showToast('服务器未响应，请先启动服务器');
      showServerDown();
    }});
}}
function showServerDown() {{
  const b = document.getElementById('server-banner');
  if (b) b.style.display = 'block';
}}
function toggleDir(el) {{
  const children = el.parentElement.querySelector('.dir-children');
  const arrow = el.querySelector('.dir-arrow');
  if (children) {{
    children.classList.toggle('collapsed');
    arrow.classList.toggle('collapsed');
  }}
}}
function toggleAll(collapse) {{
  document.querySelectorAll('.dir-children').forEach(el => {{
    if (collapse) el.classList.add('collapsed');
    else el.classList.remove('collapsed');
  }});
  document.querySelectorAll('.dir-arrow').forEach(el => {{
    if (collapse) el.classList.add('collapsed');
    else el.classList.remove('collapsed');
  }});
}}
function filterFiles(query) {{
  query = query.toLowerCase();
  document.querySelectorAll('.file-card').forEach(card => {{
    const name = card.getAttribute('data-name').toLowerCase();
    card.classList.toggle('hidden', query && !name.includes(query));
  }});
  // 搜索时自动展开所有目录
  if (query) toggleAll(false);
}}
let toastTimer;
function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2000);
}}
// 页面加载：检测服务器 + 默认折叠
window.addEventListener('DOMContentLoaded', function() {{
  fetch('/health').catch(function() {{ showServerDown(); }});
  // 默认折叠所有目录
  toggleAll(true);
}});
</script>
</body></html>'''

    return html_content


def build_tree(entries):
    """将扁平 entries 列表转为嵌套树结构"""
    root = {'type': 'root', 'children': []}
    dir_stack = [root]  # 当前目录路径栈

    for entry in entries:
        depth = entry['depth']

        # 调整栈深度
        while len(dir_stack) > depth + 1:
            dir_stack.pop()

        if entry['type'] == 'dir':
            node = {**entry, 'children': []}
            dir_stack[-1]['children'].append(node)
            dir_stack.append(node)
        else:
            dir_stack[-1]['children'].append(entry)

    return root


def render_tree_html(tree):
    """递归渲染树形 HTML"""
    parts = []
    for child in tree.get('children', []):
        if child['type'] == 'dir':
            parts.append(render_dir_html(child))
        else:
            parts.append(render_file_html(child))
    return '\n'.join(parts)


def render_dir_html(dir_node):
    """渲染一个目录节点（可折叠）"""
    name = html.escape(dir_node['name'], quote=True)
    count = dir_node['file_count']
    children_html = '\n'.join(
        render_dir_html(c) if c['type'] == 'dir' else render_file_html(c)
        for c in dir_node.get('children', [])
    )
    return f'''<div class="tree-node">
  <div class="dir-header" onclick="toggleDir(this)">
    <span class="dir-arrow">▼</span>
    <span class="dir-name">📂 {name}</span>
    <span class="dir-count">{count} 个文件</span>
  </div>
  <div class="dir-children">
    {children_html}
  </div>
</div>'''


def render_file_html(file_entry):
    """渲染一个文件卡片"""
    ft = file_entry['file_type']
    rel_js = file_entry['rel'].replace('\\', '/')
    encoded_rel = urllib.parse.quote(rel_js, safe='')
    name_escaped = html.escape(file_entry['name'], quote=True)
    name_display = file_entry['name']
    if len(name_display) > 60:
        name_display = name_display[:57] + '...'
    name_display_escaped = html.escape(name_display, quote=True)

    # 标签
    tags_html = ''
    for tag in file_entry.get('tags', []):
        style = TAG_STYLES.get(tag, {'bg': '#fff', 'color': '#000', 'label': tag})
        tags_html += f'<span class="tag" style="background:{style["bg"]};color:{style["color"]}">{html.escape(style["label"], quote=True)}</span>'

    return f'''<div class="file-card" data-name="{name_escaped}">
  <div class="file-icon {ft['css']}">{ft['icon']}</div>
  <div class="file-info">
    <span class="file-name" onclick="openFile('{encoded_rel}')" title="{name_escaped}">{name_display_escaped}</span>
    <div class="file-desc">{ft['label']}</div>
  </div>
  <div class="file-meta">
    {tags_html}
    <span class="file-size">{file_entry['size_str']}</span>
    <button class="btn-reveal" onclick="revealFile('{encoded_rel}')">定位</button>
  </div>
</div>'''


# ── 服务器脚本生成 ──────────────────────────────────────

def generate_server_script(html_filename, port, base_dir):
    """生成可独立运行的服务器脚本（跨平台）"""
    template = r'''#!/usr/bin/env python3
# 文件索引服务器 - 自动生成
# 目录: __BASE_DIR__
# 用法: python3 __SCRIPT_NAME__
# 浏览器打开: http://localhost:__PORT__

import http.server
import subprocess
import os
import sys
import urllib.parse
import json
import signal
import platform

PORT = __PORT__
BASE_DIR = __BASE_DIR__
HTML_FILE = "__HTML_FILE__"
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'

def open_file(path):
    """用系统默认应用打开文件（跨平台）"""
    if IS_WINDOWS:
        os.startfile(path)
    elif IS_MACOS:
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])

def reveal_file(path):
    """在资源管理器/Finder 中定位文件（跨平台）"""
    if IS_WINDOWS:
        subprocess.Popen(['explorer', '/select,', path])
    elif IS_MACOS:
        subprocess.Popen(['open', '-R', path])
    else:
        # Linux: 尝试用 dbus 打开所在目录
        dir_path = os.path.dirname(path)
        subprocess.Popen(['xdg-open', dir_path])

def open_browser(url):
    """打开浏览器（跨平台）"""
    if IS_WINDOWS:
        subprocess.Popen(['start', url], shell=True)
    elif IS_MACOS:
        subprocess.Popen(['open', url])
    else:
        subprocess.Popen(['xdg-open', url])

class IndexHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ('/', '/index.html'):
            html_path = os.path.join(BASE_DIR, HTML_FILE)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            with open(html_path, 'rb') as f:
                self.wfile.write(f.read())
            return
        if parsed.path == '/open':
            self._handle_action('open', parsed)
            return
        if parsed.path == '/reveal':
            self._handle_action('reveal', parsed)
            return
        if parsed.path == '/health':
            self._send_json(200, {"status": "ok"})
            return
        self.send_error(404)

    def _handle_action(self, action, parsed):
        params = urllib.parse.parse_qs(parsed.query)
        rel_path = params.get('path', [''])[0]
        rel_path = urllib.parse.unquote(rel_path)
        if not rel_path:
            self._send_json(400, {"status": "error", "message": "Missing path"})
            return
        full_path = os.path.normpath(os.path.join(BASE_DIR, rel_path))
        # 使用 commonpath 进行可靠的路径遍历检查（兼容 Windows 大小写不敏感文件系统）
        try:
            if os.path.commonpath([full_path, BASE_DIR]) != BASE_DIR:
                self._send_json(403, {"status": "error", "message": "Access denied"})
                return
        except ValueError:
            self._send_json(403, {"status": "error", "message": "Access denied"})
            return
        if not os.path.exists(full_path):
            self._send_json(404, {"status": "error", "message": "File not found", "path": rel_path})
            return
        try:
            if action == 'open':
                open_file(full_path)
            else:
                reveal_file(full_path)
            self._send_json(200, {"status": "ok", "action": action, "path": rel_path})
        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})

    def _send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, fmt, *args):
        msg = fmt % args
        if '/open' in msg or '/reveal' in msg:
            print(f"  📂 {msg}")


def kill_existing():
    """杀掉占用端口的旧进程（跨平台）"""
    try:
        if IS_WINDOWS:
            r = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True, text=True
            )
            for line in r.stdout.splitlines():
                if f':{PORT}' in line and 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    if pid and pid != str(os.getpid()):
                        subprocess.run(['taskkill', '/F', '/PID', pid],
                                       capture_output=True)
        else:
            r = subprocess.run(['lsof', '-ti', f':{PORT}'],
                               capture_output=True, text=True)
            for pid in r.stdout.strip().split('\n'):
                pid = pid.strip()
                if pid and pid != str(os.getpid()):
                    try: os.kill(int(pid), signal.SIGTERM)
                    except: pass
    except: pass


if __name__ == '__main__':
    kill_existing()
    print(f"\n  文件索引服务器")
    print(f"  ────────────────")
    print(f"  目录: {BASE_DIR}")
    print(f"  地址: http://localhost:{PORT}")
    print(f"  平台: {platform.system()}")
    print(f"  Ctrl+C 退出\n")
    class ReuseHTTPServer(http.server.HTTPServer):
        allow_reuse_address = True
    server = ReuseHTTPServer(('127.0.0.1', PORT), IndexHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  已退出")
        server.server_close()
'''
    script_name = html_filename.replace('.html', '_server.py')
    return (template
        .replace('__BASE_DIR__', repr(base_dir))
        .replace('__PORT__', str(port))
        .replace('__HTML_FILE__', html_filename)
        .replace('__SCRIPT_NAME__', script_name))


# ── 服务器启动 ──────────────────────────────────────

def kill_port_process(port):
    """杀掉占用指定端口的进程（跨平台）"""
    try:
        if IS_WINDOWS:
            r = subprocess.run(
                ['netstat', '-ano'], capture_output=True, text=True
            )
            for line in r.stdout.splitlines():
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    if pid:
                        subprocess.run(['taskkill', '/F', '/PID', pid],
                                       capture_output=True)
                        print(f"  已终止旧进程 PID={pid}")
        else:
            r = subprocess.run(['lsof', '-ti', f':{port}'],
                               capture_output=True, text=True)
            for pid in r.stdout.strip().split('\n'):
                pid = pid.strip()
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"  已终止旧进程 PID={pid}")
                    except:
                        pass
    except:
        pass


def open_in_browser(url):
    """在系统浏览器中打开 URL（跨平台）"""
    try:
        if IS_WINDOWS:
            subprocess.Popen(['start', url], shell=True)
        elif IS_MACOS:
            subprocess.Popen(['open', url])
        else:
            subprocess.Popen(['xdg-open', url])
    except:
        pass


def run_server(html_filename, server_filename, port, base_dir, open_browser=True):
    """启动服务器"""
    # 杀旧进程
    kill_port_process(port)

    # 启动服务器
    subprocess.Popen(
        [sys.executable, server_filename],
        cwd=base_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    import time
    time.sleep(1)

    # 验证
    try:
        import urllib.request
        urllib.request.urlopen(f'http://localhost:{port}/health', timeout=2)
        print(f"  ✅ 服务器已启动 http://localhost:{port}")
    except:
        print(f"  ⚠️ 服务器可能未启动成功，请手动运行: python3 {server_filename}")

    if open_browser:
        open_in_browser(f'http://localhost:{port}')
        print(f"  🌐 已在浏览器中打开")


# ── 主流程 ──────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='生成目录文件索引（Markdown 或 HTML）')
    parser.add_argument('directory', help='目标目录路径')
    parser.add_argument('--format', choices=['md', 'html'], required=True,
                        help='输出格式: md=纯展示 Markdown, html=可跳转交互式 HTML')
    parser.add_argument('--max-depth', type=int, default=None,
                        help='最大递归深度（默认不限制）')
    parser.add_argument('--port', type=int, default=8427, help='服务器端口 (默认 8427, 仅 html)')
    parser.add_argument('--no-open', action='store_true', help='不自动打开浏览器 (仅 html)')
    parser.add_argument('--tags', type=str, default='{}', help='标签规则 JSON')
    args = parser.parse_args()

    base_dir = os.path.abspath(args.directory)
    if not os.path.isdir(base_dir):
        print(f"错误: 目录不存在: {base_dir}")
        sys.exit(1)

    dir_name = os.path.basename(base_dir) or 'root'
    tags_rules = json.loads(args.tags)

    depth_info = f"（最大深度 {args.max_depth}）" if args.max_depth is not None else "（无深度限制）"
    print(f"\n  📁 扫描目录: {base_dir} {depth_info}")
    entries, skipped_dirs, skipped_depth = scan_directory(base_dir, tags_rules, max_depth=args.max_depth)
    file_count = sum(1 for e in entries if e['type'] == 'file')
    dir_count = sum(1 for e in entries if e['type'] == 'dir')
    print(f"  📄 发现 {file_count} 个文件 · {dir_count} 个目录")
    if skipped_dirs:
        print(f"  ⏭️  已跳过 {len(skipped_dirs)} 个目录：")
        for rel, reason in skipped_dirs:
            print(f"      - {rel}（{reason}）")
    if skipped_depth:
        print(f"  📏 因深度限制未展开 {len(skipped_depth)} 个子目录：{', '.join(skipped_depth)}")

    if args.format == 'md':
        # ── Markdown 纯展示版 ──
        md = generate_markdown(entries, dir_name, base_dir, skipped_dirs, skipped_depth)
        md_filename = f'INDEX_{dir_name}.md'
        md_path = os.path.join(base_dir, md_filename)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"  📝 已生成: {md_filename}")
        print(f"  ✅ 完成（Markdown 纯展示版，无需服务器）")

    else:
        # ── HTML 可跳转版 ──
        html = generate_html(entries, dir_name, base_dir, skipped_dirs, skipped_depth, port=args.port)
        html_filename = f'INDEX_{dir_name}.html'
        html_path = os.path.join(base_dir, html_filename)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  📝 已生成: {html_filename}")

        # 生成服务器脚本
        server_filename = f'INDEX_{dir_name}_server.py'
        server_path = os.path.join(base_dir, server_filename)
        server_code = generate_server_script(html_filename, args.port, base_dir)
        with open(server_path, 'w', encoding='utf-8') as f:
            f.write(server_code)
        os.chmod(server_path, 0o755)
        print(f"  🔧 已生成: {server_filename}")

        # 启动服务器
        print(f"\n  🚀 启动服务器...")
        run_server(html_filename, server_path, args.port, base_dir, open_browser=not args.no_open)

        print(f"\n  用法:")
        print(f"    浏览器打开: http://localhost:{args.port}")
        print(f"    重启服务器: python3 {server_filename}")
        if IS_WINDOWS:
            print(f"    停止服务器: netstat -ano | findstr :{args.port} → taskkill /F /PID <pid>")
        else:
            print(f"    停止服务器: kill $(lsof -ti :{args.port})")


if __name__ == '__main__':
    main()
