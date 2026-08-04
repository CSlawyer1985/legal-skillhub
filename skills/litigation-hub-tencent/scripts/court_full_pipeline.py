#!/usr/bin/env python3
"""
诉讼信息中枢 — 一键全链路脚本。
输入法院短信文本或送达链接，一键完成：解析 → 下载 → PDF解析 → 归档 → 报告。

用法:
  python3 court_full_pipeline.py --sms "法院短信原文..."
  python3 court_full_pipeline.py --sms-file /path/to/sms.txt
  python3 court_full_pipeline.py --url "https://zxfw.court.gov.cn/...?qdbh=...&sdbh=...&sdsin=..."
  python3 court_full_pipeline.py --photo /path/to/传票照片.jpg

设计目标：把原来需要 5-8 个对话回合的流程压缩到 1 个命令，大幅降低积分消耗。
模型只需要跑这个脚本 + 呈现结果，不再手动编排每一步。
"""

import sys
import os
import re
import json
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

# 本技能脚本目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
REFERENCES_DIR = os.path.join(SKILL_DIR, 'references')

# zxfw API
ZXFW_API = "https://zxfw.court.gov.cn/yzw/yzw-zxfw-sdfw/api/v1/sdfw/getWsListBySdbhNew"

# 临时下载目录
STAGING = tempfile.mkdtemp(prefix='court_pipeline_')


# ============================================================
#  第一步：短信解析
# ============================================================

def parse_sms(text):
    """从法院短信文本中提取关键信息。返回 dict。"""
    info = {
        'sms_type': 'unknown',
        'case_no': None,
        'parties': [],
        'download_url': None,
        'platform': None,
        'params': {},
        'sent_time': None,
        'raw': text,
    }

    # 1. 短信类型
    if any(kw in text for kw in ['文书送达', '请查收', '查收文书', '下载文书', '送达文书']):
        info['sms_type'] = 'document_delivery'
    elif any(kw in text for kw in ['已立案', '立案通知', '受理案件']):
        info['sms_type'] = 'filing_notification'
    else:
        info['sms_type'] = 'info_notification'

    # 2. 案号
    m = re.search(r'[（(〔\[]\s*\d{4}\s*[）)\]〕]\s*[^号]*?\d+号', text)
    if m:
        info['case_no'] = m.group(0).strip().replace(' ', '')

    # 3. 送达链接
    url_patterns = [
        (r'(https?://[^\s]*zxfw\.court\.gov\.cn[^\s]*)', 'zxfw'),
        (r'(https?://[^\s]*sd\.gdems\.com[^\s]*)', 'gdems'),
        (r'(https?://[^\s]*jysd\.10102368\.com[^\s]*)', 'jysd'),
        (r'(https?://[^\s]*dzsd\.hbfy\.gov\.cn[^\s]*)', 'hbfy'),
        (r'(https?://[^\s]*sfpt\.cdfy12368\.gov\.cn[^\s]*)', 'sfdw'),
        (r'(https?://[^\s]*171\.106\.48\.55[^\s]*)', 'sfdw'),
    ]
    for pat, platform in url_patterns:
        m = re.search(pat, text)
        if m:
            info['download_url'] = m.group(1).rstrip('，。；!；')
            info['platform'] = platform
            break

    # 4. 提取参数
    if info['download_url']:
        parsed = urlparse(info['download_url'])
        query = parse_qs(parsed.fragment.split('?')[-1] if '#' in info['download_url'] and '?' in parsed.fragment else parsed.query)
        for key in ['qdbh', 'sdbh', 'sdsin', 'key', 'msg']:
            val = query.get(key, [None])[0]
            if val:
                info['params'][key] = val

    # 5. 当事人
    company_pat = r'[\u4e00-\u9fff]{2,30}(?:有限责任公司|股份有限公司|有限公司|集团|企业)'
    person_pat = r'[\u4e00-\u9fff]{2,4}'
    # 起诉状/答辩状中的原告/被告
    for role, prefix in [('plaintiff', '原告'), ('defendant', '被告')]:
        m = re.search(rf'{prefix}[：:]\s*(.+?)(?:\n|，|。|$)', text)
        if m:
            info['parties'].append({'role': role, 'name': m.group(1).strip().rstrip('，。')})

    # 6. 发送时间
    m = re.search(r'(?:发送|时间)[：:]?\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?\s+\d{1,2}[时:]?\d{0,2})', text)
    if m:
        info['sent_time'] = m.group(1)

    # 7. 验证码（司法送达网需要）
    m = re.search(r'验证码[：:]\s*(\w{4,6})', text)
    if m:
        info['params']['captcha'] = m.group(1)

    # 8. 账号密码（湖北账号模式）
    m = re.search(r'账号\s*(\d{15,20})', text)
    if m:
        info['params']['account'] = m.group(1)
    m = re.search(r'默认密码[：:]\s*([0-9A-Za-z]+)', text)
    if m:
        info['params']['password'] = m.group(1)

    return info


