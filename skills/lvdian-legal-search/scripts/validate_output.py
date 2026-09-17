#!/usr/bin/env python3
"""
律典·法律检索 输出校验脚本（Step 4 后交付前必须运行）
=====================================================
作用：交付前自动检查输出是否符合「输出纪律」7 项硬约束。
      FAIL 即打回重做，AI 不得声明"已校验"而实际未运行本脚本。

用法：
  python3 scripts/validate_output.py --file /path/to/output.md
  cat output.md | python3 scripts/validate_output.py

检查项（对应输出纪律 ①②③④⑤⑥⑦）：
  C1 无代码块包裹法条卡（禁 ``` 包裹整张卡）
  C2 法条卡区域无表格（### 法条卡标题至下一个任意级标题之间无 | 表格行；层级覆盖自检表位于全部法条卡之后的二级标题下，豁免）
  C3 链接为 markdown 超链接格式 [库名全称](url)（禁裸 URL / 反引号包 URL）
  C4 库名全称（出现"国家法律法规数据库"，无孤立"flk 链接"/"flk 直链"等输出简称）
  C5 法规名全称（书名号内法律类名称须含"中华人民共和国"，通用规则非 hardcode 列表）
  C6 有效性已标注（每张法条卡含 现行有效/已修订/已废止）
  C7 原文已给（法条卡含"**原文**"或"原文："字段）
  C8 无个人信息（技能文档禁含姓名/执业地/单位/专属用户）
  C9 术语/编号统一（禁 R1-补/pkulaw 旧称）
  C10 第三方法律网站域名黑名单（铁律一落地为硬校验：找法网/110ask/华律网/律图等 URL 出现即违规，
      无论"问答页"还是"法规条文转载页"；线索提示仅可用文字表述并注明"未经验证、不作为依据"）

退出码：0=PASS，1=FAIL（违规项以 [FAIL] 列出）
幂等只读。
"""

import argparse
import re
import sys


# 第三方法律网站域名黑名单（铁律一·信源纪律）：URL 中命中即违规
# 找法网 findlaw.cn / 110法律咨询 110.com / 华律网 66law.cn / 律图 64365.com /
# 法律快车 lawtime.cn / 法帮网 fabang.com
THIRD_PARTY_DOMAINS = ("findlaw.cn", "110.com", "66law.cn", "64365.com", "lawtime.cn", "fabang.com")


def _strip_user_quotes(text: str) -> str:
    """剔除用户引文/场景说明回放行（"**用户提问**"/"**用户**"/blockquote 用户行），
    输入回放非 AI 输出，不参与违规检查（与 C5 引文豁免同逻辑，C10 共用）。"""
    out = []
    for l in text.splitlines():
        s = l.strip()
        if s.startswith("**用户提问**") or s.startswith("**用户**"):
            continue
        if s.startswith("> ") and ("用户" in s[:24] or "提问" in s[:24]):
            continue
        out.append(l)
    return "\n".join(out)


