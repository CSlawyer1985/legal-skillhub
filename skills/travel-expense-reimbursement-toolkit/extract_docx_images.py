# -*- coding: utf-8 -*-
"""
从 Word 文档（.docx）中提取内嵌图片，并输出图片与文字的对应关系。

用途：
  当用户提供的文件夹内含 Word 文档（如之前整理好的报销单）时，
  用本脚本提取文档内嵌的行程截图，避免遗漏凭证。

用法：
  python extract_docx_images.py "案件文档.docx" --output images/案件简称/docx_extracted/

输出：
  1. 将 word/media/ 下的图片提取到指定目录
  2. 打印每张图片在文档中对应的上下文文字（前后段落），
     帮助 Agent 判断每张图片对应哪条行程
  3. 生成 _image_mapping.json，记录图片与文字的映射关系

依赖：
  仅需 Python 标准库（zipfile, xml.etree.ElementTree, json, os, argparse）
"""
import zipfile
import xml.etree.ElementTree as ET
import json
import os
import argparse

# XML 命名空间
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'


def extract_images(docx_path, output_dir):
    """提取 docx 内嵌图片并生成映射关系"""
    if not os.path.exists(docx_path):
        print(f"错误：文件不存在 - {docx_path}")
        return None

    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(docx_path) as z:
        # 1. 提取所有内嵌图片
        media_files = [
            n for n in z.namelist()
            if n.startswith('word/media/') and not n.endswith('/')
        ]
        extracted = {}
        for name in sorted(media_files):
            basename = os.path.basename(name)
            data = z.read(name)
            out_path = os.path.join(output_dir, basename)
            with open(out_path, 'wb') as f:
                f.write(data)
            extracted[basename] = out_path
            print(f"  提取 {basename} ({len(data)} bytes)")

        # 2. 解析 document.xml.rels，建立 rId -> 图片文件名 映射
        rels_xml = z.read('word/_rels/document.xml.rels')
        rels_root = ET.fromstring(rels_xml)
        rid_to_media = {}
        for rel in rels_root:
            rid = rel.get('Id')
            target = rel.get('Target', '')
            if 'media/' in target:
                rid_to_media[rid] = os.path.basename(target)

        # 3. 解析 document.xml，建立段落-图片映射
        doc_xml = z.read('word/document.xml')
        doc_root = ET.fromstring(doc_xml)
        body = doc_root.find(f'{{{W}}}body')

        # 遍历所有段落，记录文字和图片位置
        paragraphs = []
        if body is not None:
            for p in body.iter(f'{{{W}}}p'):
                # 提取段落文字
                texts = []
                for t in p.iter(f'{{{W}}}t'):
                    if t.text:
                        texts.append(t.text)
                text = ''.join(texts).strip()

                # 提取段落中的图片引用
                image_rids = []
                for blip in p.iter(f'{{{A}}}blip'):
                    rid = blip.get(f'{{{R}}}embed')
                    if rid:
                        image_rids.append(rid)

                if text or image_rids:
                    paragraphs.append({
                        'text': text,
                        'image_rids': image_rids
                    })

        # 4. 为每张图片找到上下文文字（前后最近的非空文字段落）
        mapping = []
        for i, para in enumerate(paragraphs):
            for rid in para['image_rids']:
                media_name = rid_to_media.get(rid, '?')
                if media_name == '?':
                    continue

                # 向上找最近的文字
                context_before = ''
                for j in range(i - 1, -1, -1):
                    if paragraphs[j]['text']:
                        context_before = paragraphs[j]['text']
                        break

                # 向下找最近的文字
                context_after = ''
                for j in range(i + 1, len(paragraphs)):
                    if paragraphs[j]['text']:
                        context_after = paragraphs[j]['text']
                        break

                mapping.append({
                    'image': media_name,
                    'extracted_path': extracted.get(media_name, ''),
                    'context_before': context_before,
                    'context_after': context_after,
                    'paragraph_index': i
                })

        # 5. 打印映射关系
        print(f"\n{'='*60}")
        print("图片与文字对应关系（用于判断每张图对应哪条行程）")
        print(f"{'='*60}")
        for item in mapping:
            print(f"\n  图片: {item['image']}")
            if item['context_before']:
                print(f"  上文: {item['context_before'][:80]}")
            if item['context_after']:
                print(f"  下文: {item['context_after'][:80]}")

        # 6. 保存映射 JSON
        mapping_path = os.path.join(output_dir, '_image_mapping.json')
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        print(f"\n映射关系已保存: {mapping_path}")
        print(f"共提取 {len(extracted)} 张图片")

        return {
            'extracted': extracted,
            'mapping': mapping
        }


def main():
    parser = argparse.ArgumentParser(
        description='从 Word 文档提取内嵌图片并输出与文字的对应关系'
    )
    parser.add_argument('docx', help='Word 文档路径（.docx）')
    parser.add_argument(
        '--output', '-o',
        default='./docx_extracted',
        help='图片输出目录（默认 ./docx_extracted）'
    )
    args = parser.parse_args()

    print(f"正在提取: {args.docx}")
    print(f"输出目录: {args.output}\n")

    result = extract_images(args.docx, args.output)

    if result:
        print(f"\n完成！共提取 {len(result['extracted'])} 张图片。")
        print("请查看 _image_mapping.json 了解每张图片对应的行程文字。")
    else:
        print("\n提取失败，请检查文件路径。")


if __name__ == '__main__':
    main()
