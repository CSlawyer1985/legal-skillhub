#!/usr/bin/env python3
"""
法律术语词典清洗脚本
从香港DOJ双语词典CSV中提取适用于中国大陆法律的通用术语。

清洗策略（温和）：
- 保留：英汉民商事法律词汇、刑事诉讼词汇集、中国大陆法律来源
- 保留：香港条例中不包含香港独有机构/概念的通用术语
- 过滤：纯报告/咨询文件来源
- 过滤：包含香港独有机构/概念的条目
- 去重 + 文本清理 + 领域分类

用法：
    python clean_glossary.py <输入CSV路径> [输出CSV路径]
"""

import csv
import re
import sys
import os
from collections import Counter, defaultdict

# ========== 配置 ==========

# 必须保留的来源（完整匹配）
KEEP_SOURCES_EXACT = [
    '英汉民商事法律词汇',
    '刑事诉讼词汇集',
]

# 必须保留的来源（包含匹配）
KEEP_SOURCES_CONTAINS = [
    '中华人民共和国',
    '中国法律',
    '基本法',  # 基本法中涉及中央与地方关系的术语
]

# 必须过滤的来源（包含匹配）
FILTER_SOURCES_CONTAINS = [
    '报告书',
    '咨询文件',
    '谘询文件',
    '报告书',
    '检讨',
    'Designing Hong Kong',
    '终院民事上诉',
    '终院刑事上诉',
    '高院民事上诉',
    '高院刑事上诉',
]

# 香港独有机构关键词（出现在中文词语中则过滤）
HK_INSTITUTIONS = [
    '立法会', '行政长官', '律政司', '终审法院', '区域法院',
    '裁判法院', '枢密院', '港督', '英皇', '行政会议',
    '立法局', '临时立法会', '市政局', '区议会', '高等法院',
    '上诉法庭', '原讼法庭', '原讼法院', '上诉法院',
    '劳资审裁处', '土地审裁处', '小额钱债审裁处',
    '淫亵物品审裁处', '死因裁判法庭', '少年法庭',
    '竞争事务审裁处', '市场失当行为审裁处',
    '证券及期货事务上诉审裁处', '行政上诉委员会',
    '上诉委员团', '城市规划委员会', '乡议局',
    '区议会', '街坊会', '乡事委员会',
    '东华三院', '保良局', '香港赛马会',
    '香港金融管理局', '香港交易所', '证监会',
    '强制性公积金', '积金局', '医管局',
]

# 香港独有人员/角色关键词
HK_ROLES = [
    '大律师', '事务律师', '太平绅士', '特首',
    '政务司', '财政司', '律政专员', '法律援助署',
    '破产管理署', '公司注册处', '知识产权署',
    '土地注册处', '民政事务总署', '民政事务专员',
    '申诉专员', '廉政公署', '廉政专员',
    '个人资料私隐专员', '平等机会委员会',
    '截取通讯及监察事务专员',
]

# 香港独有法律概念/术语（出现在中文词语中）
HK_CONCEPTS = [
    '坎宁安', '考德威尔',  # 普通法特有案例概念
    '居籍',  # domicile - HK concept
    '呈请', '禀报', '誓章', '誓词',  # HK procedural
    '遗产承办', '遗嘱认证', '遗产管理书',  # HK probate
    '待决法律程序', '诉讼待决',  # lis pendens
    '新界', '原居民',  # New Territories specific
    '乡事', '街坊',  # HK local
    '英属', '殖民地',  # Colonial terms
    '海外司法管辖', '指定国家',  # Mostly HK-UK
    '经证监会', '经保险业监督',  # HK regulators
]

# 需要过滤的模板/占位符模式（中文词语中包含这些）
TEMPLATE_PATTERNS = [
    '......', '……',  # 模板占位符
    '所衍生', '所附带', '所附属',  # 连接词模式
    '所雇用', '所聘用', '所须',
    '（香港）', '（Hong Kong）', '(香港)', '(Hong Kong)',
    '（HK）', '(HK)',
]

# 来源列为 "第XX章，第XX条" 但中文为通用短语的 → 保留
# 仅当来源为报告/咨询文件且中文长度为短语时才过滤

# ========== 文本清理 ==========

