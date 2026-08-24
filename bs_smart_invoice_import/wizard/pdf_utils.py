"""Optional PDF -> page-image conversion for invoice uploads. Mirrors
``wizard/embedding_matcher.py``'s graceful-degradation pattern: import is
wrapped in try/except, and every function raises a plain ``RuntimeError``
(not an Odoo exception -- this module has no Odoo dependency) if the
optional ``pymupdf`` package isn't installed, so the module still installs
and the plain-text/image-upload paths still work without it.
"""
try:
    import pymupdf as fitz
except ImportError:
    fitz = None

# Bounds latency/cost of a single extraction call -- an invoice is very
# rarely more than a few pages, and the LLM call already gets slower/pricier
# with every extra image attached.
MAX_PDF_PAGES = 5


def is_available():
    return fitz is not None


def pdf_to_images(pdf_bytes, dpi=150):
    """Render up to MAX_PDF_PAGES pages of the given PDF bytes to PNG page
    images. Returns a list of PNG bytes, one per page. Raises RuntimeError
    if PyMuPDF isn't installed.
    """
    if fitz is None:
        raise RuntimeError(
            "PDF invoice upload requires the 'pymupdf' Python package, "
            "which isn't installed. Install it (pip install pymupdf) or "
            "upload the invoice as an image instead."
        )
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    images = []
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    try:
        for page in doc[:MAX_PDF_PAGES]:
            pix = page.get_pixmap(matrix=matrix)
            images.append(pix.tobytes('png'))
    finally:
        doc.close()
    return images
