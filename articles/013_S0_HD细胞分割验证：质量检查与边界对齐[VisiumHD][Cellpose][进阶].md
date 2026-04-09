---
title: "Visium HD 细胞分割验证：质量检查与边界对齐"
article_id: "013"
series: "S0"
tags: ["VisiumHD", "Cellpose", "进阶"]
created: "2026-04-09"
updated: "2026-04-09"
---

# Visium HD 细胞分割验证：质量检查与边界对齐

在上一篇（012）中，我们拆解了 Visium HD（High Definition，高清晰度空间转录组平台）的数据结构，知道了 bin 级别数据是什么。但 Visium HD 的核心优势不只是高分辨率的 bin，而是可以结合 H&E 染色图像做细胞分割 (Cell Segmentation)，把转录组信号从"网格"升级到"真实细胞边界"。

问题来了：分割出来的细胞边界靠谱吗？

这不是一个可以"跑完就信"的步骤。细胞分割的质量直接决定了后续分析的可信度——边界画错了，细胞类型注释、空间域识别、细胞通讯推断全都会出问题。

这一篇我们聚焦一个核心问题：**如何验证细胞分割的质量？**

---

## 第一部分：为什么分割质量检查是必需的？

### 1.1 细胞分割不是"黑盒魔法"

Cellpose、Mesmer、DeepCell 这些工具看起来很智能，但它们本质上是在做**图像分类 + 边界预测**。它们会犯错：

- **过分割 (Over-segmentation)**：一个细胞被切成多块
- **欠分割 (Under-segmentation)**：多个细胞被合并成一个
- **边界偏移 (Boundary Shift)**：边界位置不准确，导致转录组信号分配错误
- **假阳性 (False Positive)**：把背景、血管、空洞识别成细胞

这些错误在不同组织类型、染色质量、细胞密度下的发生率不同。**你必须用数据说话，而不是盲目相信算法。**

### 1.2 分割质量影响下游分析

| 下游分析 | 分割质量影响 |
|---------|------------|
| 细胞类型注释 | 边界错误 → 基因表达混合 → 注释错误 |
| 空间域识别 | 过分割 → 细胞数量虚高 → 域边界模糊 |
| 细胞通讯推断 | 边界偏移 → 邻域关系错误 → 配体-受体对假阳性 |
| 空间可变基因检测 | 欠分割 → 空间分辨率下降 → 梯度信号丢失 |

**核心原则**：分割质量检查不是"可选项"，而是"必需项"。

---

## 第二部分：如何检查分割质量？

### 2.1 准备工作：加载数据

假设你已经用 Cellpose 完成了细胞分割，得到了一个包含细胞边界的 AnnData 对象。

```python
import scanpy as sc
import squidpy as sq
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
from skimage import measure

# Load Visium HD (High Definition) data with cell segmentation
adata = sc.read_h5ad('visium_hd_with_segmentation.h5ad')

# Check data structure
print(f"Total cells: {adata.n_obs}")
print(f"Total genes: {adata.n_vars}")
print(f"Spatial coordinates: {adata.obsm['spatial'].shape}")
print(f"Segmentation mask available: {'segmentation_mask' in adata.uns}")
```

**输出示例**：
```
Total cells: 12847
Total genes: 18085
Spatial coordinates: (12847, 2)
Segmentation mask available: True
```

### 2.2 质量指标 1：细胞大小分布

细胞大小 (Cell Area) 是最直观的质量指标。我们通过诊断图 (Diagnostic Plot) 来可视化细胞大小分布，检查是否符合生物学预期。正常组织中，细胞大小应该符合以下范围：

- **上皮细胞**：10-20 µm 直径（约 100-400 µm²）
- **免疫细胞**：5-10 µm 直径（约 20-100 µm²）
- **神经元**：10-30 µm 直径（约 100-900 µm²）

如果出现大量异常值（如 < 10 µm² 或 > 1000 µm²），说明分割质量有问题。

