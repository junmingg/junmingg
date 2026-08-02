"""Renders dark_mode.svg / light_mode.svg for the GitHub profile README.

Single source of truth for both themes: edit portrait.txt or INFO below, then
run `python build.py`. The ASCII portrait itself comes from `portrait.py`.
Palette matches chenjunming.com (warm off-white / near-black, amber accent).
"""

import io
import json
from datetime import date
from xml.sax.saxutils import escape

ART = io.open("portrait.txt", encoding="utf-8").read().rstrip("\n").split("\n")
ART_COLS = max(len(line) for line in ART)

# portrait.txt is drawn for a light background (dense glyph = dark pixel). On a
# dark background the glyphs *are* the light part, so the ramp has to be
# mirrored or the hair glows and the face goes black.
# Not a plain mirror: a strict reversal renders the dark hair as '.' and it
# disappears into the background, so the dark end gets a floor of ':'.
RAMP = "@%#*+=-:."
INVERT = str.maketrans(RAMP, ":-=+*#%@@")

BIRTHDAY = date(1997, 2, 12)


def uptime(since):
    """neofetch-style '29 years, 5 months, and 21 days' — recomputed every build."""
    today = date.today()
    y = today.year - since.year - ((today.month, today.day) < (since.month, since.day))
    anniversary = date(since.year + y, since.month, since.day)
    m = (today.year - anniversary.year) * 12 + today.month - anniversary.month
    m -= today.day < anniversary.day
    d = (today - (date(anniversary.year + (anniversary.month + m - 1) // 12,
                       (anniversary.month + m - 1) % 12 + 1, anniversary.day))).days
    return f"{y} years, {m} months, and {d} days"


# Neofetch-style panel. Each entry is a (key, value) row, None for a blank line,
# or a one-element tuple for a section rule. A third element is raw tspan markup
# to render in place of the plain value.
INFO = [
    ("OS", "Windows 11, MacOS 26, Ubuntu 24.04"),
    ("Uptime", uptime(BIRTHDAY)),
    ("Host", "Modular Asset Management"),
    ("Kernel", "Software Engineer / AI Engineer"),
    ("IDE", "VSCode 1.127.0"),
    ("Terminal", "WezTerm"),
    ("Harness", "ClaudeCode, ZCode, Hermes Agent, OpenClaw"),
    None,
    ("Languages.Programming", "Python, R, Go, JavaScript"),
    ("Languages.Computer", "HTML, MD, CSS, JSON, LaTeX, YAML, XML"),
    ("Languages.Human", "English, Mandarin"),
    None,
    ("- Education",),
    ("Masters", "MSc Computer Science (AI), Georgia Institute of Technology"),
    ("Bachelors", "BSc Economics (DS&A), Singapore Management University"),
    ("Certs", "AWS SAA, AWS CCP, DeepLearning.AI (ML)"),
    None,
    ("- Contact",),
    ("Email.Personal", "chenjm246@gmail.com"),
    ("Email.Work", "j.chen@modularam.com"),
    ("LinkedIn", "jun-ming-chen"),
    ("Medium", "@junming-chen"),
]

# Written by stats.py; the section is skipped entirely when it is missing.
try:
    S = json.loads(io.open("stats.json", encoding="utf-8").read())
except FileNotFoundError:
    S = None

if S:
    net = S["loc_added"] - S["loc_deleted"]
    loc_plain = f"{net:,} ( {S['loc_added']:,}++, {S['loc_deleted']:,}-- )"
    loc_raw = (f'<tspan class="v">{net:,}</tspan> ( '
               f'<tspan class="add">{S["loc_added"]:,}++</tspan>, '
               f'<tspan class="del">{S["loc_deleted"]:,}--</tspan> )')
    INFO += [
        None,
        ("- GitHub Stats",),
        ("Repos", f"{S['repos']} {{Contributed: {S['contributed']}}}"),
        ("Commits", f"{S['commits']:,}"),
        ("Lines of Code", loc_plain, loc_raw),
    ]

HEADER = "junming@github"
TITLE = "junming@github: ~"
PROMPT = "~ $ ls -la ./credentials"
VALUE_COL = 30                     # column the values line up on
LINE_W = max(VALUE_COL + len(e[1]) for e in INFO if e and len(e) > 1)

THEMES = {
    "dark_mode.svg": dict(
        bg="#12100e", surface="#1a1815", bar="#211f1b", border="#35322c",
        fg="#e8e4dd", muted="#a29a90", accent="#e0a35c", art="#d9d3c9",
        dot1="#e0715c", dot2="#e0b45c", dot3="#7fb069", invert_art=True,
        value="#9fc9e8", cc="#57514a", plus="#6fbf73", minus="#e0715c",
    ),
    "light_mode.svg": dict(
        bg="#f2eee7", surface="#fbf9f5", bar="#efeae1", border="#e0d9cd",
        fg="#2b2622", muted="#6a6058", accent="#a4632a", art="#3a332c",
        dot1="#d0553f", dot2="#c9922f", dot3="#5d8f4e", invert_art=False,
        value="#2f6d99", cc="#b0a89b", plus="#3f8f45", minus="#c0432c",
    ),
}

