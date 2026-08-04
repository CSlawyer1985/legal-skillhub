"""合同审查（民法典）— 五维风险评估 + 12类缺失条款检测"""
import sys
import os
import json
from datetime import datetime

VERSION = "1.3.0"

# ── 民法典核心法条索引 ──────────────────────────────────
CIVIL_CODE = {
    "违约金过高": {"article": 585, "text": "约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。"},
    "不可抗力": {"article": 590, "text": "当事人一方因不可抗力不能履行合同的，根据不可抗力的影响，部分或者全部免除责任。"},
    "合同解除": {"article": 563, "text": "有下列情形之一的，当事人可以解除合同：(一)因不可抗力致使不能实现合同目的；(二)在履行期限届满前，当事人一方明确表示或者以自己的行为表明不履行主要债务..."},
    "格式条款": {"article": 496, "text": "格式条款是当事人为了重复使用而预先拟定，并在订立合同时未与对方协商的条款。"},
    "违约责任": {"article": 577, "text": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。"},
    "保密义务": {"article": 501, "text": "当事人在订立合同过程中知悉的商业秘密或者其他应当保密的信息，无论合同是否成立，不得泄露或者不正当地使用。"},
    "合同生效": {"article": 502, "text": "依法成立的合同，自成立时生效，但是法律另有规定或者当事人另有约定的除外。"},
    "损害赔偿": {"article": 584, "text": "当事人一方不履行合同义务或者履行合同义务不符合约定，造成对方损失的，损失赔偿额应当相当于因违约所造成的损失。"},
    "定金": {"article": 587, "text": "给付定金的一方不履行债务或者履行债务不符合约定，致使不能实现合同目的的，无权请求返还定金；收受定金的一方不履行债务的，应当双倍返还定金。"},
    "合同解释": {"article": 142, "text": "有相对人的意思表示的解释，应当按照所使用的词句，结合相关条款、行为的性质和目的、习惯以及诚信原则，确定意思表示的含义。"},
    "公平原则": {"article": 6, "text": "民事主体从事民事活动，应当遵循公平原则，合理确定各方的权利和义务。"},
    "诚实信用": {"article": 7, "text": "民事主体从事民事活动，应当遵循诚信原则，秉持诚实，恪守承诺。"},
    "诉讼时效": {"article": 188, "text": "向人民法院请求保护民事权利的诉讼时效期间为三年。法律另有规定的，依照其规定。"},
    "合同无效": {"article": 153, "text": "违反法律、行政法规的强制性规定的民事法律行为无效。但是，该强制性规定不导致该民事法律行为无效的除外。"},
    "格式条款无效": {"article": 497, "text": "提供格式条款的一方不合理地免除或者减轻其责任、加重对方责任、限制对方主要权利的，该格式条款无效。"},
    "显失公平": {"article": 151, "text": "一方利用对方处于危困状态、缺乏判断能力等情形，致使民事法律行为在成立时显失公平的，受损害方有权请求人民法院或者仲裁机构予以撤销。"},
    "情势变更": {"article": 533, "text": "合同成立后，合同的基础条件发生了当事人在订立合同时无法预见的、不属于商业风险的重大变化，继续履行合同对于当事人一方明显不公平的，受不利影响的当事人可以与对方重新协商；在合理期限内协商不成的，可请求法院或仲裁机构变更或解除合同。"},
    "借款利率": {"article": 680, "text": "禁止高利放贷，借款的利率不得违反国家有关规定。借款合同对支付利息没有约定的，视为没有利息。"},
    "合同形式": {"article": 469, "text": "当事人订立合同，可以采用书面形式、口头形式或者其他形式。书面形式是合同书、信件、电报、电传、传真等可以有形地表现所载内容的形式。"},
    "电子合同": {"article": 491, "text": "当事人一方通过互联网等信息网络发布的商品或者服务信息符合要约条件的，对方选择该商品或者服务并提交订单成功时合同成立，但是当事人另有约定的除外。"},
    "租赁期限": {"article": 705, "text": "租赁期限不得超过二十年。超过二十年的，超过部分无效。租赁期限届满，当事人可以续订租赁合同；但是，约定的租赁期限自续订之日起不得超过二十年。"},
    "保证合同": {"article": 681, "text": "保证合同是为保障债权的实现，保证人和债权人约定，当债务人不履行到期债务或者发生当事人约定的情形时，保证人履行债务或者承担责任的合同。"},
    "诚信履行": {"article": 509, "text": "当事人应当按照约定全面履行自己的义务。当事人应当遵循诚信原则，根据合同的性质、目的和交易习惯履行通知、协助、保密等义务。"},
    "买卖检验期": {"article": 620, "text": "买受人收到标的物时应当在约定的检验期限内检验。没有约定检验期限的，应当及时检验。"},
}

MISSING_CLAUSE_CATEGORIES = [
    {"id": 1, "name": "违约金条款", "importance": 5, "article": "584-588", "desc": "约定违约责任及违约金计算方式，违约金不宜超过实际损失的30%"},
    {"id": 2, "name": "争议解决方式", "importance": 5, "article": "民诉33-35", "desc": "约定仲裁或诉讼、管辖法院/仲裁机构"},
    {"id": 3, "name": "不可抗力条款", "importance": 4, "article": "180,590", "desc": "明确不可抗力范围、通知义务、后果分担"},
    {"id": 4, "name": "保密条款", "importance": 4, "article": "501", "desc": "约定保密信息范围、保密期限、违约责任"},
    {"id": 5, "name": "知识产权归属", "importance": 4, "article": "123", "desc": "明确知识产权归属、使用许可范围"},
    {"id": 6, "name": "竞业限制", "importance": 3, "article": "868-869", "desc": "竞业限制范围、期限、补偿金"},
    {"id": 7, "name": "送达地址确认", "importance": 4, "article": "137", "desc": "双方确认法律文书送达地址，变更通知义务"},
    {"id": 8, "name": "合同解除条件", "importance": 5, "article": "562-566", "desc": "约定解除条件、解除后果、结算清理条款"},
    {"id": 9, "name": "违约责任", "importance": 5, "article": "577-594", "desc": "全面约定违约情形、责任承担方式"},
    {"id": 10, "name": "通知方式", "importance": 3, "article": "137-139", "desc": "约定通知方式（书面/邮件/系统消息）、送达时间"},
    {"id": 11, "name": "生效条件/期限", "importance": 4, "article": "158-160", "desc": "明确合同生效条件或期限"},
    {"id": 12, "name": "附件清单", "importance": 3, "article": "实务", "desc": "列明合同附件，确保附件与正文一致"},
]

RISK_TYPES = [
    {"level": "high", "label": "高风险", "color": "[HIGH]", "desc": "违反强制性规定、权利义务严重失衡、核心条款缺失"},
    {"level": "medium", "label": "中风险", "color": "[MED]", "desc": "表述模糊、非核心条款缺失、存在可争议空间"},
    {"level": "low", "label": "低风险", "color": "[LOW]", "desc": "格式瑕疵、非实质性建议"},
]

RISK_DIMENSIONS = [
    {"name": "合法性", "weight": 0.40, "desc": "条款是否符合民法典强制性规定"},
    {"name": "公平性", "weight": 0.20, "desc": "双方权利义务是否对等"},
    {"name": "完整性", "weight": 0.20, "desc": "必要条款是否齐全"},
    {"name": "明确性", "weight": 0.10, "desc": "条款表述是否清晰无歧义"},
    {"name": "可执行性", "weight": 0.10, "desc": "条款是否具备实际可操作"},
]

# 模糊表述词库
VAGUE_WORDS = ["合理期限", "及时", "尽快", "适当", "相关", "必要时", "酌情", "视情况", "一般", "大概", "左右"]

# 格式条款/显失公平标志词
UNFAIR_WORDS = ["最终解释权", "恕不", "概不", "一律", "必须", "无条件", "不得异议", "自行承担一切"]

# 日利率型违约金关键词（覆盖多种写法，单条/批量两处共用）
DAILY_WORDS = ["每日", "每天", "按日", "日加收", "每逾期一日", "逾期一日", "每逾期", "按日加收"]

# 押金罚没标志词（押金约定不退/没收，属加重对方责任）
DEPOSIT_FORFEIT_WORDS = ["不予退还", "不予返还", "不得退还", "扣除全部", "全部扣除", "没收", "不退还", "不退"]

# ── 政府采购/招投标专项法条（命中关键词才触发，不主动要求政府条款）──
GOV_LAW = {
    "转包禁止": {"article": "政府采购法第48条",
                 "text": "经采购人同意，中标、成交供应商可依法采取分包方式履行合同。政府采购合同不得转包。"},
    "履约保证金上限": {"article": "政府采购法实施条例第48条",
                 "text": "采购文件要求提交履约保证金的，数额不得超过政府采购合同金额的10%。"},
    "质保金惯例": {"article": "国办发〔2016〕49号",
                 "text": "质量保证金比例由双方约定，工程领域通常不超过结算价款的3%。"},
    "进口产品审批": {"article": "政府采购进口产品管理办法",
                 "text": "采购进口产品须经专家论证并报设区的市以上人民政府财政部门核准。"},
    "验收书": {"article": "政府采购法实施条例第45条",
                 "text": "采购人应按合同规定的技术、服务、安全标准组织验收，并出具验收书。"},
}
GOV_BAN_WORDS = ["不得转包", "禁止转包", "不得分包", "禁止分包", "不得违法分包", "不得转包或", "不得转包，"]


def detect_gov_risks(text: str):
    """政府采购/招投标专项风险检测（仅命中关键词时触发）"""
    import re
    fs = []
    # 转包/分包：未明确禁止则提示补充（宽松识别"不得/禁止+转包/分包"语义，兼容"不得将本项目转包"等插入写法）
    if "转包" in text or "分包" in text:
        banned = (
            ("不得" in text and "转包" in text)
            or ("禁止" in text and "转包" in text)
            or (("不得" in text or "禁止" in text) and "分包" in text)
            or any(w in text for w in GOV_BAN_WORDS)
        )
        if not banned:
            fs.append({
                "level": "medium", "type": "转包/分包未明确禁止",
                "law": GOV_LAW["转包禁止"],
                "advice": "政府采购合同不得转包，分包须采购人同意。建议明确「乙方不得转包；分包须经甲方书面同意」（政府采购法第48条）"
            })
    # 履约保证金超上限（提取保证金邻近的百分比）
    if "履约保证金" in text or "履约担保" in text:
        m = re.search(r'(?:履约保证金|履约担保)[^\d]{0,15}(\d+(?:\.\d+)?)\s*%', text) \
            or re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:履约保证金|履约担保)', text)
        if m and float(m.group(1)) > 10:
            fs.append({
                "level": "high", "type": "履约保证金超10%上限",
                "law": GOV_LAW["履约保证金上限"],
                "advice": f"履约保证金{float(m.group(1))}%超过10%法定上限（实施条例第48条）"
            })
    # 质保金偏高（提取质保金邻近的百分比，支持"X%作为质量保证金"与"质量保证金X%"两种）
    if "质保金" in text or "质量保证金" in text:
        m = re.search(r'(?:质量保证金|质保金)[^\d]{0,15}(\d+(?:\.\d+)?)\s*%', text) \
            or re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:作为|为)?\s*(?:质量保证金|质保金)', text)
        if m and float(m.group(1)) > 3:
            fs.append({
                "level": "medium", "type": "质保金偏高",
                "law": GOV_LAW["质保金惯例"],
                "advice": f"质保金{float(m.group(1))}%高于工程领域3%惯例，建议核实约定依据（国办发〔2016〕49号）"
            })
    # 进口产品
    if "进口" in text:
        fs.append({
            "level": "medium", "type": "进口产品审批",
            "law": GOV_LAW["进口产品审批"],
            "advice": "涉及进口产品须完成专家论证及财政核准，建议核实审批手续（进口产品管理办法）"
        })
    return fs


