#!/usr/bin/env python3
"""Bounded interactive sample: compile existing gates, never re-observe pixels.

Every supported brief and nonempty subset is enumerated. The browser selects
an exact compiled case, not a port/reinterpretation of the Python contract.
No model calls. No original, prompt, frozen vocab or sealed input writes.
"""
import hashlib
import itertools
import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runtime.local_mvp import run, compute_coverage, SEALED_SHA256
from runtime.brief_gate import gate
from runtime.export_public import VERDICT_EN, PENDING_EN, translate_reason, FORBIDDEN_MARKERS

DEST = ROOT / 'ui/sample/cases.json'
SCENES = {'both': [{'slot':'hero','scene':'product'}, {'slot':'detail','scene':'detail'}],
          'product': [{'slot':'hero','scene':'product'}],
          'detail': [{'slot':'detail','scene':'detail'}]}
EDGES = (1000, 1400, 2400)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compile_cases():
    local, error = run()
    if error:
        raise ValueError(error)
    recorded = json.loads((ROOT/'ui/runtime/results.json').read_text())
    public_by_key = {i['asset_key']:i for i in recorded['items']}
    base = json.loads((ROOT/'briefs/brief-v1.json').read_text())
    assets = []
    for item in local['items']:
        p = public_by_key[item['asset_key']]
        image_path = ROOT/'ui/runtime'/p['image']
        if digest(image_path) != item['manifest']['sha256']:
            raise ValueError('Public image binding mismatch: '+item['asset_key'])
        if p['observed'] != item['observed'] or p['evidence_state'] != item['evidence_state']:
            raise ValueError('Recorded public observation mismatch')
        assets.append({k:deepcopy(p[k]) for k in ('asset_key','observed','evidence_state','manifest')})
        assets[-1]['image'] = '../runtime/'+p['image']
        assets[-1]['old'] = deepcopy(item['old'])
    profiles = {}
    variations = [(None,None,None)] + list(itertools.product(SCENES, (True,False), EDGES))
    for scenes, no_people, edge in variations:
        brief = None if scenes is None else deepcopy(base)
        pid = 'missing' if scenes is None else f'{scenes}:{int(no_people)}:{edge}'
        if brief is not None:
            brief['brief_id'] = 'sample:'+pid
            brief['required_scenes'] = SCENES[scenes]
            brief['hard_constraints']['no_people'] = no_people
            brief['hard_constraints']['min_long_edge'] = edge
        decided = [gate(i,brief) for i in local['items']]
        exported = []
        for it in decided:
            used = it['signals_used']
            sources = {k:it['signal_sources'][k] for k in used if k in it['signal_sources']}
            if any('mvp-stub' in str(s) for s in sources.values()):
                raise ValueError('A supported case consulted a stub; narrow the sample')
            exported.append({
                'asset_key':it['asset_key'], 'bucket':it['bucket'],
                'verdict':VERDICT_EN[it['verdict']], 'reason':translate_reason(it['reason']),
                'pending':[PENDING_EN[p] for p in it['pending']],
                'signals_used':used, 'signal_sources':sources,
                'consulted_signals':{k:it['signals'].get(k) for k in used},
            })
        subsets = {}
        for mask in range(1,1 << len(assets)):
            subset = [it for i,it in enumerate(decided) if mask & (1 << i)]
            summary = {b:sum(it['bucket']==b for it in subset) for b in ('Shortlist','Needs Review','Remaining')}
            summary['total'] = len(subset)
            subsets[str(mask)] = {'summary':summary,
                'coverage':compute_coverage(brief or {},subset)}
        # Resolver values are not published; never invent who owns a question.
        public_brief = None if brief is None else {k:v for k,v in brief.items() if k != 'resolvers'}
        profiles[pid] = {'brief':public_brief, 'decisions':exported, 'subsets':subsets}
    payload = {'schema_version':1, 'mode':'sample_case',
        'observation_mode':'recorded', 'model_calls':0,
        'sealed_sha256':SEALED_SHA256,
        'build_sources':{p:digest(ROOT/p) for p in (
            'runtime/brief_gate.py','runtime/vocab.py','agent/loop.py',
            'runtime/local_mvp.py','fixtures/smallset/signals.json',
            'fixtures/smallset/sealed-public.json','briefs/brief-v1.json')},
        'assets':assets, 'profiles':profiles}
    text = json.dumps(payload, ensure_ascii=False, separators=(',',':'))+'\n'
    # Exact source-hash filenames are intentionally published. No raw model
    # response, private paths, credentials, undeclared or stub facts enter.
    content = json.dumps({'assets':assets,'profiles':profiles},ensure_ascii=False).lower()
    for marker in FORBIDDEN_MARKERS:
        if marker.lower() in content:
            raise ValueError('Public sample audit: '+marker)
    return text

def main():
    text = compile_cases()
    if '--check' in sys.argv:
        if not DEST.is_file() or DEST.read_text() != text:
            raise SystemExit('Sample payload is stale; run tools/build_sample_case.py')
        print('Sample payload matches the current gates and sealed source.')
        return
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(text)
    sha = hashlib.sha256(text.encode()).hexdigest()
    (DEST.parent/'integrity.js').write_text('export const CASES_SHA256 = '+json.dumps(sha)+';\n')
    print(f'Built 19 brief states x 63 subsets = 1197 cases; {len(text.encode())} bytes; {sha}')

if __name__ == '__main__': main()
