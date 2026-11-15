# Emperor’s Children 4.0 playtest

Catalogue revision 66 includes 58 datasheets and 14 detachments.
The Pursuit of Perfection, Manifestation
and Summoning Rituals are in Army Rules and References. Stratagem References
shows the stratagems for the selected detachments.

| Detachment | Force Dispositions |
| --- | --- |
| The Theatre of Excess | Purge the Foe, Disruption |
| The Seductions of Slaanesh | Disruption, Take and Hold |
| The Exalted Court | Priority Assets |
| Combat Drugs | Purge the Foe |
| Blades of Exquisite Pain | Purge the Foe |
| The Gilded Host | Take and Hold |

The November 13 playtest adds Blades of Exquisite Pain, Surgical
Conditioning and the revised Martial Perfection. Pain Token conversion
timing and competing effects on Leadership tests remain open for playtesting.

Ritual Host and Carnival of Excess each allow Legions of Excess units up to
half the battle size points limit. Both have Unique: DAEMON.

Chained Thralls cost 30 points for 10 or 60 for 20 and have a 6+ invulnerable save.

Revision 57 updates seven Requisition Thresholds and seven Enhancement
prices. Perfection Through Agony protects Enraptured Flawless Blades when
Daemonic Patrons resolves at the end of the phase.

Revision 58 updates Fulgrim, Julius, Eidolon, the Threnody Dreadnought
and recovery abilities for The Pursuit of Perfection. Pain Brings Clarity
cannot clear a state during the turn it began. The Threnody is Enraptured
within range of its designated objective and Stupefied outside that range.

Revision 59 updates Fulgrim's Daemonic Poisons. It lasts until the end
of the phase and reduces the Damage of melee weapons by 1, to a minimum of 1.

Revision 60 corrects the trigger for Fulgrim's Ecstatic Slaughter Pile-in.
The limits on his weapon attacks still apply.

Revision 62 gives new variable-size units model counters, with champion
wargear and specialists listed separately. Squads retain their two legal
sizes and corresponding prices. Units already saved using Unit Size keep
that selection path. Single-weapon choices show their profile on the choice.

Revision 63 puts ability subheadings below their titles and gives Infractors,
Tormentors, and Daemonettes selectable wargear bearers. A saved unit-level
icon or instrument can be unchecked and reassigned under a model.

Revision 64 aligns shared weapons with the November Space Marines codex
profiles. Doomrider's melta modes use D3+2 and retain Melta 3. Newly added
Daemonettes use the standard Alluress and nine Daemonettes composition,
with the icon and instrument on separate eligible models.

Revision 65 restores the earlier Unit Size and specialist controls for new
units. Icon of Excess, Daemonic Icon and Instrument of Chaos appear at squad
level, following the Legionaries' Chaos icon layout. Saved model and wargear
selections from the previous layouts can still be opened.

Revision 66 updates the sonic arsenal and replaces the Land Raider's
Cathedral annihilators with Requiem cannons. Fresh variable-size squads
use direct model counters. The squad-level icon and instrument options
open a picker for models already selected in the squad. Playtest the
Requiem cannon's anti-armour output and the Cathedral sonic immolator's
Torrent damage.

Revision 67 opens an explicit bearer choice for the Infractors' Icon of
Excess. Infantry stat blocks use one profile per model type when weapon
variants share the same stats. Model loadouts still list each weapon.

Rapture Talons cost 105 points for five or 200 for ten, with a 10-point
surcharge on the third and subsequent squads. Regular Talons carry
bolt pistols. The champion carries a screamer pistol with a plasma pistol
option. Vhalyss remains 255. Awakening Chimes uses the 4.0 suspension rule.

## Rebuild

Use the published revision 43 catalogue and revision 23 game system from
commit `32516deb21809af253473b0e8b4ccb41699c1a48`.

```sh
baseline=$(mktemp -d)
git show "32516deb21809af253473b0e8b4ccb41699c1a48:Chaos - Emperor's Children.json" > "$baseline/ec.json"
git show '32516deb21809af253473b0e8b4ccb41699c1a48:Warhammer 40,000.json' > "$baseline/system.json"
python3 homebrew/ec-4.0-migrate.py \
  "$baseline/ec.json" "Chaos - Emperor's Children.json" \
  --system "$baseline/system.json" --system-output 'Warhammer 40,000.json'
```
