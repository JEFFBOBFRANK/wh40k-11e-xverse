"""Rebuild the Agents catalogue from the transcribed v0.9.2 source.

Run from any directory: python3 homebrew/build.py --upstream /path/to/BSData
Only Python's standard library is needed. Source transcription requires no PDF
at build time. All generated identifiers are deterministic.
"""
import argparse, copy, hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parent
SRC=json.loads((HERE/'source-data.json').read_text())
ARGS=argparse.ArgumentParser()
ARGS.add_argument('--upstream',type=Path,required=True)
UP=ARGS.parse_args().upstream
PT='51b2-306e-1021-d207';DP='82ae-1066-5107-6ae0';EN='f759-1bc4-cb3a-f0d2'
OLD_SYS='sys-352e-adc2-7639-d610';NEW_SYS=OLD_SYS
PARENT_COMMIT='4a1c157ac06d8ae2fbe6795d449b8d8812a3f45c'
def uid(s):
    h=hashlib.sha256(('aoti-092:'+s).encode()).hexdigest()[:16]
    return '-'.join(h[i:i+4] for i in range(0,16,4))
def load(p):return json.loads((UP/p).read_text())
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def append(o,k,x):o.setdefault(k,[]).append(x);return x
def entry(n,key,typ='upgrade'):
    return dict(name=n,id=uid(key),hidden=False,import_=True,type=typ)
def con(key,kind,val,scope='parent',field='selections',children=False):
    return dict(id=uid(key),type=kind,value=val,scope=scope,field=field,shared=True,includeChildSelections=children)
def condition(child,scope='force',kind='atLeast',value=1):
    return dict(childId=child,field='selections',scope=scope,type=kind,value=value,shared=True,includeChildSelections=True)
def mod(field,value,conditions,typ='set'):return dict(field=field,value=value,type=typ,conditions=conditions)
def cost(o,field,value,name=None):append(o,'costs',dict(name=name or {PT:'pts',DP:'Detachment Points',EN:'Enhancements'}.get(field,field),typeId=field,value=value))
def exact(o,n,key,large=None,largeid=None):
    for typ in ['min','max']:
        c=append(o,'constraints',con(key+typ,typ,n))
        if large is not None:append(o,'modifiers',mod(c['id'],large,[condition(largeid,scope=UNIT['id'])]))
def maxn(o,n,key,scope='parent',large=None):
    c=append(o,'constraints',con(key,'max',n,scope))
    if large is not None and LARGE:append(o,'modifiers',mod(c['id'],large,[condition(LARGE,scope=UNIT['id'])]))
    return c
def group(o,n,key,mini=0,maxi=1):
    g=dict(name=n,id=uid(key),hidden=False)
    append(o,'selectionEntryGroups',g)
    if mini==maxi:exact(g,mini,key)
    else:
        append(g,'constraints',con(key+'min','min',mini));append(g,'constraints',con(key+'max','max',maxi))
    return g
G=load('Warhammer 40,000.json')['gameSystem']
BASE=load('Imperium - Agents of the Imperium.json')['catalogue']
C=copy.deepcopy(BASE)
C.update(name='Imperium - Agents of the Imperium (Homebrew v0.9.2)',revision=BASE['revision']+1,gameSystemId=NEW_SYS,selectionEntries=[],entryLinks=[])
C['readme']='Agents of the Imperium v0.9.2 homebrew. See README.md and homebrew/VALIDATION.md. Select Army Roster, Battle Size, Detachments and Force Disposition. Requisitions retain parent datasheets. This is an unofficial playtest catalogue.'
for l in C.get('catalogueLinks',[]):l['importRootEntries']=False
CATS={x['name'].upper():x['id'] for x in G['categoryEntries']+C.get('categoryEntries',[])}
def catid(n):
    if n.upper() not in CATS:
        cid=uid('category:'+n.upper());CATS[n.upper()]=cid;append(C,'categoryEntries',dict(name=n,id=cid,hidden=False))
    return CATS[n.upper()]
def tag(o,n,primary=False):
    cid=catid(n);append(o,'categoryLinks',dict(name=n,id=uid(o['id']+':cat:'+n),targetId=cid,primary=primary,hidden=False));return cid
TYPES={p['name']:p for p in G['profileTypes']}
def profile(n,kind,values,key):
    typ=TYPES[kind];return dict(name=n,id=uid(key),typeId=typ['id'],typeName=kind,hidden=False,characteristics=[dict(name=t['name'],typeId=t['id'],**{'$text':v}) for t,v in zip(typ['characteristicTypes'],values)])
def ability(o,n,t,key=None):append(o,'profiles',profile(n,'Abilities',[t],key or o['id']+n))
def root(o,kind='selectionEntry'):
    append(C,'sharedSelectionEntries',o)
    append(C,'entryLinks',dict(name=o['name'],id=uid('root:'+o['id']),targetId=o['id'],type=kind,hidden=False,import_=True))
DETIDS={d['name']:uid('detachment:'+d['name']) for d in SRC['detachments']}
detconfig=entry('Detachment','detachments-config');tag(detconfig,'Configuration',True);exact(detconfig,1,'detachment-config-limit')
# New Recruit's guided setup recognizes the standard Detachment entry/group names.
dg=group(detconfig,'Detachment','selected-detachments',1,4)
dg['defaultSelectionEntryId']='none'
for d in SRC['detachments']:
    e=entry(d['name'],'detachment:'+d['name']);maxn(e,1,e['id']+'max');cost(e,DP,d['dp'])
    for disp in d['dispositions']:tag(e,disp)
    if d['dp']==3:tag(e,'3DP Detachment')
    if d['ordo']:tag(e,'Unique: ORDO')
    for r in d['rules']:ability(e,r['name'],r['text'])
    for s in d['stratagems']:ability(e,s['name']+' / '+str(s['cost'])+' CP',s['text'])
    append(dg,'selectionEntries',e)
# One Ordo across all selected detachments.
ordo=tag(detconfig,'Unique: ORDO')
detconfig['categoryLinks'][-1]['constraints']=[con('only-one-ordo','max',1,'force',children=True)]
root(detconfig)
ref=entry('Army Rules and References','references');tag(ref,'Reference',True);exact(ref,1,'reference-exact')
for r in SRC['references']:ability(ref,r['name'],r['text'])
root(ref)

# Writ definitions are shared so the once-per-army limit applies across bearers.
WRITS=[]
for w in SRC['universalWrits']:
    e=entry(w['name'],'writ:'+w['name']);maxn(e,1,e['id']+'unique','roster');ability(e,w['name'],w['text']);append(C,'sharedSelectionEntries',e);WRITS.append(e)
for d in SRC['detachments']:
    for w in d['writs']:
        e=entry(w['name'],'writ:'+d['name']+w['name']);maxn(e,1,e['id']+'unique','roster');ability(e,w['name'],str(w['cost'])+' AP. '+w['text']);e['hidden']=True;e['modifiers']=[mod('hidden',False,[condition(DETIDS[d['name']])])];tag(e,d['ordo']);append(C,'sharedSelectionEntries',e);WRITS.append(e)

