#!/usr/bin/env python3
"""
从排期表动态生成文章索引 JSON 文件
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCHEDULE_FILE = PROJECT_ROOT / "docs" / "02_项目管理" / "ST_文章排期表_v2_详细版.md"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "02_项目管理" / "article_index.json"
ARTICLES_DIR = PROJECT_ROOT / "articles"


def parse_schedule_table(content: str) -> dict:
    """解析排期表中的表格，提取文章信息"""
    articles = {}

    # 匹配表格行：| 编号 | 标题 | 标签 | 难度 | 内容要点 |
    # 标签可能是 [通用] 或 [VisiumHD][Cellpose] 这样的多标签
    pattern = r'\|\s*(\d{3})\s*\|\s*([^|]+?)\s*\|\s*(\[[^\|]+?\])\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'

    # 当前系列
    current_series = None

    for line in content.split('\n'):
        # 检测系列标题（支持多种格式）
        series_match = re.search(r'##\s+[📚🧬🔬🛠️🔍🗺️🧩💬🔄🔗⚙️🏥🚀]*\s*(S\d+)\.', line)
        if series_match:
            current_series = series_match.group(1)
            continue

        # 匹配表格行
        match = re.search(pattern, line)
        if match and current_series:
            article_id = match.group(1)
            title = match.group(2).strip()
            tags_str = match.group(3).strip()
            difficulty = match.group(4).strip()
            key_points = match.group(5).strip()

            # 解析标签：提取所有 [xxx] 格式的标签
            tags = re.findall(r'\[([^\]]+)\]', tags_str)

            articles[article_id] = {
                "id": article_id,
                "title": title,
                "series": current_series,
                "tags": tags,
                "difficulty": difficulty,
                "key_points": key_points,
                "status": "pending"
            }

    return articles


def get_completed_articles() -> set:
    """扫描 articles 目录，获取已完成的文章 ID"""
    completed = set()
    if ARTICLES_DIR.exists():
        for article_file in ARTICLES_DIR.glob("*.md"):
            # 提取文章 ID（前三位数字）
            match = re.match(r'(\d{3})_', article_file.name)
            if match:
                completed.add(match.group(1))
    return completed


def main():
    print("📖 读取排期表...")

    if not SCHEDULE_FILE.exists():
        print(f"❌ 排期表不存在: {SCHEDULE_FILE}")
        return

    # 读取排期表
    content = SCHEDULE_FILE.read_text(encoding='utf-8')

    # 解析文章信息
    print("🔍 解析文章信息...")
    articles = parse_schedule_table(content)

    if not articles:
        print("❌ 未能从排期表中提取到文章信息")
        print("   请检查排期表格式是否正确")
        return

    # 获取已完成的文章
    print("📂 扫描已完成文章...")
    completed_ids = get_completed_articles()

    # 更新状态
    for article_id in completed_ids:
        if article_id in articles:
            articles[article_id]['status'] = 'completed'

    # 写入 JSON
    print("💾 生成索引文件...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    # 统计信息
    total = len(articles)
    completed = sum(1 for a in articles.values() if a['status'] == 'completed')
    pending = total - completed

    # 按系列统计
    series_stats = {}
    for article in articles.values():
        series = article['series']
        if series not in series_stats:
            series_stats[series] = {'total': 0, 'completed': 0}
        series_stats[series]['total'] += 1
        if article['status'] == 'completed':
            series_stats[series]['completed'] += 1

    print(f"\n{'='*60}")
    print(f"✅ 文章索引已生成: {OUTPUT_FILE}")
    print(f"{'='*60}")
    print(f"总计: {total} 篇")
    print(f"已完成: {completed} 篇 ({completed/total*100:.1f}%)")
    print(f"待完成: {pending} 篇 ({pending/total*100:.1f}%)")
    print(f"\n按系列统计:")
    for series in sorted(series_stats.keys()):
        stats = series_stats[series]
        print(f"  {series}: {stats['completed']}/{stats['total']} 篇")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
