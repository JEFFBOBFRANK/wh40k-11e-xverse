# Skaven 11th-edition homebrew

Catalogue revision 13 rebuilds `Chaos%20-%20Skaven.json` from the homebrew codex
handoff in `homebrew/skaven-source/` (datasheets, points, army rules and the 12
detachments). The layout follows the Emperor's Children catalogue.

## What New Recruit shows

- 58 datasheets. Squads use real model counters with per-model wargear and an
  error unless the unit is one of its legal sizes; larger sizes add their points.
- Abilities are separate named profiles. Core abilities and weapon keywords link
  to the standard rules; Scurry Away! and [WARPSTONE] link to the Skaven rules.
- Mounts (Screaming Bell, Gnaw-beast, Plague Furnace) are options on the character.
  The mounted profile replaces the foot profile and the INFANTRY keyword changes.
- Vermindoom Land-Fortress: exactly one Clan Flagship and six jury-rigged
  hardpoints, at most two of each weapon.
- Copy limits: Epic Heroes 1, Battleline 6, others 3. Repeat costs follow
  `points.json`; a mounted character pays the higher mounted repeat cost.
- Army Rules and References: The Vermintide, The Under-Empire, Scurry Away!,
  Warpstone, Warpstone Backlash, Sacrifice, Summoned Vermin, Verminous Psychic
  Power and the four spell lores.
- Detachments carry their DP and Force Dispositions. Only one Unique: CLAN
  detachment can be taken. Stratagem References follows the chosen detachments.
- Enhancements appear only on eligible units of the chosen detachment. Unit
  Enhancements that up to three units can take are Upgrades sharing one
  Enhancement selection.
- Skryre Worship: Workshop Projects cost Workshop Tokens (6 / 12 / 18 by battle
  size), at most 2 per unit and each once per army. Hidden Workshop and other
  unassigned projects are in the army-level Workshop Projects entry.
- Clan Skurvy: Black-Flag mercenary links are unchanged. The three SKURVY
  CHARACTER enhancements are in "Skurvy Officers"; record which Black-Flag
  character carries each one.
- Shadowy Dealings: Black Contract marks up to three Clanrats units.

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
