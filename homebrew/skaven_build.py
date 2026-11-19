"""Build the Skaven 11th-edition homebrew catalogue for New Recruit.

Sources: the Skaven handoff folder (datasheets.json, points.json, army_rules.md,
detachments/*.md), the current Skaven catalogue (for IDs that saved rosters use)
and the game system. The layout follows the Emperor's Children catalogue.

Usage:
  python3 homebrew/skaven_build.py --source /path/to/handoff \
      --catalogue 'Chaos%20-%20Skaven.json' --system 'Warhammer 40,000.json' --output out.json
"""
import argparse
import copy
import hashlib
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from datasheet_format import add_ability, core_rules, detachment_point_counter, rule_link, weapon_rules  # noqa: E402
from skaven_units import MOUNTS, UNITS  # noqa: E402

POINTS = "51b2-306e-1021-d207"
ENHANCEMENT_SLOT = "f759-1bc4-cb3a-f0d2"
DP = "82ae-1066-5107-6ae0"
INCURSION, STRIKE_FORCE, ONSLAUGHT = "d62d-db22-4893-4bc0", "baf8-997f-e323-a090", "4204-82d0-908c-a62a"
REVISION = 16

RENAMED = {  # current catalogue name -> handoff name (keeps saved-roster IDs)
    "Mutant Rat Ogre": "Mutant Rat Ogor",
    "Skryre Workshop": "Skryre Worship",
    "Knawhole Architect": "Gnawhole Architect",
    "Portable Knawhole Generator": "Portable Gnawhole Generator",
    "Army Rule — Vermin": "The Vermintide",
    "Under-Empire": "The Under-Empire",
}
ARMY_RULE_ORDER = ["The Vermintide", "The Under-Empire", "Scurry Away!", "Warpstone", "Warpstone Backlash",
                   "Sacrifice", "Summoned Vermin", "Verminous Psychic Power", "Lore of Ruin", "Lore of Plague",
                   "Lore of the Hidden Fang", "Special Spells"]
CLAN_UNIQUE = {"Skryre Worship", "Moulder Flesh Laboratory", "Shadowy Dealings", "Cauldron of Pestilence",
               "Clawpack Horde", "Clan Skurvy", "Black-Fur Supremacy"}
DETACHMENTS = {  # DP and Force Dispositions from the handoff
    "Skryre Worship": (3, ["Priority Assets", "Purge the Foe"]),
    "Moulder Flesh Laboratory": (3, ["Purge the Foe", "Take and Hold"]),
    "Shadowy Dealings": (1, ["Disruption"]),
    "Cauldron of Pestilence": (3, ["Take and Hold", "Disruption"]),
    "Clawpack Horde": (2, ["Take and Hold"]),
    "Invasion of the Under-Empire": (3, ["Reconnaissance", "Disruption"]),
    "The Dreaded 13th Bell": (1, ["Priority Assets"]),
    "Clan Skurvy": (2, ["Priority Assets"]),
    "Black-Fur Supremacy": (1, ["Purge the Foe"]),
    "Prophets of the Horned Rat": (1, ["Priority Assets"]),
    "Engines of Ruin": (1, ["Reconnaissance"]),
    "Council of Treachery": (1, ["Take and Hold"]),
}
ROLE_CATEGORY = {"EPIC HERO": "Epic Hero", "CHARACTER": "Character", "BATTLELINE": "Battleline",
                 "INFANTRY": "Infantry", "MOUNTED": "Mounted", "BEAST": "Beast", "MONSTER": "Monster",
                 "VEHICLE": "Vehicle", "DEDICATED TRANSPORT": "Dedicated Transport"}
SMALL = {"of", "the", "a", "an", "and", "or", "to", "in", "on", "for", "with", "at", "by", "from"}


# ---------------------------------------------------------------- text helpers
def nid(key):
    digest = hashlib.sha256(f"skaven-11e:{key}".encode()).hexdigest()[:16]
    return "-".join(digest[i:i + 4] for i in range(0, 16, 4))


def title(text):
    """'GREAT-GREAT DIPLOMAT' -> 'Great-Great Diplomat'; leaves mixed-case text alone."""
    if text != text.upper():
        return text
    words = text.split(" ")
    out = []
    for i, word in enumerate(words):
        if i and word.lower() in SMALL and not re.search(r"[!?:.]$", words[i - 1]):
            out.append(word.lower())
            continue
        parts = []
        for j, part in enumerate(word.split("-")):
            if j and part.lower() in SMALL:
                parts.append(part.lower())
            elif re.fullmatch(r"\d+[A-Z]*|D\d+(\+\d+)?", part):
                parts.append(part.lower() if re.fullmatch(r"\d+[A-Z]+", part) else part)
            else:
                parts.append(part[:1].upper() + part[1:].lower())
        out.append("-".join(parts))
    return " ".join(out)


def weapon_keyword(keyword):
    if keyword.upper() == "TWIN-LINKED":
        return "Twin-linked"
    out = []
    for word in keyword.split(" "):
        if re.fullmatch(r"\d.*|D\d.*", word):
            out.append(word)
        else:
            out.append("-".join(p[:1].upper() + p[1:].lower() for p in word.split("-")))
    text = " ".join(out)
    return re.sub(r"(?<=: )(.+)$", lambda m: m.group(1).replace("Non-", "non-").upper().replace("NON-", "non-"),
                  text)


def labelled(line):
    """'Mounted Profile:Replace ...' -> ('Mounted Profile', 'Replace ...')."""
    m = re.match(r"^([A-Z][^:.]{1,60}?):\s*(\S.*)$", line)
    return (m.group(1).strip(), m.group(2).strip()) if m else (None, line.strip())


def norm(name):
    name = re.sub(r"\s*\(\d+ Workshop Tokens?\)$", "", name)
    return re.sub(r"\s*\[Upgrade\]$", "", name).casefold()


# ---------------------------------------------------------------- BattleScribe nodes
def constraint(cid, kind, value, scope="parent", field="selections", child=False, forces=False):
    c = dict(id=cid, type=kind, value=value, scope=scope, field=field, shared=True, includeChildSelections=child)
    if forces:
        c["includeChildForces"] = True
    return c


def selected(child, scope="force", kind="atLeast", value=1):
    return dict(childId=child, field="selections", scope=scope, type=kind, value=value, shared=True,
                includeChildSelections=True)


def entry(eid, name, kind="upgrade", **extra):
    node = dict(name=name, id=eid, type=kind, hidden=False, import_=True)
    node["import"] = node.pop("import_")
    node.update(extra)
    return node


