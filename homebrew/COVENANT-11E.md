# Covenant 11th-edition homebrew

`Xenos - Covenant (Homebrew).json` is built from Codex: Covenant v5.5.0. Caste Hierarchy is the revised
version in `homebrew/covenant-source/army_rules.md`. Shielding Trait is as printed (SP on each model, a 3+
Shield Save after a failed saving throw), except that Regenerating Shields gives each unit D3 lost SP (D3+1 for
Vehicle and Mounted units) to split between its models, instead of D3 for every model. Everything else is as
printed in the codex. The layout follows the Emperor's Children and Skaven catalogues.

## What New Recruit shows

- 65 datasheets: 7 Epic Heroes, 10 Characters, 4 Battleline, 21 Infantry, 4 Mounted, 1 Monster,
  16 Vehicles and 2 Fortifications. The 6 Sergeant and 7 Auxiliary entries are models added inside units;
  they are not units of their own.
- **Squads** use real model counters. Weapon swaps are their own model types beside the plain model, as on
  the Emperor's Children Tormentors (e.g. "Unggoy Warrior with Needler"). Limits such as "for every 5
  models, 1 can..." scale with the unit size; model types that share one limit (Plasma Rifle or Needler)
  count together. Paid swaps add their points. New Recruit shows an error for an illegal unit size.
- **Sergeant**: an optional group listing the Sergeant entries the datasheet allows. Each Sergeant keeps
  its own loadout choices and Caste Doctrines.
- **Auxiliary**: one entry per species (revision 3): Sangheili, Jiralhanae, Yig-Yar, T'vaoan, Unggoy, Huragok
  and Yanme'e. The unit's group lists the species its datasheet allows (T'vaoan have the Yig-Yar keyword, so
  they appear wherever Yig-Yar do). The allowance is shown in "Auxiliary Slots": for example a Grunt Cadre
  gets 2 slots for every 5 Unggoy Warriors, a Sangheili or Jiralhanae model uses 2 and a Yig-Yar or T'vaoan
  model 1. Fixed allowances (Special Operations Team: 5 Sangheili) are flat.
