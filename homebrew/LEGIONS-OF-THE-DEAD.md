# Legions of the Dead (11e homebrew) — draft

Nothing is built yet. This file holds the design and the datasheets as they arrive, until the catalogue is built
(planned the same way as the Covenant: source files, a builder and a validator).

## Design philosophy

Ossiarch units play like 10th-edition Custodes: few, elite, very durable models.

- Bone fortresses: T6, Sv 2+, InSv 4+, W3, M 6", OC 2.
- Every weapon choice is a role: AP-2 D2 [LETHAL HITS] against elites, high-volume [SUSTAINED HITS 1] against hordes,
  and one special weapon per unit ([DEVASTATING WOUNDS] or [HEAVY]) against big targets.
- Melee weapons carry an integrated 12" [ASSAULT] shot, so melee squads still shoot.
- The Mortek Hekatos leads each squad: a better WS/BS (2+) and an upgraded version of the squad's weapons.
- The Ossiarch Aegis is the Mortek's defensive signature; every Mortek model carries one.
- Every OSSIARCH unit has Indomitable (re-roll Unbinding Hazard rolls), so A State of Undeath rarely hurts them.

Catalogue: "Xenos - Legions of the Dead (Homebrew)", beside the Covenant.

## Keywords

- Faction keyword: LEGIONS OF THE DEAD.
- Sub-faction keyword: OSSIARCH (on every Ossiarch datasheet).
- Plus the usual keywords (INFANTRY, BATTLELINE, CHARACTER...) and the datasheet name. No GRENADES.

## Army rules

### I. Dominion of Death

If your Army Faction is LEGIONS OF THE DEAD, your army has areas of Dominion. Each of the following is the source of
an area of Dominion. The area extends 6" from its source unless a rule says otherwise.

- **Necromantic Dominion:** Each friendly model with this ability.
- **Territorial Dominion:** Each objective marker you control.

**Death's Harvest:** Each time a model is destroyed while it is within one or more areas of your Dominion, that model
has been destroyed within your Dominion.

### II. The Edicts of Nagash

Each Edict is either Active or Suspended, and each has a Passive and a Burning effect. At the start of the battle,
every Edict is Active.

- **Active:** The Edict's Passive applies.
- **Suspended:** The Edict's Passive does not apply, and the Edict cannot be burned.

At the start of each battle round, you can burn one Active Edict. Its Burning effect applies until the end of that
battle round, and that Edict becomes Suspended.

**Edict of Resurrection**
- *Passive — The Dead Shall Rise:* Once per phase, when an enemy model is destroyed within your Dominion, select one
  friendly unit within your Dominion that is within 12" of that model. That unit heals a number of wounds equal to
  that enemy model's W characteristic (maximum 3).
- *Burning — Legion Reborn:* Select up to three friendly units that were destroyed within your Dominion, excluding
  CHARACTER, MONSTER and VEHICLE units. For each of those units, add a new unit to your army that is identical to it,
  at its starting strength and with the same wargear, excluding any attached CHARACTER models. Place those new units
  into strategic reserves. Wargear abilities that can be used once per battle can be used again by those new units.

**Edict of Soul Dominion**
- *Passive — Tithe of Souls:* At the start of your Command phase, you gain 1CP.
- *Burning — Will Overridden:* Until the end of the battle round, friendly units within your Dominion cannot be
  affected by aura abilities of enemy models.

**Edict of the Grave**
- *Passive — Grave's Embrace:* Each time a friendly unit makes an Unbinding Hazard roll, you can re-roll a result of 1.
- *Burning — Death's Defiance:* Until the end of the battle round, Unbinding Hazard rolls made for friendly units
  automatically succeed.

### III. A State of Undeath

If your Army Faction is LEGIONS OF THE DEAD, each time a unit from your army fails a battle-shock roll, or would become
battle-shocked for any other reason, it does not become battle-shocked. Instead, make one hazard roll for each model in
that unit. These are Unbinding Hazard rolls.

(11e hazard roll: on a 1–2 it fails and the unit suffers 1 mortal wound, or 3 if every model in it is a
MONSTER/VEHICLE.)

### Ossiarch universal ability

**Indomitable:** You can re-roll Unbinding Hazard rolls made for models in this unit. Every OSSIARCH datasheet has it
(built as one shared rule, linked on each Ossiarch unit).

## Nagash (Epic Hero) — 500 pts

| M | T | Sv | W | Ld | OC | InSv |
|---|---|---|---|---|---|---|
| 8" | 10 | 2+ | 18 | 5+ | 5 | 4+ |

