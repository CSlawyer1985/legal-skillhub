#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PII自动脱敏脚本（pii_sanitizer.py）。

脱敏规则（十类）：
  姓名→“某甲”/“某乙”（覆盖当事人与同案人/家属/证人/被害人/近亲属/委托人等涉案人员）；
  未成年当事人→“未成年当事人”；身份证号→“身份证号[已脱敏]”；
  手机号→“1XX**XX”；住址→“[住址已脱敏]”；银行账号→“**** **** [后四位]”；
  案号→“(20XX)X刑初XX号”；办案人员姓名→“X警官”/“民警X”；
  车牌号→“[车牌已脱敏]”；邮箱→“[邮箱已脱敏]”。
  法律名词保护：证据法定名称（当事人陈述/被害人陈述/证人证言等）、程序动词
  （到案/出庭/作证/翻供等）、状态与文书用语（死亡/重伤/赔偿/谅解/笔录等）经
  防误伤词库与首字黑名单双重保护，不作为姓名脱敏。

脱敏模式（--mode）：
  external（默认）——对外共享场景（对外文书、类案报告、培训材料、对外咨询应答）：
    办案人员姓名双向脱敏（“王建国警官”→“X警官”；“民警王建国”→“民警X”）。
  internal——律所内部办案场景（会见笔录、沟通留痕、案件讨论）：
    办案人员姓名保留原样（内部文书需据以联系承办人），其余九类照常脱敏。

调用方式：
  python scripts/pii_sanitizer.py --text "待脱敏文本" [--mode external|internal]
  python scripts/pii_sanitizer.py --file 输入.txt [--mode external|internal] [--out 输出.txt]

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}，data含脱敏后文本与脱敏项统计（stats）；
  - 退出码：0成功 / 1参数错误 / 2数据文件缺失或损坏 / 3计算或校验失败；
  - 错误码：ERR_ARGS_MISSING / ERR_PII_REMAIN（脱敏后仍有残留，拦截输出）/ ERR_IO。
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_NAME = "pii_sanitizer"

# 硬PII模式（脱敏后仍残留即ERR_PII_REMAIN拦截）
# 身份证号：可选吸收紧邻的"身份证号"前缀与冒号，避免替换后前缀叠加
HARD_PATTERNS = {
    "身份证号": re.compile(r"(?:身份证号?\s*[:：]?\s*)?(?<!\d)\d{6}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)"),
    "手机号": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "银行账号": re.compile(r"(?<!\d)\d{16,19}(?!\d)"),
}

# 软PII模式（尽力脱敏＋统计）
# 办案人员：消极后顾排除"办案/承办/主管/值班/社区"等定语，防止定语被误作姓名替换
SOFT_PATTERNS = {
    "案号": re.compile(r"[（(](19|20)\d{2}[）)][\u4e00-\u9fa50-9]{0,10}(刑初|刑终|刑再|刑核|刑执|刑减|刑申|检刑诉|检刑不诉)[\u4e00-\u9fa5]{0,3}\d+号"),
    "办案人员": re.compile(r"(?:(办案|承办|主管|值班|社区|一线|专案)(警官|检察官|法官|民警|审判长))|(?:([\u4e00-\u9fa5]{1,3})(警官|检察官|法官|民警|审判长))"),
    # 称谓在前、姓名在后（external模式脱敏用）："民警王建国承办"→"民警X"
    "办案人员姓名后置": re.compile(r"(警官|检察官|法官|民警|审判长)([\u4e00-\u9fa5]{2,3})(?=[，。；、：！？\s]|承办|办案|告知|称|说|介绍|表示|带领|负责|已|于|向|对|电话|沟通|递交|陪同|讯问|询问)"),
    "当事人姓名": re.compile(r"(当事人|嫌疑人|犯罪嫌疑人|被告人|上诉人|被上诉人|罪犯)([\u4e00-\u9fa5]{2,4}?)(?=[，。；、：！？\s]|住于|住在|居住|户籍|位于|到案|到庭|到场|出庭|作证|到访|签署|签收|递交|提交|系|因|被|已|现|于|在|，)"),
    # 涉案人员姓名（V1.0.1扩展）：同案人/家属/证人/被害人等称谓+2-3字姓名。
    # 姓名后须紧跟标点边界、接续动词/虚词、或另一涉案称谓（"同案人李四家属赵五"连串指涉）；
    # 姓名上限3字（四字及以上姓名不识别，由人工复核兜底），防"情绪激动"类四字词组误伤。
    "涉案人员姓名": re.compile(
        r"(同案人|同案犯|同案被告人|家属|证人|被害人|受害人|近亲属|委托人|其妻|其夫|其父|其母|其子|其女|其兄|其弟|其姐|其妹|其嫂)"
        r"([\u4e00-\u9fa5]{2,3})"
        r"(?=[，。；、：！？\s]|称|说|表示|介绍|陪同|携带|到访|前来|来到|前往|作证|出庭|到案|到庭|到场|签署|签收|拒收|递交|提交|签|按|于|在|向|对|系|因|被|已|现|的|与|和|及|或|且|并|家属|证人|被害人|受害人|同案人|委托人|近亲属)"),
    "住址": re.compile(r"(住址|住于|居住于|户籍地|位于)[:：]?\s*[\u4e00-\u9fa5]{0,3}?(省|市|区|县|镇|村|路|街|号|幢|室)[\u4e00-\u9fa5\d\-—]{2,40}"),
    "车牌号": re.compile(r"(?<![A-Za-z0-9])[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-HJ-NP-Z][A-HJ-NP-Z0-9]{5}[A-HJ-NP-Z0-9挂学警港澳]?(?![A-HJ-NP-Z0-9挂学警港澳])"),
    "邮箱": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}

