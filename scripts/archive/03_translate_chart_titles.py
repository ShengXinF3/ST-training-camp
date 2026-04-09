#!/usr/bin/env python3
"""
将文章中的图表中文标题翻译为英文

用法:
    python scripts/translate_chart_titles.py articles/002_主线01_项目开箱.md
"""

import re
import sys
from pathlib import Path
from typing import Dict, List

# 图表标题翻译映射表
TITLE_TRANSLATIONS = {
    # 通用标题
    '所有 spot（红色=组织内）': 'All spots (red=in tissue)',
    '组织内 spot': 'In-tissue spots',
    '空间表达': 'Spatial expression',
    '总 UMI 数（Unique Molecular Identifier，唯一分子标识符）': 'Total UMI count',
    '检测到的基因数（nGene）': 'Number of detected genes (nGene)',
    '线粒体基因比例（%）': 'Mitochondrial gene percentage (%)',
    '真实空间分布': 'Real spatial distribution',
    '随机对照': 'Random control',
    
    # 主线02
    '总 UMI 数空间分布': 'Spatial distribution of total UMI count',
    '检测到的基因数空间分布': 'Spatial distribution of detected genes',
    '线粒体基因比例空间分布': 'Spatial distribution of mitochondrial gene percentage',
    'nUMI 分布': 'nUMI distribution',
    'nGene 分布': 'nGene distribution',
    'pct_mt 分布': 'pct_mt distribution',
    'QC 结果': 'QC results',
    '过滤后': 'After filtering',
    
    # 主线03
    '低 UMI 区域（可能是气泡）': 'Low UMI regions (possible bubbles)',
    '总 UMI 数': 'Total UMI count',
    'nUMI vs nGene (相关性={correlation:.3f})': 'nUMI vs nGene (correlation={correlation:.3f})',
    
    # 主线04
    '组织覆盖（官方标注）': 'Tissue coverage (official annotation)',
    '邻居数量': 'Number of neighbors',
    '孤立 spot（可能是误标注）': 'Isolated spots (possible misannotation)',
    '总 UMI 数（阈值={numi_lower:.0f}）': 'Total UMI count (threshold={numi_lower:.0f})',
    '低质量 spot': 'Low-quality spots',
    '官方标注': 'Official annotation',
    '建议剔除': 'Suggested exclusion',
    'Mask 结果（叠加组织图像）': 'Mask results (overlay on tissue image)',
}

def translate_chart_titles(content: str) -> str:
    """翻译代码中的图表标题"""
    lines = content.split('\n')
    translated_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 查找包含 title= 的行
        if 'title=' in line:
            # 处理单行 title
            for chinese, english in TITLE_TRANSLATIONS.items():
                if chinese in line:
                    line = line.replace(chinese, english)
                    break
            
            # 处理多行 title（如 f-string 中的 title）
            if 'f\'' in line and 'title=' in line:
                # 查找 f-string 中的中文
                for chinese, english in TITLE_TRANSLATIONS.items():
                    if chinese in line:
                        line = line.replace(chinese, english)
        
        translated_lines.append(line)
        i += 1
    
    return '\n'.join(translated_lines)

def process_article(article_path: str) -> None:
    """处理单篇文章"""
    path = Path(article_path)
    if not path.exists():
        print(f"❌ 文件不存在: {article_path}")
        return
    
    # 读取内容
    content = path.read_text(encoding='utf-8')
    
    # 翻译图表标题
    translated_content = translate_chart_titles(content)
    
    # 保存修改
    if content != translated_content:
        path.write_text(translated_content, encoding='utf-8')
        print(f"✅ 已更新: {article_path}")
    else:
        print(f"⚠️  无需修改: {article_path}")

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/translate_chart_titles.py <文章路径>")
        print("或: python scripts/translate_chart_titles.py all")
        sys.exit(1)
    
    article_path = sys.argv[1]
    
    if article_path.lower() == 'all':
        # 处理所有文章
        articles_dir = Path("articles")
        if not articles_dir.exists():
            print(f"❌ articles 目录不存在")
            sys.exit(1)
        
        for article_file in articles_dir.glob("*.md"):
            process_article(str(article_file))
    else:
        # 处理单篇文章
        process_article(article_path)

if __name__ == '__main__':
    main()