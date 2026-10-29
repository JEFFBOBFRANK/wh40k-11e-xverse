import json, random, itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
f={p.name:next(iter(json.loads(p.read_text()).values())) for p in R.glob('*.json')}
s=f['Warhammer 40,000.json'];c=f['Imperium - Agents of the Imperium.json'];q=f['Agents Requisitions Library.json'];src=json.loads((R/'homebrew/source-data.json').read_text());cov=json.loads((R/'homebrew/coverage.json').read_text());roots={v['id']:v for v in f.values()};checks=0
for o in [c,q]:
 linked=[o,s];seen=set();queue=[o]
 while queue:
  for l in queue.pop().get('catalogueLinks',[]):
   assert l['targetId'] in roots,l
   if l['targetId'] not in seen:seen.add(l['targetId']);linked.append(roots[l['targetId']]);queue.append(roots[l['targetId']])
 ids={n['id'] for z in linked for n in walk(z) if 'id' in n}
 for n in walk(o):
  for k in ['targetId','typeId','defaultSelectionEntryId']:
   if k in n:assert n[k] in ids or n[k] in ['', 'none'],(n.get('name'),k,n[k]);checks+=1
idx={n['id']:n for o in [s,c,q] for n in walk(o) if 'id' in n};native={n:idx[i] for n,i in cov['native_root_ids'].items()};rootids={e['targetId'] for e in c['entryLinks']}
assert len(native)==58
for u in src['units']:
 e=native[u['name']];assert e['id'] in rootids;assert sum(bool(x.get('primary')) for x in e['categoryLinks'])==1;assert next(x['value'] for x in e['costs'] if x['name']=='pts')==u['points'][0];checks+=3
 prof=[p for p in walk(e) if 'typeName' in p and 'characteristics' in p]
 for w in u['weapons']:
  assert any(p['name']==w['name'] and p['typeName']==w['kind'] and [z['$text'] for z in p['characteristics']]==w['values'] for p in prof),(u['name'],w['name']);checks+=1
 for st in u['stats']:
  assert any(p['typeName']=='Unit' and [z['$text'] for z in p['characteristics']][:7]==st['values'] for p in prof),(u['name'],'stats');checks+=1
 if len(u['points'])==2:
  size=next(g for g in e['selectionEntryGroups'] if g['name']=='Unit Size');assert [u['points'][0]+next(z['value'] for z in x['costs'] if z['name']=='pts') for x in size['selectionEntries']]==u['points'];checks+=1
rt=next(g for g in native['Rogue Trader']['selectionEntryGroups'] if g['name']=='Household Retainers');assert len(rt['selectionEntries'])==23;assert not any(x['name'] in {l['name'] for l in c['entryLinks']} for x in src['retainers']);checks+=2
cfg=next(x for x in c['sharedSelectionEntries'] if x['name']=='Detachments');dets=next(g for g in cfg['selectionEntryGroups'] if g['name']=='Selected Detachments')['selectionEntries'];assert len(dets)==17
for d in src['detachments']:
 e=next(x for x in dets if x['name']==d['name']);assert next(x['value'] for x in e['costs'] if x['name']=='Detachment Points')==d['dp'];checks+=1
 for st in d['stratagems']:assert any(p['name']==st['name']+' / '+str(st['cost'])+' CP' and p['characteristics'][0]['$text']==st['text'] for p in e['profiles']);checks+=1
assert len(next(x for x in src['detachments'] if x['name']=='Veiled Blade Elimination Force')['stratagems'])==6
assert not cov['unmatched_requisition_names']
for l in c['entryLinks']:
 if l['name'].endswith('(Requisitioned)'):assert sum(bool(x.get('primary')) for x in idx[l['targetId']]['categoryLinks'])==1;checks+=1
for n in ['Inquisitor Kroyle','Inquisitor Karamazov','Inquisitor Gideon Ravenor']:assert not native[n].get('associations');checks+=1
budgets=[l for l in next(f for f in s['forceEntries'] if f['name']=='Army Roster')['categoryLinks'] if l['name'].startswith('Requisition allowance')];assert len(budgets)==29
bonus={'Sororitas':'Purgation Force','Deathwatch':'Xenocide Force','Grey Knights':'Daemonhunt Force','Militarum':'Requisitioned Battle Group','Mechanicus':'Technological Intervention','Astartes':'Chapter Intervention','Knights':'Oathsworn Lance'};detids={x['name']:x['id'] for x in dets};sizes=[('d62d-db22-4893-4bc0',250),('baf8-997f-e323-a090',500),('4204-82d0-908c-a62a',750)]
random.seed(92);scenarios=0
for sid,base in sizes:
 for pools in [()]+[(k,) for k in bonus]+[(k,'Knights') for k in bonus if k!='Knights']:
  for mandate in [False,True]:
   if mandate and (len(pools)>1 or 'Knights' in pools):continue
   selected={sid}|{detids[bonus[x]] for x in pools}|({detids["The Emperor's Mandate"]} if mandate else set())
   for i in range(100):
    spend={x:random.choice([0,50,100,250,500,750,1000]) for x in list(bonus)+['Silence']};expected=sum(max(0,v-(base if x in pools else 0)) for x,v in spend.items())<=base*(2 if mandate else 1);valid=True
    for b in budgets:
     omit=b['name'].split(' excluding ')[1].split(', ') if ' excluding ' in b['name'] else [];cap=b['constraints'][0]['value']
     for m in b['modifiers']:
      if all(x['childId'] in selected for x in m.get('conditions',[])):cap=m['value'] if m['type']=='set' else cap+m['value']
     if sum(v for x,v in spend.items() if x not in omit)>cap:valid=False
    assert valid==expected,('budget',spend,pools,base);scenarios+=1
assert any('Skaven' in n for n in f) and any('Black-Flag' in n for n in f)
report=dict(status='PASS',structural_and_source_checks=checks,budget_allocation_scenarios=scenarios,new_recruit_runtime_test='Not completed; browser local-folder picker unavailable',source_gaps=cov['source_gaps'])
(R/'homebrew/validation-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
