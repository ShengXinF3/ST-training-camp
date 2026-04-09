---
title: "空间转录组数据分析完整流程"
article_id: "002"
series: "S0"
tags: ["通用", "Scanpy", "Squidpy", "入门"]
difficulty: "入门"
created: "2026-04-08"
updated: "2026-04-09"
---

# 空间转录组数据分析完整流程

## 第一部分：Why & What - 为什么需要标准流程？

### 你遇到过这些问题吗？

拿到一份空间转录组数据，打开文件夹看到 `filtered_feature_bc_matrix.h5`、`spatial` 文件夹、组织切片图像，然后呢？

- 不知道从哪里开始
- 不确定质控标准是否合理
- 分析到一半发现结果不可信
- 无法判断分析是否完成

这些问题的根源是：**缺少一个可验证的分析框架**。

### 什么是完整的分析流程？

空间转录组 (Spatial Transcriptomics, ST) 数据分析不是线性的"跑代码"过程，而是一个**证据驱动的决策链**。从数据加载到生物学解释，每一步都需要回答三个问题：

1. **输入是否可信？** 通过可视化图表检查数据质量和分布
2. **方法是否稳健？** 通过对照实验和参数测试验证结果的可靠性
3. **结论的边界在哪？** 明确说明分析能得出什么结论、不能得出什么结论

这种思维方式贯穿整个分析流程：在质量控制阶段，我们通过查看数据分布来判断是否需要过滤；在空间分析阶段，我们通过随机化检验来排除偶然性；在得出结论时，我们明确说明适用范围和局限性。

### 本文的目标

通过一个 Visium 数据集，演示从原始数据到可发表图表的完整流程，重点展示：
- 每一步的决策依据（不是"应该这样做"，而是"为什么这样做"）
- 如何构建可信的分析证据
- 常见陷阱的识别

---

## 第二部分：How - 完整流程实战

### 环境准备

```python
import scanpy as sc
import squidpy as sq
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 设置随机种子（可复现）
np.random.seed(42)

# 配置
sc.settings.verbosity = 3
sc.settings.set_figure_params(dpi=80, facecolor='white')
```

### Step 1: 数据加载与格式验证

**使用官方示例数据**（推荐用于学习）：

```python
# 加载 Squidpy 内置的 Visium 数据集（小鼠脑组织 H&E 染色）
adata = sq.datasets.visium_hne_adata()

# 验证数据结构
print(f"Shape: {adata.shape}")  # (spots, genes)
print(f"Spatial keys: {list(adata.obsm.keys())}")  # 应包含 'spatial'
print(f"Image keys: {list(adata.uns['spatial'].keys())}")  # 应包含样本名
```

**输出解读**：
- `Shape`: 显示 (spot数量, 基因数量)，Visium 数据通常有 2000-5000 个 spot，10000-30000 个基因
- `Spatial keys`: 应该包含 'spatial'，存储每个 spot 的 (x, y) 坐标
- `Image keys`: 包含样本名称，用于关联组织图像

**加载自己的数据**：

如果你有自己的 Visium 数据（Space Ranger 输出），数据结构通常如下：

```
your_data/
├── filtered_feature_bc_matrix.h5  # 表达矩阵
└── spatial/
    ├── tissue_positions_list.csv  # spot 坐标
    ├── scalefactors_json.json     # 缩放因子
    └── tissue_hires_image.png     # 高分辨率组织图像
```

加载方法：

```python
# 加载自己的 Visium 数据
adata = sc.read_visium(
    path='path/to/your_data',  # 包含 spatial/ 文件夹的目录
    count_file='filtered_feature_bc_matrix.h5'
)

# 如果数据已经是 h5ad 格式
adata = sc.read_h5ad('your_data.h5ad')
```

**质量检查 1：数据完整性**