def cmd_gov_review(input_file: str = None):
    """政府采购/招投标专项审查"""
    if not input_file:
        print("[参数错误] 缺少 --input 参数（政府采购合同文件路径）。")
        print("用法: python main.py gov-review --input 政府采购合同.txt")
        return
    if not os.path.exists(input_file):
        print(f"[参数错误] --input 文件不存在: {input_file}")
        print("请检查路径（当前仅支持 txt/docx/pdf）。")
        return
    content, clauses = cmd_parse_contract(input_file)
    if not content or content.startswith("[需要") or content.startswith("[PDF"):
        print("  ⚠ 无法解析文本内容（缺少 python-docx/PyPDF2，或文件为扫描件）")
        return
    print(f"[政府采购专项审查] 文件: {input_file}")
    print(f"[解析] 共 {len(clauses)} 个条款\n")
    any_hit = False
    for cl in clauses:
        fs = detect_gov_risks(cl)
        if fs:
            any_hit = True
            print(f"[条款] {cl[:80]}...")
            for f in fs:
                level_label = next((r["color"] for r in RISK_TYPES if r["level"] == f["level"]), "")
                print(f"  {level_label} [{f['type']}] {f['advice']}")
                if f.get('law'):
                    print(f"    {f['law']['article']}: {f['law']['text'][:80]}...")
    if not any_hit:
        print("  [未发现政府采购专项风险条款]（转包/分包/质保金/履约保证金/进口产品等均未命中）")


