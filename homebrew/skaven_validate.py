"""Check the built Skaven catalogue against the handoff data.

Usage: python3 homebrew/skaven_validate.py --source /path/to/handoff --catalogue 'Chaos%20-%20Skaven.json'
Prints every mismatch and exits non-zero if there are any.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skaven_build import (DETACHMENTS, CLAN_UNIQUE, POINTS, ENHANCEMENT_SLOT, DP, cards, sections, title,  # noqa
                          weapon_keyword, walk)

ROOT = Path(__file__).resolve().parent.parent
OLD_TERMS = ["Knawhole", "Ogre", "Peril", "manifest", "Battle-shock test", "Hazardous test", "Burn-Burn Warpstone",
             "Terrifying Monstrosity", "Casting Value", "Verminous Spells", "Expendable Vermin", "Tribute to Ruin"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--system", default=str(ROOT / "Warhammer 40,000.json"))
    args = parser.parse_args()
    source = Path(args.source)
    cat = json.loads(Path(args.catalogue).read_text())["catalogue"]
    system = json.loads(Path(args.system).read_text())["gameSystem"]
    data = json.loads((source / "datasheets.json").read_text())
    points = {e["name"]: e for g in json.loads((source / "points.json").read_text())["points"] for e in g["entries"]}
    problems, checks = [], 0

    def check(ok, message):
        nonlocal checks
        checks += 1
        if not ok:
            problems.append(message)

    entries = {e["name"]: e for e in cat["sharedSelectionEntries"]}
    root = {l["name"] for l in cat["entryLinks"]}

    # -- structure: unique IDs and resolvable links
    ids = [n["id"] for n in walk(cat) if isinstance(n, dict) and "id" in n and isinstance(n["id"], str)]
    dupes = {i for i in ids if ids.count(i) > 1}
    check(not dupes, f"Duplicate IDs: {sorted(dupes)[:10]}")
    known = set(ids) | {n["id"] for n in walk(system) if isinstance(n, dict) and "id" in n}
    for link in cat.get("catalogueLinks", []):
        name = link["name"]
        for f in ROOT.glob("*.json"):
            try:
                other = json.loads(f.read_text())
            except Exception:
                continue
            body = other.get("catalogue") or {}
            if body.get("id") == link["targetId"]:
                known |= {n["id"] for n in walk(body) if isinstance(n, dict) and "id" in n}
    for n in walk(cat):
        if isinstance(n, dict) and "targetId" in n:
            check(n["targetId"] in known, f"Unresolved link {n.get('name')} -> {n['targetId']}")
        if isinstance(n, dict) and n.get("childId") not in (None, "any", "model", "unit", "upgrade"):
            check(n["childId"] in known, f"Unresolved condition childId {n['childId']}")

    # -- datasheets
    for ds in data:
        name = ds["name"]
        e = entries.get(name)
        check(e is not None and name in root, f"{name}: missing datasheet")
        if not e:
            continue
        profiles = [p for p in walk(e) if isinstance(p, dict) and p.get("typeName") == "Unit"]
        stats = {c["name"]: c["$text"] for c in profiles[0]["characteristics"]}
        want = dict(M=ds["profile"]["M"], T=ds["profile"]["T"], Sv=ds["profile"]["SV"], LD=ds["profile"]["LD"],
                    OC=ds["profile"]["OC"], InSv=ds["profile"].get("INV", "-") or "-")
        for k, v in want.items():
            check(stats[k] == v, f"{name}: {k} is {stats[k]}, expected {v}")
        weapons = {}
        for p in walk(e):
            if isinstance(p, dict) and p.get("typeName") in ("Ranged Weapons", "Melee Weapons"):
                weapons.setdefault(p["name"], []).append([c["$text"] for c in p["characteristics"]])
        for w in ds["ranged_weapons"] + ds["melee_weapons"]:
            want = [w["range"], w["A"], w["BS_WS"], w["S"], w["AP"], w["D"],
                    ", ".join(weapon_keyword(k) for k in w["keywords"]) or "-"]
            got = weapons.get(w["name"])
            check(bool(got), f"{name}: weapon {w['name']} missing")
            if got:
                check(all(g == want for g in got), f"{name}: weapon {w['name']} is {got[0]}, expected {want}")
        abilities = {p["name"] for p in walk(e) if isinstance(p, dict) and p.get("typeName") == "Abilities"}
        for a in ds["abilities"]:
            if a["name"] in ("CORE", "FACTION"):
                continue
            label = "Psyker" if a["name"] == "PSYKER" else title(a["name"])
            check(label in abilities, f"{name}: ability {label} missing")
        for o in ds["other_rules"]:
            check(title(o["name"]) in abilities, f"{name}: rule {o['name']} missing")
        # points: base + size increments
        base = next(c["value"] for c in e["costs"] if c["typeId"] == POINTS)
        increments = [m["value"] for m in e.get("modifiers", []) if m.get("field") == POINTS and "conditions" in m]
        expected = [int(x) for x in re.findall(r"(\d+)pts", points[name]["points"])]
        per_model = "per model" in points[name]["points"]
        if per_model:
            model_costs = [c["value"] for m in e.get("selectionEntries", []) if m["type"] == "model"
                           for c in m.get("costs", []) if c["typeId"] == POINTS]
            check(set(model_costs) == set(expected), f"{name}: per-model cost {model_costs}, expected {expected}")
        else:
            tiers = [base]
            for inc in increments:
                tiers.append(tiers[-1] + inc)
            check(tiers == expected, f"{name}: points {tiers}, expected {expected}")
        rep = re.match(r"\+(\d+)pts from the (\d+)", points[name]["repeat_cost"])
        mods = [m for m in e.get("modifiers", []) if m.get("field") == POINTS and "conditionGroups" in m
                and not m["conditionGroups"][0].get("conditions")]
        if rep:
            check(len(mods) == 1 and mods[0]["value"] == int(rep.group(1)) and
                  mods[0]["conditionGroups"][0]["localConditionGroups"][0]["value"] == int(rep.group(2)) - 1,
                  f"{name}: repeat cost wrong, expected {points[name]['repeat_cost']}")
        else:
            check(not mods, f"{name}: unexpected repeat cost")
        limit = next(c["value"] for c in e["constraints"] if c["scope"] == "roster")
        want_limit = 1 if "EPIC HERO" in ds["keywords"] else 6 if "BATTLELINE" in ds["keywords"] else 3
        check(limit == want_limit, f"{name}: copy limit {limit}, expected {want_limit}")
        cats = {c["name"] for c in e["categoryLinks"]}
        for kw in ds["keywords"]:
            check(any(c.casefold() == kw.casefold() for c in cats), f"{name}: keyword {kw} missing")

    # mounts carry the full mounted price
    for unit, mount, total in (("Grey Seer", "Screaming Bell", 210), ("Clawlord", "Gnaw-beast", 130),
                               ("Plague Priest", "Plague Furnace", 190)):
        e = entries[unit]
        m = next(n for n in walk(e) if isinstance(n, dict) and n.get("name") == mount and "costs" in n)
        check(e["costs"][0]["value"] + m["costs"][0]["value"] == total, f"{unit} on {mount}: not {total}pts")
    flag = next(g for g in entries["Vermindoom Land-Fortress"]["selectionEntryGroups"] if g["name"] == "Clan Flagship")
    check(sorted(o["costs"][0]["value"] for o in flag["selectionEntries"]) == [0, 40, 40, 50, 60, 60],
          "Vermindoom flagship prices wrong")
    check("Verminlord" not in entries, "Old single Verminlord datasheet still present")

    # -- detachments, enhancements, stratagems
    group = entries["Detachment"]["selectionEntryGroups"][0]["selectionEntries"]
    check(len(group) == 17, f"{len(group)} detachments, expected 17")
    strat_rules = [r["name"] for r in cat["sharedRules"] if " — " in r["name"]]
    for d in group:
        dp, dispositions = DETACHMENTS[d["name"]]
        check(d["costs"][0]["value"] == dp, f"{d['name']}: DP")
        tags = {c["name"] for c in d["categoryLinks"]}
        check(set(dispositions) <= tags, f"{d['name']}: dispositions {tags}")
        check(("Unique: CLAN" in tags) == (d["name"] in CLAN_UNIQUE), f"{d['name']}: Unique: CLAN tag")
    enh = {e["name"].replace(" [Upgrade]", ""): e for e in cat["sharedSelectionEntries"]
           if any(c["typeId"] == ENHANCEMENT_SLOT for c in e.get("costs", []))}
    for path in sorted((source / "detachments").glob("*.md")):
        text = path.read_text()
        det = re.search(r"^# (.+)$", text, flags=re.M).group(1)
        for heading, lines in sections(text):
            if heading and "Enhancements" in heading:
                for card in cards(lines):
                    e = enh.get(card["name"])
                    check(e is not None, f"{det}: enhancement {card['name']} missing")
                    if e:
                        pts = next(c["value"] for c in e["costs"] if c["typeId"] == POINTS)
                        check(f"[{pts} pts]" == f"[{card['cost']}]", f"{card['name']}: {pts}pts vs {card['cost']}")
            if heading and "Stratagems" in heading:
                for card in cards(lines):
                    check(any(r.startswith(f"{det} — {card['name']} /") for r in strat_rules),
                          f"{det}: stratagem {card['name']} missing")

    # -- leftover terms
    text = json.dumps(cat, ensure_ascii=False)
    for term in OLD_TERMS:
        hits = re.findall(r".{0,40}" + re.escape(term) + r".{0,40}", text)
        check(not hits, f"Old term '{term}': {hits[:2]}")
    check("Sonic" not in text, "Sonic mention")

    print(f"{checks} checks, {len(problems)} problems")
    for p in problems:
        print(" -", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
