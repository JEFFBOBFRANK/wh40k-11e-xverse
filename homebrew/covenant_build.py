"""Build the Covenant 11th-edition homebrew catalogue for New Recruit.

Sources: homebrew/covenant-source (datasheets.json and detachments.json extracted from Codex: Covenant v5.5.0,
army_rules.md with the revised Caste Hierarchy and per-unit shield regeneration), the unit layouts in covenant_units.py and the
game system. The layout follows the Emperor's Children and Skaven catalogues.

Usage:
  python3 homebrew/covenant_build.py --source homebrew/covenant-source --system 'Warhammer 40,000.json' \
      --output 'Xenos - Covenant (Homebrew).json'
"""
import argparse
import hashlib
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from datasheet_format import add_ability, core_rules, detachment_point_counter, rule_link, weapon_rules  # noqa: E402
from covenant_units import AUX_LISTS, BORROW, MODELS, UNITS  # noqa: E402
from skaven_build import format_subrules  # noqa: E402

REVISION = 15
NAME = "Xenos - Covenant (Homebrew)"
POINTS = "51b2-306e-1021-d207"
ENHANCEMENT_SLOT = "f759-1bc4-cb3a-f0d2"
DP = "82ae-1066-5107-6ae0"
CONFIGURATION = "4ac9-fd30-1e3d-b249"
REFERENCE = "eef1-be80-500a-edfc"
ROLE = {"EPIC HERO": "Epic Hero", "CHARACTER": "Character", "BATTLELINE": "Battleline", "INFANTRY": "Infantry",
        "MOUNTED": "Mounted", "MONSTER": "Monster", "VEHICLE": "Vehicle", "FORTIFICATION": "Fortification"}
ARMY_RULES = ["Caste Hierarchy", "Shielding Trait", "Chosen of the Hierarchs", "Caste Doctrines", "Supercombine", "Plasma", "Siegebreaker",
              "Wargear Costs", "Transport Space"]
WEAPON_RULES = {"Supercombine": r"\bSupercombine\b", "Plasma": r"\bPlasma \((?:D|AP)[\dD+]+\)",
                "Siegebreaker": r"\bSiegebreaker\b"}
# Commanders with Chosen of the Hierarchs (+1CP each battle round while your Warlord), as EC's Sublime Strategist.
WARLORD_CP = {"Prophet of Truth", "Prophet of Regret", "Prophet of Mercy", "Thel 'Vadam", "Rtas 'Vadum", "Tartarus",
              "Sangheili Shipmaster", "Sangheili Fieldmaster", "Jiralhanae Chieftain", "Yig-Yar Corsair-Talon"}
# Every unit is laid out like the Emperor's Children Tormentors: Sergeant on top (as the Obsessionist), then the model
# counters, then Auxiliary models as counters too (one model type per loadout), then Auxiliary wargear and Specialist
# abilities with a model picker (as the Icon of Excess), in that order (sortIndex 0-3).
# Species keywords a unit gains from its Sergeant and Auxiliary models (core rules: a unit has the keywords of all its
# models). The unit keywords (GRUNT, ELITE, BRUTE, JACKAL, DRONE, HUNTER, ENGINEER) are on datasheets only.
SPECIES = {"Sangheili", "Special Operations", "Jiralhanae", "Yig-Yar", "T'vaoan", "Unggoy", "Huragok", "Yanme'e",
           "San'Shyuum", "Mgalekgolo", "Lekgolo"}


def nid(key):
    digest = hashlib.sha256(f"covenant-11e:{key}".encode()).hexdigest()[:16]
    return "-".join(digest[i:i + 4] for i in range(0, 16, 4))


def constraint(cid, kind, value, scope="parent", field="selections", child=False, forces=False):
    c = dict(id=cid, type=kind, value=value, scope=scope, field=field, shared=True, includeChildSelections=child)
    if forces:
        c["includeChildForces"] = True
    return c


def selected(child, scope="force", kind="atLeast", value=1):
    return dict(childId=child, field="selections", scope=scope, type=kind, value=value, shared=True,
                includeChildSelections=True)


def entry(eid, name, kind="upgrade", **extra):
    node = dict(name=name, id=eid, type=kind, hidden=False)
    node["import"] = True
    node.update(extra)
    return node


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def inches(text):
    return re.sub(r"(\d+) inches", r'\1"', text)


def split_option(option):
    """'A + B' -> [A, B]; 'Label = A + B' names a package by its label."""
    if " = " in option:
        option = option.split(" = ", 1)[1]
    return [p.strip() for p in option.split(" + ")]


def option_name(option):
    """How an option is shown: its package label, or its items as 'A', 'A and B', 'A, B and C'."""
    if " = " in option:
        return option.split(" = ", 1)[0].strip()
    parts = split_option(option)
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def sections(text, level="## "):
    out, name, lines = [], None, []
    for line in text.splitlines():
        if line.startswith(level):
            if name is not None or any(x.strip() for x in lines):
                out.append((name, lines))
            name, lines = line[len(level):].strip(), []
        else:
            lines.append(line)
    out.append((name, lines))
    return out


