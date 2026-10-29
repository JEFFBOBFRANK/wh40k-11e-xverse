# Xverse — Warhammer 40,000 11e homebrew

This fork includes Skaven, Black-Flag and a playtest Agents of the Imperium v0.9.2 catalogue.

## Install in New Recruit

1. Open **Games → Add more games → Add from Github**.
2. Choose **Latest Commit (Head)**.
3. Enter `https://github.com/JEFFBOBFRANK/wh40k-11e-xverse` and add the game.
4. Create a list using **Imperium - Agents of the Imperium (Homebrew v0.9.2)** and **Army Roster**.
5. Select Battle Size, Detachments and one Force Disposition. Add native units or Requisitions as permitted by the selected detachments.

Detachment profiles show their rules and allowed dispositions. **Unique: ORDO** permits only one Ordo Detachment in the army. Stratagems are in the separate **Stratagem References** selection and follow the selected detachments. Army references use separate readable rule sections.

If this fork is already installed, update it to **Latest Commit (Head)** and update the list's data. Catalogue and system revisions have been increased for these fixes. Existing official Agents lists may need rebuilding because the native roster has changed.

## Agents build status

58 native datasheets; 23 household retainers; 17 detachments; 46 Enhancements/Upgrades. Parent datasheets are included for Requisitions.

**Playtest build:** structural/source checks passed, but live roster and card-export testing is pending. Five unit model counts are provisional. Read [validation notes](homebrew/VALIDATION.md) before use. This catalogue replaces the Agents root roster, including its behavior when imported by other Imperial catalogues.

Skaven and Black-Flag catalogue files are preserved. No automatic upstream updates are enabled.

## Sources

- Original data: https://github.com/BSData/wh40k-11e
- Authoring tutorial: https://github.com/DerTanteKethe/custom40k-homebrew-system/wiki/NewRecruit-Data-Author-Tutorial
- Agents rules: the user's complete homebrew codex v0.9.2, transcribed in `homebrew/source-data.json`.

Unofficial fan content; not endorsed by Games Workshop or New Recruit. Parent publications remain authoritative for requisitioned datasheets and points. A rebuild script and validation script are provided in `homebrew/`.
