#!/usr/bin/env python3
"""
从 Markdown 文章中提取代码块，生成可执行的 Jupyter Notebook

用法:
    python scripts/article_to_notebook.py articles/002_主线01_项目开箱.md
"""

import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple

class ArticleToNotebook:
    def __init__(self, article_path: str):
        self.article_path = Path(article_path)
        self.content = self.article_path.read_text(encoding='utf-8')
        self.cells = []

    def extract_title(self) -> str:
        """提取文章标题"""
        match = re.search(r'^#\s+(.+)$', self.content, re.MULTILINE)
        return match.group(1) if match else "Untitled"

    def parse_content(self) -> List[Tuple[str, str]]:
        """解析文章内容，返回 (type, content) 列表"""
        blocks = []
        lines = self.content.split('\n')

        i = 0
        # 跳过 YAML frontmatter
        if lines[0].strip() == '---':
            i += 1
            while i < len(lines) and lines[i].strip() != '---':
                i += 1
            i += 1

        # 跳过文章标题（第一个 # 标题）
        while i < len(lines):
            if lines[i].strip().startswith('# '):
                i += 1
                break
            i += 1

        # 从这里开始提取所有内容（包括第一部分和第二部分）
        while i < len(lines):
            line = lines[i]

            # 代码块
            if line.strip().startswith('```'):
                lang = line.strip()[3:].strip()
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1

                if lang == 'python':
                    blocks.append(('code', '\n'.join(code_lines)))
                i += 1
                continue

            # Markdown 内容（累积到下一个代码块或结束）
            md_lines = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                md_lines.append(lines[i])
                i += 1

            md_content = '\n'.join(md_lines).strip()
            if md_content:
                blocks.append(('markdown', md_content))

        return blocks

    def create_notebook(self) -> Dict:
        """创建 Notebook 结构"""
        title = self.extract_title()
        blocks = self.parse_content()

        cells = []

        # 添加标题和说明
        header = f"# {title}\n\n"
        header += f"> 本 Notebook 对应文章：`{self.article_path.name}`\n"
        header += ">\n"
        header += "> 目标：逐步执行文章中的所有代码，验证可行性"

        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [header]
        })

        # 添加环境准备
        env_setup = "## 环境准备\n\n首次运行时，请先安装依赖包"
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [env_setup]
        })

        install_code = "# 安装依赖（首次运行时取消注释）\n"
        install_code += "# !pip install scanpy squidpy matplotlib"
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [install_code]
        })

        # 处理文章内容
        current_md = []
        for block_type, content in blocks:
            if block_type == 'markdown':
                # 累积 Markdown 内容
                current_md.append(content)
            elif block_type == 'code':
                # 先输出累积的 Markdown
                if current_md:
                    md_text = '\n\n'.join(current_md)
                    cells.append({
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": [md_text]
                    })
                    current_md = []

                # 输出代码块
                cells.append({
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [content]
                })

        # 输出剩余的 Markdown
        if current_md:
            md_text = '\n\n'.join(current_md)
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [md_text]
            })

        # 创建 Notebook 结构
        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "codemirror_mode": {
                        "name": "ipython",
                        "version": 3
                    },
                    "file_extension": ".py",
                    "mimetype": "text/x-python",
                    "name": "python",
                    "nbconvert_exporter": "python",
                    "pygments_lexer": "ipython3",
                    "version": "3.12.3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }

        return notebook

    def save_notebook(self, output_dir: str = "notebooks"):
        """保存 Notebook"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 生成输出文件名
        stem = self.article_path.stem
        output_file = output_path / f"{stem}_实践.ipynb"

        # 创建并保存 Notebook
        notebook = self.create_notebook()
        output_file.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding='utf-8')

        print(f"✅ Notebook 已生成: {output_file}")
        return output_file

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/article_to_notebook.py <文章路径>")
        sys.exit(1)

    article_path = sys.argv[1]

    if not Path(article_path).exists():
        print(f"❌ 文件不存在: {article_path}")
        sys.exit(1)

    converter = ArticleToNotebook(article_path)
    converter.save_notebook()

if __name__ == '__main__':
    main()