# ── 参数解析 ──────────────────────────────────────────────
def parse_args(argv):
    kwargs = {}
    positional = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--"):
            key = arg[2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                kwargs[key] = argv[i + 1]
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            positional.append(arg)
            i += 1
    return kwargs, positional


# ── 合同文本分析 ──────────────────────────────────────────
def analyze_contract(content: str):
    """基于合同内容实际分析五维评分（非硬编码）"""
    content_lower = content.lower()

    # 合法性：检测违反强制规定的标志
    legality_deductions = 0
    for kw in UNFAIR_WORDS:
        if kw in content:
            legality_deductions += 1
    # 违约金比例检测（含日利率型：每日X% = 年化X*365%）
    import re
    pct_matches = re.findall(r'(\d+)\s*%', content)
    for pct_str in pct_matches:
        pct_val = int(pct_str)
        # 常规比例 > 30% 触发
        if pct_val > 30 and any(w in content for w in ["违约金", "罚款", "赔偿"]):
            legality_deductions += 2
        # 日利率型：每日X%且X>=0.5 或 有"每日/日"关键词
        elif any(w in content for w in DAILY_WORDS):
            if pct_val >= 1 and any(w in content for w in ["违约金", "罚款", "赔偿", "滞纳金", "加收"]):
                legality_deductions += 3  # 日利率>1%极其危险
    legality = max(40, 100 - legality_deductions * 5)

    # 公平性：检测不平等表述数量
    unfair_count = sum(1 for kw in UNFAIR_WORDS if kw in content)
    # 押金罚没：押金约定不退/没收，属加重对方责任
    if "押金" in content and any(kw in content for kw in DEPOSIT_FORFEIT_WORDS):
        unfair_count += 2
    # 政府专项风险
    for g in detect_gov_risks(content):
        if g["level"] == "high":
            legality_deductions += 2
        else:
            unfair_count += 1
    fairness = max(40, 85 - unfair_count * 8)

    # 完整性：检测12类缺失条款命中数
    clause_keywords = {
        "违约金条款": ["违约金", "罚款", "赔偿金"],
        "争议解决方式": ["仲裁", "诉讼", "管辖", "争议解决"],
        "不可抗力条款": ["不可抗力", "force majeure"],
        "保密条款": ["保密", "商业秘密", "机密"],
        "知识产权归属": ["知识产权", "著作权", "专利", "商标"],
        "合同解除条件": ["解除", "终止"],
        "违约责任": ["违约", "赔偿损失", "继续履行"],
        "生效条件/期限": ["生效", "有效期", "期限"],
        "送达地址确认": ["送达", "地址"],
    }
    found_categories = 0
    for name, kws in clause_keywords.items():
        if any(kw in content for kw in kws):
            found_categories += 1
    completeness = min(100, 40 + found_categories * 6)

    # 明确性：检测模糊表述数量
    vague_count = sum(1 for w in VAGUE_WORDS if w in content)
    clarity = max(30, 90 - vague_count * 5)

    # 可执行性：检测是否有关键操作细节
    executable_keywords = ["日内", "个工作", "交付", "验收", "付款", "盖章", "签字", "账户", "账号", "开户行"]
    executable_hits = sum(1 for kw in executable_keywords if kw in content)
    executability = min(100, 50 + executable_hits * 5)

    return {
        "合法性": legality,
        "公平性": fairness,
        "完整性": completeness,
        "明确性": clarity,
        "可执行性": executability,
    }


# ── 命令实现 ──────────────────────────────────────────────

def cmd_parse_contract(input_file: str):
    """解析合同文件"""
    if not input_file:
        print("[错误] 缺少 --input 参数")
        print("用法: python main.py parse-contract --input contract.docx")
        return None, []

    print(f"[解析] 文件: {input_file}")

    if not os.path.exists(input_file):
        print(f"[错误] 文件不存在: {input_file}")
        return None, []

    ext = os.path.splitext(input_file)[1].lower()
    try:
        if ext == ".txt":
            with open(input_file, "r", encoding="utf-8") as f:
                content = f.read()
        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(input_file)
                content = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except ImportError:
                print("[提示] 需要安装 python-docx: pip install python-docx")
                content = "[需要 python-docx 解析]"
        elif ext == ".pdf":
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(input_file)
                parts = [ (p.extract_text() or "") for p in reader.pages ]
                content = "\n".join(parts)
                if not content.strip():
                    print("[提示] PDF 文本层为空，可能为扫描件，需 OCR 才能解析")
                    content = "[PDF 为扫描件，需 OCR]"
            except ImportError:
                print("[提示] PDF 解析需要 PyPDF2: pip install PyPDF2")
                content = "[需要 PyPDF2 解析]"
            except Exception as e:
                print(f"[错误] PDF 读取失败: {e}")
                content = "[PDF 解析失败]"
        else:
            print(f"[错误] 不支持的格式: {ext}（支持 txt/docx/pdf）")
            return None, []
    except Exception as e:
        print(f"[错误] 读取文件失败: {e}")
        return None, []

    lines = [l.strip() for l in content.split("\n") if l.strip()]
    print(f"[解析] 共 {len(lines)} 行有效内容")

    # 分条款
    clause_starts = ("第", "一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、", "九、", "十、",
                     "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.")
    clauses = []
    current = ""
    for line in lines:
        if any(line.startswith(s) for s in clause_starts):
            if current:
                clauses.append(current.strip())
            current = line
        else:
            current += " " + line
    if current:
        clauses.append(current.strip())
    print(f"[解析] 识别 {len(clauses)} 个条款")
    return content, clauses


def cmd_review_clause(clause: str):
    """审查单条条款"""
    if not clause:
        print("[参数错误] 缺少 --clause 参数（要审查的条款内容）。")
        print("用法: python main.py review-clause --clause \"违约金为合同总额的50%\"")
        print("提示: 条款内容请用引号（英文\"或中文\"）整体包裹，否则空格会被当成多个参数。")
        return []

    print(f"[审查] 条款: {clause[:80]}...")
    findings = []

    # 违约金过高检测
    if any(kw in clause for kw in ["违约金", "罚款", "赔偿", "滞纳金", "加收"]):
        import re
        pct = re.search(r'(\d+)\s*%', clause)
        multiple = re.search(r'(\d+)\s*倍', clause)
        has_daily = any(w in clause for w in DAILY_WORDS)
        if pct and int(pct.group(1)) > 30:
            findings.append({
                "level": "high",
                "type": "违约金过高",
                "law": CIVIL_CODE["违约金过高"],
                "advice": f"违约金约定为{pct.group(1)}%，超过实际损失30%的上限（民法典第585条），建议调整至合理范围"
            })
        elif pct and has_daily and int(pct.group(1)) >= 1:
            findings.append({
                "level": "high",
                "type": "违约金过高（日利率型）",
                "law": CIVIL_CODE["违约金过高"],
                "advice": f"每日{pct.group(1)}%的违约金年化高达{int(pct.group(1))*365}%，严重过高（民法典第585条），法院大概率不予支持"
            })
        elif multiple:
            findings.append({
                "level": "high",
                "type": "违约金过高",
                "law": CIVIL_CODE["违约金过高"],
                "advice": f"违约金以倍数计算，可能被认定为过高。建议改为具体金额或不超过实际损失的30%"
            })

    # 格式条款/显失公平检测
    for kw in UNFAIR_WORDS:
        if kw in clause:
            findings.append({
                "level": "medium",
                "type": "格式条款/显失公平",
                "law": CIVIL_CODE["格式条款"],
                "advice": f"「{kw}」可能被认定为格式条款或显失公平（民法典第496条），建议修改为对等表述"
            })
            break

    # 模糊表述检测
    for w in VAGUE_WORDS:
        if w in clause:
            findings.append({
                "level": "medium",
                "type": "表述模糊",
                "law": CIVIL_CODE["合同解释"],
                "advice": f"「{w}」表述模糊（民法典第142条），建议明确具体时限/标准/范围"
            })
            break

    # 定金超额检测
    if "定金" in clause:
        import re
        pct = re.search(r'(\d+)\s*%', clause)
        if pct and int(pct.group(1)) > 20:
            findings.append({
                "level": "high",
                "type": "定金超额",
                "law": CIVIL_CODE["定金"],
                "advice": f"定金比例{pct.group(1)}%超过法定的20%上限（民法典第587条），超出部分不产生定金效力"
            })

    # 押金罚没检测
    if "押金" in clause and any(kw in clause for kw in DEPOSIT_FORFEIT_WORDS):
        findings.append({
            "level": "medium",
            "type": "押金罚没风险",
            "law": CIVIL_CODE["格式条款无效"],
            "advice": f"「押金不予退还/没收」可能被认定为不合理加重对方责任、显失公平的格式条款（民法典第497条），押金应依约在租期届满且无违约时返还"
        })

    # 政府采购专项检测
    for g in detect_gov_risks(clause):
        findings.append(g)

    if not findings:
        findings.append({"level": "low", "type": "无明显问题", "law": None, "advice": "当前表述无明显法律风险"})

    for f in findings:
        level_label = next((r["color"] for r in RISK_TYPES if r["level"] == f["level"]), "")
        print(f"  {level_label} [{f['type']}] {f['advice']}")
        if f.get('law'):
            art = f['law'].get('article')
            head = f"民法典第{art}条" if isinstance(art, int) else str(art)
            print(f"    {head}: {f['law']['text'][:80]}...")

    return findings


def cmd_risk_assess(input_file: str = None):
    """五维风险评估"""
    print("=" * 50)
    print("  五维风险评估")
    print("=" * 50)

    scores = {}
    if input_file:
        if not os.path.exists(input_file):
            print(f"[参数错误] --input 文件不存在: {input_file}")
            print("请检查路径；仅支持 txt/docx/pdf。未提供 --input 则使用默认示例评分。")
            return 0
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                content = f.read()
            scores = analyze_contract(content)
            print("  [基于合同内容实际分析]")
        except Exception as e:
            print(f"  [文件读取失败: {e}，使用默认评分]")

    if not scores:
        scores = {dim["name"]: 75 for dim in RISK_DIMENSIONS}

    total_score = 0
    for dim in RISK_DIMENSIONS:
        score = scores.get(dim["name"], 75)
        weighted = score * dim['weight']
        total_score += weighted
        bar = "#" * int(score / 10) + "." * (10 - int(score / 10))
        print(f"  {dim['name']:6s}  [{bar}] {score}分 (权重{dim['weight']*100:.0f}%) — {dim['desc']}")

    print(f"\n  综合得分: {total_score:.0f}/100")
    if total_score >= 85:
        print("  评级: 良好 OK")
    elif total_score >= 65:
        print("  评级: 需修订 [!]")
    else:
        print("  评级: 高风险 FAIL")

    if not input_file:
        print("\n[提示] 提供 --input 参数可基于实际合同内容分析评分")
    return total_score


def cmd_missing_check(input_file: str = None):
    """检测12类常见缺失条款"""
    print("=" * 50)
    print("  缺失条款检测（12类）")
    print("=" * 50)

    # 如果提供了文件，基于内容检测
    content = ""
    if input_file:
        if not os.path.exists(input_file):
            print(f"[参数错误] --input 文件不存在: {input_file}")
            print("请检查路径；未提供 --input 则仅展示 12 类缺失条款清单。")
            return
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"  [文件读取失败: {e}]")

    clause_keywords = {
        "违约金条款": ["违约金", "罚款", "赔偿金"],
        "争议解决方式": ["仲裁", "诉讼", "管辖", "争议解决"],
        "不可抗力条款": ["不可抗力", "force majeure"],
        "保密条款": ["保密", "商业秘密", "机密"],
        "知识产权归属": ["知识产权", "著作权", "专利", "商标"],
        "竞业限制": ["竞业限制", "竞业禁止", "不竞争"],
        "送达地址确认": ["送达", "地址"],
        "合同解除条件": ["解除", "终止"],
        "违约责任": ["违约", "赔偿损失", "继续履行"],
        "通知方式": ["通知", "告知", "书面通知"],
        "生效条件/期限": ["生效", "有效期", "期限"],
        "附件清单": ["附件", "附录", "附表"],
    }

    missing_count = 0
    found_count = 0
    for cat in MISSING_CLAUSE_CATEGORIES:
        stars = "*" * cat['importance'] + "." * (5 - cat['importance'])
        kws = clause_keywords.get(cat['name'], [])
        is_found = content and any(kw in content for kw in kws)
        if is_found:
            status = "OK 已包含"
            found_count += 1
        else:
            status = "MISSING 缺失" if content else "可能存在"
            if content:
                missing_count += 1
        print(f"  [{status}] {cat['name']:8s} {stars} 民法典第{cat['article']}条")
        print(f"         {cat['desc']}")

    if content:
        print(f"\n  结果: {found_count}/12 已包含, {missing_count}/12 缺失")
        if missing_count > 4:
            print("  [HIGH] 缺失条款较多，建议补充")
        elif missing_count > 0:
            print("  [MED] 存在缺失条款，建议补充")
        else:
            print("  OK 条款完整")
    else:
        print(f"\n[提示] 提供 --input 参数可基于实际合同检测缺失条款")


