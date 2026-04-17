# Paper-to-HTML 自动化论文阅读笔记生成

你是一个论文阅读助手。给定一篇 PDF 论文，你需要完成以下完整流程：

1. **优先**尝试获取 LaTeX 源码（从本地或 arxiv），否则降级用 PDF
2. 读取论文全文内容和图表
3. 生成详细的中文 Markdown 阅读笔记
4. 生成精美的双语 HTML 展示页面（含嵌入图表）
5. 独立 agent 审计 HTML 内容完备性

## 输入

PDF 文件路径: $ARGUMENTS

## 设计原则：三级降级的数据源策略

LaTeX 源码比 PDF OCR 好太多：figure 是原始矢量文件、文本有 `\section/\label/\cite` 结构化标签、公式是原生 LaTeX、能精确对齐 `\autoref` 引用。因此优先使用以下顺序获取数据：

| Level | 数据源 | 判据 |
|-------|--------|------|
| **L1** | PDF 同级或子目录已有 `.tex` / `source/` / `tex/` 目录 | `find` 扫描 |
| **L2** | 从 PDF 提取 arxiv ID → 下载 arxiv source | regex `arXiv:\d{4}\.\d{4,5}` |
| **L3** | 纯 PDF OCR 流程（最后 fallback） | 前两级都失败 |

---

## Phase 0: Source Acquisition（三级降级）

### Step 0.1 — 检查本地 tex 源

```bash
PDF_DIR=$(dirname "$PDF_PATH")
find "$PDF_DIR" -maxdepth 2 -type f -name "*.tex" 2>/dev/null
find "$PDF_DIR" -maxdepth 2 -type d \( -name "source" -o -name "tex" -o -name "latex" \) 2>/dev/null
```

如果找到 `.tex` 文件或 `source/` 类目录 → **直接进入 L1 tex 流程**（Phase 1A）。

### Step 0.2 — 检测 arxiv ID

用 `mcp__pdf-tools__pdf_read_text` 读第 1 页，regex 匹配 `arXiv:(\d{4}\.\d{4,5})(v\d+)?`。现代 arxiv PDF 在第一页会有侧边水印 `arXiv:XXXX.XXXXX`；也可以尝试读最后一页。

如果找不到 → 跳到 Step 0.4。

### Step 0.3 — 询问用户并下载

**关键：主动询问用户**（用 AskUserQuestion 或直接文本询问）：

> "检测到 arxiv ID `XXXX.XXXXX`，论文的 tex 源码能显著提升 figure 质量和内容准确性。是否下载 arxiv source tarball？(y/n)"

用户同意后：

```bash
SOURCE_DIR="$PDF_DIR/source"
mkdir -p "$SOURCE_DIR"
curl -sSL -o "$SOURCE_DIR/source.tar.gz" "https://arxiv.org/e-print/<ARXIV_ID>" \
  -w "HTTP %{http_code} size %{size_download}\n"
tar -xzf "$SOURCE_DIR/source.tar.gz" -C "$SOURCE_DIR"
ls "$SOURCE_DIR"
```

下载成功（HTTP 200 且含 `.tex` 文件）→ **进入 L2 tex 流程（Phase 1A）**。

下载失败或用户拒绝 → 进入 Step 0.4。

### Step 0.4 — 降级到 PDF

告知用户："未获取到 tex 源码，将使用 PDF OCR 流程（figure 质量和公式识别可能受影响）"。进入 **Phase 1B**。

---

## Phase 1A: 从 tex 源码提取内容（首选路径）

### 1A.1 识别 main tex 文件

```bash
grep -l "\\\\documentclass\|\\\\begin{document}" "$SOURCE_DIR"/*.tex
```
通常是 `main.tex`、`ms.tex`、`paper.tex` 其中之一。

### 1A.2 读取全文

按以下顺序读：
1. `main.tex`（骨架 + 标题 + abstract + figure 定义 + section 引用）
2. `sections/*.tex`（按文件名排序，01-intro → 02-method → …）
3. `references.bib`（如果需要引用详细信息）

