#!/usr/bin/env python3
"""
工业级合同清洗系统

核心设计：
1. 规则引擎前置：所有确定性规则（术语、金额、编号、格式）由 Python 代码 100% 保证
2. 分块 + 上下文注入：长合同按条款边界切分，每块注入合同标题、甲乙方、当前位置等上下文
3. 多轮收敛：代码自检（100% 可靠）+ AI 验证（语义补充），未通过则带精确反馈重做
4. 工业级稳定性：幂等性、容错、可观测性

处理流程：
    原始合同
        ↓
    [Stage 0] 规则引擎（确定性规则，0 API调用）
        - 术语替换、金额格式化、编号规范化
        - 委托白名单、首部保护、层级修复、签署区保护
        ↓
    [Stage 1] 合同分块（按"第X条"条款边界切分）
        - 每块不超过 MAX_CHUNK_CHARS 字符（约 3000 中文字）
        - 首部（合同标题、甲乙方、鉴于条款）单独成块
        - 签署区/附件单独成块
        - 超长条款按段落切分，仍超长按句子边界兜底
        - 短合同 = 1 个块（统一路径）
        ↓
    [Stage 2] 分块AI清洗（每块注入上下文前缀 + 独立3个AI pass）
        - Pass 1: 义务句式（添加"应当"）
        - Pass 2: 结构重组（删除小标题，建立1.1/1.2层级）
        - Pass 3: 格式清理（Markdown标记清理）
        ↓
    [Stage 3] 拼接 + 全文质量验证
        ↓
    [Stage 4] 收敛检测（最多max_rounds轮迭代）
        ↓
    [Stage 5] 最终润色 + 规则引擎防退化
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('industrial_cleaner')


class PassType(Enum):
    """清洗阶段类型"""
    TERMINOLOGY = "terminology"      # 术语替换
    OBLIGATION = "obligation"        # 义务句式
    AMOUNT = "amount"                # 金额格式
    STRUCTURE = "structure"          # 结构重组
    FORMAT = "format"                # 格式清理
    FINAL_POLISH = "final_polish"    # 最终润色


class QualityGate(Enum):
    """质量门状态"""
    PASSED = "passed"           # 通过
    FAILED = "failed"           # 失败（需要重洗）
    UNCHANGED = "unchanged"     # 无变化（收敛）


# ============================================================
# 合同分块机制
# ============================================================

# 每块最大字符数（约3000中文字 ≈ 6000 tokens 输入 + 3000 tokens 输出）
MAX_CHUNK_CHARS = 3000
# 签署区/附件块最小字符数（太短则并入上一块）
MIN_CHUNK_CHARS = 100


@dataclass
class ContractChunk:
    """合同分块"""
    chunk_id: int               # 分块序号（0-based）
    content: str                # 分块内容
    chunk_type: str             # 分块类型: "header" / "body" / "signature" / "appendix"
    article_range: str          # 条款范围描述（如"第1-3条"）
    needs_ai: bool = True       # 是否需要AI处理（首部和签署区可能不需要）


class ContractChunker:
    """
    合同分块器
    
    核心设计：
    1. 按条款边界（"第X条"）切分，保证语义完整
    2. 首部（标题+甲乙方+鉴于）单独成块
    3. 签署区/附件单独成块
    4. 每块不超过MAX_CHUNK_CHARS字符
    5. 太小的块合并到相邻块
    """
    
    # 条款边界正则
    ARTICLE_BOUNDARY = re.compile(
        r'^\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条',
        re.MULTILINE
    )
    
    # 签署区开始标记
    SIGNATURE_START = re.compile(
        r'[甲乙丙丁]方[（(][^）)]+[)）][：:]\s*_+'
        r'|[甲乙丙丁]方[盖章签名签字]*[：:]\s*_+'
        r'|日期[：:]\s*_+'
        r'|法定代表人[：:]\s*_+',
        re.MULTILINE
    )
    
    # 附件标记
    APPENDIX_START = re.compile(r'^附件[一二三四五六七八九十\d]+[：:]', re.MULTILINE)
    
    @classmethod
    def chunk(cls, text: str, max_chars: int = MAX_CHUNK_CHARS) -> List[ContractChunk]:
        """
        将合同文本分块
        
        Args:
            text: 规则引擎处理后的合同文本
            max_chars: 每块最大字符数
            
        Returns:
            分块列表
        """
        chunks: List[ContractChunk] = []
        
        # 第1步：定位签署区/附件的开始位置
        sig_match = cls.SIGNATURE_START.search(text)
        appendix_match = cls.APPENDIX_START.search(text)
        
        # 确定签署区/附件的起始位置
        sig_start = len(text)  # 默认没有签署区
        if sig_match:
            sig_start = sig_match.start()
        if appendix_match and appendix_match.start() < sig_start:
            sig_start = appendix_match.start()
        
        # 分离正文和签署区
        body_text = text[:sig_start].rstrip()
        sig_text = text[sig_start:] if sig_start < len(text) else ""
        
        # 第2步：定位所有条款边界
        boundaries = list(cls.ARTICLE_BOUNDARY.finditer(body_text))
        
        if not boundaries:
            # 没有条款编号，整块处理
            if body_text.strip():
                chunks.append(ContractChunk(
                    chunk_id=0,
                    content=body_text,
                    chunk_type="body",
                    article_range="无编号",
                    needs_ai=True
                ))
        else:
            # 第3步：提取首部（第一个条款之前的内容）
            first_article_start = boundaries[0].start()
            header_text = body_text[:first_article_start].rstrip()
            
            if header_text.strip():
                chunks.append(ContractChunk(
                    chunk_id=0,
                    content=header_text,
                    chunk_type="header",
                    article_range="首部",
                    needs_ai=False  # 首部由规则引擎处理，不需要AI
                ))
            
            # 第4步：按条款边界切分正文
            chunk_id = len(chunks)
            
            for i, boundary in enumerate(boundaries):
                article_start = boundary.start()
                # 当前条款到下一个条款之间的内容
                next_start = boundaries[i + 1].start() if i + 1 < len(boundaries) else len(body_text)
                article_content = body_text[article_start:next_start].rstrip()
                article_label = boundary.group().strip()
                
                # 检查单条是否超长
                if len(article_content) > max_chars * 1.5:
                    # 单条超长 → 按段落（空行）切分
                    sub_chunks = cls._split_by_paragraphs(
                        article_content, max_chars, article_label
                    )
                    for sc in sub_chunks:
                        sc.chunk_id = chunk_id
                        chunks.append(sc)
                        chunk_id += 1
                else:
                    chunks.append(ContractChunk(
                        chunk_id=chunk_id,
                        content=article_content,
                        chunk_type="body",
                        article_range=article_label,
                        needs_ai=True
                    ))
                    chunk_id += 1
        
        # 第5步：签署区/附件
        if sig_text.strip():
            chunks.append(ContractChunk(
                chunk_id=len(chunks),
                content=sig_text,
                chunk_type="signature",
                article_range="签署区/附件",
                needs_ai=False  # 签署区不需要AI处理
            ))
        
        # 第6步：合并太小的块
        chunks = cls._merge_small_chunks(chunks)
        
        # 第7步：合并相邻小块以减少API调用
        chunks = cls._merge_adjacent_chunks(chunks, max_chars)
        
        # 重新编号
        for i, chunk in enumerate(chunks):
            chunk.chunk_id = i
        
        logger.info(f"合同分块完成: {len(chunks)}块")
        for c in chunks:
            logger.info(f"  块{c.chunk_id} [{c.chunk_type}] {c.article_range} "
                       f"({len(c.content)}字符, AI={'是' if c.needs_ai else '否'})")
        
        return chunks
    
    @staticmethod
    def _describe_article_range(articles: List[str]) -> str:
        """生成条款范围描述"""
        if not articles:
            return "无条款"
        if len(articles) == 1:
            return articles[0]
        return f"{articles[0]}~{articles[-1]}"
    
    @classmethod
    def _split_by_paragraphs(cls, content: str, max_chars: int, 
                              article_label: str) -> List[ContractChunk]:
        """
        按段落（空行）切分超长条款，进一步按句子边界兜底
        
        借鉴semchunk层级递归分割思想：
        段落边界(\n\n) > 句子边界(。？！) > 从句边界(，；)
        
        v4.0增强: 如果段落切分后仍有超长段落，按句子边界进一步切分
        """
        # 按空行分段
        paragraphs = re.split(r'\n\s*\n', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if not paragraphs:
            return [ContractChunk(
                chunk_id=0, content=content, chunk_type="body",
                article_range=article_label, needs_ai=True
            )]
        
        # 提取条款标题行（第一段的第一行通常是标题）
        first_line = paragraphs[0].split('\n')[0] if paragraphs else article_label
        
        chunks: List[ContractChunk] = []
        current_parts: List[str] = []
        current_len = 0
        
        for para in paragraphs:
            # 如果加上这段就超限，先保存当前块
            if current_len + len(para) + 2 > max_chars and current_parts:
                chunks.append(ContractChunk(
                    chunk_id=0,
                    content='\n\n'.join(current_parts),
                    chunk_type="body",
                    article_range=f"{article_label}(续{len(chunks)+1})",
                    needs_ai=True
                ))
                current_parts = []
                current_len = 0
            
            # 检查单段落是否超长（需要按句子切分）
            if len(para) > max_chars:
                sub_parts = cls._split_by_sentences(para, max_chars)
                for sub in sub_parts:
                    if current_len + len(sub) + 2 > max_chars and current_parts:
                        chunks.append(ContractChunk(
                            chunk_id=0,
                            content='\n\n'.join(current_parts),
                            chunk_type="body",
                            article_range=f"{article_label}(续{len(chunks)+1})",
                            needs_ai=True
                        ))
                        current_parts = []
                        current_len = 0
                    current_parts.append(sub)
                    current_len += len(sub) + 2
            else:
                current_parts.append(para)
                current_len += len(para) + 2
        
        # 保存最后一块
        if current_parts:
            suffix = f"(续{len(chunks)+1})" if chunks else ""
            chunks.append(ContractChunk(
                chunk_id=0,
                content='\n\n'.join(current_parts),
                chunk_type="body",
                article_range=f"{article_label}{suffix}",
                needs_ai=True
            ))
        
        return chunks
    
    @staticmethod
    def _split_by_sentences(text: str, max_chars: int) -> List[str]:
        """
        按句子边界切分超长段落（借鉴semchunk递归分割）
        
        分隔符优先级：句号>问号>感叹号>分号>逗号
        """
        # 句子终止符
        sentence_endings = re.split(r'([。？！；，])', text)
        
        # 重新组合（保留分隔符）
        sentences = []
        for i in range(0, len(sentence_endings) - 1, 2):
            sentence = sentence_endings[i]
            if i + 1 < len(sentence_endings):
                sentence += sentence_endings[i + 1]
            if sentence.strip():
                sentences.append(sentence)
        
        # 处理最后一个（可能没有分隔符）
        if len(sentence_endings) % 2 == 1 and sentence_endings[-1].strip():
            sentences.append(sentence_endings[-1])
        
        if not sentences:
            return [text]
        
        # 按max_chars合并
        result = []
        current = ""
        for sent in sentences:
            if len(current) + len(sent) > max_chars and current:
                result.append(current)
                current = sent
            else:
                current += sent
        
        if current:
            result.append(current)
        
        return result
    
    @classmethod
    def _merge_adjacent_chunks(cls, chunks: List[ContractChunk], 
                                max_chars: int) -> List[ContractChunk]:
        """
        合并相邻的小块，减少API调用次数
        
        策略：
        1. 首部(header)块如果较小，合并到下一个body块（AI会看到首部上下文更好）
        2. 相邻的body块如果合并后不超限，就合并
        3. 签署区(signature)块不合并
        """
        if not chunks:
            return chunks
        
        merged = [chunks[0]]
        for chunk in chunks[1:]:
            prev = merged[-1]
            
            # 首部块合并到下一个body块
            if (prev.chunk_type == "header" and chunk.chunk_type == "body"
                    and len(prev.content) + len(chunk.content) + 2 <= max_chars * 1.2):
                prev.content = prev.content + "\n\n" + chunk.content
                prev.chunk_type = "body"
                prev.needs_ai = True
                prev.article_range = f"首部+{chunk.article_range}"
                continue
            
            # 相邻的body块合并
            if (prev.chunk_type == "body" and chunk.chunk_type == "body"
                    and prev.needs_ai and chunk.needs_ai
                    and len(prev.content) + len(chunk.content) + 2 <= max_chars):
                prev.content = prev.content + "\n\n" + chunk.content
                prev.article_range = f"{prev.article_range}+{chunk.article_range}"
            else:
                merged.append(chunk)
        
        return merged
    
    @classmethod
    def _merge_small_chunks(cls, chunks: List[ContractChunk]) -> List[ContractChunk]:
        """合并太小的块"""
        if not chunks:
            return chunks
        
        merged = [chunks[0]]
        for chunk in chunks[1:]:
            prev = merged[-1]
            # 如果前一块和当前块都很小，且类型相同或兼容，合并
            if (len(prev.content) < MIN_CHUNK_CHARS or len(chunk.content) < MIN_CHUNK_CHARS):
                # 首部+正文可以合并
                # 签署区不与正文合并
                if chunk.chunk_type != "signature" and prev.chunk_type != "signature":
                    prev.content = prev.content + "\n\n" + chunk.content
                    prev.chunk_type = "body"
                    prev.needs_ai = True
                    prev.article_range = f"{prev.article_range}+{chunk.article_range}"
                    continue
            merged.append(chunk)
        
        return merged


@dataclass
class CleaningPass:
    """单次清洗记录"""
    pass_type: PassType
    input_hash: str             # 输入内容哈希（用于追溯）
    output_hash: str            # 输出内容哈希
    timestamp: datetime
    duration_ms: int
    success: bool
    error_message: Optional[str] = None
    changes_summary: List[str] = field(default_factory=list)


@dataclass
class QualityCheckResult:
    """质量检查结果"""
    gate: QualityGate
    round_number: int
    issues_found: List[str]
    suggestions: List[str]
    diff_count: int             # 建议修改的数量
    timestamp: datetime
    structured_issues: List[Dict] = field(default_factory=list)  # 结构化问题（用于精确路由）


@dataclass
class CleaningSession:
    """完整清洗会话"""
    session_id: str
    original_content: str
    final_content: str
    passes: List[CleaningPass]
    quality_checks: List[QualityCheckResult]
    total_rounds: int
    convergence_reached: bool
    start_time: datetime
    end_time: Optional[datetime] = None
    
    def to_report(self) -> Dict:
        """生成报告"""
        return {
            "session_id": self.session_id,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            "total_rounds": self.total_rounds,
            "convergence_reached": self.convergence_reached,
            "final_passes": len(self.passes),
            "quality_checks": [
                {
                    "round": qc.round_number,
                    "result": qc.gate.value,
                    "issues": len(qc.issues_found),
                    "diff_count": qc.diff_count
                }
                for qc in self.quality_checks
            ]
        }


class PromptSegmenter:
    """
    Prompt分段器
    
    把完整的global_text_processing.md分成多个独立的子prompt
    每个子prompt只解决一类问题，提高准确性和可观测性
    """
    
    @staticmethod
    def get_obligation_prompt() -> str:
        """义务句式专用prompt"""
        return """# 义务句式规范化

