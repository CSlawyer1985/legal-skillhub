# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
#!/usr/bin/env python3
"""
诉讼信息中枢 — 法院人员通讯录管理。
从传票/案件受理通知书中提取的法官、书记员信息写入 macOS 通讯录。

用法:
  python3 court_contacts.py add '[{"name":"张三","phone":"13800138000","role":"审判员","case_no":"(2025)苏0981民初1234号","court":"无锡市中级人民法院"}]'
  python3 court_contacts.py add-file /path/to/contacts.json
  python3 court_contacts.py list                    # 列出所有法院相关联系人
  python3 court_contacts.py check '13800138000'      # 检查号码是否已存在

设计目标：传票和案件受理通知书识别后，自动提取法官/书记员的姓名电话，
写入 macOS 通讯录，方便律师后续联系。
"""

import sys
import os
import json
import subprocess
import re
import tempfile


def _run_applescript(script):
    """执行 AppleScript 并返回 (success, output)。"""
    try:
        r = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode != 0:
            return False, r.stderr.strip()
        return True, r.stdout.strip()
    except Exception as e:
        return False, str(e)


def _escape_for_applescript(s):
    """转义 AppleScript 字符串中的危险字符。"""
    if not s:
        return ''
    return s.replace('\\', '\\\\').replace('"', '\\"')


def check_phone_exists(phone):
    """检查指定电话号码是否已在通讯录中存在。返回联系人姓名或 None。
    使用 AppleScript 'whose' 子句过滤，比遍历所有联系人快 100 倍。"""
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    if not digits or len(digits) < 7:
        return None

    # "whose phone contains" 利用 Contacts 内部索引，对大通讯录（2000+）仍能快速响应
    script = f'''
    tell application "Contacts"
        set matches to (every person whose phone contains "{digits}")
        if (count of matches) > 0 then
            return name of item 1 of matches
        end if
        return ""
    end tell
    '''
    success, output = _run_applescript(script)
    if success and output and output != 'missing value':
        return output
    return None


def add_contact(name, phone, role='', case_no='', court='', org='', case_desc='', note_text=''):
    """
    添加或更新联系人。
    case_desc: 人类可读的案件描述（如 "张某诉李某等 民间借贷纠纷"）
    note_text: 直接指定备注全文（优先级最高，用于合并联系人时传入自定义备注）
    返回 (status, message)。
    """
    if not name or not phone:
        return 'skipped', '缺少姓名或电话号码'

    safe_name = _escape_for_applescript(name)
    safe_phone = _escape_for_applescript(phone)
    safe_role = _escape_for_applescript(role)
    safe_case = _escape_for_applescript(case_no)
    safe_court = _escape_for_applescript(court)
    safe_org = _escape_for_applescript(org or court)
    safe_desc = _escape_for_applescript(case_desc or '')

    # 构建备注内容 — 如果调用方传了 note_text 直接使用，否则自动拼接
    if note_text:
        final_note = note_text
    else:
        note_lines = []
        if case_desc:
            note_lines.append(f"案件: {case_desc}")
        if case_no:
            note_lines.append(f"案号: {case_no}")
        if role:
            note_lines.append(f"职务: {role}")
        if court:
            note_lines.append(f"法院: {court}")
        final_note = '\\n'.join(note_lines) if note_lines else ''

    # 1. 先检查号段是否已存在
    existing_name = check_phone_exists(phone)
    if existing_name:
        # 同号已存在 → 追加备注，不创建新联系人
        if case_no:
            # 确认没有重复的案件备注
            append_text = _escape_for_applescript(case_desc or case_no)
            append_code = _escape_for_applescript(case_no)
            script = f'''
            tell application "Contacts"
                set targetPerson to first person whose name is "{_escape_for_applescript(existing_name)}"
                set oldNote to note of targetPerson as string
                if oldNote does not contain "{append_code}" then
                    set newNote to oldNote & "\\n\\n[诉讼中枢追加] " & "{append_text}" & " | " & "{safe_role}"
                    set note of targetPerson to newNote
                    save
                end if
            end tell
            '''
            _run_applescript(script)
        return 'updated', f'号码已存在（{existing_name}），已追加案件备注'

    # 2. 创建新联系人 —— 中文名不拆分，直接放 last name（显示即全名）
    safe_full = _escape_for_applescript(name)

    script = f'''
    tell application "Contacts"
        set newPerson to make new person with properties {{last name:"{safe_full}"}}
        make new phone at end of phones of newPerson with properties {{label:"工作", value:"{safe_phone}"}}
    '''

    if safe_org:
        script += f'\n        set organization of newPerson to "{safe_org}"'

    if final_note:
        script += f'\n        set note of newPerson to "[诉讼中枢自动添加]\\n{final_note}"'

    if safe_role and safe_role in ('审判员', '审判长', '承办法官', '法官', '执行法官', '执行员', '书记员', '法官助理'):
        script += f'\n        set job title of newPerson to "{safe_role}"'

    script += '\n        save\n    end tell'

    success, output = _run_applescript(script)
    if success:
        return 'created', f'已创建联系人: {name} ({role}) - {phone}'
    else:
        return 'failed', f'创建失败: {output}'