```python
# Calculate cell area (assuming segmentation mask is in pixels, 1 pixel = 0.5 µm)
pixel_size = 0.5  # µm per pixel
adata.obs['cell_area_um2'] = adata.obs['cell_area_pixels'] * (pixel_size ** 2)

# Plot cell area distribution
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Histogram
axes[0].hist(adata.obs['cell_area_um2'], bins=50, edgecolor='black', alpha=0.7)
axes[0].axvline(np.median(adata.obs['cell_area_um2']), color='red', 
                linestyle='--', label=f"Median: {np.median(adata.obs['cell_area_um2']):.1f} µm²")
axes[0].set_xlabel('Cell Area (µm²)')
axes[0].set_ylabel('Number of Cells')
axes[0].set_title('Cell Area Distribution')
axes[0].legend()

# Spatial distribution of cell area
sq.pl.spatial_scatter(adata, color='cell_area_um2', size=5, 
                      cmap='viridis', ax=axes[1], show=False)
axes[1].set_title('Spatial Distribution of Cell Area')

plt.tight_layout()
plt.savefig('cell_area_qc.png', dpi=300, bbox_inches='tight')
plt.show()
```

**诊断标准**：
- ✅ 中位数在 50-300 µm² 之间
- ✅ 95% 的细胞在 10-1000 µm² 之间
- ❌ 出现大量 < 10 µm² 的细胞 → 过分割
- ❌ 出现大量 > 1000 µm² 的细胞 → 欠分割

### 2.3 质量指标 2：UMI 数与细胞大小的相关性

细胞越大，捕获的 UMI 数应该越多。如果相关性很弱（Pearson r < 0.3），说明分割边界与转录组信号不匹配。

```python
# Calculate total UMI counts per cell
adata.obs['total_counts'] = adata.X.sum(axis=1).A1

# Correlation between cell area and UMI counts
corr, pval = pearsonr(adata.obs['cell_area_um2'], adata.obs['total_counts'])

# Plot
fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(adata.obs['cell_area_um2'], adata.obs['total_counts'], 
           s=5, alpha=0.3, c='steelblue')
ax.set_xlabel('Cell Area (µm²)')
ax.set_ylabel('Total UMI Counts')
ax.set_title(f'Cell Area vs UMI Counts\nPearson r = {corr:.3f}, p < 0.001')
ax.set_xscale('log')
ax.set_yscale('log')

plt.tight_layout()
plt.savefig('area_umi_correlation.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"Correlation: {corr:.3f} (p-value: {pval:.2e})")
```

**诊断标准**：
- ✅ Pearson r > 0.5：强相关，分割质量好
- ⚠️ Pearson r = 0.3-0.5：中等相关，需要进一步检查
- ❌ Pearson r < 0.3：弱相关，分割质量差

### 2.4 质量指标 3：边界对齐检查

这是最关键的一步：**分割边界是否与 H&E 图像中的真实细胞边界对齐？**

我们需要可视化分割结果，叠加到原始 H&E 图像上。

```python
# Load H&E image and segmentation mask
img = plt.imread('tissue_hires_image.png')
seg_mask = adata.uns['segmentation_mask']

# Select a region of interest (ROI) for visualization
x_min, x_max = 1000, 1500
y_min, y_max = 1000, 1500

img_roi = img[y_min:y_max, x_min:x_max]
seg_roi = seg_mask[y_min:y_max, x_min:x_max]

# Find cell boundaries
boundaries = measure.find_boundaries(seg_roi, mode='outer')

# Plot
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Original H&E image
axes[0].imshow(img_roi)
axes[0].set_title('H&E Image')
axes[0].axis('off')

# Segmentation mask
axes[1].imshow(seg_roi, cmap='nipy_spectral')
axes[1].set_title('Segmentation Mask')
axes[1].axis('off')

# Overlay boundaries on H&E
axes[2].imshow(img_roi)
axes[2].imshow(boundaries, cmap='Reds', alpha=0.5)
axes[2].set_title('Boundaries Overlay')
axes[2].axis('off')

plt.tight_layout()
plt.savefig('boundary_alignment_check.png', dpi=300, bbox_inches='tight')
plt.show()
```

