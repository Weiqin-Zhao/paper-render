# pdf-tools-mcp

Claude Code MCP server for PDF analysis — text extraction, formula recognition, and smart figure extraction.

## Tools

| Tool | Description |
|------|-------------|
| `pdf_info` | PDF metadata (page count, title, author, TOC) |
| `pdf_read_text` | Fast text extraction via PyMuPDF, optional table extraction |
| `pdf_read_formulas` | Formula/LaTeX recognition via Nougat OCR |
| **`pdf_extract_figures`** | **Smart figure extraction: auto-detect + cluster + crop (recommended)** |
| `pdf_detect_figures` | Detect figure regions, return metadata only (no rendering) |
| `pdf_render_region` | Render a specific rectangular region of a page |
| `pdf_render_page` | Render full page as PNG image |
| `pdf_extract_images` | Extract raw embedded image layers from PDF |

### Figure Extraction Workflow

```
pdf_extract_figures  →  One-step: auto-detect all figures, cluster, crop & save
pdf_detect_figures   →  Preview: detect regions only (no rendering), for debugging
pdf_render_region    →  Manual: specify exact crop area, for fine-tuning
```

## Install

```bash
# From local source
cd pdf-tools-mcp
pip install -e .

# With formula recognition support (GPU recommended)
pip install -e ".[nougat]"
```

## Register with Claude Code

```bash
claude mcp add pdf-tools -- pdf-tools-mcp
```

Or with uvx (no install needed):

```bash
claude mcp add pdf-tools -- uvx --from /path/to/pdf-tools-mcp pdf-tools-mcp
```

## Requirements

- Python >= 3.10
- [PyMuPDF](https://pymupdf.readthedocs.io/) >= 1.24.0
- [MCP](https://github.com/modelcontextprotocol/python-sdk) >= 1.0.0
- [Pillow](https://pillow.readthedocs.io/)
- For `pdf_read_formulas`: additional `nougat` dependencies + GPU recommended
