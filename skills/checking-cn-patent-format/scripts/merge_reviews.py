#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审查意见合并、去重与修订冲突解决 - 一体化脚本

功能：
1. 合并所有 Agent 的审查意见 JSON 文件
2. 多策略去重（精确、语义、包含、issue语义、跨章节vs单章节、位置邻近）
3. 修订冲突检测与解决
4. 输出最终合并结果

用法：
    python merge_reviews.py --work-dir "<work_dir>" --timestamp "<timestamp>" --output "<work_dir>/reviews_<timestamp>.json"
"""

# sys 提供系统相关功能，如退出程序
import sys
# json 用于读写 JSON 格式文件
import json
# argparse 用于解析命令行参数
import argparse
# Path 用于面向对象的文件路径处理
from pathlib import Path
# glob 用于文件模式匹配（如 reviews_agent*_*.json）
from glob import glob
# deepcopy 用于深拷贝对象
from copy import deepcopy
# unicodedata 用于Unicode规范化（解决Agent输出Unicode转义序列问题）
import unicodedata
# re 提供正则表达式支持
import re


# ===================== Unicode规范化预处理（BUG-001修复）=====================

KNOWN_VARIANT_CHARS = {
    '\u6c03': '\u6be1',
    '\u6c04': '\u6be1',
    '\u6c02': '\u6be1',
}

TEXT_FIELDS = ['issue', 'suggestion', 'context', 'highlight_text',
               'old_text', 'new_text']


def _normalize_unicode_text(text):
    """
    对文本执行Unicode规范化处理。

    处理步骤：
    1. NFC规范化（组合字符统一）
    2. 已知异体字/形近字纠错

    注意：json.load()已自动将JSON中的\\uXXXX转义序列解码为实际Unicode字符，
    因此此处不需要手动解码转义序列。异体字纠错是核心修复步骤。

    Args:
        text: 待规范化的文本字符串

    Returns:
        规范化后的文本字符串
    """
    if not text or not isinstance(text, str):
        return text

    original = text

    text = unicodedata.normalize('NFC', text)

    corrected = []
    for ch in text:
        if ch in KNOWN_VARIANT_CHARS:
            corrected.append(KNOWN_VARIANT_CHARS[ch])
        else:
            corrected.append(ch)
    text = ''.join(corrected)

    if text != original:
        diff_chars = []
        for i, (a, b) in enumerate(zip(original, text)):
            if a != b:
                diff_chars.append(f"U+{ord(a):04X}->U+{ord(b):04X}")
        if len(original) != len(text):
            diff_chars.append(f"len:{len(original)}->{len(text)}")
        if diff_chars:
            print(f"    [Unicode规范化] 修正: {', '.join(diff_chars[:5])}")

    return text


def _normalize_review_item(item):
    """
    对单条审查意见的所有文本字段执行Unicode规范化。

    Args:
        item: 审查意见字典

    Returns:
        规范化后的审查意见字典（原地修改）
    """
    for field in TEXT_FIELDS:
        if field in item and item[field] is not None and isinstance(item[field], str):
            item[field] = _normalize_unicode_text(item[field])
    return item


def normalize_agent_output(data):
    """
    对Agent输出的整个审查意见列表执行Unicode规范化预处理。

    在合并前调用，确保所有Agent输出的JSON中的中文文本使用统一的
    UTF-8编码而不含转义序列，并修正已知异体字。

    Args:
        data: 审查意见列表

    Returns:
        规范化后的审查意见列表（原地修改）
    """
    if not isinstance(data, list):
        return data

    normalized_count = 0
    for item in data:
        if isinstance(item, dict):
            old_issue = item.get('issue', '')
            _normalize_review_item(item)
            if item.get('issue', '') != old_issue:
                normalized_count += 1

    if normalized_count > 0:
        print(f"Unicode normalization: {normalized_count} items had text corrections")

    return data


def _rewrite_json_with_formatting(file_path):
    """
    重新格式化JSON文件，使用indent=2和ensure_ascii=False。

    解决Agent通过Write工具输出单行JSON的问题（BUG修复）。
    仅在文件为单行或格式不规范时才重写。

    Args:
        file_path: JSON文件路径
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        needs_rewrite = False

        lines = raw_content.strip().split('\n')
        if len(lines) <= 3:
            needs_rewrite = True

        if not needs_rewrite:
            for line in lines[:5]:
                if len(line) > 500:
                    needs_rewrite = True
                    break

        if needs_rewrite:
            data = json.loads(raw_content)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"    [格式化] 已重写 {Path(file_path).name} 为标准缩进格式")
    except (json.JSONDecodeError, Exception):
        pass


