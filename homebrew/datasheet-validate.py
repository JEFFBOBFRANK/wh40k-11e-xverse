"""Verify display cleanup against the previous published catalogues."""
import argparse
import copy
import json
from pathlib import Path
from datasheet_format import (METADATA, clean_agents_catalogue,
                              clean_ec_catalogue, walk)

p=argparse.ArgumentParser()
p.add_argument('--data',type=Path,required=True)
p.add_argument('--previous',type=Path,required=True)
a=p.parse_args()
system=json.loads((a.previous/'Warhammer 40,000.json').read_text())['gameSystem']

def mechanics(node):
    if isinstance(node,dict):
        return {k:mechanics(v) for k,v in node.items()
                if k not in {'profiles','rules','sharedRules','infoLinks','revision','readme'}}
    if isinstance(node,list):return [mechanics(v) for v in node]
    return node

reports=[]
for filename,source_name,cleaner in [
        ("Chaos - Emperor's Children.json",'ec-source-data.json',clean_ec_catalogue),
        ('Imperium - Agents of the Imperium.json','source-data.json',clean_agents_catalogue)]:
    old=json.loads((a.previous/filename).read_text())['catalogue']
    new=json.loads((a.data/filename).read_text())['catalogue']
    source=json.loads((a.data/'homebrew'/source_name).read_text())
    assert mechanics(old)==mechanics(new),(filename,'roster mechanics changed')
    index={n['id']:n for n in walk(new) if 'id' in n}
    assert len(index)==len([n for n in walk(new) if 'id' in n]),'Duplicate IDs'
    original_profiles=0
    hidden_metadata=0
    for node in walk(old):
        for profile in node.get('profiles',[]):
            shown=index[profile['id']]
            expected=copy.deepcopy(profile)
            if profile.get('typeName')=='Abilities' and profile['name'] in METADATA:
                # Only native datasheet metadata was touched; imported legacy
                # profiles may legitimately retain their original visibility.
                if shown.get('hidden') is True:
                    expected['hidden']=True
                    hidden_metadata+=not profile.get('hidden',False)
            assert shown==expected,(filename,profile['name'],'original profile changed')
            original_profiles+=1
    entries={e['name']:e for e in new['sharedSelectionEntries']}
    for unit in source['units']:
        entry=entries[unit['name']]
        assert not [x for x in entry.get('profiles',[])
                    if x.get('typeName')=='Abilities' and x['name'] in METADATA
                    and not x.get('hidden')],unit['name']
        if 'composition' in unit:
            assert unit['composition'] in entry.get('readme',''),unit['name']
    # Running either builder's display pass twice must not duplicate anything.
    again=copy.deepcopy(new)
    cleaner(again,system,source)
    assert again==new,(filename,'formatter is not idempotent')
    reports.append(dict(catalogue=new['name'],revision=new['revision'],
                        units=len(source['units']),original_profiles_preserved=original_profiles,
                        duplicate_metadata_rows_hidden=hidden_metadata,
                        roster_mechanics_unchanged=True,idempotent=True))

ec=json.loads((a.data/"Chaos - Emperor's Children.json").read_text())['catalogue']
fulgrim=next(x for x in ec['sharedSelectionEntries'] if x['name']=='Fulgrim')
visible=[x['name'] for x in fulgrim['profiles']
         if x.get('typeName')=='Abilities' and not x.get('hidden')]
assert 'Supreme Commander' in visible
assert {'Master of Excess','Sovereign of Sensation','Ordinary doses while lucid'}<=set(visible)
assert any(m.get('value')=='Deadly Demise D6' for l in fulgrim['infoLinks']
           for m in l.get('modifiers',[]))
report=dict(status='PASS',catalogues=reports,fulgrim_visible_abilities=visible)
(a.data/'homebrew/datasheet-validation-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
