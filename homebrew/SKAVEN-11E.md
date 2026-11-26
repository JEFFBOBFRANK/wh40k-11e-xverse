# Skaven 11th-edition homebrew

Catalogue revision 77 rebuilds `Chaos%20-%20Skaven.json` from the homebrew codex
handoff in `homebrew/skaven-source/` (datasheets, points, army rules and the 17
detachments). The layout follows the Emperor's Children catalogue.

## What New Recruit shows

- 67 datasheets (including the Eshin Shadowfangs, the Clan Chieftain, Arch-Warlock, Beast-Lord, Pox-Abbot,
  Eshin Sorcerer, the Warpfang Colossus, Gnawhull Brutes and Blightfang
  Ogors). Squads use real model counters with per-model wargear and an
  error unless the unit is one of its legal sizes; larger sizes add their points.
- Sub-headings in rules and abilities are bold lines, as in the Emperor's
  Children catalogue, not large Markdown headings.
- Special weapons are separate model types beside the plain models, as in the
  Emperor's Children Tormentors (e.g. "Stormvermin with Heavy shock weapon").
  Each one taken lowers the plain model count; New Recruit flags the plain count
  until it is reduced. Limits such as one per five models apply to each type.
- Abilities are separate named profiles. Core abilities and weapon keywords link
  to the standard rules; Scurry Away! and [WARPSTONE] link to the Skaven rules.
- Leaders and Supports attach to their printed units with New Recruit's
  Leading / Supporting links, as in the Emperor's Children catalogue. A Support
  must be attached; a mounted Plague Priest need not be.
- Optional wargear (Clan Standard, Scavenger Bell, Warhorn, Regimental Banner,
  Plague Banner, Doom Gong, Grounding Rod, Spare Capacitor, Voltaic Pennant, Warp-Grenade Satchel, Smoke Bombs, Shadow-step Talisman,
  Rot-bell, Plague-gas Globes) works like the Emperor's
  Children Tormentors' Icon of Excess: tick it on the unit, then pick the model that
  carries it. Squad leaders cannot carry it, and the item's ability appears only
  when it is taken. Special weapons stay separate model types (e.g. "Stormvermin
  with Heavy shock weapon"), as the Tormentors' plasma gun and meltagun.
- An item's ability (including Clanrat Shields on Sword and Board and the
  Grinderfists' Deep Strike) is shown only when the item is taken.
- Heavy shields give their models a 3+ save and 5+ invulnerable save with their
  own stat line, e.g. "Stormvermin (Heavy shield)".
- Stormclad Stormvermin (formerly Warpclad Warpack): plain Stormclads (Warp-disintegrator and Warp-glaive) plus model
  types with Warp-blade and Voltaic shield (4+ invulnerable save, own stat line),
  Warp-blaster (up to 3), Shock gauntlet (up to 2) and Warp-lance (1). The Voltaic
  Pennant is optional wargear and improves the unit's Leadership on its stat lines.
- Plague Censer Bearers (revision 78, the Stormvermin standard): the Censer-bearer Leader (W3) takes a Master plague
  censer or a Censer-hammer; plain Censer Bearers (Great plague censer) plus model types with Twin plague censers (any),
  a Fumigator censer and Censer haft (1 per 5 models) and a Plague-reliquary censer (1). Rot-bell (Choking Fumes at 6")
  and Plague-gas Globes are optional wargear. Points stay 95 / 190.
- Better Them-Than Me! (revision 79): every BTTM ability Sacrifices nearby models ("other friendly SKAVEN
  INFANTRY models within 6\" of this model"), not Bodyguard models from the character's own unit. This changed the
  Eshin Sorcerer (Shadow-Step!), Grey Seer, Warlock Engineer, Clan Chieftain, Arch-Warlock and Pox-Abbot.
- Mounts (Screaming Bell, Gnaw-beast, Plague Furnace) are options on the character.
  The mounted profile replaces the foot profile and the INFANTRY keyword changes.
- Vermindoom Land-Fortress: exactly one Clan Flagship and six jury-rigged
  hardpoints, at most two of each weapon.
- Copy limits: Epic Heroes 1, Battleline 6, others 3. Repeat costs follow
  `points.json`; a mounted character pays the higher mounted repeat cost.
- Army Rules and References: The Vermintide, The Under-Empire, Scurry Away!,
  Warpstone, Warpstone Backlash, Sacrifice, Summoned Vermin, Verminous Psychic
  Power and the three spell lores.
- Spells unique to a datasheet are abilities on that datasheet named "Spell (Psychic
  Level N)", written as the Emperor's Children homebrew writes its psychic abilities.
  Peal of Doom is on the Grey Seer's Screaming Bell.
- Damaging spells deal spell hits (no hit roll; wound rolls and saves as normal), not
  mortal wounds; see Spell Hits in Verminous Psychic Power.
- Detachment rules are one rule per named ability, as in the Emperor's Children
  catalogue; menus and procedures (ledgers, catalogues, Warlord Commands, Clawpack
  Benefits, Secret Schemes, The Great Workshops) stay whole. Army rules are not
  linked from detachments; they are in Army Rules and References.
- Detachments carry their DP and Force Dispositions. Only one Unique: CLAN
  detachment can be taken. Stratagem References follows the chosen detachments.
- Clan detachments (2 DP, Unique: CLAN): Skryre Worship, Moulder Flesh
  Laboratory, Shadowy Dealings, Cauldron of Pestilence, Clawpack Horde, Clan
  Skurvy and Council of Treachery. Each has a signature rule, a Clanrats rule and
  a broad rule, 4 enhancements and 6 stratagems.
- Other detachments: Invasion of the Under-Empire (3 DP); The Dreaded 13th Bell,
  Black-Fur Supremacy, Prophets of the Horned Rat, Engines of Ruin, Warlock
  Battery, Beast Pens, Night Stalkers, Plague Congregation and Endless Swarm (1 DP).
- Detachments that make a unit BATTLELINE (Black-Fur Supremacy, Warlock Battery,
  Beast Pens, Night Stalkers, Plague Congregation) move it into Battleline, add
  1 OC to its models and raise its copy limit to 6.
- A unit, and an Attached Unit (Leader and Bodyguard together), can have only one
  Enhancement or Upgrade.
- Enhancements appear only on eligible units of the chosen detachment. Unit
  Enhancements that up to three units can take are Upgrades sharing one
  Enhancement selection.
- Skryre Worship: Workshop Projects are options on eligible units, 1 per unit
  (2 with Chief-Chief Engineer), each up to 3 per army, on at most 3 / 6 / 9 units
  by battle size (+2 with Chief-Chief Engineer).
- Moulder Flesh Laboratory: Mutations and Ruinous Defects are options on MOULDER
  BEAST and MONSTER units, at most 3 / 6 / 9 Mutations by battle size plus one per
  Defect taken; a Defect allows a second Mutation and cannot undo its own
  Mutation. Mutations change the unit's stat lines.
- Council of Treachery: each CHARACTER can take its Clan's Council Seat (any Seat,
  and two, with Lord of Decay); each Seat once per army. Clanrats can take a
  Council Levy, which adds that Clan's keyword.
