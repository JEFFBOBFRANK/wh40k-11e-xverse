"""draft.json + detachments.json -> homebrew/covenant-source/{datasheets,detachments}.json"""
import json, re, sys
out_dir = sys.argv[1]
D = json.load(open("draft.json"))


def num(t):
    t = re.sub(r"\s+", "", t)
    return t


ds = []
for s in D:
    rec = dict(name=s["name"], category=s["category"], subtitle=s["subtitle"],
               points=int(s["points"].replace("pts", "").replace(",", "")),
               profile={k.upper(): v for k, v in s["profile"].items()}, page=s["pages"][0],
               unit_composition=s["unit_composition"], equipped=s["each_model_is_equipped_with"],
               sergeant=s["sergeant"], auxiliary=s["auxiliary"], wargear_options=s["wargear_options"],
               leader=s["leader"], transport=s["transport"], rules_notes=s["rules_notes"], wargear=s["wargear"],
               ranged_weapons=[], melee_weapons=[], abilities=s["abilities"], keywords=s["keywords"])
    for kind in ("ranged_weapons", "melee_weapons"):
        for w in s[kind]:
            if not w["A"] or " - " in w["name"] and not re.search(r" - (strike|sweep|N'tho|Usze)$", w["name"]):
                continue
            rec[kind].append(dict(name=w["name"], range=w["range"].replace("inches", '"'), A=num(w["A"]),
                                  BS_WS=w["BS_WS"], S=w["S"], AP=w["AP"], D=num(w["D"]), keywords=w["keywords"]))
    ds.append(rec)

manual = [
    dict(name="Unggoy Suicide Bomber", category="AUXILIARY", subtitle="Disposable Auxiliary", points=20,
         profile=dict(M='8"', T="3", SV="7+", W="1", LD="8+", OC="0"), page=131,
         unit_composition=["1 Unggoy Suicide Bomber"], equipped=["Unstable Plasma Charges"], sergeant=[], auxiliary=[],
         wargear_options=[], leader=[], transport=[], rules_notes=[], wargear=[], ranged_weapons=[],
         melee_weapons=[dict(name="Unstable Plasma Charges", range="Melee", A="1", BS_WS="5+", S="3", AP="0", D="1",
                             keywords=["Plasma (D1)"])],
         abilities=[dict(name="Proximity Detonation",
                         text="Each time this model ends a move within 3 inches of an enemy unit, or an enemy model "
                              "ends a move within 3 inches of it, this model detonates. Roll one D6; on a 3+, select "
                              "one such enemy unit to suffer D3+3 mortal wounds. This model is then destroyed.")],
         keywords=["Unggoy", "Infantry", "Grenades", "Auxiliary", "Suicide Bomber"]),
    dict(name="Unggoy Zealot", category="AUXILIARY", subtitle="Fanatical Auxiliary", points=10,
         profile=dict(M='8"', T="3", SV="6+", W="1", LD="7+", OC="1"), page=131,
         unit_composition=["1 Unggoy Zealot"], equipped=["Plasma Pistol", "Zealot Blade"], sergeant=[], auxiliary=[],
         wargear_options=[], leader=[], transport=[], rules_notes=[], wargear=[],
         ranged_weapons=[dict(name="Plasma Pistol", range='12"', A="1", BS_WS="4+", S="6", AP="-2", D="1",
                              keywords=["Pistol", "Plasma (AP1)"])],
         melee_weapons=[dict(name="Zealot Blade", range="Melee", A="3", BS_WS="3+", S="5", AP="-1", D="1",
                             keywords=["Lethal Hits", "Sustained Hits 2"])],
         abilities=[], keywords=["Unggoy", "Infantry", "Grenades", "Auxiliary", "Zealot"]),
]
i = next(i for i, d in enumerate(ds) if d["name"] == "Unggoy Warrior")
ds[i + 1:i + 1] = manual
for d in ds:  # tidy ability text and 'inches'
    for a in d["abilities"] + d["wargear"]:
        a["text"] = a["text"].strip()
json.dump(ds, open(out_dir + "/datasheets.json", "w"), indent=1, ensure_ascii=False)

dets = json.load(open("detachments.json"))
for d in dets:
    for e in d["enhancements"]:
        r = e["restriction"] or ""
        if r.startswith("Upgrade - "):
            m = re.match(r"^(Upgrade - .*?(?:only|units)(?:, excluding Character units)?\.)\s*(.*)$", r)
            if m and m.group(2):
                e["restriction"], extra = m.group(1), m.group(2)
                e["text"] = [extra] + e["text"]
            e["upgrade"] = True
json.dump(dets, open(out_dir + "/detachments.json", "w"), indent=1, ensure_ascii=False)
print(len(ds), "datasheets;", len(dets), "detachments")
