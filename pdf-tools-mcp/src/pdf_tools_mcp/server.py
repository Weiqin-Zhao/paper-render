"""PDF Tools MCP Server.

Exposes layered PDF parsing tools via MCP protocol:
- Fast text extraction (PyMuPDF)
- Formula recognition (Nougat OCR)
- Page rendering, region cropping, and image extraction
- Automatic figure detection and extraction
"""

import io
import logging
import re
import sys
import base64
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Logging → stderr (stdio transport requirement)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("pdf-tools")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_MB = 200
MAX_TEXT_PAGES = 50
MAX_NOUGAT_PAGES = 20

# ---------------------------------------------------------------------------
# Nougat lazy loader
# ---------------------------------------------------------------------------
_nougat_model = None
_nougat_processor = None


def _load_nougat():
    """Lazily load Nougat model on first call to pdf_read_formulas."""
    global _nougat_model, _nougat_processor
    if _nougat_model is not None:
        return _nougat_model, _nougat_processor

    logger.info("Loading Nougat model (first call, may take ~30s) ...")
    try:
        import torch
        from huggingface_hub import snapshot_download
        from nougat import NougatModel
        from nougat.utils.device import move_to_device
    except ImportError as e:
        raise RuntimeError(
            "Nougat dependencies not installed. "
            "Install with: pip install pdf-tools-mcp[nougat]"
        ) from e

    # Use local cached path so BARTDecoder can find tokenizer.json
    local_path = snapshot_download("facebook/nougat-base")
    model = NougatModel.from_pretrained(local_path)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = move_to_device(model, device)
    model.eval()

    _nougat_model = model
    _nougat_processor = model  # NougatModel has its own encoder
    logger.info("Nougat model loaded on %s", device)
    return _nougat_model, _nougat_processor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _validate_pdf(file_path: str) -> fitz.Document:
    """Validate and open a PDF file.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Opened fitz.Document.

    Raises:
        ValueError: If file is invalid or too large.
    """
    p = Path(file_path).expanduser().resolve()
    if not p.exists():
        raise ValueError(f"File not found: {p}")
    if not p.suffix.lower() == ".pdf":
        raise ValueError(f"Not a PDF file: {p}")
    size_mb = p.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB limit")
    return fitz.open(str(p))


def _parse_page_range(page_range: Optional[str], total_pages: int) -> list[int]:
    """Parse page range string into list of 0-indexed page numbers.

    Args:
        page_range: e.g. "1-5", "1,3,5", "1-3,7,10-12", or None for all.
        total_pages: Total number of pages in the document.

    Returns:
        Sorted list of 0-indexed page numbers.
    """
    if not page_range:
        return list(range(total_pages))

    pages: set[int] = set()
    for part in page_range.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start_idx = max(0, int(start) - 1)
            end_idx = min(total_pages, int(end))
            pages.update(range(start_idx, end_idx))
        else:
            idx = int(part) - 1
            if 0 <= idx < total_pages:
                pages.add(idx)
    return sorted(pages)


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "pdf-tools",
    instructions=(
        "PDF analysis tools: use pdf_info for metadata, "
        "pdf_read_text for fast text extraction, "
        "pdf_read_formulas for math/LaTeX recognition, "
        "pdf_render_page to view a page as image, "
        "pdf_extract_images to get embedded figures. "
        "For precise figure extraction: pdf_detect_figures finds figure regions, "
        "pdf_render_region crops a specific page area, "
        "pdf_extract_figures auto-detects and saves all figures to disk."
    ),
)


