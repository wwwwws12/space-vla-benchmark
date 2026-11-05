"""Test-phase interpretation using unchanged model HTTP transports and prompt.

Raw HTTP evidence is never edited. Only the separate derived answer uses the
previously approved leading-label rule. No model call occurs at import time.
"""
import base64
from copy import deepcopy
import hashlib
import time

from sfb.judger_prefix_answer_v1 import leading_yes_no, PARSER_ID
from sfb.judger_online import OnlineJudgerClient, JudgerAPIError, PILOT_PROFILE_ID
from sfb.lance_prefix_v3 import interpret_response as interpret_lance, InvalidLeadingAnswer
from sfb.nova_evaluation_v2 import NovaEvaluationClient, validate_accounting
from sfb.nova_judger import validate_schema, check_log_safe, PROMPT, REQUEST_FIELDS


class InvalidModelAnswer(RuntimeError):
    category = 'NO_UNAMBIGUOUS_LEADING_ANSWER'


def require(ok, category):
    if not ok:
        raise ValueError(category)


def interpret(model, data, status, query, request_id, binding, instance):
    check_log_safe(data)
    if model == 'lance':
        try:
            return interpret_lance(data, status, query, request_id, binding, instance)
        except InvalidLeadingAnswer:
            raise InvalidModelAnswer() from None
    require(isinstance(data, dict) and bool(instance), 'RESPONSE_OBJECT_OR_INSTANCE_MISSING')
    if status not in (200, 422):
        # Keep all existing auth/quota/unknown/billing error meanings.
        if model == 'nova':
            NovaEvaluationClient.validate_response(data, status, query, request_id, binding, instance)
        raise ValueError('HTTP_ERROR_' + str(status))
    expected = dict(request_id=request_id, episode_id=query.episode_id,
                    step_idx=query.step_idx, target_description=query.target_phrase,
                    jpeg_sha256=query.jpeg_sha256, service_instance_id=instance,
                    image_width=1920, image_height=1080,
                    prompt_sha256=hashlib.sha256(PROMPT.format(target_description=query.target_phrase).encode()).hexdigest())
    if model == 'qwen':
        from sfb.judger_online import MODEL_ID, MODEL_REVISION, USAGE_SCOPE
        expected.update(model_id=MODEL_ID, model_revision=MODEL_REVISION,
                        profile_id=PILOT_PROFILE_ID, usage_scope=USAGE_SCOPE,
                        prompt_version='visible-question-v1')
        schema = deepcopy(binding['response_schema'])
    else:
        expected.update(binding['response_expected'])
        expected['serialized_jpeg_sha256'] = query.jpeg_sha256
        schema = deepcopy(binding['success_schema'])
    require(all(type(data.get(k)) is type(v) and data[k] == v for k, v in expected.items()),
            'RESPONSE_IDENTITY_OR_CORRELATION_MISMATCH')
    schema['properties']['status'] = {'type': 'string'}
    schema['properties']['answer'] = {}
    validate_schema(data, schema)
    if status == 422:
        # These are the actual documented model-format errors, not input errors.
        code = 'unparseable_answer' if model == 'qwen' else 'truncated_answer'
        require(data.get('status') == 'error' and data.get('answer') is None
                and data.get('error') == code, 'UNRECOGNIZED_422_NOT_PREFIX_RECOVERABLE')
        if model == 'nova':
            require(data.get('parse_status') == code and data.get('stop_reason') in ('length', 'max_tokens'),
                    'NOVA_TRUNCATION_METADATA_MISMATCH')
    else:
        require(data.get('status') == 'ok' and data.get('answer') in (None, 'Yes', 'No'),
                'INVALID_RESPONSE_STATUS_OR_LABEL')
        require(data.get('stop_reason') not in ('refusal', 'content_filter', 'length', 'max_tokens'),
                'UNEXPECTED_TRUNCATION_OR_REFUSAL')
    if model == 'nova':
        # A completed answer must also have settled, known accounting.
        validate_accounting(data['evaluation_accounting'])
        require(isinstance(data.get('usage'), dict) and all(type(data['usage'].get(k)) is int
                and data['usage'][k] >= 0 for k in ('prompt_tokens', 'completion_tokens')),
                'INVALID_USAGE')
        require(bool(data.get('gateway_generation_id')) and data.get('aws_request_id') is None,
                'MISSING_GATEWAY_GENERATION_ID')
    answer = leading_yes_no(data['raw_answer'])
    if answer is None:
        raise InvalidModelAnswer()
    require(status != 200 or data.get('answer') in (None, answer), 'SERVER_DERIVED_LABEL_CONFLICT')
    # Validate the remaining original success contract through a copy. The copy
    # is never persisted as a server response; only parser-related fields differ.
    checked = deepcopy(data)
    checked.update(status='ok', answer=answer, raw_answer=answer)
    if model == 'qwen':
        OnlineJudgerClient._validate_response(checked, 200, query, request_id,
                                              query.jpeg_sha256, PILOT_PROFILE_ID)
    else:
        checked.update(parse_status='parsed_exact', stop_reason='stop')
        NovaEvaluationClient.validate_response(checked, 200, query, request_id, binding, instance)
    return dict(parser_id=PARSER_ID, derived_answer=answer, raw_answer=data['raw_answer'],
                source_http_status=status, source_parse_status=data.get('parse_status'),
                source_stop_reason=data.get('stop_reason'), format_noncompliant=status != 200
                or data['raw_answer'].strip().lower() not in ('yes', 'no', 'yes.', 'no.'))


def send(model, client, query, request_id, binding):
    """One attempt. Caller has verified health and durably reserved this ID."""
    require(client.health_record is not None, 'HEALTH_NOT_VERIFIED')
    if model == 'nova':
        payload = client.build_request(query, request_id)
    else:
        image = query.jpeg_path.read_bytes()
        require(image.startswith(b'\xff\xd8') and hashlib.sha256(image).hexdigest() == query.jpeg_sha256,
                'JPEG_BYTES_OR_SHA_MISMATCH')
        payload = dict(request_id=request_id, episode_id=query.episode_id, step_idx=query.step_idx,
                       target_description=query.target_phrase, image_base64=base64.b64encode(image).decode('ascii'),
                       jpeg_sha256=query.jpeg_sha256, profile_id=(PILOT_PROFILE_ID if model == 'qwen'
                                                                else binding['profile_id']))
        validate_schema(payload, binding['request_schema'])
    require(set(payload) == REQUEST_FIELDS, 'SEVEN_FIELD_REQUEST_REQUIRED')
    started = time.perf_counter()
    if model == 'nova':
        data, status, _ = client._request('POST', '/v1/judger/ask', payload)
    elif model == 'lance':
        data, status, _ = client._request('POST', '/v1/judger/ask', payload, authenticated=True)
    else:
        try:
            data, status = client._request('POST', '/v1/judger/ask', payload, authenticated=True)
        except JudgerAPIError:
            # Qwen transport persists the complete HTTP response before raising
            # on a non-2xx. Only its actual retained model-format 422 can proceed.
            path = client.evidence_dir / (request_id + '.http.json')
            if not path.exists():
                raise
            import json
            saved = json.loads(path.read_text(encoding='utf-8'))
            if saved['http_status'] != 422:
                raise
            data, status = saved['response'], saved['http_status']
    parsed = interpret(model, data, status, query, request_id, binding,
                       client.health_record['service_instance_id'])
    return dict(**parsed, client_RTT_ms=(time.perf_counter() - started) * 1000)