UNIT=None;LARGE=None;WEAPONS={};USED=set();SOURCE_GAPS=[]
def canon(n):
    n=re.sub(r'\s*\(alternative\)|\s*\(optional\)','',n,flags=re.I)
    n=re.sub(r'\s*(?:- )?(?:standard|supercharge|std|sup|super|scattered|focused|frag|krak|hunter|duelling|decapitation|bolt shells|toxin darts|anointed force sword|Banishing Strike)$','',n,flags=re.I)
    return n.strip().lower()
def weaponmap(u):
    out={}
    for w in u['weapons']:out.setdefault(canon(w['name']),[]).append(w)
    return out
def gear(o,n,key=None,required=True,qty=1,custom=None):
    key=key or o['id']+':gear:'+n
    e=entry(n,key);exact(e,qty if required else 0,key) if required else maxn(e,qty,key+'max')
    specs=custom if custom is not None else WEAPONS.get(canon(n))
    if specs is None:raise ValueError(f'Missing weapon {n!r} in {UNIT["name"]}')
    for i,w in enumerate(specs):append(e,'profiles',profile(w['name'],w['kind'],w['values'],key+':profile'+str(i)))
    append(o,'selectionEntries',e);USED.update((w['name'],w['kind']) for w in specs);return e
def choice(o,label,options,default=None,key=None,mini=1,maxi=1):
    key=key or o['id']+':choice:'+label;g=group(o,label,key,mini,maxi)
    for n in options:
        e=gear(g,n,required=False);maxn(e,1,e['id']+'modelmax')
        if default is None:default=n
        if n==default:g['defaultSelectionEntryId']=e['id']
    return g
def token(o,n,required=False,text=None):
    e=entry(n,o['id']+':token:'+n);append(o,'selectionEntries',e)
    if required:exact(e,1,e['id']+'fixed')
    else:maxn(e,1,e['id']+'max')
    if text:ability(e,n,text)
    return e
def model(parent,n,count=1,big=None,stat=None,key=None):
    e=entry(n,key or UNIT['id']+':model:'+n,'model');exact(e,count,e['id']+':qty',big,LARGE);append(parent,'selectionEntries',e)
    if stat:
        append(e,'profiles',profile(n,'Unit',stat['values'],e['id']+':unitprofile'))
    return e
def pool(parent,n,count,big=None):
    g=group(parent,n,UNIT['id']+':pool:'+n,0,999)
    g['constraints']=[];exact(g,count,g['id']+':count',big,LARGE);return g
def flexiblemodel(parent,n,count,big=None,stat=None):
    e=entry(n,UNIT['id']+':model:'+n,'model');maxn(e,count,e['id']+'max',large=big);append(parent,'selectionEntries',e)
    if stat:append(e,'profiles',profile(n,'Unit',stat['values'],e['id']+':profile'))
    return e
def specialty(g,n,weapons,cap,largecap=None,stat=None):
    m=flexiblemodel(g,n,cap,largecap,stat)
    for w in weapons:gear(m,w)
    return m
def variable_size(u,small,large):
    global LARGE
    g=group(UNIT,'Unit Size',UNIT['id']+':size',1,1)
    for label,diff in [(str(small)+' models',0),(str(large)+' models',u['points'][1]-u['points'][0])]:
        e=entry(label,UNIT['id']+':size:'+label);maxn(e,1,e['id']+'max');cost(e,PT,diff);append(g,'selectionEntries',e)
        if diff==0:g['defaultSelectionEntryId']=e['id']
        else:LARGE=e['id']
def add_unitsize(u):
    sizes={85:(10,20),87:(6,12),89:(5,10),90:(5,10),91:(10,20),93:(5,10),94:(3,6),96:(5,10),98:(6,11),102:(2,4),103:(3,6),105:(5,10),106:(2,4),107:(1,2)}
    if len(u['points'])>1:variable_size(u,*sizes[u['page']])
    if u['page'] in [103,104,105,106,107]:
        # Explicitly retained in the coverage report; these counts are not stated
        # in the consolidated PDF's composition band.
        SOURCE_GAPS.append(dict(unit=u['name'],page=u['page'],issue='Composition omits a complete numeric unit size; builder uses '+str(sizes.get(u['page'],(3,)))+'. Verify against original design.'))

def armoury(u):
    # The armoury is permission-driven, not a list of all weapons on the card.
    by={}
    for w in SRC['armoury']:by.setdefault(canon(w['name']),[]).append(w)
    WEAPONS.update({k:v for k,v in by.items() if k not in WEAPONS})
    bolter=WEAPONS['combi-weapon - bolter']
    for sec in ['Combi-flamer','Combi-plasma','Combi-melta','Combi-grav','Combi-condemnor']:
        found=[w for w in SRC['armoury'] if w['name'].lower().startswith(sec.lower())]
        WEAPONS[canon(sec)]=bolter+found
    pistols=['Bolt pistol','Archeotech pistol','Inferno pistol','Plasma pistol']
    xenos=['Aeldari shuriken catapult','Necron gauss blaster','Xenarch death-arc']
    combis=['Combi-flamer','Combi-plasma','Combi-melta','Combi-grav','Combi-condemnor']
    melee=['Power sword','Power maul','Power fist','Thunder hammer','Null rod','Scythian Venom Talon','Force weapon']
    page=u['page']
    ranged={62:pistols+combis+xenos,63:['Executioner pistol','Plasma pistol']+combis,64:['Combi-bolter']+pistols+combis+xenos,65:['Storm bolter']+combis+['Psycannon'],66:['Combi-bolter']+pistols+combis+xenos}[page]
    me={62:melee,63:['Power sword','Power maul','Force weapon'],64:melee,65:['Power fist','Thunder hammer','Power sword','Force weapon'],66:['Master-crafted power sword','Master-crafted power maul']+melee}[page]
    pg=group(UNIT,'Blessed Wardings or Psychic Gifts',UNIT['id']+':gifts',1,1)
    bw=token(pg,'Blessed Wardings');pg['defaultSelectionEntryId']=bw['id']
    for a in u['abilities']:
        if a['name']=='Blessed Wardings':ability(bw,a['name'],a['text'])
    gifts=token(pg,'Psychic Gifts');gifts_id=gifts['id']
    for a in u['abilities']:
        if a['name'].startswith('Psychic Gifts'):ability(gifts,a['name'],a['text'])
    for r in SRC['references']:
        if r['page'] in [12,13]:ability(gifts,r['name'],r['text'])
    append(UNIT,'modifiers',mod('category',catid('Psyker'),[condition(gifts_id,UNIT['id'])],'add'))
    for label,options in [('Ranged weapon',ranged),('Melee weapon',me)]:
        g=choice(UNIT,label,options)
        for e in g['selectionEntries']:
            if e['name'] in ['Force weapon','Psycannon']:e['hidden']=True;e['modifiers']=[mod('hidden',False,[condition(gifts_id,UNIT['id'])])]
    if page in [62,64,66]:
        g=choice(UNIT,'Psychic ranged attack',['Psychic Shock Wave','Mind Lance'],mini=0)
        g['hidden']=True;g['modifiers']=[mod('hidden',False,[condition(gifts_id,UNIT['id'])])]
    if any(a['name']=='Inquisitorial Writ' for a in u['abilities']):
        wg=group(UNIT,'Inquisitorial Writ',UNIT['id']+':writs',1,1)
        for w in WRITS:append(wg,'entryLinks',dict(name=w['name'],id=uid(wg['id']+w['id']),targetId=w['id'],type='selectionEntry',hidden=False,import_=True))