- **Auxiliary options**: each Auxiliary has its weapon options (the old specialists' loadouts) and a
  "Specialist ability" group: one ability per model, at the points shown.

  | Auxiliary | Pts | Specialist abilities |
  |---|---|---|
  | Sangheili | 20 | Forward Operative +10, Vengeful Pursuit +10, Remote Destructive Device +10 |
  | Jiralhanae | 20 | Pack Enforcer free, Sworn Protector (with Personal Shield Generator, SP 3) +15, Stalking Predator +10 |
  | Yig-Yar | 10 | Mark the Target +10, Spotter's Nest +15, Trailblazer +10 |
  | T'vaoan | 20 | Trailblazer +10, Break from the Pack +10 |
  | Unggoy | 15 | Ammunition Runner free, Forward Infiltration +10, Proximity Detonation +5 |
  | Huragok | 25 | Biological Restoration free, Shield Maintenance +5 |
  | Yanme'e | 20 | none to choose: Targeting Relay and Scouts 8" are built in |

  Proximity Detonation replaces all of the Unggoy's weapons with Unstable Plasma Charges: taking it empties the
  Weapons group, and New Recruit shows an error until the other weapon is removed. A Yig-Yar with a Covenant
  Carbine, Needle Rifle, Particle Beam Rifle or Stalker Rifle cannot take a Wrist Shield (New Recruit shows an
  error). The T'vaoan's loadout packages are the Skirmisher's, plus the Tracker's Storm Rifle, Plasma Pistol and
  Yig-Yar Plasma Sabre.
- **Shields**: a "Shields" table shows SP on the wargear that gives it (e.g. "Sangheili Personal Shield: 2",
  "Wrist Shield: 6") or on the model when no wargear does (vehicles).
- Wargear that gives an invulnerable save (Combat Shield, Layered Colony Armour) sets it on the stat line.
- Leaders attach with New Recruit's Leading links, from each datasheet's LEADER list. Shipmaster and
  Fieldmaster can add their Ultra, up to 3 Sangheili Warriors and up to 2 Unggoy Auxiliaries.
- Copy limits: Epic Heroes 1, Battleline 6, others 3. Every CHARACTER has a Warlord option.
- Chosen of the Hierarchs (army rule, as EC's Sublime Strategist): +1CP at the start of each battle round if your
  Warlord has it. On the three Prophets, Thel 'Vadam, Rtas 'Vadum, Tartarus, the Shipmaster, Fieldmaster,
  Jiralhanae Chieftain and Yig-Yar Corsair-Talon.
- Rtas 'Vadum's Fleetmaster no longer gains CP: after both players have deployed, select up to two friendly
  Covenant units, excluding Fortifications; redeploy them, or place any of them into Strategic Reserves.
- Faction icon: `icons/armies/xenos-covenant-homebrew.png`, the Covenant symbol as a black silhouette on a
  transparent background, like New Recruit's own faction symbols. Replace the file (same name,
  PNG or SVG) to use another image.
- Army Rules and References: Caste Hierarchy, Shielding Trait, Chosen of the Hierarchs, Caste Doctrines, Supercombine, Plasma,
  Siegebreaker and Wargear Costs. Weapons link Supercombine, Plasma and Siegebreaker, and the core rules.
- 18 detachments with their DP and Force Disposition (see the detachments below). None is Unique.
  Enhancements appear only on eligible units of the chosen detachment; Upgrades that up to three units can
  take share one Enhancement selection. An Attached Unit can have only one Enhancement or Upgrade.
  Stratagem References follows the chosen detachments.

## 11th-edition wording (revision 5)

`homebrew/covenant-tools/wording_11e.py` rewrote the rules text in 11th-edition terms and removed sentences that only
repeated another rule (12,812 -> 11,916 words in datasheets and detachments, plus the army rules page):

- 11e terms: hit/wound/charge/advance rolls, critical hits, normal/advance/fall-back/charge/surge moves, engaged and
  unengaged, battle-shock rolls, save rolls, below starting strength, A/S/AP/D/OC/Ld/M/Sv characteristics, inches as ".
  Weapon abilities in prose are in brackets ([PRECISION]) and keywords in capitals (COVENANT INFANTRY unit).
- Removed as repeats: the Upgrade limit on every Upgrade (11e lets you take up to three of the same Upgrade); the
  Stealth Projector note (11e Stealth already needs every model); the Shield regeneration line on 11 vehicles (the army
  rule already gives VEHICLE and MOUNTED units D3+1); "these effects cease when this model is destroyed"; a
  once-per-phase limit on a Stratagem; "automatically successful hit rolls cannot trigger this"; "does not prevent
  another unit from using the same Doctrine".
- Rewritten by hand: Fanatical Doctrines and Devoted Sergeants (The Great Journey), Integrated Battle Groups, Scuttle to
  Cover (once per battle round for each YIG-YAR unit, as its last sentence said), Honour Duel, and the army rules page
  (Caste Hierarchy, Shielding Trait without the repeated Shielding Sequence and Empty Shields, Plasma, Siegebreaker,
  Supercombine as "1 mortal wound", Wargear Costs in one sentence).
- Every Upgrade can now be taken by up to three units, as 11e allows. Thirteen Upgrades that did not say "up to three"
  were limited to one before.

## Detachments (revision 12)

18 detachments, none Unique. Species detachments have a rule for the unit keyword (ELITE, BRUTE, GRUNT, JACKAL, DRONE,
HUNTER, ENGINEER) and one for the species keyword, which also reaches that species' Sergeants and Auxiliaries in
other units; where the species has Sergeants, that rule changes how they issue Doctrines.

| DP | Detachment | Disposition | Core of the rules |
|---|---|---|---|
| 3 | The Great Journey | Take and Hold | Fanatical Doctrines from SAN'SHYUUM; GRUNT units shoot and charge after advancing |
| 2 | Fleetborne Invasion | Take and Hold | Assault Disembark from Spirits, Phantoms and Liches; +1 OC near a vessel |
| 2 | Sangheili Warhost | Priority Assets | Worthy Foe (+1 to wound); SANGHEILI Doctrines last the turn |
| 2 | Jiralhanae Warpack | Purge the Foe | +1 A after a charge; JIRALHANAE Sergeants issue a Doctrine in each player's turn |
| 2 | Covenant Expeditionary Force | Priority Assets | Sergeants issue the Doctrines of every species in their unit; infantry and vehicles within 6" re-roll hit rolls of 1 |
| 2 | Armored Spearhead | Purge the Foe | VEHICLE Plasma weapons score critical hits on 5+; shoot after advancing or falling back; +1 SP regeneration |
| 2 | Swords of Sanghelios | Take and Hold | No JIRALHANAE or SAN'SHYUUM models; ELITE re-roll hit and wound rolls of 1; GRUNT near ELITE re-roll hit rolls of 1, +1 OC |
| 1 | Yig-Yar Hunting Talon | Reconnaissance | JACKAL re-roll hit rolls against units below starting strength; Talons issue two Doctrines at once |
| 1 | Drone Hive Swarm | Reconnaissance | DRONE units shoot and charge after advancing or falling back; a Major's Doctrine also reaches another DRONE unit |
| 1 | Bonded Colony | Priority Assets | HUNTER models regain D3 wounds each Command phase; MGALEKGOLO re-roll wound rolls of 1 against VEHICLES and MONSTERS |
| 1 | Engineer Reclamation Detail | Take and Hold | Repair and Refit restores infantry shields; +1 SP regeneration within 3" of a HURAGOK |
| 1 | Grunt Levy | Take and Hold | +1 A for GRUNT units of 10+ models; Unggoy Sergeants' Doctrines reach GRUNT units within 6" |
| 1 | Siege Engines | Disruption | WALKERS shoot and charge after advancing, cross terrain up to 4", [IGNORES COVER] |
| 1 | Engines of Purification | Purge the Foe | TITANIC models ignore the Damaged penalty and re-roll hit rolls of 1; +D3 SP regeneration |
| 1 | Special Operations | Disruption | Spec Ops units have Stealth and issue Special Operations Doctrines to themselves |
| 1 | Hierarchs' Court | Priority Assets | +3" to SAN'SHYUUM abilities; HONOR GUARD and ENTOURAGE with a CHARACTER get +1 A and Feel No Pain 5+ |
| 1 | Fleet Aviation | Purge the Foe | Banshees, Vampires and Seraphs re-roll hit rolls of 1 (all hit rolls against FLY) and move 6" after shooting |
| 1 | Ghost Lances | Reconnaissance | MOUNTED units shoot and charge after advancing or falling back; mortal wounds after a charge |

- Swords of Sanghelios: New Recruit shows an error on each JIRALHANAE or SAN'SHYUUM unit, Sergeant or Auxiliary.
- Upgrades that name unit types (VEHICLE, WALKER, TITANIC with Shields, Banshee/Vampire/Seraph, SPECIAL OPERATIONS,
  RANGER or ASSASSIN INFANTRY...) carry an `eligible` rule in `detachments.json`: `all` keywords, `any` keywords,
  datasheet `names` and `sp` (needs Shields). Upgrades never go on CHARACTER, Sergeant or Auxiliary entries.
- Enhancements without a restriction fit any CHARACTER that is not an Epic Hero.

## Detachment overhaul (revision 11)

Four detachments are kept and rewritten: The Great Journey, Fleetborne Invasion, the Sangheili Warhost and the
Jiralhanae Warpack. The other eight (Covenant Expeditionary Force, Yig-Yar Hunting Talon, Shadow Cell, Armored
Spearhead, Grunt Levy, Drone Hive Swarm, Bonded Colony, Engineer Reclamation Detail) are removed. Each species
detachment has a rule for its unit keyword and one for its species keyword, which also reaches that species'
Sergeants and Auxiliaries in other units, including a change to how that species' Sergeants issue Doctrines.

- **The Great Journey (3DP, GRUNT, Take and Hold).** Fanatical Doctrines: once per turn each SAN'SHYUUM model gives
  one COVENANT INFANTRY unit within 6" a Fanatical Doctrine until the end of the turn (Shielded by Faith 4+
  invulnerable save, Claim the Sacred Path +2 OC, Wrath of the Prophets [SUSTAINED HITS 1]; Armour of the Faithful
  is gone). Fevered Pilgrimage: GRUNT units can shoot and charge after advancing. Devoted: UNGGOY Sergeants issue a
  Fanatical Doctrine each battle round as well as their Caste Doctrine. The Stratagems target GRUNT units instead of
  units affected by a Fanatical Doctrine; Martyr's Zeal replaces the Fevered Pilgrimage Stratagem. 3DP needs Strike
  Force (Incursion gives 2DP).
