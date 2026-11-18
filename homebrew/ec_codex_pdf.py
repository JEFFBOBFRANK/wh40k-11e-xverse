"""Build a printable Emperor's Children codex PDF from the published catalogue.

Usage: python3 homebrew/ec_codex_pdf.py [catalogue.json] [output.pdf]
Requires reportlab. Reads the New Recruit catalogue only; nothing is changed.
"""
import ast
import html
import re
import sys
from collections import OrderedDict
from pathlib import Path
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Frame, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent.parent
POINTS = "51b2-306e-1021-d207"
ENHANCEMENT_SLOT = "f759-1bc4-cb3a-f0d2"
DP = "82ae-1066-5107-6ae0"
SHOWN_HIDDEN = ["Unit Composition and Equipment", "Equipment Options", "CORE", "Datasheet Notes",
                "Printed Keywords and Notes"]

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
pdfmetrics.registerFont(TTFont("Body", FONT_DIR / "LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Body-Bold", FONT_DIR / "LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body-Italic", FONT_DIR / "LiberationSans-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Body-BoldItalic", FONT_DIR / "LiberationSans-BoldItalic.ttf"))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic",
                              boldItalic="Body-BoldItalic")

PURPLE = colors.HexColor("#4b1d52")
PINK = colors.HexColor("#b0306a")
PALE = colors.HexColor("#f3e9f4")
GREY = colors.HexColor("#666666")

S = {
    "title": ParagraphStyle("title", fontName="Body-Bold", fontSize=30, leading=36, alignment=TA_CENTER,
                            textColor=PURPLE),
    "subtitle": ParagraphStyle("subtitle", fontName="Body", fontSize=13, leading=18, alignment=TA_CENTER,
                               textColor=GREY),
    "h1": ParagraphStyle("h1", fontName="Body-Bold", fontSize=18, leading=22, textColor=PURPLE,
                         spaceBefore=4, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="Body-Bold", fontSize=13, leading=16, textColor=PINK,
                         spaceBefore=10, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="Body-Bold", fontSize=10, leading=13, textColor=PURPLE,
                         spaceBefore=6, spaceAfter=2),
    "body": ParagraphStyle("body", fontName="Body", fontSize=8.6, leading=11.4, spaceAfter=3),
    "bullet": ParagraphStyle("bullet", fontName="Body", fontSize=8.6, leading=11.4, leftIndent=10,
                             bulletIndent=2, spaceAfter=2),
    "small": ParagraphStyle("small", fontName="Body", fontSize=7.6, leading=9.6, textColor=GREY,
                            spaceAfter=2),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=7.6, leading=9.2),
    "cellb": ParagraphStyle("cellb", fontName="Body-Bold", fontSize=7.6, leading=9.2),
    "bar": ParagraphStyle("bar", fontName="Body-Bold", fontSize=12, leading=15, textColor=colors.white),
    "barr": ParagraphStyle("barr", fontName="Body-Bold", fontSize=11, leading=15, textColor=colors.white,
                           alignment=2),
    "toc1": ParagraphStyle("toc1", fontName="Body-Bold", fontSize=10, leading=14),
    "toc2": ParagraphStyle("toc2", fontName="Body", fontSize=8.6, leading=11, leftIndent=12),
}


# ---------------------------------------------------------------- text helpers
def inline(text):
    text = html.escape(text.replace("​", ""), quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    return text


def markup(text):
    """Convert the catalogue's light markdown into flowables."""
    text = (text or "").replace("​", "").replace("\r", "")
    text = re.sub(r"<br\s*/?>", "\n", text)
    out, table = [], []

    def flush_table():
        if not table:
            return
        rows = [r for r in table if not re.fullmatch(r"\|?\s*:?-{2,}.*", r)]
        data = [[Paragraph(inline(c.strip()), S["cell"]) for c in r.strip().strip("|").split("|")] for r in rows]
        width = max(len(r) for r in data)
        data = [r + [""] * (width - len(r)) for r in data]
        t = Table(data, hAlign="LEFT", colWidths=[170 / width * mm] * width)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, GREY),
                               ("BACKGROUND", (0, 0), (-1, 0), PALE),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        out.append(t)
        out.append(Spacer(1, 4))
        table.clear()

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|"):
            table.append(stripped)
            continue
        flush_table()
        if not stripped:
            continue
        if stripped.startswith("#"):
            out.append(Paragraph(inline(stripped.lstrip("#").strip()), S["h3"]))
        elif re.match(r"^([-•■*])\s+", stripped):
            out.append(Paragraph(inline(re.sub(r"^([-•■*])\s+", "", stripped)), S["bullet"], bulletText="•"))
        else:
            out.append(Paragraph(inline(stripped), S["body"]))
    flush_table()
    return out


