"""Geometry helpers for document corner ordering and validation."""

from __future__ import annotations

import cv2
import numpy as np


def order_corners(points: np.ndarray) -> np.ndarray:
    """Order four points as top-left, top-right, bottom-right, bottom-left."""
    ordered = np.zeros((4, 2), dtype=np.float32)
    s = points.sum(axis=1)
    diff = np.diff(points, axis=1).reshape(-1)

    ordered[0] = points[np.argmin(s)]
    ordered[2] = points[np.argmax(s)]
    ordered[1] = points[np.argmin(diff)]
    ordered[3] = points[np.argmax(diff)]
    return ordered


def validate_quadrilateral(corners: np.ndarray, image_shape: tuple[int, int]) -> bool:
    """Validate corner geometry for a document quadrilateral."""
    if corners.shape != (4, 2):
        return False

    polygon = corners.astype(np.float32)
    if not cv2.isContourConvex(polygon.reshape(-1, 1, 2)):
        return False

    height, width = image_shape[:2]
    area = cv2.contourArea(polygon)
    image_area = float(width * height)
    if area < 0.05 * image_area or area > 0.98 * image_area:
        return False

    rect = cv2.minAreaRect(polygon)
    box_w, box_h = rect[1]
    if box_w <= 1 or box_h <= 1:
        return False
    aspect = max(box_w, box_h) / min(box_w, box_h)
    if aspect > 4.5:
        return False
    return True


def refine_corners(gray: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """Refine corners using local goodFeaturesToTrack + cornerSubPix."""
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.001)
    refined = corners.copy().astype(np.float32)
    win_size = (5, 5)
    zero_zone = (-1, -1)
    cv2.cornerSubPix(gray, refined, win_size, zero_zone, criteria)
    return order_corners(refined)
