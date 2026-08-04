"""Shared clause-family ontology for package review and evaluation."""

from __future__ import annotations


CLAUSE_FAMILIES = {
    "definitions": ["定义", "释义", "definitions", "interpretation"],
    "closing_conditions": ["先决条件", "交割条件", "conditions precedent", "closing conditions"],
    "preemptive_right": ["优先认购", "preemptive right", "pre-emption right"],
    "rofr": ["优先购买", "right of first refusal", "rofr"],
    "co_sale": ["共同出售", "随售", "co-sale", "tag-along"],
    "drag_along": ["领售", "拖售", "drag-along", "drag along"],
    "redemption": ["回购", "赎回", "redemption"],
    "anti_dilution": ["反稀释", "anti-dilution", "anti dilution"],
    "liquidation_preference": ["清算优先", "优先分配", "liquidation preference"],
    "protective_provisions": ["保护性条款", "保留事项", "否决权", "reserved matters", "protective provisions"],
    "board": ["董事会", "董事委派", "board", "director appointment"],
    "information_rights": ["信息权", "检查权", "查阅权", "information rights", "inspection rights"],
    "founder_restrictions": ["创始股东限制", "创始人限制", "竞业限制", "founder restrictions", "vesting"],
    "representations_warranties": ["陈述与保证", "representations and warranties", "warranties"],
    "indemnity": ["赔偿责任", "违约赔偿", "损害赔偿", "indemnity", "indemnification"],
    "investor_transfer": ["投资人转让", "投资者转让", "investor transfer"],
    "registered_capital": ["注册资本", "认缴", "实缴", "出资期限", "registered capital", "capital contribution"],
    "esop": ["股权激励", "员工持股", "期权池", "esop", "option pool"],
    "confidentiality_data": ["保密", "个人信息", "数据", "confidentiality", "personal information", "data"],
    "governing_law_dispute": ["适用法律", "争议解决", "仲裁", "人民法院", "governing law", "arbitration", "court"],
    "document_priority": ["文件效力", "冲突", "优先适用", "document priority", "prevail", "conflict"],
}
