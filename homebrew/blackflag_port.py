#!/usr/bin/env python3
"""Rebuild the Ork, Drukhari and Corsair units of Index: Black-Flag as editable datasheets.

The Black-Flag index printed these units as flat entries (one stat line, no models or wargear choices). This
copies each unit from its source catalogue (Orks, Aeldari Library) with its real model entries, weapon choices,
unit sizes and repeat costs, the same way blackflag_csm_port.py rebuilt the Chaos Space Marine units. Then:

- 11th-edition stats, weapon profiles and points come from the IRONBUILT dataset where the repo's source
  catalogue is older (Orks).
- Abilities use the Black-Flag wording (SKURVY instead of the source faction, Plunder instead of Pain). Source
  abilities that only work with that faction's own units (e.g. Raider: Speed of the Kill) are left out.
- The units keep their Black-Flag IDs and Faction: Skurvy. Leader and Support links follow the LEADER / SUPPORT
  lists printed on the Black-Flag datasheets, or the source datasheet's list where Black-Flag prints none.

    python3 homebrew/blackflag_port.py --index 'Index - Black-Flag (Homebrew).json' --system 'Warhammer 40,000.json' \
        --ironbuilt wh40k-11e.json --output 'Index - Black-Flag (Homebrew).json'
"""
import argparse
import copy
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blackflag_csm_port as csm_port  # noqa: E402
from blackflag_csm_port import nid, walk  # noqa: E402

# Black-Flag name -> (source catalogue, source name, IRONBUILT faction)
UNITS = {
    "Big Mek": ("Orks.json", "Big Mek", "Orks"),
    "Big Mek with Shokk Attack Gun": ("Orks.json", "Big Mek with Shokk Attack Gun", "Orks"),
    "Mek": ("Orks.json", "Mek", "Orks"),
    "Warboss": ("Orks.json", "Warboss", "Orks"),
    "Boyz": ("Orks.json", "Boyz", "Orks"),
    "Flash Gitz": ("Orks.json", "Flash Gitz", "Orks"),
    "Kommandos": ("Orks.json", "Kommandos", "Orks"),
    "Breaka Boyz": ("Orks.json", "Breaka Boyz", "Orks"),
    "Tankbustas": ("Orks.json", "Tankbustas", "Orks"),
    "Trukk": ("Orks.json", "Trukk", "Orks"),
    "Archon": ("Aeldari - Aeldari Library.json", "Archon", "Drukhari"),
    "Kabalite Warriors": ("Aeldari - Aeldari Library.json", "Kabalite Warriors", "Drukhari"),
    "Scourges with Shardcarbines": ("Aeldari - Aeldari Library.json", "Scourges with Shardcarbines", "Drukhari"),
    "Scourges with Heavy Weapons": ("Aeldari - Aeldari Library.json", "Scourges with Heavy Weapons", "Drukhari"),
    "Reavers": ("Aeldari - Aeldari Library.json", "Reavers", "Drukhari"),
    "Ravager": ("Aeldari - Aeldari Library.json", "Ravager", "Drukhari"),
    "Raider": ("Aeldari - Aeldari Library.json", "Raider", "Drukhari"),
    "Venom": ("Aeldari - Aeldari Library.json", "Venom", "Drukhari"),
    "Corsair Voidreavers": ("Aeldari - Aeldari Library.json", "Corsair Voidreavers", "Aeldari"),
    "Corsair Skyreavers": ("Aeldari - Aeldari Library.json", "Corsair Skyreavers", "Aeldari"),
    "Corsair Voidscarred": ("Aeldari - Aeldari Library.json", "Corsair Voidscarred", "Aeldari"),
    "Starfangs": ("Aeldari - Aeldari Library.json", "Starfangs", "Aeldari"),
}
# Stats, weapons and points are checked against IRONBUILT (newer than the repo's Orks catalogue).
PATCH_FROM_IRONBUILT = {"Orks.json", "Aeldari - Aeldari Library.json"}
DROP = re.compile(r"^(Enhancements?.*|Warlord|Crusade.*|Weapon Modifications|Battles Played|Battles Survived|"
                  r"Enemy Units Destroyed|Battle Honours|Battle Scars|Dark Pacts)$")
