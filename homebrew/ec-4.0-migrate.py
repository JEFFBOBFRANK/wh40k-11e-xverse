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
REQUISITION_THRESHOLDS = {
    "Defiler": (2, 50),
    "Threnody Dreadnought": (2, 50),
    "Stage of Excess": (2, 25),
    "Cacophant": (3, 25),
    "Palatine Ravager": (3, 20),
    "Idol of Sublime Perfection": (3, 25),
    "Maulerfiend": (3, 15),
}
ENHANCEMENT_PRICES = {
    "Master of Exquisite Swordsmanship": 15,
    "Sceptre of Edicts": 15,
    "Silken Escape": 15,
    "Glassed Veins": 10,
    "Rapturous Applause": 10,
    "A Thousand Promises": 15,
    "Bloodless Elegance": 10,
}
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
    "Chained Thralls": (30, 60), "Rapture Talons": (105, 200),
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
    change_profiles(units["Chained Thralls"], {"Unit"}, InSv="6+")

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
            "While this model leads a Stupefied unit, that unit is eligible to shoot after Advancing or Falling Back.",
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
            "While this model is Stupefied, it can overdrive its weapons when selected to shoot. It is eligible to shoot after Advancing or Falling Back if it overdrives its weapons. Until the end of the phase, its ranged weapons have Hazardous.")
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
    rule["name"] = "The Pursuit of Perfection"
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
                                    "Army rules: The Pursuit of Perfection", unit.get("readme", ""))
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
    for name in ("The Pursuit of Perfection", "Manifestation", "Summoning Rituals"):
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
            if label == "Support":
                association["defaultSelectionEntryId"] = "none"
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


def apply_requisition_thresholds(units):
    template = copy.deepcopy(next(
        modifier for modifier in units["Defiler"]["modifiers"]
        if modifier["field"] == POINTS and modifier["type"] == "increment"
    ))
    for name, (first_charged_copy, surcharge) in REQUISITION_THRESHOLDS.items():
        unit = units[name]
        modifier = copy.deepcopy(template)
        modifier["value"] = surcharge
        preceding_copies = modifier["conditionGroups"][0]["localConditionGroups"][0]
        preceding_copies["value"] = first_charged_copy - 1
        selector = next(c for c in preceding_copies["conditions"] if c["type"] == "instanceOf")
        selector.update(childId=unit["id"], childName=name)
        unit["modifiers"] = [
            existing for existing in unit["modifiers"]
            if existing["field"] != POINTS or existing["type"] != "increment"
        ]
        unit["modifiers"].append(modifier)


def apply_revision_57(catalogue):
    entries = catalogue["sharedSelectionEntries"]
    units = {entry["name"]: entry for entry in entries if entry["type"] in {"unit", "model"}}
    apply_requisition_thresholds(units)
    for name, price in ENHANCEMENT_PRICES.items():
        named(named(entries, name)["costs"], "pts")["value"] = price
    glassed_veins = named(named(entries, "Glassed Veins")["rules"], "Glassed Veins")
    glassed_veins["description"] = (
        "Non-DAEMON Emperor's Children CHARACTER. Once per battle round, when the bearer's "
        "unit takes a Leadership test to cease being Stupefied, you can re-roll that test."
    )
    catalogue["revision"] = 57


def apply_revision_58(catalogue):
    entries = catalogue["sharedSelectionEntries"]
    revised_abilities = {
        "Fulgrim": {
            "Sovereign of Sensation": (
                "Once per battle round, when this model would become Enraptured or Stupefied, "
                "you can choose for it to enter the other state or neither state instead."
            ),
            "Phoenician Ambrosia": """**Obsessed — Perfect Precision**

Each time this model makes an attack with its Daemonic Blades against its Obsession, an unmodified Hit roll of 5+ scores a Critical Hit.

**Enraptured — Ecstatic Slaughter**

Once per Fight phase, after this model fights, it can make an additional Pile-in move of up to 3", even if it is in base-to-base contact with an enemy model. When doing so, it can move towards any enemy unit instead of the closest enemy model. After this move, this model can make attacks with the Daemonic Blades profile it did not use during its first fight this phase.

**Stupefied — Unrestrained Savagery**

Each time this model fights, it can make attacks with both profiles of its Daemonic Blades (Strike and Sweep).

**Attack restrictions**

While Enraptured or Stupefied, this model can attack with each Daemonic Blades profile and its Serpentine Tail only once per Fight phase, even if another rule allows it to fight again. Ecstatic Slaughter's additional attacks are made only by this model and do not count as fighting again.""",
        },
        "Julius Kaesoron": {
            "Gifts of the Favoured Son": (
                'At the end of your Command phase, select one other friendly Emperor\'s Children unit within 6" '
                "of this model. That unit can either become Enraptured or cease to be Stupefied "
                "without taking a Leadership test."
            ),
        },
        "Eidolon": {
            "Lord Commander Primus": (
                'Once per battle round, when another friendly Emperor\'s Children Infantry unit within 6" of '
                "this model declares a charge, that unit can re-roll its Charge roll. If that unit is Stupefied, "
                "it can also ignore the closest-target restriction of that state for that charge."
            ),
        },
        "Threnody Dreadnought": {
            "Interred in Rapture": (
                "When this model is set up during deployment, select one objective marker on the battlefield. "
                "While this model is within range of that marker, it is Enraptured. Otherwise, it is Stupefied. "
                "This model cannot become Obsessed or cease to be Enraptured or Stupefied except as specified "
                "by this ability."
            ),
        },
    }
    for unit_name, abilities in revised_abilities.items():
        for name, description in abilities.items():
            ability(named(entries, unit_name), name, description, previous=name)

    for unit_name, name, original in (
        ("Lord Exultant in Terminator Armour", "Unbroken Arrogance", "cease being Stupefied"),
        ("Chirurgeon", "Controlled Overdose", "cease being Stupefied"),
        ("Idol of Sublime Perfection", "Fed by Suffering", "ceased to be Stupefied"),
        ("Herald of Excess", "Procession of Sensation (Aura)", "ends Stupefied"),
    ):
        profile = named(named(entries, unit_name)["profiles"], name)["characteristics"][0]
        assert original in profile["$text"], name
        profile["$text"] = profile["$text"].replace(original, original.replace("Stupefied", "Enraptured or Stupefied"))
    glassed = named(named(entries, "Glassed Veins")["rules"], "Glassed Veins")
    glassed["description"] = glassed["description"].replace(
        "cease being Stupefied", "cease being Enraptured or Stupefied"
    )

    pursuit = named(catalogue["sharedRules"], "The Pursuit of Perfection")
    pursuit["description"] = pursuit["description"].replace(
        "A unit can be in only one of these states at a time.",
        "When a unit enters one of these states, it ceases to be in any other of these states.",
    )
    pursuit["description"] += (
        " Pain Brings Clarity cannot cause a unit to cease being Enraptured or Stupefied "
        "during the turn in which it entered that state."
    )

    for detachment, names in (
        ("The Exalted Court", ("By Royal Command", "Reassignment of Honour")),
        ("The Theatre of Excess", ("Steal the Spotlight", "Stolen Ovation", "The Final Bow")),
    ):
        for name in names:
            prefix = f"{detachment} — {name} / "
            strat = next(rule for rule in catalogue["sharedRules"] if rule["name"].startswith(prefix))
            target, effect = strat["description"].split("\n\n### Effect", 1)
            strat["description"] = (
                target + " You can target that friendly unit with this Stratagem even if it is Stupefied."
                "\n\n### Effect" + effect
            )

    group = named(named(entries, "Detachment")["selectionEntryGroups"], "Detachment")
    detachments = group["selectionEntries"]
    seductions = named(named(detachments, "The Seductions of Slaanesh")["rules"], "Whispers of the Dark Prince")
    seductions["description"] = seductions["description"].replace(
        "Apply all Boons and Prices from the unit's current Level and each lower Level.",
        "Apply all Boons and Prices from the unit's current Level and each lower Level. "
        "Apply any Seduction Price that requires the closest eligible enemy where possible "
        "within the targeting restrictions of Obsessed or Stupefied.",
    )
    catalogue["revision"] = 58