def clean_text(text):
    """清理中文/英文文本中的编辑标记"""
    if not text:
        return text

    # 移除 ※比较 ... ※参看 ... 等编辑标记（保留前面的正文）
    text = re.sub(r'\s*※比较\s*.+$', '', text)
    text = re.sub(r'\s*※参看\s*.+$', '', text)
    text = re.sub(r'\s*※\s*.+$', '', text)
    text = re.sub(r'\s*☛参看\s*.+$', '', text)

    # 移除注脚标记
    text = re.sub(r'\s*註腳\s*\d+', '', text)
    text = re.sub(r'\s*注脚\s*\d+', '', text)
    text = re.sub(r'\s*\[注\d+\]', '', text)

    # 清理拉丁术语中的双层引号（标准化为单层）
    # parte inaudita [""one side being unheard""] -> parte inaudita ["one side being unheard"]
    text = re.sub(r'\[""(.+?)""\]', r'["\1"]', text)

    # 去除两端多余空格
    text = text.strip()

    # 统一多余空格
    text = re.sub(r'\s{2,}', ' ', text)

    return text


def is_hk_specific(cn_text):
    """判断中文词语是否为香港独有术语或模板占位符"""
    # 检查模板/占位符模式
    for keyword in TEMPLATE_PATTERNS:
        if keyword in cn_text:
            return True, 'Template'

    # 检查香港机构
    for keyword in HK_INSTITUTIONS:
        if keyword in cn_text:
            return True, 'HK-Institution'

    # 检查香港角色
    for keyword in HK_ROLES:
        if keyword in cn_text:
            return True, 'HK-Role'

    # 检查香港独有概念
    for keyword in HK_CONCEPTS:
        if keyword in cn_text:
            return True, 'HK-Concept'

    # 检查是否包含 (香港) 或类似标记
    if re.search(r'[\(（]\s*香港\s*[\)）]', cn_text):
        return True, 'HK-Marker'
    if re.search(r'[\(（]\s*HK\s*[\)）]', cn_text, re.IGNORECASE):
        return True, 'HK-Marker'

    return False, ''


def is_report_source(src):
    """判断来源是否为报告/咨询文件"""
    for keyword in FILTER_SOURCES_CONTAINS:
        if keyword in src:
            return True
    return False


def is_keep_source(src):
    """判断来源是否必须保留"""
    for keyword in KEEP_SOURCES_EXACT:
        if keyword in src:
            return True
    for keyword in KEEP_SOURCES_CONTAINS:
        if keyword in src:
            return True
    return False


# ========== 领域分类 ==========

