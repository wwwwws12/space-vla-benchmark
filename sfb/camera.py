"""Camera contract helpers shared by scene checks and Isaac adapter."""

from __future__ import annotations

import math


def camera_rotate_xyz(yaw_deg: float, pitch_deg: float = 0.0) -> tuple[float, float, float]:
    """USD camera local -Z/+Y to stage +forward/+Z-up (v3 convention)."""
    return 90.0 + pitch_deg, 0.0, yaw_deg - 90.0


def vertical_fov_deg(width: int = 1920, height: int = 1080, hfov_deg: float = 90.0) -> float:
    if width <= 0 or height <= 0 or not (0 < hfov_deg < 180):
        raise ValueError("invalid camera dimensions or horizontal FOV")
    return math.degrees(2.0 * math.atan(math.tan(math.radians(hfov_deg) / 2.0) * height / width))
