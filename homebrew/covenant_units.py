"""Model and wargear layout for every Covenant datasheet (Codex: Covenant v5.5.0).

The codex gives wargear options as prose; this table turns them into New Recruit models and choices.
Weapon and wargear names must match datasheets.json; "2 Plasma Rifles" is the "Plasma Rifles" profile.

S(...)     a one-model datasheet. weapons/gear default to everything the datasheet equips.
U(...)     a squad: models, legal sizes and prices, Sergeants and Auxiliary pools.
M(...)     a model type in a squad: name, (min, max), weapons, wargear items.
V(...)     a model type with other weapons, beside the plain model (as the Emperor's Children Tormentors).
           per/count: up to `count` for every `per` plain models of the family; count alone: a flat limit;
           neither: any number. Model types with the same `key` share one limit. `cost` is extra points.
C(...)     a choice group on a single model. Options are "A + B" strings; costs maps an option to extra points.
           exclude=[(option, [options])] on S(): the first option cannot be taken with any of the others.
           empties=[(option, [group labels])] on S(): the option replaces those slots too (as "2 Plasma Rifles"
           replacing the Plasma Pistol); the groups must be cleared when it is taken.
           Sergeant and Auxiliary weapons use one group per slot, as the Emperor's Children Obsessionist
           ("Ranged weapon", "Sidearm", "Melee weapon"). "Label = A + B" names a package by its label.
           A model's Specialist abilities (datasheets.json "specialist_abilities") become one more choice group.
Pool(...)  an Auxiliary allowance. Lists are the codex's Auxiliary lists (by keyword) or named entries.
           weights: slots one model of that list uses (default 1). per/slots: `slots` for every `per` plain
           models; fixed: a flat number of slots.
"""


def S(weapons=None, gear=None, choices=(), sergeants=(), aux=(), extra_models=(), exclude=(), empties=()):
    return dict(single=True, weapons=weapons, gear=gear, choices=list(choices), sergeants=list(sergeants),
                aux=list(aux), extra_models=list(extra_models), exclude=list(exclude), empties=list(empties))


def U(models, sizes, prices=None, exact=True, per_model=None, sergeants=(), aux=(), counted=()):
    return dict(single=False, models=list(models), sizes=list(sizes), prices=list(prices or []), exact=exact,
                per_model=per_model, sergeants=list(sergeants), aux=list(aux), counted=list(counted))


def M(name, count, weapons, gear=(), variants=(), cost=0):
    return dict(name=name, count=count, weapons=list(weapons), gear=list(gear), variants=list(variants), cost=cost)


def V(name, weapons, per=None, count=None, key=None, cost=0, gear=None):
    return dict(name=name, weapons=list(weapons), per=per, count=count, key=key or name, cost=cost, gear=gear)


def C(label, options, minimum=1, maximum=1, costs=None):
    return dict(label=label, options=list(options), min=minimum, max=maximum, costs=dict(costs or {}))


def Pool(lists=(), entries=(), per=None, slots=1, fixed=None, weights=None, required=False, label=None):
    """required: the unit always has exactly `fixed` slots of these models (a commander's retinue)."""
    return dict(lists=list(lists), entries=list(entries), per=per, slots=slots, fixed=fixed,
                weights=dict(weights or {}), required=required, label=label)


def Counted(name, cost, exclude=()):
    """Wargear any number of models can take, counted on the unit (Wrist Shields on Marauders)."""
    return dict(name=name, cost=cost, exclude=list(exclude))


# Weapons a model swaps to that its own datasheet does not print (same profile and skill elsewhere in the codex).
BORROW = {
    ("Sangheili Special Operations Team", "Plasma Rifle"): "T'vaoan Auxiliary",
    ("T'vaoan Skirmishers", "Plasma Rifle"): "T'vaoan Auxiliary",
}

SANG_CCW = "Sangheili Close Combat Weapon"
UNG_CCW = "Unggoy Close Combat Weapon"
YY_CCW = "Yig-Yar Close Combat Weapon"

