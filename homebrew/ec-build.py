"""Build the EC v3.2 catalogue. Uses only the Python standard library.
Usage: python3 build_ec.py --baseline DIR --output DIR
Use a complete current system/catalogue snapshot as the baseline.
Source data is the adjacent ec-source-data.json (or source-data.json in work).
"""
import argparse,json,copy,hashlib,re
from pathlib import Path
A=argparse.ArgumentParser();A.add_argument('--baseline',type=Path,required=True);A.add_argument('--output',type=Path,required=True);a=A.parse_args()
HERE=Path(__file__).parent
S=json.loads(next(p for p in [HERE/'ec-source-data.json',HERE/'source-data.json'] if p.exists()).read_text())
G=json.loads((a.baseline/'Warhammer 40,000.json').read_text())['gameSystem'];OLD=json.loads((a.baseline/"Chaos - Emperor's Children.json").read_text())['catalogue']
if OLD['revision'] >= 44:
 raise SystemExit('EC 4.0 is built with homebrew/ec-4.0-migrate.py from revision 43.')
PT='51b2-306e-1021-d207';DP='82ae-1066-5107-6ae0';EN='f759-1bc4-cb3a-f0d2';INC='d62d-db22-4893-4bc0';STRIKE='baf8-997f-e323-a090';ONS='4204-82d0-908c-a62a'
def uid(s):
 h=hashlib.sha256(('ec-3.1:'+s).encode()).hexdigest()[:16];return '-'.join(h[i:i+4] for i in range(0,16,4))
def app(o,k,x):o.setdefault(k,[]).append(x);return x
def entry(n,key,t='upgrade'):return dict(name=n,id=uid(key),type=t,hidden=False,**{'import':True})
def con(key,kind,v,scope='parent',field='selections',children=False):return dict(id=uid(key),type=kind,value=v,scope=scope,field=field,shared=True,includeChildSelections=children)
def cond(child,scope='force',kind='atLeast',v=1):return dict(childId=child,field='selections',scope=scope,type=kind,value=v,shared=True,includeChildSelections=True)
def mod(field,v,cs=None,t='set'):return dict(field=field,value=v,type=t,conditions=cs or [])
def maximum(o,n,key,scope='parent'):return app(o,'constraints',con(key,'max',n,scope,children=scope!='parent'))
def exact(o,n,key):
 for kind in ['min','max']:app(o,'constraints',con(key+kind,kind,n))
def price(o,v,typ=PT):app(o,'costs',dict(name={PT:'pts',DP:'Detachment Points',EN:'Enhancements'}[typ],typeId=typ,value=v))
def group(o,n,key,mini=0,maxi=1):
 g=dict(name=n,id=uid(key),hidden=False);app(o,'selectionEntryGroups',g)
 app(g,'constraints',con(key+'min','min',mini));app(g,'constraints',con(key+'max','max',maxi));return g
C={k:OLD[k] for k in ['id','battleScribeVersion','gameSystemId','xmlns']};C.update(name="Chaos - Emperor's Children",revision=OLD['revision']+1,gameSystemRevision=G['revision']+1,library=False,type='catalogue',authorName='Xverse homebrew',readme='Emperor’s Children homebrew v3.2, 7 November 2026. Create a new Army Roster after updating. Source transcription, build and validation notes are in homebrew/ec-*.')
CATS={x['name'].upper():x['id'] for x in G['categoryEntries']+OLD.get('categoryEntries',[])}
# Keep original keyword identifiers for cross-catalogue compatibility.
C['categoryEntries']=[dict(name=x['name'],id=x['id'],hidden=False) for x in OLD.get('categoryEntries',[])]
def cat(n,global_=False):
 n=n.strip();key=n.upper()
 if key not in CATS:
  CATS[key]=uid('cat:'+key);app(G if global_ else C,'categoryEntries',dict(name=n,id=CATS[key],hidden=False))
 return CATS[key]
def tag(o,n,primary=False):
 cid=cat(n)
 if any(x['targetId']==cid for x in o.get('categoryLinks',[])):return
 app(o,'categoryLinks',dict(name=n,id=uid(o['id']+':cat:'+n),targetId=cid,primary=primary,hidden=False))
def root(e):
 app(C,'sharedSelectionEntries',e);app(C,'entryLinks',dict(name=e['name'],id=uid('root:'+e['id']),targetId=e['id'],type='selectionEntry',hidden=False,**{'import':True}))
TYPES={x['name']:x for x in G['profileTypes']}
def profile(o,n,typ,values,key=None):
 t=TYPES[typ];return app(o,'profiles',dict(name=n,id=uid(key or o['id']+':profile:'+n+typ),typeId=t['id'],typeName=typ,hidden=False,characteristics=[dict(name=c['name'],typeId=c['id'],**{'$text':str(v)}) for c,v in zip(t['characteristicTypes'],values)]))
def rule(o,n,text,key=None):return app(o,'rules',dict(name=n,id=uid(key or o['id']+':rule:'+n),hidden=False,description=text))
def ability(o,n,text):profile(o,n,'Abilities',[text])
def linkrule(o,r,name=None,cs=None):
 l=dict(name=name or r['name'],id=uid(o['id']+':r:'+r['id']),targetId=r['id'],type='rule',hidden=cs is not None)
 if cs is not None:l['modifiers']=[mod('hidden',False,cs)]
 app(o,'infoLinks',l);return l