class Builder:
    def __init__(self, source, catalogue, system):
        self.source = Path(source)
        self.old = catalogue["catalogue"]
        self.system = system["gameSystem"]
        self.data = {d["name"]: d for d in json.loads((self.source / "datasheets.json").read_text())}
        self.points = {e["name"]: e for g in json.loads((self.source / "points.json").read_text())["points"]
                       for e in g["entries"]}
        self.sys_types = {t["name"]: t for t in self.system["profileTypes"]}
        self.sys_categories = {c["name"].casefold(): c for c in self.system["categoryEntries"]}
        self.sys_rules = self.system["sharedRules"]
        old_entries = self.old["sharedSelectionEntries"]
        self.old_ids = {}
        for e in old_entries:
            self.old_ids.setdefault(norm(RENAMED.get(norm_key(e["name"]), e["name"])), e["id"])
        self.old_rules = {norm(RENAMED.get(r["name"], r["name"])): r["id"] for r in self.old["sharedRules"]}
        self.old_categories = {}
        for c in self.old["categoryEntries"]:
            self.old_categories.setdefault(RENAMED.get(c["name"], c["name"]).casefold(), c)
        self.categories = OrderedDict()
        self.rules = OrderedDict()
        self.entries = []
        self.log = []
        self.skurvy_officers = []

    # -- ids and categories
    def entry_id(self, name):
        return self.old_ids.get(norm(name)) or nid("entry:" + name)

    def category(self, name):
        key = name.casefold()
        if key in self.sys_categories:
            c = self.sys_categories[key]
            return c["id"], c["name"]
        if key not in self.categories:
            old = self.old_categories.get(key)
            cid = old["id"] if old else nid("category:" + name)
            self.categories[key] = dict(name=name, id=cid, hidden=False)
        c = self.categories[key]
        c["name"] = name
        return c["id"], name

    def category_link(self, owner, name, primary=False):
        cid, shown = self.category(name)
        return dict(name=shown, id=nid(owner + ":cat:" + cid), targetId=cid, primary=primary, hidden=False)

    def rule(self, name, description):
        rid = self.old_rules.get(norm(name)) or nid("rule:" + name)
        self.rules[name] = dict(name=name, id=rid, hidden=False, description="\n\n" + description.strip())
        return self.rules[name]

    # -- profiles
    def unit_profile(self, pid, name, stats):
        kind = self.sys_types["Unit"]
        values = dict(M=stats.get("M", "-"), T=stats.get("T", "-"), Sv=stats.get("SV", "-"), W=stats.get("W", "-"),
                      LD=stats.get("LD", "-"), OC=stats.get("OC", "-"), InSv=stats.get("INV", "-") or "-")
        return dict(id=pid, name=name, hidden=False, typeId=kind["id"], typeName="Unit",
                    characteristics=[dict(name=c["name"], typeId=c["id"], **{"$text": values[c["name"]]})
                                     for c in kind["characteristicTypes"]])

    def weapon_profile(self, pid, weapon, ranged):
        kind = self.sys_types["Ranged Weapons" if ranged else "Melee Weapons"]
        keywords = ", ".join(weapon_keyword(k) for k in weapon["keywords"]) or "-"
        values = [weapon["range"], weapon["A"], weapon["BS_WS"], weapon["S"], weapon["AP"], weapon["D"], keywords]
        return dict(id=pid, name=weapon["name"], hidden=False, typeId=kind["id"], typeName=kind["name"],
                    characteristics=[dict(name=c["name"], typeId=c["id"], **{"$text": v})
                                     for c, v in zip(kind["characteristicTypes"], values)])

    def ability_profile(self, pid, name, text, hidden=False):
        kind = self.sys_types["Abilities"]
        c = kind["characteristicTypes"][0]
        return dict(id=pid, name=name, hidden=hidden, typeId=kind["id"], typeName="Abilities",
                    characteristics=[dict(name=c["name"], typeId=c["id"], **{"$text": text.strip()})])

    # -- wargear
    def weapons_of(self, ds):
        found = OrderedDict()
        for w in ds["ranged_weapons"]:
            found.setdefault(w["name"], (w, True))
        for w in ds["melee_weapons"]:
            found.setdefault(w["name"], (w, False))
        return found

    def gear_entry(self, owner, option, weapons, fixed=False):
        """An upgrade carrying one or more weapon profiles ('A + B' takes both)."""
        names = [n.strip() for n in option.split(" + ")]
        eid = nid(owner + ":gear:" + option)
        node = entry(eid, " and ".join(names))
        for name in names:
            if name in weapons:
                weapon, ranged = weapons[name]
                node.setdefault("profiles", []).append(
                    self.weapon_profile(nid(eid + ":" + name), weapon, ranged))
            elif name not in {"Heavy shield", "Shield", "Explosive Collars", "Clan Standard", "Scavenger Bell",
                              "Warhorn", "Regimental Banner", "Grounding Rod", "Spare Capacitor", "Plague Banner",
                              "Doom Gong", "Sword and Board", "Warplock"}:
                raise ValueError(f"{owner}: unknown weapon {name}")
        node["constraints"] = [constraint(nid(eid + ":max"), "max", 1)]
        if fixed:
            node["constraints"].insert(0, constraint(nid(eid + ":min"), "min", 1))
        return node

    def choice_group(self, owner, unit_id, spec, weapons, size_large=None):
        gid = nid(owner + ":choice:" + spec["label"])
        options = []
        for option in spec["options"]:
            node = self.gear_entry(gid, option, weapons)
            if spec.get("option_max"):
                node["constraints"][-1]["value"] = spec["option_max"]
            if option in spec["unit_max"]:
                small, large = spec["unit_max"][option]
                limit = constraint(nid(node["id"] + ":unit"), "max", small, scope=unit_id, child=True)
                node["constraints"].append(limit)
                if large != small and size_large:
                    node["modifiers"] = [dict(type="set", field=limit["id"], value=large, conditions=[size_large])]
            options.append(node)
        group = dict(name=spec["label"], id=gid, hidden=False, selectionEntries=options,
                     constraints=[constraint(nid(gid + ":min"), "min", spec["min"]),
                                  constraint(nid(gid + ":max"), "max", spec["max"])])
        if spec.get("scale") and size_large:
            small, large = spec["scale"]
            group["constraints"][1]["value"] = small
            group["modifiers"] = [dict(type="set", field=group["constraints"][1]["id"], value=large,
                                       conditions=[size_large])]
        if spec["min"] >= 1 and len(options) and not spec.get("option_max"):
            group["defaultSelectionEntryId"] = options[0]["id"]
        return group

    # -- datasheets
    def points_of(self, name):
        text = self.points[name]["points"]
        return [int(x) for x in re.findall(r"(\d+)pts", text)]

    def repeat_modifier(self, unit_id, name, text, extra_condition=None, value=None):
        m = re.match(r"\+(\d+)pts from the (\d+)\w\w copy", text or "")
        if not m:
            return None
        group = dict(field="selections", includeChildForces=True, includeChildSelections=True, repeats=1,
                     scope="parent", type="atLeast", value=int(m.group(2)) - 1, conditions=[
                         dict(childId="any", field="selections", scope="self", type="before", value=1, shared=True,
                              includeChildSelections=True),
                         dict(childId=unit_id, childName=name, field="selections", scope="self", type="instanceOf",
                              value=1, shared=True, includeChildSelections=True)])
        outer = dict(type="and", localConditionGroups=[group])
        if extra_condition:
            outer["conditions"] = [extra_condition]
        return dict(field=POINTS, type="increment", value=value or int(m.group(1)), conditionGroups=[outer])

    def keywords(self, owner, ds, primary):
        links = [self.category_link(owner, primary, True)]
        for kw in ds["keywords"]:
            name = ROLE_CATEGORY.get(kw) or title(kw)
            if name != primary:
                links.append(self.category_link(owner, name))
        links.append(self.category_link(owner, "Faction: Skaven"))
        return links

    def add_abilities(self, node, ds, skip=()):
        scurry = self.rules["Scurry Away!"]
        for a in ds["abilities"]:
            name, text = a["name"], a["text"]
            if name in skip:
                continue
            if name == "CORE":
                for item in re.split(r",\s*", text):
                    try:
                        core_rules(node, self.system, item)
                    except ValueError:
                        base = re.sub(r"\s+\d*D\d+.*$", "", item)
                        rule = next(r for r in self.sys_rules if r["name"].casefold() == base.casefold())
                        rule_link(node, rule, item)
            elif name == "FACTION":
                if "SCURRY AWAY!" in text:
                    rule_link(node, scurry)
            elif name == "PSYKER":
                add_ability(node, self.system, "Psyker", text)
            else:
                add_ability(node, self.system, title(name), text)
        for other in ds["other_rules"]:
            body = []
            for line in other["text"]:
                label, rest = labelled(line)
                body.append(f"**{label}:** {rest}" if label else rest)
            add_ability(node, self.system, title(other["name"]), "\n\n".join(body))
        if ds["weapon_notes"]:
            add_ability(node, self.system, "Weapon Profiles", " ".join(ds["weapon_notes"]))

    def attachments(self, node, ds):
        text = " ".join(ds["unit_composition"])
        for kind, pattern in (("Leader", r"[Cc]an lead (.+?)(?: only while ([^.]+))?\."),
                              ("Support", r"attached as a Support to (.+?)(?: only while ([^.]+))?\.")):
            m = re.search(pattern, text)
            if not m:
                continue
            targets = re.split(r",\s*|\s+or\s+", m.group(1))
            body = "This model can be attached to the following units:\n\n" + "\n".join(
                "■ " + t.strip().upper() for t in targets if t.strip())
            if m.group(2):
                body += f"\n\nOnly while {m.group(2).strip()}."
            add_ability(node, self.system, kind, body)

    def datasheet(self, name):
        ds, spec = self.data[name], UNITS[name]
        unit_id = self.entry_id(name)
        weapons = self.weapons_of(ds)
        roles = [r.strip() for r in ds["role"].split("/")]
        primary = "Battleline" if "BATTLELINE" in roles else ROLE_CATEGORY[roles[0]]
        kind = "model" if spec.get("single") else "unit"
        node = entry(unit_id, name, kind, categoryLinks=self.keywords(unit_id, ds, primary), profiles=[],
                     infoLinks=[], selectionEntries=[], selectionEntryGroups=[], modifiers=[], constraints=[],
                     costs=[dict(name="pts", typeId=POINTS, value=0)])
        copies = 1 if "Epic Hero" in (primary, ROLE_CATEGORY.get(roles[0])) else 6 if primary == "Battleline" else 3
        node["constraints"].append(constraint(nid(unit_id + ":copies"), "max", copies, scope="roster", child=True,
                                              forces=True))
        prices = self.points_of(name)
        mount = MOUNTS.get(name)

        if spec.get("single"):
            base = self.unit_profile(nid(unit_id + ":profile"), name, ds["profile"])
            node["profiles"].append(base)
            mount_weapons = set(mount["weapons"]) if mount else set()
            fixed = spec.get("weapons") or [w for w in weapons if w not in mount_weapons]
            for weapon in fixed:
                node["selectionEntries"].append(self.gear_entry(unit_id, weapon, weapons, fixed=True))
            for choice in spec.get("choices", []):
                node["selectionEntryGroups"].append(self.choice_group(unit_id, unit_id, choice, weapons))
            node["costs"][0]["value"] = prices[0] if prices else 0
            for extra in ds["extra_profiles"]:
                if mount and extra["name"] == mount["profile"]:
                    continue
                node["profiles"].append(self.unit_profile(nid(unit_id + ":extra:" + extra["name"]),
                                                          title(extra["name"]), extra["profile"]))
                for line in extra["text"]:
                    label, rest = labelled(line)
                    add_ability(node, self.system, label or title(extra["name"]), rest)
            if mount:
                self.add_mount(node, ds, mount, weapons, base)
        else:
            self.squad(node, ds, spec, weapons, prices)

        self.add_abilities(node, ds)
        self.attachments(node, ds)
        if name == "Vermindoom Land-Fortress":
            self.flagships(node, ds)
        rep = self.repeat_modifier(unit_id, name, ds["repeat_cost"])
        if rep:
            node["modifiers"].append(rep)
        # Source text kept for the codex PDF builder, hidden on the card.
        node["profiles"] += [
            self.ability_profile(nid(unit_id + ":composition"), "Unit Composition and Equipment",
                                 "Composition: " + " ".join(ds["unit_composition"]), hidden=True),
            self.ability_profile(nid(unit_id + ":keywords"), "Printed Keywords and Notes",
                                 "Keywords: " + ", ".join(title(k) for k in ds["keywords"]) +
                                 ". Faction: Skaven.", hidden=True)]
        weapon_rules(node, self.system)
        warpstone = self.rules["Warpstone"]
        for sub in walk(node):
            if any(p.get("typeName", "").endswith("Weapons") and "Warpstone" in p["characteristics"][-1]["$text"]
                   for p in sub.get("profiles", [])):
                rule_link(sub, warpstone)
        for key in ("selectionEntries", "selectionEntryGroups", "modifiers", "infoLinks"):
            if not node[key]:
                del node[key]
        return node

    def add_mount(self, node, ds, mount, weapons, base):
        extra = next(e for e in ds["extra_profiles"] if e["name"] == mount["profile"])
        mid = nid(node["id"] + ":mount")
        option = entry(mid, mount["label"], costs=[dict(name="pts", typeId=POINTS, value=mount["cost"])],
                       constraints=[constraint(nid(mid + ":max"), "max", 1)],
                       profiles=[self.unit_profile(nid(mid + ":profile"), f"{ds['name']} on {mount['label']}",
                                                   extra["profile"])],
                       selectionEntries=[self.gear_entry(mid, w, weapons, fixed=True) for w in mount["weapons"]])
        notes = []
        for line in extra["text"]:
            label, rest = labelled(line)
            if label:
                option["profiles"].append(self.ability_profile(nid(mid + ":" + label), label, rest))
            else:
                notes.append(rest)
        if notes:  # unlabelled lines belong to the mounted-profile rule
            target = next((p for p in option["profiles"] if p["name"] == "Mounted Profile"), None)
            if target:
                target["characteristics"][0]["$text"] += " " + " ".join(notes)
        mounted = selected(mid, scope=node["id"])
        base["modifiers"] = [dict(type="set", field="hidden", value=True, conditions=[mounted])]
        group = dict(name="Mount", id=nid(mid + ":group"), hidden=False, selectionEntries=[option],
                     constraints=[constraint(nid(mid + ":gmax"), "max", 1)])
        node["selectionEntryGroups"].append(group)
        swap = re.search(r"Replace this model's (\w+) keyword with (\w+)", " ".join(extra["text"]))
        if swap:
            old_id, _ = self.category(ROLE_CATEGORY.get(swap.group(1), title(swap.group(1))))
            new_id, _ = self.category(ROLE_CATEGORY.get(swap.group(2), title(swap.group(2))))
            node["modifiers"] += [dict(type="remove", field="category", value=old_id, conditions=[mounted]),
                                  dict(type="add", field="category", value=new_id, conditions=[mounted])]
        rep = self.repeat_modifier(node["id"], ds["name"], ds["repeat_cost"], extra_condition=mounted,
                                   value=mount["repeat"])
        if rep:
            node["modifiers"].append(rep)

    def squad(self, node, ds, spec, weapons, prices):
        unit_id = node["id"]
        model_ids = {}
        sizes = spec.get("sizes", [])
        key = None
        if len(sizes) > 1:
            key = next(m for m in sizes[0] if sizes[0][m] != sizes[-1][m])
        for model in spec["models"]:
            mid = nid(unit_id + ":model:" + model["name"])
            model_ids[model["name"]] = mid
        large = selected(model_ids[key], scope=unit_id, value=sizes[1][key]) if key else None
        for model in spec["models"]:
            mid = model_ids[model["name"]]
            if model["profile"] == "main":
                stats = dict(ds["profile"])
            else:
                stats = next(e for e in ds["extra_profiles"] if e["name"] == model["profile"])["profile"]
            if model["wounds"]:
                stats["W"] = model["wounds"]
            low, high = model["count"]
            m = entry(mid, model["name"], "model",
                      constraints=[constraint(nid(mid + ":min"), "min", low),
                                   constraint(nid(mid + ":max"), "max", high)],
                      profiles=[self.unit_profile(nid(mid + ":profile"), model["name"], stats)],
                      selectionEntries=[self.gear_entry(mid, w, weapons, fixed=True) for w in model["weapons"]],
                      selectionEntryGroups=[self.choice_group(mid, unit_id, c, weapons, large)
                                            for c in model["choices"]])
            if model["cost"]:
                m["costs"] = [dict(name="pts", typeId=POINTS, value=model["cost"])]
            if not m["selectionEntryGroups"]:
                del m["selectionEntryGroups"]
            if not m["selectionEntries"]:
                del m["selectionEntries"]
            node["selectionEntries"].append(m)
        if prices and sizes:
            node["costs"][0]["value"] = prices[0]
            for i in range(1, len(sizes)):
                node["modifiers"].append(dict(field=POINTS, type="increment", value=prices[i] - prices[i - 1],
                                              conditions=[selected(model_ids[key], scope=unit_id,
                                                                   value=sizes[i][key])]))
        if len(sizes) > 1:
            legal = " or ".join(" and ".join(f"{n} {m}" for m, n in s.items()) for s in sizes)
            node["modifiers"].append(dict(type="add", field="error", value=f"Select {legal}.", conditionGroups=[
                dict(type="and", conditionGroups=[
                    dict(type="or", conditions=[selected(model_ids[m], scope=unit_id, kind="notEqualTo", value=n)
                                                for m, n in s.items()]) for s in sizes])]))
        for choice in spec.get("unit_choices", []):
            group = self.choice_group(unit_id, unit_id, choice, weapons, large)
            if choice["label"] == "Loadout":
                for option in group["selectionEntries"]:
                    loadout = spec["loadouts"][option["name"]]
                    option["selectionEntries"] = [self.gear_entry(option["id"], w, weapons, fixed=True)
                                                  for w in loadout["weapons"] + loadout.get("gear", [])]
                    if loadout.get("choices"):
                        option["selectionEntryGroups"] = [self.choice_group(option["id"], unit_id, c, weapons)
                                                          for c in loadout["choices"]]
            node["selectionEntryGroups"].append(group)
        if spec.get("weapon_teams"):
            node["selectionEntryGroups"].append(self.weapon_teams(unit_id, spec, model_ids))

    def weapon_teams(self, unit_id, spec, model_ids):
        gid = nid(unit_id + ":weapon-teams")
        options = []
        for name, source, gear, cost in spec["weapon_teams"]:
            ds = self.data[source]
            mid = nid(gid + ":" + name)
            weapons = self.weapons_of(ds)
            node = entry(mid, name, "model", costs=[dict(name="pts", typeId=POINTS, value=cost)],
                         constraints=[constraint(nid(mid + ":max"), "max", 2)],
                         profiles=[self.unit_profile(nid(mid + ":profile"), name, ds["profile"])],
                         selectionEntries=[self.gear_entry(mid, w, weapons, fixed=True) for w in gear])
            for a in ds["abilities"]:
                if a["name"] not in {"CORE", "FACTION", "PSYKER"} and not a["name"].startswith("Hide Behind"):
                    node["profiles"].append(self.ability_profile(nid(mid + ":" + a["name"]), title(a["name"]),
                                                                 a["text"]))
            options.append(node)
        limit = constraint(nid(gid + ":max"), "max", 1)
        return dict(name="Weapon Team models", id=gid, hidden=False, selectionEntries=options,
                    constraints=[limit],
                    modifiers=[dict(type="set", field=limit["id"], value=2,
                                    conditions=[selected(model_ids["Clawleader"], scope=unit_id, value=2)])])

    def flagships(self, node, ds):
        configs = ds["flagship_configurations"]
        intro = configs[0]
        gid = nid(node["id"] + ":flagship")
        options = []
        for config in configs[1:]:
            label = title(config["name"])
            price = self.points_of(next(k for k in self.points if k.startswith("Vermindoom Clan Flagship: ") and
                                        k.split(": ", 1)[1].casefold() == label.casefold()))
            oid = nid(gid + ":" + label)
            options.append(entry(oid, label, costs=[dict(name="pts", typeId=POINTS, value=price[0])],
                                 constraints=[constraint(nid(oid + ":max"), "max", 1)],
                                 profiles=[self.ability_profile(nid(oid + ":rule"), label,
                                                                " ".join(config["text"]))]))
        node["selectionEntryGroups"].append(dict(
            name="Clan Flagship", id=gid, hidden=False, selectionEntries=options,
            defaultSelectionEntryId=options[0]["id"],
            constraints=[constraint(nid(gid + ":min"), "min", 1), constraint(nid(gid + ":max"), "max", 1)]))
        add_ability(node, self.system, "Clan Flagship", " ".join(intro["text"]))


