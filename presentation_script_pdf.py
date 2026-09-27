import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        if self._pageNumber > 1:
            self.drawString(54, 750, "ClaimShield AI — Easy Speaker Script")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, footer_text)
        self.drawString(54, 36, "ClaimShield AI — Presentation Notes")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 612 - 54, 48)
        self.restoreState()


def build_presentation_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54, rightMargin=54,
        topMargin=54, bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Colors
    NAVY = colors.HexColor("#0B132B")
    RED = colors.HexColor("#E63946")
    BLUE = colors.HexColor("#1D3557")
    TEXT = colors.HexColor("#1E293B")
    MUTED = colors.HexColor("#475569")
    BG = colors.HexColor("#F8FAFC")
    BORDER = colors.HexColor("#CBD5E1")

    # Styles
    title = ParagraphStyle('T', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=NAVY, spaceAfter=6)
    subtitle = ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica', fontSize=12, leading=16, textColor=RED, spaceAfter=15)
    meta = ParagraphStyle('Meta', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=MUTED)
    h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=NAVY, spaceBefore=14, spaceAfter=8)
    slide_h = ParagraphStyle('SH', parent=styles['Heading3'], fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=RED, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10.5, leading=15, textColor=TEXT, spaceAfter=8)
    tip = ParagraphStyle('Tip', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=10, leading=14, textColor=BLUE, leftIndent=12, spaceBefore=4, spaceAfter=6)
    bullet = ParagraphStyle('Bul', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=TEXT, leftIndent=14, spaceAfter=4)

    story = []

    # ── COVER ──
    story.append(Paragraph("ClaimShield AI — Easy 5-Minute Script", title))
    story.append(Paragraph("Simple words. Short sentences. Easy to remember.", subtitle))

    info = [
        [Paragraph("<b>Total Time:</b> 5 minutes", meta), Paragraph("<b>Slides:</b> 3 + Thank You", meta)],
        [Paragraph("<b>Tone:</b> Friendly, confident, clear", meta), Paragraph("<b>Audience:</b> Lecturers / Panel / Investors", meta)],
    ]
    t = Table(info, colWidths=[250, 254])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color=RED, spaceAfter=14))

    # ── TIMING ──
    story.append(Paragraph("Quick Timing Guide", h2))
    rows = [
        ["When", "What You Talk About", "How Long"],
        ["0:00", "Open — grab attention with the problem", "45 sec"],
        ["0:45", "Slide 1 — who uses ClaimShield & why", "1 min 15 sec"],
        ["2:00", "Slide 2 — pricing & speed advantage", "1 min 15 sec"],
        ["3:15", "Slide 3 — how the tech works (4 pillars)", "1 min 15 sec"],
        ["4:30", "Wrap up — thank you & Q&A", "30 sec"],
    ]
    tt = Table(rows, colWidths=[50, 300, 154])
    tt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tt)
    story.append(Spacer(1, 16))

    # ══════════════════════════════════════════════
    #  SLIDE 1
    # ══════════════════════════════════════════════
    story.append(Paragraph("SLIDE 1 — \"Users get evidence, not just a label\"", slide_h))
    story.append(Paragraph("<b>What's on the slide:</b> Four user types + a quote about evidence.", meta))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>SAY THIS:</b>", body))

    story.append(Paragraph(
        "\"Hi everyone, thanks for being here.",
        body))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "Let me start with a simple question — when you read something online, how do you know it's true? "
        "Most fact-checking tools just say 'True' or 'False.' But that's not enough. "
        "People need to see <b>why</b> something is true or false. They need <b>evidence</b>.\"",
        body))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "\"That's what ClaimShield does. It doesn't just give a label — it shows you the proof.\"",
        body))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "\"We built it for four types of users:\"",
        body))
    story.append(Paragraph("•  <b>Journalists</b> — they can check their stories before publishing.", bullet))
    story.append(Paragraph("•  <b>Researchers</b> — they can verify citations and gather evidence fast.", bullet))
    story.append(Paragraph("•  <b>Newsrooms</b> — they can check lots of claims at once and keep an audit trail.", bullet))
    story.append(Paragraph("•  <b>Regular readers</b> — anyone can quickly check if something they read is real.", bullet))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "\"Our motto is: the value is not just the answer — it's being able to see <b>why</b> we reached that answer.\"",
        body))

    story.append(Paragraph("💡 TIP: Point at the slide when you say each user type. Make eye contact.", tip))
    story.append(Spacer(1, 12))

    # ══════════════════════════════════════════════
    #  SLIDE 2
    # ══════════════════════════════════════════════
    story.append(Paragraph("SLIDE 2 — \"A simple model with immediate value\"", slide_h))
    story.append(Paragraph("<b>What's on the slide:</b> Pricing table (Free / $19 / $49) and speed comparison (5 sec vs 30-60 min).", meta))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>SAY THIS:</b>", body))

    story.append(Paragraph(
        "\"Now let me show you how ClaimShield actually works as a product.\"",
        body))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "\"We have three simple plans:\"",
        body))
    story.append(Paragraph("•  <b>Free — $0</b> — you get 10 checks per hour with 3 sources. Great for trying it out.", bullet))
    story.append(Paragraph("•  <b>Premium — $19 a month</b> — unlimited checks, 5 sources. Perfect for journalists.", bullet))
    story.append(Paragraph("•  <b>Newsroom — $49 a month</b> — team accounts, analytics dashboard, and a bulk API for large-scale checking.", bullet))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "\"But here's the really exciting part — look at the speed.\"",
        body))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "\"Right now, if a journalist wants to fact-check a claim manually, it takes <b>30 to 60 minutes</b>. "
        "They have to search for sources, read articles, compare information. "
        "ClaimShield does all of that in <b>under 5 seconds</b>.\"",
        body))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "\"That's not just faster — it saves hundreds of working hours every month.\"",
        body))

    story.append(Paragraph("💡 TIP: Pause after \"under 5 seconds\" — let the number sink in.", tip))
    story.append(Spacer(1, 12))

    # ══════════════════════════════════════════════
    #  SLIDE 3
    # ══════════════════════════════════════════════
    story.append(Paragraph("SLIDE 3 — \"A transparent multi-agent system\"", slide_h))
    story.append(Paragraph("<b>What's on the slide:</b> Four pillars (Faster, Explainable, Safe, Responsible) and Thank You.", meta))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>SAY THIS:</b>", body))

    story.append(Paragraph(
        "\"So how does ClaimShield work behind the scenes? "
        "We use something called a <b>multi-agent system</b>. "
        "Instead of one AI doing everything, we have several specialized AI agents working together — "
        "one crawls the web for sources, one checks the facts, and one handles security and audits.\"",
        body))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "\"This gives us four big advantages:\"",
        body))
    story.append(Paragraph("•  <b>It's fast</b> — we cut verification time from 60 minutes to under 5 seconds.", bullet))
    story.append(Paragraph("•  <b>It's explainable</b> — every verdict shows you the exact quotes and sources we used. No guessing.", bullet))
    story.append(Paragraph("•  <b>It's safe</b> — because multiple agents cross-check each other, we avoid the hallucination problem that single AI models have.", bullet))
    story.append(Paragraph("•  <b>It's responsible</b> — we built it with privacy, fairness, and transparency from day one.", bullet))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CLOSING (say with confidence):</b>", body))
    story.append(Paragraph(
        "\"In short, ClaimShield bridges the gap between AI speed and human trust. "
        "We don't just tell you what's true — we show you why.\"",
        body))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "\"Thank you so much for listening. I'm happy to answer any questions!\"",
        body))

    story.append(Paragraph("💡 TIP: Smile when you say \"thank you.\" Pause. Then ask \"Any questions?\"", tip))
    story.append(Spacer(1, 14))

    # ══════════════════════════════════════════════
    #  Q&A CHEAT SHEET
    # ══════════════════════════════════════════════
    story.append(HRFlowable(width="100%", thickness=1, color=RED, spaceAfter=14))
    story.append(Paragraph("Q&A Cheat Sheet — If They Ask...", h2))

    qa = [
        ["If they ask...", "You say..."],
        [
            "\"How do you stop AI from making things up?\"",
            "\"We use multiple AI agents that cross-check each other. One finds the sources, another checks the facts. If there's no real evidence, we say 'Unverified' instead of guessing.\""
        ],
        [
            "\"Why is the newsroom plan only $49?\"",
            "\"We want newsrooms to adopt it easily. $49 gets them started with team seats and analytics. For bigger setups, we offer custom enterprise deals.\""
        ],
        [
            "\"What about paywalled websites?\"",
            "\"We crawl open web sources and public APIs. Newsrooms can also paste in their own text or connect their internal databases through our API.\""
        ],
        [
            "\"How is this different from ChatGPT?\"",
            "\"ChatGPT generates answers from memory. ClaimShield goes out, finds real live sources on the web, and shows you exactly where the evidence comes from. Every verdict is traceable.\""
        ],
        [
            "\"What tech stack do you use?\"",
            "\"Python with Streamlit for the UI, LangChain and AutoGen for multi-agent orchestration, Supabase for the database, and sentence-transformers for semantic search.\""
        ],
    ]
    qt = Table(qa, colWidths=[180, 324])
    qt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG]),
    ]))
    story.append(qt)
    story.append(Spacer(1, 16))

    # ══════════════════════════════════════════════
    #  MEMORY TRICKS
    # ══════════════════════════════════════════════
    story.append(HRFlowable(width="100%", thickness=1, color=RED, spaceAfter=14))
    story.append(Paragraph("Memory Tricks — How to Remember the Flow", h2))

    story.append(Paragraph(
        "Use this simple formula to remember the 3 slides: <b>WHO → HOW MUCH → HOW</b>",
        body))
    story.append(Spacer(1, 4))
    story.append(Paragraph("•  Slide 1 = <b>WHO</b> uses it? (4 user types: Journalists, Researchers, Newsrooms, Readers)", bullet))
    story.append(Paragraph("•  Slide 2 = <b>HOW MUCH</b> does it cost? (Free, $19, $49) + how fast? (5 seconds!)", bullet))
    story.append(Paragraph("•  Slide 3 = <b>HOW</b> does it work? (4 pillars: Fast, Explainable, Safe, Responsible)", bullet))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Key numbers to remember:</b>", body))
    num_rows = [
        ["Number", "What it means"],
        ["4", "User types (Journalists, Researchers, Newsrooms, Readers)"],
        ["3", "Pricing tiers ($0, $19, $49)"],
        ["5 seconds", "How fast ClaimShield verifies a claim"],
        ["30-60 min", "How long manual fact-checking takes"],
        ["4", "Tech pillars (Fast, Explainable, Safe, Responsible)"],
    ]
    nt = Table(num_rows, colWidths=[80, 424])
    nt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG]),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(nt)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>One-line summary you can always fall back on:</b>", body))
    story.append(Paragraph(
        "\"ClaimShield uses multiple AI agents to fact-check claims in under 5 seconds — "
        "and shows you the evidence, not just a True or False label.\"",
        tip))

    doc.build(story, canvasmaker=NumberedCanvas)


if __name__ == '__main__':
    target = os.path.join(
        r"c:\Users\PC\OneDrive\Desktop\IRWA_Project",
        "ClaimShield_5Min_Presentation_Script.pdf",
    )
    build_presentation_pdf(target)
    print(f"PDF generated: {target}")
