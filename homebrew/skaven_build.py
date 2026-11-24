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
REVISION = 77

RENAMED = {  # current catalogue name -> handoff name (keeps saved-roster IDs)
    "Warlord": "Clawlord",
    "Warpclad Warpack": "Stormclad Stormvermin",
    "Warpclad": "Stormclad",  # the keyword category  # the datasheet (and its keyword); the army's Warlord role is separate
    "Mutant Rat Ogre": "Mutant Rat Ogor",
    "Skryre Workshop": "Skryre Worship",
    "Knawhole Architect": "Gnawhole Architect",
    "Portable Knawhole Generator": "Portable Gnawhole Generator",
    "Army Rule — Vermin": "The Vermintide",
    "Under-Empire": "The Under-Empire",
}
ARMY_RULE_ORDER = ["The Vermintide", "The Under-Empire", "Scurry Away!", "Warpstone", "Warpstone Backlash",
                   "Sacrifice", "Summoned Vermin", "Verminous Psychic Power", "Lore of Ruin", "Lore of Plague",
                   "Lore of the Hidden Fang"]
CLAN_UNIQUE = {"Skryre Worship", "Moulder Flesh Laboratory", "Shadowy Dealings", "Cauldron of Pestilence",
               "Clawpack Horde", "Clan Skurvy", "Council of Treachery"}
DETACHMENTS = {  # DP and Force Dispositions from the handoff
    "Skryre Worship": (2, ["Purge the Foe"]),
    "Moulder Flesh Laboratory": (2, ["Purge the Foe"]),
    "Shadowy Dealings": (2, ["Disruption"]),
    "Cauldron of Pestilence": (2, ["Disruption"]),
    "Clawpack Horde": (2, ["Take and Hold"]),
    "Invasion of the Under-Empire": (3, ["Reconnaissance", "Disruption"]),
    "The Dreaded 13th Bell": (1, ["Priority Assets"]),
    "Clan Skurvy": (2, ["Priority Assets"]),
    "Black-Fur Supremacy": (1, ["Purge the Foe"]),
    "Prophets of the Horned Rat": (1, ["Priority Assets"]),
    "Engines of Ruin": (1, ["Reconnaissance"]),
    "Council of Treachery": (2, ["Take and Hold"]),
    "Warlock Battery": (1, ["Purge the Foe"]),
    "Beast Pens": (1, ["Purge the Foe"]),
    "Night Stalkers": (1, ["Reconnaissance"]),
    "Plague Congregation": (1, ["Take and Hold"]),
    "Endless Swarm": (1, ["Take and Hold"]),
}
# Detachments whose rule gives units the BATTLELINE keyword (and so 6 copies).
BATTLELINE_GRANTS = {"Black-Fur Supremacy": ["STORMVERMIN"], "Warlock Battery": ["WEAPON TEAM"],
                     "Beast Pens": ["RAT OGORS", "WOLF RATS"], "Night Stalkers": ["NIGHT RUNNERS"],
                     "Plague Congregation": ["PLAGUE MONKS"]}
# Sections of detachment rules that are also New Recruit options (as Workshop Projects).
OPTION_SECTIONS = {"Workshop Projects": "project", "Mutations": "mutation", "Ruinous Defects": "defect",
                   "Council Seats": "seat"}
COUNCIL_CLANS = ["VERMINUS", "SKRYRE", "MOULDER", "ESHIN", "PESTILENS", "MASTERCLAN"]
FLESH_SCULPTING = "c1a7-5e0d-4b2f-9e11"
ENH_COUNT = "e7c3-91a2-4d0b-b6f5"  # hidden cost: Enhancements and Upgrades per Attached Unit
ROLE_CATEGORY = {"EPIC HERO": "Epic Hero", "CHARACTER": "Character", "BATTLELINE": "Battleline",
                 "INFANTRY": "Infantry", "MOUNTED": "Mounted", "BEAST": "Beast", "MONSTER": "Monster",
                 "VEHICLE": "Vehicle", "DEDICATED TRANSPORT": "Dedicated Transport"}