@mcp.tool()
def pdf_info(file_path: str) -> str:
    """Get PDF metadata: page count, title, author, file size, etc.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Formatted metadata string.
    """
    p = Path(file_path).expanduser().resolve()
    doc = _validate_pdf(str(p))
    try:
        meta = doc.metadata or {}
        size_mb = p.stat().st_size / (1024 * 1024)

        lines = [
            f"File: {p.name}",
            f"Size: {size_mb:.2f} MB",
            f"Pages: {doc.page_count}",
            f"Title: {meta.get('title', 'N/A')}",
            f"Author: {meta.get('author', 'N/A')}",
            f"Subject: {meta.get('subject', 'N/A')}",
            f"Creator: {meta.get('creator', 'N/A')}",
            f"Producer: {meta.get('producer', 'N/A')}",
            f"CreationDate: {meta.get('creationDate', 'N/A')}",
        ]

        # Table of contents (first 20 entries)
        toc = doc.get_toc()
        if toc:
            lines.append(f"\nTable of Contents ({len(toc)} entries):")
            for level, title, page in toc[:20]:
                indent = "  " * (level - 1)
                lines.append(f"  {indent}{title} ... p.{page}")
            if len(toc) > 20:
                lines.append(f"  ... and {len(toc) - 20} more entries")

        return "\n".join(lines)
    finally:
        doc.close()


@mcp.tool()
def pdf_read_text(
    file_path: str,
    page_range: Optional[str] = None,
    extract_tables: bool = False,
) -> str:
    """Extract text from PDF pages using PyMuPDF (fast).

    Args:
        file_path: Absolute path to the PDF file.
        page_range: Pages to extract, e.g. "1-5", "1,3,7-10". Default: all pages.
        extract_tables: If True, also attempt to extract tables in markdown format.

    Returns:
        Extracted text with page markers.
    """
    doc = _validate_pdf(file_path)
    try:
        pages = _parse_page_range(page_range, doc.page_count)
        if len(pages) > MAX_TEXT_PAGES:
            return (
                f"Error: Requested {len(pages)} pages, max is {MAX_TEXT_PAGES}. "
                f"Use page_range to specify a subset."
            )

        output_parts: list[str] = []
        for page_num in pages:
            page = doc[page_num]
            header = f"--- Page {page_num + 1}/{doc.page_count} ---"

            text = page.get_text("text")

            if extract_tables:
                try:
                    tables = page.find_tables()
                    if tables.tables:
                        table_parts: list[str] = []
                        for i, table in enumerate(tables.tables):
                            df = table.to_pandas()
                            table_parts.append(f"\n[Table {i + 1}]\n{df.to_markdown(index=False)}")
                        text += "\n" + "\n".join(table_parts)
                except Exception as e:
                    text += f"\n[Table extraction failed: {e}]"

            output_parts.append(f"{header}\n{text.strip()}")

        return "\n\n".join(output_parts)
    finally:
        doc.close()


@mcp.tool()
def pdf_read_formulas(
    file_path: str,
    page_range: Optional[str] = None,
) -> str:
    """Recognize formulas and structured content using Nougat OCR.

    Outputs Markdown with LaTeX math. Slower than pdf_read_text but
    handles formulas, equations, and complex layouts.

    Args:
        file_path: Absolute path to the PDF file.
        page_range: Pages to process, e.g. "1-5". Default: all pages (max 20).

    Returns:
        Markdown text with LaTeX formulas.
    """
    try:
        import torch
        from PIL import Image
    except ImportError:
        return "Error: Nougat dependencies not installed. Run: pip install pdf-tools-mcp[nougat]"

    doc = _validate_pdf(file_path)
    try:
        pages = _parse_page_range(page_range, doc.page_count)
        if len(pages) > MAX_NOUGAT_PAGES:
            return (
                f"Error: Requested {len(pages)} pages, max for Nougat is {MAX_NOUGAT_PAGES}. "
                f"Use page_range to specify a subset."
            )

        model, _ = _load_nougat()

        output_parts: list[str] = []
        for page_num in pages:
            page = doc[page_num]
            # Render page at 300 DPI for Nougat
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data)).convert("RGB")

            # Nougat expects its own preprocessing
            from nougat.utils.dataset import ImageDataset

            sample = ImageDataset.ignore_none_collate(
                [{"image": model.encoder.prepare_input(img), "meta": {"page": page_num}}]
            )
            if sample is None:
                output_parts.append(f"--- Page {page_num + 1} ---\n[Failed to preprocess page]")
                continue

            device = next(model.parameters()).device
            model_input = sample["image"].to(device)

            with torch.no_grad():
                output = model.inference(image_tensors=model_input)

            page_text = output["predictions"][0] if output["predictions"] else "[No output]"

            output_parts.append(f"--- Page {page_num + 1}/{doc.page_count} ---\n{page_text}")
            logger.info("Nougat processed page %d", page_num + 1)

        return "\n\n".join(output_parts)
    finally:
        doc.close()