def add_contacts_batch(contacts):
    """
    批量添加联系人。
    contacts: list of {name, phone, role, case_no, court, org, case_desc}
    返回汇总结果。
    """
    results = {'created': [], 'updated': [], 'skipped': [], 'failed': []}
    for c in contacts:
        status, msg = add_contact(
            name=c.get('name', ''),
            phone=c.get('phone', ''),
            role=c.get('role', ''),
            case_no=c.get('case_no', ''),
            court=c.get('court', ''),
            org=c.get('org', ''),
            case_desc=c.get('case_desc', ''),
            note_text=c.get('note_text', ''),
        )
        results[status].append({'name': c.get('name'), 'msg': msg})
    return results


def list_court_contacts():
    """列出通讯录中所有带 [诉讼中枢] 备注的联系人。"""
    script = '''
    tell application "Contacts"
        set output to ""
        repeat with p in people
            if note of p contains "[诉讼中枢" then
                set output to output & name of p & " | " & (organization of p as string) & " | " & (note of p as string) & "---SEP---"
            end if
        end repeat
        return output
    end tell
    '''
    success, output = _run_applescript(script)
    if not success or not output:
        return []

    contacts = []
    for entry in output.split('---SEP---'):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(' | ', 2)
        contacts.append({
            'name': parts[0] if len(parts) > 0 else '',
            'org': parts[1] if len(parts) > 1 else '',
            'note': parts[2] if len(parts) > 2 else '',
        })
    return contacts


def export_vcf(contacts, output_path=''):
    """
    将联系人列表导出为 vCard (.vcf) 文件，可发到手机导入通讯录。
    contacts: list of {name, phone, role, case_no, court, org}
    output_path: 输出路径，默认桌面 court_contacts.vcf
    返回输出文件路径。
    """
    if not output_path:
        output_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'court_contacts.vcf')

    vcf_lines = []
    for c in contacts:
        name = c.get('name', '')
        phone = c.get('phone', '')
        if not name or not phone:
            continue

        role = c.get('role', '')
        case_no = c.get('case_no', '')
        case_desc = c.get('case_desc', '')
        court = c.get('court', '') or c.get('org', '')

        # 构建备注 — 如果调用方传了 note_text 直接使用，否则自动拼接
        if c.get('note_text'):
            note = c['note_text']
            # 确保带 [诉讼中枢] 标签（list 命令依赖此标签）
            if '[诉讼中枢]' not in note:
                note += '\\n[诉讼中枢]'
        else:
            note_parts = []
            if case_desc:
                note_parts.append(f'案件: {case_desc}')
            if case_no:
                note_parts.append(f'案号: {case_no}')
            if role:
                note_parts.append(f'职务: {role}')
            if court:
                note_parts.append(f'法院: {court}')
            note_parts.append('[诉讼中枢]')
            note = '\\n'.join(note_parts)

        # vCard 3.0 格式
        vcf_lines.append('BEGIN:VCARD')
        vcf_lines.append('VERSION:3.0')
        vcf_lines.append(f'FN:{name}')
        vcf_lines.append(f'N:;{name};;;')
        vcf_lines.append(f'TEL;TYPE=WORK,VOICE:{phone}')
        if court:
            vcf_lines.append(f'ORG:{court}')
        if role:
            vcf_lines.append(f'TITLE:{role}')
        vcf_lines.append(f'NOTE:{note}')
        vcf_lines.append('END:VCARD')
        vcf_lines.append('')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(vcf_lines))

    return output_path