| Weapon | Range | A | BS/WS | S | AP | D | Abilities |
|---|---|---|---|---|---|---|---|
| Alakanash, Staff of Power | 24" | D6+3 | 2+ | 10 | -3 | 3 | [PSYCHIC] |
| Zefet-nebtar, Mortis Blade | Melee | 6 | 2+ | 12 | -3 | 3 | [PSYCHIC] |
| Swarming Souls | Melee | 6 | 2+ | 6 | -2 | 1 | [EXTRA ATTACKS], [PSYCHIC] |

Faction: Dominion of Death, The Edicts of Nagash, A State of Undeath. Psychic Level 8 (see open points).

Nagash has no Damaged X ability (decided: kept off).

- **Undying (2):** Each time this unit suffers mortal wounds from failed Unbinding Hazard rolls, reduce the number
  of mortal wounds it suffers by 2 (to a minimum of 0). If two or more models in a unit have this ability, use the
  highest value. (Was "Indomitable (2)"; renamed so it does not clash with the Ossiarch Indomitable.)
- **Supreme Lord of the Undead:** Once per battle, at the start of your Command phase, select one friendly LEGIONS OF
  THE DEAD unit that was destroyed during the battle, excluding CHARACTER, MONSTER and VEHICLE units. Add a new unit to
  your army that is identical to it, at its starting strength and with the same wargear, excluding any attached
  CHARACTER models. Place that unit into strategic reserves.
- **Morikhane, the Black Armour:** This model has Feel No Pain 4+ against mortal wounds.
- **The Hand of Dust:** Once per battle, at the end of the Fight phase, select one enemy CHARACTER or MONSTER model
  engaged with this model and roll one D6: 1–3, that model suffers D3 mortal wounds; 4–5, it suffers D6 mortal
  wounds; 6, it is destroyed.
- **The Shyish Nadir (Aura):** This model has Necromantic Dominion, and its area of Dominion extends 18" from it.
  While a friendly LEGIONS OF THE DEAD unit is within 6" of this model, each time a model in that unit makes an
  attack, you can re-roll a hit roll of 1 and a wound roll of 1.
- **Death Magic Incarnate (Aura):** While a friendly LEGIONS OF THE DEAD unit is within 12" of this model, add 1 to
  Unbinding Hazard rolls made for that unit.
- **Arch-Necromancer:** Once per battle round, when this model uses a psychic ability, it can use that ability one
  additional time in that phase, even if it has already been used that phase.
- **Invocation of Nagash (Psychic):** In your Shooting phase, this model can use this ability. When it does, select
  one:
  - *Invocation of Life:* One friendly LEGIONS OF THE DEAD unit within 18" of this model heals D3+3.
  - *Invocation of Death:* One enemy unit within 18" of and visible to this model suffers D3+3 mortal wounds.
  - *Invocation of Undeath:* One friendly LEGIONS OF THE DEAD unit within 18" of this model: until the start of your
    next Command phase, each time a model in that unit makes an attack, re-roll a hit roll of 1.

Keywords: MONSTER, CHARACTER, EPIC HERO, FLY, PSYKER, NAGASH. Faction: LEGIONS OF THE DEAD.

## Mortek Wardens (Battleline) — 250 pts

Unit composition: 4 Mortek Wardens and 1 Mortek Hekatos.

| M | T | Sv | W | Ld | OC | InSv |
|---|---|---|---|---|---|---|
| 6" | 6 | 2+ | 3 | 6+ | 2 | 4+ |

- **Unbreakable Formation:** While this unit is within range of an objective marker you control, add 1 to the OC
  characteristic of models in this unit.
- **Indomitable** (Ossiarch universal ability).

**Wargear ability — Ossiarch Aegis:** Each time an attack is allocated to a model with this wargear, worsen the AP
characteristic of that attack by 1.

| Melee weapon | Range | A | WS | S | AP | D | Abilities |
|---|---|---|---|---|---|---|---|
| Nadirite Soulpike | Melee | 3 | 3+ | 8 | -2 | 2 | [LETHAL HITS] |
| Nadirite Reaver Blades | Melee | 5 | 3+ | 5 | -2 | 1 | [SUSTAINED HITS 1] |
| Nadirite Decapitator (special) | Melee | 3 | 3+ | 10 | -3 | 3 | [DEVASTATING WOUNDS] |
| Soulrender Glaive (Hekatos) | Melee | 5 | 2+ | 8 | -2 | 2 | [SUSTAINED HITS 1] |
| Twin Soulcleavers (Hekatos) | Melee | 7 | 2+ | 5 | -2 | 1 | [LETHAL HITS] |
| Nadirite Warmaul (Hekatos) | Melee | 4 | 2+ | 10 | -3 | 3 | [DEVASTATING WOUNDS] |

