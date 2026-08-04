"""PIPL 护栏规则库。
每个规则 profile 是一个模块，导出 PATTERNS / KEYWORDS / PROFILE 三个对象。
内核通过显式映射加载，不使用动态 import，便于安全审计。
"""
