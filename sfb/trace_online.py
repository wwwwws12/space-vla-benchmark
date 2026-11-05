"""Local TRACE control-flow contract for a future verified online Judger adapter.

This module intentionally knows no HTTP fields, model identity, prompt, or answer
parser. The adapter must be supplied from the approved Judger handoff.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from typing import Literal, Protocol


Answer = Literal["Yes", "No"]


@dataclass(frozen=True)
class JudgerQuery:
    episode_id: str
    step_idx: int
    target_phrase: str
    jpeg_path: Path
    jpeg_sha256: str


@dataclass(frozen=True)
class JudgerJudgment:
    request_id: str
    episode_id: str
    step_idx: int
    jpeg_sha256: str
    raw_answer: str
    parsed_answer: Answer
    model_id: str
    prompt_profile_id: str
    inference_ms: float | None = None
    round_trip_ms: float | None = None


class JudgerClient(Protocol):
    """In-process adapter seam; transport and wire schema remain handoff-owned."""

    def health(self) -> dict: ...

    def answer(self, query: JudgerQuery) -> JudgerJudgment: ...


@dataclass(frozen=True)
class TraceDecision:
    step_idx: int
    candidate_action_id: int
    query_performed: bool
    judger_answer: Answer | None
    consecutive_yes: int
    stop_reason: Literal["native_stop", "semantic_stop"] | None
    execute_candidate_action: bool
    request_id: str | None
    inference_ms: float | None
    judger_result: JudgerJudgment | None


class TraceController:
    """Apply frozen v3 native-STOP, q cadence, K consecutive-Yes semantics."""

    def __init__(self, episode_id: str, *, k: int = 2, q: int = 2, max_steps: int = 100):
        if not episode_id:
            raise ValueError("episode_id is required")
        if k not in (1, 2, 3) or q not in (1, 2, 3):
            raise ValueError("K/q must be one of the frozen v3 values 1, 2, or 3")
        if type(max_steps) is not int or not 1 <= max_steps <= 100:
            raise ValueError("max_steps must be between 1 and the v3 limit of 100")
        self.episode_id = episode_id
        self.k = k
        self.q = q
        self.max_steps = max_steps
        self.next_step = 0
        self.consecutive_yes = 0
        self.stop_reason: str | None = None
        self.error: str | None = None
        self._request_ids: set[str] = set()

    def query_due(self, step_idx: int, action_id: int) -> bool:
        """Return whether this action step queries; native STOP always has priority."""
        self._check_step_action(step_idx, action_id)
        return action_id != 0 and step_idx % self.q == 0

    def process(self, step_idx: int, action_id: int,
                judger_client: JudgerClient | None = None,
                query: JudgerQuery | None = None) -> TraceDecision:
        """Call Judger only at a due non-STOP frame, then decide before action execution."""
        due = self.query_due(step_idx, action_id)
        if not due:
            if query is not None:
                self.error = "JudgerInputUnexpected: query prepared on STOP/non-query frame"
                raise ValueError(self.error)
            return self.observe(step_idx, action_id)
        if judger_client is None:
            self.error = "JudgerUnavailable: required online query client is not configured"
            raise RuntimeError(self.error)
        if query is None:
            self.error = "JudgerInputMissing: current raw-frame JPEG query is required"
            raise ValueError(self.error)
        if query.episode_id != self.episode_id or query.step_idx != step_idx:
            self.error = "JudgerInputMismatch: query episode/frame is stale"
            raise ValueError(self.error)
        try:
            payload = query.jpeg_path.read_bytes()
        except OSError as exc:
            self.error = f"JudgerInputUnavailable: {type(exc).__name__}: {exc}"
            raise
        if (query.jpeg_path.suffix.lower() not in (".jpg", ".jpeg") or
                not payload.startswith(b"\xff\xd8") or
                hashlib.sha256(payload).hexdigest() != query.jpeg_sha256):
            self.error = "JudgerInputMismatch: current JPEG bytes/digest are invalid"
            raise ValueError(self.error)
        try:
            judgment = judger_client.answer(query)
            return self.observe(step_idx, action_id, judgment,
                                expected_jpeg_sha256=query.jpeg_sha256)
        except Exception as exc:
            if self.error is None:
                self.error = f"{type(exc).__name__}: {exc}"
            raise

    def _check_step_action(self, step_idx: int, action_id: int) -> None:
        if self.stop_reason is not None or self.error is not None:
            raise RuntimeError("TRACE controller is already terminal")
        if step_idx != self.next_step:
            self.error = f"StepOrderError: expected {self.next_step}, got {step_idx}"
            raise ValueError(self.error)
        if type(action_id) is not int or action_id not in range(10):
            self.error = "InvalidAction: OpenFly action_id must be an integer from 0 through 9"
            raise ValueError(self.error)
        if step_idx >= self.max_steps:
            self.error = "StepLimitError: TRACE episode has reached its configured decision limit"
            raise ValueError(self.error)

    def observe(self, step_idx: int, action_id: int, judgment: JudgerJudgment | None = None,
                *, expected_jpeg_sha256: str | None = None) -> TraceDecision:
        """Consume only the answer for this exact query frame, then decide before action."""
        self._check_step_action(step_idx, action_id)
        due = action_id != 0 and step_idx % self.q == 0

        if action_id == 0:
            if judgment is not None:
                self.error = "JudgerInputUnexpected: native STOP must end before issuing a Judger query"
                raise ValueError(self.error)
            self.stop_reason = "native_stop"
            decision = TraceDecision(step_idx, action_id, False, None, self.consecutive_yes,
                                     "native_stop", False, None, None, None)
        elif due:
            try:
                self._validate_judgment(step_idx, judgment)
                assert judgment is not None
                if (not expected_jpeg_sha256 or len(expected_jpeg_sha256) != 64 or
                        any(c not in "0123456789abcdef" for c in expected_jpeg_sha256)):
                    raise ValueError("Current query JPEG SHA-256 is required")
                if judgment.jpeg_sha256 != expected_jpeg_sha256:
                    raise ValueError("Judger result JPEG digest does not match current frame")
                if judgment.parsed_answer == "Yes":
                    self.consecutive_yes += 1
                else:
                    self.consecutive_yes = 0
                semantic_stop = self.consecutive_yes >= self.k
                if semantic_stop:
                    self.stop_reason = "semantic_stop"
                decision = TraceDecision(step_idx, action_id, True, judgment.parsed_answer,
                                         self.consecutive_yes,
                                         "semantic_stop" if semantic_stop else None,
                                         not semantic_stop, judgment.request_id,
                                         judgment.inference_ms, judgment)
            except Exception as exc:
                self.error = f"{type(exc).__name__}: {exc}"
                raise
        else:
            if judgment is not None:
                self.error = "JudgerInputUnexpected: answer supplied on a non-query frame"
                raise ValueError(self.error)
            decision = TraceDecision(step_idx, action_id, False, None, self.consecutive_yes,
                                     None, True, None, None, None)

        self.next_step += 1
        return decision

    def _validate_judgment(self, step_idx: int, judgment: JudgerJudgment | None) -> None:
        if judgment is None:
            raise ValueError(f"Missing Judger answer at required query step {step_idx}")
        if not isinstance(judgment, JudgerJudgment):
            raise TypeError("Judger adapter must return a verified JudgerJudgment")
        if not judgment.request_id or judgment.request_id in self._request_ids:
            raise ValueError("Judger request_id is missing or reused")
        if judgment.episode_id != self.episode_id or judgment.step_idx != step_idx:
            raise ValueError("Judger response episode/step does not match current query")
        if not judgment.jpeg_sha256 or len(judgment.jpeg_sha256) != 64:
            raise ValueError("Judger response is not bound to the current JPEG digest")
        if judgment.parsed_answer not in ("Yes", "No"):
            raise ValueError("Judger parsed answer must be exactly Yes or No")
        if not isinstance(judgment.raw_answer, str) or not judgment.raw_answer.strip():
            raise ValueError("Raw Judger answer must be preserved")
        if not judgment.model_id or not judgment.prompt_profile_id:
            raise ValueError("Judger model and prompt profile identity are required")
        if judgment.inference_ms is not None and (type(judgment.inference_ms) not in (int, float) or not math.isfinite(judgment.inference_ms) or judgment.inference_ms < 0):
            raise ValueError("Judger inference_ms must be nonnegative when supplied")
        self._request_ids.add(judgment.request_id)

    def finish_limit(self) -> str:
        """Close an episode after the last allowed candidate action was executed."""
        if self.stop_reason is not None or self.error is not None:
            raise RuntimeError("Cannot mark the limit after a terminal TRACE outcome")
        if self.next_step != self.max_steps:
            raise ValueError("Cannot mark the step limit before all configured steps were processed")
        self.stop_reason = "step_limit"
        return self.stop_reason


def make_judger_query(episode_id: str, step_idx: int, target_phrase: str,
                      jpeg_path: Path, jpeg_sha256: str) -> JudgerQuery:
    """Create local call metadata for an already encoded raw-frame JPEG."""
    path = Path(jpeg_path)
    if not episode_id or not target_phrase or not path.is_file():
        raise ValueError("Query requires an episode, target phrase, and saved current-frame JPEG")
    if len(jpeg_sha256) != 64 or any(c not in "0123456789abcdef" for c in jpeg_sha256):
        raise ValueError("jpeg_sha256 must be a lowercase SHA-256 digest")
    if hashlib.sha256(path.read_bytes()).hexdigest() != jpeg_sha256:
        raise ValueError("Saved JPEG digest does not match the query metadata")
    return JudgerQuery(episode_id, step_idx, target_phrase, path, jpeg_sha256)


def encode_current_frame_jpeg(raw_png_path: Path, jpeg_path: Path) -> str:
    """Encode a saved, unannotated navigation RGB PNG once using the T-track quality-85 path."""
    from PIL import Image
    source, target = Path(raw_png_path), Path(jpeg_path)
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite Judger JPEG: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        if image.mode != "RGB" or image.size != (1920, 1080):
            raise ValueError("Judger source must be an unannotated 1920x1080 RGB camera PNG")
        image.save(target, quality=85)
    payload = target.read_bytes()
    if not payload.startswith(b"\xff\xd8"):
        raise ValueError("Pillow did not produce a JPEG image")
    return hashlib.sha256(payload).hexdigest()
