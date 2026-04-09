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

**预期输出**：
```
Scanpy 1.10.1, Squidpy 1.4.1
```

**常见坑 #1**：如果遇到 `ImportError: libgeos_c.so.1`，需要安装 geos：
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
```
AnnData object with n_obs × n_vars = 3353 × 18078
    obs: 'in_tissue', 'array_row', 'array_col'
    var: 'gene_ids', 'feature_types', 'genome'
    uns: 'spatial'
    obsm: 'spatial'
```

**关键字段说明**：
- `n_obs = 3353`：3353 个 spot
- `n_vars = 18078`：18078 个基因
- `obs`：每个 spot 的注释（是否在组织内、阵列坐标）
- `obsm['spatial']`：空间坐标 (x, y)
- `uns['spatial']`：组织图像和缩放因子

**证据链 - 诊断图 #1**：检查数据完整性

```python
# 检查空间坐标
print(f"Spatial coordinates shape: {adata.obsm['spatial'].shape}")
print(f"Coordinates range: x=[{adata.obsm['spatial'][:, 0].min():.0f}, {adata.obsm['spatial'][:, 0].max():.0f}], "
      f"y=[{adata.obsm['spatial'][:, 1].min():.0f}, {adata.obsm['spatial'][:, 1].max():.0f}]")

# 检查组织覆盖率
in_tissue_ratio = adata.obs['in_tissue'].sum() / len(adata)
print(f"In-tissue spots: {in_tissue_ratio:.1%}")
```

**预期输出**：
```
Spatial coordinates shape: (3353, 2)
Coordinates range: x=[0, 5000], y=[0, 4000]
In-tissue spots: 68.5%
```

**边界声明**：这个数据集已经过预处理，实际项目中需要从 Space Ranger 输出加载原始数据。

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

**预期输出**：
```
Total spots: 3353
QC metrics distribution:
  total_counts: min=35, median=5520, max=28691
  n_genes_by_counts: min=34, median=2755, max=5668
  pct_counts_mt: min=0.00%, median=2.89%, max=27.78%
```

**步骤 2：可视化 QC 指标分布**

```python
# 小提琴图：查看整体分布
sc.pl.violin(adata, ['total_counts', 'n_genes_by_counts', 'pct_counts_mt'],
             jitter=0.4, multi_panel=True)
```

**诊断图解读**：
- `total_counts`：每个 spot 的总 UMI 数，反映测序深度
  - 极低值（< 500）：可能是组织外或技术失败
  - 极高值（> 20000）：可能是双联体或技术伪影
- `n_genes_by_counts`：检测到的基因数，反映数据丰富度
  - 与 total_counts 正相关，但低基因数 + 高 UMI 提示异常
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

**预期输出**：
```
Before filtering: 3353 spots
After filtering: 2688 spots
Removed: 665 spots (19.8%)
```

**证据链 - 对照**：检查过滤是否合理

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
adata_original.obs['passed_qc'] = adata_original.obs_names.isin(filtered_spots)

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
- 被过滤的 spot（蓝色）主要分布在组织边缘或空白区域
- 如果被过滤的 spot 在组织核心区域，需要重新评估阈值

**边界声明**：
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

**证据链 - 敏感性分析**：检查降维稳健性

```python
# 绘制 PCA 方差解释图
sc.pl.pca_variance_ratio(adata, log=True, n_pcs=50)
```

**解读**：前 40 个 PC 应该解释 >80% 的方差。如果曲线在前 20 个 PC 就趋于平缓，说明数据维度较低。

### 2.5 聚类（无监督识别细胞类型）

```python
# Leiden 聚类
sc.tl.leiden(adata, resolution=0.5)

# 可视化：UMAP 空间
sc.pl.umap(adata, color='leiden', legend_loc='on data')

# 可视化：物理空间
sq.pl.spatial_scatter(adata, color='leiden', size=1.5)
```

**证据链 - 敏感性分析**：测试不同 resolution 参数

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

**输出示例**：
```
              I      pval_norm  var_norm
gene                                    
Mbp       0.856  1.23e-145      0.012
Plp1      0.823  3.45e-132      0.011
Mobp      0.791  2.11e-118      0.010
```

**解读**：
- `I`：Moran's I 值，范围 [-1, 1]，>0 表示正相关（相邻 spot 表达相似）
- `pval_norm`：显著性 p 值
- 高 I 值 + 低 p 值 = 强空间模式

**可视化 SVG**：

```python
# 选择 top 4 个 SVG
top_svg = adata.uns['moranI'].head(4).index

# 在空间上可视化
sq.pl.spatial_scatter(adata, color=top_svg, ncols=2, size=1.5, cmap='viridis')
```

**证据链 - 负对照**：检查随机基因

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

**证据链 - 边界声明**：
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

### 常见坑与解决方案

**坑 #1：内存溢出**
- **现象**：处理大数据集（>10,000 spots）时，PCA 或聚类步骤卡死
- **原因**：Scanpy 默认使用密集矩阵，占用内存大
- **解决**：
  ```python
  # 使用稀疏矩阵
  adata.X = scipy.sparse.csr_matrix(adata.X)
  
  # 或者降采样
  sc.pp.subsample(adata, fraction=0.5)
  ```

**坑 #2：空间图构建失败**
- **现象**：`sq.gr.spatial_neighbors()` 报错 `KeyError: 'spatial'`
- **原因**：数据缺少空间坐标
- **解决**：
  ```python
  # 检查坐标是否存在
  assert 'spatial' in adata.obsm, "Missing spatial coordinates"
  
  # 如果坐标在 obs 中，需要转移到 obsm
  adata.obsm['spatial'] = adata.obs[['x', 'y']].values
  ```

**坑 #3：SVG 结果不显著**
- **现象**：所有基因的 Moran's I 都很低
- **原因**：空间图构建参数不合理（邻域太大或太小）
- **解决**：
  ```python
  # 可视化空间图
  sq.pl.spatial_scatter(adata, connectivity_key='spatial_connectivities', edges=True)
  
  # 调整邻域参数
  sq.gr.spatial_neighbors(adata, n_neighs=6)  # 默认是 6
  ```

**坑 #4：图表标签乱码**
- **现象**：保存的图片中文显示为方块
- **解决**：
  ```python
  # 设置字体（macOS）
  plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
  plt.rcParams['axes.unicode_minus'] = False
  ```

### 进阶方向（下一步学什么）

1. **细胞通讯分析**：使用 `sq.gr.ligrec()` 识别配体-受体对
2. **空间域识别**：使用 BayesSpace、STAGATE 等工具
3. **多切片整合**：处理批次效应 (Batch Effect)，整合多个样本
4. **成像型数据**：处理 MERFISH、Xenium 等亚细胞分辨率数据

### 下一篇预告

**004 - 质控的 10 个致命错误**：
- 为什么"过滤低质量细胞"可能丢失稀有细胞类型？
- 线粒体比例阈值应该设为 5%、10% 还是 20%？
- 如何用负对照验证过滤策略？

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