# Published dispositions for returning packages, explicit v3.1 permissions first.
disp=json.loads((HERE/'ec-display-data.json').read_text())['dispositions']
ALL_DISP=['Disruption','Priority Assets','Purge the Foe','Take and Hold','Reconnaissance']
UNSPECIFIED=[d['name'] for d in S['detachments'] if d['name'] not in disp]
DET={d['name']:uid('det:'+S.get('detachment_id_aliases',{}).get(d['name'],d['name'])) for d in S['detachments']}
cfg=entry('Detachment','detachment');tag(cfg,'Configuration',True);exact(cfg,1,'detachment-config');dg=group(cfg,'Detachment','det-group',1,4);dg['defaultSelectionEntryId']='none'
for d in S['detachments']:
 e=entry(d['name'],'det:'+S.get('detachment_id_aliases',{}).get(d['name'],d['name']));maximum(e,1,e['id']+'max');price(e,d['dp'],DP)
 for x in disp.get(d['name'],ALL_DISP):tag(e,x)
 if d['dp']==3:tag(e,'3DP Detachment')
 rule(e,'Detachment rule',d['rules'])
 if d['name'] in UNSPECIFIED:rule(e,'Disposition source gap','The codex does not state this detachment’s Force Disposition. Standard dispositions are provisionally selectable; agree the choice with your opponent. See homebrew/ec-VALIDATION.md.')
 app(dg,'selectionEntries',e)
root(cfg)
# References and selected-detachment stratagems are separate from detachment rules.
refs=entry('Army Rules and References','references');tag(refs,'Reference',True);exact(refs,1,'ref')
for r in S['references']:rule(refs,r['title'],r['text'],'reference:'+str(r['page']))
root(refs)
strats=entry('Stratagem References','stratagems');tag(strats,'Reference',True);exact(strats,1,'stratref')
for d in S['detachments']:
 for st in d['stratagems']:
  r=dict(name=d['name']+' — '+st['name']+' / '+str(st['cp'])+' CP',id=uid('strat:'+d['name']+st['name']),description=st['text'],hidden=False);app(C,'sharedRules',r);linkrule(strats,r,cs=[cond(DET[d['name']])])
root(strats)
# Individual shared army rules; allied models never inherit EC army rules.
ARMY={}
for name,pages in [('Combat Drugs',[5,6]),('Bound Excess',[7]),('Sublime Strategist',[8]),('Manifestation',[14]),('Warband Elixirs',[9,10]),('Summoning Rituals',[15,16])]:
 r=dict(name=name,id=uid('army:'+name),description='\n\n'.join(next(x['text'] for x in S['references'] if x['page']==i) for i in pages),hidden=False);ARMY[name]=r;app(C,'sharedRules',r)
# Elixir labels and full effects are retained as recorded before-battle choices.
ELIXIRS={}
for p in [9,10]:
 text=S['raw_pages'][str(p)];names=['Hyperstimulants','Frenzon','Adrenal Surge',"Razor's Edge"] if p==9 else ['Soporific Musk','Hallucinogens','Heightened Senses','Euphoric Numbness']
 for i,n in enumerate(names):ELIXIRS[n]=' '.join(text.split(n+'\n',1)[1].split('\n'+names[i+1]+'\n',1)[0].split()) if i+1<len(names) else ' '.join(text.split(n+'\n',1)[1].split())
ELIXIRS['Chronostim']='Start of your Shooting phase; until its end. After shooting, make a 6 inch Normal move if unengaged (9 inches if Stupefied). Cannot charge that turn.'
ELIXIRS['Sovereign Delusion']='Start of either Command phase; until the end of the turn. Add 1 OC. If Stupefied, Battle-shock does not set OC to 0; use modified OC.'
def elixir_choices(o,label,n,scopekey,optional=False):
 g=group(o,label,o['id']+scopekey,0 if optional else n,n)
 g['defaultSelectionEntryId']='none'
 for name,text in ELIXIRS.items():
  e=entry(name,g['id']+name);maximum(e,1,e['id']+'max');rule(e,name,text)
  if name in ['Chronostim','Sovereign Delusion']:e['hidden']=True;e['modifiers']=[mod('hidden',False,[cond(DET['The Perfect Formula'])])]
  app(g,'selectionEntries',e)
 return g