```python
# 先计算基本的 QC 指标（如果数据还没有）
sc.pp.calculate_qc_metrics(adata, inplace=True)

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# 1. Spot 空间分布
sq.pl.spatial_scatter(
    adata, color='in_tissue', 
    title='Spot Distribution',
    ax=axes[0]
)

# 2. UMI 计数分布
axes[1].hist(adata.obs['total_counts'], bins=50, edgecolor='black')
axes[1].set_xlabel('Total UMI Counts')
axes[1].set_ylabel('Number of Spots')
axes[1].set_title('UMI Count Distribution')

# 3. 基因检测分布
axes[2].hist(adata.obs['n_genes_by_counts'], bins=50, edgecolor='black')
axes[2].set_xlabel('Number of Genes Detected')
axes[2].set_ylabel('Number of Spots')
axes[2].set_title('Gene Detection Distribution')

plt.tight_layout()
plt.show()
```

**预期结果**：
- 左图：spot 在组织上的分布，不同颜色区分组织内外
- 中图：UMI 计数分布，中位数通常在 5000-10000 之间，分布应该相对集中
- 右图：检测到的基因数分布，中位数通常在 2000-4000 之间，与 UMI 数正相关

**这一步能说明什么？**
- 数据是否完整加载、spot 是否覆盖组织区域
- 但不能说明数据质量是否合格，需要进一步质控

### Step 2: 质量控制 - 构建诊断体系

```python
# 计算 QC 指标
adata.var['mt'] = adata.var_names.str.startswith('MT-')  # 线粒体基因
sc.pp.calculate_qc_metrics(
    adata, qc_vars=['mt'], 
    percent_top=None, log1p=False, 
    inplace=True
)
```

**质量检查 2：质控指标的空间分布**

```python
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# 空间分布图
metrics = ['total_counts', 'n_genes_by_counts', 'pct_counts_mt']
titles = ['Total UMI Counts', 'Number of Genes', 'Mitochondrial Gene %']

for i, (metric, title) in enumerate(zip(metrics, titles)):
    sq.pl.spatial_scatter(
        adata, color=metric, 
        title=f'{title} (Spatial)',
        ax=axes[0, i], cmap='viridis'
    )
    
    # 对应的分布图
    axes[1, i].hist(adata.obs[metric], bins=50, edgecolor='black')
    axes[1, i].set_xlabel(title)
    axes[1, i].set_ylabel('Number of Spots')
    axes[1, i].axvline(adata.obs[metric].median(), 
                       color='red', linestyle='--', 
                       label=f'Median: {adata.obs[metric].median():.1f}')
    axes[1, i].legend()

plt.tight_layout()
plt.show()
```

**对照验证 1：负对照区域检查**

```python
# 检查组织外 spot 的质量（预期应该很低）
tissue_mask = adata.obs['in_tissue'] == 1
out_tissue_mask = adata.obs['in_tissue'] == 0

print("Quality Metrics Comparison:")
print(f"In-tissue spots: {tissue_mask.sum()}")
print(f"Out-tissue spots: {out_tissue_mask.sum()}")
print(f"\nMedian UMI counts:")
print(f"  In-tissue: {adata.obs.loc[tissue_mask, 'total_counts'].median():.0f}")
print(f"  Out-tissue: {adata.obs.loc[out_tissue_mask, 'total_counts'].median():.0f}")
```

**稳健性测试 1：质控阈值的影响**

```python
# 测试不同阈值的影响
thresholds = {
    'loose': {'min_counts': 500, 'min_genes': 200, 'max_mt': 25},
    'medium': {'min_counts': 1000, 'min_genes': 500, 'max_mt': 20},
    'strict': {'min_counts': 2000, 'min_genes': 1000, 'max_mt': 15}
}

for name, params in thresholds.items():
    mask = (
        (adata.obs['total_counts'] >= params['min_counts']) &
        (adata.obs['n_genes_by_counts'] >= params['min_genes']) &
        (adata.obs['pct_counts_mt'] <= params['max_mt'])
    )
    print(f"{name.capitalize()} threshold: {mask.sum()} spots retained "
          f"({mask.sum()/len(adata)*100:.1f}%)")
```

**决策点**：这里选择 medium 阈值（通常保留 85-95% 的组织内 spot），但具体阈值需要根据数据分布和组织类型调整。

