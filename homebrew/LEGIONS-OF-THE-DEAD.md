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
- The Ossiarch Aegis is the faction's defensive signature; every model carries one.

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
- *Passive — The Dead Shall Rise:* Each time an enemy model is destroyed within your Dominion, select one friendly unit
  within your Dominion that is within 12" of that model. That unit heals a number of wounds equal to that enemy
  model's W characteristic.
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

If your Army Faction is LEGIONS OF THE DEAD, each time a unit from your army fails a battle-shock roll, it does not
become battle-shocked. Instead, make one hazard roll for each model in that unit. These are Unbinding Hazard rolls.

(11e hazard roll: on a 1–2 it fails and the unit suffers 1 mortal wound, or 3 if every model in it is a
MONSTER/VEHICLE.)

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

- **Indomitable (2):** Each time this unit suffers mortal wounds from failed Unbinding Hazard rolls, reduce the number
  of mortal wounds it suffers by 2 (to a minimum of 0). If two or more models in a unit have this ability, use the
  highest value.
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

## Mortek Wardens (Battleline)

Unit composition: 4 Mortek Wardens and 1 Mortek Hekatos.

| M | T | Sv | W | Ld | OC | InSv |
|---|---|---|---|---|---|---|
| 6" | 6 | 2+ | 3 | 6+ | 2 | 4+ |

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
| Nadirite Soulpike – soulshard (integrated) | 12" | 1 | 3+ | 5 | -1 | 1 | [ASSAULT] |
| Nadirite Reaver Blades – bone flechettes (integrated) | 12" | 2 | 3+ | 4 | 0 | 1 | [ASSAULT] |

Wargear options:

- Each Mortek Warden is equipped with an Ossiarch Aegis and either a Nadirite Soulpike or Nadirite Reaver Blades.
  Each weapon includes its integrated ranged profile.
- One Mortek Warden can replace its Nadirite Soulpike or Nadirite Reaver Blades with a Nadirite Decapitator. It keeps
  its Ossiarch Aegis.
- The Mortek Hekatos is equipped with an Ossiarch Aegis, a Soulshard Sidearm and one of: Soulrender Glaive, Twin
  Soulcleavers or Nadirite Warmaul.

Keywords: INFANTRY, BATTLELINE, OSSIARCH, MORTEK WARDENS. Faction: LEGIONS OF THE DEAD.

## Mortek Sentinels (Battleline)

Unit composition: 2 Mortek Sentinels and 1 Mortek Hekatos.

| M | T | Sv | W | Ld | OC | InSv |
|---|---|---|---|---|---|---|
| 6" | 6 | 2+ | 3 | 6+ | 2 | 4+ |

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

## Open points

- Psychic Level 8 (Nagash): the 11e core only says a psychic ability with a psychic level cannot be used twice in a
  phase; the army needs its own rule for what Psychic Levels do (as the Skaven Psyker Level), or Nagash drops it.
- Edict of Resurrection (Passive): healing equal to the enemy model's W characteristic also revives destroyed models
  (11e healing), and triggers once per enemy model destroyed.
- Burning an Edict suspends it for the rest of the battle (its Passive is gone and it cannot be burned again).
- A State of Undeath replaces failed battle-shock rolls only; rules that make a unit battle-shocked without a roll
  (combat or emergency disembark) still apply.
- Nagash has no Damaged X ability.

- Points and unit sizes (5 Wardens and 3 Sentinels only so far).
- Sentinels can field two Nadirite Annihilators (one Sentinel and the Hekatos); the Hekatos' Annihilator is BS 3+ as
  printed, not 2+ like his other weapons. Kept as written.
