"""House weapon standard: 11th-edition codex D3 damage and fixed attacks (used for Black-Flag and Covenant).

Follows the 11e codex profiles (lascannon D3+3, multi-melta and melta rifle D3+2, krak missile D3+3, flamers and frag
weapons with a fixed A and [BLAST X]) and the Skaven rule for S16+ guns, which hit harder than a D6 conversion.

Damage
    D3, D3+X        unchanged
    D6              D3+2 (D3+3 at S12+)
    D6+1            D3+3
    D6+2            D3+4
    D6+3            D3+5
    D6+4            D3+6
    D6+6            D3+8
    2D6             D3+5
    S16+ guns       D6 to D6+2 -> D3+6; D6+3 or D6+4 -> D3+8; D6+6 -> D3+10
Attacks (random -> fixed, the average rounded down)
    D3 2, D3+1 3, D3+2 4, D3+3 5, 2D3 4, D6 3, D6+1 4, D6+2 5, D6+3 6, D6+6 9, 2D6 7
    [TORRENT]       D6 -> 3, D6+X -> 4 (as the codex flamers)
    [BLAST]         becomes [BLAST 1], or [BLAST 2] from 6 attacks
    [TORRENT] weapons that are not pistols gain [BLAST 1] ([BLAST 2] if they had D6+X attacks)
Space Marine equivalents (11e codex S and AP)
    Meltagun        S10 AP-3 D3+2
    Krak missile    S10 AP-2 D3+3
"""
import re

FIXED_ATTACKS = {"D3": 2, "D3+1": 3, "D3+2": 4, "D3+3": 5, "2D3": 4, "D6": 3, "D6+1": 4, "D6+2": 5, "D6+3": 6,
                 "D6+4": 7, "D6+6": 9, "2D6": 7}
DAMAGE = {"D6": "D3+2", "D6+1": "D3+3", "D6+2": "D3+4", "D6+3": "D3+5", "D6+4": "D3+6", "D6+6": "D3+8",
          "2D6": "D3+5"}
BIG_DAMAGE = {"D6": "D3+6", "D6+1": "D3+6", "D6+2": "D3+6", "D6+3": "D3+8", "D6+4": "D3+8", "D6+6": "D3+10",
              "2D6": "D3+8"}
SM_EQUIVALENTS = {
    "meltagun": dict(S="10", AP="-3", D="D3+2"),
    "missile launcher - krak": dict(S="10", AP="-2", D="D3+3"),
    "havoc missile launcher - krak": dict(S="10", AP="-2", D="D3+3"),
}


def _strength(s):
    m = re.match(r"\d+", str(s))
    return int(m.group(0)) if m else 0


def _has(keywords, name):
    return any(re.match(rf"^\[?{re.escape(name)}\b", k, re.I) for k in keywords)


def convert(name, profile, keywords):
    """profile: dict with A, S, AP, D (strings); keywords: list of strings. Returns (profile, keywords, changes)."""
    profile, keywords, changes = dict(profile), list(keywords), []
    key = re.sub(r"^\W+", "", name).strip().lower()
    for field, value in SM_EQUIVALENTS.get(key, {}).items():
        if profile.get(field) != value:
            changes.append(f"{field} {profile.get(field)} -> {value}")
            profile[field] = value
    d = str(profile.get("D", "")).replace(" ", "").upper()
    if d in DAMAGE and key not in SM_EQUIVALENTS:
        big = _strength(profile.get("S")) >= 16
        new = BIG_DAMAGE[d] if big else ("D3+3" if d == "D6" and _strength(profile.get("S")) >= 12 else DAMAGE[d])
        changes.append(f"D {d} -> {new}")
        profile["D"] = new
    for i, k in enumerate(keywords):  # Plasma (D6): the critical-hit bonus follows the same rule
        m = re.match(r"^(Plasma \()(D6(?:\+\d)?)(\))$", k)
        if m:
            keywords[i] = m.group(1) + DAMAGE[m.group(2)] + m.group(3)
            changes.append(f"{k} -> {keywords[i]}")
    a = str(profile.get("A", "")).replace(" ", "").upper()
    if a in FIXED_ATTACKS:
        torrent, pistol = _has(keywords, "Torrent"), _has(keywords, "Pistol")
        fixed = (3 if a == "D6" else 4) if torrent and a.startswith("D6") else FIXED_ATTACKS[a]
        changes.append(f"A {a} -> {fixed}")
        profile["A"] = str(fixed)
        blast_n = 2 if fixed >= 6 or (torrent and a.startswith("D6+")) else 1
        for i, k in enumerate(keywords):
            if re.fullmatch(r"\[?Blast\]?", k, re.I):
                keywords[i] = f"Blast {blast_n}"
                changes.append(f"Blast -> Blast {blast_n}")
        if torrent and not pistol and not _has(keywords, "Blast"):
            keywords.append(f"Blast {blast_n}")
            changes.append(f"+Blast {blast_n}")
    return profile, keywords, changes
