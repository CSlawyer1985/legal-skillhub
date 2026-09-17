#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract.py — 案卷文字抽取 + 字段启发式取值（配置驱动归档引擎的底层工具）

供 archive_case.py / status.py 调用：
  - build_case_index(folder)  -> {相对路径: 文本}
  - extract_field(key, case_index, from_pattern) -> 取值或 None
支持 PDF(pypdf)、扫描件(PaddleOCR/Windows OCR)、WPS .doc(二进制)、.docx。
"""
import os, re, sys, hashlib, io

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(os.path.expanduser('~'), '.workbuddy',
                         'case-archiver', 'cache', 'text')


# ---------- 文本缓存（按 路径+mtime+size 命中，避免重复 OCR） ----------
def _cache_key(path):
    try:
        st = os.stat(path)
    except OSError:
        return None
    raw = '%s|%d|%d' % (os.path.abspath(path), st.st_mtime_ns, st.st_size)
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()


def _cache_get(path):
    k = _cache_key(path)
    if not k:
        return None
    f = os.path.join(CACHE_DIR, k + '.txt')
    if os.path.exists(f):
        try:
            return io.open(f, encoding='utf-8').read()
        except Exception:
            return None
    return None


def _cache_put(path, text):
    k = _cache_key(path)
    if not k or text is None:
        return
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with io.open(os.path.join(CACHE_DIR, k + '.txt'), 'w',
                     encoding='utf-8') as fh:
            fh.write(text)
    except Exception:
        pass


# ---------- OCR 白名单 ----------
# 字段提取只依赖以下几类文书；证据照片、病历、清单等扫描件跑 OCR 既慢又用不上，
# 直接跳过（仍会被原样复制归档）。设环境变量 CASE_ARCHIVER_OCR_ALL=1 可强制全量 OCR。
OCR_WORTH_RE = re.compile(
    r'申请书|起诉状|诉状|答辩状|上诉状|代理词|反诉'
    r'|合同|协议|授权|委托'
    r'|裁决|调解|判决|裁定|决定书'
    r'|发票|收据|收费|票据'
    r'|公函|所函|函件'
    r'|身份证|营业执照|企业信息|工商'
    r'|通知书|传票|受理|立案|举证'
)


def _ocr_worth(path):
    if os.environ.get('CASE_ARCHIVER_OCR_ALL') == '1':
        return True
    return bool(OCR_WORTH_RE.search(os.path.basename(path)))


# ---------- 文字抽取 ----------
def extract_text_from_file(path, use_cache=True):
    if use_cache:
        c = _cache_get(path)
        if c is not None:
            return c
    t = _extract_text_uncached(path)
    # 失败结果不入缓存，下次可重试
    if (use_cache and t and not t.startswith('[OCR失败')
            and not t.startswith('[抽取失败') and not t.startswith('[扫描件-未OCR')):
        _cache_put(path, t)
    return t


def _extract_text_uncached(path):
    ext = path.lower().rsplit('.', 1)[-1]
    try:
        if ext == 'pdf':
            try:
                import pypdf
                r = pypdf.PdfReader(path)
                out = []
                for p in r.pages:
                    t = p.extract_text()
                    if t and t.strip():
                        out.append(t.strip())
                if out:
                    return "\n".join(out)
            except Exception:
                pass
            # 扫描件 -> OCR（仅对字段提取用得上的文书）
            if not _ocr_worth(path):
                return "[扫描件-未OCR]"
            try:
                sys.path.insert(0, HERE)
                import ocr_pdf
                return ocr_pdf.ocr_pdf(path)
            except Exception as e:
                return f"[OCR失败:{e}]"
        elif ext == 'docx':
            from docx import Document
            d = Document(path)
            parts = [p.text for p in d.paragraphs if p.text.strip()]
            for tb in d.tables:
                for row in tb.rows:
                    for c in row.cells:
                        if c.text.strip():
                            parts.append(c.text.strip())
            return "\n".join(parts)
        elif ext == 'doc':
            sys.path.insert(0, HERE)
            import parse_wps_doc
            return parse_wps_doc.extract_text(path)
    except Exception as e:
        return f"[抽取失败:{e}]"
    return ""


def build_case_index(folder):
    """返回 {文件全路径: 文本}，便于按文件名匹配并复制原文件。"""
    idx = {}
    for root, _, files in os.walk(folder):
        for f in files:
            if f.startswith('~$'):
                continue
            p = os.path.join(root, f)
            try:
                idx[p] = extract_text_from_file(p)
            except Exception:
                idx[p] = ""
    return idx


# ---------- 字段取值启发式 ----------
DATE_RE = r'(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)'
CJK_NAME = r'[\u4e00-\u9fa5]{2,15}(?:公司|厂|有限公司|事务所|有限责任公司|股份公司)?'
PLACEHOLDER_NAMES = {'姓名', '（姓名）', '名称', '某某', 'X', 'XX', 'XXX', '×', '—', '-', '（名称）'}


def _year(d):
    m = re.search(r'(\d{4})\s*年', d)
    return int(m.group(1)) if m else 0


def _parse_date(d):
    """把 '2026年3月25日' 解析为可比较的 (年,月,日) 元组；失败返回 None。
    注意：不能对日期字符串做字典序 max（'3月5日' 会大于 '3月25日'）。"""
    m = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', d)
    if not m:
        return None
    try:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except Exception:
        return None


def _first(pat, text, flags=re.S):
    m = re.search(pat, text, flags)
    return m.group(1).strip() if m else None


def _all_dates(text):
    return re.findall(DATE_RE, text)


def _after_context(text, anchor_pat, value_pat, window=220):
    """在 anchor 匹配位置之后 window 字符内找 value_pat。"""
    m = re.search(anchor_pat, text)
    if not m:
        return None
    seg = text[m.end(): m.end() + window]
    return _first(value_pat, seg)


def _案由_from_folder(name):
    """案由在源文件文本中常缺失（扫描件/OCR 抽不到），但案卷文件夹名通常含案由，
    如 '3.韦琼先诉龙腾家具厂工伤事故损害赔偿纠纷案' -> '劳动争议（工伤事故损害赔偿）'。"""
    m = re.sub(r'^\d+\.\s*', '', name)            # 去序号前缀
    if '诉' in m:
        rest = m[m.index('诉') + 1:]              # 被告 + 案由
    else:
        rest = m
    rest = re.sub(r'案$', '', rest)               # 去末尾"案"
    mm = re.search(r'(工伤[一-龥]{0,12}损害赔偿|劳动争议[一-龥]{0,10}|[一-龥]{1,6}(?:纠纷|争议|合同))', rest)
    core = mm.group(1).strip('（）()') if mm else rest.strip('（）()')
    if not core:
        return None
    if '工伤' in core or '劳动' in core:
        return '劳动争议（' + core + '）'
    return core


def _judgment_案由(t):
    """从判决书/调解书/裁决书/决定书中提取明确写明的案由，原样引用（优先级最高）。"""
    # 1) 显式「案由：xxx」
    v = _first(r'案由[:：]\s*([\u4e00-\u9fa5（）()\s，,]{2,30}?)(?:\n|$)', t)
    if v and len(v.strip()) >= 2:
        return v.strip()
    # 2) 「（本案）系/为/是 xxx纠纷」「xxx争议」
    m = re.search(r'(?:本案)?\s*(?:系|为|是)\s*([\u4e00-\u9fa5（）()]{2,20}?(?:纠纷|争议))', t)
    if m:
        return m.group(1).strip('（）() ')
    return None


def _案由_from_provisions(folder_name, combined, items):
    """依《民事案件案由规定》(法〔2020〕346号) 识别纠纷类型，返回对应标准案由。
    仅在判决书/调解书/裁决书未载明案由时作为兜底。按特异性从高到低匹配。"""
    allt = "\n".join(t for _, t in items)
    full = (folder_name or '') + "\n" + combined + "\n" + allt
    # 按特异性从高到低：具体侵权/合同类型优先于泛化劳动子类型与兜底。
    # （注意：交通事故/承揽/买卖/借款/确认劳动关系 必须排在 工伤/劳动报酬/经济补偿/合同 之前，
    #  否则含「劳动报酬」措辞的交通事故案、含「经济补偿」的承揽案会被错误归并。）
    rules = [
        (r'非机动车|机动车|交通事故', '机动车交通事故责任纠纷'),
        (r'确认劳动关系', '请求确认劳动关系纠纷'),
        (r'承揽', '承揽合同纠纷'),
        (r'买卖', '买卖合同纠纷'),
        (r'借款', '借款合同纠纷'),
        (r'工伤', '工伤保险待遇纠纷'),
        (r'追索劳动报酬|拖欠工资|劳动报酬', '追索劳动报酬纠纷'),
        (r'经济补偿|赔偿金', '经济补偿金纠纷'),
        (r'劳动合同', '劳动合同纠纷'),
        (r'劳动争议|劳动仲裁|劳动人事争议', '劳动争议'),
        (r'建设工程', '建设工程合同纠纷'),
        (r'运输', '运输合同纠纷'),
        (r'劳务', '劳务合同纠纷'),
        (r'委托合同|委托代理', '委托合同纠纷'),
        (r'服务合同|服务纠纷', '服务合同纠纷'),
        (r'知识产权|专利|商标|著作权', '知识产权与竞争纠纷'),
        (r'离婚', '离婚纠纷'),
        (r'继承', '继承纠纷'),
        (r'抚养|赡养|扶养', '婚姻家庭纠纷'),
        (r'股东|股权|公司决议|公司解散', '与公司有关的纠纷'),
        (r'物权|相邻|所有权|采光|通行', '物权保护纠纷'),
        (r'健康权|身体权|生命权|人身损害', '生命权、身体权、健康权纠纷'),
        (r'物件|建筑物|脱落|坠落|高空抛物', '物件损害责任纠纷'),
        (r'产品责任|产品质量', '产品责任纠纷'),
        (r'合同|协议', '合同纠纷'),
        (r'侵权', '侵权责任纠纷'),
    ]
    for pat, cause in rules:
        if re.search(pat, full):
            return cause
    return None


def _client_name(items, texts):
    """本所代理的当事人（委托人）：优先从授权委托书/委托合同/委托代理合同取「委托人」
    （这是最可靠的信号，能正确处理「我方代理被告/被申请人」的情形，避免被起诉状里的
    原告/申请人误导）；回退到申请书/起诉状中的申请人/原告/委托人。"""
    for fn, t in items:
        if re.search(r'授权委托书|委托授权书|委托合同|聘请律师合同|委托代理合同', fn):
            v = _first(r'(?:委托人|甲方)[:：]\s*(' + CJK_NAME + r')', t)
            if v:
                return v
    for t in texts:
        v = _first(r'(?:申请人|原告|委托人)[:：]\s*(' + CJK_NAME + r')', t)
        if v:
            return v
    return None


def _apply_key(key, combined, texts, items=None, case_folder_name=None):
    if key == '受托人':
        for t in texts:
            # 兼容「受委托人：\n姓名： 覃龙腾」这类带换行/姓名标签的写法
            v = _first(r'(?:受委托人|受托人)[:：][\s\S]{0,30}?姓名[:：]\s*(' + CJK_NAME + r')', t)
            if v:
                return v
            v = _first(r'(?:受委托人|受托人)[:：]\s*(' + CJK_NAME + r')', t)
            if v:
                return v
        return None
    if key == '委托人':
        return _client_name(items, texts)
    if key == '对方当事人':
        # 对方当事人 = 起诉状/申请书中与「我方当事人」相对的那个主体
        # （兼容反诉/本诉前缀：反诉原告/本诉被告 等；反诉说理里我方常是反诉原告/本诉被告）
        client = _client_name(items, texts)
        parties = []
        for t in texts:
            for label in ('申请人', '原告', '被申请人', '被告', '相对人', '上诉人', '被上诉人'):
                v = _first(r'(?:反诉|本诉)?' + label + r'[:：]\s*(' + CJK_NAME + r')', t)
                if v:
                    parties.append(v)
        seen = set()
        uniq = [p for p in parties if not (p in seen or seen.add(p))]
        return next((p for p in uniq if p != client), None)
    if key == '委托人地址':
        for t in texts:
            v = _after_context(t, r'(?:申请人|委托人)[:：]\s*' + CJK_NAME,
                               r'(?:住址|地址)[:：]\s*([\u4e00-\u9fa50-9\s号栋室层组队]{4,28}?)(?=，|。|身份证|$)')
            if v:
                return v.strip('，, ')
        return None
    if key == '对方当事人地址':
        # 单位当事人多写「住所地/注册地/经营场所」，自然人写「住址/地址」
        addr_pat = (r'(?:住所地|经营场所|注册地址|注册地|住所|住址|地址)[:：]\s*'
                    r'([\u4e00-\u9fa50-9\s号栋室层组队\-]{4,40}?)'
                    r'(?=，|。|,|统一社会信用代码|身份证|法定代表人|联系电话|$)')
        for t in texts:
            v = _after_context(t, r'(?:被申请人|被告|被上诉人)[:：]\s*' + CJK_NAME, addr_pat)
            if v:
                return v.strip('，, ')
        return None
    if key == '处理方式':
        # 审批表「处理方式」：劳动仲裁 / 仲裁 / 二审诉讼 / 一审诉讼 / 执行
        # （一审/二审 优先于 执行，避免案卷里夹了「执行申请书」就把受理程序误判为执行）
        hay = combined + '\n' + (case_folder_name or '')
        for pat, label in (
            (r'劳动人事争议仲裁委员会|劳动仲裁申请书|劳动仲裁', '劳动仲裁'),
            (r'仲裁委员会|仲裁申请书', '仲裁'),
            (r'上诉状|二审', '二审诉讼'),
            (r'起诉状|人民法院|一审法院|立案', '一审诉讼'),
            (r'执行申请书|强制执行', '执行'),
        ):
            if re.search(pat, hay):
                return label
        return None
    if key == '电话':
        for t in texts:
            v = _first(r'(?:电话|手机|联系电话)[:：]\s*([0-9\-]{7,15})', t)
            if v:
                return v
        return None
    if key == '案由':
        # 优先级 1：判决书/调解书/裁决书/决定书中明确写明的案由，原样引用
        for fn, t in items:
            if _match_from('裁决书|调解书|判决书|决定书', fn):
                v = _judgment_案由(t)
                if v:
                    return v
        # 优先级 2：前述文书未载明案由 -> 依《民事案件案由规定》识别纠纷类型填入
        v = _案由_from_provisions(case_folder_name, combined, items)
        if v:
            return v
        # 兜底：文件夹名粗解析（旧启发式）
        if case_folder_name:
            v = _案由_from_folder(case_folder_name)
            if v:
                return v
        return None
    if key == '标的':
        # 优先「合计/总计/共计」后的金额（申请书主张总额）；否则取最大金额
        for t in texts:
            v = _first(r'(?:合计|总计|共计|总额)[:：]?\s*(?:人民币)?\s*([0-9,]+(?:\.[0-9]+)?)\s*元', t)
            if v:
                return v + '元'
        best = None
        for t in texts:
            for m in re.finditer(r'(?:人民币)?\s*([0-9,]{4,}(?:\.[0-9]+)?)\s*元', t):
                try:
                    amt = float(m.group(1).replace(',', ''))
                except Exception:
                    continue
                if best is None or amt > best[0]:
                    best = (amt, m.group(1))
        if best:
            return best[1] + '元'
        return None
    if key == '代理费金额':
        # 发票常缺失（部分归档），兜底查委托合同；免费代理标「免收」
        pools = [texts]
        contract_texts = [t for fn, t in (items or []) if '合同' in fn and ('委托' in fn or '聘请' in fn)]
        if contract_texts:
            pools.append(contract_texts)
        for pool in pools:
            for t in pool:
                # ① 先判「免收」：合同常写「免收律师费用」「零元整」「0 元」
                if re.search(r'(免收|免费|不收|不收取)\s*(律师|代理|服务)?\s*(费|费用)', t):
                    return '免收'
                if re.search(r'(?:律师费|代理费|服务费|律师代理费)[^0-9元]{0,10}(?:人民币)?\s*0+(?:\.0+)?\s*元', t):
                    return '免收'
                if re.search(r'大写[:：]?\s*零元整', t):
                    return '免收'
                # ② 再取具体金额（须 > 0）
                m = re.search(r'(?:律师费|代理费|服务费|律师代理费)[:：]?\s*(?:人民币)?\s*([0-9,]+(?:\.[0-9]+)?)\s*元?', t)
                if m:
                    try:
                        amt = float(m.group(1).replace(',', ''))
                    except Exception:
                        amt = 0
                    if amt > 0:
                        return m.group(1) + '元'
                    return '免收'
        return None
    if key == '案号':
        # 常见写法：
        #   A 仲裁：中劳人仲案字〔2026〕4582号 / 浙余姚劳人仲案（2025）第XXX号（年份在括号，可能无「字」）
        #   B 法院：（2026）浙0212民初1234号（年份在前，可能夹空格）
        # 排除律所内部编号：浙同璟律民字 / （2025）同璟民函 / 浙同璟律仲字 等。
        pats = (
            r'[\u4e00-\u9fa5]{2,12}?\s*仲案\s*[〔\[（(]\s*\d{4}\s*[〕\]）)]\s*第?\s*\d+\s*号',
            r'[\u4e00-\u9fa5]{2,12}字\s*[〔\[（(]\s*\d{4}\s*[〕\]）)]\s*第?\s*\d+\s*号',
            r'[（(]\s*\d{4}\s*[）)]\s*[\u4e00-\u9fa5]{1,8}[\u4e00-\u9fa50-9\s]{0,12}?第?\s*\d+\s*号',
        )
        firm_re = re.compile(r'同璟|律民字|律仲字|民函|委托|律所|所函')
        for t in texts:
            best = None
            for p in pats:
                m = re.search(p, t)
                if m and (best is None or m.start() < best.start()):
                    best = m
            if best:
                cand = re.sub(r'\s+', '', best.group(0))
                if firm_re.search(cand):
                    continue
                return cand
        return None
    if key == '处理机关':
        # 只匹配「地名+审判机关」形态的真实机构名（如 余姚市劳动人事争议仲裁委员会、
        # 上海市徐汇区人民法院、东莞仲裁委员会），自动排除「所在地人民法院」
        # 「被执行人…人民法院」「任何一方均可向…仲裁委员会」等管辖/执行套话
        # （那些前缀不是地名，不会以 市/区/县/省 结尾）。
        pat = (r'(?:[\u4e00-\u9fa5]{1,8}(?:市|区|县|省|自治区)[\u4e00-\u9fa5]*'
                r'(?:劳动人事争议仲裁委员会|仲裁委员会|中级人民法院|人民法院)'
                r'|中国[\u4e00-\u9fa5]{0,10}人民法院)')
        for t in texts:
            m = re.search(pat, t)
            if m:
                return m.group(0)
        return None
    if key == '收案时间':
        # 收案时间 = 委托合同落款日期。仅在「委托合同」类文件内取年份>=2010的
        # 真实最大日期（按 (年,月,日) 比较，而非字符串字典序）。
        contract_items = [(fn, t) for fn, t in items
                          if ('合同' in fn and ('委托' in fn or '聘请' in fn)) or '委托代理合同' in fn]
        pool = contract_items if contract_items else items
        cand = []
        for fn, t in pool:
            for d in _all_dates(t):
                if _year(d) >= 2010:
                    pd = _parse_date(d)
                    if pd:
                        cand.append((pd, d.replace(' ', '')))
        if cand:
            cand.sort(key=lambda x: x[0])
            return cand[-1][1]
        return None
    if key == '裁决日期':
        # 取裁决/调解书内 >=2010 的最新日期；排除当事人出生年份（如 1978）
        best = None
        for t in texts:
            for d in _all_dates(t):
                if _year(d) >= 2010:
                    pd = _parse_date(d)
                    if pd and (best is None or pd > best[0]):
                        best = (pd, d.replace(' ', ''))
        return best[1] if best else None
    if key == '案情简介':
        return _compose_案情简介(combined, texts, case_folder_name)
    return None


# ---------- 案情简介自动生成 ----------

def _pick_section(text, marker, max_chars=300):
    """取判决书/裁决书中标记段落之后的一段文字，截断到句号附近。"""
    M = re.search(marker, text)
    if not M:
        return ''
    tail = text[M.end():].strip()
    # 取到下一个大标题或段落结束
    stop = re.search(r'\n\s*[一二三四五六七八九十]\s*[、．\.]|\n\s*[0-9]+[\.\、]', tail)
    if stop:
        tail = tail[:stop.start()]
    # 清理页码残留（如 "- 2 -"）
    tail = re.sub(r'[\n\r]\s*-\s*\d+\s*-', '', tail)
    tail = re.sub(r'\n\s*-?\d+\s*-?\s*\n', '\n', tail)
    if len(tail) > max_chars:
        cut = tail.rfind('。', 0, max_chars)
        if cut > 50:
            tail = tail[:cut + 1]
        else:
            tail = tail[:max_chars] + '…'
    return tail.strip()


def _compose_案情简介(combined, texts, case_folder_name=None):
    """从案卷文书中提取关键段落，组装案情简介（200-400字）。"""
    # 诉称：匹配「原告/申请人XX向本院/本委提出诉讼/仲裁请求」「诉称」
    诉称 = _pick_section(combined, r'(?:诉讼|仲裁)\s*请求[：:]', max_chars=300)
    if not 诉称:
        诉称 = _pick_section(combined, r'(?:原告|申请人)\s*[（(]?[^）)]{1,30}[）)]?\s*(?:诉|主)?[称张][：:]', max_chars=300)
    
    # 辩称
    辩称 = _pick_section(combined, r'(?:被告|被申请人|被上?诉人)\s*[（(]?[^）)]{1,30}[）)]?\s*(?:辩|答)?[称张][：:]', max_chars=250)
    
    # 查明
    查明 = _pick_section(combined, r'(?:本院|本委)\s*经审理\s*(?:查明|认定|确认)', max_chars=300)
    if not 查明:
        查明 = _pick_section(combined, r'(?:本院认为|本委认为)[：:]', max_chars=250)
    
    # 结果
    结果 = _pick_section(combined, r'(?:判决|裁决|调解)\s*(?:如下|结果)[：:]', max_chars=200)
    if not 结果:
        结果 = _pick_section(combined, r'(?:裁定|决定)\s*如下[：:]', max_chars=200)
    if not 结果:
        # 调解书模式
        结果 = _pick_section(combined, r'(?:调解|和解)\s*(?:协议|方案|条款)[：:]', max_chars=200)
    if not 结果:
        # 仲裁调解书」关于XX纠纷一案」
        m = re.search(r'(?:本委|本院)\s*(?:依法|组成|受理|裁决)[^。]{20,150}?(?:裁决|决定|调解书)[^。]*。', combined)
        if m:
            结果 = m.group()[:200]
    
    # 未提取到足够内容时，退回全卷粗摘要
    if not 诉称 and not 结果:
        # 找不到结构化段落，取出现在最频繁的3个句子
        sents = re.split(r'[。；]', combined)
        key_sents = [s.strip() for s in sents if len(s.strip()) > 20
                     and any(kw in s for kw in ['纠纷', '争议', '请求', '诉', '判', '裁', '决', '认定'])]
        if key_sents:
            return '。'.join(key_sents[:4]) + '。'
        return None
    
    # 组装摘要
    parts = []
    if 诉称:
        parts.append(f"申请人主张：{诉称}")
    if 辩称:
        parts.append(f"被申请人辩称：{辩称}")
    if 查明:
        parts.append(f"审理查明：{查明}")
    if 结果:
        parts.append(f"处理结果：{结果}")
    
    summary = '；'.join(parts) + '。'
    # 控制字数
    if len(summary) > 450:
        # 按比例缩减每部分
        summary = summary[:400].rsplit('。', 1)[0] + '。'
    return summary


def _case_progress(case_index, case_folder_name=None):
    """从案卷文书中提取案件进程时间线，组装为多行字符串。
    事件：委托本所律师 → 提起诉讼/申请仲裁 → 提交证据 → 开庭审理 → 判决/裁决/调解。"""
    events = []  # [(date_str, event_text)]

    def _add_event(date_str, event):
        if date_str:
            events.append((date_str, event))

    def _date_after(text, anchor_re, year_min=2010):
        """在 anchor 之后找日期；返回 YYYY年M月D日 格式字符串。"""
        m = re.search(anchor_re, text)
        if not m:
            return None
        seg = text[m.end():m.end() + 200]
        dm = re.search(DATE_RE, seg)
        if not dm:
            return None
        dstr = dm.group(1).replace(' ', '')
        pd = _parse_date(dstr)
        if pd and pd[0] >= year_min:
            return f"{pd[0]}年{pd[1]}月{pd[2]}日"
        return None

    def _first_date_in(text, year_min=2010):
        """取文本中第一个 >= year_min 的日期。"""
        for d in _all_dates(text):
            pd = _parse_date(d)
            if pd and pd[0] >= year_min:
                return f"{pd[0]}年{pd[1]}月{pd[2]}日"
        return None

    def _last_date_in(text, year_min=2010):
        """取文本中所有日期中最晚的一个（>=year_min）。"""
        best = None
        for d in _all_dates(text):
            pd = _parse_date(d)
            if pd and pd[0] >= year_min:
                if best is None or pd > best[0]:
                    best = (pd, d.replace(' ', ''))
        if best:
            return f"{best[0][0]}年{best[0][1]}月{best[0][2]}日"
        return None

    def _judgment_date(text, year_min=2010):
        """判决/裁决日期：取文档后 1/3 区域内的最晚日期。"""
        # 跳过前 2/3，找后半部分的日期
        cut = len(text) * 2 // 3
        tail = text[cut:]
        d = _last_date_in(tail, year_min)
        if d:
            return d
        return _last_date_in(text, year_min)

    # 收集各文件类型
    委托_files = []   # [(date_str, file_idx)]
    起诉_files = []
    开庭_files = []
    判决_files = []
    证据_files = []

    for fpath, txt in case_index.items():
        bn = os.path.basename(fpath)
        # 1. 委托相关（多种文档都可能）
        if any(kw in bn for kw in ['授权委托书', '委托授权书', '委托代理合同', '聘请律师合同']):
            d = _date_after(txt, r'(?:签|订)字[：:]|签订[：:]|签订日|签字日|日期[：:]', year_min=2010)
            if not d:
                d = _first_date_in(txt)  # 委托取最早日期（先签的）
            if d:
                委托_files.append((d, fpath))
        # 2. 起诉/申请仲裁
        if any(kw in bn for kw in ['起诉状', '申请书', '诉状']) and '反诉' not in bn:
            d = _last_date_in(txt)
            if d:
                起诉_files.append((d, fpath))
        # 3. 反诉
        if '反诉' in bn and ('状' in bn or '书' in bn):
            d = _last_date_in(txt)
            if d:
                起诉_files.append((d, fpath))
        # 4. 开庭
        if any(kw in bn for kw in ['传票', '开庭通知书', '出庭通知']):
            d = _date_after(txt, r'开庭[时间日期]*[：:]|应到时间[：:]|出庭')
            if not d:
                d = _last_date_in(txt)
            if d:
                开庭_files.append((d, fpath))
        # 5. 判决/裁决/调解
        if any(kw in bn for kw in ['判决书', '裁决书', '调解书', '裁定书']):
            d = _judgment_date(txt)
            if d:
                判决_files.append((d, fpath, bn))
        # 6. 提交证据
        if '证据目录' in bn or '证据材料' in bn:
            d = _last_date_in(txt)
            if d:
                证据_files.append((d, fpath))

    # 处理委托：取最早的（最先生效的）
    if 委托_files:
        委托_files.sort(key=lambda x: _parse_date(x[0]) or (9999, 12, 31))
        events.append((委托_files[0][0], '委托本所律师覃龙腾代理'))

    # 处理起诉/仲裁
    for d, fp in 起诉_files:
        bn = os.path.basename(fp)
        if '反诉' in bn:
            event = '我方提起反诉'
        elif '仲裁' in bn or '劳动' in bn and '仲裁' in bn:
            event = '申请劳动仲裁'
        else:
            event = '提起诉讼'
        events.append((d, event))

    # 处理开庭
    for d, fp in 开庭_files:
        events.append((d, '开庭审理'))

    # 处理证据
    for d, fp in 证据_files:
        events.append((d, '提交证据目录及材料'))

    # 处理判决/裁决/调解
    for d, fp, bn in 判决_files:
        if '判决' in bn:
            event = '出具民事判决'
        elif '裁决' in bn:
            event = '出具仲裁裁决'
        elif '调解' in bn:
            event = '出具调解书'
        elif '裁定' in bn:
            event = '出具民事裁定'
        else:
            event = '出具法律文书'
        events.append((d, event))

    # 排序：按日期元组
    def _key(ev):
        pd = _parse_date(ev[0])
        return pd if pd else (0, 0, 0)
    events.sort(key=_key)

    # 去重：同一类型事件只保留最早的（事件前 4 字分类）
    type_first = {}
    uniq = []
    for d, e in events:
        tp = e[:4]  # 事件类型（前 4 字）
        if tp in type_first:
            continue  # 同类型已保留最早的
        type_first[tp] = d
        uniq.append((d, e))

    if not uniq:
        return None
    return '\n'.join(f"{d}，{e}。" for d, e in uniq)


# 这些字段必须来自 from 指定的文书本身；若该文书缺失（部分归档），
# 宁可留空也不要从其它文件里猜（否则会把授权委托书日期当成裁决日期）。
STRICT_FROM_KEYS = {'案号', '裁决日期', '处理结果'}


def _match_from(from_pattern, fname):
    """from 支持正则/竖线备选，如「裁决书|调解书|判决书」；退化为子串匹配。"""
    base = os.path.basename(fname)
    try:
        if re.search(from_pattern, base):
            return True
    except re.error:
        pass
    for alt in from_pattern.replace('*', '').split('|'):
        alt = alt.strip()
        if alt and alt in base:
            return True
    return False


def extract_field(key, case_index, from_pattern=None, case_folder_name=None):
    # 案件进程：需要访问全卷所有文档（不按 from 过滤）
    if key == '案件进程':
        return _case_progress(case_index, case_folder_name)
    chosen = []
    items = []
    for fname, txt in case_index.items():
        items.append((os.path.basename(fname), txt))
        if from_pattern and _match_from(from_pattern, fname):
            chosen.append(txt)
    if not chosen:
        if from_pattern and key in STRICT_FROM_KEYS:
            return None
        chosen = [t for _, t in items]
    combined = "\n".join(chosen)
    result = _apply_key(key, combined, chosen, items, case_folder_name)
    if result and result.strip() in PLACEHOLDER_NAMES:
        result = None
    # from 指定的文书存在但内容取不到（扫描件/损坏件），非强绑定字段退回全卷再试一次
    if result is None and from_pattern and key not in STRICT_FROM_KEYS:
        all_texts = [t for _, t in items]
        if len(all_texts) != len(chosen):
            result = _apply_key(key, "\n".join(all_texts), all_texts, items, case_folder_name)
            if result and result.strip() in PLACEHOLDER_NAMES:
                result = None
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: extract.py <case_folder> [key] [from_pattern]")
        sys.exit(1)
    idx = build_case_index(sys.argv[1])
    if len(sys.argv) >= 3:
        print(extract_field(sys.argv[2], idx, sys.argv[3] if len(sys.argv) > 3 else None))
    else:
        for k, v in idx.items():
            print(f"### {k}\n{v[:300]}\n")
