#!/usr/bin/env python3
"""
格式清洗器：将MD内容清洗为纯文本格式

功能：
1. 删除Markdown标记（**, -, #, * 等），但保留条款标题的整体加粗（`**第X条 标题**`和`**第X条**`）
2. 删除多余空格（保留英文单词间空格和"第n条 "后的空格）

注意：不改变原合同的全角半角（方括号、标点等保持原样）
"""

import argparse
import re
import sys
from pathlib import Path


def remove_markdown_symbols(text: str) -> str:
    """删除Markdown标记符号，但保留条款标题的整体加粗格式（`**第X条 标题**`和`**第X条**`）和表格结构"""
    # Step 0: 分离表格行和非表格行，分别处理
    lines = text.split('\n')
    table_line_indices = set()
    
    # 识别表格行
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Grid表格简单分隔行：+---+---+ 或 +===+===+
        if re.match(r'^\+[-=+:]+\+$', stripped):
            table_line_indices.add(i)
        # Grid表格混合分隔行：+---+  |  |（合并单元格边界）
        elif re.match(r'^\+[-=+:\s|]+$', stripped):
            table_line_indices.add(i)
        # Pipe/Grid表格数据行：以|开头
        elif re.match(r'^\|', stripped):
            table_line_indices.add(i)
    
    # Step 1: 保留**第X条 标题**的加粗标记，删除其他位置的**
    placeholder_bold = "\x00BOLD\x00"
    CHINESE_NUM = r'[一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟]+'
    text = re.sub(rf'\*\*(第{CHINESE_NUM}条\s*[^*]*)\*\*', lambda m: f'{placeholder_bold}{m.group(1)}{placeholder_bold}', text)
    text = re.sub(r'\*\*(第\d+条\s*[^*]*)\*\*', lambda m: f'{placeholder_bold}{m.group(1)}{placeholder_bold}', text)
    
    # 删除剩余的加粗标记 **（但不影响表格行）
    # 策略：逐行处理，跳过表格行
    lines = text.split('\n')
    result_lines = []
    for i, line in enumerate(lines):
        if i in table_line_indices:
            result_lines.append(line)
            continue
        
        stripped = line.strip()
        # 检查是否是表格行（因为上面加了placeholder，需要重新判断）
        if re.match(r'^\+[-=+:]+\+$', stripped) or re.match(r'^\+[-=+:\s|]+$', stripped) or re.match(r'^\|', stripped):
            result_lines.append(line)
            continue
        
        # 非表格行：删除加粗标记
        line = re.sub(r'\*\*', '', line)
        
        # 删除斜体标记 *（成对的斜体标记）
        line = re.sub(r'\*([^*]*)\*', r'\1', line)
        
        # 删除标题标记 #（行首）
        line = re.sub(r'^#+\s*', '', line)
        
        # 删除列表标记 - 、 ·（行首）— 但不删除grid表格分隔行
        if not re.match(r'^\+', stripped):
            line = re.sub(r'^[\-\·]\s*', '', line)
        
        result_lines.append(line)
    
    text = '\n'.join(result_lines)
    
    # 恢复第X条的加粗标记
    text = text.replace(placeholder_bold, '**')
    
    return text


def convert_brackets(text: str) -> str:
    """
    方括号转换 — 已禁用
    
    原因：不改变原合同的全角半角，方括号保持原样。
    此函数保留为直通，不执行任何转换。
    """
    return text


def clean_spaces(text: str) -> str:
    """
    删除多余空格
    
    修复BUG-09: 保留英文单词间空格和数字格式
    v2.0: 跳过表格行（grid/pipe表格的对齐空格不能删除）
    
    保留规则：
    1. 保留"第n条 "后面的空格
    2. 保留英文单词间的空格
    3. 保留数字与单位间的空格（如100 元）
    4. 保留表格行中的所有空格（对齐需要）
    """
    # 先保护表格行
    lines = text.split('\n')
    table_line_indices = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^\+[-=+:]+\+$', stripped) or re.match(r'^\+[-=+:\s|]+$', stripped) or re.match(r'^\|', stripped):
            table_line_indices.add(i)
    
    # 逐行处理
    result_lines = []
    for i, line in enumerate(lines):
        if i in table_line_indices:
            # 表格行：不做任何空格处理，保持原样
            result_lines.append(line)
            continue
        
        # 非表格行的空格清理
        # 保护"第n条 "后面的空格
        placeholder_space = "##KEEP_SPACE##"
        chinese_numbers = "一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟"
        pattern = f'([第{chinese_numbers}]+条) '
        
        def replace_space(match):
            return match.group(1) + placeholder_space
        
        line = re.sub(pattern, replace_space, line)
        
        # 保护英文单词间的空格
        placeholder_en_space = "##EN_SPACE##"
        line = re.sub(r'([a-zA-Z]) ([a-zA-Z])', lambda m: f'{m.group(1)}{placeholder_en_space}{m.group(2)}', line)
        
        # 删除连续多个半角空格（保留单个）
        line = re.sub(r' {2,}', ' ', line)
        
        # 删除行首行尾空格
        line = line.strip()
        
        # 删除全角空格
        line = line.replace('\u3000', '')
        
        # 恢复英文单词间的空格
        line = line.replace(placeholder_en_space, ' ')
        
        # 恢复被保护的空格
        line = line.replace(placeholder_space, ' ')
        
        result_lines.append(line)
    
    return '\n'.join(result_lines)


def clean_format(text: str) -> str:
    """
    执行完整的格式清洗
    """
    # 1. 删除Markdown符号（保留条款标题整体加粗）
    text = remove_markdown_symbols(text)
    
    # 2. 转换方括号（排除Markdown链接）
    text = convert_brackets(text)
    
    # 3. 清理空格（保留英文单词间空格）
    text = clean_spaces(text)
    
    # 4. 清理多余空行（连续3个及以上空行压缩为1个）
    text = clean_blank_lines(text)
    
    return text


def clean_blank_lines(text: str) -> str:
    """
    清理多余空行
    
    规则：
    1. 连续3个及以上空行（即2个以上连续空段落）压缩为1个空行
    2. 保留标准段落间距（1个空行）
    """
    # 连续3个以上换行符（2个以上空段落）压缩为2个换行符（1个空段落）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text


def main():
    parser = argparse.ArgumentParser(
        description='格式清洗：删除Markdown标记、转换方括号、清理空格'
    )
    parser.add_argument('--input', '-i', required=True, help='输入MD文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出清洗后的文件路径')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: 输入文件不存在 - {input_path}")
        sys.exit(1)
    
    # 读取文件
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 执行格式清洗
    cleaned_content = clean_format(content)
    
    # 写入输出文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"格式清洗完成: {output_path}")
    
    # 统计信息
    original_lines = content.count('\n') + 1
    cleaned_lines = cleaned_content.count('\n') + 1
    print(f"  原始行数: {original_lines}")
    print(f"  清洗后行数: {cleaned_lines}")


if __name__ == '__main__':
    main()