def equip(u):
    p=u['page'];o=UNIT
    if p in range(62,67):armoury(u);return
    # Each entry in a choice is a physical weapon. Its firing/attack modes
    # remain profiles of that weapon and never become extra weapons.
    chars={67:[['Executioner pistol','Condemnor shotgun'],['Power sword','Power maul']],70:[['Holy shotgun','Ministorum flamer','Plasma pistol'],['Power maul','Power sword']],71:[['Condemnor pistol','Inferno pistol'],['Crozius arcanum']],72:[['Master-crafted bolt pistol','Plasma pistol'],['Judicial power maul']],73:[['Bolt pistol','Plasma pistol'],['Power sword','Power maul']],75:[['Master-crafted executioner pistol','Plasma pistol'],['Power sword','Power maul']],76:[['Household pistol','Volkite serpenta','Disintegration pistol','Xenos duelling pistol'],['Monomolecular cane-rapier','Power sabre','Archeotech duelling blade']],77:[['Naval shock shotgun','Plasma pistol'],['Power cutlass','Shock maul']]}
    # Normalise abbreviated plasma firing modes to a single selectable weapon.
    for k in list(WEAPONS):
        if k.startswith('plasma pistol') and k!='plasma pistol':WEAPONS.setdefault('plasma pistol',[]).extend(WEAPONS.pop(k))
    if p in chars:
        for i,opts in enumerate(chars[p]):choice(o,['Ranged weapon','Melee weapon'][i],opts)
        return
    if p==69:
        g=group(o,'Equipment',o['id']+':equipment',1,1)
        for n,ws in [("Zealot's vindictor",["Zealot's vindictor"]),('Holy pistol and power weapon',['Holy pistol','Power weapon'])]:
            e=token(g,n)
            for w in ws:gear(e,w)
            if n.startswith('Zealot'):g['defaultSelectionEntryId']=e['id']
        return
    if p==74:
        gear(o,'Power maul');g=group(o,'Equipment',o['id']+':equipment',1,1)
        a=token(g,'Combat shotgun');gear(a,'Combat shotgun');g['defaultSelectionEntryId']=a['id']
        b=token(g,'Bolt pistol and assault shield');gear(b,'Bolt pistol');ability(b,'Assault shield','The bearer has a 4+ invulnerable save.');return
    if p<85:
        for n in WEAPONS:gear(o,WEAPONS[n][0]['name'])
        return
    if p==85:
        g=pool(o,'Frateris Militia',10,20)
        m=specialty(g,'Pilgrim', ['Pilgrim firearm','Improvised weapons'],9,19)
        z=specialty(g,'Frateris Zealot',['Pilgrim firearm','Improvised weapons'],1);z['constraints']=[];exact(z,1,z['id']+'fixed')
        specialty(g,'Pilgrim with autopistol and chainblade',['Autopistol','Chainblade'],2,4)
        specialty(g,'Pilgrim with flamer',['Flamer','Improvised weapons'],1,2)
        specialty(g,'Pilgrim with eviscerator',['Pilgrim firearm','Eviscerator'],1,2);return
    if p==86:
        s=model(o,'Navis Sergeant-at-Arms');g=group(s,'Equipment',s['id']+':gear',1,1)
        for n,ws in [('Shotgun and chainsword',['Navis shotgun','Chainsword']),('Bolt pistol and power weapon',['Bolt pistol','Power weapon'])]:
            e=token(g,n)
            for w in ws:gear(e,w)
            if not g.get('defaultSelectionEntryId'):g['defaultSelectionEntryId']=e['id']
        for n,ws in [('Endurant',['Navis heavy shotgun']),('Hatchcutter',['Autopistol','Chainfist']),('Demolition Armsman',['Navis shotgun','Demolition charge']),('Armsman with pistol and power weapon',['Autopistol','Power weapon'])]:
            e=model(o,n)
            for w in ws:gear(e,w)
            if n=='Endurant':ability(e,'Endurant shield','Apply the Endurant shield rule on this unit’s datasheet to this bearer.')
        h=model(o,'Special weapons Armsman');choice(h,'Special weapon',['Navis las-volley','Plasma gun','Meltagun'])
        m=model(o,'Navis Armsman',4);gear(m,'Navis shotgun');return
    if p in [87,88]:
        count,big=(5,10) if p==87 else (2,None)
        g=pool(o,'Agents' if p==87 else 'Handlers',count,big)
        specialty(g,'Agent' if p==87 else 'Handler',['Agent firearm','Agent melee weapon'],count,big)
        if p==87:
            for n,ws in [('Pistolier',['Plasma pistol','Agent melee weapon']),('Questkeeper',['Agent firearm','Eviscerator']),('Mystic',['Agent firearm','Mystic stave']),('Hexorcist',['Condemnor shotgun','Agent melee weapon']),('Death World Veteran',['Agent firearm','Specialist combat blades']),('Autosavant',['Agent firearm','Agent melee weapon'])]:specialty(g,n,ws,1,2)
            ts=token(o,'Tome-skull');ts['constraints']=[];exact(ts,1,ts['id']+'count',2,LARGE)
        m=model(o,'Gun Servitor',1 if p==87 else 3,2 if p==87 else None);choice(m,'Heavy weapon',['Heavy bolter','Multi-melta','Plasma cannon']);return
    if p==89:
        s=model(o,'Storm Trooper Sergeant');choice(s,'Pistol',['Hellpistol','Plasma pistol']);choice(s,'Melee weapon',['Chainsword','Power sword'])
        g=pool(o,'Storm Troopers',4,9)
        m=flexiblemodel(g,'Storm Trooper',4,9);gear(m,'Close combat weapon');primary=choice(m,'Primary weapon',['Hellgun','Hellcarbine'])
        sp=group(primary,'Special weapons',primary['id']+':special',0,1);sp['constraints']=[];maxn(sp,2,sp['id']+'squad',o['id'],4)
        for n in ['Flamer','Grenade launcher','Hot-shot volley gun','Meltagun','Plasma gun']:
            e=gear(sp,n,required=False);maxn(e,1,e['id']+'squad',o['id'],2)
        v=specialty(g,'Vox-caster bearer',['Hellpistol','Close combat weapon'],1);token(v,'Inquisitorial vox-caster',True);return
    if p==90:
        for n,c,b,ws,st in [('Crusader',3,6,['Crusader power sword','Crusader power maul'],u['stats'][0]),('Combat Servitor',2,4,['Servitor breaching drill','Servitor power claws'],u['stats'][1])]:
            m=model(o,n,c,b,st);choice(m,'Melee weapon',ws)
        return
    if p==91:
        g=pool(o,'Penitents',10,20);specialty(g,'Penitent',['Penitent weapons'],10,20)
        sp=group(g,'Punishment weapons',g['id']+':special',0,999);sp['constraints']=[];maxn(sp,2,sp['id']+'max','parent',4)
        specialty(sp,'Penitent with punishment blades',['Punishment blades'],2,4);specialty(sp,'Penitent with heavy eviscerator',['Heavy eviscerator'],2,4);return
    if p==92:
        for n,ws in [('Miraculist',['Holy fire','Burning hands']),('Salvationist',['Close combat weapon']),('Death Cult Assassin',['Death Cult blades']),('Missionary with flamer',['Ministorum flamer','Close combat weapon'])]:
            m=model(o,n)
            for w in ws:gear(m,w)
            if n=='Salvationist':token(m,'Medikit',True);gear(m,'Holy fire',required=False)
        m=model(o,'Missionary with special weapon');choice(m,'Special weapon',['Plasma gun','Meltagun']);gear(m,'Close combat weapon')
        g=pool(o,'Sanctifiers',4);m=flexiblemodel(g,'Sanctifier',4);gear(m,'Ministorum hand flamer');gear(m,'Sanctifier melee weapon');second=gear(m,'Ministorum hand flamer',key=m['id']+':secondflamer',required=False);maxn(second,1,second['id']+'unit',o['id'])
        carrier=specialty(g,'Simulacrum bearer',['Ministorum hand flamer','Sanctifier melee weapon'],1);token(carrier,'Simulacrum',True);token(o,'Cherub',True);return
    if p in [93,94]:
        m=model(o,'Arco-flagellant' if p==93 else 'Death Cult Assassin',5 if p==93 else 3,10 if p==93 else 6);gear(m,'Arco-flails' if p==93 else 'Death Cult blades');return
    if p==95:
        m=model(o,u['name'])
        for n in WEAPONS:gear(m,WEAPONS[n][0]['name'])
        return
    if p==96:
        g=pool(o,'Shrine Guardians',5,10)
        for n,c,b in [('Preceptor',1,None),('Shrine Guardian',4,9)]:
            m=flexiblemodel(g,n,c,b)
            if n=='Preceptor':m['constraints']=[];exact(m,1,m['id']+'fixed')
            gear(m,'Consecrated bolt pistol');token(m,'Storm shield',True);me=choice(m,'Melee weapon',['Sanctified power sword','Relic power maul','Relic thunder hammer']);ham=me['selectionEntries'][-1];maxn(ham,1,ham['id']+'squad',o['id'],2)
        return
    if p in [97,98,99]:
        m=model(o,'Cyber-mastiff');gear(m,'Cyber-mastiff jaws')
        if p==99:
            m=model(o,'Subductor',10);gear(m,'Shock maul');token(m,'Subductor shield',True);return
        c,b=(10,None) if p==97 else (5,10)
        g=pool(o,'Vigilants' if p==97 else 'Exactioners',c,b)
        specialty(g,'Vigilant' if p==97 else 'Exactioner',['Combat shotgun']+(['Arbites combat weapon'] if p==97 else []),c,b)
        for n,w in [('Executioner shotgun bearer','Executioner shotgun'),('Heavy stubber bearer' if p==97 else 'Shock maul bearer','Heavy stubber' if p==97 else 'Shock maul')]:specialty(g,n,[w]+(['Arbites combat weapon'] if p==97 else []),1,2 if p==98 else None)
        if p==97:token(o,'Nuncio-aquila',True)
        if p==98:
            s=token(o,'Third Exaction Squad surcharge');cost(s,PT,10);s['hidden']=True;s['modifiers']=[mod('hidden',False,[condition(o['id'],'roster','atLeast',3)])]
            # Selection-order-independent: exactly one surcharge across three squads.
            maxn(s,1,s['id']+'once','roster');c=append(s,'constraints',con(s['id']+'required','min',0,'roster',children=True));append(s,'modifiers',mod(c['id'],1,[condition(o['id'],'roster','atLeast',3)]))
        return
    if p==100:
        g=pool(o,'Marksmen',5);specialty(g,'Marksman',['Marksman long rifle','Close combat weapon'],5);specialty(g,'Executioner shotgun bearer',['Executioner shotgun','Close combat weapon'],1);return
    if p==101:
        h=model(o,'Arbites Handler',2,stat=u['stats'][0]);gear(h,'Handler combat shotgun');gear(h,'Handler shock baton');m=model(o,'Cyber-mastiff',6,stat=u['stats'][1]);gear(m,'Cyber-mastiff jaws');return
    if p==102:
        m=model(o,'Suppression Automaton',2,4);gear(m,'Concussion cannon');gear(m,'Shock baton');return
    if p==103:
        m=model(o,'Ogryn Boarder',3,6);choice(m,'Ranged weapon',['Boarding shotgun','Grenadier gauntlet']);choice(m,'Melee weapon',['Boarding maul','Breaching hammer']);token(m,'Shield',True);return
    if p==104:
        m=model(o,'Spotter');gear(m,'Boarding shotgun');gear(m,'Close combat weapon');m=model(o,'Gunner',2);choice(m,'Heavy weapon',['Rotor cannon','Naval las-volley','Shipbreaker cannon']);gear(m,'Close combat weapon');return
    if p==105:
        s=model(o,'Sergeant');gear(s,'Void carbine');choice(s,'Melee weapon',['Combat knife','Sergeant power blade']);g=pool(o,'Reconnaissance troopers',4,9);specialty(g,'Voidwalker',['Void carbine','Combat knife'],4,9)
        sp=group(g,'Special weapons',g['id']+':special',0,999);sp['constraints']=[];maxn(sp,1,sp['id']+'max','parent',2)
        specialty(sp,'Micro-melta bearer',['Micro-melta','Combat knife'],1,2);specialty(sp,'Grapnel launcher bearer',['Grapnel launcher','Combat knife'],1,2);return
    if p==106:
        m=model(o,'Shipbreaker Exosuit',2,4);g=choice(m,'Ranged weapon',['Industrial plasma cutter','Heavy rivet cannon','Melta lance']);maxn(g['selectionEntries'][-1],1,m['id']+'meltalimit',o['id'],2);g=choice(m,'Melee weapon',['Hydraulic claw','Siege drill']);maxn(g['selectionEntries'][-1],1,m['id']+'drilllimit',o['id'],2);return
    if p==107:
        m=model(o,'Penitent Engine',1,2);gear(m,'Penitent flamers');g=group(m,'Melee equipment',m['id']+':melee',1,1)
        for n,ws in [('Twin buzz-blades',['Twin buzz-blades']),('Twin flails',['Twin flails']),('Buzz-blade and penitent flail',['Buzz-blade','Penitent flail'])]:
            e=token(g,n)
            for w in ws:gear(e,w)
            if not g.get('defaultSelectionEntryId'):g['defaultSelectionEntryId']=e['id']
        return
    if p==108:choice(o,'Main weapon',['Twin heavy stubber','Twin concussion cannon']);return
    if p==110:
        choice(o,'Turret weapon',['Multi-laser','Heavy bolter','Heavy flamer']);choice(o,'Hull weapon',['Heavy bolter','Heavy flamer']);gear(o,'Lasgun array');gear(o,'Armoured tracks');choice(o,'Pintle weapon',['Heavy stubber','Storm bolter'],mini=0);gear(o,'Hunter-killer missile',required=False);return
    if p==111:gear(o,'Heavy flamer');gear(o,'Storm bolter');gear(o,'Riot cannon',required=False);return
    for n in WEAPONS:gear(o,WEAPONS[n][0]['name'])