# Force-linked point category is required for New Recruit to enforce ally caps.
ALLIED=cat('Legions of Excess',True);ac=next(x for x in G['categoryEntries'] if x['id']==ALLIED);cap=con('allied-max','max',0,'force',PT,True);cap['message']='Legions of Excess allowance exceeded ({value} points maximum).';ac['constraints']=[cap];ac['modifiers']=[]
for n in ['Perfumed Procession','Ritual Host']:app(ac,'modifiers',mod(cap['id'],500,[cond(DET[n])],'increment'))
for sid,points in [(INC,500),(STRIKE,1000),(ONS,1500)]:app(ac,'modifiers',mod(cap['id'],points,[cond(sid),cond(DET['Carnival of Excess'])]))
LIVING=cat('Living Elixir assignments',True);lc=next(x for x in G['categoryEntries'] if x['id']==LIVING);lc['constraints']=[con('living-max','max',3,'force',children=True)]
for f in G['forceEntries']:
 if f['name']=='Army Roster':
  for name,cid in [('Legions of Excess',ALLIED),('Living Elixir assignments',LIVING)]:app(f,'categoryLinks',dict(name=name,id=uid('forcecat:'+name),targetId=cid,hidden=False))
# A single local Warlord entry avoids obsolete published EC rules.
wl=entry('Warlord','warlord');tag(wl,'Warlord');maximum(wl,1,'warlord-max','roster');app(C,'sharedSelectionEntries',wl)
NATIVE={};UNIT=None;USED=set();LARGE=None
# All equipment profiles refer to v3.1; alternative firing modes stay on one weapon.
def weaponkey(n):
 if n.startswith('Helbrute plasma'):return 'Helbrute plasma cannon'
 return n.split(' - ')[0]
def gear(o,n,qty=1):
 matches=[w for w in UNIT['weapons'] if weaponkey(w['name']).casefold()==n.casefold()]
 if not matches:raise ValueError((UNIT['name'],'weapon missing',n))
 e=entry(n,o['id']+':gear:'+n);exact(e,qty,e['id']+'qty');e['defaultAmount']=qty
 for w in matches:
  vals=w['values']+[w['keywords']];profile(e,w['name'],'Melee Weapons' if vals[0]=='Melee' else 'Ranged Weapons',vals);USED.add(w['name'])
 price(e,UNIT.get('wargear_points',{}).get(n,0)) if n in UNIT.get('wargear_points',{}) else None
 app(o,'selectionEntries',e);return e
def choice(o,n,opts,minimum=1,quantity=1):
 g=group(o,n,o['id']+':choice:'+n,minimum,1);g['defaultSelectionEntryId']='none' if minimum==0 else uid(g['id']+':'+opts[0][0] if isinstance(opts[0],tuple) else g['id']+':'+opts[0])
 for opt in opts:
  label,ws=opt if isinstance(opt,tuple) else (opt,[(opt,quantity)])
  e=entry(label,g['id']+':'+label);maximum(e,1,e['id']+'max')
  for w,q in ws:gear(e,w,q)
  app(g,'selectionEntries',e)
 return g
def token(o,n,text=''):
 e=entry(n,o['id']+':'+n);maximum(e,1,e['id']+'max');app(o,'selectionEntries',e)
 if text:rule(e,n,text)
 return e
def modelgroup(o,label,count):
 g=group(o,label,o['id']+':models',count,count)
 if LARGE:
  for c in g['constraints']:app(g,'modifiers',mod(c['id'],UNIT['sizes'][1],[cond(LARGE,o['id'])]))
 return g
def model(g,n,ws,default=0,max_=None,min_=0):
 e=entry(n,g['id']+n,'model');e['defaultAmount']=default
 app(e,'constraints',con(e['id']+'min','min',min_));cc=maximum(e,UNIT['sizes'][0] if max_ is None else max_,e['id']+'max',ROOT['id'])
 if LARGE and max_ is None:app(e,'modifiers',mod(cc['id'],UNIT['sizes'][1],[cond(LARGE,ROOT['id'])]))
 profile(e,n,'Unit',UNIT['stats'])
 for w,q in ws:gear(e,w,q)
 app(g,'selectionEntries',e);return e
def limit_large(e,small,large):
 c=maximum(e,large if UNIT['sizes'][0]>BASE_SIZE else small,e['id']+'special',ROOT['id'])
 if LARGE:app(e,'modifiers',mod(c['id'],large,[cond(LARGE,ROOT['id'])]))
 return c