DOMAIN_KEYWORDS = {
    '民法': [
        '合同', '契约', '侵权', '婚姻', '继承', '物权', '债权',
        '担保', '买卖', '租赁', '赠与', '代理', '委托', '收养',
        '抚养', '赡养', '扶养', '监护', '宣告死亡', '宣告失踪',
        '相邻', '地役', '抵押', '质押', '留置', '定金',
        '不当得利', '无因管理', '缔约过失', '违约责任',
        '人身权', '人格权', '名誉权', '隐私权', '肖像权',
        '财产', '所有权', '共有', '占有', '用途物权',
        '夫妻', '配偶', '子女', '父母', '亲属', '家庭',
        '遗嘱', '遗赠', '遗产', '法定继承', '代位继承',
        '赠与', '买卖', '借款', '租赁', '承揽', '运输',
        'tort', 'contract', 'negligence', 'nuisance', 'defamation',
        'property', 'mortgage', 'lease', 'tenancy', 'easement',
        'marriage', 'divorce', 'succession', 'probate', 'will',
        'trust', 'equity', 'estoppel', 'restitution', 'remedy',
        'damage', 'damages', 'liability', 'duty of care',
        'breach', 'covenant', 'easement', 'lien', 'charge',
    ],
    '刑法': [
        '罪', '刑', '犯', '盗窃', '抢劫', '谋杀', '诈骗', '贪污',
        '贿赂', '刑罚', '监禁', '罚款', '死刑', '无期徒刑',
        '有期徒刑', '拘役', '管制', '剥夺政治权利', '没收财产',
        '自首', '立功', '累犯', '缓刑', '假释', '减刑',
        '正当防卫', '紧急避险', '犯罪', '故意', '过失',
        '共犯', '教唆', '帮助犯', '从犯', '主犯',
        'crime', 'criminal', 'offence', 'penalty', 'sentence',
        'imprisonment', 'fine', 'fraud', 'theft', 'murder',
        'manslaughter', 'assault', 'bribery', 'corruption',
        'conspiracy', 'attempt', 'abet', 'accomplice', 'aiding',
        'guilty', 'innocent', 'conviction', 'acquittal',
        'prosecution', 'defence', 'defendant', 'accused',
        'mens rea', 'actus reus', 'strict liability',
    ],
    '商法': [
        '公司', '商业', '合伙', '破产', '清算', '证券', '票据',
        '保险', '银行', '信托', '知识产权', '商标', '专利',
        '著作权', '版权', '反垄断', '竞争', '消费者',
        '股东', '董事', '董事会', '股权', '股份', '出资',
        '注册', '登记', '营业执照', '公司法', '企业',
        'company', 'corporation', 'bankruptcy', 'insolvency',
        'share', 'shareholder', 'director', 'board',
        'intellectual property', 'patent', 'trademark', 'copyright',
        'insurance', 'banking', 'security', 'bond', 'stock',
        'commercial', 'merchant', 'partnership', 'winding-up',
        'liquidation', 'receiver', 'debenture', 'prospectus',
        'capital', 'dividend', 'merger', 'acquisition',
    ],
    '诉讼法': [
        '诉讼', '上诉', '证据', '证人', '审判', '裁决', '判决',
        '仲裁', '调解', '管辖', '送达', '聆讯', '庭审',
        '起诉', '应诉', '答辩', '反诉', '抗辩', '申诉',
        '再审', '执行', '查封', '扣押', '冻结', '拍卖',
        '原告', '被告', '第三人', '诉讼代理人', '辩护人',
        '举证', '质证', '认证', '司法鉴定', '勘验',
        '法院', '法庭', '法官', '陪审', '审理', '裁定',
        'jurisdiction', 'evidence', 'witness', 'trial', 'appeal',
        'plaintiff', 'defendant', 'judgment', 'decree', 'order',
        'injunction', 'damages', 'remedy', 'procedure',
        'arbitration', 'mediation', 'litigation', 'suit',
        'summons', 'subpoena', 'discovery', 'interrogatory',
        'hearing', 'adjourn', 'dismiss', 'strike out',
        'costs', 'pleading', 'statement', 'affidavit',
    ],
    '宪法行政法': [
        '宪法', '行政', '立法', '选举', '基本法', '人权',
        '公安', '行政处', '行政复议', '行政诉讼', '国家赔偿',
        '立法法', '监督法', '选举法', '组织法', '民族区域',
        '特别行政区', '一国两制', '人民代表大会',
        '政府', '机关', '部门', '公务员', '编制',
        '许可', '审批', '备案', '登记', '行政处罚',
        'constitution', 'constitutional', 'administrative',
        'judicial review', 'human right', 'fundamental right',
        'legislation', 'legislative', 'executive', 'parliament',
        'election', 'sovereignty', 'autonomy', 'regulatory',
        'government', 'minister', 'secretary', 'department',
    ],
    '国际法': [
        '国际', '公约', '条约', '外交', '领事', '引渡',
        '海事', '海洋', '领土', '边界', '难民', '庇护',
        '战争', '武装冲突', '人道主义', '国际法院',
        '国际刑事', ' WTO ', '世界贸易', '联合国',
        'treaty', 'convention', 'international', 'diplomatic',
        'extradition', 'maritime', 'admiralty', 'territorial',
        'refugee', 'asylum', 'sovereign', 'jurisdiction',
        'protocol', 'charter', 'declaration', 'resolution',
        '缔约国', '签署', '批准', '加入', '保留',
    ],
}


def classify_domain(cn_text, en_text):
    """根据中英文关键词进行法律领域分类"""
    combined = (cn_text + ' ' + en_text).lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in combined:
                score += 1
        if score > 0:
            scores[domain] = score

    if not scores:
        return '通用'

    # 返回得分最高的领域
    best = max(scores, key=scores.get)
    # 如果得分太低，标记为通用
    if scores[best] < 2:
        return '通用'
    return best


def classify_type(cn_text, en_text):
    """判断术语类型"""
    # 拉丁术语
    if re.search(r'[a-z]+ [a-z]+ \[".*?"\]', en_text.lower()):
        return '拉丁术语'
    if re.search(r'\b(ipso|ex parte|inter alia|prima facie|stare decisis|res judicata|obiter|ratio|mens rea|actus reus|habeas corpus|certiorari|mandamus|subpoena|duces tecum|sui generis|mutatis mutandis|pro bono|amicus|noscitur|ejusdem|expressio|in rem|in personam|ultra vires|intra vires)\b', en_text.lower()):
        return '拉丁术语'

    # 定义式（很长的短语）
    cn_len = len(cn_text)
    en_len = len(en_text.split())
    if cn_len > 15 or en_len > 8:
        return '短语'

    # 单词
    if cn_len <= 4 and en_len <= 3:
        return '单词'

    return '短语'