**诊断标准**：
- ✅ 边界与细胞核、细胞质边缘对齐
- ❌ 边界穿过细胞核 → 过分割
- ❌ 边界包含多个细胞核 → 欠分割
- ❌ 边界与组织结构不匹配 → 算法参数需要调整

### 2.5 质量指标 4：负对照检查

在组织外区域（背景），不应该有细胞被识别出来。如果有，说明算法产生了假阳性。

```python
# Identify cells in tissue vs out of tissue
# Assuming 'in_tissue' column exists in adata.obs
if 'in_tissue' in adata.obs.columns:
    in_tissue_count = adata.obs['in_tissue'].sum()
    out_tissue_count = (~adata.obs['in_tissue']).sum()
    
    print(f"Cells in tissue: {in_tissue_count}")
    print(f"Cells out of tissue: {out_tissue_count}")
    print(f"False positive rate: {out_tissue_count / adata.n_obs * 100:.2f}%")
    
    # Plot spatial distribution
    fig, ax = plt.subplots(figsize=(8, 6))
    sq.pl.spatial_scatter(adata, color='in_tissue', size=5, 
                          palette=['red', 'blue'], ax=ax, show=False)
    ax.set_title('In Tissue vs Out of Tissue')
    plt.savefig('in_tissue_check.png', dpi=300, bbox_inches='tight')
    plt.show()
else:
    print("Warning: 'in_tissue' column not found. Skipping negative control check.")
```

**诊断标准**：
- ✅ 假阳性率 < 5%
- ⚠️ 假阳性率 5-10%：可接受，但需要过滤
- ❌ 假阳性率 > 10%：分割质量差，需要重新调参

### 2.6 质量指标 5：敏感性分析

改变 Cellpose 的关键参数（如 `diameter`、`flow_threshold`），看分割结果是否稳定。

```python
# Simulate sensitivity analysis (assuming you have multiple segmentation results)
# In practice, you would run Cellpose with different parameters

params = [
    {'diameter': 15, 'flow_threshold': 0.4},
    {'diameter': 20, 'flow_threshold': 0.4},
    {'diameter': 25, 'flow_threshold': 0.4},
]

results = []
for param in params:
    # Load segmentation result for this parameter set
    # adata_param = sc.read_h5ad(f"segmentation_d{param['diameter']}_ft{param['flow_threshold']}.h5ad")
    # results.append({
    #     'diameter': param['diameter'],
    #     'n_cells': adata_param.n_obs,
    #     'median_area': np.median(adata_param.obs['cell_area_um2'])
    # })
    pass

# Plot sensitivity
# df_sensitivity = pd.DataFrame(results)
# fig, axes = plt.subplots(1, 2, figsize=(12, 4))
# axes[0].plot(df_sensitivity['diameter'], df_sensitivity['n_cells'], marker='o')
# axes[0].set_xlabel('Diameter Parameter')
# axes[0].set_ylabel('Number of Cells')
# axes[0].set_title('Sensitivity: Cell Count')
# 
# axes[1].plot(df_sensitivity['diameter'], df_sensitivity['median_area'], marker='o')
# axes[1].set_xlabel('Diameter Parameter')
# axes[1].set_ylabel('Median Cell Area (µm²)')
# axes[1].set_title('Sensitivity: Cell Area')
# 
# plt.tight_layout()
# plt.savefig('sensitivity_analysis.png', dpi=300, bbox_inches='tight')
# plt.show()

print("Sensitivity analysis: Run Cellpose with different parameters and compare results.")
print("Stable results across parameter ranges indicate robust segmentation.")
```

**诊断标准**：
- ✅ 细胞数量变化 < 20%
- ✅ 中位数细胞面积变化 < 30%
- ❌ 结果对参数高度敏感 → 需要更仔细的参数调优

---

