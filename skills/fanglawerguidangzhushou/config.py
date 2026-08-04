#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
律师案件归档助手 - 配置文件
脱敏版本：不含任何个人敏感信息
"""

import os
from pathlib import Path

# ════════════════════════════════════════════════════════════════════
# 基础配置
# ════════════════════════════════════════════════════════════════════

# Python解释器路径（根据实际环境调整）
PYTHON_BIN = r"python"  # 修改为您的 Python 解释器路径

# ════════════════════════════════════════════════════════════════════
# 归档卷宗模板
# ════════════════════════════════════════════════════════════════════

# 模板文件路径（需要根据实际模板位置修改）
TEMPLATE_PATH = Path(r"模板目录/归档卷宗模板（民事）.docx")

# ════════════════════════════════════════════════════════════════════
# OCR配置
# ════════════════════════════════════════════════════════════════════

# 线程限制（防止CPU爆表）
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")

# 图片预处理参数
MAX_SIDE = 1500  # 最大边长，超过则等比缩放
CLAHE_CLIP = 2.0  # CLAHE对比度增强参数
CLAHE_TILE = (8, 8)  # CLAHE分块大小

# 支持的图片格式
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}

# OCR超时（秒）
OCR_TIMEOUT = 30

# ════════════════════════════════════════════════════════════════════
# 输出配置
# ════════════════════════════════════════════════════════════════════

# 默认律师（修改为您的姓名）
DEFAULT_LAWYER = "您的姓名"

# 默认代理阶段
DEFAULT_STAGE = "1审"

# 默认密级
DEFAULT_SECRET = "机密"

# 默认保管期限
DEFAULT_ARCHIVE_PERIOD = "长期"

# 默认归档日期
DEFAULT_ARCHIVE_DATE = "2026年    月    日"

# ════════════════════════════════════════════════════════════════════
# 邮件/通知配置（如需启用）
# ════════════════════════════════════════════════════════════════════

# 邮件配置（脱敏示例）
EMAIL_CONFIG = {
    'smtp_server': 'smtp.163.com',
    'smtp_port': 465,
    'sender_email': 'your_email@163.com',  # 修改为实际邮箱
    'sender_password': 'your_smtp_password',  # 修改为实际授权码
    'receiver_email': 'receiver@qq.com',  # 修改为实际收件人
}

# 微信推送配置（脱敏示例）
WECHAT_CONFIG = {
    'enabled': False,  # 默认关闭
    'wxpusher_enabled': False,
    'wxpusher_apptoken': '',  # 修改为实际token
    'wxpusher_uids': [],  # 修改为实际UID
}

# ════════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════════

def get_default_case_info():
    """获取默认案件信息"""
    return {
        'lawyer': DEFAULT_LAWYER,
        'stage': DEFAULT_STAGE,
        'secret': DEFAULT_SECRET,
        'archive_date': DEFAULT_ARCHIVE_DATE,
        'pages': '0',
        'catalog': [
            '民事诉讼委托代理合同风险告知书',
            '民事诉讼委托代理合同',
            '授权委托书',
            '收费凭证',
            '起诉书/答辩状',
            '证据材料',
            '判决书/调解书',
            '办案小结',
        ]
    }


def validate_template():
    """验证模板文件是否存在"""
    if not TEMPLATE_PATH.exists():
        print(f"[警告] 模板文件不存在: {TEMPLATE_PATH}")
        print("[提示] 请修改 config.py 中的 TEMPLATE_PATH")
        return False
    return True


if __name__ == "__main__":
    print("律师案件归档助手配置")
    print(f"模板路径: {TEMPLATE_PATH}")
    print(f"模板存在: {TEMPLATE_PATH.exists()}")
    print(f"默认律师: {DEFAULT_LAWYER}")