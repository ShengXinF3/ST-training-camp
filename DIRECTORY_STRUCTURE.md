# ST 项目目录结构说明

> 更新时间: 2026-04-08

## 📁 标准化目录结构

```
ST/
├── README.md                           # 项目总览（必读）
├── AGENTS.md                           # 智能体导航入口（必读）
│
├── articles/                           # 已发布文章（核心内容）
│   ├── 002_主线01_项目开箱.md
│   ├── 003_主线02_QC指标空间化.md
│   ├── 004_主线03_空间伪影识别.md
│   └── 005_主线04_组织外spot识别.md
│
├── notebooks/                          # 可执行 Jupyter Notebook
│   ├── README.md                       # Notebook 使用说明
│   ├── 002_主线01_项目开箱_实践.ipynb
│   ├── 003_主线02_QC指标空间化_实践.ipynb
│   ├── 004_主线03_空间伪影识别_实践.ipynb
│   └── 005_主线04_组织外spot识别_实践.ipynb
│
├── scripts/                            # 自动化工具
│   ├── 01_lint_article.py                 # 文章质检 Linter
│   ├── 02_article_to_notebook.py          # 文章转 Notebook 工具
│
├── docs/                               # 规范与规划文档
│   ├── README.md                       # 目录说明
│   │
│   ├── 01_快速开始/                    # 写作前必读
│   │   ├── 写作指南.md
│   │   └── 数据清单.md
│   │
│   ├── 02_项目管理/                    # 项目状态跟踪
│   │   ├── PROJECT_STATUS.md
│   │   ├── NEXT_ACTIONS.md
│   │   ├── DECISIONS.md
│   │   ├── HARNESS_PLAN.md
│   │   └── ST_文章排期表_v2.md  # 100 篇完整排期（20K）
│   │
│   └── 03_规范/                        # 质量标准体系
│       ├── README.md
│       ├── 术语表.md
│       ├── 文章交付契约_模板.md
│       ├── 文章质检清单_LINT.md
│       ├── 文风指南.md
│       ├── AI_Agent时代_生信分析可执行框架.md
│       └── 示例_CDDS_三种粒度.md
│
├── harness/                            # Harness Engineering 文件集
│   ├── README.md                       # Harness 使用说明
│   ├── 01_核心导航/
│   ├── 02_规划文档/
│   ├── 03_质量保证/
│   ├── 04_自动化工具/
│   └── 05_示例文章/
│
└── archive/                            # 归档文件（历史文档）
    └── 临时文档/
```

---

## 🎯 目录功能说明

### 核心工作目录

| 目录 | 用途 | 更新频率 |
|------|------|---------|
| `articles/` | 已发布文章 | 每周 3 篇 |
| `notebooks/` | 可执行代码验证 | 与文章同步 |
| `scripts/` | 自动化工具 | 按需更新 |
| `docs/` | 规范与规划 | 持续更新 |

### 参考目录

| 目录 | 用途 | 更新频率 |
|------|------|---------|
| `harness/` | Harness 方法论文件集 | 稳定，供复用 |
| `archive/` | 历史文档归档 | 只增不改 |

---

## 📝 文件命名规范

### 文章命名
```
00X_主线XX_标题.md
```

### Notebook 命名
```
00X_主线XX_标题_实践.ipynb
```

### 脚本命名
```
动词_名词.py
```

---

## 🚀 标准化工作流

### 1. 写文章
```bash
# 1. 从排期表确认定位
vim docs/02_项目管理/ST_文章排期表_v2.md

# 2. 创建文章
vim articles/00X_主线XX_标题.md

# 3. 运行 Linter 检查
python scripts/01_lint_article.py articles/00X_主线XX_标题.md
```

### 2. 生成 Notebook
```bash
# 自动生成可执行 Notebook
python scripts/02_article_to_notebook.py articles/00X_主线XX_标题.md
```

### 3. 验证代码
```bash
# 启动 Jupyter
cd notebooks
jupyter notebook
```

### 4. 发布
```bash
# 确认质量
python scripts/01_lint_article.py articles/00X_主线XX_标题.md

# 提交
git add articles/00X_主线XX_标题.md notebooks/00X_主线XX_标题_实践.ipynb
git commit -m "feat: add article 00X"
```

---

## 🔧 Harness Engineering 完善度

### 六大核心概念完成度

| 概念 | 完成度 | 核心组件 |
|------|--------|---------|
| 1. 仓库即记录系统 | ✅ 90% | docs/, harness/, archive/ |
| 2. 地图而非手册 | ✅ 90% | AGENTS.md, README.md |
| 3. 机械化执行 | ✅ 85% | 01_lint_article.py, 02_article_to_notebook.py |
| 4. 智能体可读性 | ✅ 85% | 术语表, 三段式结构 |
| 5. 吞吐量改变合并 | ✅ 70% | st-article-writer Skill |
| 6. 熵管理 | ⏳ 50% | 术语表检查, 质量评分 |

### 已实现的自动化

- ✅ **文章质检**: `01_lint_article.py` 自动检查规范
- ✅ **代码验证**: `02_article_to_notebook.py` 自动生成可执行 Notebook
- ✅ **质量评分**: 0-100 分评分系统
- ✅ **术语一致性**: 自动检查术语混用
- ✅ **文章生成**: st-article-writer Skill 标准化生成

### 待完善的自动化

- ⏳ **批量生成**: 并行生成多篇文章
- ⏳ **CI/CD**: 自动运行 Linter 和 Notebook
- ⏳ **熵管理**: 定期扫描术语漂移、质量下降

---

## 📊 目录纯净度

### 根目录文件（10 个）

✅ **核心文件**（保留）:
- `README.md` - 项目总览
- `AGENTS.md` - 智能体导航
- `ST_文章排期表_v2.md` - 100 篇排期

✅ **核心目录**（保留）:
- `articles/` - 已发布文章
- `notebooks/` - 可执行 Notebook
- `scripts/` - 自动化工具
- `docs/` - 规范与规划
- `harness/` - Harness 文件集

📦 **归档目录**（已整理）:
- `archive/` - 历史文档

---

## 🎯 下一步优化

### 1. 完善自动化
- 实现批量生成流程
- 添加 CI/CD 自动检查
- 实现熵管理机制

### 2. 持续优化
- 定期清理归档目录
- 更新规范文档
- 优化工具性能

---

**核心理念**: 保持目录结构清晰、规范化、易维护。
