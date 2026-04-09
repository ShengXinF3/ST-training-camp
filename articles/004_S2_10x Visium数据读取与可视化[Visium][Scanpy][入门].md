---
title: "10x Visium 数据读取与可视化"
article_id: "004"
series: "S2"
tags: ["Visium", "Scanpy", "入门"]
difficulty: "入门"
keywords: ["Visium", "数据读取", "空间可视化", "Scanpy", "AnnData"]
created: "2026-04-08"
updated: "2026-04-08"
---

# 10x Visium 数据读取与可视化

## 第一部分：Why & What

### 为什么需要专门的数据读取流程？

拿到一份 10x Visium 数据，你会发现它不是单个文件，而是一个包含多个子文件夹的目录结构。这些文件分散存储着基因表达矩阵、空间坐标、组织图像等信息。如果手动拼接这些数据，不仅繁琐，还容易出错。

更重要的是，空间转录组 (Spatial Transcriptomics, ST) 数据的特殊性在于：它需要同时管理三类信息：
- **表达矩阵**：每个 spot（Visium 平台的空间单元，直径 55 µm）检测到的基因表达量
- **空间坐标**：每个 spot 在组织切片上的物理位置
- **组织图像**：H&E 染色的高分辨率组织切片图

这三类信息必须精确对应，任何一个环节出错都会导致后续分析失败。Scanpy 提供的 `sc.read_visium()` 函数正是为了解决这个问题：它能自动解析 10x Space Ranger 的输出目录，将所有信息整合到一个 AnnData 对象中。

### 什么是 AnnData？

AnnData (Annotated Data) 是 Python 生态中专门为单细胞和空间转录组设计的数据结构。它的核心优势是：
- **统一接口**：无论是单细胞 RNA-seq 还是空间转录组，都用同一套 API (Application Programming Interface, 应用程序接口)
- **分层存储**：表达矩阵、基因注释、细胞/spot 注释、空间坐标、图像分别存储，互不干扰
- **高效计算**：底层使用稀疏矩阵，节省内存

对于 Visium 数据，AnnData 的结构如下：

```
adata
├── X: 表达矩阵 (n_spots × n_genes)
├── obs: spot 注释 (n_spots 行)
│   ├── in_tissue: 是否在组织内
│   ├── array_row, array_col: 阵列坐标
│   └── ...
├── var: 基因注释 (n_genes 行)
│   ├── gene_ids: Ensembl ID (基因标识符, Identifier)
│   ├── feature_types: 基因类型
│   └── ...
├── uns: 非结构化数据
│   └── spatial: 空间信息字典
│       └── [library_id]
│           ├── images: 组织图像
│           ├── scalefactors: 坐标缩放因子
│           └── ...
└── obsm: 多维注释
    └── spatial: spot 的像素坐标 (n_spots × 2)
```

这种结构让我们可以用统一的方式访问所有信息，而不需要记住每个文件的格式和路径。

---

## 第二部分：How

### 数据准备

10x Space Ranger 的输出目录通常包含以下结构：

```
sample_data/
├── filtered_feature_bc_matrix/
│   ├── barcodes.tsv.gz
│   ├── features.tsv.gz
│   └── matrix.mtx.gz
└── spatial/
    ├── tissue_positions_list.csv
    ├── scalefactors_json.json
    ├── tissue_hires_image.png
    └── tissue_lowres_image.png
```

如果你还没有数据，可以从 10x Genomics 官网下载示例数据集，或使用 Squidpy 提供的公开数据集。

### 读取数据

```python
import scanpy as sc
import squidpy as sq
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 设置随机种子，确保结果可复现
np.random.seed(42)

# 使用 Squidpy 提供的公开数据集
adata = sq.datasets.visium_hne_adata()

# 或者读取本地 Visium 数据
# adata = sc.read_visium(
#     path='sample_data/',  # Space Ranger 输出目录
#     count_file='filtered_feature_bc_matrix.h5',  # 可选：使用 h5 格式
#     library_id='sample_01',  # 样本标识符
#     load_images=True  # 加载组织图像
# )

# 查看数据基本信息
print(adata)
```

**输出解读**：
输出显示 AnnData 对象的基本结构，包括 spot 数量（n_obs）和基因数量（n_vars）。Visium 数据通常有 2000-5000 个 spot，10000-20000 个基因。obs 包含 spot 注释（如 in_tissue 标记是否在组织内），var 包含基因注释，uns 存储空间信息，obsm 存储像素坐标。