def cmd_generate_report(input_file: str, output_file: str = "review-report.md"):
    """生成审查报告"""
    if not input_file:
        print("[参数错误] 缺少 --input 参数（要审查的合同文件路径）。")
        print("用法: python main.py generate-report --input 合同.docx --output 报告.md")
        print("提示: 路径含空格请用引号包裹，如 --input \"D:/合同/采购合同.docx\"")
        return None
    if not os.path.exists(input_file):
        print(f"[参数错误] --input 文件不存在: {input_file}")
        print("请检查路径与文件名是否正确（当前仅支持 txt/docx/pdf）。")
        return None

    print(f"[生成报告] 输入: {input_file} -> 输出: {output_file}")

    # 先分析合同
    content = None
    clauses = []
    scores = {}
    if os.path.exists(input_file):
        content, clauses = cmd_parse_contract(input_file)
        if content:
            scores = analyze_contract(content)

    if not scores:
        scores = {dim["name"]: 75 for dim in RISK_DIMENSIONS}

    total = sum(scores.get(d["name"], 75) * d["weight"] for d in RISK_DIMENSIONS)

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    report = f"""# 合同审查报告

**审查日期**: {now}
**审查依据**: 《中华人民共和国民法典》(2021年1月1日施行)
**审查工具**: AI合同审查 v{VERSION}

---

## 一、合同基本信息
- 文件: {input_file}
- 审查模式: 五维风险评估 + 12类缺失条款检测
- 条款数: {len(clauses) if clauses else 'N/A'}

## 二、五维风险评估

| 维度 | 评分 | 权重 | 加权 |
|------|------|------|------|
"""
    for dim in RISK_DIMENSIONS:
        s = scores.get(dim["name"], 75)
        report += f"| {dim['name']} | {s} | {dim['weight']*100:.0f}% | {s*dim['weight']:.1f} |\n"

    level = "良好 OK" if total >= 85 else ("需修订" if total >= 65 else "高风险")
    report += f"\n**综合得分**: {total:.0f}/100 — {level}\n"

    report += """
## 三、风险项汇总

### 风险检测结果
请使用 `review-clause` 逐条审查具体条款，或使用 `risk-assess` 查看详细评分。

## 四、综合建议

1. 逐条审查合同中的违约金、定金条款
2. 检查是否存在模糊表述（如"合理期限""及时""尽快"等）
3. 使用 `missing-check` 检测缺失的必要条款
4. 重大合同建议咨询执业律师

---

*本报告由AI自动生成，仅供参考，不构成正式法律意见。重大合同建议咨询执业律师。*
"""
    try:
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[完成] 报告已保存: {output_file} ({len(report)} 字符)")
    except Exception as e:
        print(f"[错误] 保存报告失败: {e}")
        return None

    return output_file


