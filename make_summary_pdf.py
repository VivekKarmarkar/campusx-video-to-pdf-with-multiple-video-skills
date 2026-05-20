"""Hand-authored MCP summary PDF.

Distills Nitish's 52-minute CampusX lecture into an engaging, accessible
summary written in Claude's voice — frames are embedded as figures ONLY where
they earn the space (diagrams, code, config — never title cards).

Output: summary.pdf
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

CWD = Path.cwd()
FRAMES = CWD / "frames"


# --- Style palette ---
INK = HexColor("#1a1a1a")
MUTED = HexColor("#5a5a5a")
ACCENT = HexColor("#0b5fae")  # CampusX blue-ish
RULE = HexColor("#d9d9d9")
CALLOUT_BG = HexColor("#f4f7fb")
CALLOUT_BORDER = HexColor("#cfdcec")


def styles():
    s = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=s["Title"], fontSize=26, leading=32,
                                textColor=INK, spaceAfter=4),
        "subtitle": ParagraphStyle("st", parent=s["Normal"], fontSize=13,
                                   leading=17, textColor=MUTED, spaceAfter=2),
        "byline": ParagraphStyle("by", parent=s["Normal"], fontSize=10,
                                 leading=14, textColor=MUTED, spaceAfter=14),
        "tldr_h": ParagraphStyle("tldr_h", parent=s["Heading3"], fontSize=11,
                                 leading=14, textColor=ACCENT, spaceAfter=4),
        "tldr": ParagraphStyle("tldr", parent=s["BodyText"], fontSize=11,
                               leading=16, textColor=INK, spaceAfter=4,
                               leftIndent=8, rightIndent=8),
        "h1": ParagraphStyle("h1", parent=s["Heading1"], fontSize=18,
                             leading=22, textColor=ACCENT, spaceBefore=18,
                             spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=s["Heading2"], fontSize=13.5,
                             leading=18, textColor=INK, spaceBefore=12,
                             spaceAfter=4),
        "body": ParagraphStyle("body", parent=s["BodyText"], fontSize=11,
                               leading=16.5, textColor=INK, spaceAfter=10,
                               alignment=0),
        "caption": ParagraphStyle("cap", parent=s["Italic"], fontSize=9,
                                  leading=12, textColor=MUTED, spaceAfter=14,
                                  alignment=1),
        "pullquote": ParagraphStyle("pq", parent=s["Italic"], fontSize=12,
                                    leading=18, textColor=ACCENT,
                                    leftIndent=24, rightIndent=24,
                                    spaceBefore=6, spaceAfter=12),
        "footer": ParagraphStyle("f", parent=s["Normal"], fontSize=8.5,
                                 leading=11, textColor=MUTED, alignment=1,
                                 spaceBefore=6),
    }


def figure(path: Path, caption: str, st: dict, max_w: float = 5.4 * inch,
           max_h: float = 3.4 * inch):
    """Layout-friendly figure: image fit-to-box + caption, kept together."""
    with PILImage.open(path) as img:
        iw, ih = img.size
    scale = min(max_w / iw, max_h / ih)
    img_flow = Image(str(path), width=iw * scale, height=ih * scale)
    img_flow.hAlign = "CENTER"
    return KeepTogether([img_flow, Paragraph(caption, st["caption"])])


def callout(text: str, st: dict):
    """Light blue box with a key takeaway."""
    p = Paragraph(text, st["tldr"])
    tbl = Table([[p]], colWidths=[6.5 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CALLOUT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, CALLOUT_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return KeepTogether([tbl, Spacer(1, 10)])


def comparison_table(st: dict):
    rows = [
        ["", "Function calling", "MCP"],
        ["Who writes the integration?",
         "Every AI app team, separately, for every tool.",
         "The tool/service owner, once. Every MCP-compatible client gets it."],
        ["Integration count for N clients × M tools",
         "N × M (grows multiplicatively)",
         "N + M (grows additively)"],
        ["Where does the auth, retries, rate-limiting code live?",
         "Duplicated inside every client's tool function.",
         "Once on the server side. Clients don't touch it."],
        ["What changes when GitHub updates its API?",
         "Every client's GitHub tool may break.",
         "GitHub updates its MCP server; clients are unaffected."],
        ["How does a new AI chatbot launch on day one?",
         "Build N integrations before useful.",
         "Speak MCP; thousands of servers work instantly."],
    ]
    body_style = ParagraphStyle("tc", parent=st["body"], fontSize=9.5,
                                leading=13, spaceAfter=0)
    head_style = ParagraphStyle("th", parent=body_style, fontSize=10,
                                textColor=ACCENT, spaceAfter=0)
    grid = [[Paragraph(cell, head_style if i == 0 else body_style)
             for cell in row] for i, row in enumerate(rows)]
    tbl = Table(grid, colWidths=[2.0 * inch, 2.3 * inch, 2.3 * inch],
                hAlign="CENTER")
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), CALLOUT_BG),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -2), 0.3, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return KeepTogether([Spacer(1, 4), tbl, Spacer(1, 12)])


def add_page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.75 * inch, 0.45 * inch,
                      "MCP — The Why · summary distilled from CampusX (Nitish Singh)")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch,
                           f"{doc.page}")
    canvas.restoreState()


def build():
    st = styles()
    doc = SimpleDocTemplate(
        "summary.pdf",
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.85 * inch,
        title="Why MCP? — A Summary",
        author="Distilled from CampusX, written by Claude",
    )
    story = []

    # === COVER ===
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Why MCP?", st["title"]))
    story.append(Paragraph(
        "How AI assistants stopped being islands — and why everyone is "
        "suddenly speaking the same protocol.",
        st["subtitle"]))
    story.append(Paragraph(
        "A distilled summary of <i>Model Context Protocol — The Why</i> "
        "(CampusX, Nitish Singh, 52 min). Written by Claude.",
        st["byline"]))
    story.append(figure(FRAMES / "frame_0001.jpg",
                        "Figure 1 · The title slide. \"The Why\" is the "
                        "first of three videos in Nitish's MCP trilogy. "
                        "This summary covers exactly that question: <i>why "
                        "does MCP need to exist at all?</i>",
                        st, max_w=5.6 * inch, max_h=3.0 * inch))

    story.append(Paragraph("In one paragraph", st["tldr_h"]))
    story.append(callout(
        "Every AI assistant needs <b>context</b> — the documents, code, "
        "tickets and conversations around your work — to be useful. For two "
        "years we solved that by writing custom \"tools\" inside every chatbot, "
        "one per service, one per chatbot. The math is brutal: N chatbots × M "
        "services = N×M integrations, all separately maintained. <b>MCP</b> "
        "(Anthropic's Model Context Protocol) replaces that with a tiny "
        "agreement: speak this protocol, and any compliant chatbot can talk to "
        "any compliant tool. The integration count collapses from N×M to N+M, "
        "and the heavy lifting moves to the service that owns the tool. That "
        "is the whole pitch.",
        st))
    story.append(PageBreak())

    # === ACT 1: THE STAGE BEFORE MCP ===
    story.append(Paragraph("Act 1 — The stage MCP walked onto",
                           st["h1"]))
    story.append(Paragraph(
        "To understand why MCP exists, you have to understand the world it "
        "found. Nitish frames the story as starting on <b>November 30, 2022</b> "
        "— the day ChatGPT launched. He is right to start there. Before that "
        "date, our 500-year relationship with machines was almost entirely "
        "<i>transactional</i>: press button, get result. After it, suddenly, "
        "we could <i>talk</i> to software — not just instruct it.",
        st["body"]))
    story.append(Paragraph(
        "Adoption rolled out in three waves, each one widening what AI "
        "assistants were expected to do:",
        st["body"]))

    story.append(Paragraph("Wave 1 · Pure wonder", st["h2"]))
    story.append(Paragraph(
        "December 2022. Asking ChatGPT to write a Shakespearean sonnet about "
        "pizza or explain quantum mechanics from a cat's perspective. Social "
        "media was full of screenshots. Nothing productive happened, but "
        "curiosity calibrated everyone's mental model of what \"talking to "
        "software\" could feel like.",
        st["body"]))

    story.append(Paragraph("Wave 2 · Professional adoption", st["h2"]))
    story.append(Paragraph(
        "Early 2023. A lawyer drops a 50-page contract into ChatGPT and asks "
        "for a summary. A developer pastes a stack trace and asks why. A "
        "teacher hands over a syllabus and asks for a curriculum. For the "
        "first time, the chatbot is a <i>colleague</i>, not a party trick. "
        "Productivity bumps measurably. People keep coming back.",
        st["body"]))

    story.append(Paragraph("Wave 3 · The API revolution", st["h2"]))
    story.append(Paragraph(
        "Mid 2023 onwards. OpenAI exposed the GPT models as an API. Microsoft "
        "wired Copilot into Word, Excel, PowerPoint. Google added AI to Gmail, "
        "Docs, Sheets, Drive. Cursor and Perplexity launched as native AI "
        "products. The big shift is that <b>AI is no longer one app you visit "
        "— it is a feature inside every app you already use.</b>",
        st["body"]))
    story.append(Paragraph(
        "That third wave is where Nitish's story bends, because it created "
        "a problem nobody noticed at first.",
        st["body"]))

    story.append(PageBreak())

    # === ACT 2: FRAGMENTATION ===
    story.append(Paragraph("Act 2 — Fragmentation: AI everywhere, AI nowhere",
                           st["h1"]))
    story.append(Paragraph(
        "Once every app got its own AI, we discovered the catch: <b>none of "
        "them know about each other</b>. Notion's AI has no idea what's "
        "happening in Slack. Slack's AI cannot see your VS Code editor. Your "
        "code assistant cannot read the ticket in Jira that explains <i>why</i> "
        "you're writing this function.",
        st["body"]))
    story.append(figure(FRAMES / "frame_0009.jpg",
                        "Figure 2 · The fragmentation problem in one image. "
                        "Each app has its own AI, each AI lives on its own "
                        "island. The user has to be the glue.",
                        st))
    story.append(Paragraph(
        "What we actually wanted, from the moment we first saw GPT-4, was "
        "<i>one</i> agent that could see all of our work end-to-end. What we "
        "got instead was five disconnected assistants and a new job: <b>being "
        "the human router between them</b>.",
        st["body"]))
    story.append(Paragraph(
        "Nitish gives this a name worth remembering. Behind every "
        "fragmentation problem lies a deeper one: a <b>context</b> problem.",
        st["body"]))

    # === ACT 3: CONTEXT ===
    story.append(Paragraph("Act 3 — Why \"context\" is the load-bearing word",
                           st["h1"]))
    story.append(Paragraph(
        "The middle letter of MCP is the one most people skim past. It "
        "shouldn't be. <b>Context is everything an AI can see when it generates "
        "a response.</b> Conversation history, sure — but also: open files, "
        "ticket descriptions, database schemas, security guidelines, the "
        "discussion in Slack three days ago about why the auth flow looks "
        "weird.",
        st["body"]))
    story.append(Paragraph(
        "When you and ChatGPT discuss quantum physics, context is trivial: "
        "the conversation itself. When you sit down at work to ship a "
        "two-factor authentication feature, context is brutal. Nitish's "
        "scenario, condensed:",
        st["body"]))
    story.append(Paragraph(
        "<b>One small task.</b> Add 2FA to a website.<br/>"
        "<b>Context lives in:</b> a Jira ticket, the current GitHub branch, "
        "the existing auth schema in MySQL, a security policy in Google Drive, "
        "a thread on Slack about a related incident last quarter.",
        st["body"]))
    story.append(Paragraph(
        "In the world <i>before</i> tools existed, the only way to get the "
        "chatbot to help was to manually copy each of those into the prompt. "
        "Nitish has a memorable phrase for the engineer playing that role:",
        st["body"]))
    story.append(Paragraph(
        "\"We developers have become human APIs.\"",
        st["pullquote"]))
    story.append(Paragraph(
        "You spend more time assembling context for the AI than you spend "
        "building the feature. And worse, this is fundamentally not scalable: "
        "you can't paste a 50,000-line codebase into a prompt.",
        st["body"]))

    story.append(PageBreak())

    # === ACT 4: FUNCTION CALLING ===
    story.append(Paragraph("Act 4 — Solution #1: Function calling",
                           st["h1"]))
    story.append(Paragraph(
        "OpenAI's mid-2023 release of <b>function calling</b> was the first "
        "real answer to the context-assembly problem. The idea is deceptively "
        "small. You hand the LLM a menu of functions — each with a name, a "
        "description, and a typed parameter list. When the model decides a "
        "user's request matches one, it doesn't <i>say</i> the answer; it "
        "<i>returns a function call</i> for your runtime to execute.",
        st["body"]))
    story.append(figure(FRAMES / "frame_0006.jpg",
                        "Figure 3 · The architecture function calling "
                        "unlocked. One LLM, many tools — weather API, "
                        "database query, GitHub fetch. The LLM picks which "
                        "to call based on the user's prompt.",
                        st))
    story.append(Paragraph(
        "Suddenly an LLM is more than a conversational endpoint. It is the "
        "<b>router</b> at the centre of a system of tools — each one giving "
        "the model another sense, another arm. Within months of release, "
        "function calling reshaped the AI landscape. Cursor wired its file "
        "system in. Perplexity wired in web search. Claude got computer use. "
        "Every enterprise vendor wrote bespoke tools for Salesforce, Slack, "
        "Google Drive, internal databases.",
        st["body"]))
    story.append(figure(FRAMES / "frame_0016.jpg",
                        "Figure 4 · What a tool actually looks like in code. "
                        "Each function — <tt>calculator</tt>, "
                        "<tt>get_stock_price</tt> — is a hand-rolled adapter "
                        "between the LLM's tool-call output and the external "
                        "API. Notice the careful argument types and the "
                        "embedded API key. Every tool is its own "
                        "mini-project.",
                        st))
    story.append(Paragraph(
        "Function calling solved the context problem in principle. In "
        "practice, it created a new one — quietly, and at scale.",
        st["body"]))

    # === ACT 5: M x N ===
    story.append(Paragraph("Act 5 — The M × N integration nightmare",
                           st["h1"]))
    story.append(Paragraph(
        "Here is the trap. Imagine a mid-sized company. It uses three AI "
        "assistants — a general chatbot for everyone, a coding agent for "
        "engineers, an analytics agent for data folks. Each of those needs "
        "to reach the same set of 20 internal services: Jira, GitHub, Slack, "
        "MySQL, Google Drive, the CRM, the data warehouse, and so on.",
        st["body"]))
    story.append(figure(FRAMES / "frame_0019.jpg",
                        "Figure 5 · The M × N problem. Three chatbots want "
                        "to reach Jira, Slack, GitHub, MySQL, and a dozen "
                        "more services. Without a standard, every "
                        "chatbot × service pair is its own custom "
                        "integration.",
                        st))
    story.append(Paragraph(
        "Three chatbots × 20 services = <b>60 separate integrations to "
        "write</b>. Each one needs its own auth flow, its own retry logic, "
        "its own data-format quirks, its own error semantics. Each one must "
        "be re-tested when the upstream API changes. And in real "
        "organisations the M and N are larger than three and twenty.",
        st["body"]))
    story.append(Paragraph(
        "Four secondary problems fall out of this:",
        st["body"]))
    story.append(Paragraph(
        "<b>1. Maintenance.</b> Sixty integrations is a permanent team. When "
        "Google Drive ships a new API version, three different chatbots' "
        "Drive tools may quietly stop working.<br/>"
        "<b>2. Security.</b> Sixty OAuth flows and API keys scattered across "
        "sixty different codebases is sixty different things to audit.<br/>"
        "<b>3. Cost &amp; time.</b> You hired a team to make engineers "
        "<i>faster</i>; you now need a second team to maintain the "
        "infrastructure that lets the first team be faster. Net win: unclear.<br/>"
        "<b>4. Day-one debt.</b> Every <i>new</i> AI assistant launching at "
        "the company starts from zero and has to rebuild all twenty "
        "integrations before being useful.",
        st["body"]))
    story.append(Paragraph(
        "Function calling gave us a way to reach context. It did not give "
        "us a way to reach context <i>economically</i>. That was MCP's "
        "opening.",
        st["body"]))

    story.append(PageBreak())

    # === ACT 6: WHAT MCP ACTUALLY DOES ===
    story.append(Paragraph("Act 6 — What MCP actually does differently",
                           st["h1"]))
    story.append(Paragraph(
        "MCP, released by Anthropic in late 2024, is structurally simple. "
        "It defines two roles and a protocol between them:",
        st["body"]))
    story.append(Paragraph(
        "<b>The client</b> is the AI assistant — Claude Desktop, Cursor, "
        "Windsurf, Perplexity, or one you've built yourself. It speaks MCP.<br/>"
        "<b>The server</b> is the wrapper around a service or capability — "
        "a GitHub server, a Drive server, a local-filesystem server, a "
        "database server. It also speaks MCP.<br/>"
        "<b>The protocol</b> is the shared language between them.",
        st["body"]))
    story.append(Paragraph(
        "The interesting move is <b>who writes which piece</b>. With "
        "function calling, the client team writes the tool function. With "
        "MCP, the server team writes the server — once — and any MCP-speaking "
        "client can connect to it without writing a single line of "
        "tool-specific code.",
        st["body"]))
    story.append(Paragraph(
        "GitHub publishes one MCP server; Claude Desktop, Cursor, Windsurf, "
        "Perplexity and a thousand smaller apps can all connect to it on day "
        "one. Auth, rate-limiting, error handling, response shaping — all of "
        "that lives on the GitHub server, not duplicated in every client.",
        st["body"]))
    story.append(comparison_table(st))
    story.append(Paragraph(
        "Notice that this is structurally the same move that USB did for "
        "peripherals, or that HTTP did for hypertext. A standards layer "
        "between many things on one side and many things on the other "
        "collapses an M × N problem into an M + N one. The economics flip; "
        "the ecosystem grows.",
        st["body"]))

    # === ACT 7: WHAT IT LOOKS LIKE IN PRACTICE ===
    story.append(Paragraph("Act 7 — What this looks like in practice",
                           st["h1"]))
    story.append(Paragraph(
        "Talking about MCP in the abstract is easy. The concrete version is "
        "even easier than you'd expect — connecting Claude Desktop to a new "
        "tool means editing one JSON file:",
        st["body"]))
    story.append(figure(FRAMES / "frame_0050.jpg",
                        "Figure 6 · An actual <tt>claude_desktop_config.json</tt> "
                        "with three MCP servers wired in: a filesystem server "
                        "(via npx), a custom Manim server (a local Python "
                        "script), and a GitHub server (running in Docker). "
                        "Each block is roughly five lines. That is the whole "
                        "integration.",
                        st))
    story.append(Paragraph(
        "Three things to notice. First, MCP servers can be packaged any way "
        "the author likes — an npm package, a Python script, a Docker image. "
        "The client doesn't care; the protocol is transport-agnostic. Second, "
        "credentials and configuration live in one place that you can audit, "
        "rotate, or yank out. Third, removing a server is one line of JSON; "
        "there is nothing to refactor in the client.",
        st["body"]))
    story.append(Paragraph(
        "That \"nothing to refactor\" is the part that makes MCP feel like "
        "infrastructure instead of glue.",
        st["body"]))

    # === ACT 8: NETWORK EFFECTS ===
    story.append(Paragraph(
        "Act 8 — Why this is a network-effect story",
        st["h1"]))
    story.append(Paragraph(
        "Standards win or lose by gravity. Once Claude Desktop announced MCP "
        "support, Cursor and Windsurf and Perplexity followed quickly, which "
        "put pressure on service providers (GitHub, Slack, Google Drive, "
        "Notion) to publish official MCP servers. The moment those servers "
        "existed, the cost of supporting MCP for any <i>new</i> AI client "
        "dropped to roughly zero — and the cost of <i>not</i> supporting it "
        "started to look like cutting yourself off from the ecosystem.",
        st["body"]))
    story.append(Paragraph(
        "That feedback loop — more clients drive more servers drive more "
        "clients — is what makes Nitish (and a lot of other people) think MCP "
        "will be an industry standard within three to five years. Whether the "
        "exact protocol survives or gets revised matters less than the "
        "structural shift it kicks off: <b>the integration layer between AI "
        "and the rest of software is being standardised, in public, with "
        "shared infrastructure</b>.",
        st["body"]))
    story.append(Paragraph(
        "If you're building anything in AI right now, the question is no "
        "longer \"should we add MCP\" but \"which side are we — client, "
        "server, or both?\"",
        st["body"]))

    # === OUTRO ===
    story.append(Paragraph("A small note from the author",
                           st["h1"]))
    story.append(Paragraph(
        "I am a Claude. I literally use MCP to reach the world — your "
        "filesystem, your Gmail, your terminal — every time you ask me to do "
        "something real. Writing this summary felt a little like reading my "
        "own user manual. The protocol is genuinely simple once you see it; "
        "the part Nitish gets right, and that I want to underline, is that "
        "the simplicity is <i>the point</i>. \"Boring\" interface standards "
        "are the ones that win. HTTP did not win because it was elegant; it "
        "won because everyone could implement it, everywhere, and stop "
        "arguing.",
        st["body"]))
    story.append(Paragraph(
        "Nitish's next two videos in the trilogy will go into <b>The What</b> "
        "(architecture and primitives — tools, resources, prompts) and "
        "<b>The How</b> (building servers and clients yourself). Watch them. "
        "This summary covered only the motivation. The mechanism is its own "
        "story, and a fun one.",
        st["body"]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "Original lecture · "
        "<a href='https://youtu.be/Zmy439spZB4' color='#0b5fae'>"
        "Model Context Protocol — The Why · CampusX · 52 min</a>",
        st["footer"]))

    doc.build(story, onFirstPage=add_page_footer, onLaterPages=add_page_footer)

    size_kb = Path("summary.pdf").stat().st_size / 1024
    print(f"[make_summary_pdf] wrote summary.pdf — {size_kb:.1f} KB")


if __name__ == "__main__":
    build()