def add_retainer(o,u):
    global UNIT,WEAPONS,USED
    saved=(UNIT,WEAPONS,USED);UNIT=o;WEAPONS=weaponmap(u);USED=set()
    r=model(o,u['name'],0,stat=u['stats'][0]);r['constraints']=[];maxn(r,1,r['id']+'once');cost(r,PT,u['points'][0])
    for k in u['keywords']+['Faction: Agents of the Imperium']:tag(r,k)
    for a in u['abilities']:ability(r,a['name'],a['text'])
    alts={118:['Pulse carbine','Rail rifle'],119:['Burst cannon','Fusion blaster'],128:['Galvanic rifle','Radium carbine'],134:['Pyreblaster','Plasma incinerator'],135:['Boltgun','Ministorum flamer']}
    if u['page'] in alts:choice(r,'Ranged weapon',alts[u['page']])
    for n,ws in WEAPONS.items():
        if all((w['name'],w['kind']) in USED for w in ws):continue
        gear(r,ws[0]['name'])
    UNIT,WEAPONS,USED=saved

NATIVE=[]
for u in SRC['units']:
    UNIT=entry(u['name'],'unit:'+u['name'],'model' if (u['page']<85 and u['page']!=76) or u['page']>=108 else 'unit');LARGE=None;WEAPONS=weaponmap(u);USED=set()
    tag(UNIT,u['role'],True)
    for k in u['keywords']:
        if k.upper()!=u['role'].upper():tag(UNIT,k)
    tag(UNIT,'Faction: Agents of the Imperium')
    maxn(UNIT,1 if u['role']=='Epic Hero' or u['page']==76 else 6 if 'BATTLELINE' in u['keywords'] else 3,UNIT['id']+'datasheet-limit','roster')
    cost(UNIT,PT,u['points'][0]);add_unitsize(u)
    if len(u['stats'])==1:append(UNIT,'profiles',profile(u['stats'][0]['name'],'Unit',u['stats'][0]['values'],UNIT['id']+':stats'))
    for a in u['abilities']:
        if u['page'] in range(62,67) and (a['name']=='Blessed Wardings' or a['name'].startswith('Psychic Gifts')):continue
        ability(UNIT,a['name'],a['text'])
    ability(UNIT,'Unit composition and equipment',u['composition'])
    ability(UNIT,'Imperial Authority',next(x['text'] for x in SRC['references'] if x['page']==4))
    if 'CHARACTER' in u['keywords']:
        append(UNIT,'entryLinks',dict(name='Warlord',id=uid(UNIT['id']+'warlord'),targetId='bb9a-14e7-b947-793b',type='selectionEntry',hidden=False,import_=True))
    equip(u)
    if u['page']==76:
        household=group(UNIT,'Household Retainers',UNIT['id']+':household',0,8)
        for r in SRC['retainers']:add_retainer(household,r)
    if 78<=u['page']<=84:
        d=next(d for d in SRC['detachments'] if d['name']=='Veiled Blade Elimination Force')
        package=next(p for p in d['packages'] if p['name'].lower() in u['name'].lower())
        pk=token(UNIT,package['name']+' Temple Package',text=package['text']);cost(pk,PT,package['cost']);pk['hidden']=True;pk['modifiers']=[mod('hidden',False,[condition(DETIDS[d['name']])])]
        ability(UNIT,'Extremis Sanction (Veiled Blade only)',package['text'].split('\n')[0])
        UNIT['profiles'][-1]['hidden']=True;UNIT['profiles'][-1]['modifiers']=[mod('hidden',False,[condition(DETIDS[d['name']])])]
    missing=[w for w in u['weapons'] if (w['name'],w['kind']) not in USED]
    if missing:raise ValueError((u['name'],'unrepresented weapon profiles',[w['name'] for w in missing]))
    NATIVE.append(UNIT);root(UNIT)

