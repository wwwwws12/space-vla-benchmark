"""DEMO_ONLY client for the handoff-pinned Qwen Judger HTTP API."""
from __future__ import annotations

import base64
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
import uuid

from sfb.trace_online import JudgerJudgment, JudgerQuery


MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"
MODEL_REVISION = "66285546d2b821cf421d4f5eb2576359d3770cd3"
PROFILE_ID = "qwen25vl3b-visible-demo-v1"
PILOT_PROFILE_ID = 'qwen25vl3b-visible-pilot-target-v1'
TARGET_DESCRIPTION = "the six-wheeled rover with a raised white mast"
USAGE_SCOPE = "DEMO_ONLY_NOT_FROZEN_TRACE_JUDGER"


class JudgerAPIError(RuntimeError):
    pass


class OnlineJudgerClient:
    """HTTP adapter; credentials are read from process environment and never logged."""

    def __init__(self, base_url: str = "http://127.0.0.1:18772", *,
                 token_env: str = "SPACE_ECHO_TOKEN", timeout: tuple[float, float] = (5.0, 60.0),
                 evidence_dir: Path | None = None, profile_id: str = PROFILE_ID):
        if profile_id not in (PROFILE_ID, PILOT_PROFILE_ID):
            raise ValueError('Unknown Judger profile')
        self.profile_id = profile_id
        if not base_url.startswith("http://127.0.0.1:"):
            raise ValueError("Judger must use the handoff-approved loopback-only HTTP forward")
        self.base_url = base_url.rstrip("/")
        self.token_env = token_env
        self.connect_timeout, self.read_timeout = timeout
        self.evidence_dir = Path(evidence_dir) if evidence_dir else None
        self.health_record: dict | None = None

    def health(self) -> dict:
        data, status = self._request("GET", "/health", None, authenticated=False)
        expected = {
            "runtime_mode": "judger_inference", "model_loaded": True,
            "model_id": MODEL_ID, "model_revision": MODEL_REVISION,
        }
        if status != 200 or any(data.get(k) != v for k, v in expected.items()):
            raise JudgerAPIError("Judger health identity/readiness does not match the handoff")
        if self.profile_id == PROFILE_ID and data.get('profile_id') != PROFILE_ID:
            raise JudgerAPIError('Legacy Judger profile identity mismatch')
        if self.profile_id == PILOT_PROFILE_ID and self.profile_id not in data.get('supported_profile_ids', []):
            raise JudgerAPIError('Handed-off Pilot Judger profile is not enabled')
        if not isinstance(data.get("service_instance_id"), str) or not data["service_instance_id"]:
            raise JudgerAPIError("Judger health omitted service_instance_id")
        self.health_record = data
        return data

    def answer(self, query: JudgerQuery, request_id: str | None = None) -> JudgerJudgment:
        if self.profile_id == PROFILE_ID and query.target_phrase != TARGET_DESCRIPTION:
            raise JudgerAPIError("Query target_description differs from the fixed handoff profile")
        if not isinstance(query.target_phrase, str) or not 1 <= len(query.target_phrase) <= 256 or query.target_phrase.strip() != query.target_phrase or any(c in query.target_phrase for c in '\r\n'):
            raise JudgerAPIError('Target description violates the handed-off single-line phrase contract')
        if self.health_record is None:
            raise JudgerAPIError("Call and verify /health before the first inference request")
        image = Path(query.jpeg_path).read_bytes()
        sha = hashlib.sha256(image).hexdigest()
        if sha != query.jpeg_sha256 or not image.startswith(b"\xff\xd8"):
            raise JudgerAPIError("Current JPEG bytes or SHA-256 do not match query metadata")
        request_id = request_id or "win-" + uuid.uuid4().hex
        payload = {
            "request_id": request_id,
            "episode_id": query.episode_id,
            "step_idx": query.step_idx,
            "target_description": query.target_phrase,
            "image_base64": base64.b64encode(image).decode("ascii"),
            "jpeg_sha256": sha,
            "profile_id": self.profile_id,
        }
        started = time.perf_counter()
        response, status = self._request("POST", "/v1/judger/ask", payload, authenticated=True)
        rtt_ms = (time.perf_counter() - started) * 1000
        self._validate_response(response, status, query, request_id, sha, self.profile_id)
        if response['service_instance_id'] != self.health_record['service_instance_id']:
            raise JudgerAPIError('Judger instance changed during request')
        result = JudgerJudgment(
            request_id=response["request_id"], episode_id=response["episode_id"],
            step_idx=response["step_idx"], jpeg_sha256=response["jpeg_sha256"],
            raw_answer=response["raw_answer"], parsed_answer=response["answer"],
            model_id=response["model_id"], prompt_profile_id=response["profile_id"],
            inference_ms=float(response["inference_ms"]), round_trip_ms=rtt_ms,
        )
        if self.evidence_dir:
            self.evidence_dir.mkdir(parents=True, exist_ok=True)
            # Keep exact non-sensitive fields and byte digest; never write image bytes or auth.
            evidence = {
                "scope": USAGE_SCOPE, "http_status": status,
                "request": {k: v for k, v in payload.items() if k != "image_base64"}
                | {"image_byte_length": len(image)},
                "response": response, "client_round_trip_ms": rtt_ms,
                "service_instance_id": self.health_record["service_instance_id"],
            }
            path = self.evidence_dir / f"{request_id}.json"
            path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        return result

    def _request(self, method: str, path: str, payload: dict | None,
                 *, authenticated: bool) -> tuple[dict, int]:
        headers = {"Accept": "application/json"}
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        if authenticated:
            token = os.environ.get(self.token_env)
            if not token:
                raise JudgerAPIError(f"Required process environment variable {self.token_env} is absent")
            headers["Authorization"] = "Bearer " + token
        parts = urlsplit(self.base_url)
        connection = http.client.HTTPConnection(parts.hostname, parts.port, timeout=self.connect_timeout)
        transport_path = None
        transport = {'post_attempted': False, 'http_status': None, 'server_execution_known': False, 'automatic_retry': False}
        if payload is not None and self.evidence_dir:
            self.evidence_dir.mkdir(parents=True, exist_ok=True)
            transport_path = self.evidence_dir / (payload['request_id'] + '.transport.json')
        def record_transport():
            if transport_path:
                transport_path.write_text(json.dumps(transport, indent=2)+'\n', encoding='utf-8')
        record_transport()
        try:
            connection.connect()
            if payload is not None:
                transport['post_attempted'] = True
                record_transport()
            connection.request(method, path, body=body, headers=headers)
            if connection.sock is not None:
                connection.sock.settimeout(self.read_timeout)
            response = connection.getresponse()
            raw = response.read(8 * 1024 * 1024 + 1)
            status = response.status
            transport.update(http_status=status, server_execution_known=True)
            record_transport()
        except (TimeoutError, OSError, http.client.HTTPException) as exc:
            transport['error_type'] = type(exc).__name__
            record_transport()
            raise JudgerAPIError(f"Judger transport failure: {type(exc).__name__}") from None
        finally:
            connection.close()
        if len(raw) > 8 * 1024 * 1024:
            raise JudgerAPIError('Oversize Judger response')
        secret = os.environ.get(self.token_env, '').strip()
        if secret and secret.encode() in raw:
            raise JudgerAPIError('Credential in response; response withheld')
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            raise JudgerAPIError("Judger response was not valid UTF-8 JSON") from None
        if not isinstance(data, dict):
            raise JudgerAPIError("Judger response must be a JSON object")
        if payload is not None and self.evidence_dir:
            self.evidence_dir.mkdir(parents=True, exist_ok=True)
            evidence = {'scope': USAGE_SCOPE, 'http_status': status,
                        'request': {k: v for k, v in payload.items() if k != 'image_base64'},
                        'response': data, 'service_instance_id': (self.health_record or {}).get('service_instance_id')}
            path = self.evidence_dir / (payload['request_id'] + '.http.json')
            with path.open('x', encoding='utf-8') as f:
                json.dump(evidence, f, indent=2); f.write('\n')
        if status < 200 or status >= 300:
            raise JudgerAPIError(f"Judger HTTP {status}: {json.dumps(data, ensure_ascii=False)}")
        return data, status

    @staticmethod
    def _validate_response(data: dict, status: int, query: JudgerQuery,
                           request_id: str, sha: str, profile_id: str = PROFILE_ID) -> None:
        expected = {
            "request_id": request_id, "episode_id": query.episode_id,
            "step_idx": query.step_idx, "status": "ok", "model_id": MODEL_ID,
            "model_revision": MODEL_REVISION, "profile_id": profile_id,
            "jpeg_sha256": sha, "usage_scope": USAGE_SCOPE,
        }
        if status != 200 or any(data.get(k) != v for k, v in expected.items()):
            raise JudgerAPIError("Judger response status/identity/correlation fields mismatch")
        if profile_id == PILOT_PROFILE_ID:
            prompt = f'Is {query.target_phrase} visible in this image? Answer Yes or No only.'
            if data.get('target_description') != query.target_phrase or data.get('prompt_version') != 'visible-question-v1' or data.get('prompt_sha256') != hashlib.sha256(prompt.encode()).hexdigest():
                raise JudgerAPIError('Dynamic target or frozen prompt evidence mismatch')
        if data.get("answer") not in ("Yes", "No"):
            raise JudgerAPIError("Judger answer is not exactly Yes or No")
        raw = data.get("raw_answer")
        if not isinstance(raw, str) or raw.strip().lower() not in ("yes", "no", "yes.", "no."):
            raise JudgerAPIError("Judger raw_answer violates the pinned exact-token parser")
        if raw.strip().rstrip(".").lower() != data["answer"].lower():
            raise JudgerAPIError("Judger raw_answer and parsed answer disagree")
        if type(data.get("inference_ms")) not in (int, float) or not math.isfinite(data['inference_ms']) or data["inference_ms"] < 0:
            raise JudgerAPIError("Judger inference_ms is missing or invalid")
        if (data.get("image_width"), data.get("image_height")) != (1920, 1080):
            raise JudgerAPIError("Judger image dimensions do not match the v3 navigation camera")
        if not isinstance(data.get("service_instance_id"), str):
            raise JudgerAPIError("Judger response omitted service_instance_id")
