# Emperor’s Children 4.0 playtest

Catalogue revision 54 includes 58 datasheets and 14 detachments.
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

Rapture Talons cost 105 points for five or 200 for ten, with a 10-point
surcharge on the third and subsequent squads. Regular Talons carry
bolt pistols. The champion carries a screamer pistol with a plasma pistol
option. Vhalyss remains 255. Threnody designates an objective
when deployed, has OC 10 and cannot be Stupefied within its range, and is
Stupefied outside its range. Awakening Chimes uses the 4.0 suspension rule.

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
