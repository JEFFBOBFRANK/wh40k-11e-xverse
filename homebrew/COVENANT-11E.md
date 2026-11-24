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
