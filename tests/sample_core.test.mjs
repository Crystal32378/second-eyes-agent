import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {caseFor,makeDecision} from '../ui/sample/core.mjs';
const data=JSON.parse(fs.readFileSync(new URL('../ui/sample/cases.json',import.meta.url)));

test('all 1197 compiled cases preserve counts and evidence membership',()=>{
 let n=0;for(const id of Object.keys(data.profiles))for(let m=1;m<64;m++){
   const result=caseFor(data,id,m);assert.equal(result.items.length,result.summary.total);n++;
 }assert.equal(n,1197);
});
test('unknown profile, empty set, invalid masks fail closed',()=>{
 for(const [p,m] of [['oops',63],['__proto__',63],['both:1:1000',0],['both:1:1000',64],['missing',1.5]])assert.throws(()=>caseFor(data,p,m));
});
test('tampered summaries and coverage cannot become a displayed result',()=>{
 const bad=structuredClone(data);bad.profiles['both:1:1000'].subsets['63'].summary.Shortlist=2;
 assert.throws(()=>caseFor(bad,'both:1:1000',63));
 const wrong=structuredClone(data);wrong.profiles['both:1:1000'].subsets['63'].coverage.slots[0].members=['IG-262'];
 assert.throws(()=>caseFor(wrong,'both:1:1000',63));
});
test('a kept candidate is human intent; every unresolved question remains in export',()=>{
 const result=caseFor(data,'both:1:1000',63),before=JSON.stringify(data);
 const packet=makeDecision(data,result,['ROBE-5059'],'Keep this; request detail evidence.','2026-09-13T00:00:00Z');
 assert.equal(packet.human_decision.status,'candidates_kept');
 assert.equal(packet.items.filter(i=>i.bucket==='Needs Review').length,2);
 assert.equal(packet.selected_coverage.slots[1].status,'MISSING');
 assert.equal(packet.model_calls,0);assert.equal(packet.source_receipt_sha256,data.sealed_sha256);
 assert.equal(JSON.stringify(data),before);
});
test('pending and mismatched assets cannot be promoted by a human-selection control',()=>{
 const result=caseFor(data,'both:1:1000',63);
 for(const key of ['IG-262','BACK-5F20','invented'])assert.throws(()=>makeDecision(data,result,[key],'','now'));
 assert.throws(()=>makeDecision(data,caseFor(data,'missing',63),[],'','now'));
});
test('deferring an edit is a valid human decision, with all gaps intact',()=>{
 const packet=makeDecision(data,caseFor(data,'detail:1:1000',63),[],'Need another photograph.','now');
 assert.equal(packet.human_decision.status,'deferred');assert.equal(packet.coverage.slots[0].status,'MISSING');
});