# Requisitions and Enhancements are added below before files are written.

# Snapshot parent datasheets with their referenced profiles and wargear. A
# separate library avoids catalogue-import cycles and prevents parent roots
# from becoming native Agents units.
PARENTS={
 'Sororitas':'Imperium - Adepta Sororitas.json',
 'Mechanicus':'Imperium - Adeptus Mechanicus.json',
 'Militarum':'Imperium - Astra Militarum - Library.json',
 'Grey Knights':'Imperium - Grey Knights.json',
 'Astartes':'Imperium - Space Marines.json',
 'Silence':'Imperium - Adeptus Custodes.json',
 'Knights':'Imperium - Imperial Knights - Library.json',
 'Titans':'Library - Titans.json'}
PARENTDATA={f:load(n)['catalogue'] for f,n in PARENTS.items()}
INDEX={};NODE_NAMES={};SYSIDS={x['id'] for x in walk(G) if 'id' in x}
for f in UP.glob('*.json'):
    if f.name=='Warhammer 40,000.json':continue
    original=json.loads(f.read_text())['catalogue']
    for key,arr in original.items():
        if not isinstance(arr,list) or key in ['entryLinks','catalogueLinks']:continue
        for obj in arr:
            if not isinstance(obj,dict):continue
            for node in walk(obj):
                if 'id' in node:INDEX.setdefault(node['id'],(key,obj));NODE_NAMES.setdefault(node['id'],node.get('name',''))
def keywords(o):
    return {l.get('name',NODE_NAMES.get(l.get('targetId'),'' )).upper().replace('FACTION: ','') for l in o.get('categoryLinks',[])}
def isdatasheet(o):return o.get('type') in ['unit','model'] and any(l.get('primary') for l in o.get('categoryLinks',[])) and '[Crucible]' not in o.get('name','')
BASE_ALLOWED={
 'Sororitas':{'Battle Sisters Squad','Dominion Squad','Retributor Squad','Immolator'},
 'Grey Knights':{'Strike Squad','Brotherhood Terminator Squad','Purifier Squad','Nemesis Dreadknight'},
 'Militarum':{'Tempestus Scions','Tempestus Aquilons','Militarum Tempestus Command Squad','Commissar','Taurox Prime','Scout Sentinels','Leman Russ Battle Tank'},
 'Mechanicus':{'Skitarii Rangers','Sicarian Infiltrators','Kataphron Breachers','Servitor Battleclade','Ironstrider Ballistarii','Tech-Priest Enginseer','Tech-Priest Manipulus','Technoarcheologist'},
 'Deathwatch':{'Deathwatch Veterans','Decimus Kill Team','Deathwatch Terminator Squad','Corvus Blackstar'},
 'Astartes':set(),'Silence':set(),'Knights':set(),'Titans':set()}