- Clan Skurvy: the detachment carries the game system's Clan Skurvy Detachment
  tag, which shows the Black-Flag Allies (mercenary) units. The three SKURVY
  CHARACTER enhancements are in "Skurvy Officers"; record which Black-Flag
  character carries each one.
- Pestilent Fervour: every PESTILENS datasheet except Blightfang Ogors (BEAST) adds 1 to its
  battle-shock rolls and ignores Cornered Rats.
- Cauldron of Pestilence: every Clanrats unit gains PESTILENS and Plague Carrier.
- Skryre Worship: every Clanrats unit gains SKRYRE and Overstuffed Power Cells.
- Moulder Flesh Laboratory: every Clanrats unit gains MOULDER and Pack-Driven.
- Clanrats: each model type carries its weapons (Clanrat, Clanrat with mace, with
  spear or with Warplock carbine; the Clawleader picks Sword and Board or Warplock).
  New Recruit shows an error unless the whole unit uses one loadout.
- Shadowy Dealings: every Clanrats unit gains ESHIN and Paid Informants (Scouts 6"
  and Stealth).
- Clan Skurvy: every Clanrats unit gains the SKURVY keyword and Claim-Claim the
  Prize!.
- Random Move: Doomwheel 2D6+3", Clattertank D6+6", Hell Pit Abomination 2D6+1"
  and Doom-Flayers 2D6+5", with the Erratic Movement ability (roll once at the
  start of your Movement phase; modifiers apply after the roll).
- FRAME is on every vehicle except the Eshin Nightstrider; GRENADES is on
  Clanrats, Stormvermin, Warp-Zap Stormvermin, Stormclad Stormvermin, Skryre Acolytes,
  Night Runners, Gutter Runners, Eshin Shadowriggers and Eshin Shadowfangs.
- Movement: foot models are M7" (weapon teams stay M6"); Rat Ogors and the Mutant
  Rat Ogor are M9". Skavenslaves are 20 or 40 models at 2 pts each.
- Ranged weapons that hit on 4+ or 5+ and are not TORRENT or IGNORES COVER have
  about 1.5x (4+) or 2x (5+) the shots, to make up for cover worsening Ballistic Skill by 1.
  Anti-tank guns keep their shots: vehicles and monsters only get cover when not
  fully visible.
- A PSYKER can use any of its spells, limited only by its Psyker Level.
- Every CHARACTER has a Warlord option; the army needs exactly one Warlord. The
  Verminus captain is the Clawlord (formerly Warlord), with the CLAWLORD keyword.
