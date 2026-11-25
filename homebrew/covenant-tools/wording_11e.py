#!/usr/bin/env python3
"""11th-edition wording pass over the Covenant source (datasheets, detachments, army rules).

- 11e terms: hit/wound/charge/advance rolls, critical hits, normal/advance/fall-back/charge/surge moves, engaged and
  unengaged, battle-shock rolls, save rolls, below starting strength, A/S/AP/D/OC/Ld/M/Sv characteristics, inches as ".
- Weapon abilities in prose in [BRACKETS]; keywords in CAPITALS where a rule names them (COVENANT INFANTRY unit).
- Sentences that only repeat another rule are removed (the Upgrade limit, Stealth, Shield regeneration on vehicles,
  once-per-phase Stratagem limits, "these effects cease when this model is destroyed", ...).
- The wordiest rules are rewritten by hand (REWRITES), keeping their effect.

Usage: python3 homebrew/covenant-tools/wording_11e.py --source homebrew/covenant-source [--report report.txt]
"""
import argparse
import json
import re
from pathlib import Path

# ---------------------------------------------------------------- sentences that only repeat other rules
REMOVE = [
    r"\s*Up to three eligible units can purchase this Upgrade; each pays separately, but all copies collectively "
    r"occupy one Enhancement selection\.",                                             # 11e Upgrades rule
    r"\s*Pay the points shown on each added model's entry\.",
    r"\s*These weapon exchanges are free\.",
    r"\s*This model can take one Specialist ability from this entry, paying the points shown\.",  # army rule
    r"\s*Unless every visible model in this unit is equipped with a Stealth Projector, this wargear does not "
    r"confer Stealth to models without it\.",                                          # 11e Stealth: every model
    r"\s*These effects cease when this model is destroyed\.",                          # 11e attached-unit abilities
    r"\s*These effects are cumulative\.",
    r"\s*A model cannot be repaired by this Stratagem more than once per Command phase\.",  # once per phase
    r"\s*Automatically successful Hit rolls cannot trigger this ability\.",            # no roll, no critical hit
    r"\s*This use does not prevent another unit from using the same Doctrine in that battle round\.",
    r"\s*These effects apply in the Shooting and Fight phases\.",
    r"\s*At the start of this model's owner's Command phase, it regains D3\+1 lost SP, up to its starting SP\.",
    r"\s*At the start of its owner's Command phase, it regains D3\+1 lost SP instead of D3\.",  # VEHICLE: D3+1
]
REPLACE = [
    (r" and does not stop another unit from using the same Doctrine in that battle round", ""),
    (r"At the start of this model's owner's Command phase, it regains (D3\+2|D6\+\d+) lost SP, up to its starting "
     r"SP\.", r"Regenerating Shields gives this unit \1 lost SP instead of D3+1."),
    (r"You can only use this Stratagem once per battle\.", "You cannot use this Stratagem more than once per battle."),
]