| Ranged weapon | Range | A | BS | S | AP | D | Abilities |
|---|---|---|---|---|---|---|---|
| Soulshard Sidearm (Hekatos) | 12" | 2 | 3+ | 5 | -1 | 1 | [ASSAULT] |
| Soulshard (with a Nadirite Soulpike) | 12" | 1 | 3+ | 5 | -1 | 1 | [ASSAULT] |
| Bone Flechettes (with Nadirite Reaver Blades) | 12" | 2 | 3+ | 4 | 0 | 1 | [ASSAULT] |

Wargear options:

- Each Mortek Warden is equipped with an Ossiarch Aegis and either a Nadirite Soulpike or Nadirite Reaver Blades.
  A model with a Nadirite Soulpike also has a Soulshard; a model with Nadirite Reaver Blades also has Bone Flechettes.
- One Mortek Warden can replace its Nadirite Soulpike or Nadirite Reaver Blades with a Nadirite Decapitator. It keeps
  its Ossiarch Aegis.
- The Mortek Hekatos is equipped with an Ossiarch Aegis, a Soulshard Sidearm and one of: Soulrender Glaive, Twin
  Soulcleavers or Nadirite Warmaul.

Keywords: INFANTRY, BATTLELINE, OSSIARCH, MORTEK WARDENS. Faction: LEGIONS OF THE DEAD.

## Mortek Sentinels (Battleline) — 190 pts

Unit composition: 2 Mortek Sentinels and 1 Mortek Hekatos.

| M | T | Sv | W | Ld | OC | InSv |
|---|---|---|---|---|---|---|
| 6" | 6 | 2+ | 3 | 6+ | 2 | 4+ |

- **Execution Protocols:** Each time a model in this unit makes a ranged attack, if this unit remained stationary this
  turn, improve the AP characteristic of that attack by 1.
- **Indomitable** (Ossiarch universal ability).

**Wargear ability — Ossiarch Aegis:** as Mortek Wardens.

| Ranged weapon | Range | A | BS | S | AP | D | Abilities |
|---|---|---|---|---|---|---|---|
| Nadirite Soulcaster | 24" | 3 | 3+ | 6 | -2 | 2 | [SUSTAINED HITS 1] |
| Nadirite Boltspitter | 30" | 2 | 3+ | 8 | -2 | 2 | [LETHAL HITS] |
| Nadirite Annihilator (special) | 36" | 2 | 3+ | 12 | -3 | D3+2 | [HEAVY] |
| Twin Soulcasters (Hekatos) | 24" | 6 | 2+ | 6 | -2 | 2 | [SUSTAINED HITS 1] |
| Hekatos Boltspitter (Hekatos) | 30" | 3 | 2+ | 8 | -2 | 2 | [LETHAL HITS] |

Wargear options:

- Each Mortek Sentinel is equipped with an Ossiarch Aegis and either a Nadirite Soulcaster or a Nadirite Boltspitter.
- One Mortek Sentinel can replace its weapon with a Nadirite Annihilator.
- The Mortek Hekatos is equipped with an Ossiarch Aegis and one of: Twin Soulcasters, Hekatos Boltspitter or Nadirite
  Annihilator.

Keywords: INFANTRY, BATTLELINE, OSSIARCH, MORTEK SENTINELS. Faction: LEGIONS OF THE DEAD.

## Immortis Guard — 330 pts

Unit composition: 3 Immortis Guard.

| M | T | Sv | W | Ld | OC | InSv |
|---|---|---|---|---|---|---|
| 6" | 8 | 2+ | 5 | 6+ | 2 | 4+ |

- **Soulbound Guardians (Aura):** While a friendly LEGIONS OF THE DEAD CHARACTER unit is within 3" of this unit, models
  in that CHARACTER unit have Feel No Pain 5+.
- **Unyielding Constructs:** Each time an attack is allocated to a model in this unit, subtract 1 from the D
  characteristic of that attack (to a minimum of 1).
- **Indomitable** (Ossiarch universal ability).

| Melee weapon | Range | A | WS | S | AP | D | Abilities |
|---|---|---|---|---|---|---|---|
| Nadirite Dread Halberd | Melee | 3 | 2+ | 10 | -3 | 3 | [LETHAL HITS] |

Wargear: each model is equipped with a Nadirite Dread Halberd (no Ossiarch Aegis).

Keywords: INFANTRY, OSSIARCH, IMMORTIS GUARD. Faction: LEGIONS OF THE DEAD.

## Necropolis Stalkers — points TBD

Unit composition: 1 Necropolis Hekatos and 3 Necropolis Stalkers.

| M | T | Sv | W | Ld | OC | InSv |
|---|---|---|---|---|---|---|
| 8" | 6 | 2+ | 2 | 6+ | 2 | 4+ |

