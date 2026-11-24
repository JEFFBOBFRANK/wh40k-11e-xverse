"""Dump each datasheet page of the Covenant PDF into columns and tables: python3 -I extract_pages.py in.pdf out.json"""
import json, re, sys
import pdfplumber

src, out = sys.argv[1:3]
pages = []
with pdfplumber.open(src) as pdf:
    for n, page in enumerate(pdf.pages, 1):
        if n < 41 or n > 136:
            continue
        # Rebuild every weapon table from its ruling lines (find_tables drops the outer column on some pages).
        hl = [l for l in page.lines if abs(l["top"] - l["bottom"]) < 0.5 and l["x1"] - l["x0"] > 100]
        vl = [l for l in page.lines if abs(l["x0"] - l["x1"]) < 0.5 and l["bottom"] - l["top"] < 400]
        def joined(x, y0, y1):  # a vertical rule at x runs from y0 to y1
            return any(abs(v["x0"] - x) < 2 and v["top"] <= y0 + 2 and v["bottom"] >= y1 - 2 for v in vl)
        blocks = []
        for l in sorted(hl, key=lambda l: (round(l["x0"]), round(l["x1"]), l["top"])):
            for b in blocks:
                if (abs(b["x0"] - l["x0"]) < 2 and abs(b["x1"] - l["x1"]) < 2 and l["top"] > b["bottom"]
                        and joined(b["x0"], b["bottom"], l["top"])):
                    b["ys"].append(l["top"]); b["bottom"] = l["top"]; break
            else:
                blocks.append(dict(x0=l["x0"], x1=l["x1"], ys=[l["top"]], top=l["top"], bottom=l["top"]))
        tables = []
        for b in blocks:
            ys = sorted(set(round(y, 1) for y in b["ys"]))
            if len(ys) < 2:
                continue
            xs = sorted(set(round(l["x0"], 1) for l in vl if b["x0"] - 2 <= l["x0"] <= b["x1"] + 2
                            and l["top"] <= ys[0] + 2 and l["bottom"] >= ys[-1] - 2))
            xs = sorted(set([round(b["x0"], 1), round(b["x1"], 1)] + xs))
            bbox = (xs[0], ys[0], xs[-1], ys[-1])
            cells = page.crop(bbox).extract_table(dict(vertical_strategy="explicit", horizontal_strategy="explicit",
                                                       explicit_vertical_lines=xs, explicit_horizontal_lines=ys))
            if cells:
                tables.append(dict(bbox=bbox, rows=cells))
        boxes = [t["bbox"] for t in tables]
        words = page.extract_words(extra_attrs=["size", "fontname"], keep_blank_chars=False)

        def in_table(w):
            return any(b[0] - 2 <= w["x0"] <= b[2] + 2 and b[1] - 2 <= w["top"] <= b[3] + 2 for b in boxes)

        def lines(ws):
            rows = {}
            for w in ws:
                rows.setdefault(round(w["top"] / 2), []).append(w)
            out = []
            for k in sorted(rows):
                r = sorted(rows[k], key=lambda w: w["x0"])
                parts, cur = [], None
                for w in r:
                    b = "Bold" in w["fontname"]
                    if cur and cur[0] == b:
                        cur[1].append(w["text"])
                    else:
                        cur = [b, [w["text"]]]; parts.append(cur)
                marked = " ".join(("**" + " ".join(t) + "**") if b else " ".join(t) for b, t in parts)
                out.append(dict(top=round(r[0]["top"]), x=round(r[0]["x0"]), size=round(max(w["size"] for w in r), 1),
                                bold=all("Bold" in w["fontname"] for w in r),
                                text=" ".join(w["text"] for w in r).replace("(cid:127)", "•"),
                                marked=marked.replace("(cid:127)", "•")))
            return out
        body = [w for w in words if not in_table(w) and w["top"] < 760]
        foot = [w for w in words if not in_table(w) and w["top"] >= 760]
        head = [w for w in body if w["top"] < 125]
        left = [w for w in body if w["top"] >= 125 and w["x0"] < 305]
        right = [w for w in body if w["top"] >= 125 and w["x0"] >= 305]
        tabs = []
        for t in tables:
            rows = [[(c or "").replace("\n", " ").strip() for c in r] for r in t["rows"]]
            tabs.append(dict(bbox=[round(v) for v in t["bbox"]], rows=rows))
        pages.append(dict(page=n, head=lines(head), left=lines(left), right=lines(right), foot=lines(foot), tables=tabs))
json.dump(pages, open(out, "w"), indent=1, ensure_ascii=False)
print(len(pages), "pages")