CHAPTER={'Intercessor Squad','Assault Intercessor Squad','Heavy Intercessor Squad','Scout Squad','Sternguard Veteran Squad','Assault Intercessors with Jump Packs','Vanguard Veterans with Jump Packs','Bladeguard Veteran Squad','Company Heroes','Impulsor','Rhino'}
BONUS={'Sororitas':'Purgation Force','Deathwatch':'Xenocide Force','Grey Knights':'Daemonhunt Force','Militarum':'Requisitioned Battle Group','Mechanicus':'Technological Intervention','Astartes':'Chapter Intervention','Knights':'Oathsworn Lance'}
ALLPARENTS={k:v for k,v in PARENTDATA.items()}
dw=load('Imperium - Deathwatch.json')['catalogue']
ALLPARENTS['Deathwatch']=dw if dw.get('sharedSelectionEntries') else PARENTDATA['Astartes']
SELECTED=[];MISSING_BASE=[]
for faction,pc in ALLPARENTS.items():
    candidates=[x for x in pc.get('sharedSelectionEntries',[]) if isdatasheet(x)]
    for unit in candidates:
        kw=keywords(unit);n=unit['name'];ischar='CHARACTER' in kw;epic='EPIC HERO' in kw
        if faction=='Deathwatch' and not ('DEATHWATCH' in kw or n in BASE_ALLOWED['Deathwatch']):continue
        if faction=='Astartes' and n not in CHAPTER:continue
        if faction=='Silence' and (ischar or not ('ANATHEMA PSYKANA' in kw or n=='Anathema Psykana Rhino')):continue
        expanded=False
        if faction in ['Sororitas','Grey Knights','Deathwatch']:expanded=not ischar
        elif faction=='Militarum':expanded=('TITANIC' not in kw and not ischar) or ('OFFICER' in kw and not epic)
        elif faction=='Mechanicus':expanded=('TITANIC' not in kw and not ischar) or ('TECH-PRIEST' in kw and not epic)
        elif faction=='Astartes':expanded=n in CHAPTER
        elif faction in ['Knights','Silence','Titans']:expanded=True
        basic=n in BASE_ALLOWED[faction]
        if not basic and not expanded:continue
        gates=[] if basic else [condition(DETIDS['Daemonhunt Force' if faction=='Silence' else 'God-Engine Mandate' if faction=='Titans' else BONUS[faction]])]
        SELECTED.append(dict(faction=faction,original=unit,keywords=kw,basic=basic,gates=gates))
    present={x['name'] for x in candidates}
    for n in BASE_ALLOWED[faction]-present:MISSING_BASE.append(dict(faction=faction,unit=n))

R=dict(name='Agents Requisitions Library',id=uid('requisitions-library'),gameSystemId=NEW_SYS,gameSystemRevision=G['revision'],revision=1,battleScribeVersion=2.03,library=True,type='catalogue',xmlns='http://www.battlescribe.net/schema/catalogueSchema')
DEPS={}
for record in SELECTED:DEPS[record['original']['id']]=('sharedSelectionEntries',record['original'])
while True:
    contained={n['id'] for _,o in DEPS.values() for n in walk(o) if 'id' in n}
    needed={n['targetId'] for _,o in DEPS.values() for n in walk(o) if 'targetId' in n}-contained-SYSIDS
    needed|={n['typeId'] for _,o in DEPS.values() for n in walk(o) if 'typeId' in n}-contained-SYSIDS
    additions=[]
    for rid in sorted(needed):
        if rid in INDEX:
            k,obj=INDEX[rid]
            if obj.get('id') not in DEPS:additions.append((obj['id'],k,obj))
    if not additions:break
    for rid,k,o in additions:DEPS[rid]=(k,o)
for _,(key,obj) in DEPS.items():append(R,key,copy.deepcopy(obj))
REMAP={x['id']:uid('requisition:'+x['id']) for x in walk(R) if 'id' in x and x['id'] not in SYSIDS and x['id']!=R['id']}
def rewrite(x,mapping):
    if isinstance(x,dict):return {('import' if k=='import_' else k):rewrite(v,mapping) for k,v in x.items()}
    if isinstance(x,list):return [rewrite(v,mapping) for v in x]
    if isinstance(x,str):return mapping.get(x,x)
    return x
R=rewrite(R,REMAP)
REQIDX={x['id']:x for x in R.get('sharedSelectionEntries',[])}
REMOVED_ARMY_RULES={'Acts of Faith','Doctrina Imperatives','Voice Of Command','Voice of Command','Gate of Infinity','Oath of Moment','Combat Doctrines','Assigned Agents','Code Chivalric','Martial Ka’tah','Martial Ka\'tah','Striding Colossus'}
DROP_OPTIONS={'Enhancements','Crusade','Warlord','Codex Crusade Relics','Codex Battle Traits'}
for obj in list(walk(R)):
    for key in ['entryLinks','infoLinks','profiles','rules']:
        if key in obj:obj[key]=[x for x in obj[key] if x.get('name') not in REMOVED_ARMY_RULES|DROP_OPTIONS]
    if 'costs' in obj:obj['costs']=[x for x in obj['costs'] if x['typeId']==PT]

# Keep the shared allowance and each faction-specific allowance separate.
# Category cost constraints apply to the complete unit, including its gear.
# There can be at most two faction-specific bonus pools in a legal roster
# (one Unique: ORDO plus Oathsworn Lance). The total, single exclusions and
# pair exclusions are the complete set of relevant allocation inequalities.
import itertools
FACTIONS=list(BONUS)
EXCLUSIONS=[()]+[(x,) for x in FACTIONS]+list(itertools.combinations(FACTIONS,2))
BUDGETS=[]
SIZES=[('d62d-db22-4893-4bc0',250),('baf8-997f-e323-a090',500),('4204-82d0-908c-a62a',750)]
for omitted in EXCLUSIONS:
    label='Requisition allowance'+(' excluding '+', '.join(omitted) if omitted else ' (total)')
    cid=catid(label);next(x for x in C['categoryEntries'] if x['id']==cid)['hidden']=True
    BUDGETS.append((set(omitted),label,cid))
    for force in G['forceEntries']:
        if force['name']!='Army Roster':continue
        l=dict(name=label,id=uid('budget-link:'+label),targetId=cid,hidden=True)
        cc=con('budget:'+label,'max',250,'force',PT,True);cc['message']=label+' exceeded ({value} points maximum).';l['constraints']=[cc];l['modifiers']=[]
        for sid,base in SIZES:l['modifiers'].append(mod(cc['id'],base,[condition(sid)]))
        for faction,det in [('any',"The Emperor's Mandate")]+[(f,BONUS[f]) for f in FACTIONS if f not in omitted]:
            for sid,base in SIZES:l['modifiers'].append(mod(cc['id'],base,[condition(sid),condition(DETIDS[det])],'increment'))
        append(force,'categoryLinks',l)
TITAN_CAT=catid('Requisitioned Titan')
for force in G['forceEntries']:
    if force['name']=='Army Roster':append(force,'categoryLinks',dict(name='Requisitioned Titan',id=uid('titan-limit-link'),targetId=TITAN_CAT,hidden=True,constraints=[con('one-requisitioned-titan','max',1,'force',children=True)]))