```python
# 应用质控
sc.pp.filter_cells(adata, min_counts=1000)
sc.pp.filter_cells(adata, min_genes=500)
adata = adata[adata.obs['pct_counts_mt'] < 20, :].copy()

# 过滤低表达基因
sc.pp.filter_genes(adata, min_cells=10)

print(f"After QC: {adata.shape}")
```

**这一步能说明什么？**
- 当前数据集的质量分布、异常 spot 的比例
- 但不能说明生物学差异，需要归一化后才能比较

### Step 3: 归一化 - 消除技术变异

```python
# 保存原始计数
adata.layers['counts'] = adata.X.copy()

# 归一化（Normalization）：消除技术变异，使样本间可比较
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# 保存归一化后的数据
adata.layers['log1p_norm'] = adata.X.copy()
```

**质量检查 3：归一化效果**

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# 归一化前后的 UMI 分布
axes[0].hist(np.array(adata.layers['counts'].sum(axis=1)).flatten(), 
             bins=50, alpha=0.7, label='Before', edgecolor='black')
axes[0].set_xlabel('Total UMI Counts')
axes[0].set_ylabel('Number of Spots')
axes[0].set_title('Before Normalization')
axes[0].set_yscale('log')

axes[1].hist(np.array(adata.X.sum(axis=1)).flatten(), 
             bins=50, alpha=0.7, label='After', color='orange', edgecolor='black')
axes[1].set_xlabel('Total Normalized Counts')
axes[1].set_ylabel('Number of Spots')
axes[1].set_title('After Normalization')
axes[1].set_yscale('log')

plt.tight_layout()
plt.show()
```

### Step 4: 高变基因选择与降维

```python
# 识别高变基因
sc.pp.highly_variable_genes(
    adata, n_top_genes=2000, 
    flavor='seurat_v3', 
    layer='counts'
)

print(f"Highly variable genes: {adata.var['highly_variable'].sum()}")

# PCA 降维
sc.tl.pca(adata, n_comps=50, use_highly_variable=True)

# 邻域图构建
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=30)

# UMAP 可视化
sc.tl.umap(adata)
```

**质量检查 4：降维质量**

```python
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# PCA 方差解释（手动绘制）
variance_ratio = adata.uns['pca']['variance_ratio']
axes[0].plot(range(1, len(variance_ratio) + 1), variance_ratio, 'o-')
axes[0].set_xlabel('PC')
axes[0].set_ylabel('Variance Ratio')
axes[0].set_title('PCA Variance Explained')
axes[0].set_yscale('log')

# UMAP 可视化
sc.pl.umap(adata, color='total_counts', ax=axes[1], show=False, cmap='viridis')
axes[1].set_title('UMAP: Total Counts')

sc.pl.umap(adata, color='n_genes_by_counts', ax=axes[2], show=False, cmap='viridis')
axes[2].set_title('UMAP: Number of Genes')

plt.tight_layout()
plt.show()
```

**对照验证 2：随机化检验**

```python
# 随机打乱空间坐标，检查是否仍能检测到空间模式
adata_shuffled = adata.copy()
adata_shuffled.obsm['spatial'] = np.random.permutation(adata.obsm['spatial'])

# 如果随机化后仍有强空间模式，说明可能存在批次效应 (Batch Effect)
```

### Step 5: 空间聚类 - 识别空间域

```python
# Leiden 聚类
sc.tl.leiden(adata, resolution=0.5, key_added='clusters')

# 空间域 (Spatial Domain) 可视化
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

sc.pl.umap(adata, color='clusters', ax=axes[0], show=False, legend_loc='on data')
axes[0].set_title('Clusters (UMAP)')

sq.pl.spatial_scatter(
    adata, color='clusters', 
    title='Spatial Domains',
    ax=axes[1]
)

plt.tight_layout()
plt.show()
```

**稳健性测试 2：聚类分辨率的影响**

```python
# 测试不同分辨率
resolutions = [0.3, 0.5, 0.8, 1.0]

fig, axes = plt.subplots(1, len(resolutions), figsize=(20, 4))