def apply_revision_59(catalogue):
    fulgrim = named(catalogue["sharedSelectionEntries"], "Fulgrim")
    ability(
        fulgrim,
        "Weapon Ability: Daemonic Poisons — Serpentine Tail",
        "After resolving attacks with this weapon, each enemy unit that suffered damage from those attacks "
        "is Poisoned until the end of the phase. While a unit is Poisoned, subtract 1 from the Damage "
        "characteristic of melee weapons equipped by its models, to a minimum of 1.",
        previous="Weapon ability: Daemonic Poisons - Serpentine tail",
    )
    catalogue["revision"] = 59


def apply_revision_60(catalogue):
    fulgrim = named(catalogue["sharedSelectionEntries"], "Fulgrim")
    ambrosia = named(fulgrim["profiles"], "Phoenician Ambrosia")["characteristics"][0]
    ambrosia["$text"] = ambrosia["$text"].replace(
        "Once per Fight phase, after this model fights,",
        "After this model fights,",
    )
    catalogue["revision"] = 60


def selection_count(unit, child, kind, amount):
    return dict(childId=child, field="selections", scope=unit["id"], type=kind,
                value=amount, shared=True, includeChildSelections=True)


def expose_squad_composition(unit, legacy):
    small, large = legacy["selectionEntries"]
    source = named(small["selectionEntryGroups"], "Models")
    large_group = named(large["selectionEntryGroups"], "Models")
    small_size = next(c["value"] for c in source["constraints"] if c["type"] == "min")
    large_size = next(c["value"] for c in large_group["constraints"] if c["type"] == "min")

    # Older rosters already store a size and its child selections. Keep that
    # path active for those units and expose the model counters for new ones.
    old_size = [selection_count(unit, size["id"], "atLeast", 1) for size in (small, large)]
    new_size = [selection_count(unit, size["id"], "equalTo", 0) for size in (small, large)]
    legacy["hidden"] = True
    legacy["defaultSelectionEntryId"] = "none"
    next(c for c in legacy["constraints"] if c["type"] == "min")["value"] = 0
    legacy.setdefault("modifiers", []).append(dict(
        field="hidden", type="set", value=False,
        conditionGroups=[dict(type="or", conditions=old_size)],
    ))

    def clone_with_new_ids(branch):
        cloned = copy.deepcopy(branch)
        ids = {obj["id"]: identifier("unit-editor:" + obj["id"])
               for obj in walk(cloned) if "id" in obj}
        for obj in walk(cloned):
            for key, value in obj.items():
                if isinstance(value, str) and value in ids:
                    obj[key] = ids[value]
        return cloned

    def hide_with_legacy(entry):
        entry.setdefault("modifiers", []).append(dict(
            field="hidden", type="set", value=True,
            conditionGroups=[dict(type="or", conditions=old_size)],
        ))
        return entry

    group = clone_with_new_ids(source)
    models = group["selectionEntries"]
    regular = max(models, key=lambda e: e["defaultAmount"])
    specialists = [model for model in models if not model["defaultAmount"]]
    champions = [model for model in models if model is not regular and model["defaultAmount"]]
    champion_count = sum(model["defaultAmount"] for model in champions)
    regular_min = next(c for c in regular["constraints"] if c["type"] == "min")
    regular_max = next(c for c in regular["constraints"] if c["type"] == "max")
    regular_max.update(value=large_size - champion_count, scope="parent",
                       includeChildSelections=False)

    large_squad = selection_count(unit, "model", "atLeast", large_size)
    for model in specialists:
        large_model = named(large_group["selectionEntries"], model["name"])
        maxima = [c for c in model["constraints"] if c["type"] == "max"]
        limit = min(maxima, key=lambda c: c["value"])
        model["constraints"] = [limit]
        limit.update(scope="parent", includeChildSelections=False)
        large_limit = min(c["value"] for c in large_model["constraints"] if c["type"] == "max")
        adjustments = model.setdefault("modifiers", [])
        adjustments.insert(0, dict(field=limit["id"], type="set", value=large_limit,
                                   conditions=[large_squad]))
        for adjustment in adjustments[1:]:
            assert adjustment["field"] == limit["id"], model["name"]
            adjustment.update(type="decrement", value=1)
            for condition in adjustment["conditions"]:
                condition["scope"] = unit["id"]

    for adjustment in list(regular.get("modifiers", [])):
        if adjustment["field"] == regular_min["id"]:
            maximum_adjustment = copy.deepcopy(adjustment)
            maximum_adjustment["field"] = regular_max["id"]
            regular["modifiers"].append(maximum_adjustment)

    direct = unit.setdefault("selectionEntries", [])
    for champion in champions:
        champion_max = next(c for c in champion["constraints"] if c["type"] == "max")
        champion_max.update(scope="parent", includeChildSelections=False)
        champion["sortIndex"] = 0
        direct.append(hide_with_legacy(champion))

    if specialists:
        lower, upper = small_size - champion_count, large_size - champion_count
        group.update(name=f"{lower}-{upper} {unit['name']}",
                     defaultSelectionEntryId=regular["id"], sortIndex=1)
        for constraint in group["constraints"]:
            constraint["value"] = lower if constraint["type"] == "min" else upper
        group["selectionEntries"] = [regular, *specialists]
        unit["selectionEntryGroups"].append(hide_with_legacy(group))
    else:
        regular["sortIndex"] = 1
        direct.append(hide_with_legacy(regular))

    for option in clone_with_new_ids(small.get("selectionEntries", [])):
        option["constraints"] = [c for c in option["constraints"] if c["scope"] == "parent"]
        option["sortIndex"] = 2
        direct.append(hide_with_legacy(option))

    unit.setdefault("modifiers", []).extend([
        dict(field=POINTS, type="increment", value=named(large["costs"], "pts")["value"],
             conditions=[*new_size, selection_count(unit, "model", "greaterThan", small_size)]),
        dict(field="error", type="add", value=f"Select exactly {small_size} or {large_size} models.",
             conditions=[*new_size, selection_count(unit, "model", "greaterThan", small_size),
                         selection_count(unit, "model", "lessThan", large_size)]),
    ])


