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
 lance=next(r['id'] for r in system['sharedRules'] if r['name']=='Lance')
 for node in walk(catalogue):
  for profile in node.get('profiles',[]):
   if profile.get('typeName')=='Melee Weapons' and profile['name']=='Phoenix power spear':
    keywords=next(c for c in profile['characteristics'] if c['name']=='Keywords')
    if 'Lance' not in keywords['$text']:
     keywords['$text']='Lance' if keywords['$text'] in ['','-'] else keywords['$text']+', Lance'
    links=node.setdefault('infoLinks',[])
    if not any(link.get('targetId')==lance for link in links):
     links.append(dict(id=uid(profile['id']+':lance'),name='Lance',type='rule',targetId=lance,hidden=False))
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
  for profile in e.get('profiles',[]):
   if profile.get('typeName')=='Abilities' and profile['name'] in {'Wargear Points','Weapon Selection'}:
    profile['hidden']=True
  # Remove the extra lucid-doses explanation: the complete model-specific
  # permission belongs in Master of Excess on Fulgrim's own datasheet.
  if e['name']=='Fulgrim':
   master=next(p for p in e['profiles'] if p['name']=='Master of Excess')
   master['characteristics'][0]['$text']='Before the battle, select two different Warband Elixirs for this model. Their normal effects are always active for it without dosage tests. While not Stupefied, this model can take additional ordinary Combat Elixirs using their normal timing and dosage tests. When it becomes Stupefied, it retains both permanent elixirs, gains their Stupefied effects, and gains the normal and Stupefied effects of one additional accessible Combat Elixir.'
   for p in e['profiles']:
    if p['name']=='Ordinary Doses While Lucid':p['hidden']=True
  if e['name']=='Cacophant':
   points=next(cost for cost in e['costs'] if cost['name']=='pts')
   points['value']=190
   for node in walk(e):
    if node.get('type')=='upgrade' and node['name']=='Ectoplasma cannon':
     costs=node.setdefault('costs',[])
     cost=next((cost for cost in costs if cost['name']=='pts'),None)
     if cost is None:costs.append(dict(name='pts',typeId=points['typeId'],value=5))
     else:cost['value']=5
  if e['name']=='Lucius the Eternal':
   eternal=next(p for p in e['profiles'] if p['name']=='The Eternal')
   eternal['characteristics'][0]['$text']="**Mark a host**\n\nOnce per turn, during the Shooting or Fight phase, when Lucius is destroyed by an attack made by an enemy unit, the controller of that attacking unit must select one non-Epic Hero Infantry model from that attacking unit, if one exists. Place an ETERNAL marker on that model.\n\n**Possession**\n\nAt the start of each Fight phase, roll one D6 for the marked model. On a 3+, remove the marker, destroy that model and return Lucius to the battlefield in its former position with D6 wounds remaining.\n\n- If his base cannot fit exactly, place him as close as possible.\n- He can be set up within Engagement Range of the host's former unit or other enemy units.\n- Lucius returns as a separate single-model unit and is Stupefied and Battle-shocked.\n\n**Combat Elixir**\n\nSelect one Combat Elixir from this codex for his unit, including Signature, Warband, detachment and enhancement elixirs. It gains the normal and Stupefied effects for that state. This does not refresh an expended once-per-battle use.\n\n**Host destroyed**\n\nIf the host dies before possession resolves, that marker is lost and does not revive Lucius."
  if e['name']=='Phoenix Guard Terminators':
   cleave=next(r['id'] for r in system['sharedRules'] if r['name']=='Cleave')
   twin=next(r['id'] for r in system['sharedRules'] if r['name']=='Twin-linked')
   for node in walk(e):
    for profile in node.get('profiles',[]):
     if profile.get('typeName')=='Melee Weapons' and profile['name']=='Phoenix power spear':
      next(c for c in profile['characteristics'] if c['name']=='A')['$text']='5'
      next(c for c in profile['characteristics'] if c['name']=='Keywords')['$text']='Lance, Cleave 2'
      links=node.setdefault('infoLinks',[])
      link=next((link for link in links if link.get('targetId') in [twin,cleave]),None)
      if link is None:
       link=dict(id=uid(profile['id']+':cleave'),type='rule',hidden=False)
       links.append(link)
      link.update(name='Cleave',targetId=cleave,modifiers=[dict(field='name',type='set',value='Cleave 2')])
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
 # Stratagems use a separate labelled section for each field.
 import re
 for rule in catalogue['sharedRules']:
  if not re.search(r'/ \d+ CP$',rule['name']):continue
  body=rule['description']
  # Normalize earlier formatting so repeated builds produce identical output.
  body=re.sub(r'#{1,6}\s*(When|Target|Effect|Restriction|Requirement|Duration|Cost)\s*\n',lambda m:m[1].upper()+': ',body,flags=re.I)
  body=re.sub(r'\s*(WHEN|TARGET|EFFECT|RESTRICTION|REQUIREMENT|DURATION|COST):\s*',lambda m:'\n\n### '+m[1].title()+'\n\n',body)
  rule['description']='\n\n'+body.strip()
 apply_threnody_titanic(catalogue,system)
 apply_character_and_summoning_updates(catalogue,system)
 rename_sonic_weapons(catalogue)
 catalogue['readme']='Emperor’s Children homebrew v3.2. Dispositions assigned for all sixteen detachments. Update the list data after updating the game.'


