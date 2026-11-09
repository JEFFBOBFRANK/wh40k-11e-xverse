"""Display and reference metadata for EC v3.1; no roster mechanics are changed."""
import hashlib
import re
from collections import OrderedDict


def uid(text):
    value = hashlib.sha256(('ec-reference-v1:' + text).encode()).hexdigest()[:16]
    return '-'.join(value[i:i + 4] for i in range(0, 16, 4))


def words(text):
    return ' '.join(text.replace('**', '').split())


def tidy(text):
    text = re.sub(r'[ \t]+', ' ', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


# The fixed-width source keeps column boundaries and wrapped cells intact.
# Each tuple identifies a printed table, its last following paragraph, and
# whether the first column contains both an elixir name and a source model.
TABLES = {
    4: [('Battle size', 'Battleline and Dedicated Transport', False)],
    8: [('Eligible model', 'Excluded models', False)],
    11: [('Psyker', 'Current weapon conventions', False)],
    16: [('Initial D3', 'Existing army interactions', False)],
    49: [('Transport', 'Ordinary passengers', False)],
    121: [('Leader', 'Support', False),
          ('Support', 'One eligible Leader', False)],
    122: [('Leader', 'Joint summoning', False)],
    123: [('Elixir / source', 'This table is a reminder.', True)],
    124: [('Elixir / source', 'This table is a reminder.', True)],
    133: [('Trigger / state', 'Record chosen elixirs', False)],
}


def source_table(source, page, first, after, source_column=False):
    lines = source['raw_pages'][str(page)].splitlines()
    start = next(i for i, line in enumerate(lines)
                 if line.startswith(' ') and line.strip().startswith(first)
                 and len(re.split(r'\s{2,}', line.strip())) > 1)
    header = lines[start]
    cells = list(re.finditer(r'\S.*?(?=\s{2,}|$)', header))
    labels = [cell.group().strip() for cell in cells]
    stops = [cell.start() for cell in cells] + [None]
    end = next(i for i in range(start + 1, len(lines))
               if lines[i].strip().startswith(after))
    blocks = re.split(r'\n\s*\n', '\n'.join(lines[start + 1:end]).strip('\n'))
    rows = []
    for block in blocks:
        if not block.strip():
            continue
        columns = []
        for col in range(len(labels)):
            values = [line[stops[col]:stops[col + 1]].strip()
                      for line in block.splitlines()]
            columns.append((' / ' if col == 0 and source_column else ' ').join(
                value for value in values if value))
        assert columns[0], (page, block)
        rows.append(columns)
    return labels, rows


def reference_text(ref, source):
    text = ref['text']
    if ref['page'] == 16 and '**Blood:**' in text:
        return tidy(text)
    for first, after, source_column in TABLES.get(ref['page'], []):
        labels, rows = source_table(source, ref['page'], first, after, source_column)
        flat_header = ' '.join(labels)
        start = text.index(flat_header)
        marker = '**' + after + '**'
        end = text.index(marker if marker in text[start:] else after, start)
        formatted = '\n\n**' + ' — '.join(labels) + '**\n\n'
        formatted += '\n\n'.join(
            '- **' + row[0] + ':** ' + '; '.join(
                ('Normal effect' if label == 'Normal; if Stupefied' else label)
                + ': ' + value for label, value in zip(labels[1:], row[1:]))
            for row in rows)
        text = text[:start] + formatted + '\n\n' + text[end:]
    for label in ['Activate', 'Duration', 'If Stupefied']:
        text = re.sub(r'(?<!\*\*)\b' + label + r':\s*',
                      '\n\n**' + label + ':** ', text)
    return tidy(text)


def clean_datasheet(text, name):
    # Remove page furniture only, never an ability or its wording.
    text = re.sub(r'^' + re.escape(name) + r' / Continued\s*$', '', text, flags=re.M)
    text = re.sub(r'^[A-Z][A-Z /]+ / ABILITIES\s*$', '', text, flags=re.M)
    # This bold line is the first sentence of Ambrosia, not an ability title.
    text = re.sub(r'^\*\*(Once per battle\. Activate.+)\*\*\s*\n\s*',
                  r'\1 ', text, flags=re.M)
    return tidy(text)


def datasheet_sections(unit):
    text = clean_datasheet(unit['rules'], unit['name'])
    result = OrderedDict()
    title = 'Datasheet notes'
    for paragraph in re.split(r'\n\s*\n', text):
        heading = re.fullmatch(r'\*\*(.+?)\*\*', paragraph.strip())
        if heading:
            title = heading[1]
            result.setdefault(title, [])
            continue
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        destination = title
        if paragraph.startswith('Composition:'):
            destination = 'Unit composition and equipment'
        elif paragraph.startswith('Core:'):
            destination = 'CORE'
        elif paragraph.startswith('Army rules:'):
            destination = 'Army rules'
        elif paragraph.startswith(('Keywords:', 'Faction:')):
            destination = 'Printed keywords and notes'
        # Repeated continuation headings (notably Leader) keep all distinct text.
        if paragraph not in result.setdefault(destination, []):
            result[destination].append(paragraph)
    return [(name, '\n\n'.join(paragraphs))
            for name, paragraphs in result.items() if paragraphs]


def matching_rules(text, rules):
    """Match only the supplied core/weapon keyword field, not ability prose."""
    normalized = text.casefold().replace('‑', '-').replace('–', '-')
    result = []
    for rule in rules:
        name = rule['name']
        if name in ['Pistol', 'Crucible', 'Warpstone'] or name.endswith('*'):
            continue
        token = name.casefold()
        ending = r'(?!\w)' if name == 'Anti' else r'(?![\w-])'
        match = re.search(r'(?<![\w-])' + re.escape(token) + ending, normalized)
        if match:
            # Prefer the exact parameterized rule where the system provides one.
            if name in ['Scouts', 'Feel No Pain'] and any(
                    other['name'].startswith(name + ' ') and
                    other['name'].casefold() in normalized and
                    not other['name'].endswith('*') for other in rules):
                continue
            result.append(rule)
    return result


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def add_rule_link(node, rule):
    if any(link.get('targetId') == rule['id'] for link in node.get('infoLinks', [])):
        return False
    node.setdefault('infoLinks', []).append(dict(
        id=uid(node['id'] + ':core-reference:' + rule['id']), name=rule['name'],
        type='rule', targetId=rule['id'], hidden=False))
    return True


def apply_references(catalogue, system, source):
    publication = dict(id=uid('publication:ec3.1'),
                       name="Emperor's Children Homebrew Codex v3.2",
                       shortName='EC Homebrew v3.2', publicationDate='07/11/2026',
                       publisher='Xverse homebrew', hidden=False)
    catalogue.setdefault('publications', []).append(publication)
    reference = next(entry for entry in catalogue['sharedSelectionEntries']
                     if entry['name'] == 'Army Rules and References')
    formatted = {ref['page']: reference_text(ref, source) for ref in source['references']}
    for rule, ref in zip(reference['rules'], source['references']):
        assert rule['name'] == ref['title']
        rule.update(description=formatted[ref['page']],
                    publicationId=publication['id'], page=str(ref['page']))
    army_pages = {'Combat Drugs': [5, 6], 'Bound Excess': [7],
                  'Sublime Strategist': [8], 'Manifestation': [14],
                  'Warband Elixirs': [9, 10], 'Summoning Rituals': [15, 16]}
    for rule in catalogue['sharedRules']:
        if rule['name'] in army_pages:
            pages = army_pages[rule['name']]
            rule.update(description='\n\n'.join(formatted[p] for p in pages),
                        publicationId=publication['id'], page=', '.join(map(str, pages)))
    entries = {entry['name']: entry for entry in catalogue['sharedSelectionEntries']}
    ability_type = next(t for t in system['profileTypes'] if t['name'] == 'Abilities')
    description_type = ability_type['characteristicTypes'][0]
    core_links = weapon_links = ability_count = 0
    for unit in source['units']:
        entry = entries[unit['name']]
        entry.update(publicationId=publication['id'], page=str(unit['page']))
        # Keep the original transcription hidden for source audits and stable IDs.
        original = next(r for r in entry['rules'] if r['name'] == 'Datasheet rules and equipment')
        original.update(hidden=True, publicationId=publication['id'], page=str(unit['page']))
        for name, body in datasheet_sections(unit):
            entry.setdefault('profiles', []).append(dict(
                name=name, id=uid(entry['id'] + ':ability:' + name),
                typeId=ability_type['id'], typeName='Abilities', hidden=False,
                characteristics=[dict(name=description_type['name'],
                    typeId=description_type['id'], **{'$text': body})]))
            ability_count += 1
        core = re.search(r'\bCore:\s*([^.]*)', unit['rules'])
        if core:
            for rule in matching_rules(core[1], system['sharedRules']):
                core_links += add_rule_link(entry, rule)
        for node in walk(entry):
            weapons = [p for p in node.get('profiles', [])
                       if p.get('typeName') in ['Ranged Weapons', 'Melee Weapons']]
            if not weapons:
                continue
            keywords = ', '.join(p['characteristics'][-1]['$text'] for p in weapons)
            for rule in matching_rules(keywords, system['sharedRules']):
                weapon_links += add_rule_link(node, rule)
    from datasheet_format import clean_ec_catalogue
    clean_ec_catalogue(catalogue, system, source)
    from ec_rules_display import apply_rules_display
    apply_rules_display(catalogue, system, source)
    return dict(reference_sections=3, named_ability_profiles=ability_count,
                core_rule_links=core_links, weapon_rule_links=weapon_links,
                source_publication=publication['name'])

