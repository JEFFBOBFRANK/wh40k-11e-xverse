"""dets_raw.json + text.txt -> detachments.json"""
import json, re, sys
L = json.load(open("dets_raw.json"))
T = open("text.txt").read()
pages = re.split(r"\n\n===== PAGE (\d+) =====\n", T)
P = {int(pages[i]): pages[i + 1] for i in range(1, len(pages), 2)}


def det_name(n):
    return P[n].splitlines()[1].replace(" — CONTINUED", "").strip()


def clean(t):
    t = re.sub(r"\s+", " ", t.replace("**", "")).strip()
    return t


dets, order = {}, []
cur_det = sect = item = None
prev = None
for l in L:
    name = det_name(l["page"])
    if name not in dets:
        dets[name] = dict(name=name, header="", rules=[], rules_intro=[], enhancements=[], enh_intro=[], stratagems=[])
        order.append(name); sect = item = None; prev = None
    d = dets[name]
    txt = l["marked"]
    plain = clean(txt)
    if l["size"] == 8.4:
        d["header"] = plain; continue
    if l["size"] == 11.2 and l["bold"]:
        sect = {"DETACHMENT RULES": "rules", "ENHANCEMENTS": "enhancements", "STRATAGEMS": "stratagems"}[plain]
        item = None; prev = None; continue
    if l["size"] == 12.5 and l["bold"]:
        item = dict(title=plain, lines=[]); d[sect].append(item); prev = None; continue
    if l["size"] == 9.6 and l["bold"] and item is not None:
        item["type"] = plain; continue
    gap = prev is not None and l["page"] == prev["page"] and l["top"] - prev["top"] > 16
    target = item["lines"] if item is not None else d["rules_intro" if sect == "rules" else "enh_intro"]
    if gap or not target or re.match(r"^(When|Target|Effect|Restrictions?):", plain):
        target.append(plain)
    else:
        target[-1] += " " + plain
    prev = l

out = []
for name in order:
    d = dets[name]
    m = re.match(r"(\d)DP • KEYWORD: (\w[\w' -]*?) • (.+)$", d["header"])
    rec = dict(name=name, dp=int(m.group(1)), unique=None if m.group(2) == "None" else m.group(2),
               disposition=m.group(3).strip(), rules=[], enhancements=[], stratagems=[],
               rules_intro=d["rules_intro"], enhancements_intro=d["enh_intro"])
    for r in d["rules"]:
        rec["rules"].append(dict(name=r["title"], text=r["lines"]))
    for e in d["enhancements"]:
        mm = re.match(r"^(.*?) - (\d+)pts( per unit)?$", e["title"])
        lines = e["lines"]
        upgrade = bool(mm and mm.group(3))
        restriction = None
        if lines and re.match(r"^(Upgrade - |[A-Z][\w' ]+ model only|.*\bonly\.$)", lines[0]):
            restriction = lines[0]; lines = lines[1:]
        rec["enhancements"].append(dict(name=mm.group(1) if mm else e["title"], points=int(mm.group(2)) if mm else None,
                                        upgrade=upgrade, restriction=restriction, text=lines))
    for s in d["stratagems"]:
        mm = re.match(r"^(.*?) - (\d)CP$", s["title"])
        st = dict(name=mm.group(1) if mm else s["title"], cp=int(mm.group(2)) if mm else None, type=s.get("type", ""))
        for line in s["lines"]:
            k = re.match(r"^(When|Target|Effect|Restrictions?):\s*(.*)$", line)
            if k:
                st[k.group(1).lower().rstrip("s")] = k.group(2)
            else:
                key = [x for x in ("restriction", "effect", "target", "when") if x in st]
                if key:
                    st[key[0]] += " " + line
                else:
                    st.setdefault("note", "")
                    st["note"] += line
        rec["stratagems"].append(st)
    out.append(rec)
json.dump(out, open("detachments.json", "w"), indent=1, ensure_ascii=False)
for r in out:
    print(f"{r['name']:32} {r['dp']}DP unique={r['unique']} {r['disposition']:18} rules={[x['name'] for x in r['rules']]} enh={len(r['enhancements'])} strat={len(r['stratagems'])}")
