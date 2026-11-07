# Emperor's Children homebrew v3.1

Source: the user's `Emperors_Children_Codex_v3.1.pdf`, 7 November 2026, 133 pages. SHA-256: `9f67e82df35648405bab0aba5cb725ae9b52696dbd5621b250fad60ff348722d`. Library source version 9. The source book controls custom rules, points and profiles.

## Included

- 45 Emperor's Children and 13 Legions of Excess datasheets, all 244 printed weapon profiles.
- Fifteen detachments, forty enhancements/upgrades and sixty stratagems. Stratagem References follows only selected detachments.
- Small/large squad prices, copy limits, five copy-price surcharges, equipment replacements and alternative weapon profiles.
- Fulgrim's required Warlord selection. Epic Hero exclusions from enhancements. Native army rules and allied Manifestation remain separate.
- Exactly two different permanent Warband Elixirs for Bound Excess and Fulgrim's Master of Excess; Perfect Formula's additional Warband selections require that detachment. Threnody records one starting Warband choice.
- Allied visibility and a force-linked allied points cap. Perfumed Procession and Ritual Host grant 500 each and stack. Carnival uses its printed 500/1,000/1,500 allowance; its larger allowance supersedes the smaller packages when combined.
- Up to three Living Elixir assignments, eligible named units only. Censer requires an assigned Living Elixir. Printed Leader and Support associations are included, including Phoenix Guard/Fulgrim.
- Printed signature elixirs, psychic powers, summoning and transport rules are retained as reference text. In-battle dosage/state transitions, conditional combat modifiers, summons and damage are resolved by the players.

## Source gaps and scope

Only Coterie of the Conceited and Carnival of Excess print disposition choices in v3.1. Peerless Bladesmen, Rapid Evisceration and Mercurial Host retain the original fork's disposition permissions. The ten remaining packages provisionally permit the standard five dispositions and carry a visible source-gap note. Confirm these assignments before treating this as a final release. No Unique tag is invented for a package that has none printed.

Optional Combat Patrol/campaign rules and obsolete Crucible/retired units are not matched-play root choices. Other faction catalogues and existing Agents changes are preserved. New unit identifiers mean old EC rosters should be rebuilt after refreshing data.

## Checks

`ec-validation-results.json` records structural/source checks and 5,823 detachment/size scenarios: references resolve, new identifiers are unique, points/statistics/weapon values match the transcription, every weapon is represented, squad sizes and points tiers agree, all sixty stratagems follow selected packages, ally permissions/caps agree for every tested combination, Epic Heroes have no enhancements, and permanent elixir choices require two distinct selections.

Live New Recruit checks passed against catalogue commit `0c10885687b1870eb7e838ed589666db96b0335e`: installation and faction/list creation; all fifteen detachment options; Fulgrim at 485 with mandatory Warlord and two permanent selections; Perfect Formula additional elixirs; daemon unlocks; 540/500 allied allowance violation and its removal when Ritual Host raises the cap to 1,000; Censer hidden before Living Elixir assignment and visible afterwards; Lord Exultant costs of 95, 95 and 105; automatic 5-to-10 Infractor configuration at 95/175 points; correct 9/9 Infractor and 1/1 champion counters; repeated Bloodglass selections show a 2/3 copy count. Card exports, all individual equipment permutations, enhancement-slot accounting for repeated Upgrades, and every attachment permutation still require broader playtesting. New Recruit permits constructing invalid lists and marks violations; catalogue validation does not necessarily block every selection click.

## Rebuild

Use an isolated baseline checkout of `JEFFBOBFRANK/wh40k-11e-xverse` at `b7ecd9e447171c1c69542b57fd69e4eb0eb75ac5`. Do not rebuild against an already modified system.

`python3 homebrew/ec-build.py --baseline /path/to/baseline --output /path/to/output`

`python3 homebrew/ec-validate.py --data /path/to/output --source homebrew/ec-source-data.json`

Copy the generated two root catalogues and EC reports into the repository. The builder uses the standard library and does not require the PDF at build time.