# Black-Flag profiles that are notes, not abilities.
NOTES = re.compile(r"^(Unit Composition|Points Note|CORE|Ability \d+|WARGEAR OPTIONS.*)$")
# Source wording that names the source faction; Black-Flag units answer to SKURVY.
KEYWORD_SWAPS = [
    (r"\^\^\*\*(?:Drukhari|Orks|Asuryani)\s*([^*]*?)\s*\*\*\^\^", lambda m: ("SKURVY " + m.group(1).upper()).strip()),
    (r"\b(DRUKHARI|ORKS|ASURYANI)\b", "SKURVY"),
    (r"\bspend 1 Pain token to Empower (this|that) (unit|model)\b", r"spend 1 Plunder from \1 \2"),
    (r"\bPain token", "Plunder"),
]
POINTS = "51b2-306e-1021-d207"


def plain(name):
    text = unicodedata.normalize("NFKD", name.lower())
    return re.sub(r"(.)\1+", r"\1", re.sub(r"[^a-z0-9]", "", text))  # "Channeler" = "Channeller", "Faolchú" = "Faolchu"


def norm(name):
    """Ability names: '(Pain)' and '(Plunder)' variants are the same ability."""
    return plain(re.sub(r"\s*\(.*?\)", "", name))


def swap_keywords(text):
    for pattern, repl in KEYWORD_SWAPS:
        text = re.sub(pattern, repl, text)
    return text