你是一名专业的合同条款规范化专家。你的任务是**为义务性表述添加"应当"**，同时修正句式结构。

## ⛔ 不得修改已有内容

规则引擎已完成术语替换、金额格式化、条款标题加粗，**不得修改这些已处理的结果**。

## ⛔ 全角半角禁止规则

**绝对禁止将半角字符转为全角**：
- 禁止将半角数字0-9转为全角０-９（如"1.1"不能变成"１．１"）
- 禁止将半角英文字母转为全角（如"A"不能变成"Ａ"）
- 禁止将半角句号.转为全角间隔号．（如"1.1"不能变成"1．1"）
- 原合同用什么全角/半角，输出保持原样

## 核心任务：义务性动作必须用"应当"表达

合同中每一方对另一方的义务性动作，都必须用"应当"表述。**宁可多加，不可遗漏。**

### 必须添加"应当"的场景
- 甲/乙方义务动词前：支付、验收、归还、协助、承担、维修、退还、确保、培训等
- 孤立的"应"一律改为"应当"（"甲方应支付"→"甲方应当支付"）
- 孤立的"须"一律改为"应当"（"甲方须支付"→"甲方应当支付"）
- 双方义务性协商 → 双方应当协商

### 不需要添加"应当"的场景
- 已有"应当"的 | 权利性表述（有权/可以/享有/可）| 事实陈述（"本合同一式两份"）| 条件描述（"若甲方选择"）

