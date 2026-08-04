#!/usr/bin/env python3
"""
专利年费监控+IP资产台账 - 核心功能模块

功能：
1. 专利法律状态查询（通过免费公开数据源）
2. 年费到期日计算与提醒
3. IP资产台账管理（增删改查+CSV导入导出）
4. 多国专利支持（中国、美国、欧洲、PCT、日本、韩国、英国、德国、法国、瑞士）
5. 滞纳金计算
6. 日历提醒（iCalendar格式）
7. 推送通知生成

数据源（免费，无需API Key）：
- Google Patents: https://patents.google.com
- USPTO ODP: https://api.uspto.gov
- EPO OPS: https://ops.epo.org
- WIPO PATENTSCOPE: https://patentscope.wipo.int
"""

import csv
import io
import json
import os
import re
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Tuple, Any
from urllib.parse import quote

# IP资产管理 - 内存台账（使用技能期间持久化）
# 实际应用中可用文件持久化
IP_ASSETS: List[Dict[str, Any]] = []
DATA_FILE = os.path.join(os.path.dirname(__file__), "ip_assets.json")


# ============================================================
# 专利号识别与解析
# ============================================================

PATTERN_MAP = [
    # 美国专利: US12345678B2, US20230123456A1
    (r'^US\d{6,11}[A-Z0-9]*$', 'US', 'patent'),
    # 中国专利: CN202310123456.X, CN202310123456
    (r'^CN\d{9,13}\.?[A-Z0-9]*$', 'CN', 'patent'),
    # 中国实用新型: 已包含在CN中
    # 欧洲专利: EP12345678, EP12345678B1
    (r'^EP\d{7,10}[A-Z0-9]*$', 'EP', 'patent'),
    # PCT/WO: WO2023123456, PCT/CN2023/123456
    (r'^(WO|PCT[/]?)\d{2,4}[/]?\d{5,8}', 'WO', 'patent'),
    # 日本专利: JP12345678, JP2023123456
    (r'^JP\d{7,13}[A-Z0-9]*$', 'JP', 'patent'),
    # 韩国专利: KR1020230012345
    (r'^KR\d{9,15}[A-Z0-9]*$', 'KR', 'patent'),
    # 英国专利: GB1234567
    (r'^GB\d{7,10}[A-Z0-9]*$', 'GB', 'patent'),
    # 德国专利: DE102023123456
    (r'^DE\d{10,13}[A-Z0-9]*$', 'DE', 'patent'),
    # 法国专利: FR1234567
    (r'^FR\d{7,10}[A-Z0-9]*$', 'FR', 'patent'),
    # 瑞士专利: CH1234567, CH01234567
    (r'^CH\d{6,10}[A-Z0-9]*$', 'CH', 'patent'),
]


COUNTRY_NAMES = {
    'US': '美国', 'CN': '中国', 'EP': '欧洲', 'WO': 'PCT国际',
    'JP': '日本', 'KR': '韩国', 'GB': '英国', 'DE': '德国', 'FR': '法国',
    'CH': '瑞士',
}


def identify_patent(patent_no: str) -> Optional[Dict[str, str]]:
    """识别专利号所属国家与类型"""
    patent_no = patent_no.strip().upper()
    for pattern, country, ptype in PATTERN_MAP:
        if re.match(pattern, patent_no):
            return {
                'patent_no': patent_no,
                'country': country,
                'country_name': COUNTRY_NAMES.get(country, country),
                'type': ptype
            }
    return None


# ============================================================
# 免费数据源查询
# ============================================================

def query_google_patents(patent_no: str) -> Optional[Dict[str, Any]]:
    """
    通过 Google Patents 查询专利信息（免费，无需API Key）
    使用搜索方式获取专利的基本信息
    """
    try:
        from coze_workload_identity import requests
        
        # Google Patents 公开页面
        url = f"https://patents.google.com/patent/{quote(patent_no)}/en"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }
        resp = requests.get(url, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            return None
        
        text = resp.text
        
        # 提取基本信息（从页面元数据）
        result = {
            'patent_no': patent_no,
            'source': 'Google Patents',
            'title': _extract_meta(text, 'citation_title'),
            'publication_date': _extract_meta(text, 'citation_publication_date'),
            'patent_status': _extract_meta(text, 'citation_patent_status'),
            'filing_date': _extract_date_from_text(text, 'filing date'),
            'grant_date': _extract_meta(text, 'citation_patent_date'),
            'inventor': _extract_meta(text, 'citation_author'),
            'applicant': _extract_meta(text, 'citation_assignee'),
            'abstract': _extract_meta(text, 'citation_abstract'),
        }
        return result
    except Exception as e:
        return {'patent_no': patent_no, 'source': 'Google Patents', 'error': str(e)}


def query_uspto_bibliographic(patent_no: str) -> Optional[Dict[str, Any]]:
    """
    查询USPTO ODP API（公开数据，需注册免费API Key）
    实际使用时需要API Key，这里作为骨架
    """
    try:
        from coze_workload_identity import requests
        
        api_key = os.getenv("COZE_USPTO_API_KEY")
        if not api_key:
            return None  # 无API Key时回退到Google Patents
        
        # 提取纯数字部分
        numbers = re.findall(r'\d+', patent_no)
        if not numbers:
            return None
        app_number = numbers[0]
        
        url = "https://api.uspto.gov/api/v1/patent/applications/search"
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }
        payload = {
            "q": f"applicationNumberText:{app_number}",
            "limit": 1,
            "offset": 0
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if data.get('totalCount', 0) == 0:
            return None
        
        record = data['results'][0]
        meta = record.get('applicationMetaData', {})
        
        return {
            'patent_no': patent_no,
            'source': 'USPTO ODP',
            'title': meta.get('inventionTitleText'),
            'filing_date': meta.get('filingDate'),
            'grant_date': meta.get('grantDate'),
            'status': meta.get('applicationStatusDescriptionText'),
            'status_code': meta.get('applicationStatusCode'),
            'applicant': ', '.join([a.get('nameText','') for a in meta.get('applicantBag', []) if a.get('nameText')]),
            'inventor': ', '.join([i.get('nameText','') for i in meta.get('inventorBag', []) if i.get('nameText')]),
        }
    except Exception as e:
        return {'patent_no': patent_no, 'source': 'USPTO', 'error': str(e)}


def query_epo_ops(patent_no: str) -> Optional[Dict[str, Any]]:
    """
    查询EPO OPS API（欧洲专利局开放专利服务）
    需要注册免费账号获取API Key
    """
    try:
        from coze_workload_identity import requests
        
        # 尝试使用EPO OPS公开接口
        number = re.sub(r'[^0-9]', '', patent_no.replace('EP', ''))
        if not number:
            return None
        
        url = f"https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/{quote(patent_no)}/biblio"
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'PatentFeeMonitor/1.0'
        }
        
        resp = requests.get(url, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        # EPO返回结构复杂，提取关键字段
        exchange_doc = data.get('exchange-document', {})
        bibliographic = exchange_doc.get('bibliographic-data', {})
        publication = bibliographic.get('publication-reference', {}).get('document-id', [{}])
        
        # 简化提取
        result = {
            'patent_no': patent_no,
            'source': 'EPO OPS',
        }
        
        # 提取标题
        invention_title = bibliographic.get('invention-title', [])
        if isinstance(invention_title, list) and invention_title:
            for t in invention_title:
                if isinstance(t, dict) and t.get('$'):
                    result['title'] = t['$']
                    break
        
        # 提取申请日
        priority_info = bibliographic.get('priority-claims', {}).get('priority-claim', [])
        if isinstance(priority_info, list) and priority_info:
            date_info = priority_info[0].get('priority-date', {})
            result['filing_date'] = date_info.get('$', date_info.get('#text'))
        
        return result
    except Exception as e:
        return {'patent_no': patent_no, 'source': 'EPO', 'error': str(e)}


def query_wipo_patentscope(patent_no: str) -> Optional[Dict[str, Any]]:
    """
    查询WIPO PATENTSCOPE API（PCT国际申请）
    """
    try:
        from coze_workload_identity import requests
        
        wo_num = re.sub(r'[^0-9]', '', patent_no.replace('WO', ''))
        if not wo_num:
            return None
        
        url = f"https://patentscope.wipo.int/rest/patentscope/public/psiclaims?searchTerms=WO{wo_num}&sort=score+desc&rows=1&start=0"
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'PatentFeeMonitor/1.0'
        }
        
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None
        
        return {'patent_no': patent_no, 'source': 'WIPO PATENTSCOPE', 'data': resp.json()}
    except Exception as e:
        return {'patent_no': patent_no, 'source': 'WIPO', 'error': str(e)}