class Port(csm_port.Port):
    def __init__(self, index, source, system, ironbuilt):
        super().__init__(index, source, system)
        self.ironbuilt = ironbuilt
        self.log = []
        self.targets = {}
        game = system.get("gameSystem", system)
        self.profile_types = {t["id"] for t in game.get("profileTypes", []) + index.get("profileTypes", [])}

    def inline(self, node):
        """As the CSM port, and point default selections at the inlined copies (they take the link's ID)."""
        aliases = {l["targetId"]: l["id"] for l in node.get("entryLinks", [])}
        super().inline(node)
        if node.get("defaultSelectionEntryId") in aliases:
            node["defaultSelectionEntryId"] = aliases[node["defaultSelectionEntryId"]]

    def cleanup(self, unit, local):
        """Drop what still points at the source catalogue: unknown profile types, constraints and defaults."""
        for node in walk(unit):
            if not isinstance(node, dict):
                continue
            if "profiles" in node:
                kept = []
                for p in node["profiles"]:
                    if p.get("typeId") in self.profile_types:
                        kept.append(p)
                    else:
                        self.log.append(f"{unit['name']}: '{p['name']}' ({p.get('typeName')}) left out: "
                                        "profile type only exists in the source catalogue")
                node["profiles"] = kept
            if "constraints" in node:
                node["constraints"] = [c for c in node["constraints"] if self.known(c.get("childId"), local)]
            default = node.get("defaultSelectionEntryId")
            if default and default != "none" and default not in local:
                # Broken in the source catalogue: use the option the group is named after, else the first one.
                options = node.get("selectionEntries", [])
                pick = next((o for o in options if o["name"].casefold() == node.get("name", "").casefold()),
                            options[0] if options else None)
                if pick:
                    node["defaultSelectionEntryId"] = pick["id"]
                    self.log.append(f"{unit['name']}: default of '{node.get('name')}' set to '{pick['name']}'")
                else:
                    del node["defaultSelectionEntryId"]

    # ------------------------------------------------------------ Black-Flag text
    def abilities(self, unit, old):
        bf = {}
        for p in old.get("profiles", []):
            if p.get("typeName") == "Abilities" and not NOTES.match(p["name"]):
                bf[norm(p["name"])] = p
        used = set()
        top = unit.get("profiles", [])

        def match(name):
            key = norm(name)
            if key in bf:
                return key
            return next((k for k in bf if k and (key.startswith(k) or k.startswith(key))), None)

        for node in walk(unit):
            if not isinstance(node, dict):
                continue
            kept = []
            for p in node.get("profiles", []):
                if p.get("typeName") != "Abilities":
                    if p.get("typeName") == "Transport":
                        for c in p["characteristics"]:
                            c["$text"] = self.transport_text(old) or swap_keywords(c["$text"])
                    kept.append(p)
                    continue
                if node is unit and p["name"] in ("Leader", "Support"):
                    targets = self.targets.get((unit["id"], p["name"]))
                    if targets:
                        for c in p["characteristics"]:
                            c["$text"] = "This model can be attached to the following units:\n" + "\n".join(
                                "■ " + t.upper() for t in targets)
                        kept.append(p)
                    continue
                key = match(p["name"])
                if key:
                    used.add(key)
                    p["name"] = bf[key]["name"]
                    p["characteristics"] = copy.deepcopy(bf[key]["characteristics"])
                    kept.append(p)
                elif node is unit:
                    self.log.append(f"{old['name']}: source ability '{p['name']}' is not on the Black-Flag datasheet, "
                                    "left out")
                else:
                    for c in p["characteristics"]:
                        c["$text"] = swap_keywords(c["$text"])
                    kept.append(p)
            if "profiles" in node:
                node["profiles"] = kept
        for key, p in bf.items():
            if key not in used:
                top.append(copy.deepcopy(p))
                self.log.append(f"{old['name']}: Black-Flag ability '{p['name']}' added to the unit")
        unit["profiles"] = top

    @staticmethod
    def transport_text(old):
        for p in old.get("profiles", []):
            for c in p["characteristics"]:
                m = re.search(r"TRANSPORT:\s*(.+)$", c["$text"])
                if m:
                    return m.group(1).strip()
        return None

    # ------------------------------------------------------------ attachments
    def attachments(self, unit, source_unit, old, ids_by_name):
        comp = " ".join(c["$text"] for p in old.get("profiles", []) for c in p["characteristics"])
        unit.pop("associations", None)
        for assoc in source_unit.get("associations", []):
            kind = "SUPPORT" if assoc["name"] == "Supporting" else "LEADER"
            m = re.search(kind + r":\s*([^.]+)\.", comp)
            if m:
                targets = [t.strip() for t in re.split(r";|,", m.group(1)) if t.strip()]
            else:
                targets = [c["childName"] for c in walk(assoc.get("conditionGroups", [])) if isinstance(c, dict)
                           and c.get("childName") in ids_by_name]
            targets = [t for t in dict.fromkeys(targets) if t in ids_by_name]
            if not targets:
                self.log.append(f"{old['name']}: no {kind.title()} targets in Black-Flag")
                continue
            self.targets[(unit["id"], "Support" if kind == "SUPPORT" else "Leader")] = targets
            new = {k: v for k, v in assoc.items() if k not in ("id", "conditionGroups", "conditions")}
            new["id"] = nid(unit["id"] + ":" + assoc["name"])
            new["conditionGroups"] = [dict(type="or", conditions=[
                dict(childId=ids_by_name[t], childName=t, field="selections", scope="self", shared=True,
                     type="instanceOf", value=1) for t in targets])]
            unit.setdefault("associations", []).append(new)

    def keep_bf_categories(self, unit, old):
        have = {l["name"].casefold() for l in unit["categoryLinks"]}
        for link in old.get("categoryLinks", []):
            name = link["name"]
            if name.casefold() in have or ";" in name or name.startswith("Faction:"):
                continue
            unit["categoryLinks"].insert(-1, copy.deepcopy(link))
            have.add(name.casefold())

    # ------------------------------------------------------------ 11th-edition values
    def ib_unit(self, faction, name):
        return next(u for u in self.ironbuilt["factions"][faction]["data"]["units"]
                    if u["name"].casefold() == name.casefold())

    def patch_11e(self, unit, ib):
        weapons, model_stats = {}, {}

        def collect(models):
            for m in models:
                if m.get("isGroup"):
                    collect(m["models"])
                    continue
                model_stats[norm(m["name"])] = m.get("stats") or ib["stats"]
                for w in m.get("default", []):
                    weapons[plain(w["name"])] = w
                for g in m.get("groups", []):
                    for o in g["options"]:
                        for w in o.get("weapons", []):
                            weapons[plain(w["name"])] = w
        collect(ib["models"])
        keys = {"M": "M", "T": "T", "Sv": "SV", "SV": "SV", "W": "W", "LD": "LD", "OC": "OC"}
        for p in walk(unit):
            if not isinstance(p, dict) or "characteristics" not in p:
                continue
            if p.get("typeName") == "Unit":
                stats = model_stats.get(norm(p["name"]))
                if stats is None:
                    stats = model_stats.get(norm(re.sub(r"^\d+\s+", "", p["name"]).rstrip("s"))) or ib["stats"]
                for c in p["characteristics"]:
                    if c["name"] in keys and stats.get(keys[c["name"]]) and c["$text"] != stats[keys[c["name"]]]:
                        self.log.append(f"{unit['name']}: {p['name']} {c['name']} {c['$text']} -> "
                                        f"{stats[keys[c['name']]]}")
                        c["$text"] = stats[keys[c["name"]]]
            elif p.get("typeName", "").endswith("Weapons"):
                w = weapons.get(plain(re.sub(r"^\W+", "", p["name"])))
                if not w:
                    continue
                for c in p["characteristics"]:
                    value = w.get(c["name"])
                    if value is None or c["name"] == "Keywords":
                        continue
                    if value in ("-", "N/A") and c["$text"] in ("-", "N/A", ""):
                        continue  # no BS/WS (Torrent): keep the catalogue's own spelling
                    if c["$text"] != value:
                        self.log.append(f"{unit['name']}: {p['name']} {c['name']} {c['$text']} -> {value}")
                        c["$text"] = value
        tiers = ib["ptsTable"]
        for c in unit.get("costs", []):
            if c["typeId"] == POINTS and c["value"] != tiers[0]["pts"]:
                self.log.append(f"{unit['name']}: {c['value']} -> {tiers[0]['pts']} pts")
                c["value"] = tiers[0]["pts"]
        sizes = [m for m in unit.get("modifiers", []) if m.get("field") == POINTS and m["type"] == "set"]
        for m, tier in zip(sizes, tiers[1:]):
            if m["value"] != tier["pts"]:
                self.log.append(f"{unit['name']}: larger unit {m['value']} -> {tier['pts']} pts")
                m["value"] = tier["pts"]

    # ------------------------------------------------------------ run
    def run_units(self, names):
        shared = self.index["sharedSelectionEntries"]
        ids_by_name = {e["name"]: e["id"] for e in shared}
        source_by_name = {e["name"]: e for e in self.csm["sharedSelectionEntries"]}
        for i, old in enumerate(shared):
            if old["name"] not in names:
                continue
            path, source_name, faction = UNITS[old["name"]]
            source_unit = source_by_name[source_name]
            unit = copy.deepcopy(source_unit)
            unit["name"] = old["name"]
            unit.pop("associations", None)
            self.inline(unit)
            local = self.reid(unit, old["id"])
            self.prune(unit, local)
            self.categories(unit, old)
            self.keep_bf_categories(unit, old)
            self.attachments(unit, source_unit, old, ids_by_name)
            self.abilities(unit, old)
            self.cleanup(unit, local)
            if path in PATCH_FROM_IRONBUILT:
                self.patch_11e(unit, self.ib_unit(faction, source_name))
            unit["costs"] = [c for c in unit.get("costs", []) if c["typeId"] == POINTS] or \
                [dict(name="pts", typeId=POINTS, value=0)]
            shared[i] = unit
        return self.index