# ---------------------------------------------------------------- 11e terms (applied in order)
TERMS = [
    (r"\b(\d+) inches\b", r'\1"'),
    (r"\bnot within Engagement Range of any enemy units?\b", "unengaged"),
    (r"\bnot within Engagement Range\b", "unengaged"),
    (r"\bwithin Engagement Range of one or more enemy units\b", "engaged"),
    (r"\bEngagement Range\b", "engagement range"),
    (r"\bre-roll Battle-shock and Leadership tests taken for it\b", "re-roll battle-shock rolls made for it"),
    (r"\btakes? a Battle-shock test\b", lambda m: m.group(0).replace("take", "make").replace(
        "Battle-shock test", "battle-shock roll")),
    (r"\bBattle-shock tests taken for\b", "battle-shock rolls made for"),
    (r"\bBattle-shock tests\b", "battle-shock rolls"),
    (r"\bBattle-shock test\b", "battle-shock roll"),
    (r"\bBattle-shock", "battle-shock"),
    (r"\bsaving throws\b", "save rolls"),
    (r"\bsaving throw\b", "save roll"),
    (r"\b(Hit|Wound|Charge|Advance) (rolls?)\b", lambda m: m.group(1).lower() + " " + m.group(2)),
    (r"\bHit and Wound rolls\b", "hit and wound rolls"),
    (r"\bAdvance and Charge rolls\b", "advance and charge rolls"),
    (r"\bCritical (Hits?|Wounds?)\b", lambda m: "critical " + m.group(1).lower()),
    (r"\bNormal, Advance, Fall Back or Charge move\b", "normal, advance, fall-back or charge move"),
    (r"\bNormal, Advance or Fall Back move\b", "normal, advance or fall-back move"),
    (r"\bNormal or Advance move\b", "normal or advance move"),
    (r"\b(Normal|Advance|Charge|Surge) move\b", lambda m: m.group(1).lower() + " move"),
    (r"\bFall Back move\b", "fall-back move"),
    (r"\bin a turn in which it Advanced or Fell Back\b", "in a turn in which it made an advance or fall-back move"),
    (r"\bin a turn in which it Advanced\b", "in a turn in which it made an advance move"),
    (r"\bin a turn in which it Fell Back\b", "in a turn in which it made a fall-back move"),
    (r"\bafter Falling Back\b", "after making a fall-back move"),
    (r"\bafter Advancing\b", "after making an advance move"),
    (r"\bselected to Fall Back\b", "selected to make a fall-back move"),
    (r"\bselected to Advance\b", "selected to make an advance move"),
    (r"\bcannot Fall Back\b", "cannot make a fall-back move"),
    (r"\bAdvances, do not roll\b", "makes an advance move, do not make an advance roll"),
    (r"\b(unit|model) Advances\b", r"\1 makes an advance move"),
    (r"\bit Advanced\b", "it made an advance move"),
    (r"\bthis model Advanced\b", "this model made an advance move"),
    (r"\bcounts as having Advanced\b", "counts as having made an advance move"),
    (r"\bAdvance and charge rolls\b", "advance and charge rolls"),
    (r"\b(D\d(?:\+\d+)?) inches\b", r'\1"'),
    (r"\bMove characteristics\b", "M characteristics"),
    (r"\bactivates? (its )?Shield Regeneration\b", lambda m: m.group(0).split(" ")[0].replace("activates", "resolves")
     .replace("activate", "resolve") + " Regenerating Shields"),
    (r"\bShielding rolls made for models in (your|that) unit are successful on a 2\+",
     r"Shield Saves made for models in \1 unit succeed on a 2+"),
    (r"\bRemained Stationary\b", "remained stationary"),
    (r"\bBelow Starting Strength\b", "below starting strength"),
    (r"\bBelow Half-strength\b", "below half-strength"),
    (r"\bStarting Strength\b", "starting strength"),
    (r"\bStrategic Reserves\b", "strategic reserves"),
    (r"\bfrom Reserves\b", "from reserves"),
    (r"\bConsolidates\b", "consolidates"),
    (r"\bSave and Leadership characteristics\b", "Sv and Ld characteristics"),
    (r"\bArmour Penetration characteristic\b", "AP characteristic"),
    (r"\bAttacks characteristic\b", "A characteristic"),
    (r"\bStrength characteristic\b", "S characteristic"),
    (r"\bDamage characteristic\b", "D characteristic"),
    (r"\bObjective Control characteristic\b", "OC characteristic"),
    (r"\bLeadership characteristic\b", "Ld characteristic"),
    (r"\bMove characteristic\b", "M characteristic"),
    (r"\bSave characteristic\b", "Sv characteristic"),
    (r"\bToughness characteristic\b", "T characteristic"),
    (r"\bWounds characteristic\b", "W characteristic"),
    (r"\bPsychic Wounds\b", "psychic attacks"),
]

# Weapon abilities named in prose -> [BRACKETS]
WEAPON_ABILITIES = [
    r"Lethal Hits", r"Sustained Hits(?: \d)?", r"Precision", r"Ignores Cover", r"Devastating Wounds",
    r"Anti-[A-Za-z]+ \d\+", r"Hazardous", r"Indirect Fire", r"Rapid Fire \d", r"Extra Attacks",
    r"Twin-linked(?! Energy)", r"One Shot",
]

