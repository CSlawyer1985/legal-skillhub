#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预检验脚本 - 在运行 pipeline 前自动诊断 JSON 结构和文本匹配问题

用法:
  python3 preflight_check.py <docx文件> <changes.json> [--fix]

自动完成:
  [1/5] JSON 格式校验（扁平 vs 标准）→ 自动转换
  [2/5] 读取原始 docx 段落（精确 XML 文本）
  [3/5] 段落索引越界检测
  [4/5] 文本匹配测试（完整/部分/失败）
  [5/5] --fix: 自动修正段落索引 + 生成 _fixed.json

输入 changes.json 标准格式:
{
  "author": "Claude",
  "revisions": [
    {
      "paragraph_index": 42,
      "original_text": "原文本",
      "revised_text": "建议修改",
      "severity": "高风险",
      ...
    }
  ],
  "comments": [
    {
      "paragraph_index": 55,
      "highlight_text": "原文本",
      "comment": "批注内容",
      "severity": "中风险",
      ...
    }
  ]
}

也可接受扁平格式（自动转换）:
{
  "changes": [
    {
      "paragraph_index": 42,
      "original_text": "原文本",
      "suggestion": "修订文本（有则→revision，无则→comment）",
      "severity": "高风险"
    }
  ]
}

退出码:
  0 = 全部通过，无需修复
  1 = 发现问题（已生成 _fixed.json 或格式错误）
  2 = 参数错误或 docx 读取失败