# Wargear that changes a model's characteristics (Stormvermin heavy shields).
STAT_GEAR = {"Heavy shield": {"SV": "3+", "INV": "5+"}, "Voltaic shield": {"INV": "4+"}}
# Optional wargear (ticked on the unit) that changes the unit's stat lines while it is taken.
GEAR_STAT_EFFECTS = {"Voltaic Pennant": [("Unit", "LD", 1)]}
STAT_KEYS = {"M": "M", "T": "T", "Sv": "SV", "W": "W", "LD": "LD", "OC": "OC", "InSv": "INV"}
# Abilities that belong to an item other than the one they are named after.
GEAR_ABILITY_HOME = {"Clanrat Shields": "Shield"}
WARGEAR_SORT = 50
# Category IDs referenced from outside the rebuilt entries (the Black-Flag mercenary links add SKURVY).
KEPT_CATEGORY_IDS = {"Skurvy": "085b-ed18-2400-e7f2"}
# Squad leaders do not carry added wargear (standards, horns, banners...).
SERGEANTS = {"Clawleader", "Fangleader", "Plague Deacon", "Bombardier", "Lead Gunner", "Lead Burner",
             "Lead Scourger", "Lead Marksman", "Censer-bearer Leader", "Fang-Adept"}  # added wargear sits at the bottom of the unit editor, as on the Tormentors
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
        self.enh_ids = {}
        self.option_ids = {}
        old_entries = self.old["sharedSelectionEntries"]
        self.old_ids = {}
        # Datasheets first, so a datasheet keeps its ID when an option shares its old name (Warlord -> Clawlord).
        for e in sorted(old_entries, key=lambda e: e["type"] not in ("unit", "model")):
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

    def category(self, name, own=False):
        key = name.casefold()
        if key in self.sys_categories and not own:
            c = self.sys_categories[key]
            return c["id"], c["name"]
        if key not in self.categories:
            old = self.old_categories.get(key)
            cid = KEPT_CATEGORY_IDS.get(name) or (old["id"] if old else nid("category:" + name))
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
                              "Doom Gong", "Sword and Board", "Warplock", "Voltaic shield", "Voltaic Pennant", "Warp-Grenade Satchel",
                              "Smoke Bombs", "Shadow-step Talisman"}:
                raise ValueError(f"{owner}: unknown weapon {name}")
        node["constraints"] = [constraint(nid(eid + ":max"), "max", 1)]
        if fixed:
            node["constraints"].insert(0, constraint(nid(eid + ":min"), "min", 1))
        return node

    def choice_group(self, owner, unit_id, spec, weapons, size_large=None, model=None):
        gid = nid(owner + ":choice:" + spec["label"])
        options = []
        for option in spec["options"]:
            node = self.gear_entry(gid, option, weapons)
            gear = [g.strip() for g in option.split(" + ")]
            if model and any(g in STAT_GEAR for g in gear):
                base_profile = next(p for p in model["profiles"] if p["typeName"] == "Unit")
                stats = {STAT_KEYS[c["name"]]: c["$text"] for c in base_profile["characteristics"]}
                node.setdefault("profiles", []).insert(0, self.unit_profile(
                    nid(node["id"] + ":profile"), gear_label(base_profile["name"], gear), with_gear_stats(stats, gear)))
                base_profile.setdefault("modifiers", []).append(dict(
                    type="set", field="hidden", value=True, conditions=[selected(node["id"], scope=unit_id)]))
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
        move_gear_abilities(node)
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
                rule_link(sub, self.rules["Warpstone Backlash"])  # every [WARPSTONE] weapon shows the Backlash rule
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
        gear_specs = spec.get("bearer_gear", [])

        def gear_for(model):
            if model["name"] in SERGEANTS:
                return []
            return [(g[0], *(g[2] if len(g) > 2 else (1, 1))) for g in gear_specs if g[1] in (None, model["name"])]

        # A model type with special-weapon or wargear versions is counted through a hidden category
        # that every version carries, so "9 Clanrats" includes the standard bearer.
        families = {}
        for model in spec["models"]:
            if model["variants"] or gear_for(model):
                families[model["name"]] = self.hidden_category(f"Count: {ds['name']} - {model['name']}")

        def count_condition(model_name, kind, value):
            child = families.get(model_name, model_ids[model_name])
            return selected(child, scope=unit_id, kind=kind, value=value)

        def size_condition(i, kind="atLeast"):
            return count_condition(key, kind, sizes[i][key])

        large = size_condition(1) if key else None
        large_condition = large
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
                      selectionEntryGroups=[])
            m["selectionEntryGroups"] = [self.choice_group(mid, unit_id, c, weapons, large, model=m)
                                         for c in model["choices"]]
            m["sortIndex"] = len(node["selectionEntries"]) + len(node["selectionEntryGroups"])
            if model["cost"]:
                m["costs"] = [dict(name="pts", typeId=POINTS, value=model["cost"])]
            if not m["selectionEntryGroups"]:
                del m["selectionEntryGroups"]
            if not m["selectionEntries"]:
                del m["selectionEntries"]
            if model["name"] not in families:
                node["selectionEntries"].append(m)
                continue
            family, errors = self.model_family(unit_id, ds["name"], model, m, stats, weapons, large,
                                               gear_for(model), families[model["name"]])
            family["sortIndex"] = m.pop("sortIndex")
            node["selectionEntryGroups"].append(family)
            node["modifiers"] += errors
        # Optional wargear: tick it on the unit, then pick the model that carries it (as the Emperor's
        # Children Icon of Excess). Squad leaders cannot carry it.
        wargear = []
        for model in spec["models"]:
            items = gear_for(model)
            if not items:
                continue
            bearers = [model_ids[model["name"]]]
            for g in node["selectionEntryGroups"]:
                if g.get("id") == nid(unit_id + ":family:" + model["name"]):
                    bearers = [e["id"] for e in g["selectionEntries"]]
            for item, small, big in items:
                wid = nid(unit_id + ":wargear:" + item)
                cap = constraint(nid(wid + ":max"), "max", small)
                w = entry(wid, item, constraints=[cap], profiles=[])
                if big != small and large:
                    w["modifiers"] = [dict(type="set", field=cap["id"], value=big, conditions=[large])]
                w["associations"] = [dict(
                    name=item, id=nid(wid + ":bearer"), childId="model", includeChildSelections=True,
                    min=1, max=1, scope=unit_id, defaultSelectionEntryId="none",
                    conditionGroups=[dict(type="or", conditions=[
                        dict(childId=b_, field="selections", scope="self", type="instanceOf", value=1, shared=True,
                             includeChildSelections=True) for b_ in bearers])])]
                w["_gear"] = item
                wargear.append(w)
        for w in wargear:  # straight on the unit, at the bottom, as the Tormentors' Icon of Excess
            w["sortIndex"] = WARGEAR_SORT
            node["selectionEntries"].append(w)
        self.gear_stats = getattr(self, "gear_stats", [])
        self.gear_stats += [(node, w["id"], GEAR_STAT_EFFECTS[w["name"]]) for w in wargear
                            if w["name"] in GEAR_STAT_EFFECTS]
        if prices and sizes:
            node["costs"][0]["value"] = prices[0]
            for i in range(1, len(sizes)):
                node["modifiers"].append(dict(field=POINTS, type="increment", value=prices[i] - prices[i - 1],
                                              conditions=[size_condition(i)]))
        if len(sizes) > 1:
            legal = " or ".join(" and ".join(f"{n} {m}" for m, n in s.items()) for s in sizes)
            node["modifiers"].append(dict(type="add", field="error", value=f"Select {legal}.", conditionGroups=[
                dict(type="and", conditionGroups=[
                    dict(type="or", conditions=[count_condition(m, "notEqualTo", n) for m, n in s.items()])
                    for s in sizes])]))
        for choice in spec.get("unit_choices", []):
            group = self.choice_group(unit_id, unit_id, choice, weapons, large)
            group["sortIndex"] = 20 if choice["label"] == "Loadout" else WARGEAR_SORT
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
            teams = self.weapon_teams(unit_id, spec, model_ids)
            teams["sortIndex"] = 21
            node["selectionEntryGroups"].append(teams)

    def hidden_category(self, name):
        cid, _ = self.category(name)
        self.categories[name.casefold()]["hidden"] = True
        return cid

    def model_family(self, unit_id, unit_name, model, base, stats, weapons, large, gear, family_cat):
        """Plain models plus model types with special weapons or wargear, as in the Emperor's Children Tormentors.

        Each piece of optional wargear is its own model type ("Stormvermin with Warhorn"), so it is shown on
        the model that carries it, a model carries at most one item, and its ability appears only when taken.
        """
        low, high = model["count"]
        name = model["name"]
        if " with " in name:  # Stormfiend weapon pairs
            plural = "Stormfiends with " + " or ".join(
                n.split(" with ")[1] for n in [name] + [v[0] for v in model["variants"]])
        else:
            plural = name if name.endswith(("s", "min")) else name + "s"
        gid = nid(unit_id + ":family:" + name)
        span = f"{low}-{high}" if low != high else str(high)
        mins, maxs = base["constraints"]
        cat_link = lambda owner, cid: dict(name="count", id=nid(owner + ":cat:" + cid), targetId=cid, primary=False,
                                           hidden=False)
        base["categoryLinks"] = [cat_link(base["id"], family_cat)]
        errors = []

        def cap_error(cid, small, big, label):
            over_small = selected(cid, scope=unit_id, value=small + 1)
            if big == small or not large:
                cond = dict(conditions=[over_small])
            else:
                not_large = dict(large, type="lessThan")
                cond = dict(conditionGroups=[dict(type="or", conditions=[selected(cid, scope=unit_id, value=big + 1)],
                                                  conditionGroups=[dict(type="and",
                                                                        conditions=[over_small, not_large])])])
            limit = f"{small}" if big == small else f"{small} ({big} in the larger unit)"
            errors.append(dict(type="add", field="error", value=f"At most {limit} {label}.", **cond))

        def replaces_plain(vid):
            # Each special model replaces a plain one. A fixed-size squad keeps the plain minimum at 0
            # (see below), so only its maximum drops; lowering 0 would go negative in New Recruit.
            for limit_id in ((mins["id"], maxs["id"]) if low != high else (maxs["id"],)):
                base.setdefault("modifiers", []).append(dict(field=limit_id, type="increment", value=-1, repeats=[
                    dict(childId=vid, field="selections", scope=unit_id, shared=True, includeChildSelections=True,
                         value=1, repeats=1, roundUp=False)]))

        def make(vname, vweapons, small, big, cats):
            vid = nid(unit_id + ":variant:" + vname)
            cap = constraint(nid(vid + ":max"), "max", small)
            v = entry(vid, vname, "model", constraints=[cap],
                      profiles=[self.unit_profile(nid(vid + ":profile"), gear_label(name.split(" with ")[0], vweapons),
                                                  with_gear_stats(stats, vweapons))],
                      selectionEntries=[self.gear_entry(vid, w, weapons, fixed=True) for w in vweapons],
                      categoryLinks=[cat_link(vid, c) for c in cats])
            if big != small and large:
                v["modifiers"] = [dict(type="set", field=cap["id"], value=big, conditions=[large])]
            replaces_plain(vid)
            return v

        bases = [(name, list(model["weapons"]), None, [])]
        variants = []
        for vname, vweapons, limit in model["variants"]:
            small, big = limit or (high, high)
            cats = [family_cat]
            if limit:
                cid = self.hidden_category(f"Count: {unit_name} - {vname}")
                cats.append(cid)
                cap_error(cid, small, big, vname)
            variants.append(make(vname, vweapons, small, big, cats))
            bases.append((vname, vweapons, limit, cats[1:]))
        for item, small, big in []:  # optional wargear is a unit option with a model picker (see squad)
            for bname, bweapons, limit, extra in bases:
                if " with " in bname:
                    head, tail = bname.split(" with ", 1)
                    gname = f"{head} with {tail.replace(' and ', ', ')} and {item}"
                else:
                    gname = f"{bname} with {item}"
                s1, b1 = (small, big) if not limit else (min(small, limit[0]), min(big, limit[1]))
                v = make(gname, bweapons, s1, b1, [family_cat, gear_cat] + extra)
                v["_gear"] = item
                variants.append(v)
        base["defaultAmount"] = low  # as on the Tormentors
        if low == high:
            mins["value"] = 0  # the group's own min/max still enforce the exact squad size
        group = dict(name=f"{span} {plural}", id=gid, hidden=False, defaultSelectionEntryId=base["id"],
                     selectionEntries=[base] + variants,
                     constraints=[constraint(nid(gid + ":min"), "min", low), constraint(nid(gid + ":max"), "max", high)])
        return group, errors

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


