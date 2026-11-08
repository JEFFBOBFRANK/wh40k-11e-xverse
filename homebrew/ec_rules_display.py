"""EC gameplay wording and detachment Dispositions."""
import hashlib,json
from pathlib import Path

def uid(s):
 h=hashlib.sha256(('ec-rules-display:'+s).encode()).hexdigest()[:16]
 return '-'.join(h[i:i+4] for i in range(0,16,4))

def apply_rules_display(catalogue,system,source=None):
 data=json.loads((Path(__file__).parent/'ec-display-data.json').read_text())
 entries={e['name']:e for e in catalogue['sharedSelectionEntries']}
 cats={x['name']:x['id'] for x in system['categoryEntries']+catalogue.get('categoryEntries',[])}
 shared={r['name']:r for r in catalogue['sharedRules']}
 # Rule descriptions start beneath their heading in New Recruit's renderer.
 for name,text in data['army_rules'].items():
  shared[name]['description']='\n\n'+text
 elixirs='\n\n'.join('**'+e['name']+'**\n\n**Activate:** '+e['timing']+'.\n\n**Duration:** '+e['duration']+'.\n\n'+e['effect']+'\n\n**Stupefied:** '+e['stupefied'] for e in data['elixirs'])
 shared['Warband Elixirs']['description']='\n\n'+elixirs
 refs=entries['Army Rules and References']
 refs['rules']=[]
 refs['infoLinks']=[dict(id=uid('reference:'+n),name=n,type='rule',targetId=shared[n]['id'],hidden=False) for n in ['Combat Drugs','Bound Excess','Sublime Strategist']]
 # Elixir selection entries show the same operative effects as the rule.
 from datasheet_format import walk
 for node in walk(catalogue):
  for r in node.get('rules',[]):
   match=next((e for e in data['elixirs'] if e['name']==r['name']),None)
   if match:
    r['description']='\n\n**Activate:** '+match['timing']+'.\n\n**Duration:** '+match['duration']+'.\n\n'+match['effect']+'\n\n**Stupefied:** '+match['stupefied']
 # Combat Drugs is one rule, rather than separate linked elixir explanations.
 for e in entries.values():
  links=e.get('infoLinks',[])
  if any(l.get('targetId')==shared['Combat Drugs']['id'] for l in links):
   e['infoLinks']=[l for l in links if l.get('targetId')!=shared['Warband Elixirs']['id']]
  for p in e.get('profiles',[]):
   if p['name'].startswith('Signature Elixir: '):
    name=p['name'].split(': ',1)[1]
   elif p['name'].endswith(' (Signature Elixir)'):
    name=p['name'].removesuffix(' (Signature Elixir)')
   else:continue
   p['name']=name+' (Signature Elixir)'
   p['characteristics'][0]['$text']=data['signature_elixirs'][name]
  # Remove the extra lucid-doses explanation: the complete model-specific
  # permission belongs in Master of Excess on Fulgrim's own datasheet.
  if e['name']=='Fulgrim':
   master=next(p for p in e['profiles'] if p['name']=='Master of Excess')
   master['characteristics'][0]['$text']='Before the battle, select two different Warband Elixirs for this model. Their normal effects are always active for it without dosage tests. While not Stupefied, this model can take additional ordinary Combat Elixirs using their normal timing and dosage tests. When it becomes Stupefied, it retains both permanent elixirs, gains their Stupefied effects, and gains the normal and Stupefied effects of one additional accessible Combat Elixir.'
   for p in e['profiles']:
    if p['name']=='Ordinary Doses While Lucid':p['hidden']=True
  if e['name']=='Agoniser':
   for p in e.get('profiles',[]):
    if p['name']=='Equipment Options':
     p['name']='Paired Fists';p['characteristics'][0]['$text']='While this model is equipped with two Helbrute fists, add 2 to their Attacks characteristic and those weapons have Twin-linked.'
 # Every detachment grants its fixed allowed Disposition(s), like standard SM.
 detgroup=next(g for g in entries['Detachment']['selectionEntryGroups'] if g['name']=='Detachment')
 dispositions={'Disruption','Priority Assets','Purge the Foe','Take and Hold','Reconnaissance'}
 for e in detgroup['selectionEntries']:
  e['categoryLinks']=[l for l in e.get('categoryLinks',[]) if l['name'] not in dispositions]
  for name in data['dispositions'][e['name']]:
   e['categoryLinks'].append(dict(name=name,id=uid(e['id']+name),targetId=cats[name],primary=False,hidden=False))
  e['infoLinks']=[l for l in e.get('infoLinks',[]) if l.get('targetId')!=shared['Summoning Rituals']['id']]
  if e['name'] in ['Perfumed Procession','Ritual Host','Carnival of Excess']:
   e['infoLinks'].append(dict(id=uid(e['id']+':summoning'),name='Summoning Rituals',targetId=shared['Summoning Rituals']['id'],type='rule',hidden=False))
  # Named rules replace the generic 'Detachment rule' source dump.
  e['rules']=[dict(name=r['name'],id=uid(e['id']+':'+r['name']),description='\n\n'+r['text'],hidden=False) for r in data['detachments'][e['name']]]
 catalogue['readme']='Emperor’s Children homebrew v3.2. Dispositions assigned for all sixteen detachments. Update the list data after updating the game.'
