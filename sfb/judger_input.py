"""Credential-free request preparation only; no model choice or answer parsing."""
import base64
import hashlib
from pathlib import Path
import uuid

def prepare_request(folder, sample, episode_id, prompt_profile_id):
    if not prompt_profile_id or 'PENDING' in prompt_profile_id.upper():
        raise ValueError('A supplied frozen prompt profile is required; do not invent one')
    folder=Path(folder).resolve()
    image=(folder/sample['image_path']).resolve()
    if not image.is_relative_to(folder): raise ValueError('Image path escapes sample folder')
    data=image.read_bytes()
    if hashlib.sha256(data).hexdigest()!=sample['sha256']:
        raise ValueError('JPEG checksum mismatch')
    if sample['mime_type']!='image/jpeg' or sample['rgb_order']!='RGB' or sample['jpeg_quality']!=85:
        raise ValueError('Frozen image encoding mismatch')
    return {'protocol_version':'space-demo-inference-v1','request_id':'judger-'+uuid.uuid4().hex,
            'episode_id':episode_id,'step_idx':sample['step_idx'],
            'target_phrase':sample['target_phrase'],'prompt_profile_id':prompt_profile_id,
            'image':{'encoding':'base64','mime_type':'image/jpeg','width':sample['width'],
                     'height':sample['height'],'sha256':sample['sha256'],
                     'data_base64':base64.b64encode(data).decode('ascii')}}
