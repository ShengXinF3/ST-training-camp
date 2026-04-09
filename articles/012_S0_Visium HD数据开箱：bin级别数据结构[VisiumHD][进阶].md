---
title: "Visium HD 数据开箱：bin 级别数据结构"
article_id: "012"
series: "S0"
tags: ["VisiumHD", "进阶"]
difficulty: "进阶"
keywords: ["Visium HD", "bin", "数据结构", "空间转录组"]
created: "2026-04-08"
updated: "2026-04-08"
---

# Visium HD 数据开箱：bin 级别数据结构

## 第一部分：Why & What - 为什么需要理解 bin？

### 从 Visium 到 Visium HD：分辨率的跃迁

如果你用过 Visium，你会习惯一个概念：spot。每个 spot 直径 55 µm，覆盖约 10 个细胞。这是 Visium 的基本空间单元。

但 Visium HD 改变了游戏规则。它不再使用固定的 spot，而是引入了 **bin**（空间分箱单元）这个概念。bin 是一个正方形区域，边长可以是 2 µm、8 µm、16 µm 等。最小的 2 µm bin 接近亚细胞分辨率，而 8 µm bin 大约对应单细胞尺度。

这带来了一个根本性的变化：

- **Visium**: 数据结构固定，每个 spot 就是一个观测单元
- **Visium HD**: 数据结构灵活，你可以选择不同分辨率的 bin，甚至可以进行细胞分割

### bin vs cell：两种数据组织方式

Visium HD 提供两种数据组织方式：

1. **bin 级别数据**：将组织划分为规则的正方形网格，每个 bin 是一个观测单元
2. **cell 级别数据**（可选）：通过细胞分割算法识别单个细胞，每个细胞是一个观测单元

本文聚焦 bin 级别数据，因为：
- bin 数据是 Space Ranger 的标准输出，无需额外处理
- bin 数据结构简单，适合快速探索和质控
- 很多分析任务（如空间域识别、空间可变基因检测）在 bin 级别已经足够

cell 级别数据我们会在后续文章中专门讨论。

### 你会拿到什么文件？

当你从 10x Genomics 下载 Visium HD 数据或运行 Space Ranger 后，你会得到一个 `outs/` 目录，核心文件包括：

```
outs/
├── binned_outputs/
│   ├── square_002um/          # 2 µm bin 数据
│   │   ├── filtered_feature_bc_matrix.h5
│   │   └── spatial/
│   ├── square_008um/          # 8 µm bin 数据
│   │   ├── filtered_feature_bc_matrix.h5
│   │   └── spatial/
│   └── square_016um/          # 16 µm bin 数据
│       ├── filtered_feature_bc_matrix.h5
│       └── spatial/
└── spatial/
    ├── tissue_hires_image.png
    └── scalefactors_json.json
```

每个分辨率的 bin 数据都是独立的，包含：
- **表达矩阵**：`filtered_feature_bc_matrix.h5`（基因 × bin）
- **空间坐标**：`spatial/tissue_positions.parquet`（bin 的 x, y 坐标）
- **组织影像**：共享的高分辨率组织切片图像

### 本文目标

读完本文，你将能够：
1. 理解 bin 的定义和不同分辨率的含义
2. 读取和检查 Visium HD bin 级别数据
3. 比较不同分辨率 bin 的数据特征
4. 为后续分析选择合适的 bin 分辨率

## 第二部分：How - 如何读取和检查 bin 数据

### 环境准备

```python
import scanpy as sc
import squidpy as sq
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 设置随机种子（可复现）
np.random.seed(42)

# 设置绘图参数
sc.set_figure_params(dpi=100, frameon=False)
sns.set_style("white")

print(f"scanpy version: {sc.__version__}")
print(f"squidpy version: {sq.__version__}")
```

**预期输出**：
```
scanpy version: 1.10.0
squidpy version: 1.4.1
```

### 读取单个分辨率的 bin 数据

我们先从 8 µm bin 开始，这是平衡分辨率和计算资源的推荐选择。