def check(text: str) -> list:
    """返回 [(检查项, 是否通过, 说明)]"""
    results = []
    lines = text.splitlines()
    # 治理规范章节为规则声明（"禁止出现 X"），不参与违规检查（避免把"禁 R1-补"声明误判为违规残留）
    gov_idx = text.find("## 文档治理规范")
    content = text[:gov_idx] if gov_idx != -1 else text
    # 剔除 URL（URL 域名中的 flk 属合法链接，不算输出简称）
    non_url_text = re.sub(r"https?://\S+", "", content)

    # C1: 无代码块包裹法条卡
    fences = text.count("```")
    c1_ok = fences == 0
    results.append(("C1 无代码块包裹法条卡", c1_ok,
                    f"代码块标记数={fences}" + ("" if c1_ok else " → 法条卡被 ``` 包裹会渲染灰色、链接不可点")))

    # C2: 无表格呈现单条法条（仅检测「法条卡区域」内的表格行）
    # 法条卡区域 = 以 "### " 开头的法条卡标题行起，至下一个任意级标题（#/##/###）或文末之间。
    # 「层级覆盖自检表」（模糊/主题式问题必附）位于全部法条卡之后、通常置于 "## 四、层级覆盖自检"
    # 等二级标题下，超出卡片区域截止线，不受 C2 限制。
    headings = [i for i, l in enumerate(lines) if l.startswith("#")]
    card_heads = [i for i, l in enumerate(lines) if l.startswith("### ")]
    card_table_lines = []
    for h in card_heads:
        end = len(lines)
        for nh in headings:  # 任意级标题均截止卡片区域
            if nh > h:
                end = nh
                break
        for l in lines[h:end]:
            if l.strip().startswith("|"):
                card_table_lines.append(l)
    c2_ok = len(card_table_lines) == 0
    results.append(("C2 法条卡区域无表格（层级自检表可置于全部法条卡之后）", c2_ok,
                    f"法条卡内表格行数={len(card_table_lines)}" + ("" if c2_ok else " → 单条法条禁表格，多条法条应用合并引用清单")))

    # C3: 链接为 markdown 超链接格式
    # 违规：裸 URL（未被 []() 包裹）、反引号包裹的 URL
    raw_urls = re.findall(r"(?<!\]\()https?://[^\s\)\]）]+", text)
    backtick_urls = re.findall(r"`https?://[^`]+`", text)
    md_links = re.findall(r"\[[^\]]+\]\(https?://[^\)]+\)", text)
    c3_ok = len(raw_urls) == 0 and len(backtick_urls) == 0
    results.append(("C3 链接为可点击超链接格式", c3_ok,
                    f"超链接数={len(md_links)}、裸URL={len(raw_urls)}、反引号URL={len(backtick_urls)}" + ("" if c3_ok else " → 链接不可点击，须用 [库名](url)")))

    # C4: 库名全称（无输出侧简称；URL 域名内的 flk 属合法链接）
    bad_short = re.findall(r"flk 链接|flk 直链|FLK|以 flk|flk 官网", non_url_text)
    has_full = "国家法律法规数据库" in text
    c4_ok = has_full and len(bad_short) == 0
    results.append(("C4 库名全称（国家法律法规数据库）", c4_ok,
                    f"全称出现={has_full}、简称残留={len(bad_short)}" + ("" if c4_ok else " → 输出禁止 flk 简称")))

    # C5: 法规名全称（法律类书名号内须含"中华人民共和国"前缀）
    # 通用规则（替代 hardcode 6 部法列表，覆盖全部法律）：书名号《》内以「法/法典」结尾
    # 且不含「中华人民共和国」、又非行政法规/规章类名称（办法/条例/规定…）的，判为简称违规。
    # （P6）：用户引文/场景说明回放（"**用户提问**"/"**用户**"/blockquote 用户行）中的
    # 简称属输入回放而非 AI 输出，剔除后再检测，避免误伤（实测 S1 场景说明被 C5 误判教训）。
    # _strip_user_quotes 定义见文件顶部（C5/C10 共用）。
    non_law_suffixes = ("办法", "条例", "规定", "细则", "规则", "规程", "方案", "标准",
                        "指引", "意见", "决定", "解释", "批复", "纲要", "规划", "要点", "通知")
    law_cands = re.findall(r"《([^》]{2,24})》", _strip_user_quotes(non_url_text))
    law_short = [n for n in law_cands
                 if (n.endswith("法") or n.endswith("法典"))
                 and "中华人民共和国" not in n
                 and not any(n.endswith(s) for s in non_law_suffixes)]
    c5_ok = len(law_short) == 0
    results.append(("C5 法规名全称（法律须带'中华人民共和国'，用户引文豁免）", c5_ok,
                    f"法律简称残留={law_short}" + ("" if c5_ok else " → 法律须带'中华人民共和国'前缀")))

    # C6: 有效性已标注
    valid_marks = re.findall(r"现行有效|已修订|已废止|✅ 现行|🔴 已|🟡 已", text)
    c6_ok = len(valid_marks) > 0
    results.append(("C6 有效性已标注", c6_ok, f"有效性标注数={len(valid_marks)}"))

    # C7: 原文已给（法条卡含原文字段）
    has_orig = ("**原文**" in text) or ("原文：" in text) or ("> 原文" in text)
    results.append(("C7 条文原文已给", has_orig, f"原文字段存在={has_orig}" + ("" if has_orig else " → 模糊主题式检索每条命中条款必须给原文")))

    # C8: 个人信息检查（技能文档禁含姓名/执业地/单位/专属用户）
    pii = re.findall(r"徐律师|徐海栋|派驻|上城区|专属用户", content)
    c8_ok = len(pii) == 0
    results.append(("C8 无个人信息（姓名/执业地/单位）", c8_ok,
                    f"敏感词={len(pii)}" + ("" if c8_ok else " → 技能文档禁含个人信息，教训记录用'用户'指代")))

    # C9: 术语/编号统一（禁 R1-补/R1 旧称、pkulaw 检索词等不统一表述）
    old_terms = re.findall(r"R1-补|R1 |pkulaw 检索词|pkulaw 词|以 pkulaw 为准", non_url_text)
    c9_ok = len(old_terms) == 0
    results.append(("C9 术语/编号统一（禁 R1-补/pkulaw 旧称）", c9_ok,
                    f"旧称残留={len(old_terms)}" + ("" if c9_ok else " → 按文档治理规范术语表统一")))

    # C10: 第三方法律网站域名黑名单（铁律一·信源纪律落地为硬校验）
    # 输出中出现的第三方站点 URL（无论"问答页"还是"法规条文转载页"）一律违规；
    # 线索提示仅可用文字表述并注明"未经验证、不作为依据"，不得附 URL。
    # 用户引文回放行中的第三方 URL 属输入回放，豁免（与 C5 同逻辑）。
    third_urls = re.findall(r"https?://([^\s\)\]）]+)", _strip_user_quotes(text))
    bad_third = [u for u in third_urls if any(d in u.lower() for d in THIRD_PARTY_DOMAINS)]
    c10_ok = len(bad_third) == 0
    results.append(("C10 第三方法律网站域名黑名单（找法网/110ask/华律网/律图等，用户引文豁免）", c10_ok,
                    f"第三方站点URL={len(bad_third)}" + ("" if c10_ok else f" → 被禁域名：{bad_third[:3]}；铁律一禁作法条来源，线索提示不得附URL")))

    return results


def main():
    ap = argparse.ArgumentParser(description="律典输出校验")
    ap.add_argument("--file", help="输出文件路径")
    args = ap.parse_args()
    if args.file:
        text = open(args.file, encoding="utf-8").read()
    else:
        text = sys.stdin.read()

    print("=" * 60)
    print("律典·法律检索 输出校验报告")
    print("=" * 60)
    results = check(text)
    all_pass = True
    for name, ok, detail in results:
        mark = "✅ PASS" if ok else "❌ FAIL"
        if not ok:
            all_pass = False
        print(f"  [{mark}] {name}: {detail}")
    print("-" * 60)
    if all_pass:
        print("✅ 输出校验通过：符合输出纪律，可交付。")
        sys.exit(0)
    else:
        print("❌ 输出校验未通过：按输出纪律打回重做，不得交付。")
        sys.exit(1)


if __name__ == "__main__":
    main()