"""

import json, sys, zipfile, re, os
import xml.etree.ElementTree as ET
from pathlib import Path

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

# ── ANSI 颜色 ──────────────────────────────────────────────────────────────
def c_ok(s):   return f'\033[92m{s}\033[0m'
def c_warn(s): return f'\033[93m{s}\033[0m'
def c_fail(s): return f'\033[91m{s}\033[0m'
def c_info(s): return f'\033[94m{s}\033[0m'
def bold(s):   return f'\033[1m{s}\033[0m'


def qn(tag):
    return f'{{{W}}}{tag}'


# ── 文档解析 ────────────────────────────────────────────────────────────────
def get_paragraphs(docx_path):
    """从 docx 提取所有段落元素和纯文本"""
    with zipfile.ZipFile(docx_path) as z:
        tree = ET.parse(z.open('word/document.xml'))
    root = tree.getroot()
    body = root.find(qn('body'))
    all_p = list(body.iter(qn('p')))
    paras = []
    for i, p in enumerate(all_p):
        parts = []
        for r in p.iter(qn('r')):
            t = r.find(qn('t'))
            if t is not None and t.text:
                parts.append(t.text)
        text = ''.join(parts).strip()
        paras.append({'index': i, 'text': text, 'elem': p})
    return paras


# ── JSON 格式处理 ──────────────────────────────────────────────────────────
def detect_json_format(changes):
    """返回: 'correct' | 'flat' | 'unknown'"""
    keys = set(changes.keys())
    if 'revisions' in keys or 'comments' in keys:
        return 'correct'
    if 'changes' in keys and isinstance(changes.get('changes'), list):
        return 'flat'
    return 'unknown'


def normalize_changes(changes):
    """
    将扁平 {changes: [...]} 格式转换为标准 {revisions, comments} 结构。
    判断规则：有 revised_text/suggestion → revision；否则 → comment。
    """
    items = changes.get('changes', [])
    revisions, comments = [], []

    for item in items:
        pidx   = item.get('paragraph_index')
        orig   = item.get('original_text', '')
        revtxt = item.get('suggestion', item.get('revised_text', ''))
        sev    = item.get('severity', '中风险')
        reason = item.get('reason', '')
        legal  = item.get('legal_basis', '')
        cmt    = item.get('comment', '')

        base = dict(paragraph_index=pidx, severity=sev,
                    reason=reason, legal_basis=legal, fallback_to_comment=True)

        if revtxt:
            revisions.append({**base, 'original_text': orig, 'revised_text': revtxt})
        else:
            comments.append({**base, 'highlight_text': orig, 'comment': cmt or revtxt})

    return {
        'author': changes.get('author', 'Claude'),
        'date': changes.get('date', ''),
        'revisions': revisions,
        'comments': comments,
    }


# ── 匹配策略 ──────────────────────────────────────────────────────────────
def validate_schema(normalized: dict) -> list:
    """
    验证 JSON schema，返回错误列表。
    检查：必填字段、空值、类型等。
    """
    errors = []
    
    # 验证 revisions
    for i, rev in enumerate(normalized.get('revisions', [])):
        label = f"revisions[{i}]"
        
        # 必填字段
        if rev.get('paragraph_index') is None:
            errors.append(f"{label}: 缺少 paragraph_index")
        
        orig = rev.get('original_text', '')
        if not orig or not orig.strip():
            errors.append(f"{label}: original_text 为空")
        
        revised = rev.get('revised_text', '')
        if not revised or not revised.strip():
            errors.append(f"{label}: revised_text 为空（如只需批注请移到 comments）")
        
        # 类型检查
        if not isinstance(rev.get('paragraph_index', 0), int):
            errors.append(f"{label}: paragraph_index 应为整数")
    
    # 验证 comments
    for i, cmt in enumerate(normalized.get('comments', [])):
        label = f"comments[{i}]"
        
        if cmt.get('paragraph_index') is None:
            errors.append(f"{label}: 缺少 paragraph_index")
        
        highlight = cmt.get('highlight_text', '')
        if not highlight or not highlight.strip():
            errors.append(f"{label}: highlight_text 为空（将降级为整段批注）")
        
        comment = cmt.get('comment', cmt.get('text', ''))
        if not comment or not comment.strip():
            errors.append(f"{label}: comment 为空")
    
    return errors


def try_match(para_text, original):
    """
    模拟 apply_changes.py 的匹配逻辑。
    返回 (score, reason)，score >= 100 = 完整匹配，score >= 15 = 部分匹配
    """
    if not original:
        return 0, "原文为空"

    # 策略1：完整子串
    if original in para_text:
        return 100, f"完整匹配({len(original)}字)"

    # 策略2：长子串截取（>=8字，跳步2）
    for L in range(min(len(original), 50), 7, -2):
        for s in range(len(original) - L + 1):
            chunk = original[s:s + L]
            if chunk in para_text:
                return L * 3, f"子串{L}字 '{chunk}'"

    # 策略3：关键词交集
    orig_words = [w for w in re.findall(r'[\u4e00-\u9fff]{2,}', original) if len(w) >= 2]
    text_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', para_text))
    hits = [w for w in orig_words if w in text_words]
    if len(hits) >= 2:
        return len(hits) * 15, f"关键词 {hits} 命中"
    if hits:
        return 8, f"关键词 '{hits[0]}' 命中"

    return 0, "未匹配"


# ── 主逻辑 ────────────────────────────────────────────────────────────────
def run_preflight(docx_path: str, json_path: str, fix: bool = False) -> bool:
    """
    执行预检验。返回 True = 全部通过，False = 有问题。
    退出码由调用方根据返回值决定。
    """
    docx_path = Path(docx_path)
    json_path = Path(json_path)

    print(bold(f"\n{'='*60}"))
    print(bold(f"  预检验  {json_path.name}  vs  {docx_path.name}"))
    print(bold(f"{'='*60}\n"))

    # ── Step 1: JSON ──────────────────────────────────────────────────────
    print(c_info("[1/5] 读取 JSON..."))
    try:
        raw = json.loads(json_path.read_text(encoding='utf-8'))
    except Exception as e:
        print(c_fail(f"  ❌ JSON 解析失败: {e}"))
        return False

    fmt = detect_json_format(raw)
    if fmt == 'correct':
        n_rev = len(raw.get('revisions', []))
        n_cmt = len(raw.get('comments', []))
        print(c_ok(f"  ✅ 结构正确: revisions({n_rev}) + comments({n_cmt})"))
        normalized = raw
    elif fmt == 'flat':
        n_all = len(raw.get('changes', []))
        normalized = normalize_changes(raw)
        n_rev = len(normalized.get('revisions', []))
        n_cmt = len(normalized.get('comments', []))
        print(c_warn(f"  ⚠️  扁平格式 ({n_all} 条) → 已自动转换为标准格式"))
        print(c_info(f"  → revisions({n_rev}) + comments({n_cmt})"))
    else:
        print(c_fail(f"  ❌ 格式无法识别，keys={list(raw.keys())}"))
        return False

    # ── Step 1.5: Schema 验证 ─────────────────────────────────────────────
    print(c_info("\n[1.5/5] Schema 验证..."))
    schema_errors = validate_schema(normalized)
    if schema_errors:
        for err in schema_errors:
            print(c_fail(f"  ❌ {err}"))
        # 空值错误直接失败
        if any('为空' in e for e in schema_errors):
            print(c_fail("  ⚠️  存在空值字段，请检查 JSON 内容"))
            return False
    else:
        print(c_ok(f"  ✅ Schema 验证通过"))

    # ── Step 2: 读取段落 ──────────────────────────────────────────────────
    print(c_info("\n[2/5] 读取原始 docx 段落..."))
    try:
        paras = get_paragraphs(docx_path)
        non_empty = [p for p in paras if p['text']]
        print(c_ok(f"  ✅ 共 {len(paras)} 个 <w:p>（含 {len(non_empty)} 个有文本）"))
    except Exception as e:
        print(c_fail(f"  ❌ 读取 docx 失败: {e}"))
        return False

    # ── Step 3: 索引越界 ─────────────────────────────────────────────────
    print(c_info("\n[3/5] 段落索引校验..."))
    all_items = [(it, 'rev') for it in normalized.get('revisions', [])] + \
                [(it, 'cmt') for it in normalized.get('comments', [])]
    max_idx = len(paras) - 1
    bad_idx = [it for it, kind in all_items
               if it.get('paragraph_index') is not None
               and not (0 <= it.get('paragraph_index', -1) <= max_idx)]
    if bad_idx:
        for it in bad_idx:
            print(c_fail(f"  ❌ [{it.get('paragraph_index')}] 超出范围 (0–{max_idx})"))
    else:
        print(c_ok(f"  ✅ 所有索引在有效范围 (0–{max_idx})"))

    # ── Step 4: 文本匹配 ─────────────────────────────────────────────────
    print(c_info("\n[4/5] 原文匹配测试..."))
    issues = []   # (item, kind, reason, new_idx)
    fixed_items = {'revisions': [], 'comments': []}

    for kind, src_key in [('rev', 'revisions'), ('cmt', 'comments')]:
        for item in normalized.get(src_key, []):
            idx   = item.get('paragraph_index')
            orig  = item.get('original_text', item.get('highlight_text', ''))
            label = f"[{kind}@{idx}]"

            para_text = next((p['text'] for p in paras if p['index'] == idx), None)
            if para_text is None:
                print(c_fail(f"  ❌ {label} 无法定位段落"))
                issues.append((item, kind, f'索引{idx}无法定位段落', None))
                fixed_items[src_key].append(item)
                continue

            score, reason = try_match(para_text, orig)

            if score >= 100:
                print(c_ok(f"  ✅ {label} {reason}"))
                fixed_items[src_key].append(item)
            elif score >= 15:
                # 子串匹配 - 尝试自动补全原文
                print(c_warn(f"  ⚠️  {label} {reason}，原文: '{orig[:40]}...'"))
                if fix and len(orig) < len(para_text):
                    # 尝试找到包含 orig 的完整段落
                    if orig in para_text:
                        new_item = dict(item)
                        if kind == 'rev':
                            new_item['original_text'] = para_text
                        else:
                            new_item['highlight_text'] = para_text
                        print(c_info(f"       → 已自动补全为完整段落 ({len(para_text)}字)"))
                        fixed_items[src_key].append(new_item)
                        issues.append((item, kind, f'{reason}（已自动补全）', None))
                        continue
                issues.append((item, kind, reason, None))
                fixed_items[src_key].append(item)
            else:
                # 未匹配 → 扫描全文找最接近的段落
                best_score, best_idx = 0, idx
                for kw in re.findall(r'[\u4e00-\u9fff]{2,}', orig)[:6]:
                    for p in paras:
                        if p['index'] != idx and kw in p['text']:
                            s, _ = try_match(p['text'], orig)
                            if s > best_score:
                                best_score, best_idx = s, p['index']

                if best_idx != idx:
                    print(c_fail(f"  ❌ {label} 未匹配 → 建议改为段落 {best_idx}（匹配度 {best_score}）"))
                    print(c_warn(f"       原文: '{orig[:50]}...'"))
                    print(c_warn(f"       候选: '{next(p['text'] for p in paras if p['index']==best_idx)[:50]}...'"))
                    new_item = dict(item)
                    new_item['paragraph_index'] = best_idx
                    issues.append((item, kind, f'未匹配（建议@{best_idx}）', best_idx))
                    fixed_items[src_key].append(new_item)
                else:
                    print(c_fail(f"  ❌ {label} 全局未匹配，原文: '{orig[:40]}...'"))
                    issues.append((item, kind, '全局未匹配', None))
                    fixed_items[src_key].append(item)

    # ── Step 5: 输出报告 + 可选修复 ──────────────────────────────────────
    print(bold(f"\n{'─'*60}"))

    if not issues:
        print(c_ok(f"  ✅ 全部 {len(all_items)} 条通过匹配测试"))
        print(f"  → {'可直接运行 pipeline' if not fix else '无需修复'}")
        return True

    print(c_warn(f"  ⚠️  {len(issues)}/{len(all_items)} 条有问题"))
    for _, kind, reason, _ in issues:
        print(f"     [{kind}] {reason}")

    if not fix:
        fix_cmd = f"python3 preflight_check.py {docx_path} {json_path} --fix"
        print(bold(f"\n  → 运行 {fix_cmd} 自动生成修正版"))
        return False

    # ── 写入 _fixed.json ─────────────────────────────────────────────────
    fixed_normalized = {
        'author': normalized.get('author', 'Claude'),
        'date': normalized.get('date', ''),
        'revisions': fixed_items['revisions'],
        'comments': fixed_items['comments'],
    }
    fixed_path = json_path.parent / f"{json_path.stem}_fixed.json"
    fixed_path.write_text(json.dumps(fixed_normalized, ensure_ascii=False, indent=2), encoding='utf-8')

    print(c_info(f"\n[5/5] 已生成修正版: {fixed_path.name}"))
    print(c_warn(f"  修正 {sum(1 for _,_,_,ni in issues if ni is not None)} 处段落索引"))
    print(c_warn(f"  保留 {len([it for it,_,_,ni in issues if ni is None])} 条（无法自动修正，请手动检查）"))
    print(bold(f"\n  → 重新运行: python3 full_pipeline.py {docx_path} {fixed_path} ..."))
    return False


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(
        description='合同审核 changes.json 预检验工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    p.add_argument('docx',  help='原始 docx 文件路径')
    p.add_argument('json',  help='changes.json 路径')
    p.add_argument('--fix', action='store_true', help='自动修正并生成 _fixed.json')
    args = p.parse_args()

    ok_flag = run_preflight(args.docx, args.json, fix=args.fix)
    sys.exit(0 if ok_flag else 1)