# ---------------------------------------------------------------- markdown sources
def clean_markdown(lines):
    """Handoff markdown -> catalogue rule text (headings, bullets, tables, bold labels)."""
    out, table = [], []

    def flush():
        if table:
            out.append(table[0])
            cells = table[0].count("|") - 1
            out.append("|" + "---|" * max(cells, 1))
            out.extend(table[1:])
            out.append("")
            table.clear()

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("<!--"):
            continue
        if line.startswith("|"):
            if not re.fullmatch(r"\|[\s:|-]+\|?", line):
                table.append(line)
            continue
        flush()
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            out.append(("### " if len(m.group(1)) <= 3 else "**") + title(m.group(2)).strip() +
                       ("" if len(m.group(1)) <= 3 else "**"))
            continue
        m = re.match(r"^_(.+)_$", line.strip())
        if m:
            out.append("*" + m.group(1) + "*")
            continue
        line = re.sub(r"^\*\*[a-z_]+:\*\*\s*", "", line)  # export keys such as **intro:**
        out.append(line)
    flush()
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def gnawhole_profile(text):
    """The Gnawhole token stat list -> a one-row table."""
    stats = re.findall(r"^- (M|T|SV|W|LD|OC): (.*)$", text, flags=re.M)
    if not stats:
        return text
    table = ("**Gnawhole token profile**\n\n| " + " | ".join(k for k, _ in stats) + " |\n|" + "---|" * len(stats) +
             "\n| " + " | ".join(v for _, v in stats) + " |")
    block = re.search(r"(^- M: .*?^- OC: .*?$)", text, flags=re.M | re.S)
    return text.replace(block.group(1), table)


