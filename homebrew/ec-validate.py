"""Validate EC v3.1 source fidelity and roster restrictions."""
import json,itertools,collections,argparse,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--source',type=Path,required=True);a=p.parse_args()
G=json.loads((a.data/'Warhammer 40,000.json').read_text())['gameSystem'];C=json.loads((a.data/"Chaos - Emperor's Children.json").read_text())['catalogue'];S=json.loads(a.source.read_text());cov=json.loads((a.data/'ec-coverage.json').read_text())
def walk(o):
 if isinstance(o,dict):
  yield o
  for v in o.values():yield from walk(v)
 elif isinstance(o,list):
  for v in o:yield from walk(v)
checks=0
cn=list(walk(C));gn=list(walk(G));ids={n['id'] for n in cn+gn if 'id' in n};idx={n['id']:n for n in cn+gn if 'id'in n}
counts=collections.Counter(n['id'] for n in cn if 'id'in n);assert not [(k,v) for k,v in counts.items() if v>1],[(k,v) for k,v in counts.items() if v>1]
for n in cn:
 for k in ['targetId','typeId','defaultSelectionEntryId']:
  if k in n:assert n[k] in ids|{'none',''},(n.get('name'),k,n[k]);checks+=1
 for q in n.get('constraints',[]):assert 'childId' not in q,q
 for q in n.get('constraints',[]):
  if q['type']=='max' and q['scope']!='parent':assert q.get('includeChildSelections'),q;checks+=1
roots={l['targetId']:l for l in C['entryLinks']};native={n:idx[i] for n,i in cov['native_root_ids'].items()};assert len(native)==58
assert sum(u['allied'] for u in S['units'])==13
PT='51b2-306e-1021-d207';INC='d62d-db22-4893-4bc0';STRIKE='baf8-997f-e323-a090';ONS='4204-82d0-908c-a62a';EN='f759-1bc4-cb3a-f0d2'
def conditions(node,selected):
 out=[]
 for q in node.get('conditions',[]):
  n=int(q['childId'] in selected)
  out.append({'atLeast':n>=q['value'],'lessThan':n<q['value'],'equalTo':n==q['value']}.get(q['type'],False))
 out +=[conditions(x,selected) for x in node.get('conditionGroups',[])]
 return any(out) if node.get('type')=='or' else all(out)
def hidden(e,selected):
 h=e.get('hidden',False)
 for m in e.get('modifiers',[]):
  if m['field']=='hidden' and conditions(m,selected):h=m['value']
 return h
for u in S['units']:
 e=native[u['name']];assert e['id'] in roots;assert sum(x.get('primary',False) for x in e['categoryLinks'])==1;checks+=2
 assert next(x['value'] for x in e['costs'] if x['typeId']==PT)==u['points'][0];checks+=1
 assert [x['$text'] for x in e['profiles'][0]['characteristics']]==u['stats'];checks+=1
 profiles=[x for x in walk(e) if x.get('typeName') in ['Ranged Weapons','Melee Weapons']]
 for w in u['weapons']:
  assert any(x['name']==w['name'] and [z['$text'] for z in x['characteristics']][:6]==w['values'] for x in profiles),(u['name'],w['name']);checks+=1
 assert set(u['army_rules'])<={l['name'] for l in e['infoLinks']};checks+=1
 rule=next(x for x in e['rules'] if x['name']=='Datasheet rules and equipment');assert ' '.join(rule['description'].replace('**','').split())==' '.join(u['rules'].replace('**','').split());checks+=1
 assert e['constraints'][0]['value']==(1 if u['role']=='Epic Hero' else 6 if u['role']=='Battleline' or 'Dedicated Transport' in u['keywords'] else 3);checks+=1
 if len(u['sizes'])==2:
  sz=next(g for g in e['selectionEntryGroups'] if g['name']=='Unit Size');assert [u['points'][0]+x['costs'][0]['value'] for x in sz['selectionEntries']]==u['points'];checks+=1
 if u['role']=='Epic Hero':assert not any(g['name']=='Enhancements and Upgrades' for g in e.get('selectionEntryGroups',[]));checks+=1
 if u['allied']:assert not any(l['name']=='Warlord' for l in e.get('entryLinks',[]));checks+=1
 else:assert 'Manifestation' not in [l['name'] for l in e['infoLinks']];checks+=1
 # Required model groups enforce the correct small and large unit totals.
 if u['sizes'][0]>1:
  parts=next(g for g in e['selectionEntryGroups'] if g['name']=='Unit Size')['selectionEntries'] if len(u['sizes'])==2 else [e]
  for part,size in zip(parts,u['sizes']):
   mg=next(g for g in part['selectionEntryGroups'] if g['name']=='Models');assert [c['value'] for c in mg['constraints']]==[size]*2
   assert sum(x['defaultAmount'] for x in mg['selectionEntries'])==size;checks+=2
