# Paper-render

Automated pipeline: PDF paper → beautiful HTML reading notes. Powered by Claude Code + MCP Server.

## Features

- **PDF Full-text Parsing**: Text extraction, formula recognition (Nougat OCR), figure extraction
- **Markdown Notes Generation**: Structured Chinese reading notes with formulas, figure references, and critical analysis
- **HTML Presentation Generation**: Single-file HTML with dark/light theme toggle, bilingual (CN/EN), KaTeX formula rendering, responsive sidebar navigation

## Project Structure

```
Paper-render/
├── .claude/
│   └── commands/
│       └── paper-read.md        # Claude Code skill (one-click paper notes)
├── pdf-tools-mcp/               # PDF analysis MCP Server
│   ├── pyproject.toml
│   └── src/pdf_tools_mcp/
│       └── server.py
├── templates/                   # HTML template resources
│   ├── base.css                 # Shared CSS (dark/light themes, components)
│   ├── base.js                  # Shared JS (theme toggle, language toggle, TOC, image replacement)
│   └── skeleton.html            # HTML skeleton template (available components & structure)
├── Paper-Library/               # Generated paper notes
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

## Installation

### 1. Install pdf-tools MCP Server

```bash
cd pdf-tools-mcp

# Basic install (text extraction, page rendering, image extraction)
pip install -e .

# Full install (with Nougat formula recognition, requires GPU)
pip install -e ".[nougat]"
```

### 2. Register MCP Server with Claude Code

```bash
# Option 1: Direct registration
claude mcp add pdf-tools -- pdf-tools-mcp

# Option 2: Using uvx (no install needed)
claude mcp add pdf-tools -- uvx --from /path/to/pdf-tools-mcp pdf-tools-mcp
```

Verify registration:

```bash
# List registered MCP servers
claude mcp list
```

### 3. Confirm skill availability

The skill file is located at `.claude/commands/paper-read.md`. Claude Code automatically detects commands in the project directory.

Type `/` in Claude Code to see the `paper-read` command.

## Usage

### One-click Generation (Recommended)

In Claude Code, run:

```
/paper-read /path/to/your/paper.pdf
```

Claude will automatically:
1. Read the full PDF text (batch text extraction, formula recognition)
2. Extract all important figures from the paper
3. Generate structured Markdown reading notes
4. Generate a beautiful bilingual HTML presentation page

All outputs are saved in `Paper-Library/{paper-name}/`.

### Manual MCP Tool Usage

You can also call MCP tools directly in Claude Code:

```
# View PDF info
Use pdf_info to check basic info of paper.pdf

# Extract text
Use pdf_read_text to read pages 1-10 of paper.pdf

# Formula recognition (requires nougat + GPU)
Use pdf_read_formulas to read formulas on page 3 of paper.pdf

# One-step auto-extract all figures (recommended)
Use pdf_extract_figures to extract all figures from paper.pdf to figures/ directory

# Detect figure regions (metadata only, no rendering)
Use pdf_detect_figures to detect figure positions on pages 3-8 of paper.pdf

# Manually crop a specific region
Use pdf_render_region to render region (30,60)-(565,530) on page 3 of paper.pdf

# Render full page as image
Use pdf_render_page to render page 5 of paper.pdf

# Extract embedded images (raw image layers)
Use pdf_extract_images to extract embedded images from paper.pdf
```

## MCP Server Tools

| Tool | Description | Dependency |
|------|-------------|------------|
| `pdf_info` | PDF metadata (page count, title, author, TOC) | Basic |
| `pdf_read_text` | Fast text extraction with table support | Basic |
| `pdf_read_formulas` | Formula/LaTeX recognition (Nougat OCR) | `[nougat]` + GPU |
| **`pdf_extract_figures`** | **Smart figure extraction: auto-detect + cluster + crop (recommended)** | Basic |
| `pdf_detect_figures` | Detect figure regions, return metadata (no rendering) | Basic |
| `pdf_render_region` | Render a specific rectangular region of a page (manual fine-tuning) | Basic |
| `pdf_render_page` | Render full page as PNG image | Basic |
| `pdf_extract_images` | Extract raw embedded image layers from PDF | Basic |

### Figure Extraction Workflow

Recommended workflow for figure extraction:

1. **`pdf_extract_figures`** (preferred) — One-step auto-detect and crop all figures
   - Supports both raster images and pure vector graphics (flowcharts, diagrams)
   - Auto-clusters sub-panels belonging to the same figure
   - Crop regions include axes, labels, and vector annotations
2. **`pdf_detect_figures`** — Detect only (no rendering), for preview and debugging
3. **`pdf_render_region`** — Manually specify a rectangular region, for fine-tuning inaccurate auto-crops

## HTML Presentation Features

- **Dark/Light Theme**: One-click toggle, preference saved to localStorage
- **Bilingual (CN/EN)**: All content in both Chinese and English, one-click language switch
- **KaTeX Formulas**: Inline `$...$` and display `$$...$$` math formulas
- **Responsive Sidebar Navigation**: Fixed left TOC on desktop, collapsible menu on mobile
- **Scroll Highlighting**: Current reading position auto-highlighted in TOC
- **Rich Components**: Cards, hint boxes, flowcharts, data tables, bar charts, metric highlights, collapsible discussions, etc.
- **Lazy Image Loading**: Placeholders auto-replaced with extracted paper figures
- **Single-file Deployment**: CSS/JS fully inlined, opens directly in browser

## Customizing Templates

Template files are in `templates/`:

- `base.css` — Modify theme colors, component styles
- `base.js` — Modify interaction behavior
- `skeleton.html` — View available HTML components and structural patterns

## Dependencies

- Python >= 3.10
- [PyMuPDF](https://pymupdf.readthedocs.io/) >= 1.24.0
- [MCP](https://github.com/modelcontextprotocol/python-sdk) >= 1.0.0
- [Pillow](https://pillow.readthedocs.io/)
- (Optional) [Nougat OCR](https://github.com/facebookresearch/nougat) — Formula recognition
- (Optional) CUDA GPU — Accelerate Nougat inference
