"""Versioned leading-label parser; no HTTP, model, renderer or truth access."""
import re

PARSER_ID='judger-leading-binary-answer-v1'


def leading_yes_no(raw):
    if not isinstance(raw,str):return None
    text=raw.strip()
    m=re.match(r'^(yes|no)(?=$|[\s.,!?:;])',text,re.IGNORECASE)
    if not m:return None
    label=m.group(1).lower();tail=text[m.end():]
    opposite='no' if label=='yes' else 'yes'
    if re.search(r'\b'+opposite+r'\b',tail,re.IGNORECASE):return None
    if re.search(r"\b(?:cannot determine|can't determine|not sure|uncertain|unable to determine|cannot answer|can't answer|refuse)\b",tail,re.IGNORECASE):return None
    if label=='yes' and re.search(r"\b(?:not visible|isn't visible|cannot see|can't see|not present|not in (?:the|this) image)\b",tail,re.IGNORECASE):return None
    return label.capitalize()
