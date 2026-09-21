#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金杜"前沿观察"文章 —— 文风机械自查（可选工具）。

只检查可以机械判定的**体例与文风**项：标题格式、小标题是否带判断、忌口词、
感叹号、"您"、人称混用、香港声明、脚注编号连续性、裸事实是否缺脚注。

**它不判断法律内容对错。** 文号真伪、条款存否、论证是否成立，一概不知道。
退出码 0 只表示"没命中这些文风规则"。

用法:
    python3 scripts/lint_article.py <稿件路径>
    python3 scripts/lint_article.py --selftest

退出码:
    0  未命中
    1  命中 ERROR
    2  用法错误 / 文件读不到
"""

import re
import sys
import unicodedata

# ── 规则表 ────────────────────────────────────────────────────────────────

ABSOLUTE_WORDS = ["必将", "势必", "一定会", "毫无疑问", "史上最严", "空前", "前所未有",
                  "无疑将", "必然会"]

BANNED_WORDS = ["赋能", "抓手", "打法", "对齐颗粒度", "完美解决", "彻底规避",
                "笔者不揣浅陋", "浅析", "若干思考", "众所周知", "毋庸置疑"]

TOPIC_TITLE_PAT = re.compile(r"(浅析|初探|若干思考|之我见|的思考|简单谈谈)")

# "事件＋后果"句式中逗号才算合法分隔符：后半段须含后果性谓词
CONSEQUENCE_HINTS = ["需", "应", "将", "宜", "面临", "带来", "如何", "怎么", "值得",
                     "务必", "必须", "不得", "受", "迎来", "承压", "生变"]

HK_DECLARATION = '本文对任何提及"香港"或"香港特别行政区"的表述应解释为"中华人民共和国香港特别行政区"'

CN_NUM = "一二三四五六七八九十百千万亿零〇两"

RE_DOC_NUMBER = re.compile(r"〔\d{4}〕第?\s*\d+\s*号|\[\d{4}\]\s*第?\s*\d+\s*号|"
                           r"令第\s*\d+\s*号|第\s*\d+\s*号令|"
                           r"〔[" + CN_NUM + r"]+〕第?[" + CN_NUM + r"\d]+号")
RE_ARTICLE = re.compile(r"第\s*[" + CN_NUM + r"\d]+\s*(条|款|项)")
RE_DATE = re.compile(r"\d{4}\s*年\s*\d{1,2}\s*月|[" + CN_NUM + r"]{2,4}\s*年\s*[" + CN_NUM + r"]{1,3}\s*月")
RE_PERCENT = re.compile(r"\d+(\.\d+)?\s*%|百分之\s*[" + CN_NUM + r"\d]+")
RE_MONEY = re.compile(r"[\d" + CN_NUM + r"][\d,，.\s" + CN_NUM + r"]*\s*(亿|万)?\s*"
                      r"(元|美元|新元|欧元|英镑|日元|港元|新币|人民币)")
RE_CASENO = re.compile(r"（\s*\d{4}\s*）[^）]{1,20}号|案件编号|Case\s+No|No\.\s*\d")
RE_FOOTNOTE = re.compile(r"\[\d+\]|［\d+］|\[待核|［待核")

RE_HEADING_L1 = re.compile(r"^\s*(?:#{1,4}\s*)?([一二三四五六七八九十]+)\s*[、.]\s*(.+?)\s*$")

TOPIC_ONLY_HEADS = ["基本情况", "主要内容", "适用范围", "合规建议", "三个方面",
                    "背景介绍", "相关规定", "问题分析", "总结", "概述", "简要介绍",
                    "几点思考", "有关问题"]

# 不承载分析、不查判断的标题（SKILL.md §5 三处例外）
HEADING_EXEMPT = ["结语", "引言", "前言", "小结", "写在最后", "合规提示清单", "参考资料"]

# 附件区标题（必须整行就是这个标题，才截断正文）
ATTACHMENT_HEADS = ["参考资料", "待核清单", "分类", "注释", "脚注"]

CANNOT_CHECK = [
    "文号、条款号、案号是否真实存在",
    "所引规则是否现行有效",
    "脚注是否真的支持它所依附的命题",
    "体裁专属要求（源流—增量、反推三拍、失效形态等）是否做到位",
    "论证是否成立、判断是否得当",
]

# 扫描范围的诚实交代
NOT_SCANNED = [
    "二级及以下标题的判断性（只扫一级中文数字标题）",
    "标题与表格内的法律主张是否有脚注（C01 只扫正文句子）",
    "导语字数、层级深度、收尾件顺序、分类标签数量",
    "[待核] 是否在文末汇总、参考资料与正文引用是否一一对应",
]


class Report:
    def __init__(self):
        self.items = []
        self.rules_run = 0

    def add(self, level, code, msg, line=None):
        self.items.append([level, code, msg, line])

    @property
    def errors(self):
        return [i for i in self.items if i[0] == "ERROR"]

    def render(self):
        order = {"ERROR": 0, "WARN": 1}
        for level, code, msg, line in sorted(self.items, key=lambda x: (order[x[0]], x[1])):
            loc = f"（第 {line} 行）" if line else ""
            print(f"[{level}] {code} {msg}{loc}")
        if not self.items:
            print(f"文风自查：{rep_rules(self)} 条规则均未命中。")
        print()
        print(f"ERROR {len(self.errors)} 项 / 合计 {len(self.items)} 项")
        print()
        print("以下各项本脚本查不了，需要人来看：")
        for m in CANNOT_CHECK:
            print(f"  - {m}")
        print()
        print("以下项目本脚本未扫描（不代表合规）：")
        for m in NOT_SCANNED:
            print(f"  - {m}")


def rep_rules(rep):
    return rep.rules_run


def is_quoted(sentence, word):
    """词是否落在《》或引号内（引用官方标题/原文时不应误报）。"""
    for pat in [r"《[^》]*》", r"“[^”]*”", r'"[^"]*"', r"「[^」]*」"]:
        for m in re.finditer(pat, sentence):
            if word in m.group(0):
                return True
    return False


def title_two_part(title):
    """标题是否为「钩子＋分隔符＋界定语」。返回 (ok, note)。"""
    # 分隔符清单与 SKILL.md §3 一致（不含单破折号 — 和 ASCII |）
    for sep in ["——", "丨", "：", ":", "？", "?"]:
        if sep in title:
            head, _, tail = title.partition(sep)
            if head.strip() and tail.strip():
                return True, None
    for sep in ["，", ","]:
        if sep in title:
            head, _, tail = title.partition(sep)
            if head.strip() and tail.strip():
                if any(h in tail for h in CONSEQUENCE_HINTS):
                    return True, None
                return False, ("标题用逗号分隔，但后半段未见后果性表述"
                               "——逗号仅在「事件＋后果」句式中作为合法分隔符")
    return False, None


def heading_carries_judgement(head):
    """小标题是否携带判断。加冒号本身不算（SKILL §5）。"""
    core = head
    for sep in ["：", ":", "——", "—", "丨"]:
        if sep in head:
            core = head.split(sep, 1)[1].strip()
            break
    if not core:
        return False
    if any(core.startswith(t) or core == t for t in TOPIC_ONLY_HEADS):
        return False
    if any(head.strip() == t for t in TOPIC_ONLY_HEADS):
        return False
    return core != head or len(head) > 12


def split_body(lines):
    """返回 (正文行号列表, 正文文本)。附件区必须整行即附件标题才截断。"""
    body_idx = []
    for i, ln in enumerate(lines):
        s = ln.strip().lstrip("#*_> ").strip()
        s_nocolon = s.rstrip("：:").strip()
        if s_nocolon in ATTACHMENT_HEADS:
            break
        body_idx.append(i)
    return body_idx, "\n".join(lines[i] for i in body_idx)


def lint(text):
    text = unicodedata.normalize("NFKC", text).replace("“", '"').replace("”", '"')
    lines = text.splitlines()
    rep = Report()
    body_idx, body = split_body(lines)

    # ── 标题 ──────────────────────────────────────────────────────
    rep.rules_run += 3
    title, title_line = "", None
    for i in body_idx:
        s = lines[i].strip()
        if not s:
            continue
        title = s.lstrip("#").strip()
        title_line = i + 1
        break

    if not title:
        rep.add("ERROR", "T01", "未找到标题。")
    else:
        if TOPIC_TITLE_PAT.search(title):
            rep.add("ERROR", "T02", f"标题使用纯话题式措辞：{title}", title_line)
        ok, note = title_two_part(title)
        if not ok:
            rep.add("ERROR", "T03",
                    (note or "标题未见「钩子＋分隔符＋界定语」两段结构") + f"：{title}", title_line)
        for w in ["首次", "全面", "重磅", "史上最严"]:
            if w in title and not is_quoted(title, w):
                rep.add("WARN", "T04", f"标题含「{w}」——正文撑得起来才留。", title_line)

    # ── 一级小标题 ────────────────────────────────────────────────
    rep.rules_run += 1
    for i in body_idx:
        m = RE_HEADING_L1.match(lines[i])
        if not m:
            continue
        head = m.group(2).strip()
        if head in HEADING_EXEMPT or head.startswith("问："):
            continue
        if not heading_carries_judgement(head):
            # 这是黑名单+长度启发式，不是语义判断——由人确认
            rep.add("WARN", "H01",
                    f"疑似纯主题标题（只读标题看不出本节结论）：「{head}」", i + 1)

    # ── 香港声明（只看正文）────────────────────────────────────────
    rep.rules_run += 1
    if "香港" in body and HK_DECLARATION not in text:
        rep.add("ERROR", "HK1",
                "正文出现「香港」，但未见固定的香港表述声明（boilerplate.md，不得改写）。")

    # ── 语体 ──────────────────────────────────────────────────────
    rep.rules_run += 5
    for i in body_idx:
        ln = lines[i]
        for w in ABSOLUTE_WORDS:
            if w in ln and not is_quoted(ln, w):
                # 脚本判断不了"证据是否撑得住"，只能提示，不能断言违规
                rep.add("WARN", "S01",
                        f"疑似绝对语「{w}」——推测监管走向时不用；若正文有依据可保留。", i + 1)
        for w in BANNED_WORDS:
            if w in ln and not is_quoted(ln, w):
                rep.add("ERROR", "S02", f"出现忌口词「{w}」。", i + 1)
        if "！" in ln or "!" in ln:
            rep.add("ERROR", "S03", "出现感叹号。", i + 1)
        if re.search(r"您", ln):
            rep.add("ERROR", "S04", "出现「您」——读者称「企业／机构／相关企业」。", i + 1)

    rep.rules_run += 1
    for sent in re.split(r"[。；\n]", body):
        if re.search(r"(应当|必须).{0,40}为宜", sent):
            rep.add("ERROR", "S05",
                    f"同句混用两档断言强度：{sent.strip()[:40]}…"
                    "  二选一：「应当自……计算」或「我们理解，以……为宜」。")

    # ── 人称 ──────────────────────────────────────────────────────
    rep.rules_run += 1
    # "我们"/"笔者"基本只作第一人称用，直接数；引文内的不算
    def first_person_lines(word):
        return [ln for ln in body.splitlines() if word in ln and not is_quoted(ln, word)]
    uses_women = bool(first_person_lines("我们"))
    uses_bizhe = bool(first_person_lines("笔者"))
    if uses_women and uses_bizhe:
        rep.add("ERROR", "P01",
                "同文混用「我们」与「笔者」。多作者署名统一「我们」，单作者统一「笔者」。")

    # ── 外部事实是否紧邻脚注 ──────────────────────────────────────
    rep.rules_run += 1
    for i in body_idx:
        ln = lines[i]
        if not ln.strip() or RE_HEADING_L1.match(ln) or ln.strip().startswith("|"):
            continue
        for sentence in re.split(r"[。；]", ln):
            if not sentence.strip():
                continue
            hits = []
            for rx, label in [(RE_DOC_NUMBER, "文号"), (RE_ARTICLE, "条款号"),
                              (RE_PERCENT, "比例"), (RE_MONEY, "金额"),
                              (RE_DATE, "日期"), (RE_CASENO, "案号")]:
                if rx.search(sentence):
                    hits.append(label)
            if hits and not RE_FOOTNOTE.search(sentence):
                rep.add("WARN", "C01",
                        f"含{'／'.join(hits)}但该句未紧邻脚注或 [待核]：{sentence.strip()[:36]}…", i + 1)

    # ── 脚注编号连续性 ────────────────────────────────────────────
    rep.rules_run += 1
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", body)})
    if cited:
        missing = [n for n in range(1, max(cited) + 1) if n not in cited]
        if missing:
            rep.add("WARN", "C02", f"正文脚注编号不连续，缺：{missing}")

    return rep


# ── 回归测试 ──────────────────────────────────────────────────────────────

GOOD = """穿透到底、追索到人——简评《关于健全金融机构治理的实施意见》