def sections(text, level="## "):
    """Split markdown into (heading, lines) by a heading level."""
    result, current, lines = [], None, []
    for line in text.splitlines():
        if line.startswith(level):
            if current is not None or lines:
                result.append((current, lines))
            current, lines = line[len(level):].strip(), []
        else:
            lines.append(line)
    result.append((current, lines))
    return result


def cards(lines):
    """'### NAME  [cost]' cards -> (name, cost, italic lines, body lines, preceding marker)."""
    result, marker = [], None
    for heading, body in sections("\n".join(lines), "### "):
        if heading is None:
            for line in body:
                m = re.match(r"^_(.+)_$", line.strip())
                if m:
                    marker = m.group(1)
            continue
        m = re.match(r"^(.*?)\s*\[([^\]]+)\]\s*$", heading)
        name, cost = (m.group(1), m.group(2)) if m else (heading, None)
        italics, rest = [], []
        for line in body:
            im = re.match(r"^_(.+)_$", line.strip())
            if im and not rest:
                italics.append(im.group(1))
            elif im and any(l.strip() for l in rest) is False:
                italics.append(im.group(1))
            else:
                rest.append(line)
        trailing = [i for i, l in enumerate(rest) if re.match(r"^_(.+)_$", l.strip())]
        next_marker = None
        if trailing and all(not l.strip() for l in rest[trailing[-1] + 1:]):
            next_marker = re.match(r"^_(.+)_$", rest[trailing[-1]].strip()).group(1)
            rest = rest[:trailing[-1]]
        result.append(dict(name=title(name.strip()), cost=cost, italics=italics, body=rest, marker=marker))
        if next_marker:
            marker = next_marker
    return result