@mcp.tool()
def pdf_render_page(
    file_path: str,
    page_number: int = 1,
    dpi: int = 150,
) -> str:
    """Render a PDF page as a PNG image (base64 encoded).

    Args:
        file_path: Absolute path to the PDF file.
        page_number: 1-indexed page number to render.
        dpi: Resolution (default 150, max 300).

    Returns:
        Base64-encoded PNG image data with metadata.
    """
    doc = _validate_pdf(file_path)
    try:
        dpi = min(dpi, 300)
        page_idx = page_number - 1
        if page_idx < 0 or page_idx >= doc.page_count:
            return f"Error: Page {page_number} out of range (1-{doc.page_count})"

        page = doc[page_idx]
        pix = page.get_pixmap(dpi=dpi)

        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode("ascii")

        return (
            f"Page {page_number}/{doc.page_count} rendered at {dpi} DPI "
            f"({pix.width}x{pix.height})\n"
            f"data:image/png;base64,{b64}"
        )
    finally:
        doc.close()


@mcp.tool()
def pdf_extract_images(
    file_path: str,
    page_range: Optional[str] = None,
    min_size: int = 100,
) -> str:
    """Extract embedded images/figures from PDF pages.

    Args:
        file_path: Absolute path to the PDF file.
        page_range: Pages to extract from, e.g. "1-5". Default: all pages.
        min_size: Minimum image dimension in pixels (filters tiny icons).

    Returns:
        Summary of extracted images with base64-encoded data.
    """
    doc = _validate_pdf(file_path)
    try:
        pages = _parse_page_range(page_range, doc.page_count)
        results: list[str] = []
        total_images = 0

        for page_num in pages:
            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img_idx, img_info in enumerate(image_list):
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    if base_image is None:
                        continue

                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)
                    if width < min_size or height < min_size:
                        continue

                    ext = base_image.get("ext", "png")
                    img_bytes = base_image.get("image", b"")
                    b64 = base64.b64encode(img_bytes).decode("ascii")
                    total_images += 1

                    results.append(
                        f"[Image {total_images}] Page {page_num + 1}, "
                        f"{width}x{height} ({ext})\n"
                        f"data:image/{ext};base64,{b64}"
                    )
                except Exception as e:
                    logger.warning("Failed to extract image xref=%d: %s", xref, e)

        header = f"Found {total_images} images (min_size={min_size}px)"
        if not results:
            return f"{header}\nNo images found matching criteria."
        return f"{header}\n\n" + "\n\n".join(results)
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Figure detection helpers
# ---------------------------------------------------------------------------
def _bboxes_close(bbox1: tuple, bbox2: tuple, threshold: float) -> bool:
    """Check if two bounding boxes are within threshold distance.

    Args:
        bbox1: (x0, y0, x1, y1) first bounding box.
        bbox2: (x0, y0, x1, y1) second bounding box.
        threshold: Maximum gap in points to consider "close".

    Returns:
        True if expanded bboxes overlap.
    """
    x0_1, y0_1, x1_1, y1_1 = bbox1
    x0_2, y0_2, x1_2, y1_2 = bbox2
    return not (
        x1_1 + threshold < x0_2
        or x1_2 + threshold < x0_1
        or y1_1 + threshold < y0_2
        or y1_2 + threshold < y0_1
    )