NAME_POOL = ["某甲", "某乙", "某丙", "某丁", "某戊", "某己", "某庚", "某辛", "某壬", "某癸"]

# 办案人员称谓定语（“承办民警”组合保护——前置动词场景如“要求见承办民警”不得拆分）
OFFICER_PREFIXES = {"办案", "承办", "主管", "值班", "社区", "一线", "专案"}

# 角色称谓后接的常用名词（非姓名），防止“嫌疑人权利”“被告人信息”“当事人陈述”“证人证言”被误作姓名脱敏
ROLE_NAME_STOPWORDS = {
    # 证据法定名称与证据类用语（法律名词保护，不得脱敏）
    "陈述", "证言", "指证", "辨认", "指认", "笔录", "材料", "录音", "录像",
    "照片", "副本", "原件", "文书", "意见书", "鉴定", "勘验", "检查",
    # 程序动词类
    "到案", "到庭", "到场", "在场", "出庭", "作证", "翻供", "缺席",
    "旁听", "羁押", "取保", "释放", "拘留", "逮捕", "起诉", "抗诉",
    "申诉", "控告", "举报", "辩护", "代理", "委托", "授权", "签名", "签字",
    "捺印", "确认", "通知", "送达", "接收", "拒绝", "同意", "要求", "请求",
    "提出", "提起", "参加", "参与", "会见", "阅卷", "告知", "告知书", "有过错",
    # 实体与和解类
    "赔偿", "谅解", "和解", "退赔", "退赃", "履行", "执行", "分配", "份额",
    # 状态与后果类
    "死亡", "重伤", "轻伤", "受伤", "遇害", "失踪", "情绪", "心理", "身体",
    "状况", "范围", "名单", "关系", "诉求", "主张",
    # 时间与逻辑副词组合（“分别到案”“共同到庭”类）
    "分别", "共同", "同时", "随后", "当即", "当庭", "当场", "次日", "此前",
    "之后", "之前", "另案", "在逃", "均",
    # 原有基础库
    "权利", "义务", "情况", "身份", "信息", "下落", "供述", "辩解",
    "姓名", "年龄", "住址", "职业", "前科", "所在地", "基本情況",
    "基本情况", "基本信息", "意见", "申请", "上诉", "答辩", "质证",
}