ful=native['Fulgrim'];assert ful['costs'][0]['value']==485 and 'Bound Excess' not in [x['name'] for x in ful['infoLinks']];checks+=1
assert ful['entryLinks'][0]['constraints'][0]['value']==1;checks+=1
for u in S['units']:
 if 'Bound Excess' in u['army_rules'] or u['name']=='Fulgrim':
  e=native[u['name']];g=next(g for g in e['selectionEntryGroups'] if 'permanent elixirs' in g['name']);assert [x['value'] for x in g['constraints']]==[2,2];assert len(g['selectionEntries'])==10;assert all(x['constraints'][0]['value']==1 for x in g['selectionEntries']);checks+=3
  assert sum(not hidden(x,set()) for x in g['selectionEntries'])==8;checks+=1
cfg=next(x for x in C['sharedSelectionEntries'] if x['name']=='Detachment');dets=cfg['selectionEntryGroups'][0]['selectionEntries'];detids={x['name']:x['id'] for x in dets};assert len(dets)==15
strat=next(x for x in C['sharedSelectionEntries'] if x['name']=='Stratagem References');assert len(strat['infoLinks'])==60
for d in S['detachments']:
 e=next(x for x in dets if x['name']==d['name']);assert e['costs'][0]['value']==d['dp'];assert e['rules'][0]['description']==d['rules'];assert len(e['rules']) in [1,2];checks+=3
 for st in d['stratagems']:
  r=next(r for r in C['sharedRules'] if r['name']==d['name']+' — '+st['name']+' / '+str(st['cp'])+' CP');assert r['description']==st['text'];checks+=1
allied=next(x for x in G['categoryEntries'] if x['name']=='Legions of Excess');cap=allied['constraints'][0]
assert any(x['targetId']==allied['id'] and not x['hidden'] for f in G['forceEntries'] if f['name']=='Army Roster' for x in f['categoryLinks']);checks+=1
scenarios=0
for size,base in [(INC,500),(STRIKE,1000),(ONS,1500)]:
 for n in range(5):
  for ds in itertools.combinations(dets,n):
   selected={size}|{e['id'] for e in ds};names={e['name'] for e in ds}
   expected=base if 'Carnival of Excess' in names else 500*len(names&{'Perfumed Procession','Ritual Host'})
   actual=cap['value']
   for m in allied['modifiers']:
    if conditions(m,selected):actual=m['value'] if m['type']=='set' else actual+m['value']
   assert actual==expected,(names,size,actual,expected)
   for u in S['units']:
    if u['allied']:assert hidden(roots[native[u['name']]['id']],selected)==(expected==0);checks+=1
   visible=[x for x in strat['infoLinks'] if not hidden(x,selected)];assert len(visible)==sum(len(d['stratagems']) for d in S['detachments'] if d['name'] in names)
   scenarios+=1
# Enhancement links remain hidden without their own detachment; a Censer also
# requires an actual Living Elixir assignment on that specific bearer.
for u in S['units']:
 e=native[u['name']]
 for g in e.get('selectionEntryGroups',[]):
  if g['name']!='Enhancements and Upgrades':continue
  for l in g['entryLinks']:
   assert hidden(l,set()),(u['name'],l['name'],'unselected detachment')
   if l['name'].startswith('Censer'):
    selected={detids['Perfumed Procession']};assert hidden(l,selected)
    living=next(x for x in e['selectionEntryGroups'] if x['name']=='Living Elixir assignment')
    assert not hidden(l,selected|{living['selectionEntries'][0]['id']});checks+=2
   checks+=1
# Equipment exclusivity regression checks.
e=native['Excruciator Terminators'];models=next(g for g in e['selectionEntryGroups'] if g['name']=='Models')['selectionEntries'];assert next(x for x in models if x['name']=='Excruciator with heavy weapon')['constraints'][1]['value']==1;checks+=1
# Exact enhancement roster and eligibility boundaries.
enh={h['name'] for d in S['detachments'] for h in d['enhancements']};actual={e['name'] for e in C['sharedSelectionEntries'] if any(r['name']==e['name'] for r in e.get('rules',[])) and e['name'] in enh};assert actual==enh,(enh-actual,actual-enh);checks+=1
for u in S['units']:
 e=native[u['name']]
 for g in e.get('selectionEntryGroups',[]):
  if g['name']!='Enhancements and Upgrades':continue
  for l in g['entryLinks']:
   he=idx[l['targetId']];isupgrade='[Upgrade]' in he['name'];assert isupgrade != ('Character' in u['keywords']),(u['name'],he['name']);checks+=1
report=dict(status='PASS',source_version='3.1',source_checks=checks,detachment_and_ally_scenarios=scenarios,units=58,weapon_profiles=244,enhancements=40,stratagems=60,dispositions_unspecified=cov['dispositions_unspecified'],live_validation='Published-revision live checks are recorded in homebrew/ec-VALIDATION.md.')
(a.data/'ec-validation-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