def cmd_batch_review(directory: str, output_dir: str = None):
    """批量审查多个合同文件（真正逐份审查，而非仅列清单）"""
    if not directory or not directory.strip():
        print("[参数错误] 缺少 --dir 参数（待审查合同所在的文件夹路径）。")
        print("用法: python main.py batch-review --dir ./contracts/")
        return
    directory = directory.strip()

    if not os.path.exists(directory):
        print(f"[参数错误] 目录不存在: {directory}")
        return
    if not os.path.isdir(directory):
        print(f"[参数错误] 不是目录: {directory}（--dir 需传入文件夹路径，含空格请用引号包裹）")
        return

    files = [f for f in os.listdir(directory) if f.lower().endswith((".txt", ".docx", ".pdf"))]
    if not files:
        print("[提示] 未发现支持的合同文件（txt/docx/pdf）")
        return

    print(f"[批量审查] 目录: {directory}")
    print(f"[扫描] 发现 {len(files)} 个合同文件，开始逐份审查...\n")

    out_dir = output_dir or os.path.join(directory, "review_reports")
    os.makedirs(out_dir, exist_ok=True)

    summary = []
    for idx, f in enumerate(files, 1):
        path = os.path.join(directory, f)
        print("=" * 62)
        print(f"[{idx}/{len(files)}] 审查: {f}")
        print("=" * 62)
        content, clauses = cmd_parse_contract(path)
        if not content or content.startswith("[需要") or content.startswith("[PDF"):
            print("  ⚠ 无法解析文本内容（缺少 python-docx/PyPDF2，或文件为扫描件），跳过实质审查")
            summary.append((f, "未解析", "—", "—", "—"))
            continue

        scores = analyze_contract(content)
        total = sum(scores.get(d["name"], 75) * d["weight"] for d in RISK_DIMENSIONS)
        level = "良好" if total >= 85 else ("需修订" if total >= 65 else "高风险")

        # 逐条关键条款审查，统计非低风险项数量
        risk_hits = 0
        for cl in clauses:
            trigger = ["违约金", "罚款", "赔偿", "定金", "每日",
                       "合理期限", "及时", "尽快", "适当", "最终解释权",
                       "一律", "概不", "酌情", "视情况", "押金",
                       "转包", "分包", "质保金", "质量保证金", "履约保证金", "进口"] + DAILY_WORDS
            if any(kw in cl for kw in trigger):
                fs = cmd_review_clause(cl)
                risk_hits += len([x for x in fs if x["level"] != "low"])

        # 缺失条款计数
        clause_keywords = {
            "违约金条款": ["违约金", "罚款", "赔偿金"],
            "争议解决方式": ["仲裁", "诉讼", "管辖", "争议解决"],
            "不可抗力条款": ["不可抗力", "force majeure"],
            "保密条款": ["保密", "商业秘密", "机密"],
            "知识产权归属": ["知识产权", "著作权", "专利", "商标"],
            "竞业限制": ["竞业限制", "竞业禁止", "不竞争"],
            "送达地址确认": ["送达", "地址"],
            "合同解除条件": ["解除", "终止"],
            "违约责任": ["违约", "赔偿损失", "继续履行"],
            "通知方式": ["通知", "告知", "书面通知"],
            "生效条件/期限": ["生效", "有效期", "期限"],
            "附件清单": ["附件", "附录", "附表"],
        }
        missing = sum(1 for cat in MISSING_CLAUSE_CATEGORIES
                      if not any(kw in content for kw in clause_keywords.get(cat["name"], [])))

        # 调用既有报告生成（输出到 out_dir）
        safe = f.replace(".", "_")
        rep_path = os.path.join(out_dir, f"{safe}_review.md")
        cmd_generate_report(path, rep_path)

        print(f"  → 综合 {total:.0f}/100 [{level}]  缺失条款 {missing}/12  风险项(非低) {risk_hits}")
        summary.append((f, f"{total:.0f}", level, str(missing), str(risk_hits)))

    print("\n" + "=" * 62)
    print("  批量审查汇总")
    print("=" * 62)
    print(f"{'文件':<26s} {'得分':<8s} {'评级':<8s} {'缺失':<6s} {'风险'}")
    for f, sc, lv, ms, rh in summary:
        print(f"{f[:24]:<26s} {sc:<8s} {lv:<8s} {ms:<6s} {rh}")
    print(f"\n各合同详细报告已保存至: {out_dir}")


