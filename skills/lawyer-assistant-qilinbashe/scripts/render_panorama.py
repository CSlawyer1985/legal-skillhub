#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_panorama.py — 律师助手全景图（节点树状图）生成器

功能：
  1. 扫描技能包 agents/ 目录，按「律师实务条线」自动分类，生成全景图 STAGES 数据；
  2. 读取版本号 / 技能文件数 / 总文件数 / 今日日期，注入模板 scripts/panorama_template.html；
  3. 输出 assets/律师助手节点树状图.html。

  阶段（实务条线）与子目录（具体技能）全部来自技能包真实 agents，全量精准匹配：
  技能包增删技能后，重跑本脚本即自动更新全景图，无需手工改数据。

用法：
  python render_panorama.py                      # 重新生成 assets/ 下的最新图
  python render_panorama.py --check             # 校验已生成图的版本/技能数/文件数 == 技能包真实状态
  python render_panorama.py [源目录] [输出HTML]  # 自定义路径
"""

import argparse
import os
import re
import sys
import json
from datetime import datetime
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.dirname(HERE)  # scripts/ 的上级 = 技能包根
DEFAULT_OUT = os.path.join(DEFAULT_SRC, "assets", "律师助手节点树状图.html")
TEMPLATE = os.path.join(HERE, "panorama_template.html")

# 计数时跳过的目录与文件（与提交 zip 排除规则一致）
EXCLUDE_DIRS = {".git", "__pycache__", ".workbuddy-plugin", ".codebuddy-plugin",
                "node_modules", ".idea", ".vscode"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db", "desktop.ini",
                 "_icon.jpg", "_meta.json", "_skillhub_meta.json",
                 "fix2.py", "fix_submit_blockers.py", ".gitattributes", ".gitignore"}

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"

# ===== 律师实务条线顺序与元信息（icon / 标题 / 概述） =====
STAGE_ORDER = ['criminal', 'contract', 'family', 'labor', 'tort', 'ip',
               'bankrupt', 'execute', 'admin', 'arbitration', 'nonlit', 'tools']
STAGE_META = {
    'criminal':    ('⚔️', '刑事辩护业务',     '侦查·审查起诉·一审·二审·重罪·未成年·特殊程序·速裁，全阶段辩护'),
    'contract':    ('📑', '合同与商事纠纷',   '买卖·借款·借贷·保证·委托·建设·房屋·承揽·合伙·股权·运输等合同纠纷'),
    'family':      ('💑', '婚姻家事与继承',   '离婚·抚养·财产分割·继承·家事非诉协议'),
    'labor':       ('👷', '劳动争议',         '仲裁程序·证据体系·劳动关系认定·经济补偿·用人单位合规'),
    'tort':        ('🚧', '侵权与物业纠纷',   '交通事故·产品责任·医疗损害·网络侵权·物业服务'),
    'ip':          ('🔬', '知识产权',         '专利·商标·著作权侵权诉讼与合规申请'),
    'bankrupt':    ('🏦', '破产与清算',       '申请受理·债权申报·和解·重整·清算·管理人工作'),
    'execute':     ('🔨', '执行程序',         '申请执行·财产查控·强制措施·异议救济·和解终结'),
    'admin':       ('🏛️', '行政诉讼与复议',   '行政复议·立案分析·庭审代理'),
    'arbitration': ('⚖️', '商事仲裁',         '仲裁申请与程序推进'),
    'nonlit':      ('📋', '非诉与合规',       '合同审查起草·广告合规·数据合规·尽调·公司治理'),
    'tools':       ('🧰', '通用办案工具',     '总控路由·要件九步法·证据引擎·文书工程·类案检索·模拟法庭·期限时效'),
}

# 历史小白版编号兼容（当前包已无小白版，保留分支防御）
LITE_MAP = {
    '05A': 'tort', '09A': 'criminal', '15A': 'labor', '43A': 'tort', '51A': 'bankrupt', '61A': 'admin',
    '90B': 'contract', '91B': 'family', '92B': 'family', '93B': 'contract', '94B': 'tort', '95B': 'admin',
}
# 专业版主编号 → 条线
MAIN_MAP = {
    '09': 'criminal', '27': 'criminal', '01': 'criminal', '04': 'criminal', '40': 'criminal',
    '38': 'criminal', '44': 'criminal', '55': 'criminal', '14': 'criminal',
    '03': 'contract', '10': 'contract', '11': 'contract', '19': 'contract', '25': 'contract',
    '30': 'contract', '32': 'contract', '37': 'contract', '41': 'contract', '59': 'contract', '66': 'contract',
    '26': 'family', '28': 'family', '54': 'family', '57': 'family',
    '15': 'labor', '16': 'labor', '17': 'labor', '45': 'labor',
    '05': 'tort', '07': 'tort', '18': 'tort', '58': 'tort', '43': 'tort',
    '02': 'ip', '23': 'ip', '48': 'ip', '60': 'ip', '47': 'ip',
    '12': 'bankrupt', '13': 'bankrupt', '49': 'bankrupt', '50': 'bankrupt', '51': 'bankrupt',
    '52': 'bankrupt', '53': 'bankrupt', '56': 'bankrupt', '67': 'bankrupt',
    '08': 'execute', '33': 'execute', '34': 'execute', '35': 'execute', '36': 'execute',
    '64': 'execute', '65': 'execute',
    '61': 'admin', '62': 'admin', '63': 'admin',
    '22': 'arbitration',
    '20': 'nonlit', '21': 'nonlit', '24': 'nonlit', '29': 'nonlit', '84': 'nonlit', '85': 'nonlit', '92': 'nonlit',
    '31': 'tools', '39': 'tools', '70': 'tools', '71': 'tools', '73': 'tools', '74': 'tools', '75': 'tools',
    '76': 'tools', '77': 'tools', '78': 'tools', '79': 'tools', '80': 'tools', '81': 'tools', '82': 'tools',
    '83': 'tools', '86': 'tools', '87': 'tools', '88': 'tools', '89': 'tools', '72': 'tools', '91': 'tools',
}


def classify(fn):
    """把 agent 文件名归入实务条线，返回 (stage_key, is_lite, code)。"""
    base = fn[:-3] if fn.endswith('.md') else fn
    is_lite = '小白版' in base
    m = re.match(r'^([0-9]+[A-Za-z]?)', base)
    code = m.group(1) if m else base
    if code in LITE_MAP:
        return LITE_MAP[code], is_lite, code
    num = re.match(r'^([0-9]+)', code)
    num = num.group(1) if num else code
    return MAIN_MAP.get(num, 'tools'), is_lite, code


# ===================== 读取 / 计数 =====================

def read_version(src):
    sk = os.path.join(src, "SKILL.md")
    try:
        with open(sk, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^version:\s*"?([\d.]+)"?', line.strip())
                if m:
                    return m.group(1)
    except Exception as e:
        print("[render_panorama][WARN] 读取 SKILL.md 版本失败: %s" % e, file=sys.stderr)
    return ""


def count_agents(src):
    agents = os.path.join(src, "agents")
    if not os.path.isdir(agents):
        return 0
    # 含 00-全景图.md，与 verify_consistency.py / SKILL_INVENTORY 守门口径（105）保持一致，
    # 避免全景图 SKILLS 常量(104) 与 SKILL.md/README/manifest/INVENTORY(105) 打架。
    return len([f for f in os.listdir(agents) if f.endswith(".md")])


def count_files(src):
    total = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            if fn in EXCLUDE_FILES:
                continue
            total += 1
    return total


# ===================== frontmatter 解析 =====================

def parse_fm(text):
    """解析 agent 文件 frontmatter，返回 (fm_dict, body)。"""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.S)
    if not m:
        return {}, text
    block = m.group(1)
    body = text[m.end():]
    fm = {}
    lines = block.split('\n')
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        mm = re.match(r'^([A-Za-z_][\w]*):\s*(.*)$', line)
        if not mm:
            i += 1
            continue
        key = mm.group(1)
        val = mm.group(2).strip()
        # 内联列表 ["a","b"]
        if val.startswith('['):
            inner = val.strip('[]')
            items = [x.strip().strip('"').strip("'")
                     for x in re.split(r',\s*', inner) if x.strip()]
            fm[key] = items
            i += 1
            continue
        # 多行列表（缩进 - 项）
        if val == '' and i + 1 < n and re.match(r'^\s+-\s+', lines[i + 1]):
            items = []
            j = i + 1
            while j < n and re.match(r'^\s+-\s+', lines[j]):
                item = re.sub(r'^\s+-\s+', '', lines[j]).strip().strip('"').strip("'")
                if item:
                    items.append(item)
                j += 1
            fm[key] = items
            i = j
            continue
        fm[key] = val.strip('"').strip("'")
        i += 1
    return fm, body


def to_list(v):
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        if '|' in s:
            return [x.strip() for x in s.split('|') if x.strip()]
        return [s]
    return []


def extract_caps(body):
    """提取正文「我会做」区块的能力列表。"""
    caps = []
    cap = False
    for ln in body.split('\n'):
        if '我会做' in ln:
            cap = True
            continue
        if cap:
            s = ln.strip()
            if s.startswith('#'):
                break
            s2 = s.lstrip('>').strip() if s.startswith('>') else s
            if s2.startswith('-') or s2.startswith('*'):
                it = s2.lstrip('-*').strip().strip('"').strip("'")
                if it:
                    caps.append(it)
            elif s2 == '':
                continue
            else:
                if caps:
                    break
    seen, out = set(), []
    for c in caps:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


# ===================== 节点 / 阶段构造 =====================

def make_child(fm, body, is_lite, code, stage_icon, idx):
    name = fm.get('name') or code
    desc = (fm.get('description') or '').strip()
    caps = extract_caps(body)
    triggers = to_list(fm.get('trigger_keywords'))
    prompts = to_list(fm.get('colloquial_prompts'))
    related = to_list(fm.get('related_skills'))

    outputs = ["核心功能", "适用场景", "直接提问", "关联技能"]
    views = {
        "核心功能": {"type": "tpl",
                     "groups": [{"title": "我会做 / 核心能力",
                                 "items": (caps[:12] if caps else [desc])}]},
        "适用场景": {"type": "tpl",
                     "groups": [{"title": "触发关键词 / 适用场景",
                                 "items": (triggers if triggers else ["见技能说明"])}]},
        "直接提问": {"type": "tpl",
                     "groups": [{"title": "可直接复制的提问",
                                 "items": (prompts if prompts else ["请使用本技能协助处理本案。"])}]},
        "关联技能": {"type": "tpl",
                     "groups": [{"title": "关联技能",
                                 "items": (related if related else ["（无显式关联）"])}]},
    }

    num_prefix = re.match(r'^([0-9]+)', code)
    num_prefix = num_prefix.group(1) if num_prefix else code
    tags = [["tag-b", "小白版"]] if is_lite else [["tag-b", num_prefix + "号"]]

    prompt0 = prompts[0] if prompts else ("请使用「" + name + "」协助处理本案。")

    return {
        "num": CIRCLED[idx - 1] if idx - 1 < len(CIRCLED) else str(idx),
        "icon": stage_icon,
        "name": name,
        "detail": desc,
        "output": "、".join(outputs),
        "tags": tags,
        "reaction": prompt0,
        "prompt": prompt0,
        "views": views,
    }


def build_stages(src):
    agents_dir = os.path.join(src, "agents")
    files = sorted([f for f in os.listdir(agents_dir)
                    if f.endswith(".md") and f != "00-律师助手全景图.md"])
    buckets = {k: [] for k in STAGE_ORDER}
    for fn in files:
        p = os.path.join(agents_dir, fn)
        text = open(p, encoding="utf-8-sig", errors="replace").read()
        fm, body = parse_fm(text)
        stage, is_lite, code = classify(fn)
        buckets[stage].append((fm, body, is_lite, code))

    stages = []
    for si, sk in enumerate(STAGE_ORDER, 1):
        icon, title, count = STAGE_META[sk]
        children = []
        for idx, (fm, body, is_lite, code) in enumerate(buckets[sk], 1):
            children.append(make_child(fm, body, is_lite, code, icon, idx))
        stages.append({"cls": "p" + str(si), "icon": icon,
                       "title": title, "count": count, "children": children})
    return stages


# ===================== 渲染 =====================

def render(src, out):
    if not os.path.isfile(TEMPLATE):
        print("[render_panorama][ERROR] 模板不存在: %s" % TEMPLATE, file=sys.stderr)
        sys.exit(1)

    ver = read_version(src)
    skills = count_agents(src)
    files = count_files(src)
    today = datetime.now().strftime("%m-%d")

    if not ver:
        print("[render_panorama][ERROR] 未能从 SKILL.md 读取版本号", file=sys.stderr)
        sys.exit(1)

    disp_ver = ver if ver.lower().startswith("v") else "v" + ver
    stages = build_stages(src)

    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()

    tpl = tpl.replace("__VERSION__", disp_ver)
    tpl = tpl.replace("__SKILLS__", str(skills))
    tpl = tpl.replace("__FILES__", str(files))
    tpl = tpl.replace("__TODAY__", today)
    tpl = tpl.replace("__STAGES__", json.dumps(stages, ensure_ascii=False, indent=1))

    leftover = re.findall(r"__[A-Z]+__", tpl)
    if leftover:
        print("[render_panorama][WARN] 模板残留占位符未替换: %s" % sorted(set(leftover)), file=sys.stderr)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(tpl)

    return disp_ver, skills, files, today, len(stages), sum(len(s["children"]) for s in stages)


def extract_const(html, name):
    m = re.search(r'const\s+%s\s*=\s*"?([^";\n]+?)"?;' % re.escape(name), html)
    return m.group(1).strip() if m else None


def do_check(src, out):
    if not os.path.isfile(out):
        print("[render_panorama][CHECK] 未找到已生成图: %s" % out, file=sys.stderr)
        sys.exit(1)

    live_ver = read_version(src)
    live_skills = count_agents(src)
    live_files = count_files(src)
    today = datetime.now().strftime("%m-%d")

    html = open(out, encoding="utf-8").read()
    g_ver = extract_const(html, "VERSION")
    g_skills = extract_const(html, "SKILLS")
    g_files = extract_const(html, "FILES")
    g_today = extract_const(html, "TODAY")

    ok = True
    print("[render_panorama][CHECK] 逐项比对（图 vs 技能包真实状态）：")
    g_ver_raw = (g_ver or "").lstrip("v")
    if g_ver_raw == live_ver:
        print("  ✅ 版本号: 图=%s  包=%s" % (g_ver, live_ver))
    else:
        ok = False
        print("  ❌ 版本号: 图=%s  包=%s  （不一致！）" % (g_ver, live_ver))
    if g_skills == str(live_skills):
        print("  ✅ 技能文件数: 图=%s  包=%d" % (g_skills, live_skills))
    else:
        ok = False
        print("  ❌ 技能文件数: 图=%s  包=%d  （不一致！）" % (g_skills, live_skills))
    if g_files == str(live_files):
        print("  ✅ 总文件数: 图=%s  包=%d" % (g_files, live_files))
    else:
        ok = False
        print("  ❌ 总文件数: 图=%s  包=%d  （不一致！）" % (g_files, live_files))
    print("  ℹ️  时间轴今天: 图=%s  真实=%s%s" % (
        g_today, today, "  ✅" if g_today == today else "  ⚠️ 已过期，请重新生成"))

    if ok:
        print("[render_panorama][CHECK] 全部一致，可提交。")
        sys.exit(0)
    else:
        print("[render_panorama][CHECK] 存在差异，请先执行不带 --check 的生成命令刷新。", file=sys.stderr)
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="律师助手全景图生成器")
    ap.add_argument("src_pos", nargs="?", default=None, help="技能包源目录")
    ap.add_argument("out_pos", nargs="?", default=None, help="输出 HTML 路径")
    ap.add_argument("--src", default=None, help="技能包源目录")
    ap.add_argument("--out", default=None, help="输出 HTML 路径")
    ap.add_argument("--check", action="store_true", help="仅校验已生成图与技能包一致性")
    ap.add_argument("--refresh-source", action="store_true", help="重新生成并写回源 HTML 基线（默认行为）")
    args = ap.parse_args()

    src = args.src or args.src_pos or DEFAULT_SRC
    out = args.out or args.out_pos or DEFAULT_OUT

    if args.check:
        do_check(src, out)
        return

    disp_ver, skills, files, today, n_stage, n_node = render(src, out)
    print("[render_panorama] 版本=%s  技能文件=%d  总文件数=%d  今天=%s"
          % (disp_ver, skills, files, today))
    print("[render_panorama] 阶段数=%d  节点数=%d" % (n_stage, n_node))
    print("[render_panorama] 已生成: %s" % out)


if __name__ == "__main__":
    main()
