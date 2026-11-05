"""Unchanged Lance inference transport; separate leading-label interpretation."""
import base64
from copy import deepcopy
import hashlib

from sfb.judger_prefix_answer_v1 import leading_yes_no,PARSER_ID
from sfb.lance_judger import (LanceJudgerClient,LanceAPIError,validate_schema,require,
    MODEL_ID,MODEL_REVISION,PROFILE_ID,PROMPT,REQUEST_FIELDS)


class InvalidLeadingAnswer(LanceAPIError):
    pass


def interpret_response(data,status,query,request_id,binding,instance):
    require(isinstance(data,dict),'NON_OBJECT_RESPONSE')
    if status not in (200,422):
        # Preserve the original fatal status semantics; never extract from an
        # authentication/service/unknown response even if it contains Yes/No.
        LanceJudgerClient.validate_response(data,status,query,request_id,binding,instance)
    schema=deepcopy(binding['success_schema'])
    schema['properties']['status']={'type':'string'}
    schema['properties']['answer']={}
    validate_schema(data,schema)
    expected={k:v for k,v in binding['response_expected'].items() if k!='status'}
    expected.update(request_id=request_id,episode_id=query.episode_id,step_idx=query.step_idx,
        target_description=query.target_phrase,jpeg_sha256=query.jpeg_sha256,
        model_id=MODEL_ID,model_revision=MODEL_REVISION,profile_id=PROFILE_ID,
        service_instance_id=instance,image_width=1920,image_height=1080,
        prompt_sha256=hashlib.sha256(PROMPT.format(target_description=query.target_phrase).encode()).hexdigest())
    require(bool(instance) and all(type(data.get(k)) is type(v) and data[k]==v for k,v in expected.items()),
            'PREFIX_RESPONSE_IDENTITY_OR_CORRELATION_MISMATCH')
    if status==422:
        details=data.get('runtime_details',{});tokens=details.get('generation_token_ids')
        require(data.get('status')=='error' and data.get('answer') is None
            and data.get('error')=='truncated_answer' and data.get('parse_status')=='truncated_answer'
            and data.get('generation')==binding['generation'] and isinstance(tokens,list) and bool(tokens)
            and all(type(v) is int and v>=0 for v in tokens)
            and details.get('stop_reason')==data['stop_reason']=='max_tokens',
            'UNRECOGNIZED_422_NOT_PREFIX_RECOVERABLE')
    else:
        require(data['status']=='ok' and data.get('answer') in (None,'Yes','No'),
                'UNRECOGNIZED_200_STATUS_OR_ANSWER')
        require(data['stop_reason'] not in ('refusal','content_filter'),'REFUSED_RESPONSE_NOT_PREFIX_RECOVERABLE')
        if 'generation' in data:require(data['generation']==binding['generation'],'PREFIX_GENERATION_MISMATCH')
    answer=leading_yes_no(data['raw_answer'])
    if answer is None:raise InvalidLeadingAnswer('NO_UNAMBIGUOUS_LEADING_ANSWER',http_status=status)
    require(status!=200 or data.get('answer') in (None,answer),'PREFIX_SERVER_LABEL_CONFLICT')
    return dict(parser_id=PARSER_ID,derived_answer=answer,raw_answer=data['raw_answer'],
        source_http_status=status,source_parse_status=data['parse_status'],
        source_stop_reason=data['stop_reason'],format_noncompliant=status!=200
            or data['raw_answer'].strip().lower() not in ('yes','no','yes.','no.'))


class PrefixLanceClient(LanceJudgerClient):
    def answer(self,query,request_id=None):
        self._reviewed()
        require(self.health_record is not None and bool(request_id),'HEALTH_OR_STABLE_REQUEST_ID_MISSING')
        require(isinstance(query.target_phrase,str) and query.target_phrase.strip()==query.target_phrase
            and 1<=len(query.target_phrase)<=256 and not any(ord(c)<32 or ord(c)==127 for c in query.target_phrase),
            'INVALID_TARGET_DESCRIPTION')
        require(type(query.step_idx) is int and query.step_idx>=0 and bool(query.episode_id),'INVALID_FRAME_IDENTITY')
        image=query.jpeg_path.read_bytes()
        require(image.startswith(b'\xff\xd8') and hashlib.sha256(image).hexdigest()==query.jpeg_sha256,
                'JPEG_BYTES_OR_SHA_MISMATCH')
        payload=dict(request_id=request_id,episode_id=query.episode_id,step_idx=query.step_idx,
            target_description=query.target_phrase,image_base64=base64.b64encode(image).decode('ascii'),
            jpeg_sha256=query.jpeg_sha256,profile_id=PROFILE_ID)
        require(set(payload)==REQUEST_FIELDS,'REQUEST_FIELD_SET_MISMATCH')
        validate_schema(payload,self.binding['request_schema'])
        data,status,elapsed=self._request('POST','/v1/judger/ask',payload,authenticated=True)
        parsed=interpret_response(data,status,query,request_id,self.binding,self.health_record['service_instance_id'])
        return dict(**parsed,client_RTT_ms=elapsed)
