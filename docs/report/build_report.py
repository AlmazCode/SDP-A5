"""Build the Assignment 5 PDF plus editable vector diagrams.

Run from any directory with Python 3, reportlab and pypdf installed.
"""
from pathlib import Path
import math

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Rect, Line, PolyLine, Polygon, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/pdf/SDP_Assignment_5_Sabirzhanov_Emil.pdf"
ASSETS = ROOT / "docs/report"
UML = ROOT / "docs/strategy"
W = A4[0] - 144
INK = colors.HexColor("#20242A")
GRAY = colors.HexColor("#5D6268")
PALE = colors.HexColor("#F2F3F5")
pdfmetrics.registerFont(TTFont("Montserrat", str(ASSETS / "Montserrat-Medium.ttf")))
pdfmetrics.registerFont(TTFont("Helvetica", str(ASSETS / "LiberationSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Helvetica-Bold", str(ASSETS / "LiberationSans-Bold.ttf")))
pdfmetrics.registerFontFamily("Helvetica", normal="Helvetica", bold="Helvetica-Bold",
                             italic="Helvetica", boldItalic="Helvetica-Bold")

heading = ParagraphStyle("heading", fontName="Montserrat", fontSize=18, leading=23,
                         alignment=TA_CENTER, spaceAfter=18, textColor=INK)
title = ParagraphStyle("title", fontName="Montserrat", fontSize=25, leading=31,
                       alignment=TA_CENTER, spaceAfter=5, textColor=INK)
subtitle = ParagraphStyle("subtitle", fontName="Montserrat", fontSize=15, leading=20,
                          alignment=TA_CENTER, spaceAfter=5, textColor=GRAY)
author = ParagraphStyle("author", fontName="Montserrat", fontSize=10.5, leading=15,
                        alignment=TA_CENTER, spaceAfter=14, textColor=INK)
links = ParagraphStyle("links", fontName="Helvetica", fontSize=10, leading=15,
                       alignment=TA_CENTER, spaceAfter=8, textColor=INK)
story = []


def txt(d, x, y, text, size=8.4, anchor="start", font="Helvetica", fill=INK):
    d.add(String(x, y, text, fontName=font, fontSize=size, textAnchor=anchor, fillColor=fill))


def box(d, x, y, width, height, title, lines=(), stereotype=None, font_size=8.4):
    d.add(Rect(x, y, width, height, fillColor=colors.white, strokeColor=None))
    header = 35 if stereotype else 23
    d.add(Rect(x, y + height - header, width, header, fillColor=PALE, strokeColor=None))
    d.add(Rect(x, y, width, height, fillColor=None, strokeColor=INK, strokeWidth=.7))
    if stereotype:
        txt(d, x + width / 2, y + height - 12, f"<<{stereotype}>>", 7.7, "middle")
    title_y = y + height - (26 if stereotype else 15)
    assert pdfmetrics.stringWidth(title, "Helvetica-Bold", font_size) <= width - 6, title
    txt(d, x + width / 2, title_y, title, font_size, "middle", "Helvetica-Bold")
    d.add(Line(x, y + height - header, x + width, y + height - header, strokeColor=INK, strokeWidth=.6))
    for i, line in enumerate(lines):
        assert pdfmetrics.stringWidth(line, "Helvetica", font_size) <= width - 10, line
        txt(d, x + 5, y + height - header - 13 - 11 * i, line, font_size)


def arrow(d, points, dashed=False, realization=False):
    flat = [n for pt in points for n in pt]
    d.add(PolyLine(flat, strokeColor=INK, strokeWidth=.7,
                   strokeDashArray=[3, 2] if dashed else None, fillColor=None))
    x, y = points[-1]
    px, py = points[-2]
    angle = math.atan2(y - py, x - px)
    size = 7 if realization else 5
    dx, dy = math.cos(angle), math.sin(angle)
    left = (x - size * dx - size * .5 * dy, y - size * dy + size * .5 * dx)
    right = (x - size * dx + size * .5 * dy, y - size * dy - size * .5 * dx)
    if realization:
        d.add(Polygon([x, y, *left, *right], strokeColor=INK, strokeWidth=.7, fillColor=colors.white))
    else:
        d.add(PolyLine([*left, x, y, *right], strokeColor=INK, strokeWidth=.7, fillColor=None))


def player_uml():
    d = Drawing(W, 285)
    box(d, 0, 204, 190, 69, "PlayerStrategySelector",
        ["+ manual(mode): strategy", "+ automatic(ranked, wait, team)"])
    box(d, 230, 182, W - 230, 91, "PlayerMatchingContext",
        ["- strategy: PlayerMatchingStrategy", "+ PlayerMatchingContext(strategy)",
         "+ setStrategy(strategy): void", "+ select(pool): Optional<Player>"])
    box(d, 100, 92, 251, 59, "PlayerMatchingStrategy",
        ["+ select(pool: PlayerPool): Optional<Player>"], "interface")
    arrow(d, [(95, 204), (95, 167), (145, 167), (145, 151)], dashed=True)
    txt(d, 6, 178, "creates a concrete policy", 8)
    arrow(d, [(341, 182), (341, 167), (300, 167), (300, 151)])
    txt(d, 349, 163, "holds 1", 8)
    names = ["SkillBasedMatching", "LongestWaitingMatching", "ComplementaryRoleMatching"]
    for i, name in enumerate(names):
        x = i * 154
        box(d, x, 9, 143, 48, name, ["+ select(pool)"], font_size=8.1)
        arrow(d, [(x + 71.5, 57), (x + 71.5, 74), (151 + i * 75, 74), (151 + i * 75, 92)],
              dashed=True, realization=True)
    return d


def server_uml():
    d = Drawing(W, 376)
    box(d, 0, 296, 190, 70, "ServerStrategySelector",
        ["- loads: ServerLoadSource", "+ manual(mode) / automatic(...)"])
    box(d, 230, 274, W - 230, 92, "ServerSelectionContext",
        ["- strategy: ServerSelectionStrategy", "+ ServerSelectionContext(strategy)",
         "+ setStrategy(strategy): void", "+ select(pool): Optional<ServerCandidate>"], font_size=8)
    box(d, 88, 189, 275, 59, "ServerSelectionStrategy",
        ["+ select(pool: ServerPool): Optional<ServerCandidate>"], "interface", font_size=8)
    arrow(d, [(95, 296), (95, 266), (140, 266), (140, 248)], dashed=True)
    txt(d, 5, 277, "creates a concrete policy", 8)
    arrow(d, [(341, 274), (341, 261), (310, 261), (310, 248)])
    txt(d, 350, 258, "holds 1", 8)
    names = ["LowLatencyServer", "LeastLoadedServer", "RegionalServer"]
    for i, name in enumerate(names):
        x = i * 154
        lines = ["+ select(pool)"] if i != 1 else ["- loads: ServerLoadSource", "+ select(pool)"]
        box(d, x, 93, 143, 59, name, lines, font_size=8)
        arrow(d, [(x + 71.5, 152), (x + 71.5, 169), (151 + i * 75, 169), (151 + i * 75, 189)],
              dashed=True, realization=True)
    box(d, 0, 0, 226, 59, "ServerLoadSource",
        ["+ utilizationPercent(serverId: String): int"], "interface", font_size=8)
    box(d, 260, 0, W - 260, 59, "SimulatedServerLoadSource",
        ["- loads: Map<String, Integer>", "+ utilizationPercent(serverId): int"], font_size=8)
    arrow(d, [(225, 93), (225, 76), (145, 76), (145, 59)])
    txt(d, 6, 72, "injected data source", 8)
    arrow(d, [(260, 29), (226, 29)], dashed=True, realization=True)
    return d


def runtime_sequence():
    d = Drawing(W, 188)
    xs = [28, 153, 287, 422]
    labels = ["Client", "Selector", "Context", "Strategy"]
    for x, label in zip(xs, labels):
        txt(d, x, 177, label, 8.7, "middle", "Helvetica-Bold")
        d.add(Line(x, 6, x, 167, strokeColor=GRAY, strokeWidth=.5, strokeDashArray=[3, 3]))
    events = [
        (0, 1, 150, "automatic(situation)"),
        (1, 0, 128, "chosen strategy", True),
        (0, 2, 106, "setStrategy(chosen)"),
        (0, 2, 84, "select(same input)"),
        (2, 3, 62, "select(input)"),
        (3, 2, 40, "candidate", True),
        (2, 0, 18, "selected candidate", True),
    ]
    for source, dest, y, label, *rest in events:
        arrow(d, [(xs[source], y), (xs[dest], y)], dashed=bool(rest))
        txt(d, (xs[source] + xs[dest]) / 2, y + 4, label, 8, "middle")
    return d


def diagram(d, name):
    UML.mkdir(parents=True, exist_ok=True)
    renderSVG.drawToFile(d, str(UML / f"{name}.svg"))
    story.extend([d, Spacer(1, 7)])


story.append(Paragraph("Software Design Patterns", title))
story.append(Paragraph("Assignment 5", subtitle))
story.append(Paragraph("by Sabirzhanov Emil, SE-2533", author))
story.append(Paragraph("Player Matching Class Diagram", heading))
diagram(player_uml(), "player-matching")
story.append(Spacer(1, 18))
story.append(Paragraph("Runtime Selection Sequence Diagram", heading))
diagram(runtime_sequence(), "runtime-selection")
story.append(PageBreak())
story.append(Paragraph("Server Selection Class Diagram", heading))
diagram(server_uml(), "server-selection")
story.append(Spacer(1, 24))
story.append(Paragraph("GitHub Repository", heading))
repo = "https://github.com/AlmazCode/SDP-A5"
references = [
    (repo, repo),
]
for url, label in references:
    story.append(Paragraph(f'<link href="{url}" color="#235A8A"><u>{label}</u></link>', links))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(A4[0] / 2, 35, str(doc.page))
    canvas.restoreState()


OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=72, rightMargin=72,
                        topMargin=52, bottomMargin=52,
                        title="Assignment 5 - Strategy UML Diagrams",
                        author="Sabirzhanov Emil", subject="Video game matchmaking with two Strategy families")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == 2, f"Expected 2 pages; found {len(reader.pages)}"
text = "\n".join(page.extract_text() for page in reader.pages)
for required in ["PlayerMatchingStrategy", "ServerSelectionStrategy", "ServerLoadSource",
                 "setStrategy", "Runtime Selection Sequence Diagram", "Software Design Patterns",
                 "Assignment 5", "Sabirzhanov Emil, SE-2533", repo]:
    assert required in text, required
assert "Before refactoring" not in text and "After refactoring" not in text
actual_links = [
    ref.get_object().get("/A", {}).get("/URI")
    for page in reader.pages for ref in page.get("/Annots", [])
]
assert set(actual_links) == {url for url, _ in references}
print(f"Created {OUT} ({len(reader.pages)} pages)")
