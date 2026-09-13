const BUCKETS = ['Shortlist', 'Needs Review', 'Remaining'];
export function caseFor(data, profileId, mask) {
  if (data.schema_version !== 1 || data.assets.length !== 6 ||
      !Number.isInteger(mask) || mask < 1 || mask > 63 ||
      !Object.hasOwn(data.profiles, profileId)) throw Error('Unsupported sample selection');
  const profile = data.profiles[profileId];
  const compiled = profile.subsets[String(mask)];
  if (!compiled) throw Error('This sample result is unavailable');
  const items = data.assets.flatMap((asset, i) => {
    if (!(mask & (1 << i))) return [];
    const decision = profile.decisions[i];
    if (decision.asset_key !== asset.asset_key || !BUCKETS.includes(decision.bucket))
      throw Error('Sample evidence binding failed');
    return [{...asset, ...decision}];
  });
  for (const b of BUCKETS) if (compiled.summary[b] !== items.filter(i => i.bucket === b).length)
    throw Error('Sample count does not match its evidence');
  if (compiled.summary.total !== items.length) throw Error('Sample total does not match');
  for (const slot of compiled.coverage.slots) {
    const members = items.filter(i => i.bucket === 'Shortlist' && i.consulted_signals.scene_claim === slot.scene).map(i => i.asset_key);
    if (JSON.stringify(slot.members) !== JSON.stringify(members) || slot.count !== members.length ||
        slot.status !== (members.length ? 'HAVE' : 'MISSING')) throw Error('Sample coverage binding failed');
  }
  return structuredClone({case_id:profileId+'/'+mask, brief:profile.brief, items, ...compiled});
}
export function makeDecision(data, result, kept, note, createdAt) {
  const candidates = new Set(result.items.filter(i => i.bucket === 'Shortlist').map(i => i.asset_key));
  const selected = [...new Set(kept)];
  if (!result.brief || selected.some(k => !candidates.has(k))) throw Error('Only candidates may be kept; unresolved evidence is not overridden');
  if (typeof note !== 'string' || note.length > 2000) throw Error('Invalid editorial note');
  return {schema_version:1, kind:'human_editorial_decision', mode:'sample_case',
    created_at:createdAt, observation_mode:'recorded', model_calls:0,
    result_method:'Exact build-time result from the existing Python gates for the selected brief and subset',
    case_id:result.case_id, source_receipt_sha256:data.sealed_sha256,
    gate_source_sha256:data.build_sources['runtime/brief_gate.py'],
    brief:result.brief, summary:result.summary, coverage:result.coverage,
    human_decision:{status:selected.length?'candidates_kept':'deferred', kept_asset_keys:selected, note},
    selected_coverage:{slots:result.coverage.slots.map(s => ({...s, members:s.members.filter(k => selected.includes(k)),
      count:s.members.filter(k => selected.includes(k)).length,
      status:s.members.some(k => selected.includes(k))?'HAVE':'MISSING'}))},
    items:result.items.map(i => ({asset_key:i.asset_key, manifest:i.manifest, evidence_state:i.evidence_state,
      observed:i.observed, old:i.old, bucket:i.bucket, verdict:i.verdict, reason:i.reason,
      pending:i.pending, consulted_signals:i.consulted_signals, signal_sources:i.signal_sources})),
    boundary:'Human editorial choice only. No publishing action, legal clearance, accuracy or safety guarantee. Original evidence is not changed.'};
}