def apply_revision_62(catalogue):
    for unit in catalogue["sharedSelectionEntries"]:
        if unit.get("type") not in {"unit", "model"}:
            continue
        for group in list(unit.get("selectionEntryGroups", [])):
            if group["name"] == "Unit Size":
                expose_squad_composition(unit, group)

        for option in list(walk(unit)):
            weapons = option.get("selectionEntries", [])
            if option.get("type") != "upgrade" or len(weapons) != 1:
                continue
            weapon = weapons[0]
            if weapon["name"] != option["name"] or weapon.get("defaultAmount") != 1:
                continue
            if not any(p["typeName"] in {"Melee Weapons", "Ranged Weapons"}
                       for p in weapon.get("profiles", [])):
                continue
            for key in ("profiles", "infoLinks", "costs"):
                if key in weapon:
                    option.setdefault(key, []).extend(weapon[key])
            del option["selectionEntries"]
    catalogue["revision"] = 62


def assign_model_wargear(catalogue, unit, models, name, profile):
    legacy = [node for node in walk(unit)
              if node.get("type") == "upgrade" and node["name"] == name]
    assert legacy, (unit["name"], name)
    # Keep a saved unit-level selection visible until the player reassigns it.
    for choice in legacy:
        choice["hidden"] = True
        choice["modifiers"] = [dict(
            field="hidden", type="set", value=False,
            conditions=[selection_count(unit, choice["id"], "atLeast", 1)],
        )]
        if not choice.get("profiles"):
            legacy_profile = copy.deepcopy(profile)
            legacy_profile["id"] = identifier(choice["id"] + ":ability")
            choice["profiles"] = [legacy_profile]
        choice["profiles"][0]["characteristics"][0]["$text"] = profile["characteristics"][0]["$text"]

    target_id = identifier(unit["id"] + ":bearer:" + name)
    target = dict(name=name, id=target_id, type="upgrade", hidden=False,
                  profiles=[profile], constraints=[
                      dict(id=identifier(target_id + ":limit"), type="max", value=1,
                           field="selections", scope=unit["id"], shared=True,
                           includeChildSelections=True),
                  ])
    catalogue["sharedSelectionEntries"].append(target)
    legacy_selected = [selection_count(unit, choice["id"], "atLeast", 1) for choice in legacy]
    for model in models:
        link = dict(name=name, id=identifier(model["id"] + ":bearer:" + name),
                    targetId=target_id, type="selectionEntry", hidden=False,
                    modifiers=[dict(field="hidden", type="set", value=True,
                                    conditionGroups=[dict(type="or", conditions=legacy_selected)])])
        link["import"] = True
        model.setdefault("entryLinks", []).append(link)


