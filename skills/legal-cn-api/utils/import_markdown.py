#!/usr/bin/env python3
"""
导入 markdown 格式的法律数据 (risshun/Chinese_Laws) 到 Meilisearch
"""

import argparse
import re
from pathlib import Path
from meilisearch import Client

def parse_markdown_law(md_path: Path):
    """Parse a markdown file containing a law into articles"""
    content = md_path.read_text(encoding='utf-8')
    law_title = md_path.stem
    
    # Try to extract effective date from content or filename
    effective_date = ""
    if "（" in content and "生效" in content:
        # Simple extraction, can be improved
        pass
    
    articles = []
    # Remove the title/header that starts with # but keep content
    content_no_header = re.sub(r'^#.*\n+', '', content)
    
    # Pattern matching for articles in this repo's format:
    # "**第一条** 内容..." or "**第一条**\n内容"
    # Supports both Chinese numbers and Arabic numbers
    article_pattern = re.compile(r'\*\*(第[一二三四五六七八九十百千0-9]+条)\*\*[　\s]*(.*?)(?=\n*\*\*第[一二三四五六七八九十百千0-9]+条\*\*|$)', re.DOTALL)
    
    for match in article_pattern.finditer(content_no_header):
        article_no = match.group(1)
        article_content = match.group(2).strip()
        article_content = re.sub(r'\n+', ' ', article_content)
        article_content = re.sub(r'<br>\s*', '', article_content)
        article_content = re.sub(r'[ \t]+', ' ', article_content)
        if article_content:
            articles.append({
                'article_no': article_no,
                'title': '',
                'content': article_content
            })
    
    # If no articles found with bold pattern, try normal pattern
    if not articles:
        article_pattern2 = re.compile(r'(?:^|\n)(第[一二三四五六七八九十百千0-9]+条)[　\s]+(.*?)(?=\n+(?:第[一二三四五六七八九十百千0-9]+条|$))', re.DOTALL)
        for match in article_pattern2.finditer(content_no_header):
            article_no = match.group(1)
            article_content = match.group(2).strip()
            article_content = re.sub(r'\n+', ' ', article_content)
            article_content = re.sub(r'<br>\s*', '', article_content)
            if article_content:
                articles.append({
                    'article_no': article_no,
                    'title': '',
                    'content': article_content
                })
    
    # If still no articles found with pattern, treat whole content as one article
    if not articles:
        articles.append({
            'article_no': '',
            'title': '',
            'content': re.sub(r'\n+', ' ', content.strip())
        })
    
    return law_title, effective_date, articles

def main():
    parser = argparse.ArgumentParser(description='Import markdown legal data to Meilisearch')
    parser.add_argument('--data-dir', type=str, required=True, help='Root directory containing categorized legal md files')
    parser.add_argument('--host', type=str, default='http://localhost:7700', help='Meilisearch host')
    parser.add_argument('--master-key', type=str, default='masterKey', help='Meilisearch master key')
    parser.add_argument('--index-name', type=str, default='legal_cn', help='Index name')
    args = parser.parse_args()

    # Connect to Meilisearch
    client = Client(args.host, args.master_key)
    
    # Delete index if exists
    try:
        client.delete_index(args.index_name)
        print(f"Deleted existing index {args.index_name}")
    except Exception:
        pass
    
    # Create index
    client.create_index(args.index_name, {'primaryKey': 'id'})
    index = client.index(args.index_name)
    print(f"Created index {args.index_name}")

    # Walk data directory - each subdir is a category
    root_dir = Path(args.data_dir)
    documents = []
    doc_id = 0
    total_laws = 0

    for category_dir in root_dir.iterdir():
        if not category_dir.is_dir() or category_dir.name == '.git':
            continue
        category = category_dir.name
        print(f"Processing category: {category}")
        
        for md_file in category_dir.glob('*.md'):
            total_laws += 1
            try:
                law_title, effective_date, articles = parse_markdown_law(md_file)
                for article in articles:
                    doc_id += 1
                    documents.append({
                        'id': doc_id,
                        'law_title': law_title,
                        'category': category,
                        'article_no': article['article_no'],
                        'article_title': article['title'],
                        'content': article['content'],
                        'effective_date': effective_date
                    })
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
                continue

    print(f"\nTotal laws processed: {total_laws}")
    print(f"Total articles/documents: {len(documents)}")
    print("Starting import...")

    # Add documents to index
    task = index.add_documents(documents)
    print(f"Import task: {task}")
    print("\nDone! Meilisearch is now indexing in background.")

if __name__ == '__main__':
    main()
