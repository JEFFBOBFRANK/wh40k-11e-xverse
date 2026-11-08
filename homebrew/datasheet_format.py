"""Keep datasheet abilities separate from core rules and source metadata.

Used by both builders and the one-off catalogue migration. Also repairs Agents model pools and power selections; preserves costs,
weapons, keywords and attachments.
"""
import hashlib
import re


METADATA = {'Unit composition and equipment', 'Printed keywords and notes',
            'Datasheet notes', 'CORE', 'Army rules', 'FACTION'}


def uid(text):
    value = hashlib.sha256(('datasheet-display-v2:' + text).encode()).hexdigest()[:16]
    return '-'.join(value[i:i + 4] for i in range(0, 16, 4))


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def add_ability(entry, system, name, body):
    if not body.strip():
        return
    identifier = uid(entry['id'] + ':ability:' + name)
    if any(p['id'] == identifier for p in entry.get('profiles', [])):
        return
    # Do not repeat a source ability that already has its own profile.
    if any(p.get('typeName') == 'Abilities' and p['name'] == name
           and not p.get('hidden') for p in entry.get('profiles', [])):
        return
    kind = next(t for t in system['profileTypes'] if t['name'] == 'Abilities')
    characteristic = kind['characteristicTypes'][0]
    entry.setdefault('profiles', []).append(dict(
        id=identifier, name=name, typeId=kind['id'], typeName='Abilities',
        hidden=False, characteristics=[dict(name=characteristic['name'],
            typeId=characteristic['id'], **{'$text': body.strip()})]))


def preserve_metadata(entry, text):
    """Composition/equipment remain available in the unit configuration notes."""
    text = text.strip()
    if text and text not in entry.get('readme', ''):
        entry['readme'] = (entry.get('readme', '').rstrip() + '\n\n' + text).strip()


def rule_link(entry, rule, printed=None):
    printed = printed or rule['name']
    links = entry.setdefault('infoLinks', [])
    existing = [link for link in links if link.get('type') == 'rule'
                and link.get('targetId') == rule['id']]
    link = existing[0] if existing else dict(
        id=uid(entry['id'] + ':rule:' + rule['id']), name=rule['name'],
        targetId=rule['id'], type='rule', hidden=False)
    if not existing:
        links.append(link)
    # Match the standard factions: parameter values belong on the rule link.
    if printed != rule['name']:
        modifiers = link.setdefault('modifiers', [])
        modifiers[:] = [m for m in modifiers if m.get('field') != 'name']
        modifiers.append(dict(field='name', type='set', value=printed))
    return link


def core_rules(entry, system, text, custom=None):
    rules = {r['name'].casefold(): r for r in system['sharedRules']}
    rules.update({r['name'].casefold(): r for r in (custom or [])})
    for printed in re.split(r',\s*', text):
        printed = printed.strip()
        if printed in ('None', '-', ''):
            continue
        key = re.sub(r'\s+(?:D\d+|\d+[+\"]?)(?:\b|$).*$', '', printed,
                     flags=re.I).casefold()
        rule = rules.get(printed.casefold()) or rules.get(key)
        if rule:
            # Prefer a canonical parameterized definition if supplied by the system.
            # Remove a duplicate generic link created by an earlier formatter.
            generic = rules.get(key)
            if generic and generic['id'] != rule['id']:
                entry['infoLinks'] = [l for l in entry.get('infoLinks', [])
                                      if l.get('targetId') != generic['id']]
            rule_link(entry, rule, printed)
        elif printed.startswith('Sanctioned Psykana (Psyker Level '):
            rule_link(entry, rules['sanctioned psykana'], printed)
        elif printed == 'Fly':
            # FLY is already a native keyword, not a separate ability.
            continue
        else:
            raise ValueError(('Unrepresented core rule', entry['name'], printed))


def weapon_rules(entry, system):
    from ec_reference_format import matching_rules
    for node in list(walk(entry)):
        weapons = [p for p in node.get('profiles', [])
                   if p.get('typeName') in ('Ranged Weapons', 'Melee Weapons')]
        if not weapons:
            continue
        text = ', '.join(p['characteristics'][-1]['$text'] for p in weapons)
        for rule in matching_rules(text, system['sharedRules']):
            rule_link(node, rule)


