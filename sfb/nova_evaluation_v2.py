"""Versioned paid Nova adapter; one HTTP attempt, explicit evaluation mode."""
from decimal import Decimal, InvalidOperation
import http.client
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
import uuid

from sfb.nova_judger import (NovaJudgerClient, NovaAPIError, require, sha256,
    validate_schema, check_log_safe, write_evidence, MODEL_ID, GATEWAY_MODEL_ID,
    PROFILE_ID, PROVIDER_ENDPOINT, REGION, GENERATION, PROMPT)

CONTRACT_VERSION = 'space-nova-lite-openrouter-judger-v2'
CAMPAIGN_ID = 'nova-formal-20261028'


def money(value):
    require(type(value) in (str,int,float), 'INVALID_MONEY_TYPE')
    try:
        d=Decimal(str(value))
    except InvalidOperation:
        raise NovaAPIError('INVALID_MONEY_VALUE') from None
    require(d.is_finite() and d >= 0,'INVALID_MONEY_VALUE')
    return d


def validate_budget(b):
    require(isinstance(b,dict),'EVALUATION_BUDGET_MISSING')
    require(b.get('operation_mode')=='evaluation' and b.get('backend')=='nova'
            and b.get('campaign_id')==CAMPAIGN_ID and b.get('enabled') is True
            and b.get('call_limit')==10000 and money(b.get('budget_usd'))==Decimal('3.00'),
            'EVALUATION_CAMPAIGN_OR_LIMIT_MISMATCH')
    for key in ('total_calls','remaining_calls','pending_requests'):
        require(type(b.get(key)) is int and b[key]>=0,'INVALID_BUDGET_COUNTS')
    require(b['total_calls']+b['remaining_calls']==10000,'INCONSISTENT_CALL_COUNTS')
    for key in ('accounted_usd','provider_reported_usd','unknown_or_pending_reserved_usd',
                'remaining_usd','over_budget_usd','per_request_reservation_usd'):
        money(b.get(key))
    require(money(b['per_request_reservation_usd'])==Decimal('0.01800192'), 'RESERVATION_MISMATCH')
    require(b.get('automatic_retries')==0 and type(b.get('ready_for_new_request')) is bool,
            'BUDGET_RETRY_OR_READINESS_MISMATCH')
    return b


def validate_accounting(a):
    require(isinstance(a,dict) and a.get('campaign_id')==CAMPAIGN_ID,'ACCOUNTING_CAMPAIGN_MISMATCH')
    for k in ('reservation_usd','accounted_usd','provider_reported_usd','token_estimate_usd'):
        money(a.get(k))
    require(money(a['reservation_usd'])==Decimal('0.01800192'),'ACCOUNTING_RESERVATION_MISMATCH')
    require(money(a['accounted_usd'])>=max(money(a['provider_reported_usd']),money(a['token_estimate_usd'])),
            'ACCOUNTING_UNDERREPORTED')
    require('billing_error' in a and 'halted' in a and not a['billing_error'] and not a['halted'],
            'BILLING_OR_OUTCOME_UNKNOWN')