def norm_key(name):
    return re.sub(r"\s*\(\d+ Workshop Tokens?\)$", "", name)


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


# ---------------------------------------------------------------- army rules
def build_army_rules(b):
    text = (b.source / "army_rules.md").read_text()
    for heading, lines in sections(text):
        if heading is None:
            continue
        name = "Warpstone" if heading == "[WARPSTONE]" else heading
        body = clean_markdown(lines)
        if name == "The Under-Empire":
            body = gnawhole_profile(body)
        body = re.sub(r"^\*(Known by|Known only|Access)", r"*\1", body, flags=re.M)
        b.rule(name, body)
    missing = [n for n in ARMY_RULE_ORDER if n not in b.rules]
    assert not missing, missing


# ---------------------------------------------------------------- eligibility
def unit_keywords(ds):
    return set(ds["keywords"]) | {"SKAVEN"} | {k.split()[0] for k in ds["keywords"] if " " in k}


def eligible(ds, restriction, character_default):
    """Match a printed restriction ('PESTILENS CHARACTER model only.') against a datasheet."""
    kws = unit_keywords(ds)
    text = restriction.replace("UNIT ENHANCEMENT - ", "")
    text = re.sub(r";.*$", "", text)
    if re.search(r"non-EPIC HERO|Non-EPIC HERO", text) or character_default:
        if "EPIC HERO" in kws:
            return False
    text = re.sub(r"[Nn]on-EPIC HERO\s*", "", text)
    if re.search(r"non-CHARACTER", text):
        if "CHARACTER" in kws:
            return False
        text = text.replace("non-CHARACTER ", "")
    if "ranged weapons" in text and not ds["ranged_weapons"]:
        return False
    text = re.sub(r"\b(Select one|model|models|unit|units|only|whose .*|with one or more ranged weapons)\b", " ",
                  text)
    alternatives = [a for a in re.split(r"\s+or\s+", text.strip(" .")) if a.strip()]
    vocabulary = sorted({k for d in [ds] for k in kws} | {"WARLOCK"}, key=len, reverse=True)
    for alt in alternatives:
        words = re.findall(r"[A-Z][A-Z' -]*[A-Z]", alt)
        if not words:
            continue
        needed = []
        rest = " ".join(words)
        for phrase in re.findall(r"[A-Z][A-Z'-]*(?: [A-Z][A-Z'-]*)*", rest):
            needed.append(phrase.strip())
        ok = True
        for phrase in needed:
            tokens = phrase.split()
            # longest known keywords first: 'SKAVEN VEHICLE' -> SKAVEN + VEHICLE
            i = 0
            while i < len(tokens):
                for j in range(len(tokens), i, -1):
                    candidate = " ".join(tokens[i:j])
                    if candidate in kws or (candidate == "WARLOCK" and "WARLOCK ENGINEER" in kws) or \
                            candidate == "TRANSPORT" and ("TRANSPORT" in kws or "DEDICATED TRANSPORT" in kws):
                        i = j
                        break
                else:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            return True
    return False


