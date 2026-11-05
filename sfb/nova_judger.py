"""Nova Lite 1.0/OpenRouter adapter: offline wire validation and GET only.

Paid inference is deliberately unavailable in this precheck revision. Cloud model
mapping/processing remains provider-declared, never independently verified.
"""
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

from sfb.trace_online import JudgerQuery

MODEL_ID = 'amazon.nova-lite-v1:0'
GATEWAY_MODEL_ID = 'amazon/nova-lite-v1'
PROVIDER_ENDPOINT = 'amazon-bedrock/eu-west-1'
REGION = 'eu-west-1'
PROFILE_ID = 'nova-lite-v1-visible-topk1-openrouter-v1'
CONTRACT_VERSION = 'space-nova-lite-openrouter-judger-v1'
PROMPT = 'Is {target_description} visible in this image? Answer Yes or No only.'
GENERATION = dict(max_tokens=8,temperature=0.00001,top_k=1)
REQUEST_FIELDS = frozenset(('request_id','episode_id','step_idx','target_description',
                            'image_base64','jpeg_sha256','profile_id'))


class NovaAPIError(RuntimeError):
    def __init__(self, category, *, http_status=None):
        self.category,self.http_status = category,http_status
        super().__init__(category+(f' (HTTP {http_status})' if http_status else ''))


def require(ok, category):
    if not ok:
        raise NovaAPIError(category)


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def validate_schema(value, schema):
    """Actual handoff scalar/object schema, including nullable union types."""
    if 'const' in schema:
        require(type(value) is type(schema['const']) and value == schema['const'],'SCHEMA_CONST_MISMATCH')
    if 'enum' in schema:
        require(value in schema['enum'],'SCHEMA_ENUM_MISMATCH')
    kinds = schema.get('type',[])
    if isinstance(kinds,str):
        kinds = [kinds]
    checks = dict(object=lambda x:isinstance(x,dict),string=lambda x:isinstance(x,str),
        integer=lambda x:type(x) is int,number=lambda x:type(x) in (int,float) and math.isfinite(x),
        boolean=lambda x:type(x) is bool,null=lambda x:x is None,array=lambda x:isinstance(x,list))
    if kinds:
        require(all(k in checks for k in kinds) and any(checks[k](value) for k in kinds),'SCHEMA_TYPE_MISMATCH')
    if isinstance(value,dict):
        require(set(schema.get('required',[])) <= set(value),'SCHEMA_REQUIRED_FIELD_MISSING')
        props = schema.get('properties',{})
        if schema.get('additionalProperties') is False:
            require(set(value) <= set(props),'UNEXPECTED_REQUEST_FIELD')
        for k,v in value.items():
            if k in props:
                validate_schema(v,props[k])
    if isinstance(value,str):
        require(schema.get('minLength',0) <= len(value) <= schema.get('maxLength',float('inf')),'SCHEMA_STRING_LENGTH')
        if 'pattern' in schema:
            require(re.search(schema['pattern'],value) is not None,'SCHEMA_STRING_PATTERN')
    if type(value) in (int,float):
        require(math.isfinite(value) and value >= schema.get('minimum',-float('inf')),'SCHEMA_NUMBER_RANGE')


def check_log_safe(value):
    """Refuse evidence containing credential material or serialized image data."""
    forbidden = {'image_base64','authorization','api_key','openrouter_api_key','bearer_token','access_token'}
    if isinstance(value,dict):
        for k,v in value.items():
            require(not (k.lower() in forbidden and isinstance(v,str)),'SENSITIVE_EVIDENCE_WITHHELD')
            check_log_safe(v)
    elif isinstance(value,list):
        for v in value:
            check_log_safe(v)
    elif isinstance(value,str):
        require(not re.search(r'(?i)\bbearer\s+\S+|sk-or(?:-v1)?-[A-Za-z0-9_-]+',value),'SENSITIVE_EVIDENCE_WITHHELD')
        token = os.environ.get('SPACE_ECHO_TOKEN','').strip()
        require(not token or token not in value,'SENSITIVE_EVIDENCE_WITHHELD')


def write_evidence(path, value):
    check_log_safe(value)
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
        f.write('\n');f.flush();os.fsync(f.fileno())