def ec_notes(sections):
    """Split gameplay clauses out of the mixed source metadata paragraphs."""
    result = []
    for name, body in sections:
        if name in ('CORE', 'Printed keywords and notes'):
            remaining = re.sub(
                r'(?:Core|Army rules|Keywords|Faction):\s*[^.]*\.', '', body)
            remaining = re.sub(r'Baseline points:[^.]*\.', '', remaining).strip()
            parts = re.split(r'(?=(?:Leader|Psyker Level|Supreme Commander):)', remaining)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                heading, colon, text = part.partition(':')
                result.append((heading if colon else 'Elixir restrictions',
                               text.strip() if colon else part))
        elif name == 'Datasheet notes':
            # Weapon keyword summaries already appear in the weapon table.
            remaining = re.sub(r'[^.]*:\s*(?:\[[^\]]+\](?:,\s*)?)+\.', '', body)
            remaining = re.sub(r'Screamer pistol: Close-Quarters, Blast 1, Ignores Cover\.', '', remaining)
            remaining = re.sub(r'Focused also has \[HAZARDOUS\]\.', '', remaining)
            remaining = re.sub(r'^[A-Z][A-Z /]+ / [A-Z /]+$', '', remaining, flags=re.M)
            remaining = re.sub(r'^.+ / Abilities$', '', remaining, flags=re.M).strip()
            if remaining.startswith('Equipped with a combi-bolter and either '):
                # The existing weapon-choice group enforces this equipment choice.
                remaining = ''
            if remaining:
                result.append(('Weapon selection', remaining))
    return result


def clean_ec_catalogue(catalogue, system, source):
    from ec_reference_format import datasheet_sections
    entries = {e['name']: e for e in catalogue['sharedSelectionEntries']}
    for unit in source['units']:
        entry = entries[unit['name']]
        sections = datasheet_sections(unit)
        for profile in entry.get('profiles', []):
            if profile.get('typeName') == 'Abilities' and profile['name'] in METADATA:
                profile['hidden'] = True
                preserve_metadata(entry, profile['characteristics'][0]['$text'])
        for name, text in ec_notes(sections):
            add_ability(entry, system, name, text)
        core = re.search(r'\bCore:\s*([^.]*)', unit['rules'])
        if core:
            core_rules(entry, system, core[1])
        weapon_rules(entry, system)

    uniform_datasheets(catalogue)


def agent_composition_notes(text):
    """Keep attachment eligibility and genuine restrictions visible on the card.

    Full equipment exchanges and composition stay in configuration notes; the
    actual equipment options remain the existing selectable model/weapon groups.
    """
    result = []
    attachment = re.search(r'\b(Leader|Support):\s*(.*)', text)
    if attachment:
        result.append((attachment[1], attachment[2]))
        text = text[:attachment.start()]
    sentences = re.split(r'(?<=[.;])\s+', text)
    keep = []
    for sentence in sentences:
        if any(fragment in sentence for fragment in (
                'Cannot embark', 'Not a Leader', 'not a Leader', 'no Bodyguard',
                'combined levels of powers', 'shield bearer has',
                'Only one Rogue Trader', 'occupy two transport spaces',
                'Hunter ', 'Hunter can', 'third Exaction Squad',
                'Occupies three transport spaces', 'Excluded from ordinary transports',
                'Each model occupies', 'does not gain Extra Attacks',
                'Select one profile for each weapon',
                'Select one Arias profile')):
            keep.append(sentence)
    if keep:
        result.append(('Datasheet restrictions', ' '.join(keep)))
    return result


