#!/usr/bin/env python3
"""
模糊匹配算法模块
支持：标准化、Levenshtein 编辑距离、拼音音译、别名展开、缩写匹配
"""

import re
import unicodedata


def normalize_name(name: str) -> str:
    """
    名称标准化：统一大小写、去除多余空格和标点

    参数:
        name: 原始名称
    返回:
        标准化后的名称
    """
    # Unicode 标准化（处理变音符号等）
    name = unicodedata.normalize("NFKD", name)
    # 转小写
    name = name.lower().strip()
    # 去除常见后缀
    suffixes = [
        "ltd", "ltd.", "limited", "inc", "inc.", "incorporated",
        "corp", "corp.", "corporation", "co.", "company",
        "llc", "l.l.c.", "gmbh", "ag", "sa", "s.a.",
        "plc", "p.l.c.", "pte", "pvt",
        "有限公司", "股份有限公司", "集团", "控股",
    ]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
    # 去除标点和多余空格
    name = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def levenshtein_distance(s1: str, s2: str) -> int:
    """计算 Levenshtein 编辑距离"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def similarity_score(name1: str, name2: str) -> float:
    """
    计算两个名称的相似度 (0.0 - 1.0)

    参数:
        name1, name2: 待比较的名称
    返回:
        相似度分数 0.0（完全不同）到 1.0（完全相同）
    """
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    if n1 == n2:
        return 1.0

    # 编辑距离
    dist = levenshtein_distance(n1, n2)
    max_len = max(len(n1), len(n2))
    if max_len == 0:
        return 1.0

    return 1.0 - (dist / max_len)


# ── 中文拼音映射（简化版，覆盖常用姓氏和公司名用字）──
# 在没有 pypinyin 库的情况下使用
PINYIN_MAP = {
    "华": "hua", "为": "wei", "中": "zhong", "国": "guo",
    "海": "hai", "洋": "yang", "石": "shi", "油": "you",
    "大": "da", "疆": "jiang", "腾": "teng", "讯": "xun",
    "阿": "a", "里": "li", "巴": "ba", "百": "bai",
    "度": "du", "京": "jing", "东": "dong", "小": "xiao",
    "米": "mi", "字": "zi", "节": "jie", "跳": "tiao",
    "联": "lian", "想": "xiang", "比": "bi", "亚": "ya",
    "迪": "di", "宁": "ning", "德": "de", "科": "ke",
    "技": "ji", "电": "dian", "信": "xin", "银": "yin",
    "行": "hang", "工": "gong", "商": "shang", "建": "jian",
    "设": "she", "农": "nong", "交": "jiao", "通": "tong",
    "贸": "mao", "易": "yi", "天": "tian", "地": "di",
    "人": "ren", "民": "min", "解": "jie", "放": "fang",
    "军": "jun", "核": "he", "能": "neng", "源": "yuan",
    "航": "hang", "空": "kong", "船": "chuan", "舶": "bo",
    "武": "wu", "器": "qi", "导": "dao", "弹": "dan",
    "卫": "wei", "星": "xing", "通": "tong", "讯": "xun",
}

# 已知中英文公司名映射
# 覆盖常见被制裁/管制中国实体及大型公司
KNOWN_TRANSLATIONS = {
    # 通信/半导体
    "华为": "huawei",
    "中兴": "zte",
    "中芯国际": "smic",
    "长江存储": "ymtc",
    "紫光集团": "tsinghua unigroup",
    "长鑫存储": "cxmt",
    "海思": "hisilicon",
    "中微半导体": "amec",
    # 监控/安防
    "海康威视": "hikvision",
    "大华科技": "dahua",
    "大疆": "dji",
    "商汤": "sensetime",
    "旷视": "megvii",
    "依图": "yitu",
    "云从": "cloudwalk",
    "科大讯飞": "iflytek",
    # 互联网/科技
    "字节跳动": "bytedance",
    "腾讯": "tencent",
    "阿里巴巴": "alibaba",
    "百度": "baidu",
    "小米": "xiaomi",
    "联想": "lenovo",
    # 汽车/制造
    "比亚迪": "byd",
    "中车": "crrc",
    "宁德时代": "catl",
    # 能源/资源
    "中国海洋石油": "cnooc",
    "中国石油": "cnpc",
    "中国石化": "sinopec",
    "中广核": "cgn",
    "中国核工业": "cnnc",
    # 军工/航天
    "中国航天": "casc",
    "中国航空": "avic",
    "中国电子科技": "cetc",
    "中国船舶": "cssc",
    "北方工业": "norinco",
    "中国兵器": "norinco",
    "保利集团": "poly group",
    # 金融
    "中国银行": "bank of china",
    "工商银行": "icbc",
    "建设银行": "ccb",
}

# 全名 ↔ 简称映射（用于搜索官方网站时的名称扩展）
FULL_NAME_MAP = {
    "dji": ["SZ DJI Technology", "DJI Technology", "Da Jiang Innovations",
            "Shenzhen DJI Sciences and Technologies"],
    "huawei": ["Huawei Technologies Co", "Huawei Device", "Huawei Cloud"],
    "zte": ["ZTE Corporation", "Zhongxing Telecommunication"],
    "hikvision": ["Hangzhou Hikvision Digital Technology"],
    "smic": ["Semiconductor Manufacturing International Corp"],
    "sensetime": ["SenseTime Group", "SenseTime Technology"],
    "norinco": ["China North Industries Group", "China North Industries Corp"],
    "cetc": ["China Electronics Technology Group Corp"],
    "avic": ["Aviation Industry Corporation of China"],
    "cgn": ["China General Nuclear Power"],
    "catl": ["Contemporary Amperex Technology"],
}


def chinese_to_pinyin(text: str) -> str:
    """将中文文本转换为拼音（简化版）"""
    # 先检查已知映射
    for cn, en in KNOWN_TRANSLATIONS.items():
        if cn in text:
            return en

    # 逐字转换
    result = []
    for char in text:
        if char in PINYIN_MAP:
            result.append(PINYIN_MAP[char])
        elif re.match(r"[\u4e00-\u9fff]", char):
            result.append(char)  # 未知汉字保留
        else:
            result.append(char)
    return "".join(result)


def generate_name_variants(name: str) -> list:
    """
    生成名称的多种变体用于匹配

    策略：
      - 中文名 → 英文简称 + 英文全名 + 拼音
      - 英文名 → 中文名 + 全名扩展
      - 用于 OpenSanctions API 匹配和官方网站搜索

    参数:
        name: 原始名称
    返回:
        变体列表（包含原始名称），按搜索优先级排列
    """
    variants = [name]  # 原始名称
    normalized = normalize_name(name)
    if normalized != name.lower():
        variants.append(normalized)

    # 检查是否包含中文
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", name))

    if has_chinese:
        # 中文 → 英文简称（优先，因为官方名单用英文）
        matched_en = None
        for cn, en in KNOWN_TRANSLATIONS.items():
            if cn in name:
                matched_en = en
                variants.append(en)
                break

        # 英文简称 → 全名扩展（用于官方网站搜索）
        if matched_en and matched_en in FULL_NAME_MAP:
            for full_name in FULL_NAME_MAP[matched_en]:
                variants.append(full_name)
        elif matched_en:
            # 没有全名映射时，生成通用变体
            variants.append(f"{matched_en} technology")
            variants.append(f"{matched_en} technologies")

        # 中文 → 拼音（作为最后的回退）
        pinyin = chinese_to_pinyin(name)
        if pinyin != name and pinyin not in [v.lower() for v in variants]:
            variants.append(pinyin)
    else:
        # 英文名处理
        name_lower = name.lower().strip()

        # 检查是否有已知中文对应
        for cn, en in KNOWN_TRANSLATIONS.items():
            if en == name_lower or en in name_lower:
                variants.append(cn)
                # 同时加入全名变体
                if en in FULL_NAME_MAP:
                    for full_name in FULL_NAME_MAP[en]:
                        variants.append(full_name)
                break

    # 去重并保序
    seen = set()
    unique = []
    for v in variants:
        v_clean = v.strip()
        if v_clean and v_clean.lower() not in seen:
            seen.add(v_clean.lower())
            unique.append(v_clean)

    return unique


def fuzzy_match(query: str, candidates: list, threshold: float = 0.7) -> list:
    """
    对候选列表进行模糊匹配

    参数:
        query: 查询名称
        candidates: 候选名称列表
        threshold: 最低相似度阈值
    返回:
        匹配结果列表 [{"name": str, "score": float}, ...]
    """
    results = []
    query_variants = generate_name_variants(query)

    for candidate in candidates:
        best_score = 0.0
        for variant in query_variants:
            score = similarity_score(variant, candidate)
            best_score = max(best_score, score)

        if best_score >= threshold:
            results.append({"name": candidate, "score": best_score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


if __name__ == "__main__":
    # 简单测试
    print("=== 名称变体测试 ===")
    test_names = ["华为", "Huawei Technologies", "中国海洋石油", "CNOOC"]
    for name in test_names:
        variants = generate_name_variants(name)
        print(f"  {name} → {variants}")

    print("\n=== 相似度测试 ===")
    pairs = [
        ("Huawei", "Hauwei"),
        ("Huawei Technologies", "Huawei Tech"),
        ("中国海洋石油", "CNOOC"),
    ]
    for a, b in pairs:
        score = similarity_score(a, b)
        print(f"  {a} vs {b} → {score:.2f}")
