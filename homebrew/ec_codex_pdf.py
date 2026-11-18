"""Build the Emperor's Children codex PDF from the published catalogue.

The layout follows the Covenant codex house style: a header band on every
page, one datasheet per page with stat boxes and two columns, detachment
pages with rules, enhancements and stratagems, and a points reference.

Usage: python3 homebrew/ec_codex_pdf.py [catalogue.json] [output.pdf]
Requires reportlab. Reads the New Recruit catalogue only; nothing is changed.
"""
import ast
import html
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Flowable, Frame, FrameBreak, KeepTogether, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
POINTS = "51b2-306e-1021-d207"
ENHANCEMENT_SLOT = "f759-1bc4-cb3a-f0d2"
DP = "82ae-1066-5107-6ae0"
VERSION = "4.0"
FACTION = "EMPEROR'S CHILDREN"
ARMY_RULES = {"The Pursuit of Perfection", "Sublime Strategist", "Manifestation", "Summoning Rituals"}

# House style, taken from the Covenant codex
PAGE_BG = colors.HexColor("#edf1f0")
HEADER = colors.HexColor("#132a38")
BAR = colors.HexColor("#234f53")
ACCENT = colors.HexColor("#5fbfb4")
PILL = colors.HexColor("#2c6a6c")
INK = colors.HexColor("#1b2a33")
SUBHEAD = colors.HexColor("#1d3a4a")
GRID = colors.HexColor("#1c4250")
ZEBRA = colors.HexColor("#e1eaea")
RULE = colors.HexColor("#b9c6c8")
MUTED = colors.HexColor("#5b6b73")

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
for _name, _file in (("Body", "Regular"), ("Body-Bold", "Bold"), ("Body-Italic", "Italic"),
                     ("Body-BoldItalic", "BoldItalic")):
    pdfmetrics.registerFont(TTFont(_name, FONT_DIR / f"LiberationSans-{_file}.ttf"))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic",
                              boldItalic="Body-BoldItalic")

W, H = letter
MARGIN = 36
HEADER_H = 84
SHEET_HEADER_H = 128
TEXT_W = W - 2 * MARGIN - 28
COL_W = (W - 2 * MARGIN - 18) / 2


def style(name, size, leading=None, font="Body", color=INK, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading or size * 1.3,
                          textColor=color, **kw)


S = {
    "body": style("body", 10.5, 14, spaceAfter=5),
    "tight": style("tight", 10.5, 14, spaceAfter=3, leftIndent=8, firstLineIndent=-8),
    "bullet": style("bullet", 10.5, 14, leftIndent=12, bulletIndent=2, spaceAfter=3),
    "sub": style("sub", 12.5, 16, "Body-Bold", SUBHEAD, spaceBefore=4, spaceAfter=3),
    "bar": style("bar", 10.5, 13, "Body-Bold", colors.white),
    "cell": style("cell", 7.6, 9.4),
    "cellh": style("cellh", 6.8, 8.6, "Body-Bold", colors.white, alignment=TA_CENTER),
    "cellc": style("cellc", 7.6, 9.4, alignment=TA_CENTER),
    "pt": style("pt", 10.5, 13),
    "ptb": style("ptb", 10.5, 13, "Body-Bold"),
    "pth": style("pth", 10.5, 13, "Body-Bold", colors.white),
    "toc": style("toc", 11, 14.5, "Body-Bold"),
    "tocsub": style("tocsub", 10, 13, "Body", MUTED, leftIndent=18),
    "note": style("note", 8.6, 11, color=MUTED, spaceAfter=4),
}


# ---------------------------------------------------------------- text helpers
def clean(text):
    return (text or "").replace("​", "").replace("\r", "").strip()


def inline(text):
    text = html.escape(clean(text), quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def grid_style(table):
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), GRID), ("BOX", (0, 0), (-1, -1), 0.6, GRID),
                               ("INNERGRID", (0, 0), (-1, -1), 0.3, RULE),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA]),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return table