```python
# 定义数据路径
data_dir = Path("path/to/visium_hd_data/outs")
bin_size = "square_008um"

# 读取数据
adata = sc.read_10x_h5(
    data_dir / "binned_outputs" / bin_size / "filtered_feature_bc_matrix.h5"
)

# 读取空间坐标
spatial_dir = data_dir / "binned_outputs" / bin_size / "spatial"
positions = pd.read_parquet(spatial_dir / "tissue_positions.parquet")

# 将空间坐标添加到 adata
adata.obs = adata.obs.join(positions, how="left")
adata.obsm["spatial"] = adata.obs[["pxl_row_in_fullres", "pxl_col_in_fullres"]].values

# 读取组织影像
adata.uns["spatial"] = {
    "visium_hd": {
        "images": {
            "hires": plt.imread(data_dir / "spatial" / "tissue_hires_image.png")
        },
        "scalefactors": {
            "tissue_hires_scalef": 1.0,  # 根据实际情况调整
            "spot_diameter_fullres": 8.0  # bin 边长
        }
    }
}

print(f"Data shape: {adata.shape}")
print(f"Bins: {adata.n_obs}, Genes: {adata.n_vars}")
```

**预期输出**：
```
Data shape: (245678, 18085)
Bins: 245678, Genes: 18085
```

**关键点**：
- Visium HD 的 bin 数量远超 Visium 的 spot 数量（Visium 通常 3000-5000 个 spot）
- 8 µm bin 的数据量已经很大，2 µm bin 会更大（通常是 8 µm 的 16 倍）

### 检查 bin 的基本信息

```python
# 查看 obs（bin 的元数据）
print(adata.obs.head())

# 查看空间坐标范围
print(f"\nSpatial coordinates range:")
print(f"  X: {adata.obs['pxl_col_in_fullres'].min():.0f} - {adata.obs['pxl_col_in_fullres'].max():.0f}")
print(f"  Y: {adata.obs['pxl_row_in_fullres'].min():.0f} - {adata.obs['pxl_row_in_fullres'].max():.0f}")

# 计算基本 QC 指标
adata.var["mt"] = adata.var_names.str.startswith("MT-")
sc.pp.calculate_qc_metrics(
    adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True
)

# 查看 QC 指标分布
print(f"\nQC metrics summary:")
print(adata.obs[["total_counts", "n_genes_by_counts", "pct_counts_mt"]].describe())
```

**预期输出**：
```
                                    total_counts  n_genes_by_counts  pct_counts_mt
barcode                                                                            
AAACAAGTATCTCCCA-1                           743                571           13.2
AAACACCAATAACTGC-1                           448                326            8.9
AAACAGAGCGACTCCT-1                           550                420           11.5
...

Spatial coordinates range:
  X: 1200 - 18500
  Y: 800 - 15200

QC metrics summary:
       total_counts  n_genes_by_counts  pct_counts_mt
count      245678.0           245678.0       245678.0
mean          892.3              654.2           10.8
std           456.7              298.4            5.2
min            50.0               35.0            0.5
25%           520.0              425.0            7.1
50%           850.0              630.0           10.2
75%          1180.0              850.0           13.8
max          5200.0             2800.0           45.0
```

### 可视化 bin 的空间分布

```python
# 创建诊断图：QC 指标的空间分布
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 总 UMI 数
sc.pl.spatial(
    adata,
    color="total_counts",
    spot_size=1.0,
    frameon=False,
    title="Total UMI Counts",
    ax=axes[0],
    show=False
)

# 检测到的基因数
sc.pl.spatial(
    adata,
    color="n_genes_by_counts",
    spot_size=1.0,
    frameon=False,
    title="Number of Genes Detected",
    ax=axes[1],
    show=False
)

# 线粒体基因比例
sc.pl.spatial(
    adata,
    color="pct_counts_mt",
    spot_size=1.0,
    frameon=False,
    title="Mitochondrial Gene Percentage",
    ax=axes[2],
    show=False
)

plt.tight_layout()
plt.savefig("bin_qc_spatial.png", dpi=300, bbox_inches="tight")
plt.show()
```

**诊断要点**：
- **总 UMI 数**：应该在组织内部较高，组织外部接近 0
- **基因数**：与 UMI 数正相关，但不是线性关系
- **线粒体比例**：过高（>20%）可能表示细胞损伤或死亡

### 比较不同分辨率的 bin

现在我们读取三种分辨率的数据，比较它们的特征。

