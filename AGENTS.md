# 空间转录组全栈训练营 - 智能体导航

> 本文件是智能体的入口点。100 行以内，只指路不讲课。

## 项目目标（One-liner）

构建一套"实践主线贯穿 + 知识点按需融入"的空间转录组训练营公众号合集（206 篇规划），覆盖 Visium/HD/Xenium/Stereo-seq 等全平台，以及 Scanpy/Squidpy/Cell2location 等全工具栈。

## 核心原则

- **实践优先**: 端到端数据分析流程贯穿所有阶段
- **证据链驱动**: 诊断图 + 对照 + 敏感性 + 边界声明
- **可复现交付**: 每篇包含图/表/常见坑/验收清单
- **平台标签化**: 文件名明确标注平台/工具/难度
- **工具独立成篇**: 每个重要工具单独讲解

## 文件导航

### 项目状态与规划
- `docs/01_知识体系/空间转录组完整知识体系.md` - 完整知识体系分类（S0-S12）
- `docs/02_项目管理/ST_文章排期表_v2_详细版.md` - 完整排期表（206 篇，当前使用）
- `docs/02_项目管理/article_index.json` - 动态生成的文章索引（由 generate_article_index.py 生成）

### 写作规范（必读）
- `skills/st-article-writer/SKILL.md` - 文章写作 Skill（完整规范）
- `docs/03_规范/术语表.md` - 统一术语使用（40+ 术语）
- `docs/03_规范/文章质检清单_LINT.md` - 发布前 5 分钟检查清单

### 自动化工具（Harness Engineering）
- `scripts/harness.py` - 主控脚本（自动化流程）
- `scripts/generate_article_index.py` - 动态生成文章索引
- `scripts/01_lint_article.py` - 自动化质检（0-100 分评分）
- `scripts/02_article_to_notebook.py` - 文章转 Notebook 工具
- `scripts/03_sync_progress.py` - 同步进度

### 已发布文章（11 篇）
- S0 系列（8/12 篇）：002, 003, 007, 008, 009, 010, 011, 012
- S2 系列（1/31 篇）：004
- S4 系列（1/16 篇）：005
- S5 系列（1/21 篇）：006

所有文章均在 `articles/` 目录下，命名格式：`{ID}_{系列}_{标题}[标签][难度].md`

### 可执行 Notebooks（11 篇）
所有已发布文章均有对应的 Jupyter Notebook，位于 `notebooks/` 目录下，命名格式：`{ID}_{系列}_{标题}[标签][难度]_实践.ipynb`

## 写作流程（标准化）

### 自动化生成（推荐）

使用 harness.py 一键生成文章：

```bash
# 1. 生成文章（自动模式）
python scripts/harness.py publish 013 --auto

# 2. Claude 会自动调用 Agent 生成文章

# 3. 后续处理（lint + notebook + summary + sync）
python scripts/harness.py post-process 013
```

**完整流程**：
1. `publish --auto` 生成 prompt 并保存到 `tmp/article_XXX_prompt.txt`
2. Agent 工具执行 prompt，生成文章到 `articles/`
3. `post-process` 自动完成：
   - 生成文章摘要（`articles/summaries/`）
   - 运行 Linter 质检
   - 生成 Jupyter Notebook（`notebooks/`）
   - 同步进度到索引

### 手动写作流程

#### 1. 创建文章前
- [ ] 从 `docs/02_项目管理/ST_文章排期表_v2_详细版.md` 确认本篇定位
- [ ] 读取 `skills/st-article-writer/SKILL.md` 了解完整规范
- [ ] 读取 `docs/03_规范/术语表.md` 确保术语一致性

#### 2. 写作中
- [ ] 遵循三段式结构（Why & What → How → What's Next）
- [ ] 每个术语首次出现：中文 + 英文/缩写 + 一句解释
- [ ] 证据链四件套：诊断图 + 对照 + 敏感性 + 边界声明

#### 3. 发布前
- [ ] 运行 `python scripts/01_lint_article.py <文章路径>`
- [ ] 人工检查 `docs/03_规范/文章质检清单_LINT.md`
- [ ] 运行 `python scripts/02_article_to_notebook.py <文章路径>` 生成 Notebook
- [ ] 运行 `python scripts/03_sync_progress.py` 同步进度

## 禁止项（Hard Rules）

- ❌ 外链（http/https/DOI/期刊页面链接）
- ❌ 对文献主观评价（"写得踏实/组织得好/很全面"）
- ❌ 未定义缩写（首次出现没有解释）
- ❌ 教育口吻高密度（"你/先/必须/应该/别/记住"）

## 术语一致性（强制）

同一概念全篇用词一致，不混用：
- 空间域 ≠ 空间分区
- spot ≠ 空间位点（统一用 spot）
- 反卷积 ≠ 解卷积（统一用反卷积）

## 证据链标准（不可妥协）

每条结论至少配齐：
1. **诊断图**: 质量/分布/批次效应/空间伪影
2. **对照**: 负对照/随机化/替代解释
3. **敏感性**: 参数/方法替换后结论是否漂移
4. **边界声明**: 能说明什么、不能说明什么

## 下一步行动

当前优先级：
1. 继续生成 S0 系列文章（目标：完成 12 篇）
2. 使用 harness.py 自动化流程提高生产效率
3. 保持 Linter 评分 ≥ 97 分

## 变更记录

- 2026-04-08: 更新为 206 篇规划，移除已归档文件引用，添加 harness.py 自动化流程
- 2026-04-08: 优化 docs/ 目录结构，更新文件路径
- 2026-04-07: 创建 AGENTS.md，建立智能体导航入口