## ⛔ 嵌套禁止（规范1.5.2）
同一主语在一句中**不得重复使用"应当"**。第二次出现的"应当"必须删除。
- 错误：乙方应当确保设备应当符合规范 → 正确：乙方应当确保设备符合规范
- 错误：甲方应当提供服务，甲方应当告知收费标准 → 正确：甲方应当提供服务并告知收费标准
- 错误：甲方应当遵守规定，若造成损坏，应当负责修复 → 正确：甲方应当遵守规定，若造成损坏，负责修复
- 正确：乙方应当支付价款，甲方应当出具发票（不同主语，不算嵌套）

## 句式完整性（规范3.1）
- 禁止"小标题+冒号+内容"句式（【句式待改写】标记处必须改写为完整句子）
- 禁止添加原文不存在的概括性标题

## 术语一致性（规范1.3）
同一概念必须使用同一术语（如"项目所在地"与"工程地点"应统一）。

## 输出格式
直接输出处理后的完整合同文本，不要有任何解释。"""

    @staticmethod
    def get_structure_prompt() -> str:
        """结构重组专用prompt"""
        return """# 结构层级规范化

你是一名专业的合同结构规范化专家。你的任务是**重组条款结构**。

## ⛔ 不得修改已有内容

规则引擎已完成术语替换、金额格式化、甲乙方格式、条款标题加粗、附件编号，**不得修改**。

## ⛔ 全角半角禁止规则

**绝对禁止将半角字符转为全角**：
- 禁止将半角数字0-9转为全角０-９
- 禁止将半角英文字母转为全角
- 禁止将半角句号.转为全角间隔号．
- 原合同用什么全角/半角，输出保持原样

## 必须执行的修改

1. **删除非标准小标题**（"租赁说明""备注""说明"等），建立标准层级：
   - 一级：**第一条**……（加粗，规则引擎已完成）
   - 二级：1.1、1.2……（不加粗）
   - 三级：（1）、（2）……（仅在有二级时使用）

2. **格式统一**："第X条"后加一个空格

## ⛔ 关键保护规则

### 首部保护
合同标题、甲乙方主体行、鉴于条款**不得编入条款编号**。

### 层级递进
一级编号后**不得直接用三级编号**。无需二级分层时用自然段落。

### 禁止内容添加
不得将甲乙方单位名称写入条款正文，不得添加概括性标题，不得合并压缩原文。

### 表格保护
表格结构（pipe表格|...|和grid表格+---+---+）**必须完整保留**：
- 不得删除表格行或分隔行，不得将表格内容转为自然语言
- 可以处理单元格内的文字（术语替换、添加"应当"等）

### 非表格格式→自然语言
只有非表格的逐字段翻译格式（"编号为X，名称为Y"）才转为自然语言。

### 签署区保护
签署区独立展示，不添加条款编号。

### 附件保护
附件标题独立，不与主合同连续编号，附件内部可独立编号。

### 指代明确
首次主体用全称，后续用"甲方"/"乙方"。禁止模糊"其"，跨条款指代必须明确。

### 无法确定时的处理
保留原文并加标记："【待确认】""【需人工审核】""【修正说明】"。代码标记的【近义术语待统一】保留。

### 条款标题加粗标记**必须完整保留**
规则引擎已将条款标题格式化为 `**第X条 标题**`（整体加粗）或 `**第X条**`（无标题时仅编号加粗）。**这两种格式必须原样保留，不得拆分、截断或部分移除**。
只有非条款标题的 `**` 加粗标记才可以移除。

## 输出格式
直接输出处理后的完整合同文本，不要有任何解释。"""

    @staticmethod
    def get_full_verification_prompt() -> str:
        """完整验证prompt（代码自检的补充）"""
        return """# 合同清洗质量检查（补充验证）

你是一名合同质量检查员。代码自检已完成确定性规则验证，你只需检查**语义层面**的问题。

## 语义检查清单

