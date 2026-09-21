#!/usr/bin/env python3
# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
"""八字排盘：从公历出生日期推算四柱干支。
卷七标准算法：五虎遁(年上起月) + 公历日算日柱 + 五鼠遁(日上起时)。

用法: python3 baizi.py 1968 10 17 11 45
输出: 戊申 壬戌 庚申 壬午 (年 月 日 时)
"""
import sys
from datetime import date

# 六十甲子(甲子=0)
G60 = [
    "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未","壬申","癸酉",
    "甲戌","乙亥","丙子","丁丑","戊寅","己卯","庚辰","辛巳","壬午","癸未",
    "甲申","乙酉","丙戌","丁亥","戊子","己丑","庚寅","辛卯","壬辰","癸巳",
    "甲午","乙未","丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
    "甲辰","乙巳","丙午","丁未","戊申","己酉","庚戌","辛亥","壬子","癸丑",
    "甲寅","乙卯","丙辰","丁巳","戊午","己未","庚申","辛酉","壬戌","癸亥",
]
GAN = "甲乙丙丁戊己庚辛壬癸"

# 五虎遁: 年干→正月干 (甲己之年丙作首...)
HUDUN_YUE = {"甲":"丙","己":"丙","乙":"戊","庚":"戊","丙":"庚","辛":"庚",
             "丁":"壬","壬":"壬","戊":"甲","癸":"甲"}

# 五鼠遁: 日干→子时干 (甲己还加甲...)
SHUDUN_SHI = {"甲":"甲","己":"甲","乙":"丙","庚":"丙","丙":"戊","辛":"戊",
              "丁":"庚","壬":"庚","戊":"壬","癸":"壬"}

# 时辰地支: 按24小时映射 (子23-1, 丑1-3, 寅3-5, 卯5-7, 辰7-9, 巳9-11, 午11-13, ...)
HOUR_ZHI = ["子","丑","丑","寅","寅","卯","卯","辰","辰","巳","巳",
           "午","午","未","未","申","申","酉","酉","戌","戌","亥","亥","子"]

# 月支映射：按 (月份, 节气日, 当月地支, [节气前的旧地支])
# 从年初到年末排列
YUE_MAP = [
    (1, 6, "丑", "子"),   # 小寒
    (2, 4, "寅", "丑"),   # 立春
    (3, 6, "卯", "寅"),   # 惊蛰
    (4, 5, "辰", "卯"),   # 清明
    (5, 6, "巳", "辰"),   # 立夏
    (6, 6, "午", "巳"),   # 芒种
    (7, 7, "未", "午"),   # 小暑
    (8, 8, "申", "未"),   # 立秋
    (9, 8, "酉", "申"),   # 白露
    (10, 8, "戌", "酉"),  # 寒露
    (11, 8, "亥", "戌"),  # 立冬
    (12, 7, "子", "亥"),  # 大雪
]

def ri_gz(d: date) -> str:
    """公历日期 → 日干支。基准: 1900-01-01 = 甲戌。"""
    return G60[((d - date(1900, 1, 1)).days + 10) % 60]

def nian_zhu(y: int) -> str:
    """年柱: 立春前用上一年。默认立春在2月4日，精度足够。"""
    return G60[(y - 4) % 60]

def yue_gan_zhi(ng: str, yz: str) -> str:
    """月干支: ng=年干, yz=月支(寅卯辰...)"""
    zg = HUDUN_YUE[ng]
    ZHI_ORDER = "寅卯辰巳午未申酉戌亥子丑"
    offset = GAN.index(zg) + ZHI_ORDER.index(yz)
    return GAN[offset % 10] + yz

def yue_zhu(y: int, m: int, d: int) -> tuple:
    """月柱: 月支按节气定，返回 (月干支, 年柱)。"""
    # 立春前用上年年柱
    nz = nian_zhu(y) if not (m == 1 or (m == 2 and d < 4)) else nian_zhu(y - 1)
    ng = nz[0]
    yz = "寅"  # 默认
    for jm, jd, zhi, old_zhi in YUE_MAP:
        if (m, d) >= (jm, jd):
            yz = zhi
        elif m == jm:
            yz = old_zhi
            break
    return yue_gan_zhi(ng, yz), nz

def shi_zhu(rg: str, hour: int) -> tuple:
    """时柱: 地支按时辰，天干按五鼠遁从日干推。返回 (干支, 地支)。"""
    zhi = HOUR_ZHI[hour % 24]
    sg = SHUDUN_SHI[rg]
    ZHI_ORDER = "子丑寅卯辰巳午未申酉戌亥"
    offset = GAN.index(sg) + ZHI_ORDER.index(zhi)
    return GAN[offset % 10] + zhi, zhi

def paibazi(y: int, m: int, d: int, hour: int = 0, minute: int = 0):
    """公历日期 → 八字四柱 + 时辰地支。返回 (年柱, 月柱, 日柱, 时柱, 时辰地支)。"""
    dt = date(y, m, d)
    rz = ri_gz(dt)         # 日柱
    nz = nian_zhu(y) if not (m == 1 or (m == 2 and d < 4)) else nian_zhu(y - 1)
    yz, nz = yue_zhu(y, m, d)  # 月柱 (已处理年柱边界)
    sz, zhi = shi_zhu(rz[0], hour)
    return nz, yz, rz, sz, zhi

def main():
    if len(sys.argv) < 4:
        print("用法: python3 baizi.py 年 月 日 [时] [分]")
        print("示例: python3 baizi.py 1968 10 17 11 45")
        sys.exit(1)
    y, m, d = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    hh = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    mm = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    nz, yz, rz, sz, zhi = paibazi(y, m, d, hh, mm)
    print(f"{nz} {yz} {rz} {sz}")
    # 额外输出供 _heluo_core.py 使用
    print(f"hour_zhi={zhi}")

if __name__ == "__main__":
    main()