def budget_snapshot(health):
    b = health.get('budget')
    require(isinstance(b,dict) and isinstance(b.get('calls'),list),'BUDGET_SNAPSHOT_MISSING')
    require(b.get('max_calls_per_model') == 16 and b.get('max_total_calls') == 32
            and b.get('nova_budget_usd') == 1,'SMOKE_BUDGET_CONTRACT_CHANGED')
    calls = b['calls']
    nova = [x for x in calls if x.get('backend') == 'nova']
    require(len(nova) <= 16 and len(calls) <= 32,'SMOKE_LEDGER_LIMIT_EXCEEDED')
    reserved = [x.get('reserved_usd') for x in nova]
    require(all(type(x) in (int,float) and math.isfinite(x) and x >= 0 for x in reserved),'INVALID_RESERVED_BUDGET')
    return dict(nova_calls=len(nova),total_calls=len(calls),remaining_nova_smoke_calls=min(16-len(nova),32-len(calls)),
        nova_local_reserved_usd=sum(reserved),max_local_reserved_usd=1,halted=bool(b.get('halted')),
        ledger_sha256=sha256(json.dumps(calls,sort_keys=True).encode()))


class NovaJudgerClient:
    """Current release cannot transmit any POST, even with a valid project token."""
    def __init__(self, base_url='http://127.0.0.1:18776', *, binding, evidence_dir=None,
                 timeout=(5.,60.), token_env='SPACE_ECHO_TOKEN'):
        p = urlsplit(base_url)
        require(p.scheme == 'http' and p.hostname == '127.0.0.1' and p.port is not None
                and p.path in ('','/') and not p.username and not p.password and not p.query and not p.fragment,
                'NON_LOOPBACK_ENDPOINT')
        require(timeout == (5.,60.) or timeout == (5,60),'UNAPPROVED_TIMEOUT')
        self.base_url,self.binding = base_url.rstrip('/'),binding
        self.evidence_dir = Path(evidence_dir) if evidence_dir else None
        self.timeout,self.token_env = timeout,token_env
        self.health_record = None

    def reviewed(self):
        b = self.binding
        require(b.get('review_status') == 'ACTUAL_HANDOFF_REVIEWED','WAIT_ACTUAL_NOVA_HANDOFF')
        expected = dict(model_id=MODEL_ID,gateway_model_id=GATEWAY_MODEL_ID,provider_endpoint=PROVIDER_ENDPOINT,
                        region=REGION,profile_id=PROFILE_ID,contract_version=CONTRACT_VERSION,generation=GENERATION,
                        campaign_match_verified=False)
        require(all(b.get(k) == v for k,v in expected.items()),'HANDOFF_IDENTITY_MISMATCH')

    def health(self):
        self.reviewed()
        p = urlsplit(self.base_url)
        c = http.client.HTTPConnection(p.hostname,p.port,timeout=self.timeout[0])
        started = time.perf_counter()
        transport = dict(method='GET',path='/health',paid_POSTs=0,automatic_retries=0,http_status=None)
        try:
            c.connect();c.sock.settimeout(self.timeout[1])
            headers = {'Accept':'application/json'}
            if self.binding['health_requires_auth']:
                secret = os.environ.get(self.token_env,'').strip()
                require(bool(secret) and not secret.startswith('sk-or-'),'PROJECT_TOKEN_REQUIRED_NOT_OPENROUTER_KEY')
                headers['Authorization'] = 'Bearer '+secret
            c.request('GET','/health',headers=headers)
            r = c.getresponse();transport['http_status'] = r.status
            raw = r.read(2*1024*1024+1)
            require(len(raw) <= 2*1024*1024 and bool(raw),'INVALID_HEALTH_BODY')
            require(r.status == 200,'HEALTH_HTTP_ERROR')
            try:
                data = json.loads(raw)
            except (ValueError,UnicodeError):
                raise NovaAPIError('INVALID_HEALTH_JSON') from None
            safe = self.validate_health(data,self.binding)
            self.health_record = data
            if self.evidence_dir:
                write_evidence(self.evidence_dir/('health-'+uuid.uuid4().hex+'.json'),safe)
            return safe
        except (TimeoutError,OSError,http.client.HTTPException) as exc:
            category = 'HEALTH_TIMEOUT' if isinstance(exc,TimeoutError) else 'HEALTH_CONNECTION_ERROR'
            transport['error_category'] = category
            raise NovaAPIError(category) from None
        finally:
            c.close();transport['elapsed_ms'] = (time.perf_counter()-started)*1000
            if self.evidence_dir:
                write_evidence(self.evidence_dir/('health-transport-'+uuid.uuid4().hex+'.json'),transport)

    @staticmethod
    def validate_health(data, binding):
        require(isinstance(data,dict),'INVALID_HEALTH_OBJECT')
        require(all(type(data.get(k)) is type(v) and data.get(k) == v
                    for k,v in binding['health_expected'].items()),'HEALTH_IDENTITY_MODE_OR_GENERATION_MISMATCH')
        require(isinstance(data.get('service_instance_id'),str) and bool(data['service_instance_id']),'HEALTH_INSTANCE_MISSING')
        # This is a cloud API: model_loaded=false is expected, not a failure.
        safe = {k:data[k] for k in binding['health_expected']}
        safe.update(service_instance_id=data['service_instance_id'],budget_snapshot=budget_snapshot(data),
            status='NOVA_HEALTH_IDENTITY_PASS',cloud_weights_independently_verified=False,
            local_model_POSTs=0,formal_evaluation_completed=False)
        check_log_safe(safe)
        return safe

    def build_request(self, query: JudgerQuery, request_id=None):
        """Construct exact seven-field payload in memory only; never log it."""
        self.reviewed()
        phrase = query.target_phrase
        require(isinstance(phrase,str) and phrase.strip() == phrase and 1 <= len(phrase) <= 256
                and not any(ord(c) < 32 or ord(c) == 127 for c in phrase),'INVALID_TARGET_DESCRIPTION')
        image = Path(query.jpeg_path).read_bytes()
        require(image.startswith(b'\xff\xd8') and sha256(image) == query.jpeg_sha256,'JPEG_BYTES_OR_SHA_MISMATCH')
        payload = dict(request_id=request_id or 'nova-'+uuid.uuid4().hex,episode_id=query.episode_id,
            step_idx=query.step_idx,target_description=phrase,image_base64=base64.b64encode(image).decode('ascii'),
            jpeg_sha256=query.jpeg_sha256,profile_id=PROFILE_ID)
        require(set(payload) == REQUEST_FIELDS,'REQUEST_FIELD_SET_MISMATCH')
        validate_schema(payload,self.binding['request_schema'])
        return payload

    def answer(self, query: JudgerQuery, request_id=None):
        raise NovaAPIError('PAID_INFERENCE_DISABLED_PRECHECK_ONLY')

    @staticmethod
    def validate_response(data, status, query, request_id, binding, service_instance_id):
        """Offline validation only; error answers never become binary judgments."""
        require(isinstance(data,dict),'NON_OBJECT_RESPONSE')
        if status != 200:
            categories = {400:'HTTP_BAD_REQUEST',401:'HTTP_AUTH_ERROR',403:'EVALUATION_NOT_ENABLED_OR_FORBIDDEN',
                409:'DUPLICATE_REQUEST_ID',413:'REQUEST_TOO_LARGE',422:'INVALID_MODEL_OR_INPUT_RESPONSE',
                429:'SMOKE_BUDGET_EXHAUSTED',503:'SERVICE_OR_OUTCOME_UNKNOWN'}
            category = 'TRUNCATED_ANSWER' if status == 422 and data.get('error') == 'truncated_answer' else categories.get(status,'HTTP_ERROR')
            raise NovaAPIError(category,http_status=status)
        validate_schema(data,binding['success_schema'])
        expected = dict(binding['response_expected'],request_id=request_id,episode_id=query.episode_id,
            step_idx=query.step_idx,target_description=query.target_phrase,jpeg_sha256=query.jpeg_sha256,
            serialized_jpeg_sha256=query.jpeg_sha256,service_instance_id=service_instance_id,
            prompt_sha256=sha256(PROMPT.format(target_description=query.target_phrase).encode()))
        require(all(type(data.get(k)) is type(v) and data.get(k) == v for k,v in expected.items()),'RESPONSE_IDENTITY_OR_CORRELATION_MISMATCH')
        require(data['parse_status'] == 'parsed_exact','INVALID_PARSE_STATUS')
        require(data['stop_reason'] not in ('length','max_tokens','content_filter','refusal'),'TRUNCATED_OR_REFUSED_ANSWER')
        raw = data['raw_answer'].strip().lower()
        require(raw in ('yes','no','yes.','no.') and raw.rstrip('.') == data['answer'].lower(),'INVALID_EXACT_ANSWER')
        require((data['image_width'],data['image_height']) == (1920,1080),'IMAGE_DIMENSION_MISMATCH')
        require(bool(data['gateway_generation_id']) and data['aws_request_id'] is None,'GATEWAY_ID_OR_FABRICATED_AWS_ID')
        require(data.get('campaign_match_verified',False) is False,'UNSUPPORTED_CAMPAIGN_MATCH_CLAIM')
        if 'generation' in data:
            require(data['generation'] == GENERATION,'GENERATION_MISMATCH')
        require(data['estimated_cost_usd'] is None or data['estimated_cost_usd'] >= 0,'INVALID_COST')
        check_log_safe(data)
