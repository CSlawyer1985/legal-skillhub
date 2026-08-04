#!/usr/bin/env python3
"""
将爬取的文章转换为Markdown格式
"""

import json
import os
from datetime import datetime


def json_to_markdown(json_path, output_path):
    """将JSON文章转换为Markdown"""

    with open(json_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    # 按分类分组
    categories = {}
    for article in articles:
        cat = article['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)

    # 生成Markdown
    md_content = """# 曼昆律所文章库

## 目录
"""

    # 添加目录
    for i, cat in enumerate(categories.keys(), 1):
        md_content += f"{i}. [{cat}](#{cat.replace(' ', '-')})\n"

    md_content += "\n"

    # 添加文章内容
    for cat, article_list in categories.items():
        md_content += f"## {cat}\n\n"

        for article in article_list:
            # 跳过内容为空的文章
            if not article['content'] or article['content'] == '无法提取内容':
                continue

            md_content += f"### {article['title']}\n\n"
            md_content += f"**文章ID**: {article['id']}\n\n"
            md_content += f"**分类**: {article['category']}\n\n"
            md_content += f"**发布时间**: {article['publish_date']}\n\n"
            md_content += f"**链接**: {article['url']}\n\n"

            # 清理内容
            content = article['content'].strip()
            # 移除过多的空行
            import re
            content = re.sub(r'\n{3,}', '\n\n', content)

            md_content += f"{content}\n\n"
            md_content += "---\n\n"

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"已转换 {len(articles)} 篇文章到 Markdown 格式")
    print(f"输出文件: {output_path}")


def main():
    """主函数"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "mankun_articles.json")
    output_path = os.path.join(script_dir, "mankun_articles.md")

    json_to_markdown(json_path, output_path)


if __name__ == "__main__":
    main()