class Builder:
    def __init__(self, source, system):
        self.source = Path(source)
        self.system = system["gameSystem"]
        self.data = OrderedDict((d["name"], d) for d in json.loads((self.source / "datasheets.json").read_text()))
        self.dets = json.loads((self.source / "detachments.json").read_text())
        self.sys_types = {t["name"]: t for t in self.system["profileTypes"]}
        self.sys_categories = {c["name"].casefold(): c for c in self.system["categoryEntries"]}
        self.sys_rules = {r["name"].casefold(): r for r in self.system["sharedRules"]}
        self.categories = OrderedDict()
        self.rules = OrderedDict()
        self.shared_models = OrderedDict()
        self.aux_slot = nid("cost:auxiliary-slots")
        self.enh_count = nid("cost:enhancement-or-upgrade")
        self.shields_type = dict(id=nid("profile-type:shields"), name="Shields",
                                 characteristicTypes=[dict(id=nid("profile-type:shields:sp"), name="SP")])
        self.log = []

    # ------------------------------------------------------------ categories, rules, profiles
    def category(self, name, hidden=False):
        key = name.casefold()
        if key in self.sys_categories and not hidden:
            c = self.sys_categories[key]
            return c["id"], c["name"]
        if key not in self.categories:
            self.categories[key] = dict(name=name, id=nid("category:" + name), hidden=hidden)
        return self.categories[key]["id"], name

    def cat_link(self, owner, name, primary=False, hidden=False):
        cid, shown = self.category(name, hidden=hidden)
        return dict(name=shown, id=nid(owner + ":cat:" + cid), targetId=cid, primary=primary, hidden=False)

    def rule(self, name, description):
        rid = nid("rule:" + name)
        self.rules[name] = dict(name=name, id=rid, hidden=False, description="\n\n" + description.strip())
        return self.rules[name]

    def unit_profile(self, pid, name, stats, inv=None):
        kind = self.sys_types["Unit"]
        values = dict(M=stats.get("M", "-"), T=stats.get("T", "-"), Sv=stats.get("SV", "-"), W=stats.get("W", "-"),
                      LD=stats.get("LD", "-"), OC=stats.get("OC", "-"), InSv=inv or stats.get("INV", "-") or "-")
        return dict(id=pid, name=name, hidden=False, typeId=kind["id"], typeName="Unit",
                    characteristics=[dict(name=c["name"], typeId=c["id"], **{"$text": values[c["name"]]})
                                     for c in kind["characteristicTypes"]])

    def shields_profile(self, pid, name, sp):
        sp_type = self.shields_type["characteristicTypes"][0]
        return dict(id=pid, name=name, hidden=False, typeId=self.shields_type["id"], typeName="Shields",
                    characteristics=[dict(name="SP", typeId=sp_type["id"], **{"$text": str(sp)})])

    def weapon_profile(self, pid, weapon, ranged):
        kind = self.sys_types["Ranged Weapons" if ranged else "Melee Weapons"]
        keywords = inches(", ".join(weapon["keywords"])) or "-"
        bs = weapon["BS_WS"] or "-"
        values = [inches(weapon["range"]), weapon["A"], bs, weapon["S"], weapon["AP"], weapon["D"], keywords]
        return dict(id=pid, name=weapon["name"], hidden=False, typeId=kind["id"], typeName=kind["name"],
                    characteristics=[dict(name=c["name"], typeId=c["id"], **{"$text": v})
                                     for c, v in zip(kind["characteristicTypes"], values)])

    def ability_profile(self, pid, name, text, hidden=False):
        kind = self.sys_types["Abilities"]
        c = kind["characteristicTypes"][0]
        return dict(id=pid, name=name, hidden=hidden, typeId=kind["id"], typeName="Abilities",
                    characteristics=[dict(name=c["name"], typeId=c["id"], **{"$text": inches(text).strip()})])

    # ------------------------------------------------------------ wargear
    def weapons_of(self, ds):
        found = OrderedDict()
        for w in ds["ranged_weapons"]:
            found.setdefault(w["name"], (w, True))
        for w in ds["melee_weapons"]:
            found.setdefault(w["name"], (w, False))
        return found

    def resolve(self, ds, item):
        """An equipped item -> ('weapon', [(weapon, ranged)]) or ('gear', wargear dict)."""
        weapons = self.weapons_of(ds)
        name = re.sub(r"^\d+\s+", "", item.strip())
        for candidate in (item.strip(), name):
            if candidate in weapons:
                return "weapon", [weapons[candidate]]
        multi = [weapons[w] for w in weapons if w.startswith(name + " - ")]
        if multi:
            return "weapon", multi
        gear = next((g for g in ds["wargear"] + ds.get("specialist_abilities", []) if g["name"] == name), None)
        if gear:
            return "gear", gear
        donor = BORROW.get((ds["name"], name))
        if donor:
            w = self.weapons_of(self.data[donor]).get(name)
            if w:
                return "weapon", [w]
        for other in self.data.values():  # wargear items are printed once (e.g. Wrist Shield) and shared
            gear = next((g for g in other["wargear"] if g["name"] == name), None)
            if gear:
                return "gear", gear
        raise ValueError(f"{ds['name']}: cannot resolve '{item}'")

    def gear_entry(self, owner, option, ds, fixed=False, cost=0):
        """An upgrade carrying one or more weapons and wargear items ('A + B' takes both)."""
        parts = split_option(option)
        eid = nid(owner + ":gear:" + option)
        node = entry(eid, option_name(option), profiles=[])
        inv = None
        for part in parts:
            kind, value = self.resolve(ds, part)
            if kind == "weapon":
                for weapon, ranged in value:
                    node["profiles"].append(self.weapon_profile(nid(eid + ":" + weapon["name"]), weapon, ranged))
            else:
                node["profiles"].append(self.ability_profile(nid(eid + ":ability:" + value["name"]), value["name"],
                                                             value["text"]))
                sp = re.search(r"starting SP value of (\d+)", value["text"])
                if sp:
                    node["profiles"].append(self.shields_profile(nid(eid + ":sp"), value["name"], sp.group(1)))
                    node["_sp"] = int(sp.group(1))
                m = re.search(r"has an? (\d\+) invulnerable save", value["text"])
                if m:
                    inv = m.group(1)
        if inv:
            node["_inv"] = inv
        node["constraints"] = [constraint(nid(eid + ":max"), "max", 1)]
        if fixed:
            node["constraints"].insert(0, constraint(nid(eid + ":min"), "min", 1))
        if cost:
            node["costs"] = [dict(name="pts", typeId=POINTS, value=cost)]
        return node

    def choice_group(self, owner, spec, ds):
        gid = nid(owner + ":choice:" + spec["label"])
        options = [self.gear_entry(gid, o, ds, cost=spec["costs"].get(o, 0)) for o in spec["options"]]
        group = dict(name=spec["label"], id=gid, hidden=False, selectionEntries=options,
                     constraints=[constraint(nid(gid + ":min"), "min", spec["min"]),
                                  constraint(nid(gid + ":max"), "max", spec["max"])])
        if spec["min"]:
            group["defaultSelectionEntryId"] = options[0]["id"]
        return group

    def default_items(self, ds, spec):
        """Weapons and wargear a single model carries outside its choice groups."""
        chosen = {p for c in spec["choices"] for o in c["options"] for p in split_option(o)}
        weapons = spec.get("weapons")
        gear = spec.get("gear")
        items = []
        abilities = {a["name"] for a in ds["abilities"]}
        for item in ds["equipped"]:
            if ":" in item or item in abilities:  # "N'tho: ..." is laid out by hand; "Lich Shield" is an ability
                continue
            kind, _ = self.resolve(ds, item)
            base = re.sub(r"^\d+\s+", "", item)
            if base in chosen or item in chosen:
                continue
            if kind == "weapon" and weapons is not None and item not in weapons and base not in weapons:
                continue
            if kind == "gear" and gear is not None and base not in gear:
                continue
            items.append(item)
        for extra in (weapons or []) + (gear or []):
            if extra not in items and re.sub(r"^\d+\s+", "", extra) not in [re.sub(r"^\d+\s+", "", i) for i in items]:
                items.append(extra)
        return items

    def model_stats(self, ds, gear_nodes):
        inv = next((g["_inv"] for g in gear_nodes if g.get("_inv")), None)
        return inv

    def add_model_shields(self, model, name, ds, gear_nodes):
        """SP is shown on the wargear that gives it, or on the model when no wargear does."""
        if any(g.get("_sp") for g in gear_nodes):
            return
        sp = ds["profile"].get("SP")
        if sp and sp not in ("-", "0"):
            model.setdefault("profiles", []).append(self.shields_profile(nid(model["id"] + ":sp"), name, sp))

    # ------------------------------------------------------------ keywords and abilities
    def keywords(self, owner, ds, primary):
        links = [self.cat_link(owner, primary, primary=True)]
        for kw in ds["keywords"]:
            if kw.casefold() in (primary.casefold(),):
                continue
            links.append(self.cat_link(owner, kw))
        links.append(self.cat_link(owner, "Faction: Covenant"))
        seen, out = set(), []
        for l in links:
            if l["targetId"] not in seen:
                seen.add(l["targetId"]); out.append(l)
        return out

    def add_abilities(self, node, ds):
        for a in ds["abilities"]:
            name, text = a["name"], a["text"]
            if name == "Core":
                text = text.replace(" inches", '"')
                for item in re.split(r",\s*", text):
                    item = item.strip()
                    try:
                        core_rules(node, self.system, item)
                    except ValueError:
                        base = re.sub(r"\s+(\d*D\d+(\+\d+)?|\d+[+\"]?)$", "", item)
                        rule = self.sys_rules.get(base.casefold())
                        if rule:
                            rule_link(node, rule, item)
                        else:
                            add_ability(node, self.system, item, item)
                            self.log.append(f"{ds['name']}: core rule '{item}' has no game system rule")
            else:
                add_ability(node, self.system, name or "Ability", text)
        if ds["leader"]:
            text = " ".join(ds["leader"])
            m = re.search(r"attached to:\s*(.+?)\.(.*)$", text)
            if m:
                body = "This model can be attached to the following units:\n\n" + "\n".join(
                    "■ " + t.strip().upper() for t in re.split(r",\s*", m.group(1)) if t.strip())
                if m.group(2).strip():
                    body += "\n\n" + m.group(2).strip()
                add_ability(node, self.system, "Leader", body)
        if ds["rules_notes"]:
            add_ability(node, self.system, "Rules Notes", " ".join(ds["rules_notes"]))
        if ds["transport"]:
            kind = self.sys_types["Transport"]
            c = kind["characteristicTypes"][0]
            text = re.sub(r"^Transport capacity:\s*", "", " ".join(ds["transport"]))
            node.setdefault("profiles", []).append(dict(
                id=nid(node["id"] + ":transport"), name=ds["name"], hidden=False, typeId=kind["id"],
                typeName="Transport", characteristics=[dict(name=c["name"], typeId=c["id"], **{"$text": text})]))
            if "Transport Space" in text:
                rule_link(node, self.rules["Transport Space"])

    def link_weapon_rules(self, node):
        weapon_rules(node, self.system)
        pistol = self.sys_rules["pistol"]
        for sub in list(walk(node)):
            if not isinstance(sub, dict):
                continue
            weapons = [p for p in sub.get("profiles", []) if p.get("typeName", "").endswith("Weapons")]
            if not weapons:
                continue
            text = ", ".join(p["characteristics"][-1]["$text"] for p in weapons)
            if re.search(r"(^|, )Pistol(,|$)", text):
                rule_link(sub, pistol)
            for name, pattern in WEAPON_RULES.items():
                if re.search(pattern, text):
                    rule_link(sub, self.rules[name])

    # ------------------------------------------------------------ datasheets
    def primary(self, ds):
        if "Dedicated Transport" in ds["keywords"]:
            return "Dedicated Transport"
        return ROLE[ds["category"]]

    def single_model(self, owner, ds, spec, name=None, kind="model"):
        """One model with its default wargear and choices (characters, vehicles, Sergeants, Auxiliaries)."""
        name = name or ds["name"]
        node = entry(owner, name, kind, profiles=[], selectionEntries=[], selectionEntryGroups=[])
        gear_nodes = [self.gear_entry(owner, item, ds, fixed=True) for item in self.default_items(ds, spec)]
        node["selectionEntries"] = gear_nodes
        choices = spec["choices"] + self.specialist_choice(ds)
        node["selectionEntryGroups"] = [self.choice_group(owner, c, ds) for c in choices]
        self.option_rules(node, ds, spec, choices)
        inv = self.model_stats(ds, gear_nodes)
        node["profiles"].append(self.unit_profile(nid(owner + ":profile"), name, ds["profile"], inv=inv))
        default_gear = gear_nodes + [g["selectionEntries"][0] for g in node["selectionEntryGroups"] if g.get(
            "defaultSelectionEntryId")]
        self.add_model_shields(node, name, ds, default_gear)
        return node

    @staticmethod
    def specialist_option(ability):
        return " + ".join([ability["name"]] + ability.get("with", []))

    def specialist_choice(self, ds):
        """An Auxiliary's Specialist abilities: one per model, at the points shown."""
        abilities = ds.get("specialist_abilities", [])
        if not abilities:
            return []
        options = [self.specialist_option(a) for a in abilities]
        costs = {self.specialist_option(a): a["points"] for a in abilities if a["points"]}
        return [dict(label="Specialist ability", options=options, min=0, max=1, costs=costs)]

    def option_rules(self, node, ds, spec, choices):
        """Errors for options that cannot be combined, and abilities that replace all of a model's weapons."""
        ids = {}
        for c, g in zip(choices, node["selectionEntryGroups"]):
            for option, e in zip(c["options"], g["selectionEntries"]):
                ids[option] = e["id"]

        def has(option, kind="atLeast", value=1):
            return dict(childId=ids[option], field="selections", scope="self", shared=True,
                        includeChildSelections=True, type=kind, value=value)

        mods = []
        for option, others in spec.get("exclude", []):
            names = others[0] if len(others) == 1 else ", ".join(others[:-1]) + " or " + others[-1]
            mods.append(dict(type="add", field="error", value=f"{option} cannot be taken with a {names}.",
                             conditionGroups=[dict(type="and", conditions=[has(option)], conditionGroups=[
                                 dict(type="or", conditions=[has(o) for o in others])])]))
        groups = {c["label"]: (c, g) for c, g in zip(choices, node["selectionEntryGroups"])}
        for option, labels in spec.get("empties", []):  # e.g. 2 Plasma Rifles also replace the Plasma Pistol
            for label in labels:
                c, g = groups[label]
                picked = dict(has(option), scope="parent")
                g.setdefault("modifiers", []).extend(dict(type="set", field=k["id"], value=0, conditions=[picked])
                                                     for k in g["constraints"])
                mods.append(dict(type="add", field="error",
                                 value=f"{option_name(option)} replaces the {label.lower()}: remove it.",
                                 conditionGroups=[dict(type="and", conditions=[has(option)], conditionGroups=[
                                     dict(type="or", conditions=[has(o) for o in c["options"]])])]))
        weapon_options = [o for c in spec["choices"] for o in c["options"]]
        for a in ds.get("specialist_abilities", []):
            if not a.get("replaces_weapons"):
                continue
            assert not node["selectionEntries"], f"{ds['name']}: weapons outside the choice groups"
            option = self.specialist_option(a)
            for c, g in zip(choices, node["selectionEntryGroups"]):
                if c in spec["choices"]:  # the weapon choice is emptied while the model has this ability
                    picked = dict(has(option), scope="parent")
                    g.setdefault("modifiers", []).extend(dict(type="set", field=k["id"], value=0,
                                                              conditions=[picked]) for k in g["constraints"])
            mods.append(dict(type="add", field="error",
                             value=f"{a['name']} replaces all of this model's weapons: remove its other weapons.",
                             conditionGroups=[dict(type="and", conditions=[has(option)], conditionGroups=[
                                 dict(type="or", conditions=[has(o) for o in weapon_options])])]))
        if mods:
            node.setdefault("modifiers", []).extend(mods)

    def datasheet(self, name):
        ds, spec = self.data[name], UNITS[name]
        unit_id = nid("unit:" + name)
        primary = self.primary(ds)
        retinue = spec["single"] and (spec["sergeants"] or spec["aux"])
        if spec["single"] and not retinue:
            node = self.single_model(unit_id, ds, spec)
        else:
            node = entry(unit_id, name, "unit", profiles=[], selectionEntries=[], selectionEntryGroups=[])
            if spec["single"]:
                mid = nid(unit_id + ":model")
                model = self.single_model(mid, ds, spec)
                model["constraints"] = [constraint(nid(mid + ":min"), "min", 1), constraint(nid(mid + ":max"), "max", 1)]
                model["sortIndex"] = 0  # the character on top, then its Sergeant and Auxiliaries
                node["selectionEntries"].append(model)
                family = None
            else:
                family = self.squad(node, ds, spec)
            self.sergeants(node, spec)
            self.auxiliaries(node, spec, family)
            self.addon_keywords(node, ds)
        node["categoryLinks"] = self.keywords(unit_id, ds, primary)
        node.setdefault("costs", []).insert(0, dict(name="pts", typeId=POINTS,
                                                    value=0 if spec.get("per_model") else ds["points"]))
        node["costs"] = node["costs"][:1]
        copies = 1 if primary == "Epic Hero" else 6 if primary == "Battleline" else 3
        node.setdefault("constraints", []).append(constraint(nid(unit_id + ":copies"), "max", copies, scope="roster",
                                                             child=True, forces=True))
        self.add_abilities(node, ds)
        if "Frame" in ds["keywords"]:
            rule_link(node, self.rules["Frame"])
        if name in WARLORD_CP:
            rule_link(node, self.rules["Chosen of the Hierarchs"])
        node["profiles"].append(self.ability_profile(nid(unit_id + ":keywords"), "Printed Keywords and Notes",
                                                     "Keywords: " + ", ".join(ds["keywords"]) +
                                                     ". Faction: Covenant.", hidden=True))
        self.link_weapon_rules(node)
        for key in ("selectionEntries", "selectionEntryGroups", "modifiers", "infoLinks", "profiles"):
            if key in node and not node[key]:
                del node[key]
        return node

    def squad(self, node, ds, spec):
        unit_id = node["id"]
        node.setdefault("modifiers", [])
        families = []
        for m in spec["models"]:
            families.append(self.family(node, ds, spec, m))
        main = families[0]
        if spec.get("per_model"):
            pass
        elif len(spec["sizes"]) > 1:
            sizes, prices = spec["sizes"], spec["prices"]
            for i in range(1, len(sizes)):
                at = sizes[i] if spec["exact"] else sizes[i - 1] + 1
                node["modifiers"].append(dict(field=POINTS, type="increment", value=prices[i] - prices[i - 1],
                                              conditions=[selected(main["cat"], scope=unit_id, value=at)]))
            if spec["exact"]:
                legal = ", ".join(str(s) for s in sizes[:-1]) + f" or {sizes[-1]}"
                node["modifiers"].append(dict(type="add", field="error",
                                              value=f"Select {legal} {main['plural']}.",
                                              conditionGroups=[dict(type="and", conditions=[
                                                  selected(main["cat"], scope=unit_id, kind="notEqualTo", value=s)
                                                  for s in sizes])]))
        return main

    def family(self, node, ds, spec, m):
        """Plain models plus model types with other weapons, as in the Emperor's Children Tormentors."""
        unit_id = node["id"]
        low, high = m["count"]
        name = m["name"]
        plural = name if name.endswith("s") else name + "s"
        cat_id, _ = self.category(f"Count: {ds['name']} - {name}", hidden=True)
        per_model = spec.get("per_model")
        weapons_gear = m["weapons"] + m["gear"]

        def model(mid, mname, items, cost):
            gear_nodes = [self.gear_entry(mid, item, ds, fixed=True) for item in items]
            inv = self.model_stats(ds, gear_nodes)
            e = entry(mid, mname, "model", selectionEntries=gear_nodes,
                      profiles=[self.unit_profile(nid(mid + ":profile"), mname, ds["profile"], inv=inv)],
                      categoryLinks=[dict(name="count", id=nid(mid + ":cat:" + cat_id), targetId=cat_id,
                                          primary=False, hidden=False)])
            self.add_model_shields(e, mname, ds, gear_nodes)
            total = (per_model or 0) + cost
            if total:
                e["costs"] = [dict(name="pts", typeId=POINTS, value=total)]
            return e

        bid = nid(unit_id + ":model:" + name)
        base = model(bid, name, weapons_gear, m["cost"])
        mins, maxs = constraint(nid(bid + ":min"), "min", low), constraint(nid(bid + ":max"), "max", high)
        base["constraints"] = [mins, maxs]
        base["defaultAmount"] = low
        variants, errors = [], []
        keys = OrderedDict()
        for v in m["variants"]:
            vid = nid(unit_id + ":variant:" + v["name"])
            items = v["weapons"] + m["gear"] + (v["gear"] or [])
            ve = model(vid, v["name"], items, m["cost"] + v["cost"])
            limit_max = high
            if v["per"]:
                limit_max = v["count"] * (high // v["per"])
            elif v["count"] is not None:
                limit_max = v["count"]
            ve["constraints"] = [constraint(nid(vid + ":max"), "max", limit_max)]
            variants.append(ve)
            if v["count"] is not None:
                keys.setdefault(v["key"], dict(per=v["per"], count=v["count"], ids=[], names=[]))
                keys[v["key"]]["ids"].append(vid)
                keys[v["key"]]["names"].append(v["name"])
            # each special model replaces a plain one
            for limit_id in ((mins["id"], maxs["id"]) if low != high else (maxs["id"],)):
                base.setdefault("modifiers", []).append(dict(field=limit_id, type="increment", value=-1, repeats=[
                    dict(childId=vid, field="selections", scope=unit_id, shared=True, includeChildSelections=True,
                         value=1, repeats=1, roundUp=False)]))
        for key, lim in keys.items():
            kcat, _ = self.category(f"Count: {ds['name']} - {key}", hidden=True)
            for ve in variants:
                if ve["id"] in lim["ids"]:
                    ve["categoryLinks"].append(dict(name="count", id=nid(ve["id"] + ":cat:" + kcat), targetId=kcat,
                                                    primary=False, hidden=False))
            label = " or ".join(n.split(" with ")[-1] if " with " in n else n for n in lim["names"])
            if lim["per"]:
                rule = f"At most {lim['count']} {label} for every {lim['per']} models."
                conds = []
                for n in range(low, high + 1):
                    cap = lim["count"] * (n // lim["per"])
                    conds.append(dict(type="and", conditions=[
                        selected(cat_id, scope=unit_id, kind="equalTo", value=n),
                        selected(kcat, scope=unit_id, value=cap + 1)]))
                errors.append(dict(type="add", field="error", value=rule,
                                   conditionGroups=[dict(type="or", conditionGroups=conds)]))
            else:
                errors.append(dict(type="add", field="error", value=f"At most {lim['count']} {label}.",
                                   conditions=[selected(kcat, scope=unit_id, value=lim["count"] + 1)]))
        if low == high:
            mins["value"] = 0
        span = f"{low}-{high}" if low != high else str(high)
        gid = nid(unit_id + ":family:" + name)
        group = dict(name=f"{span} {plural}", id=gid, hidden=False, defaultSelectionEntryId=base["id"],
                     sortIndex=1,
                     selectionEntries=[base] + variants,
                     constraints=[constraint(nid(gid + ":min"), "min", low), constraint(nid(gid + ":max"), "max", high)])
        node["selectionEntryGroups"].append(group)
        node.setdefault("modifiers", []).extend(errors)
        for counted in spec.get("counted", []):
            self.counted_option(node, ds, counted, cat_id, high, variants)
        return dict(cat=cat_id, plural=plural, low=low, high=high)

    def counted_option(self, node, ds, spec, family_cat, high, variants):
        """Wargear any number of models can take, shown as a count on the unit (e.g. 3x Wrist Shield)."""
        oid = nid(node["id"] + ":counted:" + spec["name"])
        opt = self.gear_entry(node["id"] + ":counted", spec["name"], ds, cost=spec["cost"])
        opt["id"] = oid
        cap = opt["constraints"][0]
        cap["id"] = nid(oid + ":max")
        cap["value"] = high
        opt["modifiers"] = []
        for v in variants:
            if v["name"] in spec["exclude"]:
                opt["modifiers"].append(dict(field=cap["id"], type="increment", value=-1, repeats=[
                    dict(childId=v["id"], field="selections", scope=node["id"], shared=True,
                         includeChildSelections=True, value=1, repeats=1, roundUp=False)]))
        opt["name"] = spec["name"]
        node["selectionEntries"].append(opt)

    # ------------------------------------------------------------ Sergeants and Auxiliaries
    def shared_model(self, name, auxiliary):
        if name in self.shared_models:
            return self.shared_models[name]
        ds, spec = self.data[name], MODELS[name]
        mid = nid("model:" + name)
        node = self.single_model(mid, ds, spec)
        node["costs"] = [dict(name="pts", typeId=POINTS, value=ds["points"])]
        if auxiliary:
            node["costs"].append(dict(name="Auxiliary Slots", typeId=self.aux_slot, value=1))
        self.add_abilities(node, ds)
        node["profiles"].append(self.ability_profile(nid(mid + ":keywords"), "Model Keywords",
                                                     ", ".join(ds["keywords"]) + ". These keywords belong to this "
                                                     "model only, not to its unit (Caste Hierarchy)."))
        self.link_weapon_rules(node)
        self.shared_models[name] = node
        return node

    def sergeants(self, node, spec):
        if not spec["sergeants"]:
            return
        gid = nid(node["id"] + ":sergeant")
        links = []
        for name in spec["sergeants"]:
            target = self.shared_model(name, auxiliary=False)
            links.append(dict(name=name, id=nid(gid + ":" + name), targetId=target["id"], type="selectionEntry",
                              hidden=False, **{"import": True}))
        group = dict(name="Sergeant", id=gid, hidden=False, entryLinks=links,
                     constraints=[constraint(nid(gid + ":max"), "max", 1)])
        group["sortIndex"] = 1 if spec["single"] else 0  # on top, like the Tormentors' Obsessionist (below a character)
        node["selectionEntryGroups"].append(group)

    def aux_types(self, unit, pool, family, gid):
        """Tormentor layout: every Auxiliary loadout is its own model type with a counter (as "Tormentor with
        Meltagun"), and Specialist abilities and optional wargear are unit options with a model picker (as the
        Icon of Excess). An ability that replaces the model's weapons (Proximity Detonation) is a model type."""
        types, items, seen_items = [], [], set()
        for name in self.aux_members(pool):
            ds, spec = self.data[name], MODELS[name]
            weight = next((w for lst, w in pool["weights"].items() if lst in ds["keywords"]), 1)
            base_max = (pool["fixed"] or 0) // weight
            step = pool["slots"] // weight if pool["per"] and family else 0
            if not base_max and not step:
                continue

            def cap(eid, node):
                c = constraint(nid(eid + ":max"), "max", base_max)
                node.setdefault("constraints", []).append(c)
                if step:
                    node.setdefault("modifiers", []).append(dict(field=c["id"], type="increment", value=step, repeats=[
                        dict(childId=family["cat"], field="selections", scope=unit["id"], shared=True,
                             includeChildSelections=True, value=pool["per"], repeats=1, roundUp=False)]))

            slots = [c for c in spec["choices"] if c["label"] != "Wargear"]
            fixed = self.default_items(ds, spec)
            empties = {o: set(labels) for o, labels in spec.get("empties", [])}
            excluded = {o: set(others) for o, others in spec.get("exclude", [])}
            combos = [([], 0)]
            for c in slots:  # every legal loadout across the weapon slots is one model type
                combos = [(picked + [(c["label"], o)], cost + (c["costs"].get(o, 0) if o else 0))
                          for picked, cost in combos for o in c["options"] + [None]]
            loadouts = []
            for picked, cost in combos:
                chosen = [o for _, o in picked if o]
                emptied = set().union(*(empties.get(o, set()) for o in chosen))
                if all((o is None) == (label in emptied) for label, o in picked) and \
                        not any(excluded.get(o, set()) & set(chosen) for o in chosen):
                    loadouts.append((chosen, cost))
            default = set(loadouts[0][0]) if loadouts else set()
            variants = []
            for chosen, cost in loadouts:
                parts = [p for o in chosen for p in split_option(o)]
                diff = [option_name(o) for o in chosen if o not in default]
                label = (", ".join(diff[:-1]) + " and " + diff[-1]) if len(diff) > 1 else "".join(diff)
                variants.append((label, fixed + parts, cost, False, set(parts) | set(chosen)))
            for a in ds.get("specialist_abilities", []):
                if a.get("replaces_weapons"):
                    variants.append((a["name"], split_option(self.specialist_option(a)), a["points"], True, []))
            bearers = {}
            for label, gear_items, cost, replaces, parts in variants:
                tname = name + (f" with {label}" if label else "")
                tid = nid(gid + ":type:" + tname)
                gear = [self.gear_entry(tid, item, ds, fixed=True) for item in gear_items]
                e = entry(tid, tname, "model", selectionEntries=gear, profiles=[], costs=[
                    dict(name="pts", typeId=POINTS, value=ds["points"] + cost),
                    dict(name="Auxiliary Slots", typeId=self.aux_slot, value=weight)])
                e["profiles"].append(self.unit_profile(nid(tid + ":profile"), tname, ds["profile"],
                                                       inv=self.model_stats(ds, gear)))
                self.add_model_shields(e, tname, ds, gear)
                self.add_abilities(e, ds)
                e["profiles"].append(self.ability_profile(nid(tid + ":keywords"), "Model Keywords",
                                                          ", ".join(ds["keywords"]) + ". These keywords belong to "
                                                          "this model only, not to its unit (Caste Hierarchy)."))
                cap(tid, e)
                self.link_weapon_rules(e)
                for key in ("selectionEntries", "infoLinks"):
                    if key in e and not e[key]:
                        del e[key]
                e["_source"] = name
                types.append(e)
                if not replaces:
                    bearers[tid] = parts
            options = [(o, c["costs"].get(o, 0)) for c in spec["choices"] if c not in slots for o in c["options"]]
            options += [(self.specialist_option(a), a["points"]) for a in ds.get("specialist_abilities", [])
                        if not a.get("replaces_weapons")]
            for option, cost in options:
                head = option_name(split_option(option)[0])
                iname = head if head not in seen_items else f"{head} ({name})"
                seen_items.add(head)
                wid = nid(gid + ":item:" + name + ":" + option)
                item = self.gear_entry(gid + ":item:" + name, option, ds, cost=cost)
                item["id"], item["name"], item["constraints"] = wid, iname, []
                cap(wid, item)
                allowed = [t for t, parts in bearers.items() if not parts & excluded.get(option, set())]
                item["associations"] = [dict(
                    name=iname, id=nid(wid + ":bearer"), childId="model", includeChildSelections=True, min=1, max=1,
                    scope=unit["id"], defaultSelectionEntryId="none", conditionGroups=[dict(type="or", conditions=[
                        dict(childId=t, field="selections", scope="self", type="instanceOf", value=1, shared=True,
                             includeChildSelections=True) for t in allowed])])]
                item["sortIndex"] = 3
                self.link_weapon_rules(item)
                items.append(item)
        return types, items

    def addon_keywords(self, node, ds):
        """The unit gains a species keyword while it includes a Sergeant or Auxiliary model with it."""
        have = {k.casefold() for k in ds["keywords"]}
        shared = {m["id"]: n for n, m in self.shared_models.items()}
        sources = OrderedDict()
        for sub in walk(node):
            if not isinstance(sub, dict):
                continue
            name = sub.get("_source") or (shared.get(sub.get("targetId")) if sub.get("type") == "selectionEntry" else None)
            if not name:
                continue
            for kw in self.data[name]["keywords"]:
                if kw in SPECIES and kw.casefold() not in have:
                    sources.setdefault(kw, []).append(sub.get("targetId") or sub["id"])
        for kw, ids in sources.items():
            cat_id, _ = self.category(kw)
            node.setdefault("modifiers", []).append(dict(type="add", field="category", value=cat_id, conditionGroups=[
                dict(type="or", conditions=[selected(i, scope=node["id"]) for i in dict.fromkeys(ids)])]))

    def aux_members(self, pool):
        names = list(pool["entries"])
        for lst in pool["lists"]:
            for ds in self.data.values():
                if ds["category"] == "AUXILIARY" and lst in ds["keywords"] and ds["name"] not in names:
                    names.append(ds["name"])
        return names

    def auxiliaries(self, node, spec, family):
        for i, pool in enumerate(spec["aux"]):
            gid = nid(node["id"] + f":auxiliary:{i}")
            label = "Auxiliary" if len(spec["aux"]) == 1 else "Auxiliary: " + ", ".join(
                [e.replace(" Auxiliary", "") for e in pool["entries"]] + pool["lists"])
            cap = constraint(nid(gid + ":slots"), "max", pool["fixed"] or 0, field=self.aux_slot, child=True)
            types, items = self.aux_types(node, pool, family, gid)
            node["selectionEntries"].extend(items)
            group = dict(name=label, id=gid, hidden=False, constraints=[cap], selectionEntries=types, sortIndex=2)
            if pool["per"] and family:
                group["modifiers"] = [dict(field=cap["id"], type="increment", value=pool["slots"], repeats=[
                    dict(childId=family["cat"], field="selections", scope=node["id"], shared=True,
                         includeChildSelections=True, value=pool["per"], repeats=1, roundUp=False)])]
            weights = ", ".join(f"{lst} {w}" for lst, w in pool["weights"].items())
            group["_note"] = weights
            node["selectionEntryGroups"].append(group)

    # ------------------------------------------------------------ army rules
    def army_rules(self):
        text = (self.source / "army_rules.md").read_text()
        for name, lines in sections(text):
            if name is None:
                continue
            body = "\n".join(lines).strip()
            self.rule(name, body)
        # the game system has the FRAME keyword but no rule text for it; linked on every FRAME unit
        self.rule("Frame", "Core rules 17.02. Whenever a rule refers to a FRAME model's position relative to anything "
                           "else on the battlefield, such as when measuring distances, measure to and from the closest "
                           "point of that model, not necessarily its base. When a FRAME model without a base rotates "
                           "as part of a move, turn it any amount around its central axis, keeping it upright.")

    # ------------------------------------------------------------ attachments
    def associations(self, units):
        by_name = {u["name"]: u for u in units}
        for unit in units:
            ds = self.data[unit["name"]]
            text = " ".join(ds["leader"])
            m = re.search(r"attached to:\s*(.+?)\.", text)
            if not m:
                continue
            targets = [t.strip() for t in re.split(r",\s*", m.group(1)) if t.strip()]
            missing = [t for t in targets if t not in by_name]
            assert not missing, (unit["name"], missing)
            unit["associations"] = [dict(
                name="Leading", id=nid(unit["id"] + ":Leader"), action="group", childId="unit", childName="unit",
                includeChildSelections=True, label="Leader", max=1, min=0, scope="force",
                conditionGroups=[dict(type="or", conditions=[
                    dict(childId=by_name[t]["id"], field="selections", scope="self", type="instanceOf", value=1,
                         shared=True, includeChildSelections=True) for t in targets])])]

    # ------------------------------------------------------------ detachments
    def plain_keywords(self, text):
        """Restrictions print keywords in capitals (MGALEKGOLO unit only); match them by their datasheet spelling."""
        if not hasattr(self, "_keyword_case"):
            names = {k for d in self.data.values() for k in d["keywords"]} | {"Covenant", "Drone Swarm"}
            self._keyword_case = sorted(((k.upper(), k) for k in names), key=lambda t: -len(t[0]))
        for upper, plain in self._keyword_case:
            text = re.sub(rf"(?<![\w']){re.escape(upper)}(?![\w'])", plain, text)
        return text

    def eligible(self, det, enh, ds):
        """Which datasheets an Enhancement or Upgrade can go on."""
        kws = set(ds["keywords"])
        cat = ds["category"]
        restriction = self.plain_keywords(enh["restriction"] or "")
        character = "Character" in kws and "Epic Hero" not in kws
        spec = enh.get("eligible")  # {"all": [...], "any": [...], "names": [...], "sp": bool}
        if spec:
            if enh["upgrade"] and (cat in ("SERGEANT", "AUXILIARY") or "Character" in kws):
                return False
            if not enh["upgrade"] and not character:
                return False
            return ((not spec.get("names") or ds["name"] in spec["names"])
                    and all(k in kws for k in spec.get("all", []))
                    and (not spec.get("any") or bool(kws & set(spec["any"])))
                    and (not spec.get("sp") or bool(ds["profile"].get("SP"))))
        if not enh["upgrade"]:
            m = re.match(r"(.+?) model only\.?$", restriction)  # SANGHEILI model only. / SAN'SHYUUM or UNGGOY model only.
            if not m:
                return character
            names = m.group(1).split(" or ")
            if any(n in self.data for n in names):  # a named datasheet: Sangheili Shipmaster model only.
                return ds["name"] in names
            return character and bool(kws & set(names))
        if cat in ("SERGEANT", "AUXILIARY") or "Character" in kws and "excluding Character" in restriction:
            return False
        m = re.match(r"Upgrade - (\S+(?: \S+)?) Infantry unit only", restriction)
        if m:
            kw = m.group(1)
            return "Infantry" in kws and (kw == "Covenant" or kw in kws) and "Character" not in kws
        self.log.append(f"Unrecognised restriction for {enh['name']}: {restriction}")
        return False

    def detachments(self, units):
        did = nid("detachment-entry")
        gid = nid("detachment-group")
        group = dict(name="Detachment", id=gid, hidden=False, selectionEntries=[], import_=True,
                     constraints=[constraint(nid(gid + ":min"), "min", 1, field=DP, child=True),
                                  constraint(nid(gid + ":max"), "max", 2, field=DP, child=True)], modifiers=[])
        group["import"] = group.pop("import_")
        det_entry = entry(did, "Detachment", categoryLinks=[dict(name="Configuration", id=nid(did + ":cat"),
                                                                 primary=True, targetId=CONFIGURATION)],
                          constraints=[dict(id=nid(did + ":min"), field="selections", includeChildForces=True,
                                            includeChildSelections=True, scope="roster", shared=True, type="min",
                                            value=1),
                                       dict(id=nid(did + ":max"), field="selections", includeChildForces=True,
                                            includeChildSelections=True, scope="roster", shared=True, type="max",
                                            value=-1)],
                          selectionEntryGroups=[group])
        enhancements, strat_links, unique = [], [], {}
        by_name = {u["name"]: u for u in units}
        for det in self.dets:
            det_id = nid("detachment:" + det["name"])
            node = entry(det_id, det["name"], constraints=[constraint(nid(det_id + ":max"), "max", 1)],
                         costs=[dict(name="Detachment Points", typeId=DP, value=det["dp"])], rules=[],
                         categoryLinks=[])
            tags = (["3DP Detachment"] if det["dp"] == 3 else []) + [det["disposition"]]
            node["categoryLinks"] = [self.cat_link(det_id, t) for t in tags]
            if det["unique"]:
                uname = "Unique: " + det["unique"].upper()
                unique.setdefault(uname, []).append(node)
                node["categoryLinks"].append(self.cat_link(det_id, uname, hidden=True))
            intro = " ".join(det["rules_intro"])
            for r in det["rules"]:
                body = "\n\n".join(r["text"])
                if intro:
                    body = intro + "\n\n" + body
                    intro = ""
                node["rules"].append(dict(name=r["name"], id=nid(det_id + ":rule:" + r["name"]), hidden=False,
                                          description="\n\n" + inches(body)))
            group["selectionEntries"].append(node)
            if det.get("forbid"):  # Swords of Sanghelios: no JIRALHANAE or SAN'SHYUUM models in the army
                banned = set(det["forbid"])
                message = f"{det['name']}: your army cannot include " + " or ".join(
                    k.upper() for k in det["forbid"]) + " models."
                targets = units + list(self.shared_models.values()) + [
                    t for u in units for t in walk(u) if isinstance(t, dict) and t.get("_source")]
                for t in targets:
                    ds = self.data.get(t.get("_source") or t["name"])
                    if ds and banned & set(ds["keywords"]):
                        t.setdefault("modifiers", []).append(dict(type="add", field="error", value=message,
                                                                  conditions=[selected(det_id, scope="roster")]))
            for e in det["enhancements"]:
                enhancements.append(self.enhancement(det, det_id, e, units))
            for s in det["stratagems"]:
                name = f"{det['name']} — {s['name']} / {s['cp']} CP"
                fields = [("When", s.get("when")), ("Target", s.get("target")), ("Effect", s.get("effect")),
                          ("Restrictions", s.get("restriction"))]
                body = f"*{s['type']}*\n\n" + "\n\n".join(f"### {k}\n\n{inches(v)}" for k, v in fields if v)
                rule = self.rule(name, body)
                strat_links.append(dict(name=name, id=nid("stratagem-references:" + rule["id"]), targetId=rule["id"],
                                        type="rule", hidden=True, modifiers=[
                                            dict(field="hidden", value=False, type="set",
                                                 conditions=[selected(det_id)])]))
        for uname, dets in unique.items():
            ucat = self.categories[uname.casefold()]
            ucat["constraints"] = [constraint(nid(ucat["id"] + ":max"), "max", 1, scope="roster", child=True)]
            if len(dets) > 1:
                for det in dets:
                    others = [selected(o["id"], scope="roster") for o in dets if o is not det]
                    det["modifiers"] = [dict(type="set", field=det["constraints"][0]["id"], value=0,
                                             conditionGroups=[dict(type="or", conditions=others)])]
        return det_entry, enhancements, strat_links

    def enhancement(self, det, det_id, e, units):
        eid = nid("enhancement:" + det["name"] + ":" + e["name"])
        name = e["name"] + (" [Upgrade]" if e["upgrade"] else "")
        body = "\n\n".join(e["text"])
        description = ((e["restriction"] + "\n\n") if e["restriction"] else "") + body
        shared = e["upgrade"]  # 11e: up to three of the same Upgrade, sharing one Enhancement selection
        limit = 3 if shared else 1
        node = entry(eid, name, costs=[dict(name="pts", typeId=POINTS, value=e["points"]),
                                       dict(name="Enhancements", typeId=ENHANCEMENT_SLOT, value=1),
                                       dict(name="Enhancement or Upgrade", typeId=self.enh_count, value=1)],
                     constraints=[constraint(nid(eid + ":max"), "max", limit, scope="roster", child=True)],
                     rules=[dict(name=e["name"], id=nid(eid + ":rule"), hidden=False, description=inches(description))])
        if shared:  # all copies share one Enhancement selection
            node["modifiers"] = [dict(field=ENHANCEMENT_SLOT, type="set", value=0, conditionGroups=[dict(
                type="and", localConditionGroups=[dict(
                    field="selections", includeChildSelections=True, repeats=1, scope="roster", type="atLeast",
                    value=1, conditions=[
                        dict(childId="any", field="selections", scope="self", type="before", value=1, shared=True,
                             includeChildSelections=True),
                        dict(childId=eid, field="selections", scope="self", type="instanceOf", value=1, shared=True,
                             includeChildSelections=True)])])])]
        hits = 0
        for unit in units:
            ds = self.data[unit["name"]]
            if not self.eligible(det, e, ds):
                continue
            groups = unit.setdefault("selectionEntryGroups", [])
            g = next((x for x in groups if x["name"] == "Enhancements and Upgrades"), None)
            if not g:
                gid = nid(unit["id"] + ":enhancements")
                g = dict(name="Enhancements and Upgrades", id=gid, hidden=False, entryLinks=[],
                         constraints=[constraint(nid(gid + ":max"), "max", 1)])
                groups.append(g)
            link = dict(name=name, id=nid(g["id"] + ":" + eid), targetId=eid, type="selectionEntry", hidden=True,
                        modifiers=[dict(field="hidden", value=False, type="set", conditions=[selected(det_id)])],
                        constraints=[constraint(nid(g["id"] + ":" + eid + ":once"), "max", 1)])
            link["import"] = True
            g["entryLinks"].append(link)
            hits += 1
        if not hits:
            self.log.append(f"No eligible unit for {name}")
        return node


def reference_entry(eid, name, links):
    node = entry(eid, name, categoryLinks=[dict(name="Reference", id=nid(eid + ":cat"), targetId=REFERENCE,
                                                primary=True, hidden=False)],
                 constraints=[constraint(nid(eid + ":min"), "min", 1), constraint(nid(eid + ":max"), "max", 1)])
    node["infoLinks"] = links
    return node


def strip_private(node):
    for sub in walk(node):
        if isinstance(sub, dict):
            for key in [k for k in sub if k.startswith("_")]:
                del sub[key]


def build(source, system_path):
    system = json.loads(Path(system_path).read_text())
    b = Builder(source, system)
    b.army_rules()
    names = [n for n, d in b.data.items() if d["category"] not in ("SERGEANT", "AUXILIARY")]
    missing = [n for n in names if n not in UNITS] + [n for n, d in b.data.items()
                                                      if d["category"] in ("SERGEANT", "AUXILIARY") and n not in MODELS]
    assert not missing, missing
    units = [b.datasheet(n) for n in names]
    for n, d in b.data.items():  # reference entries for every Sergeant and Auxiliary model (not root-linked)
        if d["category"] in ("SERGEANT", "AUXILIARY"):
            b.shared_model(n, auxiliary=d["category"] == "AUXILIARY")
    b.associations(units)
    det_entry, enhancements, strat_links = b.detachments(units)
    for unit in units:  # an Attached Unit has at most one Enhancement or Upgrade
        unit.setdefault("constraints", []).append(dict(
            id=nid(unit["id"] + ":attached-enhancement"), childId="any", field=b.enh_count, type="max", value=1,
            scope="root-entry", shared=True, includeChildSelections=True, includeChildForces=False,
            traverseAssociationGroup=True, message="An Attached Unit can only take 1 Enhancement or Upgrade."))

    warlord_role = next(c for c in b.system["categoryEntries"] if c["name"] == "Warlord")
    warlord_id = nid("warlord-selection")
    warlord = entry(warlord_id, "Warlord", categoryLinks=[dict(name="Warlord", id=nid(warlord_id + ":cat"),
                                                               targetId=warlord_role["id"], primary=False,
                                                               hidden=False)],
                    constraints=[constraint(nid(warlord_id + ":max"), "max", 1, scope="roster", child=True)])
    for unit in units:
        if "Character" in b.data[unit["name"]]["keywords"]:
            unit.setdefault("entryLinks", []).append(dict(name="Warlord", id=nid(unit["id"] + ":warlord"),
                                                          targetId=warlord_id, type="selectionEntry", hidden=False,
                                                          **{"import": True}))
    army_ref_id = nid("army-rules-and-references")
    army_ref = reference_entry(army_ref_id, "Army Rules and References",
                               [dict(id=nid(army_ref_id + ":" + n), name=n, targetId=b.rules[n]["id"], type="rule",
                                     hidden=False) for n in ARMY_RULES])
    strat_ref = reference_entry(nid("stratagem-references"), "Stratagem References", strat_links)

    cat = OrderedDict()
    cat["name"] = NAME
    cat["id"] = nid("catalogue")
    cat["battleScribeVersion"] = 2.03
    cat["gameSystemId"] = "sys-352e-adc2-7639-d610"
    cat["xmlns"] = "http://www.battlescribe.net/schema/catalogueSchema"
    cat["library"] = False
    cat["type"] = "catalogue"
    cat["revision"] = REVISION
    cat["gameSystemRevision"] = b.system["revision"]
    cat["authorName"] = "Xverse homebrew"
    cat["authorContact"] = ""
    cat["readme"] = "Covenant 11th-edition homebrew codex (Codex: Covenant v5.5.0, revised Caste Hierarchy)."
    cat["costTypes"] = [dict(name="Auxiliary Slots", id=b.aux_slot, defaultCostLimit=-1, hidden=True),
                        dict(name="Enhancement or Upgrade", id=b.enh_count, defaultCostLimit=-1, hidden=True)]
    cat["profileTypes"] = [b.shields_type]
    cat["categoryEntries"] = list(b.categories.values())
    shared = [det_entry, army_ref, strat_ref, warlord] + units + list(b.shared_models.values()) + enhancements
    cat["sharedSelectionEntries"] = shared
    cat["entryLinks"] = [dict(name=e["name"], id=nid("root:" + e["id"]), hidden=False, targetId=e["id"],
                              type="selectionEntry", **{"import": True}) for e in [det_entry, army_ref, strat_ref] + units]
    cat["sharedRules"] = list(b.rules.values())
    strip_private(cat)
    detachment_point_counter(cat)
    format_subrules(cat)
    for msg in b.log:
        print("NOTE:", msg)
    return dict(catalogue=cat), b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--system", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data, _ = build(args.source, args.system)
    Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Wrote", args.output)


if __name__ == "__main__":
    main()