def fix_nested_categories(index, system):
    """Category links inside models point at Black-Flag categories, created by name where needed."""
    sys_ids = {n["id"] for n in walk(system) if isinstance(n, dict) and "id" in n}
    cats = {c["id"]: c for c in index["categoryEntries"]}
    by_name = {c["name"].casefold(): c for c in index["categoryEntries"]}
    for unit in index["sharedSelectionEntries"]:
        for node in walk(unit):
            if not isinstance(node, dict) or node is unit:
                continue
            for link in node.get("categoryLinks", []):
                if link["targetId"] in cats or link["targetId"] in sys_ids:
                    continue
                cat = by_name.get(link["name"].casefold())
                if cat is None:
                    cat = dict(name=link["name"], id=nid("category:" + link["name"]), hidden=False)
                    index["categoryEntries"].append(cat)
                    cats[cat["id"]] = by_name[cat["name"].casefold()] = cat
                link["targetId"] = cat["id"]


REF_KEYS = ("childId", "field", "targetId", "scope", "defaultSelectionEntryId")


def unique_ids(index):
    """Copies of one shared weapon inside a unit keep the same inner IDs: give each copy its own.

    For every repeat of an ID, the copy is the highest ancestor that does not also hold the first occurrence;
    the repeat is renamed and references to it inside that copy follow.
    """
    renamed = 0
    for unit in index["sharedSelectionEntries"]:
        occurrences = {}

        def visit(node, chain):
            if isinstance(node, dict):
                if "id" in node and node is not unit:
                    occurrences.setdefault(node["id"], []).append((node, chain))
                for value in node.values():
                    visit(value, chain + [node])
            elif isinstance(node, list):
                for value in node:
                    visit(value, chain)
        visit(unit, [])
        for old, places in occurrences.items():
            if len(places) < 2:
                continue
            first_chain = {id(n) for n in places[0][1]} | {id(places[0][0])}
            for n, (node, chain) in enumerate(places[1:], 1):
                root = node
                for ancestor in reversed(chain):
                    if id(ancestor) in first_chain:
                        break
                    root = ancestor
                new = nid(f"{unit['id']}:dup:{old}:{n}")
                node["id"] = new
                for sub in walk(root):
                    if isinstance(sub, dict):
                        for key in REF_KEYS:
                            if sub.get(key) == old:
                                sub[key] = new
                renamed += 1
    return renamed


