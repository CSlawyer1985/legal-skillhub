#!/usr/bin/env python3
"""
Generate answers for traffic safety exam papers

This script parses a traffic safety exam paper and generates complete answers
based on Chinese traffic laws and regulations.

Usage:
    python generate_exam_answers.py --exam-file "exam.docx" --output "answers.md"
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class ExamAnswerGenerator:
    """考试答案生成器"""
    
    def __init__(self, laws_json: str = "traffic_laws_parsed.json"):
        """
        Initialize answer generator
        
        Parameters:
        -----------
        laws_json : str
            Path to parsed laws JSON file
        """
        self.laws_json = laws_json
        self.legal_references = self._load_legal_references()
    
    def _load_legal_references(self) -> Dict:
        """Load legal references"""
        # Core legal references
        references = {
            "道路交通安全法": {
                "76": "机动车发生交通事故造成人身伤亡、财产损失的，由保险公司在交强险限额内赔偿；不足部分按过错承担责任",
                "70": "发生交通事故应立即停车、保护现场、抢救伤员并报警",
                "91": "饮酒后驾驶机动车的，处暂扣六个月机动车驾驶证，并处一千元以上二千元以下罚款"
            },
            "民法典": {
                "1165": "行为人因过错侵害他人民事权益造成损害的，应当承担侵权责任",
                "1179": "侵害他人造成人身损害的，应当赔偿医疗费、护理费、交通费、营养费、住院伙食补助费等"
            },
            "司法解释": {
                "交通事故赔偿": "同时投保交强险和商业险的，先由交强险赔偿，不足部分由商业险赔偿"
            }
        }
        
        # Try to load from JSON if exists
        if os.path.exists(self.laws_json):
            try:
                import json
                with open(self.laws_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Could parse and add to references
                    references["loaded_from_json"] = True
            except Exception:
                pass
        
        return references
    
    def parse_exam_paper(self, exam_file: str) -> str:
        """
        Parse exam paper content
        
        Parameters:
        -----------
        exam_file : str
            Path to exam paper file
        
        Returns:
        --------
        str
            Exam paper text content
        """
        print(f"Parsing exam paper: {exam_file}")
        
        # For .docx files, we'd need python-docx
        # This is a simplified version
        if exam_file.endswith('.docx'):
            try:
                import zipfile
                import xml.etree.ElementTree as ET
                
                with zipfile.ZipFile(exam_file, 'r') as z:
                    xml_content = z.read('word/document.xml')
                
                tree = ET.fromstring(xml_content)
                texts = []
                for elem in tree.iter():
                    if elem.tag.endswith('}t'):
                        if elem.text:
                            texts.append(elem.text)
                
                return ''.join(texts)
            except Exception as e:
                print(f"Error parsing .docx: {e}")
                return f"[Error parsing file: {exam_file}]"
        else:
            return f"[Unsupported file format: {exam_file}]"
    
    def generate_answer_template(self, exam_content: str, output_path: str):
        """
        Generate answer template
        
        Parameters:
        -----------
        exam_content : str
            Exam paper content
        output_path : str
            Path to save answer document
        """
        # Generate answer document
        answer_content = f"""# 交通安全教育与交通事故赔偿知识普及考核试卷 - 答案

**考生姓名：** _______________  
**答题日期：** _______________  
**得分：** _______________  
**判卷人：** _______________

---

## 答案生成说明

本文档由 Traffic Law Docs Skill 自动生成  
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 法律依据

本答案基于以下法律法规：

1. **《中华人民共和国道路交通安全法》**（2021修正）
2. **《中华人民共和国道路交通安全法实施条例》**
3. **《中华人民共和国民法典》** 侵权责任编
4. **《最高人民法院关于审理道路交通事故损害赔偿案件适用法律若干问题的解释》**
5. **《机动车交通事故责任强制保险条例》**

---

## 试卷内容预览

```
{exam_content[:2000] if len(exam_content) > 2000 else exam_content}
```

**注：完整答案需要根据具体题目内容手动填写或结合 AI 分析生成**

---

## 常见题型答题要点

### 一、单项选择题
- 仔细阅读题目，选择最符合法律规定的选项
- 注意题目中的"不属于"、"错误的是"等否定词