```python
# 读取三种分辨率的数据
bin_sizes = ["square_002um", "square_008um", "square_016um"]
adatas = {}

for bin_size in bin_sizes:
    # 读取表达矩阵
    adata_tmp = sc.read_10x_h5(
        data_dir / "binned_outputs" / bin_size / "filtered_feature_bc_matrix.h5"
    )
    
    # 读取空间坐标
    spatial_dir = data_dir / "binned_outputs" / bin_size / "spatial"
    positions = pd.read_parquet(spatial_dir / "tissue_positions.parquet")
    adata_tmp.obs = adata_tmp.obs.join(positions, how="left")
    
    # 计算 QC 指标
    adata_tmp.var["mt"] = adata_tmp.var_names.str.startswith("MT-")
    sc.pp.calculate_qc_metrics(
        adata_tmp, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True
    )
    
    adatas[bin_size] = adata_tmp
    print(f"{bin_size}: {adata_tmp.n_obs} bins, {adata_tmp.n_vars} genes")
```

**预期输出**：
```
square_002um: 3850124 bins, 18085 genes
square_008um: 245678 bins, 18085 genes
square_016um: 62456 bins, 18085 genes
```

**关键观察**：
- bin 数量随分辨率呈几何级数变化（2 µm → 8 µm：16 倍减少）
- 基因数保持不变（都是全基因组检测）

### 比较 QC 指标分布

```python
# 提取 QC 指标
qc_data = []
for bin_size, adata_tmp in adatas.items():
    df = adata_tmp.obs[["total_counts", "n_genes_by_counts", "pct_counts_mt"]].copy()
    df["bin_size"] = bin_size
    qc_data.append(df)

qc_df = pd.concat(qc_data, axis=0)

# 绘制对比图
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# 总 UMI 数分布
sns.violinplot(
    data=qc_df,
    x="bin_size",
    y="total_counts",
    ax=axes[0],
    order=bin_sizes
)
axes[0].set_xlabel("Bin Size")
axes[0].set_ylabel("Total UMI Counts")
axes[0].set_title("UMI Distribution Across Bin Sizes")

# 基因数分布
sns.violinplot(
    data=qc_df,
    x="bin_size",
    y="n_genes_by_counts",
    ax=axes[1],
    order=bin_sizes
)
axes[1].set_xlabel("Bin Size")
axes[1].set_ylabel("Number of Genes")
axes[1].set_title("Gene Detection Across Bin Sizes")

# 线粒体比例分布
sns.violinplot(
    data=qc_df,
    x="bin_size",
    y="pct_counts_mt",
    ax=axes[2],
    order=bin_sizes
)
axes[2].set_xlabel("Bin Size")
axes[2].set_ylabel("Mitochondrial %")
axes[2].set_title("MT Percentage Across Bin Sizes")

plt.tight_layout()
plt.savefig("bin_size_comparison.png", dpi=300, bbox_inches="tight")
plt.show()
```

**预期模式**：
- **2 µm bin**：UMI 数和基因数最低（接近单细胞或亚细胞）
- **8 µm bin**：UMI 数和基因数适中（单细胞尺度）
- **16 µm bin**：UMI 数和基因数最高（多细胞聚合）

### 敏感性分析：bin 分辨率如何影响数据特征？

```python
# 计算每种分辨率的统计量
summary = []
for bin_size, adata_tmp in adatas.items():
    summary.append({
        "bin_size": bin_size,
        "n_bins": adata_tmp.n_obs,
        "median_umi": adata_tmp.obs["total_counts"].median(),
        "median_genes": adata_tmp.obs["n_genes_by_counts"].median(),
        "median_mt": adata_tmp.obs["pct_counts_mt"].median(),
        "sparsity": 1 - (adata_tmp.X.nnz / (adata_tmp.n_obs * adata_tmp.n_vars))
    })

summary_df = pd.DataFrame(summary)
print(summary_df.to_string(index=False))
```

**预期输出**：
```
      bin_size  n_bins  median_umi  median_genes  median_mt  sparsity
 square_002um 3850124         125           98       11.2      0.985
 square_008um  245678         850          630       10.2      0.945
square_016um   62456        3200         2100        9.8      0.890
```

