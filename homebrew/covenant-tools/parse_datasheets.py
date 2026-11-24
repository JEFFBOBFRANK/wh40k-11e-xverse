"""pages.json -> datasheets draft: python3 parse_datasheets.py pages.json out.json"""
import json, re, sys
P = json.load(open(sys.argv[1]))
SECTIONS = ["UNIT COMPOSITION", "EACH MODEL IS EQUIPPED WITH", "SERGEANT", "AUXILIARY", "WARGEAR OPTIONS", "WARGEAR",
            "RANGED WEAPONS", "MELEE WEAPONS", "ABILITIES", "LEADER", "TRANSPORT", "RULES NOTES"]
CAT = {"EPIC HEROES": "EPIC HERO", "CHARACTERS": "CHARACTER", "BATTLELINE": "BATTLELINE", "INFANTRY": "INFANTRY",
       "MOUNTED": "MOUNTED", "MONSTERS": "MONSTER", "VEHICLES": "VEHICLE", "FORTIFICATIONS": "FORTIFICATION",
       "SERGEANT ENTRIES": "SERGEANT", "AUXILIARY ENTRIES": "AUXILIARY"}


def clean(t):
    t = t.replace("Rang e", "Range").replace("Mele e", "Melee").replace("•", "").strip()
    return re.sub(r"\s+", " ", t)


def weapons(rows):
    head = [clean(h) for h in rows[0]]
    out = []
    for r in rows[1:]:
        r = [clean(c) for c in r]
        d = dict(zip(head, r))
        out.append(dict(name=d.get("Weapon", ""), range=d.get("Range", ""), A=d.get("A", ""),
                        BS_WS=d.get("BS", d.get("WS", "")), S=d.get("S", ""), AP=d.get("AP", ""), D=d.get("D", ""),
                        keywords=[] if d.get("Abilities", "-") in ("-", "") else
                        [k.strip() for k in re.split(r",\s*(?![^()]*\))", d.get("Abilities", ""))]))
    return out, ("WS" in head)


sheets, order = {}, []
for p in P:
    if p["page"] == 131:  # two compact entries, written by hand
        continue
    head = p["head"]
    name = re.sub(r"\s*•\s*(PAGE|CONTINUED).*$", "", next(l["text"] for l in head if l["size"] > 20)).strip()
    if name not in sheets:
        cat = head[0]["text"]
        pts = next((l["text"] for l in head if re.fullmatch(r"[\d,]+pts", l["text"])), "")
        sub = next((l["text"] for l in head if l["size"] < 11 and l["text"] not in (cat,) and "FACTION" not in l["text"]), "")
        sub = sub.replace("FACTION: COVENANT", "").strip()
        hdr = next(l["text"] for l in head if l["text"].startswith("M "))
        vals = head[[l["text"] for l in head].index(hdr) + 1]["text"]
        keys, vs = hdr.split(), vals.split()
        sheets[name] = dict(name=name, category=CAT.get(cat, cat), subtitle=sub, points=pts,
                            profile=dict(zip(keys, vs)), pages=[], sections={}, ranged_weapons=[], melee_weapons=[],
                            keywords=[], issues=[])
        if len(keys) != len(vs):
            sheets[name]["issues"].append(f"profile {keys} vs {vs}")
        order.append(name)
    s = sheets[name]
    s["pages"].append(p["page"])
    for t in p["tables"]:
        ws, melee = weapons(t["rows"])
        (s["melee_weapons"] if melee else s["ranged_weapons"]).extend(ws)
    cur = s["sections"].get("_last")
    for col in ("left", "right"):
        for l in p[col]:
            txt = l["text"].replace("•", "").strip()
            if l["bold"] and txt in SECTIONS:
                cur = txt
                s["sections"].setdefault(cur, [])
                continue
            if cur is None:
                s["issues"].append("orphan: " + l["text"]); continue
            s["sections"][cur].append(dict(bullet=l["text"].startswith("•"), x=l["x"], top=l["top"], marked=l["marked"].replace("•", "").strip()))
    s["sections"]["_last"] = cur
    for l in p["foot"]:
        if l["text"].startswith("KEYWORDS:"):
            kw = re.sub(r"\s+\d+$", "", l["text"][len("KEYWORDS:"):]).strip()
            s["keywords"] = [k.strip() for k in kw.split(",")]


def items(lines):
    """Join wrapped lines into bullet items."""
    out = []
    for l in lines:
        if l["bullet"] or not out:
            out.append(l["marked"])
        else:
            out[-1] += " " + l["marked"]
    return [clean(re.sub(r"\*\*", "", o)) for o in out]


ART = re.compile(r"^(Covenant Army|Sanghelios Ruins|High Charity|Reach Landscape|Unyielding Hierophant|Glassing of Reach|The Ark)\b.*-")


NAME = re.compile(r"^((?:[A-Z0-9][\w'’\-]*|of|the|and|to|in|on|a|an|for|from|with|by)"
                  r"(?: (?:[A-Z0-9][\w'’\-]*|of|the|and|to|in|on|a|an|for|from|with|by|-)){0,7})[.:] (.*)$")


def abilities(lines):
    """Paragraphs are separated by a larger line gap; each starts 'Name. text' (the name is bold on most pages)."""
    paras, prev = [], None
    for l in lines:
        starts_bold = l["marked"].startswith("**")
        gap = prev is None or l["top"] - prev > 16 or (l["top"] < prev and (starts_bold or NAME.match(l["marked"])))
        if gap or not paras:
            paras.append([l["marked"]])
        else:
            paras[-1].append(l["marked"])
        prev = l["top"]
    out = []
    for p in paras:
        text = " ".join(p)
        # a bold name can also start mid-paragraph (two abilities run together)
        chunks = re.split(r"\s(?=\*\*[^*]+?[.:]\*\*)", text)
        for c in chunks:
            m = re.match(r"^\*\*([^*]+?)[.:]\*\*\s*(.*)$", c)
            if m:
                name, body = m.group(1), m.group(2)
            else:
                plain = clean(c.replace("**", ""))
                m = NAME.match(plain)
                name, body = (m.group(1), m.group(2)) if m else ("", plain)
            name, body = clean(name.replace("**", "")), clean(body.replace("**", ""))
            if ART.match(name + " -") or ART.match(name) or (not name and " - " in body and len(body) < 90):
                continue
            out.append(dict(name=name, text=body))
    return out


result = []
for name in order:
    s = sheets[name]
    sec = s.pop("sections"); sec.pop("_last", None)
    for k in ("UNIT COMPOSITION", "EACH MODEL IS EQUIPPED WITH", "SERGEANT", "AUXILIARY", "WARGEAR OPTIONS", "LEADER",
              "TRANSPORT", "RULES NOTES"):
        s[k.lower().replace(" ", "_")] = items(sec.get(k, []))
    s["wargear"] = abilities(sec.get("WARGEAR", []))
    s["abilities"] = abilities(sec.get("ABILITIES", []))
    for k in ("RANGED WEAPONS", "MELEE WEAPONS"):
        if sec.get(k):
            s["issues"].append(f"text under {k}: " + " | ".join(l["marked"] for l in sec[k])[:200])
    result.append(s)
json.dump(result, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
print(len(result), "datasheets;", sum(1 for s in result if s["issues"]), "with issues")