def markup(text, width):
    """Turn the catalogue's light markdown into flowables."""
    text = re.sub(r"<br\s*/?>", "\n", clean(text))
    out, rows = [], []

    def flush():
        if not rows:
            return
        data = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows
                if not re.fullmatch(r"\|?[\s:|-]+\|?", r)]
        rows.clear()
        n = max(len(r) for r in data)
        cells = [[Paragraph(inline(c), S["pth"] if i == 0 else S["pt"]) for c in r + [""] * (n - len(r))]
                 for i, r in enumerate(data)]
        t = grid_style(Table(cells, colWidths=[width / n] * n, hAlign="LEFT"))
        t.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        out.extend([t, Spacer(1, 6)])

    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("|"):
            rows.append(s)
            continue
        flush()
        if not s:
            continue
        heading = re.fullmatch(r"#+\s*(.+)", s) or re.fullmatch(r"\*\*([^*]+)\*\*:?", s)
        if heading:
            out.append(Paragraph(inline(heading.group(1)), S["sub"]))
        elif re.match(r"^[-•■*]\s+", s):
            out.append(Paragraph(inline(re.sub(r"^[-•■*]\s+", "", s)), S["bullet"], bulletText="•"))
        else:
            out.append(Paragraph(inline(s), S["body"]))
    flush()
    return out


def section_bar(title, width):
    t = Table([[Paragraph(html.escape(title.upper()), S["bar"])]], colWidths=[width], hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BAR), ("ROUNDEDCORNERS", [4, 4, 4, 4]),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9)]))
    return t


def sentences(text):
    return [p for p in re.split(r"(?<=[.!?])\s+(?=[A-Z])", clean(text).replace("\n", " ")) if p]


def bullets(items):
    return [Paragraph("• " + inline(i), S["tight"]) for i in items]


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
    return OrderedDict((c["name"], clean(c.get("$text"))) for c in profile.get("characteristics", []))


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


def repeat_cost(entry):
    """(extra points, first copy that pays) for a datasheet's repeat-selection cost."""
    for m in entry.get("modifiers", []):
        if m.get("field") == POINTS and m.get("type") == "increment" and m.get("conditionGroups"):
            group = m["conditionGroups"][0].get("localConditionGroups", [{}])[0]
            if any(c.get("type") == "before" for c in group.get("conditions", [])):
                return m["value"], group["value"] + 1
    return None


def ordinal(n):
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n, 'th') }"


GROUPS = ["Epic Heroes", "Characters", "Battleline", "Infantry", "Mounted", "Beasts", "Monsters",
          "Dedicated Transports", "Vehicles", "Legions of Excess"]


def group_of(entry, hidden_link):
    cats = {c["name"] for c in entry.get("categoryLinks", [])}
    if "Faction: Legions of Excess" in cats or hidden_link:
        return "Legions of Excess"
    for cat, group in (("Epic Hero", "Epic Heroes"), ("Character", "Characters"), ("Battleline", "Battleline"),
                       ("Dedicated Transport", "Dedicated Transports"), ("Vehicle", "Vehicles"),
                       ("Monster", "Monsters"), ("Mounted", "Mounted"), ("Beast", "Beasts")):
        if cat in cats:
            return group
    return "Infantry"


def subtitle_of(entry):
    cats = [c["name"] for c in entry.get("categoryLinks", [])]
    return " - ".join(c for c in ("Epic Hero", "Character", "Battleline", "Dedicated Transport", "Infantry",
                                  "Mounted", "Beast", "Monster", "Vehicle") if c in cats)


# ---------------------------------------------------------------- page furniture
class State(Flowable):
    """Zero-size marker: sets the page header and records a contents entry."""

    def __init__(self, toc=None, level=1, **info):
        super().__init__()
        self.toc, self.level, self.info = toc, level, info
        self.width = self.height = 0

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        pass


class Leader(Flowable):
    def wrap(self, aw, ah):
        self.width = aw
        return aw, 10

    def draw(self):
        c = self.canv
        c.setStrokeColor(colors.HexColor("#9aa7a9"))
        c.setDash(1, 2)
        c.setLineWidth(0.5)
        c.line(2, 2, self.width - 2, 2)