def apply_revision_63(catalogue):
    entries = catalogue["sharedSelectionEntries"]
    fulgrim = named(entries, "Fulgrim")
    ambrosia = named(fulgrim["profiles"], "Phoenician Ambrosia")["characteristics"][0]
    for state, subtitle in (("Obsessed", "Perfect Precision"),
                            ("Enraptured", "Ecstatic Slaughter"),
                            ("Stupefied", "Unrestrained Savagery")):
        ambrosia["$text"] = ambrosia["$text"].replace(
            f"**{state} — {subtitle}**\n\n", f"**{state}**  \n",
        )
    ambrosia["$text"] = ambrosia["$text"].replace(
        "Ecstatic Slaughter's additional attacks", "The additional attacks while Enraptured",
    )
    for name in ("Infractors", "Tormentors"):
        unit = named(entries, name)
        options = [node for node in walk(unit)
                   if node.get("type") == "upgrade" and node["name"] == "Icon of Excess"]
        profile = copy.deepcopy(options[0]["profiles"][0])
        profile["id"] = identifier(unit["id"] + ":bearer:icon-profile")
        profile["characteristics"][0]["$text"] = 'While this unit contains the bearer, each time this unit destroys an enemy unit with its attacks, every enemy unit within 6" of this unit must take a Battle-shock test.'
        model_name = "Infractor" if name == "Infractors" else None
        models = [node for node in walk(unit) if node.get("type") == "model"
                  and (model_name is None or node["name"] == model_name)]
        assign_model_wargear(catalogue, unit, models, "Icon of Excess", profile)

    unit = named(entries, "Daemonettes")
    model = named(named(unit["selectionEntryGroups"], "Models")["selectionEntries"], "Daemonette")
    original_links = len(model.get("entryLinks", []))
    for choice, title, effect in (
        ("Daemonic icon", "Daemonic Icon", "you can re-roll its initial Manifestation roll each time it is summoned."),
        ("Instrument of Chaos", "Instrument of Chaos", "add 1 to its Charge rolls."),
    ):
        profile = named(unit["profiles"], title)
        unit["profiles"].remove(profile)
        profile["characteristics"][0]["$text"] = "While this unit contains the bearer, " + effect
        assign_model_wargear(catalogue, unit, [model], choice, profile)
    links = model["entryLinks"]
    gear = dict(name="Bearer wargear", id=identifier(model["id"] + ":bearer-wargear"),
                hidden=False, entryLinks=links[original_links:], constraints=[
                    dict(id=identifier(model["id"] + ":bearer-limit"), type="max", value=1,
                         scope="parent", field="selections", shared=True,
                         includeChildSelections=False),
                ])
    del links[original_links:]
    if not links:
        del model["entryLinks"]
    model.setdefault("selectionEntryGroups", []).append(gear)
    catalogue["revision"] = 63


def format_daemonette_bearers(entries):
    unit = named(entries, "Daemonettes")
    models = named(unit["selectionEntryGroups"], "Models")
    daemonette = named(models["selectionEntries"], "Daemonette")
    gear = named(daemonette["selectionEntryGroups"], "Bearer wargear")
    gear["flatten"] = True
    gear["name"] = "Wargear"
    for link, suffix in zip(gear["entryLinks"], ("with Daemonic Icon", "with Instrument of Chaos")):
        target = next(entry for entry in entries if entry["id"] == link["targetId"])
        link["name"] = target["name"] = target["profiles"][0]["name"]
        daemonette.setdefault("modifiers", []).append(dict(
            type="append", field="name", value=suffix,
            conditions=[dict(childId=link["id"], field="selections", scope="self",
                             type="atLeast", value=1, shared=True, includeChildSelections=True)],
        ))
    named(unit["selectionEntries"], "Daemonic icon")["name"] = "Daemonic Icon"

    # The standard Chaos Daemons squad field one Alluress and nine Daemonettes.
    # Saved rosters with ten Daemonettes retain their selections and model count.
    alluress = copy.deepcopy(daemonette)
    alluress["name"] = "Alluress"
    alluress.pop("selectionEntryGroups")
    alluress.pop("modifiers")
    alluress["defaultAmount"] = 1
    alluress["sortIndex"] = 0
    for node in walk(alluress):
        if "id" in node:
            node["id"] = identifier(node["id"] + ":alluress")
    alluress["profiles"][0]["name"] = "Alluress"
    for limit in alluress["constraints"]:
        limit.update(value=1, scope="parent", includeChildSelections=False)

    legacy = [
        selection_count(unit, daemonette["id"], "atLeast", 10),
        selection_count(unit, alluress["id"], "equalTo", 0),
    ]
    minimum = next(c for c in alluress["constraints"] if c["type"] == "min")
    alluress["modifiers"] = [
        dict(type="set", field=minimum["id"], value=0, conditions=legacy),
        dict(type="set", field="hidden", value=True, conditions=legacy),
    ]
    daemonette["defaultAmount"] = 9
    daemonette["sortIndex"] = 1
    for limit in daemonette["constraints"]:
        limit["value"] = 9
    maximum = next(c for c in daemonette["constraints"] if c["type"] == "max")
    daemonette["modifiers"].append(dict(type="set", field=maximum["id"],
                                      value=10, conditions=legacy))
    models["selectionEntries"].insert(0, alluress)


