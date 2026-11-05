"""OpenFly-compatible discrete pose updates; no physical flight dynamics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable


@dataclass(frozen=True)
class Pose:
    """Benchmark stage pose in meters and degrees, yaw CCW from +X."""

    x: float
    y: float
    z: float
    yaw_deg: float

    def as_list(self) -> list[float]:
        return [self.x, self.y, self.z, self.yaw_deg]


def apply_action(
    pose: Pose,
    action: int,
    *,
    pos_ratio: float = 1.0,
    is_free: Callable[[float, float, float, float], bool] | None = None,
    ground_height: Callable[[float, float], float] | None = None,
    flight_height_m: float = 4.0,
) -> tuple[Pose, bool]:
    """Apply one v3 discrete action; return (new pose, blocked).

    `pos_ratio` converts OpenFly evaluator units to meters. Vertical actions are
    explicitly blocked per v3. Lateral 3-unit deltas remain provisional until
    verified against the released vlnv1 statistics; official route generation
    must not depend on them.
    """
    if action not in range(10):
        raise ValueError(f"unknown OpenFly action id: {action}")
    if pos_ratio <= 0:
        raise ValueError("pos_ratio must be positive")
    if action == 0:
        return pose, False
    if action in (4, 5):
        return pose, True

    yaw = math.radians(pose.yaw_deg)
    if action in (2, 3):
        delta = 30.0 if action == 2 else -30.0
        return Pose(pose.x, pose.y, pose.z, (pose.yaw_deg + delta) % 360.0), False

    distance_units = {1: 3.0, 6: 3.0, 7: 3.0, 8: 6.0, 9: 9.0}[action]
    distance = distance_units / pos_ratio
    if action in (1, 8, 9):
        dx, dy = distance * math.cos(yaw), distance * math.sin(yaw)
    else:
        # Body-relative lateral shift. This provisional action scale is not
        # used by v3's planar route set pending checkpoint-statistics audit.
        side = 1.0 if action == 6 else -1.0
        dx, dy = -side * distance * math.sin(yaw), side * distance * math.cos(yaw)

    nx, ny = pose.x + dx, pose.y + dy
    if is_free is not None and not is_free(pose.x, pose.y, nx, ny):
        return pose, True
    nz = ground_height(nx, ny) + flight_height_m if ground_height else pose.z
    return Pose(nx, ny, nz, pose.yaw_deg), False