2026年7月31日，四部门联合发布《关于健全金融机构治理的实施意见》（金发〔2026〕4号，下称"4号文"）[1]。我们就其制度定位与实质增量进行分析。

一、文件定位：4号文的规格与制度坐标

此前规则均由单一部门分头制定[1]。财政部基于出资人职责参与发文[2]。

二、股东治理：准入、识别、行为、追责的全周期闭环

穿透识别并非首创，《商业银行股权管理暂行办法》（银监会令2018年第1号）第九条已确立[3]。我们理解，4号文的突破在于将其一般化。

三、香港联营机构的衔接：跨境适用仍待明确

对于在香港设有联营机构的集团，4号文未作专门安排，口径有待观察。

结语

真正新设的要求集中在四处。机构宜在配套细则出台前完成差距分析。

*本文对任何提及"香港"或"香港特别行政区"的表述应解释为"中华人民共和国香港特别行政区"。

参考资料
[1] 《关于健全金融机构治理的实施意见》（金发〔2026〕4号）。
[2] 《中华人民共和国预算法》第九条。
[3] 《商业银行股权管理暂行办法》（银监会令2018年第1号）第九条。
"""

# 每例断言：必须出现的 (level, code)；expect_clean=True 表示不得出现任何 ERROR/WARN
CASES = [
    ("正当稿件不误报", GOOD, [], True),
    ("话题式标题", GOOD.replace("穿透到底、追索到人——简评《关于健全金融机构治理的实施意见》",
                            "浅析金融机构治理新规"), [("ERROR", "T02")], False),
    ("标题任意逗号", GOOD.replace("穿透到底、追索到人——简评《关于健全金融机构治理的实施意见》",
                              "人工智能，比较分析"), [("ERROR", "T03")], False),
    ("事件＋后果逗号合法", GOOD.replace("穿透到底、追索到人——简评《关于健全金融机构治理的实施意见》",
                                "FCC新规落地，机器人行业需作好应对准备"), [], True),
    ("空洞冒号标题", GOOD.replace("一、文件定位：4号文的规格与制度坐标", "一、主要内容：三个方面"),
     [("WARN", "H01")], False),
    ("裸小标题", GOOD.replace("一、文件定位：4号文的规格与制度坐标", "一、基本情况"),
     [("WARN", "H01")], False),
    ("结语标题不误报", GOOD, [], True),
    ("缺香港声明", GOOD.replace('*本文对任何提及"香港"或"香港特别行政区"的表述应解释为"中华人民共和国香港特别行政区"。', ""),
     [("ERROR", "HK1")], False),
    ("绝对语降为WARN", GOOD.replace("口径有待观察", "监管一定会扩大执法范围"),
     [("WARN", "S01")], False),
    ("引用中的绝对语不误报",
     GOOD.replace("口径有待观察", '官方文件题为《关于空前加强监管的通知》，口径有待观察'), [], True),
    ("忌口词", GOOD.replace("我们就其制度定位", "本文赋能金融机构，就其制度定位"),
     [("ERROR", "S02")], False),
    ("感叹号", GOOD.replace("口径有待观察。", "口径有待观察！"), [("ERROR", "S03")], False),
    ("出现您", GOOD.replace("对于在香港设有联营机构的集团", "请您注意，在香港设有联营机构的集团"),
     [("ERROR", "S04")], False),
    ("人称混用", GOOD.replace("我们理解，4号文", "笔者认为，4号文"), [("ERROR", "P01")], False),
    ("强度混用", GOOD.replace("口径有待观察", "起算时间应当自公布之日起计算为宜"),
     [("ERROR", "S05")], False),
    ("裸事实缺脚注报WARN", GOOD.replace("此前规则均由单一部门分头制定[1]。",
                                  "罚款比例为营业额的百分之五。"), [("WARN", "C01")], False),
    ("脚注跳号报WARN", GOOD.replace("财政部基于出资人职责参与发文[2]。",
                                "财政部基于出资人职责参与发文[5]。"), [("WARN", "C02")], False),
    ("正文截断藏匿", GOOD.replace("一、文件定位：4号文的规格与制度坐标",
                             "一、参考资料制度的业务影响：值得关注\n\n笔者认为监管必将收紧。"),
     [("ERROR", "P01"), ("WARN", "S01")], False),
]


def selftest():
    passed = failed = 0
    for name, doc, must_have, expect_clean in CASES:
        rep = lint(doc)
        got = {(lv, code) for lv, code, _m, _l in rep.items}
        problems = []
        for pair in must_have:
            if pair not in got:
                problems.append(f"缺少 {pair[0]}/{pair[1]}")
        if expect_clean and got:
            problems.append(f"应无告警但出现了 {sorted(got)}")
        if problems:
            failed += 1
            print(f"  FAIL  {name} —— {'; '.join(problems)}")
            for lv, code, msg, line in rep.items:
                print(f"          [{lv}] {code} {msg}")
        else:
            passed += 1
            print(f"  PASS  {name}")
    print(f"\n回归测试：{passed} 通过 / {failed} 失败 / 共 {len(CASES)} 例")
    return 0 if failed == 0 else 1


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        return selftest()
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"读不到文件：{exc}")
        return 2
    rep = lint(text)
    rep.render()
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