def _cluster_images(
    infos: list[dict], gap_threshold: float = 40.0
) -> list[list[dict]]:
    """Cluster images by spatial proximity using union-find.

    Args:
        infos: List of image info dicts (must have 'bbox' key).
        gap_threshold: Max gap in points between images in same cluster.

    Returns:
        List of clusters, each cluster is a list of image info dicts.
    """
    n = len(infos)
    if n == 0:
        return []

    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i + 1, n):
            if _bboxes_close(
                tuple(infos[i]["bbox"]), tuple(infos[j]["bbox"]), gap_threshold
            ):
                union(i, j)

    clusters: dict[int, list[dict]] = {}
    for i in range(n):
        root = find(i)
        clusters.setdefault(root, []).append(infos[i])

    return list(clusters.values())


def _cluster_bbox(cluster: list[dict]) -> tuple[float, float, float, float]:
    """Compute the union bounding box of a cluster of images.

    Args:
        cluster: List of image info dicts with 'bbox' key.

    Returns:
        (x0, y0, x1, y1) union bounding box.
    """
    x0 = min(img["bbox"][0] for img in cluster)
    y0 = min(img["bbox"][1] for img in cluster)
    x1 = max(img["bbox"][2] for img in cluster)
    y1 = max(img["bbox"][3] for img in cluster)
    return (x0, y0, x1, y1)


def _find_figure_label(
    page: fitz.Page, bbox: tuple[float, float, float, float]
) -> Optional[str]:
    """Search for figure label text near a cluster bounding box.

    Looks below and above the figure region for "Fig." / "Figure" patterns.
    Uses full page width for robust caption detection.

    Args:
        page: PyMuPDF page object.
        bbox: (x0, y0, x1, y1) figure bounding box.

    Returns:
        Matched label string or None.
    """
    page_rect = page.rect
    pattern = re.compile(
        r"(?:Extended\s+Data\s+)?Fig(?:ure|\.)\s*\d+", re.IGNORECASE
    )
    # Search full-width below the figure (caption often spans full column)
    for dy in [80, 150]:
        below = fitz.Rect(0, bbox[3], page_rect.width, bbox[3] + dy)
        below = below & page_rect
        if not below.is_empty:
            text = page.get_text("text", clip=below)
            match = pattern.search(text)
            if match:
                return match.group(0).strip()
    # Search above
    above = fitz.Rect(0, bbox[1] - 60, page_rect.width, bbox[1])
    above = above & page_rect
    if not above.is_empty:
        text = page.get_text("text", clip=above)
        match = pattern.search(text)
        if match:
            return match.group(0).strip()
    return None


def _find_all_captions(
    page: fitz.Page,
) -> list[dict]:
    """Find actual figure captions on a page using text search.

    Uses page.search_for() for precise positioning, avoiding false
    positives from inline text references like "see Fig. 3".
    Searches for patterns: "Fig. N |", "Figure N.", "Figure N:".

    Args:
        page: PyMuPDF page object.

    Returns:
        List of dicts with 'label', 'bbox' keys, sorted by Y position.
    """
    captions: list[dict] = []
    seen_labels: set[str] = set()

    # Search patterns: (search_template, label_template)
    # Nature style uses "Fig. N |", others use "Figure N." etc.
    patterns = [
        ("Fig. {} |", "Fig. {}"),
        ("Figure {} |", "Figure {}"),
        ("Figure {}.", "Figure {}"),
        ("Figure {}:", "Figure {}"),
    ]
    # Also check Extended Data figures
    ext_patterns = [
        ("Extended Data Fig. {} |", "Extended Data Fig. {}"),
        ("Extended Data Figure {} |", "Extended Data Figure {}"),
    ]

    for fig_num in range(1, 30):
        for search_tmpl, label_tmpl in patterns + ext_patterns:
            query = search_tmpl.format(fig_num)
            rects = page.search_for(query)
            if rects:
                label = label_tmpl.format(fig_num)
                if label not in seen_labels:
                    seen_labels.add(label)
                    # Use the first occurrence
                    r = rects[0]
                    captions.append(
                        {
                            "label": label,
                            "bbox": (r.x0, r.y0, r.x1, r.y1),
                        }
                    )
                break  # Found this fig_num, try next number

    # Sort by Y position (top to bottom)
    captions.sort(key=lambda c: c["bbox"][1])
    return captions


