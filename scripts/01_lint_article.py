#!/usr/bin/env python3
"""
文章质检 Linter - 自动化检查文章是否符合 BioF3 规范

用法:
    python scripts/lint_article.py articles/xxx.md
    python scripts/lint_article.py articles/xxx.md --fix  # 自动修复部分问题
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

class ArticleLinter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = self.file_path.read_text(encoding='utf-8')
        self.errors = []
        self.warnings = []
        self.score = 100  # 初始评分 100 分
        self.word_count = len(self.content)

        # 加载术语表
        self.terminology = self._load_terminology()

    def _load_terminology(self) -> Dict[str, str]:
        """加载术语表"""
        term_file = Path(__file__).parent.parent / 'docs' / '03_规范' / '术语表.md'
        if not term_file.exists():
            return {}

        terminology = {}
        content = term_file.read_text(encoding='utf-8')

        # 解析术语表（简单版：提取禁止混用列）
        lines = content.split('\n')
        for line in lines:
            if '❌' in line and '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5:
                    term1 = parts[1]  # 中文术语
                    forbidden = parts[4].replace('❌', '').strip()  # 禁止混用
                    if term1 and forbidden:
                        terminology[term1] = forbidden

        return terminology

    def check_all(self) -> Tuple[List[str], List[str]]:
        """运行所有检查"""
        self.check_forbidden_items()
        self.check_term_consistency()
        self.check_evidence_chain()
        self.check_structure()
        self.check_import_order()
        self.check_article_length()
        return self.errors, self.warnings

    def check_forbidden_items(self):
        """检查硬性禁止项"""
        # 检查外链
        urls = re.findall(r'https?://[^\s\)]+', self.content)
        if urls:
            self.errors.append(f"❌ 禁止外链: 发现 {len(urls)} 个链接")
            self.score -= 20
            for url in urls[:3]:  # 只显示前3个
                self.errors.append(f"   - {url}")

        # 检查对文献的主观评价
        subjective_patterns = [
            r'写得踏实', r'组织得好', r'很全面', r'很权威',
            r'非常详细', r'十分完整', r'相当不错'
        ]
        for pattern in subjective_patterns:
            if re.search(pattern, self.content):
                self.errors.append(f"❌ 禁止对文献主观评价: 发现 '{pattern}'")
                self.score -= 10

        # 检查教育口吻高密度
        education_words = ['你必须', '你应该', '你别', '记住', '一定要', '千万别']
        education_count = sum(self.content.count(word) for word in education_words)
        if education_count > 5:
            self.warnings.append(f"⚠️  教育口吻过多: 发现 {education_count} 处（建议 ≤5）")
            self.score -= 5

        # 检查 emoji 图标（AI 风格）
        emoji_patterns = ['✅', '❌', '⚠️', '📊', '📝', '🔍', '💡', '⭐', '🚀', '📋', '🎯']
        emoji_count = sum(self.content.count(emoji) for emoji in emoji_patterns)
        if emoji_count > 0:
            self.errors.append(f"❌ 禁止使用 emoji 图标: 发现 {emoji_count} 处（AI 风格过重）")
            self.score -= 15

    def check_term_consistency(self):
        """检查术语一致性"""
        # 从术语表检查混用
        for term1, forbidden in self.terminology.items():
            if term1 in self.content and forbidden in self.content:
                self.errors.append(f"❌ 术语不一致: '{term1}' 和 '{forbidden}' 混用")
                self.score -= 15

        # 额外的常见混用术语对（兜底）
        term_pairs = [
            ('空间域', '空间分区'),
            ('反卷积', '解卷积'),
            ('空间位点', 'spot'),
        ]

        for term1, term2 in term_pairs:
            if term1 in self.content and term2 in self.content:
                # 避免重复报错
                error_msg = f"❌ 术语不一致: '{term1}' 和 '{term2}' 混用"
                if error_msg not in self.errors:
                    self.errors.append(error_msg)
                    self.score -= 15

        # 检查未定义的缩写（改进版：检查是否有定义）
        # 排除常见的如 RNA, DNA, QC 等
        common_abbr = {'RNA', 'DNA', 'QC', 'PCA', 'UMAP', 'TME', 'CCC', 'SVG', 'DEG'}
        abbr_pattern = r'\b[A-Z]{2,}\b'
        abbrs = set(re.findall(abbr_pattern, self.content))

        # 检查每个缩写是否在文中有定义（括号形式）
        undefined = []
        for abbr in abbrs - common_abbr:
            # 检查是否有 "xxx (Abbr)" 或 "xxx（Abbr）" 形式的定义
            definition_patterns = [
                rf'[（(]{abbr}[)）]',  # 括号内的缩写
                rf'{abbr}[，,][^）)]+[）)]',  # 缩写在前
                rf'[（(][^)）]*{abbr}[^)）]*[)）]',  # 括号内包含缩写
            ]
            has_definition = any(re.search(pattern, self.content) for pattern in definition_patterns)
            if not has_definition:
                undefined.append(abbr)

        if undefined:
            self.warnings.append(f"⚠️  可能未定义的缩写: {', '.join(list(undefined)[:5])}")
            self.score -= 3

    def check_evidence_chain(self):
        """检查证据链四件套"""
        # 检查是否有诊断图相关描述
        diagnostic_keywords = ['诊断图', 'QC', '质量控制', '分布图', '批次效应']
        has_diagnostic = any(kw in self.content for kw in diagnostic_keywords)

        # 检查是否有对照
        control_keywords = ['负对照', '阴性对照', '随机化', '对照组', '替代解释']
        has_control = any(kw in self.content for kw in control_keywords)

        # 检查是否有敏感性分析
        sensitivity_keywords = ['敏感性', '参数', '稳健性', '鲁棒']
        has_sensitivity = any(kw in self.content for kw in sensitivity_keywords)

        # 检查是否有边界声明
        boundary_keywords = ['边界', '局限', '不能说明', '无法推断', '仅能']
        has_boundary = any(kw in self.content for kw in boundary_keywords)

        missing = []
        if not has_diagnostic:
            missing.append('诊断图')
            self.score -= 5
        if not has_control:
            missing.append('对照')
            self.score -= 5
        if not has_sensitivity:
            missing.append('敏感性')
            self.score -= 3
        if not has_boundary:
            missing.append('边界声明')
            self.score -= 3

        if missing:
            self.warnings.append(f"⚠️  证据链可能不完整: 缺少 {', '.join(missing)}")

    def check_structure(self):
        """检查文章结构"""
        # 检查是否有标题
        if not re.search(r'^#\s+.+', self.content, re.MULTILINE):
            self.errors.append("❌ 缺少文章标题")
            self.score -= 10

        # 检查是否有二级标题（章节）
        h2_count = len(re.findall(r'^##\s+.+', self.content, re.MULTILINE))
        if h2_count < 3:
            self.warnings.append(f"⚠️  章节较少: 只有 {h2_count} 个二级标题（建议 ≥3）")
            self.score -= 3

        # 检查是否有代码块（实践文章应该有）
        code_blocks = re.findall(r'```[\s\S]*?```', self.content)
        if not code_blocks and '实践' in self.file_path.name:
            self.warnings.append("⚠️  实践文章缺少代码块")
            self.score -= 5

    def check_import_order(self):
        """检查 Python 包导入顺序"""
        # 提取所有代码块
        code_blocks = re.findall(r'```python\n([\s\S]*?)```', self.content)
        if not code_blocks:
            return

        # 检查是否使用了 plt., np., pd. 等
        usage_patterns = {
            'plt.': 'matplotlib.pyplot',
            'np.': 'numpy',
            'pd.': 'pandas',
            'sc.': 'scanpy',
            'sq.': 'squidpy'
        }

        # 找到第一个代码块
        first_block = code_blocks[0]

        # 检查每个使用模式
        for pattern, module_name in usage_patterns.items():
            # 在所有代码块中查找使用
            used_in_blocks = []
            for i, block in enumerate(code_blocks):
                if pattern in block:
                    used_in_blocks.append(i)

            if not used_in_blocks:
                continue

            # 检查第一个代码块是否导入了该模块
            import_patterns = [
                f'import {module_name}',
                f'from {module_name}',
            ]

            has_import_in_first = any(imp in first_block for imp in import_patterns)

            if not has_import_in_first and used_in_blocks:
                first_usage_block = used_in_blocks[0]
                if first_usage_block > 0:
                    self.errors.append(
                        f"❌ 导入顺序错误: 代码块 #{first_usage_block + 1} 使用了 '{pattern}' "
                        f"但 {module_name} 未在第一个代码块导入"
                    )
                    self.score -= 10

    def check_article_length(self):
        """检查文章长度"""
        # 去除代码块和空行后的字数
        content_no_code = re.sub(r'```[\s\S]*?```', '', self.content)
        content_no_empty = re.sub(r'\n\s*\n', '\n', content_no_code)
        char_count = len(content_no_empty)

        if char_count < 2000:
            self.warnings.append(f"⚠️  文章较短: {char_count} 字（建议 2000-5000 字）")
            self.score -= 5
        elif char_count > 8000:
            self.warnings.append(f"⚠️  文章较长: {char_count} 字（建议 2000-5000 字）")
            self.score -= 3

    def calculate_final_score(self) -> int:
        """计算最终评分"""
        # 确保评分在 0-100 之间
        return max(0, min(100, self.score))

    def print_report(self):
        """打印检查报告"""
        print(f"\n{'='*60}")
        print(f"文章质检报告: {self.file_path.name}")
        print(f"{'='*60}\n")

        # 计算最终评分
        final_score = self.calculate_final_score()

        # 评分等级
        if final_score >= 90:
            grade = "优秀 ⭐⭐⭐"
        elif final_score >= 80:
            grade = "良好 ⭐⭐"
        elif final_score >= 70:
            grade = "及格 ⭐"
        else:
            grade = "不及格 ❌"

        print(f"📊 质量评分: {final_score}/100 ({grade})")
        print(f"📝 文章字数: {self.word_count} 字\n")

        if not self.errors and not self.warnings:
            print("✅ 所有检查通过！")
            return True

        if self.errors:
            print(f"🚫 发现 {len(self.errors)} 个错误（必须修复）:\n")
            for error in self.errors:
                print(f"  {error}")
            print()

        if self.warnings:
            print(f"⚠️  发现 {len(self.warnings)} 个警告（建议修复）:\n")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        return len(self.errors) == 0

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/lint_article.py <文章路径>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    linter = ArticleLinter(file_path)
    errors, warnings = linter.check_all()
    success = linter.print_report()

    # 返回状态码
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
