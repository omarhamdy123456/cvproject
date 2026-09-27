"""Build the DMET 901 Milestone 1 deck (v2) — a 5-minute, 12-slide version.

Sections mirror the Milestone 1 guideline:
  3.1 Problem statement and motivation
  3.2 The dataset (source, composition, annotations, samples, distribution,
      challenges, justification)
  3.3 Model and tooling
  3.4 Evaluation plan

Slides carry only headline facts; the detail lives in the speaker notes.
All numbers come from figures/summary.json, which analysis/build_figures.py
writes from the published RDD2022 counts and the local Czech XML files.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
SAMPLES = FIG / "samples"
OUT = ROOT / "slides" / "DMET901_Milestone1_RoadDamage_v2.pptx"

# "Asphalt and road paint" palette.
ASPHALT = "1E232A"
ASPHALT_2 = "2B323B"
AMBER = "F0A431"
AMBER_DARK = "B8741A"
BG = "F4F5F7"
CARD = "FFFFFF"
BORDER = "D8DDE4"
TEXT = "1F252C"
MUTED = "66707C"
WHITE = "FFFFFF"
GREEN = "2F7A5B"
RED = "B04A3A"

CLASS_COLORS = {"D00": "1F4E79", "D10": "C47B2B", "D20": "8C3A3A", "D40": "2F6F5E"}
CLASS_NAMES = {
    "D00": "Longitudinal crack",
    "D10": "Transverse crack",
    "D20": "Alligator crack",
    "D40": "Pothole",
}
CLASSES = ("D00", "D10", "D20", "D40")

W, H = 13.333, 7.5
TOTAL = 12
FONT = "Segoe UI"
MONO = "Consolas"


# --------------------------------------------------------------------------- helpers
def rgb(value: str) -> RGBColor:
    value = value.lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _strip_effects(shape) -> None:
    sp_pr = shape.fill._xPr.getparent()
    effect = sp_pr.find(qn("a:effectLst"))
    if effect is not None:
        sp_pr.remove(effect)


def rect(slide, x, y, w, h, fill, line=None, radius=None):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        shape.adjustments[0] = radius
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(1)
    _strip_effects(shape)
    return shape


def text(
    slide,
    x,
    y,
    w,
    h,
    content,
    size,
    color=TEXT,
    bold=False,
    align="left",
    anchor="top",
    font=FONT,
    italic=False,
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(frame, side, Emu(0))
    frame._txBody.bodyPr.set("anchor", {"top": "t", "middle": "ctr", "bottom": "b"}[anchor])
    lines = content if isinstance(content, list) else [content]
    for i, line in enumerate(lines):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
        p.line_spacing = 1.08
        run = p.add_run()
        run.text = line
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = rgb(color)
    return box


def bullets(slide, x, y, w, h, items, size=18, color=TEXT, gap=12, marker="•"):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(frame, side, Emu(0))
    for i, item in enumerate(items):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.space_after = Pt(gap)
        p.line_spacing = 1.08
        if isinstance(item, tuple):
            head, body = item
            r1 = p.add_run()
            r1.text = f"{marker} {head} "
            r1.font.bold = True
            r1.font.name, r1.font.size, r1.font.color.rgb = FONT, Pt(size), rgb(color)
            r2 = p.add_run()
            r2.text = body
            r2.font.name, r2.font.size, r2.font.color.rgb = FONT, Pt(size), rgb(color)
        else:
            r = p.add_run()
            r.text = f"{marker} {item}"
            r.font.name, r.font.size, r.font.color.rgb = FONT, Pt(size), rgb(color)
    return box


def pill(slide, x, y, label, fill=AMBER, color=ASPHALT, size=11, w=None):
    w = w or (0.16 * len(label) + 0.4)
    rect(slide, x, y, w, 0.32, fill, radius=0.5)
    text(slide, x, y, w, 0.32, label, size, color, bold=True, align="center", anchor="middle")
    return w


def card(slide, x, y, w, h, accent=None):
    rect(slide, x, y, w, h, CARD, BORDER, radius=0.04)
    if accent:
        rect(slide, x, y, 0.09, h, accent)


def picture_fit(slide, path: Path, x, y, w, h, border=True):
    """Place an image inside (x, y, w, h) keeping its aspect ratio; returns geometry."""
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    px, py = x + (w - pw) / 2, y + (h - ph) / 2
    pic = slide.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))
    if border:
        pic.line.color.rgb = rgb(BORDER)
        pic.line.width = Pt(0.75)
    return px, py, pw, ph


def notes(slide, content: str) -> None:
    slide.notes_slide.notes_text_frame.text = content


def chrome(prs, section: str, title: str, number: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, 0, 0, W, H, BG)
    rect(slide, 0, 0, W, 1.2, ASPHALT)
    rect(slide, 0, 1.2, W, 0.05, AMBER)
    pill(slide, 0.5, 0.26, section)
    text(slide, 0.5, 0.58, 11.5, 0.5, title, 28, WHITE, bold=True)
    text(slide, 0.5, 7.08, 9, 0.3, "DMET 901  ·  Milestone 1  ·  Road damage detection on RDD2022", 10, MUTED, anchor="middle")
    text(slide, 11.3, 7.08, 1.55, 0.3, f"{number} / {TOTAL}", 10, MUTED, align="right", anchor="middle")
    return slide


def class_chip(slide, x, y, code, w=3.0, size=15):
    rect(slide, x, y, 0.85, 0.4, CLASS_COLORS[code], radius=0.25)
    text(slide, x, y, 0.85, 0.4, code, size, WHITE, bold=True, align="center", anchor="middle")
    text(slide, x + 0.98, y, w - 0.98, 0.4, CLASS_NAMES[code], size, TEXT, anchor="middle")


def label_row(slide, x, y, w, h, head, body, head_w=2.2, size=18):
    """Dark label on the left, one plain sentence on the right."""
    rect(slide, x, y, head_w, h, ASPHALT, radius=0.06)
    text(slide, x, y, head_w, h, head, 17, WHITE, bold=True, align="center", anchor="middle")
    card(slide, x + head_w + 0.12, y, w - head_w - 0.12, h)
    text(slide, x + head_w + 0.4, y, w - head_w - 0.7, h, body, size, TEXT, anchor="middle")


# --------------------------------------------------------------------------- slides
def s01_title(prs, summary):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, 0, 0, W, H, ASPHALT)
    rect(slide, 0, 0, W, 0.09, AMBER)
    for i in range(9):
        rect(slide, 0.5 + i * 0.75, 4.32, 0.42, 0.035, AMBER_DARK)
    text(slide, 0.5, 0.45, 8, 0.3, "GERMAN UNIVERSITY IN CAIRO  ·  MET DEPARTMENT", 12, AMBER, bold=True)
    text(slide, 0.5, 0.75, 8, 0.3, "DMET 901 Computer Vision  ·  Dr. Mohamed Karam", 13, "B9C0C9")
    text(slide, 0.5, 1.6, 6.9, 0.35, "MILESTONE 1", 15, AMBER, bold=True)
    text(slide, 0.5, 2.0, 6.9, 2.2, ["Road Damage", "Detection"], 50, WHITE, bold=True)
    text(slide, 0.5, 4.55, 6.6, 1.0, "Cracks and potholes in one dashcam frame.\nObject detection on RDD2022 with YOLOv8s.", 17, "D3D8DE")
    text(slide, 0.5, 6.0, 6.5, 0.3, "Presenter:  <your name>          Team:  <team members>", 13, "B9C0C9")
    px, py, pw, ph = picture_fit(slide, SAMPLES / "io_output.jpg", 7.55, 1.35, 5.3, 4.2, border=False)
    rect(slide, px - 0.06, py - 0.06, pw + 0.12, ph + 0.12, ASPHALT_2)
    slide.shapes.add_picture(str(SAMPLES / "io_output.jpg"), Inches(px), Inches(py), Inches(pw), Inches(ph))
    text(slide, px, py + ph + 0.12, pw, 0.3, f"Real training frame {summary['czech']['io_sample']['source_image']}, ground-truth boxes.", 10, "8B949E", italic=True)
    notes(
        slide,
        "≈15 s. One sentence: a road photo goes in, labelled boxes come out, four damage types. "
        "Milestone 1 fixes the problem, the dataset and the starting model. Fill in the name placeholders.",
    )


def s02_problem(prs):
    slide = chrome(prs, "3.1  PROBLEM", "One RGB frame in, labelled boxes out", 2)
    label_row(slide, 0.5, 1.6, 8.0, 1.05, "Task", "Object detection — several objects, four classes")
    label_row(slide, 0.5, 2.8, 8.0, 1.05, "Input", "One RGB image from a camera on a moving car")
    label_row(slide, 0.5, 4.0, 8.0, 1.05, "Output", "A box + class for every damage; empty if the road is fine")
    card(slide, 8.85, 1.6, 4.0, 3.45)
    text(slide, 9.1, 1.75, 3.6, 0.4, "Output classes", 16, TEXT, bold=True)
    for i, code in enumerate(CLASSES):
        class_chip(slide, 9.1, 2.3 + i * 0.62, code, w=3.6, size=14)
    text(
        slide,
        0.5,
        5.45,
        12.3,
        0.9,
        "Not classification (a frame can hold many damages), not segmentation (the labels are boxes, not masks).",
        15,
        MUTED,
        italic=True,
    )
    notes(
        slide,
        "≈30 s. Say the task type: object detection. Output format: (class, xmin, ymin, xmax, ymax, confidence), zero or more per frame. "
        "No severity, no masks — the labels do not contain them. Frame-by-frame; tracking is out of scope.",
    )


def s03_input_output(prs, summary):
    io = summary["czech"]["io_sample"]
    slide = chrome(prs, "3.1  INPUT → OUTPUT", "What goes in, what must come out", 3)
    text(slide, 0.5, 1.5, 5.6, 0.4, "INPUT", 16, AMBER_DARK, bold=True)
    picture_fit(slide, SAMPLES / "io_input.jpg", 0.5, 1.95, 5.6, 4.1)
    text(slide, 0.5, 6.2, 5.6, 0.4, f"{io['width']} × {io['height']} JPEG, smartphone on the windscreen", 13, MUTED)
    arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(6.25), Inches(3.65), Inches(0.85), Inches(0.7))
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = rgb(AMBER)
    arrow.line.fill.background()
    _strip_effects(arrow)
    text(slide, 7.25, 1.5, 5.6, 0.4, "OUTPUT", 16, AMBER_DARK, bold=True)
    picture_fit(slide, SAMPLES / "io_output.jpg", 7.25, 1.95, 5.6, 4.1)
    counts = {}
    for box in io["boxes"]:
        counts[box["name"]] = counts.get(box["name"], 0) + 1
    x = 7.25
    for code in CLASSES:
        if not counts.get(code):
            continue
        rect(slide, x, 6.2, 1.25, 0.4, CLASS_COLORS[code], radius=0.25)
        text(slide, x, 6.2, 1.25, 0.4, f"{counts[code]}× {code}", 13, WHITE, bold=True, align="center", anchor="middle")
        x += 1.4
    notes(
        slide,
        f"≈30 s. Frame {io['source_image']} from the Czech training set; the boxes are the dataset's ground truth drawn by our code — "
        "the exact format the detector must produce. Six boxes, all four classes in one frame; boxes overlap, which is fine for detection. "
        "Top of the frame cropped for display only (windscreen glare).",
    )


def s04_motivation(prs):
    slide = chrome(prs, "3.1  MOTIVATION", "Why, and for whom", 4)
    rows = [
        ("Why", "Potholes wreck wheels and cause crashes; cracks become potholes if missed.", AMBER),
        ("Who", "Drivers (in-car warning) and road authorities (automatic damage reports).", GREEN),
        ("Today", "The driver spots it by eye — too late in traffic, at night or in glare.", RED),
    ]
    for i, (head, body, accent) in enumerate(rows):
        y = 1.65 + i * 1.5
        card(slide, 0.5, y, 12.35, 1.3, accent=accent)
        text(slide, 0.85, y, 1.6, 1.3, head, 22, accent, bold=True, anchor="middle")
        text(slide, 2.6, y, 9.9, 1.3, body, 19, TEXT, anchor="middle")
    text(slide, 0.5, 6.3, 12.3, 0.4, "Framing: a driver-assistance feature that turns any dashcam into a damage detector.", 15, MUTED, italic=True, align="center")
    notes(
        slide,
        "≈25 s. Concrete user: a driver with a dashcam, secondary: the municipality receiving geotagged detections. "
        "Human baseline: eyesight and manual inspection routes — slow, subjective, and blind at night. Cairo is the target deployment.",
    )


def s05_dataset(prs, summary):
    slide = chrome(prs, "3.2  DATASET", "RDD2022 — 47,420 images, 6 countries, CC BY 4.0", 5)
    headers = ["Country", "Train", "Test", "Boxes", "Resolution"]
    widths = [2.6, 1.3, 1.2, 1.3, 1.7]
    rows = [
        ["Japan", "10,506", "2,627", "16,470", "600 × 600"],
        ["India", "7,706", "1,959", "6,831", "720 × 720"],
        ["Czech Republic", "2,829", "709", "1,745", "600 × 600"],
        ["Norway", "8,161", "2,040", "11,229", "3650 × 2044"],
        ["United States", "4,805", "1,200", "11,014", "640 × 640"],
        ["China (bike + drone)", "4,378", "500", "7,718", "512 × 512"],
        ["Total", f"{summary['train_images']:,}", f"{summary['test_images']:,}", f"{summary['train_instances']:,}", "—"],
    ]
    x0, y0, rh = 0.5, 1.6, 0.52
    x = x0
    for w_, head in zip(widths, headers):
        rect(slide, x, y0, w_, rh, ASPHALT)
        text(slide, x + 0.12, y0, w_ - 0.15, rh, head, 14, WHITE, bold=True, anchor="middle")
        x += w_
    for r, row in enumerate(rows):
        y = y0 + (r + 1) * rh
        last = r == len(rows) - 1
        fill = "FBEBD0" if last else (CARD if r % 2 == 0 else "EEF0F3")
        x = x0
        for c, (w_, val) in enumerate(zip(widths, row)):
            rect(slide, x, y, w_, rh, fill, BORDER)
            text(slide, x + 0.12, y, w_ - 0.15, rh, val, 14, TEXT, bold=(c == 0 or last), anchor="middle")
            x += w_
    card(slide, 8.85, 1.6, 4.0, 4.16)
    bullets(
        slide,
        9.1,
        1.8,
        3.6,
        3.9,
        [
            ("Source:", "Arya et al., figshare (2022)"),
            ("Camera:", "smartphone on a car (most), Street View, drone"),
            ("Files:", "JPEG + one Pascal VOC XML per image"),
            ("Label:", "class + pixel box. No mask, no severity"),
            ("On disk:", "Czech subset, audited by our code"),
        ],
        size=14,
        gap=9,
    )
    notes(
        slide,
        "≈40 s. Counts are Figures 4–5 of the RDD2022 data article; row sums verified in code. Full archive 12.4 GB; Czech (≈300 MB) is local. "
        "Test images have no public labels, so validation will be a held-out slice of train. 62 % of Czech training XMLs have zero boxes. "
        "Licence CC BY 4.0 — usable with attribution.",
    )


def s06_samples(prs, summary):
    slide = chrome(prs, "3.2  SAMPLES", "One real training image per class", 6)
    for i, code in enumerate(CLASSES):
        col, row = i % 2, i // 2
        x = 0.5 + col * 6.2
        y = 1.55 + row * 2.72
        px, py, pw, ph = picture_fit(slide, SAMPLES / f"{code}_road.jpg", x, y, 3.55, 2.3)
        class_chip(slide, x + 3.75, y + 0.5, code, w=2.55, size=13)
        text(slide, x + 3.8, y + 1.05, 2.3, 1.1, {
            "D00": "Along the driving direction",
            "D10": "Across the lane",
            "D20": "Mesh of cracks, whole patch",
            "D40": "A hole; smallest class",
        }[code], 13, MUTED)
        text(slide, px, py + ph + 0.04, pw, 0.22, summary["czech"]["samples"][code]["source_image"], 9, MUTED, font=MONO)
    notes(
        slide,
        "≈25 s. Czech training frames, boxes drawn from the XML by analysis/build_figures.py, tops cropped for glare. "
        "A crack is a thin line inside a big rectangle — that is why tight IoU is hard for D00/D10.",
    )


def s07_distribution(prs, summary):
    totals = summary["class_totals"]
    n = summary["train_instances"]
    slide = chrome(prs, "3.2  CLASS DISTRIBUTION", "Longitudinal cracks are almost half of all boxes", 7)
    picture_fit(slide, FIG / "class_distribution.png", 0.5, 1.5, 7.9, 5.4, border=False)
    card(slide, 8.65, 1.6, 4.2, 5.2)
    y = 1.85
    for code in CLASSES:
        rect(slide, 8.9, y, 0.2, 0.55, CLASS_COLORS[code])
        text(slide, 9.25, y, 0.9, 0.55, code, 16, TEXT, bold=True, anchor="middle")
        text(slide, 10.1, y, 2.6, 0.55, f"{totals[code]:,}  ({totals[code] / n:.0%})", 16, TEXT, anchor="middle")
        y += 0.7
    bullets(
        slide,
        8.9,
        4.85,
        3.75,
        1.8,
        [
            f"{totals['D00'] / totals['D40']:.0f} : 1 between largest and smallest class",
            "Potholes are the rarest — and the most dangerous",
            "→ report per-class AP, not one average",
        ],
        size=13,
        gap=6,
    )
    notes(
        slide,
        "≈30 s. Training split only (test labels private). Imbalance also differs by country: India has 3,187 potholes but 68 transverse cracks; "
        "the US is the reverse (135 potholes). That is why validation is stratified per country.",
    )


def s08_challenges(prs, summary):
    geo = summary["czech"]["geometry"]
    empty = summary["czech"]["empty_annotations"] / summary["czech"]["xml_files"]
    slide = chrome(prs, "3.2  CHALLENGES", "What will make the detector fail", 8)
    blur = summary["czech"]["blur_sample"]
    items = [
        ("Class imbalance", "D00 is 47 % of boxes, D40 only 12 %", None),
        ("Small objects", f"median pothole = {geo['D40']['median_box_area_fraction']:.1%} of the frame", None),
        ("Mostly empty frames", f"{empty:.0%} of Czech frames have no damage", None),
        ("Domain shift", "5 camera types, 512² to 3650×2044, six countries", None),
        ("Motion blur", "handheld phone on a moving car (real frame →)", SAMPLES / "blur.jpg"),
        ("Near-duplicates", "consecutive frames — split by sequence, not at random", None),
    ]
    for i, (head, body, image) in enumerate(items):
        col, row = i % 2, i // 2
        x = 0.5 + col * 6.2
        y = 1.6 + row * 1.7
        card(slide, x, y, 6.0, 1.5, accent=AMBER if i % 2 == 0 else ASPHALT_2)
        text_w = 2.7 if image else 5.4
        text(slide, x + 0.35, y + 0.18, text_w, 0.45, head, 19, TEXT, bold=True)
        text(slide, x + 0.35, y + 0.7, text_w, 0.7, body, 15, MUTED)
        if image:
            picture_fit(slide, image, x + 3.1, y + 0.1, 2.75, 1.3)
    notes(
        slide,
        f"≈40 s. Every line is a measured number. The blur frame is {blur['source_image']}, the lowest Laplacian variance over the road "
        "region in the Czech training set — an underpass shot from a moving car. Also: windscreen glare and dashboard in every frame, "
        "parked cars hiding the kerb lane, label noise (crack extent is a judgement call), no night images. "
        "D10 boxes are 5.3× wider than tall vs 0.77 for D00 → no rotation augmentation, it would swap the classes.",
    )


def s09_justification(prs):
    slide = chrome(prs, "3.2  JUSTIFICATION", "Right task, wrong geography", 9)
    card(slide, 0.5, 1.7, 6.0, 3.9, accent=GREEN)
    text(slide, 0.85, 1.9, 5.4, 0.5, "Why it fits", 22, GREEN, bold=True)
    bullets(slide, 0.85, 2.7, 5.3, 2.8, [
        "The pictures look like what our camera will see: a phone on a car, pointed at the road ahead.",
        "It marks exactly what we want to find — a box around every crack and pothole, sorted into four types.",
    ], size=17, gap=18)
    card(slide, 6.85, 1.7, 6.0, 3.9, accent=RED)
    text(slide, 7.2, 1.9, 5.4, 0.5, "Where it falls short", 22, RED, bold=True)
    bullets(slide, 7.2, 2.7, 5.3, 2.8, [
        "None of the roads are in Egypt, so Cairo streets will look unfamiliar to the model at first.",
        "A hairline crack and a wheel-breaking pothole get the same label — the data says nothing about how bad the damage is.",
    ], size=17, gap=18)
    text(slide, 0.5, 5.95, 12.3, 0.5, "So: train on RDD2022 first, then check the gap with a small set of Cairo dashcam frames later.", 15, MUTED, italic=True, align="center")
    notes(
        slide,
        "≈25 s. Extra points if asked: it is the largest public set with a permissive licence; six countries let us measure generalisation; "
        "labels are boxes not masks, so thin cracks are coarsely captured; frames are daytime only; official test labels are private.",
    )


def s10_model(prs):
    slide = chrome(prs, "3.3  MODEL & TOOLS", "YOLOv8s, fine-tuned from COCO weights", 10)
    label_row(slide, 0.5, 1.6, 12.35, 0.95, "Architecture", "YOLOv8s — boxes + classes, real-time, 11 M params fits a 4 GB GPU", head_w=2.4, size=17)
    label_row(slide, 0.5, 2.7, 12.35, 0.95, "Training", "Fine-tune all layers from COCO; 38k images is too few to train from scratch", head_w=2.4, size=17)
    label_row(slide, 0.5, 3.8, 12.35, 0.95, "Recipe", "640 px, batch 8, ≤100 epochs, early stop on val mAP50; h-flip + mosaic, no rotation", head_w=2.4, size=17)
    label_row(slide, 0.5, 4.9, 12.35, 0.95, "Tools", "PyTorch, Ultralytics, OpenCV · VOC → YOLO converter · RTX 3050 4 GB, Colab fallback", head_w=2.4, size=17)
    text(slide, 0.5, 6.15, 12.3, 0.5, "Rejected: Faster R-CNN (slow, two-stage), DETR/ViT (data-hungry), U-Net (no masks in the labels).", 14, MUTED, italic=True, align="center")
    notes(
        slide,
        "≈40 s. Why YOLO: labels are boxes, many per frame, and an in-car warning needs real time. Why fine-tune: 38k images is medium — "
        "enough to adapt, not to learn from random init. Why no rotation: a quarter turn turns a transverse crack into a longitudinal one. "
        "4 GB VRAM is the reason for the small variant; YOLOv8n is the fallback. Start on Czech to verify the pipeline, then add countries.",
    )


def s11_evaluation(prs):
    slide = chrome(prs, "3.4  EVALUATION", "Metrics that survive a 4 : 1 imbalance", 11)
    rows = [
        ("mAP@0.5", "Primary. Standard for detection, averaged over classes", AMBER),
        ("mAP@0.5:0.95", "Localisation quality — will be low for thin cracks", ASPHALT_2),
        ("Per-class AP", "So D00 cannot hide a weak D40", GREEN),
        ("Precision / Recall / F1", "At one confidence threshold — the driver's operating point", RED),
        ("Per country", "To expose domain shift instead of averaging it away", MUTED),
    ]
    for i, (head, body, accent) in enumerate(rows):
        y = 1.6 + i * 0.98
        card(slide, 0.5, y, 12.35, 0.85, accent=accent)
        text(slide, 0.85, y, 3.6, 0.85, head, 18, TEXT, bold=True, anchor="middle")
        text(slide, 4.6, y, 8.0, 0.85, body, 16, TEXT, anchor="middle")
    text(slide, 0.5, 6.55, 12.3, 0.4, "Not used: plain accuracy — meaningless with 62 % empty frames.", 14, MUTED, italic=True, align="center")
    notes(
        slide,
        "≈30 s. mAP because it is detection; per class because of imbalance; per country because of domain shift; F1 at a fixed confidence "
        "because a warning system has one threshold and F1 was the official CRDDC'2022 metric.",
    )


def s12_references(prs):
    slide = chrome(prs, "REFERENCES", "Sources", 12)
    refs = [
        "Arya, D., Maeda, H., Ghosh, S. K., Toshniwal, D., & Sekimoto, Y. (2024). RDD2022: A multi-national image dataset for automatic road damage detection. Geoscience Data Journal, 11(4), 846–862.",
        "Arya, D., et al. (2022). RDD2022 dataset. figshare. https://doi.org/10.6084/m9.figshare.21431547 — CC BY 4.0.",
        "Maeda, H., et al. (2018). Road damage detection and classification using deep neural networks with smartphone images. Computer-Aided Civil and Infrastructure Engineering, 33(12).",
        "Jocher, G., Chaurasia, A., & Qiu, J. (2023). Ultralytics YOLOv8. https://github.com/ultralytics/ultralytics",
    ]
    bullets(slide, 0.5, 1.7, 12.3, 4.5, refs, size=15, gap=16, marker="▪")
    notes(slide, "Dataset counts are from the 2024 data article (Figures 4–5); Czech-specific numbers are from our own XML audit.")


# --------------------------------------------------------------------------- build
def build() -> Path:
    summary = json.loads((FIG / "summary.json").read_text(encoding="utf-8"))
    if "io_sample" not in summary["czech"]:
        raise SystemExit("summary.json has no io_sample — run analysis/build_figures.py first.")

    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    prs.core_properties.title = "DMET 901 Milestone 1 — Road Damage Detection (RDD2022)"
    prs.core_properties.subject = "Computer Vision"
    prs.core_properties.category = "Milestone 1"

    s01_title(prs, summary)
    s02_problem(prs)
    s03_input_output(prs, summary)
    s04_motivation(prs)
    s05_dataset(prs, summary)
    s06_samples(prs, summary)
    s07_distribution(prs, summary)
    s08_challenges(prs, summary)
    s09_justification(prs)
    s10_model(prs)
    s11_evaluation(prs)
    s12_references(prs)

    assert len(prs.slides) == TOTAL, len(prs.slides)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    return OUT


if __name__ == "__main__":
    print(build())
