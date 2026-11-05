"""Independent Lance v2 HTTP adapter. Never changes the frozen Qwen client."""
from __future__ import annotations

import base64
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import uuid

from sfb.trace_online import JudgerJudgment, JudgerQuery

MODEL_ID = 'bytedance-research/Lance/Lance_3B'
MODEL_REVISION = '7395315758865e6f56ab87ad06a88c7ac172f056'
PROFILE_ID = 'lance3b-image-visible-greedy-v1'
CONTRACT_VERSION = 'space-lance-image-judger-v2'
PROMPT = 'Is {target_description} visible in this image? Answer Yes or No only.'
REQUEST_FIELDS = frozenset(('request_id', 'episode_id', 'step_idx', 'target_description',
                            'image_base64', 'jpeg_sha256', 'profile_id'))


class LanceAPIError(RuntimeError):
    def __init__(self, category, *, http_status=None, server_code=None):
        self.category = category
        self.http_status = http_status
        self.server_code = server_code
        super().__init__(category + (f' (HTTP {http_status})' if http_status else ''))


def write_json(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + '\n'
    if exclusive:
        with path.open('x', encoding='utf-8') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
    else:
        temp = path.with_suffix(path.suffix + '.tmp')
        temp.write_text(text, encoding='utf-8')
        os.replace(temp, path)


def require(ok, category):
    if not ok:
        raise LanceAPIError(category)


def validate_schema(value, schema):
    """Validate the actual handoff's small scalar/object schema, fail on bad types."""
    if 'const' in schema:
        require(value == schema['const'], 'RESPONSE_SCHEMA_CONST_MISMATCH')
    if 'enum' in schema:
        require(value in schema['enum'], 'RESPONSE_SCHEMA_ENUM_MISMATCH')
    kind = schema.get('type')
    checks = {'object':lambda v:isinstance(v,dict), 'string':lambda v:isinstance(v,str),
              'integer':lambda v:type(v) == int, 'number':lambda v:type(v) in (int,float) and math.isfinite(v),
              'boolean':lambda v:type(v) == bool, 'null':lambda v:v is None}
    if kind:
        require(kind in checks and checks[kind](value), 'RESPONSE_SCHEMA_TYPE_MISMATCH')
    if isinstance(value,dict):
        require(set(schema.get('required',[])) <= set(value), 'RESPONSE_SCHEMA_REQUIRED_FIELD_MISSING')
        props = schema.get('properties',{})
        if schema.get('additionalProperties') is False:
            require(set(value) <= set(props), 'UNEXPECTED_JSON_FIELD')
        for k,v in value.items():
            if k in props:
                validate_schema(v,props[k])
    if isinstance(value,str):
        require(len(value) >= schema.get('minLength',0) and len(value) <= schema.get('maxLength',float('inf')),
                'SCHEMA_STRING_LENGTH')
        if 'pattern' in schema:
            require(re.search(schema['pattern'],value) is not None,'SCHEMA_STRING_PATTERN')
    if type(value) in (int,float):
        require(value >= schema.get('minimum',-float('inf')),'SCHEMA_NUMBER_RANGE')


class LanceJudgerClient:
    def __init__(self, base_url='http://127.0.0.1:18774', *, evidence_dir=None,
                 timeout=(5.0, 120.0), token_env='SPACE_ECHO_TOKEN', binding=None):
        parts = urlsplit(base_url)
        require(parts.scheme == 'http' and parts.hostname == '127.0.0.1' and parts.port is not None
                and not parts.username and not parts.password and parts.path in ('', '/')
                and not parts.query and not parts.fragment, 'NON_LOOPBACK_ENDPOINT')
        require(len(timeout) == 2 and all(type(v) in (int, float) and math.isfinite(v) and 0 < v <= 180 for v in timeout),
                'INVALID_TIMEOUT')
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.token_env = token_env
        self.evidence_dir = Path(evidence_dir) if evidence_dir else None
        self.binding = binding
        self.health_record = None

    def _reviewed(self):
        require(isinstance(self.binding, dict) and self.binding.get('review_status') == 'ACTUAL_HANDOFF_REVIEWED',
                'WAIT_ACTUAL_LANCE_HANDOFF_REVIEW')
        require(self.binding.get('contract_version') == CONTRACT_VERSION and
                self.binding.get('model_id') == MODEL_ID and
                self.binding.get('model_revision') == MODEL_REVISION and
                self.binding.get('profile_id') == PROFILE_ID, 'HANDOFF_BINDING_IDENTITY_MISMATCH')

    def health(self):
        self._reviewed()
        response, status, _ = self._request('GET', '/health', None, authenticated=False)
        require(status == 200, 'HEALTH_HTTP_ERROR')
        expected = self.binding['health_expected']
        require(all(response.get(k) == v for k, v in expected.items()), 'HEALTH_IDENTITY_OR_MODE_MISMATCH')
        require(isinstance(response.get('service_instance_id'), str) and bool(response['service_instance_id']),
                'HEALTH_INSTANCE_MISSING')
        self.health_record = response
        return response

    def answer(self, query: JudgerQuery, request_id=None):
        self._reviewed()
        require(self.health_record is not None, 'HEALTH_NOT_VERIFIED')
        require(isinstance(query.target_phrase, str) and query.target_phrase.strip() == query.target_phrase
                and 1 <= len(query.target_phrase) <= 256
                and not any(ord(c) < 32 or ord(c) == 127 for c in query.target_phrase), 'INVALID_TARGET_DESCRIPTION')
        require(type(query.step_idx) == int and query.step_idx >= 0 and bool(query.episode_id), 'INVALID_FRAME_IDENTITY')
        image = Path(query.jpeg_path).read_bytes()
        require(image.startswith(b'\xff\xd8') and hashlib.sha256(image).hexdigest() == query.jpeg_sha256,
                'JPEG_BYTES_OR_SHA_MISMATCH')
        rid = request_id or 'lance-' + uuid.uuid4().hex
        payload = dict(request_id=rid, episode_id=query.episode_id, step_idx=query.step_idx,
                       target_description=query.target_phrase, image_base64=base64.b64encode(image).decode('ascii'),
                       jpeg_sha256=query.jpeg_sha256, profile_id=PROFILE_ID)
        require(set(payload) == REQUEST_FIELDS, 'REQUEST_FIELD_SET_MISMATCH')
        validate_schema(payload,self.binding['request_schema'])
        response, status, elapsed = self._request('POST', '/v1/judger/ask', payload, authenticated=True)
        self.validate_response(response, status, query, rid, self.binding,
                               self.health_record['service_instance_id'])
        return JudgerJudgment(rid, query.episode_id, query.step_idx, query.jpeg_sha256,
                              response['raw_answer'], response['answer'], MODEL_ID, PROFILE_ID,
                              float(response['inference_ms']), elapsed)

    @staticmethod
    def validate_response(data, status, query, request_id, binding, service_instance_id):
        require(isinstance(data, dict), 'NON_OBJECT_RESPONSE')
        if status != 200:
            code = data.get('error')
            if isinstance(code, dict):
                code = code.get('code') or code.get('type')
            if not isinstance(code, str):
                code = data.get('error_code') or data.get('detail')
            category = {400:'HTTP_BAD_REQUEST',401:'HTTP_AUTH_ERROR',403:'HTTP_AUTH_ERROR',
                        409:'DUPLICATE_REQUEST_ID',413:'REQUEST_TOO_LARGE',422:'HTTP_422_INVALID_ANSWER',
                        429:'UNEXPECTED_QUOTA_OR_MODE_ERROR',503:'SERVICE_UNAVAILABLE_OR_UNKNOWN'}.get(status,'HTTP_SERVER_ERROR')
            if code == 'truncated_answer':
                category = 'TRUNCATED_ANSWER'
            raise LanceAPIError(category, http_status=status, server_code=code if isinstance(code, str) else None)
        validate_schema(data,binding['success_schema'])
        expected = dict(request_id=request_id, episode_id=query.episode_id, step_idx=query.step_idx,
                        model_id=MODEL_ID, model_revision=MODEL_REVISION, profile_id=PROFILE_ID,
                        jpeg_sha256=query.jpeg_sha256, target_description=query.target_phrase, status='ok',
                        service_instance_id=service_instance_id)
        expected.update(binding.get('response_expected', {}))
        require(all(data.get(k) == v for k, v in expected.items()), 'RESPONSE_IDENTITY_OR_CORRELATION_MISMATCH')
        require(type(data.get('step_idx')) == int, 'INVALID_RESPONSE_STEP_TYPE')
        require(data.get('answer') in ('Yes', 'No'), 'INVALID_PARSED_ANSWER')
        raw = data.get('raw_answer')
        require(isinstance(raw, str) and raw.strip().lower() in ('yes', 'no', 'yes.', 'no.'), 'INVALID_RAW_ANSWER')
        require(raw.strip().rstrip('.').lower() == data['answer'].lower(), 'RAW_PARSED_ANSWER_MISMATCH')
        expected_prompt = hashlib.sha256(PROMPT.format(target_description=query.target_phrase).encode()).hexdigest()
        require(data.get('prompt_sha256') == expected_prompt, 'PROMPT_SHA_MISMATCH')
        require((data.get('image_width'), data.get('image_height')) == (1920, 1080), 'ORIGINAL_IMAGE_DIMENSION_MISMATCH')
        value = data.get('inference_ms')
        require(type(value) in (int, float) and math.isfinite(value) and value >= 0, 'INVALID_INFERENCE_TIME')

    def _request(self, method, endpoint, payload, *, authenticated):
        headers = {'Accept': 'application/json', 'X-Space-Run-Mode': 'evaluation'}
        secret = os.environ.get(self.token_env, '').strip()
        if authenticated:
            require(bool(secret), 'SPACE_ECHO_TOKEN_ABSENT')
            headers['Authorization'] = 'Bearer ' + secret
        body = None
        if payload is not None:
            headers['Content-Type'] = 'application/json'
            body = json.dumps(payload, separators=(',', ':'), allow_nan=False).encode()
        rid = payload['request_id'] if payload else 'health-' + uuid.uuid4().hex
        transport = dict(request_id=rid, connect_started=False, connected=False, post_attempted=False,
                         request_written=False, http_status=None, response_received=False,
                         server_execution_known=False, automatic_retry=False)
        evidence = None
        if self.evidence_dir:
            self.evidence_dir.mkdir(parents=True, exist_ok=True)
            evidence = self.evidence_dir/rid
            require(not evidence.with_suffix('.transport.json').exists(), 'DUPLICATE_REQUEST_ID')
        def record():
            if evidence:
                write_json(evidence.with_suffix('.transport.json'), transport)
        parts = urlsplit(self.base_url)
        connection = http.client.HTTPConnection(parts.hostname, parts.port, timeout=self.timeout[0])
        started = time.perf_counter()
        try:
            transport['connect_started'] = True
            record()
            connection.connect()
            transport['connected'] = True
            connection.sock.settimeout(self.timeout[1])
            transport['post_attempted'] = method == 'POST'
            record()
            connection.request(method, endpoint, body=body, headers=headers)
            transport['request_written'] = True
            record()
            response = connection.getresponse()
            transport['http_status'] = response.status
            record()
            raw = response.read(8*1024*1024+1)
            require(len(raw) <= 8*1024*1024, 'OVERSIZE_RESPONSE')
            require(bool(raw), 'EMPTY_HTTP_RESPONSE')
            require(not secret or secret.encode() not in raw, 'CREDENTIAL_IN_RESPONSE_WITHHELD')
            try:
                data = json.loads(raw.decode('utf-8'))
            except (UnicodeError, ValueError):
                if evidence:
                    write_json(evidence.with_suffix('.invalid_response.json'),
                               dict(http_status=response.status, body_sha256=hashlib.sha256(raw).hexdigest(),
                                    body_bytes=len(raw)), True)
                raise LanceAPIError('INVALID_JSON_RESPONSE') from None
            require(isinstance(data, dict), 'NON_OBJECT_RESPONSE')
            elapsed = (time.perf_counter()-started)*1000
            transport.update(response_received=True, server_execution_known=response.status in (200, 422))
            if evidence:
                write_json(evidence.with_suffix('.http.json'), dict(
                    scope='DIAGNOSTIC_ONLY_LANCE', http_status=response.status,
                    request={k:v for k,v in (payload or {}).items() if k != 'image_base64'},
                    run_mode_header='evaluation', response=data, client_round_trip_ms=elapsed,
                    service_instance_id=(self.health_record or {}).get('service_instance_id')), True)
            return data, response.status, elapsed
        except (TimeoutError, OSError, http.client.HTTPException) as exc:
            category = 'TIMEOUT_UNKNOWN' if isinstance(exc, TimeoutError) else 'CONNECTION_REFUSED' if isinstance(exc, ConnectionRefusedError) else 'TRANSPORT_ERROR_UNKNOWN'
            transport['error_category'] = category
            transport['error_type'] = type(exc).__name__
            raise LanceAPIError(category) from None
        finally:
            transport['elapsed_ms'] = (time.perf_counter()-started)*1000
            record()
            connection.close()
