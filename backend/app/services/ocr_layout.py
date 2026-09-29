"""OCR extraction and layout consistency heuristics."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from app.schemas.forensics import ExtractedTextBlock, OCRLayoutResult
from app.services.forensics_utils import load_document_rgb, pil_to_numpy


class OCRLayoutAnalyzer:
    """Extract text regions and detect layout anomalies indicative of tampering."""

    def __init__(
        self,
        min_confidence: float = 0.35,
        overlap_iou_threshold: float = 0.15,
        baseline_tolerance_px: float = 12.0,
        min_aspect_ratio: float = 0.05,
        max_aspect_ratio: float = 25.0,
    ) -> None:
        self.min_confidence = min_confidence
        self.overlap_iou_threshold = overlap_iou_threshold
        self.baseline_tolerance_px = baseline_tolerance_px
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio

    def analyze(self, file_path: str | Path) -> OCRLayoutResult:
        path = Path(file_path)
        image = load_document_rgb(path)
        image_array = pil_to_numpy(image)

        raw_detections = self._run_ocr(image_array)
        extracted_text = self._normalize_detections(raw_detections)
        layout_inconsistencies = self._detect_layout_inconsistencies(extracted_text)

        return {
            "extracted_text": extracted_text,
            "layout_inconsistencies": layout_inconsistencies,
        }

    def _run_ocr(self, image_array: np.ndarray) -> list[Any]:
        try:
            reader = _get_easyocr_reader()
            return reader.readtext(image_array)
        except Exception:
            return self._run_tesseract_fallback(image_array)

    def _run_tesseract_fallback(self, image_array: np.ndarray) -> list[Any]:
        try:
            import pytesseract
            from pytesseract import Output
        except ImportError as exc:
            raise RuntimeError(
                "Neither EasyOCR nor pytesseract is available for OCR analysis."
            ) from exc

        data = pytesseract.image_to_data(
            image_array,
            output_type=Output.DICT,
            config="--psm 6",
        )
        detections: list[Any] = []
        count = len(data["text"])
        for index in range(count):
            text = (data["text"][index] or "").strip()
            confidence = float(data["conf"][index])
            if not text or confidence < 0:
                continue
            x, y, w, h = (
                data["left"][index],
                data["top"][index],
                data["width"][index],
                data["height"][index],
            )
            bbox = [
                [x, y],
                [x + w, y],
                [x + w, y + h],
                [x, y + h],
            ]
            detections.append((bbox, text, confidence / 100.0))
        return detections

    def _normalize_detections(self, detections: list[Any]) -> list[ExtractedTextBlock]:
        blocks: list[ExtractedTextBlock] = []

        for detection in detections:
            bbox, text, confidence = detection
            text = str(text).strip()
            confidence = float(confidence)
            if not text or confidence < self.min_confidence:
                continue

            xs = [point[0] for point in bbox]
            ys = [point[1] for point in bbox]
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)
            aspect_ratio = float(width / (height + 1e-6))
            baseline_y = float(max(ys))

            blocks.append(
                {
                    "text": text,
                    "confidence": round(confidence, 4),
                    "bbox": [[float(x), float(y)] for x, y in bbox],
                    "aspect_ratio": round(aspect_ratio, 4),
                    "baseline_y": round(baseline_y, 2),
                }
            )

        return blocks

    def _detect_layout_inconsistencies(
        self, blocks: list[ExtractedTextBlock]
    ) -> list[str]:
        inconsistencies: list[str] = []

        if not blocks:
            inconsistencies.append("No OCR text detected in document.")
            return inconsistencies

        for block in blocks:
            ratio = block["aspect_ratio"]
            if ratio < self.min_aspect_ratio or ratio > self.max_aspect_ratio:
                inconsistencies.append(
                    "Abnormal text bounding box aspect ratio detected "
                    f"for '{block['text'][:32]}' (ratio={ratio})."
                )

        inconsistencies.extend(self._detect_overlaps(blocks))
        inconsistencies.extend(self._detect_baseline_drift(blocks))

        return inconsistencies

    def _detect_overlaps(self, blocks: list[ExtractedTextBlock]) -> list[str]:
        flags: list[str] = []
        for i, left in enumerate(blocks):
            left_rect = _bbox_to_rect(left["bbox"])
            for right in blocks[i + 1 :]:
                right_rect = _bbox_to_rect(right["bbox"])
                iou = _intersection_over_union(left_rect, right_rect)
                if iou >= self.overlap_iou_threshold:
                    flags.append(
                        "Overlapping OCR text boxes detected "
                        f"between '{left['text'][:24]}' and '{right['text'][:24]}'."
                    )
        return flags

    def _detect_baseline_drift(self, blocks: list[ExtractedTextBlock]) -> list[str]:
        if len(blocks) < 2:
            return []

        sorted_blocks = sorted(blocks, key=lambda item: item["baseline_y"])
        row_groups: list[list[ExtractedTextBlock]] = []
        current_row: list[ExtractedTextBlock] = []

        for block in sorted_blocks:
            if not current_row:
                current_row = [block]
                continue

            if abs(block["baseline_y"] - current_row[-1]["baseline_y"]) <= self.baseline_tolerance_px:
                current_row.append(block)
            else:
                row_groups.append(current_row)
                current_row = [block]

        if current_row:
            row_groups.append(current_row)

        flags: list[str] = []
        for row in row_groups:
            if len(row) < 2:
                continue
            baselines = [item["baseline_y"] for item in row]
            drift = max(baselines) - min(baselines)
            if drift > self.baseline_tolerance_px:
                flags.append(
                    "Inconsistent text baseline alignment detected within a text row "
                    f"(drift={drift:.1f}px)."
                )
        return flags


@lru_cache(maxsize=1)
def _get_easyocr_reader() -> Any:
    import easyocr

    return easyocr.Reader(["en"], gpu=False, verbose=False)


def _bbox_to_rect(bbox: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in bbox]
    ys = [point[1] for point in bbox]
    return min(xs), min(ys), max(xs), max(ys)


def _intersection_over_union(
    rect_a: tuple[float, float, float, float],
    rect_b: tuple[float, float, float, float],
) -> float:
    ax1, ay1, ax2, ay2 = rect_a
    bx1, by1, bx2, by2 = rect_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h
    if intersection == 0:
        return 0.0

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0