for i, res in enumerate(resolutions):
    sc.tl.leiden(adata, resolution=res, key_added=f'leiden_{res}')
    n_clusters = adata.obs[f'leiden_{res}'].nunique()
    
    sq.pl.spatial_scatter(
        adata, color=f'leiden_{res}',
        title=f'Resolution {res} ({n_clusters} clusters)',
        ax=axes[i]
    )

plt.tight_layout()
plt.show()
```

**决策点**：建议选择能够区分主要组织结构的分辨率（通常在 0.5-0.8 之间），但具体数值需要结合组织学知识判断。

### Step 6: 差异表达分析

```python
# 计算每个空间域的标志基因
sc.tl.rank_genes_groups(
    adata, groupby='clusters', 
    method='wilcoxon', 
    key_added='rank_genes_clusters'
)

# 可视化 top 标志基因
sc.pl.rank_genes_groups_heatmap(
    adata, n_genes=5, 
    groupby='clusters',
    show_gene_labels=True,
    show=True
)
```

**质量检查 5：标志基因的空间分布**

```python
# 选择 top 3 标志基因
top_genes = []
for cluster in adata.obs['clusters'].cat.categories:
    genes = sc.get.rank_genes_groups_df(
        adata, group=cluster, key='rank_genes_clusters'
    ).head(1)['names'].values
    top_genes.extend(genes)

# 空间表达图
sq.pl.spatial_scatter(
    adata, color=top_genes[:6], 
    ncols=3, cmap='viridis'
)
```

### Step 7: 空间可变基因检测

```python
# 空间可变基因 (Spatially Variable Genes, SVG)：
# 表达量在空间上呈现非随机分布模式的基因

# 构建空间邻域 (Neighborhood) 图
sq.gr.spatial_neighbors(adata, coord_type='generic', n_neighs=6)

# 检测 SVG（使用 Moran's I 统计量）
sq.gr.spatial_autocorr(
    adata,
    mode='moran',
    n_perms=100,  # 排列检验次数
    n_jobs=4
)

# 提取显著的 SVG
svg_results = adata.uns['moranI'].copy()
svg_results = svg_results[svg_results['pval_norm_fdr_bh'] < 0.05]
svg_results = svg_results.sort_values('I', ascending=False)

print(f"Significant SVGs: {len(svg_results)}")
print(svg_results.head(10))
```

**对照验证 3：随机基因的空间自相关**

```python
# 生成随机表达矩阵作为负对照
adata_random = adata.copy()
adata_random.X = np.random.rand(*adata.X.shape)

sq.gr.spatial_autocorr(
    adata_random,
    mode='moran',
    n_perms=100,
    n_jobs=4
)

# 比较真实数据与随机数据的 Moran's I 分布
fig, ax = plt.subplots(figsize=(8, 5))

ax.hist(adata.uns['moranI']['I'], bins=50, alpha=0.7, 
        label='Real Data', edgecolor='black')
ax.hist(adata_random.uns['moranI']['I'], bins=50, alpha=0.7, 
        label='Random Data', edgecolor='black')
ax.set_xlabel("Moran's I")
ax.set_ylabel('Number of Genes')
ax.set_title("Spatial Autocorrelation: Real vs Random")
ax.legend()
plt.show()
```

**质量检查 6：Top SVG 的空间模式**

```python
top_svgs = svg_results.head(6).index.tolist()

sq.pl.spatial_scatter(
    adata, color=top_svgs,
    ncols=3, cmap='viridis',
    title=[f'{gene} (I={svg_results.loc[gene, "I"]:.2f})' 
           for gene in top_svgs]
)
```

**这一步能说明什么？**
- 哪些基因在空间上有非随机分布、空间自相关 (Spatial Autocorrelation) 的强度
- 但不能说明空间模式的生物学机制，需要结合先验知识

### Step 8: 空间邻域富集分析

```python
# 计算每个 spot 的邻域 (Neighborhood) 组成
sq.gr.nhood_enrichment(adata, cluster_key='clusters')

