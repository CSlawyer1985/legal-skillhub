"""NDR 系 Word 输出格式唯一事实来源。

所有 NDR 业务技能的生成脚本应 from format_base import *，
禁止在脚本本地硬编码字体、页边距、行距、缩进、日期、文件名等格式常量。
跨系强制一致项须与 DR / Judge 系 base 保持同值。
"""
from docx.shared import Cm, Pt

MARGIN_TB = Cm(2.54)
MARGIN_LR = Cm(3.18)
LINE_SPACING = 1.5
FONT_VARIANT = '仿宋_GB2312'
FIRST_INDENT = Cm(0.85)
DATE_MODE = 'chinese'

TITLE_FONT = '黑体'
FONT_KAITI = '楷体'
BODY_SIZE = Pt(12)


def _to_chinese_date(date_str):
    import re
    digits = re.findall(r'\d+', date_str)
    if len(digits) < 3:
        return date_str
    year, month, day = int(digits[0]), int(digits[1]), int(digits[2])
    num_map = {0: '〇', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九', 10: '十'}
    year_str = ''.join(num_map[int(d)] for d in str(year))
    if month <= 10:
        month_str = num_map[month] + '月'
    elif month < 20:
        month_str = '十' + num_map[month - 10] + '月'
    else:
        month_str = num_map[month // 10] + '十' + (num_map[month % 10] if month % 10 else '') + '月'
    if day <= 10:
        day_str = num_map[day] + '日'
    elif day < 20:
        day_str = '十' + num_map[day - 10] + '日'
    elif day < 30:
        day_str = num_map[day // 10] + '十' + (num_map[day % 10] if day % 10 else '') + '日'
    else:
        day_str = num_map[day // 10] + '十' + num_map[day % 10] + '日'
    return f'{year_str}年{month_str}{day_str}'


def _resolve_size(val):
    """将字号参数安全转换为 Pt 对象。int/float 返回 Pt(val)，已是 Length 则原样返回。"""
    from docx.shared import Length
    if isinstance(val, Length):
        return val
    if isinstance(val, (int, float)):
        return Pt(val)
    return val


# ── 跨平台字体映射（Windows → macOS）──
# 定义在 format_base 层，供所有下游脚本通过 from format_base import * 使用
_EA_FONT_MAP = {
    '\u4eff\u5b8b_GB2312': 'STFangsong',
    '\u9ed1\u4f53': 'STHeiti',
    '\u6977\u4f53': 'STKaiti',
    '\u5b8b\u4f53': 'STSong',
    '\u5fae\u8f6f\u96c5\u9ed1': 'STHeiti',
    'FangSong': 'STFangsong',
    'SimHei': 'STHeiti',
    'KaiTi': 'STKaiti',
    'SimSun': 'STSong',
    'Microsoft YaHei': 'STHeiti',
}


def _ea_font(font_name):
    """将 Windows 字体名映射为 macOS 对应字体名，未命中则原样返回。"""
    return _EA_FONT_MAP.get(font_name, font_name)


def build_filename(doc_type, party, matter):
    return f'{doc_type}_{party}_{matter}.docx'

__all__ = ['MARGIN_TB', 'MARGIN_LR', 'LINE_SPACING', 'FONT_VARIANT', 'FIRST_INDENT', 'DATE_MODE', 'TITLE_FONT', 'FONT_KAITI', 'BODY_SIZE', '_resolve_size', '_to_chinese_date', 'build_filename', '_EA_FONT_MAP', '_ea_font']
