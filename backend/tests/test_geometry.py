"""Unit tests for document corner geometry helpers."""

import numpy as np

from app.utils.geometry import order_corners, validate_quadrilateral


def test_order_corners_returns_tl_tr_br_bl():
    points = np.array(
        [
            [10, 10],  # top-left
            [100, 12],  # top-right
            [98, 80],  # bottom-right
            [12, 78],  # bottom-left
        ],
        dtype=np.float32,
    )
    ordered = order_corners(points)
    np.testing.assert_allclose(ordered[0], [10, 10], rtol=0, atol=1)
    np.testing.assert_allclose(ordered[1], [100, 12], rtol=0, atol=1)


def test_validate_quadrilateral_accepts_reasonable_document_quad():
    corners = np.array(
        [[50, 50], [450, 55], [445, 300], [55, 295]],
        dtype=np.float32,
    )
    assert validate_quadrilateral(corners, (480, 640))


def test_validate_quadrilateral_rejects_tiny_area():
    corners = np.array([[0, 0], [2, 0], [2, 2], [0, 2]], dtype=np.float32)
    assert not validate_quadrilateral(corners, (480, 640))
