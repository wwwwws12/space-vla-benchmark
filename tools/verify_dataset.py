"""Portable, stdlib-only verifier. Reads ONLY files below the supplied package root.

This verifies transport integrity and associations, not a new pixel/luma calibration.
The original semantic acceptance and its limitations are preserved as provenance.
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def local(base, name):
    p = Path(name)
    if p.is_absolute() or '..' in p.parts or ':' in str(name) or '\\' in str(name):
        raise ValueError('Not a portable relative path: ' + str(name))
    p = base/p
    if not p.resolve().is_relative_to(base.resolve()):
        raise ValueError('Path escapes dataset: ' + str(name))
    return p


def physical_files(base):
    for folder, dirs, files in os.walk(base, followlinks=False):
        for name in [*dirs, *files]:
            p = Path(folder)/name
            s = p.lstat()
            if p.is_symlink() or getattr(s, 'st_file_attributes', 0) & 1024:
                raise ValueError('Link/reparse point prohibited: ' + str(p))
            if name in files:
                if s.st_nlink != 1:
                    raise ValueError('Hard link prohibited: ' + str(p))
                yield p


def validate(base):
    base = base.resolve()
    freeze = read(base/'dataset_freeze.json')
    if freeze['packaging_schema'] != 'sfb.standalone.v1':
        raise ValueError('Not a standalone package')
    for key, name in [('source_sha256_manifest','source_sha256.json'),
                      ('data_sha256_manifest','data_sha256.json'),
                      ('validation_sha256','validation.json')]:
        if digest(base/name) != freeze[key]:
            raise ValueError('Freeze binding mismatch: '+name)
    data = read(base/'data_sha256.json')
    source = read(base/'source_sha256.json')
    actual = {p.relative_to(base).as_posix() for p in physical_files(base)}
    excluded = {'dataset_freeze.json','data_sha256.json','validation.json'}
    if actual != set(data) | excluded:
        raise ValueError('Unexpected/missing package files: '+str(actual ^ (set(data)|excluded)))
    for name, expected in data.items():
        if digest(local(base, name)) != expected:
            raise ValueError('File SHA mismatch: '+name)
    for name, expected in source.items():
        if data.get(name) != expected:
            raise ValueError('Source content not covered by package: '+name)
    mapping = read(base/'_provenance/source_path_map.json')
    original_source = read(base/'_provenance/original_standard/source_sha256.json')
    if set(mapping) != set(original_source):
        raise ValueError('Incomplete historical source mapping')
    for old, entry in mapping.items():
        if data.get(entry['local_path']) != original_source[old] or entry['sha256'] != original_source[old]:
            raise ValueError('Historical source integrity mismatch: '+old)
    manifest = read(base/'dataset_manifest.json')
    contract = read(local(base, manifest['contract']))
    if digest(local(base, manifest['contract'])) != manifest['contract_sha256']:
        raise ValueError('Storage contract mismatch')
    index = read(base/'route_directory_index.json')
    frames = {}
    splits = collections.Counter()
    seen = set()
    for row in index['route_directories']:
        rid = row['route_id']; folder = local(base,row['directory'])
        rec = read(folder/'record.json')
        if rid in seen or rec['route_id'] != rid or rec['scene_id'] != manifest['scene_id']:
            raise ValueError('Route identity mismatch')
        seen.add(rid); splits[rec['split']] += 1
        if rec['track'] != 'T' or len(rec['captures']) != len(rec['steps'])+1:
            raise ValueError('Incomplete trajectory')
        if not set(contract['required_route_fields']) <= set(rec):
            raise ValueError('Missing route fields')
        for i, c in enumerate(rec['captures']):
            if c['frame_idx'] != i or c['route_id'] != rid:
                raise ValueError('Frame identity mismatch')
            if c['action_after'] != (rec['steps'][i] if i < len(rec['steps']) else None):
                raise ValueError('Action association mismatch')
            if not set(contract['required_frame_fields']) <= set(c):
                raise ValueError('Missing frame fields')
            for kind, name in c['files'].items():
                rel=local(folder,name).relative_to(base).as_posix()
                if data.get(rel) != c['sha256'][kind]:
                    raise ValueError('Record/file association mismatch')
            frames[(rid,i)] = (rec,c,row['directory'])
        for child, pattern in [('rgb','*.png'),('semantic','*.npz'),('semantic','*_labels.json'),('mask','*.png')]:
            if len(list((folder/child).glob(pattern))) != len(rec['captures']):
                raise ValueError('Extra/missing frame payload')
    if len(seen)!=manifest['routes'] or len(frames)!=manifest['frames'] or dict(splits)!=manifest['split_counts']:
        raise ValueError('Totals/splits mismatch')
    if len(seen)!=100 or dict(splits)!={'dev':20,'test':80}:
        raise ValueError('Formal 100-route split required')
    online_seen=set()
    for line in (base/'judger_frame_index.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line);key=(row['route_id'],row['frame_idx'])
        if key in online_seen or not set(row)<=set(contract['online_input_allowlist']):
            raise ValueError('Online duplicates or truth leakage')
        rec,c,folder=frames[key];online_seen.add(key)
        expected=(Path(folder)/c['files']['rgb']).as_posix()
        if row['rgb_png']!=expected or row['png_sha256']!=c['sha256']['rgb'] or row['target_description']!=rec['target_description'] or row['split']!=rec['split']:
            raise ValueError('Online association mismatch')
    if online_seen!=set(frames):raise ValueError('Online index incomplete')
    truth_seen=set()
    for line in (base/'truth_EVALUATION_ONLY.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line);key=(row['route_id'],row['frame_idx'])
        if key in truth_seen:raise ValueError('Duplicate truth')
        rec,c,folder=frames[key];truth_seen.add(key)
        for kind in ('mask','semantic'):
            if row[kind]!=(Path(folder)/c['files'][kind]).as_posix():
                raise ValueError('Truth path mismatch')
    if truth_seen!=set(frames):raise ValueError('Truth index incomplete')
    return dict(status='STANDALONE_INTEGRITY_PASS',scene_id=manifest['scene_id'],
        routes=len(seen),frames=len(frames),split_counts=dict(splits),files=len(actual),
        junctions=0,symlinks=0,hardlinks=0,all_file_sha256_verified=True,
        external_files_opened=0,source_bindings=len(mapping),
        strict_new_capture_metadata_pass=read(base/'validation.json')['strict_new_capture_metadata_pass'])


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent/'standard_v1')
    p.add_argument('--dataset',type=Path)
    a=p.parse_args()
    paths=[a.dataset] if a.dataset else sorted(a.root.glob('*/*/*/dataset_freeze.json'))
    if not paths:raise ValueError('No completed standalone dataset found')
    for path in paths:
        base=path if a.dataset else path.parent
        print(json.dumps(validate(base)),flush=True)


if __name__=='__main__':main()
