#!/usr/bin/env python3
"""
导入数据到 Meilisearch
risshun/Chinese_Laws 仓库格式
"""

import argparse
import json
from pathlib import Path
from meilisearch import Client

def main():
    parser = argparse.ArgumentParser(description='Import legal data to Meilisearch')
    parser.add_argument('--data-dir', type=str, required=True, help='Root directory containing categorized legal JSON')
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

    for category_dir in root_dir.iterdir():
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        print(f"Processing category: {category}")
        
        for json_file in category_dir.glob('*.json'):
            with open(json_file, 'r', encoding='utf-8') as f:
                try:
                    law = json.load(f)
                    law_title = law.get('title', json_file.stem)
                    effective_date = law.get('effective_date', '')
                    articles = law.get('articles', [])
                    
                    for article in articles:
                        doc_id += 1
                        documents.append({
                            'id': doc_id,
                            'law_title': law_title,
                            'category': category,
                            'article_no': article.get('article_no', ''),
                            'article_title': article.get('title', ''),
                            'content': article.get('content', ''),
                            'effective_date': effective_date
                        })
                except Exception as e:
                    print(f"Error processing {json_file}: {e}")
                    continue

    print(f"\nTotal documents: {len(documents)}")
    print("Starting import...")

    # Add documents to index
    task = index.add_documents(documents)
    print(f"Task info: {task}")
    print("\nDone! Wait for Meilisearch to finish indexing.")

if __name__ == '__main__':
    main()