def extract_from_pdf_text(text, filename=''):
    """
    从 PDF 文本中提取法院人员联系信息。
    返回 list of {name, phone, role}。
    """
    contacts = []
    seen = set()  # 去重: (name, phone)
    assigned_persons = set()  # 已分配电话的人员: (name, pos)

    # 法院文书中的常见模式：
    # 1. 审判员/审判长/承办法官 + 姓名 + 电话
    # 2. 书记员 + 姓名 + 电话
    # 3. 联系电话独立一行，紧跟人员姓名

    # 模式1: "审判员：张三  电话：13800138000"
    # 先匹配带电话的
    for role_label, role_name in [
        ('审判[员长]', '审判员'),
        ('审判员', '审判员'),
        ('审判长', '审判长'),
        ('承办法官', '承办法官'),
        ('法官', '法官'),
        ('书记员', '书记员'),
        ('法官助理', '法官助理'),
    ]:
        # 完整模式: 角色 可选冒号 + 姓名 + 可选动作词（承办/负责/审理）+ 电话（不跨行）
        # 支持: "审判员：张三  电话：13800138000" / "审判员张三 电话13800138000" / "本案由审判员张某承办，联系电话：18812345678"
        pat = rf'(?:{role_label})\s*[：:]?\s*([\u4e00-\u9fff]{{2,4}})(?:\s*(?:承办|负责|审理))?\s*(?:[,，])?\s*(?:电话|联系电话|联系方式|手机)[：:]?\s*([\d\-()（）\s]{{7,20}})'
        for m in re.finditer(pat, text):
            name = m.group(1).strip()
            phone = re.sub(r'[\s\-()（）]', '', m.group(2).strip())
            # 后处理：去掉名字末尾被误捕的动作词
            for suffix in ['承办', '负责', '审理']:
                if name.endswith(suffix) and len(name) > len(suffix):
                    name = name[:-len(suffix)]
            # 去干扰词
            if name in ('本案', '本案由', '本案经', '联系电话', '联系法官',
                        '应到时', '应到处', '开庭时', '开庭地',
                        '电话', '联系方式', '手机'):
                continue
            # 跨行检测：如果姓名的行和电话号码不在同一行，跳过（交给模式2处理）
            name_line_end = text.find('\n', m.start())
            phone_start = m.group(0).find(m.group(2))
            if name_line_end > 0 and m.start(2) > name_line_end:
                continue
            if len(phone) >= 7 and (name, phone) not in seen:
                seen.add((name, phone))
                contacts.append({'name': name, 'phone': phone, 'role': role_name})

    # 模式1.5: "联系人：NamePhone" — 联系人后直接跟号码，无"电话："标签
    # 法院传票/通知书常见格式："联系人：张法官0519-00000000" / "联系人：张三 13800138000"
    for role_label, role_name in [
        ('联系人', '联系人'),
    ]:
        # 联系人 可选冒号 + 姓名 + 可选空格 + 电话号码（7-20位数字，允许短横和空格）
        pat = rf'(?:{role_label})\s*[：:]?\s*([\u4e00-\u9fff]{{2,4}})\s*([\d\-()（）\s]{{7,20}})'
        for m in re.finditer(pat, text):
            name = m.group(1).strip()
            phone = re.sub(r'[\s\-()（）]', '', m.group(2).strip())
            # 去干扰词
            if name in ('本案', '本院', '电话', '联系方式', '手机', '联系电话',
                        '应到时', '应到处', '开庭时', '开庭地', '案由', '案号',
                        '联系人'):
                continue
            if len(phone) >= 7 and (name, phone) not in seen:
                seen.add((name, phone))
                contacts.append({'name': name, 'phone': phone, 'role': role_name})

    # 模式2: 角色 + 姓名（无电话行，但后续有联系电话）
    # 分两遍：第一遍找姓名，第二遍找附近的电话
    person_lines = []
    person_seen = set()  # 去重: 同一文本位置只记一次
    for role_label, role_name in [
        ('审判[员长]', '审判员'),
        ('审判员', '审判员'),
        ('审判长', '审判长'),
        ('承办法官', '承办法官'),
        ('法官', '法官'),
        ('书记员', '书记员'),
        ('法官助理', '法官助理'),
        ('执行[员官]', '执行员'),
    ]:
        pat = rf'(?:{role_label})\s*[：:]?\s*([\u4e00-\u9fff]{{2,4}})'
        for m in re.finditer(pat, text):
            name = m.group(1).strip()
            # 后处理：去掉名字末尾被误捕的动作词
            for suffix in ['承办', '负责', '审理']:
                if name.endswith(suffix) and len(name) > len(suffix):
                    name = name[:-len(suffix)]
            # 去常见干扰词
            if name in ('本案', '本案由', '本案经', '联系电话', '联系法官',
                        '应到时', '应到处', '开庭时', '开庭地', '案由', '案号',
                        '电话', '联系方式', '手机'):
                continue
            # 去重：同一位置只记一次
            pos_key = (m.start(), name)
            if pos_key not in person_seen:
                person_seen.add(pos_key)
                person_lines.append({'name': name, 'role': role_name, 'pos': m.start()})

    # 找"联系电话"/"联系方式"等，分配给最近的人员（窗口内）
    if person_lines:
        phone_pat = r'(?:联系电话|联系方式|电话|手机|法官电话|书记员电话)\s*[：:]\s*([\d\-()（）\s]{7,20})'
        phone_matches = list(re.finditer(phone_pat, text))

        # 按人员出现顺序分配电话（每人最多一个电话）
        person_lines.sort(key=lambda p: p['pos'])

        for pm in phone_matches:
            raw_phone = pm.group(1).strip()
            phone = re.sub(r'[\s\-()（）]', '', raw_phone)
            if len(phone) < 7:
                continue

            # 找最近、未被分配的人员（向前 500 字符内）
            best_person = None
            best_dist = 9999
            for p in person_lines:
                if (p['name'], p['pos']) in assigned_persons:
                    continue
                dist = pm.start() - p['pos']
                if 0 <= dist <= 500 and dist < best_dist:
                    best_dist = dist
                    best_person = p

            if best_person and (best_person['name'], phone) not in seen:
                seen.add((best_person['name'], phone))
                assigned_persons.add((best_person['name'], best_person['pos']))
                contacts.append({
                    'name': best_person['name'],
                    'phone': phone,
                    'role': best_person['role'],
                })

    # 模式3: 独立电话行，格式如 "电话：0510-12345678" 或 "手机：13800138000"
    # 如果前面有人员线索（如"本案承办法官：张三"不带电话），尝试配对
    standalone_phone_pat = r'(?:联系电话|联系方式|电话|手机|座机|fax|传真)?\s*[：:]\s*([\d\-()（）\s]{7,20})'
    for m in re.finditer(standalone_phone_pat, text):
        raw = m.group(1).strip()
        phone = re.sub(r'[\s\-()（）]', '', raw)
        if len(phone) < 7:
            continue
        # 如果已有其他 person 没配到电话，且这个 phone 还未使用
        unmatched = [p for p in person_lines
                     if (p['name'], phone) not in seen
                     and (p['name'], p['pos']) not in assigned_persons]
        if unmatched and phone not in [c['phone'] for c in contacts]:
            # 取最近的未匹配人员
            best_p = min(unmatched, key=lambda p: abs(m.start() - p['pos']))
            if abs(m.start() - best_p['pos']) <= 800:
                seen.add((best_p['name'], phone))
                assigned_persons.add((best_p['name'], best_p['pos']))
                contacts.append({
                    'name': best_p['name'],
                    'phone': phone,
                    'role': best_p['role'],
                })

    return contacts