def squads(o):
 p=UNIT['page'];size=UNIT['sizes'][0];g=modelgroup(o,'Models',size)
 def m(n,ws,d=0,mx=None,mn=0):return model(g,n,[(x,1) for x in ws],d,mx,mn)
 if p in [85,86]:
  champ=m('Obsessionist',['Bolt pistol','Power sword'],1,1,1)
  # Replace rather than retain the default weapons.
  champ.pop('selectionEntries');choice(champ,'Sidearm',['Bolt pistol','Plasma pistol']);choice(champ,'Melee weapon',['Power sword','Rapture lash'])
  ws=['Bolt pistol','Duelling sabre'] if p==85 else ['Boltgun','Close combat weapon']
  trooper=m('Infractor' if p==85 else 'Tormentor',ws,size-1)
  if p==86:
   for name in ['Plasma gun','Meltagun']:
    e=m('Tormentor with '+name,[name,'Close combat weapon']);limit_large(e,1,2)
  icon=token(o,'Icon of Excess');maximum(icon,1,icon['id']+'unit',o['id'])
  return
 if p==87:m('Congregation champion',['Congregation firearm','Champion lash'],1,1,1);m('Devotee',['Congregation firearm','Ritual blade'],size-1);return
 if p==88:
  m('Fleshbound',['Implant gun','Grafted blades'],size);e=m('Fleshbound with heavy cleaver',['Implant gun','Heavy cleavers']);limit_large(e,2,4);return
 if p==90:
  e=m('Disharmonist',['Sonic blaster','Close combat weapon'],1,1,1);e.pop('selectionEntries');choice(e,'Disharmonist equipment',[('Sonic blaster',[('Sonic blaster',1),('Close combat weapon',1)]),('Screamer pistol and power sword',[('Screamer pistol',1),('Power sword',1),('Close combat weapon',1)])])
  m('Noise Marine',['Sonic blaster','Close combat weapon'],5);e=m('Noise Marine with blastmaster',['Blastmaster','Close combat weapon'],0,2);return
 if p==92:
  m('Excruciator',['Combi-weapon','Accursed blade'],5)
  fist=m('Excruciator with power fist',['Combi-weapon','Power fist'],0,2)
  heavy=m('Excruciator with heavy weapon',[],0,1);choice(heavy,'Heavy weapon',['Shriek cannon','Doomfire projector']);mg=choice(heavy,'Melee weapon',['Accursed blade','Power fist'])
  c=fist['constraints'][-1];app(fist,'modifiers',mod(c['id'],1,[cond(mg['selectionEntries'][1]['id'],o['id'])]))
  m('Excruciator with paired blades',['Paired blades'],0,1);return
 if p==95:
  m('Ghost champion',['Whisper carbine','Champion power blade'],1,1,1);m('Ghost',['Whisper carbine','Ghost blade'],size-1);e=m('Ghost with execution needler',['Execution needler','Ghost blade']);limit_large(e,1,2);return
 if p==97:
  e=m('Talon champion',[],1,1,1);choice(e,'Sidearm',['Screamer pistol','Bolt pistol','Plasma pistol']);choice(e,'Melee weapon',['Talon blade','Champion power weapon'])
  e=m('Rapture Talon',[],size-1);choice(e,'Sidearm',['Screamer pistol','Bolt pistol']);gear(e,'Talon blade');return
 if p==101:
  champ=m('Cavalier champion',[],1,1,1);cg=choice(champ,'Ranged weapon',['Twin sonic blaster','Combi-weapon']);gear(champ,'Champion power weapon')
  m('Cavalier',['Twin sonic blaster','Rider blade'],size-1)
  e=m('Cavalier with combi-weapon',['Combi-weapon','Rider blade']);c=limit_large(e,1,2)
  app(e,'modifiers',mod(c['id'],1 if UNIT['sizes'][0]>BASE_SIZE else 0,[cond(cg['selectionEntries'][1]['id'],o['id'])]))
  if LARGE:app(e,'modifiers',mod(c['id'],1,[cond(LARGE,o['id']),cond(cg['selectionEntries'][1]['id'],o['id'])]))
  return
 defaults={89:['Slashing claws'],91:['Blissblade','Bolt pistol'],93:['Phoenix power spear'],94:['Dreadblastmaster','Crushing fists'],96:['Desperate blows'],98:['Shardglass blades'],99:['Hooked claws'],100:['Unmaking chorus','Talons of discord'],103:['Slashing claws','Lashing tongue'],104:['Hideous mutations'],106:['Barbed tail and dissecting claws']}
 e=m(UNIT['name'].rstrip('s'),defaults[p],size)
 if p in [89,103]:
  for name in ['Daemonic icon','Instrument of Chaos']:x=token(o,name);maximum(x,1,x['id']+'unit',o['id'])
 return