# 可视化邻域富集矩阵
sq.pl.nhood_enrichment(
    adata, cluster_key='clusters',
    method='average', cmap='coolwarm',
    title='Neighborhood Enrichment',
    show=True
)
```

**解读**：
- 对角线高值：同类型 spot 倾向于聚集
- 非对角线高值：两种类型 spot 倾向于相邻（可能存在细胞通讯 (Cell-Cell Communication, CCC)）

### Step 9: 保存结果

```python
# 保存处理后的数据
adata.write('processed_visium_data.h5ad')

# 导出关键结果
results = {
    'svg_genes': svg_results,
    'cluster_markers': sc.get.rank_genes_groups_df(adata, group=None),
    'qc_summary': adata.obs[['total_counts', 'n_genes_by_counts', 
                              'pct_counts_mt', 'clusters']].describe()
}

# 保存为逗号分隔值文件 (Comma-Separated Values, CSV)
for name, df in results.items():
    df.to_csv(f'{name}.csv')
```

---

## 第三部分：What's Next - 验收与进阶

### 验收清单

完成以下检查，确认分析质量：

**数据质量**：
- 组织内 spot 保留率通常在 80% 以上
- 线粒体基因比例中位数一般低于 20%（但代谢活跃组织可能更高）
- 归一化后总计数分布应该趋于一致

**空间分析**：
- 空间域应该与组织结构对应
- 标志基因在空间上应该有明确模式
- SVG 检测建议包含负对照验证

**可复现性**：
- 设置随机种子
- 记录所有参数
- 保存中间结果

**分析证据**：
- 每个结论有对应的可视化图表
- 包含负对照或随机化检验
- 进行稳健性测试
- 明确说明结论的适用范围

### 常见陷阱

**陷阱 1：过度质控**
- 问题：设置过严的阈值，丢失真实的生物学变异
- 解决：通过稳健性测试选择阈值，一般保留 85-95% 的组织内 spot

**陷阱 2：忽略空间信息**
- 问题：只做转录组分析，不利用空间坐标
- 解决：始终检查结果的空间分布，使用空间统计方法

**陷阱 3：缺少负对照**
- 问题：无法判断结果是否为假阳性
- 解决：使用组织外 spot、随机化、排列检验作为对照

**陷阱 4：参数依赖**
- 问题：结论对单一参数过度敏感
- 解决：测试多个参数组合，报告稳健的结果

**陷阱 5：边界模糊**
- 问题：不清楚结论的适用范围
- 解决：明确说明"能说明什么"和"不能说明什么"

### 进阶方向

完成基础流程后，可以探索：

1. **细胞类型反卷积** (Deconvolution)：从混合信号中推断各组分比例
   - 工具：Cell2location, RCTD, SPOTlight
   - 应用：推断每个 spot 的细胞类型组成

2. **细胞通讯分析**：
   - 工具：CellPhoneDB, COMMOT, stLearn
   - 应用：识别配体-受体对、推断信号通路

3. **空间轨迹推断**：
   - 工具：SpatialDE, Giotto, stLearn
   - 应用：识别基因表达梯度 (Gradient)、边界 (Boundary)

4. **多样本整合**：
   - 工具：Harmony, Seurat, scVI
   - 应用：消除批次效应 (Batch Effect)、跨样本比较

---

## 核心要点回顾

本文展示了空间转录组数据分析的完整流程，从数据加载到生物学解释的 9 个关键步骤。核心思想是**证据驱动的决策链**：每个分析步骤都需要通过可视化图表检查数据质量、通过对照实验排除假阳性、通过参数测试验证结果稳健性、明确说明结论的适用范围和局限性。

在质量控制阶段，我们不是简单地套用固定阈值，而是通过查看数据分布、比较组织内外 spot、测试不同参数的影响来选择合适的过滤标准。在空间分析阶段，我们通过随机化检验来验证空间模式不是偶然产生的，通过负对照来评估假阳性率。在得出结论时，我们明确说明每一步能说明什么、不能说明什么。

这种思维方式比具体的代码更重要。记住三个关键问题：输入是否可信？方法是否稳健？结论的边界在哪？掌握这套思维方式，你就能应对任何空间转录组数据集，而不是机械地套用代码模板。

分析不是跑代码，而是构建可信的证据链。