class Codex(BaseDocTemplate):
    def __init__(self, filename, revision):
        super().__init__(filename, pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN,
                         bottomMargin=MARGIN, title="Codex: Emperor's Children", author="Xverse homebrew")
        self.revision = revision
        self.info = {}
        self.last_title = None
        self.entries = []
        body_top = H - HEADER_H - 22
        sheet_top = H - SHEET_HEADER_H - 14
        self.addPageTemplates([
            PageTemplate("cover", [Frame(0, 0, W, H, id="c")], onPage=self.cover),
            PageTemplate("section", [Frame(MARGIN + 14, 56, TEXT_W, body_top - 56, id="s")],
                         onPage=self.background, onPageEnd=self.section_header),
            PageTemplate("sheet", [
                Frame(MARGIN, 62, COL_W, sheet_top - 62, id="l", leftPadding=0, rightPadding=0),
                Frame(MARGIN + COL_W + 18, 62, COL_W, sheet_top - 62, id="r", leftPadding=0, rightPadding=0),
            ], onPage=self.background, onPageEnd=self.sheet_header),
        ])

    def handle_flowable(self, flowables):
        if flowables and isinstance(flowables[0], State):
            state = flowables[0]
            if "title" in state.info:
                self.info = state.info
            if state.toc:
                self.entries.append((state.toc, state.level, self.page))
        super().handle_flowable(flowables)

    def cover(self, c, doc):
        c.saveState()
        c.setFillColor(colors.HexColor("#0c0f1c"))
        c.rect(0, 0, W, H, stroke=0, fill=1)
        c.setStrokeColor(colors.HexColor("#1d2540"))
        c.setLineWidth(12)
        c.ellipse(80, 250, W - 80, 640, stroke=1, fill=0)
        c.setLineWidth(1)
        c.setStrokeColor(ACCENT)
        c.rect(18, 18, W - 36, H - 36, stroke=1, fill=0)
        c.setStrokeColor(colors.HexColor("#3c4a66"))
        c.rect(24, 24, W - 48, H - 48, stroke=1, fill=0)
        for y, h, rule_y in ((H - 196, 160, H - 39), (52, 140, 52)):
            c.setFillColor(colors.HexColor("#121a2b"))
            c.rect(36, y, W - 72, h, stroke=0, fill=1)
            c.setFillColor(ACCENT)
            c.rect(36, rule_y, W - 72, 3, stroke=0, fill=1)
        c.setFont("Body-Bold", 7.5)
        c.drawCentredString(W / 2, H - 62, "UNOFFICIAL WARHAMMER 40,000 ARMY RULES")
        c.setFillColor(colors.white)
        c.setFont("Body-Bold", 17)
        c.drawCentredString(W / 2, H - 100, "CODEX:")
        c.setFont("Body-Bold", 34)
        c.drawCentredString(W / 2, H - 142, FACTION)
        c.setFillColor(colors.HexColor("#c9cdd8"))
        c.setFont("Body-Bold", 7.5)
        c.drawCentredString(W / 2, H - 170, "THE PURSUIT OF PERFECTION")
        c.setFillColor(colors.HexColor("#2b3452"))
        c.setFont("Body-Bold", 60)
        c.drawCentredString(W / 2, 425, "EXCESS")
        c.setFillColor(colors.white)
        c.setFont("Body-Bold", 12)
        c.drawCentredString(W / 2, 160, "DEVELOPMENT GAMEPLAY EDITION")
        c.setFont("Body-Bold", 13)
        c.drawCentredString(W / 2, 128, f"VERSION {VERSION}")
        c.setFillColor(ACCENT)
        c.setFont("Body-Bold", 7.5)
        c.drawCentredString(W / 2, 104, "PLAYTEST BUILD")
        c.setFillColor(colors.HexColor("#c9cdd8"))
        c.setFont("Body", 6.8)
        c.drawCentredString(W / 2, 86, f"New Recruit catalogue revision {self.revision}")
        c.drawCentredString(W / 2, 32, "Unofficial fan content. Not endorsed by Games Workshop or New Recruit.")
        c.restoreState()

    def background(self, c, doc):
        c.saveState()
        c.setFillColor(PAGE_BG)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        c.restoreState()

    def title_for(self, title):
        shown = title + " — CONTINUED" if title and title == self.last_title else title
        self.last_title = title
        return shown

    def band(self, c, height):
        c.setFillColor(HEADER)
        c.rect(0, H - height, W, height, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#3f7f7e"))
        c.rect(0, H - height - 4, W, 4, stroke=0, fill=1)

    @staticmethod
    def fit(text, font, size, width, minimum):
        while pdfmetrics.stringWidth(text, font, size) > width and size > minimum:
            size -= 0.5
        return size

    def section_header(self, c, doc):
        info = self.info
        c.saveState()
        self.band(c, HEADER_H)
        c.setFillColor(ACCENT)
        c.setFont("Body-Bold", 7.5)
        c.drawString(MARGIN + 14, H - 24, info.get("kicker", ""))
        title = self.title_for(info.get("title", ""))
        c.setFillColor(colors.white)
        c.setFont("Body-Bold", self.fit(title, "Body-Bold", 25, TEXT_W, 14))
        c.drawString(MARGIN + 14, H - 57, title)
        if info.get("meta"):
            c.setFillColor(colors.HexColor("#d9e2e4"))
            c.setFont("Body-Bold", 7.5)
            c.drawRightString(W - MARGIN - 14, H - 76, info["meta"])
        c.setStrokeColor(colors.HexColor("#c4cdcc"))
        c.setLineWidth(0.6)
        c.line(MARGIN + 14, 46, W - MARGIN - 14, 46)
        c.setFillColor(MUTED)
        c.setFont("Body-Bold", 7)
        c.drawString(MARGIN + 14, 33, f"UNOFFICIAL FAN-MADE GAMEPLAY RULES  •  VERSION {VERSION}")
        c.setFillColor(INK)
        c.drawRightString(W - MARGIN - 14, 30, str(self.page))
        c.restoreState()

    def sheet_header(self, c, doc):
        info = self.info
        c.saveState()
        self.band(c, SHEET_HEADER_H)
        c.setFillColor(ACCENT)
        c.setFont("Body-Bold", 7.5)
        c.drawString(MARGIN, H - 18, info.get("kicker", ""))
        title = self.title_for(info.get("title", ""))
        c.setFillColor(colors.white)
        c.setFont("Body-Bold", self.fit(title, "Body-Bold", 22, W - 2 * MARGIN - 130, 12))
        c.drawString(MARGIN, H - 46, title)
        c.setFillColor(colors.HexColor("#c9d3d6"))
        c.setFont("Body", 8.5)
        c.drawString(MARGIN, H - 63, info.get("subtitle", ""))
        pts = info.get("points", "")
        pw = max(84, pdfmetrics.stringWidth(pts, "Body-Bold", 12) + 26)
        c.setFillColor(PILL)
        c.roundRect(W - MARGIN - pw, H - 60, pw, 30, 6, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Body-Bold", 12)
        c.drawCentredString(W - MARGIN - pw / 2, H - 49, pts)
        c.setFillColor(ACCENT)
        c.setFont("Body-Bold", 7)
        c.drawRightString(W - MARGIN, H - 73, "FACTION: " + info.get("faction", "").upper())
        stats = info.get("stats") or []
        if stats:
            gap = 6
            bw = (W - 2 * MARGIN - gap * (len(stats) - 1)) / len(stats)
            for i, (k, v) in enumerate(stats):
                bx = MARGIN + i * (bw + gap)
                c.setFillColor(colors.white)
                c.setStrokeColor(ACCENT)
                c.setLineWidth(0.8)
                c.roundRect(bx, H - 122, bw, 38, 4, stroke=1, fill=1)
                c.setFillColor(SUBHEAD)
                c.setFont("Body-Bold", 7.5)
                c.drawCentredString(bx + bw / 2, H - 96, k)
                c.setFillColor(INK)
                c.setFont("Body-Bold", 13)
                c.drawCentredString(bx + bw / 2, H - 114, v)
        c.setStrokeColor(colors.HexColor("#c4cdcc"))
        c.setLineWidth(0.6)
        c.line(W / 2, 64, W / 2, H - SHEET_HEADER_H - 14)
        c.setFillColor(HEADER)
        c.roundRect(MARGIN, 18, W - 2 * MARGIN, 32, 3, stroke=0, fill=1)
        kw = "KEYWORDS: " + info.get("keywords", "")
        c.setFillColor(colors.white)
        c.setFont("Body-Bold", self.fit(kw, "Body-Bold", 7.6, W - 2 * MARGIN - 50, 5.5))
        c.drawString(MARGIN + 11, 30, kw)
        c.setFillColor(colors.HexColor("#6f8c97"))
        c.setFont("Body", 7)
        c.drawRightString(W - MARGIN - 10, 30, str(self.page))
        c.restoreState()


# ---------------------------------------------------------------- content builders
def contents_story(entries, groups):
    pages = {(t, lvl): p for t, lvl, p in entries}
    story = []
    for title, items in groups:
        bar = Table([[Paragraph(html.escape(title.upper()), S["bar"]),
                      Paragraph(f"<para alignment='right'>{pages.get((title, 0), '')}</para>", S["bar"])]],
                    colWidths=[TEXT_W - 50, 50])
        bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BAR), ("ROUNDEDCORNERS", [4, 4, 4, 4]),
                                 ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        rows = [[Paragraph(html.escape(item), S["toc"]), Leader(),
                 Paragraph(f"<b>{pages.get((item, 1), '')}</b>", S["toc"])] for item in items]
        name_w = max(pdfmetrics.stringWidth(i, "Body-Bold", 11) for i in items) + 22
        t = Table(rows, colWidths=[name_w, TEXT_W - name_w - 34, 34], hAlign="LEFT")
        t.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                               ("LEFTPADDING", (0, 0), (0, -1), 12), ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
        story += [CondPageBreak(90), bar, Spacer(1, 7), t, Spacer(1, 10)]
    return story


def army_rules_story(army_links, rules):
    story = [State("Army Rules", 0, kicker=f"{FACTION} CORE RULES", title="Army Rules"),
             Paragraph("The army rules below apply to every <b>Emperor's Children</b> army.", S["body"])]
    for name in army_links:
        story += [CondPageBreak(110), State(name, 1), section_bar(name, TEXT_W), Spacer(1, 5)]
        story += markup(rules[name].get("description", ""), TEXT_W)
    return story


def detachment_story(det, enhancements, strats, first):
    name = det["name"]
    cats = [c["name"] for c in det.get("categoryLinks", []) if not c["name"].startswith("3DP")]
    meta = "  •  ".join([f"{cost(det, DP)}DP"] + cats)
    story = [State("Detachments", 0)] if first else []
    story += [State(name, 1, kicker=f"{FACTION} DETACHMENT", title=name, meta=meta),
              section_bar("Detachment Rules", TEXT_W), Spacer(1, 4)]
    for rule in det.get("rules", []):
        if not rule.get("hidden"):
            story.append(Paragraph(inline(rule["name"]), S["sub"]))
            story += markup(rule.get("description", ""), TEXT_W)
    if enhancements:
        story += [CondPageBreak(90), section_bar("Enhancements", TEXT_W), Spacer(1, 4)]
        for e in sorted(enhancements, key=lambda e: ("[Upgrade]" in e["name"], e["name"])):
            upgrade = "[Upgrade]" in e["name"]
            pts = f"{cost(e, POINTS)}pts" + (" per unit" if upgrade else "")
            block = [Paragraph(f"{inline(e['name'].replace(' [Upgrade]', ''))} - {pts}", S["sub"])]
            if upgrade:
                limit = next((c["value"] for c in e.get("constraints", []) if c["type"] == "max"), 1)
                block.append(Paragraph(f"Upgrade. Up to {limit} eligible units can purchase this Upgrade; each pays "
                                       "separately, but all copies collectively occupy one Enhancement selection.",
                                       S["body"]))
            desc = " ".join(clean(r.get("description")) for r in e.get("rules", []) if not r.get("hidden"))
            story.append(KeepTogether(block + markup(desc, TEXT_W)))
    if strats:
        story += [CondPageBreak(110), section_bar("Stratagems", TEXT_W), Spacer(1, 4)]
        for r in strats:
            title, cp = re.match(r".+? — (.+) / (\d+) CP$", r["name"]).groups()
            parts = re.split(r"^#+\s*(When|Target|Effect|Restrictions)\s*$", clean(r.get("description")), flags=re.M)
            block = [Paragraph(f"{inline(title)} - {cp}CP", S["sub"])]
            if len(parts) > 1:
                block += [Paragraph(f"{parts[i]}: {inline(parts[i + 1].strip())}", S["body"])
                          for i in range(1, len(parts) - 1, 2)]
            else:
                block += markup(r.get("description", ""), TEXT_W)
            story.append(KeepTogether(block))
    return story


def weapon_table(profiles, width):
    cols = list(chars(profiles[0]).keys())
    head = ["Weapon"] + [("Abilities" if c == "Keywords" else c) for c in cols]
    fixed = [0.25, 0.115] + [0.064] * (len(cols) - 2)
    widths = [width * f for f in fixed] + [width * (1 - sum(fixed))]
    data = [[Paragraph(h, S["cellh"]) for h in head]]
    for p in profiles:
        vals = list(chars(p).values())
        data.append([Paragraph(inline(p["name"]), S["cell"])] +
                    [Paragraph(inline(v), S["cell"] if i == len(vals) - 1 else S["cellc"])
                     for i, v in enumerate(vals)])
    t = grid_style(Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT"))
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 2.5), ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]))
    return t