def apply_revision_64(catalogue, system):
    entries = catalogue["sharedSelectionEntries"]
    # Use the November Space Marines codex profiles for shared weapons and
    # the equivalent Chaos chassis for stock Chaos-only weapons, with the
    # homebrew Twin lascannon set to two attacks.
    standard = {
        "Meltagun": dict(D="D3+2"),
        "Multi-melta": dict(S="10", AP="-3", D="D3+2", Keywords="Melta 3"),
        "Multi-melta - Hunter": dict(AP="-3", D="D3+2", Keywords="Melta 3, Hunter: Monster/Vehicle"),
        "Heavy bolter": dict(S="5"),
        "Twin heavy bolter": dict(A="3", S="5", Keywords="Rapid Fire 2, Sustained Hits 1, Twin-linked"),
        "Twin lascannon": dict(A="2"),
        "Heavy flamer": dict(A="3", S="5", Keywords="Blast 2, Torrent"),
        "Predator autocannon": dict(A="4", Keywords="Rapid Fire 2"),
        "Havoc launcher": dict(A="D6"),
    }
    renamed = {
        "Combi-weapon - plasma": "Combi-weapon - Purgatus",
        "Combi-weapon - melta": "Combi-weapon - Damnatus",
    }
    for unit in entries:
        if unit.get("type") not in {"unit", "model"}:
            continue
        for node in list(walk(unit)):
            updated_keywords = False
            for profile in node.get("profiles", []):
                if profile["typeName"] != "Ranged Weapons":
                    continue
                name = profile["name"]
                changes = standard.get(name, {})
                if unit["name"] == "Doomrider" and name.startswith("Daemonic twin meltagun - "):
                    changes = dict(D="D3+2")
                elif unit["name"] == "Lord Exultant in Terminator Armour" and name == "Combi-bolter":
                    changes = dict(A="2", Keywords="Rapid Fire 2")
                elif unit["name"] == "Threnody Dreadnought" and name == "Heavy bolter":
                    changes = dict(S="5", Keywords="Rapid Fire 2, Sustained Hits 1")
                elif unit["name"] == "Heldrake" and name == "Hades autocannon":
                    changes = dict(A="6", S="8", D="2")
                elif unit["name"] == "Agoniser" and name == "Missile launcher - frag":
                    changes = dict(A="4", S="4")
                for characteristic, value in changes.items():
                    named(profile["characteristics"], characteristic)["$text"] = value
                updated_keywords |= "Keywords" in changes
                profile["name"] = renamed.get(name, name)
            if updated_keywords:
                # Only the heavy flamer loses a linked keyword in this pass.
                if any(p["name"] == "Heavy flamer" for p in node["profiles"]):
                    node["infoLinks"] = [link for link in node.get("infoLinks", [])
                                         if link["name"].casefold() != "ignores cover"]
                weapon_rules(node, system)

    format_daemonette_bearers(entries)
    catalogue["revision"] = 64


def restore_squad_wargear(entries, unit, name):
    squad_option = named(unit["selectionEntries"], name)
    saved_options = [entry for entry in walk(unit)
                     if entry is not squad_option and entry.get("name") == name
                     and entry.get("type") in {"upgrade", "selectionEntry"}]
    squad_option.update(hidden=False, modifiers=[dict(
        field="hidden", type="set", value=True,
        conditionGroups=[dict(type="or", conditions=[
            selection_count(unit, entry["id"], "atLeast", 1) for entry in saved_options
        ])],
    )])
    for old in saved_options:
        old.update(hidden=True, modifiers=[dict(
            field="hidden", type="set", value=False,
            conditions=[selection_count(unit, old["id"], "atLeast", 1)],
        )])
    # The option remains a bearer-dependent rule, like the Legionaries' icon.
    profile = squad_option["profiles"][0]
    if name == "Icon of Excess":
        profile["characteristics"][0]["$text"] = (
            'Each time the bearer’s unit destroys an enemy unit with its attacks, every enemy '
            'unit within 6" of the bearer’s unit must take a Battle-shock test.'
        )
    for entry in saved_options:
        target = next((e for e in entries if e["id"] == entry.get("targetId")), entry)
        target["profiles"][0]["characteristics"][0]["$text"] = profile["characteristics"][0]["$text"]


def apply_revision_65(catalogue):
    entries = catalogue["sharedSelectionEntries"]
    for name in ("Infractors", "Tormentors"):
        restore_squad_wargear(entries, named(entries, name), "Icon of Excess")

    unit = named(entries, "Daemonettes")
    models = named(unit["selectionEntryGroups"], "Models")
    alluress = named(models["selectionEntries"], "Alluress")
    daemonette = named(models["selectionEntries"], "Daemonette")
    alluress_selected = selection_count(unit, alluress["id"], "atLeast", 1)
    alluress.update(hidden=True, defaultAmount=0, modifiers=[
        dict(type="set", field="hidden", value=False, conditions=[alluress_selected]),
    ])
    next(c for c in alluress["constraints"] if c["type"] == "min")["value"] = 0
    daemonette["modifiers"] = [m for m in daemonette["modifiers"] if m["field"] == "name"]
    daemonette["defaultAmount"] = 10
    for limit in daemonette["constraints"]:
        limit["value"] = 10
        daemonette["modifiers"].append(dict(type="set", field=limit["id"], value=9,
                                          conditions=[alluress_selected]))
    for name in ("Daemonic Icon", "Instrument of Chaos"):
        restore_squad_wargear(entries, unit, name)

    catalogue["revision"] = 65


def add_bearer_pickers(entries):
    for unit_name, gear_names, eligible in (
        ("Infractors", {"Icon of Excess"}, "Infractor"),
        ("Tormentors", {"Icon of Excess"}, None),
        ("Daemonettes", {"Daemonic Icon", "Instrument of Chaos"}, "Daemonette"),
    ):
        unit = named(entries, unit_name)
        models = [model for model in walk(unit)
                  if model.get("type") == "model" and model.get("name") == eligible]
        for gear in list(walk(unit)):
            if gear.get("type") != "upgrade" or gear.get("name") not in gear_names:
                continue
            association = dict(
                name="Instrument" if gear["name"] == "Instrument of Chaos" else "Icon",
                id=identifier(gear["id"] + ":bearer"),
                childId=models[0]["id"] if len(models) == 1 else "model",
                includeChildSelections=True, min=1, max=1, scope=unit["id"],
            )
            if len(models) > 1:
                association["conditionGroups"] = [dict(type="or", conditions=[
                    dict(childId=model["id"], field="selections", scope="self",
                         type="instanceOf", value=1, shared=True, includeChildSelections=False)
                    for model in models
                ])]
            gear["associations"] = [association]


