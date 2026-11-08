"""Keep datasheet abilities separate from core rules and source metadata.

Used by both builders and the one-off catalogue migration. Does not alter
selections, costs, weapons, keywords, attachments or roster constraints.
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
