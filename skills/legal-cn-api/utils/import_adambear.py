#!/usr/bin/env python3
"""
导入 AdamBear/laws-markdown 格式数据到 Meilisearch
数据来自 https://github.com/AdamBear/laws-markdown
"""

import argparse
import re
from pathlib import Path
import yaml
from meilisearch import Client

def parse_frontmatter(content: str):
    """Parse YAML frontmatter from markdown"""
    # Frontmatter is between ---
    pattern = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
    match = pattern.match(content)
    if match:
        try:
            data = yaml.safe_load(match.group(1))
            content_no_frontmatter = content[match.end():]
            return data, content_no_frontmatter
        except Exception as e:
            print(f"Error parsing frontmatter: {e}")
    return None, content

def parse_articles(content: str, law_title: str):
    """Parse articles from markdown content"""
    articles = []
    
    # Pattern matching for articles like **第一条** content
    # Supports both **第一条** and **第X条** content
    article_pattern = re.compile(r'\*\*(第[一二三四五六七八九十百千0-9]+条)\*\*[　\s]*(.*?)(?=\n*\*\*第[一二三四五六七八九十百千0-9]+条\*\*|$)', re.DOTALL)
    
    for match in article_pattern.finditer(content):
        article_no = match.group(1)
        article_content = match.group(2).strip()
        article_content = re.sub(r'\n+', ' ', article_content)
        article_content = re.sub(r'[ \t]+', ' ', article_content)
        # Clean up extra markdown
        article_content = article_content.replace('**', '').replace('*', '')
        if article_content:
            articles.append({
                'article_no': article_no,
                'content': article_content
            })
    
    # If no articles found with pattern, try to split by chapters
    if not articles:
        # Try to split by headings ## 第一章...
        chapter_pattern = re.compile(r'##\s+(.+?)\n(.*?)(?=##\s+|$)', re.DOTALL)
        for match in chapter_pattern.finditer(content):
            chapter_title = match.group(1).strip()
            chapter_content = match.group(2).strip()
            # Still look for articles inside chapter
            article_pattern2 = re.compile(r'\*\*(第[一二三四五六七八九十百千0-9]+条)\*\*[　\s]*(.*?)(?=\n*\*\*第[一二三四五六七八九十百千0-9]+条\*\*|$)', re.DOTALL)
            found = False
            for match2 in article_pattern2.finditer(chapter_content):
                found = True
                article_no = match2.group(1)
                article_content = match2.group(2).strip()
                article_content = re.sub(r'\n+', ' ', article_content)
                article_content = re.sub(r'[ \t]+', ' ', article_content)
                article_content = article_content.replace('**', '').replace('*', '')
                if article_content:
                    articles.append({
                        'article_no': article_no,
                        'content': article_content
                    })
            if not found and chapter_content:
                # Whole chapter as one article
                article_content = chapter_title + " " + re.sub(r'\n+', ' ', chapter_content).strip()
                article_content = article_content.replace('**', '').replace('*', '')
                articles.append({
                    'article_no': '',
                'content': article_content
            })
    
    # If still no articles, just add whole content
    if not articles:
        content_clean = re.sub(r'\n+', ' ', content)
        content_clean = content_clean.replace('**', '').replace('*', '')
        articles.append({
            'article_no': '',
            'content': content_clean.strip()
        })
    
    return articles

def main():
    parser = argparse.ArgumentParser(description='Import AdamBear laws-markdown to Meilisearch')
    parser.add_argument('--data-dir', type=str, required=True, help='Root directory (content/)')
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

    # Walk data directory
    root_dir = Path(args.data_dir)
    documents = []
    doc_id = 0
    total_laws = 0
    
    # Iterate categories: 宪法, 法律, 行政法规, 监察法规, 司法解释
    for category_dir in root_dir.iterdir():
        if not category_dir.is_dir() or category_dir.name in ['about', 'search', 'appendix']:
            continue
        category = category_dir.name
        print(f"Processing category: {category}")
        
        for md_file in category_dir.glob('*.md'):
            total_laws += 1
            try:
                content = md_file.read_text(encoding='utf-8')
                frontmatter, content_clean = parse_frontmatter(content)
                if frontmatter and 'title' in frontmatter:
                    law_title = frontmatter['title']
                else:
                    law_title = md_file.stem
                
                effective_date = frontmatter.get('effective_date', '') if frontmatter else ''
                
                articles = parse_articles(content_clean, law_title)
                
                for article in articles:
                    doc_id += 1
                    documents.append({
                        'id': doc_id,
                        'law_title': law_title,
                        'category': category,
                        'article_no': article['article_no'],
                        'article_title': '',
                        'content': article['content'],
                        'effective_date': str(effective_date),
                        'status': frontmatter.get('status', '') if frontmatter else ''
                    })
                
                if total_laws % 100 == 0:
                    print(f"  Processed {total_laws} laws, {doc_id} articles so far...")
                
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
                import traceback
                traceback.print_exc()
                continue

    print(f"\n====== Summary ======")
    print(f"Total laws processed: {total_laws}")
    print(f"Total articles/documents: {doc_id}")
    print(f"Starting import to Meilisearch...")

    # Add documents to index
    task = index.add_documents(documents)
    print(f"Import task enqueued: {task}")
    print("\nDone! Meilisearch is indexing in background. This may take a few minutes...")

if __name__ == '__main__':
    main()
