# 实践 Notebooks

> 本目录包含所有文章的可执行 Jupyter Notebook，用于验证代码的可行性

## 📁 目录结构

```
notebooks/
├── README.md                                   # 本文件
├── 002_主线01_项目开箱_实践.ipynb              # 文章 002 的可执行代码
├── 003_主线02_QC指标空间化_实践.ipynb          # 文章 003 的可执行代码
├── 004_主线03_空间伪影识别_实践.ipynb          # 文章 004 的可执行代码
└── 005_主线04_组织外spot识别_实践.ipynb        # 文章 005 的可执行代码
```

---

## 🚀 快速开始

### 1. 安装依赖

首次使用前，需要安装必要的 Python 包：

```bash
pip install scanpy squidpy matplotlib jupyter
```

或使用 conda：

```bash
conda install -c conda-forge scanpy squidpy matplotlib jupyter
```

### 2. 启动 Jupyter

```bash
cd notebooks
jupyter notebook
```

或使用 JupyterLab：

```bash
jupyter lab
```

### 3. 运行 Notebook

- 打开任意 `.ipynb` 文件
- 按顺序执行每个 Cell（Shift + Enter）
- 查看输出结果和可视化图表

---

## 📝 Notebook 说明

### 每个 Notebook 包含

1. **环境准备**：导入必要的库，设置随机种子
2. **分步代码**：文章中的所有代码块，按顺序组织
3. **验收清单**：检查每个步骤是否成功
4. **可视化输出**：图表和统计结果

### Notebook 特点

- ✅ **可复现**：设置随机种子，结果一致
- ✅ **分步执行**：每个 Cell 独立，便于调试
- ✅ **即时反馈**：立即看到代码执行结果
- ✅ **可修改**：可以调整参数，观察变化

---

## 🛠️ 自动生成 Notebook

如果文章更新，可以使用脚本重新生成 Notebook：

```bash
# 为单篇文章生成 Notebook
python scripts/article_to_notebook.py articles/002_主线01_项目开箱.md

# 批量生成所有文章的 Notebook
for file in articles/*.md; do
    python scripts/article_to_notebook.py "$file"
done
```

---

## 📊 数据说明

### 使用的数据集

所有 Notebook 使用 Squidpy 内置的示例数据：

```python
adata = sq.datasets.visium_hne_adata()
```

**数据特点**：
- 平台：10x Visium
- 组织：小鼠脑切片（H&E 染色）
- Spot 数：~3,000 个
- 基因数：~18,000 个
- 大小：~50 MB（自动下载）

### 首次运行

首次运行时，Squidpy 会自动下载数据到缓存目录：
- macOS/Linux: `~/.cache/squidpy/`
- Windows: `C:\Users\<用户名>\.cache\squidpy\`

下载完成后，后续运行会直接使用缓存数据。

---

## ⚠️ 常见问题

### 1. 依赖安装失败

**问题**：`pip install scanpy` 报错

**解决**：
```bash
# 使用 conda 安装（推荐）
conda install -c conda-forge scanpy squidpy

# 或升级 pip
pip install --upgrade pip
pip install scanpy squidpy
```

### 2. 数据下载慢

**问题**：`sq.datasets.visium_hne_adata()` 下载很慢

**解决**：
- 使用代理或 VPN
- 手动下载数据后放到缓存目录
- 使用国内镜像源（如果有）

### 3. 图表不显示

**问题**：运行代码后没有图表输出

**解决**：
```python
# 在 Notebook 开头添加
%matplotlib inline

# 或使用交互式后端
%matplotlib widget
```

### 4. 内存不足

**问题**：运行时提示内存不足

**解决**：
- 关闭其他程序释放内存
- 只保留组织内 spot：`adata = adata[adata.obs['in_tissue'] == 1]`
- 减少可视化的 DPI：`sc.settings.set_figure_params(dpi=50)`

---

## 🎯 使用建议

### 学习路径

1. **按顺序学习**：从 002 开始，逐步深入
2. **动手实践**：不要只看，要运行每个 Cell
3. **修改参数**：尝试调整参数，观察结果变化
4. **记录笔记**：在 Notebook 中添加自己的 Markdown Cell

### 最佳实践

1. **保存副本**：修改前先复制一份 Notebook
2. **清理输出**：提交前清理输出（Cell → All Output → Clear）
3. **重启内核**：遇到问题时重启内核重新运行
4. **版本控制**：使用 Git 管理 Notebook 版本

---

## 📚 相关资源

### 官方文档

- [Scanpy 文档](https://scanpy.readthedocs.io/)
- [Squidpy 文档](https://squidpy.readthedocs.io/)
- [Jupyter 文档](https://jupyter.org/documentation)

### 教程

- [Scanpy 教程](https://scanpy-tutorials.readthedocs.io/)
- [Squidpy 教程](https://squidpy.readthedocs.io/en/stable/tutorials.html)

---

## 🔄 更新记录

- 2026-04-08: 创建 notebooks 目录，生成前 4 篇文章的 Notebook
- 2026-04-08: 添加自动生成脚本 `article_to_notebook.py`

---

**核心理念**: 代码必须经过实践验证，才能可靠地交付给读者。