def query_patent_with_retry(patent_no: str, country: str = 'CN') -> Optional[Dict[str, Any]]:
    """
    多源重试查询策略：按优先级依次尝试多个数据源，直到成功

    Args:
        patent_no: 专利号
        country: 国家代码，用于选择查询优先级

    Returns:
        查询结果字典，或None（全部失败）
    """
    # 定义查询源优先级（按国家）
    source_priority = {
        'US': [query_uspto_bibliographic, query_google_patents],
        'EP': [query_epo_ops, query_google_patents],
        'WO': [query_wipo_patentscope, query_google_patents],
        'CN': [query_google_patents],
        'JP': [query_google_patents],
        'KR': [query_google_patents],
        'GB': [query_google_patents],
        'DE': [query_google_patents],
        'FR': [query_google_patents],
        'CH': [query_google_patents],
    }

    # 通用回退：所有国家都可以尝试Google Patents
    sources = source_priority.get(country, [query_google_patents])
    # 确保Google Patents作为最终回退
    if query_google_patents not in sources:
        sources.append(query_google_patents)

    last_error = None
    for query_func in sources:
        try:
            result = query_func(patent_no)
            if result and not result.get('error'):
                return result
            if result and result.get('error'):
                last_error = result['error']
        except Exception as e:
            last_error = str(e)
            continue

    # 全部失败，返回最后错误
    return {'patent_no': patent_no, 'error': last_error or '所有数据源查询均失败'}


# ============================================================
# 辅助函数
# ============================================================