def equipment(o):
 p=UNIT['page']
 if UNIT['sizes'][0]>1:squads(o);return
 if p==63:
  gear(o,'Bolt pistol');gear(o,'Close combat weapon');choice(o,'Secondary weapon',['Plasma pistol','Power fist','Rapture lash']);choice(o,'Primary weapon',['Phoenix power spear','Master-crafted power sword','Screamer pistol']);return
 if p==64:
  gear(o,'Screamer pistol');choice(o,'Equipment',[('Power sword',[('Power sword',1)]),('Second screamer pistol and close combat weapon',[('Screamer pistol',1),('Close combat weapon',1)])]);return
 if p==70:gear(o,'Combi-bolter');choice(o,'Melee weapon',['Phoenix power spear','Sceptre of Exquisite Ruin']);return
 if p==73:choice(o,'Sidearm',['Injector pistol','Bolt pistol','Plasma pistol','Screamer pistol']);gear(o,'Surgical implements');gear(o,'Reductor');return
 if p==74:choice(o,'Sidearm',['Bolt pistol','Plasma pistol','Screamer pistol']);choice(o,'Melee weapon',['Phoenix power spear','Power fist']);return
 if p==75:choice(o,'Sidearm',['Bolt pistol','Plasma pistol']);gear(o,'Staff of excess');return
 if p==78:
  for w in ['Phantasmagoria','Witstealer sword','Snapping claws']:gear(o,w)
  g=choice(o,'Additional equipment',['Living whip','Ritual knife',('Shining aegis',[])])
  aegis=g['selectionEntries'][-1];rule(aegis,'Shining aegis','Improve this model’s Save characteristic to 3+.');app(o['profiles'][0],'modifiers',mod(TYPES['Unit']['characteristicTypes'][2]['id'],'3+',[cond(aegis['id'],o['id'])]));return
 if p==107:
  gear(o,'Combi-bolter');gear(o,'Armoured tracks');choice(o,'Additional weapon',['Combi-bolter','Combi-weapon'],0);choice(o,'Havoc launcher',['Havoc launcher'],0);return
 if p==108:gear(o,'Maulerfiend fists');choice(o,'Equipment',['Lasher tendrils',('Two magma cutters',[('Magma cutter',2)])]);return
 if p==109:
  gear(o,'Shearing claws');choice(o,'Main cannon',['Hades battle cannon','Ectoplasma destructor','Defiler blastmaster']);choice(o,'Secondary pair',[('Two excruciator cannons',[('Excruciator cannon',2)]),('Two magma cutters',[('Magma cutter',2)])])
  scourges=[]
  for name,default in [('Left mount','Heavy missile launcher'),('Right mount','Heavy baleflamer')]:
   opts=[default,'Hades lascannon','Heavy reaper autocannon','Electroscourge']+(['Sonic balespewer'] if default=='Heavy baleflamer' else [])
   g=choice(o,name,opts);scourges.append(next(e for e in g['selectionEntries'] if e['name']=='Electroscourge'))
  for e,other in [(scourges[0],scourges[1]),(scourges[1],scourges[0])]:app(e,'modifiers',mod(e['constraints'][0]['id'],0,[cond(other['id'],o['id'])]))
  return
 if p==111:
  fist=('Fist and heavy flamer',[('Helbrute fist',1),('Heavy flamer',1)])
  fist_choices=[]
  for label,opts in [('Ranged arm',['Multi-melta','Helbrute plasma cannon','Twin autocannon','Twin lascannon','Twin heavy bolter',fist,'Helbrute hammer','Power scourge']),('Melee arm',[fist,'Missile launcher','Helbrute hammer','Power scourge'])]:
   g=choice(o,label,opts);fist_choices.append(next(x for x in g['selectionEntries'] if x['name']=='Fist and heavy flamer'))
  for e in fist_choices:
   fp=next(x for ge in e['selectionEntries'] if ge['name']=='Helbrute fist' for x in ge['profiles']);cs=[cond(x['id'],o['id']) for x in fist_choices]
   app(fp,'modifiers',mod(TYPES['Melee Weapons']['characteristicTypes'][1]['id'],2,cs,'increment'));app(fp,'modifiers',mod(TYPES['Melee Weapons']['characteristicTypes'][-1]['id'],'Twin-linked',cs))
  gear(o,'Armoured limbs');return
 if p==112:
  gear(o,'Cathedral sonic immolator');gear(o,'Crushing tread');choice(o,'Secondary pair',[('Two heavy bolters',[('Heavy bolter',2)]),('Two sonic blasters',[('Sonic blaster',2)])]);choice(o,'Arm weapon',['Cathedral fist','Twin lascannon','Grand blastmaster']);return
 if p==113:
  choice(o,'Arm weapons',[('Two Hades autocannons',[('Hades autocannon',2)]),('Two ectoplasma cannons',[('Ectoplasma cannon',2)]),('Two resonance cannons',[('Resonance cannon',2)])]);choice(o,'Head weapon',['Cacophant jaws',('Ectoplasma cannon and armoured limbs',[('Ectoplasma cannon',1),('Armoured limbs',1)]),('Resonance cannon and armoured limbs',[('Resonance cannon',1),('Armoured limbs',1)])]);return
 if p==114:
  gear(o,'Armoured tracks');choice(o,'Turret',['Predator autocannon','Twin lascannon','Sonic destructor']);choice(o,'Sponsons',[('Two heavy bolters',[('Heavy bolter',2)]),('Two lascannons',[('Lascannon',2)]),('Two sonic blasters',[('Sonic blaster',2)])]);choice(o,'Havoc launcher',['Havoc launcher'],0);return
 if p==116:
  gear(o,'Armoured tracks');choice(o,'Main pair',[('Two soulshatter lascannons',[('Soulshatter lascannon',2)]),('Two cathedral blastmasters',[('Cathedral blastmaster',2)])]);choice(o,'Secondary',['Twin heavy bolter','Twin sonic blaster']);choice(o,'Multi-melta',['Multi-melta'],0);choice(o,'Havoc launcher',['Havoc launcher'],0);return
 if p==117:gear(o,'Heldrake claws');choice(o,'Ranged weapon',['Hades autocannon','Sonic balespewer']);return
 for key in dict.fromkeys(weaponkey(w['name']) for w in UNIT['weapons']):gear(o,key)