- **Indomitable** (Ossiarch universal ability).
- **Quadrarch Aspects:** At the start of the Fight phase, select one aspect; this unit has it until the end of the phase.
  - *Domination:* Subtract 1 from the OC characteristic of models in enemy units engaged with this unit (to a minimum
    of 1).
  - *Blade-Parry:* Each time an enemy model makes a melee attack that targets this unit, subtract 1 from the hit roll.
  - *Destroyer:* Melee weapons equipped by models in this unit have [DEVASTATING WOUNDS].
  - *Precision:* Each time a model in this unit makes a melee attack that targets a CHARACTER unit, that attack has
    [PRECISION].

| Melee weapon | Range | A | WS | S | AP | D | Abilities |
|---|---|---|---|---|---|---|---|
| Nadirite Stalker Blades | Melee | 6 | 2+ | 6 | -2 | 2 | [SUSTAINED HITS 1] |
| Nadirite Dread Falchions | Melee | 4 | 2+ | 10 | -3 | 3 | [LETHAL HITS] |
| Nadirite Daggers | Melee | 8 | 2+ | 5 | -2 | 1 | [TWIN-LINKED] |

Wargear options: each model is equipped with Nadirite Stalker Blades; any model can replace them with Nadirite Dread
Falchions or Nadirite Daggers. The Necropolis Hekatos uses the same profile and weapons.

Keywords: INFANTRY, OSSIARCH, NECROPOLIS STALKERS. Faction: LEGIONS OF THE DEAD.

## Mortis Reapers — points TBD

Unit composition: 1 Mortis Hekatos and 4 Mortis Reapers.

| M | T | Sv | W | Ld | OC | InSv |
|---|---|---|---|---|---|---|
| 8" | 5 | 3+ | 2 | 6+ | 1 | 4+ |

- **Indomitable** (Ossiarch universal ability).
- **Reapers of the Dominion:** Each time a model is destroyed within your Dominion (Death's Harvest) within 12" of this
  unit, this unit gains 1 Reaping token. It can hold at most 3 Reaping tokens; any more are lost. At the start of your
  Shooting phase or of the Fight phase, you can spend any number of this unit's Reaping tokens. For each one, add 1 to
  the A characteristic of the ranged weapons (Shooting phase) or melee weapons (Fight phase) equipped by models in this
  unit until the end of the phase.

| Weapon | Range | A | BS/WS | S | AP | D | Abilities |
|---|---|---|---|---|---|---|---|
| Reaper Blades | Melee | 4 | 3+ | 5 | -2 | 1 | [PRECISION] |
| Soulshard Rifles | 24" | 3 | 3+ | 6 | -2 | 2 | [ASSAULT] |

Wargear options: every model in this unit is equipped with Reaper Blades, or every model with Soulshard Rifles. The
Mortis Hekatos uses the same profile and weapons.

Keywords: INFANTRY, OSSIARCH, MORTIS REAPERS. Faction: LEGIONS OF THE DEAD.

## Open points

- Psychic Level 8 (Nagash): the 11e core only says a psychic ability with a psychic level cannot be used twice in a
  phase. It does nothing yet; when the army's spells arrive it gets a rule (as the Skaven Psyker Level), otherwise
  it is dropped.
- Unit sizes are fixed so far (Wardens 5, Sentinels 3, Immortis Guard 3, Necropolis Stalkers 4, Mortis Reapers 5);
  say if any can be larger.
- Points for the Necropolis Stalkers and Mortis Reapers.
- Which characters can lead the Immortis Guard (and the Mortek units) comes with the characters.
- Sentinels can field two Nadirite Annihilators (one Sentinel and the Hekatos); the Hekatos' Annihilator is BS 3+ as
  printed, not 2+ like his other weapons. Kept as written.

## Decisions

- The Dead Shall Rise: once per phase, heal at most 3 (11e healing also revives destroyed models, so uncapped it
  brought back several models per kill).
- A State of Undeath also covers rules that battle-shock a unit without a roll (combat or emergency disembark):
  those units make Unbinding Hazard rolls instead.
- Burning an Edict suspends it for the rest of the battle (at most three burns): kept.
- Nagash has no Damaged X.
- The Mortek Wardens' Decapitator model keeps its Ossiarch Aegis and the Wardens' Hekatos has one, as decided, though
  the updated datasheet text still says the Decapitator replaces it.
- Nagash's "Indomitable (2)" is now "Undying (2)", so it does not share a name with the Ossiarch Indomitable (two
  different rules cannot share a name in New Recruit).
- Reaping tokens are capped at 3 per unit: uncapped, a unit near a big kill (or Nagash's 18" Dominion) gained a
  token per model destroyed, friendly or enemy, and added that many attacks to every model.
- Necropolis Stalkers start with Nadirite Stalker Blades (the datasheet gave three choices but no default).
- Edict of the Grave's Passive (re-roll Unbinding Hazard rolls of 1) adds nothing for OSSIARCH units, which re-roll
  them anyway; it matters for the other Legions.
