"""Model and wargear layout for every Skaven datasheet.

The handoff gives profiles, weapons and abilities in datasheets.json, but
wargear options only as prose. This table turns that prose into New Recruit
models and choices. Weapon names must match datasheets.json exactly.

M(...)  a model type in the unit: name, (min, max), fixed weapons, choices.
C(...)  a choice group. Options are weapon names; "A + B" takes both.
        unit_max limits an option across the whole unit as (small, large).
Sizes   one dict per legal unit size (model name -> count), with matching points.
"""


def M(name, count, weapons=(), choices=(), profile="main", cost=0, wounds=None):
    return dict(name=name, count=count, weapons=list(weapons), choices=list(choices), profile=profile,
                cost=cost, wounds=wounds)


def C(label, options, minimum=1, maximum=1, unit_max=None, option_max=None, scale=None):
    return dict(label=label, options=list(options), min=minimum, max=maximum, unit_max=unit_max or {},
                option_max=option_max, scale=scale)


def single(**extra):
    """A one-model datasheet: every weapon on the datasheet is equipped."""
    return dict(single=True, **extra)


MOUNTS = {
    "Grey Seer": dict(profile="SCREAMING BELL", label="Screaming Bell", cost=120, repeat=10,
                      weapons=["Crushing Bell", "Rat Ogor claws", "Attendant weapons"]),
    "Warlord": dict(profile="GNAW-BEAST", label="Gnaw-beast", cost=65, repeat=10, weapons=["Gnaw-beast claws"]),
    "Plague Priest": dict(profile="PLAGUE FURNACE", label="Plague Furnace", cost=120, repeat=10,
                          weapons=["Great Censer", "Rat Ogor claws", "Attendant weapons"]),
}

STORMFIEND_ROLES = [
    ("Stormfiend (gauntlets)", ["Doom-Flayer gauntlets", "Shock gauntlets"]),
    ("Stormfiend (grinderfists or ratling cannons)", ["Grinderfists", "Ratling cannons"]),
    ("Stormfiend (warpfire projectors or windlaunchers)", ["Warpfire projectors", "Windlaunchers"]),
]

