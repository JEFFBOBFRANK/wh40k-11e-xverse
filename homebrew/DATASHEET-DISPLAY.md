# Datasheet display cleanup

Applied to EC catalogue revision 19 and Agents catalogue revision 21.

- EC: 58 datasheets; 226 duplicate metadata rows hidden.
- Agents: 58 datasheets and 23 household retainers; 127 duplicate metadata rows hidden.
- All 1,880 original stat, weapon and ability profiles retain their content and IDs; only redundant metadata visibility changes.
- Structural comparison confirms identical costs, selections, categories, attachment associations, constraints, default selections and modifiers affecting roster construction.
- Composition and equipment source text remains in unit configuration notes. Mixed metadata clauses such as Supreme Commander, psychic levels and Leader/Support permissions remain visible as named abilities.
- Shared core rules use standard references. Parameterized values remain on the references. Agents Imperial Strategist and Sanctioned Psykana are linked from the corresponding models. Weapon keyword references resolve through the game system.
- Both formatter passes are idempotent.

Validation commands (run against the complete repository and the previous published catalogue snapshot):

```sh
python3 homebrew/datasheet-validate.py --data . --previous /path/to/previous
python3 homebrew/ec-validate.py --data . --source homebrew/ec-source-data.json --previous /path/to/previous
python3 homebrew/validate.py
```

EC roster tests: 5,823 detachment/ally scenarios passed. Agents roster tests: 6,300 Requisition-budget scenarios and 3,214 detachment scenarios passed. The Agents validation script now follows budget-category links to their definitions, matching the deployed catalogue structure. Existing codex source gaps are unchanged.

Live New Recruit verification passed using the GitHub Latest changes installation after publication:

- Fulgrim: seven actual ability/clarification rows; composition, printed keywords and weapon-trait summaries absent from Abilities; Supreme Commander and ordinary-dose text retained; Deadly Demise D6 shown in Rules.
- Inquisitor Coteaz: six ability rows including explicit Leader permissions; Imperial Authority and Imperial Strategist in Rules; one native keyword list.
- Eversor Assassin: three bespoke abilities; Scouts 8" and Feel No Pain 5+ shown in Rules; Epic Hero keyword retained.
- Inquisitor Gideon Ravenor: psychic powers and three-level budget retained; Sanctioned Psykana (Psyker Level 3) reference expands correctly.

Screenshots of Fulgrim and Coteaz were captured from the live imported catalogues. New Recruit successfully created and opened both faction rosters. These are targeted datasheet display checks, not a new full live army/card-export certification.