这里有几个关键参数：
- `path`: Space Ranger 输出的根目录
- `count_file`: 如果有 `.h5` 文件，读取速度更快；否则自动读取 `filtered_feature_bc_matrix/` 目录
- `library_id`: 给样本命名，后续多样本分析时用于区分
- `load_images`: 是否加载组织图像（默认 True）

对于快速测试，推荐使用 `sq.datasets.visium_hne_adata()` 加载公开数据集，无需下载文件。

### 数据质量检查

读取数据后，第一步是检查数据质量。我们需要关注三个核心指标：

```python
# 计算 QC 指标
adata.var['mt'] = adata.var_names.str.startswith('MT-')  # 标记线粒体基因
sc.pp.calculate_qc_metrics(
    adata,
    qc_vars=['mt'],
    percent_top=None,
    log1p=False,
    inplace=True
)

# 查看关键指标
print(f"Total spots: {adata.n_obs}")
print(f"Spots in tissue: {adata.obs['in_tissue'].sum()}")
print(f"Total genes: {adata.n_vars}")
print(f"Median UMI per spot: {np.median(adata.obs['total_counts']):.0f}")
print(f"Median genes per spot: {np.median(adata.obs['n_genes_by_counts']):.0f}")
```

**输出解读**：
这些数字反映数据质量的三个维度：
- **总 spot 数**：Visium 芯片上的所有 spot（包括组织内和组织外）
- **组织内 spot 数**：实际覆盖组织的 spot，这是分析的主要对象
- **中位 UMI 数**：每个 spot 捕获的 RNA 分子数，反映测序深度（通常 5000-15000）
- **中位基因数**：每个 spot 检测到的基因种类，反映数据复杂度（通常 2000-5000）

### 诊断图：QC 指标分布

```python
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# 1. Total UMI counts distribution
axes[0].hist(adata.obs['total_counts'], bins=50, edgecolor='black')
axes[0].set_xlabel('Total UMI Counts')
axes[0].set_ylabel('Number of Spots')
axes[0].set_title('UMI Count Distribution')
axes[0].axvline(np.median(adata.obs['total_counts']), 
                color='red', linestyle='--', label='Median')
axes[0].legend()

# 2. Number of genes detected
axes[1].hist(adata.obs['n_genes_by_counts'], bins=50, edgecolor='black')
axes[1].set_xlabel('Number of Genes Detected')
axes[1].set_ylabel('Number of Spots')
axes[1].set_title('Gene Count Distribution')
axes[1].axvline(np.median(adata.obs['n_genes_by_counts']), 
                color='red', linestyle='--', label='Median')
axes[1].legend()

# 3. Mitochondrial gene percentage
axes[2].hist(adata.obs['pct_counts_mt'], bins=50, edgecolor='black')
axes[2].set_xlabel('Mitochondrial Gene Percentage (%)')
axes[2].set_ylabel('Number of Spots')
axes[2].set_title('MT Gene Percentage Distribution')
axes[2].axvline(np.median(adata.obs['pct_counts_mt']), 
                color='red', linestyle='--', label='Median')
axes[2].legend()

plt.tight_layout()
plt.savefig('qc_distributions.png', dpi=300, bbox_inches='tight')
plt.show()
```

**如何解读这些分布图**：
- **UMI 分布**：正常情况下应呈单峰分布，如果出现双峰，可能存在批次效应 (Batch Effect) 或组织异质性
- **基因数分布**：与 UMI 分布类似，但更能反映生物学复杂度
- **线粒体基因比例**：通常 < 20%，过高提示细胞损伤或死亡

### 空间可视化

空间转录组的核心优势是保留了空间信息。我们可以将 QC 指标映射到组织切片上：

```python
fig, axes = plt.subplots(2, 2, figsize=(12, 12))

# 1. Tissue image with spots
# 将布尔值转换为字符串以避免绘图错误
adata.obs['in_tissue_str'] = adata.obs['in_tissue'].astype(str)

sc.pl.spatial(
    adata,
    img_key='hires',
    color='in_tissue_str',
    size=1.5,
    ax=axes[0, 0],
    show=False,
    title='Spot Coverage'
)

# 2. Total UMI counts
sc.pl.spatial(
    adata,
    img_key='hires',
    color='total_counts',
    size=1.5,
    ax=axes[0, 1],
    show=False,
    title='Total UMI Counts',
    cmap='viridis'
)

# 3. Number of genes detected
sc.pl.spatial(
    adata,
    img_key='hires',
    color='n_genes_by_counts',
    size=1.5,
    ax=axes[1, 0],
    show=False,
    title='Number of Genes Detected',
    cmap='viridis'
)

# 4. Mitochondrial gene percentage
sc.pl.spatial(
    adata,
    img_key='hires',
    color='pct_counts_mt',
    size=1.5,
    ax=axes[1, 1],
    show=False,
    title='Mitochondrial Gene Percentage',
    cmap='Reds'
)

plt.tight_layout()
plt.savefig('spatial_qc.png', dpi=300, bbox_inches='tight')
plt.show()
```