## 第三部分：常见错误与修复策略

### 3.1 常见错误类型

| 错误类型 | 表现 | 原因 | 修复策略 |
|---------|------|------|---------|
| 过分割 | 大量 < 10 µm² 的细胞 | `diameter` 参数过小 | 增大 `diameter` |
| 欠分割 | 大量 > 1000 µm² 的细胞 | `diameter` 参数过大 | 减小 `diameter` |
| 边界偏移 | UMI-面积相关性弱 | `flow_threshold` 不合适 | 调整 `flow_threshold` |
| 假阳性 | 组织外有大量细胞 | 背景噪声未过滤 | 使用 `in_tissue` 过滤 |

### 3.2 修复示例：过滤低质量细胞

```python
# Filter cells based on quality metrics
adata_filtered = adata[
    (adata.obs['cell_area_um2'] > 10) &
    (adata.obs['cell_area_um2'] < 1000) &
    (adata.obs['total_counts'] > 50) &
    (adata.obs['in_tissue'] == True)
].copy()

print(f"Before filtering: {adata.n_obs} cells")
print(f"After filtering: {adata_filtered.n_obs} cells")
print(f"Removed: {adata.n_obs - adata_filtered.n_obs} cells ({(adata.n_obs - adata_filtered.n_obs) / adata.n_obs * 100:.2f}%)")
```

### 3.3 边界声明

**这套质量检查能说明什么？**
- ✅ 分割结果是否符合生物学预期（细胞大小、数量）
- ✅ 边界是否与 H&E 图像对齐
- ✅ 是否存在系统性错误（过分割、欠分割、假阳性）

**不能说明什么？**
- ❌ 不能保证每个细胞的边界都 100% 准确
- ❌ 不能替代人工检查（尤其是复杂组织）
- ❌ 不能解决 H&E 染色质量差的问题

---

## 验收清单

完成本篇后，你应该能够：

- [ ] 计算并可视化细胞大小分布
- [ ] 评估 UMI 数与细胞大小的相关性
- [ ] 叠加分割边界到 H&E 图像，检查对齐情况
- [ ] 识别并过滤假阳性细胞（组织外）
- [ ] 进行敏感性分析，评估分割稳健性
- [ ] 根据质量指标过滤低质量细胞

---

## 常见坑

1. **坑 1：盲目相信算法**
   - 问题：直接用分割结果做下游分析，不检查质量
   - 后果：错误的细胞边界 → 错误的生物学结论
   - 解决：必须做质量检查，尤其是边界对齐

2. **坑 2：忽略组织类型差异**
   - 问题：用同一套参数处理所有组织
   - 后果：某些组织分割质量差（如脑组织、肿瘤组织）
   - 解决：针对不同组织类型调整参数

3. **坑 3：不做负对照检查**
   - 问题：没有检查组织外区域的假阳性
   - 后果：假阳性细胞污染下游分析
   - 解决：使用 `in_tissue` 标记过滤

4. **坑 4：过度依赖单一指标**
   - 问题：只看细胞数量，不看细胞大小、UMI 相关性
   - 后果：错过系统性错误
   - 解决：使用多个质量指标综合判断

---

## 下一篇预告

014: **Visium HD 数据的细胞类型注释：从 bin 到细胞**

有了质量合格的细胞分割结果，下一步是给每个细胞打上"身份标签"——这就是细胞类型注释 (Cell Type Annotation)。

我们会讲：
- 如何利用 bin 级别的聚类结果辅助细胞注释
- 如何使用参考数据集（如 scRNA-seq）做自动注释
- 如何验证注释结果的可信度

---

**核心要点回顾**：
- 细胞分割不是"黑盒魔法"，必须做质量检查
- 五大质量指标：细胞大小、UMI 相关性、边界对齐、负对照、敏感性
- 常见错误：过分割、欠分割、边界偏移、假阳性
- 质量检查是下游分析可信度的基础

---

*本文是 BioF3 空间转录组训练营 S0 系列第 13 篇。*