KEYWORDS = ["Dedicated Transport", "Special Operations", "Epic Hero", "Jump Pack", "Drone Swarm", "Covenant", "Grunt",
            "Elite", "Jackal", "Drone", "Hunter", "Engineer",
            "Infantry", "Grenades", "Fly", "Character", "Sangheili", "Vehicle", "Jiralhanae", "Brute", "Yig-Yar",
            "Transport", "Unggoy", "San'Shyuum", "T'vaoan", "Battleline", "Mgalekgolo", "Lekgolo", "Mounted",
            "Titanic", "Walker", "Yanme'e", "Huragok", "Aircraft", "Fortification", "Monster", "Towering",
            "Artillery"]
KW = "(?:" + "|".join(re.escape(k) for k in sorted(KEYWORDS, key=len, reverse=True)) + ")"
KW_RUN = re.compile(rf"\b{KW}(?:(?:\s+|,\s*|\s+(?:or|and)\s+|/){KW})*(?=\s+(?:units?|models?|keywords?)\b)")
NON_KW = re.compile(rf"\bnon-({KW})\b")
# "against Infantry", "against Monsters and Vehicles" (11e: singular and plural keywords work the same way)
AGAINST_KW = re.compile(rf"\bagainst ((?:{KW})s?(?:(?:, | or | and )(?:{KW})s?)*)\b")

# ---------------------------------------------------------------- hand rewrites, keyed by (owner, rule name)
REWRITES = {
    ("The Great Journey", "Fanatical Doctrines"): [
        "SAN'SHYUUM models from your army have the following ability.",
        "**Voice of the Great Journey:** At the start of any phase, this model can issue one Fanatical Doctrine "
        "it has not issued this turn to one friendly COVENANT INFANTRY unit within 6\" that is not affected by a "
        "Fanatical Doctrine. Until the end of the phase, that unit is affected by that Doctrine. Each SAN'SHYUUM "
        "model can issue one Fanatical Doctrine per phase. A unit can be affected by one Caste Doctrine and one "
        "Fanatical Doctrine at the same time.",
        "**Shielded by Faith:** Models in this unit have a 4+ invulnerable save.\n"
        "**Claim the Sacred Path:** Add 2 to the OC characteristic of models in this unit.\n"
        "**Armour of the Faithful:** Improve the Sv characteristic of models in this unit by 1 (to a maximum of 2+)."],
    ("The Great Journey", "Devoted Sergeants"): [
        "UNGGOY Sergeant models from your army have the following ability.",
        "**Fanatical Preacher:** At the start of any phase, instead of issuing a Caste Doctrine this battle round, "
        "this model can issue one Fanatical Doctrine to its unit."],
    ("Covenant Expeditionary Force", "Integrated Battle Groups"): [
        "Line Elements are friendly COVENANT INFANTRY and MOUNTED units. Support Elements are friendly COVENANT "
        "VEHICLE and MONSTER units.",
        "After a Line Element has made its attacks, select one enemy unit it hit: that unit is Designated until "
        "the end of the phase. After a Support Element has made its attacks, select one enemy unit it hit: that "
        "unit is Suppressed until the end of the phase.",
        "Each time a model in a Support Element attacks a Designated unit, add 1 to the hit roll. Each time a model "
        "in a Line Element attacks a Suppressed unit, improve the AP characteristic of that attack by 1."],
    ("Yig-Yar Hunting Talon", "Scuttle to Cover"): [
        "Once per battle round, each time a friendly YIG-YAR unit is selected as the target of one or more ranged "
        "attacks, before those attacks are made, it can make a normal move of up to D6+2\". The attacking unit can "
        "then select new targets for any of its attacks. Each YIG-YAR unit can do this once per battle round."],
}
STRATAGEM_REWRITES = {
    ("Sangheili Warhost", "Honour Duel"): dict(
        target="One SANGHEILI CHARACTER unit within engagement range of one or more enemy CHARACTER units.",
        effect="Select one SANGHEILI CHARACTER model in your unit and one enemy CHARACTER model within engagement "
               "range of it. Your opponent accepts or refuses the duel.\n"
               "■ Accepted: until both models have fought, each can only make melee attacks against the other, and "
               "other attacks cannot be allocated to either of them. If either would be reduced to 0 wounds by the "
               "other before it has fought, it is left with 1 wound and is destroyed after it has fought. If your "
               "unit is Exultant, add 1 to the D characteristic of your model's melee weapons.\n"
               "■ Refused: until the end of the phase, models in your unit can re-roll hit and wound rolls for "
               "melee attacks that target that enemy CHARACTER's unit."),
}


