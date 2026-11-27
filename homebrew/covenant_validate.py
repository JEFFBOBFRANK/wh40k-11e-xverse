"""Check the built Covenant catalogue against its source files.

Usage: python3 homebrew/covenant_validate.py --source homebrew/covenant-source --catalogue 'Xenos - Covenant (Homebrew).json'
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from covenant_units import MODELS, UNITS  # noqa: E402
from covenant_build import DOCTRINE_RULES, OWN_SPECIES_ALLOWED, SERGEANT_DOCTRINES, UNIT_KEYWORD  # noqa: E402

problems = []
POINTS_ID = "51b2-306e-1021-d207"
checks = 0


def check(ok, message):
    global checks
    checks += 1
    if not ok:
        problems.append(message)


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--catalogue", required=True)
    args = parser.parse_args()
    source = Path(args.source)
    data = json.loads((source / "datasheets.json").read_text())
    dets = json.loads((source / "detachments.json").read_text())
    cat = json.loads(Path(args.catalogue).read_text())["catalogue"]
    entries = {e["name"]: e for e in cat["sharedSelectionEntries"]}
    rules = {r["id"]: r for r in cat["sharedRules"]}
    roots = {l["targetId"] for l in cat["entryLinks"]}

    for ds in data:
        name = ds["name"]
        reference = ds["category"] in ("SERGEANT", "AUXILIARY")
        check(name in entries, f"{name}: missing entry")
        if name not in entries:
            continue
        e = entries[name]
        check((e["id"] in roots) != reference, f"{name}: root link wrong (reference models are not units)")
        profiles = [p for p in walk(e) if isinstance(p, dict) and p.get("typeName")]
        units = [p for p in profiles if p["typeName"] == "Unit"]
        check(units, f"{name}: no Unit profile")
        if units:
            stats = {c["name"]: c["$text"] for c in units[0]["characteristics"]}
            for key, src in (("M", "M"), ("T", "T"), ("Sv", "SV"), ("W", "W"), ("LD", "LD"), ("OC", "OC")):
                check(stats.get(key) == ds["profile"].get(src), f"{name}: {key} {stats.get(key)} != {ds['profile'].get(src)}")
        names = {p["name"] for p in profiles}
        spec = (MODELS if reference else UNITS)[name]
        for w in ds["ranged_weapons"] + ds["melee_weapons"]:
            check(w["name"] in names, f"{name}: weapon {w['name']} not offered")
        for a in ds["abilities"]:
            if a["name"] in ("Core", ""):
                continue
            if a["name"] == "Caste Doctrines" and ds["category"] == "SERGEANT":  # shown as the Doctrines themselves
                shown = {p["name"] for p in profiles if p["typeName"] == "Caste Doctrines"}
                for doctrine in re.findall(r"issue (.+)\.$", a["text"])[0].replace(" or ", ", ").split(", "):
                    check(doctrine in shown, f"{name}: Caste Doctrine {doctrine} not shown")
                continue
            check(a["name"] in names, f"{name}: ability {a['name']} missing")
        if ds["category"] == "SERGEANT":
            check(name in SERGEANT_DOCTRINES and any(p["typeName"] == "Caste Doctrines" for p in profiles),
                  f"{name}: no Caste Doctrines box")
        if ds["category"] == "AUXILIARY":
            check(not any(p["typeName"] == "Abilities" for p in profiles),
                  f"{name}: an ability is outside the Auxiliary box")
        for g in ds["wargear"]:
            if g["name"] in [x for x in ds["equipped"]] or any(g["name"] in o for o in ds["wargear_options"]):
                check(g["name"] in names, f"{name}: wargear {g['name']} missing")
        sp = ds["profile"].get("SP")
        if sp:
            shields = [p for p in profiles if p["typeName"] == "Shields"]
            check(any(p["characteristics"][0]["$text"] == sp for p in shields) or
                  any("starting SP value" in g["text"] for g in ds["wargear"]), f"{name}: SP {sp} not shown")
        cost = e.get("costs", [{}])[0].get("value")
        if not reference:
            expected = 0 if spec.get("per_model") else ds["points"]
            check(cost == expected, f"{name}: points {cost} != {expected}")
            cats = {c["name"] for c in e.get("categoryLinks", [])}
            for kw in ds["keywords"]:
                check(any(c.casefold() == kw.casefold() for c in cats), f"{name}: keyword {kw} missing")
            check("Faction: Covenant" in cats, f"{name}: faction missing")
            copies = next((c["value"] for c in e["constraints"] if c["scope"] == "roster" and c["type"] == "max"
                           and c["field"] == "selections"), None)
            want = 1 if "Epic Hero" in ds["keywords"] else 6 if "Battleline" in ds["keywords"] else 3
            check(copies == want, f"{name}: copy limit {copies}, expected {want}")
            m = re.match(r"\+(\d+)pts from the (\d+)\w\w copy", ds.get("repeat_cost") or "")
            if m:
                steps = [x for x in e.get("modifiers", []) if x.get("type") == "increment" and x.get("value") == int(m.group(1))
                         and any(g.get("value") == int(m.group(2)) - 1 for cg in x.get("conditionGroups", [])
                                 for g in cg.get("localConditionGroups", []))]
                check(steps, f"{name}: points step {ds['repeat_cost']} missing")
            if ds["leader"]:
                check(e.get("associations"), f"{name}: Leader links missing")
        else:
            check(cost == ds["points"], f"{name}: model points {cost} != {ds['points']}")
            for a in ds.get("specialist_abilities", []):
                option = next((n for n in walk(e) if n.get("type") == "upgrade" and
                               any(p.get("name") == a["name"] for p in n.get("profiles", []))), None)
                check(option is not None, f"{name}: Specialist ability {a['name']} missing")
                pts = next((c["value"] for c in (option or {}).get("costs", []) if c["name"] == "pts"), 0)
                check(pts == a["points"], f"{name}: {a['name']} costs {pts}, expected {a['points']}")

    # Tormentor layout: every Auxiliary in a unit is a set of model types, with its Specialist abilities offered
    by_ds = {d["name"]: d for d in data}
    for uname, spec in UNITS.items():
        unit = entries.get(uname)
        if not unit:
            continue
        nodes = list(walk(unit))
        groups = [g for g in unit.get("selectionEntryGroups", [])]
        serg = next((g for g in groups if g["name"] == "Sergeant"), None)
        if spec["sergeants"]:
            check(serg is not None and serg.get("sortIndex") == (1 if spec["single"] else 0),
                  f"{uname}: Sergeant group not on top")
        for pool in spec["aux"]:
            members = list(pool["entries"]) + [d["name"] for d in data if d["category"] == "AUXILIARY"
                                               and any(l in d["keywords"] for l in pool["lists"])
                                               and d["name"] not in pool["entries"]]
            own = set() if uname in OWN_SPECIES_ALLOWED else {k for k in by_ds[uname]["keywords"]
                                                               if k in UNIT_KEYWORD.values()}
            members = [m for m in members if not any(UNIT_KEYWORD.get(k) in own for k in by_ds[m]["keywords"])]
            offered = {l["name"] for g in unit.get("selectionEntryGroups", []) if g["name"].startswith("Auxiliary")
                       for l in g.get("entryLinks", [])}
            for name in offered:
                check(not any(UNIT_KEYWORD.get(k) in own for k in by_ds[name]["keywords"]),
                      f"{uname}: offers {name}, an Auxiliary of its own species")
            for m in dict.fromkeys(members):
                if any(n.get("type") == "selectionEntry" and n.get("name") == m and n.get("targetId") ==
                       entries.get(m, {}).get("id") for n in nodes):
                    continue  # added with "+", weapons and Specialist ability chosen on the model itself
                types = [n for n in nodes if n.get("type") == "model" and
                         (n.get("name") == m or str(n.get("name", "")).startswith(m + " with "))]
                check(types, f"{uname}: no {m} model types")
                for a in by_ds[m].get("specialist_abilities", []):
                    if a.get("replaces_weapons"):
                        ok = any(t["name"] == f"{m} with {a['name']}" for t in types)
                    else:
                        ok = any(n.get("type") == "upgrade" and n.get("associations") and
                                 next((c["value"] for c in n.get("costs", []) if c["name"] == "pts"), 0) == a["points"] and
                                 any(p.get("name") == a["name"] for p in walk(n) if isinstance(p, dict)
                                     and p.get("typeName")) for n in nodes)
                    check(ok, f"{uname}: {m} Specialist ability {a['name']} missing")

    det_entry = entries["Detachment"]
    options = det_entry["selectionEntryGroups"][0]["selectionEntries"]
    check(len(options) == len(dets) == 18, f"{len(options)} detachments, expected 18")
    by_name = {o["name"]: o for o in options}
    strat_ref = entries["Stratagem References"]
    strat_names = {rules[l["targetId"]]["name"] for l in strat_ref["infoLinks"]}
    for d in dets:
        o = by_name.get(d["name"])
        check(o is not None, f"{d['name']}: detachment missing")
        if not o:
            continue
        check(o["costs"][0]["value"] == d["dp"], f"{d['name']}: DP")
        cats = {c["name"] for c in o["categoryLinks"]}
        for disp in (d["disposition"] if isinstance(d["disposition"], list) else [d["disposition"]]):
            check(disp in cats, f"{d['name']}: disposition {disp} missing")
        if d["unique"]:
            check(f"Unique: {d['unique'].upper()}" in cats, f"{d['name']}: unique tag missing")
        check({r["name"] for r in o["rules"]} == {r["name"] for r in d["rules"]}, f"{d['name']}: rules differ")
        for en in d["enhancements"]:
            ename = en["name"] + (" [Upgrade]" if en["upgrade"] else "")
            check(ename in entries, f"{d['name']}: enhancement {ename} missing")
            linked = sum(1 for n in walk(cat["sharedSelectionEntries"]) if isinstance(n, dict)
                         and n.get("targetId") == entries.get(ename, {}).get("id"))
            check(linked > 0, f"{d['name']}: enhancement {ename} on no unit")
            pts = next(c["value"] for c in entries[ename]["costs"] if c["name"] == "pts") if ename in entries else None
            check(pts == en["points"], f"{ename}: points {pts} != {en['points']}")
        for s in d["stratagems"]:
            check(f"{d['name']} — {s['name']} / {s['cp']} CP" in strat_names, f"{d['name']}: stratagem {s['name']}")
    frame = next(r["id"] for r in rules.values() if r["name"] == "Frame")
    for ds in data:
        if "Frame" in ds["keywords"] and ds["name"] in entries:
            check(any(l.get("targetId") == frame for l in entries[ds["name"]].get("infoLinks", [])),
                  f"{ds['name']}: Frame rule not linked")
    chosen = next(r["id"] for r in rules.values() if r["name"] == "Chosen of the Hierarchs")
    for n in ("Rtas 'Vadum", "Sangheili Shipmaster", "Prophet of Truth"):
        check(any(l.get("targetId") == chosen for l in entries[n].get("infoLinks", [])),
              f"{n}: Chosen of the Hierarchs missing")
    army = entries["Army Rules and References"]
    army_names = {rules[l["targetId"]]["name"] for l in army["infoLinks"]}
    for n in ("Caste Hierarchy", "Shielding Trait", "Caste Doctrines", *DOCTRINE_RULES, "Supercombine", "Plasma",
              "Conversion", "Gravity Slam", "Siegebreaker", "Transport Space"):
        check(n in army_names, f"army rule {n} missing")
    text = json.dumps(cat)
    for old in ("400 points", "50% of its Non-Auxiliary"):
        if old in text:
            print("NOTE: still printed:", old)
    # points are always multiples of 5: costs and points modifiers alike
    for n in walk(cat):
        if not isinstance(n, dict):
            continue
        for co in n.get("costs", []) or []:
            if co.get("name") == "pts":
                check(co["value"] % 5 == 0, f"{n.get('name')}: {co['value']} pts is not a multiple of 5")
        if n.get("field") == POINTS_ID and isinstance(n.get("value"), (int, float)):
            check(n["value"] % 5 == 0, f"points modifier {n['value']} is not a multiple of 5")
    print(f"{checks} checks, {len(problems)} problems")
    for p in problems:
        print(" -", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
