#!/usr/bin/env python3
"""Generate the KnowledgeGraph AI project poster as a print-ready 16:9 PDF.

Run from any directory:
    python scripts/generate_knowledgegraph_poster.py

Override the destination with:
    python scripts/generate_knowledgegraph_poster.py --output poster.pdf

Requires: reportlab
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "output" / "pdf" / "knowledgegraph_ai_poster.pdf"
LOGO_PATH = ROOT / "assets" / "mitaoe_logo.png"

PAGE_W, PAGE_H = 2592, 1458  # 36 x 20.25 inches, 16:9 landscape
NAVY = HexColor("#0b2e5f")
NAVY_DARK = HexColor("#08264e")
TEAL = HexColor("#12a99c")
BLUE = HexColor("#4288dd")
AMBER = HexColor("#f4b72d")
GREEN = HexColor("#21a47a")
PURPLE = HexColor("#9e72d5")
INK = HexColor("#1a3150")
MUTED = HexColor("#526883")
BG = HexColor("#f0f4f9")
PALE = HexColor("#eaf1f9")
LINE = HexColor("#cbd8e7")

MARGIN = 40
GAP = 22
COL_W = (PAGE_W - MARGIN * 2 - GAP * 2) / 3


def y_from_top(top: float) -> float:
    return PAGE_H - top


def rounded_box(c: canvas.Canvas, x: float, top: float, w: float, h: float,
                fill: Color = white, stroke: Color = LINE, radius: float = 12) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1.5)
    c.roundRect(x, y_from_top(top + h), w, h, radius, fill=1, stroke=1)


def text(c: canvas.Canvas, value: str, x: float, top: float, size: float,
         color: Color = INK, font: str = "Helvetica", align: str = "left") -> None:
    c.setFillColor(color)
    c.setFont(font, size)
    y = y_from_top(top + size)
    if align == "right":
        c.drawRightString(x, y, value)
    elif align == "center":
        c.drawCentredString(x, y, value)
    else:
        c.drawString(x, y, value)


def wrapped(c: canvas.Canvas, value: str, x: float, top: float, width: float,
            size: float = 20, leading: float | None = None,
            color: Color = INK, font: str = "Helvetica", max_lines: int | None = None) -> float:
    """Draw wrapped text and return the next top coordinate."""
    leading = leading or size * 1.34
    lines = simpleSplit(value, font, size, width)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and c.stringWidth(last + "...", font, size) > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "..."
    for line in lines:
        text(c, line, x, top, size, color, font)
        top += leading
    return top


def section(c: canvas.Canvas, x: float, top: float, w: float, h: float,
            number: str, title: str, accent: Color = TEAL) -> tuple[float, float]:
    rounded_box(c, x, top, w, h)
    header_h = 48
    c.setFillColor(NAVY)
    c.roundRect(x, y_from_top(top + header_h), w, header_h, 12, fill=1, stroke=0)
    # Square the lower corners of the header band.
    c.rect(x, y_from_top(top + header_h), w, 12, fill=1, stroke=0)
    c.setFillColor(accent)
    c.circle(x + 28, y_from_top(top + 24), 17, fill=1, stroke=0)
    text(c, number, x + 28, top + 14, 13, NAVY_DARK, "Helvetica-Bold", "center")
    text(c, title, x + 56, top + 9, 27, white, "Helvetica-Bold")
    return x + 20, top + header_h + 16


def bullet_list(c: canvas.Canvas, items: Iterable[str], x: float, top: float,
                width: float, size: float = 19, color: Color = INK,
                gap: float = 7) -> float:
    for item in items:
        c.setFillColor(TEAL)
        c.circle(x + 4, y_from_top(top + size * 0.62), 3, fill=1, stroke=0)
        top = wrapped(c, item, x + 16, top, width - 16, size, size * 1.28, color)
        top += gap
    return top


def pill(c: canvas.Canvas, label: str, value: str, x: float, top: float,
         w: float, h: float, fill: Color = PALE, value_color: Color = NAVY) -> None:
    rounded_box(c, x, top, w, h, fill=fill, stroke=fill, radius=9)
    text(c, value, x + w / 2, top + 8, 26, value_color, "Helvetica-Bold", "center")
    text(c, label, x + w / 2, top + 38, 15, MUTED, "Helvetica", "center")


def draw_header(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, y_from_top(164), PAGE_W, 164, fill=1, stroke=0)
    c.setFillColor(AMBER)
    c.rect(0, y_from_top(164), 15, 164, fill=1, stroke=0)
    # White logo tile keeps the embedded MITAOE mark readable at print size.
    rounded_box(c, 42, 32, 385, 98, white, white, 10)
    if LOGO_PATH.exists():
        logo = ImageReader(str(LOGO_PATH))
        c.drawImage(logo, 42, y_from_top(128), width=385, height=96,
                    preserveAspectRatio=True, anchor="c", mask="auto")
    else:
        text(c, "MITAOE", 66, 51, 43, NAVY, "Helvetica-Bold")
        text(c, "MIT Academy of Engineering", 68, 98, 17, NAVY, "Helvetica-Bold")

    center_x = PAGE_W * 0.52
    text(c, "KnowledgeGraph AI", center_x, 33, 52, white, "Helvetica-Bold", "center")
    text(c, "Evidence-linked document analytics with NLP", center_x, 91, 28,
         HexColor("#d7e5f7"), "Helvetica-Bold", "center")
    text(c, "React  ·  FastAPI  ·  spaCy  ·  NetworkX", center_x, 130, 18,
         HexColor("#b9cce5"), "Helvetica", "center")
    c.setStrokeColor(HexColor("#91a8c7"))
    c.setLineWidth(1.4)
    c.line(PAGE_W - 360, y_from_top(34), PAGE_W - 360, y_from_top(132))
    text(c, "NLP PROJECT", PAGE_W - 170, 61, 24, white, "Helvetica-Bold", "center")
    text(c, "MITAOE", PAGE_W - 170, 96, 19, HexColor("#d7e5f7"), "Helvetica", "center")


def draw_card_text(c: canvas.Canvas, x: float, top: float, h: float,
                   number: str, title: str, body: str,
                   accent: Color = TEAL, size: float = 19) -> None:
    inner_x, body_top = section(c, x, top, COL_W, h, number, title, accent)
    wrapped(c, body, inner_x, body_top, COL_W - 40, size, size * 1.34)


def draw_left_column(c: canvas.Canvas, x: float) -> None:
    top = 186
    draw_card_text(c, x, top, 122, "01", "Project overview",
                   "KnowledgeGraph AI converts PDF, DOCX and TXT documents into linked entities and relations. It presents extracted facts as a searchable graph with source-sentence evidence.")
    top += 136
    draw_card_text(c, x, top, 140, "02", "Problem statement",
                   "Facts in documents are difficult to explore with keyword search alone. The project connects an NLP notebook workflow to a usable tool that exposes who did what and lets readers inspect the supporting sentence.")
    top += 154
    ix, iy = section(c, x, top, COL_W, 168, "03", "Objectives")
    bullet_list(c, [
        "Extract named entities and subject-predicate-object relations.",
        "Resolve repeated entity names and build a directed graph.",
        "Enable evidence-led graph search, filtering and analytics.",
        "Export triples and graph data for downstream use.",
    ], ix, iy, COL_W - 40, 17, gap=2)
    top += 182
    draw_card_text(c, x, top, 191, "04", "Literature review",
                   "Keyword search finds matching strings but leaves relations implicit. Dependency-rule extraction is transparent and lightweight, though it can miss varied phrasing. Transformer-based relation extraction is a comparison path that needs model selection and labelled evaluation data. This project implements an interpretable baseline.", size=17)
    top += 205
    ix, iy = section(c, x, top, COL_W, 250, "05", "Dataset", AMBER)
    wrapped(c, "Four built-in topical documents provide 34 example sentences. Uploads support PDF, DOCX and TXT (up to 20 MB); samples are demonstrations, not a benchmark corpus.", ix, iy, COL_W - 40, 17, 22)
    text(c, "BUILT-IN SAMPLE SENTENCES (n = 34)", ix, iy + 76, 14, MUTED, "Helvetica-Bold")
    for idx, (label, value, color) in enumerate([
        ("Technology", 11, TEAL), ("Space", 9, BLUE),
        ("Science", 7, AMBER), ("Climate", 7, GREEN),
    ]):
        row_top = iy + 102 + idx * 22
        text(c, label, ix, row_top, 15, INK)
        bar_x = ix + 128
        c.setFillColor(PALE)
        c.roundRect(bar_x, y_from_top(row_top + 15), 440, 12, 6, fill=1, stroke=0)
        c.setFillColor(color)
        c.roundRect(bar_x, y_from_top(row_top + 15), 440 * value / 11, 12, 6, fill=1, stroke=0)
        text(c, str(value), ix + COL_W - 46, row_top, 15, INK, "Helvetica-Bold", "right")
    top += 264
    draw_card_text(c, x, top, 183, "06", "NLP preprocessing",
                   "Extract embedded PDF text, DOCX paragraphs or UTF-8 text. Normalize whitespace and punctuation, then use spaCy for sentence splitting, tokenization, named entity recognition and dependency parsing. A local smoothed TF-IDF baseline ranks salient terms.", size=17)


def draw_methodology(c: canvas.Canvas, x: float, top: float) -> float:
    ix, iy = section(c, x, top, COL_W, 370, "07", "Methodology")
    end = wrapped(c, "Dependency patterns capture active and passive voice, coordinated subjects and objects, role relations such as CEO_OF, and prepositional relations such as HEADQUARTER_IN. Entity normalization and fuzzy matching reduce duplicates. Each triple retains provenance and a heuristic score.", ix, iy, COL_W - 40, 18, 24)
    labels = ["Text\nextract", "Clean +\nsplit", "spaCy\nNER + parse", "Relation\nrules", "Resolve\nentities", "Graph +\ntriples"]
    gap = 10
    bw = (COL_W - 40 - 5 * gap) / 6
    top_boxes = end + 12
    for i, label in enumerate(labels):
        bx = ix + i * (bw + gap)
        c.setFillColor([HexColor("#e5f5f2"), HexColor("#e5f5f2"), PALE][i % 3])
        c.roundRect(bx, y_from_top(top_boxes + 55), bw, 55, 10, fill=1, stroke=0)
        for j, line in enumerate(label.split("\n")):
            text(c, line, bx + bw / 2, top_boxes + 8 + j * 20, 14,
                 NAVY, "Helvetica-Bold", "center")
        if i < len(labels) - 1:
            text(c, "›", bx + bw + gap / 2, top_boxes + 10, 25, TEAL, "Helvetica-Bold", "center")
    note_top = top_boxes + 69
    wrapped(c, "Example: Apple -> HEADQUARTER_IN -> Cupertino. “Apple is headquartered in Cupertino, California.” Score 0.80 is heuristic, not calibrated.", ix, note_top, COL_W - 40, 15, 19, MUTED)
    cy = top + 292
    c.setStrokeColor(TEAL)
    c.setLineWidth(3)
    c.line(ix + 116, y_from_top(cy + 35), ix + COL_W - 150, y_from_top(cy + 35))
    c.line(ix + COL_W - 150, y_from_top(cy + 35), ix + COL_W - 168, y_from_top(cy + 23))
    c.line(ix + COL_W - 150, y_from_top(cy + 35), ix + COL_W - 168, y_from_top(cy + 47))
    for cx, label in [(ix + 116, "Apple"), (ix + COL_W - 150, "Cupertino")]:
        c.setFillColor(PALE)
        c.setStrokeColor(BLUE)
        c.circle(cx, y_from_top(cy + 35), 32, fill=1, stroke=1)
        text(c, label, cx, cy + 28, 15, NAVY, "Helvetica-Bold", "center")
    text(c, "HEADQUARTER_IN", ix + COL_W / 2, cy - 2, 15, TEAL, "Helvetica-Bold", "center")
    return top + 382


def draw_architecture(c: canvas.Canvas, x: float, top: float) -> float:
    ix, iy = section(c, x, top, COL_W, 206, "08", "System architecture")
    wrapped(c, "React sends document and graph queries to FastAPI. The backend runs spaCy and relation rules, builds a NetworkX directed graph, then returns analytics and evidence to the browser.", ix, iy, COL_W - 40, 17, 22)
    labels = [("REACT UI", "Upload · graph · charts"), ("FASTAPI", "Analyze · query · export"),
              ("NLP PIPELINE", "spaCy · rules · TF-IDF"), ("NETWORKX", "Directed evidence graph")]
    gap, bw = 12, (COL_W - 40 - 3 * 12) / 4
    box_top = top + 121
    for i, (title, desc) in enumerate(labels):
        bx = ix + i * (bw + gap)
        c.setFillColor(HexColor("#f1f6fc"))
        c.setStrokeColor(LINE)
        c.roundRect(bx, y_from_top(box_top + 62), bw, 62, 9, fill=1, stroke=1)
        text(c, title, bx + bw / 2, box_top + 8, 14, NAVY, "Helvetica-Bold", "center")
        text(c, desc, bx + bw / 2, box_top + 33, 11, MUTED, "Helvetica", "center")
        if i < 3:
            text(c, "›", bx + bw + gap / 2, box_top + 18, 22, BLUE, "Helvetica-Bold", "center")
    return top + 220


def draw_implementation(c: canvas.Canvas, x: float, top: float) -> float:
    draw_card_text(c, x, top, 132, "09", "Implementation",
                   "Backend: Python, FastAPI, spaCy, NetworkX, PyMuPDF and python-docx. Frontend: React, Vite and React Flow. Exports: CSV, JSON and GraphML. Optional Gemini Q&A uses matched graph evidence.", size=16)
    return top + 146


def draw_confusion_matrix(c: canvas.Canvas, x: float, top: float) -> None:
    text(c, "SENTIMENT CONFUSION MATRIX  /  n = 28", x, top, 14, MUTED, "Helvetica-Bold")
    labels = ["Neg", "Neu", "Pos"]
    matrix = [[10, 0, 1], [0, 8, 0], [0, 0, 9]]
    cell = 40
    left = x + 165
    base_top = top + 33
    for j, label in enumerate(labels):
        text(c, label, left + j * (cell + 5) + cell / 2, base_top, 13, INK, "Helvetica", "center")
    for i, row in enumerate(matrix):
        text(c, ["Negative", "Neutral", "Positive"][i], x, base_top + 28 + i * 45, 13, INK)
        for j, value in enumerate(row):
            fill = HexColor("#d8eee8") if i == j else (HexColor("#f7e9df") if value else PALE)
            bx = left + j * (cell + 5)
            by = base_top + 24 + i * 45
            c.setFillColor(fill)
            c.rect(bx, y_from_top(by + cell), cell, cell, fill=1, stroke=0)
            text(c, str(value), bx + cell / 2, by + 11, 16, NAVY, "Helvetica-Bold", "center")
    text(c, "Rows: actual  ·  Columns: predicted", x, base_top + 178, 12, MUTED)


def draw_experiment(c: canvas.Canvas, x: float, top: float) -> None:
    ix, iy = section(c, x, top, COL_W, 410, "10", "Experimental setup", AMBER)
    bullet_list(c, [
        "Sentiment demo: 28 hand-labelled examples, three classes.",
        "Graph figures: Technology Companies sample (11 sentences).",
        "Topic check is illustrative; no relation benchmark or model comparison.",
    ], ix, iy, COL_W - 40, 15, gap=1)
    draw_confusion_matrix(c, ix, iy + 114)


def draw_results(c: canvas.Canvas, x: float, top: float) -> float:
    ix, iy = section(c, x, top, COL_W, 690, "11", "Results & analysis", AMBER)
    wrapped(c, "Technology Companies sample: 11 sentences, 18 entities, 16 relations, 16 unique graph edges; density 5.2%. Entity and predicate counts below are from the supplied dashboard screenshot.", ix, iy, COL_W - 40, 15, 19, MUTED)
    metrics_y = iy + 55
    mgap = 10
    mw = (COL_W - 40 - 3 * mgap) / 4
    for i, (label, value) in enumerate([("Entities", "18"), ("Relations", "16"), ("Sentences", "11"), ("Density", "5.2%")]):
        pill(c, label, value, ix + i * (mw + mgap), metrics_y, mw, 70)

    # Entity type doughnut chart.
    chart_top = metrics_y + 88
    chart_cx, chart_cy, radius = ix + 204, y_from_top(chart_top + 111), 58
    values = [14, 6, 5, 5]
    colors = [BLUE, TEAL, PURPLE, AMBER]
    total = sum(values)
    angle = 90
    for value, color in zip(values, colors):
        sweep = 360 * value / total
        c.setFillColor(color)
        c.wedge(chart_cx - radius, chart_cy - radius, chart_cx + radius, chart_cy + radius,
                angle, sweep, fill=1, stroke=0)
        angle += sweep
    c.setFillColor(white)
    c.circle(chart_cx, chart_cy, 49, fill=1, stroke=0)
    text(c, "30", chart_cx, chart_top + 99, 23, NAVY, "Helvetica-Bold", "center")
    text(c, "mentions", chart_cx, chart_top + 126, 12, MUTED, "Helvetica", "center")
    for i, (label, value, color) in enumerate(zip(["ORG", "GPE", "PERSON", "DATE"], values, colors)):
        ly = chart_top + 25 + i * 25
        c.setFillColor(color)
        c.circle(ix + 349, y_from_top(ly + 8), 5, fill=1, stroke=0)
        text(c, label, ix + 364, ly, 15, MUTED)
        text(c, str(value), ix + 518, ly, 16, INK, "Helvetica-Bold", "right")

    bars_top = chart_top + 183
    text(c, "MOST COMMON EXTRACTED PREDICATES", ix, bars_top, 14, MUTED, "Helvetica-Bold")
    predicates = [("FOUND", 3), ("FOUND_IN", 3), ("HEADQUARTER_IN", 3),
                  ("CEO_OF", 2), ("ACQUIRE", 2), ("ACQUIRE_IN", 2), ("DEVELOP", 1)]
    for i, (label, value) in enumerate(predicates):
        row_top = bars_top + 24 + i * 22
        text(c, label, ix + 178, row_top, 14, INK, "Helvetica", "right")
        bx, bw = ix + 191, COL_W - 260
        c.setFillColor(PALE)
        c.roundRect(bx, y_from_top(row_top + 15), bw, 12, 6, fill=1, stroke=0)
        c.setFillColor(BLUE)
        c.roundRect(bx, y_from_top(row_top + 15), bw * value / 3, 12, 6, fill=1, stroke=0)
        text(c, str(value), ix + COL_W - 28, row_top, 14, INK, "Helvetica-Bold", "right")

    note_top = bars_top + 184
    wrapped(c, "Sentiment demo (n = 28): accuracy 96.4%, macro precision 96.7%, macro recall 97.0%, macro F1 96.7%. Small hand-labelled set; illustrative only.", ix, note_top, COL_W - 40, 15, 19, MUTED)
    kpis_top = note_top + 44
    for i, (value, label) in enumerate([
        ("96.4%", "Accuracy"), ("96.7%", "Macro precision"),
        ("97.0%", "Macro recall"), ("96.7%", "Macro F1"),
    ]):
        pill(c, label, value, ix + i * (mw + mgap), kpis_top, mw, 70, HexColor("#e8f4f1"), HexColor("#168871"))
    return top + 690


def draw_right_column(c: canvas.Canvas, x: float, top: float) -> None:
    top = draw_results(c, x, top)
    top += 13
    ix, iy = section(c, x, top, COL_W, 119, "12", "Key highlights")
    bullet_list(c, [
        "Triples retain source sentences for inspection.",
        "Rules handle passive voice and coordinated entities.",
        "One interface combines graphs, analytics, queries and exports.",
    ], ix, iy, COL_W - 40, 14, gap=0)
    top += 131
    ix, iy = section(c, x, top, COL_W, 119, "13", "Applications")
    bullet_list(c, [
        "Explore company, product and acquisition links.",
        "Trace entities in science, space and climate reports.",
        "Ask source-backed questions about document facts.",
    ], ix, iy, COL_W - 40, 14, gap=0)
    top += 131
    draw_card_text(c, x, top, 132, "14", "Conclusion",
                   "The project demonstrates an end-to-end path from documents to a visual, queryable knowledge graph. Its strengths are traceable evidence and a lightweight, interpretable NLP baseline. Broader evaluation is needed before making accuracy claims.", size=16, accent=AMBER)
    top += 144
    draw_card_text(c, x, top, 100, "15", "Limitations & future scope",
                   "Rule patterns can miss varied phrasing; confidence is heuristic. No OCR or persistent storage. Future work: relation evaluation and coreference resolution.", size=15)


def draw_footer(c: canvas.Canvas) -> None:
    top, h = PAGE_H - 58, 42
    c.setFillColor(NAVY)
    c.roundRect(MARGIN, y_from_top(top + h), PAGE_W - 2 * MARGIN, h, 8, fill=1, stroke=0)
    text(c, "Sources: README.md  ·  backend/app/main.py  ·  backend/app/nlp_features.py  ·  backend/evaluate_rubric.py  ·  dashboard snapshot",
         MARGIN + 16, top + 11, 14, HexColor("#d7e5f7"))
    text(c, "MIT Academy of Engineering  |  NLP Project", PAGE_W - MARGIN - 16,
         top + 11, 14, white, "Helvetica-Bold", "right")


def build_poster(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("KnowledgeGraph AI - NLP Project Poster")
    c.setAuthor("MIT Academy of Engineering project team")
    c.setSubject("Evidence-linked document analytics with NLP")
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    draw_header(c)

    left_x = MARGIN
    middle_x = MARGIN + COL_W + GAP
    right_x = MARGIN + 2 * (COL_W + GAP)
    draw_left_column(c, left_x)

    middle_top = 186
    middle_top = draw_methodology(c, middle_x, middle_top)
    middle_top += 12
    middle_top = draw_architecture(c, middle_x, middle_top)
    middle_top += 12
    middle_top = draw_implementation(c, middle_x, middle_top)
    middle_top += 12
    draw_experiment(c, middle_x, middle_top)

    draw_right_column(c, right_x, 186)
    draw_footer(c)
    c.showPage()
    c.save()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"PDF destination (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()
    destination = args.output if args.output.is_absolute() else Path.cwd() / args.output
    print(build_poster(destination.resolve()))


if __name__ == "__main__":
    main()
