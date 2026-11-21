# Skaven 11th-edition homebrew

Catalogue revision 27 rebuilds `Chaos%20-%20Skaven.json` from the homebrew codex
handoff in `homebrew/skaven-source/` (datasheets, points, army rules and the 12
detachments). The layout follows the Emperor's Children catalogue.

## What New Recruit shows

- 58 datasheets. Squads use real model counters with per-model wargear and an
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
  Plague Banner, Doom Gong, Grounding Rod, Spare Capacitor) is a model type of
  its own, e.g. "Stormvermin with Warhorn" or "Plague Monk with Plague staff and
  Plague Banner", so it shows on the model carrying it. Each model carries at
  most one item, squad leaders carry none, and the item's ability appears only
  when it is taken.
- An item's ability (including Clanrat Shields on Sword and Board and the
  Grinderfists' Deep Strike) is shown only when the item is taken.
- Heavy shields give their models a 3+ save and 5+ invulnerable save with their
  own stat line, e.g. "Stormvermin (Heavy shield)".
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
- Clan Skurvy: the detachment carries the game system's Clan Skurvy Detachment
  tag, which shows the Black-Flag Allies (mercenary) units. The three SKURVY
  CHARACTER enhancements are in "Skurvy Officers"; record which Black-Flag
  character carries each one.
- Shadowy Dealings: Black Contract marks up to three Clanrats units; each gains
  the ESHIN keyword, Paid Informants and Scouts 6".
- Clan Skurvy: every Clanrats unit gains the SKURVY keyword and Claim-Claim the
  Prize!.
- Random Move: Doomwheel 2D6+3", Clattertank D6+6", Hell Pit Abomination 2D6+1"
  and Doom-Flayers 2D6+5", with the Erratic Movement ability (roll once at the
  start of your Movement phase; modifiers apply after the roll).
- Every CHARACTER has a Warlord option; the army needs exactly one Warlord. The
  Warlord datasheet's WARLORD keyword is its own keyword, not the Warlord role.
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