**空间模式的生物学意义**：
- **均匀分布**：技术质量良好，没有明显的空间偏差
- **边缘效应**：边缘 spot 的 UMI 数偏低，可能是组织切片不完整
- **局部高线粒体**：可能对应坏死区域或代谢活跃区域

### 对照：组织内 vs 组织外

组织外的 spot 是天然的负对照 (Negative Control)，它们应该检测到极少的 UMI：

```python
# 比较组织内外的 UMI 数
in_tissue = adata.obs[adata.obs['in_tissue'] == 1]['total_counts']
out_tissue = adata.obs[adata.obs['in_tissue'] == 0]['total_counts']

fig, ax = plt.subplots(figsize=(8, 6))
ax.boxplot(
    [in_tissue, out_tissue],
    labels=['In Tissue', 'Out of Tissue'],
    showfliers=False
)
ax.set_ylabel('Total UMI Counts')
ax.set_title('UMI Counts: In vs Out of Tissue')
ax.set_yscale('log')
plt.savefig('in_vs_out_tissue.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"Median UMI (in tissue): {np.median(in_tissue):.0f}")
print(f"Median UMI (out of tissue): {np.median(out_tissue):.0f}")
print(f"Fold change: {np.median(in_tissue) / np.median(out_tissue):.1f}x")
```

**输出解读**：
- 组织内 spot 的 UMI 数通常是组织外的 10-100 倍
- 如果差异不明显，说明组织外存在污染或组织内质量不佳

### 坐标系统详解

Visium 数据包含两套坐标系统：

1. **阵列坐标** (array_row, array_col)：spot 在芯片上的逻辑位置（整数）
2. **像素坐标** (spatial)：spot 在组织图像上的物理位置（浮点数）

```python
# 查看坐标信息
print("Array coordinates (first 5 spots):")
print(adata.obs[['array_row', 'array_col']].head())

print("\nPixel coordinates (first 5 spots):")
print(adata.obsm['spatial'][:5])

# 可视化两套坐标系统
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 将布尔值转换为数值以便绘图
in_tissue_numeric = adata.obs['in_tissue'].astype(int)

# 阵列坐标
axes[0].scatter(
    adata.obs['array_col'],
    adata.obs['array_row'],
    c=in_tissue_numeric,
    cmap='coolwarm',
    s=10
)
axes[0].set_xlabel('Array Column')
axes[0].set_ylabel('Array Row')
axes[0].set_title('Array Coordinates')
axes[0].invert_yaxis()

# 像素坐标
axes[1].scatter(
    adata.obsm['spatial'][:, 0],
    adata.obsm['spatial'][:, 1],
    c=in_tissue_numeric,
    cmap='coolwarm',
    s=10
)
axes[1].set_xlabel('Pixel X')
axes[1].set_ylabel('Pixel Y')
axes[1].set_title('Pixel Coordinates')
axes[1].invert_yaxis()

plt.tight_layout()
plt.savefig('coordinate_systems.png', dpi=300, bbox_inches='tight')
plt.show()
```

**两套坐标的用途**：
- **阵列坐标**：用于计算空间邻域 (Neighborhood)，因为相邻 spot 的阵列坐标差值固定
- **像素坐标**：用于叠加到组织图像上，实现精确的空间可视化

### 基因表达可视化

最后，我们可以可视化特定基因的空间表达模式：

```python
# 选择几个标志基因（小鼠脑组织）
# 注意：小鼠基因命名为首字母大写，人类基因为全大写
marker_genes = ['Cd3d', 'Cd79a', 'Ms4a1', 'Cd68']  # T细胞、B细胞、巨噬细胞标志基因

# 检查基因是否存在
available_genes = [g for g in marker_genes if g in adata.var_names]
print(f"Available genes: {available_genes}")

# 如果没有找到，尝试查找脑组织特异性基因
if not available_genes:
    # 小鼠脑组织常见标志基因
    brain_markers = ['Snap25', 'Gad1', 'Slc17a7', 'Mbp', 'Aldh1l1']
    available_genes = [g for g in brain_markers if g in adata.var_names]
    print(f"Brain-specific genes: {available_genes}")

# 空间表达可视化
if available_genes:
    sc.pl.spatial(
        adata,
        img_key='hires',
        color=available_genes[:4],  # 最多显示4个基因
        size=1.5,
        ncols=2,
        cmap='viridis',
        save='_marker_genes.png'
    )
else:
    print("⚠️ 未找到指定的标志基因，请检查基因命名")
```

