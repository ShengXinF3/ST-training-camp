#!/usr/bin/env python3
"""
BioF3 ST 文章生成主控脚本 (Harness)

功能：
- 从索引获取文章信息
- 完整发布流程（生成 + lint + notebook + sync）
- 质检单篇/全部
- 生成 notebook
- 同步进度
- 查看状态

用法：
    python scripts/harness.py publish 007
    python scripts/harness.py lint articles/002_*.md
    python scripts/harness.py lint-all
    python scripts/harness.py notebook articles/002_*.md
    python scripts/harness.py sync
    python scripts/harness.py status
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
ARTICLE_INDEX = PROJECT_ROOT / "docs" / "02_项目管理" / "article_index.json"
ARTICLES_DIR = PROJECT_ROOT / "articles"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


class ArticleHarness:
    """文章生成主控类"""

    def __init__(self):
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """加载文章索引"""
        if not ARTICLE_INDEX.exists():
            print(f"❌ 文章索引不存在: {ARTICLE_INDEX}")
            print("   请先运行: python scripts/generate_article_index.py")
            sys.exit(1)

        with open(ARTICLE_INDEX, "r", encoding="utf-8") as f:
            return json.load(f)

    def _generate_article_prompt(self, info: Dict) -> str:
        """生成文章生成 prompt（优化 token 使用）"""
        tags_str = ', '.join(info['tags'])

        # 获取已发布文章上下文（同系列）
        published_context = self._get_published_context(info['id'])

        # 提取核心术语（避免 Agent 读取术语表全文）
        core_terms = self._extract_core_terms()

        prompt = f'''你需要生成空间转录组训练营的第 {info['id']} 号文章。

## 文章信息
- ID: {info['id']}
- 标题: {info['title']}
- 系列: {info['series']}
- 标签: {tags_str}
- 难度: {info['difficulty']}
- 内容要点: {info['key_points']}

{published_context}

## 写作规范

**重要提示**：
- ✅ 必须读取：skills/st-article-writer/SKILL.md（完整规范）
- ✅ 必须读取：docs/03_规范/术语表.md（完整术语表）
- ✅ 不要读取：docs/02_项目管理/article_index.json（太大，201篇）
- ❌ 不要读取：docs/02_项目管理/ST_文章排期表_v2_详细版.md（太大，516行）
- ❌ 不要读取：已发布文章的全文（使用上面提供的系列上下文即可）

核心要点（已提取，供快速参考）：

### 1. 文章结构（三段式）
- **第一部分**: Why & What（为什么需要？是什么？）
- **第二部分**: How（怎么做？代码示例）
- **第三部分**: What's Next（验收清单、常见坑、下一篇预告）

### 2. 证据链四件套（必须包含）
- ✅ 诊断图：QC 指标、分布图
- ✅ 对照：负对照、随机化
- ✅ 敏感性：参数变化、稳健性
- ✅ 边界声明：能说明什么、不能说明什么

### 3. 术语规范（核心术语快速参考）
**首次出现**：中文 + 英文/缩写 + 一句解释
**后续使用**：优先用中文
**禁止混用**：同一概念只用一个术语

{core_terms}

### 4. 图表规范（重要）
- **所有图表标题、轴标签、图例必须使用英文**
- 示例：
  - ✅ 正确：`title='Total UMI Counts'`
  - ❌ 错误：`title='总 UMI 数'`

### 5. 禁止项
❌ **绝对禁止**：
- 随意拼凑的外链（如果需要引用，必须使用真实存在的 URL）
- 对文献的主观评价
- 教育口吻高密度
- 术语混用
- **图表中使用中文标题、标签或图例**（必须使用英文）

### 6. 输出要求
- 文件名格式：`{info['id']}_{info['series']}_{info['title']}[{tags_str}][{info['difficulty']}].md`
- 保存路径：`articles/` 目录下
- 质量标准：Linter 评分 ≥ 80 分

请直接生成完整文章，确保内容准确、结构清晰、可读性强。'''

        return prompt

    def _extract_core_terms(self) -> str:
        """提取核心术语（避免 Agent 读取术语表全文）"""
        terms_file = PROJECT_ROOT / "docs" / "03_规范" / "术语表.md"

        if not terms_file.exists():
            return ""

        # 读取术语表，提取核心术语
        content = terms_file.read_text(encoding='utf-8')

        # 提取表格中的术语（简化版，只取前20个核心术语）
        core_terms = """