# ========== 主流程 ==========

def clean_glossary(input_path, output_path=None):
    """主清洗流程"""
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = base + '_cleaned.csv'

    print(f"读取原始数据: {input_path}")

    # 读取原始数据
    rows = []
    with open(input_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) >= 4:
                rows.append(row)

    total_input = len(rows)
    print(f"  输入条目数: {total_input}")

    # ===== 步骤1：过滤来源 =====
    stats = Counter()
    filtered_rows = []

    for row in rows:
        src = row[3].strip() if len(row) > 3 else ''
        cn = row[1].strip() if len(row) > 1 else ''

        # 跳过报告/咨询文件
        if is_report_source(src):
            stats['filtered:report'] += 1
            continue

        # 跳过香港独有术语
        is_hk, reason = is_hk_specific(cn)
        if is_hk:
            stats[f'filtered:{reason}'] += 1
            continue

        # 如果是HK条例来源且不是必须保留的来源，检查更多
        if not is_keep_source(src):
            # 检查中文是否包含第X章这类引用
            if re.search(r'第\d+[A-Z]*章', cn):
                stats['filtered:ordinance-ref-in-cn'] += 1
                continue

        filtered_rows.append(row)
        stats['kept'] += 1

    print(f"\n  过滤后: {len(filtered_rows)} 条")
    for key, count in stats.most_common():
        if key.startswith('filtered'):
            print(f"    {key}: {count}")

    # ===== 步骤2：文本清理 =====
    cleaned_rows = []
    for row in filtered_rows:
        new_row = [
            clean_text(row[0]) if len(row) > 0 else '',
            clean_text(row[1]) if len(row) > 1 else '',
            clean_text(row[2]) if len(row) > 2 else '',
            row[3].strip() if len(row) > 3 else '',
        ]
        # 清理后如果中文或英文为空，跳过
        if new_row[1] and new_row[2]:
            cleaned_rows.append(new_row)

    print(f"  文本清理后: {len(cleaned_rows)} 条")

    # ===== 步骤3：去重（按 CN+EN 键） =====
    source_priority = {
        '英汉民商事法律词汇': 1,
        '刑事诉讼词汇集': 2,
    }
    # 中国大陆法律来源优先级较高
    def get_source_priority(src):
        for keyword in KEEP_SOURCES_CONTAINS:
            if keyword in src:
                return 1
        for keyword in KEEP_SOURCES_EXACT:
            if keyword in src:
                return source_priority.get(keyword, 3)
        return 4  # HK ordinance etc.

    seen = {}
    deduped = []
    dup_count = 0
    for row in cleaned_rows:
        key = (row[1], row[2])  # (CN, EN)
        src = row[3]
        priority = get_source_priority(src)

        if key not in seen:
            seen[key] = (row, priority)
            deduped.append(row)
        else:
            existing_priority = seen[key][1]
            if priority < existing_priority:
                # 替换为更高优先级的来源
                deduped.remove(seen[key][0])
                seen[key] = (row, priority)
                deduped.append(row)
            dup_count += 1

    print(f"  去重后: {len(deduped)} 条 (移除 {dup_count} 条重复)")
    print(f"  唯一中文词语: {len(set(r[1] for r in deduped))}")

    # ===== 步骤4：领域分类与类型标注 =====
    output_header = ['中文词语', '英文词语', '来源', '领域', '类型']

    final_rows = []
    for row in deduped:
        cn = row[1]
        en = row[2]
        src = row[3]
        domain = classify_domain(cn, en)
        term_type = classify_type(cn, en)
        final_rows.append([cn, en, src, domain, term_type])

    # 统计
    domain_counts = Counter(r[3] for r in final_rows)
    type_counts = Counter(r[4] for r in final_rows)
    print(f"\n  领域分布:")
    for domain, count in domain_counts.most_common():
        print(f"    {domain}: {count} ({100*count/len(final_rows):.1f}%)")
    print(f"\n  类型分布:")
    for t, count in type_counts.most_common():
        print(f"    {t}: {count} ({100*count/len(final_rows):.1f}%)")

    # ===== 步骤5：输出 =====
    # 按中文拼音排序（简单按字符排序）
    final_rows.sort(key=lambda r: r[0])

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(output_header)
        writer.writerows(final_rows)

    print(f"\n清洗完成！输出: {output_path}")
    print(f"  最终条目数: {len(final_rows)}")

    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(input_path):
        print(f"错误: 找不到文件 {input_path}")
        sys.exit(1)

    clean_glossary(input_path, output_path)
