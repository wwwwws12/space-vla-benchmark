"""Portable scene manifest and target/asset consistency checks."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any

ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class Scene:
    root: Path
    config: dict[str, Any]

    @property
    def scene_id(self) -> str:
        return self.config["scene_id"]

    @property
    def targets(self) -> list[dict[str, Any]]:
        return self.config["targets"]

    @property
    def pose(self) -> list[float]:
        return self.config["home_pose"]


def validate_scene(config: dict[str, Any], root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if config.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if not str(config.get("scene_id", "")).startswith("isaac_"):
        errors.append("scene_id must contain the isaac_ prefix")
    if "high" in str(config.get("scene_id", "")).lower():
        errors.append("scene_id must not contain 'high'")
    if config.get("world") not in {"mars", "moon", "cabin"}:
        errors.append("world must be mars, moon, or cabin")
    pose = config.get("home_pose")
    if not isinstance(pose, list) or len(pose) != 4 or not all(isinstance(x, (int, float)) for x in pose):
        errors.append("home_pose must be [x_m, y_m, z_m, yaw_deg]")
    camera = config.get("camera", {})
    if (camera.get("width"), camera.get("height"), camera.get("hfov_deg")) != (1920, 1080, 90.0):
        errors.append("camera must preserve the v3 1920x1080, 90 degree horizontal FOV")
    ids: set[str] = set()
    for i, target in enumerate(config.get("targets", [])):
        target_id = str(target.get("id", ""))
        if not ID_RE.fullmatch(target_id) or "high" in target_id.lower():
            errors.append(f"target {i}: invalid id {target_id!r}")
        if target_id.lower() in ids:
            errors.append(f"target {i}: duplicate id ignoring case: {target_id}")
        ids.add(target_id.lower())
        if not isinstance(target.get("phrase"), str) or not target["phrase"].strip():
            errors.append(f"target {target_id or i}: phrase must be a non-empty string")
        if "primitive" not in target and "asset" not in target:
            errors.append(f"target {target_id or i}: needs primitive or asset")
        if "primitive" in target and target["primitive"] not in {"box", "ball", "cylinder"}:
            errors.append(f"target {target_id}: unsupported primitive {target['primitive']!r}")
        if "asset" in target and root is not None:
            asset_path = (root / target["asset"]).resolve()
            if not asset_path.is_relative_to(root.resolve()):
                errors.append(f"target {target_id}: asset path escapes project scene root")
            elif not asset_path.exists() and "primitive" not in target:
                errors.append(f"target {target_id}: missing asset {target['asset']} without primitive fallback")
    return errors


def load_scene(path: str | Path) -> Scene:
    root = Path(path).resolve()
    config_path = root / "world.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    errors = validate_scene(config, root)
    if errors:
        raise ValueError("invalid scene:\n- " + "\n- ".join(errors))
    return Scene(root=root, config=config)


def terrain_height_m(scene: Scene, x_m: float, y_m: float) -> float:
    """Bilinearly sample inline or lazy-loaded NPY terrain in stage meters.

    Scenes without a terrain grid use the flat-stage height 0.
    USD construction and the camera adapter share this interpolation so the
    rendered camera clearance and target terrain agree for synthetic scenes.
    """
    terrain = scene.config.get("terrain")
    if not terrain:
        return 0.0
    if "heights_m" in terrain:
        heights = terrain["heights_m"]
    elif "height_file" in terrain:
        height_path=(scene.root / terrain["height_file"]).resolve()
        heights = _height_file(str(height_path),height_path.stat().st_mtime_ns)
    else:
        return 0.0
    ny, nx = len(heights), len(heights[0])
    if nx < 2 or ny < 2 or any(len(row) != nx for row in heights):
        raise ValueError("terrain heights_m must be a rectangular grid of at least 2x2")
    gx = (x_m + terrain["width_m"] / 2.0) * (nx - 1) / terrain["width_m"]
    gy = (y_m + terrain["depth_m"] / 2.0) * (ny - 1) / terrain["depth_m"]
    gx = min(max(gx, 0.0), nx - 1.0)
    gy = min(max(gy, 0.0), ny - 1.0)
    i0, j0 = int(gx), int(gy)
    i1, j1 = min(i0 + 1, nx - 1), min(j0 + 1, ny - 1)
    tx, ty = gx - i0, gy - j0
    z0 = heights[j0][i0] * (1.0 - tx) + heights[j0][i1] * tx
    z1 = heights[j1][i0] * (1.0 - tx) + heights[j1][i1] * tx
    return float(z0 * (1.0 - ty) + z1 * ty)


@lru_cache(maxsize=8)
def _height_file(path: str, mtime_ns: int):
    """Lazy pure-numpy data dependency; importing scene needs no Isaac/numpy."""
    import numpy as np
    heights=np.load(path,allow_pickle=False)
    if heights.ndim!=2 or not np.isfinite(heights).all():
        raise ValueError("height_file must contain a finite 2D numpy array")
    heights.setflags(write=False)
    return heights


def save_scene(root: str | Path, config: dict[str, Any]) -> Scene:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    errors = validate_scene(config, root)
    if errors:
        raise ValueError("invalid scene:\n- " + "\n- ".join(errors))
    (root / "world.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return load_scene(root)