# 姓名候选首字黑名单：高频文言虚词/副词/连词/介词开头的基本可判定非姓名
# （“未到庭”“尚未到”“分别在”“有过错”“之一”类组合不作为姓名；曾/尚两姓罕见，以人工复核兜底）
NEG_NAME_HEAD_CHARS = set("未不无已曾将均系于在尚正再又都也还即遂经应须"
                          "很较太过请暂仍且但是因为所以若虽然并同各该其"
                          "此每另分毫没莫非之为以从由按依据遭获受得")


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def sanitize(text, mode="external"):
    stats = {}
    name_map = {}

    # 1. 身份证号
    n = len(HARD_PATTERNS["身份证号"].findall(text))
    if n:
        text = HARD_PATTERNS["身份证号"].sub("身份证号[已脱敏]", text)
        stats["身份证号"] = n

    # 2. 银行账号（保留后四位）
    def bank_repl(m):
        tail = m.group(0)[-4:]
        return "**** **** " + tail
    n = len(HARD_PATTERNS["银行账号"].findall(text))
    if n:
        text = HARD_PATTERNS["银行账号"].sub(bank_repl, text)
        stats["银行账号"] = n

    # 3. 手机号
    n = len(HARD_PATTERNS["手机号"].findall(text))
    if n:
        text = HARD_PATTERNS["手机号"].sub("1XX**XX", text)
        stats["手机号"] = n

    # 4. 案号
    n = len(SOFT_PATTERNS["案号"].findall(text))
    if n:
        text = SOFT_PATTERNS["案号"].sub("(20XX)X刑初XX号", text)
        stats["案号"] = n

    # 5. 办案人员姓名（external模式脱敏，internal模式保留——内部文书需据以联系承办人）
    if mode == "external":
        # 5a. 姓名在前、称谓在后（“王建国警官”→“X警官”；定语组合原样保留，不误作姓名）
        def officer_repl(m):
            if m.group(3):  # 姓名分支命中
                # 定语保护：“要求见承办民警”中B分支会把“见承办”误作姓名——
                # 姓名候选以称谓定语（承办/办案等）结尾的，原样保留
                if any(m.group(3).endswith(p) for p in OFFICER_PREFIXES):
                    return m.group(0)
                return "X%s" % m.group(4)
            return m.group(0)  # 定语组合分支：原样保留
        hits = [m for m in SOFT_PATTERNS["办案人员"].finditer(text) if m.group(3)]
        if hits:
            text = SOFT_PATTERNS["办案人员"].sub(officer_repl, text)
            stats["办案人员姓名"] = len(hits)
        # 5b. 称谓在前、姓名在后（“民警王建国承办”→“民警X”）
        def officer_after_repl(m):
            return "%sX" % m.group(1)
        n_after = len(SOFT_PATTERNS["办案人员姓名后置"].findall(text))
        if n_after:
            text = SOFT_PATTERNS["办案人员姓名后置"].sub(officer_after_repl, text)
            stats["办案人员姓名"] = stats.get("办案人员姓名", 0) + n_after

    # 6. 当事人姓名（角色称谓后2-4字姓名→某甲/某乙序列；称谓后常用名词保护）
    def name_repl(m):
        role, name = m.group(1), m.group(2)
        if name in ROLE_NAME_STOPWORDS:
            return m.group(0)  # 称谓后接常用名词/法律名词，非姓名，原样保留
        if name[0] in NEG_NAME_HEAD_CHARS:
            return m.group(0)  # 虚词/副词开头组合（“未到庭”类），非姓名
        if name not in name_map:
            name_map[name] = NAME_POOL[len(name_map) % len(NAME_POOL)]
        return role + name_map[name]
    name_matches = SOFT_PATTERNS["当事人姓名"].findall(text)
    text = SOFT_PATTERNS["当事人姓名"].sub(name_repl, text)
    n_replaced = sum(1 for _role, nm in name_matches
                     if nm not in ROLE_NAME_STOPWORDS and nm[0] not in NEG_NAME_HEAD_CHARS)
    if n_replaced:
        stats["当事人姓名"] = n_replaced

    # 6b. 涉案人员姓名（V1.0.1扩展：同案人/家属/证人/被害人等称谓+姓名；
    #     与当事人姓名共享name_map——同一人在不同称谓下替换为同一代号）
    def involved_repl(m):
        role, name = m.group(1), m.group(2)
        if name in ROLE_NAME_STOPWORDS:
            return m.group(0)  # “证人证言”“被害人陈述”等法律名词，原样保留
        if name[0] in NEG_NAME_HEAD_CHARS:
            return m.group(0)  # “委托人未到庭”“同案人分别在”类，原样保留
        if name not in name_map:
            name_map[name] = NAME_POOL[len(name_map) % len(NAME_POOL)]
        return role + name_map[name]
    involved_matches = SOFT_PATTERNS["涉案人员姓名"].findall(text)
    text = SOFT_PATTERNS["涉案人员姓名"].sub(involved_repl, text)
    n_involved = sum(1 for _role, nm in involved_matches
                     if nm not in ROLE_NAME_STOPWORDS and nm[0] not in NEG_NAME_HEAD_CHARS)
    if n_involved:
        stats["涉案人员姓名"] = n_involved

    # 7. 住址
    n = len(SOFT_PATTERNS["住址"].findall(text))
    if n:
        text = SOFT_PATTERNS["住址"].sub("[住址已脱敏]", text)
        stats["住址"] = n

    # 8. 车牌号
    n = len(SOFT_PATTERNS["车牌号"].findall(text))
    if n:
        text = SOFT_PATTERNS["车牌号"].sub("[车牌已脱敏]", text)
        stats["车牌号"] = n

    # 9. 邮箱
    n = len(SOFT_PATTERNS["邮箱"].findall(text))
    if n:
        text = SOFT_PATTERNS["邮箱"].sub("[邮箱已脱敏]", text)
        stats["邮箱"] = n

    # 10. 未成年当事人提示（上下文检测，输出人工复核提示）
    warnings = []
    if "未成年" in text:
        warnings.append("检出“未成年”表述：未成年当事人请统一替换为“未成年当事人”，请人工复核")
    # 姓名类残余风险提示（V1.0.1）：凡发生姓名类替换，提示正则识别无法穷尽
    if any(k in stats for k in ("当事人姓名", "涉案人员姓名", "办案人员姓名")):
        warnings.append("自然人姓名按称谓上下文识别，无法穷尽（无称谓前缀的姓名、"
                        "四字及以上姓名、代词指涉等不在覆盖内），对外共享前请人工复核全文")
    return text, stats, warnings


