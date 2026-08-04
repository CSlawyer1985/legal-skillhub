#!/usr/bin/env python3
"""
Parse traffic accident legal documents from E:\jiaotong directory

This script parses all .doc/.docx files in the legal documents directory
and generates a structured JSON file with the extracted content.

Usage:
    python parse_legal_docs.py --output laws.json
    python parse_legal_docs.py --laws-dir "D:\\custom\\path" --output output.json
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Optional


def parse_docx_file(file_path: str) -> Optional[str]:
    """
    Parse a .docx file and extract text content.
    
    Note: This is a simplified version. For production use,
    consider using python-docx library.
    """
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        
        # docx is a zip file
        with zipfile.ZipFile(file_path, 'r') as z:
            xml_content = z.read('word/document.xml')
        
        # Parse XML
        tree = ET.fromstring(xml_content)
        
        # Extract text
        texts = []
        for elem in tree.iter():
            if elem.tag.endswith('}t'):
                if elem.text:
                    texts.append(elem.text)
        
        return ''.join(texts)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None


def parse_legal_docs(laws_dir: str, output_path: str) -> Dict:
    """
    Parse all legal documents in the specified directory.
    
    Parameters:
    -----------
    laws_dir : str
        Directory containing legal documents
    output_path : str
        Path to save the parsed JSON file
    
    Returns:
    --------
    Dict
        Dictionary containing parsed document data
    """
    print("=== Traffic Law Documents Parser ===")
    print(f"Source: {laws_dir}")
    print(f"Output: {output_path}")
    
    # Check if directory exists
    if not os.path.exists(laws_dir):
        raise FileNotFoundError(f"Directory not found: {laws_dir}")
    
    # Get all document files
    laws_path = Path(laws_dir)
    files = [f for f in laws_path.glob("*.doc*") if not f.name.startswith("~$")]
    
    if not files:
        raise FileNotFoundError(f"No .doc or .docx files found in {laws_dir}")
    
    print(f"Found {len(files)} document(s)")
    
    laws_data = {}
    
    for i, file in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Processing: {file.name}")
        
        law_entry = {
            "filename": file.name,
            "full_path": str(file),
            "file_size": file.stat().st_size,
            "last_modified": file.stat().st_mtime
        }
        
        try:
            if file.suffix == ".docx":
                content = parse_docx_file(str(file))
            else:
                # For .doc files, we'd need additional libraries
                content = f"[Old format .doc file - requires manual parsing: {file.name}]"
            
            if content:
                # Extract articles (simple pattern matching for Chinese articles)
                articles = {}
                pattern = r'第[一二三四五六七八九十百千零]+条|第\d+条'
                matches = list(re.finditer(pattern, content))
                
                print(f"  Found {len(matches)} article references")
                
                # Extract sample articles (first 10)
                for j, match in enumerate(matches[:10]):
                    article_num = match.group()
                    start_pos = match.end()
                    end_pos = min(start_pos + 500, len(content))
                    article_text = content[start_pos:end_pos].strip()
                    article_text = re.sub(r'\s+', ' ', article_text)
                    
                    if article_num not in articles:
                        articles[article_num] = article_text
                
                law_entry["content_preview"] = content[:3000] if len(content) > 3000 else content
                law_entry["articles"] = articles
                law_entry["article_count"] = len(matches)
                law_entry["status"] = "parsed"
                
                print(f"  SUCCESS - Extracted {len(articles)} sample articles")
            else:
                law_entry["status"] = "parse_error"
                
        except Exception as e:
            print(f"  ERROR: {e}")
            law_entry["status"] = "error"
            law_entry["error"] = str(e)
        
        laws_data[file.name] = law_entry
    
    # Save to JSON
    print(f"\nSaving results to JSON...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(laws_data, f, ensure_ascii=False, indent=2)
    
    print(f"SUCCESS! Saved to: {output_path}")
    print(f"Total documents processed: {len(laws_data)}")
    
    # Show file size
    file_size = os.path.getsize(output_path)
    print(f"File size: {file_size / 1024:.2f} KB")
    
    return laws_data


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Parse traffic accident legal documents"
    )
    parser.add_argument(
        "--laws-dir",
        default=r"E:\jiaotong\法律法规\法律法规",
        help="Directory containing legal documents"
    )
    parser.add_argument(
        "--output",
        default="traffic_laws_parsed.json",
        help="Path to save the parsed JSON file"
    )
    
    args = parser.parse_args()
    
    try:
        parse_legal_docs(args.laws_dir, args.output)
        print("\n=== Done ===")
    except Exception as e:
        print(f"\nError: {e}")
        exit(1)


if __name__ == "__main__":
    main()
