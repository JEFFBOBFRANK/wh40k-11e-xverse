import json, random, itertools, re
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
for u in src['retainers']:
 e=next(x for x in rt['selectionEntries'] if x['name']==u['name'])
 assert next(x['value'] for x in e['costs'] if x['name']=='pts')==u['points'][0];checks+=1
 prof=[p for p in walk(e) if 'typeName' in p and 'characteristics' in p]
 for w in u['weapons']:
  assert any(p['name']==w['name'] and p['typeName']==w['kind'] and [z['$text'] for z in p['characteristics']]==w['values'] for p in prof),(u['name'],w['name']);checks+=1
 for st in u['stats']:
  assert any(p['typeName']=='Unit' and [z['$text'] for z in p['characteristics']][:7]==st['values'] for p in prof),(u['name'],'stats');checks+=1
cfg=next(x for x in c['sharedSelectionEntries'] if x['name']=='Detachment');dets=next(g for g in cfg['selectionEntryGroups'] if g['name']=='Detachment')['selectionEntries'];assert len(dets)==17
stratref=next(x for x in c['sharedSelectionEntries'] if x['name']=='Stratagem References')
for d in src['detachments']:
 e=next(x for x in dets if x['name']==d['name']);assert next(x['value'] for x in e['costs'] if x['name']=='Detachment Points')==d['dp'];checks+=1
 sr=next(x for x in stratref['selectionEntries'] if x['name']==d['name']+' Stratagems')
 assert sr['hidden'] and sr['modifiers'][0]['conditions'][0]['childId']==e['id'];checks+=1
 for st in d['stratagems']:
  name=st['name']+' / '+str(st['cost'])+' CP'
  assert not any(p['name']==name for p in e.get('profiles',[]))
  assert any(p['name']==name and ' '.join(p['description'].replace('**','').split())==' '.join(st['text'].split()) for p in sr['rules']);checks+=2
assert len(next(x for x in src['detachments'] if x['name']=='Veiled Blade Elimination Force')['stratagems'])==6
# Compare the source's dispositions to the actual standard category IDs. This
# catches names that look identical in the UI but contain PDF whitespace.
expected_dispositions={"The Emperor's Mandate":['Take and Hold','Disruption'],'Purgation Force':['Purge the Foe'],'Xenocide Force':['Reconnaissance'],'Daemonhunt Force':['Priority Assets'],'Requisitioned Battle Group':['Take and Hold'],'Technological Intervention':['Priority Assets'],'Quarantine Force':['Take and Hold'],'Chapter Intervention':['Purge the Foe'],'Temporal Intervention':['Disruption'],'Execution Directorate':['Reconnaissance'],'Imperial Cordon':['Take and Hold'],'Veiled Blade Elimination Force':['Purge the Foe'],'Warrant of Exploration':['Reconnaissance'],'Navis Boarding Force':['Priority Assets'],'Procession of Faith':['Take and Hold'],'God-Engine Mandate':['Priority Assets','Purge the Foe'],'Oathsworn Lance':['Purge the Foe']}
categories={x['name']:x for x in s['categoryEntries']}
dispcats={n:categories[n]['id'] for n in ['Disruption','Priority Assets','Purge the Foe','Take and Hold','Reconnaissance']}
ordocat=categories['Unique: ORDO'];assert ordocat['constraints'][0]['scope']=='roster' and ordocat['constraints'][0]['value']==1
assert not any(l['targetId']==ordocat['id'] for l in cfg['categoryLinks']);checks+=2
for d in src['detachments']:
 e=next(x for x in dets if x['name']==d['name'])
 assert [x.strip() for x in d['dispositions']]==expected_dispositions[d['name']]
 actual={l['targetId'] for l in e['categoryLinks']}&set(dispcats.values())
 assert actual=={dispcats[n] for n in expected_dispositions[d['name']]},d['name']
 assert any(l['targetId']==ordocat['id'] for l in e['categoryLinks'])==bool(d['ordo']);checks+=3
assert all(x['name']==x['name'].strip() for x in s['categoryEntries']);checks+=1
def condition_matches(q,selected,counts):
 count=counts.get(q['childId'],int(q['childId'] in selected))
 if q['type']=='notInstanceOf':return q['childId']!=c['id']
 if q['type']=='instanceOf':return q['childId']==c['id']
 return {'atLeast':lambda:count>=q['value'],'lessThan':lambda:count<q['value'],'greaterThan':lambda:count>q['value'],'equalTo':lambda:count==q['value']}[q['type']]()
def conditions_match(node,selected,counts):
 results=[condition_matches(q,selected,counts) for q in node.get('conditions',[])]+[conditions_match(q,selected,counts) for q in node.get('conditionGroups',[])]
 return any(results) if node.get('type')=='or' else all(results)
dispgroup=next(x for x in s['sharedSelectionEntryGroups'] if x['id']=='eece-6d68-6710-7a7f')
config_scenarios=0
for size in range(5):
 for chosen in itertools.combinations(dets,size):
  selected={x['id'] for x in chosen};counts={}
  for e in chosen:
   for l in e['categoryLinks']:counts[l['targetId']]=counts.get(l['targetId'],0)+1
  expected=set().union(*(set(expected_dispositions[e['name']]) for e in chosen))
  actual=set()
  for e in dispgroup['selectionEntries']:
   hidden=e.get('hidden',False)
   for m in e.get('modifiers',[]):
    if m['field']=='hidden' and conditions_match(m,selected,counts):hidden=m['value']
   if not hidden:actual.add(e['name'])
  assert actual==expected,('dispositions',selected,expected,actual)
  unique_valid=counts.get(ordocat['id'],0)<=ordocat['constraints'][0]['value']
  entry_valid=True
  for e in chosen:
   limit=e['constraints'][0]['value']
   for m in e.get('modifiers',[]):
    if m['field']==e['constraints'][0]['id'] and conditions_match(m,selected,counts):limit=m['value']
   entry_valid &= 1<=limit
  assert unique_valid==entry_valid,('Ordo Unique',selected)
  config_scenarios+=1
ref=next(x for x in c['sharedSelectionEntries'] if x['name']=='Army Rules and References')
assert not ref.get('profiles') and len(ref['rules'])==len(src['references']);checks+=1
for rr in ref['rules']:
 assert '\n\n' in rr['description'],rr['name']
 assert not re.search(r'(?<!\n)\n(?!\n|\- )',rr['description']),rr['name'];checks+=2
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
report=dict(status='PASS',structural_and_source_checks=checks,budget_allocation_scenarios=scenarios,detachment_configuration_scenarios=config_scenarios,new_recruit_runtime_test='Initial GitHub installation, faction selection and manual roster creation passed. This revision fixes Ordo Unique, disposition categories and reference formatting; live regression verification is recorded in VALIDATION.md. Complete roster validation and card export remain pending.',source_gaps=cov['source_gaps'])
(R/'homebrew/validation-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