# Correct source-table keyword aliases from the explicitly printed character text.
for u in S['units']:
 for w in u['weapons']:
  n=w['name']
  if u['name']=='Ramos' and 'Refrain' in n:w['keywords']='Blast 2, Ignores Cover'
  if u['name']=='Doomrider' and n.startswith('Daemonic twin meltagun'):w['keywords']='Melta 3, Twin-linked'+(', Hunter: Monster/Vehicle' if 'Hunter' in n else '')
  if u['name']=='Raptureweaver' and n.startswith('Blissfire'):w['keywords']='Psychic, Torrent, Blast 1, Ignores Cover'+(', Hazardous' if 'Focused' in n else '')
  if u['name']=='Torment Oracle' and n.startswith('Soulspike'):w['keywords']='Psychic, Precision'+(', Hazardous' if 'Focused' in n else '')
  if u['name'] in ['Lord Exultant','Lord Kakophonist']:
   kw={'Bolt pistol':'Close-Quarters','Plasma pistol - standard':'Close-Quarters','Plasma pistol - supercharge':'Close-Quarters, Hazardous','Screamer pistol':'Close-Quarters, Blast 1, Ignores Cover','Master-crafted power sword':'Precision','Phoenix power spear':'Lance','Rapture lash':'Extra Attacks'}
   w['keywords']=kw.get(n,w['keywords'])
