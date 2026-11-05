"""Read-only byte-integrity check against the supplied SHA256SUMS."""
import hashlib
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    count=0;errors=[]
    for line in (ROOT/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected,name=line.split('  ',1)
        p=(ROOT/name).resolve()
        if not p.is_relative_to(ROOT) or not p.is_file():
            errors.append(name);continue
        with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=expected:errors.append(name)
        count+=1
    print(f'Files read: {count}; mismatches/missing: {len(errors)}')
    for name in errors:print(name)
    return 1 if errors else 0

if __name__=='__main__':sys.exit(main())