def _detect_page_figures(
    page: fitz.Page,
    min_size: int = 100,
    gap_threshold: float = 60.0,
) -> list[dict]:
    """Detect all figures on a page (both image-based and vector-based).

    Strategy:
    1. Find image clusters (embedded raster images).
    2. Find all "Fig. N" captions via precise text search.
    3. Match captions to nearest cluster above (generous distance).
    4. Unmatched captions → vector-only figures (estimate region).
    5. Unmatched clusters → unlabeled figures.

    Args:
        page: PyMuPDF page object.
        min_size: Minimum image dimension in pixels.
        gap_threshold: Max gap for clustering images (default 60pt).

    Returns:
        List of figure dicts with 'type', 'label', 'bbox', 'num_images'.
    """
    page_rect = page.rect

    # Step 1: Image clusters
    infos = page.get_image_info(xrefs=True)
    infos = [
        i for i in infos if i["width"] >= min_size and i["height"] >= min_size
    ]
    clusters = _cluster_images(infos, gap_threshold) if infos else []

    # Step 2: All captions (precise positions via search_for)
    captions = _find_all_captions(page)

    # Step 3: Match captions to clusters
    figures: list[dict] = []
    used_clusters: set[int] = set()

    for caption in captions:
        cap_y = caption["bbox"][1]

        # Find nearest cluster whose bottom edge is ABOVE the caption
        best_idx: Optional[int] = None
        best_dist = float("inf")
        for idx, cluster in enumerate(clusters):
            if idx in used_clusters:
                continue
            cluster_bottom = max(img["bbox"][3] for img in cluster)
            if cluster_bottom <= cap_y + 30:
                dist = cap_y - cluster_bottom
                if dist < best_dist:
                    best_dist = dist
                    best_idx = idx

        # Generous threshold: captions can be far below figures in
        # journal layouts (Nature, Science) with text between them
        if best_idx is not None and best_dist < 500:
            # Image-based figure: cluster region down to caption
            cluster = clusters[best_idx]
            used_clusters.add(best_idx)
            cbbox = _cluster_bbox(cluster)
            # Figure spans from cluster top to below caption
            # Estimate caption block height ~60pt for multi-line captions
            fig_bbox = (
                min(cbbox[0], page_rect.x0 + 30),
                cbbox[1],
                max(cbbox[2], page_rect.x1 - 30),
                min(cap_y + 70, page_rect.y1),
            )
            figures.append(
                {
                    "type": "image",
                    "label": caption["label"],
                    "bbox": fig_bbox,
                    "num_images": len(cluster),
                }
            )
        else:
            # Vector-based figure: estimate region above caption
            # Look for page margin / column boundaries
            margin_x = 35.0
            # Figure top: use page top margin or halfway up the page
            # as a reasonable estimate for figure start
            fig_top = max(page_rect.y0 + 20, cap_y - 380)
            fig_bbox = (
                page_rect.x0 + margin_x,
                fig_top,
                page_rect.x1 - margin_x,
                min(cap_y + 70, page_rect.y1),
            )
            figures.append(
                {
                    "type": "vector",
                    "label": caption["label"],
                    "bbox": fig_bbox,
                    "num_images": 0,
                }
            )

    # Step 4: Remaining unmatched clusters
    for idx, cluster in enumerate(clusters):
        if idx not in used_clusters:
            cbbox = _cluster_bbox(cluster)
            label = _find_figure_label(page, cbbox)
            figures.append(
                {
                    "type": "image",
                    "label": label,
                    "bbox": cbbox,
                    "num_images": len(cluster),
                }
            )

    # Sort by vertical position
    figures.sort(key=lambda f: f["bbox"][1])
    return figures