1. **义务句式**：义务性表述是否有"应当"？是否有遗漏？是否有嵌套"应当"？
2. **句式完整性**：是否有"小标题+冒号+内容"形式？【句式待改写】标记是否已处理？
3. **术语一致性**：同一概念是否用了不同表述？"本合同"与"本协议"是否混用？
4. **指代明确**：模糊"其"是否修正？跨条款指代是否明确？
5. **结构合理性**：首部是否被编入条款？层级递进是否正确？签署区是否独立？
6. **内容忠实度**：是否添加了原文不存在的概括性标题或内容？

## 输出格式

```json
{
  "status": "PASS" 或 "NEEDS_FIX",
  "issues_found": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"],
  "confidence": 0.95
}
```

**只输出JSON，不要有任何其他内容。**"""

    @staticmethod
    def get_format_prompt() -> str:
        """格式清理专用prompt"""
        return """# 格式清理

你是一名专业的合同格式清理专家。你的任务是**清理格式标记，统一排版**。

## ⛔ 不得修改已有内容

前面所有pass已完成术语替换、金额格式化、义务句式、结构重组、条款加粗等，**不得修改**。

## 格式清理规则

1. **移除Markdown标记**：规则引擎已将条款标题格式化为 `**第X条 标题**`（整体加粗）或 `**第X条**`（仅编号加粗），**这两种格式必须原样完整保留，不得拆分或截断**；其他非条款标题的 `**` 加粗标记一律移除；移除标题标记（`#`）、列表标记、斜体标记
2. **空格处理**：保留"第X条 "后一个空格，删除行首空格、连续多空格、段尾空格
3. **段落格式**：每段之间空一行，首行不缩进
4. **⛔ 不得改变全角半角**：原合同用什么标点（半角或全角），输出保持原样，不做任何括号、标点的全角半角转换。**尤其禁止**：半角数字→全角数字、半角英文→全角英文、半角句号.→全角间隔号．（如"1.1"绝不能变成"１．１"）