# ---------------------------------------------------------------- detachments
def build_detachments(b, units):
    detachment_entry = next(e for e in b.old["sharedSelectionEntries"] if e["name"] == "Detachment")
    detachment_entry = copy.deepcopy(detachment_entry)
    group = detachment_entry["selectionEntryGroups"][0]
    old = {RENAMED.get(d["name"], d["name"]): d for d in group["selectionEntries"]}
    clan_id, _ = b.category("Unique: CLAN")
    group["selectionEntries"] = []
    enhancements, stratagems, projects = [], [], []
    files = sorted((b.source / "detachments").glob("*.md"))
    for path in files:
        text = path.read_text()
        name = re.search(r"^# (.+)$", text, flags=re.M).group(1).strip()
        dp, dispositions = DETACHMENTS[name]
        det = old.get(name) or dict(id=nid("detachment:" + name))
        det = dict(name=name, id=det["id"], type="upgrade", hidden=False, **{"import": True},
                   constraints=[constraint(nid(det["id"] + ":max"), "max", 1)],
                   costs=[dict(name="Detachment Points", typeId=DP, value=dp)], rules=[], categoryLinks=[])
        tags = (["3DP Detachment"] if dp == 3 else []) + dispositions + (["Unique: CLAN"] if name in CLAN_UNIQUE else [])
        det["categoryLinks"] = [b.category_link(det["id"], t) for t in tags]
        for heading, lines in merge_continued(sections(text)):
            if heading is None:
                continue
            cost_tokens = re.search(r"\[(\d+) TOKENS?\]", heading)
            if "Stratagems" in heading:
                for card in cards(lines):
                    stratagems.append((det, card))
            elif "Enhancements" in heading:
                for card in cards(lines):
                    enhancements.append((det, card))
            elif cost_tokens:
                for card in cards(lines):
                    card["cost"] = int(cost_tokens.group(1))
                    projects.append((det, card))
            else:
                add_detachment_rules(det, heading, lines)
        link_army_rules(b, det, text)
        group["selectionEntries"].append(det)

    # Only one Unique: CLAN detachment per army.
    clan = [d for d in group["selectionEntries"] if d["name"] in CLAN_UNIQUE]
    for det in clan:
        others = [selected(o["id"]) for o in clan if o is not det]
        det["modifiers"] = [dict(type="set", field=det["constraints"][0]["id"], value=0,
                                 conditionGroups=[dict(type="or", conditions=others)])]
    skryre = next(d for d in group["selectionEntries"] if d["name"] == "Skryre Worship")
    return detachment_entry, enhancements, stratagems, projects, skryre


# Sections whose sub-headings are menu options or procedure steps stay as one rule.
WHOLE_SECTIONS = {"Secret Schemes", "The Great Workshops", "The Master Moulder's Ledger", "The Hidden Ledger", "The Plague Catalogue",
                  "Warlord Commands", "Clawpack Benefits", "The Plunder Ledger"}
ARMY_RULE_PATTERNS = OrderedDict([
    ("The Vermintide", r"\bVermin\b(?! Abilit)|Vermin Abilit|They Just Keep Coming|More-More Bodies"),
    ("The Under-Empire", r"Under-Empire|Gnawhole"),
    ("Scurry Away!", r"Scurry Away|Cornered Rats"),
    ("Warpstone", r"\[WARPSTONE\]"),
    ("Warpstone Backlash", r"Warpstone Backlash"),
    ("Sacrifice", r"\bSacrific"),
    ("Summoned Vermin", r"Summoned Vermin"),
    ("Verminous Psychic Power", r"\bspells?\b|Psyker Level|psychic roll|Overcast"),
])


def merge_continued(parts):
    """Join '<Section> - Continued' back onto its section."""
    merged = []
    for heading, lines in parts:
        base = re.sub(r"\s*[-—]\s*Continued$", "", heading or "")
        if heading and base != heading and merged and merged[-1][0] == base:
            merged[-1] = (base, merged[-1][1] + [""] + lines)
        else:
            merged.append((heading, lines))
    return merged


def add_detachment_rules(det, heading, lines):
    """One rule per named ability, as in the Emperor's Children catalogue."""
    name = title(heading)
    parts = sections("\n".join(lines), "### ")
    if name in WHOLE_SECTIONS or len(parts) == 1:
        det["rules"].append(dict(name=name, id=nid(det["id"] + ":rule:" + name), hidden=False,
                                 description="\n\n" + clean_markdown(lines)))
        return
    for sub, body in parts:
        text = clean_markdown(body)
        if not text:
            continue
        rule_name = name if sub is None else title(sub)
        det["rules"].append(dict(name=rule_name, id=nid(det["id"] + ":rule:" + rule_name), hidden=False,
                                 description="\n\n" + text))


def link_army_rules(b, det, text):
    """Link the army rules a detachment relies on, like Ritual Host -> Summoning Rituals."""
    links = []
    for name, pattern in ARMY_RULE_PATTERNS.items():
        if re.search(pattern, text):
            rule = b.rules[name]
            links.append(dict(id=nid(det["id"] + ":link:" + name), name=name, targetId=rule["id"], type="rule",
                              hidden=False))
    if links:
        det["infoLinks"] = links


def gated(owner_id, target_id, name, det_id, link_type="selectionEntry"):
    link = dict(name=name, id=nid(owner_id + ":" + target_id), targetId=target_id, type=link_type, hidden=True,
                modifiers=[dict(field="hidden", value=False, type="set", conditions=[selected(det_id)])])
    if link_type == "selectionEntry":
        link["import"] = True
    return link