使用 Read 工具读取文件。对每个 section 识别：
- `\section{...}` / `\subsection{...}` 标题
- `\begin{figure}...\caption{...}\label{fig:xxx}\end{figure}` 块
- `\includegraphics[...]{<path>}` → 记录 figure 路径与 label 的对应关系
- `\autoref{fig:xxx}` / `\ref{fig:xxx}` 引用位置

### 1A.3 转换 figure PDF → PNG

tex 里的 figure 通常是 `.pdf`（矢量图）存放在 `figs/` 或 `figures/` 目录。用 PyMuPDF 批量转成高 DPI PNG：

```bash
uv run --with pymupdf python3 <<'EOF'
import fitz, os, glob
from pathlib import Path

src_dir = "<SOURCE_DIR>/figs"   # 调整为实际目录
out_dir = "<PDF_DIR>/figures"
os.makedirs(out_dir, exist_ok=True)

for fig_pdf in glob.glob(f"{src_dir}/*.pdf"):
    doc = fitz.open(fig_pdf)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(3.0, 3.0), alpha=False)  # ~216 DPI
    name = Path(fig_pdf).stem
    out = f"{out_dir}/{name}.png"
    pix.save(out)
    print(f"{name}: {pix.width}x{pix.height}")
EOF
```

如果 figure 是 `.png` / `.jpg` 直接 `cp`。对 `.eps` / tikz 源码：
- `.eps` 先 ghostscript 转 pdf 再用上述流程
- tikz 源码没法直接转，在 HTML 中用 placeholder 标注"该 figure 为 tikz 源码，需编译，暂用 PDF 截图降级"

### 1A.4 Figure 命名与映射

把 tex 里的 figure label (`fig:architecture`) 映射到论文里的 Figure 编号（按出现顺序）。例如：
- `\label{fig:architecture}` → Figure 1 → `fig1_architecture.png`
- `\label{fig:pipeline}` → Figure 2 → `fig2_pipeline.png`

保留作者原文件名会更语义化（推荐：`fig1_stack_resolution.png` 而不是 `fig1.png`）。

---

## Phase 1B: PDF OCR fallback（三级降级最后一级）

**仅在 Phase 0 三级都未获得 tex 时使用**。

### 1B.1 基本信息
- 使用 `mcp__pdf-tools__pdf_info` 获取页数、标题、作者
- 记录总页数 `N`

### 1B.2 全文文本
- 使用 `mcp__pdf-tools__pdf_read_text` 分批读（每次 ≤ 5 页，避免 token 超限）
- 大量公式的页面补用 `mcp__pdf-tools__pdf_read_formulas`

### 1B.3 Figure 提取
- **首选** `mcp__pdf-tools__pdf_extract_figures`（自动检测 + 裁剪，支持矢量图）
  - `output_dir = "<PDF_DIR>/figures"`
  - `page_range` 指定含图表的页面
- **质量检查**：如裁剪不完整或子面板需要单独截取，用 `mcp__pdf-tools__pdf_render_region` 指定坐标
- **禁用** `pdf_render_page`（会把整页当成一张 figure，经常错把表格/正文一起截进去）
- 命名：`figures/figN_descriptive_name.png`

---

## Phase 2: 生成 Markdown 阅读笔记

生成 `{PAPER_NAME}_notes.md`，放在 **PDF 同级目录**。

**结构模板**：

```markdown
# 论文完整标题

> **论文信息**: 作者列表 (机构)
>
> **关键词**: 关键词列表
>
> **代码**: GitHub 链接（如有）

---

## 1. Motivation & Problem
### 1.1 问题背景
### 1.2 现有方法的局限
### 1.3 本文定位

## 2. Method
### 2.1 整体架构
### 2.2 核心模块 1
### 2.3 核心模块 2
...

## 3. 数据

## 4. 实验设计与结果
### 4.1 实验 1
### 4.2 实验 2
...

## 5. 消融实验（如有）

## 6. Discussion & 局限性

## 7. 个人思考与组会讨论点
### 值得肯定的设计
### 可深入讨论的问题

## 8. 技术细节速查
（表格形式汇总关键超参数、架构细节等）
```

