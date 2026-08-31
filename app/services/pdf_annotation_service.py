"""PDF annotation service — render pages and export annotated PDFs via PyMuPDF."""

import logging
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

FOOTER_MIN_HEIGHT = 80
FOOTER_MAX_HEIGHT = 300
FOOTER_HEIGHT_STEP = 40
MIN_FONT_SIZE = 6


def get_page_count(file_path: str) -> int:
    """Return number of pages in a PDF. Raises ValueError on invalid file."""
    try:
        with fitz.open(file_path) as doc:
            return len(doc)
    except Exception as e:
        raise ValueError(f"Ungültige PDF-Datei: {e}") from e


def render_page(file_path: str, page_num: int, dpi: int = 150) -> bytes | None:
    """
    Render a PDF page to PNG bytes.

    Args:
        file_path: Absolute path to the PDF file.
        page_num: 1-indexed page number.
        dpi: Rendering resolution (default 150).

    Returns:
        PNG bytes or None on error.
    """
    try:
        doc = fitz.open(file_path)
        if page_num < 1 or page_num > len(doc):
            doc.close()
            raise ValueError(f"Seite {page_num} außerhalb des Bereichs (1–{len(doc)})")
        page = doc[page_num - 1]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = bytes(pix.tobytes("png"))
        doc.close()
        return png_bytes
    except Exception as e:
        logger.error(
            "Fehler beim Rendern von Seite %d aus %s: %s", page_num, file_path, e
        )
        return None


def _text_fits(text: str, width: float, height: float, font_size: float) -> bool:
    """Check whether text fits in a box using a scratch page."""
    scratch = fitz.open()
    try:
        p = scratch.new_page(width=width + 20, height=height + 20)
        spare: float = p.insert_textbox(
            fitz.Rect(10, 10, width + 10, height + 10),
            text,
            fontsize=font_size,
            fontname="courier",
            color=(0, 0, 0),
        )
        return bool(spare >= 0)
    finally:
        scratch.close()


def _add_annotation_to_page(page: fitz.Page, content: str, timestamp: str) -> None:
    """Embed an annotation footer on a PDF page (modifies page in place)."""
    page_rect = page.rect
    full_text = f"{timestamp}\n{content}"

    footer_height = FOOTER_MIN_HEIGHT
    font_size = 9.0
    while not _text_fits(
        full_text, page_rect.width - 20, footer_height - 20, font_size
    ):
        if font_size > MIN_FONT_SIZE:
            font_size -= 1
        elif footer_height < FOOTER_MAX_HEIGHT:
            footer_height = min(footer_height + FOOTER_HEIGHT_STEP, FOOTER_MAX_HEIGHT)
            font_size = 9.0
        else:
            logger.warning(
                "Annotation passt möglicherweise nicht vollständig auf Seite %d",
                page.number + 1,
            )
            break

    margin = 10
    footer_rect = fitz.Rect(
        margin,
        page_rect.height - footer_height,
        page_rect.width - margin,
        page_rect.height - margin,
    )
    page.draw_rect(footer_rect, color=(1, 1, 0.9), fill=(1, 1, 0.9), width=0.5)
    page.insert_textbox(
        footer_rect,
        full_text,
        fontsize=font_size,
        fontname="courier",
        color=(0, 0.5, 0),
        align=0,
    )


def create_annotated_pdf(
    original_path: str,
    annotations: list[dict],
    output_path: Path,
) -> bool:
    """
    Create a copy of the PDF with annotation footers on annotated pages.

    Args:
        original_path: Path to the source PDF.
        annotations: List of dicts with keys: page_number (int), content (str), updated_at (datetime).
        output_path: Where to write the annotated PDF.

    Returns:
        True on success, False on error.
    """
    try:
        doc = fitz.open(original_path)
        annotated = 0
        for ann in annotations:
            content = (ann.get("content") or "").strip()
            if not content:
                continue
            page_num = ann["page_number"]
            if page_num < 1 or page_num > len(doc):
                continue
            updated_at = ann.get("updated_at")
            if isinstance(updated_at, datetime):
                ts = updated_at.strftime("[%Y-%m-%d %H:%M]")
            else:
                ts = f"[{updated_at}]" if updated_at else ""
            _add_annotation_to_page(doc[page_num - 1], content, ts)
            annotated += 1

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))
        doc.close()
        logger.info(
            "Annotiertes PDF erstellt: %s (%d Seiten annotiert)", output_path, annotated
        )
        return True
    except Exception as e:
        logger.error("Fehler beim Erstellen des annotierten PDFs: %s", e)
        return False