def clean_agents_catalogue(catalogue, system, source):
    refs = {r['name']: ' '.join(r['text'].split()) for r in source['references']}
    strategist = refs['Imperial Authority'].split('Imperial Strategist: ', 1)[1]
    psykana = refs['Sanctioned Psykana'].split('Prescience - Psychic Level 1:', 1)[0]
    custom = []
    for name, description in [('Imperial Strategist', strategist),
                              ('Sanctioned Psykana', psykana)]:
        rule = dict(id=uid('agents:' + name), name=name, description=description, hidden=False)
        if not any(r['id'] == rule['id'] for r in catalogue.get('sharedRules', [])):
            catalogue.setdefault('sharedRules', []).append(rule)
        custom.append(rule)
    authority = next(r for r in catalogue['sharedRules'] if r['name'] == 'Imperial Authority')
    entries = {e['name']: e for e in catalogue['sharedSelectionEntries']}
    for unit in source['units']:
        entry = entries[unit['name']]
        for node in list(walk(entry)):
            for profile in node.get('profiles', []):
                if profile.get('typeName') != 'Abilities':
                    continue
                text = profile['characteristics'][0]['$text']
                if profile['name'] == 'CORE':
                    core_rules(node, system, text, custom)
                    profile['hidden'] = True
                elif profile['name'] in ('FACTION', 'Imperial Authority'):
                    profile['hidden'] = True
                    rule_link(node, authority)
                elif profile['name'] == 'Unit composition and equipment':
                    profile['hidden'] = True
                    preserve_metadata(node, text)
        for name, text in agent_composition_notes(unit['composition']):
            add_ability(entry, system, name, text)
        weapon_rules(entry, system)

    uniform_datasheets(catalogue)


def uniform_datasheets(catalogue):
    """Apply consistent display labels/order without changing gameplay text."""
    labels = {
        'Army rules': 'Army Rules',
        'Unit composition and equipment': 'Unit Composition and Equipment',
        'Printed keywords and notes': 'Printed Keywords and Notes',
        'Datasheet notes': 'Datasheet Notes',
        'Equipment options': 'Equipment Options',
        'Eligible attachments': 'Eligible Attachments',
        'Elixir restrictions': 'Elixir Restrictions',
        'Weapon selection': 'Weapon Selection',
        'Datasheet restrictions': 'Datasheet Restrictions',
        'Ordinary doses while lucid': 'Ordinary Doses While Lucid',
        'Attached manifestation': 'Attached Manifestation',
        'Bound daemonic body': 'Bound Daemonic Body',
        'Persistent poison': 'Persistent Poison',
        'Endurant shield': 'Endurant Shield',
    }
    # Include previous labels so rebuilding and cleaning stay idempotent.
    METADATA.update(labels.get(n, n) for n in tuple(METADATA))
    for node in walk(catalogue):
        for profile in node.get('profiles', []):
            if profile.get('typeName') != 'Abilities':
                continue
            name = labels.get(profile['name'], profile['name'])
            name = re.sub(r'^IMPERIAL SANCTION / ', 'Imperial Sanction: ', name)
            name = re.sub(r' - Psychic Level (\d+)$', r' (Psychic Level \1)', name)
            name = re.sub(r' - (\d+) inch Aura$', r' (\1" Aura)', name)
            name = re.sub(r' - Aura$', ' (Aura)', name)
            profile['name'] = name
        # Audited display-only summaries: the underlying rules and equipment
        # remain in their native profiles, references and configuration notes.
        redundant = {'Bound Daemonic Body', 'Armoury', 'Sidearms', 'Equipment'}
        duplicate_restrictions = {'Arbites Proctor', 'Reliquary Procession',
                                  'Voidship Ogryn Boarders'}
        for profile in node.get('profiles', []):
            if profile.get('typeName') != 'Abilities' or profile.get('hidden'):
                continue
            name = profile['name']
            # Agoniser's options paragraph also states a two-fist combat bonus.
            # Preserve that functional rule; ordinary equipment exchanges are
            # already represented by the selectable equipment groups.
            hide = (name in redundant or
                    (name == 'Equipment Options' and node.get('name') != 'Agoniser') or
                    (name == 'Datasheet Restrictions' and
                     node.get('name') in duplicate_restrictions))
            if hide:
                preserve_metadata(node, name + ': ' + profile['characteristics'][0]['$text'])
                profile['hidden'] = True
        # Stable ordering preserves the source order within each section.
        def rank(profile):
            if profile.get('hidden'):
                return 4
            if profile.get('typeName') != 'Abilities':
                return 0
            if profile['name'] in ('Leader', 'Support', 'Attachments', 'Eligible Attachments'):
                return 2
            if profile['name'] in ('Equipment Options', 'Weapon Selection', 'Datasheet Restrictions'):
                return 3
            return 1
        if 'profiles' in node:
            node['profiles'].sort(key=rank)

    if catalogue.get("id") == "b00-cd86-4b4c-97ba":
        repair_agents_structure(catalogue)
        agents_rule_layout(catalogue)
        enforce_agents_writ_limits(catalogue)