UNITS = {
    # Epic Heroes
    "Prophet of Truth": S(),
    "Prophet of Regret": S(),
    "Prophet of Mercy": S(),
    "Thel 'Vadam": S(),
    "Rtas 'Vadum": S(),
    "Champions of the Arbiter": U(
        [M("N'tho 'Sraom", (1, 1), ["Covenant Carbine - N'tho", "Plasma Pistol - N'tho", "Energy Sword"],
           gear=["Hero Personal Shield"]),
         M("Usze 'Taham", (1, 1), ["Plasma Rifles - Usze", "Energy Sword"], gear=["Hero Personal Shield"])],
        sizes=[2], prices=[160]),
    "Tartarus": S(),

    # Characters
    "San'Shyuum Advisor": S(),
    "Sangheili Shipmaster": S(),
    "Sangheili Fieldmaster": S(),
    "Sangheili Blademaster": S(),
    "Jiralhanae Chieftain": S(weapons=[], gear=["Chieftain Shield"], choices=[C("Weapons", [
        "Spiker + Chieftain's War Blade", "Bolt Spiker + Chieftain's War Blade",
        "Brute Shot + Chieftain's War Blade", "Skewer + Chieftain's War Blade", "Mangler + Chieftain's Gravity Hammer"],
        costs={"Skewer + Chieftain's War Blade": 10, "Mangler + Chieftain's Gravity Hammer": 10})]),
    "Yig-Yar Corsair-Talon": S(),
    "Yig-Yar Headtaker": S(weapons=["Plasma Pistol", YY_CCW], choices=[C("Precision weapon", [
        "Covenant Carbine", "Needle Rifle", "Particle Beam Rifle", "Stalker Rifle"])]),
    "T'vaoan Raider": S(),
    "Unggoy Deacon": S(),
    "Huragok Engineer": S(),

    # Battleline
    "Jiralhanae Assault Pack": U(
        [M("Jiralhanae Warrior", (4, 8), ["Spiker", "Mangler", "Brute Close Combat Weapon"], variants=[
            V("Jiralhanae Warrior with Brute Shot", ["Brute Shot", "Mangler", "Brute Heavy Melee Weapon"],
              per=4, count=1, key="heavy"),
            V("Jiralhanae Warrior with Bolt Spiker", ["Bolt Spiker", "Mangler", "Brute Heavy Melee Weapon"],
              per=4, count=1, key="heavy"),
            V("Jiralhanae Warrior with Skewer", ["Skewer", "Mangler", "Brute Heavy Melee Weapon"],
              per=4, count=1, key="heavy", cost=10)])],
        sizes=[4, 8], prices=[75, 150], exact=False,
        sergeants=["Jiralhanae Pack Alpha", "Sangheili Ultra"], aux=[Pool(lists=["Unggoy"], per=4, slots=1)]),
    "Yig-Yar Marauders": U(
        [M("Yig-Yar Marauder", (8, 8), ["Plasma Pistol", YY_CCW], variants=[
            V("Yig-Yar Marauder with Needler", ["Needler", YY_CCW], per=4, count=1),
            V("Yig-Yar Marauder with Covenant Carbine", ["Covenant Carbine", YY_CCW], per=4, count=1),
            V("Yig-Yar Marauder with Plasma Rifle", ["Plasma Rifle", YY_CCW], per=4, count=1)])],
        sizes=[8], prices=[55], sergeants=["Jiralhanae Pack Alpha", "Sangheili Ultra", "Yig-Yar Talon"],
        aux=[Pool(lists=["Unggoy"], per=4, slots=2)],
        counted=[Counted("Wrist Shield", 5, exclude=["Yig-Yar Marauder with Covenant Carbine"])]),
    "Grunt Cadre": U(
        [M("Unggoy Warrior", (5, 20), ["Plasma Pistol", UNG_CCW], variants=[
            V("Unggoy Warrior with Plasma Rifle", ["Plasma Rifle", UNG_CCW], per=5, count=1, key="special"),
            V("Unggoy Warrior with Needler", ["Needler", UNG_CCW], per=5, count=1, key="special")])],
        sizes=[5, 10, 20], prices=[25, 45, 85],
        sergeants=["Sangheili Ultra", "Unggoy Ultra", "Jiralhanae Pack Alpha"],
        aux=[Pool(lists=["Sangheili", "Jiralhanae", "Yig-Yar"], per=5, slots=2,
                  weights={"Sangheili": 2, "Jiralhanae": 2, "Yig-Yar": 1})]),
    "Yanme'e Drone Swarm": U(
        [M("Yanme'e Drone", (5, 10), ["Plasma Pistols", "Drone Claws"])], sizes=[5, 10], per_model=8,
        sergeants=["Yanme'e Major"]),

    # Infantry
    "Sangheili Warrior Cadre": U(
        [M("Sangheili Warrior", (3, 6), ["Plasma Pistol", "Storm Rifle", SANG_CCW], gear=["Sangheili Personal Shield"],
           variants=[
               V("Sangheili Warrior with Plasma Rifles", ["Plasma Rifles", SANG_CCW], per=3, count=1, key="rifles"),
               V("Sangheili Warrior with Covenant Carbine", ["Plasma Pistol", "Covenant Carbine", SANG_CCW],
                 per=3, count=1, key="carbine"),
               V("Sangheili Warrior with Needler", ["Plasma Pistol", "Needler", SANG_CCW], per=3, count=1,
                 key="carbine"),
               V("Sangheili Warrior with Plasma Repeater", ["Plasma Pistol", "Plasma Repeater", SANG_CCW],
                 per=3, count=1, key="heavy"),
               V("Sangheili Warrior with Fuel Rod", ["Plasma Pistol", "Fuel Rod", SANG_CCW], per=3, count=1,
                 key="heavy", cost=10)])],
        sizes=[3, 6], prices=[50, 100], exact=False, sergeants=["Sangheili Ultra"],
        aux=[Pool(lists=["Unggoy", "Yig-Yar", "Jiralhanae"], per=3, slots=3, weights={"Jiralhanae": 3})]),
    "Sangheili Rangers": U(
        [M("Sangheili Ranger", (2, 2), ["Covenant Carbine", "Plasma Pistol", SANG_CCW],
           gear=["Sangheili Personal Shield", "Stealth Projector"])],
        sizes=[2], prices=[45], sergeants=["Sangheili Ultra", "Sangheili Shadowmaster"]),
    "Sangheili Swordmasters": U(
        [M("Sangheili Swordmaster", (2, 4), ["Energy Sword", "Plasma Pistol"],
           gear=["Sangheili Personal Shield", "Stealth Projector"])],
        sizes=[2, 4], prices=[55, 110], sergeants=["Sangheili Ultra"],
        aux=[Pool(entries=["Sangheili Auxiliary"], per=2, slots=1)]),
    "Sangheili Special Operations Team": U(
        [M("Sangheili Special Operations Warrior", (3, 3), ["Plasma Rifles", SANG_CCW],
           gear=["Sangheili Personal Shield", "Stealth Projector"], variants=[
               V("Special Operations Warrior with Particle Beam Rifle", ["Particle Beam Rifle", SANG_CCW], count=1,
                 key="long"),
               V("Special Operations Warrior with Stalker Rifle", ["Stalker Rifle", SANG_CCW], count=1, key="long"),
               V("Special Operations Warrior with Energy Sword", ["Plasma Rifle", "Energy Sword"], count=1),
               V("Special Operations Warrior with Satchel Charge", ["Plasma Rifle", "Satchel Charge", SANG_CCW],
                 count=1)])],
        sizes=[3], prices=[110], sergeants=["Sangheili Ultra", "Sangheili Shadowmaster"],
        aux=[Pool(entries=["Sangheili Auxiliary"], fixed=5)]),
    "Sangheili Assassins": U(
        [M("Sangheili Assassin", (3, 6), ["Covenant Carbine", "Plasma Pistol", SANG_CCW],
           gear=["Sangheili Personal Shield"], variants=[
               V("Sangheili Assassin with Energy Sword", ["Energy Sword", "Plasma Pistol", SANG_CCW])])],
        sizes=[3, 6], prices=[75, 150], exact=False, sergeants=["Sangheili Ultra", "Sangheili Shadowmaster"],
        aux=[Pool(lists=["Yig-Yar"], per=3, slots=2)]),
    "Sangheili Zealots": U(
        [M("Sangheili Zealot", (5, 10), ["Storm Rifle", "Plasma Pistol", SANG_CCW], variants=[
            V("Sangheili Zealot with Fuel Rod", ["Fuel Rod", "Plasma Pistol", SANG_CCW], per=5, count=1, cost=10),
            V("Sangheili Zealot with Energy Sword", ["Plasma Pistol", "Energy Sword"], per=5, count=1),
            V("Sangheili Zealot with Plasma Rifles", ["Plasma Rifles", SANG_CCW])])],
        sizes=[5, 10], prices=[125, 250], exact=False, sergeants=["Sangheili Ultra"]),
    "Sangheili Honor Guard": U(
        [M("Sangheili Honor Guard", (3, 3), ["Honor Guard Pike"], gear=["Honor Guard Personal Shield"])],
        sizes=[3], prices=[100]),
    "Jiralhanae Shock Pack": U(
        [M("Jiralhanae Shock Trooper", (4, 8), ["Mangler", "Brute Heavy Melee Weapon"])],
        sizes=[4, 8], prices=[90, 180], exact=False,
        aux=[Pool(entries=["Yanme'e Auxiliary"], per=4, slots=1)]),
    "Jiralhanae Heavy Weapons Pack": U(
        [M("Jiralhanae Gunner", (3, 3), ["Bolt Spiker", "Brute Heavy Melee Weapon"], variants=[
            V("Jiralhanae Gunner with Skewer", ["Skewer", "Brute Heavy Melee Weapon"], cost=10)])],
        sizes=[3], prices=[80], aux=[Pool(lists=["Unggoy", "Yig-Yar", "Yanme'e", "Huragok"], fixed=1)]),
    "Jiralhanae Linebreakers": U(
        [M("Jiralhanae Linebreaker", (4, 4), ["Gravity Hammer"])], sizes=[4], prices=[140],
        sergeants=["Jiralhanae Pack Alpha"], aux=[Pool(lists=["Yig-Yar", "Yanme'e"], fixed=1)]),
    "Jiralhanae Entourage": U(
        [M("Jiralhanae Honor Guard", (2, 2), ["Gravity Hammer", "Mangler"], gear=["Honor Guard Shield"])],
        sizes=[2], prices=[80]),
    "Yig-Yar Corsairs": U(
        [M("Yig-Yar Corsair", (5, 10), ["Plasma Rifle", "Yig-Yar Plasma Sabre"], variants=[
            V("Yig-Yar Corsair with Needler", ["Needler", "Yig-Yar Plasma Sabre"], per=5, count=2)])],
        sizes=[5, 10], prices=[65, 130], sergeants=["Sangheili Ultra", "Yig-Yar Talon"],
        aux=[Pool(entries=["Yanme'e Auxiliary"], per=5, slots=1)]),
    "Yig-Yar Marksmen": U(
        [M("Yig-Yar Marksman", (3, 6), ["Covenant Carbine", "Plasma Pistol", YY_CCW], gear=["Stealth Projector"],
           variants=[V("Yig-Yar Marksman with Needle Rifle", ["Needle Rifle", "Plasma Pistol", YY_CCW]),
                     V("Yig-Yar Marksman with Particle Beam Rifle", ["Particle Beam Rifle", "Plasma Pistol", YY_CCW]),
                     V("Yig-Yar Marksman with Stalker Rifle", ["Stalker Rifle", "Plasma Pistol", YY_CCW])])],
        sizes=[3, 6], prices=[90, 170], exact=False, sergeants=["Yig-Yar Talon", "Sangheili Shadowmaster"]),
    "T'vaoan Butchers": U(
        [M("T'vaoan Butcher", (5, 10), ["Plasma Pistol", "T'vaoan Plasma Sabres"], variants=[
            V("T'vaoan Butcher with Heavy Plasma Melee Weapon", ["Plasma Pistol", "Heavy Plasma Melee Weapon"],
              count=2)])],
        sizes=[5, 10], prices=[65, 120], sergeants=["Yig-Yar Talon", "Jiralhanae Pack Alpha"]),
    "T'vaoan Skirmishers": U(
        [M("T'vaoan Skirmisher (Rifleman)", (6, 6), ["Plasma Rifles", "T'vaoan Plasma Sabres"], variants=[
            V("T'vaoan Skirmisher (Carbine)", ["Covenant Carbine", "Plasma Rifle", "T'vaoan Plasma Sabres"]),
            V("T'vaoan Skirmisher (Storm)", ["Storm Rifle", "Bolt Spiker", "T'vaoan Plasma Sabres"]),
            V("T'vaoan Skirmisher (Repeater)", ["Plasma Repeater", "Spiker", "T'vaoan Plasma Sabres"]),
            V("T'vaoan Skirmisher (Demolitionist)", ["Brute Shot", "Plasma Pistol", "Satchel Charge",
                                                     "T'vaoan Plasma Sabres"]),
            V("T'vaoan Skirmisher (Heavy Gunner, Heavy Plasma)", ["Plasma Rifles", "Heavy Plasma Melee Weapon"]),
            V("T'vaoan Skirmisher (Heavy Gunner, Brute Heavy)", ["Plasma Rifles", "Brute Heavy Melee Weapon"]),
            V("T'vaoan Skirmisher (Melee Specialist)", ["Plasma Rifles", "Energy Sword"]),
            V("T'vaoan Skirmisher (Shield Raider)", ["Plasma Rifle", "T'vaoan Plasma Sabres"], gear=["Wrist Shield"],
              cost=5),
            V("T'vaoan Skirmisher (Needler)", ["Needlers", "T'vaoan Plasma Sabres"], cost=10),
            V("T'vaoan Skirmisher (Anti-armour, Fuel Rod)", ["Fuel Rod", "Plasma Pistol", "T'vaoan Plasma Sabres"],
              cost=10),
            V("T'vaoan Skirmisher (Anti-armour, Skewer)", ["Skewer", "Plasma Pistol", "T'vaoan Plasma Sabres"],
              cost=10),
            V("T'vaoan Skirmisher (Twin-Blade)", ["Plasma Rifles", "Twin-linked Energy Swords"], cost=10)])],
        sizes=[6], prices=[150]),
    "Suicide Grunts": U([M("Suicide Grunt", (5, 10), ["Unstable Plasma Charges"])], sizes=[5, 10], prices=[45, 85],
                        exact=False),
    "Unggoy Heavy Weapons Team": U(
        [M("Unggoy Heavy Weapon Gunner", (3, 6), ["Fuel Rod", "Plasma Pistol", UNG_CCW])],
        sizes=[3, 6], prices=[75, 150], exact=False, sergeants=["Unggoy Ultra", "Sangheili Ultra", "Yig-Yar Talon"]),
    "Unggoy Zealots": U(
        [M("Unggoy Zealot", (10, 20), ["Plasma Pistol", UNG_CCW])], sizes=[10, 20], prices=[60, 115], exact=False,
        sergeants=["Jiralhanae Pack Alpha", "Sangheili Ultra"]),
    "Mgalekgolo Bond-Brother Pair": U(
        [M("Mgalekgolo Hunter", (2, 2), ["Mgalekgolo Assault Cannon", "Shield Bash"], gear=["Combat Shield"])],
        sizes=[2], prices=[200]),
    "Mgalekgolo Assault Pair": U(
        [M("Mgalekgolo Assault Hunter", (2, 2), ["Assault Beam", "Crushing Shield"], gear=["Combat Shield"])],
        sizes=[2], prices=[180]),
    "Mgalekgolo Artillery Pair": U(
        [M("Mgalekgolo Artillery Hunter", (2, 2), ["Heavy Plasma Mortar", "Shield Bash"], gear=["Combat Shield"])],
        sizes=[2], prices=[190]),

    # Mounted and Monster
    "Brute Chopper": U([M("Brute Chopper", (1, 3), ["Bolt Spikers", "Chainwheel"])], sizes=[1, 3], per_model=70),
    "Ghost": S(),
    "Revenant": S(),
    "Spectre": S(),
    "Mgalekgolo Goliath": S(),

    # Vehicles
    "Marauder": S(),
    "Prowler Command Barge": S(),
    "Goblin Battlesuit": S(weapons=["Shardstorm Launcher", "Goblin Grenade Launcher", "Power Wrist", "Furious Feet"],
                           choices=[C("Main weapon", ["Heavy Needle Cannon", "Focus Cannon"])]),
    "Blisterback Siege Crawler": S(),
    "Wraith": S(weapons=["Light Plasma Cannon", "Grav-assisted Ram"], choices=[C("Main weapon", [
        "Heavy Plasma Mortar", "Rapid-fire Fuel Rod Flak Cannons", "Heavy Anti-tank Plasma Cannon"])]),
    "Locust": S(),
    "Banshee": S(),
    "Spirit": S(),
    "Vampire": S(),
    "Seraph": S(),
    "Yig-Yar Raider-Skiff": S(weapons=["Raider-Skiff Blades"], choices=[C("Main weapon", [
        "Heavy Needler", "Twin Plasma Repeaters", "Particle Beam Cannon", "Fuel Rod Bombard"])]),
    "Shadow": S(),
    "Phantom": S(),
    "Scarab": S(),
    "Lich": S(),
    "Kraken": S(),

    # Fortifications
    "Covenant Deployable Turret": S(),
    "Covenant Barricade": S(),
}

