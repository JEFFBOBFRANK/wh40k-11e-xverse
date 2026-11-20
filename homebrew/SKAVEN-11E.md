# Skaven 11th-edition homebrew

Catalogue revision 17 rebuilds `Chaos%20-%20Skaven.json` from the homebrew codex
handoff in `homebrew/skaven-source/` (datasheets, points, army rules and the 12
detachments). The layout follows the Emperor's Children catalogue.

## What New Recruit shows

- 58 datasheets. Squads use real model counters with per-model wargear and an
  error unless the unit is one of its legal sizes; larger sizes add their points.
- Sub-headings in rules and abilities are bold lines, as in the Emperor's
  Children catalogue, not large Markdown headings.
- Abilities are separate named profiles. Core abilities and weapon keywords link
  to the standard rules; Scurry Away! and [WARPSTONE] link to the Skaven rules.
- Leaders and Supports attach to their printed units with New Recruit's
  Leading / Supporting links, as in the Emperor's Children catalogue. A Support
  must be attached; a mounted Plague Priest need not be.
- Unit wargear (Clan Standard, Scavenger Bell, Warhorn, Regimental Banner, Plague
  Banner, Doom Gong, Grounding Rod, Spare Capacitor) is taken on the squad and
  given to a chosen model, like the Emperor's Children Tormentors' Icon of Excess.
  Each item is separate, so a unit can have both.
- Mounts (Screaming Bell, Gnaw-beast, Plague Furnace) are options on the character.
  The mounted profile replaces the foot profile and the INFANTRY keyword changes.
- Vermindoom Land-Fortress: exactly one Clan Flagship and six jury-rigged
  hardpoints, at most two of each weapon.
- Copy limits: Epic Heroes 1, Battleline 6, others 3. Repeat costs follow
  `points.json`; a mounted character pays the higher mounted repeat cost.
- Army Rules and References: The Vermintide, The Under-Empire, Scurry Away!,
  Warpstone, Warpstone Backlash, Sacrifice, Summoned Vermin, Verminous Psychic
  Power and the four spell lores.
- Detachment rules are one rule per named ability, as in the Emperor's Children
  catalogue; menus and procedures (ledgers, catalogues, Warlord Commands, Clawpack
  Benefits, Secret Schemes, The Great Workshops) stay whole. Each detachment links
  the army rules it uses.
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
- Weapon teams start with their lead crew (Lead Gunner, Lead Burner or Lead
  Scourger: W3, Crew-leader blades, optional Warplock pistol). Skryre Acolytes are
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