def apply_revision_66(catalogue, system):
    profiles = {
        "Screamer pistol": ('12"', "3", "6", "-1", "2", "Close-Quarters"),
        "Sonic blaster": ('18"', "3", "6", "-1", "2", ""),
        "Twin sonic blaster": ('18"', "4", "6", "-1", "2", "Twin-linked"),
        "Combi-weapon - sonic": ('18"', "4", "5", "-1", "1", "Assault"),
        "Whisper carbine": ('18"', "2", "6", "-1", "1", ""),
        "Blastmaster - varied frequency": ('18"', "6", "6", "-2", "1", "Blast 2"),
        "Blastmaster - single frequency": ('18"', "3", "10", "-2", "3", "Blast 2"),
        "Shriek cannon": ('24"', "4", "7", "-2", "2", "Precision"),
        "Discord cannon - crescendo": ('24"', "8", "8", "-2", "2", "Blast 2"),
        "Discord cannon - rupture": ('24"', "3", "14", "-3", "D3+3", "Blast 2"),
        "Requiem cannon - crescendo": ('24"', "6", "9", "-2", "2", ""),
        "Requiem cannon - rupture": ('24"', "2", "16", "-4", "D3+3", ""),
        "Dreadblaster - crescendo": ('24"', "4", "8", "-2", "2", "Blast 2"),
        "Dreadblaster - rupture": ('24"', "2", "14", "-3", "D3+3", ""),
        "Resonance cannon - crescendo": ('24"', "4", "8", "-1", "2", "Blast 1"),
        "Resonance cannon - rupture": ('24"', "2", "12", "-2", "3", "Blast 1"),
        "Sonic destructor - crescendo": ('24"', "4", "8", "-1", "2", "Blast 2"),
        "Sonic destructor - rupture": ('36"', "2", "14", "-3", "D3+3", ""),
        "Sonic balespewer": ('18"', "6", "10", "-2", "2", "Torrent"),
        "Cathedral sonic immolator": ('18"', "8", "12", "-2", "3", "Torrent"),
        "Grand vox array": ('24"', "10", "6", "-1", "2", "Blast 1"),
    }
    sonic_without_new_stats = {"Death Scream", "The Eighth's Refrain", "First Scream"}
    entries = catalogue["sharedSelectionEntries"]
    raider = named(entries, "Chaos Land Raider")
    ghosts = named(entries, "Ghosts")
    # Retain selection and profile IDs for existing two-cannon loadouts.
    for node in walk(raider):
        for field in ("name", "description", "readme", "$text"):
            if field not in node:
                continue
            node[field] = node[field].replace("Cathedral annihilator", "Requiem cannon")
            node[field] = node[field].replace("cathedral annihilator", "requiem cannon")
    ghosts["infoLinks"] = [link for link in ghosts["infoLinks"] if link["name"] != "Stealth"]
    for node in walk(ghosts):
        for field in ("description", "readme", "$text"):
            if field in node:
                node[field] = node[field].replace("Infiltrators, Stealth", "Infiltrators")

    blast_id = named(system["sharedRules"], "Blast")["id"]
    for node in list(walk(catalogue)):
        ranged = [p for p in node.get("profiles", []) if p["typeName"] == "Ranged Weapons"]
        changed = False
        for profile in ranged:
            name = profile["name"]
            characteristics = {c["name"]: c for c in profile["characteristics"]}
            if name in profiles:
                distance, attacks, strength, ap, damage, keywords = profiles[name]
                for field, value in zip(("Range", "A", "S", "AP", "D"),
                                        (distance, attacks, strength, ap, damage)):
                    characteristics[field]["$text"] = value
                keywords = keywords.split(", ") if keywords else []
                keywords.append("Ignores Cover")
            elif name.split(" - ", 1)[0] in sonic_without_new_stats:
                keywords = [keyword for keyword in characteristics["Keywords"]["$text"].split(", ")
                            if not keyword.casefold().startswith("blast")]
            else:
                continue
            characteristics["Keywords"]["$text"] = ", ".join(keywords)
            changed = True
        if changed:
            if not any("blast" in named(p["characteristics"], "Keywords")["$text"].casefold()
                       for p in ranged):
                node["infoLinks"] = [link for link in node.get("infoLinks", [])
                                     if link["targetId"] != blast_id]
            weapon_rules(node, system)

    rule_link(named(entries, "Army Rules and References"),
              named(catalogue["sharedRules"], "Sonic Weapons"))
    add_bearer_pickers(entries)
    catalogue["revision"] = 66


def consolidate_unit_profiles(entries):
    for unit in entries:
        if unit.get("type") != "unit":
            continue

        model_profiles = [profile for model in walk(unit) if model.get("type") == "model"
                          for profile in model.get("profiles", [])
                          if profile["typeName"] == "Unit" and not profile.get("hidden")]
        if not model_profiles:
            continue

        stats = {profile["name"]: tuple(c["$text"] for c in profile["characteristics"])
                 for profile in model_profiles}
        for profile in model_profiles:
            base_name, separator, _ = profile["name"].partition(" with ")
            if separator and stats.get(base_name) == stats[profile["name"]]:
                profile["name"] = base_name

        # The models already supply these stats. Keep any distinct unit profile.
        unit["profiles"] = [
            profile for profile in unit.get("profiles", [])
            if profile["typeName"] != "Unit"
            or tuple(c["$text"] for c in profile["characteristics"]) not in stats.values()
        ]


def apply_revision_67(catalogue):
    entries = catalogue["sharedSelectionEntries"]
    infractors = named(entries, "Infractors")
    for option in walk(infractors):
        if option.get("name") == "Icon of Excess":
            for association in option.get("associations", []):
                association["defaultSelectionEntryId"] = "none"

    consolidate_unit_profiles(unit for unit in entries if any(
        link["name"] == "Infantry" for link in unit.get("categoryLinks", [])
    ))
    catalogue["revision"] = 67