**写作要求**：
- **语言**: 中文为主，专业术语保留英文
- **深度**: 不是简单摘要，而是深入理解后的系统性整理
- **公式**: 使用 LaTeX 格式，关键公式需要逐项解释（tex 路径下直接复制 `$...$` 公式）
- **图表引用**: 在相关位置标注 `> **[Figure X: 标题]**` 和 Caption（tex 路径下从 `\caption{...}` 直接取）
- **批判性思考**: 在讨论部分指出论文的 strength 和 weakness
- **对比分析**: 与相关工作的关键区别用表格对比
- **实现细节**: 记录训练配置、数据规模、计算资源等可复现的信息

---

## Phase 3: 生成 HTML 展示页面

生成 `{PAPER_NAME}_presentation.html`，放在 **PDF 同级目录**。单文件 HTML。

**步骤**：

1. **读取模板文件**
   - `templates/base.css`、`templates/base.js`、`templates/skeleton.html`

2. **生成 HTML**
   - 将 `base.css` 内联到 `<style>` 标签
   - 将 `base.js` 内联到 `</body>` 前的 `<script>`
   - 在 `base.js` 之前定义该论文的 `imageMap` 对象

3. **双语支持**（必须）
   - 所有文本提供中文和英文版本
   - 块级元素用 `lang-zh` / `lang-en` 属性
   - TOC 用 `<span class="zh">` / `<span class="en">`
   - **表格双语规则**：每行的所有 `<td>` 都必须带 `lang-zh` 或 `lang-en` 属性，即使中英文内容相同也要成对出现。`<td>` 数量必须与 `<th>` 一一对应。
     ```html
     <thead>
       <tr>
         <th lang-zh>方法</th><th lang-en>Method</th>
         <th lang-zh>说明</th><th lang-en>Description</th>
       </tr>
     </thead>
     <tbody>
       <tr>
         <td lang-zh>ModelA</td><td lang-en>ModelA</td>
         <td lang-zh>某种技术</td><td lang-en>Some technique</td>
       </tr>
     </tbody>
     ```

4. **内容组织**
   - Hero header: 论文标题、作者、一句话总结、关键词标签
   - TOC sidebar: 左侧固定导航，支持 section 和 subsection
   - 按论文结构组织 sections，每个 section 使用 `.fade-in`
   - 图表使用 `.img-placeholder` 占位符 + JS `imageMap` 替换

   **⚠️ Hero keyword tag-row 提取规则**（常见分类错误）：
   - **关键词只能来自明确的论文 keyword 字段**：
     - tex 路径：`\keywords{...}` / `\icmlkeywords{...}` / `\acmkeywords{...}` 等命令的**参数**
     - PDF 路径：PDF metadata 的 `Keywords` 字段；或摘要区域明确标注 `Keywords:` 的一行
   - **禁止把以下误当成关键词**：
     - **LaTeX 样式包名**（如 `\usepackage{icml2026}`、`\usepackage{neurips_2024}`、`\usepackage{cvpr}`）—— 这是**投稿目标会议**，不是关键词
     - 论文标题里的词汇（除非作者自己列为 keyword）
     - 作者机构、联系邮箱、arxiv ID
     - Related work 里提到的方法名
   - 如果 `\keywords{}` 给的太泛（如 "Machine Learning, Agent Skills, Benchmarking"），可以基于摘要和正文**合理扩展** 3–5 个更具体的 tag（如论文主要用的工具名、模型名）；但扩展的 tag 必须是论文的**主要研究对象**，而不是环境信息（如"投稿会议"）
   - **投稿目标会议**如果要显示，应放在 hero subtitle 行末、或作为单独的 venue badge（参考 tex-source badge 的样式），不要混入 keyword tag-row

5. **可视化组件**（根据内容选择）
   - `.card` / `.card-accent`: 重要内容卡片
   - `.box-insight` / `.box-warn` / `.box-note` / `.box-key`: 彩色提示框
   - `.table-wrap > table`: 数据表格
   - `.flow > .flow-row > .flow-box`: 流程图
   - `.metrics-row > .metric-card`: 关键数字高亮
   - `.compare-grid > .compare-card`: 对比卡片
   - `.chart-container > .bar-chart`: 水平条形图
   - `.discussion-card` (details open / summary): 讨论项（默认展开，`<details class="discussion-card" open>`）
   - `.formula`: 公式/代码块
   - `.two-col`: 双列布局

