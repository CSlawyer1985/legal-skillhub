#!/usr/bin/env python3
# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
"""河洛理数 · 通用排盘引擎 v1
只做算法计算，不嵌入爻辞/卷四数据。
干支取数/卦表等基础数据为内嵌常量；爻辞由上层按 SKILL.md 指引从 references/yaoci.json 读取。

用法: python3 _heluo_core.py "戊申 壬戌 庚申 壬午" 女 1968
输出: 本命卦/后天卦/元堂/大运结构/流年框架 (JSON)
"""
import sys, json

# ═══════════════════════ 基础数据 ═══════════════════════

# 卦映射: (上卦三画名, 下卦三画名) → (全名, Unicode)
GUA_MAP = {
    ("乾","乾"):("乾为天","䷀"),("乾","兑"):("天泽履","䷉"),("乾","离"):("天火同人","䷌"),
    ("乾","震"):("天雷无妄","䷘"),("乾","巽"):("天风姤","䷫"),("乾","坎"):("天水讼","䷅"),
    ("乾","艮"):("天山遁","䷠"),("乾","坤"):("天地否","䷋"),
    ("兑","乾"):("泽天夬","䷪"),("兑","兑"):("兑为泽","䷹"),("兑","离"):("泽火革","䷰"),
    ("兑","震"):("泽雷随","䷐"),("兑","巽"):("泽风大过","䷛"),("兑","坎"):("泽水困","䷮"),
    ("兑","艮"):("泽山咸","䷞"),("兑","坤"):("泽地萃","䷬"),
    ("离","乾"):("火天大有","䷍"),("离","兑"):("火泽睽","䷥"),("离","离"):("离为火","䷝"),
    ("离","震"):("火雷噬嗑","䷔"),("离","巽"):("火风鼎","䷱"),("离","坎"):("火水未济","䷿"),
    ("离","艮"):("火山旅","䷷"),("离","坤"):("火地晋","䷢"),
    ("震","乾"):("雷天大壮","䷡"),("震","兑"):("雷泽归妹","䷵"),("震","离"):("雷火丰","䷶"),
    ("震","震"):("震为雷","䷲"),("震","巽"):("雷风恒","䷟"),("震","坎"):("雷水解","䷧"),
    ("震","艮"):("雷山小过","䷽"),("震","坤"):("雷地豫","䷏"),
    ("巽","乾"):("风天小畜","䷈"),("巽","兑"):("风泽中孚","䷼"),("巽","离"):("风火家人","䷤"),
    ("巽","震"):("风雷益","䷩"),("巽","巽"):("巽为风","䷸"),("巽","坎"):("风水涣","䷺"),
    ("巽","艮"):("风山渐","䷴"),("巽","坤"):("风地观","䷓"),
    ("坎","乾"):("水天需","䷄"),("坎","兑"):("水泽节","䷻"),("坎","离"):("水火既济","䷾"),
    ("坎","震"):("水雷屯","䷂"),("坎","巽"):("水风井","䷯"),("坎","坎"):("坎为水","䷜"),
    ("坎","艮"):("水山蹇","䷦"),("坎","坤"):("水地比","䷇"),
    ("艮","乾"):("山天大畜","䷙"),("艮","兑"):("山泽损","䷨"),("艮","离"):("山火贲","䷕"),
    ("艮","震"):("山雷颐","䷚"),("艮","巽"):("山风蛊","䷑"),("艮","坎"):("山水蒙","䷃"),
    ("艮","艮"):("艮为山","䷳"),("艮","坤"):("山地剥","䷖"),
    ("坤","乾"):("地天泰","䷊"),("坤","兑"):("地泽临","䷒"),("坤","离"):("地火明夷","䷣"),
    ("坤","震"):("地雷复","䷗"),("坤","巽"):("地风升","䷭"),("坤","坎"):("地水师","䷆"),
    ("坤","艮"):("地山谦","䷎"),("坤","坤"):("坤为地","䷁"),
}
SANHUA = {"111":"乾","110":"兑","101":"离","100":"震","011":"巽","010":"坎","001":"艮","000":"坤"}
STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
BRS   = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