def cmd_law_lookup(article: str = None):
    """查询民法典法条"""
    if article:
        found = False
        for key, law in CIVIL_CODE.items():
            if str(law['article']) == article or str(law['article']).startswith(article):
                print(f"[民法典第{law['article']}条] {key}")
                print(f"  {law['text']}")
                found = True
        if not found:
            print(f"[未找到] 第{article}条，当前收录 {len(CIVIL_CODE)} 条核心法条")
            print("可用: " + ", ".join(f"第{str(l['article'])}条" for l in CIVIL_CODE.values()))
    else:
        print(f"已收录民法典核心法条（{len(CIVIL_CODE)} 条）:")
        for key, law in sorted(CIVIL_CODE.items(), key=lambda x: x[1]['article']):
            print(f"  第{str(law['article']):>4s}条 — {key}")


def cmd_list_risk_types():
    """列出风险类型"""
    for rt in RISK_TYPES:
        print(f"{rt['color']} {rt['label']}: {rt['desc']}")


def cmd_list_missing_categories():
    """列出缺失条款类别"""
    print(f"{'#':<4s} {'类别':<12s} {'重要性':<10s} {'依据':<12s}")
    print("-" * 45)
    for cat in MISSING_CLAUSE_CATEGORIES:
        stars = "*" * cat['importance']
        print(f"{cat['id']:<4d} {cat['name']:<10s} {stars:<8s} 第{cat['article']}条")


