#!/usr/bin/env python3
"""
曼昆律所网站文章爬取脚本（改进版）
爬取 www.mankunlaw.com 上的全部文章并整理为结构化知识库
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os
import sys
import re

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MankunCrawler:
    """曼昆律所网站爬虫"""

    def __init__(self):
        self.base_url = "https://www.mankunlaw.com"
        self.categories = {
            "activity": "曼昆动态",
            "promulgate": "曼昆普法",
            "case-studies": "曼昆案例"
        }
        self.session = requests.Session()
        self.session.verify = False  # 禁用SSL验证
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.articles = []

    def get_article_list(self, category):
        """获取指定分类的文章列表"""
        url = f"{self.base_url}/index.php/zh/article/{category}"
        print(f"正在爬取分类: {self.categories[category]} ({url})")

        try:
            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找文章链接
            article_links = soup.find_all('a', href=True)

            article_ids = set()
            for link in article_links:
                href = link.get('href', '')
                # 提取文章ID
                if '/article/' in href:
                    parts = href.split('/article/')
                    if len(parts) > 1:
                        article_id = parts[1].split('?')[0].split('/')[0]
                        if article_id.isdigit():
                            article_ids.add(article_id)

            print(f"  找到 {len(article_ids)} 篇文章")
            return list(article_ids)

        except Exception as e:
            print(f"  错误: {e}")
            return []

    def get_article_detail(self, article_id, category):
        """获取文章详情"""
        url = f"{self.base_url}/index.php/zh/article/{article_id}"

        try:
            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题 - 尝试多种方式
            title = ""
            title_tag = soup.find('h1') or soup.find('h2') or soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
                # 清理标题
                title = re.sub(r'\s+', ' ', title)
                title = title.split(' - ')[0]  # 移除网站名称

            # 提取文章内容 - 尝试多种选择器
            content = ""
            content_selectors = [
                ('div', {'class': 'article-body'}),
                ('div', {'class': 'item-page'}),
                ('article', {}),
                ('div', {'id': 'content'}),
                ('div', {'class': 'content'}),
                ('main', {}),
            ]

            for tag, attrs in content_selectors:
                content_div = soup.find(tag, attrs)
                if content_div:
                    # 移除script、style、nav等无关标签
                    for tag_to_remove in content_div.find_all(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                        tag_to_remove.decompose()

                    # 提取文本
                    text = content_div.get_text(separator='\n', strip=True)
                    if len(text) > 100:  # 确保有足够的内容
                        content = text
                        break

            # 如果没找到内容，尝试提取整个body的文本
            if not content or len(content) < 100:
                body = soup.find('body')
                if body:
                    # 移除无关标签
                    for tag_to_remove in body.find_all(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                        tag_to_remove.decompose()
                    content = body.get_text(separator='\n', strip=True)
                    # 移除菜单和导航等无关内容
                    content = re.sub(r'主页|关于曼昆|团队成员|联系我们|法律咨询|招聘职位', '', content)
                    content = re.sub(r'\n\s*\n', '\n\n', content).strip()

            # 提取发布时间
            publish_date = ""
            date_tag = soup.find('time')
            if date_tag:
                publish_date = date_tag.get('datetime', '') or date_tag.get_text().strip()

            article = {
                "id": article_id,
                "title": title,
                "content": content,
                "category": self.categories[category],
                "url": url,
                "publish_date": publish_date,
                "crawled_at": datetime.now().isoformat()
            }

            print(f"    已爬取: {title[:50]}... ({len(content)} 字符)")
            return article

        except Exception as e:
            print(f"    错误 (ID {article_id}): {e}")
            return None

    def crawl_all(self):
        """爬取所有分类的文章"""
        print("开始爬取曼昆律所网站文章...")

        for category, category_name in self.categories.items():
            article_ids = self.get_article_list(category)

            for article_id in article_ids:
                article = self.get_article_detail(article_id, category)
                if article and len(article['content']) > 50:
                    self.articles.append(article)

                # 避免请求过快
                time.sleep(0.3)

        print(f"\n爬取完成! 共获取 {len(self.articles)} 篇文章")
        return self.articles

    def save_to_json(self, output_path):
        """保存到JSON文件"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)

        print(f"已保存到: {output_path}")


def main():
    """主函数"""
    # 确定输出路径（相对于脚本所在位置）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "mankun_articles.json")

    crawler = MankunCrawler()
    articles = crawler.crawl_all()
    crawler.save_to_json(output_path)

    # 输出统计信息
    print("\n统计信息:")
    category_count = {}
    for article in articles:
        cat = article['category']
        category_count[cat] = category_count.get(cat, 0) + 1

    for category, count in category_count.items():
        print(f"  {category}: {count} 篇")

    # 输出第一篇文章的样例
    if articles:
        print("\n样例文章（前3篇）:")
        for i, article in enumerate(articles[:3]):
            print(f"\n{i+1}. {article['title']}")
            print(f"   内容长度: {len(article['content'])} 字符")
            print(f"   内容预览: {article['content'][:200]}...")


if __name__ == "__main__":
    main()