TIANGAN_NUM = {"戊":1,"乙":2,"癸":2,"庚":3,"辛":4,"壬":6,"甲":6,"丁":7,"丙":8,"己":9}
DIZHI_NUM = {
    "亥":[1,6],"子":[1,6],"寅":[3,8],"卯":[3,8],
    "巳":[2,7],"午":[2,7],"申":[4,9],"酉":[4,9],
    "辰":[5,10],"戌":[5,10],"丑":[5,10],"未":[5,10],
}
LUOSHU_GUA = {1:"坎",2:"坤",3:"震",4:"巽",6:"乾",7:"兑",8:"艮",9:"离"}

def ystem(y): return (y - 4) % 10
def is_yang_year(y): return ystem(y) % 2 == 0

def gua_info(ln):
    """ln = [a,b,c,d,e,f], 下卦abc上卦def → (全名,符号)"""
    l = "".join(str(b) for b in ln[:3])
    u = "".join(str(b) for b in ln[3:])
    return GUA_MAP.get((SANHUA[u], SANHUA[l]), ("?", "?"))

def yaoname(p, is_yang):
    pn = ["初","二","三","四","五","上"][p]
    yy = "九" if is_yang else "六"
    # 初爻/上爻: 位置在前（初九、上六）; 中间四爻: 九六在前（九二、六三）
    if p == 0 or p == 5:
        return f"{pn}{yy}"
    return f"{yy}{pn}"

def tg(ln, p):
    """toggle 位置 p 的爻"""
    n = ln[:]; n[p] = 1 - n[p]; return n


# ═══════════════════════ 第 1 步：天地数 → 本命卦 ═══════════════════════
# 原书行号：天干取数 922–926 / 地支取数 932–936
# 天数地数 962–966 / 洛书配卦 968–974 / 遇十不用 1048–1054
# 五数寄宫 1014–1030 / 八卦相荡 988–1012

def compute_bazi_nums(bazi_str):
    """从八字字符串提取 12 个数"""
    parts = bazi_str.split()
    nums = []
    for p in parts:
        g, z = p[0], p[1]
        nums.append(TIANGAN_NUM[g])
        nums.extend(DIZHI_NUM[z])
    return nums

def yushu_qigua(tian, di):
    """余数起卦 (行 962–974 + 遇十不用 行 1048–1054)
    规则：天数满 25、地数满 30，超出则减去满数；再「遇十不用」——
      余数取个位数；若为整十则 10→1、20→2、30→3。
    验证(原书例)：天 31→6 / 29→4 / 35→1 / 22→2 / 25→5；
                 地 34→4 / 40→1 / 50→2 / 60→3 / 24→4 / 30→3。
    """
    def _yushu(val, man):
        r = val - man if val > man else val
        if r % 10 == 0 and r > 0:   # 整十 → 10/20/30 → 1/2/3
            return r // 10
        return r % 10               # 否则取个位
    return _yushu(tian, 25), _yushu(di, 30)