def build_enhancements(b, enhancements, units):
    shared = []
    for det, card in enhancements:
        restriction = card["italics"][0] if card["italics"] else ""
        unit_level = restriction.startswith("UNIT ENHANCEMENT") or (card["marker"] or "").startswith("Upgrade")
        if card["name"] == "Captain":
            unit_level = False
        name = card["name"] + (" [Upgrade]" if unit_level else "")
        eid = b.old_ids.get(norm(card["name"])) or nid("enhancement:" + card["name"])
        points = int(re.search(r"(\d+)", card["cost"]).group(1))
        body = clean_markdown(card["body"])
        description = (restriction + "\n\n" + body).strip() if restriction else body
        limit = 3 if unit_level and re.search(r"up to three", restriction + body, flags=re.I) else 1
        e = entry(eid, name, costs=[dict(name="pts", typeId=POINTS, value=points),
                                    dict(name="Enhancements", typeId=ENHANCEMENT_SLOT, value=1)],
                  constraints=[constraint(nid(eid + ":max"), "max", limit, scope="roster", child=True)],
                  rules=[dict(name=card["name"], id=nid(eid + ":rule"), hidden=False, description=description)])
        if unit_level and limit > 1:
            e["modifiers"] = [dict(field=ENHANCEMENT_SLOT, type="set", value=0, conditionGroups=[dict(
                type="and", localConditionGroups=[dict(
                    field="selections", includeChildSelections=True, repeats=1, scope="roster", type="atLeast",
                    value=1, conditions=[
                        dict(childId="any", field="selections", scope="self", type="before", value=1, shared=True,
                             includeChildSelections=True),
                        dict(childId=eid, field="selections", scope="self", type="instanceOf", value=1, shared=True,
                             includeChildSelections=True)])])])]
        shared.append(e)
        hits = 0
        for unit in units:
            ds = b.data[unit["name"]]
            if not eligible(ds, restriction or "SKAVEN CHARACTER", not unit_level):
                continue
            if not unit_level and "CHARACTER" not in ds["keywords"]:
                continue
            groups = unit.setdefault("selectionEntryGroups", [])
            g = next((x for x in groups if x["name"] == "Enhancements and Upgrades"), None)
            if not g:
                gid = nid(unit["id"] + ":enhancements")
                g = dict(name="Enhancements and Upgrades", id=gid, hidden=False, entryLinks=[],
                         constraints=[constraint(nid(gid + ":max"), "max", 1)])
                groups.append(g)
            g["entryLinks"].append(gated(g["id"], eid, name, det["id"]))
            hits += 1
        if not hits and "SKURVY CHARACTER" in restriction:
            b.skurvy_officers.append((det, e))
        elif not hits:
            b.log.append(f"No eligible unit for enhancement {name} ({restriction})")
    return shared


PROJECT_TOKENS = "95a1-fc42-7bd0-9091"


def build_projects(b, projects, units, skryre):
    shared, army_level = [], []
    for det, card in projects:
        restriction = card["italics"][0] if card["italics"] else ""
        eid = b.old_ids.get(norm(card["name"])) or nid("project:" + card["name"])
        body = clean_markdown(card["body"])
        e = entry(eid, card["name"], costs=[dict(name="Workshop Tokens", typeId=PROJECT_TOKENS, value=card["cost"])],
                  constraints=[constraint(nid(eid + ":max"), "max", 1, scope="roster", child=True)],
                  rules=[dict(name=card["name"], id=nid(eid + ":rule"), hidden=False,
                              description=(f"*{restriction}*\n\n" if restriction else "") + body)])
        shared.append(e)
        if not restriction or restriction.startswith("Unassigned") or card["name"] == "Doomsphere":
            army_level.append(e)
            continue
        hits = 0
        for unit in units:
            ds = b.data[unit["name"]]
            character = "CHARACTER" in restriction
            if character and "CHARACTER" not in ds["keywords"]:
                continue
            ok = eligible(ds, restriction, character)
            big_guns = (not ok and "WEAPON TEAM" in restriction and "STORMFIENDS" in ds["keywords"])
            if not ok and not big_guns:
                continue
            groups = unit.setdefault("selectionEntryGroups", [])
            g = next((x for x in groups if x["name"] == "Workshop Projects"), None)
            if not g:
                gid = nid(unit["id"] + ":projects")
                g = dict(name="Workshop Projects", id=gid, hidden=False, entryLinks=[],
                         constraints=[constraint(nid(gid + ":max"), "max", 2)])
                groups.append(g)
            link = gated(g["id"], eid, card["name"], skryre["id"])
            if big_guns:  # Big-Big Guns For Big-Big Rats! opens Weapon Team projects to Stormfiends
                bbg = next(x for d, x in projects if x["name"].startswith("Big-Big Guns"))
                bbg_id = b.old_ids.get(norm(bbg["name"])) or nid("project:" + bbg["name"])
                link["modifiers"][0]["conditions"].append(selected(bbg_id, scope=unit["id"]))
            g["entryLinks"].append(link)
            hits += 1
        if not hits:
            b.log.append(f"No eligible unit for project {card['name']} ({restriction})")
    budget = constraint(nid(skryre["id"] + ":tokens"), "max", 12, scope="roster", field=PROJECT_TOKENS, child=True,
                        forces=True)
    skryre["constraints"].append(budget)
    skryre.setdefault("modifiers", []).extend([
        dict(type="set", field=budget["id"], value=6, conditions=[selected(INCURSION, scope="roster")]),
        dict(type="set", field=budget["id"], value=18, conditions=[selected(ONSLAUGHT, scope="roster")])])
    return shared, army_level


def build_stratagems(b, stratagems):
    links = []
    for det, card in stratagems:
        cost = card["cost"].replace(" ", "").upper().replace("CP", "")
        name = f"{det['name']} — {card['name']} / {cost} CP"
        fields = OrderedDict()
        for line in card["body"]:
            m = re.match(r"^\*\*(WHEN|TARGET|EFFECT|RESTRICTIONS?):\*\*\s*(.*)$", line.strip())
            if m:
                fields[m.group(1).title()] = m.group(2)
            elif fields and line.strip():
                last = next(reversed(fields))
                fields[last] += "\n\n" + line.strip()
        kind = card["italics"][0] if card["italics"] else ""
        body = (f"*{kind}*\n\n" if kind else "") + "\n\n".join(f"### {k}\n\n{v}" for k, v in fields.items())
        rule = b.rule(name, body)
        links.append(gated("stratagem-references", rule["id"], name, det["id"], "rule"))
    return links


# ---------------------------------------------------------------- display
def format_subrules(catalogue):
    """Emperor's Children layout: sub-headings are bold lines, not large Markdown headings.

    Same rules as format_subrules in ec-4.0-migrate.py, after turning '### Heading' into '**Heading**'.
    """
    paragraph_label = re.compile(r"(^|\n\n)(\*\*[^*\n]+[.:]\*\*) +")
    opening_heading = re.compile(r"^\*\*[^*\n]+\*\*[ \t]*\n")
    heading_before_text = re.compile(r"^(\*\*[^*\n]+\*\*)[ \t]*\n{1,2}(?=[\w'\"“‘*|■-])", re.M)

    def format_text(text):
        text = re.sub(r"^#{1,6}\s+(.+?)\s*$", r"**\1**", text, flags=re.M)
        start = text.lstrip()
        start = paragraph_label.sub(r"\1\2  \n", start)
        body = heading_before_text.sub(r"\1<br>", start)
        if not opening_heading.match(start):
            return text[:len(text) - len(text.lstrip())] + body
        return "\u200b<br><br>" + body

    for node in walk(catalogue):
        for key in ("rules", "sharedRules"):
            for rule in node.get(key, []):
                if not rule.get("hidden") and isinstance(rule.get("description"), str):
                    rule["description"] = format_text(rule["description"])
        if node.get("typeName") == "Abilities" and not node.get("hidden"):
            for field in node["characteristics"]:
                field["$text"] = format_text(field["$text"])


