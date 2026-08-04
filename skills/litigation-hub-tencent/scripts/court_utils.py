#!/usr/bin/env python3
"""
法院案卷通用工具模块。
提供: 未处理文件追踪、文件归类、提醒合并/升级。

用法:
  from court_utils import PendingTracker, categorize_file, merge_reminders
"""

import json
import os
from datetime import datetime

PENDING_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            'references', 'pending-items.json')


class PendingTracker:
    """未处理/未归类文件追踪"""

    @staticmethod
    def load():
        if not os.path.exists(PENDING_FILE):
            return {"items": [], "updated": ""}
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save(data):
        data['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        os.makedirs(os.path.dirname(PENDING_FILE), exist_ok=True)
        with open(PENDING_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def add(file_path, reason="未归类", meta=None):
        data = PendingTracker.load()
        # 去重
        for item in data['items']:
            if item.get('file') == os.path.basename(file_path):
                return
        data['items'].append({
            "file": os.path.basename(file_path),
            "path": file_path,
            "reason": reason,
            "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "meta": meta or {},
        })
        PendingTracker.save(data)

    @staticmethod
    def remove(file_path):
        data = PendingTracker.load()
        data['items'] = [i for i in data['items'] if i.get('file') != os.path.basename(file_path)]
        PendingTracker.save(data)

    @staticmethod
    def get_pending():
        data = PendingTracker.load()
        return data.get('items', [])

    @staticmethod
    def count():
        return len(PendingTracker.get_pending())

    @staticmethod
    def summary():
        items = PendingTracker.get_pending()
        if not items:
            return None
        lines = [f"📋 你有 {len(items)} 个未处理的文件："]
        for item in items:
            lines.append(f"   · {item['file']} — {item['reason']}")
        return '\n'.join(lines)


# ============================================================
#  文件归类增强
# ============================================================

# 关键词 → 子目录映射（法院文书以外）
FILE_CATEGORY_MAP = {
    # 02 我方提交资料
    "02 我方提交资料": [
        "起诉状", "答辩状", "代理词", "代理意见", "证据清单",
        "证据目录", "质证意见", "辩论意见", "上诉状", "申诉状",
        "复议申请", "异议申请", "追加当事人", "变更诉讼请求",
    ],
    # 03 对方提交资料
    "03 对方提交资料": [
        "对方", "被告提交", "原告提交",
    ],
    # 04 案件原始材料
    "04 案件原始材料": [
        "合同", "协议", "借条", "欠条", "收据", "发票",
        "银行流水", "转账记录", "聊天记录", "通话记录",
    ],
    # 05 律师工作文本
    "05 律师工作文本": [
        "法律意见", "分析报告", "庭审提纲", "备忘录",
        "工作记录", "办案小结", "案件评估",
    ],
    # 06 委托签署材料
    "06 委托签署材料": [
        "委托代理合同", "授权委托书", "风险告知书", "委托书",
        "代理合同", "法律服务合同",
    ],
    # 07 邮件收寄记录
    "07 邮件收寄记录": [
        "邮件", "快递", "EMS", "邮寄", "签收",
    ],
    # 08 法规类案检索
    "08 法规类案检索": [
        "法规", "司法解释", "类案", "检索报告", "法律检索",
        "判例", "指导案例",
    ],
    # 09 法院庭审笔录
    "09 法院庭审笔录": [
        "庭审笔录", "听证笔录", "勘验笔录", "调解笔录",
    ],
    # 10 案件保全资料
    "10 案件保全资料": [
        "保全", "冻结", "查封", "扣押", "担保",
        "保函", "保险",
    ],
}


def categorize_non_court_file(filename, content_preview=""):
    """
    对非法院文书进行归类。
    返回子目录名（如 "02 我方提交资料"）或 None。
    """
    text = filename + " " + content_preview

    # 去数字前缀
    clean = filename
    for prefix in ['01-', '02-', '03-', '04-', '05-', '06-', '07-', '08-', '09-', '10-']:
        if clean.startswith(prefix):
            clean = clean[3:]
            break

    for category, keywords in FILE_CATEGORY_MAP.items():
        for kw in keywords:
            if kw in text or kw in clean:
                return category
    return None


# ============================================================
#  提醒合并
# ============================================================

def merge_same_day_reminders(items):
    """
    合并同一天的提醒为一条复合提醒。
    items: list of {case_no, case_type, label, before_days, ...}
    返回合并后的列表。
    """
    if len(items) <= 1:
        return items

    # 按日期分组
    grouped = {}
    for item in items:
        key = (item.get('case_no', ''), item.get('before_days', 0))
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(item)

    merged = []
    for key, group in grouped.items():
        if len(group) == 1:
            merged.append(group[0])
        else:
            # 合并：取第一个的 meta，拼接标签
            base = dict(group[0])
            labels = [g['label'] for g in group]
            base['label'] = ' · '.join(labels)
            base['_merged_count'] = len(group)
            merged.append(base)
    return merged


# ============================================================
#  提醒升级
# ============================================================

ESCALATION_LEVELS = {
    "critical": {"emoji": "🚨🚨", "tone": "紧急"},
    "warning": {"emoji": "⚠️", "tone": "注意"},
    "info": {"emoji": "ℹ️", "tone": "提醒"},
}


def escalate_reminder_level(label, event_type, days_remaining):
    """
    根据剩余天数和提醒类型升级提醒强度。
    保全到期 < 7天 → 最高级别。
    """
    if '保全' in event_type or '冻结' in event_type or '查封' in event_type:
        if days_remaining <= 7:
            return 'critical'
        elif days_remaining <= 14:
            return 'warning'
    return 'warning'  # default


# ============================================================
#  桌面 Markdown 提醒文件生成（本机电脑提醒渠道）
# ============================================================

def generate_desktop_md_reminder(title, lines, filename_hint="提醒", subfolder=None):
    """
    在桌面生成 Markdown 提醒文件（本机电脑提醒渠道的持久化部分）。
    不依赖系统通知是否弹出，用户回到桌面即可看到，是"本机电脑提醒"的兜底。

    参数:
      title:         Markdown 一级标题，如 "⚠️ 开庭提醒"
      lines:         Markdown 正文行列表（不含标题）
      filename_hint: 文件名前缀（建议含日期时间，避免互相覆盖），如 "开庭提醒_2026-07-09_0930"
      subfolder:     可选，桌面下的子文件夹名；为 None 时直接放桌面根

    返回:
      生成的 .md 文件路径
    """
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    target_dir = os.path.join(desktop, subfolder) if subfolder else desktop
    os.makedirs(target_dir, exist_ok=True)

    # 清理文件名非法字符（macOS/Windows）
    safe_hint = "".join(c for c in filename_hint if c not in '/\\:*?"<>|')
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"# {title}\n\n" + "\n".join(lines) + f"\n\n> 本提醒由 诉讼信息中枢系统 自动生成（{ts}）\n"
    path = os.path.join(target_dir, f"{safe_hint}.md")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(md)
    return path
