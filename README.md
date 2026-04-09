# 空间转录组训练营（ST Training Camp）

以 10x Visium 公共数据为主线，构建从概念到实践的完整学习路径。

## 项目定位

**从概念到实践的完整学习路径** - 不仅教你"怎么做"，更让你理解"为什么这么做"和"方法的本质是什么"。

### 核心特色

- 实践优先：端到端数据分析流程贯穿所有阶段
- 证据链驱动：质量检查、对照验证、稳健性测试、结论边界
- 可复现交付：每篇包含图表、常见陷阱、验收清单
- 自动化流程：harness.py 一键生成文章（prompt → Agent → lint → notebook → sync）

## 项目状态

- 规模：206 篇文章，S0-S12 系列体系
- 已发布：13 篇文章
  - S0 系列：10/12 篇
  - S2 系列：1/31 篇
  - S4 系列：1/16 篇
  - S5 系列：1/21 篇
- 技术栈：Python (Scanpy + Squidpy)
- 数据主线：10x Visium / Visium HD 公共数据
- 平均 Linter 评分：97-100/100

## 仓库结构

```
ST/
├── AGENTS.md                    # 智能体导航入口（必读）
├── README.md                    # 本文件
│
├── articles/                    # 已发布文章（13 篇）
│   ├── 002_S0_空间转录组数据分析完整流程[通用][Scanpy][Squidpy][入门].md
│   ├── 003_S0_Scanpy与Squidpy快速上手[通用][Scanpy][Squidpy][入门].md
│   ├── ... (其他 11 篇)
│   └── summaries/               # 文章摘要（供系列上下文使用）
│
├── notebooks/                   # 可执行 Jupyter Notebook（13 篇）
│   ├── README.md                # Notebook 使用说明
│   ├── 002_S0_空间转录组数据分析完整流程[通用][Scanpy][Squidpy][入门]_实践.ipynb
│   └── ... (其他 12 个 notebooks)
│
├── docs/                        # 项目文档
│   ├── 01_知识体系/
│   │   └── 空间转录组完整知识体系.md  # S0-S12 系列规划
│   │
│   ├── 02_项目管理/
│   │   ├── article_index.json          # 206 篇文章索引（动态生成）
│   │   └── ST_文章排期表_v2_详细版.md  # 完整排期表
│   │
│   └── 03_规范/                 # 质量标准体系
│       ├── 术语表.md            # 40+ 核心术语
│       └── 文章质检清单_LINT.md
│
└── scripts/                     # 自动化工具
    ├── harness.py               # 主控脚本（自动化流程）
    ├── 01_lint_article.py       # 文章质检 Linter
    ├── 02_article_to_notebook.py # 文章转 Notebook
    ├── 03_sync_progress.py      # 同步进度
    └── 04_test_notebook.py      # Notebook 测试
```

## 快速开始

### 自动化生成文章（推荐）

使用 harness.py 一键生成文章：

```bash
# 1. 生成文章（自动模式）
python scripts/harness.py publish 013 --auto

# 2. Claude 会自动调用 Agent 生成文章

# 3. 后续处理（lint + notebook + summary + sync）
python scripts/harness.py post-process 013
```

完整流程：
1. `publish --auto` 生成 prompt 并保存到 `tmp/article_XXX_prompt.txt`
2. Agent 工具执行 prompt，生成文章到 `articles/`
3. `post-process` 自动完成：
   - 生成文章摘要（`articles/summaries/`）
   - 运行 Linter 质检
   - 生成 Jupyter Notebook（`notebooks/`）
   - 同步进度到索引

### 对于智能体（AI Agent）

1. 必读：`AGENTS.md` - 了解项目目标、规范、流程
2. 写作前：读取 `skills/st-article-writer/SKILL.md` 和 `docs/03_规范/术语表.md`
3. 写作中：遵循三段式结构、证据链标准、术语表
4. 写作后：harness.py 自动运行 Linter

### 对于人类（Human）

1. 了解项目：读本 README
2. 查看排期：`docs/02_项目管理/ST_文章排期表_v2_详细版.md`
3. 理解规范：`docs/03_规范/术语表.md`
4. 查看进度：`python scripts/harness.py status`

## 文章概览

- S0 总纲 (002-003, 007-016)：框架与验收体系 - 10/12 篇已完成
- S1 生物学底座 (017-031)：组织学、TME、空间逻辑
- S2 平台与实验 (004, 032-061)：Visium/Xenium/MERFISH 等 - 1/31 篇已完成
- S3 数据工程 (062-076)：预处理、版本控制、可复现
- S4 QC/去噪/补值 (005, 077-091)：质量控制与数据清理 - 1/16 篇已完成
- S5 域/SVG/模块 (006, 092-111)：空间域分割、空间可变基因 - 1/21 篇已完成
- S6 细胞组成 (112-126)：反卷积与细胞类型推断
- S7 CCC (127-141)：细胞通讯
- S8 轨迹 (142-151)：空间轨迹与梯度
- S9 多组学 (152-166)：多模态整合
- S10 工程化 (167-181)：Pipeline、测试、规范
- S11 应用 (182-196)：肿瘤、神经、纤维化等应用
- S12 前沿 (197-206)：AI、3D、未来路线图

完整排期见 `docs/02_项目管理/ST_文章排期表_v2_详细版.md`

## 核心原则

### 写作原则

1. 高屋建瓴 - 揭示方法的本质，而不是罗列技术细节
2. 深入浅出 - 用具体案例说明抽象概念
3. 知行合一 - 每个概念都有对应的实操验证
4. 认知递进 - 从现象 → 功能 → 原理的三层递进
5. 启发思考 - 用问题引导，而不是直接给答案

### 质量标准

- 证据链完整：质量检查 + 对照验证 + 稳健性测试 + 结论边界
- 术语一致：同一概念全篇用词一致
- 可复现：每篇都有验收清单和复现记录
- Linter 评分：≥ 80 分

## 工具使用

### Harness 主控脚本

```bash
# 查看项目状态
python scripts/harness.py status

# 生成文章（自动模式）
python scripts/harness.py publish 013 --auto

# 后续处理（生成后）
python scripts/harness.py post-process 013

# 单独运行 lint
python scripts/harness.py lint articles/013_*.md

# 单独生成 notebook
python scripts/harness.py notebook articles/013_*.md

# 同步进度
python scripts/harness.py sync
```

### 运行 Linter

```bash
# 检查单篇文章
python scripts/01_lint_article.py articles/003_xxx.md

# 检查所有文章
python scripts/harness.py lint-all
```

### 生成可执行 Notebook

```bash
# 单篇文章
python scripts/02_article_to_notebook.py articles/002_xxx.md

# 批量生成
for file in articles/*.md; do
    python scripts/02_article_to_notebook.py "$file"
done
```

### 运行 Notebook

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Jupyter
cd notebooks
jupyter notebook

# 或使用 JupyterLab
jupyter lab
```

详见 `notebooks/README.md`

**扫码关注微信公众号【生信F3】获取文章完整内容，分享生物信息学最新知识。**

![ShengXinF3_QRcode](https://raw.githubusercontent.com/ShengXinF3/ShengXinF3/master/ShengXinF3_QRcode.jpg)

## License

MIT

---

核心理念：Agent 做体力活，人做判断与质检。