for u in S['units']:
 UNIT=u;USED=set();LARGE=None;o=entry(u['name'],'unit:'+u['name'],'unit' if u['sizes'][0]>1 else 'model');ROOT=o;NATIVE[u['name']]=o
 role='Dedicated Transport' if 'Dedicated Transport' in u['keywords'] else u['role'];tag(o,'Legions of Excess' if u['allied'] else role,True)
 for kw in u['keywords']:
  if kw.upper()!=role.upper() or u['allied']:tag(o,kw)
 tag(o,'Faction: Legions of Excess' if u['allied'] else "Faction: Emperor's Children")
 tag(o,u['name'])
 limit=1 if u['role']=='Epic Hero' else 6 if role in ['Battleline','Dedicated Transport'] else 3
 capu=maximum(o,limit,o['id']+'copies','roster')
 if limit>1:app(o,'modifiers',mod(capu['id'],limit//3*2,[cond(INC)]))
 price(o,u['points'][0]);profile(o,u['name'],'Unit',u['stats'])
 repeat_cost=S['additional_selection_costs'].get(u['name'])
 if repeat_cost:
  app(o,'modifiers',dict(field=PT,type='increment',value=repeat_cost['points'],conditionGroups=[dict(type='and',localConditionGroups=[dict(field='selections',includeChildForces=True,includeChildSelections=True,repeats=1,scope='parent',type='atLeast',value=repeat_cost['from_selection']-1,conditions=[cond('any','self','before'),cond(o['id'],'self','instanceOf')])])]))
 if len(u['sizes'])==2:
  sz=group(o,'Unit Size',o['id']+':size',1,1)
  for j,n in enumerate(u['sizes']):
   e=entry(str(n)+' models',sz['id']+str(n));maximum(e,1,e['id']+'max');price(e,u['points'][j]-u['points'][0]);app(sz,'selectionEntries',e)
   if j==0:sz['defaultSelectionEntryId']=e['id']
   else:LARGE=e['id']
 # Keep exact datasheet text readable rather than flattening it into an abilities table.
 rule(o,'Datasheet rules and equipment',u['rules'])
 for name in u['army_rules']:linkrule(o,ARMY[name])
 if 'Combat Drugs' in u['army_rules'] or 'Bound Excess' in u['army_rules']:linkrule(o,ARMY['Warband Elixirs'])
 if u['allied']:linkrule(o,ARMY['Summoning Rituals'])
 if 'Character' in u['keywords'] and not u['allied']:
  l=dict(name='Warlord',id=uid(o['id']+'warlord'),type='selectionEntry',targetId=wl['id'],hidden=False,**{'import':True})
  if u['name']=='Fulgrim':l['constraints']=[con(l['id']+'required','min',1)]
  else:l['modifiers']=[mod('hidden',True,[cond(uid('unit:Fulgrim'))])]
  app(o,'entryLinks',l)
 if 'Bound Excess' in u['army_rules'] or u['name']=='Fulgrim':elixir_choices(o,'Master of Excess — permanent elixirs' if u['name']=='Fulgrim' else 'Bound Excess — permanent elixirs',2,'permanent')
 if u['name']=='Threnody Dreadnought':
  g=elixir_choices(o,'Interred in Rapture — starting elixir',1,'threnody')
 if u['name'] in ['Keeper of Secrets','Tranceweaver','Infernal Enrapturess','Contorted Epitome','Fiends','Choir of Unmaking']:
  g=elixir_choices(o,'Living Elixir assignment',1,'living',True);g['hidden']=True;g['modifiers']=[mod('hidden',False,[cond(DET['Perfumed Procession'])])]
  for e in g['selectionEntries']:tag(e,'Living Elixir assignments')
 BASE_SIZE=u['sizes'][0]
 parts=[]
 if len(u['sizes'])==2:
  sz=next(g for g in o['selectionEntryGroups'] if g['name']=='Unit Size');LARGE=None
  for size,part in zip(u['sizes'],sz['selectionEntries']):
   UNIT=copy.deepcopy(u);UNIT['sizes']=[size];equipment(part);parts.append(part)
  UNIT=u
 else:equipment(o);parts=[o]
 if u['sizes'][0]>1:
  for part in parts:
   mg=next(g for g in part['selectionEntryGroups'] if g['name']=='Models');regular=max(mg['selectionEntries'],key=lambda e:e['defaultAmount']);mc=regular['constraints'][0];mc['value']=regular['defaultAmount'];mx=regular['constraints'][1];mx['value']=regular['defaultAmount']
   for special in mg['selectionEntries']:
    if special['defaultAmount'] or special is regular:continue
    app(regular,'modifiers',dict(field=mc['id'],type='increment',value=-1,repeats=[dict(childId=special['id'],field='selections',scope=o['id'],shared=True,includeChildSelections=True,value=1,repeats=1,roundUp=False)]))
 missing={w['name'] for w in u['weapons']}-USED
 if missing:raise ValueError((u['name'],'unrepresented weapons',missing))
 root(o)
 if u['allied']:
  l=C['entryLinks'][-1];l['hidden']=True;l['modifiers']=[dict(field='hidden',type='set',value=False,conditionGroups=[dict(type='or',conditions=[cond(DET[n]) for n in ['Carnival of Excess','Perfumed Procession','Ritual Host']])])]
# Attachment index is explicit, rather than guessing eligibility from substrings.
LEADERS={'Lucius the Eternal':['Flawless Blades','Phoenix Guard Terminators'],'Eidolon':['Infractors','Flawless Blades','Rapture Talons'],'Ramos':['Noise Marines','Excruciator Terminators','Dissonant Colossi'],'Lord Exultant':['Infractors','Tormentors'],'Lord Kakophonist':['Noise Marines','Excruciator Terminators'],'Raptureweaver':['Tormentors','Infractors','Noise Marines'],'Torment Oracle':['Tormentors','Noise Marines','Flawless Blades'],'Lord Exultant in Terminator Armour':['Excruciator Terminators','Phoenix Guard Terminators'],'Lord Exultant with Jump Pack':['Rapture Talons'],'The Gilded Knife':['Ghosts','Ecstatic Congregation'],'Sibyl of Excess':['Ecstatic Congregation','Chained Thralls','Fleshbound'],"Syll'Esske":['Daemonettes','Mirror Guard'],'Tranceweaver':['Daemonettes'],'Infernal Enrapturess':['Daemonettes','Choir of Unmaking'],'Contorted Epitome':['Daemonettes','Mirror Guard','Choir of Unmaking'],'Fulgrim':['Phoenix Guard Terminators']}
SUPPORT={'Chirurgeon':['Tormentors','Infractors','Noise Marines','Flawless Blades','Fleshbound'],'Herald of Excess':['Tormentors','Infractors','Noise Marines','Flawless Blades','Fleshbound','Ecstatic Congregation']}
for kind,lookup in [('Leader',LEADERS),('Support',SUPPORT)]:
 for name,targets in lookup.items():
  e=NATIVE[name];app(e,'associations',dict(name='Leading' if kind=='Leader' else 'Supporting',id=uid(e['id']+':attachment'),action='group',childId='unit',childName='unit',includeChildSelections=True,label=kind,max=1,min=1 if kind=='Support' else 0,scope='force',conditionGroups=[dict(type='or',conditions=[cond(NATIVE[n]['id'],'self','instanceOf') for n in targets])]))
SONIC_WEAPONS = {'sonic blaster','twin sonic blaster','screamer pistol','combi-weapon - sonic','blastmaster','dreadblastmaster','grand blastmaster','cathedral blastmaster','defiler blastmaster','sonic balespewer','sonic destructor','cathedral sonic immolator','resonance cannon','shriek cannon','grand vox array','death scream',"the eighth's refrain"}
def is_sonic(name):
 n=name.casefold()
 return any(n==w or n.startswith(w+' - ') for w in SONIC_WEAPONS)
def walk_nodes(node):
 if isinstance(node,dict):
  yield node
  for value in node.values():yield from walk_nodes(value)
 elif isinstance(node,list):
  for value in node:yield from walk_nodes(value)
# Eligibility is based on the printed first sentence and explicit unit names.
def eligible(u,d,h):
 kw=set(u['keywords']);name=u['name'];text=h['text'].split('. ')[0];allied=u['allied'];char='Character' in kw
 if u['role']=='Epic Hero':return False
 if not h['upgrade'] and not char:return False
 if h['upgrade'] and char:return False
 if h['name'].startswith('Censer'):return allied and name in ['Keeper of Secrets','Tranceweaver','Infernal Enrapturess','Contorted Epitome']
 if h['name']=='Warp Walker':return not allied or name=='Keeper of Secrets'
 if d['name']=='The Harmonic Cabal':return char and 'Psyker' in kw
 if allied:return False
 if 'Non-Daemon' in text or 'non-Daemon' in text:
  if 'Daemon' in kw:return False
 if h['name'] in ['Master of Reconstruction',"Reanimator's Vial"]:return name=='Chirurgeon'
 if h['name']=="Conductor's Baton":return name=='Lord Kakophonist'
 if h['name']=='Gilded Command':return name=='Lord Exultant in Terminator Armour'
 if h['upgrade']:
  n=h['name'];specific={'Awakening Chimes':['Threnody Dreadnought'],'Rapt Congregation':['Ecstatic Congregation','Chained Thralls','Fleshbound'],'Vanishing Refrain':['Ghosts'],'Auric Panoply':['Excruciator Terminators','Phoenix Guard Terminators'],'Resonance Baffles':['Noise Marines','Dissonant Colossi','Threnody Dreadnought'],'Exquisite Balance':['Infractors','Flawless Blades','Excruciator Terminators','Phoenix Guard Terminators'],'Bounding Excess':['Howling Cavaliers','Rapture Talons']}
  n=n.replace(' [Upgrade]','')
  if n in specific:return name in specific[n]
  if n=='Perfumed Furnace':return {'Daemon','Vehicle'}<=kw
  if n=='Expanded Processional Hold':return 'Transport' in kw
  if n=='Cathedral Amplifier':return 'Vehicle' in kw
  if n=='Bloodglass Infusions':return 'Infantry' in kw and 'Daemon' not in kw and 'Combat Drugs' in u['army_rules']
  raise ValueError(('unhandled upgrade',h))
 if 'Infantry or Mounted' in text:return bool(kw&{'Infantry','Mounted'})
 if 'Infantry' in text and 'Infantry' not in kw:return False
 if 'excluding Terminators' in text and 'Terminator' in kw:return False
 if 'excluding Vehicles' in text and 'Vehicle' in kw:return False
 return True
# Store enhancements in this catalogue; all datasheets share one combined slot.
for u in S['units']:
 e=NATIVE[u['name']];pairs=[(d,h) for d in S['detachments'] for h in d['enhancements'] if eligible(u,d,h)]
 if not pairs:continue
 g=group(e,'Enhancements and Upgrades',e['id']+':enhancements',0,1);g['defaultSelectionEntryId']='none'
 for d,h in pairs:
  eid=uid('enh:'+d['name']+h['name']);existing=next((x for x in C.get('sharedSelectionEntries',[]) if x['id']==eid),None)
  if existing is None:
   he=entry(h['name'],'enh:'+d['name']+h['name']);price(he,h['points']);price(he,1,EN);maximum(he,3 if h['upgrade'] else 1,he['id']+'roster','roster');rule(he,h['name'],h['text']);
   if h['name'] in ["Alchemist's Chalice",'Bloodglass Infusions [Upgrade]']:
    page=S['raw_pages']['23'];label='Kingsbane Distillate' if h['name']=="Alchemist's Chalice" else 'Glassvein Nectar';text=page.split('Personal Elixir: '+label+'\n',1)[1].split('Personal Elixir:',1)[0];rule(he,label,' '.join(text.split()))
   he['hidden']=False
   if h['upgrade']:
    app(he,'modifiers',dict(field=EN,type='set',value=0,conditionGroups=[dict(type='and',localConditionGroups=[dict(field='selections',includeChildSelections=True,repeats=1,scope='roster',type='atLeast',value=1,conditions=[cond('any','self','before'),cond(eid,'self','instanceOf')])])]))
   app(C,'sharedSelectionEntries',he)
  l=dict(name=h['name'],id=uid(g['id']+eid),targetId=eid,type='selectionEntry',hidden=True,modifiers=[mod('hidden',False,[cond(DET[d['name']])])],**{'import':True})
  if h['name'].startswith('Censer'):
   living=next(x for x in e['selectionEntryGroups'] if x['name']=='Living Elixir assignment');l['modifiers'].append(mod('hidden',True,[cond(x['id'],e['id'],'lessThan') for x in living['selectionEntries']]))
  app(g,'entryLinks',l)
# Update only the current system snapshot; preserve previous Agents fixes.
G['revision']+=1;C['gameSystemRevision']=G['revision']
from ec_reference_format import apply_references
REFERENCE_REPORT=apply_references(C,G,S)
a.output.mkdir(parents=True,exist_ok=True)
for fn,key,obj in [("Chaos - Emperor's Children.json",'catalogue',C),('Warhammer 40,000.json','gameSystem',G)]:
 (a.output/fn).write_text(json.dumps({key:obj},indent=2,ensure_ascii=False)+'\n')
coverage=dict(source_version=S['version'],source_pdf_sha256=S['pdf_sha256'],reference_display=REFERENCE_REPORT,native_units=sum(not u['allied'] for u in S['units']),allied_units=sum(u['allied'] for u in S['units']),weapon_profiles=sum(len(u['weapons']) for u in S['units']),detachments=16,enhancements=sum(len(d['enhancements']) for d in S['detachments']),stratagems=sum(len(d['stratagems']) for d in S['detachments']),dispositions_inherited=['Peerless Bladesmen','Rapid Evisceration','Mercurial Host'],dispositions_unspecified=UNSPECIFIED,native_root_ids={n:e['id'] for n,e in NATIVE.items()},runtime_test='Published-revision live checks are recorded in homebrew/ec-VALIDATION.md.')
(a.output/'ec-coverage.json').write_text(json.dumps(coverage,indent=2)+'\n');print(json.dumps(coverage,indent=2))

