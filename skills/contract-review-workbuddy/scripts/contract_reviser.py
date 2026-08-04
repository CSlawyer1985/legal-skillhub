#!/usr/bin/env python3
"""
合同一键修订模块 v4.0
根据风险点与条款库匹配结果，生成带修订标记的合同文档

修订标记规则：
- 红色删除线：建议删除或替换的原文
- 绿色下划线：建议替换为的推荐条款文本
- 灰色斜体批注：修订理由、法律依据、风险等级

输出格式：
- .docx  带格式修订稿（需 python-docx）
- .md    纯文本对照修订稿（无依赖，始终可用）
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 最大处理文本长度，与规则引擎保持一致
MAX_TEXT_LENGTH = 500000

# 严重等级归一化映射（规则引擎与 LLM 输出两套口径统一）
SEVERITY_ALIAS = {
    'critical': '严重', 'high': '中等', 'medium': '一般', 'low': '提示',
    '严重': '严重', '中等': '中等', '一般': '一般', '提示': '提示',
    '高': '中等', '中': '一般', '低': '提示',
}

SEVERITY_ORDER = {'严重': 0, '中等': 1, '一般': 2, '提示': 3}

SEVERITY_MARK = {'严重': '🔴', '中等': '🟡', '一般': '🟢', '提示': 'ℹ️'}


def normalize_severity(value: str) -> str:
    """归一化严重等级"""
    if not value:
        return '一般'
    return SEVERITY_ALIAS.get(str(value).strip(), '一般')


class RevisionItem:
    """单条修订记录"""

    def __init__(self, risk: Dict, clause: Optional[Dict] = None):
        self.risk_id = risk.get('risk_id', '')
        self.title = risk.get('title', '未命名风险')
        self.severity = normalize_severity(risk.get('severity', ''))
        self.original_text = (risk.get('text_snippet') or '').strip()
        self.description = risk.get('description', '')
        self.legal_basis = risk.get('legal_basis', '')
        self.clause_ref = risk.get('clause_ref', '')
        self.clause = clause or {}

        # 推荐文本优先级：条款库推荐文本 > 风险点自带范本 > 修改建议
        self.recommended_text = (
            self.clause.get('recommended_text')
            or risk.get('template')
            or risk.get('suggestion')
            or ''
        ).strip()
        self.clause_id = self.clause.get('id', '')
        self.clause_name = self.clause.get('name', '')
        # 条款库法律依据可补充风险点缺失的依据
        if not self.legal_basis:
            self.legal_basis = self.clause.get('legal_basis', '')
        self.notes = self.clause.get('notes', '')
        # 是否可在正文中定位并替换
        self.located = False
        self.match_start = -1
        self.match_end = -1

    def to_dict(self) -> Dict[str, Any]:
        return {
            'risk_id': self.risk_id,
            'title': self.title,
            'severity': self.severity,
            'original_text': self.original_text,
            'recommended_text': self.recommended_text,
            'clause_id': self.clause_id,
            'clause_name': self.clause_name,
            'legal_basis': self.legal_basis,
            'description': self.description,
            'clause_ref': self.clause_ref,
            'notes': self.notes,
            'located': self.located,
        }


class ContractReviser:
    """合同修订生成器"""

    def __init__(self, matcher=None):
        """
        Args:
            matcher: ClauseMatcher 实例，为空时自动创建
        """
        self.matcher = matcher
        self._revisions: List[RevisionItem] = []

    def _get_matcher(self):
        """惰性获取条款匹配器"""
        if self.matcher is None:
            try:
                from clause_matcher import ClauseMatcher
            except ImportError:
                try:
                    from .clause_matcher import ClauseMatcher
                except ImportError:
                    logger.warning("条款匹配器不可用，将仅使用风险点自带建议")
                    return None
            self.matcher = ClauseMatcher()
            self.matcher.load()
        return self.matcher

    def build_revisions(self, risks: List[Dict], contract_type: str = "") -> List[RevisionItem]:
        """
        为风险点构建修订记录

        Args:
            risks: 风险点列表
            contract_type: 合同类型

        Returns:
            修订记录列表（按严重等级排序）
        """
        matcher = self._get_matcher()
        revisions = []

        for risk in risks:
            clause = None
            if matcher is not None:
                try:
                    clause = matcher.match(risk, contract_type)
                except Exception as e:
                    logger.debug(f"条款匹配失败 ({risk.get('risk_id')}): {e}")
            item = RevisionItem(risk, clause)
            # 无任何推荐文本的风险点不生成修订条目
            if not item.recommended_text:
                continue
            revisions.append(item)

        revisions.sort(key=lambda r: SEVERITY_ORDER.get(r.severity, 99))
        self._revisions = revisions
        logger.info(f"生成修订建议 {len(revisions)} 条（风险点 {len(risks)} 个）")
        return revisions

    def locate_in_text(self, text: str, revisions: List[RevisionItem]) -> List[RevisionItem]:
        """
        在合同全文中定位每条修订的原文位置（不重叠）

        Args:
            text: 合同全文
            revisions: 修订记录列表

        Returns:
            标注了定位结果的修订记录列表
        """
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]

        occupied: List[Tuple[int, int]] = []

        for item in revisions:
            snippet = item.original_text
            if not snippet or len(snippet) < 4:
                continue

            start = self._find_snippet(text, snippet, occupied)
            if start < 0:
                continue

            item.located = True
            item.match_start = start
            item.match_end = start + len(snippet)
            occupied.append((item.match_start, item.match_end))

        located_count = sum(1 for r in revisions if r.located)
        logger.info(f"原文定位成功 {located_count}/{len(revisions)} 条")
        return revisions

    @staticmethod
    def _find_snippet(text: str, snippet: str, occupied: List[Tuple[int, int]]) -> int:
        """在文本中查找片段，跳过已被占用的区间；失败时降级为去空白匹配"""

        def is_free(s: int, e: int) -> bool:
            return all(e <= os_ or s >= oe for os_, oe in occupied)

        # 精确匹配
        pos = text.find(snippet)
        while pos >= 0:
            if is_free(pos, pos + len(snippet)):
                return pos
            pos = text.find(snippet, pos + 1)

        # 降级：去除空白字符后匹配前 20 字
        head = re.sub(r'\s+', '', snippet)[:20]
        if len(head) >= 6:
            pos = text.find(head)
            while pos >= 0:
                if is_free(pos, pos + len(head)):
                    return pos
                pos = text.find(head, pos + 1)

        return -1

    def generate_markdown(self, revisions: List[RevisionItem], contract_info: Dict,
                          output_path: str) -> str:
        """
        生成 Markdown 格式修订对照稿（无第三方依赖）

        Returns:
            输出文件路径
        """
        lines = []
        lines.append('# 合同修订建议对照稿')
        lines.append('')
        lines.append(f"- 合同文件：{contract_info.get('file_name', '未知')}")
        lines.append(f"- 合同类型：{contract_info.get('contract_type', '未识别')}")
        industry_name = contract_info.get('industry_name', '')
        if industry_name:
            lines.append(f"- 行业专项：{industry_name}")
        lines.append(f"- 修订条目：{len(revisions)} 条")
        lines.append(f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append('')
        lines.append('> 标记说明：~~删除线~~ 为建议删除或替换的原文，**推荐条款** 为建议采用的表述。')
        lines.append('')
        lines.append('---')
        lines.append('')

        current_severity = None
        for i, item in enumerate(revisions, 1):
            if item.severity != current_severity:
                current_severity = item.severity
                mark = SEVERITY_MARK.get(item.severity, '⚪')
                lines.append(f'## {mark} {item.severity}风险修订')
                lines.append('')

            lines.append(f'### {i}. {item.title}')
            lines.append('')
            if item.clause_ref:
                lines.append(f'- 位置：{item.clause_ref}')
            if item.clause_id:
                lines.append(f'- 匹配条款：{item.clause_id} {item.clause_name}')
            lines.append(f"- 原文定位：{'已定位' if item.located else '未定位（需人工核对）'}")
            lines.append('')

            if item.original_text:
                lines.append('**原文（建议修改）**')
                lines.append('')
                lines.append(f'> ~~{item.original_text}~~')
                lines.append('')

            lines.append('**建议替换为**')
            lines.append('')
            lines.append(f'> {item.recommended_text}')
            lines.append('')

            if item.description:
                lines.append(f'**修订理由**：{item.description}')
                lines.append('')
            if item.legal_basis:
                lines.append(f'**法律依据**：{item.legal_basis}')
                lines.append('')
            if item.notes:
                lines.append(f'**实务提示**：{item.notes}')
                lines.append('')
            lines.append('---')
            lines.append('')

        lines.append('## 免责声明')
        lines.append('')
        lines.append('本修订建议由 AI 自动生成，仅供参考，不构成法律意见。')
        lines.append('重大合同请务必经执业律师审核后签署。')
        lines.append('')
        lines.append('有更好建议：njskills@agent.qq.com')

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text('\n'.join(lines), encoding='utf-8')
        logger.info(f"Markdown 修订稿已保存: {out}")
        return str(out)

    def generate_docx(self, revisions: List[RevisionItem], contract_info: Dict,
                      output_path: str, contract_text: str = "") -> str:
        """
        生成 Word 格式修订稿（红色删除线 + 绿色下划线 + 灰色批注）

        Args:
            revisions: 修订记录
            contract_info: 合同信息
            output_path: 输出路径
            contract_text: 合同全文，提供时生成"全文修订版"，否则生成"修订清单版"

        Returns:
            输出文件路径
        """
        try:
            from docx_generator import _ensure_docx
        except ImportError:
            from .docx_generator import _ensure_docx
        _ensure_docx()
        import docx_generator as dg

        doc = dg.Document()

        # 标题
        title = doc.add_heading('合同修订建议稿', level=0)
        title.alignment = dg.WD_ALIGN_PARAGRAPH.CENTER

        # 基本信息
        info_lines = [
            f"合同文件：{contract_info.get('file_name', '未知')}",
            f"合同类型：{contract_info.get('contract_type', '未识别')}",
            f"修订条目：{len(revisions)} 条",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if contract_info.get('industry_name'):
            info_lines.insert(2, f"行业专项：{contract_info['industry_name']}")
        for line in info_lines:
            p = doc.add_paragraph()
            run = p.add_run(line)
            run.font.size = dg.Pt(10)

        # 图例
        p = doc.add_paragraph()
        run = p.add_run('标记说明：')
        run.bold = True
        run = p.add_run('删除线红字')
        run.font.strike = True
        run.font.color.rgb = dg.RGBColor(0xCC, 0x00, 0x00)
        p.add_run(' = 建议删除/替换的原文；')
        run = p.add_run('下划线绿字')
        run.underline = True
        run.font.color.rgb = dg.RGBColor(0x00, 0x80, 0x00)
        p.add_run(' = 建议采用的推荐条款。')

        if contract_text:
            self._write_full_text_revision(doc, dg, revisions, contract_text)
        else:
            self._write_revision_list(doc, dg, revisions)

        # 免责声明
        doc.add_heading('免责声明', level=1)
        p = doc.add_paragraph()
        run = p.add_run(
            '本修订建议由 AI 自动生成，仅供参考，不构成法律意见。'
            '重大合同请务必经执业律师审核后签署。'
        )
        run.font.size = dg.Pt(9)
        run.font.color.rgb = dg.RGBColor(0x88, 0x88, 0x88)
        p = doc.add_paragraph()
        run = p.add_run('有更好建议：njskills@agent.qq.com')
        run.font.size = dg.Pt(9)
        run.font.color.rgb = dg.RGBColor(0x88, 0x88, 0x88)

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out))
        logger.info(f"Word 修订稿已保存: {out}")
        return str(out)

    def _write_full_text_revision(self, doc, dg, revisions: List[RevisionItem],
                                  contract_text: str):
        """写入全文修订版：在原文中就地标记删除线与推荐文本"""
        doc.add_heading('一、合同全文修订对照', level=1)

        if len(contract_text) > MAX_TEXT_LENGTH:
            contract_text = contract_text[:MAX_TEXT_LENGTH]

        located = [r for r in revisions if r.located]
        located.sort(key=lambda r: r.match_start)

        cursor = 0
        para = doc.add_paragraph()
        for idx, item in enumerate(located, 1):
            # 修订点之前的原文
            plain = contract_text[cursor:item.match_start]
            if plain:
                para.add_run(plain)

            # 原文（红色删除线）
            run = para.add_run(contract_text[item.match_start:item.match_end])
            run.font.strike = True
            run.font.color.rgb = dg.RGBColor(0xCC, 0x00, 0x00)

            # 推荐文本（绿色下划线）
            run = para.add_run(item.recommended_text)
            run.underline = True
            run.font.color.rgb = dg.RGBColor(0x00, 0x80, 0x00)

            # 批注（灰色斜体上标编号）
            note = f'［修订{idx}：{item.title}'
            if item.legal_basis:
                note += f'；依据 {item.legal_basis}'
            note += '］'
            run = para.add_run(note)
            run.italic = True
            run.font.size = dg.Pt(8)
            run.font.color.rgb = dg.RGBColor(0x99, 0x99, 0x99)

            cursor = item.match_end

        # 剩余原文
        if cursor < len(contract_text):
            para.add_run(contract_text[cursor:])

        # 未定位的修订单列
        unlocated = [r for r in revisions if not r.located]
        if unlocated:
            doc.add_heading('二、未定位修订建议（需人工核对位置）', level=1)
            self._write_revision_items(doc, dg, unlocated, start_index=1)

    def _write_revision_list(self, doc, dg, revisions: List[RevisionItem]):
        """写入修订清单版（无全文时）"""
        doc.add_heading('一、修订建议清单', level=1)
        if not revisions:
            doc.add_paragraph('本次审查未生成可执行的修订建议。')
            return
        self._write_revision_items(doc, dg, revisions, start_index=1)

    def _write_revision_items(self, doc, dg, revisions: List[RevisionItem],
                              start_index: int = 1):
        """逐条写入修订项"""
        current_severity = None
        for i, item in enumerate(revisions, start_index):
            if item.severity != current_severity:
                current_severity = item.severity
                mark = SEVERITY_MARK.get(item.severity, '⚪')
                doc.add_heading(f'{mark} {item.severity}风险', level=2)

            p = doc.add_paragraph()
            run = p.add_run(f'{i}. {item.title}')
            run.bold = True
            run.font.size = dg.Pt(12)

            meta = []
            if item.clause_ref:
                meta.append(f'位置：{item.clause_ref}')
            if item.clause_id:
                meta.append(f'匹配条款：{item.clause_id} {item.clause_name}')
            if meta:
                p = doc.add_paragraph()
                run = p.add_run(' | '.join(meta))
                run.font.size = dg.Pt(9)
                run.font.color.rgb = dg.RGBColor(0x66, 0x66, 0x66)

            if item.original_text:
                p = doc.add_paragraph()
                run = p.add_run('原文：')
                run.bold = True
                run = p.add_run(item.original_text)
                run.font.strike = True
                run.font.color.rgb = dg.RGBColor(0xCC, 0x00, 0x00)

            p = doc.add_paragraph()
            run = p.add_run('建议替换为：')
            run.bold = True
            run.font.color.rgb = dg.RGBColor(0x00, 0x80, 0x00)
            run = p.add_run(item.recommended_text)
            run.underline = True
            run.font.color.rgb = dg.RGBColor(0x00, 0x80, 0x00)

            if item.description:
                p = doc.add_paragraph()
                run = p.add_run('修订理由：')
                run.bold = True
                p.add_run(item.description)

            if item.legal_basis:
                p = doc.add_paragraph()
                run = p.add_run('法律依据：')
                run.bold = True
                run.font.color.rgb = dg.RGBColor(0x00, 0x00, 0x80)
                p.add_run(item.legal_basis)

            if item.notes:
                p = doc.add_paragraph()
                run = p.add_run(f'实务提示：{item.notes}')
                run.italic = True
                run.font.size = dg.Pt(9)
                run.font.color.rgb = dg.RGBColor(0x99, 0x99, 0x99)

            p = doc.add_paragraph()
            p.add_run('─' * 50).font.color.rgb = dg.RGBColor(0xDD, 0xDD, 0xDD)

    def revise(self, risks: List[Dict], contract_info: Dict, output_path: str,
               contract_text: str = "", fmt: str = "auto") -> Dict[str, Any]:
        """
        一键修订主入口

        Args:
            risks: 风险点列表
            contract_info: 合同信息（file_name/contract_type/industry_name）
            output_path: 输出路径（后缀决定格式，fmt=auto 时）
            contract_text: 合同全文（提供时生成全文修订版）
            fmt: 输出格式 auto/docx/md

        Returns:
            {'output': 路径, 'count': 修订条数, 'located': 定位成功数, 'revisions': [...]}
        """
        contract_type = contract_info.get('contract_type', '')
        revisions = self.build_revisions(risks, contract_type)

        if contract_text:
            revisions = self.locate_in_text(contract_text, revisions)

        out_path = Path(output_path)
        if fmt == 'auto':
            fmt = 'docx' if out_path.suffix.lower() == '.docx' else 'md'

        if fmt == 'docx':
            try:
                path = self.generate_docx(revisions, contract_info,
                                          str(out_path), contract_text)
            except ImportError as e:
                logger.warning(f"{e}\n已降级为 Markdown 格式输出")
                path = self.generate_markdown(revisions, contract_info,
                                              str(out_path.with_suffix('.md')))
        else:
            path = self.generate_markdown(revisions, contract_info,
                                          str(out_path.with_suffix('.md')))

        return {
            'output': path,
            'count': len(revisions),
            'located': sum(1 for r in revisions if r.located),
            'revisions': [r.to_dict() for r in revisions],
        }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='合同一键修订生成器 v4.0')
    parser.add_argument('risks_json', help='风险点 JSON 文件（含 risks 列表）')
    parser.add_argument('-o', '--output', default='revision.docx', help='输出文件路径')
    parser.add_argument('-t', '--text', help='合同全文 txt 文件（生成全文修订版）')
    parser.add_argument('-c', '--contract-type', default='', help='合同类型')
    parser.add_argument('-f', '--format', default='auto',
                        choices=['auto', 'docx', 'md'], help='输出格式')
    args = parser.parse_args()

    with open(args.risks_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    risks = data.get('risks', data) if isinstance(data, dict) else data

    contract_text = ''
    if args.text:
        contract_text = Path(args.text).read_text(encoding='utf-8')

    reviser = ContractReviser()
    result = reviser.revise(
        risks,
        {'file_name': Path(args.risks_json).name, 'contract_type': args.contract_type},
        args.output,
        contract_text=contract_text,
        fmt=args.format,
    )

    print(f"修订稿已生成：{result['output']}")
    print(f"修订条目：{result['count']} 条，原文定位成功：{result['located']} 条")


if __name__ == '__main__':
    main()
