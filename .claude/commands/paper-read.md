# Paper-to-HTML 自动化论文阅读笔记生成

你是一个论文阅读助手。给定一篇 PDF 论文，你需要完成以下完整流程：
1. 读取 PDF 全文内容和图表
2. 生成详细的中文 Markdown 阅读笔记
3. 生成精美的双语 HTML 展示页面（含嵌入图表）

## 输入

PDF 文件路径: $ARGUMENTS

## 执行流程

### Phase 1: PDF 读取与理解

1. **获取 PDF 基本信息**
   - 使用 `mcp__pdf-tools__pdf_info` 获取页数、标题、作者等元数据
   - 记录总页数 `N`

2. **提取全文文本**
   - 使用 `mcp__pdf-tools__pdf_read_text` 分批读取（每次最多 15 页）
   - 按 `1-15`, `16-30`, ... 的顺序读完全部页面
   - 如果文本中包含大量公式，对关键公式页使用 `mcp__pdf-tools__pdf_read_formulas` 补充识别

3. **提取论文图表**（使用智能 figure 提取工具链）

   **首选方案**：一步到位自动提取
   - 使用 `mcp__pdf-tools__pdf_extract_figures` 自动检测并提取所有 figure
     - 设置 `output_dir` 为 `figures/` 子目录，`page_range` 为包含图表的页面范围
     - 该工具同时支持光栅图和纯矢量图（如流程图、示意图等）
     - 自动聚类同一 figure 的多个面板，按区域裁剪（包含坐标轴、标签等矢量标注）

   **质量检查与补救**：
   - 查看检测结果，如果某个 figure 裁剪不完整（例如上方的矢量部分被截断），使用 `mcp__pdf-tools__pdf_render_region` 手动指定精确的裁剪区域
   - 如果需要提取 figure 的某个子面板（如 Fig. 1e），同样使用 `pdf_render_region` 指定子区域
   - `mcp__pdf-tools__pdf_detect_figures` 可单独调用来预览检测结果（不渲染图片），用于调试

   **最终文件命名**: `figures/figN_descriptive_name.png`

### Phase 2: 生成 Markdown 阅读笔记

生成 `{PAPER_NAME}_notes.md`，内容要求：

**结构模板**（参考 Paper-Library/ 中已有的笔记）：

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
- **公式**: 使用 LaTeX 格式，关键公式需要逐项解释
- **图表引用**: 在相关位置标注 `> **[Figure X: 标题]**` 和 Caption
- **批判性思考**: 在讨论部分指出论文的 strength 和 weakness
- **对比分析**: 与相关工作的关键区别用表格对比
- **实现细节**: 记录训练配置、数据规模、计算资源等可复现的信息

### Phase 3: 生成 HTML 展示页面

生成 `{PAPER_NAME}_presentation.html`，这是一个独立的单文件 HTML 页面。

**步骤**：

1. **读取模板文件**
   - 读取 `templates/base.css` 获取完整 CSS 样式
   - 读取 `templates/base.js` 获取共用 JS 代码
   - 读取 `templates/skeleton.html` 了解 HTML 结构模式

2. **生成 HTML**
   - 将 `base.css` 内联到 `<style>` 标签中
   - 将 `base.js` 内联到 `</body>` 前的 `<script>` 标签中
   - 在 `base.js` 之前定义该论文的 `imageMap` 对象

3. **HTML 内容要求**

   **双语支持**（必须）：
   - 所有文本内容同时提供中文和英文版本
   - 块级元素使用 `lang-zh` / `lang-en` 属性
   - TOC 中使用 `<span class="zh">` / `<span class="en">`
   - 默认显示中文，可通过右上角按钮切换

   **内容组织**：
   - Hero header: 论文标题、作者、一句话总结、关键词标签
   - TOC sidebar: 左侧固定导航，支持 section 和 subsection
   - 按论文结构组织 sections，每个 section 使用 `.fade-in` 动画
   - 图表使用 `.img-placeholder` 占位符，通过 JS `imageMap` 替换为真实图片

   **丰富的可视化组件**（根据内容选择使用）：
   - `.card` / `.card-accent`: 重要内容卡片
   - `.box-insight` / `.box-warn` / `.box-note` / `.box-key`: 彩色提示框
   - `.table-wrap > table`: 数据表格
   - `.flow > .flow-row > .flow-box`: 流程图
   - `.metrics-row > .metric-card`: 关键数字高亮
   - `.compare-grid > .compare-card`: 对比卡片
   - `.chart-container > .bar-chart`: 水平条形图
   - `.discussion-card` (details open / summary): 讨论项（默认展开，使用 `<details class="discussion-card" open>`）
   - `.formula`: 公式/代码块
   - `.two-col`: 双列布局

   **数学公式**：使用 KaTeX 语法（`$...$` 行内，`$$...$$` 行间）

### Phase 4: 输出文件组织

所有输出放在 `Paper-Library/{PAPER_NAME}/` 目录下：

```
Paper-Library/{PAPER_NAME}/
├── {PAPER_NAME}.pdf          (原始 PDF，如果不在此处则复制过来)
├── {PAPER_NAME}_notes.md     (Markdown 阅读笔记)
├── {PAPER_NAME}_presentation.html  (HTML 展示页面)
└── figures/                   (提取的论文图表)
    ├── fig1_xxx.png
    ├── fig2_xxx.png
    └── ...
```

`PAPER_NAME` 从论文标题中提取一个简短的标识名（如 "LPFM", "PixCell", "UNI"）。

## 重要提示

- **图片提取是关键**：尽可能提取论文中所有重要的 Figure。每个 Figure 对应一个 `.img-placeholder` 和 `imageMap` 条目
- **优先使用 `pdf_extract_figures`** 进行自动提取，然后用 `pdf_render_region` 微调不准确的裁剪
- **HTML 必须是单文件**：CSS 和 JS 全部内联，不依赖外部文件（KaTeX CDN 除外）
- **内容质量 > 覆盖面**：如果论文太长，优先保证方法和实验部分的深度，可以适当精简背景介绍
- **保持批判性**：讨论部分不只是总结，要提出有深度的问题和思考
- **不要使用整页截图**：绝不使用 `pdf_render_page` 提取 figure — 应使用 `pdf_extract_figures`（自动）或 `pdf_render_region`（手动区域）
- HTML 中的公式确保 KaTeX 能正确渲染（注意转义 `&`, `<`, `>` 等 HTML 特殊字符）

## 参考

现有论文笔记可作为质量参考：
- `Paper-Library/LPFM/` - LPFM 论文笔记
- `Paper-Library/PixCell/` - PixCell 论文笔记