# ---------------------------------------------------------------- data helpers
def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def chars(profile):
    return OrderedDict((c["name"], (c.get("$text") or "").strip()) for c in profile.get("characteristics", []))


def text_of(profile):
    return next(iter(chars(profile).values()), "")


def cost(entry, type_id):
    return next((c["value"] for c in entry.get("costs", []) if c.get("typeId") == type_id), 0)


def unit_prices():
    tree = ast.parse((ROOT / "homebrew" / "ec-4.0-migrate.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "UNIT_PRICES":
            return ast.literal_eval(node.value)
    return {}


def surcharge(entry):
    for m in entry.get("modifiers", []):
        if m.get("field") == POINTS and m.get("type") == "increment" and m.get("conditionGroups"):
            group = m["conditionGroups"][0].get("localConditionGroups", [{}])[0]
            if any(c.get("type") == "before" for c in group.get("conditions", [])):
                n = group["value"] + 1
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n, "th")
                return f"+{m['value']} pts for the {n}{suffix} and each later copy"
    return None


# ---------------------------------------------------------------- sections
def stratagem_cells(desc):
    parts = re.split(r"^#+\s*(When|Target|Effect|Restrictions)\s*$", desc.replace("​", ""), flags=re.M)
    fields = OrderedDict()
    for i in range(1, len(parts) - 1, 2):
        fields[parts[i]] = parts[i + 1].strip()
    return fields


def build(catalogue_path, out_path):
    cat = json.loads(Path(catalogue_path).read_text())["catalogue"]
    entries = cat["sharedSelectionEntries"]
    by_id = {e["id"]: e for e in entries}
    by_name = {e["name"]: e for e in entries}
    rules = {r["name"]: r for r in cat["sharedRules"]}
    prices = unit_prices()

    story = []
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"], S["toc2"]]

    # Title page
    story += [Spacer(1, 70 * mm), Paragraph("EMPEROR'S CHILDREN", S["title"]), Spacer(1, 6),
              Paragraph("Codex 4.0 — Playtest Reference", S["subtitle"]), Spacer(1, 4),
              Paragraph(f"Generated from the New Recruit catalogue, revision {cat['revision']}", S["subtitle"]),
              Spacer(1, 40 * mm),
              Paragraph("Unofficial homebrew fan content. Not endorsed by Games Workshop or New Recruit.",
                        S["small"]),
              PageBreak(), Paragraph("Contents", S["h1"]), toc, PageBreak()]

    # Army rules
    story.append(Paragraph("Army Rules", S["h1"]))
    army = by_name["Army Rules and References"]
    for link in army.get("infoLinks", []):
        rule = rules.get(link["name"])
        if rule:
            story.append(Paragraph(inline(rule["name"]), S["h2"]))
            story += markup(rule.get("description", ""))
    story.append(PageBreak())

    # Detachments
    story.append(Paragraph("Detachments", S["h1"]))
    detachments = by_name["Detachment"]["selectionEntryGroups"][0]["selectionEntries"]
    det_ids = {d["id"]: d["name"] for d in detachments}
    enh_by_det = OrderedDict((d["name"], []) for d in detachments)
    enhancements = [e for e in entries if cost(e, ENHANCEMENT_SLOT)]
    for enh in enhancements:
        owners = set()
        for node in walk(entries):
            if node.get("targetId") == enh["id"]:
                blob = json.dumps(node)
                owners |= {name for i, name in det_ids.items() if i in blob}
        for owner in owners:
            enh_by_det[owner].append(enh)

    first = True
    for det in detachments:
        if not first:
            story.append(PageBreak())
        first = False
        name = det["name"]
        dispositions = [c["name"] for c in det.get("categoryLinks", []) if not c["name"].startswith(("3DP", "Unique"))]
        uniques = [c["name"] for c in det.get("categoryLinks", []) if c["name"].startswith("Unique")]
        story.append(Paragraph(inline(name), S["h2"]))
        meta = f"<b>{cost(det, DP)} DP</b>"
        if dispositions:
            meta += " · Force Dispositions: " + ", ".join(dispositions)
        if uniques:
            meta += " · " + ", ".join(uniques)
        story.append(Paragraph(meta, S["small"]))
        for rule in det.get("rules", []):
            if rule.get("hidden"):
                continue
            story.append(Paragraph(inline(rule["name"]), S["h3"]))
            story += markup(rule.get("description", ""))

        enh = sorted(enh_by_det[name], key=lambda e: e["name"])
        if enh:
            story.append(Paragraph("Enhancements and Upgrades", S["h3"]))
            rows = [[Paragraph("<b>Name</b>", S["cell"]), Paragraph("<b>Pts</b>", S["cell"]),
                     Paragraph("<b>Rule</b>", S["cell"])]]
            for e in enh:
                limit = next((c["value"] for c in e.get("constraints", []) if c["type"] == "max"), None)
                label = inline(e["name"])
                if "[Upgrade]" in e["name"] and limit:
                    label += f"<br/><font color='#666666'>Up to {limit} per army</font>"
                desc = " ".join(r.get("description", "") for r in e.get("rules", []) if not r.get("hidden"))
                desc = desc.replace("​", "").strip()
                rows.append([Paragraph(label, S["cellb"]), Paragraph(str(cost(e, POINTS)), S["cell"]),
                             Paragraph(inline(desc).replace("\n", "<br/>"), S["cell"])])
            t = Table(rows, colWidths=[42 * mm, 12 * mm, 116 * mm], repeatRows=1, hAlign="LEFT")
            t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, GREY), ("BACKGROUND", (0, 0), (-1, 0), PALE),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.append(t)

        strats = [r for r in cat["sharedRules"] if r["name"].startswith(name + " — ")]
        if strats:
            story.append(Paragraph("Stratagems", S["h3"]))
            for r in strats:
                title = r["name"][len(name) + 3:]
                fields = stratagem_cells(r.get("description", ""))
                rows = [[Paragraph(f"<b>{inline(title)}</b>", S["bar"])]]
                body = []
                for key, value in fields.items():
                    body.append(Paragraph(f"<b>{key.upper()}:</b> {inline(value)}".replace("\n", "<br/>"),
                                          S["cell"]))
                if not fields:
                    body = markup(r.get("description", ""))
                rows += [[b] for b in body]
                t = Table(rows, colWidths=[170 * mm], hAlign="LEFT")
                t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PURPLE),
                                       ("BOX", (0, 0), (-1, -1), 0.5, PURPLE),
                                       ("TOPPADDING", (0, 1), (-1, -1), 2),
                                       ("BOTTOMPADDING", (0, 1), (-1, -1), 2)]))
                story += [KeepTogether(t), Spacer(1, 4)]
    story.append(PageBreak())

    # Datasheets
    root = [l for l in cat["entryLinks"] if by_id.get(l["targetId"], {}).get("type") in {"unit", "model"}]
    native, legions = [], []
    for link in root:
        entry = by_id[link["targetId"]]
        cats = {c["name"] for c in entry.get("categoryLinks", [])}
        (legions if "Faction: Legions of Excess" in cats or link.get("hidden") else native).append(entry)

    summary = []
    for title, units in (("Datasheets", native), ("Legions of Excess", legions)):
        story.append(Paragraph(title, S["h1"]))
        for i, unit in enumerate(units):
            if i:
                story.append(CondPageBreak(120 * mm))
            story += datasheet(unit, prices, rules)
            summary.append((title, unit))
        story.append(PageBreak())

    # Points summary
    story.append(Paragraph("Points Summary", S["h1"]))
    rows = [[Paragraph("<b>Unit</b>", S["cell"]), Paragraph("<b>Points</b>", S["cell"]),
             Paragraph("<b>Repeat cost</b>", S["cell"])]]
    for group, unit in summary:
        rows.append([Paragraph(inline(unit["name"]) + (" <font color='#666666'>(Legions)</font>"
                                                       if group != "Datasheets" else ""), S["cell"]),
                     Paragraph(points_text(unit, prices), S["cell"]),
                     Paragraph(surcharge(unit) or "–", S["cell"])])
    t = Table(rows, colWidths=[70 * mm, 40 * mm, 60 * mm], repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, GREY), ("BACKGROUND", (0, 0), (-1, 0), PALE),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf6fb")])]))
    story.append(t)

    doc = CodexDoc(str(out_path), revision=cat["revision"])
    doc.multiBuild(story)