def bracket_weapon_abilities(text):
    for pattern in WEAPON_ABILITIES:
        text = re.sub(rf"(?<![\[\w-])({pattern})(?![\]\w])", lambda m: "[" + m.group(1).upper() + "]", text)
    return text


def capitalise_keywords(text):
    text = KW_RUN.sub(lambda m: m.group(0).upper().replace(" OR ", " or ").replace(" AND ", " and "), text)
    text = AGAINST_KW.sub(lambda m: "against " + m.group(1).upper().replace(" OR ", " or ").replace(" AND ", " and "),
                          text)
    text = re.sub(r"\bFly\b", "FLY", text)
    return NON_KW.sub(lambda m: "non-" + m.group(1).upper(), text)


def clean(text, keywords=True):
    original = text
    for pattern in REMOVE:
        text = re.sub(pattern, "", text)
    for pattern, repl in REPLACE + TERMS:
        text = re.sub(pattern, repl, text)
    text = bracket_weapon_abilities(text)
    if keywords:
        text = capitalise_keywords(text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
    return text, text != original


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--report")
    a = ap.parse_args()
    src = Path(a.source)
    data = json.loads((src / "datasheets.json").read_text())
    dets = json.loads((src / "detachments.json").read_text())
    report, words = [], [0, 0]

    def do(label, text, keywords=True):
        new, changed = clean(text, keywords)
        words[0] += len(text.split())
        words[1] += len(new.split())
        if changed:
            report.append(f"## {label}\n- {text}\n+ {new}\n")
        return new

    for ds in data:
        for field in ("abilities", "wargear", "specialist_abilities"):
            kept = []
            for item in ds.get(field, []):
                if item["name"] == "Core":
                    kept.append(item)
                    continue
                item["text"] = do(f"{ds['name']} / {item['name']}", item["text"])
                if item["text"]:
                    kept.append(item)
                else:
                    report.append(f"## {ds['name']} / {item['name']}\n  removed: it only repeated Regenerating Shields\n")
            if field in ds:
                ds[field] = kept
        for field in ("rules_notes", "unit_composition", "wargear_options"):
            ds[field] = [t for t in (do(f"{ds['name']} / {field}", t, keywords=field == "rules_notes")
                                     for t in ds[field]) if t]
    for det in dets:
        for rule in det["rules"]:
            key = (det["name"], rule["name"])
            if key in REWRITES:
                before = " ".join(rule["text"])
                rule["text"] = REWRITES[key]
                words[0] += len(before.split())
                words[1] += len(" ".join(rule["text"]).split())
                report.append(f"## [{det['name']}] {rule['name']} (rewritten)\n- {before}\n+ "
                              + " / ".join(rule["text"]) + "\n")
            else:
                rule["text"] = [do(f"[{det['name']}] {rule['name']}", t) for t in rule["text"]]
        det["rules_intro"] = [do(f"[{det['name']}] intro", t) for t in det["rules_intro"]]
        det["enhancements_intro"] = [do(f"[{det['name']}] enhancements intro", t) for t in det["enhancements_intro"]]
        for e in det["enhancements"]:
            e["text"] = [t for t in (do(f"[{det['name']}] {e['name']}", t) for t in e["text"]) if t]
            if e.get("restriction"):
                e["restriction"] = do(f"[{det['name']}] {e['name']} restriction", e["restriction"])
        for s in det["stratagems"]:
            override = STRATAGEM_REWRITES.get((det["name"], s["name"]), {})
            for k in ("when", "target", "effect", "restriction"):
                if k in override:
                    words[0] += len(s[k].split())
                    s[k] = override[k]
                    words[1] += len(s[k].split())
                    report.append(f"## [{det['name']}] {s['name']} {k} (rewritten)\n+ {s[k]}\n")
                elif s.get(k):
                    s[k] = do(f"[{det['name']}] {s['name']} {k}", s[k])
    (src / "datasheets.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    (src / "detachments.json").write_text(json.dumps(dets, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(report)} texts changed; {words[0]} -> {words[1]} words")
    if a.report:
        Path(a.report).write_text("\n".join(report))


if __name__ == "__main__":
    main()