# ============================================================
#  CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='诉讼信息中枢 — 法院人员通讯录管理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s extract "审判员：张三  电话：13800138000\\n书记员：李四  电话：13900139000"
  %(prog)s extract-file /path/to/传票.txt
  %(prog)s add '[{"name":"张三","phone":"13800138000","role":"审判员","case_no":"(2025)苏0981民初1234号","court":"无锡中院"}]'
  %(prog)s add-file /path/to/contacts.json
  %(prog)s list
  %(prog)s check 13800138000
        '''
    )
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # extract — 从文本中提取联系人
    extr = subparsers.add_parser('extract', help='从文本中提取法院人员联系信息')
    extr.add_argument('text', help='PDF 文本内容')

    extr_file = subparsers.add_parser('extract-file', help='从文本文件提取法院人员联系信息')
    extr_file.add_argument('file', help='文本文件路径')

    # add — 添加联系人
    add = subparsers.add_parser('add', help='添加联系人到通讯录')
    add.add_argument('contacts_json', help='联系人 JSON 数组字符串')

    add_file = subparsers.add_parser('add-file', help='从 JSON 文件批量添加联系人')
    add_file.add_argument('file', help='JSON 文件路径')

    # list — 列出
    subparsers.add_parser('list', help='列出所有法院相关联系人')

    # check — 检查
    check = subparsers.add_parser('check', help='检查号码是否已存在')
    check.add_argument('phone', help='电话号码')

    # export — 导出 vCard
    export = subparsers.add_parser('export', help='导出联系人为 vCard 文件（发手机导入通讯录）')
    export.add_argument('contacts_json', help='联系人 JSON 数组字符串')
    export.add_argument('-o', '--output', help='输出路径（默认桌面 court_contacts.vcf）', default='')

    args = parser.parse_args()

    if args.command == 'extract':
        results = extract_from_pdf_text(args.text)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        print(f"\n共提取 {len(results)} 位联系人", file=sys.stderr)
        return 0

    elif args.command == 'extract-file':
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
        results = extract_from_pdf_text(text)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        print(f"\n共提取 {len(results)} 位联系人", file=sys.stderr)
        return 0

    elif args.command == 'add':
        contacts = json.loads(args.contacts_json)
        results = add_contacts_batch(contacts)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        # 汇总
        total = sum(len(v) for v in results.values())
        created = len(results['created'])
        updated = len(results['updated'])
        failed = len(results['failed'])
        print(f"\n{'='*40}", file=sys.stderr)
        print(f"通讯录更新: 新建 {created} / 更新 {updated} / 失败 {failed} / 跳过 {len(results['skipped'])}", file=sys.stderr)
        return 0 if failed == 0 else 1

    elif args.command == 'add-file':
        with open(args.file, 'r', encoding='utf-8') as f:
            contacts = json.load(f)
        results = add_contacts_batch(contacts)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        created = len(results['created'])
        updated = len(results['updated'])
        failed = len(results['failed'])
        print(f"\n通讯录更新: 新建 {created} / 更新 {updated} / 失败 {failed} / 跳过 {len(results['skipped'])}", file=sys.stderr)
        return 0 if failed == 0 else 1

    elif args.command == 'list':
        contacts = list_court_contacts()
        print(json.dumps(contacts, ensure_ascii=False, indent=2))
        print(f"\n共 {len(contacts)} 位法院相关联系人", file=sys.stderr)
        return 0

    elif args.command == 'check':
        existing = check_phone_exists(args.phone)
        if existing:
            print(f"✅ 已存在: {existing}")
        else:
            print("❌ 未找到")
        return 0

    elif args.command == 'export':
        contacts = json.loads(args.contacts_json)
        path = export_vcf(contacts, args.output)
        print(f"📱 vCard 已导出: {path}", file=sys.stderr)
        print(f"   共 {len(contacts)} 位联系人", file=sys.stderr)
        print(f"   发到手机 → 点开 .vcf 文件 → 自动导入通讯录", file=sys.stderr)
        print(path)  # 最后一行输出路径，方便管道
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