# ============================================================
#  第二步：下载文书
# ============================================================

def download_zxfw(params, staging=STAGING):
    """
    全国法院统一送达平台（zxfw）—— API 直连下载。
    返回 {success: bool, files: list, court_name: str, sent_at: str, error: str}
    """
    qdbh = params.get('qdbh', '')
    sdbh = params.get('sdbh', '')
    sdsin = params.get('sdsin', '')

    if not all([qdbh, sdbh, sdsin]):
        return {'success': False, 'files': [], 'error': '缺少必需参数 qdbh/sdbh/sdsin'}

    try:
        import urllib.request
        req = urllib.request.Request(
            ZXFW_API,
            data=json.dumps({"qdbh": qdbh, "sdbh": sdbh, "sdsin": sdsin}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {'success': False, 'files': [], 'error': f'API 请求失败: {e}'}

    if not data.get('success'):
        return {'success': False, 'files': [], 'error': data.get('msg', 'API 返回失败')}

    documents = data.get('data', [])
    if not documents:
        return {'success': False, 'files': [], 'error': '无待签收文书'}

    court_name = documents[0].get('c_fymc', '')
    sent_at = documents[0].get('dt_cjsj', '')

    # 下载每个文书
    files = []
    os.makedirs(staging, exist_ok=True)
    for doc in documents:
        name = doc.get('c_wsmc', '未知文书')
        url = doc.get('wjlj', '')
        if not url:
            continue
        safe_name = re.sub(r'[<>:"|?*/\\]', '', name)
        filepath = os.path.join(staging, f"{safe_name}.pdf")
        try:
            import urllib.request
            urllib.request.urlretrieve(url, filepath)
            if os.path.getsize(filepath) > 100:  # 确保不是空文件
                files.append({'name': name, 'path': filepath, 'size': os.path.getsize(filepath)})
        except Exception as e:
            print(f"  ⚠️ 下载失败: {name} — {e}", file=sys.stderr)

    return {
        'success': len(files) > 0,
        'files': files,
        'court_name': court_name,
        'sent_at': sent_at,
        'total_docs': len(documents),
        'downloaded': len(files),
    }


# ============================================================
#  第三步：PDF 解析
# ============================================================

def parse_pdfs(files):
    """
    解析下载的 PDF 文件，提取关键信息。
    优先 pypdf，不可用则回退到 pdftotext。
    返回文档列表。
    """
    try:
        from pypdf import PdfReader
        _has_pypdf = True
    except ImportError:
        _has_pypdf = False

    results = []
    for f in files:
        text = ''
        try:
            if _has_pypdf:
                reader = PdfReader(f['path'])
                text = '\n'.join(page.extract_text() or '' for page in reader.pages[:3])
            else:
                r = subprocess.run(['pdftotext', '-l', '3', f['path'], '-'],
                                   capture_output=True, text=True, timeout=30)
                text = r.stdout
        except Exception:
            pass

        # 解析关键字段
        doc_info = {
            'filename': f['name'],
            'document_type': '未知',
            'hearing_time': None,
            'hearing_location': None,
            'case_no': None,
            'case_type': None,
            'judge_name': None,
            'has_text': len(text) > 50,
        }

        if text:
            # 文书类型
            for dtype, keywords in [
                ('判决书', ['判决书']), ('裁定书', ['裁定书']),
                ('传票', ['应到时间', '应到处所']),
                ('应诉通知书', ['应诉通知']), ('举证通知书', ['举证通知']),
            ]:
                if any(kw in text for kw in keywords):
                    doc_info['document_type'] = dtype
                    break

            # 开庭时间
            m = re.search(r'(?:应到时间|开庭时间)[：:]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日.{0,10}?(\d{1,2})[：:](\d{2})', text)
            if m:
                g = m.groups()
                doc_info['hearing_time'] = f"{g[0]}-{g[1].zfill(2)}-{g[2].zfill(2)} {g[3].zfill(2)}:{g[4].zfill(2)}"

            # 地点
            m = re.search(r'(?:应到处所|开庭地点)[：:]\s*(.+?)(?:\n|$)', text)
            if m:
                doc_info['hearing_location'] = m.group(1).strip()

            # 案号
            m = re.search(r'[（(]\s*\d{4}\s*[）)]\s*[^号]*?\d+号', text)
            if m:
                doc_info['case_no'] = m.group(0).strip().replace(' ', '')

            # 案由
            m = re.search(r'案\s*由[：:]\s*(.+?)(?:\n|$)', text)
            if m:
                doc_info['case_type'] = m.group(1).strip().rstrip('一案')

            # 法官
            m = re.search(r'(?:审判[员长]|审判员|审判长|承办法官)\s*[：:]?\s*([\u4e00-\u9fff]{2,4})', text)
            if m:
                doc_info['judge_name'] = m.group(1).strip()

        results.append(doc_info)

    return results


# ============================================================
#  第四步：归档
# ============================================================

DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')


# 行业词 → 短称映射（核心品牌 <3 字时用短称代替完整行业词）
INDUSTRY_SHORT = {
    '房地产开发': '地产',
    '建设工程': '建设',
    '房地产': '地产',
    '计算机系统': '计算机',
    '信息技术': '信息',
    '网络科技': '网络',
    '进出口': '贸易',
    '商贸': '商贸',
}


def abbreviate_name(name):
    """将当事人名称缩写至≤5字。
    第一性原理：公司名 = 地名前缀 + 核心品牌 + 行业词 + 公司类型。
    缩写保留「核心品牌 + 行业词」，去除地名前缀和公司类型后缀。
    目标 ≤5 字（不是凑满 5 字），自然人为全名。
    """
    if not name or len(name) <= 5:
        return name

    # 公司类型后缀（按长度降序，最长优先匹配）
    company_suffixes = sorted([
        '集团有限公司', '有限责任公司', '股份有限公司', '有限公司',
        '集团', '总公司', '分公司', '律师事务所', '会计事务所',
    ], key=len, reverse=True)
    is_company = False
    for suffix in company_suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            is_company = True
            break
    if not is_company:
        return name[:5]

    # 行业词（去除后核心品牌还剩 ≥2 字才允许去除）
    industry_words = sorted([
        '房地产开发', '建设工程', '房地产', '建工', '建设', '科技',
        '电子', '机械', '实业', '投资', '贸易', '商贸', '进出口',
        '计算机系统', '信息技术', '网络科技', '装饰', '安装',
    ], key=len, reverse=True)

    # 行政地名前缀（含省市后缀的放在前面，最长优先匹配）
    # 省份 + 直辖市（无后缀）
    provinces_bare = [
        '北京', '上海', '天津', '重庆',
        '江苏', '浙江', '广东', '山东', '河南', '河北', '湖南', '湖北',
        '四川', '福建', '安徽', '江西', '辽宁', '吉林', '黑龙江',
        '陕西', '山西', '甘肃', '青海', '云南', '贵州', '海南',
        '内蒙古', '广西', '西藏', '宁夏', '新疆',
    ]
    # 江苏省地级市 + 其他常见城市（无后缀）
    cities_bare = [
        '无锡', '苏州', '南京', '常州', '镇江', '扬州', '南通',
        '徐州', '泰州', '淮安', '盐城', '连云港', '宿迁',
        '杭州', '深圳', '广州', '成都', '武汉', '长沙', '合肥',
        '郑州', '济南', '青岛', '大连', '厦门', '福州', '珠海',
        '东莞', '佛山', '宁波', '温州', '江阴', '宜兴', '常熟',
        '张家港', '昆山', '太仓', '南昌', '南宁', '昆明', '贵阳',
        '太原', '兰州', '哈尔滨', '长春', '沈阳', '石家庄',
    ]
    # 生成所有前缀变体：无后缀 + 省/市/自治区/特别行政区 后缀
    admin_prefixes = []
    for p in provinces_bare:
        admin_prefixes.append(p + '省')
    for c in cities_bare + provinces_bare:
        admin_prefixes.append(c + '市')
    for a in ['内蒙古', '广西', '西藏', '宁夏', '新疆']:
        admin_prefixes.append(a + '自治区')
    admin_prefixes.extend(['香港特别行政区', '澳门特别行政区'])
    # 加上无后缀版本（城市名放前面，因为可能被误匹配）
    admin_prefixes.extend(cities_bare)
    admin_prefixes.extend(provinces_bare)
    # 去重并按长度降序
    admin_prefixes = sorted(set(admin_prefixes), key=len, reverse=True)

    # Step A: 去掉行政地名前缀（保留核心品牌 ≥2 字）
    for prefix in admin_prefixes:
        if name.startswith(prefix) and len(name) - len(prefix) >= 2:
            name = name[len(prefix):]
            break

    # Step A2: 去掉尾部括号内容（律师事务所分所标注，如"德恒（无锡）"→"德恒"）
    name = re.sub(r'（[^）]*）$', '', name)

    # Step B: 如果仍然 >5 字，尝试去掉行业词
    # 保留"核心品牌 + 行业短称"（如"瑞悦地产"），而非全部去掉行业词
    if len(name) > 5:
        for w in industry_words:
            if name.endswith(w) and len(name) - len(w) >= 2:
                core = name[:-len(w)]
                name = core + (INDUSTRY_SHORT.get(w, w[:2]) if len(core) < 3 else '')
                break

    # Step C: 最终兜底截断
    if len(name) > 5:
        name = name[:5]

    # Step D: 清理尾部括号等残留
    name = re.sub(r'[（(]+$', '', name)
    return name


def build_case_folder_name(sms_info, docs):
    """根据案由和当事人构建案卷文件夹名。返回 (folder_name, case_type, parties_str)。"""
    # 从文书提取案由
    case_type = ''
    for d in docs:
        if d.get('case_type'):
            case_type = d['case_type']
            break
    if not case_type:
        case_type = sms_info.get('sms_type', '未命名').replace('_', ' ')

    # 当事人
    parties = sms_info.get('parties', [])
    plaintiff = next((p['name'] for p in parties if p['role'] == 'plaintiff'), None)
    defendant = next((p['name'] for p in parties if p['role'] == 'defendant'), None)

    if plaintiff and defendant:
        folder_name = f"{abbreviate_name(plaintiff)}诉{abbreviate_name(defendant)} {case_type}"
    elif plaintiff:
        folder_name = f"{abbreviate_name(plaintiff)} {case_type}"
    elif defendant:
        folder_name = f"{abbreviate_name(defendant)} {case_type}"
    else:
        folder_name = case_type or "未命名案卷"

    folder_name = re.sub(r'[<>:"|?*/\\]', '', folder_name).strip()
    return folder_name, case_type, f"{plaintiff} vs {defendant}" if plaintiff else ''


def archive_to_desktop(sms_info, docs, files):
    """归档到桌面案卷文件夹。返回归档路径。"""
    folder_name, case_type, parties_str = build_case_folder_name(sms_info, docs)
    case_folder = os.path.join(DESKTOP, folder_name)

    # 送达日期
    sent_at = sms_info.get('sent_at') or datetime.now().strftime('%Y%m%d')
    if len(sent_at) >= 8:
        date_str = sent_at[:4] + sent_at[5:7] + sent_at[8:10] if '-' in sent_at else sent_at[:8]
    else:
        date_str = datetime.now().strftime('%Y%m%d')

    # 确定文件夹名（按优先级选命名文书）
    priority = ['判决书', '裁定书', '传票', '受理案件通知书', '举证通知书']
    naming_doc = '文书'
    for p in priority:
        for d in docs:
            if d.get('document_type') == p:
                naming_doc = p
                break
        if naming_doc != '文书':
            break

    batch_dir = os.path.join(case_folder, '01 法院送达文书', f'{naming_doc}_{date_str}送达')
    os.makedirs(batch_dir, exist_ok=True)

    # 复制文件
    archived = []
    for f in files:
        dest = os.path.join(batch_dir, f"{f['name']}.pdf")
        # 同名处理
        if os.path.exists(dest):
            base, ext = os.path.splitext(dest)
            dest = f"{base}_2{ext}"
        shutil.copy2(f['path'], dest)
        archived.append(dest)

    # 写 OCR 结果
    text_path = os.path.join(batch_dir, '文书解析结果.txt')
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(f"案号: {sms_info.get('case_no', '未知')}\n")
        f.write(f"法院: {sms_info.get('download_result', {}).get('sent_at', '未知')}\n")
        f.write(f"送达日期: {sent_at}\n")
        f.write(f"\n--- 文书清单 ---\n")
        for d in docs:
            f.write(f"\n【{d.get('document_type', '未知')}】{d['filename']}\n")
            if d.get('hearing_time'):
                f.write(f"  开庭时间: {d['hearing_time']}\n")
            if d.get('hearing_location'):
                f.write(f"  开庭地点: {d['hearing_location']}\n")
            if d.get('case_type'):
                f.write(f"  案由: {d['case_type']}\n")

    return {
        'case_folder': case_folder,
        'batch_dir': batch_dir,
        'archived_files': archived,
        'folder_name': folder_name,
    }


# ============================================================
#  第五步：创建提醒（所有三条渠道，一次调用完成）
# ============================================================

def create_all_reminders(report_json_or_file):
    """
    根据全链路报告 JSON 创建所有必要的提醒。
    一次调用覆盖三条渠道（日历 + 系统通知/桌面MD + QQ邮件），
    模型不需要逐渠道调用。
    """
    # 支持文件路径或 JSON 字符串
    if os.path.isfile(report_json_or_file):
        with open(report_json_or_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
    else:
        report = json.loads(report_json_or_file)

    case_no = report.get('sms_parse', {}).get('case_no', '')
    court = report.get('download', {}).get('court_name', '')
    sent_at = report.get('download', {}).get('sent_at', datetime.now().strftime('%Y-%m-%d'))
    if len(sent_at) >= 10:
        sent_at = sent_at[:10]
    else:
        sent_at = datetime.now().strftime('%Y-%m-%d')

    docs = report.get('documents', [])
    results = {'calendar': [], 'deadline': []}

    cal_script = os.path.join(SCRIPT_DIR, 'court_calendar.py')
    deadline_script = os.path.join(SCRIPT_DIR, 'court_deadline_reminder.py')

    for doc in docs:
        hearing_time = doc.get('hearing_time', '')
        hearing_location = doc.get('hearing_location', '')
        case_type = doc.get('case_type', '案件')
        doc_type = doc.get('document_type', '')

        # 传票/开庭 → 日历提醒（三条渠道内置）
        if hearing_time and doc_type in ('传票', '应诉通知书', '出庭通知书'):
            print(f"\n📅 创建开庭提醒: {doc['filename']}", file=sys.stderr)
            r = subprocess.run([
                sys.executable, cal_script,
                case_no, case_type, hearing_time or '待确认', hearing_location or '待确认',
                '工作'
            ], capture_output=True, text=True, timeout=30)
            print(r.stdout, file=sys.stderr)
            if r.stderr:
                print(r.stderr, file=sys.stderr)
            results['calendar'].append({
                'doc': doc['filename'],
                'time': hearing_time,
                'success': '✅ 日历事件已创建' in r.stdout,
            })

        # 判决书/裁定书 → 期限提醒（三条渠道内置）
        if doc_type in ('判决书', '裁定书'):
            print(f"\n⏰ 创建期限提醒: {doc['filename']}", file=sys.stderr)
            r = subprocess.run([
                sys.executable, deadline_script, 'setup',
                case_no, case_type, doc_type, '', sent_at, court
            ], capture_output=True, text=True, timeout=30)
            print(r.stdout, file=sys.stderr)
            if r.stderr:
                print(r.stderr, file=sys.stderr)
            results['deadline'].append({
                'doc': doc['filename'],
                'type': doc_type,
                'success': '全部提醒已设置' in r.stdout,
            })

    return results


# ============================================================
#  第六步：报告生成
# ============================================================

def generate_report(sms_info, download_result, docs, archive_result):
    """生成结构化报告。"""
    report = {
        'success': download_result.get('success', False),
        'pipeline_version': '2.3.0',
        'generated_at': datetime.now().isoformat(),
        'sms_parse': {
            'type': sms_info['sms_type'],
            'case_no': sms_info['case_no'],
            'platform': sms_info['platform'],
            'parties': sms_info['parties'],
        },
        'download': {
            'platform': sms_info['platform'],
            'court_name': download_result.get('court_name', ''),
            'sent_at': download_result.get('sent_at', ''),
            'total': download_result.get('total_docs', 0),
            'downloaded': download_result.get('downloaded', 0),
            'error': download_result.get('error', ''),
        },
        'documents': docs,
        'archive': {
            'folder': archive_result.get('folder_name', ''),
            'path': archive_result.get('case_folder', ''),
            'batch': archive_result.get('batch_dir', ''),
            'files': [os.path.basename(f) for f in archive_result.get('archived_files', [])],
        },
        'actions_needed': [],
        '_remind_command': None,  # 用户确认后直接复制执行
    }

    # 需要后续处理的提示
    if any(d.get('hearing_time') for d in docs):
        report['actions_needed'].append({
            'type': 'calendar_reminder',
            'message': '检测到开庭时间，需要创建日历提醒。请回复「确认」创建。',
            'hearing_info': [
                {'time': d['hearing_time'], 'location': d.get('hearing_location', ''),
                 'doc': d['filename']}
                for d in docs if d.get('hearing_time')
            ]
        })

    # 判决书/裁定书 → 上诉期限
    appeal_docs = [d for d in docs if d['document_type'] in ('判决书', '裁定书')]
    if appeal_docs:
        report['actions_needed'].append({
            'type': 'appeal_deadline',
            'message': f'检测到{len(appeal_docs)}份判决/裁定书，需要设置上诉期限提醒。请回复「确认」创建。',
        })

    # 非 zxfw 平台 → 需要浏览器
    if sms_info['platform'] and sms_info['platform'] != 'zxfw':
        report['actions_needed'].append({
            'type': 'browser_download',
            'platform': sms_info['platform'],
            'message': f'{sms_info["platform"]} 平台无公开 API，需通过浏览器下载。请回复「打开链接」或手动访问。',
            'url': sms_info['download_url'],
        })

    # 生成提醒命令（用户说「确认」后直接跑）
    if report['actions_needed'] and any(a['type'] in ('calendar_reminder', 'appeal_deadline') for a in report['actions_needed']):
        report['_remind_command'] = f"python3 scripts/court_full_pipeline.py --remind '{json.dumps(report, ensure_ascii=False)}'"

    return report


# ============================================================
#  CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='诉讼信息中枢 — 一键全链路（短信→下载→解析→归档→报告）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s --sms "【xx法院】您有(2025)苏0981民初1234号案件文书送达，请点击链接..."
  %(prog)s --sms-file /path/to/sms.txt
  %(prog)s --url "https://zxfw.court.gov.cn/...?qdbh=...&sdbh=...&sdsin=..."
  %(prog)s --photo /path/to/传票.jpg
        '''
    )
    parser.add_argument('--sms', help='法院短信原文')
    parser.add_argument('--sms-file', help='包含短信原文的文件路径')
    parser.add_argument('--url', help='直接提供送达链接（跳过短信解析）')
    parser.add_argument('--photo', help='纸质文书照片路径（调用 OCR）')
    parser.add_argument('--no-archive', action='store_true', help='不归档，仅下载和解析')
    parser.add_argument('--json-only', action='store_true', help='仅输出 JSON，不打印可读报告')
    parser.add_argument('--remind', help='根据全链路 JSON 报告创建提醒——一次调用覆盖全部三条渠道')
    parser.add_argument('--remind-file', help='从 JSON 文件读取报告创建提醒（避免命令行长度限制）')
    parser.add_argument('--no-remind', action='store_true', help='不自动创建提醒（需要提醒时用 --remind 单独执行）')

    args = parser.parse_args()

    # --- 提醒模式：根据 JSON 报告创建全部提醒 ---
    remind_input = args.remind or args.remind_file
    if remind_input:
        if args.remind_file:
            remind_input = args.remind_file  # 文件路径模式
        print("⏰ 创建全部提醒（日历 + 系统通知 + QQ邮件）...", file=sys.stderr)
        results = create_all_reminders(remind_input)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        # 汇总
        cal_ok = sum(1 for r in results['calendar'] if r['success'])
        dl_ok = sum(1 for r in results['deadline'] if r['success'])
        print(f"\n✅ 日历提醒: {cal_ok}/{len(results['calendar'])} 已创建", file=sys.stderr)
        print(f"✅ 期限提醒: {dl_ok}/{len(results['deadline'])} 已创建", file=sys.stderr)
        print(f"📋 三条渠道全覆盖: 系统日历 + 本机通知/桌面MD + QQ邮件", file=sys.stderr)
        return 0

    # --- 获取输入 ---
    sms_text = None
    image_path = None
    direct_url = None

    if args.sms:
        sms_text = args.sms
    elif args.sms_file:
        with open(args.sms_file, 'r', encoding='utf-8') as f:
            sms_text = f.read()
    elif args.url:
        direct_url = args.url
    elif args.photo:
        image_path = args.photo
    else:
        parser.print_help()
        sys.exit(1)

    # --- 照片模式：委托给 court_photo_ocr.py ---
    if image_path:
        print("📷 照片 OCR 模式", file=sys.stderr)
        ocr_script = os.path.join(SCRIPT_DIR, 'court_photo_ocr.py')
        r = subprocess.run([sys.executable, ocr_script, image_path],
                           capture_output=True, text=True, timeout=120)
        print(r.stderr, file=sys.stderr)
        try:
            result = json.loads(r.stdout.strip().split('\n')[-1])
        except:
            result = {'error': 'OCR 解析失败', 'raw': r.stdout[:500]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not result.get('error') else 1

    # --- 纯链接模式：直接用 URL 的参数 ---
    if direct_url and not sms_text:
        sms_text = f"送达链接: {direct_url}"

    # --- 短信模式：完整链路 ---
    print("=" * 55, file=sys.stderr)
    print("📋 诉讼信息中枢 · 一键全链路", file=sys.stderr)
    print("=" * 55, file=sys.stderr)

    # 第一步：解析
    print("\n🔍 第一步：解析短信...", file=sys.stderr)
    sms_info = parse_sms(sms_text)
    print(f"   类型: {sms_info['sms_type']}", file=sys.stderr)
    print(f"   案号: {sms_info['case_no'] or '未识别'}", file=sys.stderr)
    print(f"   平台: {sms_info['platform'] or '未识别'}", file=sys.stderr)

    # 第二步：下载
    download_result = {'success': False, 'files': [], 'error': ''}
    if sms_info['platform'] == 'zxfw' and sms_info['params']:
        print(f"\n⬇️  第二步：下载文书 (zxfw API)...", file=sys.stderr)
        download_result = download_zxfw(sms_info['params'])
        if download_result['success']:
            print(f"   ✅ 已下载 {download_result['downloaded']}/{download_result['total_docs']} 份文书", file=sys.stderr)
            print(f"   法院: {download_result['court_name']}", file=sys.stderr)
        else:
            print(f"   ❌ {download_result.get('error', '下载失败')}", file=sys.stderr)
    elif sms_info['platform']:
        print(f"\n⬇️  第二步：{sms_info['platform']} 平台需浏览器下载", file=sys.stderr)
        download_result['error'] = f"{sms_info['platform']} 平台无公开 API，需通过浏览器下载"
        download_result['url'] = sms_info['download_url']
    else:
        print(f"\n⬇️  第二步：未识别送达平台，无法下载", file=sys.stderr)

    # 第三步：PDF 解析
    docs = []
    if download_result.get('files'):
        print(f"\n📄 第三步：解析文书...", file=sys.stderr)
        docs = parse_pdfs(download_result['files'])
        for d in docs:
            extra = ''
            if d.get('hearing_time'):
                extra = f" | ⚠️ 开庭: {d['hearing_time']}"
            print(f"   {d['document_type']}: {d['filename']}{extra}", file=sys.stderr)

    # 第四步：归档
    archive_result = {}
    if not args.no_archive and download_result.get('files'):
        print(f"\n📁 第四步：归档...", file=sys.stderr)
        archive_result = archive_to_desktop(sms_info, docs, download_result['files'])
        print(f"   {archive_result['folder_name']}", file=sys.stderr)
        print(f"   {archive_result['batch_dir']}", file=sys.stderr)

    # 第五步：报告
    sms_info['download_result'] = download_result
    report = generate_report(sms_info, download_result, docs, archive_result)

    # --- 默认自动创建提醒（除非 --no-remind）---
    if not args.no_remind and report['actions_needed']:
        has_reminders = any(a['type'] in ('calendar_reminder', 'appeal_deadline') for a in report['actions_needed'])
        if has_reminders:
            print(f"\n⏰ 自动创建提醒（日历 + 系统通知 + QQ邮件）...", file=sys.stderr)
            remind_results = create_all_reminders(json.dumps(report, ensure_ascii=False))
            report['_auto_remind_results'] = remind_results

    if not args.json_only:
        print(f"\n{'='*55}", file=sys.stderr)
        print(f"📊 处理完成", file=sys.stderr)
        print(f"{'='*55}", file=sys.stderr)
        if report['download']['downloaded']:
            print(f"   📥 下载: {report['download']['downloaded']} 份文书", file=sys.stderr)
        if report['archive'].get('path'):
            print(f"   📁 归档: {report['archive']['path']}", file=sys.stderr)
        if not args.no_remind and report.get('_auto_remind_results'):
            cal = report['_auto_remind_results'].get('calendar', [])
            dl = report['_auto_remind_results'].get('deadline', [])
            print(f"   ⏰ 提醒已自动创建: 日历 {sum(1 for r in cal if r['success'])} 项 + 期限 {sum(1 for r in dl if r['success'])} 项", file=sys.stderr)
            print(f"   📋 三条渠道: 日历 + 通知/桌面MD + QQ邮件", file=sys.stderr)
        else:
            for action in report['actions_needed']:
                print(f"   ⚡ 待处理: {action['message']}", file=sys.stderr)

    # 输出 JSON
    print(json.dumps(report, ensure_ascii=False, indent=2))

    # 清理
    try:
        shutil.rmtree(STAGING)
    except OSError:
        pass

    return 0 if report['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
