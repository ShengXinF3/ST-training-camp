# Scanpy 与 Squidpy 快速上手

---
title: "Scanpy 与 Squidpy 快速上手"
article_id: "003"
series: "S0"
tags: ["通用", "Scanpy", "Squidpy", "入门"]
difficulty: "入门"
created: "2026-04-08"
updated: "2026-04-09"
---

---

## 第一部分：Why & What

### 为什么需要这两个工具？

在上一篇《空间转录组数据分析完整流程》中，我们建立了从数据加载到验收的 9 步框架。但框架只是地图，真正走路还需要工具。

空间转录组 (Spatial Transcriptomics, ST) 数据分析面临三个核心挑战：

1. **数据结构复杂**：既有基因表达矩阵（细胞 × 基因），又有空间坐标（x, y），还有组织图像
2. **分析流程长**：从质控到可视化，涉及 20+ 个步骤，每步都有多个参数
3. **工具碎片化**：降维用一个包，聚类用另一个包，空间分析又是第三个包

Scanpy 和 Squidpy 的组合解决了这些问题：

- **Scanpy**：单细胞分析的瑞士军刀，处理表达矩阵的标准工具
- **Squidpy**：Scanpy 的空间扩展，专门处理空间信息和组织图像

这不是"又一个新工具"，而是社区经过 5 年沉淀的事实标准。2024 年发表的空间转录组文章中，超过 60% 使用了这个组合。

### 它们是什么？

**Scanpy** (Single-Cell Analysis in Python)：
- 核心数据结构：`AnnData` 对象，统一存储表达矩阵、细胞注释、基因注释
- 功能覆盖：质控 → 归一化 (Normalization) → 降维 → 聚类 → 差异分析
- 设计哲学：链式调用，每步结果自动存回对象

**Squidpy** (Spatial Single-Cell Analysis)：
- 继承 Scanpy 的 `AnnData` 结构，增加空间信息
- 核心功能：空间邻域 (Neighborhood) 构建、空间自相关 (Spatial Autocorrelation)、细胞通讯 (Cell-Cell Communication, CCC)
- 设计哲学：无缝衔接 Scanpy，空间分析只需加几行代码

**关键概念**：
- **AnnData 对象**：核心数据容器，包含 `.X`（表达矩阵）、`.obs`（细胞/spot 注释）、`.var`（基因注释）、`.obsm`（降维结果）、`.uns`（其他信息）
- **spot**：Visium 平台的空间单元，直径 55 µm，每个 spot 包含 1-10 个细胞
- **空间图 (Spatial Graph)**：描述 spot 之间邻接关系的网络结构

---

## 第二部分：How - 从安装到第一个分析

### 2.1 环境配置（5 分钟）

**推荐方案**：使用 conda 创建独立环境，避免依赖冲突。

```bash
# 创建环境
conda create -n st-analysis python=3.10 -y
conda activate st-analysis

# 安装核心包
pip install scanpy squidpy

# 验证安装
python -c "import scanpy as sc; import squidpy as sq; print(f'Scanpy {sc.__version__}, Squidpy {sq.__version__}')"
```

**输出解读**：显示已安装的 Scanpy 和 Squidpy 版本号。只要能成功输出版本号（通常 Scanpy 1.9+ 和 Squidpy 1.2+），说明安装成功。如果遇到 `ImportError: libgeos_c.so.1`，需要安装 geos：
```bash
conda install -c conda-forge geos
```

### 2.2 数据加载（理解 AnnData 结构）

使用 Squidpy 内置的示例数据集（小鼠脑切片，Visium 平台）：

```python
import scanpy as sc
import squidpy as sq
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 设置绘图参数
sc.set_figure_params(dpi=100, frameon=False)

# 加载数据
adata = sq.datasets.visium_hne_adata()

# 查看数据结构
print(adata)
```

**输出解读**：
- `n_obs × n_vars`：显示 (spot 数量 × 基因数量)，Visium 数据通常有 2000-5000 个 spot，10000-30000 个基因
- `obs`：每个 spot 的注释信息，包括是否在组织内 (`in_tissue`)、阵列坐标 (`array_row`, `array_col`)
- `var`：基因注释信息，包括基因 ID、特征类型、参考基因组
- `obsm['spatial']`：空间坐标 (x, y)，用于绘制空间图
- `uns['spatial']`：组织图像和缩放因子，用于叠加显示

**检查数据完整性**：

```python
# 检查空间坐标
print(f"Spatial coordinates shape: {adata.obsm['spatial'].shape}")
print(f"Coordinates range: x=[{adata.obsm['spatial'][:, 0].min():.0f}, {adata.obsm['spatial'][:, 0].max():.0f}], "
      f"y=[{adata.obsm['spatial'][:, 1].min():.0f}, {adata.obsm['spatial'][:, 1].max():.0f}]")

# 检查组织覆盖率
in_tissue_ratio = adata.obs['in_tissue'].sum() / len(adata)
print(f"In-tissue spots: {in_tissue_ratio:.1%}")
```