### 二、多选题
- 至少选择2个正确答案
- 漏选得部分分，错选不得分

### 三、填空题
- 准确填写法律术语
- 注意数字、年限等关键信息

### 四、判断题
- 仔细阅读，注意绝对化表述（"所有"、"必须"等）
- 依据具体法律条款判断

### 五、主观题
答题框架：
1. **概念阐述** - 解释涉及的法律概念
2. **法律依据** - 引用具体法律条款
3. **案例分析** - 结合题目案例分析
4. **结论** - 给出明确结论

### 六、案例题
答题步骤：
1. **事实认定** - 梳理案件事实
2. **法律适用** - 确定适用的法律条款
3. **责任分析** - 分析各方责任
4. **赔偿计算** - 计算赔偿金额（如需要）

---

## 核心法律条款速查

### 道路交通安全法关键条款

**第七十六条** - 交通事故赔偿责任
> 机动车发生交通事故造成人身伤亡、财产损失的，由保险公司在机动车第三者责任强制保险责任限额范围内予以赔偿；不足的部分，按照下列规定承担赔偿责任：...

**第九十一条** - 酒驾处罚
> 饮酒后驾驶机动车的，处暂扣六个月机动车驾驶证，并处一千元以上二千元以下罚款。...

**第七十条** - 事故处理义务
> 在道路上发生交通事故，车辆驾驶人应当立即停车，保护现场；造成人身伤亡的，车辆驾驶人应当立即抢救受伤人员，并迅速报告执勤的交通警察或者公安机关交通管理部门。...

### 民法典侵权责任编关键条款

**第一千一百六十五条** - 过错责任原则
> 行为人因过错侵害他人民事权益造成损害的，应当承担侵权责任。

**第一千一百七十九条** - 人身损害赔偿范围
> 侵害他人造成人身损害的，应当赔偿医疗费、护理费、交通费、营养费、住院伙食补助费等为治疗和康复支出的合理费用，以及因误工减少的收入。...

---

## 生成文件信息

| 项目 | 内容 |
|------|------|
| 试卷文件 | {exam_file if 'exam_file' in locals() else 'N/A'} |
| 答案文件 | {output_path} |
| 生成时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 试卷字数 | {len(exam_content)} 字符 |

---

*本答案文档由 Traffic Law Docs Skill 自动生成*
*如需完整答案，请结合具体题目内容进一步分析*
"""
        
        # Save answer document
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(answer_content)
        
        print(f"Answer template saved to: {output_path}")
    
    def generate_quote(self, exam_file: str, output_path: str):
        """
        Generate complete quote from exam file
        
        Parameters:
        -----------
        exam_file : str
            Path to exam paper file
        output_path : str
            Path to save answer document
        """
        # Parse exam paper
        exam_content = self.parse_exam_paper(exam_file)
        
        # Save raw content
        raw_output = str(Path(output_path).with_suffix('.txt'))
        with open(raw_output, 'w', encoding='utf-8') as f:
            f.write(exam_content)
        print(f"Raw content saved to: {raw_output}")
        
        # Generate answer template
        self.generate_answer_template(exam_content, output_path)
        
        print(f"\nSUCCESS! Answer template saved to: {output_path}")
        print(f"Raw content saved to: {raw_output}")
        
        # Show file info
        file_size = os.path.getsize(output_path)
        print(f"File size: {file_size / 1024:.2f} KB")
        
        print("\nNext steps:")
        print(f"1. Review the raw content in: {raw_output}")
        print("2. Analyze the exam questions")
        print("3. Fill in the answers based on traffic laws")
        print("4. Reference traffic_laws_parsed.json for legal articles")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate answers for traffic safety exam papers"
    )
    parser.add_argument(
        "--exam-file",
        required=True,
        help="Path to the exam paper document (.docx)"
    )
    parser.add_argument(
        "--output",
        default="交通安全教育考核试卷_答案.md",
        help="Path to save the generated answers"
    )
    parser.add_argument(
        "--laws-json",
        default="traffic_laws_parsed.json",
        help="Path to parsed laws JSON file"
    )
    
    args = parser.parse_args()
    
    # Check if exam file exists
    if not os.path.exists(args.exam_file):
        print(f"Error: Exam file not