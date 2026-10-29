# Agents homebrew v0.9.2 — playtest build

This catalogue transcribes the user's complete Agents of the Imperium v0.9.2 codex. It is a playtest build, not a final validated release.

## Included

- 58 native datasheets, 23 individually paid Rogue Trader retainers, 17 detachments, and 46 Enhancements/Upgrades.
- Weapon exchanges, firing modes grouped under their weapon, psychic choices, unique Writs, Leader/Support associations, and seven paid Temple packages.
- Requisitions use parent datasheets from the existing fork at commit `4a1c157ac06d8ae2fbe6795d449b8d8812a3f45c`. Detachment gates and shared/faction points allowances are encoded separately from native units.
- Source text and deterministic build script are included. Existing Skaven and Black-Flag files are not changed by this upload.

## Checks completed

Structural and source checks cover catalogue links, profile types, defaults, root visibility structure, primary categories, native stats, source weapon values, both squad points tiers, retainer nesting, detachment DP and Stratagem text. 6,300 independent allowance-allocation scenarios and 3,214 detachment combinations (zero to four detachments) test Requisition budgets, disposition unions, and Ordo Unique restrictions. Exact check counts are in `validation-results.json`.

## Detachment and reference fixes

- Strip PDF whitespace from category names so all 17 detachments unlock the standard dispositions shown in the codex.
- Count the nine selected Ordo detachments under a roster-wide **Unique: ORDO** maximum of one, and cap each Ordo choice at zero when another Ordo is selected. Non-Ordo detachments do not consume this allowance.
- Remove Stratagem profiles from each detachment's rules view. A separate **Stratagem References** selection shows the selected detachments' Stratagems; costs and rules are retained.
- Display army references as named Rules with paragraphs, labels and readable lists, instead of a single Abilities table containing PDF line breaks.
- Increase catalogue and system revisions to invalidate older cached data.

Live New Recruit smoke checks passed for GitHub installation, faction selection, and manual Army Roster creation, with native units and gated Requisitions visible. The guided setup initially skipped Detachment; the entry/group names were corrected to the standard `Detachment` names. Retesting guided setup against refreshed data remains pending. If the wizard offers no Force Disposition choices, go Back and select **Skip the guided setup and create the list right away**, then configure Battle Size, Detachment and Force Disposition in the roster. Full list validation and 40k Card exports still require testing.

## Provisional model counts

The consolidated PDF's composition text omits complete counts for these units. These are explicit implementation assumptions, not confirmed additional rules:

| Unit | Implemented count |
| --- | --- |
| Voidship Ogryn Boarders | 3 or 6 |
| Naval Ordnance Detail | 1 Spotter and 2 Gunners |
| Voidwalker Reconnaissance Team | 5 or 10 |
| Shipbreaker Exosuits | 2 or 4 |
| Ecclesiarchy Penitent Engine | 1 or 2 |

Confirm these against the original design before treating the catalogue as final. `build.py` records these choices in `add_unitsize` and `equip`.

## Other testing required

- Verify points-category constraints in New Recruit for shared and additional Requisition pools, including a unit whose points span two allowances.
- Verify selection-dependent equipment limits after changing squad size, and changing detachments after adding Writs, Temple packages or Enhancements.
- Check Upgrade selection counters, mixed-profile units, attached Leaders/Support and all card exports.
- Parent datasheets preserve inherited equipment logic. One dangling parent default alias was reset to `none`; its choices and points were preserved. Some inherited constraint identifiers are reused by parent data.
- This upload replaces the Agents catalogue's root roster. It does not preserve official Assigned Agents list-building behavior for other Imperial armies. Other factions' native files remain unchanged.

## Rebuilding

Run `python3 homebrew/build.py --upstream /path/to/original-fork-snapshot`, then `python3 homebrew/validate.py`. Use the original parent commit above as the snapshot; rebuilding from the already modified game system would add the generated global definitions again.

Authoring reference: https://github.com/DerTanteKethe/custom40k-homebrew-system/wiki/NewRecruit-Data-Author-Tutorial

Universal rules use rule links where available; bespoke abilities use Abilities profiles. Every native datasheet has a root selection link and one primary category. Retainers are nested model selections, never independent root units. Source provenance and PDF SHA-256 are in `source-data.json`.
