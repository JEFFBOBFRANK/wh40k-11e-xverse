"""Display-only formatting of PDF reference text; preserve source wording."""
import re

def reference_text(ref):
    name=ref['name']; text=ref['text']
    # Reconstruct tables as short labelled rows for narrow New Recruit panels.
    # Text outside the tables is kept verbatim apart from whitespace.
    if name=='Imperial Requisitions':
        start=text.index('Chamber\nMilitant');end=text.index('Requisitioned identity:')
        text=text[:start]+'''\n\n**Chamber Militant — eligible datasheets**

- **Deathwatch:** Deathwatch Veterans; Decimus Kill Team; Deathwatch Terminators; Corvus Blackstar
- **Grey Knights:** Strike Squad; Brotherhood Terminators; Purifiers; Nemesis Dreadknight
- **Adepta Sororitas:** Battle Sisters; Dominions; Retributors; Immolator

**General Requisitions — eligible datasheets**

- **Astra Militarum:** Tempestus Scions; Tempestus Aquilons; Militarum Tempestus Command Squad; Commissar; Taurox Prime; Scout Sentinels; Leman Russ Battle Tank
- **Adeptus Mechanicus:** Skitarii Rangers; Sicarian Infiltrators; Kataphron Breachers; Servitor Battleclade; Ironstrider Ballistarii; Tech-Priest Enginseer; Tech-Priest Manipulus; Technoarcheologist

'''+text[end:]
    elif name=='Command and Retinue Attachments':
        start=text.index('Permission\n');end=text.index('Model and unit keywords:')
        text=text[:start]+'''\n\n- **Full Inquisitors:** The native units listed on the datasheet; IMPERIUM BATTLELINE INFANTRY; and Requisitioned IMPERIUM INFANTRY. Requisitioned JUMP PACK, JUMP PACKS, MOUNTED and FLY units are excluded.
- **High Interrogator:** Inquisitorial Agents, Inquisitorial Storm Troopers and IMPERIUM BATTLELINE INFANTRY.
- **Inquisitorial Interrogator:** Support: Inquisitorial Agents, Inquisitorial Weapons Cell and IMPERIUM BATTLELINE INFANTRY.
- **Jokaero Weaponsmith:** Support: Inquisitorial Agents or Inquisitorial Weapons Cell.
- **Excluded Bodyguards:** CHARACTER, VEHICLE and MONSTER units; SUPPRESSION AUTOMATA unless expressly permitted.
- **Independent characters:** Kroyle, Karamazov and Ravenor do not have Leader.

'''+text[end:]
    elif name=='Sanctioned Psykana':
        start=text.index('Variant\n');end=text.index('Rex and Ravenor')
        text=text[:start]+'''\n\n**Variant — Psyker Level — Unique Psychic Ability**

- **High Interrogator:** 1 — Psychometric Survey (Level 1)
- **Inquisitor:** 1 — Mental Interrogation (Level 1)
- **Power Armour:** 1 — Psychic Onslaught (Level 1)
- **Terminator Armour:** 1 — Displacement Field (Level 1)
- **Inquisitor Lord:** 2 — Dominion of the Mind (Level 2)

'''+text[end:]
    # PDF line wrapping is not a paragraph boundary.
    text=re.sub(r'(?<!\n)\n(?!\n|\- )',' ',text)
    text=re.sub(r'[ \t]+',' ',text).strip()
    labels=[
        'Imperial Authority','Priority Target','Priority Site','Imperial Sanction','Imperial Strategist',
        'Requisition Allowance','Separate Command','Requisitioned identity',
        'Faction and branch keywords','Weapon conventions','Objective Secured','Mixed-model transports','Psychic abilities',
        'Model and unit keywords','Requisitioned forces','Existing attachments',
        'Rogue Trader household','Active models and granted effects','Keywords and psychic models','Mixed Toughness and capacity','Example',
        'Detachment Points','Unique: ORDO','Ordo Writs','Enhancements and Upgrades','Rules recipients','Additional Requisitions',
    ]
    for label in sorted(labels,key=len,reverse=True):
        text=re.sub(r'(?<!\*\*)'+re.escape(label)+r': ',lambda m:'\n\n**'+label+':** ',text)
    # Expenditures and psychic powers retain their own timing/target/effect text.
    for label in ['Priority Target Elimination - 1 AP','Operational Momentum - 1 AP','Field Protection - 1 AP','Prescience - Psychic Level 1','Psychic Barrier - Psychic Level 1','Mental Interrogation - Level 1 / Inquisitor','Psychometric Survey - Level 1 / High Interrogator','Psychic Onslaught - Level 1 / Power Armour','Displacement Field - Level 1 / Terminator Armour','Dominion of the Mind - Level 2 / Inquisitor Lord']:
        text=text.replace(label+':','\n\n**'+label+':**')
    text=text.replace('IMPERIAL SANCTION / ','\n\nIMPERIAL SANCTION / ')
    text=text.replace('Pay AP each time','\n\nPay AP each time').replace('A Battle-shocked unit cannot initiate','\n\nA Battle-shocked unit cannot initiate').replace('Rex and Ravenor use','\n\nRex and Ravenor use')
    # Do not repeat the section heading at the beginning of its body.
    text=re.sub(r'^\s*\*\*'+re.escape(name)+r':\*\*\s*','',text)
    return re.sub(r'\n{3,}','\n\n',text).strip()