def apply_revision_68(catalogue):
    consolidate_unit_profiles(catalogue["sharedSelectionEntries"])
    catalogue["revision"] = 68


def apply_revision_69(catalogue):
    infractors = named(catalogue["sharedSelectionEntries"], "Infractors")
    icons = [option for option in walk(infractors) if option.get("name") == "Icon of Excess"]
    legacy_icons = [option for option in icons if option.get("type") == "upgrade"]
    legacy_selected = [selection_count(infractors, option["id"], "atLeast", 1)
                       for option in legacy_icons]
    for option, selected in zip(legacy_icons, legacy_selected):
        # Keep old rosters editable. New icons live under the bearer model.
        option.update(hidden=True, modifiers=[dict(
            field="hidden", type="set", value=False, conditions=[selected],
        )])
    for link in icons:
        if link.get("type") == "selectionEntry":
            taken = selection_count(infractors, link["targetId"], "atLeast", 1)
            unselected_here = dict(childId=link["id"], field="selections", scope="parent",
                                   type="equalTo", value=0, shared=True, includeChildSelections=True)
            link.update(hidden=False, modifiers=[
                dict(field="hidden", type="set", value=True,
                     conditionGroups=[dict(type="or", conditions=legacy_selected)]),
                dict(field="hidden", type="set", value=True, conditions=[taken, unselected_here]),
            ])
    catalogue["revision"] = 69


def apply_revision_70(catalogue):
    entries = catalogue["sharedSelectionEntries"]
    restore_squad_wargear(entries, named(entries, "Infractors"), "Icon of Excess")
    catalogue["revision"] = 70


def apply_revision_71(catalogue, system):
    # Keep the category for the Incursion budget calculation.
    category = named(system["categoryEntries"], "3DP Detachment")
    del category["constraints"]
    catalogue["revision"] = 71


def apply_revision_72(catalogue, system):
    labels = [rule["name"] for rule in system["sharedRules"]]
    labels += [category["name"].removeprefix("Faction: ")
               for book in (system, catalogue) for category in book["categoryEntries"]]
    canonical = {label.upper(): label for label in labels if len(label) > 3 and not label.isupper()}
    names = "|".join(re.escape(label) for label in sorted(canonical, key=len, reverse=True))
    keyword = re.compile(rf"(?<![A-Za-z])(?:{names})(?![A-Za-z])")

    for node in walk(catalogue):
        for field in ("description", "readme", "$text"):
            if isinstance(node.get(field), str):
                node[field] = keyword.sub(lambda match: canonical[match[0]], node[field])
    catalogue["revision"] = 72


def format_subrules(catalogue):
    paragraph_label = re.compile(r"(^|\n\n)(\*\*[^*\n]+[.:]\*\*) +")
    opening_heading = re.compile(r"^\*\*[^*\n]+\*\*[ \t]*\n")
    heading_before_text = re.compile(r"^(\*\*[^*\n]+\*\*)[ \t]*\n{1,2}(?=[\w'\"“‘])", re.M)

    def format_text(text):
        start = text.lstrip()
        start = paragraph_label.sub(r"\1\2  \n", start)
        body = heading_before_text.sub(r"\1<br>", start)
        if not opening_heading.match(start):
            return text[:len(text) - len(text.lstrip())] + body
        # New Recruit places the first Markdown paragraph inline with the title.
        # HTML breaks avoid the extra line spacing of Markdown breaks here.
        return "\u200b<br><br>" + body

    for node in walk(catalogue):
        for key in ("rules", "sharedRules"):
            for rule in node.get(key, []):
                if not rule.get("hidden") and isinstance(rule.get("description"), str):
                    rule["description"] = format_text(rule["description"])
        if node.get("typeName") == "Abilities" and not node.get("hidden"):
            for field in node["characteristics"]:
                if field["name"] == "Description":
                    field["$text"] = format_text(field["$text"])


def remove_psychic_ignores_cover(catalogue, system):
    cover = named(system["sharedRules"], "Ignores Cover")
    for entry in walk(catalogue):
        keywords = [named(profile["characteristics"], "Keywords")
                    for profile in entry.get("profiles", [])
                    if profile["typeName"] in {"Ranged Weapons", "Melee Weapons"}]
        removed = False
        for characteristic in keywords:
            values = characteristic["$text"].split(", ")
            if "Psychic" in values and cover["name"] in values:
                values.remove(cover["name"])
                characteristic["$text"] = ", ".join(values)
                removed = True
        if removed and not any(cover["name"] in column["$text"].split(", ") for column in keywords):
            entry["infoLinks"] = [link for link in entry.get("infoLinks", [])
                                  if link["targetId"] != cover["id"]]

    for unit, before, after in (
        ("Raptureweaver", "[Blast 1], [Ignores Cover]. Focused", "[Blast 1]. Focused"),
        ("Torment Oracle", " Soulspike gains [Ignores Cover].", ""),
    ):
        for node in walk(named(catalogue["sharedSelectionEntries"], unit)):
            for field in ("description", "$text"):
                if isinstance(node.get(field), str):
                    node[field] = node[field].replace(before, after)


def update_daemon_abilities(units):
    aura = 'Reality Unravels (12" Aura)'
    aura_text = (
        'While a unit is within 12" of one or more Greater Daemons with this ability, improve the '
        'Armour Penetration characteristic of its melee weapons by 1 if it is a Daemon unit. '
        'If it is an enemy non-Daemon unit, worsen its Leadership characteristic by 1.'
    )
    for name in GREATER_DAEMONS:
        ability(units[name], aura, aura_text, previous=aura)

    ability(units["Infernal Enrapturess"], "Harmonic Alignment",
            'At the start of your Command phase, select one friendly Legions of Excess unit within '
            '6" of this model. That unit heals D3 wounds.', previous="Harmonic Alignment")