**关键发现**：
- **稀疏性**：随 bin 尺寸增大而降低（更多基因被检测到）
- **UMI 数**：随 bin 尺寸增大而增加（更多细胞的聚合）
- **线粒体比例**：随 bin 尺寸增大略有下降（稀释效应）

### 负对照：组织外 bin 的特征

```python
# 识别组织外 bin（假设 total_counts < 100 为组织外）
adata.obs["in_tissue"] = adata.obs["total_counts"] >= 100

# 比较组织内外的 QC 指标
tissue_stats = adata.obs.groupby("in_tissue")[
    ["total_counts", "n_genes_by_counts", "pct_counts_mt"]
].median()

print("Tissue vs Background:")
print(tissue_stats)

# 可视化组织内外分布
fig, ax = plt.subplots(1, 1, figsize=(8, 6))
sc.pl.spatial(
    adata,
    color="in_tissue",
    spot_size=1.0,
    frameon=False,
    title="Tissue Annotation",
    ax=ax,
    show=False
)
plt.savefig("tissue_annotation.png", dpi=300, bbox_inches="tight")
plt.show()
```

**预期输出**：
```
Tissue vs Background:
           total_counts  n_genes_by_counts  pct_counts_mt
in_tissue                                                 
False                45                 32           15.8
True                920                680           10.1
```

**负对照验证**：
- 组织外 bin 的 UMI 数和基因数应该显著低于组织内
- 组织外 bin 的线粒体比例可能更高（背景噪声）

## 第三部分：What's Next - 验收清单与下一步

### 验收清单

完成本文的学习后，你应该能够：

- [ ] 解释 bin 和 cell 的区别
- [ ] 说明 2 µm、8 µm、16 µm bin 的含义和适用场景
- [ ] 读取 Visium HD 的 bin 级别数据（表达矩阵 + 空间坐标）
- [ ] 计算和可视化 bin 的 QC 指标（UMI、基因数、线粒体比例）
- [ ] 比较不同分辨率 bin 的数据特征
- [ ] 识别组织内外的 bin

### 常见坑

**坑 1：内存不足**
- **现象**：读取 2 µm bin 数据时内存溢出
- **原因**：2 µm bin 数据量巨大（通常 >300 万个 bin）
- **解决**：优先使用 8 µm bin，或使用 `backed='r'` 模式读取

```python
# 使用 backed 模式（只读取需要的部分）
adata = sc.read_10x_h5(
    "filtered_feature_bc_matrix.h5",
    backed="r"
)
```

**坑 2：空间坐标单位混淆**
- **现象**：空间可视化时 bin 位置不对
- **原因**：Visium HD 的坐标是像素坐标，需要根据 `scalefactors` 转换
- **解决**：使用 `pxl_row_in_fullres` 和 `pxl_col_in_fullres`，不要自己转换

**坑 3：bin 分辨率选择不当**
- **现象**：分析结果不理想或计算太慢
- **原因**：不同分析任务对分辨率的需求不同
- **解决**：
  - 快速探索和质控：16 µm bin
  - 常规分析（空间域、SVG）：8 µm bin
  - 亚细胞分析（细胞器定位）：2 µm bin

### 边界声明

**本文能说明什么**：
- ✅ Visium HD bin 数据的文件结构和读取方法
- ✅ 不同分辨率 bin 的数据特征差异
- ✅ bin 级别数据的基本质控流程

**本文不能说明什么**：
- ❌ 如何选择最优的 bin 分辨率（取决于具体分析任务）
- ❌ 如何进行细胞分割和 cell 级别分析（后续文章）
- ❌ 如何处理 bin 数据的批次效应（需要多样本数据）

### 下一篇预告

**013: Visium HD 细胞分割：从 bin 到 cell**

在本文中，我们学习了 bin 级别数据的结构。但 Visium HD 的真正优势在于亚细胞分辨率，这需要细胞分割。下一篇文章将介绍：

- 细胞分割的原理和工具（Cellpose、Baysor）
- 如何将 bin 数据转换为 cell 数据
- cell 级别数据的质控和验证
- bin vs cell：何时使用哪种数据

---

**参考资源**：
- 10x Genomics Visium HD 官方文档
- Space Ranger 输出文件说明
- Scanpy 空间数据教程