def with_gear_stats(stats, gear):
    stats = dict(stats)
    for item in gear:
        stats.update(STAT_GEAR.get(item, {}))
    return stats


def gear_label(name, gear):
    """'Stormvermin' -> 'Stormvermin (Heavy shield)' when wargear changes the stat line."""
    changed = [g for g in gear if g in STAT_GEAR]
    return f"{name} ({', '.join(changed)})" if changed else name


def move_gear_abilities(node):
    """Show an item's ability only when the item is taken."""
    carriers = {}
    for sub in walk(node.get("selectionEntries", []) + node.get("selectionEntryGroups", [])):
        if isinstance(sub, dict) and sub.get("_gear"):
            carriers.setdefault(sub.pop("_gear"), []).append(sub)
    kept = []
    for profile in node.get("profiles", []):
        if profile.get("typeName") == "Abilities" and profile["name"] in carriers:
            for carrier in carriers[profile["name"]]:
                carrier["profiles"].append(dict(profile, id=nid(carrier["id"] + ":ability:" + profile["name"])))
        else:
            kept.append(profile)
    node["profiles"] = kept
    homes = {}
    for sub in walk(node.get("selectionEntries", []) + node.get("selectionEntryGroups", [])):
        if isinstance(sub, dict) and sub.get("type") in ("upgrade", "model") and "name" in sub:
            homes.setdefault(sub["name"], []).append(sub)
    kept = []
    for profile in node.get("profiles", []):
        found = homes.get(GEAR_ABILITY_HOME.get(profile["name"], profile["name"]))
        if profile.get("typeName") == "Abilities" and not profile.get("hidden") and found:
            for i, home in enumerate(found):  # every copy of the item (e.g. each Clanrat's shield) shows it
                home.setdefault("profiles", []).append(
                    profile if i == 0 else dict(profile, id=nid(home["id"] + ":ability:" + profile["name"])))
        else:
            kept.append(profile)
    node["profiles"] = kept


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
        if name == "Clan Skurvy":
            tags.append("Clan Skurvy Detachment")  # the game system shows Black-Flag Allies only with this tag
        det["categoryLinks"] = [b.category_link(det["id"], t) for t in tags]
        for heading, lines in merge_continued(sections(text)):
            if heading is None:
                continue
            option = OPTION_SECTIONS.get(heading)
            if "Stratagems" in heading:
                for card in cards(lines):
                    stratagems.append((det, card))
            elif "Enhancements" in heading:
                for card in cards(lines):
                    enhancements.append((det, card))
            elif option:
                for card in cards(lines):
                    card["cost"], card["kind"] = 1, option
                    projects.append((det, card))
                add_detachment_rules(det, heading, lines)
            else:
                add_detachment_rules(det, heading, lines)
        # Detachments do not link the army rules; those live in Army Rules and References.
        group["selectionEntries"].append(det)

    # Only one Unique: CLAN detachment per army.
    clan = [d for d in group["selectionEntries"] if d["name"] in CLAN_UNIQUE]
    clan_category = b.categories["unique: clan"]
    clan_category["constraints"] = [constraint(nid(clan_category["id"] + ":max"), "max", 1, scope="roster",
                                               child=True)]  # as the game system's Unique: ORDO
    for det in clan:
        others = [selected(o["id"], scope="roster") for o in clan if o is not det]
        det["modifiers"] = [dict(type="set", field=det["constraints"][0]["id"], value=0,
                                 conditionGroups=[dict(type="or", conditions=others)])]
    dets = {d["name"]: d for d in group["selectionEntries"]}
    battleline_id = b.category("Battleline")[0]
    for det_name, keywords in BATTLELINE_GRANTS.items():
        for unit in units:
            if not set(keywords) & set(b.data[unit["name"]]["keywords"]):
                continue
            copies = next(c for c in unit["constraints"] if c["id"] == nid(unit["id"] + ":copies"))
            granted = [selected(dets[det_name]["id"], scope="roster")]
            for sub in walk(unit):  # +1 OC on every model's stat line
                for profile in sub.get("profiles", []) if isinstance(sub, dict) else []:
                    if profile.get("typeName") == "Unit":
                        oc = next(c for c in profile["characteristics"] if c["name"].upper() == "OC")
                        profile.setdefault("modifiers", []).append(dict(
                            field=oc["typeId"], type="increment", value=1, conditions=granted))
            unit.setdefault("modifiers", []).extend([
                dict(type="add", field="category", value=battleline_id, conditions=granted),
                dict(type="set-primary", field="category", value=battleline_id, conditions=granted),
                dict(type="set", field=copies["id"], value=max(copies["value"], 6),
                     conditions=[selected(dets[det_name]["id"], scope="roster")])])
    return detachment_entry, enhancements, stratagems, projects, dets