## 输出格式
直接输出处理后的完整合同文本，不要有任何解释。"""

    @classmethod
    def get_pass_sequence(cls) -> List[Tuple[PassType, Callable[[], str]]]:
        """
        获取完整的清洗阶段序列
        
        架构v2.0变更：术语替换+金额格式已由RuleEngine在Stage 1完成
        AI只负责语义理解（义务句式+结构重组+格式清理）
        """
        return [
            # Stage 1 (RuleEngine) 已在clean()方法中执行，无需API调用
            # Stage 2: AI语义处理
            (PassType.OBLIGATION, cls.get_obligation_prompt),
            (PassType.STRUCTURE, cls.get_structure_prompt),
            (PassType.FORMAT, cls.get_format_prompt),
        ]


class IndustrialContractCleaner:
    """
    工业级合同清洗器
    
    核心特性：
    1. 分段处理 - 每个阶段只解决一类问题
    2. 幂等性 - 相同输入产生相同输出
    3. 可观测性 - 详细的日志和报告
    4. 容错性 - 单阶段失败可回滚
    """
    
    def __init__(self, api_config, max_rounds: int = 3):
        self.api_config = api_config
        self.max_rounds = max_rounds
        self.session: Optional[CleaningSession] = None
        
    def _hash_content(self, content: str) -> str:
        """计算内容哈希（用于幂等性检查）"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def _classify_feedback(self, suggestions: List[str],
                            structured_issues: Optional[List[Dict]] = None) -> Dict[PassType, List[str]]:
        """
        按类型分发反馈（BUG-D02修复 + v5.0增强 + v5.1精确路由 + v5.2结构化路由）
        
        v5.2变更: 优先使用 VerificationIssue 的结构化字段（prompt_location）进行精确路由，
        不再依赖正则解析 suggestion 字符串。字符串解析仅作为无结构化信息时的回退。
        """
        feedback_by_type: Dict[PassType, List[str]] = {
            PassType.OBLIGATION: [],
            PassType.STRUCTURE: [],
            PassType.FORMAT: [],
        }
        
        # 从prompt_location到PassType的精确路由映射
        prompt_location_to_pass = {
            "义务Prompt": PassType.OBLIGATION,
            "结构Prompt": PassType.STRUCTURE,
            "格式Prompt": PassType.FORMAT,
        }
        
        # 分类关键词映射（回退方案）
        type_keywords = {
            PassType.OBLIGATION: ["应当", "义务", "句式", "义务性", "乙方提供", "甲方负责",
                                  "嵌套应当", "句式完整性", "待改写",
                                  "术语", "缴纳", "滞纳金", "罚款", "执行合同", "权力",
                                  "抵消", "抵销", "替换", "委托", "近义术语",
                                  "金额", "¥", "￥", "人民币", "格式化", "大小写"],
            PassType.STRUCTURE: ["标题", "层级", "结构", "小标题", "1.1", "第X条", "首部保护",
                                  "层级递进", "内容添加", "签署区", "附件保护", "指代明确"],
            PassType.FORMAT: ["格式", "标记", "Markdown", "加粗", "括号", "标点", "空格", "**", "日期格式"],
        }
        
        # v5.2: 如果有结构化issues，优先按 prompt_location 精确路由
        issue_lookup = {}
        if structured_issues:
            for idx, issue in enumerate(structured_issues):
                issue_lookup[idx] = issue
        
        for idx, suggestion in enumerate(suggestions):
            matched = False
            
            # 优先策略1：结构化路由（v5.2）
            if idx in issue_lookup:
                prompt_loc = issue_lookup[idx].get("prompt_location", "")
                if prompt_loc:
                    for loc_key, pass_type in prompt_location_to_pass.items():
                        if prompt_loc.startswith(loc_key):
                            feedback_by_type[pass_type].append(suggestion)
                            matched = True
                            break
            
            # 优先策略2：从 suggestion 字符串中提取 "参见Prompt:"（向后兼容）
            if not matched:
                prompt_loc_match = re.search(r'→ 参见Prompt:\s*(\S+?Prompt)', suggestion)
                if prompt_loc_match:
                    target_prompt = prompt_loc_match.group(1)
                    for loc_key, pass_type in prompt_location_to_pass.items():
                        if target_prompt == loc_key or target_prompt.startswith(loc_key):
                            feedback_by_type[pass_type].append(suggestion)
                            matched = True
                            break
            
            # 回退策略3：关键词匹配
            if not matched:
                for pt, keywords in type_keywords.items():
                    if any(kw in suggestion for kw in keywords):
                        feedback_by_type[pt].append(suggestion)
                        matched = True
                        break  # 每条反馈只分到一个类别
            
            # 兜底策略4：无法分类的反馈，发送到所有pass
            if not matched:
                for pt in feedback_by_type:
                    feedback_by_type[pt].append(suggestion)
        
        return feedback_by_type
    
    def _call_api(self, content: str, system_prompt: str, expect_json: bool = False,
                  pass_type: Optional[PassType] = None) -> str:
        """
        调用API（带重试和错误处理）

        Args:
            content: 合同内容
            system_prompt: 系统prompt
            expect_json: 是否期望JSON输出
            pass_type: 当前清洗阶段（用于错误消息定位）
        """
        import requests
        
        provider = self.api_config.provider or "anthropic"
        max_retries = 3
        stage_name = pass_type.value if pass_type else "未知阶段"
        
        for attempt in range(max_retries):
            try:
                if provider == "anthropic":
                    result = self._call_anthropic(content, system_prompt, expect_json, pass_type)
                else:
                    result = self._call_openai_compatible(content, system_prompt, expect_json, pass_type)
                
                return result
                
            except Exception as e:
                logger.warning(f"API调用失败（阶段={stage_name}，尝试{attempt+1}/{max_retries}）: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    raise
    
    def _call_anthropic(self, content: str, system_prompt: str, expect_json: bool,
                        pass_type: Optional[PassType] = None) -> str:
        """调用Claude API"""
        import requests
        
        stage_name = pass_type.value if pass_type else "未知阶段"
        
        headers = {
            "x-api-key": self.api_config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.api_config.model or "claude-3-5-sonnet-20241022",
            "max_tokens": 8192,
            "temperature": 0.1,  # 低温度确保确定性
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": content}
            ]
        }
        
        response = requests.post(
            f"{self.api_config.base_url or 'https://api.anthropic.com'}/v1/messages",
            headers=headers,
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        
        result = response.json()
        
        stop_reason = result.get('stop_reason')
        if stop_reason == 'max_tokens':
            raise RuntimeError(
                f"阶段[{stage_name}]输出被截断（max_tokens限制）！"
                f"合同内容可能不完整，请减小输入或增加max_tokens"
            )
        
        text = result['content'][0]['text']
        
        # 如果期望JSON，尝试解析
        if expect_json:
            return self._extract_json(text)
        
        return text
    
    def _call_openai_compatible(self, content: str, system_prompt: str, expect_json: bool,
                                pass_type: Optional[PassType] = None) -> str:
        """调用OpenAI兼容API"""
        import requests
        
        stage_name = pass_type.value if pass_type else "未知阶段"
        
        headers = {
            "Authorization": f"Bearer {self.api_config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.api_config.model or "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            "temperature": 0.1,
            "max_tokens": 8192
        }
        
        response = requests.post(
            f"{self.api_config.base_url or 'https://api.openai.com'}/chat/completions",
            headers=headers,
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        
        result = response.json()
        
        finish_reason = result['choices'][0].get('finish_reason')
        if finish_reason == 'length':
            raise RuntimeError(
                f"阶段[{stage_name}]输出被截断（max_tokens限制）！"
                f"合同内容可能不完整，请减小输入或增加max_tokens"
            )
        
        text = result['choices'][0]['message']['content']
        
        if expect_json:
            return self._extract_json(text)
        
        return text
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON"""
        # 查找 ```json ... ```
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        
        # 查找 ``` ... ```
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        
        # 查找 { ... }
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        
        return text
    
    def _execute_pass(self, content: str, pass_type: PassType, 
                     prompt_func: Callable[[], str]) -> Tuple[str, CleaningPass]:
        """
        执行单个清洗阶段
        """
        input_hash = self._hash_content(content)
        prompt = prompt_func()
        
        logger.info(f"开始阶段: {pass_type.value}")
        start_time = time.time()
        
        try:
            result = self._call_api(content, prompt, pass_type=pass_type)
            
            duration_ms = int((time.time() - start_time) * 1000)
            output_hash = self._hash_content(result)
            
            # 计算变化
            changes = self._summarize_changes(content, result)
            
            cleaning_pass = CleaningPass(
                pass_type=pass_type,
                input_hash=input_hash,
                output_hash=output_hash,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                success=True,
                changes_summary=changes
            )
            
            logger.info(f"阶段完成: {pass_type.value}, 耗时{duration_ms}ms, 变化: {len(changes)}项")
            return result, cleaning_pass
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            cleaning_pass = CleaningPass(
                pass_type=pass_type,
                input_hash=input_hash,
                output_hash=input_hash,  # 失败时输出等于输入
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                success=False,
                error_message=str(e)
            )
            logger.error(f"阶段失败: {pass_type.value}, 错误: {e}")
            raise
    
    def _summarize_changes(self, old: str, new: str) -> List[str]:
        """总结两个文本之间的变化"""
        import difflib
        
        changes = []
        diff = list(difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            lineterm='',
            n=0
        ))
        
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                changes.append(f"添加: {line[1:50]}...")
            elif line.startswith('-') and not line.startswith('---'):
                changes.append(f"删除: {line[1:50]}...")
        
        return changes[:10]  # 最多返回10条
    
    def _quality_verification(self, content: str, round_number: int,
                               original: str = "") -> QualityCheckResult:
        """
        质量验证 — 双轨制：代码自检（100%可靠） + AI验证（补充）
        
        v5.0变更: 先跑 self_verifier 代码自检，ERROR 级别问题 100% 可靠；
        再用 AI 验证作为补充，捕获语义层面的问题。
        两路结果合并后决定是否需要重做。
        """
        logger.info(f"开始第{round_number}轮质量验证（双轨制）")
        
        all_issues = []
        all_suggestions = []
        structured_issues = []
        
        # ============================================================
        # 第一轨：代码自检（100%可靠，0 API调用）
        # ============================================================
        try:
            from self_verifier import ContractSelfVerifier
            verifier = ContractSelfVerifier()
            code_report = verifier.verify(original, content)
            
            code_errors = [i for i in code_report.issues if i.severity == "ERROR"]
            code_warnings = [i for i in code_report.issues if i.severity == "WARNING"]
            
            for issue in code_errors:
                all_issues.append(f"[代码自检-ERROR] {issue.rule}: {issue.message}")
                # 精确定位：规范条款号 + Prompt位置 + 修复提示
                spec_info = f"（规范{issue.spec_ref}）" if issue.spec_ref else ""
                prompt_loc = f"→ 参见Prompt: {issue.prompt_location}" if issue.prompt_location else ""
                suggestion_text = f"{issue.rule}{spec_info} — {issue.suggestion}（位置: {issue.location[:50]}）"
                if prompt_loc:
                    suggestion_text += f"\n    {prompt_loc}"
                all_suggestions.append(suggestion_text)
                structured_issues.append({
                    "source": "code",
                    "severity": issue.severity,
                    "rule": issue.rule,
                    "prompt_location": issue.prompt_location,
                    "suggestion": suggestion_text,
                })
            
            for issue in code_warnings:
                all_issues.append(f"[代码自检-WARNING] {issue.rule}: {issue.message}")
                spec_info = f"（规范{issue.spec_ref}）" if issue.spec_ref else ""
                prompt_loc = f"→ 参见Prompt: {issue.prompt_location}" if issue.prompt_location else ""
                suggestion_text = f"{issue.rule}{spec_info} — {issue.suggestion}"
                if prompt_loc:
                    suggestion_text += f"\n    {prompt_loc}"
                all_suggestions.append(suggestion_text)
                structured_issues.append({
                    "source": "code",
                    "severity": issue.severity,
                    "rule": issue.rule,
                    "prompt_location": issue.prompt_location,
                    "suggestion": suggestion_text,
                })
            
            logger.info(f"代码自检: {len(code_errors)}个ERROR, {len(code_warnings)}个WARNING")
            
            if code_errors:
                for err in code_errors[:5]:
                    logger.warning(f"  ✗ [代码自检] {err.rule}: {err.message}")
            else:
                logger.info("  ✓ 代码自检无ERROR")
                
        except Exception as e:
            logger.error(f"代码自检执行失败: {e}")
        
        # ============================================================
        # 第二轨：AI验证（补充语义层面检查）
        # ============================================================
        prompt = PromptSegmenter.get_full_verification_prompt()
        
        try:
            result_json = self._call_api(content, prompt, expect_json=True,
                                          pass_type=PassType.FINAL_POLISH)
            result = json.loads(result_json)
            
            ai_status = result.get("status", "NEEDS_FIX")
            ai_issues = result.get("issues_found", [])
            ai_suggestions = result.get("suggestions", [])
            
            for issue in ai_issues:
                if issue not in all_issues:  # 去重
                    all_issues.append(f"[AI验证] {issue}")
            
            for suggestion in ai_suggestions:
                if suggestion not in all_suggestions:
                    all_suggestions.append(suggestion)
            
            logger.info(f"AI验证: {ai_status}, {len(ai_issues)}个问题")
            
        except Exception as e:
            logger.error(f"AI验证失败: {e}")
            # AI验证失败不影响代码自检的结果
        
        # ============================================================
        # 合并判断：代码自检有ERROR → 必须重做
        # ============================================================
        code_error_count = sum(1 for i in all_issues if i.startswith("[代码自检-ERROR]"))
        ai_error_count = sum(1 for i in all_issues if i.startswith("[AI验证]"))
        
        if code_error_count == 0 and ai_error_count == 0:
            gate = QualityGate.PASSED
        elif code_error_count == 0 and ai_error_count > 0:
            # 只有AI发现问题，降级为WARNING（AI不一定对）
            gate = QualityGate.PASSED  # 代码自检通过就放行
            logger.info("代码自检通过，AI问题降级为参考（不影响收敛判断）")
        else:
            gate = QualityGate.FAILED
        
        check_result = QualityCheckResult(
            gate=gate,
            round_number=round_number,
            issues_found=all_issues,
            suggestions=all_suggestions,
            diff_count=len(all_issues),
            timestamp=datetime.now(),
            structured_issues=structured_issues
        )
        
        logger.info(f"双轨质量验证完成: {gate.value}, "
                    f"代码自检ERROR={code_error_count}, AI问题={ai_error_count}")
        return check_result
    
    def clean(self, content: str) -> CleaningSession:
        """
        执行完整清洗流程
        
        架构v4.1 — 统一分块路径 + 最终润色:
        Stage 0: 规则引擎（确定性规则，0 API调用，全文处理）
        Stage 1: 合同分块（按条款边界切分，短合同=1块）
        Stage 2: 分块AI清洗（每块注入上下文前缀 + 独立3个AI pass）
        Stage 3: 拼接 + 全文质量验证
        Stage 4: 收敛检测
        Stage 5: 最终润色（极简提示词，修语法/句法/低级错误/怪异表达）
        
        v4.0变更: 统一为单条路径，短合同作为"1个块"的特例走分块流程
        """
        session_id = self._hash_content(content + str(time.time()))
        
        self.session = CleaningSession(
            session_id=session_id,
            original_content=content,
            final_content=content,
            passes=[],
            quality_checks=[],
            total_rounds=0,
            convergence_reached=False,
            start_time=datetime.now()
        )
        
        # ============================================================
        # Stage 0: 规则引擎（确定性规则，0 API调用，全文处理）
        # ============================================================
        logger.info("\n" + "="*60)
        logger.info("Stage 0: 规则引擎（确定性规则，0 API调用）")
        logger.info("="*60)
        
        from rule_engine import RuleEngine
        rule_engine = RuleEngine()
        current_content, rule_changes = rule_engine.apply_all_rules(content)
        
        # 内容添加检测（对比原始和规则引擎输出）
        has_addition, addition_issues = rule_engine.detect_content_addition(content, current_content)
        if has_addition:
            for issue in addition_issues:
                logger.warning(f"⚠ {issue}")
                rule_changes.append(f"⚠ {issue}")
        
        if rule_changes:
            logger.info(f"规则引擎执行了{len(rule_changes)}项确定性修改:")
            for change in rule_changes:
                logger.info(f"  - {change}")
            
            # 记录规则引擎pass
            self.session.passes.append(CleaningPass(
                pass_type=PassType.OBLIGATION,  # 规则引擎现在覆盖术语+金额+格式
                input_hash=self._hash_content(content),
                output_hash=self._hash_content(current_content),
                timestamp=datetime.now(),
                duration_ms=0,  # 无API调用
                success=True,
                changes_summary=rule_changes
            ))
        else:
            logger.info("规则引擎: 无需修改")
        
        # ============================================================
        # Stage 1: 合同分块（短合同=1块，长合同按条款切分）
        # ============================================================
        logger.info("\n" + "="*60)
        logger.info("Stage 1: 合同分块")
        logger.info("="*60)
        
        chunks = ContractChunker.chunk(current_content)
        ai_chunks = [c for c in chunks if c.needs_ai]
        logger.info(f"合同共{len(chunks)}块（其中{len(ai_chunks)}块需要AI处理）")
        
        # ============================================================
        # Stage 2-4: 统一分块AI清洗（所有合同走同一条路径）
        # Stage 5: 最终润色（在_clean_chunks中执行）
        # ============================================================
        current_content = self._clean_chunks(chunks, current_content)
        
        # 完成会话
        self.session.final_content = current_content
        
        # AI处理后内容添加检测
        rule_engine_check = RuleEngine()
        has_addition, addition_issues = rule_engine_check.detect_content_addition(
            content, current_content
        )
        if has_addition:
            logger.warning("⚠ AI处理后内容添加检测发现问题:")
            for issue in addition_issues:
                logger.warning(f"  ⚠ {issue}")
        
        self.session.end_time = datetime.now()
        
        return self.session
    
    def _build_context_prefix(self, chunks: List[ContractChunk], 
                               chunk: ContractChunk,
                               full_text: str) -> str:
        """
        为每个块构建上下文前缀（借鉴LLM×MapReduce结构化信息协议）
        
        让AI知道：
        1. 这是哪份合同、甲乙方是谁
        2. 当前处理的是哪一部分
        3. 全文共有多少条款
        4. 跨块一致性要求
        
        这解决了分块后AI"看不到全文"的根本问题。
        """
        # 提取合同标题
        title = ""
        for line in full_text.split('\n')[:10]:  # 只看前10行
            stripped = line.strip().strip('*').strip()
            if stripped and ('合同' in stripped or '协议' in stripped or '书' in stripped):
                title = stripped
                break
        
        # 提取甲乙方
        parties = []
        for line in full_text.split('\n')[:20]:
            stripped = line.strip()
            match = re.match(r'^[甲乙丙丁]方[（(]?[^）)]*[)）]?[：:]\s*(.+)', stripped)
            if match:
                parties.append(match.group(1).strip())
        
        # 统计总条款数
        total_articles = len(re.findall(
            r'^\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条', full_text, re.MULTILINE
        ))
        
        # 构建前缀
        parts = ["【合同上下文 — 请严格遵循】"]
        if title:
            parts.append(f"合同名称: {title}")
        if parties:
            parts.append(f"合同主体: {'; '.join(parties)}")
        if total_articles > 0:
            parts.append(f"全文共{total_articles}条条款")
        parts.append(f"当前处理: {chunk.article_range}")
        parts.append("")
        parts.append("跨块一致性要求:")
        parts.append("- 术语必须与全文保持一致（如'支付'不能改成'缴纳'）")
        parts.append("- 不要重复添加'应当'（其他条款可能已添加）")
        parts.append("- 条款编号必须与上下文衔接，不要重新编号")
        parts.append("- 不要将甲乙方信息写入条款正文")
        parts.append("")
        
        return "\n".join(parts)
    
    def _clean_chunks(self, chunks: List[ContractChunk], 
                       full_text: str) -> str:
        """
        统一的分块AI清洗（v4.0 单一路径）
        
        所有合同（无论长短）都走这条路径：
        1. 每块注入上下文前缀
        2. 每块独立经过3个AI pass
        3. 拼接所有块
        4. 全文质量验证（代码自检 + AI验证，双轨制）
        5. 收敛检测（最多max_rounds轮）
        
        短合同只是"1个块"的特例，逻辑完全相同。
        
        v5.0变更: 质量验证改为双轨制（代码自检100%可靠 + AI验证补充）
        代码自检的ERROR直接决定收敛，不依赖AI判断
        """
        current_content = full_text
        previous_feedback_by_type: Dict[PassType, List[str]] = {}
        original_content = full_text  # 保存原始文本用于代码自检
        
        for round_num in range(1, self.max_rounds + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"第{round_num}/{self.max_rounds}轮清洗")
            logger.info(f"{'='*60}")
            
            self.session.total_rounds = round_num
            
            if round_num == 1:
                # === 第1轮：分块AI清洗 ===
                logger.info("Stage 2: 分块AI清洗（带上下文前缀）")
                
                cleaned_chunks: List[Tuple[int, str]] = []  # (chunk_id, cleaned_content)
                
                for chunk in chunks:
                    if not chunk.needs_ai:
                        # 首部和签署区不需要AI处理
                        logger.info(f"  块{chunk.chunk_id} [{chunk.chunk_type}] 跳过AI处理")
                        cleaned_chunks.append((chunk.chunk_id, chunk.content))
                        continue
                    
                    logger.info(f"\n  --- 清洗块{chunk.chunk_id} [{chunk.chunk_type}] "
                               f"{chunk.article_range} ({len(chunk.content)}字符) ---")
                    
                    context_prefix = self._build_context_prefix(chunks, chunk, full_text)
                    
                    chunk_content = chunk.content
                    for pass_type, prompt_func in PromptSegmenter.get_pass_sequence():
                        try:
                            # 注入上下文前缀 + 合同内容
                            input_content = context_prefix + chunk_content
                            
                            chunk_content, cleaning_pass = self._execute_pass(
                                input_content, pass_type, prompt_func
                            )
                            cleaning_pass.changes_summary.insert(
                                0, f"[块{chunk.chunk_id}] {chunk.article_range}"
                            )
                            self.session.passes.append(cleaning_pass)
                        except Exception as e:
                            logger.error(f"  块{chunk.chunk_id} {pass_type.value}阶段失败: {e}")
                            # 分块模式下，单块失败不终止，保留该块原始内容
                            break
                    
                    cleaned_chunks.append((chunk.chunk_id, chunk_content))
                
                # 拼接
                cleaned_chunks.sort(key=lambda x: x[0])
                current_content = "\n\n".join(content for _, content in cleaned_chunks)
                
                # 清理多余空行（拼接可能产生连续空行）
                current_content = re.sub(r'\n{3,}', '\n\n', current_content)
                
            else:
                # === 收敛轮：带反馈的全文清洗 ===
                logger.info(f"Stage 4: 收敛轮（带反馈）")
                
                for pass_type, prompt_func in PromptSegmenter.get_pass_sequence():
                    try:
                        input_content = current_content
                        pass_feedback = previous_feedback_by_type.get(pass_type, [])
                        if pass_feedback:
                            # 精确反馈注入：每条反馈都带规范条款号和Prompt位置
                            # 从节约token的角度，只注入与当前pass相关的反馈
                            feedback_prefix = "【⚠️ 上一轮自检未通过，以下问题必须修正】\n\n"
                            for i, s in enumerate(pass_feedback):
                                feedback_prefix += f"{i+1}. {s}\n\n"
                            feedback_prefix += "=== 请按上述反馈中的规范条款和Prompt位置重新执行 ===\n\n"
                            feedback_prefix += "=== 待清洗内容 ===\n\n"
                            input_content = feedback_prefix + current_content
                            logger.info(f"已注入{pass_type.value}阶段反馈（{len(pass_feedback)}条，含规范定位）")
                        
                        current_content, cleaning_pass = self._execute_pass(
                            input_content, pass_type, prompt_func
                        )
                        self.session.passes.append(cleaning_pass)
                    except Exception as e:
                        logger.error(f"收敛轮{pass_type.value}阶段失败: {e}")
                        break
            
            # === 质量验证（双轨制：代码自检 + AI验证） ===
            quality_result = self._quality_verification(
                current_content, round_num, original=original_content
            )
            self.session.quality_checks.append(quality_result)
            
            # === 收敛检测 ===
            if quality_result.gate in (QualityGate.PASSED, QualityGate.UNCHANGED):
                logger.info(f"✓ 第{round_num}轮{'通过质量验证' if quality_result.gate == QualityGate.PASSED else '无变化'}，清洗完成")
                self.session.convergence_reached = True
                break
            elif quality_result.gate == QualityGate.FAILED:
                logger.warning(f"✗ 第{round_num}轮未通过，发现{quality_result.diff_count}个问题")
                if round_num < self.max_rounds:
                    if quality_result.suggestions:
                        previous_feedback_by_type = self._classify_feedback(
                            quality_result.suggestions,
                            structured_issues=quality_result.structured_issues
                        )
                        logger.info(f"已保存{len(quality_result.suggestions)}条反馈建议")
                    else:
                        previous_feedback_by_type = {}
                else:
                    logger.warning(f"达到最大轮次({self.max_rounds})，强制结束")
        
        # ============================================================
        # 兜底修复：嵌套应当确定性修复（规范1.5.2）
        # AI可能未能完全消除嵌套应当，用规则引擎做最终兜底
        # ============================================================
        from rule_engine import RuleEngine
        fix_engine = RuleEngine()
        fixed_content, fix_changes = fix_engine.apply_nested_yingdang_fix(current_content)
        if fix_changes:
            logger.info(f"嵌套应当兜底修复: {len(fix_changes)}处")
            for fc in fix_changes:
                logger.info(f"  - {fc}")
            current_content = fixed_content
        
        # ============================================================
        # Stage 5: 最终润色（极简提示词，修语法/句法/低级错误/怪异表达）
        # ============================================================
        logger.info("\n" + "="*60)
        logger.info("Stage 5: 最终润色")
        logger.info("="*60)
        
        polish_prompt = (
            '你是一位中文法律文书润色专家。你的唯一任务是：\n'
            '修正下面合同文档中的语法错误、句法错误、低级错误和表达怪异的地方。\n\n'
            '规则：\n'
            '1. 只修错误和怪异表达，不改变任何法律含义\n'
            '2. 不改变文档结构（条款编号、标题、段落划分）\n'
            '3. 不改变术语和已经规范化的用词（如"应当""支付""逾期付款违约金"等）\n'
            '4. 保持Markdown格式不变\n'
            '5. 不改变全角半角（原合同用什么标点，输出保持原样，不做括号、标点的全角半角转换）。绝对禁止：半角数字→全角数字（0→０）、半角英文→全角英文（A→Ａ）、半角句号→全角间隔号（.→．），如"1.1"绝不能变成"１．１"\n'
            '6. 如果没有需要修正的地方，原样输出\n'
            '7. 直接输出修正后的全文，不要解释\n'
        )
        
        try:
            polish_start = time.time()
            polished = self._call_api(
                current_content, polish_prompt,
                expect_json=False, pass_type=PassType.FINAL_POLISH
            )
            polish_duration_ms = int((time.time() - polish_start) * 1000)
            
            # 基本安全检查：润色后不应大幅缩水
            if len(polished) < len(current_content) * 0.8:
                logger.warning(f"润色后内容异常缩短（{len(current_content)}→{len(polished)}），跳过润色")
            else:
                current_content = polished
                logger.info("润色完成")
                
                # 润色后重新应用规则引擎确定性规则（修复润色可能引入的退化，如¥符号、术语回退等）
                polish_fix_engine = RuleEngine()
                current_content, polish_fixes = polish_fix_engine.apply_all_rules(current_content)
                if polish_fixes:
                    logger.info(f"润色后规则引擎修正: {len(polish_fixes)}处（修复润色退化）")
                
                # 记录润色pass
                self.session.passes.append(CleaningPass(
                    pass_type=PassType.FINAL_POLISH,
                    input_hash=self._hash_content(fixed_content if fix_changes else current_content),
                    output_hash=self._hash_content(current_content),
                    timestamp=datetime.now(),
                    duration_ms=polish_duration_ms,
                    success=True,
                    changes_summary=["最终润色：修正语法/句法/低级错误/怪异表达"]
                ))
        except Exception as e:
            logger.warning(f"润色pass失败（非致命），跳过: {e}")
        
        return current_content
    
    def get_detailed_report(self) -> str:
        """生成详细报告"""
        if not self.session:
            return "无清洗会话"
        
        s = self.session
        lines = [
            "\n" + "="*70,
            "工业级合同清洗详细报告",
            "="*70,
            f"会话ID: {s.session_id}",
            f"开始时间: {s.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"结束时间: {s.end_time.strftime('%Y-%m-%d %H:%M:%S') if s.end_time else 'N/A'}",
            f"总耗时: {(s.end_time - s.start_time).total_seconds():.1f}秒" if s.end_time else "",
            f"总轮次: {s.total_rounds}/{self.max_rounds}",
            f"是否收敛: {'是' if s.convergence_reached else '否'}",
            "",
            "清洗阶段详情:",
            "-"*70,
        ]
        
        for i, p in enumerate(s.passes, 1):
            lines.append(f"\n{i}. [{p.pass_type.value}] {p.timestamp.strftime('%H:%M:%S')}")
            lines.append(f"   状态: {'✓ 成功' if p.success else '✗ 失败'}")
            lines.append(f"   耗时: {p.duration_ms}ms")
            lines.append(f"   输入哈希: {p.input_hash}")
            lines.append(f"   输出哈希: {p.output_hash}")
            if p.changes_summary:
                lines.append(f"   主要变化:")
                for change in p.changes_summary[:3]:
                    lines.append(f"     - {change}")
        
        lines.extend([
            "",
            "质量验证详情:",
            "-"*70,
        ])
        
        for qc in s.quality_checks:
            lines.append(f"\n第{qc.round_number}轮:")
            lines.append(f"  结果: {qc.gate.value}")
            lines.append(f"  问题数: {len(qc.issues_found)}")
            lines.append(f"  建议修改数: {qc.diff_count}")
            if qc.issues_found:
                lines.append(f"  问题列表:")
                for issue in qc.issues_found[:5]:
                    lines.append(f"    - {issue}")
        
        lines.extend([
            "",
            "="*70,
            "结论:",
            "="*70,
        ])
        
        if s.convergence_reached:
            lines.append("✓ 清洗成功完成，质量验证通过或已收敛")
        else:
            lines.append("⚠ 达到最大轮次但未完全收敛，建议人工检查")
        
        lines.append("="*70 + "\n")
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='工业级合同清洗系统（分段Prompt + 两轮验证）'
    )
    parser.add_argument('--input', '-i', required=True, help='输入合同文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出文件路径')
    parser.add_argument('--max-rounds', '-r', type=int, default=3, 
                       help='最大清洗轮次（默认3）')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 读取输入
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {input_path}")
        sys.exit(1)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"读取文件: {input_path}")
    print(f"文件大小: {len(content)}字符")
    
    # 加载API配置（复用auto_cleaner的配置）
    sys.path.insert(0, str(Path(__file__).parent))
    from auto_cleaner import load_api_config
    
    api_config = load_api_config()
    if not api_config.api_key:
        print("错误: 未配置API Key，请先运行: python auto_cleaner.py --config")
        sys.exit(1)
    
    # 执行清洗
    cleaner = IndustrialContractCleaner(
        api_config=api_config,
        max_rounds=args.max_rounds
    )
    
    try:
        session = cleaner.clean(content)
        
        # 写入输出
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(session.final_content)
        
        print(f"\n✓ 清洗完成，输出保存至: {output_path}")
        
        # 输出报告
        if args.verbose:
            print(cleaner.get_detailed_report())
        else:
            report = session.to_report()
            print(f"\n摘要:")
            print(f"  总轮次: {report['total_rounds']}")
            print(f"  是否收敛: {'是' if report['convergence_reached'] else '否'}")
            print(f"  清洗阶段数: {report['final_passes']}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n✗ 清洗失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