- Weapon teams start with their lead crew (Lead Gunner, Lead Burner, Lead
  Scourger or Lead Marksman: W3, Crew-leader blades, optional Warplock pistol). Skryre Acolytes are
  1 Bombardier and 4 or 9 Poison Wind Globadiers. Weapon Team models added to
  Clanrats are always normal team models.

## Removed

- The single Verminlord datasheet (now Warbringer, Warpseer, Deceiver and
  Corruptor), Lord Skreech's old abilities and weapons, the old Warp Lightning and
  Peal of Doom weapon profiles, Ikit Claw's Iron claws, Expendable Vermin,
  Tribute to Ruin! and Burn-Burn Warpstone!.
- The Thirteen-Eyed Augur enhancement, which is not in the new Prophets of the
  Horned Rat.
- The old reference blocks (casting values, old Verminous Spells, old detachment
  profiles); their replacements are rules in the EC style.

## Rebuild and check

```sh
python3 homebrew/skaven_build.py --source homebrew/skaven-source \
  --catalogue 'Chaos%20-%20Skaven.json' --system 'Warhammer 40,000.json' --output /tmp/skaven.json
python3 homebrew/skaven_validate.py --source homebrew/skaven-source --catalogue /tmp/skaven.json
```

The builder reuses the IDs of the current catalogue, so rebuilding is stable.
Wargear options are written out in `homebrew/skaven_units.py`, because the
handoff gives them only as prose. The validator compares every datasheet with
`datasheets.json` and `points.json` and searches for retired terms.

## Black-Flag Chaos Space Marines

`homebrew/blackflag_csm_port.py` rebuilds the eight CSM units of Index: Black-Flag
(Chaos Lord, Chaos Lord with Jump Pack, Red Corsairs Reave-Captain, Legionaries,
Havocs, Raptors, Red Corsairs Raiders, Chaos Bikers) from the current Chaos Space
Marines catalogue: real model entries, weapon choices, unit sizes and repeat costs.
Marks of Chaos, Dark Pacts, CSM Enhancements and Crusade content are left out. The
units keep their Black-Flag IDs and Faction: Skurvy, and Leader links follow the
LEADER lists on the Black-Flag datasheets.

```sh
python3 homebrew/blackflag_csm_port.py --index 'Index - Black-Flag (Homebrew).json' \
  --csm 'Chaos - Chaos Space Marines.json' --system 'Warhammer 40,000.json' --output out.json
```

## Black-Flag Ork, Drukhari and Corsair units

`homebrew/blackflag_port.py` does the same for the other 22 Black-Flag units, which the index printed as flat
entries (one stat line, no models or wargear choices): Big Mek, Big Mek with Shokk Attack Gun, Mek, Warboss,
Boyz, Flash Gitz, Kommandos, Breaka Boyz, Tankbustas and Trukk from `Orks.json`; Archon, Kabalite Warriors, both
Scourges units, Reavers, Ravager, Raider, Venom and the four Corsair units from `Aeldari - Aeldari Library.json`.

- Each unit has its real models, weapon choices, unit sizes and repeat costs. Faction-only content is left out:
  Waaagh!, Power from Pain, Battle Focus, enhancements and enhancement upgrades, Warlord and Crusade.
- Stats, weapons and points are checked against the IRONBUILT 11th-edition dataset. The repo's `Orks.json` is
  older, so its points were updated: Big Mek 100, Big Mek with Shokk Attack Gun 110, Mek 55, Boyz 85/170,
  Flash Gitz 110/220, Breaka Boyz 120, Tankbustas 160. Scourges with Shardcarbines are Ld 6+ and Corsair
  Voidscarred Ld 6+. The eight CSM units already matched.
- Abilities use the Black-Flag wording (SKURVY instead of Orks/Drukhari, Plunder instead of Pain). The Raider's
  Speed of the Kill (Wyches) and Visions of Butchery (Wracks) are left out, as no Skurvy unit can use them.
- The units keep their Black-Flag IDs and Faction: Skurvy, so Clan Skurvy's links still work. Leader and Support
  links follow the LEADER / SUPPORT lists on the Black-Flag datasheets (the Archon leads Kabalite Warriors).
- The script also gives every copied weapon its own IDs (copies of one shared weapon used to repeat them) and
  points category links inside models at Black-Flag categories. Both also apply to the CSM units.

- Weapons follow the house standard in `homebrew/house_dice.py` (all 30 units): D6 damage becomes D3+X (blaster and
  lascannon D3+3, dark lance D3+4, heat lance and wraithcannon D3+3, fusion and meltagun D3+2), meltaguns are S10 AP-3
  and krak missiles S10 D3+3 as in the 11e codex, and flamers, shredders and frag missiles have 3 attacks with
  [BLAST 1] instead of D6 (hand flamers 3, no Blast).

```sh
python3 homebrew/blackflag_port.py --index 'Index - Black-Flag (Homebrew).json' --system 'Warhammer 40,000.json' \
  --ironbuilt wh40k-11e.json --output 'Index - Black-Flag (Homebrew).json'
```
