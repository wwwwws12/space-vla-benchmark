"""Aggregate the supplied numerical rollout export. No models or rendering."""
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method', choices=['TRACE','delay_only','oracle_visibility','Baseline'], default='TRACE')
    parser.add_argument('--all-grid', action='store_true', help='Display all saved K/q cells; never select parameters')
    args = parser.parse_args()
    frozen=json.loads((ROOT/'protocols/evaluation.json').read_text(encoding='utf-8'))['selection']['frozen']
    groups=defaultdict(list)
    with gzip.open(ROOT/'results/rollouts.jsonl.gz','rt',encoding='utf-8') as f:
        for line in f:
            r=json.loads(line)
            if r['method']!=args.method: continue
            if not args.all_grid and args.method!='Baseline' and [r['K'],r['q']]!=frozen[r['world']]: continue
            groups[(r['lighting'],r['world'],r['model'],r['K'],r['q'])].append(r)
    print('| Light | World | Model | K/q | n | Successes | SR (%) | SPL | Queries |')
    print('|---|---|---|---|---:|---:|---:|---:|---:|')
    for (light,world,model,k,q),rows in sorted(groups.items(),key=lambda x:str(x[0])):
        n=len(rows); successes=sum(r['SR'] for r in rows)
        print(f'| {light} | {world} | {model} | {k}/{q} | {n} | {successes} | {100*successes/n:.2f} | '
              f'{sum(r["SPL"] for r in rows)/n:.4f} | {sum(r["logical_queries"] for r in rows)/n:.3f} |')

if __name__=='__main__':main()