UNITS = {
    # Epic Heroes, characters, monsters and vehicles: one model, all weapons.
    "Thanquol and Boneripper": single(),
    "Queek Headtaker": single(),
    "Ikit Claw": single(),
    "Deathmaster Snikch": single(),
    "Lord Skrolk": single(),
    "Throt the Unclean": single(),
    "Lord Skreech Verminking": single(),
    "Grey Seer": single(weapons=["Warp bolts", "Grey Seer staff"]),
    "Warlord": single(weapons=["Warplock pistol"],
                      choices=[C("Melee weapon", ["Warpstone blade", "Shock halberd"])]),
    "Deathmaster": single(),
    "Plague Priest": single(weapons=["Pox blast", "Plague staff"]),
    "Warlock Engineer": single(),
    "Master Moulder": single(),
    "Verminlord Warbringer": single(),
    "Verminlord Warpseer": single(),
    "Verminlord Deceiver": single(),
    "Verminlord Corruptor": single(),
    "Clattertank": single(),
    "Warp-Grinder Team": single(),
    "Mutant Rat Ogor": single(),
    "Brood Horror": single(),
    "Hell Pit Abomination": single(),
    "Verminwyrm": single(),
    "Brood Terror": single(),
    "Doomwheel": single(),
    "Eshin Nightstrider": single(),
    "Warp Lightning Cannon": single(),
    "Plagueclaw Catapult": single(),
    "Ratling Warpblaster": single(),
    "Warp-Doom Magma Cannon": single(),
    "Cauldron of a Thousand Poxes": single(),
    "Warpclaw Battle Tank": single(),
    "Doomgrinder Siege Tank": single(),
    "Warpstone Harvester": single(),
    "Gnawdrill Excavator": single(),
    "Vermindoom Land-Fortress": single(
        weapons=["Warp-zap annihilator", "Grinding ram"],
        choices=[C("Jury-rigged hardpoints", ["Ratling battery", "Warpfire projector", "Warp-melta cannon",
                                              "Warp-lightning coil"], minimum=6, maximum=6, option_max=2)]),

    # Squads
    "Skavenslaves": dict(
        models=[M("Skavenslave", (20, 40), ["Skavenslave blades"])],
        sizes=[{"Skavenslave": 20}, {"Skavenslave": 30}, {"Skavenslave": 40}],
        unit_choices=[C("Explosive Collars", ["Explosive Collars"], minimum=0)]),
    "Clanrats": dict(
        models=[M("Clawleader", (1, 2), ["Clawleader blade"]), M("Clanrat", (9, 18))],
        sizes=[{"Clawleader": 1, "Clanrat": 9}, {"Clawleader": 2, "Clanrat": 18}],
        unit_choices=[
            C("Loadout", ["Sword and Board", "Warplock"]),
            C("Clan Standard or Scavenger Bell", ["Clan Standard", "Scavenger Bell"], minimum=0)],
        loadouts={
            "Sword and Board": dict(weapons=["Stubber pistol"], gear=["Shield"],
                                    choices=[C("Clanrat weapon", ["Clanrat blade", "Clanrat mace",
                                                                  "Clanrat spear"])]),
            "Warplock": dict(weapons=["Warplock carbine", "Clanrat blade", "Stubber pistol"]),
        },
        weapon_teams=[("Ratling Gun Team", "Ratling Gun Teams", ["Ratling gun", "Crew blades"], 35),
                      ("Warpfire Thrower Team", "Warpfire Thrower Teams", ["Warpfire thrower", "Crew blades"], 40),
                      ("Poison Wind Globadier", "Skryre Acolytes", ["Poison-wind globes", "Acolyte blades"], 12)]),
    "Stormvermin": dict(
        models=[M("Fangleader", (1, 1), wounds="2", choices=[
                    C("Weapons", ["Master-forged storm-glaive", "Master-forged stormblade + Heavy shield"]),
                    C("Pistol", ["Warplock pistol"], minimum=0)]),
                M("Stormvermin", (9, 9), choices=[
                    C("Weapons", ["Storm-glaive", "Stormblade + Heavy shield", "Heavy shock weapon"],
                      unit_max={"Heavy shock weapon": (1, 1)})])],
        sizes=[{"Fangleader": 1, "Stormvermin": 9}],
        unit_choices=[C("Warhorn or Regimental Banner", ["Warhorn", "Regimental Banner"], minimum=0)]),
    "Warp-Zap Stormvermin": dict(
        models=[M("Fangleader", (1, 1), wounds="2", choices=[
                    C("Ranged weapon", ["Heavy Warp-Zapper", "Long-barrel Warp-Zapper", "Warp-zap pistol"]),
                    C("Melee weapon", ["Fangleader blade", "Shock halberd"])]),
                M("Warp-Zap Stormvermin", (4, 9), ["Stormvermin sidearm blades"], choices=[
                    C("Ranged weapon", ["Heavy Warp-Zapper", "Long-barrel Warp-Zapper"],
                      unit_max={"Long-barrel Warp-Zapper": (1, 2)})])],
        sizes=[{"Fangleader": 1, "Warp-Zap Stormvermin": 4}, {"Fangleader": 1, "Warp-Zap Stormvermin": 9}],
        unit_choices=[C("Grounding Rod or Spare Capacitor", ["Grounding Rod", "Spare Capacitor"], minimum=0)]),
    "Warpclad Warpack": dict(
        models=[M("Fangleader", (1, 1), wounds="3", choices=[
                    C("Ranged weapon", ["Warp-disintegrator", "Warp-blaster"]),
                    C("Melee weapon", ["Warp-glaive", "Master-forged warp-glaive", "Shock gauntlet"])]),
                M("Warpclad", (9, 9), ["Warp-disintegrator", "Warp-glaive"])],
        sizes=[{"Fangleader": 1, "Warpclad": 9}]),
    "Plague Monks": dict(
        models=[M("Plague Deacon", (1, 1), ["Deacon blade"]),
                M("Plague Monk", (9, 19), choices=[
                    C("Weapon", ["Twin foetid blades", "Plague staff"], unit_max={"Plague staff": (2, 2)})])],
        sizes=[{"Plague Deacon": 1, "Plague Monk": 9}, {"Plague Deacon": 1, "Plague Monk": 19}],
        unit_choices=[C("Plague Banner", ["Plague Banner"], minimum=0, scale=(1, 2)),
                      C("Doom Gong", ["Doom Gong"], minimum=0, scale=(1, 2))]),
    "Plague Censer Bearers": dict(
        models=[M("Censer-bearer Leader", (1, 1), ["Censer-bearer leader weapon"]),
                M("Plague Censer Bearer", (4, 9), ["Great plague censer"])],
        sizes=[{"Censer-bearer Leader": 1, "Plague Censer Bearer": 4},
               {"Censer-bearer Leader": 1, "Plague Censer Bearer": 9}]),
    "Pusbags": dict(models=[M("Pusbag", (10, 20), ["Diseased bites"])],
                    sizes=[{"Pusbag": 10}, {"Pusbag": 20}]),
    "Night Runners": dict(
        models=[M("Night Runner", (10, 20), ["Eshin blade"], choices=[
            C("Ranged weapon", ["Eshin shuriken", "Eshin sling", "Poisoned shuriken"],
              unit_max={"Poisoned shuriken": (1, 2)})])],
        sizes=[{"Night Runner": 10}, {"Night Runner": 20}]),
    "Gutter Runners": dict(
        models=[M("Gutter Runner", (5, 10), ["Twin Eshin blades"], choices=[
            C("Ranged weapon", ["Warpstar repeater", "Poisoned shuriken", "Eshin sling"])])],
        sizes=[{"Gutter Runner": 5}, {"Gutter Runner": 10}]),
    "Eshin Shadowriggers": dict(
        models=[M("Eshin Shadowrigger", (5, 5), ["Warp-needle pistol", "Servo-assisted Eshin blades"])],
        sizes=[{"Eshin Shadowrigger": 5}]),
    "Ratling Gun Teams": dict(models=[
        M("Lead Gunner", (1, 1), ["Ratling gun", "Crew-leader blades"], choices=[C("Pistol", ["Warplock pistol"], minimum=0)], cost=35, wounds="3"),
        M("Ratling Gun Team", (0, 2), ["Ratling gun", "Crew blades"], cost=35)]),
    "Warpfire Thrower Teams": dict(models=[
        M("Lead Burner", (1, 1), ["Warpfire thrower", "Crew-leader blades"], choices=[C("Pistol", ["Warplock pistol"], minimum=0)], cost=40, wounds="3"),
        M("Warpfire Thrower Team", (0, 2), ["Warpfire thrower", "Crew blades"], cost=40)]),
    "Warpvolt Scourger Teams": dict(models=[
        M("Lead Scourger", (1, 1), ["Warpvolt scourger", "Crew-leader blades"], choices=[C("Pistol", ["Warplock pistol"], minimum=0)], cost=50, wounds="3"),
        M("Warpvolt Scourger Team", (0, 2), ["Warpvolt scourger", "Crew blades"], cost=50)]),
    "Skryre Acolytes": dict(
        models=[M("Bombardier", (1, 1), ["Poison-wind globes", "Bombardier blade"], wounds="2",
                  choices=[C("Pistol", ["Warplock pistol"], minimum=0)]),
                M("Poison Wind Globadier", (4, 9), ["Acolyte blades"], choices=[
                    C("Ranged weapon", ["Poison-wind globes", "Death globe", "Poison-wind mortar"],
                      unit_max={"Death globe": (1, 2), "Poison-wind mortar": (1, 2)})])],
        sizes=[{"Bombardier": 1, "Poison Wind Globadier": 4}, {"Bombardier": 1, "Poison Wind Globadier": 9}]),
    "Warplock Jezzails": dict(
        models=[M("Warplock Jezzail Team", (3, 6), ["Warplock jezzail", "Crew blades"])],
        sizes=[{"Warplock Jezzail Team": 3}, {"Warplock Jezzail Team": 6}]),
    "Doom-Flayers": dict(models=[M("Doom-Flayer", (2, 6), ["Doom-Flayer blades", "Crew blades"], cost=35)]),
    "Rat Ogors": dict(
        models=[M("Rat Ogor", (3, 6), ["Rat Ogor claws"]),
                M("Packmaster", (1, 2), ["Pack whip"], profile="PACKMASTER")],
        sizes=[{"Rat Ogor": 3, "Packmaster": 1}, {"Rat Ogor": 6, "Packmaster": 2}]),
    "Vermadillos": dict(
        models=[M("Vermadillo", (3, 6), ["Warp-hardened Claws", "Crushing Roll"])],
        sizes=[{"Vermadillo": 3}, {"Vermadillo": 6}]),
    "Stormfiends": dict(
        models=[M(name, (1, 2), ["Crushing fists"], choices=[C("Weapons", options)])
                for name, options in STORMFIEND_ROLES],
        sizes=[{name: 1 for name, _ in STORMFIEND_ROLES}, {name: 2 for name, _ in STORMFIEND_ROLES}]),
    "Wolf Rats": dict(
        models=[M("Wolf Rat", (5, 10), ["Warp-fanged bites"]),
                M("Packmaster", (1, 1), ["Pack whip"], profile="PACKMASTER")],
        sizes=[{"Wolf Rat": 5, "Packmaster": 1}, {"Wolf Rat": 10, "Packmaster": 1}]),
    "Rat Packs": dict(
        models=[M("Rat Pack swarm base", (1, 3), ["Seething tide"]),
                M("Packmaster", (1, 1), ["Pack whip"], profile="PACKMASTER")],
        sizes=[{"Rat Pack swarm base": n, "Packmaster": 1} for n in (1, 2, 3)]),
}
