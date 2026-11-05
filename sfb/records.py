"""Route and per-frame records shared by Windows and Linux tooling."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .actions import Pose


def validate_record(record: dict[str, Any], scene_id: str | None = None) -> list[str]:
    errors: list[str] = []
    if record.get("schema_version") != 1:
        errors.append("record schema_version must equal 1")
    if scene_id is not None and record.get("scene_id") != scene_id:
        errors.append("record scene_id does not match the loaded scene")
    frames = record.get("frames")
    if not isinstance(frames, list) or not frames:
        return errors + ["record must contain at least one frame"]
    previous_time = -float("inf")
    for i, frame in enumerate(frames):
        pose = frame.get("pose_m_deg")
        if not isinstance(pose, list) or len(pose) != 4:
            errors.append(f"frame {i}: pose_m_deg must be [x_m, y_m, z_m, yaw_deg]")
        if frame.get("step") != i:
            errors.append(f"frame {i}: step index is not contiguous")
        t = frame.get("elapsed_s")
        if not isinstance(t, (int, float)) or t < previous_time:
            errors.append(f"frame {i}: elapsed wall time must be numeric and non-decreasing")
        else:
            previous_time = t
    return errors


class RouteRecorder:
    def __init__(self, output_dir: str | Path, route_id: str, instruction: str, target_id: str):
        self.root = Path(output_dir) / route_id
        self.root.mkdir(parents=True, exist_ok=False)
        self.record: dict[str, Any] = {
            "schema_version": 1,
            "route_id": route_id,
            "instruction": instruction,
            "target_id": target_id,
            "frames": [],
            "created_utc": datetime.now(timezone.utc).isoformat(),
        }

    def add_frame(self, step: int, pose: Pose, action: int | None, *, elapsed_s: float, image_path: str | None = None) -> None:
        self.record["frames"].append({
            "step": step,
            "pose_m_deg": pose.as_list(),
            "action": action,
            "elapsed_s": elapsed_s,
            "image": image_path,
        })

    def close(self, stop_reason: str) -> Path:
        self.record["stop_reason"] = stop_reason
        out = self.root / "record.json"
        out.write_text(json.dumps(self.record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return out