# ---------------------------------------------------------------------------
# New tools: figure detection, region rendering, auto-extraction
# ---------------------------------------------------------------------------
@mcp.tool()
def pdf_detect_figures(
    file_path: str,
    page_range: Optional[str] = None,
    min_size: int = 100,
    gap_threshold: float = 60.0,
) -> str:
    """Detect figure regions on PDF pages.

    Handles both image-based figures (raster) and vector-only figures
    by combining image clustering with caption text detection.
    Returns metadata only (no image data) — lightweight and fast.
    Use pdf_render_region to render individual detected figures.

    Args:
        file_path: Absolute path to the PDF file.
        page_range: Pages to scan, e.g. "1-10". Default: all pages.
        min_size: Minimum image dimension in pixels (filters icons).
        gap_threshold: Max gap in points between images in same figure.

    Returns:
        Text listing detected figure regions with page, type, bbox, label.
    """
    doc = _validate_pdf(file_path)
    try:
        pages = _parse_page_range(page_range, doc.page_count)
        all_figures: list[str] = []
        fig_count = 0

        for page_num in pages:
            page = doc[page_num]
            page_figs = _detect_page_figures(page, min_size, gap_threshold)

            for fig in page_figs:
                fig_count += 1
                bbox = fig["bbox"]
                label_str = fig["label"] if fig["label"] else "unlabeled"
                fig_type = fig["type"]

                all_figures.append(
                    f"[Figure {fig_count}] Page {page_num + 1}, "
                    f"type={fig_type}, "
                    f"label=\"{label_str}\", "
                    f"images={fig['num_images']}, "
                    f"bbox=({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f})"
                )

        header = f"Detected {fig_count} figure regions"
        if not all_figures:
            return f"{header}\nNo figure regions found."
        return f"{header}\n\n" + "\n".join(all_figures)
    finally:
        doc.close()


@mcp.tool()
def pdf_render_region(
    file_path: str,
    page_number: int,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    dpi: int = 200,
    padding: float = 10.0,
    save_path: Optional[str] = None,
) -> str:
    """Render a specific rectangular region of a PDF page as PNG.

    Coordinates are in PDF points (72 points = 1 inch).
    Includes both raster images AND vector graphics (axes, labels, arrows).

    Args:
        file_path: Absolute path to the PDF file.
        page_number: 1-indexed page number.
        x0: Left edge of region in points.
        y0: Top edge of region in points.
        x1: Right edge of region in points.
        y1: Bottom edge of region in points.
        dpi: Resolution (default 200, max 300).
        padding: Extra padding in points around the region.
        save_path: If provided, save PNG to this path instead of returning base64.

    Returns:
        If save_path: confirmation message with file path and size.
        Otherwise: base64-encoded PNG with metadata.
    """
    doc = _validate_pdf(file_path)
    try:
        dpi = min(dpi, 300)
        page_idx = page_number - 1
        if page_idx < 0 or page_idx >= doc.page_count:
            return f"Error: Page {page_number} out of range (1-{doc.page_count})"

        page = doc[page_idx]
        clip = fitz.Rect(
            x0 - padding, y0 - padding, x1 + padding, y1 + padding
        )
        clip = clip & page.rect  # Intersect with page boundaries

        if clip.is_empty:
            return "Error: Specified region is outside page boundaries."

        pix = page.get_pixmap(dpi=dpi, clip=clip)

        if save_path:
            save_p = Path(save_path).expanduser().resolve()
            save_p.parent.mkdir(parents=True, exist_ok=True)
            pix.save(str(save_p))
            size_kb = save_p.stat().st_size / 1024
            return (
                f"Saved: {save_p}\n"
                f"Size: {size_kb:.1f} KB ({pix.width}x{pix.height} at {dpi} DPI)"
            )

        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode("ascii")
        return (
            f"Region ({x0:.1f},{y0:.1f})-({x1:.1f},{y1:.1f}) "
            f"page {page_number}, {dpi} DPI ({pix.width}x{pix.height})\n"
            f"data:image/png;base64,{b64}"
        )
    finally:
        doc.close()