**如何选择标志基因**：
- **物种差异**：小鼠基因首字母大写（如 Cd3d），人类基因全大写（如 CD3D）
- 根据组织类型选择（如肿瘤、脑、肝等）
- 优先选择高表达、空间特异性强的基因
- 避免选择管家基因（如 Gapdh、Actb），它们在所有位置都高表达

---

## 第三部分：What's Next

### 验收清单

完成本文的学习后，你应该能够：

- 理解 Visium 数据的目录结构和文件组成
- 使用 `sc.read_visium()` 读取数据到 AnnData 对象
- 计算并解读 QC 指标（UMI 数、基因数、线粒体比例）
- 绘制 QC 指标的分布图和空间图
- 区分阵列坐标和像素坐标的用途
- 使用组织外 spot 作为负对照验证数据质量
- 可视化特定基因的空间表达模式

### 常见问题

**Q1: 读取数据时报错 "FileNotFoundError"**

检查以下几点：
- `path` 参数是否指向正确的目录
- 目录中是否包含 `filtered_feature_bc_matrix/` 和 `spatial/` 子文件夹
- 如果使用 `count_file` 参数，确保 `.h5` 文件存在

**Q2: 组织外 spot 的 UMI 数异常高**

可能原因：
- 组织切片时有碎片掉落到组织外区域
- Space Ranger 的组织检测算法不准确
- 解决方法：手动筛选组织内 spot（`adata = adata[adata.obs['in_tissue'] == 1]`）

**Q3: 空间可视化时图像模糊**

- 使用 `img_key='hires'` 而不是 `'lowres'`
- 增大 `size` 参数（但不要超过 2.0，否则 spot 会重叠）
- 保存图片时设置 `dpi=300`

**Q4: 某些基因无法可视化**

- 检查基因名是否正确（区分大小写）
- 使用 `adata.var_names` 查看所有可用基因
- 如果基因表达量极低，可能被过滤掉了

### 边界声明

本文展示的方法适用于：
- 10x Visium 标准流程（Space Ranger 输出）
- 单个样本的初步探索
- 数据质量的快速评估

本文不涉及：
- Visium HD (High Definition, 高分辨率) 数据（需要特殊处理，见后续文章）
- 多样本批次校正
- 高级空间分析（空间域识别、细胞通讯等）

---

## 核心要点回顾

本文建立了 Visium 数据分析的起点：从原始文件到可解释的空间图谱。核心要点包括：

**数据结构理解**：Visium 数据不是单一文件，而是表达矩阵、空间坐标、组织图像的三元组。AnnData 对象通过分层存储（X 存矩阵、obs 存 spot 注释、obsm 存坐标、uns 存图像）将这三类信息统一管理，避免了手动拼接的错误风险。

**质量控制的三个维度**：UMI 数反映测序深度（中位数通常 5000-15000），基因数反映生物学复杂度（中位数通常 2000-5000），线粒体基因比例反映细胞损伤（通常 < 20%）。这三个指标必须同时检查，单一指标无法判断数据质量。

**空间可视化的诊断价值**：将 QC 指标映射到组织切片上，能发现分布图无法揭示的问题。均匀分布说明技术质量良好，边缘效应提示切片不完整，局部高线粒体可能对应坏死区域。空间模式是技术偏差和生物学信号的混合体，需要结合组织学知识解读。

**负对照的关键作用**：组织外 spot 是天然的负对照，其 UMI 数应远低于组织内（通常 10-100 倍差异）。如果差异不明显，说明存在污染或组织检测算法失败，必须在后续分析中手动筛选组织内 spot。

**坐标系统的双重性**：阵列坐标用于计算空间邻域（因为相邻 spot 的坐标差值固定），像素坐标用于叠加到组织图像（因为需要精确对齐）。混淆两者会导致空间分析失败。

**可复现性保障**：代码中设置随机种子、保存所有图表、打印关键指标的中位数，确保结果可被他人验证。这是科学分析的基本要求。

本文建立的工作流程是所有下游分析的基础。如果数据读取或质量检查出现问题，后续的聚类、差异分析、空间域识别都会失败。
