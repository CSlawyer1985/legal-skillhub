#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archive_case.py — 配置驱动归档主流程（V3 引擎）

用法:
  python archive_case.py <案卷文件夹> [--firm tongjing] [--merge yes|no] [--output-name X]
  python archive_case.py <案卷文件夹> --values 填写覆盖.json

流程: 读 firm_config -> 抽源文字 -> 按 archive_plan 分类处理
      (表格类按 field_map 填 / 纯模板抽页 / 既定文件复制)
      -> 写 manifest + 待补齐清单 -> 按偏好问合并
"""
import os, sys, json, fnmatch, shutil, datetime, re

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_ROOT = os.path.abspath(os.path.join(os.path.expanduser('~'), '.workbuddy', 'case-archiver'))
sys.path.insert(0, HERE)

import extract
import fill_docx


def load_firm(firm):
    base = os.path.join(CONFIG_ROOT, 'firm_config', firm)
    paths = json.load(open(os.path.join(base, 'paths.json'), encoding='utf-8'))
    field_map = json.load(open(os.path.join(base, 'field_map.json'), encoding='utf-8'))
    plan = json.load(open(os.path.join(base, 'archive_plan.json'), encoding='utf-8'))
    pref = json.load(open(os.path.join(base, 'preferences.json'), encoding='utf-8'))
    return base, paths, field_map, plan, pref


def find_default_firm():
    s = os.path.join(CONFIG_ROOT, 'settings.json')
    if os.path.exists(s):
        try:
            return json.load(open(s, encoding='utf-8')).get('default_firm')
        except Exception:
            pass
    return None


def resolve_case(arg, paths):
    if os.path.isdir(arg):
        return arg
    # 当作源目录下的子文件夹名
    cand = os.path.join(paths['source_base'], arg)
    if os.path.isdir(cand):
        return cand
    return arg


def normalize_case_name(name):
    """规范化案卷输出名：与→诉，补「案」后缀。"""
    # 「A与B纠纷」→「A诉B纠纷」
    name = re.sub(r'(?<=[\u4e00-\u9fa5\d)）])与(?=[\u4e00-\u9fa5])', '诉', name)
    # 结尾加「案」字（如果以纠纷/争议/仲裁结束且没有案）
    if re.search(r'(纠纷|争议|仲裁)$', name):
        if not name.endswith('案'):
            name += '案'
    return name


def copy_existing_file(case_index, patterns, case_folder, exclude_patterns=None):
    """按 patterns 优先级搜索（第一个命中的模式优先），根目录文件优先于子目录。
    自动跳过 .__old__ 残留文件；可选 exclude_patterns 排除误抓。"""
    case_root = os.path.normpath(case_folder)
    roots = []; subs = []
    for p in case_index:
        bn = os.path.basename(p)
        if '.__old__' in bn:
            continue
        parent = os.path.dirname(p)
        if os.path.normpath(parent) == case_root:
            roots.append(p)
        else:
            subs.append(p)
    # 按模式顺序（非文件顺序）搜索，确保优先级高的模式先命中
    for pat in patterns:
        for path in roots + subs:
            bn = os.path.basename(path)
            if fnmatch.fnmatch(bn, pat):
                # 排除模式检查（在函数内部，确保跳过误抓后继续尝试下一匹配）
                if exclude_patterns:
                    if any(fnmatch.fnmatch(bn, ep) for ep in exclude_patterns):
                        continue
                return path
    return None


def fill_table_template(tpl_path, out_path, tpl_spec, case_index, values_override, case_folder_name=None):
    fields = []
    fv_list = []
    for f in tpl_spec['fields']:
        name = f['name']
        if f.get('source') == 'auto':
            val = extract.extract_field(f['key'], case_index, f.get('from'), case_folder_name)
            status = 'auto'
        elif f.get('source') == 'agent':
            val = (values_override or {}).get(name)
            status = 'agent' if val is None else 'agent-filled'
        else:  # client
            val = None
            status = 'client'
        fv = dict(f)
        fv['value'] = val
        fv_list.append(fv)
        fields.append({'name': name, 'value': val or '', 'status': status})
    report = fill_docx.fill_template(
        tpl_path,
        out_path,
        fv_list,
        strict=tpl_spec.get('strict', True),
    )
    for field_status, write_status in zip(fields, report.get('fields', [])):
        field_status['write_status'] = write_status.get('status')
        if write_status.get('error'):
            field_status['write_error'] = write_status['error']
    return fields, report


def resolve_output(case_folder, paths, output_name=None):
    if output_name:
        name = output_name
    else:
        name = os.path.basename(case_folder.rstrip('/\\'))
        name = normalize_case_name(name)
    out = os.path.join(paths['output_base'], name)
    return out


def detect_mixed_folder(case_index):
    """检测同一源文件夹是否包含多种案件材料（多份互斥文件）。"""
    indicators = {
        '起诉状': ['*起诉状*'],
        '授权委托书': ['*授权委托书*', '*委托授权书*'],
        '委托代理合同': ['*委托代理合同*', '*聘请律师合同*'],
        '裁决书/判决书/调解书': ['*裁决书*', '*判决书*', '*调解书*'],
    }
    warnings = []
    for label, patterns in indicators.items():
        matches = []
        for p in case_index:
            bn = os.path.basename(p)
            for pat in patterns:
                if fnmatch.fnmatch(bn, pat):
                    matches.append(bn)
                    break
        # 排除明显的子文件（如 本诉xxx、反诉xxx 是同一案件的正常多份）
        uniq = set(matches)
        if len(uniq) > 1:
            # 如果两份文件名里都含「诉」字且不互为 本诉/反诉 关系，则报警
            warnings.append(f"  · {label}: {', '.join(sorted(uniq)[:5])}")
    return warnings


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: archive_case.py <案卷文件夹> [--firm X] [--merge yes|no] [--output-name X] [--values f.json]")
        sys.exit(1)
    case_arg = args[0]
    firm = find_default_firm() or 'tongjing'
    merge_arg = None
    values_path = None
    output_name = None
    for i, a in enumerate(args[1:], 1):
        if a == '--firm' and i + 1 < len(args):
            firm = args[i + 1]
        elif a == '--merge' and i + 1 < len(args):
            merge_arg = args[i + 1]
        elif a == '--values' and i + 1 < len(args):
            values_path = args[i + 1]
        elif a == '--output-name' and i + 1 < len(args):
            output_name = args[i + 1]

    base, paths, field_map, plan, pref = load_firm(firm)
    case_folder = resolve_case(case_arg, paths)
    if not os.path.isdir(case_folder):
        print(f"[错误] 找不到案卷文件夹: {case_folder}")
        sys.exit(1)
    out_dir = resolve_output(case_folder, paths, output_name)
    os.makedirs(out_dir, exist_ok=True)

    print(f"[归档] 律所={firm}  案卷={case_folder}")
    print(f"[归档] 输出={out_dir}")

    case_index = extract.build_case_index(case_folder)
    # P3: 混合文件夹检测
    mixed_warnings = detect_mixed_folder(case_index)
    if mixed_warnings:
        print(f"[警告] 源文件夹可能包含多种案件材料：")
        for w in mixed_warnings:
            print(w)
        print("[警告] 建议将不同案件的材料分开放置，避免字段提取互相污染。\n")
    values_override = json.load(open(values_path, encoding='utf-8')) if values_path and os.path.exists(values_path) else {}

    manifest_items = []
    pending = []
    agent_needed = []

    for item in plan['order']:
        seq = item['seq']; name = item['name']; typ = item['type']
        if typ == 'skip':
            continue
        out_name = item['out']
        if typ == 'table':
            tpl_file = field_map['templates'][item['template']]['file']
            tpl_path = os.path.join(paths['template_dir'], tpl_file)
            out_path = os.path.join(out_dir, out_name)
            try:
                fields, fill_report = fill_table_template(
                    tpl_path,
                    out_path,
                    field_map['templates'][item['template']],
                    case_index,
                    values_override,
                    os.path.basename(case_folder.rstrip('/\\')),
                )
                manifest_items.append({
                    'seq': seq, 'name': name, 'type': typ, 'status': 'done',
                    'out': out_name, 'fields': fields,
                    'fill_report': {
                        'engine': fill_report.get('engine'),
                        'warnings': fill_report.get('warnings', []),
                    },
                })
                for fld in fields:
                    if fld['status'] == 'agent':
                        agent_needed.append(f"{out_name} ▸ {fld['name']}")
                print(f"  [表格] {out_name}")
                for warning in fill_report.get('warnings', []):
                    print(f"    [表格警告] {warning}")
            except fill_docx.TemplateFillError as exc:
                report = exc.report or {}
                manifest_items.append({
                    'seq': seq, 'name': name, 'type': typ, 'status': 'error',
                    'out': out_name, 'note': str(exc), 'fill_report': report,
                })
                pending.append(f"{name}（表格填写失败: {exc}）")
                print(f"  [表格失败] {out_name}: {exc}")
            except Exception as exc:
                manifest_items.append({
                    'seq': seq, 'name': name, 'type': typ, 'status': 'error',
                    'out': out_name, 'note': str(exc),
                })
                pending.append(f"{name}（表格处理异常: {exc}）")
                print(f"  [表格异常] {out_name}: {exc}")
        elif typ == 'pure':
            src = os.path.join(paths['template_dir'], item['source'])
            out_path = os.path.join(out_dir, out_name)
            try:
                import pdf_util
                pdf_util.extract_pages(src, item['pages'], out_path)
                manifest_items.append({'seq': seq, 'name': name, 'type': typ, 'status': 'done', 'out': out_name})
                print(f"  [纯模板] {out_name} (页 {item['pages']})")
            except Exception as e:
                manifest_items.append({'seq': seq, 'name': name, 'type': typ, 'status': 'error', 'note': str(e)})
                pending.append(f"{name}（纯模板抽取失败: {e}）")
        elif typ == 'copy':
            found = copy_existing_file(case_index, item['match'], case_folder, item.get('exclude'))
            if found:
                ext = os.path.splitext(found)[1] or '.pdf'
                fname = out_name + ext
                # 注：本受控 Python 的 os.path.join 对含中文路径偶发吞掉扩展名，
                # 故统一用显式拼接构造目标路径。
                dest = out_dir + '\\' + fname
                try:
                    if os.path.exists(dest):
                        os.remove(dest)
                except PermissionError:
                    dest = out_dir + '\\' + out_name + f".{os.getpid()}" + ext
                shutil.copy2(found, dest)
                manifest_items.append({'seq': seq, 'name': name, 'type': typ, 'status': 'done', 'out': os.path.basename(dest)})
                print(f"  [复制] {os.path.basename(dest)}  <- {os.path.basename(found)}")
            else:
                note = f"源文件夹未找到匹配 {item['match']}"
                manifest_items.append({'seq': seq, 'name': name, 'type': typ, 'status': 'pending', 'note': note})
                pending.append(f"{name} —— {note}")
                print(f"  [缺失] {name}")

    # 目录模板
    try:
        dt = os.path.join(paths['template_dir'], paths['directory_template'])
        if os.path.exists(dt):
            shutil.copy2(dt, os.path.join(out_dir, plan.get('directory_template_out', '0.归档卷宗目录.doc')))
    except Exception as e:
        print(f"  [警告] 目录模板复制失败: {e}")

    # 写 manifest
    manifest = {
        'firm': firm, 'case': os.path.basename(case_folder), 'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
        'items': manifest_items,
    }
    with open(os.path.join(out_dir, '.归档状态.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # 待补齐清单
    lines = [f"待补齐材料清单 — {os.path.basename(case_folder)}", f"生成时间：{manifest['generated_at']}", ""]
    if pending:
        lines.append("【缺失/待补材料】（源文件夹未找到，需补交后「完卷」）：")
        for p in pending:
            lines.append(f"  · {p}")
    else:
        lines.append("【缺失/待补材料】无")
    lines.append("")
    if agent_needed:
        lines.append("【需承办律师/助理填写】（agent 字段，非源文件自动提取）：")
        for a in agent_needed:
            lines.append(f"  · {a}")
    else:
        lines.append("【需承办律师填写】无")
    with open(os.path.join(out_dir, '待补齐材料清单.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n[完成] 已输出 {out_dir}")
    print(f"[统计] 已处理 {sum(1 for i in manifest_items if i['status']=='done')} 项，"
          f"缺失 {sum(1 for i in manifest_items if i['status']=='pending')} 项，"
          f"失败 {sum(1 for i in manifest_items if i['status']=='error')} 项，"
          f"需承办律师填 {len(agent_needed)} 项")

    # 合并 PDF 只能由显式 --merge yes 触发；preferences 不再绕过确认。
    pref_merge = pref.get('merge_pdf', 'ask')
    if merge_arg == 'yes':
        do_merge = True
    else:
        do_merge = False
        if pref_merge != 'never' and merge_arg != 'no':
            print("\n[提示] 案卷已整理。是否合并成 PDF 合集（带页码+目录）？"
                  "确认后使用 --merge yes 或直接说「合并」。")
    if do_merge:
        try:
            import merge_volume
            merge_volume.merge_volume(out_dir, base, plan)
        except Exception as e:
            print(f"[合并失败] {e}")


if __name__ == '__main__':
    main()