REQUISITIONS=[];REQMETA=[]
for rec in SELECTED:
    e=REQIDX[REMAP[rec['original']['id']]];f=rec['faction'];kw=rec['keywords'];e['hidden']=False
    e['name']=rec['original']['name']+' (Requisitioned)'
    # Remove parent army composition restrictions at the datasheet root while
    # retaining its weapon, size and points logic.
    e['modifiers']=[m for m in e.get('modifiers',[]) if m.get('field')!='hidden']
    e['modifiers']=[m for m in e['modifiers'] if m.get('field')!='category']
    for mg in e.get('modifierGroups',[]):
        for node in walk(mg):
            if 'modifiers' in node:node['modifiers']=[m for m in node['modifiers'] if m.get('field') not in ['hidden','category']]
    for l in e.get('categoryLinks',[]):l['primary']=False
    tag(e,'Requisitions',True);tag(e,'Requisitioned')
    if f=='Titans':tag(e,'Requisitioned Titan');tag(e,'Adeptus Titanicus')
    else:
        for omitted,label,cid in BUDGETS:
            if f not in omitted:tag(e,label)
    if f in BONUS:
        det=next(d for d in SRC['detachments'] if d['name']==BONUS[f])
        if det['ordo']:append(e,'modifiers',mod('category',catid(det['ordo']),[condition(DETIDS[det['name']])],'add'))
    ability(e,'Separate Command','This is a Requisitioned unit. Use its parent datasheet and published points. It does not gain Agents of the Imperium or parent faction army rules unless an explicit selected Detachment grants access. See Imperial Requisitions. Parent snapshot: JEFFBOBFRANK/wh40k-11e-xverse '+PARENT_COMMIT+'.')
    if f=='Titans':ability(e,'Sanctioned Command','Do not apply Striding Colossus to this Requisitioned model.')
    if f=='Astartes' and rec['original']['name']=='Company Heroes':ability(e,'Company Liaison','An INQUISITOR with Leader can lead this unit and satisfies its CAPTAIN or CHAPTER MASTER requirement.')
    if f=='Astartes' and rec['original']['name']=='Rhino':ability(e,'Company Liaison','This Requisitioned Rhino can transport TACTICUS models; retain all other passenger restrictions and capacity costs.')
    link=dict(name=e['name'],id=uid('root:'+e['id']),targetId=e['id'],type='selectionEntry',hidden=bool(rec['gates']),import_=True)
    if rec['gates']:link['modifiers']=[mod('hidden',False,rec['gates'])]
    append(C,'entryLinks',link);REQUISITIONS.append(e);REQMETA.append((e,kw|{'REQUISITIONED'},f))
append(C,'catalogueLinks',dict(name=R['name'],id=uid('requisitions-import'),targetId=R['id'],type='catalogue',importRootEntries=False))
reqcat=catid('Requisitions')
for force in G['forceEntries']:
    if force['name']=='Army Roster':append(force,'categoryLinks',dict(name='Requisitions',id=uid('requisitions-force-category'),targetId=reqcat,hidden=False))

UPGRADE_MARKERS=[]
def enhancement_eligible(e,kw,f,d,enh):
    first=enh['text'].split('model.')[0].split('unit.')[0]
    if 'EPIC HERO' in kw:return False
    if 'UPGRADE' in enh['text']:
        if 'CHARACTER' in kw:return False
        if 'TRANSPORT' in first:return f is None and 'TRANSPORT' in kw
        if 'INFANTRY' not in kw:return False
        if 'AGENTS OF THE IMPERIUM' in first:return f is None
        names=['INQUISITION','ADEPTUS ARBITES','MINISTORUM','ANATHEMA PSYKANA']
        if any(n in first and n in kw for n in names):return True
        return d['ordo'] and d['ordo'] in first and f in BONUS and BONUS[f]==d['name']
    if 'AGENTS OF THE IMPERIUM CHARACTER' in first and f is None and 'CHARACTER' in kw:
        if 'with an Imperial Sanction' in first:
            return any('IMPERIAL SANCTION' in p['name'] or p['name']=='Inquisitorial Writ' for p in e.get('profiles',[]))
        return True
    if f=='Titans':return 'Requisitioned ADEPTUS TITANICUS' in first
    if f=='Knights':return 'Requisitioned IMPERIAL KNIGHTS CHARACTER' in first and 'CHARACTER' in kw
    if f=='Militarum':return 'Requisitioned ORDO MILITARUM CHARACTER' in first and 'CHARACTER' in kw
    if f=='Mechanicus':return 'Requisitioned ORDO MACHINUM TECH-PRIEST' in first and 'TECH-PRIEST' in kw
    return False
ENH_DEFS=[]
for d in SRC['detachments']:
    for enh in d['enhancements']:
        upgrade='UPGRADE' in enh['text'];e=entry(enh['name'],'enhancement:'+d['name']+enh['name']);e['hidden']=True;e['modifiers']=[mod('hidden',False,[condition(DETIDS[d['name']])])]
        cost(e,PT,enh['cost']);ability(e,enh['name'],enh['text']);maxn(e,3 if upgrade else 1,e['id']+'unique','roster');maxn(e,1,e['id']+'per-bearer')
        if upgrade:
            marker=token(detconfig,'Upgrade selection: '+enh['name']);marker['hidden']=True;marker['modifiers']=[mod('hidden',False,[condition(e['id'],'roster')])];cost(marker,EN,1)
            c=append(marker,'constraints',con(marker['id']+'min','min',0));append(marker,'modifiers',mod(c['id'],1,[condition(e['id'],'roster')]))
            UPGRADE_MARKERS.append(marker)
        else:cost(e,EN,1)
        append(C,'sharedSelectionEntries',e);ENH_DEFS.append((d,enh,e))
for e,kw,f in [(e,set(u['keywords']),None) for e,u in zip(NATIVE,SRC['units'])]+REQMETA:
    eligible=[(d,enh,de) for d,enh,de in ENH_DEFS if enhancement_eligible(e,kw,f,d,enh)]
    if not eligible:continue
    eg=group(e,'Enhancements and Upgrades',e['id']+':enhancements',0,1 if 'CHARACTER' in kw or f=='Titans' else len(eligible))
    for d,enh,de in eligible:append(eg,'entryLinks',dict(name=de['name'],id=uid(eg['id']+de['id']),targetId=de['id'],type='selectionEntry',hidden=False,import_=True))

# Unit keyword changes from Writs are conditional on the selected Writ.
for e,u in zip(NATIVE,SRC['units']):
    if any(a['name']=='Inquisitorial Writ' for a in u['abilities']):
        for d in SRC['detachments']:
            for w in d['writs']:append(e,'modifiers',mod('category',catid(d['ordo']),[condition(uid('writ:'+d['name']+w['name']),e['id'])],'add'))