- **Fleetborne Invasion (2DP, Take and Hold).** Invasion Vessels are the Spirit, Phantom and Lich (not the Kraken).
  Drop Assault: units disembarking from a vessel that did not arrive from reserves this turn can make an Assault
  Disembark move (11e core 18.06) and still charge. Beachhead: +1 OC for COVENANT INFANTRY within 6" of a vessel,
  replacing Landing Force. New Stratagems: Hot Drop (2CP, Assault Disembark on the turn of arrival),
  Gravity-Lift Insertion (Shock Disembark after the vessel advanced) and Strafing Run (six D6, twelve for a Lich,
  a mortal wound on each 4+ against a unit the vessel moved over). Cut: Orbital Descent Vector (the datasheets'
  Rapid Aerial Insertion already does it), Launch the Second Wave, Renewed Glassing Authorisation, Fleet Command
  Network, and three of the seven Enhancements.
- **Sangheili Warhost (2DP, ELITE, Priority Assets).** Worthy Foe: one enemy unit each battle round, +1 to wound for
  ELITE units against it. Shields of the Sangheili: SANGHEILI models re-roll a Shield Save of 1, units with SANGHEILI
  models add 1 to battle-shock rolls, and Doctrines issued by SANGHEILI Sergeants last until the end of the turn.
  Exultant and Honour-Bound Veterans are gone. Enhancements: Blade of the Kaidon, Mark of Glory (1CP when the
  bearer's unit destroys the Worthy Foe), Kaidon's Shield Generator, Hunter's Eye.
- **Jiralhanae Warpack (2DP, BRUTE, Purge the Foe).** Bloodlust: +1 A on melee weapons after a charge move. Pack
  Dominance: units with JIRALHANAE models re-roll charge rolls, and JIRALHANAE Sergeants issue a Doctrine in each
  player's turn. Pack Encirclement is gone. Pin the Prey is 2CP; Hold Them Fast forces a Desperate Escape test.
- Enhancement restrictions read "SANGHEILI model only", "SAN'SHYUUM or UNGGOY model only" or name a datasheet
  ("Sangheili Shipmaster model only"); they go on CHARACTERS that are not Epic Heroes.

## Keywords (revision 10)

- As in the core rules (02.05.01), a unit has the keywords of all its models, Sergeants and Auxiliaries included: a
  Sangheili Warrior Cadre with an Unggoy Auxiliary is also an UNGGOY unit. New Recruit adds the species keyword to the
  unit while it includes such a model.
- Each species' own datasheets also have a unit keyword that their Sergeant and Auxiliary models do not: GRUNT
  (Unggoy), ELITE (Sangheili), BRUTE (Jiralhanae), JACKAL (Yig-Yar and T'vaoan), DRONE (Yanme'e), HUNTER (Mgalekgolo)
  and ENGINEER (Huragok), the names the detachments' Unique tags use. BRUTE was taken off the Pack Alpha and the
  Jiralhanae Auxiliary. The Goblin Battlesuit (UNGGOY) is GRUNT and the Yig-Yar Raider-Skiff is JACKAL.
- Rules that target a species' units use its unit keyword: the detachment rules for ELITE, BRUTE and GRUNT units, the
  Unggoy Deacon's Voice of the Deacon and Religious Authority (GRUNT), Consecrated War Harnesses (GRUNT), the
  Raider-Skiff's Raider Extraction (JACKAL) and the Yanme'e Major's Control Node (DRONE). Rules about models ("each
  SANGHEILI model") keep the species keyword.

## Sergeant and Auxiliary weapons (revision 8)

Sergeants and Auxiliaries pick their weapons one slot at a time, as the Emperor's Children Obsessionist ("Melee weapon",
"Sidearm"): "Ranged weapon", "Sidearm", "Melee weapon" and "Wargear", one weapon per option. Weapons that never change
are fixed (the Pack Alpha's Mangler, the Unggoy Ultra's Close Combat Weapon).

