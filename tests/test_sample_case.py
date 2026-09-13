import hashlib
import itertools
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from tools.build_sample_case import compile_cases, SCENES, EDGES
from runtime.local_mvp import run, compute_coverage
from runtime.brief_gate import gate
from runtime.export_public import translate_reason

ROOT = Path(__file__).resolve().parents[1]

class SampleCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'ui/sample/cases.json').read_text())
        cls.local,err=run()
        assert err is None,err

    def test_all_supported_subsets_use_existing_gate_and_coverage(self):
        count=0
        for pid,profile in self.data['profiles'].items():
            decisions=[gate(i,profile['brief']) for i in self.local['items']]
            for got,want in zip(profile['decisions'],decisions):
                self.assertEqual(got['bucket'],want['bucket'])
                self.assertEqual(got['reason'],translate_reason(want['reason']))
            for m in range(1,64):
                items=[it for i,it in enumerate(decisions) if m&(1<<i)]
                got=profile['subsets'][str(m)]
                self.assertEqual(got['summary']['total'],len(items))
                for b in ('Shortlist','Needs Review','Remaining'):
                    self.assertEqual(got['summary'][b],sum(i['bucket']==b for i in items))
                self.assertEqual(got['coverage'],compute_coverage(profile['brief'] or {},items))
                count+=1
        self.assertEqual(count,1197)

    def test_missing_brief_never_has_candidates_or_coverage(self):
        for case in self.data['profiles']['missing']['subsets'].values():
            self.assertEqual(case['summary']['Shortlist'],0)
            self.assertEqual(case['summary']['Remaining'],0)
            self.assertEqual(case['summary']['Needs Review'],case['summary']['total'])
            self.assertEqual(case['coverage']['slots'],[])

    def test_default_matches_recorded_run(self):
        recorded=json.loads((ROOT/'ui/runtime/results.json').read_text())
        case=self.data['profiles']['both:1:1000']['subsets']['63']
        self.assertEqual(case['summary'],recorded['summary'])
        self.assertEqual(case['coverage'],recorded['coverage'])

    def test_stricter_brief_and_subset_change_outcome(self):
        detail=self.data['profiles']['detail:1:1000']['subsets']['63']
        self.assertEqual(detail['summary']['Shortlist'],0)
        self.assertEqual(detail['summary']['Remaining'],4)
        without_robe=self.data['profiles']['both:1:1000']['subsets'][str(63^(1<<4))]
        self.assertEqual(without_robe['summary']['Shortlist'],0)
        self.assertTrue(all(s['status']=='MISSING' for s in without_robe['coverage']['slots']))
        higher=self.data['profiles']['both:1:2400']['subsets']['63']
        self.assertEqual(higher['summary']['Shortlist'],0)

    def test_reproducible_and_integrity_pinned(self):
        text=compile_cases()
        self.assertEqual(text,(ROOT/'ui/sample/cases.json').read_text())
        self.assertIn(hashlib.sha256(text.encode()).hexdigest(),(ROOT/'ui/sample/integrity.js').read_text())

    def test_public_payload_excludes_private_and_stub_data(self):
        text=json.dumps(self.data,ensure_ascii=False)
        for forbidden in ['mvp-stub','/Users/','/home/','"raw"','"usage"','"resolver"','GOOGLE_','AKIA']:
            self.assertNotIn(forbidden,text)
        for asset in self.data['assets']:
            path=ROOT/'ui/sample'/asset['image']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),asset['manifest']['sha256'])

    def test_changed_or_failed_sealed_input_cannot_compile(self):
        with patch('tools.build_sample_case.run',return_value=(None,'custody failure')):
            with self.assertRaisesRegex(ValueError,'custody failure'):compile_cases()

    def test_new_public_image_binding_is_checked(self):
        bad=deepcopy(self.local);bad['items'][0]['manifest']['sha256']='0'*64
        with patch('tools.build_sample_case.run',return_value=(bad,None)):
            with self.assertRaisesRegex(ValueError,'binding mismatch'):compile_cases()

    def test_no_upload_or_storage_channel_and_strict_csp(self):
        page=(ROOT/'ui/sample/index.html').read_text()
        script=(ROOT/'ui/sample/app.js').read_text()
        for token in ['type="file"','<iframe','<script src="https:']:
            self.assertNotIn(token,page)
        for token in ['localStorage','sessionStorage','sendBeacon','XMLHttpRequest','document.cookie','innerHTML','eval(']:
            self.assertNotIn(token,script)
        self.assertIn("form-action 'none'",page)
        self.assertIn("connect-src 'self'",page)
        self.assertIn("a.image",script)
        self.assertIn("await sha(b)!==a.manifest.sha256",script)
        self.assertIn("await im.decode()",script)
        self.assertIn("Promise.allSettled",script)

    def test_pages_includes_sample_without_changing_existing_routes(self):
        from tools.build_pages import stage,check_links,manifest
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'_site';self.assertEqual(stage(out),0)
            self.assertEqual(check_links(out),[])
            files=manifest(out)
            for rel in ['try/index.html','try/app.js','try/core.mjs','try/cases.json','try/integrity.js','try/sample.css']:
                self.assertIn(rel,files)
            self.assertIn('href="try/"',(out/'brief-established.html').read_text())
            self.assertIn('href="../try/"',(out/'runtime/index.html').read_text())
