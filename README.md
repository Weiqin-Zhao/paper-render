# Paper-render

PDF 论文 → 精美 HTML 阅读笔记的自动化流水线。基于 Claude Code + MCP Server 实现。

## 功能

- **PDF 全文解析**：文本提取、公式识别 (Nougat OCR)、图表提取
- **Markdown 笔记生成**：结构化的中文论文阅读笔记，含公式、图表引用、批判性思考
- **HTML 展示页面生成**：单文件 HTML，支持暗色/亮色主题切换、中英文双语、KaTeX 公式渲染、响应式侧边导航

## 项目结构

```
Paper-render/
├── .claude/
│   └── commands/
│       └── paper-read.md        # Claude Code skill（一键生成论文笔记）
├── pdf-tools-mcp/               # PDF 解析 MCP Server
│   ├── pyproject.toml
│   └── src/pdf_tools_mcp/
│       └── server.py
├── templates/                   # HTML 模板资源
│   ├── base.css                 # 共用 CSS 样式（暗色/亮色主题、组件样式）
│   ├── base.js                  # 共用 JS（主题切换、语言切换、TOC 导航、图片替换）
│   └── skeleton.html            # HTML 骨架模板（展示可用组件和结构）
├── Paper-Library/               # 已生成的论文笔记
│   ├── LPFM/
│   │   ├── LPFM.pdf
│   │   ├── LPFM_notes.md
│   │   ├── LPFM_presentation.html
│   │   └── figures/
│   └── PixCell/
│       ├── PixCell.pdf
│       ├── PixCell_notes.md
│       ├── PixCell_presentation.html
│       └── figures/
└── README.md
```

## 安装

### 1. 安装 pdf-tools MCP Server

```bash
cd pdf-tools-mcp

# 基础安装（文本提取、页面渲染、图片提取）
pip install -e .

# 完整安装（含 Nougat 公式识别，需要 GPU）
pip install -e ".[nougat]"
```

### 2. 注册 MCP Server 到 Claude Code

```bash
# 方式 1: 直接注册
claude mcp add pdf-tools -- pdf-tools-mcp

# 方式 2: 使用 uvx（无需安装）
claude mcp add pdf-tools -- uvx --from /path/to/pdf-tools-mcp pdf-tools-mcp
```

注册后可以在 Claude Code 中验证：

```bash
# 查看已注册的 MCP servers
claude mcp list
```

### 3. 确认 skill 可用

skill 文件位于 `.claude/commands/paper-read.md`，Claude Code 会自动识别项目目录下的 commands。

在 Claude Code 中输入 `/` 即可看到 `paper-read` 命令。

## 使用方法

### 一键生成（推荐）

在 Claude Code 中运行：

```
/paper-read /path/to/your/paper.pdf
```

Claude 会自动完成：
1. 读取 PDF 全文（分批提取文本、识别公式）
2. 提取论文中的所有重要图表
3. 生成结构化的 Markdown 阅读笔记
4. 生成精美的 HTML 双语展示页面

所有输出保存在 `Paper-Library/{论文名}/` 目录下。

### 手动使用 MCP 工具

也可以直接在 Claude Code 对话中调用 MCP 工具：

```
# 查看 PDF 信息
使用 pdf_info 查看 paper.pdf 的基本信息

# 提取文本
使用 pdf_read_text 读取 paper.pdf 第 1-10 页

# 公式识别（需要 nougat 依赖和 GPU）
使用 pdf_read_formulas 读取 paper.pdf 第 3 页的公式

# 一步自动提取所有 figure（推荐）
使用 pdf_extract_figures 从 paper.pdf 提取所有图表到 figures/ 目录

# 检测 figure 区域（仅元数据，不渲染）
使用 pdf_detect_figures 检测 paper.pdf 第 3-8 页的 figure 位置

# 手动裁剪指定区域
使用 pdf_render_region 渲染 paper.pdf 第 3 页的 (30,60)-(565,530) 区域

# 渲染整页为图片
使用 pdf_render_page 渲染 paper.pdf 第 5 页

# 提取嵌入图片（原始图层）
使用 pdf_extract_images 从 paper.pdf 提取嵌入图片
```

## MCP Server 工具说明

| 工具 | 功能 | 依赖 |
|------|------|------|
| `pdf_info` | PDF 元数据（页数、标题、作者、目录） | 基础 |
| `pdf_read_text` | 快速文本提取，支持表格 | 基础 |
| `pdf_read_formulas` | 公式/LaTeX 识别 (Nougat OCR) | `[nougat]` + GPU |
| **`pdf_extract_figures`** | **智能 figure 提取：自动检测+聚类+裁剪（推荐）** | 基础 |
| `pdf_detect_figures` | 检测 figure 区域，返回元数据（不渲染） | 基础 |
| `pdf_render_region` | 渲染页面指定矩形区域（手动精调） | 基础 |
| `pdf_render_page` | 渲染整页为 PNG 图片 | 基础 |
| `pdf_extract_images` | 提取 PDF 嵌入的原始图片图层 | 基础 |

### Figure 提取工具链

推荐的 figure 提取工作流：

1. **`pdf_extract_figures`**（首选）— 一步到位，自动检测所有 figure 并裁剪保存
   - 支持光栅图（嵌入图片）和纯矢量图（流程图、示意图）
   - 自动聚类同一 figure 的多个子面板
   - 裁剪区域包含坐标轴、标签等矢量标注
2. **`pdf_detect_figures`** — 仅检测不渲染，用于预览和调试
3. **`pdf_render_region`** — 手动指定矩形区域，用于微调不准确的自动裁剪

## HTML 展示页面特性

- **暗色/亮色主题**：右上角一键切换，偏好自动保存到 localStorage
- **中英文双语**：所有内容同时提供中英文，一键切换语言
- **KaTeX 公式**：支持行内 `$...$` 和行间 `$$...$$` 数学公式
- **响应式侧边导航**：桌面端固定左侧 TOC，移动端折叠菜单
- **滚动高亮**：当前阅读位置在 TOC 中自动高亮
- **丰富组件**：卡片、提示框、流程图、数据表格、条形图、指标高亮、可折叠讨论等
- **图片懒加载**：占位符自动替换为提取的论文图表
- **单文件部署**：CSS/JS 全部内联，可直接在浏览器中打开

## 自定义模板

模板文件位于 `templates/` 目录：

- `base.css` — 修改主题颜色、组件样式
- `base.js` — 修改交互行为
- `skeleton.html` — 查看可用的 HTML 组件和结构模式

## 依赖

- Python >= 3.10
- [PyMuPDF](https://pymupdf.readthedocs.io/) >= 1.24.0
- [MCP](https://github.com/modelcontextprotocol/python-sdk) >= 1.0.0
- [Pillow](https://pillow.readthedocs.io/)
- (可选) [Nougat OCR](https://github.com/facebookresearch/nougat) — 公式识别
- (可选) CUDA GPU — 加速 Nougat 推理