def _extract_meta(html: str, meta_name: str) -> Optional[str]:
    """从HTML中提取meta标签内容"""
    patterns = [
        rf'<meta\s+name=["\']{meta_name}["\']\s+content=["\']([^"\']+)["\']',
        rf'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']{meta_name}["\']',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _extract_date_from_text(html: str, keyword: str) -> Optional[str]:
    """从HTML文本中提取日期"""
    # 简单模式：找 keyword 附近的日期
    pat = rf'{keyword}.*?(\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}})'
    m = re.search(pat, html[:5000], re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def _normalize_date(date_str: str) -> Optional[str]:
    """标准化日期为 YYYY-MM-DD 格式"""
    if not date_str:
        return None
    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%d/%m/%Y', '%m/%d/%Y']:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return date_str


# ============================================================
# 年费计算引擎
# ============================================================

CN_PATENT_FEES = {
    'invention': {  # 发明专利
        (1, 3): 900, (4, 6): 1200, (7, 9): 2000,
        (10, 12): 4000, (13, 15): 6000, (16, 20): 8000,
    },
    'utility': {  # 实用新型
        (1, 3): 600, (4, 5): 900, (6, 8): 1200, (9, 10): 2000,
    },
    'design': {  # 外观设计
        (1, 3): 600, (4, 5): 900, (6, 8): 1200, (9, 10): 2000,
    },
}

US_MAINTENANCE_FEES = {
    'large': {3.5: 1600, 7.5: 3600, 11.5: 7400},
    'small': {3.5: 800, 7.5: 1800, 11.5: 3700},
    'micro': {3.5: 400, 7.5: 900, 11.5: 1850},
}

# 欧洲专利生效国年费参考（EUR/年）
# 来源：EPO成员国官方年费标准（仅供参考）
EP_COUNTRY_FEES = {
    'DE': {  # 德国
        (1, 3): 60, (4, 6): 120, (7, 9): 190,
        (10, 12): 300, (13, 15): 500, (16, 20): 800,
    },
    'GB': {  # 英国
        (1, 3): 50, (4, 6): 100, (7, 9): 160,
        (10, 12): 250, (13, 15): 400, (16, 20): 600,
    },
    'FR': {  # 法国
        (1, 3): 60, (4, 6): 120, (7, 9): 200,
        (10, 12): 320, (13, 15): 520, (16, 20): 750,
    },
    'CH': {  # 瑞士
        (1, 3): 100, (4, 6): 200, (7, 9): 350,
        (10, 12): 500, (13, 15): 700, (16, 20): 1000,
    },
    'IT': {  # 意大利
        (1, 3): 50, (4, 6): 100, (7, 9): 150,
        (10, 12): 250, (13, 15): 400, (16, 20): 550,
    },
    'NL': {  # 荷兰
        (1, 3): 60, (4, 6): 120, (7, 9): 200,
        (10, 12): 300, (13, 15): 450, (16, 20): 650,
    },
    'SE': {  # 瑞典
        (1, 3): 60, (4, 6): 120, (7, 9): 200,
        (10, 12): 300, (13, 15): 450, (16, 20): 600,
    },
}

# 滞纳金规则（按国家）
SURCHARGE_RULES = {
    'CN': {
        'description': '中国专利滞纳金',
        'rules': [
            (0, 30, 0.05),    # 1个月内（含）：加收5%
            (30, 60, 0.10),   # 1-2个月：加收10%
            (60, 90, 0.15),   # 2-3个月：加收15%
            (90, 180, 0.20),  # 3-6个月：加收20%
            (180, 99999, -1), # 超过6个月：专利权终止
        ]
    },
    'US': {
        'description': '美国专利滞纳金',
        'rules': [
            (0, 180, 0.05),   # 6个月内：加收5%
            (180, 99999, -1), # 超过6个月：专利权终止
        ]
    },
    'EP': {
        'description': '欧洲专利滞纳金',
        'rules': [
            (0, 30, 0.05),    # 1个月内：加收5%
            (30, 60, 0.10),   # 1-2个月：加收10%
            (60, 90, 0.15),   # 2-3个月：加收15%
            (90, 180, 0.25),  # 3-6个月：加收25%
            (180, 99999, -1), # 超过6个月：专利权终止
        ]
    },
    'default': {
        'description': '通用滞纳金规则',
        'rules': [
            (0, 30, 0.05),
            (30, 60, 0.10),
            (60, 90, 0.15),
            (90, 180, 0.25),
            (180, 99999, -1),
        ]
    }
}


def calc_cn_fee_year(filing_date_str: str, reference_date: Optional[str] = None) -> Tuple[int, float]:
    """
    计算中国专利当前年度和应交年费
    """
    filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d')
    ref = datetime.strptime(reference_date, '%Y-%m-%d') if reference_date else datetime.now()
    
    # 计算从申请日起的第几年
    year_count = (ref.year - filing_date.year) + 1
    if ref.month < filing_date.month or (ref.month == filing_date.month and ref.day < filing_date.day):
        year_count -= 1
    if year_count < 1:
        year_count = 1
    
    return year_count, 0  # 具体金额需要确定专利类型


def calc_cn_fee(patent_type: str, year_count: int) -> float:
    """计算中国专利指定年度的年费"""
    fee_table = CN_PATENT_FEES.get(patent_type, CN_PATENT_FEES['invention'])
    for (start, end), fee in fee_table.items():
        if start <= year_count <= end:
            return fee
    return list(fee_table.values())[-1]  # 超过年限返回最高档


def calc_us_maintenance_fee(patent_no: str, grant_date_str: str, entity_size: str = 'small') -> List[Dict]:
    """
    计算美国专利维护费到期日
    美国专利需要在授权后的第3.5、7.5、11.5年缴纳维护费
    """
    grant_date = datetime.strptime(grant_date_str, '%Y-%m-%d')
    fees = US_MAINTENANCE_FEES.get(entity_size, US_MAINTENANCE_FEES['small'])
    
    deadlines = []
    for year_mark, amount in fees.items():
        due_date = grant_date + timedelta(days=int(year_mark * 365))
        deadlines.append({
            'due_year': year_mark,
            'due_date': due_date.strftime('%Y-%m-%d'),
            'amount': amount,
            'entity_size': entity_size,
            'grace_period_end': (due_date + timedelta(days=180)).strftime('%Y-%m-%d'),
        })
    
    return deadlines


def calc_ep_country_fee(country: str, year_count: int) -> Optional[float]:
    """
    计算欧洲专利在指定生效国的年费

    Args:
        country: 国家代码（DE/GB/FR/CH/IT/NL/SE）
        year_count: 专利年数

    Returns:
        年费金额（EUR），如无对应国家规则返回None
    """
    fee_table = EP_COUNTRY_FEES.get(country)
    if not fee_table:
        return None
    for (start, end), fee in fee_table.items():
        if start <= year_count <= end:
            return fee
    return list(fee_table.values())[-1]


def calc_ep_fees(filing_date_str: str, countries: List[str] = None) -> List[Dict]:
    """
    计算欧洲专利在各生效国的年费

    Args:
        filing_date_str: 申请日
        countries: 生效国列表，默认全部

    Returns:
        各生效国年费列表
    """
    if countries is None:
        countries = ['DE', 'GB', 'FR', 'CH', 'IT', 'NL', 'SE']
    
    year_count, _ = calc_cn_fee_year(filing_date_str)
    results = []
    
    for country in countries:
        fee = calc_ep_country_fee(country, year_count)
        if fee is not None:
            results.append({
                'country': country,
                'country_name': COUNTRY_NAMES.get(country, country),
                'year_count': year_count,
                'fee_eur': fee,
                'fee_approx_cny': round(fee * 8.0, 2),  # 近似汇率
            })
    
    return results


def calc_surcharge(country: str, overdue_days: int, base_fee: float) -> Dict[str, Any]:
    """
    计算滞纳金

    Args:
        country: 国家代码
        overdue_days: 逾期天数
        base_fee: 基础年费

    Returns:
        滞纳金计算结果
    """
    rules = SURCHARGE_RULES.get(country, SURCHARGE_RULES['default'])
    
    for start, end, rate in rules["rules"]:
        if start <= overdue_days < end:
            if rate < 0:
                return {
                    'overdue_days': overdue_days,
                    'status': 'expired',
                    'message': f'逾期超过{end}天，专利权可能已终止',
                    'surcharge_rate': None,
                    'surcharge_amount': None,
                    'total_due': None,
                }
            else:
                surcharge = round(base_fee * rate, 2)
                return {
                    'overdue_days': overdue_days,
                    'status': 'overdue',
                    'surcharge_rate': rate,
                    'surcharge_amount': surcharge,
                    'total_due': round(base_fee + surcharge, 2),
                    'message': f'逾期{overdue_days}天，滞纳金{rate:.0%}，需缴{base_fee + surcharge:.2f}',
                }
    
    return {
        'overdue_days': overdue_days,
        'status': 'unknown',
        'message': '未知逾期状态',
    }


def calc_remaining_days(due_date_str: str) -> int:
    """计算距离截止日的剩余天数"""
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
    delta = (due_date - datetime.now()).days
    return max(delta, 0)


def get_risk_level(remaining_days: int) -> Tuple[str, str]:
    """根据剩余天数判断风险等级"""
    if remaining_days > 90:
        return '🟢', '正常'
    elif remaining_days > 30:
        return '🟡', '黄色预警'
    elif remaining_days > 0:
        return '🔴', '红色警报'
    else:
        return '⚫', '已过期'


# ============================================================
# 日历提醒生成（iCalendar格式）
# ============================================================

def generate_calendar_reminder(patent_no: str, title: str, due_date_str: str,
                                fee_amount: str = '', notes: str = '') -> Dict[str, str]:
    """
    生成iCalendar格式的日历提醒

    Args:
        patent_no: 专利号
        title: 事件标题
        due_date_str: 到期日（YYYY-MM-DD）
        fee_amount: 费用金额
        notes: 备注

    Returns:
        包含ics内容和文件路径的字典
    """
    ics_content = _generate_ics_content(patent_no, title, due_date_str, fee_amount, notes)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    ics_dir = os.path.join(script_dir, 'calendar')
    os.makedirs(ics_dir, exist_ok=True)

    safe_patent = re.sub(r'[^\w]', '_', patent_no)
    filename = f'patent_reminder_{safe_patent}_{due_date_str}.ics'
    filepath = os.path.join(ics_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(ics_content)

    return {
        'ics_content': ics_content,
        'file_path': filepath,
        'filename': filename,
    }


def _generate_ics_content(patent_no: str, title: str, due_date_str: str,
                           fee_amount: str = '', notes: str = '') -> str:
    """
    生成iCalendar格式的文本内容

    Args:
        patent_no: 专利号
        title: 事件标题
        due_date_str: 到期日（YYYY-MM-DD）
        fee_amount: 费用金额
        notes: 备注

    Returns:
        iCalendar格式文本
    """
    from datetime import timezone

    now = datetime.now(timezone.utc)
    due_dt = datetime.strptime(due_date_str, '%Y-%m-%d')
    due_dt_utc = due_dt.replace(tzinfo=timezone.utc)

    # 事件描述
    description = f"专利年费到期提醒 - {patent_no}"
    if fee_amount:
        description += f"\\n应付金额：{fee_amount}"
    if notes:
        description += f"\\n备注：{notes}"
    description += f"\\n\\n请在到期日前缴纳年费，逾期将产生滞纳金。"

    # 提前7天提醒
    alarm_due = due_dt_utc - timedelta(days=7)

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//PatentFeeMonitor//CN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{patent_no}@{due_date_str}
DTSTAMP:{now.strftime('%Y%m%dT%H%M%SZ')}
DTSTART;VALUE=DATE:{due_dt.strftime('%Y%m%d')}
DTEND;VALUE=DATE:{due_dt.strftime('%Y%m%d')}
SUMMARY:专利年费到期 - {title}
DESCRIPTION:{description}
CATEGORIES:专利年费
BEGIN:VALARM
TRIGGER:-P7D
ACTION:DISPLAY
DESCRIPTION:专利年费即将到期
END:VALARM
END:VEVENT
END:VCALENDAR"""
    return ics


# ============================================================
# 推送通知生成
# ============================================================

def generate_push_notifications(assets: List[Dict] = None) -> List[Dict[str, Any]]:
    """
    生成推送通知列表

    Args:
        assets: IP资产列表，默认从台账加载

    Returns:
        通知列表
    """
    if assets is None:
        assets = load_assets()

    today = datetime.now()
    notifications = []

    for asset in assets:
        fee_date_str = asset.get('next_fee_date', '')
        if not fee_date_str:
            continue

        try:
            fee_date = datetime.strptime(fee_date_str, '%Y-%m-%d')
            remaining = (fee_date - today).days
        except ValueError:
            continue

        risk_icon, risk_text = get_risk_level(remaining)
        ip_no = asset.get('ip_no', '')
        title = asset.get('title', '未命名')

        notification = {
            'asset_id': asset.get('id'),
            'ip_no': ip_no,
            'title': title,
            'due_date': fee_date_str,
            'remaining_days': max(remaining, 0),
            'risk_icon': risk_icon,
            'risk_level': risk_text,
            'message': f'{risk_icon} [{risk_text}] {ip_no} - {title}，到期日：{fee_date_str}，剩余{max(remaining, 0)}天',
        }

        # 标记紧急程度
        if remaining <= 0:
            notification['priority'] = 'critical'
            notification['action_required'] = '立即缴费，专利可能已过期'
        elif remaining <= 30:
            notification['priority'] = 'high'
            notification['action_required'] = '尽快缴费，避免逾期'
        elif remaining <= 90:
            notification['priority'] = 'medium'
            notification['action_required'] = '安排缴费计划'
        else:
            notification['priority'] = 'low'
            notification['action_required'] = '无需立即处理'

        notifications.append(notification)

    # 按紧急程度排序
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    notifications.sort(key=lambda n: priority_order.get(n.get('priority', 'low'), 99))

    return notifications


def get_due_soon_summary(days: int = 30) -> List[Dict[str, Any]]:
    """
    获取即将到期的专利摘要

    Args:
        days: 未来天数，默认30天

    Returns:
        即将到期的专利列表
    """
    assets = load_assets()
    today = datetime.now()
    cutoff = today + timedelta(days=days)

    due_soon = []
    for asset in assets:
        fee_date_str = asset.get('next_fee_date', '')
        if not fee_date_str:
            continue
        try:
            fee_date = datetime.strptime(fee_date_str, '%Y-%m-%d')
            if today <= fee_date <= cutoff:
                remaining = (fee_date - today).days
                due_soon.append({
                    'id': asset.get('id'),
                    'ip_no': asset.get('ip_no', ''),
                    'title': asset.get('title', '未命名'),
                    'due_date': fee_date_str,
                    'remaining_days': remaining,
                    'risk_icon': '🔴' if remaining <= 7 else '🟡',
                })
        except ValueError:
            continue

    due_soon.sort(key=lambda x: x['remaining_days'])
    return due_soon


# ============================================================
# IP资产台账管理
# ============================================================

def load_assets() -> List[Dict]:
    """从本地文件加载IP资产"""
    global IP_ASSETS
    if IP_ASSETS:
        return IP_ASSETS
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                IP_ASSETS = json.load(f)
    except Exception:
        IP_ASSETS = []
    return IP_ASSETS


def save_assets():
    """保存IP资产到本地文件"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(IP_ASSETS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存台账失败: {e}")


def add_asset(asset: Dict) -> Dict:
    """添加一个IP资产"""
    assets = load_assets()
    
    # 规范化字段
    entry = {
        'id': len(assets) + 1,
        'ip_no': asset.get('ip_no', '').strip(),
        'title': asset.get('title', '').strip(),
        'type': asset.get('type', 'patent'),  # patent/trademark/copyright
        'sub_type': asset.get('sub_type', 'invention'),  # invention/utility/design
        'country': asset.get('country', 'CN'),
        'filing_date': _normalize_date(asset.get('filing_date', '')),
        'grant_date': _normalize_date(asset.get('grant_date', '')),
        'next_fee_date': _normalize_date(asset.get('next_fee_date', '')),
        'status': asset.get('status', '未知'),
        'owner': asset.get('owner', ''),
        'inventor': asset.get('inventor', ''),
        'notes': asset.get('notes', ''),
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    assets.append(entry)
    IP_ASSETS = assets
    save_assets()
    return entry


def update_asset(asset_id: int, updates: Dict) -> Optional[Dict]:
    """更新IP资产信息"""
    assets = load_assets()
    for i, asset in enumerate(assets):
        if asset.get('id') == asset_id:
            for key, val in updates.items():
                if val is not None:
                    assets[i][key] = val
            assets[i]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            IP_ASSETS = assets
            save_assets()
            return assets[i]
    return None


def delete_asset(asset_id: int) -> bool:
    """删除IP资产"""
    assets = load_assets()
    new_assets = [a for a in assets if a.get('id') != asset_id]
    if len(new_assets) < len(assets):
        IP_ASSETS = new_assets
        save_assets()
        return True
    return False


def get_asset_by_no(ip_no: str) -> Optional[Dict]:
    """根据编号查找IP资产"""
    assets = load_assets()
    for asset in assets:
        if asset.get('ip_no', '').upper() == ip_no.strip().upper():
            return asset
    return None


def import_csv(csv_content: str) -> Tuple[int, List[str]]:
    """从CSV内容批量导入IP资产"""
    lines = csv_content.strip().split('\n')
    reader = csv.DictReader(io.StringIO(csv_content))
    success = 0
    errors = []
    
    for row_num, row in enumerate(reader, start=2):
        if not row.get('ip_no', '').strip():
            errors.append(f"第{row_num}行缺少ip_no")
            continue
        try:
            add_asset({
                'ip_no': row.get('ip_no', ''),
                'title': row.get('title', ''),
                'type': row.get('type', 'patent'),
                'sub_type': row.get('sub_type', 'invention'),
                'country': row.get('country', 'CN'),
                'filing_date': row.get('filing_date', ''),
                'grant_date': row.get('grant_date', ''),
                'next_fee_date': row.get('next_fee_date', ''),
                'status': row.get('status', '未知'),
                'owner': row.get('owner', ''),
                'notes': row.get('notes', ''),
            })
            success += 1
        except Exception as e:
            errors.append(f"第{row_num}行导入失败: {e}")
    
    return success, errors


def get_assets_summary() -> Dict:
    """获取资产总览统计"""
    assets = load_assets()
    summary = {
        'total': len(assets),
        'patents': 0,
        'trademarks': 0,
        'copyrights': 0,
        'by_country': {},
        'by_status': {},
        'due_soon': 0,  # 30天内到期
        'due_warning': 0,  # 30-90天
        'safe': 0,  # 90天以上
    }
    
    today = datetime.now()
    
    for asset in assets:
        atype = asset.get('type', 'patent')
        country = asset.get('country', '其他')
        status = asset.get('status', '未知')
        fee_date_str = asset.get('next_fee_date', '')
        
        if atype == 'patent':
            summary['patents'] += 1
        elif atype == 'trademark':
            summary['trademarks'] += 1
        elif atype == 'copyright':
            summary['copyrights'] += 1
        
        summary['by_country'][country] = summary['by_country'].get(country, 0) + 1
        summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
        
        if fee_date_str:
            try:
                fee_date = datetime.strptime(fee_date_str, '%Y-%m-%d')
                remaining = (fee_date - today).days
                if remaining <= 0:
                    summary['due_soon'] += 1
                elif remaining <= 30:
                    summary['due_soon'] += 1
                elif remaining <= 90:
                    summary['due_warning'] += 1
                else:
                    summary['safe'] += 1
            except ValueError:
                pass
    
    return summary


def export_assets_csv() -> str:
    """导出IP资产台账为CSV"""
    assets = load_assets()
    if not assets:
        return "暂无IP资产数据"
    
    output = io.StringIO()
    fieldnames = ['ip_no', 'title', 'type', 'sub_type', 'country', 
                  'filing_date', 'grant_date', 'next_fee_date', 
                  'status', 'owner', 'inventor', 'notes']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for asset in assets:
        writer.writerow({k: asset.get(k, '') for k in fieldnames})
    
    return output.getvalue()


# ============================================================
# 年费监控主流程
# ============================================================

def monitor_patent_fee(patent_no: str, auto_query: bool = True) -> Dict[str, Any]:
    """
    监控单件专利的年费状态

    Args:
        patent_no: 专利号
        auto_query: 是否自动联网查询

    Returns:
        监控结果字典
    """
    identified = identify_patent(patent_no)
    if not identified:
        return {
            'error': True,
            'message': f'❌ 无法识别的专利号格式：{patent_no}\n\n'
                       f'请检查格式，支持格式示例：\n'
                       f'• US12345678B2（美国专利）\n'
                       f'• CN202310123456.X（中国专利）\n'
                       f'• EP12345678（欧洲专利）\n'
                       f'• WO2023/123456（PCT申请）\n'
                       f'• JP12345678（日本专利）\n'
                       f'• KR1020230012345（韩国专利）\n'
                       f'• GB1234567（英国专利）\n'
                       f'• DE102023123456（德国专利）\n'
                       f'• FR1234567（法国专利）\n'
                       f'• CH1234567（瑞士专利）',
            'patent_no': patent_no,
        }
    
    result = {
        'patent_no': patent_no,
        'country': identified['country'],
        'country_name': identified['country_name'],
    }
    
    # 1. 先查本地台账
    local_asset = get_asset_by_no(patent_no)
    if local_asset:
        result['local_data'] = local_asset
    
    # 2. 联网查询（可选）- 使用多源重试策略
    query_result = None
    if auto_query:
        query_result = query_patent_with_retry(patent_no, identified['country'])
    
    if query_result and not query_result.get('error'):
        result['query_result'] = query_result
    elif query_result and query_result.get('error'):
        result['query_error'] = query_result['error']
    
    # 3. 计算年费到期日
    fee_dates = _calc_fee_deadlines(result)
    result['fee_info'] = fee_dates
    
    return result


def _calc_fee_deadlines(result: Dict) -> Dict[str, Any]:
    """根据已有信息计算年费截止日"""
    country = result.get('country', 'CN')
    today = datetime.now()
    
    fee_info = {
        'risk_level': '⚪',
        'risk_text': '信息不足',
        'remaining_days': None,
        'next_fee_date': None,
        'estimated_amount': None,
    }
    
    # 优先使用台账中记录的下次年费到期日
    next_fee_date_str = None
    if result.get('local_data', {}).get('next_fee_date'):
        next_fee_date_str = result['local_data']['next_fee_date']
    
    # 其次使用查询结果推算
    if not next_fee_date_str and result.get('query_result'):
        qr = result['query_result']
        grant_date = qr.get('grant_date') or qr.get('patent_date')
        if grant_date:
            # 简单推算：授权日周年
            grant_dt = datetime.strptime(grant_date[:10], '%Y-%m-%d')
            next_due = grant_dt.replace(year=today.year)
            if next_due < today:
                next_due = next_due.replace(year=today.year + 1)
            next_fee_date_str = next_due.strftime('%Y-%m-%d')
    
    if next_fee_date_str:
        try:
            due_date = datetime.strptime(next_fee_date_str, '%Y-%m-%d')
            remaining = (due_date - today).days
            
            risk_icon, risk_text = get_risk_level(remaining)
            
            fee_info = {
                'risk_level': risk_icon,
                'risk_text': risk_text,
                'remaining_days': max(remaining, 0),
                'next_fee_date': next_fee_date_str,
                'overdue_days': -remaining if remaining < 0 else 0,
            }
            
            # 估算年费
            if country == 'CN' and result.get('local_data', {}).get('filing_date'):
                fd = result['local_data']['filing_date']
                ptype = result['local_data'].get('sub_type', 'invention')
                year_count, _ = calc_cn_fee_year(fd)
                amount = calc_cn_fee(ptype, year_count)
                fee_info['estimated_amount'] = f'约¥{amount:.0f}/年'
                fee_info['patent_year'] = f'第{year_count}年'
                
                # 计算滞纳金（如果已过期）
                if remaining < 0:
                    surcharge = calc_surcharge('CN', -remaining, amount)
                    fee_info['surcharge'] = surcharge
            
            elif country == 'US' and result.get('local_data', {}).get('grant_date'):
                gd = result['local_data']['grant_date']
                deadlines = calc_us_maintenance_fee(result['patent_no'], gd)
                fee_info['us_maintenance'] = deadlines
                
            elif country == 'EP' and result.get('local_data', {}).get('filing_date'):
                ep_fees = calc_ep_fees(result['local_data']['filing_date'])
                fee_info['ep_country_fees'] = ep_fees
                
        except ValueError:
            pass
    
    return fee_info


# ============================================================
# 格式化输出
# ============================================================

def format_monitor_result(patent_no: str, result: Dict) -> str:
    """格式化单条监控结果为可读文本"""
    if result.get('error'):
        return result['message']
    
    lines = []
    lines.append(f"📋 专利年费监控报告")
    lines.append(f"{'─' * 40}")
    lines.append(f"专利号：{patent_no}")
    lines.append(f"所属国家：{result.get('country_name', '未知')}")
    
    # 专利名称
    title = None
    if result.get('local_data', {}).get('title'):
        title = result['local_data']['title']
    elif result.get('query_result', {}).get('title'):
        title = result['query_result']['title']
    if title:
        lines.append(f"专利名称：{title}")
    
    # 法律状态
    status = None
    if result.get('local_data', {}).get('status'):
        status = result['local_data']['status']
    elif result.get('query_result', {}).get('status'):
        status = result['query_result']['status']
    if status:
        lines.append(f"法律状态：{status}")
    
    # 申请日/授权日
    filing_date = None
    if result.get('local_data', {}).get('filing_date'):
        filing_date = result['local_data']['filing_date']
    elif result.get('query_result', {}).get('filing_date'):
        filing_date = result['query_result']['filing_date']
    if filing_date:
        lines.append(f"申请日：{filing_date}")
    
    grant_date = None
    if result.get('local_data', {}).get('grant_date'):
        grant_date = result['local_data']['grant_date']
    elif result.get('query_result', {}).get('grant_date'):
        grant_date = result['query_result']['grant_date']
    if grant_date:
        lines.append(f"授权日：{grant_date}")
    
    # 年费信息
    fee_info = result.get('fee_info', {})
    if fee_info.get('next_fee_date'):
        lines.append(f"{'─' * 40}")
        lines.append(f"💰 年费信息")
        lines.append(f"下次年费到期日：{fee_info['next_fee_date']}")
        remaining = fee_info.get('remaining_days')
        if remaining is not None:
            lines.append(f"剩余天数：{remaining}天")
        lines.append(f"风险等级：{fee_info.get('risk_level', '')} {fee_info.get('risk_text', '')}")
        
        overdue = fee_info.get('overdue_days', 0)
        if overdue > 0:
            lines.append(f"⚠️ 已逾期{overdue}天！请尽快缴费，可能产生滞纳金")
            # 显示滞纳金信息
            surcharge = fee_info.get('surcharge')
            if surcharge:
                lines.append(f"📊 滞纳金信息：{surcharge.get('message', '')}")
        
        amount = fee_info.get('estimated_amount')
        if amount:
            lines.append(f"预估费用：{amount}")
        
        patent_year = fee_info.get('patent_year')
        if patent_year:
            lines.append(f"当前年度：{patent_year}")
    
    # 美国维护费明细
    us_maintenance = fee_info.get('us_maintenance', [])
    if us_maintenance:
        lines.append(f"{'─' * 40}")
        lines.append(f"🇺🇸 美国专利维护费明细")
        for m in us_maintenance:
            lines.append(f"  • 第{m['due_year']}年：{m['due_date']}到期")
            lines.append(f"    费用：${m['amount']}（{m['entity_size']}实体）")
            lines.append(f"    宽限至：{m['grace_period_end']}")
    
    # 欧洲生效国年费
    ep_country_fees = fee_info.get('ep_country_fees', [])
    if ep_country_fees:
        lines.append(f"{'─' * 40}")
        lines.append(f"🇪🇺 欧洲生效国年费明细")
        for ef in ep_country_fees:
            lines.append(f"  • {ef['country_name']}：€{ef['fee_eur']}/年（约¥{ef['fee_approx_cny']}）")
    
    # 数据源
    if result.get('query_result'):
        lines.append(f"{'─' * 40}")
        lines.append(f"📡 数据来源：{result['query_result'].get('source', '网络查询')}")
    elif result.get('local_data'):
        lines.append(f"{'─' * 40}")
        lines.append(f"📡 数据来源：本地台账")
    
    # 操作建议
    if result.get('query_error'):
        lines.append(f"")
        lines.append(f"⚠️ 联网查询异常：{result['query_error']}")
        lines.append(f"建议手动核验或补充日期信息")
    
    lines.append(f"")
    lines.append(f"💡 提示：输入「添加到台账」可将此专利加入IP资产清单")
    lines.append(f"💡 提示：输入「查看台账」可查看所有IP资产")
    lines.append(f"💡 提示：输入「生成日历提醒」可生成iCalendar日历提醒")
    lines.append(f"💡 提示：输入「查看通知」可查看推送通知列表")
    
    return '\n'.join(lines)


def format_assets_summary() -> str:
    """格式化资产总览"""
    summary = get_assets_summary()
    
    lines = []
    lines.append(f"📊 IP资产台账总览")
    lines.append(f"{'─' * 40}")
    lines.append(f"总计：{summary['total']}项")
    lines.append(f"├─ 专利：{summary['patents']}项")
    lines.append(f"├─ 商标：{summary['trademarks']}项")
    lines.append(f"└─ 软著：{summary['copyrights']}项")
    
    lines.append(f"")
    if summary['by_country']:
        lines.append(f"🌍 按国家分布：")
        for country, count in sorted(summary['by_country'].items()):
            lines.append(f"  • {COUNTRY_NAMES.get(country, country)}：{count}项")
    
    lines.append(f"")
    
    # 年费到期风险
    lines.append(f"⚠️ 年费到期风险：")
    if summary['due_soon'] > 0:
        lines.append(f"  🔴 即将到期（30天内）：{summary['due_soon']}项")
    if summary['due_warning'] > 0:
        lines.append(f"  🟡 近期预警（90天内）：{summary['due_warning']}项")
    if summary['safe'] > 0:
        lines.append(f"  🟢 正常（90天以上）：{summary['safe']}项")
    
    if summary['total'] > 0:
        lines.append(f"")
        lines.append(f"💡 输入「查看详情 序号」可查看具体资产信息")
        lines.append(f"💡 输入「导出台账」可导出CSV文件")
        lines.append(f"💡 输入「查看通知」可查看推送通知")
    else:
        lines.append(f"暂无IP资产数据")
        lines.append(f"💡 输入「添加专利 XXXXXX」或「导入CSV」开始管理")
    
    return '\n'.join(lines)


def format_asset_detail(asset: Dict) -> str:
    """格式化单个资产详情"""
    lines = []
    
    type_icons = {'patent': '📜', 'trademark': '🏷️', 'copyright': '📝'}
    type_names = {'patent': '专利', 'trademark': '商标', 'copyright': '软著'}
    icon = type_icons.get(asset.get('type', 'patent'), '📄')
    
    lines.append(f"{icon} IP资产详情")
    lines.append(f"{'─' * 40}")
    lines.append(f"编号：{asset.get('ip_no', '')}")
    lines.append(f"名称：{asset.get('title', '未命名')}")
    lines.append(f"类型：{type_names.get(asset.get('type', ''), asset.get('type', ''))}")
    lines.append(f"国家：{COUNTRY_NAMES.get(asset.get('country', ''), asset.get('country', ''))}")
    
    if asset.get('filing_date'):
        lines.append(f"申请日：{asset['filing_date']}")
    if asset.get('grant_date'):
        lines.append(f"授权日：{asset['grant_date']}")
    if asset.get('status'):
        lines.append(f"法律状态：{asset['status']}")
    
    # 年费到期
    if asset.get('next_fee_date'):
        remaining = calc_remaining_days(asset['next_fee_date'])
        risk_icon, risk_text = get_risk_level(remaining)
        lines.append(f"")
        lines.append(f"💰 年费：到期日 {asset['next_fee_date']} | "
                     f"剩余 {remaining}天 | {risk_icon} {risk_text}")
    
    if asset.get('owner'):
        lines.append(f"权利人：{asset['owner']}")
    if asset.get('notes'):
        lines.append(f"备注：{asset['notes']}")
    
    lines.append(f"")
    lines.append(f"🆔 资产ID：{asset.get('id', '')}")
    lines.append(f"💡 输入「更新资产 {asset.get('id', '')} [字段=值]」可修改")
    lines.append(f"💡 输入「删除资产 {asset.get('id', '')}」可移除")
    lines.append(f"💡 输入「生成日历提醒」可导出iCalendar日历提醒文件")
    
    return '\n'.join(lines)


# ============================================================
# 主入口
# ============================================================

def search_patent(patent_no: str) -> str:
    """
    查询并监控单个专利的年费状态（对外接口）
    
    Args:
        patent_no: 专利号，如 US12345678B2、CN202310123456.X
    
    Returns:
        格式化的监控报告
    """
    result = monitor_patent_fee(patent_no, auto_query=True)
    return format_monitor_result(patent_no, result)


def add_asset_cli(text: str) -> str:
    """
    通过自然语言添加IP资产
    
    Args:
        text: 如 "添加专利 US12345678B2 名称为一种新方法"
    """
    # 尝试从文本中提取信息
    ip_no_match = re.search(r'[A-Z]{2,3}[\d.]+[A-Z0-9]*', text.upper())
    if not ip_no_match:
        return "❌ 未识别到有效的专利/商标编号，请提供编号"
    
    ip_no = ip_no_match.group()
    
    # 识别类型
    asset_type = 'patent'
    if '商标' in text:
        asset_type = 'trademark'
    elif '软著' in text:
        asset_type = 'copyright'
    
    # 提取名称
    title = ''
    title_match = re.search(r'(?:名称|标题|名为)[：:]\s*(.+)', text)
    if title_match:
        title = title_match.group(1).strip()
    
    asset = add_asset({
        'ip_no': ip_no,
        'title': title,
        'type': asset_type,
    })
    
    return f"✅ 已添加{ip_no}到台账（ID: {asset['id']}）"


def import_csv_cli(csv_text: str) -> str:
    """
    从CSV文本批量导入
    
    Args:
        csv_text: CSV格式的文本内容
    """
    success, errors = import_csv(csv_text)
    msg = f"✅ 导入完成：成功{success}条"
    if errors:
        msg += f"，{len(errors)}条失败"
        for err in errors[:5]:
            msg += f"\n  • {err}"
        if len(errors) > 5:
            msg += f"\n  ...还有{len(errors)-5}条错误"
    return msg


def show_summary() -> str:
    """显示IP资产总览"""
    return format_assets_summary()


def show_detail(asset_id: int) -> str:
    """显示单个资产详情"""
    assets = load_assets()
    for asset in assets:
        if asset.get('id') == asset_id:
            return format_asset_detail(asset)
    return f"❌ 未找到ID为{asset_id}的资产"


def export_csv_cli() -> str:
    """导出CSV，文件名包含时间戳"""
    csv_content = export_assets_csv()
    if csv_content.startswith("暂无"):
        return csv_content
    
    # 保存到文件，文件名包含时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(os.path.dirname(__file__), f"ip_assets_export_{timestamp}.csv")
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(csv_content)
    
    return f"✅ 台账已导出到：{output_path}"


def delete_asset_cli(asset_id: int) -> str:
    """删除资产"""
    if delete_asset(asset_id):
        return f"✅ 已删除资产ID {asset_id}"
    return f"❌ 未找到ID为{asset_id}的资产"


def calendar_reminder_cli(patent_no: str) -> str:
    """生成日历提醒"""
    result = monitor_patent_fee(patent_no, auto_query=False)
    if result.get('error'):
        return result['message']
    
    title = '未命名'
    if result.get('local_data', {}).get('title'):
        title = result['local_data']['title']
    elif result.get('query_result', {}).get('title'):
        title = result['query_result']['title']
    
    fee_date = result.get('fee_info', {}).get('next_fee_date')
    if not fee_date:
        return f"❌ {patent_no}缺少到期日信息，无法生成日历提醒"
    
    amount = result.get('fee_info', {}).get('estimated_amount', '')
    
    reminder = generate_calendar_reminder(patent_no, title, fee_date, amount)
    return f"✅ 日历提醒已生成：{reminder['file_path']}\n💡 可导入到Google Calendar、Apple Calendar等"


def show_notifications_cli() -> str:
    """显示推送通知列表"""
    notifications = generate_push_notifications()
    
    if not notifications:
        return "暂无待处理通知"
    
    lines = []
    lines.append(f"📬 专利年费推送通知 ({len(notifications)}条)")
    lines.append(f"{'─' * 40}")
    
    for n in notifications:
        lines.append(f"{n['message']}")
        lines.append(f"   → {n['action_required']}")
        lines.append(f"")
    
    return '\n'.join(lines)


def show_due_soon_cli(days: int = 30) -> str:
    """显示即将到期的专利"""
    due_soon = get_due_soon_summary(days)
    
    if not due_soon:
        return f"✅ 未来{days}天内没有即将到期的专利"
    
    lines = []
    lines.append(f"⏰ 未来{days}天内到期的专利 ({len(due_soon)}件)")
    lines.append(f"{'─' * 40}")
    
    for d in due_soon:
        lines.append(f"{d['risk_icon']} {d['ip_no']} - {d['title']}")
        lines.append(f"   到期日：{d['due_date']}（剩余{d['remaining_days']}天）")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    # 简单测试
    print("专利年费监控工具 v2.0")
    print("=" * 50)
    
    # 测试专利号识别（含瑞士）
    test_nos = ['US12345678B2', 'CN202310123456.X', 'EP12345678', 'WO2023/123456', 'CH1234567']
    for no in test_nos:
        result = identify_patent(no)
        print(f"{no} → {result}")