**输出解读**：
- `Spatial coordinates shape`：应该是 (spot 数量, 2)，表示每个 spot 有 x 和 y 坐标
- `Coordinates range`：坐标范围取决于图像分辨率，通常在几千像素范围内
- `In-tissue spots`：组织内 spot 的比例，通常在 50-80% 之间，过低可能提示组织覆盖不足

**说明**：这个数据集已经过预处理，实际项目中需要从 Space Ranger 输出加载原始数据。

### 2.3 质控（QC）- 第一个证据链

质控的目标：过滤低质量 spot，避免技术噪声干扰生物信号。

**步骤 1：计算 QC 指标**

```python
# 计算 QC 指标
sc.pp.calculate_qc_metrics(adata, inplace=True)

# 添加线粒体基因比例
adata.var['mt'] = adata.var_names.str.startswith('mt-')
sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], inplace=True)

# 查看数据分布（用于确定阈值）
print(f"Total spots: {adata.n_obs}")
print(f"\nQC metrics distribution:")
print(f"  total_counts: min={adata.obs['total_counts'].min():.0f}, "
      f"median={adata.obs['total_counts'].median():.0f}, "
      f"max={adata.obs['total_counts'].max():.0f}")
print(f"  n_genes_by_counts: min={adata.obs['n_genes_by_counts'].min():.0f}, "
      f"median={adata.obs['n_genes_by_counts'].median():.0f}, "
      f"max={adata.obs['n_genes_by_counts'].max():.0f}")
print(f"  pct_counts_mt: min={adata.obs['pct_counts_mt'].min():.2f}%, "
      f"median={adata.obs['pct_counts_mt'].median():.2f}%, "
      f"max={adata.obs['pct_counts_mt'].max():.2f}%")
```

**输出解读**：
- `total_counts`：每个 spot 的总 UMI 数，反映测序深度。Visium 数据中位数通常在 3000-8000 之间，极低值（< 500）可能是组织外或技术失败，极高值（> 20000）可能是双联体
- `n_genes_by_counts`：检测到的基因数，反映数据丰富度。通常与 total_counts 正相关，中位数在 2000-4000 之间
- `pct_counts_mt`：线粒体基因比例，高值提示细胞损伤。正常范围通常 < 10%，超过 20% 提示细胞破裂或凋亡

**步骤 2：可视化 QC 指标分布**

```python
# 小提琴图：查看整体分布
sc.pl.violin(adata, ['total_counts', 'n_genes_by_counts', 'pct_counts_mt'],
             jitter=0.4, multi_panel=True)
```

**图表解读**：
- `total_counts`：每个 spot 的总 UMI 数，反映测序深度
  - 极低值（< 500）：可能是组织外或技术失败
  - 极高值（> 20000）：可能是双联体或技术伪影
- `n_genes_by_counts`：检测到的基因数，反映数据丰富度
  - 与 total_counts 正相关，但低基因数加高 UMI 提示异常
- `pct_counts_mt`：线粒体基因比例，高值提示细胞损伤或低质量
  - 正常范围：< 10%
  - 高值（> 20%）：细胞破裂或凋亡

**步骤 3：根据分布设定过滤阈值**

```python
# 根据上面的分布，设定阈值
min_counts = 500      # 过滤极低 UMI 的 spot
max_counts = 20000    # 过滤极高 UMI 的 spot（可能是双联体）
max_mt = 20           # 过滤高线粒体比例的 spot

# 过滤前统计
print(f"\nBefore filtering: {adata.n_obs} spots")

# 执行过滤
sc.pp.filter_cells(adata, min_counts=min_counts)
sc.pp.filter_cells(adata, max_counts=max_counts)
adata = adata[adata.obs['pct_counts_mt'] < max_mt, :]

# 过滤后统计
print(f"After filtering: {adata.n_obs} spots")
print(f"Removed: {3353 - adata.n_obs} spots ({(3353 - adata.n_obs)/3353:.1%})")
```

**输出解读**：显示过滤前后的 spot 数量和移除比例。通常移除 10-30% 的 spot 是合理的，如果移除比例过高（> 50%），需要重新评估阈值设置。

**检查过滤是否合理**：