def show_help():
    print(f"合同审查（民法典）v{VERSION}")
    print("Usage: python main.py <command> [args]")
    print()
    print("Commands:")
    print("  parse-contract --input <file>      解析合同文件")
    print("  review-clause --clause <text>      审查单条条款")
    print("  risk-assess [--input <file>]       五维风险评估")
    print("  missing-check [--input <file>]     缺失条款检测")
    print("  generate-report --input --output   生成审查报告")
    print("  batch-review --dir <dir>           批量审查")
    print("  law-lookup [--article <num>]       查询民法典法条")
    print("  list-risk-types                    列出风险类型")
    print("  list-missing-categories            列出缺失条款类别")
    print("  help, -h, --help                   Show this help")
    print("  version, -v, --version             Show version")


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    cmd = sys.argv[1]
    raw_args = sys.argv[2:]

    if cmd in ("help", "-h", "--help"):
        show_help()
        return
    if cmd in ("version", "-v", "--version"):
        print(f"合同审查（民法典）v{VERSION}")
        return

    kwargs, positional = parse_args(raw_args)

    try:
        if cmd == "parse-contract":
            cmd_parse_contract(kwargs.get("input", ""))
        elif cmd == "review-clause":
            clause = kwargs.get("clause") or " ".join(positional)
            cmd_review_clause(clause)
        elif cmd == "risk-assess":
            cmd_risk_assess(kwargs.get("input"))
        elif cmd == "missing-check":
            cmd_missing_check(kwargs.get("input"))
        elif cmd == "generate-report":
            cmd_generate_report(kwargs.get("input"), kwargs.get("output", "review-report.md"))
        elif cmd == "batch-review":
            cmd_batch_review(kwargs.get("dir", ""))
        elif cmd == "law-lookup":
            cmd_law_lookup(kwargs.get("article"))
        elif cmd == "gov-review":
            cmd_gov_review(kwargs.get("input"))
        elif cmd == "list-risk-types":
            cmd_list_risk_types()
        elif cmd == "list-missing-categories":
            cmd_list_missing_categories()
        else:
            print(f"未知命令: {cmd}")
            print("运行 python main.py help 查看帮助")
            sys.exit(1)
    except Exception as e:
        print(f"[异常] {e}")
        print(f"[提示] 运行 python main.py help 查看帮助")
        sys.exit(1)


if __name__ == "__main__":
    main()
