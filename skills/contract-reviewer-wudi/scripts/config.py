#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享配置模块 v1.0.0
集中管理所有可配置项，避免硬编码
"""

import os
import atexit
import shutil
from pathlib import Path

# ============================================================
# 配色方案
# ============================================================
SEVERITY_COLORS = {
    '高风险': 'C00000',   # 深红
    '中风险': 'E36C09',   # 橙色
    '低风险': '2E75B6',   # 蓝色
    '信息':   '595959',   # 深灰
}

SEVERITY_BG = {
    '高风险': 'FFE7E7',
    '中风险': 'FFF3E0',
    '低风险': 'E7F3FF',
    '信息':   'F5F5F5',
}

SEVERITY_DOTS = {
    '高风险': '🔴',
    '中风险': '🟡',
    '低风险': '🔵',
    '信息':   '⚪',
}

# ============================================================
# 字体配置
# ============================================================
DEFAULT_FONT = os.environ.get('CONTRACT_REVIEW_FONT', 'SimSun')
DEFAULT_FONT_SIZE = int(os.environ.get('CONTRACT_REVIEW_FONT_SIZE', '21'))

# Mac/Linux 备选字体
FALLBACK_FONTS = {
    'darwin': ['PingFang SC', 'STHeiti', 'Heiti SC'],
    'linux': ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Droid Sans Fallback'],
}

def get_system_font():
    """获取系统可用的中文字体"""
    import platform
    system = platform.system().lower()
    
    # Windows 默认用 SimSun
    if system == 'windows':
        return 'SimSun'
    
    # Mac/Linux 检查备选字体
    fallbacks = FALLBACK_FONTS.get(system, [])
    for font in fallbacks:
        # 简单检查：假设字体可用（实际应检查 fontconfig）
        return font
    
    return DEFAULT_FONT

# ============================================================
# 匹配阈值
# ============================================================
MATCH_THRESHOLD = float(os.environ.get('CONTRACT_MATCH_THRESHOLD', '0.3'))
FUZZY_MATCH_MIN_LENGTH = 8  # 最短子串匹配长度

# ============================================================
# 作者识别模式
# ============================================================
OUR_AUTHOR_PATTERNS = [
    r'^Claude',
    r'^OpenClaw',
    r'^AI.*审核',
    r'.*法律审核.*',
]

COUNTERPARTY_PATTERNS = [
    r'^对方',
    r'^乙方',
    r'^甲方',
]

# ============================================================
# 临时文件管理
# ============================================================
_tmp_dirs = []

def register_tmp_dir(path: str):
    """注册临时目录，程序退出时自动清理"""
    _tmp_dirs.append(Path(path))

def cleanup_tmp_dirs():
    """清理所有注册的临时目录"""
    for d in _tmp_dirs:
        if d.exists():
            try:
                shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass

atexit.register(cleanup_tmp_dirs)

# ============================================================
# 日志配置
# ============================================================
import logging

def setup_logging(level=logging.INFO):
    """设置统一日志格式"""
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )
    return logging.getLogger('contract-reviewer')

# ============================================================
# 导出配置
# ============================================================
__all__ = [
    'SEVERITY_COLORS',
    'SEVERITY_BG', 
    'SEVERITY_DOTS',
    'DEFAULT_FONT',
    'DEFAULT_FONT_SIZE',
    'get_system_font',
    'MATCH_THRESHOLD',
    'FUZZY_MATCH_MIN_LENGTH',
    'OUR_AUTHOR_PATTERNS',
    'COUNTERPARTY_PATTERNS',
    'register_tmp_dir',
    'cleanup_tmp_dirs',
    'setup_logging',
]