```python
# 在空间上可视化过滤结果
# 保存过滤后的 spot 索引
filtered_spots = adata.obs_names

# 重新加载原始数据用于对比
adata_original = sq.datasets.visium_hne_adata()
sc.pp.calculate_qc_metrics(adata_original, inplace=True)
adata_original.var['mt'] = adata_original.var_names.str.startswith('mt-')
sc.pp.calculate_qc_metrics(adata_original, qc_vars=['mt'], inplace=True)

# 标记过滤状态
adata_original.obs['passed_qc'] = adata_original.obs_names.isin(filtered_spots).astype(str)

# 可视化
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 左图：过滤前的 total_counts 分布
sq.pl.spatial_scatter(adata_original, color='total_counts', ax=axes[0], 
                      title='Before QC', size=1.5)

# 右图：标记哪些 spot 被过滤
sq.pl.spatial_scatter(adata_original, color='passed_qc', ax=axes[1],
                      title='QC Result (red=passed)', size=1.5)

plt.tight_layout()
plt.show()
```

**关键观察**：
- 被过滤的 spot 主要分布在组织边缘或空白区域
- 如果被过滤的 spot 在组织核心区域，需要重新评估阈值

**说明**：
- 这些阈值是基于小鼠脑组织的经验值
- 不同组织类型需要调整：脂肪组织 UMI 数通常更低，肿瘤组织线粒体比例可能更高
- 过滤过严会丢失真实信号，过滤过松会引入噪声，需要在下游分析中验证

### 2.4 归一化与降维（标准流程）

```python
# 归一化：消除测序深度差异
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# 识别高变基因
sc.pp.highly_variable_genes(adata, n_top_genes=2000)

# 保存原始数据
adata.raw = adata

# 只保留高变基因用于降维
adata = adata[:, adata.var['highly_variable']]

# 标准化：z-score 转换
sc.pp.scale(adata, max_value=10)

# PCA 降维
sc.tpp.pca(adata, n_comps=50)

# 计算邻域图
sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40)

# UMAP 可视化
sc.tl.umap(adata)
```

**检查降维稳健性**：

```python
# 绘制 PCA 方差解释图
sc.pl.pca_variance_ratio(adata, log=True, n_pcs=50)
```

**解读**：前 40 个 PC 应该解释大部分方差（通常 > 80%）。如果曲线在前 20 个 PC 就趋于平缓，说明数据维度较低。

### 2.5 聚类（无监督识别细胞类型）

```python
# Leiden 聚类
sc.tl.leiden(adata, resolution=0.5)

# 可视化：UMAP 空间
sc.pl.umap(adata, color='leiden', legend_loc='on data')


# 清除所有与 leiden 相关的颜色配置
for key in list(adata.uns.keys()):
    if 'leiden_colors' in key:
        adata.uns.pop(key)

# 重新设置分类
adata.obs['leiden'] = adata.obs['leiden'].astype('category')

# 可视化：物理空间
sq.pl.spatial_scatter(adata, color='leiden', size=1.5)
```

**测试不同 resolution 参数**：

```python
# 测试多个 resolution
for res in [0.3, 0.5, 0.8, 1.0]:
    sc.tl.leiden(adata, resolution=res, key_added=f'leiden_r{res}')

# 对比可视化
sc.pl.umap(adata, color=['leiden_r0.3', 'leiden_r0.5', 'leiden_r0.8', 'leiden_r1.0'],
           ncols=2)
```

**判断标准**：
- resolution 太低：聚类过粗，丢失细节
- resolution 太高：过度分割，生物学意义不明确
- 推荐：选择能区分主要组织结构的最小 resolution

### 2.6 空间分析（Squidpy 的核心功能）

**构建空间邻域图**：

```python
# 构建空间图（基于物理距离）
sq.gr.spatial_neighbors(adata, coord_type='generic', delaunay=True)

# 检查邻域统计
print(f"Average neighbors per spot: {adata.obsp['spatial_connectivities'].sum(axis=1).mean():.1f}")
```

**输出解读**：显示每个 spot 平均有多少个邻居。Visium 数据通常每个 spot 有 4-8 个邻居，取决于组织形状和边缘效应。

**空间自相关分析**：识别空间可变基因 (Spatially Variable Genes, SVG)

```python
# 计算 Moran's I（空间自相关指标）
sq.gr.spatial_autocorr(
    adata,
    mode='moran',
    n_perms=100,  # 置换检验次数
    n_jobs=4
)

# 查看结果
print(adata.uns['moranI'].head(10))
```

**输出解读**：
- `I`：Moran's I 值，范围 [-1, 1]，大于 0 表示正相关（相邻 spot 表达相似）
- `pval_norm`：显著性 p 值，小于 0.05 表示空间模式显著
- 高 I 值加低 p 值表示强空间模式，这些基因在组织中呈现明显的区域化表达

**可视化 SVG**：

```python
# 选择 top 4 个 SVG
top_svg = adata.uns['moranI'].head(4).index

# 在空间上可视化
sq.pl.spatial_scatter(adata, color=top_svg, ncols=2, size=1.5, cmap='viridis')
```