CHAR_W = 8.43                      # advance width of the 14px body text
ART_FS = 8.0                       # small font = fine detail; SVG stays crisp zoomed in
ART_CW = ART_FS * 0.6
ART_LH = ART_CW * 2                # cells were generated at a 0.5 aspect ratio
BAR_H = 36
PAD = 26
ART_X = 34
ART_H = len(ART) * ART_LH
INFO_X = ART_X + ART_COLS * ART_CW + 30
INFO_LH = 21
INFO_H = (len(INFO) + 1) * INFO_LH   # + the header line
# whichever column is taller sets the height; centre the shorter one against it
BODY_H = max(ART_H, INFO_H)
ART_TOP = PAD + (BODY_H - ART_H) / 2
INFO_TOP = PAD + (BODY_H - INFO_H) / 2 + INFO_LH
W = round(INFO_X + LINE_W * CHAR_W + 34)
H = round(BAR_H + PAD + BODY_H + 46)


def rule(title):
    """'<title> -——————…——-—-' padded out to the panel width."""
    dashes = max(4, LINE_W - len(title) - 1)
    return (f'<tspan class="hdr">{escape(title)}</tspan>'
            f'<tspan class="cc"> -{"—" * (dashes - 4)}-—-</tspan>')


def row(key, value, raw=None):
    """'. key: ......... value' with the values aligned on VALUE_COL."""
    dots = max(1, VALUE_COL - len(key) - 5)
    parts = ['<tspan class="cc">. </tspan>']
    for i, seg in enumerate(key.split(".")):        # Languages.Programming
        if i:
            parts.append('<tspan class="cc">.</tspan>')
        parts.append(f'<tspan class="k">{escape(seg)}</tspan>')
    parts.append(f'<tspan class="cc">: {"." * dots} </tspan>')
    parts.append(raw or f'<tspan class="v">{escape(value)}</tspan>')
    return "".join(parts)


def text(x, y, cls, body):
    return (
        f'<text x="{x:.0f}" y="{y:.1f}" class="{cls}" '
        f'xml:space="preserve">{body}</text>'
    )


def render(theme):
    rows = []
    for i, line in enumerate(ART):
        if theme["invert_art"]:
            line = line.translate(INVERT)
        rows.append(text(ART_X, BAR_H + ART_TOP + i * ART_LH, "art", escape(line)))

    y = BAR_H + INFO_TOP
    rows.append(text(INFO_X, y, "row", rule(HEADER)))
    for entry in INFO:
        y += INFO_LH
        if entry is None:
            continue
        body = rule(entry[0]) if len(entry) == 1 else row(*entry)
        rows.append(text(INFO_X, y, "row", body))

    py = H - 26
    prompt = text(ART_X, py, "row",
                  f'<tspan class="k">{escape(PROMPT)} </tspan>')
    cursor = (
        f'<rect x="{ART_X + len(PROMPT) * CHAR_W + CHAR_W:.0f}" y="{py - 11:.0f}" '
        f'width="8" height="14" fill="{theme["accent"]}">'
        f'<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" '
        f'repeatCount="indefinite"/></rect>'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Chen Jun Ming - AI/ML Engineer">
  <style>
    text {{ font-family: ui-monospace, "SF Mono", "JetBrains Mono", "DejaVu Sans Mono", Menlo, Consolas, monospace; font-size: 14px; }}
    .art {{ fill: {theme["art"]}; font-size: {ART_FS}px; letter-spacing: 0; }}
    .hdr {{ fill: {theme["accent"]}; font-weight: 700; }}
    .k {{ fill: {theme["accent"]}; }}
    .v {{ fill: {theme["value"]}; }}
    .cc {{ fill: {theme["cc"]}; }}
    .add {{ fill: {theme["plus"]}; }}
    .del {{ fill: {theme["minus"]}; }}
    .title {{ fill: {theme["muted"]}; font-size: 12px; }}
  </style>
  <rect width="{W}" height="{H}" rx="12" fill="{theme["bg"]}"/>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="11" fill="{theme["surface"]}" stroke="{theme["border"]}"/>
  <path d="M1 13a12 12 0 0 1 12-12h{W - 26}a12 12 0 0 1 12 12v{BAR_H - 13}H1z" fill="{theme["bar"]}"/>
  <line x1="1" y1="{BAR_H}" x2="{W - 1}" y2="{BAR_H}" stroke="{theme["border"]}"/>
  <circle cx="22" cy="18" r="5" fill="{theme["dot1"]}"/>
  <circle cx="40" cy="18" r="5" fill="{theme["dot2"]}"/>
  <circle cx="58" cy="18" r="5" fill="{theme["dot3"]}"/>
  <text x="{W / 2:.0f}" y="23" class="title" text-anchor="middle">{escape(TITLE)}</text>
{chr(10).join("  " + r for r in rows)}
  {prompt}
  {cursor}
</svg>
'''


for filename, theme in THEMES.items():
    with open(filename, "w", encoding="utf-8") as fh:
        fh.write(render(theme))
    print("wrote", filename)