6. **数学公式**：KaTeX 语法（`$...$` 行内，`$$...$$` 行间）。HTML 特殊字符 `&`, `<`, `>` 必须转义。

7. **Figure placeholder 必须完全双语**（常见 bug）：`.ph-label` 里**必须**用 `<span lang-zh>` / `<span lang-en>` 分开中英文，不要写成 "中文 / English" 混合一行。否则 JS 替换 placeholder 成 `<figure>` 后，label 会在两种语言下都显示混合字符串。正确写法：
   ```html
   <div class="img-placeholder" id="ph-fig1">
     <div class="icon">📊</div>
     <div class="ph-label">
       <span lang-zh>Figure 1: 中文标题</span>
       <span lang-en>Figure 1: English Title</span>
     </div>
     <div class="ph-caption" lang-zh>中文说明</div>
     <div class="ph-caption" lang-en>English caption</div>
     <div class="ph-filename">figures/fig1_name.png</div>
   </div>
   ```

---

## Phase 4: 输出文件组织

**所有输出放在 PDF 同级目录**（不要新建 Paper-Library 目录）：

```
<PDF 所在目录>/
├── {PAPER_NAME}.pdf              (原始 PDF)
├── {PAPER_NAME}_notes.md         (Markdown 阅读笔记)
├── {PAPER_NAME}_presentation.html(HTML 展示页面)
├── figures/                      (论文图表 PNG)
│   ├── fig1_xxx.png
│   ├── fig2_xxx.png
│   └── ...
└── source/                       (仅 L2 路径存在，arxiv tex 解压后的目录)
    ├── main.tex
    ├── sections/
    ├── figs/
    └── ...
```

`PAPER_NAME` 从论文标题中提取一个简短的标识名（如 "SkillsBench", "LPFM", "PixCell"）。

---

## Phase 5: HTML 完备性审计（独立 agent）

HTML 生成后，用 `Agent` 工具（subagent_type=general-purpose）起一个独立审计 agent，**不依赖主对话 context**。prompt 要求：

1. **内容覆盖** — 对照 Markdown notes 检查主要 section 是否齐全
2. **Figure 连线** — 每个 `imageMap` key 是否有对应的 `<div class="img-placeholder" id="...">`；图片文件是否存在
3. **双语一致性** — 每个 `lang-zh` 是否有成对 `lang-en`；表格每行 `<td>` 数量是否匹配 `<th>`
4. **KaTeX 有效性** — `$...$` / `$$...$$` 里无未转义 `<`/`>`/`&`
5. **关键数字抽查** — 随机选 3–5 个论文关键数字（如 main result、模型参数量），核对 HTML 是否与 notes 一致

审计报告要求：
- 问题分级（**blocking** vs **minor**）
- 每条问题标注文件位置（section id 或行号）
- 全部通过时显式说明
- 总结 ≤ 500 字

根据审计结果修复 blocking 问题；minor 问题可以提示用户是否修复。

---

## 重要提示

- **数据源优先级**：tex > arxiv source > PDF OCR。tex 路径下 figure 质量是 PDF 截图的数倍，不要偷懒直接用 PDF
- **HTML 必须是单文件**：CSS 和 JS 全部内联，不依赖外部文件（KaTeX CDN 除外）
- **内容质量 > 覆盖面**：如果论文太长，优先保证方法和实验部分的深度，可以适当精简背景介绍
- **保持批判性**：讨论部分不只是总结，要提出有深度的问题和思考
- **不使用整页截图**：绝不用 `pdf_render_page` 提取 figure；PDF 路径下用 `pdf_extract_figures`/`pdf_render_region`
- **输出永远放 PDF 同级目录**，不新建 Paper-Library 目录
- **HTML 生成后必须跑 Phase 5 审计**

## 参考

已完成的高质量笔记可作参考：
- `paper-library/EHR-Agent/SkillBench/` - SkillsBench 论文笔记（L2 tex 路径 POC 验证过）
- `paper-library/Virtual-Stain/MIPHEI/` - MIPHEI 论文笔记