def wushu_jigong(r, gender, is_yangming, byear):
    """五数寄宫 (行 1018–1038)。寄宫诗：上元男艮女坤，下元男离女兑，
    中元阳男阴女艮、阴男阳女坤。
    三元 60 年一循环：1864 上元 / 1924 中元 / 1984 下元（行 1038）。
    """
    if r != 5: return r
    yuan = ((byear - 1864) // 60) % 3   # 0上元 1中元 2下元（对任意年份成立）
    if yuan == 0:      # 上元: 男艮(8) 女坤(2)
        return 8 if gender == "男" else 2
    if yuan == 2:      # 下元: 男离(9) 女兑(7)
        return 9 if gender == "男" else 7
    # 中元: 阳男/阴女→艮(8); 阴男/阳女→坤(2)
    if gender == "男": return 8 if is_yangming else 2
    return 2 if is_yangming else 8

def get_benming_gua(bazi_str, gender, byear):
    """计算本命卦与元堂 (行 918–1166)"""
    nums = compute_bazi_nums(bazi_str)
    tian = sum(n for n in nums if n % 2 == 1)
    di  = sum(n for n in nums if n % 2 == 0)

    ts, ds = yushu_qigua(tian, di)
    parts = bazi_str.split()
    nian_gan = parts[0][0]
    is_yangming = nian_gan in "甲丙戊庚壬"

    ts = wushu_jigong(ts, gender, is_yangming, byear)
    ds = wushu_jigong(ds, gender, is_yangming, byear)

    tian_gua = LUOSHU_GUA[ts]
    di_gua   = LUOSHU_GUA[ds]

    # 八卦相荡 (行 990): 阳命男/阴命女→天数在上；阴命男/阳命女→天数在下
    if (is_yangming and gender == "男") or (not is_yangming and gender == "女"):
        upper, lower = tian_gua, di_gua
        placement = "天数在上·地数在下"
    else:
        upper, lower = di_gua, tian_gua
        placement = "天数在下·地数在上"

    # 确认上下卦：GUA_MAP key = (上卦, 下卦)
    fn, sym = GUA_MAP.get((upper, lower), ("?", "?"))
    # 六爻数组：下卦三爻 + 上卦三爻
    shang_sanhua = [k for k,v in SANHUA.items() if v == upper][0]
    xia_sanhua   = [k for k,v in SANHUA.items() if v == lower][0]
    liuyao = [int(c) for c in xia_sanhua] + [int(c) for c in shang_sanhua]

    return {
        "tian_total": tian, "di_total": di,
        "tian_yushu": ts, "di_yushu": ds,
        "tian_gua": tian_gua, "di_gua": di_gua,
        "is_yangming": is_yangming,
        "placement": placement,
        "benming_name": fn, "benming_symbol": sym,
        "liuyao": liuyao,  # [初,二,三,四,五,上]
        "upper_gua": upper, "lower_gua": lower,
    }


# ═══════════════════════ 第 2 步：取元堂 ═══════════════════════
# 原书行号 1056–1166，起元堂诗 1064

def get_yuantang(liuyao, hour_zhi, gender="男", is_yang_season=True):
    """按出生时辰取元堂爻位 (行 1056–1160)
    liuyao: 六爻数组 [初,二,三,四,五,上], 0=阴1=阳
    hour_zhi: 时辰地支 (子丑寅卯辰巳午未申酉戌亥)
    gender: 男/女。纯爻(乾/坤)时男女取法不同 (行 1138–1158)。
    is_yang_season: 出生是否阳令季节 (冬至后~夏至前)。仅纯爻顺/逆判定用到。
    """
    yang_hours = ["子","丑","寅","卯","辰","巳"]  # 上六时
    is_yang_shi = hour_zhi in yang_hours

    # 统计同极性爻的位置
    target_polarity = 1 if is_yang_shi else 0  # 阳时取阳爻，阴时取阴爻
    same_pol = [i for i, v in enumerate(liuyao) if v == target_polarity]
    opp_pol  = [i for i, v in enumerate(liuyao) if v != target_polarity]
    n_same = len(same_pol)

    # 时辰索引：阳时从 0(子) 开始，阴时从 6(午) 开始
    all_hours = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    hour_idx = all_hours.index(hour_zhi)
    start_idx = 0 if is_yang_shi else 6
    offset = hour_idx - start_idx  # 0..5

    # 起元堂诗 (行 1064):
    # 1-2根：一二重而寄 — 同极性爻重复两轮，再借反极性
    #   例: 师卦(1阳) → [2,2,0,1,3,4]  /  萃卦(2阳) → [3,4,3,4,0,1]
    # 3根：三位虽重没寄宫 — 同极性爻重复两轮覆盖6时辰，不借反极性
    #   例: 旅卦(3阳) → [2,3,5,2,3,5]
    # 4-5根：四五无重应有寄 — 同极性先数完，再借反极性
    # 6根：纯爻男女不相同 — 纯阳/纯阴特殊处理

    # 纯爻(乾/坤)判定须独立于时辰阴阳：纯卦六爻同性，阴时纯阳卦 same_pol 会为 0，
    # 若按 n_same==6 判会被误路由。故先判纯卦。
    all_yang = all(v == 1 for v in liuyao)
    is_pure = all_yang or all(v == 0 for v in liuyao)

    if is_pure:
        # 纯爻男女不相同 (行 1138–1158)。顺数=自下而上，逆数=自上行下。
        # 男得乾/女得坤 恒顺；女得乾阳令逆、阴令顺；男得坤阴令逆、阳令顺。
        if gender == "男":
            shun = all_yang or is_yang_season
        else:
            shun = (not all_yang) or (not is_yang_season)
        if shun:   # 顺: 阳时数下卦(初二三), 阴时数上卦(四五上)
            pos = offset % 3 if is_yang_shi else 3 + offset % 3
        else:      # 逆: 阳时自上行下数上卦(上五四), 阴时自上行下数下卦(三二初)
            pos = 5 - offset % 3 if is_yang_shi else 2 - offset % 3
    elif n_same <= 2:
        # 一二重而寄: same_pol 重复两轮，再借 opp_pol
        seq = (same_pol * 2) + opp_pol
        pos = seq[offset]
    elif n_same == 3:
        # 三位虽重没寄宫: same_pol 重复两轮 = 6时辰，不需要借
        seq = same_pol * 2
        pos = seq[offset]
    else:  # 4-5 根
        # 四五无重应有寄: 同极性先数完，再借反极性
        full_seq = same_pol + opp_pol
        pos = full_seq[offset]

    is_yang_yao = liuyao[pos] == 1
    yt_name = yaoname(pos, is_yang_yao)
    return pos, yt_name


# ═══════════════════════ 第 3 步：换后天卦 ═══════════════════════
# 原书行号 1167–1185
# 第一步：翻元堂爻（阳变阴、阴变阳）
# 第二步：内外卦易位（上卦⇄下卦）
# 例外（行 1175–1185）：坎、屯、蹇三卦，元堂在九五/上六时：
#   九五 + 阴令 → 翻爻但不换位
#   上六 + 阳令 → 翻爻但不换位
#   「令」按出生时辰区分：子丑寅卯辰巳=阳令，午未申酉戌亥=阴令

def get_houtian_gua(liuyao, yt_pos, hour_zhi):
    """后天卦变换 (行 1169–1185)。hour_zhi 必填：坎屯蹇例外依时辰定阳令/阴令。"""
    fn_before, _ = gua_info(liuyao)
    yang_hours = ["子","丑","寅","卯","辰","巳"]
    is_yang_ling = hour_zhi in yang_hours  # 阳令/阴令

    # 查是否触发坎屯蹇例外
    is_kantunji = any(k in fn_before for k in ["坎","屯","蹇"])
    skip_swap = False
    if is_kantunji and yt_pos == 4:  # 九五
        if not is_yang_ling:  # 阴令
            skip_swap = True
    elif is_kantunji and yt_pos == 5:  # 上六
        if is_yang_ling:  # 阳令
            skip_swap = True

    # 翻元堂爻
    flipped = liuyao[:]
    flipped[yt_pos] = 1 - flipped[yt_pos]

    if skip_swap:
        # 变而不易：只翻爻，不换位
        fn, sym = gua_info(flipped)
        new_yt = yt_pos  # 元堂位置不变
    else:
        # 正常：翻爻 + 内外易位
        swapped = flipped[3:6] + flipped[0:3]
        fn, sym = gua_info(swapped)
        # 新元堂: 原在下→易位后在上; 原在上→易位后在下
        new_yt = yt_pos + 3 if yt_pos < 3 else yt_pos - 3
        flipped = swapped  # 后续使用 flipped 状态

    new_is_yang = flipped[new_yt] == 1
    new_yt_name = yaoname(new_yt, new_is_yang)

    return {
        "houtian_name": fn, "houtian_symbol": sym,
        "houtian_liuyao": flipped,
        "houtian_yt_pos": new_yt, "houtian_yt_name": new_yt_name,
    }


# ═══════════════════════ 第 4 步：排大运 ═══════════════════════
# 原书行号 1345–1373: 阳爻9年、阴爻6年，从元堂顺行六爻

def get_dayun(liuyao, yt_pos):
    """排12段大运（先天6段+后天6段），每段 (start_age, end_age, yao_pos, is_yang, yao_name)"""
    yuns = []
    pos = yt_pos
    for _ in range(6):
        is_yang = (liuyao[pos] == 1)
        dur = 9 if is_yang else 6
        yuns.append({"pos": pos, "is_yang": is_yang, "dur": dur, "yao_name": yaoname(pos, is_yang)})
        pos = (pos + 1) % 6

    # 累加岁数
    result = []
    age = 0
    for y in yuns:
        result.append({**y, "start_age": age, "end_age": age + y["dur"] - 1})
        age += y["dur"]
    return result


# ═══════════════════════ 第 5 步：排流年 ═══════════════════════
# 所有流年规则来自卷一（原书行 8225 阴爻、行 1349 阳爻）。
# 卷四是卷一规则跑完后的预计算结果（查表用），卷四本身不给规则。
#
# 阴爻: 累加双向 toggle — 每年在上一年结果上翻一个爻（阴↔阳互换）。
#       规则行 8225，已用两个实例交叉验证（坤初六 + 同人六二）。
#       卷四阴爻列是此规则的结果，可直接查也可自行计算。
#
# 阳爻: 行 1349 坐明堂→取应爻→复还本爻→行六爻，已实现为 liunian_yang，
#       经原书同人九三(阳年)+同人九四(阴年)两实例逐年验证全中。阴阳只看运首年。

def liunian_yin(base_gua, start_pos, start_age, start_year):
    """阴爻运 6 年流年 (卷一 行 8225 + 行 1361)
    「一年变一爻，自下而上」。双向翻转（阴↔阳），累加在前一年结果上。
    已验证: 坤初六 → 复临泰大壮夬乾 / 同人六二 → 乾履中孚损临师。
    不需要卷四，规则自洽。
    """
    results = []
    current = base_gua[:]
    for i in range(6):
        ag = start_age + i
        yr = start_year + i
        p = (start_pos + i) % 6
        current[p] = 1 - current[p]  # 在前一年结果上累加翻转
        nm, sym = gua_info(current)
        y = yaoname(p, current[p])
        results.append({"age": ag, "year": yr, "stem": STEMS[ystem(yr)],
                        "gua_name": nm, "gua_symbol": sym, "yao_name": y,
                        "method": "toggle"})
    return results

def liunian_yang(base_gua, start_pos, start_age, start_year):
    """阳爻运 9 年流年 (卷一 行 1349–1353 两个完整实例验证)

    阴阳只看「运首年」(第一年)天干 — 眉批「切须仔细看初爻之年是阳是阴」。
      Year1 坐明堂: 阳年不变 / 阴年翻本爻
      Year2 取应爻: 只翻应爻
      Year3 复还本爻: toggle 本爻
      Year4-9 行六爻: 每年只翻一爻 fp=(P+1+i-3)%6 (自下而上绕一圈), 不碰本爻

    已验证: 同人九三(阳年)→同人革随屯复颐剥蒙蛊;
           同人九四(阴年)→家人渐遯旅小过丰大壮归妹临。9 年全中。
    """
    P = start_pos  # 本爻
    Y = (P + 3) % 6  # 应爻
    yun_yang = is_yang_year(start_year)  # 运首年定阴阳 (眉批: 看初爻之年是阳是阴)
    results = []
    current = base_gua[:]
    for i in range(9):
        ag = start_age + i
        yr = start_year + i

        if i == 0:
            # Year 1: 坐明堂 — 阳年不变, 阴年翻本爻
            if not yun_yang:
                current[P] = 1 - current[P]
            fp = P
        elif i == 1:
            # Year 2: 取应爻 — 只翻应爻
            current[Y] = 1 - current[Y]
            fp = Y
        elif i == 2:
            # Year 3: 复还本爻 — toggle 本爻
            current[P] = 1 - current[P]
            fp = P
        else:
            # Year 4–9: 行六爻 — 每年只翻一爻 (自下而上), 不碰本爻
            fp = (P + 1 + i - 3) % 6
            current[fp] = 1 - current[fp]

        nm, sym = gua_info(current)
        y = yaoname(fp, current[fp])
        results.append({"age": ag, "year": yr, "stem": STEMS[ystem(yr)],
                        "gua_name": nm, "gua_symbol": sym, "yao_name": y,
                        "method": "juan1_yang"})
    return results


# ═══════════════════════ 主入口 ═══════════════════════

def paipan(bazi_str, gender, byear, hour_zhi, is_yang_season=True):
    """完整的河洛排盘，返回 dict
    is_yang_season: 出生是否阳令季节(冬至后~夏至前)。仅纯乾/纯坤命造取元堂时用。"""
    # 1. 本命卦
    bm = get_benming_gua(bazi_str, gender, byear)
    liuyao = bm["liuyao"]

    # 2. 元堂
    yt_pos, yt_name = get_yuantang(liuyao, hour_zhi, gender, is_yang_season)

    # 3. 后天卦
    ht = get_houtian_gua(liuyao, yt_pos, hour_zhi)

    # 4. 大运
    xian_dayun = get_dayun(liuyao, yt_pos)
    hou_dayun  = get_dayun(ht["houtian_liuyao"], ht["houtian_yt_pos"])

    # 5. 流年 (框架)
    all_liunian = []
    birth_year = byear

    # 先天段流年
    for dy in xian_dayun:
        base = liuyao
        if dy["is_yang"]:
            all_liunian.extend(
                liunian_yang(base, dy["pos"], dy["start_age"], birth_year + dy["start_age"])
            )
        else:
            all_liunian.extend(
                liunian_yin(base, dy["pos"], dy["start_age"], birth_year + dy["start_age"])
            )

    # 后天段：年龄从先天段结束后接续
    xian_end_age = xian_dayun[-1]["end_age"]
    for dy in hou_dayun:
        dy_adj = {**dy, "start_age": dy["start_age"] + xian_end_age + 1,
                  "end_age": dy["end_age"] + xian_end_age + 1}
        base = ht["houtian_liuyao"]
        if dy_adj["is_yang"]:
            all_liunian.extend(
                liunian_yang(base, dy_adj["pos"], dy_adj["start_age"], birth_year + dy_adj["start_age"])
            )
        else:
            all_liunian.extend(
                liunian_yin(base, dy_adj["pos"], dy_adj["start_age"], birth_year + dy_adj["start_age"])
            )

    return {
        "bazi": bazi_str, "gender": gender, "birth_year": byear, "hour_zhi": hour_zhi,
        "tian_total": bm["tian_total"], "di_total": bm["di_total"],
        "tian_yushu": bm["tian_yushu"], "di_yushu": bm["di_yushu"],
        "tian_gua": bm["tian_gua"], "di_gua": bm["di_gua"],
        "is_yangming": bm["is_yangming"],
        "placement": bm["placement"],
        "benming_name": bm["benming_name"],
        "benming_symbol": bm["benming_symbol"],
        "benming_liuyao": liuyao,
        "yuantang_pos": yt_pos,
        "yuantang_name": yt_name,
        "houtian_name": ht["houtian_name"],
        "houtian_symbol": ht["houtian_symbol"],
        "houtian_liuyao": ht["houtian_liuyao"],
        "houtian_yt_pos": ht["houtian_yt_pos"],
        "houtian_yt_name": ht["houtian_yt_name"],
        "xian_dayun": xian_dayun,
        "hou_dayun": hou_dayun,
        "liunian": all_liunian,
        # 卷四复核: 以下输出可用于与卷四原表逐行比对
        "juan4_verify": "以卷一算法自算，应与卷四原表一致。不一致处需排查。",
    }


def main():
    if len(sys.argv) < 5:
        print("用法: python3 _heluo_core.py '八字' 性别 出生年 时辰地支")
        print("示例: python3 _heluo_core.py '戊申 壬戌 庚申 壬午' 女 1968 午")
        sys.exit(1)
    bazi = sys.argv[1]
    gender = sys.argv[2]
    byear = int(sys.argv[3])
    hour_zhi = sys.argv[4]
    result = paipan(bazi, gender, byear, hour_zhi)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
