"""Build the EC 4.0 playtest catalogue from the published revision 43.
Pass an explicit revision 43 input and a separate output path.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

from datasheet_format import detachment_point_counter, rule_link, weapon_rules

POINTS = "51b2-306e-1021-d207"
GREATER_DAEMONS = {"Shalaxi Helbane", "Keeper of Secrets", "Vhalyss, the First Scream"}
RETIRED_DETACHMENTS = {
    "Perfumed Procession", "The Perfect Formula", "Rapid Evisceration", "The Veiled Hunt",
    "Cult of Perfect Agony", "The Gilded Retinue", "Kakophonic Conclave",
}
RULES = json.loads(Path(__file__).with_name("ec-4.0-rules.json").read_text())
UNIT_PRICES = {
    "Fulgrim": (485,), "Lucius the Eternal": (190,), "Eidolon": (215,),
    "Ramos": (200,), "Julius Kaesoron": (240,), "Doomrider": (230,),
    "Shalaxi Helbane": (280,), "The Masque of Slaanesh": (85,), "Syll'Esske": (125,),
    "Lord Exultant": (95,), "Lord Kakophonist": (70,), "Raptureweaver": (65,),
    "Torment Oracle": (90,), "Daemon Prince of Slaanesh": (165,),
    "Daemon Prince with Wings": (215,), "Lord Exultant in Terminator Armour": (110,),
    "Idol of Sublime Perfection": (200,), "Chirurgeon": (50,),
    "Lord Exultant with Jump Pack": (90,), "Herald of Excess": (40,),
    "The Gilded Knife": (70,), "Sibyl of Excess": (120,), "Keeper of Secrets": (220,),
    "Tranceweaver": (50,), "Infernal Enrapturess": (60,), "Contorted Epitome": (105,),
    "Infractors": (95, 175), "Tormentors": (85, 170), "Ecstatic Congregation": (50, 90),
    "Fleshbound": (80, 150), "Daemonettes": (70,), "Noise Marines": (175,),
    "Flawless Blades": (95, 190), "Excruciator Terminators": (195,),
    "Phoenix Guard Terminators": (210,), "Dissonant Colossi": (250,), "Ghosts": (85, 160),
    "Chained Thralls": (40, 75), "Rapture Talons": (105, 200),
    "Mirror Guard": (100, 200), "Furies of Slaanesh": (45, 90),
    "Choir of Unmaking": (125,), "Howling Cavaliers": (110, 210), "Stage of Excess": (200,),
    "Chaos Spawn": (75,), "Greater Chaos Spawn": (145,), "Fiends": (80, 160),
    "Chaos Rhino": (70,), "Maulerfiend": (120,), "Defiler": (300,), "Agoniser": (185,),
    "Threnody Dreadnought": (425,), "Cacophant": (190,), "Palatine Ravager": (150,),
    "Dreadclaw": (115,), "Chaos Land Raider": (250,), "Heldrake": (205,),
}


def identifier(key):
    digest = hashlib.sha256(f"ec-4.0:{key}".encode()).hexdigest()[:16]
    return "-".join(digest[i:i + 4] for i in range(0, 16, 4))


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def named(items, name):
    return next(item for item in items if item["name"] == name)


def ability(unit, name, text, previous=None):
    match = next((p for p in unit["profiles"] if p["name"] == (previous or name)), None)
    if match is None:
        assert previous is None, (unit["name"], previous)
        template = next(p for p in unit["profiles"] if p["typeName"] == "Abilities")
        match = copy.deepcopy(template)
        match["id"] = identifier(unit["id"] + ":" + name)
        unit["profiles"].append(match)
    match.update(name=name, hidden=False)
    match["characteristics"][0]["$text"] = text


def remove_profiles(unit, *names):
    unit["profiles"] = [p for p in unit["profiles"] if p["name"] not in names]


def change_profiles(unit, type_names, profile_name=None, **values):
    matches = [
        node for node in walk(unit)
        if node.get("typeName") in type_names
        and (profile_name is None or node["name"].casefold() == profile_name.casefold())
    ]
    assert matches, (unit["name"], profile_name)
    for profile in matches:
        for key, value in values.items():
            named(profile["characteristics"], key)["$text"] = value


def apply_costs(units):
    for name, prices in UNIT_PRICES.items():
        unit = units[name]
        named(unit["costs"], "pts")["value"] = prices[0]
        if len(prices) == 2:
            sizes = named(unit["selectionEntryGroups"], "Unit Size")["selectionEntries"]
            assert len(sizes) == 2, name
            for size, price in zip(sizes, prices):
                named(size["costs"], "pts")["value"] = price - prices[0]
    # Its 4.0 price is a flat 190 plus the three selectable cannon costs.
    cacophant = units["Cacophant"]
    cacophant["modifiers"] = [modifier for modifier in cacophant["modifiers"]
                             if modifier["field"] != POINTS]


def clean_timing(unit):
    for p in unit["profiles"]:
        if p["typeName"] != "Abilities" or p.get("hidden"):
            continue
        characteristic = p["characteristics"][0]
        characteristic["$text"] = re.sub(
            r"\b(start|end) of either(?: player's)? (Fight|Shooting) phase\b",
            r"\1 of the \2 phase", characteristic["$text"],
        )


def apply_native_units(units):
    unit = units["Fulgrim"]
    change_profiles(unit, {"Unit"}, T="11", W="18")
    for mode, keywords in [("strike", "Sustained Hits 1"), ("sweep", "Cleave 2, Sustained Hits 1")]:
        change_profiles(unit, {"Melee Weapons"}, f"Daemonic blades - {mode}", Keywords=keywords)
    ability(unit, "Weapon ability: Daemonic Poisons - Serpentine tail",
            "After resolving attacks with this weapon, each enemy unit that suffered damage from those attacks is Poisoned until the end of the battle round. While a unit is Poisoned, subtract 1 from the Damage characteristic of weapons equipped by its models, to a minimum of 1.")
    ability(unit, "Phoenician Ambrosia",
            "Once per battle, at the start of the Fight phase, this model can use this ability. Until the end of the phase, attacks made with its daemonic blades score Critical Hits on unmodified Hit rolls of 5+. While this model is Stupefied, it can use both blade profiles when it fights. Resolve its Serpentine tail attacks once.",
            previous="Phoenician Ambrosia (Signature Elixir)")
    ability(unit, "Peerless Swordsman",
            "In your opponent's Fight phase, before your opponent selects their first unit to fight in the Fights Remaining step, this model can be selected to fight if it is eligible.")
    ability(unit, "Sovereign of Sensation",
            "While this model is Stupefied, it cannot be Battle-shocked.")
    remove_profiles(unit, "Master of Excess", "Ordinary Doses While Lucid")

    unit = units["Lucius the Eternal"]
    ability(unit, "The Perfect Moment",
            "Once per battle, at the start of the Fight phase, this model can use this ability. Until the end of the phase, its melee weapons have Devastating Wounds.",
            previous="The Perfect Moment (Signature Elixir)")
    eternal = named(unit["profiles"], "The Eternal")["characteristics"][0]
    eternal["$text"] = re.sub(r"\n\n\*\*Combat Elixir\*\*\n\n.*?(?=\n\n\*\*Host destroyed\*\*)",
                               "", eternal["$text"], flags=re.S)
    remove_profiles(unit, "Duellist's Ichor (Signature Elixir)")
    ability(unit, "A Moment of Lucidity",
            "Once per battle, at the start of a phase, this model's unit can ignore the effects of Stupefied until the end of the turn and immediately cease to be Battle-shocked.")

    unit = units["Eidolon"]
    ability(unit, "Kakophonic Fury",
            "While this model is Stupefied, after its unit Piles In and before making melee attacks, this model can shoot its Death Scream at one enemy unit within Engagement Range of its unit. For those attacks, remove Blast, add 2 to its Attacks characteristic and give it Devastating Wounds.",
            previous="Kakophonic Distillate (Signature Elixir)")
    ability(unit, "Lord Commander Primus",
            'Once per battle round, when another friendly Stupefied Emperor\'s Children Infantry unit within 6" of this model declares a charge, that unit can ignore the closest-target restriction from Stupefied and re-roll its Charge roll.')

    ability(units["Ramos"], "Deathless Chorus",
            "While this model leads a Stupefied unit, when it shoots after Advancing or Falling Back, its ranged attacks use their normal Ballistic Skill instead of only hitting on unmodified Hit rolls of 5+.",
            previous="Deathless Chorus (Signature Elixir)")

    unit = units["Julius Kaesoron"]
    change_profiles(unit, {"Melee Weapons"}, "Favoured blade", A="8", WS="2+", S="10",
                    AP="-3", D="4", Keywords="Sustained Hits 1")
    ability(unit, "Gifts of the Favoured Son",
            'At the end of your Command phase, select one other friendly Emperor\'s Children unit within 6" of this model. That unit can become Stupefied or cease to be Stupefied without taking a Leadership test.')
    remove_profiles(units["Doomrider"], "Hunting the Broken")
    remove_profiles(units["Doomrider"], "Revel in Slaughter")

    exultant = units["Lord Exultant"]
    bodyguard = units["Flawless Blades"]
    choices = exultant["associations"][0]["conditionGroups"][0]["conditions"]
    extra_choice = copy.deepcopy(choices[0])
    extra_choice["childId"] = bodyguard["id"]
    choices.append(extra_choice)
    exultant["readme"] = exultant["readme"].replace("Leader: Infractors, Tormentors.",
                                                  "Leader: Infractors, Tormentors, Flawless Blades.")

    ability(units["Raptureweaver"], "Prismatic Nectar",
            'Each time this unit Advances, add 6" to the Move characteristic of its models instead of making an Advance roll.',
            previous="Prismatic Nectar (Signature Elixir)")
    ability(units["Torment Oracle"], "Tyrant's Tears",
            "While this model is Stupefied, add 1 to Wound rolls for attacks made with its Soulspike.",
            previous="Tyrant's Tears (Signature Elixir)")

    change_profiles(units["Daemon Prince of Slaanesh"], {"Unit"}, T="10", W="10", Sv="2+", InSv="4+")
    unit = units["Daemon Prince with Wings"]
    ability(unit, "Gift of Ascension",
            'Once per Charge phase, immediately after a friendly Emperor\'s Children unit within 6" of this model fails a Charge roll, that unit can re-roll that roll.')
    remove_profiles(unit, "Ichor of Ascension (Signature Elixir)")

    unit = units["Lord Exultant in Terminator Armour"]
    ability(unit, "Unbroken Arrogance",
            "Add 1 to Leadership tests taken for this model's unit to cease being Stupefied.")
    ability(unit, "Sovereign Ichor",
            "Add 1 to the Damage characteristic of this model's melee weapons. While this model is Stupefied, those weapons have Cleave 2.",
            previous="Sovereign Ichor (Signature Elixir)")

    unit = units["Idol of Sublime Perfection"]
    ability(unit, "Communion of Excess (Aura)",
            'While a friendly non-Daemon Emperor\'s Children unit is within 6" of this model, add 1 to the Attacks characteristic of melee weapons equipped by models in that unit.',
            previous="Communion of Excess")
    remove_profiles(unit, "Nectar of the Idol (Signature Elixir)", "Bound Daemonic Body")
    fed = named(unit["profiles"], "Fed by Suffering")["characteristics"][0]
    fed["$text"] = fed["$text"].replace("invoked Pain Brings Clarity", "ceased to be Stupefied through Pain Brings Clarity")

    ability(units["Chirurgeon"], "Controlled Overdose",
            "Once per battle round, you can re-roll a Leadership test taken for this model's unit to cease being Stupefied.")
    remove_profiles(units["Lord Exultant with Jump Pack"], "Exultant Dosage")

    unit = units["Herald of Excess"]
    text = named(unit["profiles"], "Procession of Sensation (Aura)")["characteristics"][0]
    text["$text"] = text["$text"].replace("clears Battle-shock from", "ends Stupefied for")

    icon = ('Each time this unit destroys an enemy unit with its attacks, every enemy '
            'unit within 6" of this unit must take a Battle-shock test.')
    for name in ("Infractors", "Tormentors"):
        unit = units[name]
        original = copy.deepcopy(named(unit["profiles"], "Icon of Excess"))
        remove_profiles(unit, "Icon of Excess")
        options = [n for n in walk(unit) if n.get("name") == "Icon of Excess" and n.get("type") == "upgrade"]
        assert len(options) == 2, name
        for option in options:
            profile = copy.deepcopy(original)
            profile["id"] = identifier(option["id"] + ":icon")
            profile["characteristics"][0]["$text"] = icon
            option["profiles"] = [profile]
    change_profiles(units["Infractors"], {"Melee Weapons"}, "Rapture lash",
                    Keywords="Extra Attacks, Precision")

    ability(units["Flawless Blades"], "Mirrorblood Distillate",
            "At the start of the Fight phase, this unit takes a Leadership test. If failed, it suffers D3 mortal wounds. Regardless of the result, until the end of the phase, models in this unit have a 4+ invulnerable save. Each unmodified saving throw of 6 against a melee attack inflicts 1 mortal wound on the attacking enemy unit, to a maximum of 6 mortal wounds per phase.",
            previous="Mirrorblood Distillate (Signature Elixir)")
    unit = units["Phoenix Guard Terminators"]
    change_profiles(unit, {"Melee Weapons"}, "Phoenix power spear",
                    A="5", WS="2+", S="7", AP="-2", D="2", Keywords="Lance, Cleave 2")
    ability(unit, "Aureate Vitae",
            "You can re-roll Charge rolls for this unit. While this unit is Stupefied, it has Fights First.",
            previous="Aureate Vitae (Signature Elixir)")
    retinue = named(unit["profiles"], "Retinue of the Phoenician")["characteristics"][0]
    retinue["$text"] = " ".join(s for s in re.split(r"(?<=\.)\s+", retinue["$text"]) if "elixir" not in s.lower())
    change_profiles(units["Ghosts"], {"Unit"}, M='8"')
    ghost = named(units["Ghosts"]["profiles"], "False Echoes")["characteristics"][0]
    ghost["$text"] = ghost["$text"].removesuffix(" Apply the normal detection rules.")

    unit = units["Rapture Talons"]
    for model in [n for n in walk(unit) if n.get("name") in {"Rapture Talon", "Talon champion"} and n.get("type") == "model"]:
        group = named(model["selectionEntryGroups"], "Sidearm")
        allowed = {"Bolt pistol"} if model["name"] == "Rapture Talon" else {"Screamer pistol", "Plasma pistol"}
        group["selectionEntries"] = [entry for entry in group["selectionEntries"] if entry["name"] in allowed]
        group["defaultSelectionEntryId"] = group["selectionEntries"][0]["id"]
    unit["readme"] = unit["readme"].replace("Each: screamer pistol and Talon blade.",
        "Each Talon: bolt pistol and Talon blade. The champion has a screamer pistol.")
    unit["readme"] = unit["readme"].replace("Any model may replace screamer pistol with bolt pistol. Champion may instead take a plasma pistol",
        "The champion may replace its screamer pistol with a plasma pistol")
    cut = named(unit["profiles"], "Cut and Depart")["characteristics"][0]
    cut["$text"] = cut["$text"].removesuffix(" This is additional to its normal Pile-in and Consolidation.")

    change_profiles(units["Howling Cavaliers"], {"Unit"}, M='12"')
    cavaliers = units["Howling Cavaliers"]
    cavaliers["infoLinks"] = [link for link in cavaliers["infoLinks"] if link["name"] != 'Scouts 6"']
    cavaliers["readme"] = cavaliers["readme"].replace('Core: Scouts 6".\n\n', "")
    ability(units["Stage of Excess"], "Grand Performance",
            'At the start of the Fight phase, select one enemy unit within 12" of this model. That unit must take a Battle-shock test.')
    ability(units["Stage of Excess"], "Encore",
            'Once per battle round, after a friendly Emperor\'s Children unit within 12" of this model destroys an enemy unit, this model can shoot with its grand vox array.')
    for name in ("Chaos Spawn", "Greater Chaos Spawn"):
        ability(units[name], "Unstable Metabolism",
                "While this unit is Stupefied, add 1 to Wound rolls for its melee attacks.")

    unit = units["Agoniser"]
    ability(unit, "Devoted to Destruction",
            "If this model is equipped with two melee weapons in addition to its armoured limbs, add 2 to the Attacks characteristic of those two weapons.",
            previous="Agony Made Manifest")
    ability(unit, "Paired Fists",
            "While this model is equipped with two Helbrute fists, those weapons have Twin-linked.")
    unit["readme"] = unit["readme"].replace("Two fists grant their attacks +2 A and Twin-linked.",
                                            "Two Helbrute fists have Twin-linked.")
    ability(unit, "Sarcophagus Ichor",
            "At the start of the Shooting or Fight phase, this model can use this ability. Until the end of the phase, subtract 1 from the Damage characteristic of attacks that target this model, to a minimum of 1. While this model is Stupefied, after an enemy unit finishes making its attacks against this model, it heals D3 wounds if it survives.",
            previous="Sarcophagus Ichor (Signature Elixir)")
    change_profiles(units["Threnody Dreadnought"], {"Unit"}, M='6"')
    threnody = units["Threnody Dreadnought"]
    ability(threnody, "Interred in Rapture",
            'When this model is set up during deployment, select one objective marker on the battlefield. While this model is within range of that marker, it cannot be Stupefied and its Objective Control characteristic is 10. While it is outside range of that marker, it is Stupefied.')
    remove_profiles(threnody, "This Ground Is My Stage")
    ability(threnody, "Cacophonous Annihilation",
            'While this model is Stupefied, improve the AP of its ranged attacks against enemy units within 12" by 1.')
    ability(units["Cacophant"], "Predatory Crescendo",
            "While this model is Stupefied, when selected to shoot it can overdrive its weapons. Until the end of the phase, its ranged weapons have Hazardous. If it Advanced or Fell Back, its ranged attacks use their normal Ballistic Skill instead of only hitting on unmodified Hit rolls of 5+.")
    heldrake = units["Heldrake"]
    change_profiles(heldrake, {"Unit"}, M='14"', T="10", W="16", Sv="3+", InSv="5+", OC="0")
    change_profiles(heldrake, {"Ranged Weapons"}, "Sonic balespewer", A="6")
    change_profiles(heldrake, {"Melee Weapons"}, "Heldrake claws", AP="-1", D="3")
    ability(heldrake, "Relentless Pursuer",
            "While this model is Stupefied, add 1 to Advance and Charge rolls made for it.")
    for name in ("Maulerfiend", "Defiler", "Cacophant", "Heldrake"):
        ability(units[name], "Exultation in Ruin",
                'After this unit shoots or fights, if its attacks destroyed an enemy unit, select one friendly non-Daemon Emperor\'s Children unit within 6". That unit can resolve Pain Brings Clarity.')


def apply_legions(catalogue, units):
    seeker = units["Seekers"]
    catalogue["sharedSelectionEntries"].remove(seeker)
    catalogue["entryLinks"] = [link for link in catalogue["entryLinks"] if link.get("targetId") != seeker["id"]]
    del units["Seekers"]
    for unit in units.values():
        if not any(link["name"] == "Legions of Excess" for link in unit.get("categoryLinks", [])):
            continue
        maximum = 9 if unit["name"] in GREATER_DAEMONS else 6
        ability(unit, "Manifestation", f"Maximum {maximum} Manifestation points.",
                previous="Summoning and Manifestation")
        unit["infoLinks"] = [link for link in unit["infoLinks"]
                             if link["name"] not in {"Manifestation", "Summoning Rituals"}]
        remove_profiles(unit, "Attached Manifestation")
        unit["selectionEntryGroups"] = [group for group in unit.get("selectionEntryGroups", [])
                                         if group["name"] != "Living Elixir assignment"]
    furies = units["Furies of Slaanesh"]
    value = named(furies["profiles"], "Insignificant Manifestations")["characteristics"][0]
    value["$text"] = value["$text"].split(" Initial D3+1", 1)[0]
    edits = {
        "Fiends": ("Intoxicating Arrival", " Resolve this before Manifestation loss at the end of your Charge phase."),
        "Mirror Guard": ("Through the Looking Glass", " They cannot end overlapping another model's base. All other restrictions on those moves apply."),
        "Choir of Unmaking": ("Unending Refrain (Psychic Level 1)", " Preserving a point does not consume the recipient's point-gain allowance."),
    }
    for name, (profile, suffix) in edits.items():
        value = named(units[name]["profiles"], profile)["characteristics"][0]
        value["$text"] = value["$text"].removesuffix(suffix)
    for name, profile in [
        ("Syll'Esske", "Discordant Union (Psychic Level 2)"),
        ("Keeper of Secrets", "Rapturous Dominion (Psychic Level 3)"),
        ("Vhalyss, the First Scream", "A Symphony Without End"),
    ]:
        value = named(units[name]["profiles"], profile)["characteristics"][0]
        value["$text"] = re.sub(r" and (?:the limit of gaining 1 point per phase|the normal per-phase gain limit)", "", value["$text"])


def apply_army_rules(catalogue, units):
    rules = catalogue["sharedRules"]
    rule = named(rules, "Combat Drugs")
    rule["name"] = "Thrill Seekers"
    obsolete = {named(rules, name)["id"] for name in ("Bound Excess", "Warband Elixirs")}
    for name, description in RULES["armyRules"].items():
        named(rules, name)["description"] = "\n\n" + description
    catalogue["sharedRules"] = [item for item in rules if item["id"] not in obsolete]

    for unit in units.values():
        links = unit.get("infoLinks", [])
        native = any(link["targetId"] in obsolete | {rule["id"]} for link in links)
        unit["infoLinks"] = [link for link in links if link["targetId"] not in obsolete | {rule["id"]}]
        if native:
            rule_link(unit, rule)
            unit["readme"] = re.sub(r"Army rules: (?:Combat Drugs|Bound Excess)",
                                    "Army rules: Thrill Seekers", unit.get("readme", ""))
            unit["readme"] = re.sub(r" (?:Julius|Doomrider|This Prince) does not consume Combat Elixirs or become Stupefied\.", "", unit["readme"])
            unit["readme"] = re.sub(r" This Prince supplies its own elixir to another unit; it does not consume it or become Stupefied\.", "", unit["readme"])
            unit["readme"] = re.sub(r"\n\nBound Daemonic Body:.*?(?=\n\n|\Z)", "", unit["readme"], flags=re.S)
        if "selectionEntryGroups" in unit:
            unit["selectionEntryGroups"] = [
                group for group in unit["selectionEntryGroups"]
                if "elixir" not in group["name"].lower()
            ]
        remove_profiles(unit, "Army Rules")
    refs = named(catalogue["sharedSelectionEntries"], "Army Rules and References")
    refs["infoLinks"] = [link for link in refs["infoLinks"] if link["targetId"] not in obsolete | {rule["id"]}]
    for name in ("Thrill Seekers", "Manifestation", "Summoning Rituals"):
        rule_link(refs, named(catalogue["sharedRules"], name))


def stratagem(catalogue, detachment, name, when, target, effect):
    prefix = f"{detachment} — {name} / "
    rule = next(rule for rule in catalogue["sharedRules"] if rule["name"].startswith(prefix))
    rule["description"] = f"\n\n### When\n\n{when}\n\n### Target\n\n{target}\n\n### Effect\n\n{effect}"


def apply_peerless(catalogue, detachment):
    friendly = "friendly Emperor's Children unit"
    detachment["rules"][0].update(
        name="The Killing Sequence",
        description="\n\nOnce per Fight phase, after a friendly Emperor's Children unit finishes fighting and its melee attacks inflicted damage, select one other friendly Emperor's Children unit within 6\" that is eligible to fight and has not fought this phase. That unit fights immediately.",
    )
    name = detachment["name"]
    stratagem(catalogue, name, "Unerring Lunge",
              f"Your Charge phase, before a {friendly} makes a Charge roll.",
              "That unit.", "Add 2 to that Charge roll.")
    stratagem(catalogue, name, "Faultless Parry",
              "The Fight phase, after an enemy unit selects its targets.",
              f"One {friendly} selected as a target.",
              "Until that enemy unit finishes attacking, subtract 1 from the Damage characteristic of melee attacks that target your unit, to a minimum of 1.")
    stratagem(catalogue, name, "Cut Out the Heart",
              f"The Fight phase, when a {friendly} is selected to fight.",
              "That unit.", "Until the end of the phase, melee weapons equipped by models in your unit have Precision.")
    stratagem(catalogue, name, "Cut Down the Weak",
              "Your opponent's Movement phase, immediately after an enemy unit finishes a Fall Back move.",
              f"One {friendly} within 6\" of that enemy unit that is eligible to charge it.",
              "Your unit can declare a charge that includes that enemy unit as a target.")
    stratagem(catalogue, name, "Exploit the Opening",
              "The Fight phase, when a unit is selected to fight using The Killing Sequence.",
              "That unit.", 'Before it fights, your unit can make an additional Pile-in move of up to 3".')
    stratagem(catalogue, name, "Flawless Execution",
              "The Fight phase, when a unit is selected to fight using The Killing Sequence.",
              "That unit.", "Until the end of the phase, add 1 to the Damage characteristic of melee weapons equipped by models in your unit.")
    entries = catalogue["sharedSelectionEntries"]
    named(entries, "Master of Exquisite Swordsmanship")["rules"][0]["description"] = (
        "Once per battle round, when the bearer's unit is involved in The Killing Sequence, "
        'use 9" instead of 6" for the distance between the two units.'
    )
    named(entries, "Exquisite Balance [Upgrade]")["rules"][0]["description"] = (
        'Infractors, Flawless Blades, Excruciator Terminators or Phoenix Guard Terminators. '
        'Models in this unit can make Pile-in moves of up to 6".'
    )


def gated_link(name, target_id, detachment_id, link_type, owner_id):
    link = {
        "name": name, "id": identifier(owner_id + ":" + target_id),
        "targetId": target_id, "type": link_type, "hidden": True,
        "modifiers": [{"field": "hidden", "value": False, "type": "set", "conditions": [{
            "childId": detachment_id, "field": "selections", "scope": "force",
            "type": "atLeast", "value": 1, "shared": True, "includeChildSelections": True,
        }]}],
    }
    if link_type == "selectionEntry":
        link["import"] = True
    return link


def clone_entry(template, name):
    entry = copy.deepcopy(template)
    entry["name"] = name
    for node in walk(entry):
        if "id" in node:
            node["id"] = identifier(name + ":" + node["id"])
    return entry


def eligible(unit, restriction):
    categories = {link["name"] for link in unit.get("categoryLinks", [])}
    if restriction == "character-or-keeper" and unit["name"] == "Keeper of Secrets":
        return True
    if "Faction: Emperor's Children" not in categories:
        return False
    if restriction == "vehicle":
        return "Vehicle" in categories
    if restriction == "gilded-elite":
        return unit["name"] in {"Flawless Blades", "Dissonant Colossi", "Noise Marines"}
    if restriction == "chirurgeon":
        return unit["name"] == "Chirurgeon"
    if "Character" not in categories or "Epic Hero" in categories:
        return False
    if restriction == "strategist":
        return any(link["name"] == "Sublime Strategist" for link in unit.get("infoLinks", []))
    if restriction == "non-daemon":
        return "Daemon" not in categories
    if restriction == "terminator":
        return "Terminator" in categories
    assert restriction in {"character", "character-or-keeper"}
    return True


def add_enhancement(entries, det, upgrade, template, previous=None, previous_links=None):
    name = upgrade["name"]
    enhancement = previous if previous is not None else clone_entry(template, name)
    named(enhancement["costs"], "pts")["value"] = upgrade["points"]
    enhancement["rules"][0].update(name=name, description=upgrade["text"])
    for unit in entries:
        if eligible(unit, upgrade["eligibility"]):
            options = named(unit["selectionEntryGroups"], "Enhancements and Upgrades")
            key = (options["id"], enhancement["id"])
            link = (previous_links or {}).get(key)
            if link is None:
                link = gated_link(name, enhancement["id"], det["id"], "selectionEntry", options["id"])
            options["entryLinks"].append(link)
    entries.append(enhancement)


def add_stratagem(catalogue, det, strat, refs, previous=None):
    name = f'{det["name"]} — {strat["name"]} / {strat["cp"]} CP'
    rule = previous if previous is not None else {"id": identifier(name), "hidden": False}
    rule["name"] = name
    catalogue["sharedRules"].append(rule)
    stratagem(catalogue, det["name"], strat["name"], strat["when"], strat["target"], strat["effect"])
    refs["infoLinks"].append(gated_link(name, rule["id"], det["id"], "rule", refs["id"]))


def add_detachment_packages(catalogue, system, detachments, theatre, enhancement_template):
    entries = catalogue["sharedSelectionEntries"]
    stratagems = named(entries, "Stratagem References")
    categories = {cat["name"]: cat["id"] for cat in system["categoryEntries"]}
    for package in RULES["detachments"]:
        name = package["name"]
        det = theatre if name == theatre["name"] else clone_entry(theatre, name)
        det["costs"][0]["value"] = package["points"]
        tags = (["3DP Detachment"] if package["points"] == 3 else []) + package["dispositions"]
        det["categoryLinks"] = [
            {"name": tag, "id": identifier(det["id"] + ":" + tag), "targetId": categories[tag],
             "primary": False, "hidden": False} for tag in tags
        ]
        rule = package["rule"]
        det["rules"] = [{"name": rule["name"], "id": identifier(det["id"] + ":rule"),
                         "description": "\n\n" + rule["text"], "hidden": False}]
        if det is not theatre:
            detachments.append(det)

        for upgrade in package["enhancements"]:
            add_enhancement(entries, det, upgrade, enhancement_template)

        for strat in package["stratagems"]:
            add_stratagem(catalogue, det, strat, stratagems)


def replace_detachment_contents(catalogue, detachments, template):
    entries = catalogue["sharedSelectionEntries"]
    refs = named(entries, "Stratagem References")
    for name, changes in RULES["revisions"].items():
        det = named(detachments, name)
        if "rules" in changes:
            previous_rules = {rule["name"]: rule["id"] for rule in det["rules"]}
            det["rules"] = [
                {"name": title, "id": previous_rules.get(title, identifier(det["id"] + ":" + title)),
                 "hidden": False, "description": "\n\n" + description}
                for title, description in changes["rules"].items()
            ]
        if "enhancements" in changes:
            removed = set()
            previous_links = {}
            for unit in entries:
                for group in unit.get("selectionEntryGroups", []):
                    if group["name"] != "Enhancements and Upgrades":
                        continue
                    kept = []
                    for link in group["entryLinks"]:
                        if any(n.get("childId") == det["id"] for n in walk(link)):
                            removed.add(link["targetId"])
                            previous_links[(group["id"], link["targetId"])] = link
                        else:
                            kept.append(link)
                    group["entryLinks"] = kept
            previous = {entry["name"]: entry for entry in entries if entry["id"] in removed}
            entries[:] = [entry for entry in entries if entry["id"] not in removed]
            for upgrade in changes["enhancements"]:
                add_enhancement(entries, det, upgrade, template, previous.get(upgrade["name"]), previous_links)
        if "stratagems" in changes:
            prefix = name + " — "
            previous = {r["name"][len(prefix):].split(" / ")[0]: r
                        for r in catalogue["sharedRules"] if r["name"].startswith(prefix)}
            ids = {rule["id"] for rule in previous.values()}
            catalogue["sharedRules"] = [r for r in catalogue["sharedRules"] if r["id"] not in ids]
            refs["infoLinks"] = [link for link in refs["infoLinks"] if link["targetId"] not in ids]
            for strat in changes["stratagems"]:
                add_stratagem(catalogue, det, strat, refs, previous.get(strat["name"]))


def set_daemon_allowance(catalogue, system, detachments):
    daemon_dets = [named(detachments, name) for name in ("Ritual Host", "Carnival of Excess")]
    category_name = "Unique: DAEMON"
    category_id = identifier(category_name)
    catalogue["categoryEntries"].append({
        "name": category_name, "id": category_id, "hidden": False,
        "constraints": [{"id": identifier(category_name + ":max"), "type": "max", "value": 1,
                         "scope": "roster", "field": "selections", "shared": True,
                         "includeChildSelections": True, "includeChildForces": True}],
    })
    for det, other in (daemon_dets, daemon_dets[::-1]):
        det["categoryLinks"].append({
            "name": category_name, "id": identifier(det["id"] + ":" + category_name),
            "targetId": category_id, "primary": False, "hidden": False,
        })
        det["modifiers"] = [{
            "field": det["constraints"][0]["id"], "type": "set", "value": 0,
            "conditions": [{"childId": other["id"], "field": "selections", "scope": "roster",
                            "type": "atLeast", "value": 1, "shared": True,
                            "includeChildSelections": True, "includeChildForces": True}],
        }]
        det["rules"].append({"name": category_name, "id": identifier(det["id"] + ":unique-daemon"),
                             "hidden": False, "description": "Your army can include one Unique: DAEMON detachment."})
    legions = named(system["categoryEntries"], "Legions of Excess")
    allowance = []
    for modifier in legions["modifiers"]:
        if modifier["type"] != "set":
            continue
        battle_size, gate = modifier["conditions"]
        assert gate["childId"] == daemon_dets[1]["id"]
        for det in daemon_dets:
            allowance.append(dict(modifier, conditions=[battle_size, dict(gate, childId=det["id"])]))
    assert {modifier["value"] for modifier in allowance} == {500, 1000, 1500}
    legions["modifiers"] = allowance


def apply_detachment_changes(catalogue, system):
    entries = catalogue["sharedSelectionEntries"]
    group = named(named(entries, "Detachment")["selectionEntryGroups"], "Detachment")
    theatre = named(group["selectionEntries"], "The Theatre of Excess")
    enhancement_template = named(entries, "The Golden Laurels")
    retired = {det["id"] for det in group["selectionEntries"] if det["name"] in RETIRED_DETACHMENTS}
    group["selectionEntries"] = [det for det in group["selectionEntries"] if det["id"] not in retired]
    removed_rules = {
        rule["id"] for rule in catalogue["sharedRules"]
        if rule["name"].split(" — ", 1)[0] in RETIRED_DETACHMENTS | {theatre["name"]}
    }
    catalogue["sharedRules"] = [rule for rule in catalogue["sharedRules"] if rule["id"] not in removed_rules]
    stratagems = named(entries, "Stratagem References")
    stratagems["infoLinks"] = [link for link in stratagems["infoLinks"] if link["targetId"] not in removed_rules]

    replaced_gates = retired | {theatre["id"]}
    removed_enhancements = set()
    for unit in entries:
        for options in unit.get("selectionEntryGroups", []):
            if options["name"] != "Enhancements and Upgrades":
                continue
            kept = []
            for link in options.get("entryLinks", []):
                if any(node.get("childId") in replaced_gates for node in walk(link)):
                    removed_enhancements.add(link["targetId"])
                else:
                    kept.append(link)
            options["entryLinks"] = kept
    catalogue["sharedSelectionEntries"] = [entry for entry in entries if entry["id"] not in removed_enhancements]
    for link in catalogue["entryLinks"]:
        for node in walk(link):
            if "conditions" in node:
                node["conditions"] = [c for c in node["conditions"] if c.get("childId") not in retired]
    legions = named(system["categoryEntries"], "Legions of Excess")
    legions["modifiers"] = [
        modifier for modifier in legions["modifiers"]
        if all(condition.get("childId") not in retired for condition in modifier.get("conditions", []))
    ]
    add_detachment_packages(catalogue, system, group["selectionEntries"], theatre, enhancement_template)
    detachment_point_counter(catalogue)
    apply_peerless(catalogue, named(group["selectionEntries"], "Peerless Bladesmen"))

    apply_compatibility(catalogue, group["selectionEntries"])
    replace_detachment_contents(catalogue, group["selectionEntries"], enhancement_template)
    set_daemon_allowance(catalogue, system, group["selectionEntries"])


def apply_compatibility(catalogue, detachments):
    entries = catalogue["sharedSelectionEntries"]
    for patch in RULES["compatibility"]["detachmentRules"]:
        det = named(detachments, patch["detachment"])
        rule = named(det["rules"], patch["name"])
        rule["description"] = "\n\n" + patch["text"]
    for patch in RULES["compatibility"]["enhancements"]:
        named(entries, patch["name"])["rules"][0]["description"] = patch["text"]
    for patch in RULES["compatibility"]["stratagems"]:
        stratagem(catalogue, patch["detachment"], patch["name"],
                  patch["when"], patch["target"], patch["effect"])
    dark_apparitions = next(rule for rule in catalogue["sharedRules"]
                            if rule["name"].startswith("Carnival of Excess — Dark Apparitions / "))
    dark_apparitions["name"] = dark_apparitions["name"].replace("/ 2 CP", "/ 1 CP")
    for link in named(entries, "Stratagem References")["infoLinks"]:
        if link["targetId"] == dark_apparitions["id"]:
            link["name"] = dark_apparitions["name"]


def edit_player_text(catalogue, units):
    editorial = RULES["editorial"]
    rule_text = dict(editorial["rules"])
    ability_text = dict(editorial["abilities"])
    for node in walk(catalogue):
        node_id = node.get("id")
        if node_id in rule_text:
            node["description"] = rule_text.pop(node_id)
        if node_id in ability_text:
            node["characteristics"][0]["$text"] = ability_text.pop(node_id)
    assert not rule_text and not ability_text, (rule_text.keys(), ability_text.keys())

    for unit in units.values():
        notes = []
        for paragraph in unit.get("readme", "").split("\n\n"):
            if paragraph.startswith(("Army rules:", "Core:", "Keywords:", "Faction:")):
                continue
            if paragraph.strip() in {"", "VEHICLE / EQUIPMENT AND ABILITIES", "Defiler", "Abilities", "Defiler\nAbilities"}:
                continue
            if paragraph.startswith("Equipment Options:"):
                paragraph = paragraph.removeprefix("Equipment Options: No options. ")
                if paragraph == "Equipment Options: None.":
                    continue
            notes.append(paragraph)
        readme = "\n\n".join(notes)
        for before, after in editorial["noteReplacements"].get(unit["name"], {}).items():
            assert before in readme, (unit["name"], before)
            readme = readme.replace(before, after)
        for redundant in editorial["noteCuts"].get(unit["name"], []):
            assert redundant in readme, (unit["name"], redundant)
            readme = readme.replace(redundant, "")
        readme = re.sub(r"(?<!\n) Equipment: ", "\nEquipment: ", readme)
        unit["readme"] = "\n\n".join(part.strip() for part in readme.split("\n\n") if part.strip())
    named(units["Sibyl of Excess"]["profiles"], "Psyker Level 3")["name"] = "Psyker Level"


def format_leader_and_support(units, system):
    names_by_id = {unit["id"]: unit["name"] for unit in units.values()}
    core = {rule["name"]: rule for rule in system["sharedRules"] if rule["name"] in {"Leader", "Support"}}
    for unit in units.values():
        remove_profiles(unit, "Attachments", "Eligible Attachments")
        for association in unit.get("associations", []):
            label = association.get("label")
            if label not in core:
                continue
            targets = dict.fromkeys(
                names_by_id[condition["childId"]]
                for group in association["conditionGroups"]
                for condition in group["conditions"]
                if condition["type"] == "instanceOf"
            )
            assert targets, unit["name"]
            noun = "unit" if len(targets) == 1 else "units"
            bullets = "\n".join("■ " + name.upper() for name in targets)
            ability(unit, label, f"This model can be attached to the following {noun}:\n\n{bullets}")
            rule_link(unit, core[label])


def migrate(catalogue, system):
    assert catalogue["revision"] == 43
    units = {entry["name"]: entry for entry in catalogue["sharedSelectionEntries"]
             if entry["type"] in {"unit", "model"}}
    apply_costs(units)
    apply_native_units(units)
    change_profiles(units["Lord Exultant with Jump Pack"], {"Melee Weapons"}, "Phoenix power spear", A="5")
    for name in ("Lord Exultant with Jump Pack", "Excruciator Terminators"):
        change_profiles(units[name], {"Melee Weapons"}, "Power fist", S="8")
    apply_legions(catalogue, units)
    apply_army_rules(catalogue, units)
    apply_detachment_changes(catalogue, system)
    for unit in units.values():
        clean_timing(unit)
        remove_profiles(unit, "Elixir Restrictions")
    weapon_rules(units["Infractors"], system)
    edit_player_text(catalogue, units)
    format_leader_and_support(units, system)
    catalogue["revision"] = 52
    system["revision"] += 2
    catalogue["gameSystemRevision"] = system["revision"]
    catalogue["readme"] = "Emperor's Children 4.0 playtest."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--system", type=Path, required=True)
    parser.add_argument("--system-output", type=Path, required=True)
    args = parser.parse_args()
    assert args.baseline.resolve() != args.output.resolve(), "Use a separate output path."
    assert args.system.resolve() != args.system_output.resolve(), "Use a separate system output path."
    data = json.loads(args.baseline.read_text())
    system = json.loads(args.system.read_text())["gameSystem"]
    migrate(data["catalogue"], system)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    args.system_output.write_text(json.dumps({"gameSystem": system}, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
