"""Detachment pages (11-39) as marked lines: python3 -I extract_dets.py in.pdf out.json"""
import json, sys
import pdfplumber
src, out = sys.argv[1:3]
res = []
with pdfplumber.open(src) as pdf:
    for n in range(11, 40):
        page = pdf.pages[n - 1]
        words = [w for w in page.extract_words(extra_attrs=["size", "fontname"]) if 40 < w["top"] < 760]
        rows = {}
        for w in words:
            rows.setdefault(round(w["top"] / 2), []).append(w)
        for k in sorted(rows):
            r = sorted(rows[k], key=lambda w: w["x0"])
            parts, cur = [], None
            for w in r:
                b = "Bold" in w["fontname"]
                if cur and cur[0] == b:
                    cur[1].append(w["text"])
                else:
                    cur = [b, [w["text"]]]; parts.append(cur)
            res.append(dict(page=n, top=round(r[0]["top"]), x=round(r[0]["x0"]), size=round(max(w["size"] for w in r), 1),
                            bold=all("Bold" in w["fontname"] for w in r),
                            marked=" ".join(("**" + " ".join(t) + "**") if b else " ".join(t) for b, t in parts).replace("(cid:127)", "•")))
json.dump(res, open(out, "w"), indent=0, ensure_ascii=False)
print(len(res))
