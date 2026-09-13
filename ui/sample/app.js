import { CASES_SHA256 } from './integrity.js';
import { caseFor, makeDecision } from './core.mjs';

// Captions are display-only; asset keys bind all evidence and decisions.
const CAPTION = {
 'ROBE-5059':['Blue robe, hanging','A blue robe hanging against a pink backdrop.'],
 'IG-262':['Lace on ochre','White lace lingerie on an ochre chair.'],
 'IG-277':['Blush & flowers','Pink lace, flowers and editorial props.'],
 'BACK-5F20':['Back construction','A close back view of blue-lilac lingerie.'],
 'IMG-4489':['Out in the light','Outdoor styling, with a raised arm against a blue sky.'],
 'WEAR-8106':['An everyday layer','Lilac lace under an open shirt.']
};
const GLOSS = {'藍':'blue','膚':'nude','粉':'pink','黑':'black','白':'white'};
const caption = k => (CAPTION[k] || [k,k])[0];
const alt = k => (CAPTION[k] || [k,k])[1];
const $ = id => document.getElementById(id);
const el = (tag, cls, text) => {const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
let data=null, current=null, kept=new Set(), imageURLs=new Map(), loading=false;
const sha = async bytes => [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
const clean = id => {$(id).replaceChildren(); return $(id);};
function mask() {return [...document.querySelectorAll('#asset-picker input')].reduce((m,n,i)=>m|(n.checked?(1<<i):0),0);}
function revokeImages(){for(const u of imageURLs.values())URL.revokeObjectURL(u);imageURLs.clear();}
function imageLink(it,label){
 const a=el('a','image-link');a.href=imageURLs.get(it.asset_key);a.target='_blank';a.rel='noopener';
 a.setAttribute('aria-label',`Open photograph: ${caption(it.asset_key)} (${it.asset_key})`);
 const im=el('img');im.src=imageURLs.get(it.asset_key);im.alt=alt(it.asset_key);a.append(im);
 if(label)a.append(el('span','asset-label',label));return a;
}
function evidence(it){
 const d=el('details','evidence');d.append(el('summary',null,'Evidence details'));
 const dl=el('dl');const row=(key,value)=>dl.append(el('dt',null,key),el('dd',null,value));
 row('Photograph',it.asset_key);row('State',it.evidence_state+' — recorded, unverified observation');
 row('Observed',Object.entries(it.observed||{}).filter(([,v])=>v).map(([k,v])=>`${k}: ${v.value}${GLOSS[v.value]?' ['+GLOSS[v.value]+']':''} · ref ${v.ref}`).join('; ')||'No valid observation with a reference');
 row('Prior labels',Object.entries(it.old||{}).filter(([,v])=>v).map(([k,v])=>k+': '+v).join('; ')||'No comparable prior labels supplied');
 if(it.signals_used){row('Consulted facts',it.signals_used.map(k=>`${k}: ${it.consulted_signals[k]===null?'UNKNOWN':String(it.consulted_signals[k])} · ${it.signal_sources[k]||'no source supplied'}`).join('; ')||'None — the gate stopped before consulting publishing facts');}
 row('Image SHA-256',it.manifest.sha256);row('Evidence ref',it.manifest.ref_convention);d.append(dl);return d;
}
function sourceCard(it){
 const f=el('figure','asset');f.append(imageLink(it,'PUBLIC SAMPLE'));
 const fc=el('figcaption'),line=el('div','asset-line');line.append(el('h3',null,caption(it.asset_key)),el('span','asset-code',it.asset_key));
 fc.append(line,el('p',null,'Recorded observation · not evaluated against your brief yet'));f.append(fc);return f;
}
function standardCard(it,canKeep){
 const f=el('figure','asset');f.append(imageLink(it,canKeep?'CANDIDATE':'BRIEF MISMATCH'));
 const fc=el('figcaption'),line=el('div','asset-line');line.append(el('h3',null,caption(it.asset_key)),el('span','asset-code',it.asset_key));
 fc.append(line,el('p','reason',it.reason),el('p','state-label',`${it.evidence_state} / ${it.verdict}`));
 if(canKeep){const b=el('button','keep','Keep for my edit');b.type='button';b.setAttribute('aria-pressed','false');b.setAttribute('aria-label',`Keep ${it.asset_key} for my edit`);b.addEventListener('click',()=>{
   if(kept.has(it.asset_key))kept.delete(it.asset_key);else kept.add(it.asset_key);
   b.setAttribute('aria-pressed',String(kept.has(it.asset_key)));b.textContent=kept.has(it.asset_key)?'Kept for my edit':'Keep for my edit';updateDecision();
 });fc.append(b);}
 fc.append(evidence(it));f.append(fc);return f;
}
function question(it){
 const a=el('article','question'),top=el('div','question-top');top.append(imageLink(it));
 const info=el('div');info.append(el('div','eyebrow',it.evidence_state==='CONFLICT'?'CONFLICT':'MISSING EVIDENCE'),el('h3',null,caption(it.asset_key)),el('p','asset-code',it.asset_key),el('p',null,it.reason),el('p',null,'Needed: '+(it.pending.join('; ')||'A sourced human answer')));top.append(info);a.append(top,evidence(it));return a;
}
function invalidate(message){
 current=null;kept.clear();$('editor-note').value='';$('export-status').textContent='';
 $('results').hidden=true;$('before').hidden=false;$('brief-state').textContent='Not applied';
 $('form-message').textContent=message||'';
 if(data)$('source-count').textContent=String([...document.querySelectorAll('#asset-picker input')].filter(n=>n.checked).length);
}
function resetSession(){
 $('brief-form').reset();invalidate('Session cleared. Your note and kept choices were removed; downloaded files are unchanged.');
 $('setup').open=true;
 if(data)renderSource();
}
function renderSource(){
 const list=clean('source-wall');data.assets.forEach((a,i)=>{if(mask()&(1<<i))list.append(sourceCard(a));});
 if(!mask())list.append(el('p','empty','Choose at least one sample photograph.'));
 $('source-count').textContent=String(data.assets.filter((_,i)=>mask()&(1<<i)).length);
}
function updateDecision(){
 $('kept-summary').textContent=kept.size?`${kept.size} kept: ${[...kept].join(', ')}`:'No photographs kept. You can defer this edit.';
 $('chosen-coverage').textContent='Your kept set: '+current.coverage.slots.map(s=>`${s.slot} / ${s.scene} — ${s.members.some(k=>kept.has(k))?'HAVE':'MISSING'}`).join(' · ');
 $('export-status').textContent='';
}
function renderResult(result){
 const buckets={'Shortlist':['count-shortlist','shortlist-cards'],'Needs Review':['count-review','review-cards'],'Remaining':['count-remaining','remaining-cards']};
 for(const [bucket,[count,id]] of Object.entries(buckets)){
   $(count).textContent=String(result.summary[bucket]);const container=clean(id);
   result.items.filter(i=>i.bucket===bucket).forEach(it=>container.append(bucket==='Needs Review'?question(it):standardCard(it,bucket==='Shortlist')));
   if(!container.childElementCount)container.append(el('p','empty',bucket==='Shortlist'?'No candidate meets this brief.':bucket==='Needs Review'?'No unresolved question in this selection.':'Nothing filed out by this brief.'));
 }
 const cov=clean('coverage');for(const s of result.coverage.slots){const tile=el('div','coverage-item'+(s.status==='MISSING'?' gap':''));tile.append(el('strong',null,`${s.slot} / ${s.scene}`),el('small',null,s.status==='MISSING'?'MISSING — not guessed':`${s.count} candidate: ${s.members.join(', ')}`));cov.append(tile);}
 $('coverage-section').hidden=!result.brief;$('missing-brief-note').hidden=!!result.brief;$('human-decision').hidden=!result.brief;
 $('result-summary').textContent=`${result.summary.total} included · ${result.summary.Shortlist} Shortlist · ${result.summary['Needs Review']} Needs Review · ${result.summary.Remaining} Remaining. Recorded observations; no new model call.`;
 const lineage=clean('case-lineage');for(const [term,value] of [['Case',result.case_id],['Recorded receipt SHA-256',data.sealed_sha256],['Gate source SHA-256',data.build_sources['runtime/brief_gate.py']],['Case payload SHA-256',CASES_SHA256]])lineage.append(el('dt',null,term),el('dd',null,value));
 $('load-status').hidden=true;$('before').hidden=true;$('results').hidden=false;$('setup').open=false;
 $('brief-state').textContent=result.brief?'Applied · '+result.brief.brief_id:'Missing — review required';
 if(result.brief)updateDecision();$('results').focus();
}
function apply(missing=false){
 if(!data||loading)return;
 const m=mask();if(!m){$('form-message').textContent='Choose at least one photograph before applying the brief.';return;}
 invalidate('');
 try{current=caseFor(data,missing?'missing':`${$('scenes').value}:${$('people').value}:${$('edge').value}`,m);renderResult(current);}
 catch(e){invalidate('The requested case could not be verified. No candidate was offered.');$('setup').open=true;}
}
async function load(){
 if(loading)return;loading=true;invalidate('');revokeImages();data=null;
 $('workspace').hidden=true;$('load-error').hidden=true;$('load-status').hidden=false;
 $('load-status').textContent='Loading the public case and checking all six image references…';
 try{
   if(!crypto.subtle)throw Error('A secure HTTPS or localhost connection is required to check the case.');
   const response=await fetch('cases.json',{cache:'no-store',credentials:'omit'});if(!response.ok)throw Error('The public case data could not be loaded.');
   const bytes=await response.arrayBuffer();if(await sha(bytes)!==CASES_SHA256)throw Error('The public case data changed or is incomplete. Its checksum does not match.');
   const parsed=JSON.parse(new TextDecoder().decode(bytes));caseFor(parsed,'both:1:1000',63);
   const checked=await Promise.allSettled(parsed.assets.map(async a=>{
     if(!/^\.\.\/runtime\/assets\/[A-Z0-9-]+\.jpg$/.test(a.image))throw Error(`${a.asset_key}: unsupported public image reference`);
     const r=await fetch(a.image,{cache:'no-store',credentials:'omit'});if(!r.ok)throw Error(`${a.asset_key}: image unavailable`);
     const b=await r.arrayBuffer();if(await sha(b)!==a.manifest.sha256)throw Error(`${a.asset_key}: image checksum mismatch`);
     const u=URL.createObjectURL(new Blob([b],{type:'image/jpeg'}));imageURLs.set(a.asset_key,u);
     const im=new Image();im.src=u;try{await im.decode();}catch{throw Error(`${a.asset_key}: image unreadable`);}
   }));
   const failures=checked.filter(r=>r.status==='rejected').map(r=>r.reason.message||'A sample image was unreadable');
   if(failures.length)throw Error(failures.join('; '));
   data=parsed;const picker=clean('asset-picker');
   data.assets.forEach((a,i)=>{const label=el('label'),input=el('input');input.type='checkbox';input.value=a.asset_key;input.checked=true;input.defaultChecked=true;input.setAttribute('aria-label','Include '+a.asset_key);
     const im=el('img');im.src=imageURLs.get(a.asset_key);im.alt='';label.append(input,im,el('span',null,a.asset_key));picker.append(label);});
   $('brief-form').reset();renderSource();$('workspace').hidden=false;$('load-status').textContent='Six public image references checked. Your brief has not been applied yet.';
 }catch(e){revokeImages();data=null;$('error-message').textContent=e.message||'The public sample could not be read.';$('load-error').hidden=false;$('load-status').hidden=true;}
 finally{loading=false;}
}
$('brief-form').addEventListener('submit',e=>{e.preventDefault();apply();});
$('brief-form').addEventListener('change',()=>{invalidate('Settings changed. Previous choices were cleared. Apply the brief again.');renderSource();});
$('no-brief').addEventListener('click',()=>apply(true));
$('edit-brief').addEventListener('click',()=>{$('setup').open=true;$('scenes').focus();});
$('reset').addEventListener('click',()=>{resetSession();$('scenes').focus();});
$('retry').addEventListener('click',load);
$('download').addEventListener('click',()=>{
 if(!current||!current.brief)return;
 try{const packet=makeDecision(data,current,[...kept],$('editor-note').value,new Date().toISOString());
   const blob=new Blob([JSON.stringify(packet,null,2)+'\n'],{type:'application/json'}),u=URL.createObjectURL(blob),a=el('a');a.href=u;a.download='second-eyes-sample-decision.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000);
   $('export-status').textContent='Download requested. The file contains your decision, its brief, reasons, unresolved questions and evidence references. It contains no image bytes.';
 }catch{$('export-status').textContent='Decision export stopped. No unresolved item can be promoted into a candidate.';}
});
window.addEventListener('pageshow',e=>{if(e.persisted&&data)resetSession();});
window.addEventListener('pagehide',e=>{$('editor-note').value='';kept.clear();current=null;if(!e.persisted)revokeImages();});
load();
