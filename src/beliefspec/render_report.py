"""Render the editable report to a local PDF, with no external service."""

import html
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from beliefspec.dataio import write_json
from beliefspec.experiment import ROOT


def inline(text):
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#245a8d">\1</link>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier" size="8">\1</font>', text)
    return text


def render(source, destination):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("ReportBody", parent=styles["BodyText"], fontSize=9.2,
                              leading=12.4, spaceAfter=5, alignment=TA_LEFT))
    styles.add(ParagraphStyle("ReportTitle", parent=styles["Title"], fontSize=17,
                              leading=20, spaceAfter=10, alignment=TA_LEFT))
    styles.add(ParagraphStyle("ReportH2", parent=styles["Heading2"], fontSize=11.5,
                              leading=14, spaceBefore=7, spaceAfter=5))
    styles.add(ParagraphStyle("ReportH3", parent=styles["Heading3"], fontSize=10,
                              leading=12, spaceBefore=5, spaceAfter=4))
    styles.add(ParagraphStyle("ReportTable", parent=styles["BodyText"], fontSize=7.8,
                              leading=10, spaceAfter=2, wordWrap="CJK"))
    width = A4[0] - 88
    flow = []
    lines = source.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        if line == "<!-- pagebreak -->":
            flow.append(PageBreak())
            continue
        picture = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if picture:
            path = (source.parent / picture.group(2)).resolve()
            image_width, image_height = ImageReader(str(path)).getSize()
            flow.append(Image(str(path), width=width, height=width * image_height / image_width))
            flow.append(Spacer(1, 4))
            continue
        if line.startswith("|"):
            table_lines = [line]
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            cells = []
            for row in table_lines:
                parts = [v.strip() for v in row.strip("|").split("|")]
                if all(re.fullmatch(r"[-: ]+", v) for v in parts):
                    continue
                cells.append([Paragraph(inline(v), styles["ReportTable"]) for v in parts])
            table = Table(cells, colWidths=[width / len(cells[0])] * len(cells[0]), repeatRows=1)
            table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eff4")),
                                       ("LINEBELOW", (0, 0), (-1, 0), .5, colors.HexColor("#536579")),
                                       ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                       ("LEFTPADDING", (0, 0), (-1, -1), 4),
                                       ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                                       ("TOPPADDING", (0, 0), (-1, -1), 4),
                                       ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
            flow.extend([table, Spacer(1, 6)])
            continue
        if line.startswith("# "):
            flow.append(Paragraph(inline(line[2:]), styles["ReportTitle"]))
        elif line.startswith("## "):
            flow.append(Paragraph(inline(line[3:]), styles["ReportH2"]))
        elif line.startswith("### "):
            flow.append(Paragraph(inline(line[4:]), styles["ReportH3"]))
        else:
            paragraph = [line]
            if not line.startswith(("- ", "* ")):
                while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "!", "<!--", "- ")):
                    paragraph.append(lines[i].strip())
                    i += 1
            text = " ".join(paragraph)
            if text.startswith("- "):
                text = "&#8226; " + inline(text[2:])
            else:
                text = inline(text)
            flow.append(Paragraph(text, styles["ReportBody"]))
    pages = []

    def footer(canvas, _document):
        pages.append(canvas.getPageNumber())
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#586472"))
        canvas.drawString(44, 27, "BeliefSpec | local pilot | 2026-10-01 | exploratory evidence")
        canvas.drawRightString(A4[0] - 44, 27, str(canvas.getPageNumber()))

    document = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=44, leftMargin=44,
                                 topMargin=40, bottomMargin=42, title="BeliefSpec pilot report",
                                 author="BeliefSpec project — AI-assisted engineering")
    document.build(flow, onFirstPage=footer, onLaterPages=footer)
    return len(pages)


def main():
    source = ROOT / "docs/pilot_report.md"
    output = ROOT / "docs/pilot_report.pdf"
    pages = render(source, output)
    write_json(ROOT / "artifacts/report_render.json", {"source": str(source.relative_to(ROOT)),
                                                       "pdf": str(output.relative_to(ROOT)),
                                                       "pages": pages, "bytes": output.stat().st_size})
    print(f"Rendered {pages} pages: {output}")


if __name__ == "__main__":
    main()
