"""Shared helpers for forensic image/PDF loading."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def is_pdf(file_path: Path) -> bool:
    return file_path.suffix.lower() == ".pdf"


def is_image(file_path: Path) -> bool:
    return file_path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES


def load_pil_image(file_path: Path) -> Image.Image:
    """Load an image file as RGB PIL Image."""
    image = Image.open(file_path)
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image


def pdf_first_page_to_pil(file_path: Path, dpi: int = 200) -> Image.Image:
    """Render the first page of a PDF to a PIL RGB image."""
    import fitz  # PyMuPDF

    with fitz.open(file_path) as document:
        if document.page_count == 0:
            raise ValueError("PDF contains no pages.")
        page = document.load_page(0)
        pixmap = page.get_pixmap(dpi=dpi, alpha=False)
        return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def load_document_rgb(file_path: str | Path, dpi: int = 200) -> Image.Image:
    """
    Load a supported document (image or PDF first page) as an RGB PIL image.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    if is_pdf(path):
        return pdf_first_page_to_pil(path, dpi=dpi)
    if is_image(path):
        return load_pil_image(path)

    raise ValueError(f"Unsupported document type for image loading: {path.suffix}")


def pil_to_numpy(image: Image.Image) -> np.ndarray:
    """Convert PIL RGB image to OpenCV-compatible BGR ndarray."""
    rgb = np.asarray(image)
    return rgb[:, :, ::-1].copy()