def rename_sonic_weapons(node):
 import re
 names={'dreadblastmaster':'dreadblaster','dread blastmaster':'dreadblaster','defiler blastmaster':'discord cannon','grand blastmaster':'requiem cannon','cathedral blastmaster':'cathedral annihilator'}
 pattern=re.compile(r'\b(?:'+ '|'.join(re.escape(n) for n in names)+r')(s?)\b',re.I)
 def replace(match):
  old=match[0]; key=old[:-1] if match[1] else old
  new=names[key.casefold()]
  if key[0].isupper():new=new[0].upper()+new[1:]
  return new+match[1]
 if isinstance(node,dict):
  for key,value in node.items():
   if isinstance(value,str):node[key]=pattern.sub(replace,value)
   else:rename_sonic_weapons(value)
 elif isinstance(node,list):
  for value in node:rename_sonic_weapons(value)


def apply_character_and_summoning_updates(catalogue,system):
 import re
 entries={entry['name']:entry for entry in catalogue['sharedSelectionEntries']}
 doom=next(p for p in entries['Doomrider']['profiles'] if p.get('typeName')=='Unit')
 next(c for c in doom['characteristics'] if c['name']=='InSv')['$text']='4+'
 def map_text(node,transform):
  if isinstance(node,dict):
   for key,value in node.items():
    if isinstance(value,str):node[key]=transform(value)
    else:map_text(value,transform)
  elif isinstance(node,list):
   for value in node:map_text(value,transform)
 lucius=entries['Lucius the Eternal']
 map_text(lucius,lambda text:text.replace('Feel No Pain 4+','Feel No Pain 5+'))
 fnp=next(r['id'] for r in system['sharedRules'] if r['name']=='Feel No Pain 5+')
 for link in lucius.get('infoLinks',[]):
  if link.get('name')=='Feel No Pain 5+':link['targetId']=fnp
 def summoning(text):
  text=re.sub(r'(Initial(?: Manifestation:)? )D3(?![+0-9])',r'\g<1>D3+1',text)
  text=re.sub(r'(?<=gains )D3(?![+0-9])(?= Manifestation points)',r'D3+1',text)
  text=text.replace('Roll two D3 for initial Manifestation and select one result.',
                    'Roll two D3, select one result and add 1 for initial Manifestation.')
  if 'initial Manifestation' in text:
   text=text.replace('roll two D3 and select one result.',
                     'roll two D3, select one result and add 1.')
  return text
 map_text(catalogue,summoning)


def apply_threnody_titanic(catalogue,system):
 from datasheet_format import walk
 entry=next(e for e in catalogue['sharedSelectionEntries'] if e['name']=='Threnody Dreadnought')
 titanic=next(c['id'] for c in system['categoryEntries']+catalogue.get('categoryEntries',[]) if c['name']=='Titanic')
 if not any(link.get('targetId')==titanic for link in entry['categoryLinks']):
  entry['categoryLinks'].append(dict(name='Titanic',id=uid(entry['id']+':titanic'),targetId=titanic,primary=False,hidden=False))
 for node in walk(entry):
  for key,value in node.items():
   if isinstance(value,str):
    node[key]=value.replace('Keywords: Vehicle, Walker, Threnody Dreadnought','Keywords: Vehicle, Walker, Titanic, Threnody Dreadnought')
