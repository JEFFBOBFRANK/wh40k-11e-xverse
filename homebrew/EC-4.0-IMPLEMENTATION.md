# Emperor’s Children 4.0 playtest

Catalogue revision 85 includes 58 datasheets and 14 detachments.
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

Revision 68 applies the same stat block format to Howling Cavaliers, Chaos
Spawn, and Fiends.

Revision 69 records the Infractors' Icon of Excess as wargear on one regular
Infractor in roster exports. In older squads with a squad-level icon, untick
that icon and select it under an Infractor's wargear.

Revision 70 uses the Tormentors' squad-level Icon of Excess control for
Infractors. Its bearer picker accepts one regular Infractor. Existing
model-level icon selections remain editable until removed.

Revision 71 removes the shared cap on the number of 3-DP detachments.
Legions of Excess benefit from Thresholds of Agony and Pain Payments.
Ritual Host and Carnival of Excess remain mutually exclusive in list building.

Revision 72 matches all-caps weapon and unit keyword text to the catalogue's
standard labels, such as Hazardous and Devastating Wounds.

Revision 73 states the scope of Thresholds of Agony and Pain Payments at the
top of The Art of Suffering and gives Pain Token generation its own heading.

Revision 74 uses the revised Art of Suffering wording. Exposed Nerves worsens
armour saves against all attackers, and Agony Beyond Endurance permits one
move per phase.

Revision 75 separates leading subrule headings from their rule and ability
titles in New Recruit. Standalone subrule headings sit directly above their text.

Revision 76 applies the same layout to subrule paragraphs after introductory
text, preserving list labels and ordinary inline rule descriptions.

Revision 77 removes Ignores Cover from Psychic weapon profiles.

Revision 78 limits the Leadership penalty from Reality Unravels to enemy
non-Daemons, uses standard healing wording for Harmonic Alignment, and sets
Twin lascannons to two attacks.

Revision 79 makes Profane Conductor upgrade D3+1 initial Manifestation to D3+3.

Revision 80 requires players to choose which unit each Support attaches to.

Revision 81 grants D3+3 initial Manifestation to units the bearer of
Profane Conductor summons wholly within 8" of the bearer.

Revision 82 charges Dissonant Colossi +20 points from the second copy,
instead of the third. Immaculate Panoply, Perfected Targeting Array and
Predatory Overdrive allow three copies, like the other Upgrades. Repeated
copies of an Upgrade use one Enhancement slot in total.

Revision 83 removes the Sonic Weapons rule and every reference to it.
Vhalyss's The First Symphony now re-rolls one Wound roll of 1 for a unit's
ranged attacks. Weapon names such as sonic blaster are unchanged.

Revision 84 leaves The Gilded Host's Gilded Defiance as the only -1 Damage
stratagem. Peerless Bladesmen's Faultless Parry now subtracts 1 from Hit
rolls for melee attacks against the unit, and The Exalted Court's Iron
Mandate subtracts 1 from Wound rolls for attacks against the unit.

Revision 85 stops the Obsessionist carrying the Icon of Excess: the Infractors'
and Tormentors' icon picker offers only their other models.

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
