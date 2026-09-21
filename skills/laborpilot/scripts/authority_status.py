"""废止复核（2026-09-07）：浙江2026-08-25目录的窄范围效力闸门。

仅匹配文档身份，不扫描条文正文；目录日期不等于推定的效力终止日。
与 LaborPilot 同名模块同步维护，独立分发时各自可运行。
"""
import re
import unicodedata

REPEALED_IDS = {f"ZJLAC-LABOR-{n}" for n in (125, 128, 129, 130, 131, 132)}
NOTICE = "已列入浙江2026-08-25废止目录；仅供历史研究，不作现行依据，观点另核有效来源。"


def known_repeal(record):
    """识别七件劳动文件；不扩大到解答六、七、纪要、国家司法解释。"""
    if str(record.get("document_id", "")) in REPEALED_IDS:
        return True
    values = [str(record.get(k) or "") for k in ("title", "document_title", "law", "document_number")]
    for value in values:
        value = re.sub(r"\s+", "", unicodedata.normalize("NFKC", value))
        if re.search(r"浙法民一[〔\[(]2009[〕\])]3号|浙劳仲院[〔\[(]2012[〕\])]3号|浙高法民一[〔\[(](?:2014[〕\])]7|2015[〕\])]9|2016[〕\])]3|2019[〕\])]1)号", value):
            return True
        if "浙江" not in value and "浙高法" not in value:
            continue
        if "关于加班工资仲裁时效的解答" in value:
            return True
        if "关于审理劳动争议案件若干问题的意见(试行)" in value:
            return True
        if "关于审理劳动争议纠纷案件若干疑难问题的解答" in value:
            return True
        if re.search(r"关于审理劳动争议案件若干问题的解答\([二三四五]\)", value):
            return True
        if re.search(r"(?:浙江(?:省)?高院|浙高法)(?:民一庭)?解答(?:[一二三四五](?![一二三四五六七八九十])|\([一二三四五]\))", value):
            return True
    return False


def current_status(record):
    return "已废止" if known_repeal(record) else record.get("validity_status", "未标注")