- Swaps that replace more than one weapon follow the codex: 2 Plasma Pistols, 2 Plasma Rifles or 2 Needlers replace the
  Plasma Pistol too; Twin-linked Energy Swords replace every weapon; an Energy Sword (Sangheili Auxiliary) replaces the
  Storm Rifle; a Gravity Hammer replaces the Spiker; a Bolt Spiker, Brute Shot or Skewer (Jiralhanae Auxiliary) replaces
  the Mangler and needs a Brute Heavy Melee Weapon. Taking one empties the slot it replaces, and New Recruit shows an
  error until that weapon is removed.
- Pairings the codex does not allow show an error, e.g. a Pack Alpha's Brute Shot with a Brute Heavy Melee Weapon.
- The Yig-Yar Talon's swap replaces all three items at once, so it stays one list ("Covenant Carbine, Plasma Pistol and
  Yig-Yar Close Combat Weapon"). The T'vaoan Auxiliary's packages, which cannot be combined, use the codex names
  (Rifleman, Carbine, Demolitionist, Shield Raider, Twin-Blade...).
- Combined names read "A, B and C" everywhere.
- In the Tormentor layout, each legal combination is one Auxiliary model type.

## Tormentor layout (revision 7, Jiralhanae Assault Pack)

The Jiralhanae Assault Pack is laid out like the Emperor's Children Tormentors (`TORMENTOR_STYLE` in
`covenant_build.py`):

