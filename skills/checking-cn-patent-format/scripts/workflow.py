#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

SKILL_ROOT = Path(__file__).parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.error_handling import (
    check_python_version,
    PatentReviewError,
    ExtractionError,
    AnnotationError,
    VerificationError,
    MergeError,
    AnnotationBatchLogger,
)
from scripts.review_adder import add_reviews
from scripts.merge_reviews import merge_all_agent_files, deduplicate, detect_conflicts, resolve_conflicts, save_reviews, pre_group_dedup, dedup_redundant_replaces, detect_replace_comment_conflicts, resolve_replace_comment_conflicts
from scripts.format_json import format_json_files
from scripts.verify import verify as verify_document


class PatentReviewWorkflow:
    def __init__(
        self,
        input_doc: str,
        skill_root: str = None,
        author: str = "checking-cn-patent-format",
    ):
        check_python_version(min_version=(3, 10))

        self.input_doc = Path(input_doc)
        self.skill_root = Path(skill_root) if skill_root else SKILL_ROOT
        self.author = author
        self.timestamp = None
        self.work_dir = None
        self.input_dir = self.input_doc.parent
        self.input_stem = self.input_doc.stem

        self.extraction_result = None
        self.review_stats: Dict = {}
        self.merge_result = None
        self.annotation_logger = AnnotationBatchLogger()
        self.verification_result = None
        self.skip_relocation_result = None
        self.compliance_result = None
        self.bug_review_result = None

        self.errors: List[Dict] = []
        self.start_time = datetime.now()

    def step1_validate_input(self) -> bool:
        suffix = self.input_doc.suffix.lower()
        if suffix not in ('.docx', '.doc'):
            self.errors.append({
                'step': 'validate_input',
                'message': f"不支持的文件格式: {suffix}，仅支持 .docx 和 .doc"
            })
            return False
        if not self.input_doc.exists():
            self.errors.append({
                'step': 'validate_input',
                'message': f"输入文件不存在: {self.input_doc}"
            })
            return False
        return True

    def step2_create_work_dir(self) -> bool:
        try:
            from datetime import datetime as dt
            result = dt.now().astimezone().strftime('%Y%m%d_%H%M%S')
            self.timestamp = result
            self.work_dir = self.input_dir / f"{self.author}_{self.timestamp}"
            self.work_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.errors.append({
                'step': 'create_work_dir',
                'message': str(e)
            })
            return False

    def step5_merge_reviews(self, enable_dedup_log: bool = False) -> bool:
        if not self.work_dir or not self.timestamp:
            self.errors.append({
                'step': 'merge_reviews',
                'message': 'work_dir 或 timestamp 未初始化'
            })
            return False

        try:
            reviews, agent_counts, found, merged, skipped = merge_all_agent_files(
                self.work_dir
            )

            if skipped > 0:
                self.errors.append({
                    'step': 'merge_reviews',
                    'message': f'{skipped} 个 Agent 文件被跳过'
                })

            if not reviews:
                output_path = self.work_dir / f"reviews_{self.timestamp}.json"
                save_reviews([], output_path)
                self.merge_result = {'total': 0, 'agent_counts': agent_counts}
                return True

            reviews, pre_dup_removed, _ = pre_group_dedup(reviews, enable_logging=enable_dedup_log)
            reviews, dup_removed, dedup_log = deduplicate(reviews, enable_logging=enable_dedup_log)
            dedup_redundant_replaces(reviews)

            conflicts = detect_conflicts(reviews)
            if conflicts:
                resolve_conflicts(reviews, conflicts)

            rc_conflicts = detect_replace_comment_conflicts(reviews)
            if rc_conflicts:
                resolve_replace_comment_conflicts(reviews, rc_conflicts)

            action_order = {'comment': 0, 'replace': 1, 'delete': 1}
            reviews.sort(key=lambda x: (
                action_order.get(x.get('action_type', 'comment'), 1),
                x.get('section', ''),
                x.get('paragraph_index') or 0
            ))

            output_path = self.work_dir / f"reviews_{self.timestamp}.json"
            save_reviews(reviews, output_path)

            self.merge_result = {
                'total': len(reviews),
                'agent_counts': agent_counts,
                'pre_dup_removed': pre_dup_removed,
                'dup_removed': dup_removed,
                'conflicts': len(conflicts),
            }
            return True

        except Exception as e:
            self.errors.append({
                'step': 'merge_reviews',
                'message': str(e)
            })
            return False

    def step6_add_annotations(self) -> bool:
        if not self.work_dir or not self.timestamp:
            self.errors.append({
                'step': 'add_annotations',
                'message': 'work_dir 或 timestamp 未初始化'
            })
            return False

        reviews_path = self.work_dir / f"reviews_{self.timestamp}.json"
        if not reviews_path.exists():
            self.errors.append({
                'step': 'add_annotations',
                'message': f'审查意见文件不存在: {reviews_path}'
            })
            return False

        try:
            with open(reviews_path, 'r', encoding='utf-8') as f:
                reviews = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append({
                'step': 'add_annotations',
                'message': f'JSON 解析失败: {e}'
            })
            return False

        output_docx = self.input_dir / f"{self.input_stem}_ReviewOut_{self.timestamp}.docx"

        try:
            result = add_reviews(
                str(self.input_doc),
                str(output_docx),
                reviews,
                author=self.author
            )
            self.review_stats = result
            return True
        except Exception as e:
            self.errors.append({
                'step': 'add_annotations',
                'message': str(e)
            })
            return False

    def step7_verify(self) -> bool:
        if not self.work_dir or not self.timestamp:
            return False

        output_docx = self.input_dir / f"{self.input_stem}_ReviewOut_{self.timestamp}.docx"
        if not output_docx.exists():
            self.errors.append({
                'step': 'verify',
                'message': f'审查后文档不存在: {output_docx}'
            })
            return False

        try:
            result = verify_document(
                str(self.input_doc),
                str(output_docx),
                str(self.work_dir)
            )
            self.verification_result = result
            return result == 0
        except Exception as e:
            self.errors.append({
                'step': 'verify',
                'message': str(e)
            })
            return False

    def step5a_format_json(self) -> bool:
        if not self.work_dir:
            return False

        try:
            format_json_files(self.work_dir)
            return True
        except Exception as e:
            self.errors.append({
                'step': 'format_json',
                'message': str(e)
            })
            return False

    def save_annotation_log(self) -> Optional[str]:
        if not self.work_dir or not self.timestamp:
            return None

        log_path = str(self.work_dir / f"annotation_log_{self.timestamp}.json")
        self.annotation_logger.save_log_json(log_path)
        return log_path

    def generate_summary(self) -> str:
        duration = (datetime.now() - self.start_time).total_seconds()

        lines = []
        lines.append("=" * 60)
        lines.append("专利审查工作流摘要")
        lines.append("=" * 60)
        lines.append(f"\n输入文件: {self.input_doc}")
        lines.append(f"工作目录: {self.work_dir}")
        lines.append(f"时间戳: {self.timestamp}")
        lines.append(f"执行时间: {duration:.2f} 秒")

        if self.merge_result:
            lines.append(f"\n合并结果:")
            lines.append(f"  最终审查意见数: {self.merge_result.get('total', 0)}")
            lines.append(f"  Agent 分布: {self.merge_result.get('agent_counts', {})}")

        if self.review_stats:
            lines.append(f"\n批注添加结果:")
            lines.append(f"  总数: {self.review_stats.get('total', 0)}")
            lines.append(f"  成功: {self.review_stats.get('success', 0)}")
            lines.append(f"  跳过: {self.review_stats.get('skip', 0)}")

        if self.verification_result is not None:
            lines.append(f"\n验证结果: {'通过' if self.verification_result == 0 else '失败'}")

        if self.errors:
            lines.append(f"\n错误列表:")
            for i, err in enumerate(self.errors, 1):
                lines.append(f"  {i}. [{err.get('step', '?')}] {err.get('message', '')}")

        lines.append("\n" + "=" * 60)
        return '\n'.join(lines)


if __name__ == "__main__":
    print("专利审查工作流模块")
    print("=" * 60)
    print()
    print("使用示例:")
    print()
    print("from scripts.workflow import PatentReviewWorkflow")
    print()
    print("workflow = PatentReviewWorkflow('专利申请文件.docx')")
    print("workflow.step1_validate_input()")
    print("workflow.step2_create_work_dir()")
    print("# ... 子Agent执行审查 ...")
    print("workflow.step5_merge_reviews()")
    print("workflow.step6_add_annotations()")
    print("workflow.step7_verify()")
    print("print(workflow.generate_summary())")