def points_text(unit, prices):
    tiers = prices.get(unit["name"]) or (cost(unit, POINTS),)
    return " / ".join(str(p) for p in tiers)


def datasheet(unit, prices, rules):
    out = []
    head = Table([[Paragraph(inline(unit["name"]).upper(), S["bar"]),
                   Paragraph(points_text(unit, prices) + " pts", S["barr"])]],
                 colWidths=[130 * mm, 40 * mm])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PURPLE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    out.append(head)
    rep = surcharge(unit)
    if rep:
        out.append(Paragraph(rep, S["small"]))

    stats, ranged, melee, seen = [], [], [], set()
    for node in walk(unit):
        for p in node.get("profiles", []) if isinstance(node, dict) else []:
            key = (p.get("typeName"), p["name"], tuple(chars(p).items()))
            if key in seen or p.get("hidden"):
                continue
            seen.add(key)
            if p.get("typeName") == "Unit":
                stats.append(p)
            elif p.get("typeName") == "Ranged Weapons":
                ranged.append(p)
            elif p.get("typeName") == "Melee Weapons":
                melee.append(p)

    def grid(profiles, first_col, widths):
        if not profiles:
            return None
        cols = list(chars(profiles[0]).keys())
        rows = [[Paragraph(f"<b>{first_col}</b>", S["cell"])] + [Paragraph(f"<b>{c}</b>", S["cell"]) for c in cols]]
        for p in profiles:
            rows.append([Paragraph(inline(p["name"]), S["cellb"])] +
                        [Paragraph(inline(v), S["cell"]) for v in chars(p).values()])
        t = Table(rows, colWidths=widths(len(cols)), repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
                               ("BACKGROUND", (0, 0), (-1, 0), PALE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
        return t

    if stats:
        out.append(Spacer(1, 3))
        out.append(grid(stats, "Model", lambda n: [50 * mm] + [120 * mm / n] * n))
    for profiles, label in ((ranged, "Ranged weapon"), (melee, "Melee weapon")):
        if profiles:
            out.append(Spacer(1, 3))
            out.append(grid(profiles, label,
                            lambda n: [44 * mm, 14 * mm] + [10 * mm] * (n - 3) + [13 * mm] + [170 * mm - 71 * mm - 10 * mm * (n - 3)]))

    abilities = [p for p in unit.get("profiles", []) if p.get("typeName") == "Abilities" and not p.get("hidden")]
    links = [i["name"] for i in unit.get("infoLinks", []) if i.get("type") == "rule" and i["name"] != "Leader"]
    if links:
        out.append(Paragraph("<b>Rules:</b> " + inline(", ".join(OrderedDict.fromkeys(links))), S["body"]))
    if abilities:
        out.append(Paragraph("Abilities", S["h3"]))
        for p in abilities:
            body = markup(text_of(p))
            label = Paragraph(f"<b>{inline(p['name'])}</b>", S["body"])
            out.append(KeepTogether([label] + body[:1]))
            out += body[1:]

    hidden = {p["name"]: text_of(p) for p in unit.get("profiles", []) if p.get("hidden")}
    notes = []
    for name in SHOWN_HIDDEN:
        value = (hidden.get(name) or "").strip()
        if value and value not in {"Core: None."}:
            notes.append(Paragraph(inline(value).replace("\n", "<br/>"), S["small"]))
    option_costs = []
    for node in walk(unit.get("selectionEntries", []) + unit.get("selectionEntryGroups", [])):
        if (isinstance(node, dict) and node.get("type") == "upgrade" and cost(node, POINTS)
                and not re.fullmatch(r"\d+ models?", node["name"].strip())):
            option_costs.append(f"{node['name']} +{cost(node, POINTS)}")
    if option_costs:
        notes.append(Paragraph("Option costs: " + inline(", ".join(OrderedDict.fromkeys(option_costs))),
                               S["small"]))
    if notes:
        out.append(Paragraph("Composition and keywords", S["h3"]))
        out += notes
    out.append(Spacer(1, 10))
    return out


class CodexDoc(BaseDocTemplate):
    def __init__(self, filename, revision, **kw):
        super().__init__(filename, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                         topMargin=18 * mm, bottomMargin=16 * mm, title="Emperor's Children Codex 4.0",
                         author="Xverse homebrew", **kw)
        self.revision = revision
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=self.decorate)])

    def decorate(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setFont("Body", 7.5)
        canvas.setFillColor(GREY)
        canvas.drawString(20 * mm, 10 * mm, f"Emperor's Children Codex 4.0 · revision {self.revision}")
        canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            if style in {"h1", "h2"} and flowable.getPlainText() != "Contents":
                self.notify("TOCEntry", (0 if style == "h1" else 1, flowable.getPlainText(), self.page))


if __name__ == "__main__":
    catalogue = sys.argv[1] if len(sys.argv) > 1 else ROOT / "Chaos - Emperor's Children.json"
    output = sys.argv[2] if len(sys.argv) > 2 else ROOT / "Emperors-Children-Codex-4.0.pdf"
    build(catalogue, output)
    print("Wrote", output)