# ---------------------------------------------------------------- assembly
def reference_entry(eid, name, links=None, rules_links=None):
    node = entry(eid, name, categoryLinks=[dict(name="Reference", id=nid(eid + ":cat"),
                                                targetId="eef1-be80-500a-edfc", primary=True, hidden=False)],
                 constraints=[constraint(nid(eid + ":min"), "min", 1), constraint(nid(eid + ":max"), "max", 1)])
    if links:
        node["infoLinks"] = links
    return node


def build(source, catalogue_path, system_path):
    catalogue = json.loads(Path(catalogue_path).read_text())
    system = json.loads(Path(system_path).read_text())
    b = Builder(source, catalogue, system)
    build_army_rules(b)
    units = [b.datasheet(name) for name in b.data]
    detachment_entry, enhancements, stratagems, projects, skryre = build_detachments(b, units)
    shared_enh = build_enhancements(b, enhancements, units)
    shared_projects, army_projects = build_projects(b, projects, units, skryre)
    strat_links = build_stratagems(b, stratagems)

    # Black Contracts (Shadowy Dealings): mark up to three Clanrats units.
    contract_id = b.old_ids.get(norm("Black Contract - Paid Informants")) or nid("black-contract")
    contract = entry(contract_id, "Black Contract - Paid Informants",
                     constraints=[constraint(nid(contract_id + ":max"), "max", 3, scope="roster", child=True)],
                     rules=[dict(name="Paid Informants", id=nid(contract_id + ":rule"), hidden=False,
                                 description="This unit gains the ESHIN keyword and has Scouts 6\".")])
    shadowy = next(d for d in detachment_entry["selectionEntryGroups"][0]["selectionEntries"]
                   if d["name"] == "Shadowy Dealings")
    clanrats = next(u for u in units if u["name"] == "Clanrats")
    gid = nid(clanrats["id"] + ":contract")
    clanrats["selectionEntryGroups"].append(dict(
        name="Black Contract", id=gid, hidden=False, entryLinks=[gated(gid, contract_id, contract["name"],
                                                                      shadowy["id"])],
        constraints=[constraint(nid(gid + ":max"), "max", 1)]))

    # SKURVY CHARACTER enhancements go on Black-Flag mercenary characters, which live in another catalogue.
    officers_id = nid("skurvy-officers")
    skurvy_det = b.skurvy_officers[0][0] if b.skurvy_officers else None
    officers = entry(officers_id, "Skurvy Officers (Black-Flag characters)", hidden=True,
                     categoryLinks=[dict(name="Configuration", id=nid(officers_id + ":cat"),
                                         targetId="4ac9-fd30-1e3d-b249", primary=True, hidden=False)],
                     constraints=[constraint(nid(officers_id + ":max"), "max", 1)],
                     rules=[dict(name="Skurvy Officers", id=nid(officers_id + ":rule"), hidden=False,
                                 description="Each Enhancement here is given to a SKURVY CHARACTER model from "
                                             "Index: Black-Flag. Record which model carries it on your roster.")],
                     entryLinks=[dict(name=e["name"], id=nid(officers_id + ":" + e["id"]), targetId=e["id"],
                                      type="selectionEntry", hidden=False, **{"import": True})
                                 for _, e in b.skurvy_officers])
    if skurvy_det:
        officers["modifiers"] = [dict(field="hidden", type="set", value=False,
                                      conditions=[selected(skurvy_det["id"])])]
    army_ref_id = nid("army-rules-and-references")
    army_ref = reference_entry(army_ref_id, "Army Rules and References",
                               [dict(id=nid(army_ref_id + ":" + n), name=n, targetId=b.rules[n]["id"], type="rule",
                                     hidden=False) for n in ARMY_RULE_ORDER])
    strat_ref = reference_entry(nid("stratagem-references"), "Stratagem References", strat_links)
    workshop_id = nid("army-workshop-projects")
    workshop = entry(workshop_id, "Workshop Projects (Army)", hidden=True,
                     categoryLinks=[dict(name="Configuration", id=nid(workshop_id + ":cat"),
                                         targetId="4ac9-fd30-1e3d-b249", primary=True, hidden=False)],
                     modifiers=[dict(field="hidden", type="set", value=False, conditions=[selected(skryre["id"])])],
                     constraints=[constraint(nid(workshop_id + ":max"), "max", 1)],
                     entryLinks=[dict(name=p["name"], id=nid(workshop_id + ":" + p["id"]), targetId=p["id"],
                                      type="selectionEntry", hidden=False, **{"import": True})
                                 for p in army_projects])

    old = b.old
    keep_links = [l for l in old["entryLinks"]
                  if l["targetId"] not in {e["id"] for e in old["sharedSelectionEntries"]}]  # Black-Flag units
    shared_entries = [detachment_entry, army_ref, strat_ref, workshop, officers, contract] + units + shared_enh + \
        shared_projects
    root_links = []
    for e in [detachment_entry, army_ref, strat_ref, workshop, officers] + units:
        link_id = next((l["id"] for l in old["entryLinks"] if l["targetId"] == e["id"]), nid("root:" + e["id"]))
        root_links.append(dict(name=e["name"], id=link_id, hidden=False, targetId=e["id"], type="selectionEntry",
                               **{"import": True}))
    new = OrderedDict()
    for key in ("name", "id", "battleScribeVersion", "gameSystemId", "xmlns", "library", "type"):
        new[key] = old[key]
    new["name"] = "Chaos - Skaven"
    new["revision"] = REVISION
    new["gameSystemRevision"] = b.system["revision"]
    new["authorName"] = "Xverse homebrew"
    new["authorContact"] = ""
    new["readme"] = "Skaven 11th-edition homebrew codex."
    new["costTypes"] = old.get("costTypes", [])
    new["catalogueLinks"] = old.get("catalogueLinks", [])
    new["categoryEntries"] = list(b.categories.values())
    new["sharedSelectionEntries"] = shared_entries
    new["entryLinks"] = root_links + keep_links
    new["sharedRules"] = list(b.rules.values())
    detachment_point_counter(new)
    format_subrules(new)
    for msg in b.log:
        print("NOTE:", msg)
    return dict(catalogue=new), b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--system", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data, _ = build(args.source, args.catalogue, args.system)
    Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Wrote", args.output)


if __name__ == "__main__":
    main()