def profile_table(profiles, width):
    cols = list(chars(profiles[0]).keys())
    widths = [width * 0.34] + [width * 0.66 / len(cols)] * len(cols)
    data = [[Paragraph("Model", S["cellh"])] + [Paragraph(c, S["cellh"]) for c in cols]]
    data += [[Paragraph(inline(p["name"]), S["cell"])] + [Paragraph(inline(v), S["cellc"]) for v in chars(p).values()]
             for p in profiles]
    return grid_style(Table(data, colWidths=widths, hAlign="LEFT"))


def datasheet_story(unit, group, prices, first_in_group):
    hidden = {p["name"]: text_of(p).replace("\n", " ") for p in unit.get("profiles", []) if p.get("hidden")}
    stats, ranged, melee, seen = [], [], [], set()
    for node in walk(unit):
        for p in node.get("profiles", []):
            key = (p.get("typeName"), p["name"], tuple(chars(p).items()))
            if key in seen or p.get("hidden"):
                continue
            seen.add(key)
            {"Unit": stats, "Ranged Weapons": ranged, "Melee Weapons": melee}.get(p.get("typeName"), []).append(p)

    labels = {"LD": "Ld", "InSv": "InvSv"}
    stat_boxes = [(labels.get(k, k), v) for k, v in (chars(stats[0]) if stats else {}).items()]
    tiers = prices.get(unit["name"]) or (cost(unit, POINTS),)

    kw_text = hidden.get("Printed Keywords and Notes", "") + " " + hidden.get("CORE", "")
    km = re.search(r"Keywords:\s*(.+?)\.(?:\s|$)", kw_text)
    fm = re.search(r"Faction:\s*([^.]+)", kw_text)
    keywords = km.group(1).strip() if km else ", ".join(
        c["name"] for c in unit.get("categoryLinks", []) if not c["name"].startswith("Faction"))
    core_parts = sentences(re.sub(r"^Core:\s*", "", hidden.get("CORE", "")))
    core = core_parts[0].rstrip(".") if core_parts else ""
    core = re.sub(r"\s*Army rules:.*$", "", core).strip().rstrip(".")
    core_notes = [c for c in core_parts[1:]
                  if not re.match(r"(Leader|Support|Keywords|Baseline points|Army rules|Faction)\b", c)]
    extra = [(n, t) for n, t in hidden.items()
             if n not in {"Unit Composition and Equipment", "Equipment Options", "CORE", "Datasheet Notes",
                          "Printed Keywords and Notes", "Datasheet rules and equipment"} and t.strip()]

    left, right = [], []
    cm = re.match(r"Composition:\s*(.+?)\s*(?:Equipment:\s*(.+))?$", hidden.get("Unit Composition and Equipment", ""))
    if cm:
        comp = [p.strip() for p in re.split(r";\s*", cm.group(1).rstrip(".")) if p.strip()]
        if len(tiers) > 1:
            comp.append(f"Points: {tiers[0]}pts for the smaller unit or {tiers[1]}pts for the larger unit.")
        rep = repeat_cost(unit)
        if rep:
            comp.append(f"Repeat cost: +{rep[0]}pts for the {ordinal(rep[1])} and each later copy of this "
                        "datasheet.")
        left += [section_bar("Unit Composition", COL_W), Spacer(1, 4)] + bullets(comp)
        if cm.group(2):
            left += [Spacer(1, 3), section_bar("Each Model Is Equipped With", COL_W), Spacer(1, 4)]
            left += bullets(s.rstrip(".") for s in sentences(cm.group(2)))
    option_costs = OrderedDict.fromkeys(
        f"{n['name']} +{cost(n, POINTS)}pts" for n in walk(unit.get("selectionEntryGroups", []))
        if n.get("type") == "upgrade" and cost(n, POINTS) and not re.fullmatch(r"\d+ models?", n["name"].strip()))
    options = sentences(hidden.get("Equipment Options", ""))
    if options or option_costs:
        left += [Spacer(1, 3), section_bar("Wargear Options", COL_W), Spacer(1, 4)]
        left += bullets(list(options) + list(option_costs))
    if extra:
        left += [Spacer(1, 3), section_bar("Wargear", COL_W), Spacer(1, 4)]
        left += [Paragraph(f"<b>{inline(n)}.</b> {inline(t)}", S["body"]) for n, t in extra]
    if len({tuple(chars(p).values()) for p in stats}) > 1:
        left += [Spacer(1, 3), section_bar("Model Profiles", COL_W), Spacer(1, 4), profile_table(stats, COL_W),
                 Spacer(1, 6)]

    for profiles, label in ((ranged, "Ranged Weapons"), (melee, "Melee Weapons")):
        if profiles:
            right += [section_bar(label, COL_W), weapon_table(profiles, COL_W), Spacer(1, 6)]
    if hidden.get("Datasheet Notes"):
        right.append(Paragraph(inline(hidden["Datasheet Notes"]), S["note"]))

    right += [section_bar("Abilities", COL_W), Spacer(1, 4)]
    if core and core.lower() != "none":
        right.append(Paragraph(f"<b>Core.</b> {inline(core)}", S["body"]))
    right += [Paragraph(inline(n), S["body"]) for n in core_notes]
    army = list(OrderedDict.fromkeys(i["name"] for i in unit.get("infoLinks", []) if i["name"] in ARMY_RULES))
    if army:
        right.append(Paragraph(f"<b>Faction.</b> {inline(', '.join(army))}", S["body"]))
    for p in unit.get("profiles", []):
        if p.get("typeName") != "Abilities" or p.get("hidden"):
            continue
        flows = markup(text_of(p), COL_W)
        if p["name"] in {"Leader", "Support"}:
            left += [Spacer(1, 3), section_bar(p["name"], COL_W), Spacer(1, 4)] + flows
        elif flows and getattr(flows[0], "style", None) is S["body"]:
            right += [Paragraph(f"<b>{inline(p['name'])}.</b> {flows[0].text}", S["body"])] + flows[1:]
        else:
            right += [Paragraph(f"<b>{inline(p['name'])}.</b>", S["body"])] + flows

    head = [State(group, 0)] if first_in_group else []
    head.append(State(unit["name"], 1, kicker=group.upper(), title=unit["name"], subtitle=subtitle_of(unit),
                      points=" / ".join(str(t) for t in tiers) + "pts",
                      faction=fm.group(1).strip() if fm else "Emperor's Children",
                      stats=stat_boxes, keywords=keywords))
    return head + left + [FrameBreak()] + right


