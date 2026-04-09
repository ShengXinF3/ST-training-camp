#!/usr/bin/env python3
from pathlib import Path
import json
import re

def scan_articles():
    """扫描 articles 目录，提取文章 ID"""
    articles = []
    for f in sorted(Path('articles').glob('*.md')):
        # 从文件名提取 ID（前三位数字）
        match = re.match(r'(\d{3})_', f.name)
        if match:
            articles.append({
                'id': match.group(1),
                'filename': f.name
            })
    return articles

def update_index(articles):
    """更新 article_index.json 中的 status"""
    index_file = Path('docs/02_项目管理/article_index.json')

    with open(index_file, 'r', encoding='utf-8') as f:
        index = json.load(f)

    # 获取已发布文章的 ID 集合
    published_ids = {a['id'] for a in articles}

    # 更新状态
    updated_count = 0
    for article_id in index:
        if article_id in published_ids and index[article_id]['status'] != 'completed':
            index[article_id]['status'] = 'completed'
            updated_count += 1

    # 写回文件
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return updated_count

def update_agents_md(articles):
    """更新 AGENTS.md 中的已发布文章列表"""
    agents_file = Path('AGENTS.md')
    content = agents_file.read_text(encoding='utf-8')
    article_list = f"### 已发布文章（{len(articles)} 篇，按新命名规范）\n"
    for a in articles:
        article_list += f"- `articles/{a['filename']}`\n"
    pattern = r'### 已发布文章.*?\n(?:- `articles/.*?\n)+'
    content = re.sub(pattern, article_list, content, flags=re.DOTALL)
    agents_file.write_text(content, encoding='utf-8')

if __name__ == '__main__':
    articles = scan_articles()
    updated = update_index(articles)
    update_agents_md(articles)
    print(f"✅ 更新完成（{len(articles)} 篇文章，{updated} 篇状态更新为 completed）")