**验证空间模式**：

```python
# 随机选择低 Moran's I 的基因
random_genes = adata.uns['moranI'].tail(4).index

# 对比可视化
sq.pl.spatial_scatter(adata, color=random_genes, ncols=2, size=1.5, cmap='viridis')
```

**预期结果**：随机基因应该呈现"盐和胡椒"分布，没有明显空间模式。

### 2.7 邻域富集分析（Niche Identification）

识别哪些细胞类型倾向于共定位：

```python
# 计算邻域富集
sq.gr.nhood_enrichment(adata, cluster_key='leiden')

# 可视化
sq.pl.nhood_enrichment(adata, cluster_key='leiden', method='average', cmap='coolwarm')
```

**解读**：
- 热图对角线：同类型 spot 的邻域富集（通常为正值）
- 非对角线：不同类型间的共定位模式
- 显著正值：两种类型倾向于相邻（可能存在细胞通讯）
- 显著负值：两种类型倾向于分离

**说明**：
- 能说明：哪些细胞类型在空间上共定位
- 不能说明：共定位的因果关系（需要配体-受体分析）

---

## 第三部分：What's Next

### 验收清单（完成这 5 项才算掌握）

- [ ] **数据加载**：能够加载 Space Ranger 输出，理解 AnnData 结构
- [ ] **质控**：能够根据 QC 指标设定合理阈值，绘制诊断图
- [ ] **降维聚类**：能够调整 resolution 参数，在 UMAP 和空间上验证聚类
- [ ] **空间分析**：能够识别 SVG，解读 Moran's I 结果
- [ ] **证据链**：每个分析步骤都包含诊断图、对照或敏感性分析

### 核心要点回顾

Scanpy 和 Squidpy 不是"又一个新工具"，而是空间转录组分析的事实标准。掌握这两个工具的关键不在于记住所有函数，而在于理解三个核心概念：

1. **AnnData 是一切的基础**：表达矩阵、空间坐标、细胞注释、降维结果都存储在同一个对象中。理解 `.X`、`.obs`、`.var`、`.obsm`、`.uns` 的作用，就能理解整个分析流程的数据流动。

2. **质控决定分析质量**：过滤阈值不是固定的数字，而是基于数据分布的判断。通过小提琴图查看 `total_counts`、`n_genes_by_counts`、`pct_counts_mt` 的分布，在空间上可视化过滤结果，确保被过滤的 spot 主要在组织边缘而非核心区域。不同组织类型需要调整阈值：脂肪组织 UMI 数通常更低，肿瘤组织线粒体比例可能更高。

3. **空间分析的核心是邻域关系**：Squidpy 通过构建空间图（spatial graph）描述 spot 之间的邻接关系，在此基础上进行空间自相关分析（识别 SVG）和邻域富集分析（识别共定位模式）。Moran's I 值大于 0 且 p 值显著表示基因呈现区域化表达，邻域富集热图的非对角线元素揭示不同细胞类型的空间共定位模式。

4. **证据链贯穿每个步骤**：不要盲目相信默认参数。PCA 方差解释图验证降维是否充分，测试多个 resolution 参数选择合适的聚类粒度，对比 SVG 和随机基因的空间分布验证空间模式的真实性。每个分析步骤都需要通过可视化、对照或参数敏感性测试来验证结果的稳健性。

5. **边界意识同样重要**：邻域富集分析能说明哪些细胞类型在空间上共定位，但不能说明共定位的因果关系，这需要配体-受体分析。空间自相关分析识别的是表达模式的空间聚集性，但高 Moran's I 值不等于生物学功能的空间依赖性。

### 进阶方向（下一步学什么）

1. **细胞通讯分析**：使用 `sq.gr.ligrec()` 识别配体-受体对
2. **空间域识别**：使用 BayesSpace、STAGATE 等工具
3. **多切片整合**：处理批次效应 (Batch Effect)，整合多个样本
4. **成像型数据**：处理 MERFISH、Xenium 等亚细胞分辨率数据

---

## 参考资源

**官方文档**：
- Scanpy 和 Squidpy 官方文档提供了完整的 API 参考和教程

**关键文献**：
- Wolf et al. (2018). SCANPY: large-scale single-cell gene expression data analysis. *Genome Biology*. - 引入 AnnData 结构和 Scanpy 工作流
- Palla et al. (2022). Squidpy: a scalable framework for spatial omics analysis. *Nature Methods*. - Squidpy 原始论文，介绍空间分析方法

**数据集**：
- 10x Genomics Visium 公开数据集可通过官方网站获取
- Squidpy 内置数据集: `sq.datasets.visium_*`

---

**写作日期**: 2026-04-08  
**版本**: v1.0  
**作者**: BioF3 空间转录组训练营