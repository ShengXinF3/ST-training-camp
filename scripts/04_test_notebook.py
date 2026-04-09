#!/usr/bin/env python3
"""
Notebook 执行测试脚本

用法:
    python scripts/04_test_notebook.py notebooks/003_xxx.ipynb
    python scripts/04_test_notebook.py notebooks/003_xxx.ipynb --mode full
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import tempfile


class NotebookTester:
    def __init__(self, notebook_path: str):
        self.notebook_path = Path(notebook_path)
        self.notebook = self._load_notebook()
        self.results = {
            'passed': False,
            'errors': [],
            'execution_time': 0,
            'cells_executed': 0,
            'total_cells': 0
        }

    def _load_notebook(self) -> Dict:
        """加载 notebook"""
        if not self.notebook_path.exists():
            raise FileNotFoundError(f"Notebook not found: {self.notebook_path}")

        with open(self.notebook_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test(self, mode: str = 'quick', timeout: int = 300) -> Dict:
        """
        执行 notebook 测试

        Args:
            mode: 'quick' (前3个代码块) 或 'full' (所有代码块)
            timeout: 超时时间（秒）

        Returns:
            测试结果字典
        """
        print(f"\n{'='*60}")
        print(f"📓 测试 Notebook: {self.notebook_path.name}")
        print(f"{'='*60}\n")

        start_time = time.time()

        # 统计代码块数量
        code_cells = [cell for cell in self.notebook['cells'] if cell['cell_type'] == 'code']
        self.results['total_cells'] = len(code_cells)

        # 确定要执行的代码块数量
        if mode == 'quick':
            cells_to_test = min(3, len(code_cells))
            print(f"🚀 快速测试模式: 执行前 {cells_to_test} 个代码块\n")
        else:
            cells_to_test = len(code_cells)
            print(f"🚀 完整测试模式: 执行所有 {cells_to_test} 个代码块\n")

        # 使用 nbconvert 执行 notebook
        try:
            result = self._execute_with_nbconvert(cells_to_test, timeout)
            self.results['passed'] = result['passed']
            self.results['errors'] = result['errors']
            self.results['cells_executed'] = result['cells_executed']
        except Exception as e:
            self.results['passed'] = False
            self.results['errors'].append({
                'cell': 0,
                'error_type': 'ExecutionError',
                'error': str(e)
            })

        self.results['execution_time'] = time.time() - start_time

        return self.results

    def _execute_with_nbconvert(self, cells_to_test: int, timeout: int) -> Dict:
        """使用 nbconvert 执行 notebook"""
        # 创建临时 notebook（只包含要测试的代码块）
        temp_nb = self._create_temp_notebook(cells_to_test)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False, encoding='utf-8') as f:
            json.dump(temp_nb, f, ensure_ascii=False, indent=1)
            temp_path = f.name

        try:
            # 执行 notebook
            cmd = [
                'jupyter', 'nbconvert',
                '--to', 'notebook',
                '--execute',
                '--ExecutePreprocessor.timeout=' + str(timeout),
                '--output', temp_path,
                temp_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 10
            )

            if result.returncode == 0:
                return {
                    'passed': True,
                    'errors': [],
                    'cells_executed': cells_to_test
                }
            else:
                # 解析错误信息
                error_info = self._parse_error(result.stderr)
                return {
                    'passed': False,
                    'errors': [error_info],
                    'cells_executed': error_info.get('cell', 0)
                }

        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'errors': [{
                    'cell': cells_to_test,
                    'error_type': 'TimeoutError',
                    'error': f'Execution timeout after {timeout}s'
                }],
                'cells_executed': cells_to_test
            }

        except FileNotFoundError:
            # jupyter nbconvert 未安装
            return {
                'passed': False,
                'errors': [{
                    'cell': 0,
                    'error_type': 'EnvironmentError',
                    'error': 'jupyter nbconvert not found. Install: pip install nbconvert'
                }],
                'cells_executed': 0
            }

        finally:
            # 清理临时文件
            Path(temp_path).unlink(missing_ok=True)

    def _create_temp_notebook(self, cells_to_test: int) -> Dict:
        """创建临时 notebook（只包含前 N 个代码块）"""
        temp_nb = {
            'cells': [],
            'metadata': self.notebook['metadata'],
            'nbformat': self.notebook['nbformat'],
            'nbformat_minor': self.notebook['nbformat_minor']
        }

        code_cell_count = 0
        for cell in self.notebook['cells']:
            if cell['cell_type'] == 'code':
                if code_cell_count < cells_to_test:
                    temp_nb['cells'].append(cell)
                    code_cell_count += 1
                else:
                    break
            else:
                # 保留 markdown 单元格（用于上下文）
                temp_nb['cells'].append(cell)

        return temp_nb

    def _parse_error(self, stderr: str) -> Dict:
        """解析错误信息"""
        error_info = {
            'cell': 0,
            'error_type': 'UnknownError',
            'error': stderr
        }

        # 尝试提取单元格编号
        if 'Cell' in stderr:
            import re
            match = re.search(r'Cell (\d+)', stderr)
            if match:
                error_info['cell'] = int(match.group(1))

        # 尝试提取错误类型
        if 'NameError' in stderr:
            error_info['error_type'] = 'NameError'
        elif 'ImportError' in stderr or 'ModuleNotFoundError' in stderr:
            error_info['error_type'] = 'ImportError'
        elif 'AttributeError' in stderr:
            error_info['error_type'] = 'AttributeError'
        elif 'TypeError' in stderr:
            error_info['error_type'] = 'TypeError'
        elif 'ValueError' in stderr:
            error_info['error_type'] = 'ValueError'

        return error_info

    def print_report(self):
        """打印测试报告"""
        print(f"\n{'='*60}")
        print(f"测试报告: {self.notebook_path.name}")
        print(f"{'='*60}\n")

        if self.results['passed']:
            print(f"✅ 测试通过")
            print(f"   执行了 {self.results['cells_executed']}/{self.results['total_cells']} 个代码块")
            print(f"   耗时: {self.results['execution_time']:.2f}s")
        else:
            print(f"❌ 测试失败")
            print(f"   执行了 {self.results['cells_executed']}/{self.results['total_cells']} 个代码块")
            print(f"   耗时: {self.results['execution_time']:.2f}s\n")

            print(f"🚫 发现 {len(self.results['errors'])} 个错误:\n")
            for i, error in enumerate(self.results['errors'], 1):
                print(f"  错误 #{i}:")
                print(f"    代码块: #{error.get('cell', 'unknown')}")
                print(f"    类型: {error.get('error_type', 'Unknown')}")
                print(f"    信息: {error.get('error', 'No details')[:200]}")
                print()

        print(f"{'='*60}\n")

        return self.results['passed']


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/04_test_notebook.py <notebook路径> [--mode quick|full]")
        sys.exit(1)

    notebook_path = sys.argv[1]
    mode = 'quick'

    if '--mode' in sys.argv:
        mode_idx = sys.argv.index('--mode')
        if mode_idx + 1 < len(sys.argv):
            mode = sys.argv[mode_idx + 1]

    if mode not in ['quick', 'full']:
        print(f"❌ 无效的模式: {mode}（应为 'quick' 或 'full'）")
        sys.exit(1)

    tester = NotebookTester(notebook_path)
    tester.test(mode=mode)
    passed = tester.print_report()

    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