1. The Sergeant sits at the top, as the Obsessionist: one choice, Jiralhanae Pack Alpha or Sangheili Ultra, and its
   weapon choices open underneath. Ticking the other replaces it.
2. The Jiralhanae Warrior counters, with the Bolt Spiker, Brute Shot and Skewer model types, as before.
3. Auxiliary models are counters too, one model type per loadout, as "Tormentor with Meltagun": Unggoy Auxiliary
   (Plasma Pistol), with Plasma Rifle, Needler, Storm Rifle, Fuel Rod (+10) or Proximity Detonation (+5, replaces
   its weapons). Each goes up to 1 per 4 Warriors, and the Auxiliary Slots total still applies.
4. Specialist abilities that do not replace weapons (Ammunition Runner, Forward Infiltration +10) are at the bottom,
   as the Icon of Excess: set how many, then pick which Auxiliary model carries each one.

New Recruit shows a model with choices as a "+" button (each one configured separately) and a fixed-loadout model as
a counter, so the counters need one model type per loadout.

## House weapon standard (revision 6)

Weapons follow `homebrew/house_dice.py`, the 11e codex style also used for Skaven and Black-Flag: D6 damage becomes
D3+X and random attacks become fixed, with [BLAST 1] or [BLAST 2].

| Weapon | Was | Now |
|---|---|---|
| Fuel Rod (S10) | D D6 | D D3+2 |
| Fuel Rod Cannon Array (S12) | D D6 | D D3+3 |
| Focus Cannon | D D6+2 | D D3+4 |
| Heavy Anti-tank Plasma Cannon (S16) | D D6+2 | D D3+6 |
| Emim-pattern Focus Beam (S18) | D D6+4, Plasma (D6) | D D3+8, Plasma (D3+2) |
| Light Plasma Mortar | A D6+1, Blast | A4, Blast 1 |
| Heavy Plasma Mortar (Mgalekgolo / Wraith) | A D6+2 / D6+3, Blast | A5 Blast 1 / A6 Blast 2 |
| Fuel Rod Bombard, Goblin Grenade Launcher | A D6+2, Blast | A5, Blast 1 |
| Mgalekgolo Assault Cannon | A D3+2, Blast | A4, Blast 1 |
| Plasma Charge, Ultra-heavy Plasma Cannon | A D6+3, Blast | A6, Blast 2 |
| Annihilator Siege Missile Battery, Shardstorm Launcher | A D6+6, Blast | A9, Blast 2 |
| Plasma Beam (Scarab) | A D3+1 | A3 |

## Choices made where the codex is open

- Sergeants are optional (0-1). "Add 1 model from the ... Auxiliary lists" is up to 1.
- "Add up to N additional models - X pts" adds X points for any number of extra models; "Add N additional
  models - X pts" (no "up to") allows only the two sizes.
- Marauders' Wrist Shields are counted on the unit ("3x Wrist Shield", +5 pts each, not on Carbine models).
- T'vaoan Skirmishers pick their loadout package as a model type for each model.
- A Plasma Rifle swapped onto Special Operations Team and T'vaoan models uses the Sangheili BS 3+ profile.
- Sworn Protector's "A unit cannot contain more than one Jiralhanae Bodyguard" now reads "more than one model with
  this ability".

## Open points in the codex text

- **Gravity Slam** and **Conversion Beam** are weapon abilities with no definition in v5.5.0; they are shown
  on the weapons but not linked to a rule.

## Rebuild and check

```sh
python3 homebrew/covenant_build.py --source homebrew/covenant-source --system 'Warhammer 40,000.json' \
  --output 'Xenos - Covenant (Homebrew).json'
python3 homebrew/covenant_validate.py --source homebrew/covenant-source --catalogue 'Xenos - Covenant (Homebrew).json'
```

The source JSON was extracted from the codex PDF with the scripts in `homebrew/covenant-tools/`
(`extract_pages.py` and `extract_dets.py` read the PDF, `parse_datasheets.py` and `parse_dets.py` structure it,
`finalize.py` writes the source files). The PDF itself is not kept in the repository.