def agents_rule_layout(catalogue):
    """Place rule bodies and labelled subparts below their headings."""
    lord = next(e for e in catalogue['sharedSelectionEntries'] if e['name'] == 'Inquisitor Lord')
    for constraint in lord.get('constraints', []):
        if constraint.get('type') == 'max' and constraint.get('scope') == 'roster' and constraint.get('field') == 'selections':
            constraint['value'] = 1
    for profile in lord.get('profiles', []):
        if profile['name'] == 'Inquisitorial Supremacy':
            profile['hidden'] = False
            profile['characteristics'][0]['$text'] = '\n\nYou cannot include more than one INQUISITOR LORD unit in your army.'

    def layout(text):
        text = re.sub(r'(?m)^-[ \t]*\n+', '\n\n', text)
        text = re.sub(r'\s*\*\*([^*\n]+:)\*\*[ \t\n]*',
                      lambda m: '\n\n**' + m[1] + '**\n\n', text)
        text = re.sub(r'(?<![\w*])(WHEN|TARGET|EFFECT|RESTRICTION|REQUIREMENT|DURATION|COST|LIMIT):[ \t\n]*',
                      lambda m: '\n\n**' + m[1] + ':**\n\n', text, flags=re.I)
        text = re.sub(r'[ \t]+(?=\n)', '', text)
        text = re.sub(r'(?m)^([A-Z][A-Za-z0-9 /()’"+\-]{0,65}:)[ \t]+',
                      lambda m: m[1] + '\n\n', text)
        return '\n\n' + re.sub(r'\n{3,}', '\n\n', text.strip())
    for node in walk(catalogue):
        if node.get('hidden'):
            continue
        if 'description' in node:
            node['description'] = layout(node['description'])
        if node.get('typeName') == 'Abilities':
            for characteristic in node.get('characteristics', []):
                if characteristic.get('name') == 'Description':
                    characteristic['$text'] = layout(characteristic['$text'])


def enforce_agents_writ_limits(catalogue):
    writ_ids = set()
    for entry in catalogue['sharedSelectionEntries']:
        for group in entry.get('selectionEntryGroups', []):
            if group['name'] != 'Inquisitorial Writ':
                continue
            for constraint in group.get('constraints', []):
                if constraint.get('field') == 'selections':
                    constraint['value'] = 1
                    constraint['includeChildSelections'] = True
            for link in group.get('entryLinks', []):
                writ_ids.add(link['targetId'])
                constraints = link.setdefault('constraints', [])
                if not any(c.get('type') == 'max' and c.get('scope') == 'parent' for c in constraints):
                    constraints.append(dict(id=uid(link['id']+':writ-local-max'),type='max',value=1,scope='parent',field='selections',shared=True,includeChildSelections=True))
    for entry in catalogue['sharedSelectionEntries']:
        if entry['id'] in writ_ids:
            for constraint in entry.get('constraints', []):
                if constraint.get('type') == 'max' and constraint.get('scope') == 'roster':
                    constraint['value'] = 1
                    constraint['includeChildSelections'] = True


