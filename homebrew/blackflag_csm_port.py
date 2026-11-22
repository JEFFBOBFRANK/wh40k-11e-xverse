#!/usr/bin/env python3
"""Rebuild the Chaos Space Marine units of Index: Black-Flag from the current Chaos Space Marines catalogue.

The Black-Flag units keep their IDs (Clan Skurvy links to them) and their Faction: Skurvy keyword. The datasheets
are copied from the CSM catalogue with their real model entries, weapon choices, unit sizes and repeat costs. Marks
of Chaos, Dark Pacts, CSM Enhancements and Crusade content are left out, as they do not apply to mercenaries.
Leader links follow the "LEADER:" lists printed on the Black-Flag datasheets.

    python3 homebrew/blackflag_csm_port.py --index 'Index - Black-Flag (Homebrew).json' \
        --csm 'Chaos - Chaos Space Marines.json' --system 'Warhammer 40,000.json' --output out.json
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

# Black-Flag name -> CSM catalogue name
UNITS = {
    "Chaos Lord": "Chaos Lord",
    "Chaos Lord with Jump Pack": "Chaos Lord with Jump Pack",
    "Red Corsairs Reave-Captain": "Red Corsairs Reave-captain",
    "Legionaries": "Legionaries",
    "Havocs": "Havocs",
    "Raptors": "Raptors",
    "Red Corsairs Raiders": "Red Corsairs Raiders",
    "Chaos Bikers": "Chaos Bikers",
}
DROP = re.compile(r"^(Mark of Chaos|Enhancements|Warlord|Chaos Boons|Weapon Modifications|Unholy Patronage.*|"
                  r"Battles Played|Battles Survived|Enemy Units Destroyed|Battle Honours|Battle Scars|Crusade.*|"
                  r"Dark Destiny|Khorne|Nurgle|Slaanesh|Tzeentch|Chaos Undivided|Dark Pacts)$")
SCOPES = {"self", "parent", "roster", "force", "unit", "model", "model-or-unit", "ancestor", "root-entry",
          "primary-catalogue", "primary-category", "any", "upgrade"}
# 11th-edition values from the IRONBUILT dataset (wh40k-11e, 2026-11-21) that the repo's CSM catalogue lacks.
STATS = {"Chaos Lord": {"T": "5"}, "Chaos Lord with Jump Pack": {"T": "5"}, "Red Corsairs Reave-Captain": {"T": "5"},
         "Legionaries": {"T": "5"}, "Raptors": {"T": "5"}, "Red Corsairs Raiders": {"T": "5"},
         "Havocs": {"W": "3"}, "Chaos Bikers": {"T": "6"}}
POINTS = {"Chaos Lord": (95, None), "Chaos Lord with Jump Pack": (85, None), "Red Corsairs Reave-Captain": (65, None),
          "Legionaries": (95, 180), "Havocs": (135, None), "Raptors": (115, 225), "Red Corsairs Raiders": (120, 220),
          "Chaos Bikers": (80, 150)}
WEAPONS = {"Bolt pistol": {"S": "5", "AP": "-1"}, "Boltgun": {"S": "5", "AP": "-1"},
           "Combi-bolter": {"S": "5", "AP": "-1"}, "Close combat weapon": {"S": "5"},
           "Astartes chainsword": {"S": "5"}, "Astartes chainblade": {"S": "5"}}
POINTS_TYPE = "51b2-306e-1021-d207"
# Black-Flag wording kept where the CSM text depends on CSM-only rules.
BLACK_FLAG_TEXT = {
    "Chaos icon": "Each time the bearer's unit takes a Battle-shock test, you can re-roll that test.",
}


def nid(key):
    digest = hashlib.sha256(f"blackflag-csm:{key}".encode()).hexdigest()[:16]
    return "-".join(digest[i:i + 4] for i in range(0, 16, 4))


def walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def all_ids(data):
    return {n["id"] for n in walk(data) if isinstance(n, dict) and "id" in n}


class Port:
    def __init__(self, index, csm, system):
        self.index, self.csm, self.system = index, csm, system
        self.sys_ids = all_ids(system)
        self.csm_shared = {e["id"]: e for e in csm["sharedSelectionEntries"] + csm.get("sharedSelectionEntryGroups", [])}
        self.csm_profiles = {p["id"]: p for p in csm.get("sharedProfiles", [])}
        self.bf_cats = {c["name"].casefold(): c for c in index["categoryEntries"]}
        self.csm_cats = {c["id"]: c for c in csm["categoryEntries"]}

    def inline(self, node):
        """Replace entry links and CSM info links with copies; drop CSM-only options."""
        for key in ("selectionEntries", "selectionEntryGroups"):
            node[key] = [s for s in node.get(key, []) if not DROP.match(s["name"])]
        links = []
        for link in node.get("entryLinks", []):
            if DROP.match(link["name"]):
                continue
            target = self.csm_shared.get(link["targetId"])
            if target is None or DROP.match(target["name"]):
                continue
            copy_ = copy.deepcopy(target)
            copy_["id"] = link["id"]
            for key in ("constraints", "modifiers", "modifierGroups"):
                if link.get(key):
                    copy_[key] = copy.deepcopy(link[key]) + copy_.get(key, [])
            if link.get("name"):
                copy_["name"] = link["name"]
            group = "selectionEntryGroups" if link["type"] == "selectionEntryGroup" else "selectionEntries"
            node.setdefault(group, []).append(copy_)
        node.pop("entryLinks", None)
        infos = []
        for info in node.get("infoLinks", []):
            if info["name"] == "Dark Pacts":
                continue
            if info["targetId"] in self.csm_profiles:
                node.setdefault("profiles", []).append(copy.deepcopy(self.csm_profiles[info["targetId"]]))
            elif info["targetId"] in self.sys_ids:
                infos.append(info)
        if infos:
            node["infoLinks"] = infos
        else:
            node.pop("infoLinks", None)
        for p in node.get("profiles", []):
            if p["name"] in BLACK_FLAG_TEXT:
                for c in p["characteristics"]:
                    c["$text"] = BLACK_FLAG_TEXT[p["name"]]
        for key in ("selectionEntries", "selectionEntryGroups"):
            for child in node.get(key, []):
                self.inline(child)
            if not node.get(key):
                node.pop(key, None)

    def reid(self, unit, bf_id):
        mapping = {}
        for n in walk(unit):
            if isinstance(n, dict) and "id" in n:
                mapping.setdefault(n["id"], bf_id if n is unit else nid(bf_id + ":" + n["id"]))
                n["id"] = mapping[n["id"]]
        for n in walk(unit):
            if not isinstance(n, dict):
                continue
            for key in ("childId", "field", "scope", "targetId", "defaultSelectionEntryId"):
                if n.get(key) in mapping:
                    n[key] = mapping[n[key]]
        return set(mapping.values())

    def known(self, value, local):
        return value is None or value in local or value in self.sys_ids or value in SCOPES or \
            value in ("selections", "forces", "hidden", "category", "name", "annotation", "page") or \
            not re.match(r"^[0-9a-f]{1,4}(-[0-9a-f]{1,4}){3}$", str(value))

    def prune(self, node, local):
        """Drop modifiers and conditions that point at CSM-only things (Marks, detachments, Crusade)."""
        def ok_conditions(m):
            for c in walk(m.get("conditions", []) + m.get("conditionGroups", []) + m.get("repeats", [])):
                if isinstance(c, dict) and ("childId" in c or "scope" in c) and not (
                        self.known(c.get("childId"), local) and self.known(c.get("scope"), local)):
                    return False
            return True
        for n in walk(node):
            if not isinstance(n, dict):
                continue
            if "modifiers" in n:
                n["modifiers"] = [m for m in n["modifiers"] if ok_conditions(m) and self.known(m.get("field"), local)
                                  and (m.get("field") != "category" or self.known(m.get("value"), local))]
                if not n["modifiers"]:
                    del n["modifiers"]
            n.pop("modifierGroups", None)
            if "constraints" in n:
                n["constraints"] = [c for c in n["constraints"] if self.known(c.get("field"), local)
                                    and self.known(c.get("scope"), local)]

    def categories(self, unit, old):
        links = []
        for link in unit.get("categoryLinks", []):
            if link.get("name", "").startswith("Faction:") or \
                    self.csm_cats.get(link["targetId"], {}).get("name", "").startswith("Faction:"):
                continue
            if link["targetId"] in self.sys_ids:
                links.append(link)
                continue
            name = self.csm_cats.get(link["targetId"], {}).get("name", link["name"])
            if name.startswith("Faction:"):
                continue
            cat = self.bf_cats.get(name.casefold())
            if cat is None:
                cat = dict(name=name, id=nid("category:" + name), hidden=False)
                self.index["categoryEntries"].append(cat)
                self.bf_cats[name.casefold()] = cat
            links.append(dict(link, name=cat["name"], targetId=cat["id"]))
        skurvy = next(l for l in old["categoryLinks"] if l["name"] == "Faction: Skurvy")
        unit["categoryLinks"] = links + [skurvy]

    def leaders(self, unit, old, ids_by_name):
        comp = " ".join(c["$text"] for p in old.get("profiles", []) if p["name"] == "Unit Composition"
                        for c in p["characteristics"])
        m = re.search(r"LEADER:\s*([^.]+)\.", comp) or re.search(r"can lead ([^.]+)\.", comp)
        if not m:
            unit.pop("associations", None)
            return
        targets = [t.strip() for t in re.split(r";|,|\bor\b", m.group(1)) if t.strip()]
        conditions = [dict(childId=ids_by_name[t], childName=t, field="selections", scope="self", shared=True,
                           type="instanceOf", value=1) for t in targets if t in ids_by_name]
        unit["associations"] = [dict(name="Leading", id=nid(unit["id"] + ":leading"), action="group", childId="unit",
                                     childName="unit", includeChildSelections=True, label="Leader", max=1, min=0,
                                     scope="force", conditionGroups=[dict(type="or", conditions=conditions)])]

    def run(self):
        shared = self.index["sharedSelectionEntries"]
        ids_by_name = {e["name"]: e["id"] for e in shared}
        csm_by_name = {e["name"]: e for e in self.csm["sharedSelectionEntries"]}
        for i, old in enumerate(shared):
            if old["name"] not in UNITS:
                continue
            unit = copy.deepcopy(csm_by_name[UNITS[old["name"]]])
            unit["name"] = old["name"]
            unit.pop("associations", None)
            self.inline(unit)
            local = self.reid(unit, old["id"])
            self.prune(unit, local)
            self.categories(unit, old)
            self.leaders(unit, old, ids_by_name)
            # Black-Flag-only abilities (e.g. Red Corsairs Raiders may take SKURVY leaders) replace the CSM wording.
            bf_text = {p["name"]: p for p in old.get("profiles", []) if p.get("typeName") == "Abilities"}
            for p in unit.get("profiles", []):
                if p["name"] == "Attached Unit" and "Attached Unit" in bf_text:
                    p["characteristics"] = copy.deepcopy(bf_text["Attached Unit"]["characteristics"])
            leftovers = [n["name"] for n in walk(unit) if isinstance(n, dict) and "Dark Pact" in json.dumps(
                n.get("characteristics", ""))]
            for name in leftovers:
                print(f"NOTE: {old['name']}: '{name}' mentions Dark Pacts")
            for n in walk(unit):
                if not isinstance(n, dict) or "characteristics" not in n:
                    continue
                if n.get("typeName") == "Unit":
                    changes = STATS.get(old["name"], {})
                elif n.get("typeName", "").endswith("Weapons"):
                    changes = WEAPONS.get(re.sub(r"^\W+", "", n["name"]).strip(), {})
                else:
                    continue
                for c in n["characteristics"]:
                    if c["name"] in changes:
                        c["$text"] = changes[c["name"]]
            if old["name"] in POINTS:
                base, large = POINTS[old["name"]]
                for c in unit.get("costs", []):
                    if c["typeId"] == POINTS_TYPE:
                        c["value"] = base
                for m in unit.get("modifiers", []):
                    if large and m.get("field") == POINTS_TYPE and m["type"] == "set":
                        m["value"] = large
            shared[i] = unit
        return self.index


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", required=True)
    ap.add_argument("--csm", required=True)
    ap.add_argument("--system", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    index = json.loads(Path(a.index).read_text())
    csm = json.loads(Path(a.csm).read_text())["catalogue"]
    system = json.loads(Path(a.system).read_text())
    cat = Port(index["catalogue"], csm, system).run()
    cat["revision"] = cat.get("revision", 0) + 1
    Path(a.output).write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    print("Wrote", a.output, "revision", cat["revision"])


if __name__ == "__main__":
    main()
