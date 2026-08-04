#!/usr/bin/env python3
import pdfplumber
import re
import sys

def extract_parties(pdf_path):
    """提取PDF中的当事人信息"""
    parties = {
        '原告': set(),
        '被告': set(),
        '第三人': set()
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 读取前5页（通常起诉状在前几页）
            for i, page in enumerate(pdf.pages[:5]):
                text = page.extract_text()
                if not text:
                    continue
                    
                # 查找原告信息
                plaintiff_patterns = [
                    r'原告[：:]\s*([^\n\r]+)',
                    r'原告人[：:]\s*([^\n\r]+)',
                    r'起诉人[：:]\s*([^\n\r]+)',
                    r'原告\s+([^\n\r]+)'
                ]
                
                # 查找被告信息
                defendant_patterns = [
                    r'被告[：:]\s*([^\n\r]+)',
                    r'被告人[：:]\s*([^\n\r]+)',
                    r'被申请人[：:]\s*([^\n\r]+)',
                    r'被告\s+([^\n\r]+)'
                ]
                
                # 查找第三人信息
                third_party_patterns = [
                    r'第三人[：:]\s*([^\n\r]+)',
                    r'第三[人]?[：:]\s*([^\n\r]+)'
                ]
                
                # 尝试匹配
                for pattern in plaintiff_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        parties['原告'].add(match.strip())
                
                for pattern in defendant_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        parties['被告'].add(match.strip())
                
                for pattern in third_party_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        parties['第三人'].add(match.strip())
                
                # 如果找到当事人，提前结束
                if any(len(v) > 0 for v in parties.values()):
                    break
                    
    except Exception as e:
        return {'error': str(e)}
    
    # 清理空集合
    result = {k: list(v) for k, v in parties.items() if len(v) > 0}
    
    # 如果没找到，尝试更宽松的搜索
    if not result:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ''
            for i, page in enumerate(pdf.pages[:3]):
                text = page.extract_text()
                if text:
                    full_text += text + '\n'
            
            # 查找包含"公司"、"有限"等关键词的行
            lines = full_text.split('\n')
            for line in lines:
                if '公司' in line or '有限' in line or '厂' in line or '店' in line:
                    if '原告' in line:
                        parties['原告'].add(line.strip())
                    elif '被告' in line:
                        parties['被告'].add(line.strip())
                    elif '第三人' in line:
                        parties['第三人'].add(line.strip())
            
            result = {k: list(v) for k, v in parties.items() if len(v) > 0}
    
    return result

if __name__ == "__main__":
    # 示例用法：替换为实际PDF文件路径
    # pdf_path = "/path/to/your/example_pdf_file.pdf"
    # result = extract_parties(pdf_path)
    # print(result)
    print("请提供PDF文件路径以提取当事人信息")