class NovaEvaluationClient(NovaJudgerClient):
    def __init__(self,base_url='http://127.0.0.1:18776',*,binding,evidence_dir=None,
                 timeout=(5,120),token_env='SPACE_ECHO_TOKEN'):
        p=urlsplit(base_url)
        require(p.scheme=='http' and p.hostname=='127.0.0.1' and p.port==18776
            and not p.username and not p.password and p.path in ('','/') and not p.query and not p.fragment,
            'NON_FROZEN_LOOPBACK_ENDPOINT')
        require(timeout==(5,120),'UNAPPROVED_CLIENT_TIMEOUT')
        self.base_url,self.binding,self.timeout,self.token_env=base_url.rstrip('/'),binding,timeout,token_env
        self.evidence_dir=Path(evidence_dir) if evidence_dir else None
        self.health_record=None

    def reviewed(self):
        b=self.binding
        require(b.get('review_status')=='ACTUAL_EVALUATION_HANDOFF_REVIEWED','WAIT_ACTUAL_V2_HANDOFF')
        expected=dict(contract_version=CONTRACT_VERSION,model_id=MODEL_ID,gateway_model_id=GATEWAY_MODEL_ID,
            provider_endpoint=PROVIDER_ENDPOINT,region=REGION,profile_id=PROFILE_ID,operation_mode='evaluation')
        require(all(b['health_expected'].get(k)==v for k,v in expected.items())
            and b['generation']==GENERATION and b['prompt_template']==PROMPT,'V2_HANDOFF_IDENTITY_MISMATCH')

    def _request(self,method,path,payload=None):
        self.reviewed()
        secret=os.environ.get(self.token_env,'').strip()
        require(not secret.startswith('sk-or-'),'PROJECT_TOKEN_REQUIRED_NOT_OPENROUTER_KEY')
        if method=='POST' or self.binding['health_requires_auth']:
            require(bool(secret),'SPACE_ECHO_TOKEN_ABSENT')
        headers={'Accept':'application/json','X-Space-Run-Mode':'evaluation'}
        if secret:headers['Authorization']='Bearer '+secret
        body=None
        if payload is not None:
            body=json.dumps(payload,separators=(',',':'),allow_nan=False).encode()
            headers['Content-Type']='application/json'
        rid=payload['request_id'] if payload else 'health-'+uuid.uuid4().hex
        prefix=self.evidence_dir/rid if self.evidence_dir else None
        transport=dict(request_id=rid,method=method,path=path,run_mode='evaluation',
            connected=False,post_attempted=False,request_written=False,http_status=None,
            response_received=False,server_execution_known=False,automatic_retry=False)
        def record():
            if prefix:
                p=prefix.with_suffix('.transport.json')
                # Atomic current transport state; never persist headers/body.
                check_log_safe(transport);p.parent.mkdir(parents=True,exist_ok=True)
                temp=p.with_suffix('.json.tmp')
                with temp.open('w',encoding='utf-8') as f:
                    json.dump(transport,f,indent=2);f.flush();os.fsync(f.fileno())
                os.replace(temp,p)
        require(prefix is None or not prefix.with_suffix('.transport.json').exists(),
                'REQUEST_ID_ALREADY_ATTEMPTED_NO_RETRY')
        p=urlsplit(self.base_url);c=http.client.HTTPConnection(p.hostname,p.port,timeout=self.timeout[0])
        start=time.perf_counter()
        try:
            record();c.connect();transport['connected']=True;c.sock.settimeout(self.timeout[1])
            transport['post_attempted']=method=='POST';record()
            c.request(method,path,body=body,headers=headers);transport['request_written']=True;record()
            r=c.getresponse();transport['http_status']=r.status;record()
            raw=r.read(4*1024*1024+1)
            require(bool(raw) and len(raw)<=4*1024*1024,'EMPTY_OR_OVERSIZE_RESPONSE')
            require(not secret or secret.encode() not in raw,'CREDENTIAL_IN_RESPONSE_WITHHELD')
            try:data=json.loads(raw)
            except (ValueError,UnicodeError):
                raise NovaAPIError('INVALID_JSON_OUTCOME_UNKNOWN',http_status=r.status) from None
            check_log_safe(data)
            require(isinstance(data,dict),'NON_OBJECT_RESPONSE')
            transport.update(response_received=True,server_execution_known=r.status in (200,422))
            elapsed=(time.perf_counter()-start)*1000
            if prefix:
                # Historical smoke ledger is summarized, not imported as answers.
                saved=data if method=='POST' else {k:v for k,v in data.items() if k!='smoke_budget'}
                if method=='GET' and 'smoke_budget' in data:
                    saved['smoke_budget_sha256']=sha256(json.dumps(data['smoke_budget'],sort_keys=True).encode())
                write_evidence(prefix.with_suffix('.http.json'),dict(method=method,run_mode_header='evaluation',
                    request={k:v for k,v in (payload or {}).items() if k!='image_base64'},
                    http_status=r.status,response=saved,client_round_trip_ms=elapsed,
                    service_instance_id=(self.health_record or {}).get('service_instance_id')))
            return data,r.status,elapsed
        except (TimeoutError,OSError,http.client.HTTPException) as exc:
            category='TIMEOUT_UNKNOWN' if isinstance(exc,TimeoutError) else 'CONNECTION_REFUSED' if isinstance(exc,ConnectionRefusedError) else 'TRANSPORT_ERROR_UNKNOWN'
            transport['error_category']=category
            raise NovaAPIError(category) from None
        finally:
            c.close();transport['elapsed_ms']=(time.perf_counter()-start)*1000;record()

    def health(self,require_ready=True):
        d,status,_=self._request('GET','/health')
        require(status==200,'HEALTH_HTTP_ERROR')
        self.validate_health(d,self.binding,require_ready=require_ready)
        self.health_record=d
        return d

    @staticmethod
    def validate_health(d,binding,require_ready=True):
        require(isinstance(d,dict) and all(type(d.get(k)) is type(v) and d[k]==v
                for k,v in binding['health_expected'].items()),'HEALTH_IDENTITY_MODE_OR_GENERATION_MISMATCH')
        require(isinstance(d.get('service_instance_id'),str) and bool(d['service_instance_id']),'HEALTH_INSTANCE_MISSING')
        require(type(d.get('ready')) is bool,'INVALID_HEALTH_READY')
        b=validate_budget(d.get('budget'))
        require(d.get('evaluation_budget',b)==b,'INCONSISTENT_EVALUATION_BUDGET')
        if require_ready:
            require(d['ready'] and b['ready_for_new_request'] and not b.get('halted')
                and b['pending_requests']==0 and b['remaining_calls']>0
                and money(b['remaining_usd'])>=money(b['per_request_reservation_usd']),
                'EVALUATION_NOT_READY_OR_BUDGET_EXHAUSTED')
        return d

    def answer(self,query,request_id=None):
        require(bool(request_id),'STABLE_REQUEST_ID_REQUIRED')
        # No paid inference without a fresh identity/readiness/budget GET.
        self.health()
        payload=self.build_request(query,request_id)
        d,status,elapsed=self._request('POST','/v1/judger/ask',payload)
        self.validate_response(d,status,query,request_id,self.binding,self.health_record['service_instance_id'])
        return d,elapsed

    @staticmethod
    def validate_response(d,status,query,request_id,binding,service_instance_id):
        if status!=200:
            category={400:'INVALID_REQUEST',401:'AUTH_ERROR',403:'AUTH_OR_MODE_FORBIDDEN',
                409:'DUPLICATE_OPERATION_NO_RETRY',413:'REQUEST_TOO_LARGE',422:'MODEL_OR_INPUT_FAILURE',
                429:'EVALUATION_BUDGET_EXHAUSTED',503:'SERVICE_OR_BILLING_OUTCOME_UNKNOWN'}.get(status,'HTTP_OUTCOME_UNKNOWN')
            if status==422 and d.get('error')=='truncated_answer':category='TRUNCATED_ANSWER'
            raise NovaAPIError(category,http_status=status)
        # Same exact parser/provider/correlation checks as v1; actual v2 schema
        # and constants are supplied via the separately reviewed binding.
        NovaJudgerClient.validate_response(d,status,query,request_id,binding,service_instance_id)
        require(d.get('operation_mode')=='evaluation','RESPONSE_MODE_MISMATCH')
        validate_accounting(d['evaluation_accounting'])
        require(isinstance(d.get('usage'),dict),'VALID_USAGE_REQUIRED')
        for k in ('prompt_tokens','completion_tokens'):
            require(type(d['usage'].get(k)) is int and d['usage'][k]>=0,'INVALID_USAGE')
