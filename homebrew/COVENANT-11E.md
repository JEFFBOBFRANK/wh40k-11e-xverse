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
- 12 detachments with their DP and Force Disposition. "KEYWORD: X" in the codex is Unique: only one
  detachment with the same keyword (e.g. The Great Journey and Grunt Levy, both Grunt) can be taken.
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

1. The Sergeant sits at the top, as the Obsessionist: tick Jiralhanae Pack Alpha or Sangheili Ultra and its weapon
   choices open underneath. Taking both shows an error.
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