def points_story(grouped, prices):
    story = [State("References", 0), State("Points Reference", 1, kicker=f"{FACTION} REFERENCE",
                                           title="Points Reference"),
             Paragraph("This index lists the points for every datasheet in this volume. Unit sizes, repeat costs "
                       "and option costs are also shown on each datasheet.", S["body"])]
    for group, units in grouped.items():
        rows = [[Paragraph(h, S["pth"]) for h in ("ENTRY", "POINTS", "REPEAT COST")]]
        for u in units:
            tiers = prices.get(u["name"]) or (cost(u, POINTS),)
            rep = repeat_cost(u)
            rows.append([Paragraph(inline(u["name"]), S["pt"]),
                         Paragraph(" / ".join(f"{p}pts" for p in tiers), S["ptb"]),
                         Paragraph(f"+{rep[0]}pts from the {ordinal(rep[1])} copy" if rep else "–", S["pt"])])
        t = grid_style(Table(rows, colWidths=[TEXT_W * 0.5, TEXT_W * 0.22, TEXT_W * 0.28], repeatRows=1,
                             hAlign="LEFT"))
        t.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story += [CondPageBreak(110), section_bar(group, TEXT_W), t, Spacer(1, 10)]
    return story


# ---------------------------------------------------------------- assembly
def build(catalogue_path, out_path):
    cat = json.loads(Path(catalogue_path).read_text())["catalogue"]
    entries = cat["sharedSelectionEntries"]
    by_id = {e["id"]: e for e in entries}
    by_name = {e["name"]: e for e in entries}
    rules = {r["name"]: r for r in cat["sharedRules"]}
    prices = unit_prices()

    army_links = [l["name"] for l in by_name["Army Rules and References"].get("infoLinks", []) if l["name"] in rules]
    detachments = by_name["Detachment"]["selectionEntryGroups"][0]["selectionEntries"]
    det_ids = {d["id"]: d["name"] for d in detachments}
    enh_by_det = {d["name"]: [] for d in detachments}
    for enh in (e for e in entries if cost(e, ENHANCEMENT_SLOT)):
        for node in walk(entries):
            if node.get("targetId") == enh["id"]:
                blob = json.dumps(node)
                for i, n in det_ids.items():
                    if i in blob and enh not in enh_by_det[n]:
                        enh_by_det[n].append(enh)

    grouped = OrderedDict((g, []) for g in GROUPS)
    for link in cat["entryLinks"]:
        unit = by_id.get(link["targetId"])
        if unit and unit["type"] in {"unit", "model"}:
            grouped[group_of(unit, link.get("hidden"))].append(unit)
    grouped = OrderedDict((g, u) for g, u in grouped.items() if u)

    toc_groups = [("Army Rules", army_links), ("Detachments", [d["name"] for d in detachments])]
    toc_groups += [(g, [u["name"] for u in units]) for g, units in grouped.items()]
    toc_groups.append(("References", ["Points Reference"]))

    def story(toc_entries):
        s = [NextPageTemplate("section"), PageBreak(),
             State(None, kicker=f"CODEX: {FACTION}", title="Contents")]
        s += contents_story(toc_entries, toc_groups)
        s += [PageBreak()] + army_rules_story(army_links, rules)
        for i, det in enumerate(detachments):
            strats = [r for r in cat["sharedRules"] if r["name"].startswith(det["name"] + " — ")]
            s += [PageBreak()] + detachment_story(det, enh_by_det[det["name"]], strats, i == 0)
        s.append(NextPageTemplate("sheet"))
        for group, units in grouped.items():
            for i, unit in enumerate(units):
                s += [PageBreak()] + datasheet_story(unit, group, prices, i == 0)
        s += [NextPageTemplate("section"), PageBreak()] + points_story(grouped, prices)
        return s

    toc_entries = []
    for _ in range(2):  # pass 1 finds page numbers, pass 2 prints them in the contents
        doc = Codex(str(out_path), cat["revision"])
        doc.build(story(toc_entries))
        toc_entries = doc.entries
    return out_path


if __name__ == "__main__":
    catalogue = sys.argv[1] if len(sys.argv) > 1 else ROOT / "Chaos - Emperor's Children.json"
    output = sys.argv[2] if len(sys.argv) > 2 else ROOT / "homebrew" / "Emperors-Children-Codex-4.0.pdf"
    build(catalogue, output)
    print("Wrote", output)