# Sections whose sub-headings are menu options or procedure steps stay as one rule.
WHOLE_SECTIONS = {"Secret Schemes", "The Hidden Ledger", "The Plague Catalogue", "Warlord Commands", "The Plunder Ledger",
                  "Workshop Projects", "Mutations", "Ruinous Defects", "Council Seats"}
ARMY_RULE_PATTERNS = OrderedDict([
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
        spaced, seen = [], False  # a blank line between ledger entries, so they do not run together
        for line in lines:
            if line.startswith("### "):
                if seen:
                    spaced += ["<br>", ""]
                seen = True
            spaced.append(line)
        det["rules"].append(dict(name=name, id=nid(det["id"] + ":rule:" + name), hidden=False,
                                 description="\n\n" + clean_markdown(spaced)))
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
        b.enh_ids[card["name"]] = eid
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


PROJECT_TOKENS = "95a1-fc42-7bd0-9091"  # the "Workshop Projects" cost type (formerly Workshop Tokens)
CHAR_KEYS = {"M": "M", "T": "T", "SV": "SV", "W": "W", "OC": "OC", "A": "A", "WS": "WS", "S": "S", "INSV": "INV", "INV": "INV"}


def add_number(text, n, floor=None):
    """'7"' + 2 -> '9"'; '2D6+1"' + 2 -> '2D6+3"'; 'D6' + 1 -> 'D6+1'."""
    m = re.match(r'^(.*?)(\d+)?(")?$', text)
    head, num, inch = m.group(1), m.group(2), m.group(3) or ""
    if num is None:
        return text if n < 0 else f"{text}+{n}"
    if head.endswith("+") or head.endswith("-"):
        value = int(num) * (1 if head.endswith("+") else -1) + n
        head = head[:-1]
        return f"{head}{'+' if value >= 0 else '-'}{abs(value)}{inch}" if value else f"{head}{inch}"
    value = int(num) + n
    if floor is not None:
        value = max(floor, value)
    return f"{head}{value}{inch}"


def add_roll(text, n, best=3):
    """'4+' improved by 1 -> '3+' (never better than best); worsened -> '5+'."""
    m = re.match(r"^(\d)\+$", text.strip())
    if not m:
        return text
    value = int(m.group(1)) - n
    if n > 0:
        value = max(best, value) if int(m.group(1)) > best else int(m.group(1))
    return f"{value}+"


# Mutation / Ruinous Defect -> (profile kind, characteristic, change)
MUTATION_EFFECTS = {
    "Thickened Hide": ("Unit", "T", 1), "Soft Flesh": ("Unit", "T", -1),
    "Chitinous Plates": ("Unit", "SV", 1), "Exposed Organs": ("Unit", "SV", -1),
    "Too Many Limbs": ("Melee Weapons", "A", 1), "Missing Limbs": ("Melee Weapons", "A", -1),
    "Overgrown Musculature": ("Melee Weapons", "S", 1), "Atrophied Musculature": ("Melee Weapons", "S", -1),
    "Lengthened Legs": ("Unit", "M", 2), "Stunted Legs": ("Unit", "M", -2),
    "Predatory Reflexes": ("Melee Weapons", "WS", 1),
    "Uncontrollable": ("Unit", "OC", -1),
    "Bloated Mass": ("Unit", "W", 2), "Withered Frame": ("Unit", "W", -2),
}
DEFECT_PAIRS = {"Soft Flesh": "Thickened Hide", "Exposed Organs": "Chitinous Plates", "Missing Limbs": "Too Many Limbs",
                "Atrophied Musculature": "Overgrown Musculature", "Stunted Legs": "Lengthened Legs",
                "Withered Frame": "Bloated Mass"}


def changed_value(char, value, change):
    if char in ("SV", "WS"):
        return add_roll(value, change, best=3)
    if char == "LD":
        return add_roll(value, change, best=4)
    floor = 1 if char in ("A", "OC", "T", "W") else None
    return add_number(value, change, floor)


def stat_modifiers(unit, entry_id, effects):
    """Show an option's stat changes on the unit's stat lines, as Keeper of Secrets in the Emperor's Children
    catalogue. Numbers are incremented so several bonuses add up; Move, saves and skills are set."""
    condition = [selected(entry_id, scope=unit["id"])]
    for kind, char, change, *best in effects:
        for sub in walk(unit):
            for profile in sub.get("profiles", []) if isinstance(sub, dict) else []:
                if profile.get("typeName") != kind:
                    continue
                for c in profile["characteristics"]:
                    text = c.get("$text", "-")
                    if char == "Keywords" and c["name"] == "Keywords":
                        if change.upper() not in text.upper():  # appended, so several keywords add up
                            kind_ = "set" if text in ("-", "") else "append"
                            profile.setdefault("modifiers", []).append(dict(
                                field=c["typeId"], type=kind_, value=change if kind_ == "set" else ", " + change,
                                conditions=condition))
                        continue
                    if char == "AP" and c["name"] == "AP":
                        value = int(text.replace("\u2212", "-")) if re.match(r"^[-\u2212]?\d+$", text) else None
                        if value is not None:
                            profile.setdefault("modifiers", []).append(dict(
                                field=c["typeId"], type="set", value=str(value + change), conditions=condition))
                        continue
                    if CHAR_KEYS.get(c["name"].upper(), c["name"].upper()) != char or text in ("-", "", "N/A"):
                        continue
                    if char == "A" and "EXTRA ATTACKS" in profile["characteristics"][-1].get("$text", "").upper():
                        continue
                    if text.isdigit():
                        if int(text) + change >= 1:
                            profile.setdefault("modifiers", []).append(dict(
                                field=c["typeId"], type="increment", value=change, conditions=condition))
                        continue
                    if profile["name"].startswith(("Gnaw-beast", "Screaming Bell", "Plague Furnace")):
                        continue  # a mount's weapons are not the bearer's
                    if char == "INV":
                        new = add_roll(text, change, best=4)
                    elif best:
                        new = add_roll(text, change, best=best[0])
                    else:
                        new = changed_value(char, text, change)
                    if new != text:
                        profile.setdefault("modifiers", []).append(dict(
                            field=c["typeId"], type="set", value=new, conditions=condition))


def mutation_modifiers(unit, mutation_id, name):
    stat_modifiers(unit, mutation_id, [MUTATION_EFFECTS[name]])


# Enhancements, Upgrades and Workshop Projects whose effect is a plain stat change.
STAT_EFFECTS = {
    "Scrap-Welded Armour": [("Unit", "M", -1)],
    "Warpstone Supercharger": [("Ranged Weapons", "S", 2)],
    "Voltaic Shield Amplifiers": [("Unit", "INV", 1)],
    "Reinforced-Ramshackle Hull": [("Unit", "T", 1), ("Unit", "M", -1)],
    "Best-Best Killer": [("Melee Weapons", "WS", 1, 2)],
    "Black-Flag Rigging Upgrade": [("Unit", "M", 2)],
    "Warp-Fed Gearbox": [("Unit", "M", 2)],
    "Overgrown": [("Unit", "T", 1)],
    "Shadow Blade": [("Melee Weapons", "AP", -1), ("Melee Weapons", "Keywords", "Precision")],
    "Weeping Blades": [("Melee Weapons", "Keywords", "Lethal Hits")],
}
# Upgrades that give the unit a keyword.
CATEGORY_EFFECTS = {"Black-Fur Boarders Upgrade": "Skurvy", "Prize Gunnery Crews Upgrade": "Skurvy",
                    "Black-Flag Rigging Upgrade": "Skurvy"}


def one_per_unit(b, units, shared_enh):
    """Each option once per unit, shown as a checkbox; a unit has at most one Enhancement or Upgrade, and so does
    an Attached Unit (Leader and Bodyguard together), as the official catalogues check it."""
    for e in shared_enh:  # a hidden cost that is never zeroed, unlike the shared Upgrade slot
        e["costs"].append(dict(name="Enhancement or Upgrade", typeId=ENH_COUNT, value=1))
    for unit in units:
        unit.setdefault("constraints", []).append(dict(
            id=nid(unit["id"] + ":attached-enhancement"), childId="any", field=ENH_COUNT, type="max", value=1,
            scope="root-entry", shared=True, includeChildSelections=True, includeChildForces=False,
            traverseAssociationGroup=True, message="An Attached Unit can only take 1 Enhancement or Upgrade."))
        for g in unit.get("selectionEntryGroups", []):
            if g["name"] in ("Enhancements and Upgrades", "Council Levy"):
                for link in g["entryLinks"]:
                    link["constraints"] = [constraint(nid(link["id"] + ":once"), "max", 1)]


def apply_stat_effects(b, units):
    ids = dict(b.enh_ids, **b.option_ids)
    for name, effects in STAT_EFFECTS.items():
        eid = ids.get(name)
        assert eid, name
        for unit in units:
            if any(isinstance(n, dict) and n.get("targetId") == eid for n in walk(unit)):
                stat_modifiers(unit, eid, effects)
    for name, keyword in CATEGORY_EFFECTS.items():
        eid = b.enh_ids[name]
        cat_id = b.category(keyword)[0]
        for unit in units:
            if any(isinstance(n, dict) and n.get("targetId") == eid for n in walk(unit)):
                unit.setdefault("modifiers", []).append(dict(type="add", field="category", value=cat_id,
                                                             conditions=[selected(eid, scope=unit["id"])]))


def option_group(unit, key, name, limit):
    groups = unit.setdefault("selectionEntryGroups", [])
    g = next((x for x in groups if x["name"] == name), None)
    if not g:
        gid = nid(unit["id"] + ":" + key)
        g = dict(name=name, id=gid, hidden=False, entryLinks=[], constraints=[constraint(nid(gid + ":max"), "max", limit)])
        groups.append(g)
    return g


def build_options(b, options, units, dets):
    """Workshop Projects, Mutations, Ruinous Defects and Council Seats as capped options on eligible units."""
    shared, ids = [], {}
    for det, card in options:
        restriction = card["italics"][0] if card["italics"] else ""
        eid = b.old_ids.get(norm(card["name"])) or nid(card["kind"] + ":" + card["name"])
        ids[card["name"]] = eid
        b.option_ids[card["name"]] = eid
        body = clean_markdown(card["body"])
        costs, roster_max = [], None
        if card["kind"] == "project":
            costs, roster_max = [dict(name="Workshop Projects", typeId=PROJECT_TOKENS, value=1)], 3
        elif card["kind"] == "mutation":
            costs = [dict(name="Flesh-Sculpting", typeId=FLESH_SCULPTING, value=1)]
        elif card["kind"] == "defect":
            costs = []  # each Defect taken raises the Mutation cap by 1 (see below)
        elif card["kind"] == "seat":
            roster_max = 1
        label = {"project": "", "mutation": "Mutation: ", "defect": "Ruinous Defect: ", "seat": ""}[card["kind"]]
        e = entry(eid, label + card["name"], costs=costs,
                  rules=[dict(name=card["name"], id=nid(eid + ":rule"), hidden=False,
                              description=(f"*{restriction}*\n\n" if restriction and card["kind"] == "project" else "")
                              + body)])
        if roster_max:
            e["constraints"] = [constraint(nid(eid + ":max"), "max", roster_max, scope="roster", child=True)]
        shared.append(e)
        hits = 0
        for unit in units:
            ds = b.data[unit["name"]]
            kws = set(ds["keywords"])
            if card["kind"] == "project":
                character = "CHARACTER" in restriction
                if character and "CHARACTER" not in kws:
                    continue
                ok = eligible(ds, restriction, character) or (
                    "WEAPON TEAM" in restriction and "STORMFIENDS" in kws)  # Stormfiends take Weapon Team Projects
                if not ok:
                    continue
                g = option_group(unit, "projects", "Workshop Projects", 1)
                g["entryLinks"].append(gated(g["id"], eid, card["name"], det["id"]))
            elif card["kind"] in ("mutation", "defect"):
                if "MOULDER" not in kws or not kws & {"BEAST", "MONSTER"} or "CHARACTER" in kws:
                    continue
                if "MONSTER unit only" in restriction and "MONSTER" not in kws:
                    continue
                title_ = "Mutations" if card["kind"] == "mutation" else "Ruinous Defect"
                g = option_group(unit, card["kind"] + "s", "Flesh-Sculpting: " + title_, 1)
                link = gated(g["id"], eid, e["name"], det["id"])
                pair = DEFECT_PAIRS.get(card["name"])
                if pair:  # a Defect cannot undo its own Mutation
                    link["modifiers"].append(dict(field="hidden", value=True, type="set",
                                                  conditions=[selected(ids[pair], scope=unit["id"])]))
                g["entryLinks"].append(link)
                mutation_modifiers(unit, eid, card["name"])
            elif card["kind"] == "seat":
                if "CHARACTER" not in kws:
                    continue
                clan = card["name"].replace(" Seat", "").upper()
                g = option_group(unit, "seat", "Council Seat", 1)
                link = gated(g["id"], eid, card["name"], det["id"])
                if clan not in kws:  # Lord of Decay: any Seat
                    link["modifiers"][0]["conditions"].append(selected(b.enh_ids["Lord of Decay"], scope=unit["id"]))
                    link["modifiers"][0] = dict(link["modifiers"][0], conditionGroups=[dict(
                        type="and", conditions=link["modifiers"][0].pop("conditions"))])
                g["entryLinks"].append(link)
            hits += 1
        if not hits:
            b.log.append(f"No eligible unit for {card['kind']} {card['name']} ({restriction})")

    # Caps: Workshop Projects and Mutations on 3 / 6 / 9 units; a Defect buys a second Mutation.
    for det_name, cost_id, limits in (("Skryre Worship", PROJECT_TOKENS, (3, 6, 9)),
                                       ("Moulder Flesh Laboratory", FLESH_SCULPTING, (3, 6, 9))):
        det = dets[det_name]
        cap = constraint(nid(det["id"] + ":cap"), "max", limits[1], scope="roster", field=cost_id, child=True,
                         forces=True)
        det["constraints"].append(cap)
        det.setdefault("modifiers", []).extend([
            dict(type="set", field=cap["id"], value=limits[0], conditions=[selected(INCURSION, scope="roster")]),
            dict(type="set", field=cap["id"], value=limits[2], conditions=[selected(ONSLAUGHT, scope="roster")])])
        if det_name == "Moulder Flesh Laboratory":
            for e in shared:
                if e["name"].startswith("Ruinous Defect: "):
                    det["modifiers"].append(dict(type="increment", field=cap["id"], value=1, repeats=[dict(
                        childId=e["id"], field="selections", scope="roster", value=1, repeats=1, shared=True,
                        includeChildSelections=True, roundUp=False)]))
        if det_name == "Skryre Worship" and "Chief-Chief Engineer" in b.enh_ids:
            det["modifiers"].append(dict(type="increment", field=cap["id"], value=2, conditions=[
                selected(b.enh_ids["Chief-Chief Engineer"], scope="roster")]))
    for unit in units:
        for g in unit.get("selectionEntryGroups", []):
            if g["name"] in ("Flesh-Sculpting: Mutations", "Workshop Projects", "Council Seat"):
                for link in g["entryLinks"]:  # each option once per unit, shown as a checkbox
                    link["constraints"] = [constraint(nid(link["id"] + ":once"), "max", 1)]
            if g["name"] == "Flesh-Sculpting: Mutations":
                defects = next((x for x in unit["selectionEntryGroups"] if x["name"] == "Flesh-Sculpting: Ruinous Defect"), None)
                if defects:
                    g["modifiers"] = [dict(type="increment", field=g["constraints"][0]["id"], value=1, conditions=[
                        dict(childId=defects["id"], field="selections", scope=unit["id"], type="atLeast", value=1,
                             shared=True, includeChildSelections=True)])]
            elif g["name"] == "Workshop Projects" and "Chief-Chief Engineer" in b.enh_ids:
                g["modifiers"] = [dict(type="set", field=g["constraints"][0]["id"], value=2, conditions=[
                    selected(b.enh_ids["Chief-Chief Engineer"], scope="roster")])]
            elif g["name"] == "Council Seat" and "Lord of Decay" in b.enh_ids:
                g["modifiers"] = [dict(type="set", field=g["constraints"][0]["id"], value=2, conditions=[
                    selected(b.enh_ids["Lord of Decay"], scope=unit["id"])])]
    return shared


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


# ---------------------------------------------------------------- attachments
def add_associations(b, units):
    """New Recruit Leader/Support links, as in the Emperor's Children catalogue."""
    by_name = {u["name"]: u for u in units}
    skryre_teams = [n for n, d in b.data.items() if {"SKRYRE", "WEAPON TEAM"} <= set(d["keywords"])]
    for unit in units:
        text = " ".join(b.data[unit["name"]]["unit_composition"])
        for label, pattern in (("Leader", r"[Cc]an lead (.+?)(?: only while [^.]+)?\."),
                               ("Support", r"attached as a Support to (.+?)(?: only while [^.]+)?\.")):
            m = re.search(pattern, text)
            if not m:
                continue
            targets = []
            for part in re.split(r",\s*|\s+or\s+", m.group(1)):
                part = part.strip()
                if part.lower() == "a skryre weapon team":
                    targets += skryre_teams
                elif part:
                    targets.append(part)
            missing = [t for t in targets if t not in by_name]
            assert not missing, (unit["name"], missing)
            conditions = [dict(childId=by_name[t]["id"], field="selections", scope="self", type="instanceOf", value=1,
                               shared=True, includeChildSelections=True) for t in dict.fromkeys(targets)]
            mounted_only_free = "only while" in m.group(0)
            unit["associations"] = [dict(
                name="Leading" if label == "Leader" else "Supporting", id=nid(unit["id"] + ":" + label),
                action="group", childId="unit", childName="unit", includeChildSelections=True, label=label, max=1,
                min=0 if label == "Leader" or mounted_only_free else 1, scope="force",
                conditionGroups=[dict(type="or", conditions=conditions)])]
            if label == "Support":
                unit["associations"][0]["defaultSelectionEntryId"] = "none"


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
    add_associations(b, units)
    detachment_entry, enhancements, stratagems, projects, dets = build_detachments(b, units)
    shared_enh = build_enhancements(b, enhancements, units)
    shared_projects = build_options(b, projects, units, dets)
    apply_stat_effects(b, units)
    for unit, item_id, effects in getattr(b, "gear_stats", []):
        stat_modifiers(unit, item_id, effects)
    one_per_unit(b, units, shared_enh)
    strat_links = build_stratagems(b, stratagems)

    # Warlord: any CHARACTER can be chosen, as in the Emperor's Children catalogue; the game system requires one.
    warlord_role = next(c for c in b.system["categoryEntries"] if c["name"] == "Warlord")
    warlord_id = nid("warlord-selection")
    warlord = entry(warlord_id, "Warlord", categoryLinks=[dict(name="Warlord", id=nid(warlord_id + ":cat"),
                                                               targetId=warlord_role["id"], primary=False,
                                                               hidden=False)],
                    constraints=[constraint(nid(warlord_id + ":max"), "max", 1, scope="roster", child=True)])
    for unit in units:
        if "CHARACTER" in b.data[unit["name"]]["keywords"]:
            unit.setdefault("entryLinks", []).append(dict(name="Warlord", id=nid(unit["id"] + ":warlord"),
                                                          targetId=warlord_id, type="selectionEntry", hidden=False,
                                                          **{"import": True}))

    # Detachment rules that give every Clanrats unit a keyword and an ability (as Clan Skurvy's Black-Flag
    # Clanrats): shown on the Clanrats card while the detachment is taken.
    clanrats = next(u for u in units if u["name"] == "Clanrats")

    def clanrats_gain(det_name, keyword, label, core=()):
        det = dets[det_name]
        in_det = selected(det["id"])
        clanrats["modifiers"].append(dict(type="add", field="category", value=b.category(keyword)[0],
                                          conditions=[in_det]))
        text = next(re.search(r"\*\*" + re.escape(label) + r":\*\*\s*(.+)", r["description"]).group(1)
                    for r in det["rules"] if label + ":" in r["description"])
        ability = b.ability_profile(nid(clanrats["id"] + ":" + label), label, text.strip(), hidden=True)
        ability["modifiers"] = [dict(type="set", field="hidden", value=False, conditions=[in_det])]
        clanrats["profiles"].insert(len([x for x in clanrats["profiles"] if not x.get("hidden")]), ability)
        for name in core:
            rule = next(r for r in b.sys_rules if r["name"] == name)
            clanrats.setdefault("infoLinks", []).append(dict(
                id=nid(clanrats["id"] + ":" + label + ":" + name), name=name, targetId=rule["id"], type="rule",
                hidden=True, modifiers=[dict(type="set", field="hidden", value=False, conditions=[in_det])]))

    clanrats_gain("Shadowy Dealings", "Eshin", "Paid Informants", ('Scouts 6"', "Stealth"))
    clanrats_gain("Cauldron of Pestilence", "Pestilens", "Plague Carrier")
    clanrats_gain("Skryre Worship", "Skryre", "Overstuffed Power Cells")
    clanrats_gain("Moulder Flesh Laboratory", "Moulder", "Pack-Driven")

    # Black-Flag Clanrats (Clan Skurvy): every Clanrats unit gains SKURVY and Claim-Claim the Prize!.
    skurvy_det = next(d for d in detachment_entry["selectionEntryGroups"][0]["selectionEntries"]
                      if d["name"] == "Clan Skurvy")
    skurvy_id, _ = b.category("Skurvy")
    assert skurvy_id == KEPT_CATEGORY_IDS["Skurvy"], skurvy_id
    in_skurvy = selected(skurvy_det["id"])
    clanrats["modifiers"].append(dict(type="add", field="category", value=skurvy_id, conditions=[in_skurvy]))
    claim_text = next(re.search(r"\*\*Claim-Claim the Prize!:\*\*\s*(.+)", r["description"]).group(1)
                      for r in skurvy_det["rules"] if "Claim-Claim the Prize!" in r["description"])
    claim = b.ability_profile(nid(clanrats["id"] + ":claim"), "Claim-Claim the Prize!", claim_text.strip(), hidden=True)
    claim["modifiers"] = [dict(type="set", field="hidden", value=False, conditions=[in_skurvy])]
    clanrats["profiles"].insert(len([p for p in clanrats["profiles"] if not p.get("hidden")]), claim)

    # Clanrats loadout: every model uses the same one (Sword and Board with one weapon, or Warplock).
    tags = {}
    for n in walk(clanrats):
        if not isinstance(n, dict) or n.get("type") not in ("model", "upgrade") or not n.get("name"):
            continue
        gear = " ".join(x["name"] for x in n.get("selectionEntries", []) if isinstance(x, dict)) + " " + n["name"]
        if n.get("type") == "upgrade" and n["name"].startswith(("Clawleader blade and", "Warplock carbine and Clawleader")):
            tag = "Clawleader: Warplock" if "Warplock" in n["name"] else "Clawleader: Sword and Board"
        elif n.get("type") == "model" and n["name"].startswith("Clanrat"):
            tag = ("Warplock" if "Warplock carbine" in gear else "mace" if "Clanrat mace" in gear
                   else "spear" if "Clanrat spear" in gear else "blade")
        else:
            continue
        cid = tags.setdefault(tag, b.hidden_category(f"Count: Clanrats loadout - {tag}"))
        n.setdefault("categoryLinks", []).append(dict(name="count", id=nid(n["id"] + ":loadout"), targetId=cid,
                                                      primary=False, hidden=False))
    for n in walk(clanrats):
        if isinstance(n, dict) and n.get("type") == "upgrade" and n.get("name", "").startswith(
                ("Clawleader blade and", "Warplock carbine and Clawleader")):
            n["name"] = ("Warplock: " if n["name"].startswith("Warplock") else "Sword and Board: ") + \
                n["name"].replace(" and ", ", ")
    clash = [("blade", "mace"), ("blade", "spear"), ("mace", "spear"), ("blade", "Warplock"), ("mace", "Warplock"),
             ("spear", "Warplock"), ("Clawleader: Sword and Board", "Warplock"), ("Clawleader: Warplock", "blade"),
             ("Clawleader: Warplock", "mace"), ("Clawleader: Warplock", "spear")]
    clanrats["modifiers"].append(dict(type="add", field="error", value="Every model in this unit must use the same "
                                      "loadout: Sword and Board with the same weapon, or Warplock.",
                                      conditionGroups=[dict(type="or", conditionGroups=[
                                          dict(type="and", conditions=[selected(tags[x], scope=clanrats["id"]),
                                                                       selected(tags[y], scope=clanrats["id"])])
                                          for x, y in clash])]))

    # Council Levies (Council of Treachery): each Clanrats unit can swear to one Clan.
    council = dets["Council of Treachery"]
    levies = []
    gid = nid(clanrats["id"] + ":levy")
    levy_group = dict(name="Council Levy", id=gid, hidden=False, entryLinks=[],
                      constraints=[constraint(nid(gid + ":max"), "max", 1)])
    for clan in COUNCIL_CLANS:
        lid = nid("council-levy:" + clan)
        clan_id, clan_name = b.category(title(clan))
        levies.append(entry(lid, f"Council Levy: {title(clan)}", rules=[dict(
            name="Council Levies", id=nid(lid + ":rule"), hidden=False,
            description=f"This unit is sworn to the {clan} Seat. It gains the {clan} keyword, and has that Seat's "
                        "benefit while that Seat is held.")]))
        levy_group["entryLinks"].append(gated(gid, lid, levies[-1]["name"], council["id"]))
        clanrats["modifiers"].append(dict(type="add", field="category", value=clan_id,
                                          conditions=[selected(lid, scope=clanrats["id"])]))
    clanrats["selectionEntryGroups"].append(levy_group)

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
    old = b.old
    keep_links = [l for l in old["entryLinks"]
                  if l["targetId"] not in {e["id"] for e in old["sharedSelectionEntries"]}]  # Black-Flag units

    shared_entries = [detachment_entry, army_ref, strat_ref, officers, warlord] + levies + units + shared_enh + \
        shared_projects
    root_links = []
    for e in [detachment_entry, army_ref, strat_ref, officers] + units:
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
    new["costTypes"] = copy.deepcopy(old.get("costTypes", []))
    for ct in new["costTypes"]:
        if ct["id"] == PROJECT_TOKENS:
            ct["name"] = "Workshop Projects"
            ct["modifiers"] = [dict(field="hidden", type="set", value=False,
                                    conditions=[selected(dets["Skryre Worship"]["id"], scope="roster")])]
    if not any(ct["id"] == ENH_COUNT for ct in new["costTypes"]):
        new["costTypes"].append(dict(name="Enhancement or Upgrade", id=ENH_COUNT, defaultCostLimit=-1, hidden=True))
    if not any(ct["id"] == FLESH_SCULPTING for ct in new["costTypes"]):
        new["costTypes"].append(dict(name="Flesh-Sculpting", id=FLESH_SCULPTING, defaultCostLimit=-1, hidden=True))
    for ct in new["costTypes"]:
        if ct["id"] == FLESH_SCULPTING:
            ct["modifiers"] = [dict(field="hidden", type="set", value=False,
                                    conditions=[selected(dets["Moulder Flesh Laboratory"]["id"], scope="roster")])]
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
