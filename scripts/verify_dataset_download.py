"""Verify extracted sfb.download.v1 groups with Python's standard library."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(root):
    root = root.resolve()
    manifests = ([root / 'dataset_manifest.json'] if (root / 'dataset_manifest.json').is_file()
                 else sorted(root.glob('**/dataset_manifest.json')))
    groups = []
    checked = 0
    for path in manifests:
        manifest = json.loads(path.read_text(encoding='utf-8'))
        if manifest.get('schema') != 'sfb.download.group.v1':
            continue
        base = path.parent
        for part in manifest['parts']:
            inventory = base / part['inventory']
            data = json.loads(inventory.read_text(encoding='utf-8'))
            if data['group_id'] != manifest['id']:
                raise ValueError('Group inventory mismatch')
            for item in data['files']:
                target = (base / item['path']).resolve()
                if not target.is_relative_to(base.resolve()) or not target.is_file():
                    raise ValueError('Missing or unsafe file: ' + item['path'])
                if target.stat().st_size != item['bytes']:
                    raise ValueError('Size mismatch: ' + item['path'])
                with target.open('rb') as f:
                    digest = hashlib.file_digest(f, 'sha256').hexdigest()
                if digest != item['sha256']:
                    raise ValueError('SHA256 mismatch: ' + item['path'])
                checked += 1
        groups.append(manifest['id'])
    if not groups:
        raise ValueError('No sfb.download.v1 group manifest found')
    return {'status': 'SHA256_PASS', 'groups': groups, 'files': checked}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='Extracted group or space-vla-dataset-v1 directory')
    args = parser.parse_args()
    print(json.dumps(verify(args.directory)))