# Sergeant and Auxiliary models: added to units, never taken on their own.
MODELS = {
    "Sangheili Ultra": S(weapons=[], choices=[
        C("Ranged weapon", ["Storm Rifle", "Plasma Repeater", "Covenant Carbine", "Needle Rifle", "Particle Beam Rifle",
                            "Stalker Rifle", "Fuel Rod", "2 Plasma Pistols", "2 Plasma Rifles", "2 Needlers"],
          costs={"Fuel Rod": 10, "2 Needlers": 10}),
        C("Sidearm", ["Plasma Pistol"]),
        C("Melee weapon", [SANG_CCW, "Twin-linked Energy Swords"], costs={"Twin-linked Energy Swords": 10})],
        empties=[("2 Plasma Pistols", ["Sidearm"]), ("2 Plasma Rifles", ["Sidearm"]), ("2 Needlers", ["Sidearm"]),
                 ("Twin-linked Energy Swords", ["Ranged weapon", "Sidearm"])]),
    "Sangheili Shadowmaster": S(weapons=[], choices=[
        C("Ranged weapon", ["Plasma Repeater", "2 Plasma Rifles"]),
        C("Sidearm", ["Plasma Pistol"]),
        C("Melee weapon", ["Energy Sword", "Twin-linked Energy Swords"], costs={"Twin-linked Energy Swords": 10})],
        empties=[("2 Plasma Rifles", ["Sidearm"]), ("Twin-linked Energy Swords", ["Ranged weapon", "Sidearm"])]),
    "Jiralhanae Pack Alpha": S(weapons=["Mangler"], choices=[
        C("Ranged weapon", ["Spiker", "Brute Shot"]),
        C("Melee weapon", ["Brute Close Combat Weapon", "Brute Heavy Melee Weapon", "Gravity Hammer"],
          costs={"Gravity Hammer": 10}),
        C("Wargear", ["Officer Shield Generator"], minimum=0, costs={"Officer Shield Generator": 20})],
        empties=[("Gravity Hammer", ["Ranged weapon"])],
        exclude=[("Brute Shot", ["Brute Heavy Melee Weapon"])]),
    "Yig-Yar Talon": S(weapons=[], gear=[], choices=[C("Weapons", [
        "Needler + Wrist Shield + Yig-Yar Plasma Sabre", f"Covenant Carbine + Plasma Pistol + {YY_CCW}",
        f"Needle Rifle + Plasma Pistol + {YY_CCW}", f"Particle Beam Rifle + Plasma Pistol + {YY_CCW}",
        f"Stalker Rifle + Plasma Pistol + {YY_CCW}"])]),
    "Unggoy Ultra": S(weapons=[UNG_CCW], choices=[C("Ranged weapon", [
        "Plasma Rifle", "Needler", "Storm Rifle", "Plasma Repeater", "Fuel Rod"], costs={"Fuel Rod": 10})]),
    "Yanme'e Major": S(),
    # One Auxiliary entry per species. Each model can take one Specialist ability (datasheets.json).
    "Sangheili Auxiliary": S(weapons=[], choices=[
        C("Ranged weapon", ["Storm Rifle", "Covenant Carbine", "Plasma Repeater", "Needler", "Fuel Rod",
                            "2 Plasma Rifles"], costs={"Fuel Rod": 10}),
        C("Sidearm", ["Plasma Pistol"]),
        C("Melee weapon", [SANG_CCW, "Energy Sword", "Twin-linked Energy Swords"],
          costs={"Twin-linked Energy Swords": 10}),
        C("Wargear", ["Stealth Projector"], minimum=0, costs={"Stealth Projector": 5})],
        empties=[("2 Plasma Rifles", ["Sidearm"]), ("Energy Sword", ["Ranged weapon"]),
                 ("Twin-linked Energy Swords", ["Ranged weapon", "Sidearm"])]),
    "Jiralhanae Auxiliary": S(weapons=[], choices=[
        C("Ranged weapon", ["Spiker", "Bolt Spiker", "Brute Shot", "Skewer"], costs={"Skewer": 10}),
        C("Sidearm", ["Mangler"]),
        C("Melee weapon", ["Brute Close Combat Weapon", "Brute Heavy Melee Weapon", "Gravity Hammer"],
          costs={"Gravity Hammer": 10})],
        empties=[("Bolt Spiker", ["Sidearm"]), ("Brute Shot", ["Sidearm"]), ("Skewer", ["Sidearm"]),
                 ("Gravity Hammer", ["Ranged weapon"])],
        exclude=[("Brute Heavy Melee Weapon", ["Spiker"]),
                 ("Bolt Spiker", ["Brute Close Combat Weapon", "Gravity Hammer"]),
                 ("Brute Shot", ["Brute Close Combat Weapon", "Gravity Hammer"]),
                 ("Skewer", ["Brute Close Combat Weapon", "Gravity Hammer"])]),
    "Yig-Yar Auxiliary": S(weapons=[YY_CCW], gear=[], choices=[
        C("Ranged weapon", ["Plasma Rifle", "Needler", "Covenant Carbine", "Needle Rifle", "Particle Beam Rifle",
                            "Stalker Rifle"],
          costs={"Needle Rifle": 10, "Particle Beam Rifle": 10, "Stalker Rifle": 10}),
        C("Wargear", ["Wrist Shield"], minimum=0, costs={"Wrist Shield": 5})],
        exclude=[("Wrist Shield", ["Covenant Carbine", "Needle Rifle", "Particle Beam Rifle", "Stalker Rifle"])]),
    "T'vaoan Auxiliary": S(weapons=[], gear=[], choices=[C("Loadout package", [
        "Rifleman = Plasma Rifles + T'vaoan Plasma Sabres",
        "Carbine = Covenant Carbine + Plasma Rifle + T'vaoan Plasma Sabres",
        "Storm = Storm Rifle + Bolt Spiker + T'vaoan Plasma Sabres",
        "Repeater = Plasma Repeater + Spiker + T'vaoan Plasma Sabres",
        "Demolitionist = Brute Shot + Plasma Pistol + Satchel Charge + T'vaoan Plasma Sabres",
        "Heavy Gunner (Heavy Plasma) = Plasma Rifles + Heavy Plasma Melee Weapon",
        "Heavy Gunner (Brute Heavy) = Plasma Rifles + Brute Heavy Melee Weapon",
        "Melee Specialist = Plasma Rifles + Energy Sword",
        "Tracker = Storm Rifle + Plasma Pistol + Yig-Yar Plasma Sabre",
        "Shield Raider = Plasma Rifle + Wrist Shield + T'vaoan Plasma Sabres",
        "Needler = Needlers + T'vaoan Plasma Sabres",
        "Anti-armour (Fuel Rod) = Fuel Rod + Plasma Pistol + T'vaoan Plasma Sabres",
        "Anti-armour (Skewer) = Skewer + Plasma Pistol + T'vaoan Plasma Sabres",
        "Twin-Blade = Plasma Rifles + Twin-linked Energy Swords"],
        costs={"Shield Raider = Plasma Rifle + Wrist Shield + T'vaoan Plasma Sabres": 5,
               "Needler = Needlers + T'vaoan Plasma Sabres": 10,
               "Anti-armour (Fuel Rod) = Fuel Rod + Plasma Pistol + T'vaoan Plasma Sabres": 10,
               "Anti-armour (Skewer) = Skewer + Plasma Pistol + T'vaoan Plasma Sabres": 10,
               "Twin-Blade = Plasma Rifles + Twin-linked Energy Swords": 10})]),
    "Unggoy Auxiliary": S(weapons=[], choices=[
        C("Ranged weapon", ["Plasma Pistol", "Plasma Rifle", "Needler", "Storm Rifle", "Fuel Rod"], costs={"Fuel Rod": 10}),
        C("Melee weapon", [UNG_CCW])]),
    "Huragok Auxiliary": S(),
    "Yanme'e Auxiliary": S(),
}

# The codex's Auxiliary lists, by the keyword on each Auxiliary entry.
AUX_LISTS = ["Sangheili", "Jiralhanae", "Yig-Yar", "Unggoy", "Huragok", "Yanme'e"]  # T'vaoan are also Yig-Yar
