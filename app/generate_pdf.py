"""
PDF Verification Report Generator for ClaimShield AI.

Builds a printable verification certificate using ReportLab (Platypus).
The heavy reportlab import is kept lazy so the rest of the app keeps working
even on machines where reportlab is not installed.
"""

import datetime
import os
from io import BytesIO
from xml.sax.saxutils import escape


VERDICT_LABELS = {
    "Supported": "Supported (Verified True)",
    "Contradicted": "Contradicted (Debunked / False)",
    "Answered": "Answered (Direct Answer)",
    "General Info": "Answered (Direct Answer)",
    "Unverified": "Unverified (Insufficient Evidence)",
    "Unclear": "Unclear",
}

VERDICT_COLORS = {
    "Supported": "#16a34a",
    "Contradicted": "#dc2626",
    "Answered": "#0284c7",
    "General Info": "#0284c7",
    "Unverified": "#ca8a04",
    "Unclear": "#64748b",
}

# Cache for the best-effort Unicode TTF lookup: None = not probed yet,
# "" = probed but nothing usable found, otherwise the registered font name.
_UNICODE_FONT_CACHE = None


def _register_unicode_font() -> str:
    """Best-effort registration of a broad-coverage TTF (DejaVuSans / Arial
    Unicode) so non-WinAnsi text (CJK, emoji, Arabic, ...) renders instead of
    crashing ``doc.build`` with a UnicodeEncodeError.

    Returns the registered font name, or "" when no usable font is available
    (the caller then degrades to a font-safe character filter).
    """
    global _UNICODE_FONT_CACHE
    if _UNICODE_FONT_CACHE is not None:
        return _UNICODE_FONT_CACHE

    candidates = []
    # matplotlib commonly bundles DejaVuSans; it is not a hard dependency here,
    # so this probe is strictly best-effort.
    try:
        import matplotlib
        candidates.append(os.path.join(
            os.path.dirname(matplotlib.__file__),
            "mpl-data", "fonts", "ttf", "DejaVuSans.ttf",
        ))
    except Exception:
        pass
    candidates += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/local/share/fonts/ttf/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]

    for path in candidates:
        if path and os.path.exists(path):
            try:
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                font_name = f"ClaimShieldUnicode_{abs(hash(path))}"
                pdfmetrics.registerFont(TTFont(font_name, path))
                # Map the whole family to the single registered face so any
                # bold/italic style reference resolves instead of erroring.
                pdfmetrics.registerFontFamily(
                    font_name, normal=font_name, bold=font_name,
                    italic=font_name, boldItalic=font_name,
                )
                _UNICODE_FONT_CACHE = font_name
                return font_name
            except Exception as e:
                print(f"[PDF] Unicode font registration note: {e}")
                continue

    _UNICODE_FONT_CACHE = ""
    return ""