def house_weapons(index, system):
    """Apply the house weapon standard (house_dice.py: D3 damage, fixed attacks, [BLAST X]) to every unit."""
    from house_dice import convert
    blast = next(r for r in system["gameSystem"]["sharedRules"] if r["name"] == "Blast")
    changed = []
    for unit in index["sharedSelectionEntries"]:
        for node in walk(unit):
            if not isinstance(node, dict):
                continue
            for p in node.get("profiles", []):
                if not p.get("typeName", "").endswith("Weapons"):
                    continue
                chars = {c["name"]: c for c in p["characteristics"]}
                keywords = [k.strip() for k in chars.get("Keywords", {}).get("$text", "").split(",")
                            if k.strip() and k.strip() != "-"]
                profile = {k: chars[k]["$text"] for k in ("A", "S", "AP", "D") if k in chars}
                new, new_keywords, changes = convert(p["name"], profile, keywords)
                if not changes:
                    continue
                for k, v in new.items():
                    chars[k]["$text"] = v
                if "Keywords" in chars:
                    upper = any(k.isupper() and len(k) > 3 for k in keywords)
                    chars["Keywords"]["$text"] = ", ".join(k.upper() if upper else k for k in new_keywords) or "-"
                if any(c.startswith("+Blast") for c in changes) and not any(
                        i.get("targetId") == blast["id"] for i in node.get("infoLinks", [])):
                    node.setdefault("infoLinks", []).append(dict(id=nid(node["id"] + ":blast"), name="Blast",
                                                                 hidden=False, targetId=blast["id"], type="rule"))
                changed.append(f"{unit['name']}: {p['name']}: {'; '.join(changes)}")
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", required=True)
    ap.add_argument("--system", required=True)
    ap.add_argument("--ironbuilt", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    csm_port.DROP = DROP
    data = json.loads(Path(a.index).read_text())
    system = json.loads(Path(a.system).read_text())
    ironbuilt = json.loads(Path(a.ironbuilt).read_text())
    index = data["catalogue"]
    by_source = {}
    for name, (path, _, _) in UNITS.items():
        by_source.setdefault(path, []).append(name)
    for path, names in by_source.items():
        source = json.loads(Path(path).read_text())["catalogue"]
        port = Port(index, source, system, ironbuilt)
        port.run_units(set(names))
        for line in port.log:
            print("NOTE:", line)
    fix_nested_categories(index, system)
    print("Gave", unique_ids(index), "repeated inner IDs their own ID")
    for line in sorted(set(house_weapons(index, system))):
        print("WEAPON:", line)
    index["revision"] = index.get("revision", 0) + 1
    Path(a.output).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Wrote", a.output, "revision", index["revision"])


if __name__ == "__main__":
    main()