def migrate(catalogue, system):
    assert catalogue["revision"] == 43
    units = {entry["name"]: entry for entry in catalogue["sharedSelectionEntries"]
             if entry["type"] in {"unit", "model"}}
    apply_costs(units)
    apply_native_units(units)
    for unit, profile, attacks in (
        ("Excruciator Terminators", "Shriek cannon", "4"),
        ("Dissonant Colossi", "Dreadblaster - crescendo", "4"),
        ("Stage of Excess", "Grand vox array", "10"),
        ("Defiler", "Discord cannon - crescendo", "8"),
        ("Defiler", "Sonic balespewer", "7"),
        ("Cacophant", "Resonance cannon - crescendo", "4"),
        ("Palatine Ravager", "Sonic destructor - crescendo", "6"),
        ("Chaos Land Raider", "Cathedral annihilator - crescendo", "6"),
        ("Chaos Land Raider", "Twin sonic blaster", "4"),
        ("Vhalyss, the First Scream", "First Scream - Crescendo", "6"),
    ):
        change_profiles(units[unit], {"Ranged Weapons"}, profile, A=attacks)
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
    apply_revision_57(catalogue)
    apply_revision_58(catalogue)
    apply_revision_59(catalogue)
    apply_revision_60(catalogue)
    apply_revision_62(catalogue)
    apply_revision_63(catalogue)
    apply_revision_64(catalogue, system)
    apply_revision_65(catalogue)
    apply_revision_66(catalogue, system)
    apply_revision_67(catalogue)
    apply_revision_68(catalogue)
    apply_revision_69(catalogue)
    apply_revision_70(catalogue)
    apply_revision_71(catalogue, system)
    apply_revision_72(catalogue, system)
    format_subrules(catalogue)
    remove_psychic_ignores_cover(catalogue, system)
    update_daemon_abilities(units)
    apply_revision_82(catalogue)
    apply_revision_83(catalogue)
    apply_revision_84(catalogue)
    catalogue["revision"] = 84
    system["revision"] += 3
    catalogue["gameSystemRevision"] = system["revision"]
    catalogue["readme"] = "Emperor's Children 4.0 playtest."


ENHANCEMENT_SLOTS = "f759-1bc4-cb3a-f0d2"
UPGRADE_LIMIT = 3


def apply_revision_82(catalogue):
    """Colossi pay +20 from the second copy; every Upgrade allows three copies.

    Repeated copies of an Upgrade use one Enhancement slot in total, matching
    the Upgrades carried over from earlier revisions.
    """
    entries = catalogue["sharedSelectionEntries"]
    colossi = named(entries, "Dissonant Colossi")
    surcharges = [m for m in colossi["modifiers"] if m["field"] == POINTS and m["type"] == "increment"]
    assert len(surcharges) == 1 and surcharges[0]["value"] == 20
    surcharges[0]["conditionGroups"][0]["localConditionGroups"][0]["value"] = 1

    upgrades = [entry for entry in entries if entry["name"].endswith("[Upgrade]")]
    template = next(
        m for entry in upgrades for m in entry.get("modifiers", [])
        if m["field"] == ENHANCEMENT_SLOTS and m["type"] == "set" and m["value"] == 0
    )
    for entry in upgrades:
        maxima = [c for c in entry["constraints"] if c["type"] == "max" and c["scope"] == "roster"]
        assert len(maxima) == 1, entry["name"]
        maxima[0]["value"] = UPGRADE_LIMIT
        if any(m["field"] == ENHANCEMENT_SLOTS for m in entry.get("modifiers", [])):
            continue
        modifier = copy.deepcopy(template)
        group = modifier["conditionGroups"][0]["localConditionGroups"][0]
        selector = next(c for c in group["conditions"] if c["type"] == "instanceOf")
        selector["childId"] = entry["id"]
        entry.setdefault("modifiers", []).append(modifier)


SONIC_SYMPHONY = "for its attacks made with Sonic Weapons."
RANGED_SYMPHONY = "for its ranged attacks."


def apply_revision_83(catalogue):
    """Remove the Sonic Weapons rule; Vhalyss's First Symphony covers all ranged attacks."""
    rule = named(catalogue["sharedRules"], "Sonic Weapons")
    catalogue["sharedRules"].remove(rule)
    for node in walk(catalogue):
        links = node.get("infoLinks")
        if links:
            node["infoLinks"] = [link for link in links if link["targetId"] != rule["id"]]
    vhalyss = named(catalogue["sharedSelectionEntries"], "Vhalyss, the First Scream")
    replaced = 0
    for node in walk(vhalyss):
        for key in ("$text", "description"):
            if isinstance(node.get(key), str) and SONIC_SYMPHONY in node[key]:
                node[key] = node[key].replace(SONIC_SYMPHONY, RANGED_SYMPHONY)
                replaced += 1
    assert replaced, "First Symphony text not found"
    assert "Sonic Weapons" not in json.dumps(catalogue)


DAMAGE_STRATAGEM_EFFECTS = {
    "Peerless Bladesmen — Faultless Parry / 1 CP": (
        "subtract 1 from the Damage characteristic of melee attacks that target your unit, to a minimum of 1.",
        "subtract 1 from the Hit roll for melee attacks that target your unit."),
    "The Exalted Court — Iron Mandate / 1 CP": (
        "subtract 1 from the Damage characteristic of attacks targeting your unit (minimum 1).",
        "subtract 1 from the Wound roll for attacks that target your unit."),
}


def apply_revision_84(catalogue):
    """Only The Gilded Host keeps a -1 Damage stratagem."""
    for name, (old, new) in DAMAGE_STRATAGEM_EFFECTS.items():
        rule = named(catalogue["sharedRules"], name)
        assert rule["description"].count(old) == 1, name
        rule["description"] = rule["description"].replace(old, new)


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