def repair_agents_structure(catalogue):
    import copy
    entries={e['name']:e for e in catalogue['sharedSelectionEntries']}
    def value(node,kind):
        return next((c['value'] for c in node.get('constraints',[]) if c.get('field')=='selections' and c['type']==kind),0)
    # Model pools open with the complete basic squad; specialists replace basics.
    for entry in entries.values():
        if entry.get('type') not in ['model','unit']:continue
        for group in list(walk(entry)):
            models=[n for n in group.get('selectionEntries',[]) if n.get('type')=='model']
            if group.get('type')=='model' or not models or not value(group,'min'):continue
            flexible=[m for m in models if any(c['id']==uid(m['id']+':basic-min') for c in m.get('constraints',[]))] or [m for m in models if not value(m,'min')]
            if not flexible:continue
            regular=max(flexible,key=lambda m:value(m,'max'))
            if value(regular,'max')<value(group,'min')-sum(value(m,'min') for m in models):continue
            needed=value(group,'min')-sum(value(m,'min') for m in models if m is not regular)
            minimum=next((c for c in regular.get('constraints',[]) if c['type']=='min'),None)
            if minimum is None:
                minimum=dict(id=uid(regular['id']+':basic-min'),type='min',scope='parent',field='selections',value=needed,shared=True,includeChildSelections=False)
                regular.setdefault('constraints',[]).append(minimum)
            regular['defaultAmount']=needed
            maximum=next(c for c in regular['constraints'] if c['type']=='max')
            for modifier in list(regular.get('modifiers',[])):
                if modifier.get('field')==maximum['id'] and modifier.get('type')=='set':
                    clone=copy.deepcopy(modifier);clone['field']=minimum['id']
                    if clone not in regular['modifiers']:regular['modifiers'].append(clone)
            # Include specialist models in nested replacement subgroups too.
            replacements=[n for n in walk(group) if n.get('type')=='model' and n is not regular and not value(n,'min')]
            for specialist in replacements:
                for constraint in [minimum,maximum]:
                    modifier=dict(field=constraint['id'],type='increment',value=-1,repeats=[dict(childId=specialist['id'],field='selections',scope=entry['id'],shared=True,includeChildSelections=True,value=1,repeats=1,roundUp=False)])
                    if modifier not in regular.setdefault('modifiers',[]):regular['modifiers'].append(modifier)
        for node in list(walk(entry)):
            if node.get('type')=='model':node.setdefault('defaultAmount',value(node,'min'))
        # Guard/EC-style physical models each carry their own stat profile.
        if entry.get('type')!='unit' or entry['name']=='Rogue Trader':continue
        models=[n for n in walk(entry) if n is not entry and n.get('type')=='model']
        stats=next((p for p in entry.get('profiles',[]) if p.get('typeName')=='Unit'),None)
        if not models or stats is None:continue
        for model in models:
            if not any(p.get('typeName')=='Unit' for p in model.get('profiles',[])):
                profile=copy.deepcopy(stats);profile.update(id=uid(model['id']+':stats'),name=stats['name'],hidden=False)
                model.setdefault('profiles',[]).insert(0,profile)
            if entry['name']=='Imperial Navy Breachers' and model['name']=='Endurant':
                for profile in model['profiles']:
                    if profile.get('typeName')=='Unit':
                        profile['name']='Endurant';next(c for c in profile['characteristics'] if c['name']=='InSv')['$text']='4+'
                for profile in model['profiles']:
                    if profile.get('typeName')=='Abilities' and 'Apply the Endurant shield rule' in profile['characteristics'][0]['$text']:profile['hidden']=True
        stats['hidden']=True
    # Count the Rogue Trader as a physical model alongside household retainers.
    trader=entries['Rogue Trader']
    captain_id=uid(trader['id']+':captain-model')
    if not any(n.get('id')==captain_id for n in trader.get('selectionEntries',[])):
        stats=next(p for p in trader['profiles'] if p['typeName']=='Unit')
        profile=copy.deepcopy(stats);profile.update(id=uid(captain_id+':stats'),hidden=False)
        captain=dict(id=captain_id,name='Rogue Trader',type='model',hidden=False,import_=True,defaultAmount=1,
            profiles=[profile],constraints=[dict(id=uid(captain_id+':'+kind),type=kind,value=1,scope='parent',field='selections',shared=True,includeChildSelections=False) for kind in ['min','max']])
        captain['import']=captain.pop('import_')
        captain['selectionEntryGroups']=[g for g in trader['selectionEntryGroups'] if g['name'] in ['Ranged weapon','Melee weapon']]
        trader['selectionEntryGroups']=[g for g in trader['selectionEntryGroups'] if g['name'] not in ['Ranged weapon','Melee weapon']]
        trader.setdefault('selectionEntries',[]).insert(0,captain);stats['hidden']=True
    # Restore the Jokaero's three printed choices lost during text extraction.
    jokaero=entries['Jokaero Weaponsmith']
    ability=next(p for p in jokaero['profiles'] if p['name']=='Inconceivable Augmentation')
    ability['characteristics'][0]['$text']='At the start of your Command phase, select one augmentation below. Until the start of your next Command phase, ranged weapons equipped by models in this unit gain its benefit.\n\n**Weapon Calibration:**\n\nAdd 6" to the Range characteristic.\n\n**Lethal Augmentation:**\n\nThose weapons have Lethal Hits: MONSTER/VEHICLE.\n\n**Armour Disruption:**\n\nImprove the Armour Penetration characteristic by 1.'
    for p in jokaero['profiles']:
        if p['name'].startswith('Lethal Augmentation Those'):p['hidden']=True
    for link in jokaero.get('entryLinks',[]):
        if link['name']=='Warlord':
            link['hidden']=True
            if not any(c['type']=='max' and c['value']==0 for c in link.get('constraints',[])):
                link.setdefault('constraints',[]).append(dict(id=uid(link['id']+':not-warlord'),type='max',value=0,scope='parent',field='selections',shared=True,includeChildSelections=False))
    # Psychic Gifts show only the chosen variant's actual powers, not two chapters.
    variants={'Inquisitor':'Mental Interrogation','High Interrogator':'Psychometric Survey','Inquisitor in Power Armour':'Psychic Onslaught','Inquisitor in Terminator Armour':'Displacement Field','Inquisitor Lord':'Dominion of the Mind'}
    psykana=next(r for r in catalogue['sharedRules'] if r['name']=='Sanctioned Psykana')
    for name,power in variants.items():
        entry=entries[name]
        gifts=next(n for n in walk(entry) if n.get('type')=='upgrade' and n['name']=='Psychic Gifts')
        if any(p['name']==power+' (Psychic Level '+('2' if name=='Inquisitor Lord' else '1')+')' for p in gifts.get('profiles',[])):continue
        common=next(p for p in gifts['profiles'] if p['name']=='Sanctioned Psykana')
        unique=next(p for p in gifts['profiles'] if p['name']=='Psychic Gifts')
        text=' '.join(common['characteristics'][0]['$text'].split())
        prescience=text.split('Prescience - Psychic Level 1:',1)[1].split('Psychic Barrier - Psychic Level 1:',1)[0]
        barrier=text.split('Psychic Barrier - Psychic Level 1:',1)[1].split('Variant',1)[0]
        text=' '.join(unique['characteristics'][0]['$text'].split())
        import re
        matches=list(re.finditer(r'(Mental Interrogation|Psychometric Survey|Psychic Onslaught|Displacement Field|Dominion of the Mind) - Level (\d) / [^:]+:',text))
        match=next(m for m in matches if m[1]==power);i=matches.index(match);body=text[match.end():matches[i+1].start() if i+1<len(matches) else len(text)]
        for profile in gifts['profiles']:profile['hidden']=True
        for title,description in [('Prescience (Psychic Level 1)',prescience),('Psychic Barrier (Psychic Level 1)',barrier),(power+' (Psychic Level '+match[2]+')',body)]:
            profile=copy.deepcopy(common);profile.update(id=uid(gifts['id']+':'+title),name=title,hidden=False);profile['characteristics'][0]['$text']=description.strip();gifts['profiles'].append(profile)
        rule_link(gifts,psykana,'Sanctioned Psykana (Psyker Level '+('2' if name=='Inquisitor Lord' else '1')+')')
        for profile in entry['profiles']:
            if profile['name']=='Blessed Wardings / Psychic Gifts':profile['hidden']=True
    vindicare=entries['Vindicare Assassin']
    ammunition=next(p for p in vindicare['profiles'] if p['name']=='Exitus Ammunition')
    choices=[p for p in vindicare['profiles'] if p['name'] in ['Turbo-penetrator','Hellfire','Shieldbreaker']]
    if '**Turbo-penetrator:**' not in ammunition['characteristics'][0]['$text']:
        for p in choices:
            ammunition['characteristics'][0]['$text']+='\n\n**'+p['name']+':**\n\n'+p['characteristics'][0]['$text'].strip()
            p['hidden']=True
