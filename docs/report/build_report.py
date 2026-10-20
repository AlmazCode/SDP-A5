"""Build the Assignment 5 PDF plus editable vector diagrams.

Run from any directory with Python 3, reportlab and pypdf installed.
Run `mvn clean verify` in the repository first to refresh test evidence.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
import math
import re

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Rect, Line, PolyLine, Polygon, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/pdf/SDP_Assignment_5_Sabirzhanov_Emil.pdf"
ASSETS = ROOT / "docs/report"
UML = ROOT / "docs/strategy"
W = A4[0] - 144
INK = colors.HexColor("#20242A")
GRAY = colors.HexColor("#5D6268")
PALE = colors.HexColor("#F2F3F5")
BLUE = colors.HexColor("#235A8A")
pdfmetrics.registerFont(TTFont("Montserrat", str(ASSETS / "Montserrat-Medium.ttf")))
pdfmetrics.registerFont(TTFont("Helvetica", str(ASSETS / "LiberationSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Helvetica-Bold", str(ASSETS / "LiberationSans-Bold.ttf")))
pdfmetrics.registerFontFamily("Helvetica", normal="Helvetica", bold="Helvetica-Bold",
                             italic="Helvetica", boldItalic="Helvetica-Bold")
pdfmetrics.registerFont(TTFont("Courier", str(ASSETS / "LiberationMono-Regular.ttf")))

styles = {
    "title": ParagraphStyle("title", fontName="Montserrat", fontSize=25, leading=31,
                            alignment=TA_CENTER, spaceAfter=5, textColor=INK),
    "subtitle": ParagraphStyle("subtitle", fontName="Montserrat", fontSize=15, leading=20,
                               alignment=TA_CENTER, spaceAfter=5, textColor=GRAY),
    "author": ParagraphStyle("author", fontName="Montserrat", fontSize=10.5, leading=15,
                             alignment=TA_CENTER, spaceAfter=16),
    "h1": ParagraphStyle("h1", fontName="Montserrat", fontSize=18, leading=23,
                         alignment=TA_CENTER, spaceAfter=12, textColor=INK),
    "h2": ParagraphStyle("h2", fontName="Montserrat", fontSize=12, leading=16,
                         spaceBefore=10, spaceAfter=6, textColor=INK),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10.5, leading=14,
                           spaceAfter=8, textColor=INK),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=9, leading=12,
                            spaceAfter=7, textColor=INK),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=9, leading=11.5,
                           textColor=INK),
    "cellsmall": ParagraphStyle("cellsmall", fontName="Helvetica", fontSize=8.6, leading=11,
                                textColor=INK),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.6, leading=12,
                           backColor=PALE, borderPadding=7, spaceBefore=5, spaceAfter=12),
}
story = []


def p(text, style="body"):
    story.append(Paragraph(text, styles[style]))


def table(rows, widths, compact=False):
    style = styles["cellsmall" if compact else "cell"]
    cells = [[Paragraph(str(cell), style) for cell in row] for row in rows]
    t = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), .6, colors.HexColor("#9AA0A6")),
        ("LINEBELOW", (0, 1), (-1, -1), .3, colors.HexColor("#D9DCE0")),
    ]))
    story.extend([t, Spacer(1, 8)])


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


def break_page():
    story.append(PageBreak())


def link(url, label):
    return f'<link href="{url}" color="#235A8A"><u>{escape(label)}</u></link>'


readme = (ROOT / "README.md").read_text()
reports = [ET.parse(path).getroot() for path in (ROOT / "target/surefire-reports").glob("TEST-*.xml")]
assert reports, "Run mvn clean verify before generating the report."
stats = {key: sum(int(r.attrib.get(key, 0)) for r in reports)
         for key in ["tests", "failures", "errors", "skipped"]}
assert stats == {"tests": 62, "failures": 0, "errors": 0, "skipped": 0}, stats
coverage = ET.parse(ROOT / "target/site/jacoco/jacoco.xml").getroot()
for package in ["matchmaking/strategy/player", "matchmaking/strategy/server"]:
    counter = coverage.find(f"package[@name='{package}']/counter[@type='LINE']")
    assert counter is not None and counter.attrib["missed"] == "0"

# PAGE 1
p("Software Design Patterns", "title")
p("Assignment 5", "subtitle")
p("by Sabirzhanov Emil, SE-2533", "author")
p("Player Matching Class Diagram", "h1")
p("The video game matchmaking project uses two Strategy families: selecting a player "
  "and selecting a server. Each family has one interface, three concrete algorithms, "
  "a replaceable context and a separate selector.")
diagram(player_uml(), "player-matching")
p("Dashed lines with hollow triangles denote interface realization. Solid arrows denote "
  "held references; dashed open arrows denote creation dependencies. UML method parameters "
  "are abbreviated outside the strategy interface.", "small")
table([
    ["<b>Concrete strategy</b>", "<b>Selection logic</b>"],
    ["SkillBasedMatching", "Smallest absolute rating gap."],
    ["LongestWaitingMatching", "Longest waiting time among eligible candidates."],
    ["ComplementaryRoleMatching", "Different role first; smallest rating gap second."],
], [173, W - 173])
p("<b>Shared contract.</b> <font face='Courier'>PlayerPool</font> excludes the seeker "
  "and rating gaps above 300. Ratings range from 0 to 5000. Ties keep the first candidate. "
  "No suitable player produces <font face='Courier'>Optional.empty()</font>. "
  "The algorithms select one player; they do not implement sorting algorithms.", "small")

# PAGE 2
break_page()
p("Server Selection Class Diagram", "h1")
p("Server policies share one selection contract but optimize different criteria. "
  "The load-aware policy obtains external measurements through our own interface.")
diagram(server_uml(), "server-selection")
table([
    ["<b>Concrete strategy</b>", "<b>Selection logic</b>"],
    ["LowLatencyServer", "Lowest latency among eligible servers."],
    ["LeastLoadedServer", "Lowest measured utilization below 100%."],
    ["RegionalServer", "Preferred region first; lowest latency second."],
], [173, W - 173])
p("<b>Isolation from change.</b> <font face='Courier'>ServerLoadSource</font> hides the "
  "measurement source. The demo injects a simulated map; tests inject fixed fake readings. "
  "Replacing it with a monitoring adapter requires no change to the strategy or context. "
  "Each call reads every eligible server once and refreshes readings on the next call.", "small")
p("<b>Shared contract.</b> <font face='Courier'>ServerPool</font> excludes latency above 100 ms. "
  "Empty pools return an empty optional. Only the load policy checks utilization; full servers "
  "are excluded, unknown simulated servers count as full, invalid percentages are rejected.", "small")

# PAGE 3
break_page()
p("Selection and Runtime Switching", "h1")
p("Selectors evaluate rules in the following priority order. Only selectors branch on "
  "which strategy to construct; contexts simply delegate through an interface.", "small")
table([
    ["<b>Family</b>", "<b>First matching situation</b>", "<b>Policy</b>"],
    ["Player", "1. Ranked match", "Skill"],
    ["Player", "2. Casual; seeker waited at least 120 s", "Longest waiting"],
    ["Player", "3. Casual team match; shorter wait", "Complementary role"],
    ["Player", "4. Remaining situations", "Skill"],
    ["Server", "1. Competitive match", "Low latency"],
    ["Server", "2. Noncompetitive; demand at least 80%", "Least loaded"],
    ["Server", "3. Remaining situations", "Regional"],
], [49, 258, W - 307], compact=True)
diagram(runtime_sequence(), "runtime-selection")
p("Manual selection uses <font face='Courier'>manual(Mode)</font>. Automatic selection uses "
  "<font face='Courier'>automatic(...)</font>. Both return an interface implementation. "
  "The same context accepts the returned object through <font face='Courier'>setStrategy()</font>.", "small")
p("<b>Fixed demo inputs.</b> Seeker: rating 1000, tank, waited 30 s. Candidates: "
  "close (1010, tank, 10 s), waiting (1200, tank, 180 s), support (1100, healer, 50 s). "
  "Preferred region: KZ. Servers: fast (EU, 20 ms, 90% load), free (US, 70 ms, 10%), "
  "local (KZ, 40 ms, 50%).", "small")
table([
    ["<b>Demonstration</b>", "<b>Player result</b>", "<b>Server result</b>"],
    ["Same input, all algorithms", "Skill: close<br/>Waiting: waiting<br/>Role: support",
     "Latency: fast<br/>Load: free<br/>Region: local"],
    ["Manual choice", "Skill: close", "Latency: fast"],
    ["Runtime switch", "close -&gt; waiting", "fast -&gt; free"],
    ["Automatic: casual team, 30 s, 90% demand", "Role: support", "Load: free"],
], [190, 125, W - 315], compact=True)
p("The automatic result enters the existing Facade with ratings 1000/1100 and latency 70 ms. "
  "The saved match reaches COMPLETED. Candidate IDs are shown in the demo; the existing "
  "CSV schema stores ratings and latency.", "small")

# PAGE 4
break_page()
p("Design Rationale and Verification", "h1")
rationale = readme.split("### Why Strategy, not State or Template Method\n\n")[1].split(
    "\n### Before and after refactoring")[0]
for paragraph in rationale.strip().split("\n\n"):
    text = re.sub(r"`([^`]+)`", r"\1", paragraph.replace("\n", " "))
    p(escape(text), "small")
p("Refactoring with Git History", "h2")
repo = "https://github.com/AlmazCode/SDP-A5"
before = "ebfded42276c855ed7cb6cb623ed048ae08d482e"
after = "bfb4c782c1d61c1c203c66eb49e4489c6f464458"
p(link(f"{repo}/commit/{before}", "Before: ebfded4") +
  " places all player algorithms in one ConditionalPlayerMatching switch. " +
  link(f"{repo}/commit/{after}", "After: bfb4c78") +
  " extracts three strategies. PlayerStrategyTest is unchanged; all 42 tests present at "
  "that stage pass in clean snapshots of both commits.", "small")
p("JUnit 5 Results", "h2")
table([
    ["<b>Test suite</b>", "<b>Cases</b>", "<b>Evidence</b>"],
    ["PlayerStrategyTest", "15", "Three algorithms, every selector rule, boundaries, runtime replacement."],
    ["ServerStrategyTest", "18", "Three algorithms, every rule, fake source, refreshed readings, full servers."],
    ["StrategyDemoTest", "2", "Console results plus a persisted completed match through the Facade."],
    ["Existing Assignment 4 tests", "27", "Facade behavior, recovery, subsystem validation, console input."],
], [151, 46, W - 197], compact=True)
p("<b>62 tests passed; zero failures, errors or skipped cases.</b> Both families have a "
  "<font face='Courier'>@ParameterizedTest</font> eligibility check over all three policies. Each strategy package has 100% "
  "line coverage; JaCoCo enforces at least 80% per package. Verification: 20 October 2026.", "small")
p("<font face='Courier'>./run-strategy.sh</font> runs the demo. "
  "<font face='Courier'>mvn clean verify</font> runs the complete test suite.", "small")
p("<b>GitHub Repository:</b> " + link(repo, repo), "small")

# PAGE 5
break_page()
p("Class Responsibilities", "h1")
p("Assignment 5 production types are listed below. Each responsibility is one sentence "
  "of at most 25 words, without the conjunctions prohibited by the assignment.", "small")
section = readme.split("### Class responsibilities")[1].split("### Why Strategy")[0]
rows = [["<b>Type</b>", "<b>Single responsibility</b>"]]
for line in section.splitlines():
    if line.startswith("| `"):
        name, responsibility = [part.strip() for part in line.split("|")[1:3]]
        name = name.strip("`")
        assert len(responsibility.split()) <= 25
        assert not re.search(r"\b(if|and|or|but)\b", responsibility, re.I)
        # Nested enum names wrap at the dot rather than inside class names.
        name = name.replace(".Mode", ".<br/>Mode")
        rows.append([name, escape(responsibility)])
assert len(rows) == 22
table(rows, [170, W - 170], compact=True)
p("Live Coding Extension Points", "h2")
p("Add a strategy by implementing the family interface and injecting it with "
  "<font face='Courier'>setStrategy()</font>. Change automatic behavior in the selector. "
  "Replace utilization data by supplying another <font face='Courier'>ServerLoadSource</font>. "
  "Existing contexts and algorithms remain unchanged when a new strategy is injected directly.", "small")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(A4[0] / 2, 35, str(doc.page))
    canvas.restoreState()


OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=72, rightMargin=72,
                        topMargin=52, bottomMargin=52,
                        title="Software Design Patterns - Assignment 5 - Strategy Pattern",
                        author="Sabirzhanov Emil", subject="Video game matchmaking with two Strategy families")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(OUT)
assert len(reader.pages) == 5, f"Expected 5 pages; found {len(reader.pages)}"
text = "\n".join(page.extract_text() for page in reader.pages)
for required in ["PlayerMatchingStrategy", "ServerSelectionStrategy", "ServerLoadSource",
                 "setStrategy", "Template Method", "ebfded4", "bfb4c78", "62 tests"]:
    assert required in text, required
print(f"Created {OUT} ({len(reader.pages)} pages)")