@mcp.tool()
def pdf_extract_figures(
    file_path: str,
    page_range: Optional[str] = None,
    output_dir: Optional[str] = None,
    dpi: int = 200,
    min_size: int = 100,
    gap_threshold: float = 60.0,
    padding: float = 15.0,
) -> str:
    """Auto-detect and extract all figures from PDF pages.

    Combines figure detection (image clustering + caption matching)
    with region rendering. Handles both raster and vector-only figures.
    Each figure is rendered as a cropped page region that includes
    both raster images AND vector graphics (axes, labels, arrows).

    Args:
        file_path: Absolute path to the PDF file.
        page_range: Pages to scan, e.g. "3-8". Default: all pages.
        output_dir: Directory to save PNGs. If None, returns base64 data.
        dpi: Resolution for rendering (default 200, max 300).
        min_size: Minimum image dimension to consider (filters icons).
        gap_threshold: Max gap in points to cluster images together.
        padding: Extra padding around figure region in points.

    Returns:
        Summary of extracted figures. If output_dir is set, files are saved
        to disk and paths are returned instead of base64 data.
    """
    doc = _validate_pdf(file_path)
    try:
        dpi = min(dpi, 300)
        pages = _parse_page_range(page_range, doc.page_count)
        results: list[str] = []
        fig_count = 0

        if output_dir:
            out_path = Path(output_dir).expanduser().resolve()
            out_path.mkdir(parents=True, exist_ok=True)

        for page_num in pages:
            page = doc[page_num]
            page_figs = _detect_page_figures(page, min_size, gap_threshold)

            for fig in page_figs:
                fig_count += 1
                bbox = fig["bbox"]
                label_str = fig["label"] if fig["label"] else f"figure_{fig_count}"
                fig_type = fig["type"]

                # Build clip rect with padding
                clip = fitz.Rect(
                    bbox[0] - padding,
                    bbox[1] - padding,
                    bbox[2] + padding,
                    bbox[3] + padding,
                )
                clip = clip & page.rect

                if clip.is_empty:
                    continue

                pix = page.get_pixmap(dpi=dpi, clip=clip)

                # Generate clean filename from label
                safe_name = re.sub(
                    r"[^a-zA-Z0-9]+", "_", label_str
                ).strip("_").lower()
                fname = f"fig{fig_count}_{safe_name}.png"

                meta = (
                    f"[Figure {fig_count}] Page {page_num + 1}, "
                    f"type={fig_type}, "
                    f"label=\"{label_str}\", "
                    f"images={fig['num_images']}, "
                    f"bbox=({bbox[0]:.1f}, {bbox[1]:.1f}, "
                    f"{bbox[2]:.1f}, {bbox[3]:.1f}), "
                    f"render={pix.width}x{pix.height}"
                )

                if output_dir:
                    save_file = out_path / fname
                    pix.save(str(save_file))
                    size_kb = save_file.stat().st_size / 1024
                    results.append(
                        f"{meta}\n  -> {save_file} ({size_kb:.1f} KB)"
                    )
                else:
                    img_bytes = pix.tobytes("png")
                    b64 = base64.b64encode(img_bytes).decode("ascii")
                    results.append(f"{meta}\ndata:image/png;base64,{b64}")

                logger.info(
                    "Extracted figure %d (%s, %s) from page %d",
                    fig_count, label_str, fig_type, page_num + 1,
                )

        header = f"Extracted {fig_count} figures"
        if not results:
            return f"{header}\nNo figures detected."
        return f"{header}\n\n" + "\n\n".join(results)
    finally:
        doc.close()


def main():
    """Entry point for the MCP server."""
    logger.info("Starting PDF Tools MCP Server ...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
