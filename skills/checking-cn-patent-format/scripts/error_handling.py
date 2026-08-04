#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


class PatentReviewError(Exception):
    pass


class ExtractionError(PatentReviewError):
    pass


class AnnotationError(PatentReviewError):
    pass


class VerificationError(PatentReviewError):
    pass


class MergeError(PatentReviewError):
    pass


class PackError(PatentReviewError):
    pass


class UnpackError(PatentReviewError):
    pass


class PythonVersionError(PatentReviewError):
    pass


def check_python_version(min_version: tuple = (3, 10),
                         recommended_version: tuple = (3, 10)) -> None:
    current = (sys.version_info.major, sys.version_info.minor)

    if current < min_version:
        raise PythonVersionError(
            f"Python {'.'.join(map(str, min_version))}+ required, "
            f"current: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )

    if current < recommended_version:
        import warnings
        warnings.warn(
            f"Python {'.'.join(map(str, recommended_version))}+ recommended for best compatibility. "
            f"Current: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            UserWarning
        )


def format_error_summary(errors: List[Dict]) -> str:
    if not errors:
        return "✓ 无错误"

    lines = []
    lines.append(f"✗ 发现 {len(errors)} 个错误:\n")

    for i, error in enumerate(errors, 1):
        lines.append(f"\n{i}. {error.get('type', 'Unknown Error')}")
        lines.append(f"   位置: {error.get('location', 'N/A')}")
        lines.append(f"   原因: {error.get('message', 'N/A')}")

        if 'suggestion' in error:
            lines.append(f"   建议: {error['suggestion']}")

        if 'risk_level' in error:
            lines.append(f"   风险等级: {error['risk_level']}")

    return '\n'.join(lines)


class AnnotationBatchLogger:
    def __init__(self):
        self.successful = []
        self.skipped = []
        self.failed = []
        self.warnings = []
        self.start_time = datetime.now()

    def log_success(self, comment_id: int, section: str, context_preview: str, action_type: str = "comment"):
        self.successful.append({
            'id': comment_id,
            'section': section,
            'context_preview': context_preview,
            'action_type': action_type,
            'timestamp': datetime.now()
        })

    def log_skip(self, section: str, context_preview: str, reason: str, review_index: int):
        self.skipped.append({
            'section': section,
            'context_preview': context_preview,
            'reason': reason,
            'review_index': review_index,
            'timestamp': datetime.now()
        })

    def log_failure(self, section: str, context_preview: str, error: Exception, review_index: int):
        self.failed.append({
            'section': section,
            'context_preview': context_preview,
            'error': str(error),
            'error_type': type(error).__name__,
            'traceback': traceback.format_exc(),
            'review_index': review_index,
            'timestamp': datetime.now()
        })

    def log_warning(self, message: str, details: str = ""):
        self.warnings.append({
            'message': message,
            'details': details,
            'timestamp': datetime.now()
        })

    def generate_summary(self) -> str:
        duration = (datetime.now() - self.start_time).total_seconds()

        lines = []
        lines.append("=" * 60)
        lines.append("批注添加摘要")
        lines.append("=" * 60)
        lines.append(f"\n执行时间: {duration:.2f} 秒")
        lines.append(f"成功: {len(self.successful)} 个")
        lines.append(f"跳过: {len(self.skipped)} 个")
        lines.append(f"失败: {len(self.failed)} 个")
        lines.append(f"警告: {len(self.warnings)} 个")

        total = len(self.successful) + len(self.skipped) + len(self.failed)
        if total > 0:
            success_rate = len(self.successful) / total * 100
            lines.append(f"成功率: {success_rate:.1f}%")

        if self.skipped:
            skip_reasons = {}
            for item in self.skipped:
                reason = item['reason']
                skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            lines.append("\n跳过原因分布:")
            for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1]):
                lines.append(f"  - {reason}: {count} 个")

        if self.failed:
            lines.append("\n失败详情:")
            lines.append("-" * 60)
            for i, fail in enumerate(self.failed, 1):
                lines.append(f"\n{i}. Section: {fail['section']}")
                lines.append(f"   Context: {fail['context_preview'][:50]}...")
                lines.append(f"   错误类型: {fail['error_type']}")
                lines.append(f"   错误: {fail['error'][:100]}")

        if self.warnings:
            lines.append("\n警告:")
            lines.append("-" * 60)
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"{i}. {warning['message']}")
                if warning['details']:
                    lines.append(f"   详情: {warning['details'][:80]}")

        lines.append("\n" + "=" * 60)
        return '\n'.join(lines)

    def save_to_file(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_summary())
            f.write("\n\n详细错误追踪:\n")
            f.write("=" * 60 + "\n\n")

            for i, fail in enumerate(self.failed, 1):
                f.write(f"错误 #{i}:\n")
                f.write(f"Section: {fail['section']}\n")
                f.write(f"Review Index: {fail['review_index']}\n")
                f.write(f"时间: {fail['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"错误类型: {fail['error_type']}\n")
                f.write(f"错误信息:\n{fail['traceback']}\n")
                f.write("\n" + "-" * 60 + "\n\n")

            if self.warnings:
                f.write("\n警告详情:\n")
                f.write("=" * 60 + "\n\n")
                for i, warning in enumerate(self.warnings, 1):
                    f.write(f"警告 #{i}:\n")
                    f.write(f"时间: {warning['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"消息: {warning['message']}\n")
                    if warning['details']:
                        f.write(f"详情: {warning['details']}\n")
                    f.write("\n")

    def get_statistics(self) -> Dict:
        total = len(self.successful) + len(self.skipped) + len(self.failed)
        success_rate = (len(self.successful) / total * 100) if total > 0 else 0

        skip_reasons = {}
        for item in self.skipped:
            reason = item['reason']
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1

        return {
            'total': total,
            'successful': len(self.successful),
            'skipped': len(self.skipped),
            'failed': len(self.failed),
            'warnings': len(self.warnings),
            'success_rate': success_rate,
            'skip_reasons': skip_reasons,
            'duration_seconds': (datetime.now() - self.start_time).total_seconds()
        }

    def save_log_json(self, filepath: str):
        import json
        stats = self.get_statistics()
        log_data = {
            'timestamp': self.start_time.isoformat(),
            'duration_seconds': stats['duration_seconds'],
            'summary': {
                'total': stats['total'],
                'successful': stats['successful'],
                'skipped': stats['skipped'],
                'failed': stats['failed'],
                'success_rate': stats['success_rate'],
                'skip_reasons': stats['skip_reasons']
            },
            'skipped_items': [
                {
                    'section': item['section'],
                    'context_preview': item['context_preview'][:80],
                    'reason': item['reason'],
                    'review_index': item['review_index']
                }
                for item in self.skipped
            ],
            'failed_items': [
                {
                    'section': item['section'],
                    'context_preview': item['context_preview'][:80],
                    'error': item['error'][:200],
                    'error_type': item['error_type'],
                    'review_index': item['review_index']
                }
                for item in self.failed
            ]
        }

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("专利审查错误处理工具")
    print("=" * 60)
    print()
    print("功能模块:")
    print("1. 自定义异常类: PatentReviewError, ExtractionError 等")
    print("2. 版本检查: check_python_version()")
    print("3. 错误格式化: format_error_summary()")
    print("4. 批注日志: AnnotationBatchLogger")