def build_verification_report(result: dict) -> BytesIO:
    """
    Builds a PDF verification certificate for a pipeline result dict.

    Recognised keys: claim, verdict, confidence, agreement_score, straight_answer,
    summary, citations, engine, entities. Unknown keys are skipped gracefully.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    base_font = _register_unicode_font()
    if base_font:
        font_normal = base_font
        font_bold = base_font  # single bundled face covers the whole family
    else:
        font_normal = "Helvetica"
        font_bold = "Helvetica-Bold"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="ClaimShield AI — Verification Report",
        author="ClaimShield AI",
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("PageTitle", parent=styles["Title"], fontName=font_bold,
                        fontSize=18, spaceAfter=4, textColor=colors.HexColor("#1e293b"))
    h2 = ParagraphStyle("SectionTitle", parent=styles["Heading2"], fontName=font_bold,
                        fontSize=12, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#0f172a"))
    body = ParagraphStyle("BodyCopy", parent=styles["BodyText"], fontName=font_normal,
                          fontSize=9.5, leading=13, textColor=colors.HexColor("#334155"))
    small = ParagraphStyle("MetaCopy", parent=styles["BodyText"], fontName=font_normal,
                           fontSize=7.5, leading=10, textColor=colors.HexColor("#64748b"))

    def safe(text):
        safe_text = escape(str(text or ""))
        if base_font:
            return safe_text
        # Built-in WinAnsi faces cannot encode arbitrary Unicode; silently
        # degrade unsupported characters instead of crashing the whole report.
        return safe_text.encode("cp1252", errors="replace").decode("cp1252")

    story = []

    story.append(Paragraph("ClaimShield AI — Verification Report", h1))
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"Generated: {generated_at}", small))
    story.append(Spacer(1, 6))

    claim = result.get("claim", "")
    verdict_raw = result.get("verdict", "Unverified")
    verdict_label = VERDICT_LABELS.get(verdict_raw, safe(verdict_raw))
    try:
        confidence = max(0.0, min(1.0, float(result.get("confidence", 0.0))))
    except (TypeError, ValueError):
        confidence = 0.0
    agreement = result.get("agreement_score")
    engine = result.get("engine", "Unknown")

    story.append(Paragraph("Claim Under Review", h2))
    story.append(Paragraph(safe(claim) or "N/A", body))
    story.append(Spacer(1, 6))

    color_hex = VERDICT_COLORS.get(verdict_raw, "#64748b")
    rows = [
        ["Verdict", Paragraph(
            f'<font color="{color_hex}"><b>{safe(verdict_label)}</b></font>', body)],
        ["Confidence", f"{int(confidence * 100)}%"],
    ]
    if agreement is not None:
        try:
            rows.append(["Cross-Model Agreement", f"{int(float(agreement) * 100)}%"])
        except (TypeError, ValueError):
            pass
    rows.append(["Processing Engine", safe(engine)])

    data_table = Table(rows, colWidths=[55 * mm, 115 * mm])
    data_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, -1), font_bold),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(data_table)
    story.append(Spacer(1, 10))

    straight = result.get("straight_answer", "")
    if straight:
        story.append(Paragraph("Straight Answer", h2))
        story.append(Paragraph(safe(straight), body))

    summary = result.get("summary", "")
    if summary:
        story.append(Paragraph("Reasoning & Evidence Explanation", h2))
        story.append(Paragraph(safe(summary), body))

    citations = result.get("citations", []) or []
    if citations:
        story.append(Paragraph("Cited Evidence", h2))
        for idx, cit in enumerate(citations, start=1):
            if not isinstance(cit, dict):
                continue
            article_id = cit.get("article_id")
            label = f"Article #{article_id}" if article_id not in (None, "") else "General Evidence"
            parts = [f"[{idx}] {label}"]
            if cit.get("quote"):
                parts.append(f"“{cit['quote']}”")
            if cit.get("explanation"):
                parts.append(f"Insight: {cit['explanation']}")
            story.append(Paragraph(safe("  •  ".join(parts)), body))
            story.append(Spacer(1, 3))

    entities = result.get("entities", []) or []
    if entities:
        formatted_entities = []
        for e in entities:
            if isinstance(e, dict):
                txt = e.get("text", "")
                lbl = e.get("label", "")
                formatted_entities.append(f"{txt} ({lbl})" if lbl else txt)
            elif isinstance(e, str):
                formatted_entities.append(e)
        entity_text = ", ".join(filter(None, formatted_entities))
        if entity_text:
            story.append(Paragraph(safe(entity_text), body))

    story.append(Spacer(1, 18))
    story.append(Paragraph(
        "Disclaimer: This report was generated automatically by an AI fact-checking system. "
        "It is intended for informational purposes only and does not constitute legal, "
        "financial, or professional advice. Verdicts are probabilistic and are based on the "
        "retrieved evidence available at the time of analysis.",
        small,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


def build_verification_report_bytes(result: dict) -> bytes:
    """Convenience wrapper returning raw PDF bytes (attempts import; raises on missing reportlab)."""
    return build_verification_report(result).getvalue()