# Native Leader/Support associations use the printed eligible Bodyguards.
NAMES={u['name']:e['id'] for u,e in zip(SRC['units'],NATIVE)}
for u,e in zip(SRC['units'],NATIVE):
    core=next((a['text'] for a in u['abilities'] if a['name']=='CORE'),'')
    kind='Support' if 'Support' in core else 'Leader' if 'Leader' in core else None
    if not kind:continue
    permitted=[];composition=u['composition'].replace('Storm Troopers','Inquisitorial Storm Troopers')
    text=composition.split(kind+':',1)[-1]
    for n,eid in NAMES.items():
        if n!=u['name'] and n in text:permitted.append(condition(eid,'self','instanceOf'))
    broad=[]
    if 'IMPERIUM BATTLELINE INFANTRY' in text:broad.append(dict(type='and',conditions=[condition(catid(k),'self','instanceOf') for k in ['Imperium','Battleline','Infantry']]))
    if 'qualifying Requisitioned IMPERIUM INFANTRY' in text:
        broad.append(dict(type='and',conditions=[condition(catid(k),'self','instanceOf') for k in ['Requisitioned','Imperium','Infantry']]+[condition(catid(k),'self','notInstanceOf') for k in ['Jump Pack','Jump Packs','Mounted','Fly']]))
    or_group=dict(type='or',conditions=permitted,conditionGroups=broad)
    exclude=[condition(catid(k),'self','notInstanceOf') for k in ['Character','Vehicle','Monster','Suppression Automata']]
    association=dict(name='Supporting' if kind=='Support' else 'Leading',id=uid(e['id']+':association'),action='group',childId='unit',childName='unit',includeChildSelections=True,label=kind,max=1,min=0,scope='force',conditionGroups=[dict(type='and',conditions=exclude,conditionGroups=[or_group])])
    append(e,'associations',association)

# Shared universal rules and faction references follow the tutorial's card
# structure. Bespoke datasheet abilities remain Abilities profiles.
armyrule=dict(name='Imperial Authority',id=uid('imperial-authority-rule'),hidden=False,description=next(r['text'] for r in SRC['references'] if r['page']==4))
append(C,'sharedRules',armyrule)
coreindex={r['name'].lower():r for r in G.get('sharedRules',[])}
for e in NATIVE:
    kept=[]
    for p in e.get('profiles',[]):
        if p['name'] in ['FACTION','Imperial Authority']:continue
        if p['name']=='CORE':
            for text in p['characteristics'][0]['$text'].split(', '):
                key=re.sub(r' \d.*$','',text).lower()
                if key in coreindex:append(e,'infoLinks',dict(name=text,id=uid(e['id']+':core:'+text),targetId=coreindex[key]['id'],type='rule',hidden=False))
            # Preserve printed distances/values and homebrew core abilities.
        kept.append(p)
    e['profiles']=kept
    append(e,'infoLinks',dict(name='Imperial Authority',id=uid(e['id']+':factionrule'),targetId=armyrule['id'],type='rule',hidden=False))

# Preserve the existing fork's system identity and its other homebrew factions.
# Keep only legacy Agents definitions directly used by other factions, plus
# their transitive dependencies. They are library definitions, never roots.
base_index={}
for k,arr in BASE.items():
    if isinstance(arr,list) and k not in ['entryLinks','catalogueLinks','categoryEntries']:
        for o in arr:
            if isinstance(o,dict):
                for n in walk(o):
                    if 'id' in n:base_index[n['id']]=(k,o)
external={'bb9a-14e7-b947-793b'}  # Standard Warlord selection used by native characters.
for f in UP.glob('*.json'):
    if f.name=='Imperium - Agents of the Imperium.json':continue
    for n in walk(json.loads(f.read_text())):
        if n.get('targetId') in base_index:external.add(n['targetId'])
legacy={};pending=list(external)
while pending:
    rid=pending.pop()
    if rid not in base_index:continue
    k,o=base_index[rid]
    if o['id'] in legacy:continue
    legacy[o['id']]=(k,o)
    for n in walk(o):
        for field in ['targetId','typeId']:
            if n.get(field) in base_index:pending.append(n[field])
for k in ['sharedSelectionEntries','sharedSelectionEntryGroups','sharedProfiles','sharedRules','sharedInfoGroups','profileTypes']:
    old={o['id'] for o in BASE.get(k,[]) if isinstance(o,dict) and 'id' in o}
    if k in C:C[k]=[o for o in C[k] if o.get('id') not in old or o.get('id') in legacy]
# All imported-library references must resolve without a back-reference to
# their importing faction. Place shared enhancements and new categories in
# the game system, which every catalogue already imports.
newcats=[x for x in C.get('categoryEntries',[]) if x['id'] not in {z['id'] for z in G['categoryEntries']}]
for x in newcats:append(G,'categoryEntries',x)
C['categoryEntries']=[x for x in C.get('categoryEntries',[]) if x not in newcats]
enhids={x['id'] for _,_,x in ENH_DEFS}
for x in C['sharedSelectionEntries']:
    if x['id'] in enhids:append(G,'sharedSelectionEntries',x)
C['sharedSelectionEntries']=[x for x in C['sharedSelectionEntries'] if x['id'] not in enhids]
# Correct dangling default aliases inherited from parent data without changing
# the permitted choices or costs. A required group remains required.
allids={n['id'] for rootobj in [G,C,R] for n in walk(rootobj) if 'id' in n}
validdefaults=allids|{'none','',None}
DEFAULT_FIXES=[]
for node in walk(R):
    if node.get('defaultSelectionEntryId') not in validdefaults:
        DEFAULT_FIXES.append(node.get('name'));node['defaultSelectionEntryId']='none'
for f in UP.glob('*.json'):
    if f.name in ['Warhammer 40,000.json','Imperium - Agents of the Imperium.json']:continue
    (REPO/f.name).write_bytes(f.read_bytes())
G['id']=NEW_SYS;G['revision']+=1
for node in walk(G):
    if node.get('name')=='3. Onslaught (3000 Point limit)':node['hidden']=False
    if node.get('name')=='Army Roster':node['readme']=node.get('readme','')+'\n\nAgents homebrew v0.9.2: see homebrew/VALIDATION.md for source gaps and validation status.'
for filename,rootkey,obj in [('Warhammer 40,000.json','gameSystem',G),('Imperium - Agents of the Imperium.json','catalogue',C),('Agents Requisitions Library.json','catalogue',R)]:
    (REPO/filename).write_text(json.dumps(rewrite({rootkey:obj},{}),indent=2,ensure_ascii=False)+'\n')
coverage={'source_version':SRC['version'],'upstream':'JEFFBOBFRANK/wh40k-11e-xverse','upstream_commit':PARENT_COMMIT,'native_units':len(NATIVE),'retainers':len(SRC['retainers']),'detachments':len(SRC['detachments']),'enhancements':len(ENH_DEFS),'requisition_datasheets':len(REQUISITIONS),'requisition_budget_constraints':len(BUDGETS),'source_gaps':SOURCE_GAPS,'unmatched_requisition_names':MISSING_BASE,'parent_default_aliases_reset':DEFAULT_FIXES,'native_root_ids':{u['name']:e['id'] for u,e in zip(SRC['units'],NATIVE)},'requisition_units':[dict(name=r['original']['name'],faction=r['faction'],basic=r['basic']) for r in SELECTED]}
(HERE/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
print(json.dumps({k:v for k,v in coverage.items() if k not in ['native_root_ids','requisition_units']},indent=2))
