import io
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_report_pdf(report_data: Dict[str, Any], title: str = "Loan Truth & Clarity Report") -> io.BytesIO:
    """Generate a clean, professional, permission-aware PDF report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette: Slate & Teal
    TEAL = colors.HexColor("#0D9488")
    DARK_SLATE = colors.HexColor("#1E293B")
    AMBER = colors.HexColor("#D97706")
    MUTED = colors.HexColor("#64748B")
    LIGHT_BG = colors.HexColor("#F8FAFC")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=TEAL
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=MUTED
    )
    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=DARK_SLATE,
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=DARK_SLATE
    )
    disclaimer_style = ParagraphStyle(
        'DisclaimerCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=MUTED
    )

    story = []

    # Header
    story.append(Paragraph(title, title_style))
    story.append(Paragraph("Fear-Free Family Truth Companion — Neutral Financial Clarity", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceBefore=4, spaceAfter=12))

    # Summary Statement
    summary_text = report_data.get("summaryStatement") or report_data.get("modelSummary") or "Analysis completed."
    story.append(Paragraph("Summary Assessment", h2_style))
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))

    # Extracted Terms Table
    terms = report_data.get("extractedTerms")
    if terms and isinstance(terms, dict):
        story.append(Paragraph("Identified Financial Terms", h2_style))
        table_data = [["Field", "Value", "Source Reference", "Status"]]
        for k, v in terms.items():
            if isinstance(v, dict):
                f_name = v.get("fieldName", k)
                f_val = str(v.get("value") or "Not found")
                f_ref = str(v.get("sourceReference") or "—")
                f_stat = str(v.get("status") or "not_found").replace("_", " ").title()
                table_data.append([
                    Paragraph(f_name, body_style),
                    Paragraph(f_val, body_style),
                    Paragraph(f_ref, body_style),
                    Paragraph(f_stat, body_style)
                ])

        t = Table(table_data, colWidths=[160, 150, 120, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), DARK_SLATE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # Findings Table
    findings = report_data.get("findings", [])
    if findings and isinstance(findings, list):
        story.append(Paragraph("Disclosed & Overlooked Charges", h2_style))
        for f in findings:
            f_title = f.get("title", "Finding")
            f_sev = (f.get("severity") or "informational").upper()
            f_cat = f.get("category", "")
            f_expl = f.get("plainLanguageExplanation", "")
            f_q = f.get("recommendedQuestionForLender", "")
            f_quote = f.get("supportingQuote")

            finding_header = f"<b>{f_title}</b> [{f_sev}] — <i>{f_cat}</i>"
            story.append(Paragraph(finding_header, body_style))
            story.append(Paragraph(f_expl, body_style))
            if f_quote:
                quote_text = f"<i>Supporting quote:</i> “{f_quote}” (Ref: {f.get('sourceReference', '—')})"
                story.append(Paragraph(quote_text, disclaimer_style))
            if f_q:
                q_text = f"<b>Recommended question to ask lender:</b> {f_q}"
                story.append(Paragraph(q_text, body_style))
            story.append(Spacer(1, 8))

    # URL Checks if applicable
    checks = report_data.get("checks", [])
    if checks and isinstance(checks, list):
        story.append(Paragraph("Website Risk Indicators & Verifications", h2_style))
        for c in checks:
            c_name = c.get("checkName", "Check")
            c_stat = (c.get("status") or "").replace("_", " ").upper()
            c_expl = c.get("explanation", "")
            c_next = c.get("recommendedNextStep", "")

            story.append(Paragraph(f"<b>{c_name}</b>: {c_stat}", body_style))
            story.append(Paragraph(c_expl, body_style))
            if c_next:
                story.append(Paragraph(f"<i>Recommended step:</i> {c_next}", disclaimer_style))
            story.append(Spacer(1, 6))

    # Limitations & Legal Disclaimer
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=6, spaceAfter=8))
    disclaimer_p = (
        "IMPORTANT NOTICE: This report is generated solely to assist borrowers in understanding loan documents "
        "and identifying terms requiring clarification. It does not sell financial products, rate commercial offerings, "
        "or guarantee the legitimacy, safety, or regulatory standing of any lender. Absence of identified charges "
        "does not establish that no other charges apply. Always verify binding terms directly with an authorized representative."
    )
    story.append(Paragraph(disclaimer_p, disclaimer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
