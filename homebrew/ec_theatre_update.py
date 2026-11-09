"""Apply the accepted Theatre, Vhalyss and Greater Ritual changes."""
import copy,hashlib,json
from pathlib import Path

PT='51b2-306e-1021-d207';EN='f759-1bc4-cb3a-f0d2'
OLD="The Grand Symphony";NEW="The Theatre of Excess";VHALYSS='Vhalyss, the First Scream'
OLD_ENH={"Maestro's Perfect Pitch",'Audience of One Thousand','Amplification Array [Upgrade]'}

def uid(s):
 h=hashlib.sha256(('ec-3.1:'+s).encode()).hexdigest()[:16]
 return '-'.join(h[i:i+4] for i in range(0,16,4))

def walk(n):
 if isinstance(n,dict):
  yield n
  for v in n.values():yield from walk(v)
 elif isinstance(n,list):
  for v in n:yield from walk(v)

def constraint(key,typ,value,scope='parent'):
 return dict(id=uid(key),type=typ,value=value,scope=scope,field='selections',shared=True,includeChildSelections=scope!='parent')

def condition(child):
 return dict(childId=child,field='selections',scope='force',shared=True,includeChildSelections=True,type='atLeast',value=1)

def apply_latest(catalogue,system,source=None):
 here=Path(__file__).parent
 source=source or json.loads((here/'ec-source-data.json').read_text())
 display=json.loads((here/'ec-display-data.json').read_text())
 det_source=next(d for d in source['detachments'] if d['name']==NEW)
 types={t['name']:t for t in system['profileTypes']}
 cats={x['name']:x['id'] for x in system['categoryEntries']+catalogue.get('categoryEntries',[])}
 shared={r['name']:r for r in catalogue['sharedRules']}
 def cat(name):
  if name not in cats:
   cats[name]=uid('cat:'+name.upper());catalogue.setdefault('categoryEntries',[]).append(dict(name=name,id=cats[name],hidden=False))
  return cats[name]
 def profile(owner,name,typ,values):
  t=types[typ]
  return dict(name=name,id=uid(owner+':profile:'+name+typ),typeId=t['id'],typeName=typ,hidden=False,characteristics=[dict(name=c['name'],typeId=c['id'],**{'$text':str(v)}) for c,v in zip(t['characteristicTypes'],values)])
 def tag(e,name,primary=False):
  e.setdefault('categoryLinks',[]).append(dict(name=name,id=uid(e['id']+':cat:'+name),targetId=cat(name),primary=primary,hidden=False))
 def rule_link(e,rule,printed=None):
  link=dict(name=rule['name'],id=uid(e['id']+':core:'+rule['id']),targetId=rule['id'],type='rule',hidden=False)
  if printed:link['modifiers']=[dict(field='name',type='set',value=printed)]
  e.setdefault('infoLinks',[]).append(link)
 # Remove the unit keyword and every conditional source of that keyword.
 sonic={x['id'] for x in catalogue.get('categoryEntries',[]) if x['name'].upper()=='SONIC'}
 for n in list(walk(catalogue)):
  if 'categoryLinks' in n:n['categoryLinks']=[l for l in n['categoryLinks'] if l.get('targetId') not in sonic]
  if 'modifiers' in n:n['modifiers']=[m for m in n['modifiers'] if not (m.get('field')=='category' and m.get('value') in sonic)]
 catalogue['categoryEntries']=[x for x in catalogue.get('categoryEntries',[]) if x['id'] not in sonic]
 # Retain the old detachment ID so existing roster selections can update.
 config=next(e for e in catalogue['sharedSelectionEntries'] if e['name']=='Detachment')
 det=next(e for e in config['selectionEntryGroups'][0]['selectionEntries'] if e['name'] in [OLD,NEW]);det['name']=NEW
 det['rules']=[dict(name=r['name'],id=uid(det['id']+':theatre:'+r['name']),description='\n\n'+r['text'],hidden=False) for r in display['detachments'][NEW]]
 # The Executioner changes only its fighting-form effect.
 peerless=next(e for e in config['selectionEntryGroups'][0]['selectionEntries'] if e['name']=='Peerless Bladesmen')
 for r in peerless['rules']:
  if r['name']=='Exquisite Swordsmanship':r['description']='\n\n'+next(x['text'] for x in display['detachments']['Peerless Bladesmen'] if x['name']==r['name'])
 # Remove the old detachment's upgrades and all links to them.
 new_names={h['name'] for h in det_source['enhancements']}
 removed={e['id'] for e in catalogue['sharedSelectionEntries'] if e['name'] in OLD_ENH|new_names}
 catalogue['sharedSelectionEntries']=[e for e in catalogue['sharedSelectionEntries'] if e['id'] not in removed]
 for n in list(walk(catalogue)):
  if 'entryLinks' in n:n['entryLinks']=[l for l in n['entryLinks'] if l.get('targetId') not in removed]
 # Replace, rather than retain, the Stage Token stratagems.
 old_rules={r['id'] for r in catalogue['sharedRules'] if r['name'].startswith((OLD+' — ',NEW+' — '))}
 catalogue['sharedRules']=[r for r in catalogue['sharedRules'] if r['id'] not in old_rules]
 refs=next(e for e in catalogue['sharedSelectionEntries'] if e['name']=='Stratagem References')
 refs['infoLinks']=[l for l in refs['infoLinks'] if l['targetId'] not in old_rules]
 import re
 for st in det_source['stratagems']:
  name=NEW+' — '+st['name']+' / '+str(st['cp'])+' CP';identifier=uid('strat:'+NEW+st['name'])
  body=re.sub(r'\s*(WHEN|TARGET|EFFECT):\s*',lambda m:'\n\n### '+m[1].title()+'\n\n',st['text']).strip()
  catalogue['sharedRules'].append(dict(name=name,id=identifier,description='\n\n'+body,hidden=False))
  refs['infoLinks'].append(dict(name=name,id=uid('theatre:strat-link:'+identifier),targetId=identifier,type='rule',hidden=True,modifiers=[dict(field='hidden',type='set',value=False,conditions=[condition(det['id'])])]))
 # Update the shared ritual and the two existing Greater Daemon cards.
 shared['Summoning Rituals']['description']='\n\n'+display['army_rules']['Summoning Rituals']
 shared['Manifestation']['description']='\n\n'+display['army_rules']['Manifestation']
 for entry in catalogue['sharedSelectionEntries']:
  if any(l['name']=='Greater Daemon' for l in entry.get('categoryLinks',[])):
   for p in entry.get('profiles',[]):
    if p['name']=='Summoning and Manifestation':p['characteristics'][0]['$text']='Greater Daemonic Ritual. Maximum Manifestation: 6.'
 # Apply the wording of the Ritual Host options to both new and existing data.
 ritual=next(d for d in source['detachments'] if d['name']=='Ritual Host')
 for st in ritual['stratagems']:
  if st['name'] not in ['Summoning Circle','An Offering Nonetheless']:continue
  target=next(r for r in catalogue['sharedRules'] if r['name'].startswith('Ritual Host — '+st['name']+' / '))
  target['description']='\n\n'+re.sub(r'\s*(WHEN|TARGET|EFFECT):\s*',lambda m:'\n\n### '+m[1].title()+'\n\n',st['text']).strip()
 knife=next(e for e in catalogue['sharedSelectionEntries'] if e['name']=='Consecrated Sacrificial Knife')
 knife['rules'][0]['description']=next(h['text'] for h in ritual['enhancements'] if h['name']==knife['name'])
 # Vhalyss carries its own profiles, using the game's standard schema.
 u=next(u for u in source['units'] if u['name']==VHALYSS);eid=uid('unit:'+VHALYSS)
 e=dict(name=VHALYSS,id=eid,type='model',hidden=False,**{'import':True},constraints=[constraint(eid+'copies','max',1,'roster')],costs=[dict(name='pts',typeId=PT,value=u['points'][0])],profiles=[profile(eid,VHALYSS,'Unit',u['stats'])],rules=[dict(name='Datasheet rules and equipment',id=uid(eid+':rule:Datasheet rules and equipment'),description=u['rules'],hidden=True)])
 tag(e,'Legions of Excess',True)
 for keyword in u['keywords']:tag(e,keyword)
 tag(e,VHALYSS)
 tag(e,'Faction: Legions of Excess')
 for a in u['abilities']:e['profiles'].append(profile(eid,a['name'],'Abilities',[a['text']]))
 for name in ['Manifestation','Summoning Rituals']:rule_link(e,shared[name])
 core={r['name']:r for r in system['sharedRules']}
 for name,printed in [('Deadly Demise','Deadly Demise D6'),('Damaged','Damaged 6')]:rule_link(e,core[name],printed)
 scream=dict(name='First Scream',id=uid(eid+':weapon:First Scream'),type='upgrade',hidden=False,**{'import':True},defaultAmount=1,constraints=[constraint(eid+':scream-min','min',1),constraint(eid+':scream-max','max',1)],profiles=[])
 talons=dict(name='Talons of Discord',id=uid(eid+':weapon:Talons of Discord'),type='upgrade',hidden=False,**{'import':True},defaultAmount=1,constraints=[constraint(eid+':talons-min','min',1),constraint(eid+':talons-max','max',1)],profiles=[])
 for w in u['weapons']:
  owner=talons if w['values'][0]=='Melee' else scream
  owner['profiles'].append(profile(owner['id'],w['name'],'Melee Weapons' if owner is talons else 'Ranged Weapons',w['values']+[w['keywords']]))
 for name,printed in [('Blast','Blast 2'),('Ignores Cover',None),('Psychic',None)]:rule_link(scream,core[name],printed)
 e['selectionEntries']=[scream,talons]
 existing=next((i for i,n in enumerate(catalogue['sharedSelectionEntries']) if n['id']==eid),None)
 if existing is None:catalogue['sharedSelectionEntries'].append(e)
 else:catalogue['sharedSelectionEntries'][existing]=e
 root=next((l for l in catalogue['entryLinks'] if l['targetId']==eid),None)
 if root is None:
  root=dict(name=VHALYSS,id=uid('root:'+eid),targetId=eid,type='selectionEntry',hidden=True,**{'import':True});catalogue['entryLinks'].append(root)
 allowed=[x['id'] for x in config['selectionEntryGroups'][0]['selectionEntries'] if x['name'] in ['Carnival of Excess','Perfumed Procession','Ritual Host']]
 root['hidden']=True;root['modifiers']=[dict(field='hidden',type='set',value=False,conditionGroups=[dict(type='or',conditions=[condition(i) for i in allowed])])]
 # Retain the Sonic Weapon definition without recreating the SONIC unit keyword.
 sonic_ref=next(x for x in source['references'] if x['page']==136)
 sonic_rule=next((r for r in catalogue['sharedRules'] if r['name']=='Sonic Weapons'),None)
 if sonic_rule is None:
  sonic_rule=dict(name='Sonic Weapons',id=uid('rule:sonic-weapon-register'),hidden=False);catalogue['sharedRules'].append(sonic_rule)
 sonic_rule['description']=sonic_ref['text'];rule_link(e,sonic_rule)
 catalogue['sharedRules']=[r for r in catalogue['sharedRules'] if r['id']!=sonic_rule['id']]+[sonic_rule]
 # Four enhancements, one standard slot per eligible Character, each army-unique.
 unit_source={u['name']:u for u in source['units']}
 for h in det_source['enhancements']:
  hid=uid('enh:'+NEW+h['name']);he=dict(name=h['name'],id=hid,type='upgrade',hidden=False,**{'import':True},costs=[dict(name='pts',typeId=PT,value=h['points']),dict(name='Enhancements',typeId=EN,value=1)],constraints=[constraint(hid+'roster','max',1,'roster')],rules=[dict(name=h['name'],id=uid(hid+':rule:'+h['name']),hidden=False,description=h['text'])]);catalogue['sharedSelectionEntries'].append(he)
  for entry in catalogue['sharedSelectionEntries']:
   src=unit_source.get(entry['name'])
   if src is None or src['allied'] or src['role']=='Epic Hero' or 'Character' not in src['keywords']:continue
   group=next((g for g in entry.get('selectionEntryGroups',[]) if g['name']=='Enhancements and Upgrades'),None)
   if group is None:
    gid=uid(entry['id']+':enhancements');group=dict(name='Enhancements and Upgrades',id=gid,hidden=False,defaultSelectionEntryId='none',constraints=[constraint(gid+'min','min',0),constraint(gid+'max','max',1)],entryLinks=[]);entry.setdefault('selectionEntryGroups',[]).append(group)
   group.setdefault('entryLinks',[]).append(dict(name=h['name'],id=uid(group['id']+hid),targetId=hid,type='selectionEntry',hidden=True,**{'import':True},modifiers=[dict(field='hidden',type='set',value=False,conditions=[condition(det['id'])])]))
 catalogue['readme']="Emperor's Children homebrew: Theatre of Excess and Vhalyss update. Update your list's data after updating the game."