def residual_hard_pii(text):
    remain = {}
    for k, pat in HARD_PATTERNS.items():
        hits = pat.findall(text)
        if hits:
            remain[k] = len(hits)
    return remain


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="PII自动脱敏：十类规则（姓名/未成年/身份证号/手机号/住址/银行账号/案号/办案人员/车牌号/邮箱），残留即拦截。",
        epilog=(
            "脱敏模式：\n"
            "  --mode external（默认）对外共享场景——办案人员姓名双向脱敏（“王建国警官”→“X警官”；“民警王建国”→“民警X”）\n"
            "  --mode internal    律所内部办案场景——办案人员姓名保留原样，其余九类照常脱敏\n"
            "\n"
            "姓名覆盖（V1.0.1扩展）：当事人及同案人/家属/证人/被害人/近亲属/委托人等涉案人员称谓后的姓名；\n"
            "证据法定名称（当事人陈述/被害人陈述/证人证言等）与程序用语经防误伤词库保护，不作姓名脱敏。\n"
            "\n"
            "调用示例：\n"
            "  python scripts/pii_sanitizer.py --text \"当事人张三，民警王建国承办\" --mode external\n"
            "  python scripts/pii_sanitizer.py --file 意见书.txt --mode internal --out 脱敏后.txt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--text", help="待脱敏文本")
    parser.add_argument("--file", help="待脱敏文件路径（UTF-8文本）")
    parser.add_argument("--mode", choices=["external", "internal"], default="external",
                        help="脱敏模式：external对外共享（默认，办案人员姓名一并脱敏）／internal律所内部（办案人员姓名保留）")
    parser.add_argument("--out", help="脱敏结果输出文件路径（可选）")
    args = parser.parse_args()
    trace_id = make_trace_id()

    if not args.text and not args.file:
        print(json.dumps(envelope("error", "ERR_ARGS_MISSING", "--text或--file至少提供一个", None),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    if args.file:
        if not os.path.exists(args.file):
            print(json.dumps(envelope("error", "ERR_IO", "文件不存在：%s" % args.file, None),
                             ensure_ascii=False, indent=2))
            sys.exit(2)
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            print(json.dumps(envelope("error", "ERR_IO", "文件读取失败：%s" % exc, None),
                             ensure_ascii=False, indent=2))
            sys.exit(2)
    else:
        text = args.text

    sanitized, stats, warnings = sanitize(text, mode=args.mode)
    remain = residual_hard_pii(sanitized)

    if remain:
        print(json.dumps(envelope("error", "ERR_PII_REMAIN",
                                  "脱敏后仍有硬PII残留，拦截输出",
                                  {"trace_id": trace_id, "residual": remain,
                                   "sanitized_preview": sanitized[:200]}),
                         ensure_ascii=False, indent=2))
        sys.exit(3)

    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(sanitized)
        except OSError as exc:
            print(json.dumps(envelope("error", "ERR_IO", "输出文件写入失败：%s" % exc, None),
                             ensure_ascii=False, indent=2))
            sys.exit(2)

    data = {"trace_id": trace_id, "mode": args.mode,
            "mode_note": ("external模式：办案人员姓名已双向脱敏，适用于对外共享输出"
                          if args.mode == "external"
                          else "internal模式：办案人员姓名已保留（仅限律所内部办案使用，"
                               "对外共享前须以external模式重新脱敏）"),
            "sanitized_text": sanitized,
            "stats": stats, "warnings": warnings,
            "total_sanitized": sum(stats.values())}
    print(json.dumps(envelope("ok", None, "脱敏完成", data), ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