**核心术语（必须遵守）**：
- 空间转录组 (Spatial Transcriptomics, ST) - 保留空间位置信息的基因表达测量
- 空间域 (Spatial Domain) - 基因表达模式相似且空间连续的区域
- 空间可变基因 (Spatially Variable Genes, SVG) - 表达量在空间上呈现非随机分布的基因
- 反卷积 (Deconvolution) - 从混合信号中推断各组分比例（❌ 不要用"解卷积"）
- 细胞通讯 (Cell-Cell Communication, CCC) - 细胞间通过配体-受体相互作用传递信号
- spot - Visium 平台的空间单元（直径 55 µm）（❌ 不要用"空间位点"）
- 成像型 (Imaging-based) - 通过原位杂交或测序直接在组织上成像的技术
- 测序型 (Sequencing-based) - 通过空间条码捕获 RNA 后测序的技术
- 归一化 (Normalization) - 消除技术变异（❌ 不要与"标准化"混用）
- 批次效应 (Batch Effect) - 非生物因素导致的系统性差异
- 空间自相关 (Spatial Autocorrelation) - 空间邻近位置的表达值相似程度
- 邻域 (Neighborhood) - 以某个 spot/细胞为中心的周围区域
- 肿瘤微环境 (Tumor Microenvironment, TME) - 肿瘤细胞及周围基质、免疫、血管等生态系统
- 生态位 (Niche) - 细胞所处的特定微环境及其功能状态
- 梯度 (Gradient) - 基因表达或细胞状态在空间上的连续变化
- 边界 (Boundary) - 不同空间域或组织结构之间的分界线
- 负对照 (Negative Control) - 预期无信号的对照条件，用于评估假阳性
- 证据链 (Evidence Chain) - 支撑结论的完整证据序列
"""
        return core_terms

    def _get_published_context(self, current_id: str) -> str:
        """获取已发布文章上下文（同系列既往文章摘要）"""
        current_num = int(current_id)
        current_article = self.index.get(current_id.zfill(3))

        if not current_article:
            return ""

        current_series = current_article['series']

        # 收集同系列且已发布的文章
        same_series_published = []
        for article_id in sorted(self.index.keys()):
            num = int(article_id)
            article = self.index[article_id]
            if (num < current_num and
                article['series'] == current_series and
                article['status'] == 'completed'):
                same_series_published.append(article)

        if not same_series_published:
            return f"\n## 系列上下文\n本文是 {current_series} 系列的第一篇已发布文章。"

        # 列出同系列所有已发布文章（只显示基本信息，不读取全文）
        context_lines = [f"\n## 系列上下文（{current_series} 系列既往文章）"]
        for article in same_series_published:
            # 尝试读取摘要文件（如果存在）
            summary = self._load_article_summary(article['id'])
            if summary:
                context_lines.append(f"- {article['id']}: {article['title']}")
                context_lines.append(f"  核心观点: {', '.join(summary.get('core_arguments', [])[:2])}")
            else:
                # 如果没有摘要，只显示基本信息
                context_lines.append(f"- {article['id']}: {article['title']} - {article['key_points']}")

        return "\n".join(context_lines)

    def _load_article_summary(self, article_id: str) -> dict:
        """加载文章摘要（如果存在）"""
        summary_file = PROJECT_ROOT / "articles" / "summaries" / f"{article_id}_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _generate_article_summary(self, article_id: str, article_file: Path):
        """生成文章摘要（供后续文章参考，避免读取全文）"""
        summary_dir = PROJECT_ROOT / "articles" / "summaries"
        summary_dir.mkdir(exist_ok=True)

        summary_file = summary_dir / f"{article_id}_summary.json"

        # 读取文章内容，提取关键信息
        content = article_file.read_text(encoding='utf-8')

        # 简单提取：标题、前500字作为摘要
        lines = content.split('\n')
        title = ""
        for line in lines[:10]:
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                break

        # 提取前500字作为核心内容
        text_content = '\n'.join(lines[:50])

        info = self.get_article_info(article_id)

        summary = {
            "id": article_id,
            "title": info['title'] if info else title,
            "series": info['series'] if info else "",
            "key_points": info['key_points'] if info else "",
            "preview": text_content[:500] + "...",
            "generated_at": "2026-04-08"
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 摘要已生成: {summary_file.name}")

    def _call_agent(self, prompt: str) -> str:
        """返回 Agent prompt 供外部调用"""
        return prompt

    def get_article_info(self, article_id: str) -> Optional[Dict]:
        """获取文章信息"""
        article_id = article_id.zfill(3)  # 补齐为 3 位
        return self.index.get(article_id)

    def publish(self, article_id: str, auto_mode: bool = False):
        """完整发布流程

        Args:
            article_id: 文章编号
            auto_mode: 自动模式（返回 prompt 供 Claude Agent 使用）
        """
        print(f"\n{'='*60}")
        print(f"📝 开始发布文章: {article_id}")
        print(f"{'='*60}\n")

        # 1. 获取文章信息
        info = self.get_article_info(article_id)
        if not info:
            print(f"❌ 文章 {article_id} 不存在于索引中")
            return False

        print(f"📋 文章信息:")
        print(f"   ID: {info['id']}")
        print(f"   标题: {info['title']}")
        print(f"   系列: {info['series']}")
        print(f"   标签: {', '.join(info['tags'])}")
        print(f"   难度: {info['difficulty']}")
        print(f"   要点: {info['key_points']}")
        print(f"   状态: {info['status']}\n")

        # 2. 生成文章 prompt
        print("🚀 步骤 1/4: 准备生成文章...")
        agent_prompt = self._generate_article_prompt(info)
        prompt_file = PROJECT_ROOT / "tmp" / f"article_{article_id}_prompt.txt"
        prompt_file.parent.mkdir(exist_ok=True)
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(agent_prompt)
        print(f"   ✓ Agent prompt 已保存到: {prompt_file}")

        if auto_mode:
            # 自动模式：返回 prompt 供 Claude Agent 使用
            print(f"   🤖 自动模式：返回 prompt 供 Agent 执行")
            return agent_prompt
        else:
            # 手动模式：等待用户确认
            print(f"   📋 请在 Claude 中使用 Agent 工具执行此 prompt")
            print(f"   等待文章生成完成后，按 Enter 继续...")
            input()

        # 3. 后续处理
        return self.post_process(article_id)

    def post_process(self, article_id: str, skip_test: bool = False, auto_continue: bool = False):
        """文章生成后的后续处理（lint、notebook、test、summary、sync）

        Args:
            article_id: 文章编号
            skip_test: 是否跳过 notebook 测试
            auto_continue: 自动模式，遇到问题自动继续（不等待用户输入）
        """
        print(f"\n{'='*60}")
        print(f"📝 后续处理文章: {article_id}")
        print(f"{'='*60}\n")

        # 1. 查找生成的文章文件
        article_files = list(ARTICLES_DIR.glob(f"{article_id}_*.md"))
        if not article_files:
            print(f"❌ 未找到文章文件: {ARTICLES_DIR}/{article_id}_*.md")
            return False

        article_file = article_files[0]
        print(f"✓ 找到文章: {article_file.name}\n")

        # 2. 生成文章摘要（供后续文章参考）
        print("📝 生成文章摘要...")
        self._generate_article_summary(article_id, article_file)

        # 3. 运行 lint
        print("\n🔍 步骤 2/5: 质量检查...")
        if not self.lint(str(article_file)):
            if not auto_continue:
                print("⚠️  质检发现问题，是否继续？(y/n)")
                if input().lower() != 'y':
                    return False
            else:
                print("⚠️  质检发现问题，但自动模式继续执行...")

        # 4. 生成 notebook
        print("\n📓 步骤 3/5: 生成 Jupyter Notebook...")
        self.notebook(str(article_file))

        # 5. 测试 notebook（可选）
        if not skip_test:
            print("\n🧪 步骤 4/5: 测试 Notebook...")
            notebook_file = self._find_notebook(article_id)
            if notebook_file:
                test_passed = self.test_notebook(str(notebook_file))
                if not test_passed:
                    print("\n⚠️  Notebook 测试失败！")
                    if not auto_continue:
                        print("   选项:")
                        print("   1. 继续发布 (c)")
                        print("   2. 跳过并手动修复 (s)")
                        print("   3. 调用 Agent 修复 (a) [暂未实现]")
                        choice = input("   请选择 (c/s/a): ").lower()
                        if choice == 's':
                            print("\n⏸️  已暂停发布流程，请手动修复后重新运行 post-process")
                            return False
                        elif choice == 'a':
                            print("\n⚠️  Agent 自动修复功能暂未实现，请手动修复")
                            return False
                        # choice == 'c' 继续
                    else:
                        print("   自动模式：继续发布...")
        else:
            print("\n⏭️  步骤 4/5: 跳过 Notebook 测试（--skip-test）")

        # 6. 同步进度
        print("\n📊 步骤 5/5: 同步进度...")
        self.sync()

        info = self.get_article_info(article_id)
        print(f"\n{'='*60}")
        print(f"✅ 文章发布完成: {info['title'] if info else article_id}")
        print(f"{'='*60}\n")
        return True

    def lint(self, file_path: str) -> bool:
        """质检单篇文章"""
        lint_script = SCRIPTS_DIR / "01_lint_article.py"
        if not lint_script.exists():
            print(f"❌ lint 脚本不存在: {lint_script}")
            return False

        try:
            result = subprocess.run(
                ["python", str(lint_script), file_path],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ 运行 lint 失败: {e}")
            return False

    def lint_all(self):
        """质检所有文章"""
        print("\n🔍 质检所有文章...\n")
        article_files = sorted(ARTICLES_DIR.glob("*.md"))

        if not article_files:
            print("❌ 未找到任何文章文件")
            return

        passed = 0
        failed = 0

        for article_file in article_files:
            print(f"检查: {article_file.name}")
            if self.lint(str(article_file)):
                passed += 1
            else:
                failed += 1
            print()

        print(f"\n{'='*60}")
        print(f"质检完成: 通过 {passed} 篇，失败 {failed} 篇")
        print(f"{'='*60}\n")

    def notebook(self, file_path: str):
        """生成 Jupyter Notebook"""
        notebook_script = SCRIPTS_DIR / "02_article_to_notebook.py"
        if not notebook_script.exists():
            print(f"❌ notebook 脚本不存在: {notebook_script}")
            return

        try:
            result = subprocess.run(
                ["python", str(notebook_script), file_path],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        except Exception as e:
            print(f"❌ 生成 notebook 失败: {e}")

    def _find_notebook(self, article_id: str) -> Optional[Path]:
        """查找生成的 notebook 文件"""
        notebooks_dir = PROJECT_ROOT / "notebooks"
        notebook_files = list(notebooks_dir.glob(f"{article_id}_*_实践.ipynb"))
        if notebook_files:
            return notebook_files[0]
        return None

    def test_notebook(self, notebook_path: str, mode: str = 'quick') -> bool:
        """测试 Jupyter Notebook"""
        test_script = SCRIPTS_DIR / "04_test_notebook.py"
        if not test_script.exists():
            print(f"❌ test 脚本不存在: {test_script}")
            return True  # 脚本不存在时跳过测试

        try:
            result = subprocess.run(
                ["python", str(test_script), notebook_path, "--mode", mode],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ 测试 notebook 失败: {e}")
            return False

    def sync(self):
        """同步进度"""
        sync_script = SCRIPTS_DIR / "03_sync_progress.py"
        if not sync_script.exists():
            print(f"❌ sync 脚本不存在: {sync_script}")
            return

        try:
            result = subprocess.run(
                ["python", str(sync_script)],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        except Exception as e:
            print(f"❌ 同步进度失败: {e}")

    def status(self):
        """查看状态"""
        print(f"\n{'='*60}")
        print("📊 文章状态统计")
        print(f"{'='*60}\n")

        total = len(self.index)
        completed = sum(1 for a in self.index.values() if a['status'] == 'completed')
        pending = sum(1 for a in self.index.values() if a['status'] == 'pending')

        print(f"总计: {total} 篇")
        print(f"已完成: {completed} 篇 ({completed/total*100:.1f}%)")
        print(f"待完成: {pending} 篇 ({pending/total*100:.1f}%)\n")

        # 按系列统计
        series_stats = {}
        for article in self.index.values():
            series = article['series']
            if series not in series_stats:
                series_stats[series] = {'total': 0, 'completed': 0}
            series_stats[series]['total'] += 1
            if article['status'] == 'completed':
                series_stats[series]['completed'] += 1

        print("按系列统计:")
        for series in sorted(series_stats.keys()):
            stats = series_stats[series]
            print(f"  {series}: {stats['completed']}/{stats['total']} 篇")

        print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="BioF3 ST 文章生成主控脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s publish 007              # 发布文章 007
  %(prog)s lint articles/002_*.md   # 质检单篇
  %(prog)s lint-all                 # 质检所有
  %(prog)s notebook articles/002_*.md  # 生成 notebook
  %(prog)s sync                     # 同步进度
  %(prog)s status                   # 查看状态
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # publish 命令
    publish_parser = subparsers.add_parser('publish', help='完整发布流程')
    publish_parser.add_argument('article_id', help='文章 ID (如 007)')
    publish_parser.add_argument('--auto', action='store_true', help='自动模式（返回 prompt）')

    # post-process 命令
    post_process_parser = subparsers.add_parser('post-process', help='文章生成后的后续处理')
    post_process_parser.add_argument('article_id', help='文章 ID (如 007)')
    post_process_parser.add_argument('--skip-test', action='store_true', help='跳过 Notebook 测试')
    post_process_parser.add_argument('--auto-continue', action='store_true', help='自动模式，遇到问题自动继续')

    # lint 命令
    lint_parser = subparsers.add_parser('lint', help='质检单篇文章')
    lint_parser.add_argument('file_path', help='文章文件路径')

    # lint-all 命令
    subparsers.add_parser('lint-all', help='质检所有文章')

    # notebook 命令
    notebook_parser = subparsers.add_parser('notebook', help='生成 Jupyter Notebook')
    notebook_parser.add_argument('file_path', help='文章文件路径')

    # sync 命令
    subparsers.add_parser('sync', help='同步进度')

    # status 命令
    subparsers.add_parser('status', help='查看状态')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    harness = ArticleHarness()

    if args.command == 'publish':
        result = harness.publish(args.article_id, auto_mode=getattr(args, 'auto', False))
        if isinstance(result, str) and args.auto:
            # 自动模式：输出 prompt 供 Claude 使用
            print("\n" + "="*60)
            print("📋 Agent Prompt:")
            print("="*60)
            print(result)
    elif args.command == 'post-process':
        harness.post_process(
            args.article_id,
            skip_test=getattr(args, 'skip_test', False),
            auto_continue=getattr(args, 'auto_continue', False)
        )
    elif args.command == 'lint':
        harness.lint(args.file_path)
    elif args.command == 'lint-all':
        harness.lint_all()
    elif args.command == 'notebook':
        harness.notebook(args.file_path)
    elif args.command == 'sync':
        harness.sync()
    elif args.command == 'status':
        harness.status()


if __name__ == "__main__":
    main()