def load_reviews(file_path):
    """从 JSON 文件加载审查意见列表。"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_reviews(reviews, file_path):
    """将审查意见列表保存为 JSON 文件。"""
    output_path = Path(file_path)
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)


def merge_all_agent_files(work_dir, pattern="reviews_agent*_*.json"):
    """
    合并所有 Agent 的审查意见。

    通过 glob 模式匹配查找所有 Agent 输出的 JSON 文件，
    将它们的内容合并为一个列表。
    """
    # 构建搜索模式路径
    search_pattern = str(work_dir / pattern)
    # 查找所有匹配的文件并排序
    matched_files = sorted(glob(search_pattern))

    files_found = len(matched_files)
    files_merged = 0
    files_skipped = 0
    merged_reviews = []
    agent_counts = {}

    # 遍历所有匹配到的文件
    for file_path_str in matched_files:
        file_path = Path(file_path_str)
        try:
            # 打开并解析 JSON 文件
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 确保数据是列表格式
            if isinstance(data, list):
                # 【BUG-001修复】Unicode规范化预处理：解码转义序列、NFC规范化、异体字纠错
                normalize_agent_output(data)
                # 【BUG修复】重写单行JSON为标准缩进格式
                _rewrite_json_with_formatting(file_path_str)
                merged_reviews.extend(data)
                agent_counts[file_path.name] = len(data)
                files_merged += 1
            else:
                print(f"Warning: {file_path.name} does not contain a JSON array, skipping")
                files_skipped += 1
        except FileNotFoundError:
            print(f"Warning: {file_path.name} not found, skipping")
            files_skipped += 1
        except json.JSONDecodeError as e:
            print(f"Warning: {file_path.name} could not be parsed as JSON ({e}), skipping")
            files_skipped += 1
        except Exception as e:
            print(f"Warning: {file_path.name} could not be read ({e}), skipping")
            files_skipped += 1

    # 打印合并统计信息
    print(f"Files found: {files_found}")
    print(f"Files merged: {files_merged}")
    print(f"Files skipped: {files_skipped}")
    print(f"Agent counts: {agent_counts}")
    print(f"Total reviews before dedup: {len(merged_reviews)}")

    return merged_reviews, agent_counts, files_found, files_merged, files_skipped


def _get(item, field):
    """安全地获取字典字段值。"""
    return item.get(field)


# ===================== 去重日志记录系统（调试与分析功能）=====================

class DeduplicationLog:
    """
    去重操作日志记录器 - 用于详细记录每种去重策略去除的条目信息。

    功能：
    1. 记录每种去重策略的去除详情（被去除条目、保留条目、去除原因）
    2. 支持输出为JSON格式日志文件，便于后续分析和调试
    3. 提供统计摘要功能，快速了解各策略的去重效果

    日志数据结构：
    {
        "timestamp": "ISO格式时间戳",
        "summary": {
            "total_reviews_before": int,
            "total_reviews_after": int,
            "total_removed": int,
            "strategies_used": [str]
        },
        "strategy_details": [
            {
                "strategy_name": str,
                "removed_count": int,
                "removed_items": [
                    {
                        "removed_index": int,          # 被去除条目的原始索引
                        "kept_index": int,              # 保留条目的原始索引
                        "removed_item_summary": {       # 被去除条目的关键信息
                            "section": str,
                            "paragraph_index": int|null,
                            "action_type": str,
                            "issue": str,
                            "context_preview": str      # context前80字符
                        },
                        "kept_item_summary": {           # 保留条目的关键信息
                            "section": str,
                            "paragraph_index": int|null,
                            "action_type": str,
                            "issue": str,
                            "context_preview": str
                        },
                        "removal_reason": str            # 去除原因说明
                    }
                ]
            }
        ]
    }
    """

    def __init__(self):
        """初始化日志记录器。"""
        from datetime import datetime
        self.timestamp = datetime.now().isoformat()
        self.strategy_logs = []
        self._current_strategy = None

    def start_strategy(self, strategy_name):
        """
        开始记录某个去重策略的操作。

        Args:
            strategy_name: 策略名称（如"精确去重"、"位置邻近去重"等）
        """
        self._current_strategy = {
            "strategy_name": strategy_name,
            "removed_count": 0,
            "removed_items": []
        }
        return self

    def log_removal(self, removed_idx, kept_idx, removed_item, kept_item, reason=""):
        """
        记录一次去重操作。

        Args:
            removed_idx: 被去除条目的原始索引
            kept_idx: 保留条目的原始索引
            removed_item: 被去除的完整审查意见字典
            kept_item: 保留的完整审查意见字典
            reason: 去除原因说明（可选）
        """
        if self._current_strategy is None:
            raise ValueError("必须先调用 start_strategy() 开始一个策略")

        # 提取关键信息用于日志（避免存储完整内容导致文件过大）
        removal_entry = {
            "removed_index": removed_idx,
            "kept_index": kept_idx,
            "removed_item_summary": {
                "section": _get(removed_item, 'section'),
                "paragraph_index": _get(removed_item, 'paragraph_index'),
                "action_type": _get(removed_item, 'action_type'),
                "issue": _get(removed_item, 'issue'),
                "context_preview": (_get(removed_item, 'context') or '')[:80],
                "suggestion_preview": (_get(removed_item, 'suggestion') or '')[:80]
            },
            "kept_item_summary": {
                "section": _get(kept_item, 'section'),
                "paragraph_index": _get(kept_item, 'paragraph_index'),
                "action_type": _get(kept_item, 'action_type'),
                "issue": _get(kept_item, 'issue'),
                "context_preview": (_get(kept_item, 'context') or '')[:80],
                "suggestion_preview": (_get(kept_item, 'suggestion') or '')[:80]
            },
            "removal_reason": reason or f"被{self._current_strategy['strategy_name']}策略判定为重复"
        }

        self._current_strategy["removed_items"].append(removal_entry)
        self._current_strategy["removed_count"] += 1

    def end_strategy(self):
        """结束当前策略的记录。"""
        if self._current_strategy:
            self.strategy_logs.append(self._current_strategy)
            self._current_strategy = None
        return self

    def generate_log(self, original_count, final_count):
        """
        生成完整的去重日志数据结构。

        Args:
            original_count: 去重前的总条目数
            final_count: 去重后的总条目数

        Returns:
            dict: 完整的日志数据结构
        """
        total_removed = sum(log["removed_count"] for log in self.strategy_logs)

        return {
            "timestamp": self.timestamp,
            "summary": {
                "total_reviews_before": original_count,
                "total_reviews_after": final_count,
                "total_removed": total_removed,
                "removal_rate": round(total_removed / original_count * 100, 2) if original_count > 0 else 0,
                "strategies_used": [log["strategy_name"] for log in self.strategy_logs]
            },
            "strategy_details": self.strategy_logs
        }

    def save_to_file(self, file_path, original_count, final_count):
        """
        将日志保存为JSON文件。

        Args:
            file_path: 输出文件路径
            original_count: 去重前的总条目数
            final_count: 去重后的总条目数
        """
        log_data = self.generate_log(original_count, final_count)
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        print(f"Deduplication log saved to: {output_path}")
        print(f"Total removals logged: {log_data['summary']['total_removed']}")
        return output_path

    def print_summary(self, original_count, final_count):
        """
        打印去重操作的统计摘要到控制台。

        Args:
            original_count: 去重前的总条目数
            final_count: 去重后的总条目数
        """
        log_data = self.generate_log(original_count, final_count)
        summary = log_data['summary']

        print("\n" + "="*70)
        print("📊 去重操作详细日志 (Deduplication Log Summary)")
        print("="*70)
        print(f"⏰ 时间戳: {log_data['timestamp']}")
        print(f"📥 去重前总数: {summary['total_reviews_before']}")
        print(f"📤 去重后总数: {summary['total_reviews_after']}")
        print(f"🗑️  总去除数: {summary['total_removed']} ({summary['removal_rate']}%)")
        print("-"*70)

        for detail in log_data['strategy_details']:
            print(f"\n✂️  {detail['strategy_name']}:")
            print(f"   去除数量: {detail['removed_count']}")

            if detail['removed_count'] > 0 and len(detail['removed_items']) <= 5:
                # 如果数量较少，显示所有详情
                for i, item in enumerate(detail['removed_items'], 1):
                    print(f"\n   📌 去除项 #{i}:")
                    print(f"      索引: [{item['removed_index']}] → 保留 [{item['kept_index']}]")
                    print(f"      Section: {item['removed_item_summary']['section']}")
                    print(f"      段落: {item['removed_item_summary']['paragraph_index']}")
                    print(f"      类型: {item['removed_item_summary']['action_type']}")
                    issue = item['removed_item_summary']['issue']
                    print(f"      Issue: {issue[:60]}..." if len(issue) > 60 else f"      Issue: {issue}")
                    print(f"      Context: {item['removed_item_summary']['context_preview'][:50]}...")
                    print(f"      原因: {item['removal_reason']}")
            elif detail['removed_count'] > 5:
                # 如果数量较多，只显示前3个和统计信息
                for i, item in enumerate(detail['removed_items'][:3], 1):
                    print(f"\n   📌 去除项 #{i} (示例):")
                    print(f"      索引: [{item['removed_index']}] → 保留 [{item['kept_index']}]")
                    print(f"      Section: {item['removed_item_summary']['section']}")
                    issue = item['removed_item_summary']['issue']
                    print(f"      Issue: {issue[:60]}..." if len(issue) > 60 else f"      Issue: {issue}")
                    print(f"      原因: {item['removal_reason']}")
                print(f"\n   ... 还有 {detail['removed_count'] - 3} 条未显示（详见日志文件）")

        print("\n" + "="*70)


# ===================== 去重逻辑 =====================

def is_exact_duplicate(item1, item2):
    """
    精确去重：context、issue 和 old_text 完全相同。
    如果 context 和 old_text 都为 None，则只比较 issue。
    """
    ctx1 = _get(item1, 'context')
    ctx2 = _get(item2, 'context')
    issue1 = _get(item1, 'issue')
    issue2 = _get(item2, 'issue')
    old1 = _get(item1, 'old_text')
    old2 = _get(item2, 'old_text')

    if ctx1 == ctx2 and issue1 == issue2 and old1 == old2:
        return True
    if ctx1 is None and ctx2 is None and old1 is None and old2 is None and issue1 == issue2:
        return True
    return False


def is_semantic_duplicate(item1, item2):
    """
    语义去重：old_text 相同且非 null，section 相同，claim_number 相同，
    且 context 也相同或高度相似。
    
    关键约束：同一 old_text 可能出现在文档的不同位置（不同 context），
    此时它们是不同的审查意见，不应去重。只有当 context 也相同时，
    才说明两个 Agent 对同一处文本提出了相同的修改建议。
    """
    old1 = _get(item1, 'old_text')
    old2 = _get(item2, 'old_text')
    if old1 is None or old2 is None:
        return False
    if old1 != old2:
        return False
    if _get(item1, 'section') != _get(item2, 'section'):
        return False
    if _get(item1, 'claim_number') != _get(item2, 'claim_number'):
        return False
    ctx1 = _get(item1, 'context') or ''
    ctx2 = _get(item2, 'context') or ''
    if ctx1 and ctx2:
        if ctx1 == ctx2:
            return True
        if ctx1 in ctx2 or ctx2 in ctx1:
            return True
        if _ngram_overlap_ratio(ctx1, ctx2, 4) >= 0.7:
            return True
        return False
    return True


def is_containment_duplicate(item1, item2):
    """
    包含去重：一条的 old_text 是另一条的子串，且 section 相同，且 context 也相同或高度相似。
    返回 (要删除的项, 要保留的项)，保留 old_text 更长的那条。
    
    关键约束：如果两条意见的 context 不同，说明它们位于文档的不同位置，
    即使 old_text 有包含关系也不应去重（它们修改的是不同位置的文本）。
    """
    old1 = _get(item1, 'old_text')
    old2 = _get(item2, 'old_text')
    if old1 is None or old2 is None:
        return None, None
    if _get(item1, 'section') != _get(item2, 'section'):
        return None, None
    ctx1 = _get(item1, 'context') or ''
    ctx2 = _get(item2, 'context') or ''
    if ctx1 and ctx2:
        if ctx1 != ctx2 and ctx1 not in ctx2 and ctx2 not in ctx1:
            if _ngram_overlap_ratio(ctx1, ctx2, 4) < 0.7:
                return None, None
    if old1 == old2:
        return item2, item1
    if old1 in old2:
        return item1, item2
    if old2 in old1:
        return item2, item1
    return None, None


def _ngram_overlap_ratio(text1, text2, n=4):
    """
    计算 n-gram 重叠率。
    
    将文本拆分为连续 n 个字符的子串（n-gram），计算两个文本的
    n-gram 集合的 Jaccard 相似度。相比字符集重叠，n-gram 能更好
    地捕捉文本的局部相似性，避免因共享常见汉字而误判。
    """
    if len(text1) < n or len(text2) < n:
        if text1 in text2 or text2 in text1:
            return 1.0
        return 0.0
    ngrams1 = set(text1[i:i+n] for i in range(len(text1) - n + 1))
    ngrams2 = set(text2[i:i+n] for i in range(len(text2) - n + 1))
    intersection = len(ngrams1 & ngrams2)
    union = len(ngrams1 | ngrams2)
    if union == 0:
        return 0.0
    return intersection / union


def _group_key(item):
    """
    生成分组键：(section, paragraph_index)。
    
    用于将审查意见按位置分组，组内进行预去重。
    paragraph_index 为 None 时使用 -1 作为占位符。
    """
    section = _get(item, 'section') or ''
    pi = _get(item, 'paragraph_index')
    return (section, pi if pi is not None else -1)


def pre_group_dedup(reviews, enable_logging=False):
    """
    预分组去重：按 (section, paragraph_index) 分组后，在组内进行
    基于issue关键词的快速预去重。
    
    此步骤在主去重流程之前执行，目的是在同一段落内快速识别
    语义高度相似的审查意见，减少后续去重的计算量。
    
    去重逻辑：
    1. 按 (section, paragraph_index) 分组
    2. 在每组内，对每对审查意见检查：
       a. old_text 相同（如果都有）→ 语义重复
       b. issue 包含相同的核心关键词（>=2个）且 context 高度重叠 → 语义重复
    3. 保留策略：优先保留 action_type 更具体的，其次保留 suggestion 更长的
    
    Args:
        reviews: 审查意见列表
        enable_logging: 是否启用日志记录
        
    Returns:
        tuple: (预去重后的列表, 去除数量, 日志对象或None)
    """
    if not reviews:
        return [], 0, None
    
    pre_dedup_log = DeduplicationLog() if enable_logging else None
    if pre_dedup_log:
        pre_dedup_log.start_strategy("预分组去重")
    
    groups = {}
    for idx, item in enumerate(reviews):
        key = _group_key(item)
        groups.setdefault(key, []).append(idx)
    
    to_remove = set()
    pre_dup_found = 0
    
    for key, indices in groups.items():
        if len(indices) <= 1:
            continue
        
        for i_pos in range(len(indices)):
            idx1 = indices[i_pos]
            if idx1 in to_remove:
                continue
            for j_pos in range(i_pos + 1, len(indices)):
                idx2 = indices[j_pos]
                if idx2 in to_remove:
                    continue
                
                item1 = reviews[idx1]
                item2 = reviews[idx2]
                
                old1 = _get(item1, 'old_text')
                old2 = _get(item2, 'old_text')
                
                is_dup = False
                reason = ""
                
                if old1 is not None and old2 is not None and old1 == old2:
                    is_dup = True
                    reason = f"同组内old_text相同: '{old1[:30]}...'" if len(str(old1)) > 30 else f"同组内old_text相同: '{old1}'"
                elif is_issue_similar(item1, item2):
                    ctx1 = _get(item1, 'context') or ''
                    ctx2 = _get(item2, 'context') or ''
                    if context_overlap_ratio(ctx1, ctx2, 0.6):
                        is_dup = True
                        reason = f"同组内issue同类且context重叠"
                
                if is_dup:
                    action_prio = {'replace': 3, 'delete': 2, 'comment': 1}
                    p1 = action_prio.get(_get(item1, 'action_type'), 0)
                    p2 = action_prio.get(_get(item2, 'action_type'), 0)
                    s1 = len(_get(item1, 'suggestion') or '')
                    s2 = len(_get(item2, 'suggestion') or '')
                    
                    if p1 > p2 or (p1 == p2 and s1 >= s2):
                        remove_idx = idx2
                        kept_idx = idx1
                    else:
                        remove_idx = idx1
                        kept_idx = idx2
                    
                    if remove_idx not in to_remove:
                        if pre_dedup_log:
                            pre_dedup_log.log_removal(
                                removed_idx=remove_idx,
                                kept_idx=kept_idx,
                                removed_item=reviews[remove_idx],
                                kept_item=reviews[kept_idx],
                                reason=reason
                            )
                        to_remove.add(remove_idx)
                        pre_dup_found += 1
    
    if pre_dedup_log:
        pre_dedup_log.end_strategy()
    
    result = [reviews[i] for i in range(len(reviews)) if i not in to_remove]
    
    if pre_dup_found > 0:
        print(f"Pre-group dedup: {len(reviews)} → {len(result)} ({pre_dup_found} pre-group duplicates removed)")
    
    if pre_dedup_log:
        pre_dedup_log.print_summary(len(reviews), len(result))
    
    return result, pre_dup_found, pre_dedup_log


def context_overlap_ratio(ctx1, ctx2, threshold=0.8):
    """
    检查 context 重叠率。
    
    使用 n-gram Jaccard 相似度代替字符集重叠率。
    字符集重叠率对中文文本不可靠（太多常见字导致误判），
    n-gram 能更好地反映文本的局部结构相似性。
    """
    if ctx1 is None or ctx2 is None:
        return False
    if ctx1 in ctx2 or ctx2 in ctx1:
        return True
    return _ngram_overlap_ratio(ctx1, ctx2, 4) >= threshold


def is_issue_similar(item1, item2):
    """
    检查 issue 是否描述同一类问题。
    通过检查是否包含相同的关键词来判断。
    要求至少有 2 个共同关键词才判定为同类问题，
    避免仅因共享泛关键词（如'权利要求'）而误判。
    """
    issue1 = (_get(item1, 'issue') or '')
    issue2 = (_get(item2, 'issue') or '')
    if not issue1 or not issue2:
        return False
    keywords = ['CPU', '排油口', '引用', '权利要求', '摘要', '说明书', '格式',
                '标点', '缺少', '错误', '所述', '主题', '附图', '发明名称',
                '技术领域', '商业', '重复', '不一致', '用语', '错别字',
                '公开不充分', '单一性', '保护范围', '具体数值', '择一']
    shared = sum(1 for kw in keywords if kw in issue1 and kw in issue2)
    return shared >= 2


def is_issue_semantic_duplicate(item1, item2):
    """
    issue语义去重：context 重叠 + section 相同 + claim_number 相同 + issue 同类。
    返回 (要删除的项, 要保留的项)，优先保留 action_type 更具体或 suggestion 更长的。
    
    关键约束：如果两条意见都有非 null 的 old_text 且 old_text 不同，
    说明它们修改的是同一 context 内的不同文本位置，不应去重。
    例如同一权利要求中"碳毡电极主体"缺"所述"和"第一表面"缺"所述"
    是两个不同的修改操作，都必须保留。
    """
    if _get(item1, 'section') != _get(item2, 'section'):
        return None, None
    if _get(item1, 'claim_number') != _get(item2, 'claim_number'):
        return None, None
    old1 = _get(item1, 'old_text')
    old2 = _get(item2, 'old_text')
    if old1 is not None and old2 is not None and old1 != old2:
        return None, None
    if not context_overlap_ratio(_get(item1, 'context'), _get(item2, 'context')):
        return None, None
    if not is_issue_similar(item1, item2):
        return None, None
    action_prio = {'replace': 2, 'delete': 2, 'comment': 1}
    p1 = action_prio.get(_get(item1, 'action_type'), 0)
    p2 = action_prio.get(_get(item2, 'action_type'), 0)
    s1 = len(_get(item1, 'suggestion') or '')
    s2 = len(_get(item2, 'suggestion') or '')
    if p1 > p2:
        return item2, item1
    if p2 > p1:
        return item1, item2
    if s1 < s2:
        return item1, item2
    return item2, item1


def is_cross_chapter_vs_single_duplicate(item1, item2):
    """
    跨章节与单章节去重：同一问题被单章节Agent和跨章节Agent同时报告。

    增加约束：
    1. claim_number 必须相同（都为 null 或都为同一整数）
    2. 如果两条意见都有非 null 的 old_text 且 old_text 不同，不去重
    """
    s1 = _get(item1, 'section')
    s2 = _get(item2, 'section')
    if s1 != s2:
        return None, None
    cn1 = _get(item1, 'claim_number')
    cn2 = _get(item2, 'claim_number')
    if cn1 != cn2:
        return None, None
    old1 = _get(item1, 'old_text')
    old2 = _get(item2, 'old_text')
    if old1 is not None and old2 is not None and old1 != old2:
        return None, None
    if not is_issue_similar(item1, item2):
        return None, None
    ctx1 = _get(item1, 'context') or ''
    ctx2 = _get(item2, 'context') or ''
    if not (ctx1 in ctx2 or ctx2 in ctx1 or context_overlap_ratio(ctx1, ctx2, 0.5)):
        return None, None
    action_prio = {'replace': 2, 'delete': 2, 'comment': 1}
    p1 = action_prio.get(_get(item1, 'action_type'), 0)
    p2 = action_prio.get(_get(item2, 'action_type'), 0)
    if p1 >= p2:
        return item2, item1
    return item1, item2


def is_positional_proximity_duplicate(item1, item2):
    """
    位置邻近去重（P1优化，2026-05-10新增）：检测同一段落中相近位置的相似审查意见。

    适用场景：
    - 多个Agent对同一段落（paragraph_index相差<=2）中的相近文本提出了相似的审查意见
    - 这些意见可能是对同一问题的不同表述、不同侧重点或不同程度的详细说明
    - 例如：Agent A指出"第3段缺少所述"，Agent B指出"第3段用语不规范需补充所述"

    判定条件（必须全部满足）：
    1. section相同
    2. paragraph_index相近（差距<=2，或都为None但context高度重叠）
    3. issue描述的是同类问题（使用is_issue_similar判断）
    4. context有较高的文本重叠（n-gram重叠率>=0.6）

    排除条件（任一满足则不去重）：
    - 两条意见都有非null的old_text且old_text不同（说明修改的是不同文本位置）
    - 一条是replace/delete，另一条是comment，且comment包含unique信息（如具体的格式错误细节）

    返回值：
    - (to_delete, to_keep)：要删除和要保留的项
    - (None, None)：不构成位置邻近重复

    保留策略：
    1. 优先保留action_type更具体的（replace > delete > comment）
    2. 如果action_type相同，保留suggestion更长的（信息量更大）
    3. 如果仍相同，保留paragraph_index较小的（靠前的通常更具体）
    """
    # 条件1：section必须相同
    if _get(item1, 'section') != _get(item2, 'section'):
        return None, None

    # 条件2：paragraph_index相近
    pi1 = _get(item1, 'paragraph_index')
    pi2 = _get(item2, 'paragraph_index')

    if pi1 is not None and pi2 is not None:
        # 都有paragraph_index，检查是否相近（差距<=2）
        if abs(pi1 - pi2) > 2:
            return None, None
    elif pi1 is not None or pi2 is not None:
        # 一个有一个没有，不视为位置邻近
        return None, None
    else:
        # 都没有paragraph_index，依赖context重叠判断
        ctx1 = _get(item1, 'context') or ''
        ctx2 = _get(item2, 'context') or ''
        if not context_overlap_ratio(ctx1, ctx2, 0.7):
            return None, None

    # 排除条件：如果两条意见的old_text都非null且不同，说明修改的是不同位置
    old1 = _get(item1, 'old_text')
    old2 = _get(item2, 'old_text')
    if old1 is not None and old2 is not None and old1 != old2:
        return None, None

    # 条件3：issue必须是同类问题
    if not is_issue_similar(item1, item2):
        return None, None

    # 条件4：context必须有较高重叠
    ctx1 = _get(item1, 'context') or ''
    ctx2 = _get(item2, 'context') or ''
    if not context_overlap_ratio(ctx1, ctx2, 0.6):
        return None, None

    # 确定保留策略
    action_prio = {'replace': 3, 'delete': 2, 'comment': 1}
    p1 = action_prio.get(_get(item1, 'action_type'), 0)
    p2 = action_prio.get(_get(item2, 'action_type'), 0)

    # 优先保留action_type更具体的
    if p1 > p2:
        return item2, item1
    if p2 > p1:
        return item1, item2

    # action_type相同，保留suggestion更长的
    s1 = len(_get(item1, 'suggestion') or '')
    s2 = len(_get(item2, 'suggestion') or '')
    if s1 > s2:
        return item2, item1
    if s2 > s1:
        return item1, item2

    # 都相同，保留paragraph_index较小的
    if pi1 is not None and pi2 is not None:
        if pi1 <= pi2:
            return item2, item1
        else:
            return item1, item2

    # 最终fallback：保留第一个
    return item2, item1


def deduplicate(reviews, enable_logging=False):
    """
    执行所有去重策略。

    按顺序执行：
    1. 精确去重
    2. 语义去重
    3. 包含去重
    4. issue语义去重
    5. 跨章节vs单章节去重
    6. 位置邻近去重（P1优化，2026-05-10新增）

    Args:
        reviews: 审查意见列表
        enable_logging: 是否启用详细日志记录（默认False以保持向后兼容）

    Returns:
        tuple: (去重后的列表, 去除数量, 日志对象或None)
    """
    original_count = len(reviews)
    if original_count == 0:
        return [], 0, None

    # 初始化日志记录器（如果启用）
    dedup_log = DeduplicationLog() if enable_logging else None

    indices = list(range(original_count))
    to_remove = set()
    dup_found = 0

    # 简单去重步骤（直接比较，返回 bool）
    # 【BUG-007修复】增加context精确匹配作为最高优先级去重策略
    # 当两条review的context完全相同时（无论issue措辞是否不同），
    # 它们针对的是文档中同一位置，应优先考虑去重
    dedup_steps = [
        ("context精确匹配", None),  # 特殊处理，内联逻辑
        ("精确去重", is_exact_duplicate),
        ("语义去重", is_semantic_duplicate),
    ]

    for step_name, fn in dedup_steps:
        if dedup_log:
            dedup_log.start_strategy(step_name)

        remaining = [i for i in indices if i not in to_remove]

        # 【BUG-007修复】context精确匹配特殊处理
        if step_name == "context精确匹配":
            context_groups = {}
            for idx in remaining:
                ctx = (_get(reviews[idx], 'context') or '')
                if ctx:
                    context_groups.setdefault(ctx, []).append(idx)

            for ctx, idx_list in context_groups.items():
                if len(idx_list) > 1:
                    for k in range(1, len(idx_list)):
                        remove_idx = idx_list[k]
                        keep_idx = idx_list[0]
                        if remove_idx not in to_remove:
                            if dedup_log:
                                dedup_log.log_removal(
                                    removed_idx=remove_idx,
                                    kept_idx=keep_idx,
                                    removed_item=reviews[remove_idx],
                                    kept_item=reviews[keep_idx],
                                    reason=f"context完全相同: '{ctx[:60]}...'"
                                )
                            to_remove.add(remove_idx)
                            dup_found += 1
            if dedup_log:
                dedup_log.end_strategy()
            continue

        for i_idx in range(len(remaining)):
            idx1 = remaining[i_idx]
            for j_idx in range(i_idx + 1, len(remaining)):
                idx2 = remaining[j_idx]
                if fn(reviews[idx1], reviews[idx2]):
                    # 记录日志
                    if dedup_log:
                        dedup_log.log_removal(
                            removed_idx=idx2,
                            kept_idx=idx1,
                            removed_item=reviews[idx2],
                            kept_item=reviews[idx1],
                            reason=f"与索引[{idx1}]的条目{step_name}匹配"
                        )

                    to_remove.add(idx2)
                    dup_found += 1

        if dedup_log:
            dedup_log.end_strategy()

    # 复杂去重步骤（返回保留/删除对）
    complex_steps = [
        ("包含去重", is_containment_duplicate),
        ("issue语义去重", is_issue_semantic_duplicate),
        ("跨章节vs单章节去重", is_cross_chapter_vs_single_duplicate),
        ("位置邻近去重", is_positional_proximity_duplicate),  # P1优化新增
    ]
    for step_name, fn in complex_steps:
        if dedup_log:
            dedup_log.start_strategy(step_name)

        remaining = [i for i in indices if i not in to_remove]
        for i_idx in range(len(remaining)):
            idx1 = remaining[i_idx]
            if idx1 in to_remove:
                continue
            for j_idx in range(i_idx + 1, len(remaining)):
                idx2 = remaining[j_idx]
                if idx2 in to_remove:
                    continue
                result = fn(reviews[idx1], reviews[idx2])
                if result[0] is not None:
                    # result = (to_delete, to_keep)
                    del_item, keep_item = result
                    target_idx = idx1 if del_item == reviews[idx1] else idx2
                    kept_idx = idx1 if keep_item == reviews[idx1] else idx2

                    if target_idx not in to_remove:
                        # 记录日志
                        if dedup_log:
                            dedup_log.log_removal(
                                removed_idx=target_idx,
                                kept_idx=kept_idx,
                                removed_item=del_item,
                                kept_item=keep_item,
                                reason=f"{step_name}: 被去除条目的内容是保留条目的子集或相似项"
                            )

                        to_remove.add(target_idx)
                        dup_found += 1

        if dedup_log:
            dedup_log.end_strategy()

    # 构建去重后的列表
    deduplicated = [reviews[i] for i in indices if i not in to_remove]

    print(f"Dedup: {original_count} → {len(deduplicated)} ({dup_found} duplicates removed)")

    # 如果启用了日志，打印摘要
    if dedup_log:
        dedup_log.print_summary(original_count, len(deduplicated))

    return deduplicated, original_count - len(deduplicated), dedup_log


# ===================== 修订冲突检测与解决 =====================

def detect_conflicts(reviews):
    """
    检测同一 context 内的修订冲突。

    冲突定义：
    - 两个审查意见在同一个 section
    - 至少一个是 replace 或 delete 操作
    - context 相同或重叠
    - old_text 有重叠
    """
    conflicts = []
    for i in range(len(reviews)):
        for j in range(i + 1, len(reviews)):
            item1 = reviews[i]
            item2 = reviews[j]
            ctx1 = _get(item1, 'context')
            ctx2 = _get(item2, 'context')
            if ctx1 is None or ctx2 is None:
                continue
            if _get(item1, 'section') != _get(item2, 'section'):
                continue
            action1 = _get(item1, 'action_type')
            action2 = _get(item2, 'action_type')
            if action1 not in ('replace', 'delete') and action2 not in ('replace', 'delete'):
                continue
            if ctx1 != ctx2 and ctx1 not in ctx2 and ctx2 not in ctx1:
                if not context_overlap_ratio(ctx1, ctx2, 0.8):
                    continue
            old1 = _get(item1, 'old_text')
            old2 = _get(item2, 'old_text')
            has_overlap = bool(old1 and old2 and (set(old1) & set(old2)))
            if has_overlap or ctx1 == ctx2 or ctx1 in ctx2 or ctx2 in ctx1:
                conflicts.append((i, j))
    return conflicts


def detect_replace_comment_conflicts(reviews):
    """
    检测 replace/delete 与 comment 之间的文本覆盖冲突。

    当 replace 的 old_text 与 comment 的 highlight_text 精确匹配时，
    即使排序后 comment 先处理，两者指向同一文本也会造成批注冗余。
    此类冲突需要特殊处理：将 comment 的信息合并到 replace 中。

    注意：由于排序策略确保 comment 先于 replace/delete 处理，
    大部分 replace-comment 文本覆盖问题已通过排序解决。
    此函数仅检测 highlight_text 与 old_text 精确匹配的冗余情况。
    """
    conflicts = []
    for i in range(len(reviews)):
        for j in range(len(reviews)):
            if i == j:
                continue
            item_rd = reviews[i]
            item_cmt = reviews[j]
            action_rd = _get(item_rd, 'action_type')
            action_cmt = _get(item_cmt, 'action_type')
            if action_rd not in ('replace', 'delete') or action_cmt != 'comment':
                continue
            if _get(item_rd, 'section') != _get(item_cmt, 'section'):
                continue
            old_rd = _get(item_rd, 'old_text')
            if not old_rd:
                continue
            hl_cmt = _get(item_cmt, 'highlight_text')
            if hl_cmt and hl_cmt == old_rd:
                conflicts.append((i, j))
            elif hl_cmt and old_rd in hl_cmt and len(old_rd) >= len(hl_cmt) * 0.8:
                conflicts.append((i, j))
    return conflicts


def resolve_replace_comment_conflicts(reviews, conflicts):
    """
    解决 replace/delete 与 comment 之间的文本覆盖冲突。

    策略：将 comment 的 issue/suggestion 信息合并到 replace/delete 的批注中，
    然后移除 comment 条目。这样 replace 执行修改时会同时标注两类问题，
    避免 comment 因文本被修改而无法定位。
    """
    if not conflicts:
        return 0

    to_remove = set()
    merged_count = 0

    for rd_idx, cmt_idx in conflicts:
        if cmt_idx in to_remove:
            continue
        item_rd = reviews[rd_idx]
        item_cmt = reviews[cmt_idx]
        cmt_issue = _get(item_cmt, 'issue')
        cmt_suggestion = _get(item_cmt, 'suggestion')
        if cmt_issue or cmt_suggestion:
            existing_issue = _get(item_rd, 'issue') or ''
            existing_suggestion = _get(item_rd, 'suggestion') or ''
            if cmt_issue and cmt_issue not in existing_issue:
                item_rd['issue'] = existing_issue + '；[合并批注]' + cmt_issue if existing_issue else cmt_issue
            if cmt_suggestion and cmt_suggestion not in existing_suggestion:
                item_rd['suggestion'] = existing_suggestion + '；[合并建议]' + cmt_suggestion if existing_suggestion else cmt_suggestion
        to_remove.add(cmt_idx)
        merged_count += 1

    for idx in sorted(to_remove, reverse=True):
        reviews.pop(idx)

    print(f"Replace-comment conflict resolution: {merged_count} comments merged into replace entries, {len(to_remove)} comments removed")
    return merged_count


def _build_conflict_groups(conflicts, total):
    """
    将冲突分组为连通组件。

    使用并查集/广度优先搜索的思想，将相互关联的冲突归为一组。
    例如：A 与 B 冲突，B 与 C 冲突，则 A、B、C 属于同一组。
    """
    groups = {}
    for i, j in conflicts:
        groups.setdefault(i, []).append(j)
        groups.setdefault(j, []).append(i)

    processed = set()
    all_groups = []
    for idx in range(total):
        if idx in processed or idx not in groups:
            continue
        group_indices = set()
        queue = [idx]
        while queue:
            cur = queue.pop()
            if cur in processed:
                continue
            processed.add(cur)
            group_indices.add(cur)
            for nb in groups.get(cur, []):
                if nb not in group_indices:
                    queue.append(nb)
        all_groups.append(sorted(group_indices))
    return all_groups


def resolve_conflicts(reviews, conflicts):
    """
    解决修订冲突。

    策略：
    - 对于每组冲突，只保留一条 replace/delete，其余降级为 comment。
    - 优先保留 action_type 优先级高的（replace > delete > comment）。
    """
    if not conflicts:
        return 0, 0, 0

    total = len(reviews)
    conflict_groups = _build_conflict_groups(conflicts, total)
    action_prio = {'replace': 3, 'delete': 2, 'comment': 1}
    resolved = 0
    converted = 0

    for group in conflict_groups:
        group_items = [(i, reviews[i]) for i in group]
        # 按 action_type 优先级降序排序
        group_items.sort(key=lambda x: action_prio.get(x[1].get('action_type'), 0), reverse=True)

        if len(group_items) >= 3:
            # 对于3个及以上的冲突组，只保留第一条 replace/delete
            first_rd = None
            for i, item in group_items:
                if item.get('action_type') in ('replace', 'delete'):
                    first_rd = i
                    break
            for i, item in group_items:
                if i != first_rd and item.get('action_type') in ('replace', 'delete'):
                    item['action_type'] = 'comment'
                    item['old_text'] = None
                    item['new_text'] = None
                    converted += 1
                    resolved += 1
        else:
            # 对于2个元素的冲突组，保留优先级高的，另一个降级
            idx1, item1 = group_items[0]
            idx2, item2 = group_items[1]
            p1 = action_prio.get(item1.get('action_type'), 0)
            p2 = action_prio.get(item2.get('action_type'), 0)
            if p1 <= p2:
                if item2.get('action_type') in ('replace', 'delete'):
                    item2['action_type'] = 'comment'
                    item2['old_text'] = None
                    item2['new_text'] = None
                    converted += 1
            else:
                if item1.get('action_type') in ('replace', 'delete'):
                    item1['action_type'] = 'comment'
                    item1['old_text'] = None
                    item1['new_text'] = None
                    converted += 1
            resolved += 1

    print(f"Conflict resolution: {len(conflict_groups)} groups, {resolved} resolved, {converted} converted to comment")
    return resolved, converted, 0


# ===================== 冗余 replace 去重 =====================

def dedup_redundant_replaces(reviews):
    """
    冗余 replace 去重：同一段落中 old_text 完全相同的 replace 只保留一条，
    其余降级为 comment。
    
    关键约束：如果两条 replace 的 old_text 不同，说明它们修改的是段落中
    不同的文本位置，不是冗余的，不应去重。例如同一段落中需要分别在
    "碳毡电极主体"前加"所述"和在"第一表面"前加"所述"，这是两个不同的
    修改操作，都必须保留。
    """
    groups = {}
    for idx, item in enumerate(reviews):
        if item.get('action_type') != 'replace':
            continue
        ctx = item.get('context', '')
        section = item.get('section', '')
        old_text = item.get('old_text', '')
        key = (section, ctx[:30] if len(ctx) >= 30 else ctx, old_text)
        groups.setdefault(key, []).append(idx)

    converted = 0
    for key, indices in groups.items():
        if len(indices) <= 1:
            continue
        for idx in indices[1:]:
            reviews[idx]['action_type'] = 'comment'
            reviews[idx]['old_text'] = None
            reviews[idx]['new_text'] = None
            converted += 1

    if converted:
        print(f"Redundant replace dedup: {converted} converted to comment")
    return converted


# ===================== 主入口 =====================

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="审查意见合并、去重与冲突解决")
    parser.add_argument("--work-dir", required=True, help="工作目录路径")
    parser.add_argument("--timestamp", required=True, help="时间戳")
    parser.add_argument("--output", required=True, help="输出 JSON 文件路径")
    parser.add_argument("--pattern", default="reviews_agent*_*.json", help="Agent 输出文件匹配模式")
    parser.add_argument("--skip-dedup", action="store_true", help="跳过去重步骤")
    parser.add_argument("--skip-conflicts", action="store_true", help="跳过冲突解决步骤")

    # 日志记录相关参数
    parser.add_argument("--enable-dedup-log", action="store_true",
                        help="启用去重操作详细日志记录（记录每种策略去除的条目详情）")
    parser.add_argument("--dedup-log-output", default=None,
                        help="去重日志输出文件路径（默认为<output>_dedup_log.json）")

    args = parser.parse_args()

    work_dir = Path(args.work_dir)
    output_path = Path(args.output)

    # 确定日志输出路径
    if args.enable_dedup_log:
        if args.dedup_log_output:
            log_output_path = Path(args.dedup_log_output)
        else:
            # 自动生成日志文件名：在output基础上添加_dedup_log后缀
            log_output_path = output_path.with_name(output_path.stem + "_dedup_log" + output_path.suffix)
    else:
        log_output_path = None

    # 如果输出文件已存在，先删除
    if output_path.exists():
        output_path.unlink()

    # 1. 合并所有 Agent 文件
    reviews, agent_counts, found, merged, skipped = merge_all_agent_files(
        work_dir, args.pattern
    )

    # 如果有文件被跳过，提示常见修复方法
    if skipped > 0:
        print(f"\nWarning: {skipped} files were skipped. Check the files for JSON syntax errors.")
        print("Common fixes: check for Chinese quotes '' misused as JSON delimiters,")
        print("unescaped double quotes in string values, missing/extra commas, bracket mismatches.")
        return 1

    # 如果没有审查意见，输出空列表并退出
    if not reviews:
        print("No reviews found from any agent. Exiting.")
        save_reviews([], output_path)
        return 0

    merge_count = len(reviews)

    # 2. 预分组去重（按section+paragraph_index分组，组内快速去重）
    pre_dup_removed = 0
    if not args.skip_dedup:
        reviews, pre_dup_removed, _ = pre_group_dedup(reviews, enable_logging=args.enable_dedup_log)

    # 3. 多策略去重（支持日志记录）
    dedup_log = None
    if not args.skip_dedup:
        reviews, dup_removed, dedup_log = deduplicate(reviews, enable_logging=args.enable_dedup_log)
    else:
        dup_removed = 0

    # 4. 冗余 replace 去重
    if not args.skip_conflicts:
        dedup_redundant_replaces(reviews)

    # 5. 修订冲突检测与解决
    if not args.skip_conflicts:
        conflicts = detect_conflicts(reviews)
        print(f"Conflicts detected: {len(conflicts)}")
        if conflicts:
            res, conv, mgd = resolve_conflicts(reviews, conflicts)
        else:
            res = conv = mgd = 0
    else:
        conflicts = []
        res = conv = mgd = 0

    # 6. replace-comment 文本覆盖冲突检测与解决
    rc_merged = 0
    if not args.skip_conflicts:
        rc_conflicts = detect_replace_comment_conflicts(reviews)
        print(f"Replace-comment conflicts detected: {len(rc_conflicts)}")
        if rc_conflicts:
            rc_merged = resolve_replace_comment_conflicts(reviews, rc_conflicts)

    # 7. 排序：comment 类型优先于 replace/delete，确保批注先在原文上添加
    action_order = {'comment': 0, 'replace': 1, 'delete': 1}
    reviews.sort(key=lambda x: (action_order.get(x.get('action_type', 'comment'), 1), x.get('section', ''), x.get('paragraph_index') or 0))

    # 8. 保存最终结果
    save_reviews(reviews, output_path)

    # 9. 保存去重日志（如果启用）
    if args.enable_dedup_log and dedup_log and log_output_path:
        final_count = len(reviews)
        dedup_log.save_to_file(log_output_path, merge_count, final_count)

    final_count = len(reviews)
    print(f"\n========== Merge Summary ==========")
    print(f"Agent files found:   {found}")
    print(f"Agent files merged:  {merged}")
    print(f"Agent files skipped: {skipped}")
    print(f"Reviews before dedup: {merge_count}")
    print(f"Pre-group duplicates removed: {pre_dup_removed}")
    print(f"Multi-strategy duplicates removed: {dup_removed}")
    print(f"Total duplicates removed: {pre_dup_removed + dup_removed}")
    print(f"Conflicts resolved:   {res} ({conv} → comment, {mgd} merged)")
    print(f"Replace-comment merged: {rc_merged}")
    print(f"Final review count:   {final_count}")
    print(f"Output: {output_path}")

    if args.enable_dedup_log and log_output_path:
        print(f"Deduplication log:   {log_output_path}")

    return 0


# 当直接运行此脚本时执行 main 函数
if __name__ == "__main__":
    sys.exit(main())
